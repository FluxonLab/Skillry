"""Content-addressed archive receiver and local/SSH sender."""
import hashlib
import json
import os
import pathlib
import select
import secrets
import shlex
import signal
import subprocess
import sys
import threading
import time
from contextlib import contextmanager

from .engine import StorageError, dump, no_symlink_components


@contextmanager
def managed_process(process):
    old_term = None
    if threading.current_thread() is threading.main_thread():
        old_term = signal.getsignal(signal.SIGTERM)

        def cancelled(_signal, _frame):
            raise StorageError("cancelled", "Transfer was cancelled")

        signal.signal(signal.SIGTERM, cancelled)
    try:
        yield process
    finally:
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
        if old_term is not None:
            signal.signal(signal.SIGTERM, old_term)


def run_group(command, timeout, input_bytes=None):
    process = subprocess.Popen(command, stdin=subprocess.PIPE if input_bytes is not None else subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, start_new_session=True)
    with managed_process(process):
        try:
            output, _ = process.communicate(input=input_bytes, timeout=timeout)
        except subprocess.TimeoutExpired:
            raise StorageError("timeout", "External command exceeded configured deadline")
        if len(output) > 65536:
            raise StorageError("invalid_response", "External command response is too large")
        return process.returncode, output


def target_paths(root, digest):
    root = pathlib.Path(root)
    return root / "objects" / digest[:2] / digest, root / "receipts" / (digest + ".json")


def secure_directory(root, names):
    no_symlink_components(root)
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    path = pathlib.Path(root)
    try:
        for name in names:
            if name in ("", ".", "..") or "/" in name:
                raise StorageError("invalid_transfer", "Invalid archive component")
            try:
                os.mkdir(name, 0o700, dir_fd=fd)
            except FileExistsError:
                pass
            child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
            path = path / name
        return fd, path
    except Exception:
        os.close(fd)
        raise


def sync_directory(fd):
    os.fsync(fd)


def validate_origin(origin):
    if origin is None:
        return None
    required = ("job_id", "original_name", "source_host", "category", "rights", "received_at")
    if not isinstance(origin, dict) or any(key not in origin for key in required):
        raise StorageError("invalid_origin", "Missing archive origin fields")
    for key in ("job_id", "original_name", "source_host", "category", "rights"):
        value = origin[key]
        if not isinstance(value, str) or not value or len(value) > 255 or "\0" in value or (key == "original_name" and ("/" in value or "\\" in value)):
            raise StorageError("invalid_origin", "Invalid archive origin field")
    if origin["rights"] != "unknown" or type(origin["received_at"]) is not int:
        raise StorageError("invalid_origin", "Invalid rights or timestamp")
    if origin.get("tag") is not None and (not isinstance(origin["tag"], str) or len(origin["tag"]) > 100):
        raise StorageError("invalid_origin", "Invalid archive tag")
    return {key: origin.get(key) for key in (*required, "tag")}


def merge_origin(record, origin):
    origins = record.get("origins", [])
    if not isinstance(origins, list):
        raise StorageError("invalid_receipt", "Malformed origins")
    if origin and not any(item.get("job_id") == origin["job_id"] and item.get("source_host") == origin["source_host"] for item in origins):
        origins.append(origin)
    record["origins"] = origins
    return record


def catalog_reconcile(config, root, digest, size):
    """Link a verified object to the owner-configured catalog, if present."""
    bridge = config.get("catalog_bridge")
    if not bridge:
        return {"state": "not_configured", "last_attempt_at": None}
    path = verified_receipt(root, digest, size)
    if not path:
        return {"state": "gap", "error": "archive_proof_missing", "last_attempt_at": int(time.time())}
    attempted = int(time.time())
    try:
        command = [*bridge["command"], "--require-sha256", digest]
        code, output = run_group(command, bridge.get("timeout_seconds", 120))
        response = json.loads(output)
    except StorageError as exc:
        if exc.code == "cancelled":
            raise
        response = None
        code = None
    except (OSError, ValueError):
        response = None
        code = None
    if code == 0 and isinstance(response, dict) and response.get("status") in ("COMPLETED", "NO_CHANGE", "IDEMPOTENT") and response.get("source_id") and response.get("snapshot_id") and response.get("matched_sha256") == digest:
        outcome = {"state": "linked", "source_id": response["source_id"], "snapshot_id": response["snapshot_id"],
                   "source_name": response.get("source_name"), "last_attempt_at": attempted, "error": None}
    else:
        outcome = {"state": "gap", "source_id": None, "snapshot_id": None, "source_name": None,
                   "last_attempt_at": attempted, "error": (response.get("reason") if isinstance(response, dict) else None) or "bridge_unavailable"}
    _, receipt = target_paths(root, digest)
    receipt_fd, _ = secure_directory(root, ("receipts",))
    try:
        record = json.loads(receipt.read_text())
        record["catalog_sync"] = outcome
        write_receipt(receipt_fd, receipt.name, record)
    finally:
        os.close(receipt_fd)
    return outcome


def verified_receipt(root, digest, size):
    target, receipt = target_paths(root, digest)
    try:
        no_symlink_components(target)
        no_symlink_components(receipt)
        record = json.loads(receipt.read_text())
        if target.is_symlink() or receipt.is_symlink() or record.get("sha256") != digest or record.get("bytes") != size or not target.is_file():
            return None
        h = hashlib.sha256()
        with target.open("rb") as stream:
            for part in iter(lambda: stream.read(1024 * 1024), b""):
                h.update(part)
        return str(target) if h.hexdigest() == digest else None
    except (OSError, ValueError):
        return None


def write_receipt(receipt_dir_fd, name, record):
    stage_name = ".receipt-" + secrets.token_hex(12)
    fd = os.open(stage_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=receipt_dir_fd)
    try:
        with os.fdopen(fd, "w") as out:
            out.write(dump(record) + "\n")
            out.flush()
            os.fsync(out.fileno())
        os.replace(stage_name, name, src_dir_fd=receipt_dir_fd, dst_dir_fd=receipt_dir_fd)
        sync_directory(receipt_dir_fd)
    finally:
        try:
            os.unlink(stage_name, dir_fd=receipt_dir_fd)
        except FileNotFoundError:
            pass


def receive_stream(root, digest, size, stream, origin=None):
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest) or type(size) is not int or size < 0:
        raise StorageError("invalid_transfer", "Invalid transfer header")
    origin = validate_origin(origin)
    root = pathlib.Path(root)
    if not root.is_dir() or root.is_symlink():
        raise StorageError("archive_offline", "Archive root is unavailable")
    objects_fd, objects_dir = secure_directory(str(root), ("objects", digest[:2]))
    try:
        receipts_fd, receipts_dir = secure_directory(str(root), ("receipts",))
    except Exception:
        os.close(objects_fd)
        raise
    target = objects_dir / digest
    receipt = receipts_dir / (digest + ".json")
    try:
        existing = verified_receipt(root, digest, size)
        if existing:
            remaining = size
            while remaining:
                part = stream.read(min(1024 * 1024, remaining))
                if not part:
                    raise StorageError("interrupted", "Source stream ended early")
                remaining -= len(part)
            if origin:
                record = json.loads(receipt.read_text())
                write_receipt(receipts_fd, receipt.name, merge_origin(record, origin))
            return {"sha256": digest, "bytes": size, "path": existing, "deduplicated": True}
        stage_name = ".stage-" + secrets.token_hex(12)
        fd = os.open(stage_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=objects_fd)
        h = hashlib.sha256()
        remaining = size
        try:
            with os.fdopen(fd, "wb") as out:
                while remaining:
                    part = stream.read(min(1024 * 1024, remaining))
                    if not part:
                        raise StorageError("interrupted", "Source stream ended early")
                    h.update(part)
                    out.write(part)
                    remaining -= len(part)
                out.flush()
                os.fsync(out.fileno())
            if h.hexdigest() != digest:
                raise StorageError("digest_mismatch", "Received bytes do not match SHA-256")
            if target.is_symlink() or receipt.is_symlink():
                raise StorageError("symlink_path", "Archive object or receipt is a symlink")
            if target.exists():
                existing_hash = hashlib.sha256()
                with target.open("rb") as existing_file:
                    for chunk in iter(lambda: existing_file.read(1024 * 1024), b""):
                        existing_hash.update(chunk)
                if existing_hash.hexdigest() != digest or target.stat().st_size != size:
                    raise StorageError("archive_collision", "Existing archive object differs")
            else:
                try:
                    os.link(stage_name, digest, src_dir_fd=objects_fd, dst_dir_fd=objects_fd, follow_symlinks=False)
                except FileExistsError:
                    existing_hash = hashlib.sha256()
                    with target.open("rb") as existing_file:
                        for chunk in iter(lambda: existing_file.read(1024 * 1024), b""):
                            existing_hash.update(chunk)
                    if existing_hash.hexdigest() != digest or target.stat().st_size != size:
                        raise StorageError("archive_collision", "Concurrent archive object differs")
                sync_directory(objects_fd)
            record = {"schema_version": 1, "sha256": digest, "bytes": size, "path": str(target)}
            write_receipt(receipts_fd, receipt.name, merge_origin(record, origin))
            return {**record, "deduplicated": False}
        finally:
            try:
                os.unlink(stage_name, dir_fd=objects_fd)
            except FileNotFoundError:
                pass
    finally:
        os.close(objects_fd)
        os.close(receipts_fd)


def check_archive_root(archive):
    root = archive["root"]
    if not os.path.isdir(root) or os.path.islink(root):
        raise StorageError("archive_offline", "Archive root is unavailable")
    for component in (pathlib.Path(root),) + tuple(pathlib.Path(root).parents):
        if component.is_symlink():
            raise StorageError("symlink_path", "Archive root contains a symlink")
    mount = archive.get("mount_path")
    if mount and (not os.path.ismount(mount) or os.path.commonpath((root, mount)) != mount):
        raise StorageError("archive_offline", "Expected archive volume is not mounted")
    expected = archive.get("expected_device")
    if expected is not None and os.stat(root).st_dev != expected:
        raise StorageError("archive_device_changed", "Archive volume identity changed")


def rclone_path(archive, digest):
    return archive["root"].rstrip("/") + "/objects/" + digest[:2] + "/" + digest


def verify_rclone(archive, digest, size):
    target = rclone_path(archive, digest)
    binary = archive["binary"]
    if not os.path.isfile(binary):
        return None
    try:
        process = subprocess.Popen([binary, "cat", target], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                   start_new_session=True)
    except OSError:
        return None
    h = hashlib.sha256()
    count = 0
    with managed_process(process):
        try:
            deadline = time.monotonic() + archive.get("verify_timeout_seconds", 21600)
            while True:
                if time.monotonic() >= deadline:
                    return None
                readable, _, _ = select.select([process.stdout], [], [], max(0, deadline - time.monotonic()))
                if not readable:
                    return None
                part = os.read(process.stdout.fileno(), 1024 * 1024)
                if not part:
                    break
                count += len(part)
                if count > size:
                    return None
                h.update(part)
            code = process.wait(timeout=max(0.1, deadline - time.monotonic()))
        except (OSError, subprocess.TimeoutExpired):
            return None
    return target if code == 0 and count == size and h.hexdigest() == digest else None


def stream_ssh(command, source_path, header, size, timeout):
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                               start_new_session=True)
    with managed_process(process), open(source_path, "rb") as source:
        os.set_blocking(process.stdin.fileno(), False)
        os.set_blocking(process.stdout.fileno(), False)
        pending = memoryview((dump(header) + "\n").encode())
        remaining = size
        input_closed = False
        output = bytearray()
        deadline = time.monotonic() + timeout
        while True:
            if time.monotonic() >= deadline:
                raise StorageError("timeout", "SSH archive transfer exceeded configured deadline")
            if not pending and remaining:
                chunk = source.read(min(1024 * 1024, remaining))
                if not chunk:
                    raise StorageError("interrupted", "Source stream ended before declared size")
                pending = memoryview(chunk)
                remaining -= len(chunk)
            if not pending and not remaining and not input_closed:
                process.stdin.close()
                input_closed = True
            readable, writable, _ = select.select([process.stdout], [] if input_closed or not pending else [process.stdin], [],
                                                    min(1, max(0, deadline - time.monotonic())))
            if writable:
                try:
                    written = os.write(process.stdin.fileno(), pending)
                    pending = pending[written:]
                except BrokenPipeError:
                    raise StorageError("archive_offline", "Receiver closed transfer stream")
            if readable:
                part = os.read(process.stdout.fileno(), 65536)
                if not part:
                    break
                output.extend(part)
                if len(output) > 65536:
                    raise StorageError("invalid_receipt", "Receiver response is too large")
        code = process.wait(timeout=max(0.1, deadline - time.monotonic()))
        return code, bytes(output)


def transfer(path, archive, digest, size, critical=False, origin=None):
    kind = archive.get("kind", "none")
    if kind == "local":
        check_archive_root(archive)
        with open(path, "rb") as source:
            return receive_stream(archive["root"], digest, size, source, origin=origin)
    if kind == "ssh":
        pieces = [archive["receiver_command"]]
        if archive.get("receiver_config"):
            pieces += ["--config", archive["receiver_config"]]
        pieces += ["receive", "--root", archive["root"], "--sha256", digest, "--bytes", str(size)]
        if archive.get("expected_device") is not None:
            pieces += ["--expected-device", str(archive["expected_device"])]
        if archive.get("mount_path"):
            pieces += ["--mount-path", archive["mount_path"]]
        if critical:
            pieces.append("--critical")
        command = " ".join(shlex.quote(value) for value in pieces)
        ssh_command = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
                       "-o", "ServerAliveInterval=15", "-o", "ServerAliveCountMax=3", archive["ssh_alias"], command]
        header = {"schema_version": 1, "sha256": digest, "bytes": size, "origin": validate_origin(origin)}
        try:
            code, output = stream_ssh(ssh_command, path, header, size, archive.get("transfer_timeout_seconds", 21600))
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise StorageError("archive_offline", str(exc))
        if code:
            raise StorageError("archive_offline", "Receiver failed or archive unavailable")
        try:
            response = json.loads(output)
        except ValueError:
            raise StorageError("invalid_receipt", "Receiver did not return JSON")
        if not response.get("ok") or response.get("sha256") != digest or response.get("bytes") != size or (critical and not response.get("second_receipt")):
            raise StorageError("invalid_receipt", "Receiver proof does not match source")
        return response
    if kind == "rclone":
        binary = archive["binary"]
        if not os.path.isfile(binary):
            raise StorageError("archive_offline", "rclone binary is unavailable")
        target = rclone_path(archive, digest)
        if verify_rclone(archive, digest, size) == target:
            return {"sha256": digest, "bytes": size, "path": target, "deduplicated": True}
        try:
            code, _ = run_group([binary, "copyto", "--immutable", path, target], archive.get("transfer_timeout_seconds", 21600))
        except (OSError, StorageError):
            raise StorageError("archive_offline", "rclone transfer failed or timed out")
        if code or verify_rclone(archive, digest, size) != target:
            raise StorageError("archive_unverified", "rclone copy could not be fully verified")
        return {"sha256": digest, "bytes": size, "path": target, "deduplicated": False}
    raise StorageError("archive_offline", "Archive target is not configured")


def reconcile_remote_catalog(archive, digest, size):
    if archive.get("kind") != "ssh":
        raise StorageError("invalid_archive", "Catalog reconcile requires SSH archive")
    pieces = [archive["receiver_command"]]
    if archive.get("receiver_config"):
        pieces += ["--config", archive["receiver_config"]]
    pieces += ["catalog", "--root", archive["root"], "--sha256", digest, "--bytes", str(size)]
    if archive.get("expected_device") is not None:
        pieces += ["--expected-device", str(archive["expected_device"])]
    if archive.get("mount_path"):
        pieces += ["--mount-path", archive["mount_path"]]
    command = " ".join(shlex.quote(value) for value in pieces)
    try:
        code, output = run_group(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
                                  "-o", "ServerAliveInterval=15", "-o", "ServerAliveCountMax=3",
                                  archive["ssh_alias"], command], archive.get("catalog_timeout_seconds", 3700))
        response = json.loads(output)
    except (OSError, StorageError, ValueError):
        raise StorageError("catalog_unavailable", "Receiver catalog reconcile failed")
    if code or not response.get("ok") or response.get("sha256") != digest or response.get("bytes") != size:
        raise StorageError("catalog_unavailable", "Receiver catalog reconcile did not verify object")
    return response.get("catalog_sync")


def verify_remote(archive, digest, size, critical=False, second_expected=None, require_catalog=False):
    if archive.get("kind") == "local":
        check_archive_root(archive)
        if require_catalog:
            _, receipt = target_paths(archive["root"], digest)
            try:
                if json.loads(receipt.read_text()).get("catalog_sync", {}).get("state") != "linked":
                    return None
            except (OSError, ValueError):
                return None
        return verified_receipt(archive["root"], digest, size)
    if archive.get("kind") == "rclone":
        return verify_rclone(archive, digest, size)
    if archive.get("kind") != "ssh":
        return None
    pieces = [archive["receiver_command"]]
    if archive.get("receiver_config"):
        pieces += ["--config", archive["receiver_config"]]
    pieces += ["verify", "--root", archive["root"], "--sha256", digest, "--bytes", str(size)]
    if archive.get("expected_device") is not None:
        pieces += ["--expected-device", str(archive["expected_device"])]
    if archive.get("mount_path"):
        pieces += ["--mount-path", archive["mount_path"]]
    if critical:
        pieces.append("--critical")
    if require_catalog:
        pieces.append("--require-catalog")
    command = " ".join(shlex.quote(value) for value in pieces)
    try:
        code, output = run_group(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
                                  "-o", "ServerAliveInterval=15", "-o", "ServerAliveCountMax=3",
                                  archive["ssh_alias"], command], archive.get("verify_timeout_seconds", 21600))
        response = json.loads(output)
        if code == 0 and response.get("ok") and response.get("sha256") == digest and response.get("bytes") == size and (not critical or response.get("second_receipt")) and (second_expected is None or response.get("second_receipt") == second_expected) and (not require_catalog or response.get("catalog_sync", {}).get("state") == "linked"):
            return response.get("path")
    except (OSError, StorageError, ValueError):
        pass
    return None


def require_independent_second(primary_root, primary_path, second, second_path=None):
    if second.get("kind") == "none":
        raise StorageError("second_copy_required", "Receiver has no second archive")
    if second.get("kind") == "local":
        check_archive_root(second)
        if (os.path.realpath(primary_root) == os.path.realpath(second["root"])
                or os.stat(primary_root).st_dev == os.stat(second["root"]).st_dev):
            raise StorageError("second_not_independent", "Critical second copy is on the same device")
    if second_path is not None:
        if second_path == primary_path:
            raise StorageError("second_not_independent", "Critical second copy resolves to primary object")
        if second.get("kind") == "local" and (
                os.path.realpath(primary_path) == os.path.realpath(second_path)
                or os.path.samestat(os.stat(primary_path), os.stat(second_path))
                or os.stat(primary_path).st_dev == os.stat(second_path).st_dev):
            raise StorageError("second_not_independent", "Critical second copy is on the same device")


def receiver_main(args):
    try:
        check_archive_root({"root": args.root, "expected_device": args.expected_device, "mount_path": args.mount_path})
        header_line = sys.stdin.buffer.readline(4097)
        if not header_line.endswith(b"\n") or len(header_line) > 4096:
            raise StorageError("invalid_transfer", "Missing bounded transfer header")
        try:
            header = json.loads(header_line)
        except ValueError:
            raise StorageError("invalid_transfer", "Transfer header is not JSON")
        if header.get("schema_version") != 1 or header.get("sha256") != args.sha256 or header.get("bytes") != args.bytes:
            raise StorageError("invalid_transfer", "Transfer header does not match command")
        result = receive_stream(args.root, args.sha256, args.bytes, sys.stdin.buffer, origin=header.get("origin"))
        if args.critical:
            from .engine import load_config
            config = load_config(pathlib.Path(args.config))
            second = config["second_archive"]
            require_independent_second(args.root, result["path"], second)
            second_result = transfer(result["path"], second, args.sha256, args.bytes)
            require_independent_second(args.root, result["path"], second, second_result["path"])
            result["second_receipt"] = {"sha256": args.sha256, "bytes": args.bytes, "path": second_result["path"],
                                        "kind": second["kind"], "root": second["root"]}
            _, receipt_file = target_paths(args.root, args.sha256)
            record = json.loads(receipt_file.read_text())
            record["second_receipt"] = result["second_receipt"]
            receipts_fd, _ = secure_directory(args.root, ("receipts",))
            try:
                write_receipt(receipts_fd, receipt_file.name, record)
            finally:
                os.close(receipts_fd)
        from .engine import load_config
        config = load_config(pathlib.Path(args.config))
        result["catalog_sync"] = catalog_reconcile(config, args.root, args.sha256, args.bytes)
        print(dump({"schema_version": 1, "ok": True, **result}))
        return 0
    except StorageError as exc:
        print(dump({"schema_version": 1, "ok": False, "error": {"code": exc.code, "message": str(exc)}}))
        return 1


def verifier_main(args):
    try:
        check_archive_root({"root": args.root, "expected_device": args.expected_device, "mount_path": args.mount_path})
    except StorageError:
        path = None
    else:
        path = verified_receipt(args.root, args.sha256, args.bytes)
    second_receipt = None
    if path and args.critical:
        from .engine import load_config
        try:
            config = load_config(pathlib.Path(args.config))
            second = config["second_archive"]
            require_independent_second(args.root, path, second)
            secondary_path = verify_remote(second, args.sha256, args.bytes)
            if secondary_path:
                require_independent_second(args.root, path, second, secondary_path)
                second_receipt = {"sha256": args.sha256, "bytes": args.bytes, "path": secondary_path,
                                  "kind": second["kind"], "root": second["root"]}
            else:
                path = None
        except (StorageError, OSError):
            path = None
    catalog_sync = None
    if path:
        _, receipt_file = target_paths(args.root, args.sha256)
        try:
            catalog_sync = json.loads(receipt_file.read_text()).get("catalog_sync")
        except (OSError, ValueError):
            path = None
    if args.require_catalog and (not isinstance(catalog_sync, dict) or catalog_sync.get("state") != "linked"):
        path = None
    if path:
        print(dump({"schema_version": 1, "ok": True, "sha256": args.sha256, "bytes": args.bytes, "path": path,
                    "second_receipt": second_receipt, "catalog_sync": catalog_sync}))
        return 0
    print(dump({"schema_version": 1, "ok": False, "error": {"code": "invalid_receipt", "message": "Archive object or receipt does not verify"}}))
    return 1


def catalog_main(args):
    try:
        check_archive_root({"root": args.root, "expected_device": args.expected_device, "mount_path": args.mount_path})
        from .engine import load_config
        config = load_config(pathlib.Path(args.config))
        outcome = catalog_reconcile(config, args.root, args.sha256, args.bytes)
        if not verified_receipt(args.root, args.sha256, args.bytes):
            raise StorageError("invalid_receipt", "Archive proof no longer verifies")
        print(dump({"schema_version": 1, "ok": True, "sha256": args.sha256, "bytes": args.bytes,
                    "catalog_sync": outcome}))
        return 0
    except StorageError as exc:
        print(dump({"schema_version": 1, "ok": False, "error": {"code": exc.code, "message": str(exc)}}))
        return 1


def stream_archive_process(command, digest, size, output, timeout):
    process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, start_new_session=True)
    hasher = hashlib.sha256()
    count = 0
    with managed_process(process):
        deadline = time.monotonic() + timeout
        while True:
            if time.monotonic() >= deadline:
                raise StorageError("timeout", "Archive retrieval exceeded configured deadline")
            readable, _, _ = select.select([process.stdout], [], [], min(1, max(0, deadline - time.monotonic())))
            if not readable:
                continue
            part = os.read(process.stdout.fileno(), 1024 * 1024)
            if not part:
                break
            count += len(part)
            if count > size:
                raise StorageError("digest_mismatch", "Archive stream exceeded receipt size")
            hasher.update(part)
            output.write(part)
        code = process.wait(timeout=max(0.1, deadline - time.monotonic()))
        if code or count != size or hasher.hexdigest() != digest:
            raise StorageError("digest_mismatch", "Retrieved archive stream failed verification")


def read_archive(archive, digest, size, output):
    kind = archive.get("kind")
    if kind == "local":
        check_archive_root(archive)
        path = verified_receipt(archive["root"], digest, size)
        if not path:
            raise StorageError("invalid_receipt", "Local archive no longer verifies")
        hasher = hashlib.sha256()
        count = 0
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, "rb") as source:
            for part in iter(lambda: source.read(1024 * 1024), b""):
                count += len(part)
                if count > size:
                    raise StorageError("digest_mismatch", "Archive object exceeds receipt size")
                hasher.update(part)
                output.write(part)
        if count != size or hasher.hexdigest() != digest:
            raise StorageError("digest_mismatch", "Local archive changed during retrieval")
        return
    if kind == "rclone":
        stream_archive_process([archive["binary"], "cat", rclone_path(archive, digest)], digest, size, output,
                               archive.get("transfer_timeout_seconds", 21600))
        return
    if kind == "ssh":
        pieces = [archive["receiver_command"]]
        if archive.get("receiver_config"):
            pieces += ["--config", archive["receiver_config"]]
        pieces += ["read", "--root", archive["root"], "--sha256", digest, "--bytes", str(size)]
        if archive.get("expected_device") is not None:
            pieces += ["--expected-device", str(archive["expected_device"])]
        if archive.get("mount_path"):
            pieces += ["--mount-path", archive["mount_path"]]
        command = " ".join(shlex.quote(value) for value in pieces)
        stream_archive_process(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
                                "-o", "ServerAliveInterval=15", "-o", "ServerAliveCountMax=3",
                                archive["ssh_alias"], command], digest, size, output,
                               archive.get("transfer_timeout_seconds", 21600))
        return
    raise StorageError("archive_offline", "Archive target is not configured")


def reader_main(args):
    try:
        check_archive_root({"root": args.root, "expected_device": args.expected_device, "mount_path": args.mount_path})
        path = verified_receipt(args.root, args.sha256, args.bytes)
        if not path:
            raise StorageError("invalid_receipt", "Archive object no longer verifies")
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, "rb") as source:
            for part in iter(lambda: source.read(1024 * 1024), b""):
                sys.stdout.buffer.write(part)
        sys.stdout.buffer.flush()
        return 0
    except (StorageError, OSError) as exc:
        print(dump({"schema_version": 1, "ok": False, "error": {"code": getattr(exc, "code", "read_failed"), "message": str(exc)}}), file=sys.stderr)
        return 1


def disk_main(args):
    try:
        check_archive_root({"root": args.root, "expected_device": args.expected_device, "mount_path": args.mount_path})
        size = os.statvfs(args.root)
        print(dump({"schema_version": 1, "ok": True, "total_bytes": size.f_blocks * size.f_frsize,
                    "free_bytes": size.f_bavail * size.f_frsize, "device": os.stat(args.root).st_dev}))
        return 0
    except (StorageError, OSError) as exc:
        print(dump({"schema_version": 1, "ok": False, "error": {"code": "archive_offline", "message": str(exc)}}))
        return 1

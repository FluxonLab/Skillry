"""Policy, state and local operations for Skillry Storage.

Only registered, accepted outputs and identified inbox files can be removed.
Every mutation is guarded again immediately before it happens.
"""
import argparse
import contextlib
import fcntl
import gzip
import hashlib
import json
import os
import pathlib
import plistlib
import re
import shutil
import socket
import sqlite3
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import uuid

from . import SCHEMA_VERSION


class StorageError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise StorageError("invalid_arguments", message)


def default_config_path():
    return pathlib.Path.home() / ".config/skillry/storage.json"


def default_state_dir():
    if sys.platform == "darwin":
        return pathlib.Path.home() / "Library/Application Support/SkillryStorage"
    return pathlib.Path(os.environ.get("XDG_STATE_HOME", pathlib.Path.home() / ".local/state")) / "skillry-storage"


DEFAULT = {
    "profile": "generic", "state_dir": None, "intake_dir": None,
    "automatic_cleanup": False, "automatic_archive": False,
    "settle_seconds": 120, "local_grace_seconds": 86400,
    "archive": {"kind": "none"}, "second_archive": {"kind": "none"},
    "workspace_roots": [], "application_roots": [], "remote_hosts": [], "applications": {},
    "retired_app_paths": [], "tools": {}, "archive_tag": None, "app_rollback_root": None,
    "catalog_bridge": None, "retrieval_cache_max_bytes": 32 * 1024 * 1024 * 1024,
    "retrieval_cache_max_items": 8,
    "jev": {"enabled": False, "helper_path": None, "secret_kind": "keychain", "service": None, "account": None},
}


def now():
    return int(time.time())


def dump(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def ensure_absolute(path):
    if not isinstance(path, str) or not os.path.isabs(path):
        raise StorageError("invalid_path", "An absolute path is required")
    return os.path.normpath(path)


def inside(path, roots):
    actual = os.path.realpath(path)
    return any(os.path.commonpath((actual, os.path.realpath(root))) == os.path.realpath(root)
               and actual != os.path.realpath(root) for root in roots)


def no_symlink_components(path):
    current = pathlib.Path(path)
    for component in (current,) + tuple(current.parents):
        if component.is_symlink():
            raise StorageError("symlink_path", "Symlink components are not eligible")


def validate_archive(archive):
    if not isinstance(archive, dict) or archive.get("kind", "none") not in ("none", "local", "ssh", "rclone"):
        raise StorageError("invalid_config", "Archive kind must be none, local, ssh or rclone")
    kind = archive.get("kind", "none")
    if kind in ("local", "ssh"):
        ensure_absolute(archive.get("root"))
        if "catalog_required" in archive and type(archive["catalog_required"]) is not bool:
            raise StorageError("invalid_config", "catalog_required must be boolean")
        if "catalog_timeout_seconds" in archive and (type(archive["catalog_timeout_seconds"]) is not int or not 1 <= archive["catalog_timeout_seconds"] <= 3700):
            raise StorageError("invalid_config", "catalog timeout must be 1-3700 seconds")
        for key in ("transfer_timeout_seconds", "verify_timeout_seconds"):
            if key in archive and (type(archive[key]) is not int or not 1 <= archive[key] <= 86400):
                raise StorageError("invalid_config", key + " must be 1-86400 seconds")
        if archive.get("mount_path") is not None:
            mount = ensure_absolute(archive["mount_path"])
            if not inside(archive["root"], [mount]):
                raise StorageError("invalid_config", "Archive root must be below mount_path")
        if "expected_device" in archive and (type(archive["expected_device"]) is not int or archive["expected_device"] < 0):
            raise StorageError("invalid_config", "Expected archive device must be an integer")
    if kind == "ssh":
        alias = archive.get("ssh_alias")
        if not isinstance(alias, str) or not re.fullmatch(r"[A-Za-z0-9._-]+", alias):
            raise StorageError("invalid_config", "SSH archive requires a fixed host alias")
        command = archive.get("receiver_command")
        if not isinstance(command, str) or not command.startswith("/") or any(c in command for c in " \t\n\r'\"`$;|&<>"):
            raise StorageError("invalid_config", "Receiver command must be one absolute executable path")
        if archive.get("receiver_config") is not None:
            ensure_absolute(archive["receiver_config"])
    if kind == "rclone":
        root = archive.get("root")
        binary = archive.get("binary")
        if not isinstance(root, str) or not re.fullmatch(r"[A-Za-z0-9_-]+:[A-Za-z0-9_./-]+", root) or ".." in root.split("/"):
            raise StorageError("invalid_config", "rclone requires a fixed remote root")
        if not isinstance(binary, str) or not binary.startswith("/"):
            raise StorageError("invalid_config", "rclone requires an absolute binary path")


def validate_config(config):
    if not isinstance(config, dict) or set(config) - set(DEFAULT):
        raise StorageError("invalid_config", "Unknown configuration field")
    for key in ("workspace_roots", "application_roots", "retired_app_paths"):
        if not isinstance(config.get(key), list):
            raise StorageError("invalid_config", key + " must be a list")
        for item in config[key]:
            ensure_absolute(item)
    if config.get("intake_dir") is not None:
        ensure_absolute(config["intake_dir"])
    if config.get("state_dir") is not None:
        ensure_absolute(config["state_dir"])
    if config.get("app_rollback_root") is not None:
        ensure_absolute(config["app_rollback_root"])
    bridge = config.get("catalog_bridge")
    if bridge is not None:
        if not isinstance(bridge, dict) or not isinstance(bridge.get("command"), list) or not bridge["command"]:
            raise StorageError("invalid_config", "catalog_bridge needs a command array")
        command = bridge["command"]
        ensure_absolute(command[0])
        if any(not isinstance(arg, str) or not arg or len(arg) > 1024 for arg in command) or "--apply" not in command:
            raise StorageError("invalid_config", "catalog_bridge requires fixed --apply arguments")
        timeout = bridge.get("timeout_seconds", 120)
        if type(timeout) is not int or not 1 <= timeout <= 3600:
            raise StorageError("invalid_config", "catalog_bridge timeout must be 1-3600 seconds")
    if not isinstance(config["remote_hosts"], list):
        raise StorageError("invalid_config", "remote_hosts must be a list")
    for remote in config["remote_hosts"]:
        validate_archive({**remote, "kind": "ssh"})
        if not isinstance(remote.get("id"), str) or not isinstance(remote.get("name"), str):
            raise StorageError("invalid_config", "Remote host requires id and name")
    for key in ("settle_seconds", "local_grace_seconds"):
        if type(config.get(key)) is not int or config[key] < 0:
            raise StorageError("invalid_config", key + " must be a nonnegative integer")
    if type(config.get("retrieval_cache_max_bytes")) is not int or config["retrieval_cache_max_bytes"] < 1:
        raise StorageError("invalid_config", "retrieval_cache_max_bytes must be positive")
    if type(config.get("retrieval_cache_max_items")) is not int or not 1 <= config["retrieval_cache_max_items"] <= 100:
        raise StorageError("invalid_config", "retrieval_cache_max_items must be 1-100")
    for key in ("automatic_cleanup", "automatic_archive"):
        if type(config.get(key)) is not bool:
            raise StorageError("invalid_config", key + " must be a boolean")
    for key in ("archive", "second_archive"):
        validate_archive(config[key])
    if config["archive"].get("kind") != "none" and config["archive"] == config["second_archive"]:
        raise StorageError("invalid_config", "Second archive must be an independent target")
    if not isinstance(config.get("applications"), dict) or not isinstance(config.get("jev"), dict):
        raise StorageError("invalid_config", "Invalid application or Jev configuration")
    if not isinstance(config.get("tools"), dict) or not isinstance(config.get("profile"), str):
        raise StorageError("invalid_config", "Invalid tools or profile configuration")
    if config.get("archive_tag") is not None and (not isinstance(config["archive_tag"], str) or len(config["archive_tag"]) > 100):
        raise StorageError("invalid_config", "archive_tag must be short text")
    for bundle, role in config["applications"].items():
        if not isinstance(bundle, str) or not isinstance(role, (str, dict)):
            raise StorageError("invalid_config", "Invalid application role")
        if isinstance(role, str):
            ensure_absolute(role)
        else:
            for key in ("canonical", "rollback", "rollback_archive"):
                if key in role:
                    ensure_absolute(role[key])
    return config


def load_config(path):
    if path.exists():
        try:
            user = json.loads(path.read_text())
        except (OSError, ValueError) as exc:
            raise StorageError("invalid_config", str(exc))
        if not isinstance(user, dict):
            raise StorageError("invalid_config", "Configuration must be an object")
    else:
        user = {}
    if "jev" in user and not isinstance(user["jev"], dict):
        raise StorageError("invalid_config", "jev must be an object")
    config = {**DEFAULT, **user}
    config["jev"] = {**DEFAULT["jev"], **user.get("jev", {})}
    return validate_config(config)


def save_config(path, update):
    if not isinstance(update, dict) or set(update) - set(DEFAULT) or "state_dir" in update:
        raise StorageError("invalid_config", "Invalid or immutable configuration field")
    config = load_config(path)
    config.update(update)
    if "jev" in update:
        if not isinstance(update["jev"], dict):
            raise StorageError("invalid_config", "jev must be an object")
        config["jev"] = {**load_config(path)["jev"], **update["jev"]}
    validate_config(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".storage-", dir=str(path.parent))
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w") as stream:
            stream.write(dump(config) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return config


def atomic_json_file(path, record):
    parent = os.path.dirname(path)
    no_symlink_components(parent)
    fd, stage = tempfile.mkstemp(prefix=".storage-", dir=parent)
    try:
        with os.fdopen(fd, "w") as out:
            out.write(dump(record) + "\n")
            out.flush()
            os.fsync(out.fileno())
        os.replace(stage, path)
        directory_fd = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(stage):
            os.unlink(stage)


class Store:
    def __init__(self, config):
        state = pathlib.Path(config["state_dir"] or default_state_dir())
        state.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.state_dir = state
        self.db = sqlite3.connect(str(state / "state.sqlite"), timeout=2)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript("""
          CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS workspaces(
            id TEXT PRIMARY KEY,path TEXT UNIQUE NOT NULL,name TEXT NOT NULL,owner TEXT NOT NULL,
            state TEXT NOT NULL,hold INTEGER NOT NULL DEFAULT 0, heartbeat INTEGER NOT NULL,
            pid INTEGER, outputs TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS jobs(
            id TEXT PRIMARY KEY,path TEXT UNIQUE NOT NULL,name TEXT NOT NULL,category TEXT NOT NULL,
            state TEXT NOT NULL,size INTEGER NOT NULL,mtime_ns INTEGER NOT NULL,dev INTEGER NOT NULL,
            ino INTEGER NOT NULL,digest TEXT,archive_path TEXT,receipt TEXT,second_receipt TEXT,
            committed_at INTEGER,error TEXT,observed_at INTEGER NOT NULL,catalog_sync TEXT,
            claim_path TEXT,claim_started_at INTEGER);
          CREATE TABLE IF NOT EXISTS events(
            id TEXT PRIMARY KEY,time INTEGER NOT NULL,action TEXT NOT NULL,state TEXT NOT NULL,
            message TEXT NOT NULL,path TEXT);
          CREATE TABLE IF NOT EXISTS receipts(
            id TEXT PRIMARY KEY,job_id TEXT NOT NULL,digest TEXT NOT NULL,bytes INTEGER NOT NULL,
            target TEXT NOT NULL,time INTEGER NOT NULL);
          CREATE TABLE IF NOT EXISTS retrievals(
            id TEXT PRIMARY KEY,job_id TEXT NOT NULL,path TEXT UNIQUE NOT NULL,digest TEXT NOT NULL,
            bytes INTEGER NOT NULL,created_at INTEGER NOT NULL,expires_at INTEGER NOT NULL,state TEXT NOT NULL);
        """)
        columns = {row[1] for row in self.db.execute("PRAGMA table_info(jobs)")}
        if "catalog_sync" not in columns:
            self.db.execute("ALTER TABLE jobs ADD COLUMN catalog_sync TEXT")
        if "claim_path" not in columns:
            self.db.execute("ALTER TABLE jobs ADD COLUMN claim_path TEXT")
        if "claim_started_at" not in columns:
            self.db.execute("ALTER TABLE jobs ADD COLUMN claim_started_at INTEGER")
        self.db.commit()

    def get(self, key, default=None):
        row = self.db.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def set(self, key, value):
        self.db.execute("INSERT OR REPLACE INTO meta VALUES (?,?)", (key, dump(value)))
        self.db.commit()

    def event(self, action, state, message, path=None):
        self.db.execute("INSERT INTO events VALUES (?,?,?,?,?,?)", (uuid.uuid4().hex, now(), action, state, message, path))
        self.db.commit()

    def rows(self, table):
        return [dict(row) for row in self.db.execute("SELECT * FROM " + table)]


def fingerprint(path):
    no_symlink_components(path)
    value = os.stat(path, follow_symlinks=False)
    if not stat.S_ISREG(value.st_mode) or value.st_nlink != 1:
        raise StorageError("unsupported_source", "Only standalone regular files are eligible")
    return (value.st_size, value.st_mtime_ns, value.st_dev, value.st_ino)


def digest_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(part)
    return digest.hexdigest()


def pid_running(pid):
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def lsof_holders(paths):
    """One lsof scan of paths: False when no process holds any of them, True when one does,
    None when the scan failed or lsof is missing."""
    if not shutil.which("lsof"):
        return None
    try:
        result = subprocess.run(["lsof", "-t", *paths], capture_output=True, timeout=8, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    # macOS lsof can return 1 for an incomplete scan while still reporting
    # matching PIDs. Those matches must protect the file from retirement.
    if result.stdout.strip():
        return True
    return False if result.returncode in (0, 1) else None


def path_open(path):
    return lsof_holders([path]) is not False


def open_paths(paths):
    """The paths a process holds open. One scan covers the whole batch; only a batch that
    reports a holder is split, and a failed scan protects its whole batch."""
    if not paths:
        return set()
    held = lsof_holders(paths)
    if held is False:
        return set()
    if held is None or len(paths) == 1:
        return set(paths)
    middle = len(paths) // 2
    return open_paths(paths[:middle]) | open_paths(paths[middle:])


def tree_open(path):
    if not shutil.which("lsof"):
        return True
    try:
        command = ["lsof", "-t", "+D", path] if os.path.isdir(path) else ["lsof", "-t", path]
        result = subprocess.run(command, capture_output=True, timeout=10, check=False)
        return bool(result.stdout.strip()) or result.returncode not in (0, 1)
    except (OSError, subprocess.TimeoutExpired):
        return True


def process_cwds():
    """Resolved working directories of every process from one lsof scan; None when the scan failed."""
    if not shutil.which("lsof"):
        return []
    try:
        result = subprocess.run(["lsof", "-Fn", "-d", "cwd"], capture_output=True, timeout=8, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    cwds = []
    for line in result.stdout.splitlines():
        if line.startswith(b"n"):
            cwd = os.fsdecode(line[1:])
            if os.path.isabs(cwd):
                cwds.append(os.path.realpath(cwd))
    return cwds


def cwd_inside(cwds, path):
    if cwds is None:
        return True
    actual = os.path.realpath(path)
    return any(os.path.commonpath((cwd, actual)) == actual for cwd in cwds)


def workspace_process_active(path):
    return cwd_inside(process_cwds(), path)


class ProcessEvidence:
    """Open-process evidence for one cleanup pass.

    workspace_process_active and path_open each make lsof walk every process on the
    machine. On a loaded Mac that cost 5-6 seconds per output, and one tick spent hours
    in cleanup holding tick.lock while inbox transfers waited. Here one cwd scan serves
    every output and one batched path scan serves the next WINDOW outputs of the pass.
    An answer older than MAX_AGE seconds is scanned again, so the evidence behind a
    removal stays about as fresh as a scan per output was.
    """
    MAX_AGE = 15
    WINDOW = 200

    def __init__(self, paths):
        self.paths = list(dict.fromkeys(paths))
        self.position = {path: index for index, path in enumerate(self.paths)}
        self.cwds = None
        self.cwds_at = None
        self.held = {}

    def fresh(self, taken):
        return taken is not None and time.monotonic() - taken <= self.MAX_AGE

    def workspace_active(self, path):
        if not self.fresh(self.cwds_at):
            self.cwds_at = time.monotonic()
            self.cwds = process_cwds()
        return cwd_inside(self.cwds, path)

    def path_open(self, path):
        answer, taken = self.held.get(path, (True, None))
        if self.fresh(taken):
            return answer
        batch = [path]
        for other in self.paths[self.position.get(path, len(self.paths)) + 1:]:
            if len(batch) >= self.WINDOW:
                break
            if not self.fresh(self.held.get(other, (True, None))[1]) and os.path.lexists(other):
                batch.append(other)
        taken = time.monotonic()
        held = open_paths(batch)
        for other in batch:
            self.held[other] = (other in held, taken)
        return path in held


def git_tracked(path):
    base = path if os.path.isdir(path) else os.path.dirname(path)
    probe = subprocess.run(["git", "-C", base, "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=False)
    if probe.returncode:
        return False
    root = probe.stdout.strip()
    result = subprocess.run(["git", "-C", root, "ls-files", "-z", "--", os.path.relpath(path, root)], capture_output=True, check=False)
    if result.returncode or result.stdout:
        return True
    # A generated directory must not contain untracked user edits. Ignore only
    # the explicitly declared output tree; no generic ignored/cache heuristic.
    return False


def workspace_op(store, config, action, args):
    if action == "list":
        return {"workspaces": public_workspaces(store)}
    if action == "register":
        path = ensure_absolute(args.path)
        no_symlink_components(path)
        if not os.path.isdir(path) or not inside(path, config["workspace_roots"]):
            raise StorageError("outside_root", "Workspace must be inside a configured root")
        outputs = list(dict.fromkeys(json.loads(args.outputs) + args.generated_path))
        if not isinstance(outputs, list) or not outputs or any(not isinstance(p, str) or p in ("", ".") or p.startswith("/") or ".." in pathlib.PurePath(p).parts for p in outputs):
            raise StorageError("invalid_outputs", "Declare relative generated output paths")
        for item in outputs:
            if not inside(os.path.join(path, item), [path]):
                raise StorageError("invalid_outputs", "Output escapes workspace")
        store.db.execute("BEGIN IMMEDIATE")
        try:
            prior = store.db.execute("SELECT * FROM workspaces WHERE path=?", (path,)).fetchone()
            if prior:
                live = prior["state"] in ("open", "active") or pid_running(prior["pid"])
                if prior["owner"] != args.owner and (live or prior["hold"]):
                    raise StorageError("workspace_owned", "An active or held workspace belongs to another owner")
                pid = args.pid if args.pid is not None else prior["pid"] if live and pid_running(prior["pid"]) else None
                store.db.execute("UPDATE workspaces SET name=?,owner=?,state=?,heartbeat=?,pid=?,outputs=? WHERE id=?",
                                 (args.name or os.path.basename(path), args.owner, args.state, now(), pid, dump(outputs), prior["id"]))
                ident = prior["id"]
            else:
                ident = uuid.uuid4().hex
                store.db.execute("INSERT INTO workspaces VALUES (?,?,?,?,?,?,?,?,?)",
                                 (ident, path, args.name or os.path.basename(path), args.owner, args.state, 0, now(), args.pid, dump(outputs)))
            store.db.commit()
        except Exception:
            store.db.rollback()
            raise
        store.event("workspace_register", "reopened" if prior else "open",
                    "Registered workspace reopened" if prior else "Registered workspace", path)
        store.set("cleanup_preview", None)
        return {"id": ident}
    row = store.db.execute("SELECT * FROM workspaces WHERE id=?", (args.id,)).fetchone()
    if not row:
        raise StorageError("not_found", "Workspace not found")
    if action == "heartbeat":
        store.db.execute("UPDATE workspaces SET heartbeat=?,state='active',pid=COALESCE(?,pid) WHERE id=?", (now(), args.pid, args.id))
    elif action == "finish":
        store.db.execute("UPDATE workspaces SET state=?,pid=NULL WHERE id=?", (args.state, args.id))
    elif action == "close":
        if not args.accepted:
            raise StorageError("not_accepted", "Close requires --accepted")
        if pid_running(row["pid"]):
            raise StorageError("active_process", "Registered process is still running")
        store.db.execute("UPDATE workspaces SET state='closed',pid=NULL WHERE id=?", (args.id,))
    elif action in ("pin", "unpin"):
        store.db.execute("UPDATE workspaces SET hold=? WHERE id=?", (action == "pin", args.id))
    store.db.commit()
    store.event("workspace_" + action, action, "Workspace updated", row["path"])
    store.set("cleanup_preview", None)
    if action in ("close", "unpin"):
        store.set("cleanup_pending", True)
    return {"workspace": next(item for item in public_workspaces(store) if item["id"] == args.id)}


def public_workspaces(store):
    return [{key: row[key] for key in ("id", "path", "name", "owner", "state", "hold")} for row in store.rows("workspaces")]


def cleanup_candidate(row, relative, config, measure=True, evidence=None):
    path = os.path.join(row["path"], relative)
    evidence = evidence or ProcessEvidence([path])
    reason = None
    if row["state"] != "closed" or row["hold"] or pid_running(row["pid"]):
        reason = "workspace_active_or_held"
    elif not inside(path, [row["path"]]) or not inside(row["path"], config["workspace_roots"]):
        reason = "outside_root"
    elif not os.path.lexists(path):
        reason = "missing"
    else:
        try:
            no_symlink_components(path)
            if git_tracked(path):
                reason = "tracked"
            elif evidence.workspace_active(row["path"]) or evidence.path_open(path):
                reason = "open_process"
            elif os.path.isdir(path):
                if not shutil.rmtree.avoids_symlink_attacks:
                    reason = "unsafe_platform"
                else:
                    for base, dirs, files in os.walk(path, followlinks=False):
                        if ".git" in dirs + files or ".skillry-keep" in dirs + files:
                            reason = "meaningful_state"
                            break
        except StorageError as exc:
            reason = exc.code
    return {"workspace_id": row["id"], "path": path, "eligible": reason is None,
            "reason": reason, "bytes": tree_bytes(path) if reason is None and measure else 0}


def cleanup_evidence(store):
    return ProcessEvidence(os.path.join(row["path"], relative) for row in store.rows("workspaces")
                           if row["state"] == "closed" and not row["hold"] for relative in json.loads(row["outputs"]))


def cleanup_candidates(store, config):
    evidence = cleanup_evidence(store)
    return [cleanup_candidate(row, relative, config, evidence=evidence) for row in store.rows("workspaces")
            for relative in json.loads(row["outputs"])]


def tree_bytes(path):
    # Another cleanup (the disk guard runs one too) may take entries while they are counted.
    try:
        if os.path.isfile(path):
            return os.lstat(path).st_size
    except FileNotFoundError:
        return 0
    total = 0
    for base, dirs, files in os.walk(path, followlinks=False):
        for name in dirs + files:
            if name in dirs and not os.path.islink(os.path.join(base, name)):
                continue
            try:
                total += os.stat(os.path.join(base, name), follow_symlinks=False).st_size
            except FileNotFoundError:
                continue
    return total


def remove_generated(path):
    """Remove one checked candidate. FileNotFoundError means it was already gone;
    entries of a tree that vanish during the removal are not an error."""
    def vanished(function, failed, error):
        error = error[1] if isinstance(error, tuple) else error
        if not isinstance(error, FileNotFoundError) or failed == path:
            raise error
    if os.path.isdir(path):
        shutil.rmtree(path, **({"onexc": vanished} if sys.version_info >= (3, 12) else {"onerror": vanished}))
    else:
        os.unlink(path)


def free_bytes(path):
    try:
        return shutil.disk_usage(path).free
    except OSError:
        return None


def record_removed(store, logical_bytes, before, after):
    store.set("logical_bytes_removed", store.get("logical_bytes_removed", 0) + logical_bytes)
    if before is not None and after is not None:
        delta = after - before
        store.set("observed_free_delta_bytes", store.get("observed_free_delta_bytes", 0) + delta)
        store.set("observed_gain_bytes", store.get("observed_gain_bytes", 0) + max(0, delta))
        store.set("last_space_measurement", now())


# A tick holds tick.lock for its whole run. Cleanup inside a tick stops after this many
# seconds and goes on in the next tick, so inbox transfers never wait for a whole pass.
CLEANUP_TICK_SECONDS = 300


def cleanup_op(store, config, apply, deadline=None):
    if apply and store.get("paused", False):
        raise StorageError("paused", "Worker is paused")
    if apply and not config["automatic_cleanup"]:
        raise StorageError("not_enabled", "Automatic cleanup is disabled")
    if not apply:
        candidates = cleanup_candidates(store, config)
        candidate_bytes = sum(item["bytes"] for item in candidates if item["eligible"])
        store.set("cleanup_preview", {"candidate_bytes": candidate_bytes, "at": now()})
        return {"candidates": candidates, "removed": [], "candidate_bytes": candidate_bytes}
    # Each output is checked immediately before its removal. The row is read again because
    # a workspace can be reopened while the pass runs.
    evidence = cleanup_evidence(store)
    store.set("cleanup_preview", None)
    candidates, removed, stopped = [], [], False
    for ident, relative in [(row["id"], relative) for row in store.rows("workspaces") for relative in json.loads(row["outputs"])]:
        if store.get("paused", False):
            break
        if deadline is not None and time.monotonic() >= deadline:
            stopped = True
            break
        row = store.db.execute("SELECT * FROM workspaces WHERE id=?", (ident,)).fetchone()
        if not row:
            continue
        item = cleanup_candidate(row, relative, config, measure=False, evidence=evidence)
        candidates.append(item)
        if not item["eligible"]:
            continue
        item["bytes"] = tree_bytes(item["path"])
        if store.get("paused", False):
            break
        before = free_bytes(os.path.dirname(item["path"]))
        try:
            remove_generated(item["path"])
        except FileNotFoundError:
            # Taken by another cleanup between the check and the removal.
            continue
        record_removed(store, item["bytes"], before, free_bytes(os.path.dirname(item["path"])))
        removed.append(item["path"])
        store.event("cleanup", "removed", "Generated output removed", item["path"])
    if stopped:
        store.set("cleanup_pending", True)
    elif not store.get("paused", False):
        store.set("cleanup_preview", {"candidate_bytes": 0, "at": now()})
        store.set("cleanup_pending", False)
        store.set("cleanup_retry_at", now() + 3600)
    return {"candidates": candidates, "removed": removed,
            "candidate_bytes": sum(item["bytes"] for item in candidates if item["eligible"])}


PARTIAL = (".crdownload", ".part", ".download", ".tmp")
REVIEW_EXT = (".db", ".sqlite", ".sqlite3", ".app", ".dmg", ".pkg", ".zip")


def reconcile_claims(store):
    for row in store.db.execute("SELECT * FROM jobs WHERE state='evicting' AND claim_path IS NOT NULL").fetchall():
        source = row["path"]
        claim = row["claim_path"]
        source_exists = os.path.lexists(source)
        claim_exists = os.path.lexists(claim)
        if claim_exists and source_exists:
            job_update(store, row["id"], state="review_claim", error="source_and_claim_exist")
            store.event("inbox_recovery", "review_claim", "Source and eviction claim both exist", source)
            continue
        if claim_exists:
            try:
                candidate = fingerprint(claim)
                if candidate != (row["size"], row["mtime_ns"], row["dev"], row["ino"]) or digest_file(claim) != row["digest"]:
                    raise StorageError("claim_changed", "Eviction claim no longer matches source")
                os.link(claim, source, follow_symlinks=False)
                os.unlink(claim)
                job_update(store, row["id"], state="grace", claim_path=None, claim_started_at=None, error=None)
                store.event("inbox_recovery", "restored", "Verified source restored after interrupted eviction", source)
            except (OSError, StorageError):
                job_update(store, row["id"], state="review_claim", error="claim_changed")
            continue
        if source_exists:
            try:
                require_identity(row)
                job_update(store, row["id"], state="grace", claim_path=None, claim_started_at=None, error=None)
            except StorageError:
                job_update(store, row["id"], state="review_claim", error="source_changed")
            continue
        # Crash after unlink and before the final DB commit. The old source is
        # gone; do not infer APFS gain or count its logical bytes a second time.
        job_update(store, row["id"], state="evicted", claim_path=None, claim_started_at=None, error="space_gain_unmeasured")
        store.event("inbox_recovery", "evicted", "Completed eviction recovered; space gain unmeasured", source)


def intake_scan(store, config):
    intake = config["intake_dir"]
    if not intake or not os.path.isdir(intake) or os.path.islink(intake):
        return
    for entry in os.scandir(intake):
        if entry.is_symlink():
            continue
        path = entry.path
        if re.search(r"\.skillry-evict-[0-9a-f]{32}$", entry.name):
            continue
        if entry.is_dir(follow_symlinks=False):
            if not store.db.execute("SELECT 1 FROM jobs WHERE path=?", (path,)).fetchone():
                value = entry.stat(follow_symlinks=False)
                store.db.execute("INSERT INTO jobs(id,path,name,category,state,size,mtime_ns,dev,ino,digest,archive_path,receipt,second_receipt,committed_at,error,observed_at,catalog_sync) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                 (uuid.uuid4().hex, path, entry.name, "review", "review", 0, value.st_mtime_ns,
                                  value.st_dev, value.st_ino, None, None, None, None, None, None, now(), None))
                store.db.commit()
            continue
        if not entry.is_file(follow_symlinks=False):
            continue
        try:
            size, modified, dev, ino = fingerprint(path)
        except (OSError, StorageError):
            continue
        row = store.db.execute("SELECT * FROM jobs WHERE path=?", (path,)).fetchone()
        if row:
            if row["state"] in ("evicting", "review_claim"):
                continue
            # A path replaced with another file cannot inherit the old proof.
            if (size, modified, dev, ino) != (row["size"], row["mtime_ns"], row["dev"], row["ino"]):
                fresh_id = uuid.uuid4().hex
                store.db.execute("UPDATE jobs SET id=?,size=?,mtime_ns=?,dev=?,ino=?,digest=NULL,archive_path=NULL,receipt=NULL,second_receipt=NULL,committed_at=NULL,catalog_sync=NULL,state='settling',observed_at=?,error=NULL WHERE id=?",
                                 (fresh_id, size, modified, dev, ino, now(), row["id"]))
                store.db.commit()
            continue
        category = "review" if path.lower().endswith(REVIEW_EXT) else "ordinary"
        state = "review" if category == "review" else "settling"
        if path.lower().endswith(PARTIAL):
            state, category = "waiting_download", "review"
        store.db.execute("INSERT INTO jobs(id,path,name,category,state,size,mtime_ns,dev,ino,digest,archive_path,receipt,second_receipt,committed_at,error,observed_at,catalog_sync) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                         (uuid.uuid4().hex, path, entry.name, category, state, size, modified, dev, ino,
                          None, None, None, None, None, None, now(), None))
        store.db.commit()
    for row in store.db.execute("SELECT id,path,state FROM jobs WHERE state NOT IN ('evicted','evicting','review_claim')").fetchall():
        if not os.path.lexists(row["path"]) and row["state"] != "missing":
            job_update(store, row["id"], state="missing", error="source_missing")


def public_jobs(store):
    result = []
    for row in store.rows("jobs"):
        result.append({"id": row["id"], "name": row["name"], "state": row["state"], "bytes": row["size"],
                       "category": row["category"], "error": row["error"], "local_path": row["path"],
                       "archive_path": row["archive_path"],
                       "catalog_sync": json.loads(row["catalog_sync"]) if row["catalog_sync"] else None,
                       "suggestion": store.get("storage_suggestion_" + row["id"])})
    return result


def require_identity(row):
    try:
        current = fingerprint(row["path"])
    except (OSError, StorageError):
        raise StorageError("source_changed", "Original source identity is no longer present")
    if current != (row["size"], row["mtime_ns"], row["dev"], row["ino"]):
        raise StorageError("source_changed", "Original source changed")


def eligible_intake_type(path):
    if path.lower().endswith(PARTIAL + (".db", ".sqlite", ".sqlite3", ".db-wal", ".db-shm")):
        raise StorageError("unsupported_source", "Partial downloads and databases cannot enter automatic archive")
    with open(path, "rb") as stream:
        if stream.read(16).startswith(b"SQLite format 3"):
            raise StorageError("unsupported_source", "Live database files cannot enter automatic archive")


def job_update(store, row_id, **fields):
    allowed = {"state", "digest", "archive_path", "receipt", "second_receipt", "committed_at", "error", "category", "catalog_sync", "claim_path", "claim_started_at"}
    if set(fields) - allowed:
        raise ValueError("Unexpected job field")
    assignments = ",".join(key + "=?" for key in fields)
    store.db.execute("UPDATE jobs SET " + assignments + " WHERE id=?", (*fields.values(), row_id))
    store.db.commit()


def process_job(store, config, row):
    from .transfer import transfer, catalog_reconcile, reconcile_remote_catalog
    origin = {"job_id": row["id"], "original_name": row["name"], "source_host": socket.gethostname(),
              "tag": config.get("archive_tag"), "category": row["category"], "rights": "unknown", "received_at": now()}
    if row["state"] in ("evicted", "review", "waiting_download", "missing", "review_claim", "evicting"):
        return
    if store.get("paused", False):
        return
    if row["category"] not in ("ordinary", "critical"):
        return
    require_identity(row)
    eligible_intake_type(row["path"])
    if path_open(row["path"]):
        job_update(store, row["id"], state="in_use")
        return
    if store.get("paused", False):
        return
    if now() - row["observed_at"] < config["settle_seconds"] or now() - row["mtime_ns"] // 1000000000 < config["settle_seconds"]:
        job_update(store, row["id"], state="settling")
        return
    newly_archived = False
    if not row["receipt"]:
        if not config["automatic_archive"]:
            job_update(store, row["id"], state="pending")
            return
        digest = digest_file(row["path"])
        require_identity(row)
        job_update(store, row["id"], state="transferring", digest=digest)
        receiver_critical = row["category"] == "critical" and config["archive"]["kind"] == "ssh" and config["second_archive"]["kind"] == "none"
        receipt = transfer(row["path"], config["archive"], digest, row["size"], critical=receiver_critical, origin=origin)
        require_identity(row)
        # Receipt contains identity, target and digest; returned receiver proof is
        # persisted before any source eviction is considered.
        record = {"sha256": digest, "bytes": row["size"], "path": receipt["path"], "kind": config["archive"]["kind"], "root": config["archive"]["root"]}
        catalog_sync = receipt.get("catalog_sync")
        job_update(store, row["id"], state="archived", receipt=dump(record), archive_path=receipt["path"],
                   committed_at=now(), catalog_sync=dump(catalog_sync) if catalog_sync else None, error=None)
        if config["archive"]["kind"] == "local" and config.get("catalog_bridge") and not store.get("paused", False):
            catalog_sync = catalog_reconcile(config, config["archive"]["root"], digest, row["size"])
            job_update(store, row["id"], catalog_sync=dump(catalog_sync))
        newly_archived = True
        if row["category"] == "critical" and isinstance(receipt.get("second_receipt"), dict):
            job_update(store, row["id"], second_receipt=dump(receipt["second_receipt"]))
            store.db.execute("INSERT OR REPLACE INTO receipts VALUES (?,?,?,?,?,?)",
                             (row["id"] + ":second", row["id"], digest, row["size"], receipt["second_receipt"]["path"], now()))
            store.db.commit()
        store.db.execute("INSERT OR REPLACE INTO receipts VALUES (?,?,?,?,?,?)", (row["id"] + ":primary", row["id"], digest, row["size"], receipt["path"], now()))
        store.db.commit()
        store.event("archive", "archived", "Verified archive receipt", row["path"])
        if isinstance(catalog_sync, dict) and catalog_sync.get("state") == "linked":
            store.event("catalog_link", "linked", "Catalog snapshot " + str(catalog_sync.get("snapshot_id")), row["path"])
        row = store.db.execute("SELECT * FROM jobs WHERE id=?", (row["id"],)).fetchone()
    catalog_required = bool(config["archive"].get("catalog_required") or config.get("catalog_bridge"))
    if catalog_required:
        catalog_sync = json.loads(row["catalog_sync"]) if row["catalog_sync"] else None
        if not catalog_sync or catalog_sync.get("state") != "linked":
            if newly_archived:
                job_update(store, row["id"], state="catalog_pending", error=(catalog_sync or {}).get("error", "catalog_gap"))
                return
            if config["archive"]["kind"] == "ssh":
                try:
                    catalog_sync = reconcile_remote_catalog(config["archive"], row["digest"], row["size"])
                except StorageError as exc:
                    catalog_sync = {"state": "gap", "error": exc.code, "last_attempt_at": now()}
            elif config["archive"]["kind"] == "local":
                catalog_sync = catalog_reconcile(config, config["archive"]["root"], row["digest"], row["size"])
            if not isinstance(catalog_sync, dict):
                catalog_sync = {"state": "gap", "error": "invalid_catalog_response", "last_attempt_at": now()}
            job_update(store, row["id"], catalog_sync=dump(catalog_sync),
                       state="archived" if catalog_sync.get("state") == "linked" else "catalog_pending",
                       error=None if catalog_sync.get("state") == "linked" else catalog_sync.get("error", "catalog_gap"))
            if catalog_sync.get("state") == "linked":
                store.event("catalog_link", "linked", "Catalog snapshot " + str(catalog_sync.get("snapshot_id")), row["path"])
            row = store.db.execute("SELECT * FROM jobs WHERE id=?", (row["id"],)).fetchone()
        if catalog_sync.get("state") != "linked":
            return
    if store.get("paused", False):
        return
    if row["category"] == "critical" and not row["second_receipt"]:
        if config["second_archive"]["kind"] == "none":
            job_update(store, row["id"], state="second_copy_required")
            return
        if config["archive"]["kind"] == "local" and config["second_archive"]["kind"] == "local":
            try:
                if os.stat(config["archive"]["root"]).st_dev == os.stat(config["second_archive"]["root"]).st_dev:
                    raise StorageError("second_not_independent", "Critical second copy is on the same device")
            except FileNotFoundError:
                raise StorageError("archive_offline", "Critical second archive is unavailable")
        second = transfer(row["path"], config["second_archive"], row["digest"], row["size"], origin=origin)
        require_identity(row)
        record = {"sha256": row["digest"], "bytes": row["size"], "path": second["path"], "kind": config["second_archive"]["kind"], "root": config["second_archive"]["root"]}
        job_update(store, row["id"], second_receipt=dump(record), state="archived")
        store.db.execute("INSERT OR REPLACE INTO receipts VALUES (?,?,?,?,?,?)", (row["id"] + ":second", row["id"], row["digest"], row["size"], second["path"], now()))
        store.db.commit()
        row = store.db.execute("SELECT * FROM jobs WHERE id=?", (row["id"],)).fetchone()
    if row["committed_at"] is None or now() - row["committed_at"] < config["local_grace_seconds"]:
        job_update(store, row["id"], state="grace")
        return
    # Recheck source and archive evidence immediately before unlink.
    require_identity(row)
    if digest_file(row["path"]) != row["digest"]:
        raise StorageError("source_changed", "Source digest changed before eviction")
    if path_open(row["path"]):
        job_update(store, row["id"], state="in_use")
        return
    from .transfer import verify_remote
    for key, archive in (("receipt", config["archive"]), ("second_receipt", config["second_archive"])):
        if key == "second_receipt" and row["category"] != "critical":
            continue
        proof = json.loads(row[key]) if row[key] else None
        remote_second = key == "second_receipt" and archive["kind"] == "none" and config["archive"]["kind"] == "ssh"
        if not proof or proof["sha256"] != row["digest"] or proof["bytes"] != row["size"] or (not remote_second and (proof["kind"] != archive["kind"] or proof["root"] != archive.get("root"))):
            raise StorageError("invalid_receipt", "Archive proof is missing or target changed")
        if remote_second:
            continue  # primary remote verification below includes second proof
        expected_second = json.loads(row["second_receipt"]) if row["category"] == "critical" and archive["kind"] == "ssh" and config["second_archive"]["kind"] == "none" else None
        if verify_remote(archive, row["digest"], row["size"], critical=expected_second is not None,
                         second_expected=expected_second, require_catalog=catalog_required and key == "receipt") != proof["path"]:
            raise StorageError("invalid_receipt", "Archive proof no longer verifies")
    if store.get("paused", False):
        return
    # Rename first, then verify the moved inode. A concurrent path replacement
    # can be moved to quarantine but cannot be deleted under an old receipt.
    require_identity(row)
    quarantine = row["path"] + ".skillry-evict-" + row["id"]
    if os.path.lexists(quarantine):
        raise StorageError("quarantine_exists", "Previous source quarantine needs review")
    job_update(store, row["id"], state="evicting", claim_path=quarantine, claim_started_at=now())
    os.rename(row["path"], quarantine)
    try:
        moved = fingerprint(quarantine)
        if moved != (row["size"], row["mtime_ns"], row["dev"], row["ino"]) or digest_file(quarantine) != row["digest"] or path_open(quarantine):
            raise StorageError("source_changed", "Source changed during eviction")
        if store.get("paused", False):
            raise StorageError("paused", "Worker paused before source eviction")
    except (StorageError, OSError):
        if not os.path.lexists(row["path"]):
            try:
                os.link(quarantine, row["path"], follow_symlinks=False)
                os.unlink(quarantine)
            except FileExistsError:
                job_update(store, row["id"], state="review_claim", error="source_and_claim_exist")
        raise
    before = free_bytes(os.path.dirname(row["path"]))
    os.unlink(quarantine)
    record_removed(store, row["size"], before, free_bytes(os.path.dirname(row["path"])))
    job_update(store, row["id"], state="evicted", claim_path=None, claim_started_at=None)
    store.event("inbox_evict", "evicted", "Verified source bytes removed", row["path"])


def inbox_op(store, config, action, args):
    intake_scan(store, config)
    if action == "list":
        return {"queue": public_jobs(store)}
    row = store.db.execute("SELECT * FROM jobs WHERE id=?", (args.id,)).fetchone()
    if not row:
        raise StorageError("not_found", "Inbox item not found")
    if action == "retrieve":
        return {"retrieval": retrieve_job(store, config, row)}
    if action == "retry":
        if row["state"] == "review_claim":
            if row["claim_path"] and not os.path.lexists(row["claim_path"]):
                require_identity(row)
                job_update(store, row["id"], state="grace", claim_path=None, claim_started_at=None, error=None)
                return {"queue": public_jobs(store)}
            raise StorageError("review_claim", "Conflicting eviction claim requires manual review")
        if row["state"] != "evicted":
            job_update(store, row["id"], state="pending", error=None)
        return {"queue": public_jobs(store)}
    category = args.category
    if category not in ("ordinary", "critical", "downloadable", "review"):
        raise StorageError("invalid_category", "Invalid closed-set category")
    if category in ("ordinary", "critical"):
        require_identity(row)
        eligible_intake_type(row["path"])
    from .classification import record_owner_class
    record_owner_class(store, row, category)
    job_update(store, row["id"], category=category, state="pending" if category in ("ordinary", "critical") else "review", error=None)
    store.event("inbox_classify", category, "Inbox class set", row["path"])
    return {"queue": public_jobs(store)}


def retrieval_cache_root(store):
    root = store.state_dir / "retrieved"
    root.mkdir(mode=0o700, exist_ok=True)
    no_symlink_components(str(root))
    return root


def cleanup_retrieval_cache(store, config):
    removed = 0
    root = retrieval_cache_root(store)
    for item in store.db.execute("SELECT id,path FROM retrievals").fetchall():
        if not os.path.lexists(item["path"]):
            store.db.execute("DELETE FROM retrievals WHERE id=?", (item["id"],))
    for item in store.db.execute("SELECT * FROM retrievals WHERE expires_at<=? AND state IN ('verified','staging') ORDER BY expires_at LIMIT 32", (now(),)).fetchall():
        path = item["path"]
        if not inside(path, [str(root)]):
            store.db.execute("UPDATE retrievals SET state='review' WHERE id=?", (item["id"],))
            continue
        if not os.path.lexists(path):
            store.db.execute("DELETE FROM retrievals WHERE id=?", (item["id"],))
            continue
        if item["state"] == "staging":
            try:
                no_symlink_components(path)
                if os.path.isfile(path) and not path_open(path):
                    os.unlink(path)
                    store.db.execute("DELETE FROM retrievals WHERE id=?", (item["id"],))
                    removed += 1
            except (OSError, StorageError):
                store.db.execute("UPDATE retrievals SET state='review' WHERE id=?", (item["id"],))
            continue
        try:
            current = fingerprint(path)
            if current[0] != item["bytes"] or digest_file(path) != item["digest"]:
                store.db.execute("UPDATE retrievals SET state='edited' WHERE id=?", (item["id"],))
                continue
        except (OSError, StorageError):
            store.db.execute("UPDATE retrievals SET state='review' WHERE id=?", (item["id"],))
            continue
        if path_open(path):
            continue
        os.unlink(path)
        store.db.execute("DELETE FROM retrievals WHERE id=?", (item["id"],))
        removed += 1
    store.db.commit()
    return removed


def retrieve_job(store, config, row):
    from .transfer import read_archive
    if not row["receipt"] or not row["digest"]:
        raise StorageError("not_archived", "Inbox item has no verified archive receipt")
    receipt = json.loads(row["receipt"])
    archive = config["archive"]
    if receipt.get("sha256") != row["digest"] or receipt.get("bytes") != row["size"] or receipt.get("kind") != archive["kind"] or receipt.get("root") != archive.get("root"):
        raise StorageError("invalid_receipt", "Archive identity no longer matches configured target")
    cleanup_retrieval_cache(store, config)
    cache_root = retrieval_cache_root(store)
    if not re.fullmatch(r"[0-9a-f]{32}", row["id"]):
        raise StorageError("invalid_job", "Invalid inbox job identity")
    job_dir = cache_root / row["id"]
    job_dir.mkdir(mode=0o700, exist_ok=True)
    no_symlink_components(str(job_dir))
    for item in store.db.execute("SELECT * FROM retrievals WHERE job_id=? ORDER BY created_at DESC", (row["id"],)).fetchall():
        if item["state"] == "staging" or not inside(item["path"], [str(job_dir)]):
            continue
        try:
            if fingerprint(item["path"])[0] == item["bytes"] and digest_file(item["path"]) == item["digest"] == row["digest"]:
                expires = now() + config["local_grace_seconds"]
                store.db.execute("UPDATE retrievals SET expires_at=?,state='verified' WHERE id=?", (expires, item["id"]))
                store.db.commit()
                return {"id": item["id"], "name": row["name"], "path": item["path"], "bytes": item["bytes"],
                        "sha256": item["digest"], "cached": True, "expires_at": expires}
        except (OSError, StorageError):
            pass
        store.db.execute("UPDATE retrievals SET state='edited' WHERE id=?", (item["id"],))
    store.db.commit()
    items = [dict(item) for item in store.db.execute("SELECT * FROM retrievals")]
    used = sum(os.path.getsize(item["path"]) for item in items if os.path.isfile(item["path"]) and not os.path.islink(item["path"]))
    if row["size"] > config["retrieval_cache_max_bytes"] or used + row["size"] > config["retrieval_cache_max_bytes"] or len(items) >= config["retrieval_cache_max_items"]:
        raise StorageError("cache_full", "Verified retrieval cache is full; edited or open entries were preserved")
    if shutil.disk_usage(str(cache_root)).free < row["size"]:
        raise StorageError("disk_full", "Local disk has insufficient space for this retrieval")
    filename = row["name"]
    if filename in ("", ".", "..") or "/" in filename or "\\" in filename:
        raise StorageError("invalid_name", "Archived original name cannot be used as a cache filename")
    target = job_dir / filename
    if target.exists() or target.is_symlink():
        try:
            if fingerprint(str(target))[0] == row["size"] and digest_file(str(target)) == row["digest"]:
                ident = uuid.uuid4().hex
                expires = now() + config["local_grace_seconds"]
                store.db.execute("INSERT INTO retrievals VALUES (?,?,?,?,?,?,?,?)", (ident, row["id"], str(target), row["digest"], row["size"], now(), expires, "verified"))
                store.db.commit()
                return {"id": ident, "name": filename, "path": str(target), "bytes": row["size"],
                        "sha256": row["digest"], "cached": True, "expires_at": expires}
        except (OSError, StorageError):
            pass
        target = job_dir / ("verified-" + uuid.uuid4().hex[:8] + "-" + filename)
    job_fd = os.open(str(job_dir), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    stage_name = ".retrieve-" + uuid.uuid4().hex
    try:
        fd = os.open(stage_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=job_fd)
    except Exception:
        os.close(job_fd)
        raise
    stage = str(job_dir / stage_name)
    ident = uuid.uuid4().hex
    expires = now() + config["local_grace_seconds"]
    try:
        store.db.execute("INSERT INTO retrievals VALUES (?,?,?,?,?,?,?,?)", (ident, row["id"], stage, row["digest"], row["size"], now(), expires, "staging"))
        store.db.commit()
        with os.fdopen(fd, "wb") as output:
            read_archive(archive, row["digest"], row["size"], output)
            output.flush()
            os.fsync(output.fileno())
        if os.path.lexists(target):
            raise StorageError("cache_collision", "Retrieval target appeared during transfer")
        os.link(stage_name, target.name, src_dir_fd=job_fd, dst_dir_fd=job_fd, follow_symlinks=False)
        os.fsync(job_fd)
        store.db.execute("UPDATE retrievals SET path=?,state='verified',expires_at=? WHERE id=?", (str(target), expires, ident))
        store.db.commit()
        store.event("inbox_retrieve", "verified", "Archived file retrieved to local cache", str(target))
        return {"id": ident, "name": filename, "path": str(target), "bytes": row["size"],
                "sha256": row["digest"], "cached": False, "expires_at": expires}
    finally:
        try:
            os.close(fd)
        except OSError:
            pass
        try:
            os.unlink(stage_name, dir_fd=job_fd)
        except FileNotFoundError:
            pass
        os.close(job_fd)
        store.db.execute("DELETE FROM retrievals WHERE id=? AND state='staging'", (ident,))
        store.db.commit()


def tick(store, config):
    if store.get("paused", False):
        store.set("worker_state", "paused")
        return {"worker": "paused", "processed": 0}
    # An OS lock stays held for the entire tick, including remote transfer.
    lock_fd = os.open(str(store.state_dir / "tick.lock"), os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(lock_fd)
        return {"worker": "busy", "processed": 0}
    if store.get("paused", False):
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)
        return {"worker": "paused", "processed": 0}
    store.set("worker_state", "running")
    processed = 0
    errors = []
    classification = None
    try:
        # Claim recovery moves files, so it runs only here under tick.lock. Run from status or
        # inbox it took a live eviction's claim for an interrupted one and moved the file back.
        reconcile_claims(store)
        intake_scan(store, config)
        if not store.get("paused", False):
            from .classification import classify_pending, owner_classified, KNOWN_DURABLE
            try:
                classification = classify_pending(config, store, jev_classify, job_update)
                hold_ids = set(classification.get("hold_ids", []))
            except Exception:
                hold_ids = {row["id"] for row in store.db.execute("SELECT * FROM jobs WHERE category='ordinary'")
                            if pathlib.Path(row["path"]).suffix.casefold() not in KNOWN_DURABLE
                            and not owner_classified(store, row)}
                classification = {"provider_status": "unavailable", "hold_ids": sorted(hold_ids), "error": "classification_failed"}
        else:
            hold_ids = set()
        if not store.get("paused", False):
            cleanup_retrieval_cache(store, config)
        if config["automatic_archive"]:
            for row in store.db.execute("SELECT * FROM jobs WHERE state!='evicted' ORDER BY observed_at,id").fetchall():
                if store.get("paused", False):
                    break
                if row["id"] in hold_ids:
                    continue
                try:
                    process_job(store, config, row)
                    processed += 1
                except StorageError as exc:
                    job_update(store, row["id"], state="error", error=exc.code)
                    errors.append({"id": row["id"], "code": exc.code})
        retry_at = store.get("cleanup_retry_at")
        if config["automatic_cleanup"] and not store.get("paused", False) and (store.get("cleanup_pending", False) or retry_at is None or retry_at <= now()):
            cleanup_op(store, config, True, deadline=time.monotonic() + CLEANUP_TICK_SECONDS)
    finally:
        store.set("worker_state", "idle")
        store.set("last_run", now())
        store.set("last_error", errors[-1]["code"] if errors else None)
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)
    return {"worker": "idle", "processed": processed, "errors": errors, "classification": classification}


def tools_status(config):
    commands = {"dust": "dust", "czkawka": "czkawka_cli", "mole": "mole", "rclone": "rclone"}
    result = []
    for key, default in commands.items():
        executable = config.get("tools", {}).get(key, default)
        path = shutil.which(executable)
        version = None
        reason = None
        if path:
            try:
                completed = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=5, check=False)
                version = (completed.stdout or completed.stderr).splitlines()[0][:120] if (completed.stdout or completed.stderr) else None
            except (OSError, subprocess.TimeoutExpired):
                reason = "version_unavailable"
        else:
            reason = "not_installed"
        result.append({"id": key, "available": bool(path), "path": path, "version": version, "reason": reason,
                       "preview_command": [path, "--version"] if path else None})
    return result


def tool_preview(config, tool_id, root, run=False):
    root = ensure_absolute(root)
    if not os.path.isdir(root) or os.path.islink(root):
        raise StorageError("invalid_root", "Preview root is unavailable")
    entry = next((item for item in tools_status(config) if item["id"] == tool_id), None)
    if not entry:
        raise StorageError("unknown_tool", "Unknown adapter")
    if not entry["available"]:
        return {"id": tool_id, "available": False, "reason": entry["reason"], "command": None}
    # Typed, read-only suggestions. The engine never executes a tool's own
    # broad purge/sync command; applying policy remains inside this engine.
    if tool_id == "rclone":
        archive = config["archive"] if config["archive"]["kind"] == "rclone" else config["second_archive"]
        if archive["kind"] != "rclone":
            return {"id": tool_id, "available": False, "reason": "no_rclone_archive", "command": None}
        options = ["check", "--download", root, archive["root"]]
    else:
        options = {
            "dust": ["-d", "2", "--no-colors", "--limit-filesystem", root],
            "czkawka": ["dup", "-d", root, "--search-method", "HASH", "--delete-method", "NONE", "--dry-run"],
            "mole": ["analyze", root],
        }[tool_id]
    command = [entry["path"], *options]
    result = {"id": tool_id, "available": True, "command": command, "mode": "read_only_preview",
              "note": "Candidate output does not authorize deletion", "executed": False}
    if run:
        try:
            completed = subprocess.run(command, capture_output=True, text=True, timeout=60, check=False)
            result.update(executed=True, exit_code=completed.returncode, output=(completed.stdout or completed.stderr)[:20000])
        except (OSError, subprocess.TimeoutExpired) as exc:
            result.update(executed=True, error=str(exc))
    return result


def jev_status(config, store):
    settings = config["jev"]
    helper = settings.get("helper_path")
    enabled = bool(settings.get("enabled"))
    state = "disabled" if not enabled else "unavailable"
    service = settings.get("service")
    account = settings.get("account")
    if enabled and helper and os.path.isfile(helper):
        try:
            result = subprocess.run([helper, "status", "--client", "storage"], capture_output=True, text=True, timeout=5, check=False)
            data = json.loads(result.stdout)
            if result.returncode == 0:
                state = "ready" if data.get("enabled", True) else "unavailable"
                service = service or data.get("service")
                account = account or data.get("account")
        except (OSError, subprocess.TimeoutExpired, ValueError):
            pass
    return {"state": state,
            "enabled": enabled, "helper_path": helper, "secret_kind": settings.get("secret_kind"),
            "service": service, "account": account,
            "last_status": store.get("jev_last_status"), "usage": store.get("storage_jev_last_usage")}


def jev_classify(config, store, data_class, payload):
    settings = config["jev"]
    if data_class not in ("public", "synthetic"):
        raise StorageError("private_data", "Jev accepts only public or synthetic abstractions")
    records = payload.get("records") if isinstance(payload, dict) else None
    if not isinstance(records, list) or not 1 <= len(records) <= 16:
        raise StorageError("invalid_records", "Supply 1-16 abstract records")
    for record in records:
        if not isinstance(record, dict) or set(record) != {"id", "text"} or not isinstance(record["id"], str) or not isinstance(record["text"], str) or len(record["text"]) > 300:
            raise StorageError("invalid_records", "Records require short id/text fields")
        if "/" in record["text"] or "\\" in record["text"] or "@" in record["text"]:
            raise StorageError("private_data", "Paths and addresses are excluded from Jev input")
    key = hashlib.sha256(dump([data_class, records, settings.get("model"), settings.get("helper_path")]).encode()).hexdigest()
    cached = store.get("jev_cache_" + key)
    if cached:
        if isinstance(cached, dict) and "result" in cached:
            return {"status": "cached", "result": cached["result"],
                    "usage": cached.get("usage"), "api_calls": cached.get("api_calls")}
        return {"status": "cached", "result": cached, "usage": None, "api_calls": None}
    helper = settings.get("helper_path")
    if not settings.get("enabled") or not helper or not os.path.isfile(helper):
        store.set("jev_last_status", "unavailable")
        return {"status": "unavailable", "result": None}
    request = {"operation": "classify", "task": "Classify abstract technical artifacts for storage review",
               "data_class": data_class, "records": records,
               "labels": {"durable": "Original durable artifact for review", "reproducible": "Regenerable output for review", "review": "Unclear, ask owner"}}
    response = None
    try:
        response = subprocess.run([helper, "operate", "--client", "storage"], input=dump(request), capture_output=True, text=True,
                                  timeout=45, check=False)
        value = json.loads(response.stdout)
    except (OSError, subprocess.TimeoutExpired, ValueError):
        value = None
    if response is None or response.returncode:
        store.set("jev_last_status", "unavailable")
        return {"status": "unavailable", "result": None}
    if not isinstance(value, dict) or value.get("status") != "computed" or value.get("authority") != "typed_data_only":
        store.set("jev_last_status", "unavailable")
        return {"status": "unavailable", "result": None}
    result = value.get("result")
    if not isinstance(result, dict):
        raise StorageError("invalid_jev", "Jev returned no typed result")
    usage = value.get("usage")
    api_calls = value.get("api_calls")
    store.set("jev_cache_" + key, {"result": result, "usage": usage, "api_calls": api_calls})
    store.set("jev_last_status", "computed")
    return {"status": "computed", "result": result, "usage": usage, "api_calls": api_calls}


def application_inventory(config, probe_active=True, only_paths=None):
    apps = []
    canonical = config["applications"]
    for root in config["application_roots"]:
        if not os.path.isdir(root) or os.path.islink(root):
            continue
        for entry in os.scandir(root):
            if only_paths is not None and entry.path not in only_paths:
                continue
            if entry.is_symlink() or not entry.name.endswith(".app") or not entry.is_dir(follow_symlinks=False):
                continue
            info_path = os.path.join(entry.path, "Contents", "Info.plist")
            try:
                with open(info_path, "rb") as stream:
                    info = plistlib.load(stream)
            except (OSError, ValueError, TypeError):
                info = {}
            bundle = str(info.get("CFBundleIdentifier", ""))
            item = canonical.get(bundle, {})
            if isinstance(item, str):
                item = {"canonical": item}
            apps.append({"bundle_id": bundle, "name": str(info.get("CFBundleDisplayName", info.get("CFBundleName", entry.name))),
                         "path": entry.path, "is_canonical": os.path.realpath(entry.path) == os.path.realpath(item.get("canonical", "")),
                         "version": str(info.get("CFBundleShortVersionString", "")), "active": tree_open(entry.path) if probe_active else None,
                         "rollback": os.path.realpath(entry.path) == os.path.realpath(item.get("rollback", ""))})
    return apps


def package_identity(path):
    identity = []
    for base, dirs, files in os.walk(path, followlinks=False):
        for name in sorted(dirs + files):
            child = os.path.join(base, name)
            value = os.lstat(child)
            identity.append((os.path.relpath(child, path), value.st_dev, value.st_ino,
                             value.st_size, value.st_mtime_ns, value.st_mode))
    return identity


def apps_op(store, config, action, only_paths=None):
    apps = application_inventory(config, only_paths=only_paths)
    if action == "inventory":
        return {"applications": apps}
    plans = []
    for app in apps:
        if app["path"] not in config["retired_app_paths"]:
            continue
        reason = None
        role = config["applications"].get(app["bundle_id"], {})
        if isinstance(role, str):
            role = {"canonical": role}
        plan_action = "pack_rollback" if app["rollback"] else "retire"
        if app["is_canonical"]:
            reason = "protected_role"
        elif app["active"]:
            reason = "active"
        elif not app["bundle_id"] or app["bundle_id"] not in config["applications"]:
            reason = "unknown_bundle"
        elif not inside(app["path"], config["application_roots"]):
            reason = "outside_root"
        elif app["rollback"]:
            destination = role.get("rollback_archive")
            rollback_root = config.get("app_rollback_root")
            if not rollback_root or not destination or not inside(destination, [rollback_root]) or not destination.endswith(".tar.gz"):
                reason = "rollback_archive_unconfigured"
        plans.append({"path": app["path"], "bundle_id": app["bundle_id"], "action": plan_action,
                      "eligible": reason is None, "reason": reason,
                      "bytes": tree_bytes(app["path"]) if reason is None else 0})
    applied = []
    if action == "apply":
        if store.get("paused", False) or not config["automatic_cleanup"]:
            raise StorageError("not_enabled", "App retirement requires active cleanup opt-in")
        for plan in plans:
            if store.get("paused", False):
                break
            if not plan["eligible"]:
                continue
            # Retirement is whole-bundle only. The selected rollback is already
            # protected by its canonical role; nonselected retired builds are
            # removed only when explicitly listed in retired_app_paths.
            fresh = next((x for x in apps_op(store, config, "preview", {plan["path"]})["plans"] if x["path"] == plan["path"]), None)
            if fresh and fresh["eligible"]:
                if store.get("paused", False):
                    break
                no_symlink_components(plan["path"])
                before = package_identity(plan["path"])
                free_before = free_bytes(os.path.dirname(plan["path"]))
                if plan["action"] == "pack_rollback":
                    role = config["applications"][plan["bundle_id"]]
                    rollback_root = config["app_rollback_root"]
                    if not os.path.isdir(rollback_root) or os.path.islink(rollback_root):
                        raise StorageError("archive_offline", "Rollback root is unavailable")
                    no_symlink_components(rollback_root)
                    destination = role["rollback_archive"]
                    no_symlink_components(os.path.dirname(destination))
                    os.makedirs(os.path.dirname(destination), exist_ok=True)
                    no_symlink_components(os.path.dirname(destination))
                    fd, stage = tempfile.mkstemp(prefix=".rollback-", dir=os.path.dirname(destination))
                    os.close(fd)
                    try:
                        with open(stage, "wb") as raw:
                            with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as zipped:
                                with tarfile.open(fileobj=zipped, mode="w|", dereference=False) as package:
                                    package.add(plan["path"], arcname=os.path.basename(plan["path"]), recursive=True)
                            raw.flush()
                            os.fsync(raw.fileno())
                        archive_digest = digest_file(stage)
                        if os.path.exists(destination):
                            if digest_file(destination) != archive_digest:
                                raise StorageError("archive_collision", "Rollback package already exists with different bytes")
                        else:
                            os.replace(stage, destination)
                        receipt = destination + ".receipt.json"
                        atomic_json_file(receipt, {"schema_version": 1, "sha256": archive_digest,
                                                   "bytes": os.path.getsize(destination), "bundle_id": plan["bundle_id"]})
                    finally:
                        if os.path.exists(stage):
                            os.unlink(stage)
                if tree_open(plan["path"]) or package_identity(plan["path"]) != before:
                    raise StorageError("source_changed", "App bundle changed or became active")
                if store.get("paused", False):
                    break
                shutil.rmtree(plan["path"])
                record_removed(store, plan["bytes"], free_before, free_bytes(os.path.dirname(plan["path"])))
                applied.append(plan["path"])
                store.event("app_retire", "removed", "Retired app bundle removed", plan["path"])
    return {"applications": apps, "plans": plans, "applied": applied}


def disk_status(config, local_only=False):
    disks = []
    locations = [("local", str(pathlib.Path.home()))]
    remote_keys = {(remote["ssh_alias"], os.path.normpath(remote["root"])) for remote in config["remote_hosts"]}
    for ident, archive in (("archive", config["archive"]), ("second_archive", config["second_archive"])):
        if archive.get("kind") == "local":
            locations.append((ident, archive["root"]))
        elif archive.get("kind") == "ssh" and (archive["ssh_alias"], os.path.normpath(archive["root"])) not in remote_keys:
            disks.append({"id": ident, "name": ident, "location": archive["root"], "total_bytes": None,
                          "free_bytes": None, "available": False, "last_checked": now()})
    for ident, path in locations:
        try:
            usage = shutil.disk_usage(path)
            disks.append({"id": ident, "name": ident, "location": path, "total_bytes": usage.total,
                          "free_bytes": usage.free, "available": True, "last_checked": now()})
        except OSError:
            disks.append({"id": ident, "name": ident, "location": path, "total_bytes": None,
                          "free_bytes": None, "available": False, "last_checked": now()})
    seen_remote = set()
    for remote in config["remote_hosts"]:
        key = (remote["ssh_alias"], os.path.normpath(remote["root"]))
        if key in seen_remote:
            continue
        seen_remote.add(key)
        item = {"id": remote["id"], "name": remote["name"], "location": remote["root"],
                "total_bytes": None, "free_bytes": None, "available": False, "last_checked": now()}
        if not local_only:
            import shlex
            command = [remote["receiver_command"], "disk", "--root", remote["root"]]
            if remote.get("expected_device") is not None:
                command.extend(["--expected-device", str(remote["expected_device"])])
            if remote.get("mount_path") is not None:
                command.extend(["--mount-path", remote["mount_path"]])
            try:
                result = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", remote["ssh_alias"],
                                         " ".join(shlex.quote(value) for value in command)], capture_output=True, timeout=10, check=False)
                payload = json.loads(result.stdout)
                if result.returncode == 0 and payload.get("ok"):
                    item.update(total_bytes=payload["total_bytes"], free_bytes=payload["free_bytes"], available=True)
            except (OSError, subprocess.TimeoutExpired, ValueError, KeyError):
                pass
        disks.append(item)
    return disks


def status(store, config, local_only=False):
    intake_scan(store, config)
    jobs = public_jobs(store)
    cleanup_preview = store.get("cleanup_preview")
    recent = store.db.execute("SELECT * FROM events ORDER BY time DESC LIMIT 20").fetchall()
    due = []
    for row in store.rows("jobs"):
        if row["state"] == "settling":
            due.append(max(row["observed_at"], row["mtime_ns"] // 1000000000) + config["settle_seconds"])
        elif row["state"] == "grace" and row["committed_at"]:
            due.append(row["committed_at"] + config["local_grace_seconds"])
    return {"profile": config["profile"], "paused": store.get("paused", False),
            "worker": {"state": "paused" if store.get("paused", False) else store.get("worker_state", "idle"),
                       "last_run": store.get("last_run"), "last_error": store.get("last_error"), "next_run": None},
            "disks": disk_status(config, local_only),
            "summary": {"ready_cleanup_bytes": cleanup_preview.get("candidate_bytes") if isinstance(cleanup_preview, dict) else None,
                        "cleanup_preview_at": cleanup_preview.get("at") if isinstance(cleanup_preview, dict) else None,
                        "review_bytes": sum(x["bytes"] for x in jobs if x["state"] in ("review", "waiting_download")),
                        "pending_count": sum(x["state"] not in ("evicted", "archived") for x in jobs),
                        "catalog_pending_count": sum(x["state"] == "catalog_pending" for x in jobs),
                        "archived_count": sum(x["state"] in ("archived", "grace", "evicted", "second_copy_required") for x in jobs),
                        "freed_bytes": store.get("observed_gain_bytes"),
                        "observed_free_delta_bytes": store.get("observed_free_delta_bytes"),
                        "logical_bytes_removed": store.get("logical_bytes_removed", 0),
                        "last_space_measurement": store.get("last_space_measurement"),
                        "next_cleanup_at": min(due) if due else None},
            "workspaces": public_workspaces(store), "queue": jobs, "applications": application_inventory(config, probe_active=False),
            "tools": tools_status(config), "jev": jev_status(config, store),
            "recent": [dict(row) for row in recent], "config": config}


def parser():
    top = JsonArgumentParser(prog="skillry-storage")
    top.add_argument("--config", default=str(default_config_path()))
    commands = top.add_subparsers(dest="command", required=True)
    for name in ("status", "pause", "resume", "tick"):
        command = commands.add_parser(name)
        if name == "status":
            command.add_argument("--local-only", action="store_true")
    config = commands.add_parser("config")
    config_actions = config.add_subparsers(dest="action", required=True)
    config_actions.add_parser("read")
    config_actions.add_parser("set")
    tools = commands.add_parser("tools")
    tools.add_argument("action", nargs="?", choices=("list", "preview"), default="list")
    tools.add_argument("id", nargs="?")
    tools.add_argument("--root")
    tools.add_argument("--run", action="store_true")
    workspace = commands.add_parser("workspace")
    ws_actions = workspace.add_subparsers(dest="action", required=True)
    ws_actions.add_parser("list")
    register = ws_actions.add_parser("register")
    register.add_argument("path", nargs="?")
    register.add_argument("--path", dest="path_flag")
    register.add_argument("--name")
    register.add_argument("--owner", required=True)
    register.add_argument("--state", choices=("open", "active"), default="open")
    register.add_argument("--outputs", default="[]")
    register.add_argument("--generated-path", action="append", default=[])
    register.add_argument("--pid", type=int)
    for name in ("heartbeat", "finish", "close", "pin", "unpin"):
        item = ws_actions.add_parser(name)
        item.add_argument("id", nargs="?")
        item.add_argument("--id", dest="id_flag")
        if name == "heartbeat":
            item.add_argument("--pid", type=int)
        if name == "finish":
            item.add_argument("--state", choices=("delivered", "failed"), required=True)
        if name == "close":
            item.add_argument("--accepted", action="store_true")
    cleanup = commands.add_parser("cleanup")
    cleanup_actions = cleanup.add_subparsers(dest="action", required=True)
    for name in ("preview", "apply"):
        cleanup_actions.add_parser(name)
    inbox = commands.add_parser("inbox")
    inbox_actions = inbox.add_subparsers(dest="action", required=True)
    inbox_actions.add_parser("list")
    for name in ("retry", "classify", "retrieve"):
        item = inbox_actions.add_parser(name)
        item.add_argument("id", nargs="?")
        item.add_argument("--id", dest="id_flag")
        if name == "classify":
            item.add_argument("--category", required=True)
    apps = commands.add_parser("apps")
    apps_actions = apps.add_subparsers(dest="action", required=True)
    for name in ("inventory", "preview", "apply"):
        apps_actions.add_parser(name)
    jev = commands.add_parser("jev")
    jev_actions = jev.add_subparsers(dest="action", required=True)
    jev_actions.add_parser("status")
    classify = jev_actions.add_parser("classify")
    classify.add_argument("--data-class", choices=("public", "synthetic"), required=True)
    receiver = commands.add_parser("receive")
    receiver.add_argument("--root", required=True)
    receiver.add_argument("--sha256", required=True)
    receiver.add_argument("--bytes", required=True, type=int)
    receiver.add_argument("--expected-device", type=int)
    receiver.add_argument("--mount-path")
    receiver.add_argument("--critical", action="store_true")
    verifier = commands.add_parser("verify")
    verifier.add_argument("--root", required=True)
    verifier.add_argument("--sha256", required=True)
    verifier.add_argument("--bytes", required=True, type=int)
    verifier.add_argument("--expected-device", type=int)
    verifier.add_argument("--mount-path")
    verifier.add_argument("--critical", action="store_true")
    verifier.add_argument("--require-catalog", action="store_true")
    catalog = commands.add_parser("catalog")
    catalog.add_argument("--root", required=True)
    catalog.add_argument("--sha256", required=True)
    catalog.add_argument("--bytes", required=True, type=int)
    catalog.add_argument("--expected-device", type=int)
    catalog.add_argument("--mount-path")
    disk = commands.add_parser("disk")
    disk.add_argument("--root", required=True)
    disk.add_argument("--expected-device", type=int)
    disk.add_argument("--mount-path")
    reader = commands.add_parser("read")
    reader.add_argument("--root", required=True)
    reader.add_argument("--sha256", required=True)
    reader.add_argument("--bytes", required=True, type=int)
    reader.add_argument("--expected-device", type=int)
    reader.add_argument("--mount-path")
    return top


def dispatch(args):
    if args.command == "receive":
        from .transfer import receiver_main
        return receiver_main(args)
    if args.command == "verify":
        from .transfer import verifier_main
        return verifier_main(args)
    if args.command == "catalog":
        from .transfer import catalog_main
        return catalog_main(args)
    if args.command == "disk":
        from .transfer import disk_main
        return disk_main(args)
    if args.command == "read":
        from .transfer import reader_main
        return reader_main(args)
    config_path = pathlib.Path(args.config)
    if args.command == "config":
        if args.action == "set":
            update = json.load(sys.stdin)
            config = save_config(config_path, update)
        else:
            config = load_config(config_path)
        return {"config": config}
    config = load_config(config_path)
    store = Store(config)
    try:
        if args.command == "status":
            return status(store, config, args.local_only)
        if args.command in ("pause", "resume"):
            paused = args.command == "pause"
            store.set("paused", paused)
            if paused:
                lock_fd = os.open(str(store.state_dir / "tick.lock"), os.O_CREAT | os.O_RDWR, 0o600)
                try:
                    fcntl.flock(lock_fd, fcntl.LOCK_EX)
                    fcntl.flock(lock_fd, fcntl.LOCK_UN)
                finally:
                    os.close(lock_fd)
            store.set("worker_state", "paused" if paused else "idle")
            return {"paused": paused, "worker": {"state": "paused" if paused else "idle"}}
        if args.command == "tick":
            return tick(store, config)
        if args.command == "tools":
            if args.action == "preview":
                return {"tool": tool_preview(config, args.id, args.root, args.run)}
            return {"tools": tools_status(config)}
        if args.command == "workspace":
            args.path = getattr(args, "path_flag", None) or getattr(args, "path", None)
            args.id = getattr(args, "id_flag", None) or getattr(args, "id", None)
            return workspace_op(store, config, args.action, args)
        if args.command == "cleanup":
            return cleanup_op(store, config, args.action == "apply")
        if args.command == "inbox":
            args.id = getattr(args, "id_flag", None) or getattr(args, "id", None)
            return inbox_op(store, config, args.action, args)
        if args.command == "apps":
            return apps_op(store, config, args.action)
        if args.command == "jev":
            if args.action == "classify":
                return {"jev": jev_classify(config, store, args.data_class, json.load(sys.stdin))}
            return {"jev": jev_status(config, store)}
        raise StorageError("unknown_command", "Unsupported command")
    finally:
        store.db.close()


def main(argv=None):
    try:
        result = dispatch(parser().parse_args(argv))
        if isinstance(result, int):
            return result
        print(dump({"schema_version": SCHEMA_VERSION, "ok": True, **result}))
        return 0
    except (StorageError, sqlite3.Error, OSError, ValueError, json.JSONDecodeError) as exc:
        code = exc.code if isinstance(exc, StorageError) else "operation_failed"
        print(dump({"schema_version": SCHEMA_VERSION, "ok": False, "error": {"code": code, "message": str(exc)}}))
        return 1

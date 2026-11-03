"""Synthetic storage lifecycle evidence; no host archive or user files."""
import io
import fcntl
import hashlib
import json
import os
import plistlib
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from storage import engine, transfer


class StorageEngineTest(unittest.TestCase):
    def test_app_retirement_rechecks_target_and_preserves_newly_active_bundle(self):
        apps = self.root / "Applications"
        apps.mkdir()
        current, retired = [apps / name for name in ("Current.app", "Old.app")]
        for bundle in (current, retired):
            (bundle / "Contents").mkdir(parents=True)
            (bundle / "Contents/Info.plist").write_bytes(plistlib.dumps({"CFBundleIdentifier": "example.app"}))
        self.config.update(application_roots=[str(apps)], applications={"example.app": {"canonical": str(current)}}, retired_app_paths=[str(retired)])
        calls = []
        def probe(path):
            calls.append(path)
            return path == str(retired) and calls.count(path) > 1
        with mock.patch.object(engine, "tree_open", side_effect=probe):
            result = engine.apps_op(self.store, self.config, "apply")
        self.assertEqual(result["applied"], [])
        self.assertTrue(current.exists())
        self.assertTrue(retired.exists())
        self.assertEqual(calls.count(str(current)), 1)
        self.assertEqual(calls.count(str(retired)), 2)

    def test_lsof_partial_result_still_protects_active_paths(self):
        with mock.patch.object(shutil, "which", return_value="/usr/sbin/lsof"), \
             mock.patch.object(subprocess, "run", return_value=SimpleNamespace(returncode=1, stdout=b"57052\n")):
            self.assertTrue(engine.path_open("/example/file"))
            self.assertTrue(engine.tree_open("/example/app"))

    def test_missing_lsof_does_not_authorize_removal(self):
        with mock.patch.object(shutil, "which", return_value=None):
            self.assertTrue(engine.path_open("/example/file"))
            self.assertTrue(engine.tree_open("/example/app"))

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        # macOS exposes the temporary root through /var -> /private/var.
        # Resolve the owned fixture before exercising production symlink guards.
        self.root = Path(self.temp.name).resolve(strict=True)
        self.workspace_root = self.root / "work"
        self.workspace_root.mkdir()
        self.intake = self.root / "intake"
        self.intake.mkdir()
        self.archive = self.root / "archive"
        self.archive.mkdir()
        self.config = {**engine.DEFAULT, "state_dir": str(self.root / "state"), "workspace_roots": [str(self.workspace_root)],
                       "intake_dir": str(self.intake), "archive": {"kind": "local", "root": str(self.archive)},
                       "automatic_archive": True, "automatic_cleanup": True, "settle_seconds": 0, "local_grace_seconds": 0}
        self.store = engine.Store(self.config)
        self.addCleanup(self.store.db.close)

    def workspace(self, output="dist"):
        path = self.workspace_root / "job"
        path.mkdir(exist_ok=True)
        args = type("Args", (), {"path": str(path), "outputs": json.dumps([output]), "generated_path": [], "name": "job",
                                "owner": "fixture", "pid": None, "state": "open"})()
        ident = engine.workspace_op(self.store, self.config, "register", args)["id"]
        return path, ident

    def test_closed_registered_output_only(self):
        path, ident = self.workspace()
        (path / "dist").mkdir()
        (path / "dist" / "generated").write_text("compiled")
        self.assertFalse(engine.cleanup_op(self.store, self.config, False)["candidates"][0]["eligible"])
        args = type("Args", (), {"id": ident, "accepted": True})()
        engine.workspace_op(self.store, self.config, "close", args)
        engine.cleanup_op(self.store, self.config, True)
        self.assertFalse((path / "dist").exists())

    def test_cleanup_goes_on_when_another_cleanup_took_a_path_first(self):
        path = self.workspace_root / "job"
        path.mkdir()
        args = type("Args", (), {"path": str(path), "outputs": '["build", "dist"]', "generated_path": [], "name": "job",
                                "owner": "fixture", "pid": None, "state": "open"})()
        ident = engine.workspace_op(self.store, self.config, "register", args)["id"]
        for output in ("build", "dist"):
            (path / output).mkdir()
            (path / output / "generated").write_text("compiled")
        engine.workspace_op(self.store, self.config, "close", type("Args", (), {"id": ident, "accepted": True})())
        checked = engine.cleanup_candidate
        def racing(row, relative, config, measure=True, evidence=None):
            result = checked(row, relative, config, measure, evidence)
            if not measure and relative == "build":
                shutil.rmtree(path / "build")
            return result
        with mock.patch.object(engine, "cleanup_candidate", side_effect=racing):
            outcome = engine.cleanup_op(self.store, self.config, True)
        self.assertEqual(outcome["removed"], [str(path / "dist")])
        self.assertFalse((path / "dist").exists())

    def test_register_reopens_closed_workspace_before_cleanup(self):
        path, ident = self.workspace()
        (path / "node_modules").mkdir()
        engine.workspace_op(self.store, self.config, "close", type("Args", (), {"id": ident, "accepted": True})())
        args = type("Args", (), {"path": str(path), "outputs": '["node_modules"]', "generated_path": [],
                                "name": "reused job", "owner": "fixture", "pid": None, "state": "active"})()
        self.assertEqual(engine.workspace_op(self.store, self.config, "register", args)["id"], ident)
        row = self.store.db.execute("SELECT * FROM workspaces WHERE id=?", (ident,)).fetchone()
        self.assertEqual(row["state"], "active")
        self.assertEqual(row["name"], "reused job")
        self.assertEqual(json.loads(row["outputs"]), ["node_modules"])
        self.assertEqual(engine.cleanup_op(self.store, self.config, False)["candidates"][0]["reason"], "workspace_active_or_held")
        self.assertTrue((path / "node_modules").exists())

    def test_register_rejects_other_owner_of_active_workspace(self):
        path, ident = self.workspace()
        args = type("Args", (), {"path": str(path), "outputs": '["dist"]', "generated_path": [],
                                "name": "takeover", "owner": "other owner", "pid": None, "state": "active"})()
        with self.assertRaises(engine.StorageError) as raised:
            engine.workspace_op(self.store, self.config, "register", args)
        self.assertEqual(raised.exception.code, "workspace_owned")
        row = self.store.db.execute("SELECT * FROM workspaces WHERE id=?", (ident,)).fetchone()
        self.assertEqual(row["owner"], "fixture")
        self.assertEqual(row["state"], "open")

    def test_logical_removal_does_not_inflate_measured_free_space(self):
        path, ident = self.workspace()
        (path / "dist").mkdir()
        (path / "dist" / "generated").write_bytes(b"a" * 100)
        engine.workspace_op(self.store, self.config, "close", type("Args", (), {"id": ident, "accepted": True})())
        with mock.patch.object(engine, "free_bytes", return_value=5000):
            engine.cleanup_op(self.store, self.config, True)
        summary = engine.status(self.store, self.config, local_only=True)["summary"]
        self.assertEqual(summary["logical_bytes_removed"], 100)
        self.assertEqual(summary["freed_bytes"], 0)
        self.assertEqual(summary["observed_free_delta_bytes"], 0)

    def test_active_process_and_pin_prevent_cleanup(self):
        path, ident = self.workspace()
        (path / "dist").mkdir()
        self.store.db.execute("UPDATE workspaces SET pid=? WHERE id=?", (os.getpid(), ident))
        self.store.db.commit()
        with self.assertRaises(engine.StorageError):
            engine.workspace_op(self.store, self.config, "close", type("Args", (), {"id": ident, "accepted": True})())
        self.store.db.execute("UPDATE workspaces SET pid=NULL,hold=1,state='closed' WHERE id=?", (ident,))
        self.store.db.commit()
        self.assertFalse(engine.cleanup_op(self.store, self.config, False)["candidates"][0]["eligible"])

    def test_finish_records_delivery_without_accepting_cleanup(self):
        path, ident = self.workspace()
        (path / "dist").mkdir()
        engine.workspace_op(self.store, self.config, "finish", type("Args", (), {"id": ident, "state": "delivered"})())
        self.assertEqual(self.store.rows("workspaces")[0]["state"], "delivered")
        self.assertFalse(engine.cleanup_op(self.store, self.config, False)["candidates"][0]["eligible"])

    def test_database_must_stay_in_review(self):
        database = self.intake / "live.db"
        database.write_bytes(b"SQLite format 3\0some bytes")
        engine.intake_scan(self.store, self.config)
        self.assertEqual(self.store.rows("jobs")[0]["state"], "review")
        with self.assertRaises(engine.StorageError):
            engine.inbox_op(self.store, self.config, "classify", type("Args", (), {"id": self.store.rows("jobs")[0]["id"], "category": "ordinary"})())
        self.assertTrue(database.exists())

    def test_overlapping_tick_is_skipped(self):
        lock = os.open(str(self.store.state_dir / "tick.lock"), os.O_CREAT | os.O_RDWR, 0o600)
        try:
            fcntl.flock(lock, fcntl.LOCK_EX)
            self.assertEqual(engine.tick(self.store, self.config)["worker"], "busy")
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
            os.close(lock)

    def test_tracked_output_and_symlink_escape_are_protected(self):
        path, ident = self.workspace()
        output = path / "dist"
        output.mkdir()
        subprocess.run(["git", "-C", str(path), "init", "-q"], check=True)
        (output / "source.txt").write_text("keep")
        subprocess.run(["git", "-C", str(path), "add", "dist/source.txt"], check=True)
        engine.workspace_op(self.store, self.config, "close", type("Args", (), {"id": ident, "accepted": True})())
        self.assertEqual(engine.cleanup_op(self.store, self.config, False)["candidates"][0]["reason"], "tracked")
        (output / "source.txt").unlink()
        output.rmdir()
        output.symlink_to(self.root / "archive", target_is_directory=True)
        self.assertFalse(engine.cleanup_op(self.store, self.config, False)["candidates"][0]["eligible"])

    def test_pnpm_member_symlinks_unlinked_without_following_external_store(self):
        if not shutil.rmtree.avoids_symlink_attacks:
            self.skipTest("This platform lacks fd-safe rmtree")
        path, ident = self.workspace("node_modules")
        modules = path / "node_modules"
        (modules / ".bin").mkdir(parents=True)
        (modules / ".pnpm").mkdir()
        external = self.root / "shared-store"
        external.mkdir()
        (external / "keep.js").write_text("preserve")
        (modules / ".bin" / "tool").symlink_to(external / "keep.js")
        (modules / ".pnpm" / "package").symlink_to(external, target_is_directory=True)
        engine.workspace_op(self.store, self.config, "close", type("Args", (), {"id": ident, "accepted": True})())
        with mock.patch.object(engine, "process_cwds", return_value=[]), mock.patch.object(engine, "lsof_holders", return_value=False):
            preview = engine.cleanup_op(self.store, self.config, False)
            self.assertTrue(preview["candidates"][0]["eligible"])
            engine.cleanup_op(self.store, self.config, True)
        self.assertFalse(modules.exists())
        self.assertEqual((external / "keep.js").read_text(), "preserve")

    def closed_outputs(self, count):
        outputs = []
        for index in range(count):
            path = self.workspace_root / f"job{index}"
            path.mkdir()
            args = type("Args", (), {"path": str(path), "outputs": '["dist"]', "generated_path": [], "name": path.name,
                                    "owner": "fixture", "pid": None, "state": "open"})()
            ident = engine.workspace_op(self.store, self.config, "register", args)["id"]
            (path / "dist").mkdir()
            (path / "dist" / "generated").write_text("compiled")
            engine.workspace_op(self.store, self.config, "close", type("Args", (), {"id": ident, "accepted": True})())
            outputs.append(path / "dist")
        return outputs

    def fake_lsof(self, held=(), fail=False):
        """Answer lsof like a machine where no process works in the fixtures; other commands run for real."""
        calls, real_run = [], subprocess.run
        def run(argv, **kwargs):
            if argv[0] != "lsof":
                return real_run(argv, **kwargs)
            calls.append(argv)
            if argv[1] == "-Fn":
                return SimpleNamespace(returncode=0, stdout=b"p1\nfcwd\nn/\n")
            if fail:
                raise subprocess.TimeoutExpired(argv, 8)
            hit = any(str(path) in argv[2:] for path in held)
            return SimpleNamespace(returncode=0 if hit else 1, stdout=b"4242\n" if hit else b"")
        return calls, mock.patch.object(subprocess, "run", side_effect=run)

    def test_cleanup_pass_scans_processes_once_instead_of_twice_per_output(self):
        outputs = self.closed_outputs(5)
        calls, lsof = self.fake_lsof()
        with mock.patch.object(shutil, "which", return_value="/usr/sbin/lsof"), lsof:
            outcome = engine.cleanup_op(self.store, self.config, True)
        self.assertEqual(sorted(outcome["removed"]), sorted(map(str, outputs)))
        self.assertEqual([argv[:2] for argv in calls], [["lsof", "-Fn"], ["lsof", "-t"]])
        self.assertEqual(sorted(calls[1][2:]), sorted(map(str, outputs)))

    def test_batched_scan_protects_only_the_output_a_process_holds(self):
        outputs = self.closed_outputs(4)
        calls, lsof = self.fake_lsof(held=[outputs[2]])
        with mock.patch.object(shutil, "which", return_value="/usr/sbin/lsof"), lsof:
            preview = engine.cleanup_op(self.store, self.config, False)
            outcome = engine.cleanup_op(self.store, self.config, True)
        self.assertEqual([item["reason"] for item in preview["candidates"]], [None, None, "open_process", None])
        self.assertEqual(sorted(outcome["removed"]), sorted(str(path) for path in outputs if path != outputs[2]))
        self.assertTrue(outputs[2].exists())

    def test_failed_batch_scan_protects_every_output_without_splitting(self):
        outputs = self.closed_outputs(4)
        calls, lsof = self.fake_lsof(fail=True)
        with mock.patch.object(shutil, "which", return_value="/usr/sbin/lsof"), lsof:
            outcome = engine.cleanup_op(self.store, self.config, True)
        self.assertEqual(outcome["removed"], [])
        self.assertTrue(all(path.exists() for path in outputs))
        self.assertEqual(len([argv for argv in calls if argv[1] == "-t"]), 1)

    def test_stale_process_evidence_is_scanned_again_before_removal(self):
        outputs = self.closed_outputs(3)
        calls, lsof = self.fake_lsof()
        with mock.patch.object(shutil, "which", return_value="/usr/sbin/lsof"), lsof, \
             mock.patch.object(engine.ProcessEvidence, "MAX_AGE", -1):
            outcome = engine.cleanup_op(self.store, self.config, True)
        self.assertEqual(len(outcome["removed"]), 3)
        self.assertEqual(len([argv for argv in calls if argv[1] == "-Fn"]), 3)
        self.assertEqual([len(argv) - 2 for argv in calls if argv[1] == "-t"], [3, 2, 1])

    def test_tick_cleanup_stops_at_its_budget_and_resumes_on_the_next_tick(self):
        outputs = self.closed_outputs(2)
        (self.intake / "delivery.mp4").write_bytes(b"inbox file")
        self.store.set("cleanup_pending", False)
        calls, lsof = self.fake_lsof()
        with mock.patch.object(shutil, "which", return_value="/usr/sbin/lsof"), lsof:
            with mock.patch.object(engine, "CLEANUP_TICK_SECONDS", 0):
                engine.tick(self.store, self.config)
            self.assertIsNotNone(self.store.rows("jobs")[0]["receipt"])
            self.assertTrue(all(path.exists() for path in outputs))
            self.assertTrue(self.store.get("cleanup_pending"))
            engine.tick(self.store, self.config)
        self.assertFalse(any(path.exists() for path in outputs))
        self.assertFalse(self.store.get("cleanup_pending"))

    def test_status_uses_cached_cleanup_preview(self):
        path, ident = self.workspace()
        (path / "dist").mkdir()
        engine.workspace_op(self.store, self.config, "close", type("Args", (), {"id": ident, "accepted": True})())
        with mock.patch.object(engine, "cleanup_candidates", side_effect=AssertionError("heavy scan")):
            self.assertIsNone(engine.status(self.store, self.config, local_only=True)["summary"]["ready_cleanup_bytes"])

    def test_matching_ssh_archive_uses_one_named_available_remote_disk(self):
        remote_root = "/Volumes/Fixture-SSD/Archive/Inbox"
        archive = {"kind": "ssh", "root": remote_root, "ssh_alias": "fixture-m1",
                   "receiver_command": "/fixture/skillry-storage"}
        remote = {"id": "m1-ssd", "name": "M1 SSD", "root": remote_root,
                  "ssh_alias": "fixture-m1", "receiver_command": "/fixture/skillry-storage"}
        config = {**self.config, "archive": archive,
                  "remote_hosts": [remote, {**remote, "id": "duplicate", "name": "Duplicate"}]}
        response = subprocess.CompletedProcess([], 0, stdout=json.dumps({"ok": True, "total_bytes": 1000, "free_bytes": 750}).encode())
        with mock.patch.object(engine.subprocess, "run", return_value=response) as probe, \
             mock.patch.object(engine.shutil, "disk_usage", return_value=SimpleNamespace(total=2000, free=1000)):
            disks = engine.disk_status(config)
        self.assertEqual(probe.call_count, 1)
        self.assertEqual([disk["id"] for disk in disks], ["local", "m1-ssd"])
        self.assertEqual(disks[1]["name"], "M1 SSD")
        self.assertTrue(disks[1]["available"])
        self.assertEqual(disks[1]["free_bytes"], 750)

    def test_pause_and_identity_change_keep_source(self):
        source = self.intake / "report.txt"
        source.write_text("v1")
        engine.intake_scan(self.store, self.config)
        self.store.set("paused", True)
        self.assertEqual(engine.tick(self.store, self.config)["worker"], "paused")
        self.assertTrue(source.exists())
        source.unlink()
        source.write_text("v2")
        self.store.set("paused", False)
        self.config["automatic_archive"] = False
        engine.tick(self.store, self.config)
        self.assertEqual(source.read_text(), "v2")

    def test_archive_receipt_before_eviction_and_repeat_is_idempotent(self):
        source = self.intake / "photo.jpg"
        source.write_bytes(b"unique-fixture")
        self.config["local_grace_seconds"] = 5
        engine.intake_scan(self.store, self.config)
        result = engine.tick(self.store, self.config)
        self.assertEqual(result["errors"], [])
        self.assertTrue(source.exists())
        self.store.db.execute("UPDATE jobs SET committed_at=committed_at-10")
        self.store.db.commit()
        engine.tick(self.store, self.config)
        self.assertFalse(source.exists())
        receipts = self.store.rows("receipts")
        self.assertEqual(len(receipts), 1)
        self.assertEqual(len(list((self.archive / "objects").rglob(receipts[0]["digest"]))), 1)

    def test_critical_needs_second_independent_copy(self):
        source = self.intake / "original.jpg"
        source.write_bytes(b"critical")
        engine.intake_scan(self.store, self.config)
        row = self.store.rows("jobs")[0]
        engine.job_update(self.store, row["id"], category="critical")
        engine.tick(self.store, self.config)
        self.assertTrue(source.exists())
        self.assertEqual(self.store.rows("jobs")[0]["state"], "second_copy_required")

    def test_same_device_second_copy_is_not_independent(self):
        second = self.root / "second"
        second.mkdir()
        self.config["second_archive"] = {"kind": "local", "root": str(second)}
        source = self.intake / "critical.jpg"
        source.write_bytes(b"critical unique")
        engine.intake_scan(self.store, self.config)
        row = self.store.rows("jobs")[0]
        engine.job_update(self.store, row["id"], category="critical")
        self.assertEqual(engine.tick(self.store, self.config)["errors"][0]["code"], "second_not_independent")
        self.assertTrue(source.exists())

    def test_archive_offline_or_wrong_device_keeps_source(self):
        source = self.intake / "sample.jpg"
        source.write_bytes(b"sample")
        self.config["archive"]["expected_device"] = os.stat(self.archive).st_dev + 1
        engine.intake_scan(self.store, self.config)
        self.assertEqual(engine.tick(self.store, self.config)["errors"][0]["code"], "archive_device_changed")
        self.assertTrue(source.exists())

    def test_interrupted_or_wrong_digest_receiver_never_commits(self):
        correct = engine.hashlib.sha256(b"abcdef").hexdigest()
        with self.assertRaises(engine.StorageError):
            transfer.receive_stream(self.archive, correct, 6, io.BytesIO(b"abc"))
        self.assertIsNone(transfer.verified_receipt(self.archive, correct, 6))
        with self.assertRaises(engine.StorageError):
            transfer.receive_stream(self.archive, correct, 6, io.BytesIO(b"123456"))
        self.assertIsNone(transfer.verified_receipt(self.archive, correct, 6))

    def test_archive_objects_symlink_cannot_escape_root(self):
        outside = self.root / "outside"
        outside.mkdir()
        (self.archive / "objects").symlink_to(outside, target_is_directory=True)
        digest = engine.hashlib.sha256(b"bytes").hexdigest()
        with self.assertRaises((engine.StorageError, OSError)):
            transfer.receive_stream(self.archive, digest, 5, io.BytesIO(b"bytes"))
        self.assertEqual(list(outside.iterdir()), [])

    def test_duplicate_digest_preserves_each_original_name(self):
        content = b"shared bytes"
        digest = engine.hashlib.sha256(content).hexdigest()
        common = {"source_host": "fixture-host", "category": "ordinary", "rights": "unknown", "tag": None, "received_at": 1}
        first = {**common, "job_id": "job-one", "original_name": "first.txt"}
        second = {**common, "job_id": "job-two", "original_name": "second.txt"}
        transfer.receive_stream(self.archive, digest, len(content), io.BytesIO(content), origin=first)
        transfer.receive_stream(self.archive, digest, len(content), io.BytesIO(content), origin=second)
        _, receipt = transfer.target_paths(self.archive, digest)
        origins = json.loads(receipt.read_text())["origins"]
        self.assertEqual({item["original_name"] for item in origins}, {"first.txt", "second.txt"})

    def test_catalog_bridge_gap_then_link_reuses_committed_object(self):
        content = b"catalog fixture"
        digest = engine.hashlib.sha256(content).hexdigest()
        transfer.receive_stream(self.archive, digest, len(content), io.BytesIO(content))
        target, receipt = transfer.target_paths(self.archive, digest)
        before = target.stat().st_ino
        self.config["catalog_bridge"] = {"command": ["/trusted/catalog-bridge", "--apply"], "timeout_seconds": 60}
        gap = (2, json.dumps({"status": "gap", "reason": "catalog_offline"}).encode())
        linked = (0, json.dumps({"status": "COMPLETED", "source_id": "source-1", "snapshot_id": "scan-1", "source_name": "fixture", "matched_sha256": digest}).encode())
        with mock.patch.object(transfer, "run_group", side_effect=[gap, linked]):
            self.assertEqual(transfer.catalog_reconcile(self.config, self.archive, digest, len(content))["state"], "gap")
            self.assertEqual(transfer.catalog_reconcile(self.config, self.archive, digest, len(content))["state"], "linked")
        self.assertEqual(target.stat().st_ino, before)
        self.assertEqual(json.loads(receipt.read_text())["catalog_sync"]["snapshot_id"], "scan-1")

    def test_catalog_bridge_success_for_other_digest_is_still_gap(self):
        content = b"required digest"
        digest = engine.hashlib.sha256(content).hexdigest()
        transfer.receive_stream(self.archive, digest, len(content), io.BytesIO(content))
        self.config["catalog_bridge"] = {"command": ["/trusted/catalog-bridge", "--apply"], "timeout_seconds": 60}
        wrong = (0, json.dumps({"status": "COMPLETED", "source_id": "source-1",
                               "snapshot_id": "scan-1", "matched_sha256": "0" * 64}).encode())
        with mock.patch.object(transfer, "run_group", return_value=wrong):
            outcome = transfer.catalog_reconcile(self.config, self.archive, digest, len(content))
        self.assertEqual(outcome["state"], "gap")

    def test_crash_after_claim_rename_restores_verified_source(self):
        source = self.intake / "claim.txt"
        source.write_bytes(b"claim bytes")
        engine.intake_scan(self.store, self.config)
        row = self.store.rows("jobs")[0]
        claim = str(source) + ".skillry-evict-" + row["id"]
        engine.job_update(self.store, row["id"], state="evicting", digest=engine.digest_file(source),
                          claim_path=claim, claim_started_at=engine.now())
        os.rename(source, claim)
        engine.intake_scan(self.store, self.config)
        self.assertEqual(source.read_bytes(), b"claim bytes")
        self.assertFalse(os.path.lexists(claim))
        self.assertEqual(self.store.rows("jobs")[0]["state"], "grace")

    def test_crash_after_claim_unlink_marks_evicted_without_claimed_gain(self):
        source = self.intake / "claim.txt"
        source.write_bytes(b"claim bytes")
        engine.intake_scan(self.store, self.config)
        row = self.store.rows("jobs")[0]
        claim = str(source) + ".skillry-evict-" + row["id"]
        engine.job_update(self.store, row["id"], state="evicting", digest=engine.digest_file(source),
                          claim_path=claim, claim_started_at=engine.now())
        os.rename(source, claim)
        os.unlink(claim)
        engine.intake_scan(self.store, self.config)
        self.assertEqual(self.store.rows("jobs")[0]["state"], "evicted")
        self.assertIsNone(self.store.get("observed_gain_bytes"))
        self.assertEqual(self.store.get("logical_bytes_removed", 0), 0)

    def test_source_replaced_during_remote_proof_is_retained(self):
        source = self.intake / "mutable.jpg"
        source.write_bytes(b"original")
        self.config["local_grace_seconds"] = 5
        engine.intake_scan(self.store, self.config)
        engine.tick(self.store, self.config)
        self.store.db.execute("UPDATE jobs SET committed_at=committed_at-10")
        self.store.db.commit()
        real_verify = transfer.verify_remote

        def replace_then_verify(archive, digest, size, **kwargs):
            source.unlink()
            source.write_bytes(b"replacement")
            return real_verify(archive, digest, size, **kwargs)

        with mock.patch.object(transfer, "verify_remote", side_effect=replace_then_verify):
            self.assertEqual(engine.tick(self.store, self.config)["errors"][0]["code"], "source_changed")
        self.assertEqual(source.read_bytes(), b"replacement")

    def test_pause_during_archive_verification_retains_source(self):
        source = self.intake / "pause.jpg"
        source.write_bytes(b"pause proof")
        self.config["local_grace_seconds"] = 5
        engine.intake_scan(self.store, self.config)
        engine.tick(self.store, self.config)
        self.store.db.execute("UPDATE jobs SET committed_at=committed_at-10")
        self.store.db.commit()
        real_verify = transfer.verify_remote

        def pause_then_verify(archive, digest, size, **kwargs):
            self.store.set("paused", True)
            return real_verify(archive, digest, size, **kwargs)

        with mock.patch.object(transfer, "verify_remote", side_effect=pause_then_verify):
            engine.tick(self.store, self.config)
        self.assertTrue(source.exists())

    def test_retrieve_evicted_file_and_preserve_edited_cache(self):
        source = self.intake / "recent.txt"
        source.write_bytes(b"archived original")
        engine.intake_scan(self.store, self.config)
        engine.tick(self.store, self.config)
        self.assertFalse(source.exists())
        row = self.store.db.execute("SELECT * FROM jobs").fetchone()
        first = engine.retrieve_job(self.store, self.config, row)
        self.assertEqual(Path(first["path"]).read_bytes(), b"archived original")
        Path(first["path"]).write_bytes(b"user edit")
        second = engine.retrieve_job(self.store, self.config, row)
        self.assertNotEqual(first["path"], second["path"])
        self.assertEqual(Path(first["path"]).read_bytes(), b"user edit")
        self.assertEqual(Path(second["path"]).read_bytes(), b"archived original")

    def test_corrupt_archive_refuses_retrieval_and_leaves_no_cache_file(self):
        source = self.intake / "recent.txt"
        source.write_bytes(b"archived original")
        engine.intake_scan(self.store, self.config)
        engine.tick(self.store, self.config)
        row = self.store.db.execute("SELECT * FROM jobs").fetchone()
        object_path, _ = transfer.target_paths(self.archive, row["digest"])
        object_path.write_bytes(b"corrupt")
        with self.assertRaises(engine.StorageError):
            engine.retrieve_job(self.store, self.config, row)
        cache_dir = self.store.state_dir / "retrieved" / row["id"]
        self.assertEqual(list(cache_dir.iterdir()), [])

    def test_tick_uses_jev_only_for_synthetic_ambiguous_record(self):
        source = self.intake / "private-customer-name.odd"
        source.write_bytes(b"private source content")
        self.config["jev"] = {**self.config["jev"], "enabled": True}
        captured = []

        def synthetic_only(_config, _store, data_class, payload):
            captured.append((data_class, payload))
            return {"status": "computed", "result": {"buckets": {"durable": [{"id": "r0"}]}, "review": []}, "usage": None}

        with mock.patch.object(engine, "jev_classify", side_effect=synthetic_only):
            engine.tick(self.store, self.config)
        self.assertEqual(len(captured), 1)
        self.assertEqual(captured[0][0], "synthetic")
        self.assertNotIn("private-customer-name", json.dumps(captured[0][1]))
        self.assertNotIn("private source content", json.dumps(captured[0][1]))
        self.assertEqual(self.store.rows("jobs")[0]["state"], "review")
        self.assertTrue(source.exists())

    def test_owner_classified_unknown_type_archives_after_settling(self):
        # Regression: an owner classification of an unrecognised type (.tar) was put
        # back in review once the job settled, so it could never reach the archive.
        source = self.intake / "delivery.tar"
        source.write_bytes(b"owner-approved package")
        self.config["jev"] = {**self.config["jev"], "enabled": True}
        self.config["settle_seconds"] = 3600
        with mock.patch.object(engine, "jev_classify", return_value={"status": "unavailable", "result": None}):
            engine.tick(self.store, self.config)
            job = self.store.rows("jobs")[0]
            self.assertEqual((job["category"], job["state"]), ("review", "review"))
            engine.inbox_op(self.store, self.config, "classify",
                            type("Args", (), {"id": job["id"], "category": "ordinary"})())
            engine.tick(self.store, self.config)
            self.assertEqual(self.store.rows("jobs")[0]["state"], "settling")
            engine.tick(self.store, self.config)
            job = self.store.rows("jobs")[0]
            self.assertEqual((job["category"], job["state"]), ("ordinary", "settling"))
            self.config["settle_seconds"] = 0
            engine.tick(self.store, self.config)
        job = self.store.rows("jobs")[0]
        self.assertEqual(job["category"], "ordinary")
        self.assertIsNotNone(job["receipt"])
        self.assertEqual(json.loads(job["receipt"])["sha256"], hashlib.sha256(b"owner-approved package").hexdigest())


if __name__ == "__main__":
    unittest.main()

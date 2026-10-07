"""Offline checks for the operation-only Storage identity and helper setup."""
import contextlib
import base64
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from jev.catalog import OPERATION_CALLERS, SKILL_ROOTS, digest
from jev.cli import explicit_request, hook_request, main as cli_main
from jev.core import Invalid, MODEL, decide, validate_request
from jev.install import apply, plan


class StorageJevTests(unittest.TestCase):
    def derived_fixture(self, home):
        root = home / ".skillry/jev"
        root.mkdir(parents=True)
        (root / "config.json").write_text(json.dumps({"schema_version": 1, "enabled": True,
            "clients": ["codex"], "secret": {"kind": "keychain", "service": "existing.service",
            "account": "owner"}, "projects": {}}))
        old = {"schema_version": 1, "catalog_version": "old", "records": [],
               "excluded": [], "private_entries": []}
        old["version"] = digest(old["records"])
        current = {**old, "records": [{"id": "new-installed-skill"}]}
        current["version"] = digest(current["records"])
        path = root / "inventory.json"
        path.write_text(json.dumps(current))
        previous = {"status": "applied", "clients": ["codex"], "changes": [
            {"path": str(path), "after_sha256": digest(json.dumps(old).encode())}]}
        (root / "installation.json").write_text(json.dumps(previous))
        catalog = {"schema_version": 1, "entries": []}
        catalog["version"] = digest(catalog["entries"])
        return path, current, catalog

    def test_derived_inventory_reconciliation_is_explicit_and_records_actual_preimage(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory).resolve()
            inventory_path, current, catalog = self.derived_fixture(home)
            args = (home, ["codex"], sys.executable, home / "provider-python", None, "owner")
            with patch("jev.install.build_public", return_value=catalog):
                with self.assertRaisesRegex(Invalid, "managed_drift.*inventory.json"):
                    plan(*args, storage_only=True)
                with self.assertRaisesRegex(Invalid, "requires_storage_only"):
                    plan(*args, reconcile_derived_inventory=True)
                receipt = plan(*args, storage_only=True, reconcile_derived_inventory=True)
            self.assertEqual(receipt["reconciled_paths"], [str(inventory_path)])
            change = next(row for row in receipt["changes"] if row["path"] == str(inventory_path))
            self.assertEqual(base64.b64decode(change["before"]), json.dumps(current).encode())
            apply(receipt, home)
            refreshed = json.loads(inventory_path.read_text())
            self.assertEqual(refreshed["version"], digest(refreshed["records"]))
            self.assertEqual(refreshed["catalog_version"], catalog["version"])
            self.assertEqual(refreshed["records"], [])

    def test_reconciliation_refuses_unrelated_managed_wrapper_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory).resolve()
            _, _, catalog = self.derived_fixture(home)
            wrapper = home / ".local/bin/skillry-jev"
            wrapper.parent.mkdir(parents=True)
            wrapper.write_bytes(b"locally changed wrapper")
            receipt_path = home / ".skillry/jev/installation.json"
            previous = json.loads(receipt_path.read_text())
            previous["changes"].append({"path": str(wrapper), "after_sha256": digest(b"old wrapper")})
            receipt_path.write_text(json.dumps(previous))
            with patch("jev.install.build_public", return_value=catalog):
                with self.assertRaisesRegex(Invalid, "managed_drift.*skillry-jev"):
                    plan(home, ["codex"], sys.executable, home / "provider-python", None,
                         "owner", storage_only=True, reconcile_derived_inventory=True)

    def test_reconciliation_rejects_invalid_inventory_projection(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory).resolve()
            inventory_path, current, catalog = self.derived_fixture(home)
            current["version"] = "wrong"
            inventory_path.write_text(json.dumps(current))
            with patch("jev.install.build_public", return_value=catalog):
                with self.assertRaisesRegex(Invalid, "managed_drift.*inventory.json"):
                    plan(home, ["codex"], sys.executable, home / "provider-python", None,
                         "owner", storage_only=True, reconcile_derived_inventory=True)

    def test_storage_compute_uses_typed_data_only(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory).resolve()
            config = {"enabled": True, "public_advice": False,
                      "operation_clients": ["storage"], "projects": {},
                      "monthly_budget_eur": None, "deadline_seconds": 3,
                      "choice_confidence_floor": 0.4}
            raw = {"operation": "classify", "task": "Classify abstract artifacts",
                   "data_class": "synthetic", "records": [{"id": "a", "text": "Declared build output"}],
                   "labels": {"reproducible": "Generated from protected source"}}
            request = explicit_request(raw | {"mode": "compute"}, "storage", config)
            calls = []

            def transport(state, questions, _config, _deadline):
                calls.append(state)
                key = "classify:a"
                self.assertEqual(questions[key]["type"], "choice")
                return {"response": {"model": MODEL, "answers": {key: {
                    "type": "choice", "choice": "reproducible", "confidence": 0.99,
                    "probabilities": {"reproducible": 1.0, "none": 0.0}}},
                    "usage": {"input_tokens": 20, "output_tokens": 3}}}

            result = decide(request, config, {"version": "v"}, {"version": "i"},
                            home, home / "state", transport, explicit_advice=True)
            self.assertEqual(result["status"], "computed", result)
            self.assertEqual(result["authority"], "typed_data_only")
            self.assertEqual(result["result"]["buckets"]["reproducible"][0]["id"], "a")
            self.assertEqual(len(calls), 1)

    def test_storage_has_no_agent_or_raw_hook_identity(self):
        self.assertIn("storage", OPERATION_CALLERS)
        self.assertNotIn("storage", SKILL_ROOTS)
        self.assertIsNone(hook_request({"hook_event_name": "UserPromptSubmit"}, "storage", {}, {}))
        for mode in ("skill", "agent", "workflow", "tool"):
            raw = {"client": "storage", "session_id": "s", "request_id": "r",
                   "workspace": "/tmp", "identity": "local", "tenant": "local",
                   "permission_version": "p", "mode": mode, "task": "Select a skill"}
            with self.subTest(mode=mode), self.assertRaises(Invalid):
                validate_request(raw)
        with patch("jev.cli.load_config") as load:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                cli_main(["advise", "--client", "storage"])
            load.assert_not_called()
            self.assertEqual(json.loads(out.getvalue())["status"], "unavailable")

    def test_status_exposes_only_keychain_reference(self):
        config = {"enabled": True, "operation_clients": ["storage"],
                  "runtime_version": "fixture", "clients": ["codex"],
                  "monthly_budget_eur": None,
                  "secret": {"kind": "keychain", "service": "existing.service",
                             "account": "existing-account"}}
        inventory = {"records": [], "excluded": []}
        with patch("jev.cli.load_config", return_value=(config, {}, inventory)):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                cli_main(["status", "--client", "storage"])
        result = json.loads(out.getvalue())
        self.assertEqual((result["service"], result["account"]),
                         ("existing.service", "existing-account"))
        self.assertNotIn("key", result)

    def test_storage_only_setup_preserves_existing_clients_and_secret_reference(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory).resolve()
            config_dir = home / ".skillry/jev"
            config_dir.mkdir(parents=True)
            existing = {"schema_version": 1, "enabled": True, "clients": ["codex", "claude"],
                        "secret": {"kind": "keychain", "service": "existing.service",
                                   "account": "existing-account"},
                        "projects": {"/example": {"data_classes": ["synthetic"],
                                                   "modes": ["compute"]}},
                        "custom_owner_setting": "keep"}
            (config_dir / "config.json").write_text(json.dumps(existing))
            (config_dir / "installation.json").write_text(json.dumps({"status": "applied", "changes": []}))
            catalog = {"schema_version": 1, "entries": []}
            catalog["version"] = digest(catalog["entries"])
            with patch("jev.install.build_public", return_value=catalog):
                receipt = plan(home, ["storage"], sys.executable, home / "provider-python",
                               None, "unused-new-account", storage_only=True)
            changed = {row["path"]: row for row in receipt["changes"]}
            config_change = changed[str(config_dir / "config.json")]
            import base64
            updated = json.loads(base64.b64decode(config_change["after"]))
            self.assertEqual(updated["clients"], ["codex", "claude"])
            self.assertEqual(updated["operation_clients"], ["storage"])
            self.assertEqual(updated["secret"], existing["secret"])
            self.assertEqual(updated["projects"], existing["projects"])
            self.assertEqual(updated["custom_owner_setting"], "keep")
            self.assertFalse(any("/skills/" in path or "/hooks.json" in path or
                                 "/settings.json" in path for path in changed))

    def test_fresh_storage_only_setup_has_no_phantom_install_targets(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory).resolve()
            catalog = {"schema_version": 1, "entries": []}
            catalog["version"] = digest(catalog["entries"])
            with patch("jev.install.build_public", return_value=catalog):
                receipt = plan(home, ["codex", "claude"], sys.executable,
                               home / "provider-python", None, "owner", storage_only=True)
            import base64
            path = str(home / ".skillry/jev/config.json")
            config = json.loads(base64.b64decode(next(row["after"] for row in receipt["changes"]
                                                  if row["path"] == path)))
            self.assertEqual(config["clients"], [])
            self.assertEqual(config["operation_clients"], ["storage"])
            self.assertTrue(config["enabled"])
            self.assertFalse(any("/skills/" in row["path"] or "/hooks.json" in row["path"]
                                 for row in receipt["changes"]))


if __name__ == "__main__":
    unittest.main()

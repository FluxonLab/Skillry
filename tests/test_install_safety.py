"""Installer safety contracts from the 3.1.0 review (R-07, R-08); no real home writes."""
import importlib.util
import json
import os
import pathlib
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("safety_installer", ROOT / "tools/install.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallSafetyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = pathlib.Path(self.tmp.name).resolve()
        self.repo = self.home / "repo"
        self.skills = []
        for name in ("alpha", "beta"):
            folder = self.repo / "skills" / name
            folder.mkdir(parents=True)
            (folder / "SKILL.md").write_text(f"---\nname: {name}\ndescription: {name}.\n---\nBody.\n")
            self.skills.append((folder, name))
        self.cfg = {**installer.TARGETS["cursor"], "skills": self.home / ".cursor/skills",
                    "agents": self.home / ".cursor/agents"}
        self.patches = [patch.object(installer, "HOME", self.home), patch.object(installer, "REPO", self.repo),
                        patch.object(installer, "MANIFEST_ROOT", self.home / ".skillry/manifests")]
        for item in self.patches:
            item.start()

    def tearDown(self):
        for item in self.patches:
            item.stop()
        self.tmp.cleanup()

    def plan(self):
        return installer.build_target_plan("cursor", self.cfg, self.skills, [], {})

    def manifest_paths(self):
        data = json.loads((self.home / ".skillry/manifests/cursor.json").read_text())
        return sorted(entry["path"] for entry in data["files"])

    def test_hardlinked_destination_is_refused_and_its_other_name_is_untouched(self):
        installer.apply_target_plan(self.plan())
        installed = self.home / ".cursor/skills/alpha/SKILL.md"
        outside = self.home / "elsewhere.md"
        outside.write_bytes(installed.read_bytes())
        installed.unlink()
        os.link(outside, installed)
        (self.repo / "skills/alpha/SKILL.md").write_text("---\nname: alpha\ndescription: alpha.\n---\nNew body.\n")
        with self.assertRaises(installer.SafetyError):
            installer.apply_target_plan(self.plan())
        self.assertNotIn("New body", outside.read_text())

    def test_interrupted_install_records_only_files_that_reached_disk(self):
        real_write = installer.atomic_write_destination
        written = []

        def fail_on_second(destination, content, mode):
            if written:
                raise OSError("disk full")
            real_write(destination, content, mode)
            written.append(destination)

        with patch.object(installer, "atomic_write_destination", side_effect=fail_on_second):
            with self.assertRaises(OSError):
                installer.apply_target_plan(self.plan())
        self.assertEqual(self.manifest_paths(), [os.fspath(written[0])])
        resumed = self.plan()
        self.assertNotIn(written[0], resumed["writes"])
        self.assertTrue(resumed["writes"])
        installer.apply_target_plan(resumed)
        self.assertEqual(self.plan()["writes"], [])


if __name__ == "__main__":
    unittest.main()

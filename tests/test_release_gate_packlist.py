"""Package file-list guard added after 3.2.0 shipped stray local bytecode; no npm call."""
import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("packlist_release_gate", ROOT / "tools/release-gate.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class PacklistTests(unittest.TestCase):
    def test_local_development_artifacts_are_flagged(self):
        junk = [
            "tools/storage/__pycache__/engine.cpython-314.pyc",
            "plugins/backend-and-api/skills/x/scripts/helper.pyc",
            ".pytest_cache/v/cache/nodeids",
            "community/source/.venv/bin/python",
            "npm-debug.log",
            "skillry-3.2.0.tgz",
        ]
        clean = [
            "tools/storage/engine.py",
            "plugins/backend-and-api/skills/16-error-handling-observability/SKILL.md",
            "docs/INSTALL.md",
            "CHANGELOG.md",
            "registry/skill-lock.json",
        ]
        self.assertEqual(gate.packlist_violations(junk + clean), sorted(junk))

    def test_package_files_exclude_python_caches(self):
        excluded = [item for item in gate.PACKAGE_FILES if item.startswith("!")]
        self.assertEqual(excluded, ["!**/__pycache__/**", "!**/*.py[cod]"])


if __name__ == "__main__":
    unittest.main()

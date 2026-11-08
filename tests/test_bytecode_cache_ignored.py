"""Bytecode caches inside a skill never change its checksum and are never installed."""
import importlib.util
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = pathlib.Path(__file__).resolve().parents[1]


def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


installer = load("cache_installer", "tools/install.py")
lockbuilder = load("cache_lockbuilder", "tools/build-lock.py")


class BytecodeCacheTests(unittest.TestCase):
    def test_pycache_and_pyc_do_not_change_the_checksum(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp).resolve()
            skill = repo / "skills" / "alpha"
            (skill / "scripts").mkdir(parents=True)
            (skill / "SKILL.md").write_text("---\nname: alpha\ndescription: alpha.\n---\nBody.\n")
            (skill / "scripts" / "tool.py").write_text("print('hi')\n")
            with patch.object(installer, "REPO", repo):
                before = installer.sha_tree(skill)
                lock_before = lockbuilder.sha_tree(skill)
                (skill / "scripts" / "__pycache__").mkdir()
                (skill / "scripts" / "__pycache__" / "tool.cpython-312.pyc").write_bytes(b"\x00bytecode")
                (skill / "scripts" / "stray.pyc").write_bytes(b"\x00bytecode")
                self.assertEqual(installer.sha_tree(skill), before)
                self.assertEqual(lockbuilder.sha_tree(skill), lock_before)
                names = [p.name for p in installer.source_tree_files(skill)]
                self.assertEqual(sorted(names), ["SKILL.md", "tool.py"])


if __name__ == "__main__":
    unittest.main()

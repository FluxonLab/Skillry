"""skillry storage answers in its JSON error shape on Windows instead of failing on fcntl."""
import contextlib
import io
import json
import os
from pathlib import Path
import runpy
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "tools" / "storage.py"


class StoragePlatformGuardTests(unittest.TestCase):
    def test_windows_gets_a_clear_unsupported_platform_error(self):
        out = io.StringIO()
        with mock.patch.object(os, "name", "nt"), \
                mock.patch.object(sys, "path", [str(CLI.parent)] + sys.path), \
                contextlib.redirect_stdout(out), \
                self.assertRaises(SystemExit) as stop:
            runpy.run_path(str(CLI), run_name="__main__")
        self.assertEqual(stop.exception.code, 1)
        answer = json.loads(out.getvalue())
        self.assertFalse(answer["ok"])
        self.assertEqual(answer["error"]["code"], "unsupported_platform")


if __name__ == "__main__":
    unittest.main()

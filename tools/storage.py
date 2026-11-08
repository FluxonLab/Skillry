#!/usr/bin/env python3
"""Skillry Storage JSON CLI."""
import json
import os
import sys

sys.dont_write_bytecode = True

if os.name == "nt":
    # The engine relies on POSIX file locks (fcntl) and lsof, which Windows does not have.
    # Answer in the CLI's JSON error shape instead of failing on the import.
    from storage import SCHEMA_VERSION

    print(json.dumps({"schema_version": SCHEMA_VERSION, "ok": False, "error": {
        "code": "unsupported_platform",
        "message": "skillry storage runs on macOS and Linux only; "
                   "the installer and the skills also work on Windows"}}))
    raise SystemExit(1)

from storage.engine import main

if __name__ == "__main__":
    raise SystemExit(main())

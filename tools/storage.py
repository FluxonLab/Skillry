#!/usr/bin/env python3
"""Skillry Storage JSON CLI."""
import sys

sys.dont_write_bytecode = True

from storage.engine import main

if __name__ == "__main__":
    raise SystemExit(main())

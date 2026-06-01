#!/usr/bin/env python3
"""Generate per-platform agent instruction files from the canonical CLAUDE.md.

CLAUDE.md is the single source of truth. This writes platform-correct copies so every
supported tool picks up the same engineering guidance:

  AGENTS.md                        OpenAI Codex, GitHub Copilot, Google Antigravity, Cursor … (open standard)
  GEMINI.md                        Gemini CLI + Google Antigravity
  .github/copilot-instructions.md  GitHub Copilot (VS Code)

Dry-run prints a summary; --apply writes the files. CI re-runs with --apply and fails if the
committed copies are stale (same idempotency contract as build-marketplace.py).
"""
from __future__ import annotations
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "CLAUDE.md"
APPLY = "--apply" in sys.argv

GENERATED = "<!-- GENERATED from CLAUDE.md by tools/build-agent-instructions.py — do not edit directly. -->"

# title + intro paragraph for each generated file; the shared body (from the first '## ' on) is appended.
TARGETS = {
    "AGENTS.md": (
        "# AGENTS.md\n\n"
        "Cross-tool agent instructions following the open [AGENTS.md](https://agents.md) standard — "
        "read by OpenAI Codex, GitHub Copilot, Google Antigravity, Cursor, and others. It ships with "
        "**Skillry** and is **generated from `CLAUDE.md`** (the canonical source); edit that file and run "
        "`python3 tools/build-agent-instructions.py --apply`. Project-agnostic: copy it into any repo.\n"
    ),
    "GEMINI.md": (
        "# GEMINI.md\n\n"
        "Project instructions for **Gemini CLI** and **Google Antigravity**. It ships with **Skillry** and "
        "is **generated from `CLAUDE.md`** (the canonical source); edit that file and run "
        "`python3 tools/build-agent-instructions.py --apply`. Project-agnostic: copy it into any repo.\n"
    ),
    ".github/copilot-instructions.md": (
        "# GitHub Copilot — repository instructions\n\n"
        "Instructions for **GitHub Copilot** (VS Code). It ships with **Skillry** and is "
        "**generated from `CLAUDE.md`** (the canonical source); edit that file and run "
        "`python3 tools/build-agent-instructions.py --apply`. Project-agnostic: copy it into any repo.\n"
    ),
}

def body_of(text: str) -> str:
    """Everything from the first top-level section ('## ') onward — the shared content."""
    m = re.search(r"^## ", text, re.M)
    if not m:
        raise SystemExit("CLAUDE.md: could not find a '## ' section to split on.")
    return text[m.start():].rstrip() + "\n"

def main() -> None:
    if not SRC.exists():
        raise SystemExit("CLAUDE.md not found at repo root.")
    body = body_of(SRC.read_text(encoding="utf-8"))
    print(f"{'APPLY' if APPLY else 'DRY-RUN'} — agent instruction files from CLAUDE.md:")
    for rel, header in TARGETS.items():
        out = ROOT / rel
        shared = body
        # files in subdirectories need '../' on links to root-level docs
        if "/" in rel:
            shared = shared.replace("](CLAUDE.md)", "](../CLAUDE.md)").replace("](CONTRIBUTING.md)", "](../CONTRIBUTING.md)")
        content = f"{header}\n{GENERATED}\n\n{shared}"
        print(f"  - {rel}  ({len(content.splitlines())} lines)")
        if APPLY:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(content, encoding="utf-8")
    if not APPLY:
        print("\n(dry-run — nothing written; re-run with --apply)")

if __name__ == "__main__":
    main()

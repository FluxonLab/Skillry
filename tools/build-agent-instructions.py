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

# Assistant identity per target. Each generated file must say which assistant it
# is for, and must carry that assistant's governance block rather than Claude's.
# Before this, every target inherited whatever the canonical source said, so
# AGENTS.md and GEMINI.md both introduced themselves as Claude and shipped
# Claude's governance - which for Codex also meant losing the repository-common
# clauses it can only receive inline.
ASSISTANT_OF = {
    "AGENTS.md": "codex",
    "GEMINI.md": "gemini",
    ".github/copilot-instructions.md": "copilot",
}
CANONICAL_ASSISTANT = "claude"      # CLAUDE.md itself

# Governance blocks are marked per assistant in the canonical source. A target
# receives ONLY its own block; every other assistant's block is stripped.
GOV_BEGIN = "<!-- BEGIN FACTORY MANAGED PROJECT POLICY v2:%s -->"
GOV_END = "<!-- END FACTORY MANAGED PROJECT POLICY v2:%s -->"
GOV_ANY = re.compile(
    r"^<!-- BEGIN FACTORY MANAGED PROJECT POLICY v2:(?P<who>[a-z]+) -->$"
    r".*?"
    r"^<!-- END FACTORY MANAGED PROJECT POLICY v2:(?P=who) -->$\n?",
    re.M | re.S,
)

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

GOV_DIR = ROOT / ".factory" / "governance"


def governance_for(text: str, assistant: str) -> str:
    """The governance block for `assistant`.

    Claude's lives in CLAUDE.md itself, because that file IS Claude's
    instruction file and the Factory merges its managed region there. Every
    other assistant's lives under .factory/governance/, deliberately outside
    CLAUDE.md: Codex's block inlines the repository-common rules it can only
    receive inline, and carrying that inside CLAUDE.md would deliver those rules
    to Claude a second time - it already inherits them from an ancestor file.
    """
    if assistant == CANONICAL_ASSISTANT:
        for m in GOV_ANY.finditer(text):
            if m.group("who") == assistant:
                return m.group(0)
        return ""
    src = GOV_DIR / ("%s.md" % assistant)
    if not src.exists():
        raise SystemExit("missing governance source: %s" % src)
    for m in GOV_ANY.finditer(src.read_text(encoding="utf-8")):
        if m.group("who") == assistant:
            return m.group(0)
    raise SystemExit("%s contains no v2:%s block" % (src, assistant))


def strip_all_governance(text: str) -> str:
    """The shared body with every assistant's governance block removed.

    Stripping ALL of them and re-adding exactly one is deliberate: appending
    without stripping would let a target accumulate two assistants' blocks, and
    stripping only the non-matching ones would depend on source ordering.
    """
    return GOV_ANY.sub("", text)


def main() -> None:
    if not SRC.exists():
        raise SystemExit("CLAUDE.md not found at repo root.")
    source = SRC.read_text(encoding="utf-8")
    body = body_of(source)
    shared_body = strip_all_governance(body)
    print(f"{'APPLY' if APPLY else 'DRY-RUN'} — agent instruction files from CLAUDE.md:")
    for rel, header in TARGETS.items():
        out = ROOT / rel
        assistant = ASSISTANT_OF[rel]
        governance = governance_for(source, assistant)
        shared = shared_body.rstrip() + "\n"
        if governance:
            shared = shared + "\n" + governance.rstrip() + "\n"
        # files in subdirectories need '../' on links to root-level docs
        if "/" in rel:
            shared = shared.replace("](CLAUDE.md)", "](../CLAUDE.md)").replace("](CONTRIBUTING.md)", "](../CONTRIBUTING.md)")
        content = f"{header}\n{GENERATED}\n\n{shared}"
        print(f"  - {rel}  ({len(content.splitlines())} lines, assistant={assistant}, "
              f"governance={'yes' if governance else 'MISSING'})")
        if APPLY:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(content, encoding="utf-8")
    if not APPLY:
        print("\n(dry-run — nothing written; re-run with --apply)")

if __name__ == "__main__":
    main()

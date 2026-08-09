#!/usr/bin/env python3
"""Generated agent-instruction family contract tests.

These exist because the previous check on this family was a marker count, and a
marker count reported a correct family while `AGENTS.md` had silently lost every
repository-common rule and every generated file introduced itself as Claude.

Counting markers proves a block exists. It does not prove the block says
anything, or says the right thing, or says it to the right assistant. Each test
below asserts one of those instead.

Standard library only, Python 3.9 compatible. No network, no installs.
"""

from __future__ import annotations

import hashlib
import pathlib
import re
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "tools" / "build-agent-instructions.py"

GOV = re.compile(
    r"^<!-- BEGIN FACTORY MANAGED PROJECT POLICY v2:(?P<who>[a-z]+) -->$.*?"
    r"^<!-- END FACTORY MANAGED PROJECT POLICY v2:(?P=who) -->$\n?",
    re.M | re.S,
)

FAMILY = {
    "CLAUDE.md": ("claude", "Claude"),
    "AGENTS.md": ("codex", "Codex"),
    "GEMINI.md": ("gemini", "Gemini"),
    ".github/copilot-instructions.md": ("copilot", "GitHub Copilot"),
}

# Repository-common clauses. Codex begins discovery at the Git repository root
# and never reads files above it, so these can only reach it inline. Claude
# reaches the same rules through an ancestor file, so a copy in CLAUDE.md would
# be a second delivery of one layer.
REPO_COMMON_CLAUSES = (
    "Discover the framework, package manager and scripts from this repository's own manifests",
    "Use the package manager the lockfile implies",
    "Never print repository secret material",
    "Never run a production migration, deployment or publish as a side effect",
    "Modify only files the task names",
    "State which build and test commands were actually run",
    "A dirty working tree is unfinished work",
    "Distinguish generated artifacts from source",
)

PROJECT_CLAUSE_MARKERS = ("## Project facts", "## Prohibited", "## Success criteria")


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def governance_blocks(text):
    return {m.group("who"): m.group(0) for m in GOV.finditer(text)}


def shared_body(rel):
    """The body with every governance block removed and link depth normalised."""
    text = read(rel)
    match = re.search(r"^## ", text, re.M)
    body = text[match.start():] if match else text
    body = GOV.sub("", body)
    body = body.replace("](../CLAUDE.md)", "](CLAUDE.md)")
    body = body.replace("](../CONTRIBUTING.md)", "](CONTRIBUTING.md)")
    return re.sub(r"\n{2,}", "\n\n", body).strip()


def shared_digest(rel):
    return hashlib.sha256(shared_body(rel).encode("utf-8")).hexdigest()


def regenerate():
    return subprocess.run([sys.executable, str(GENERATOR), "--apply"],
                          cwd=str(ROOT), capture_output=True, text=True)


class AssistantIdentity(unittest.TestCase):
    def test_every_file_identifies_its_own_assistant(self):
        for rel, (_who, title) in FAMILY.items():
            line = next(l for l in read(rel).splitlines()
                        if l.startswith("# skillry - project policy"))
            self.assertIn("(%s)" % title, line, "%s identifies as the wrong assistant" % rel)

    def test_no_two_files_claim_the_same_identity(self):
        titles = []
        for rel in FAMILY:
            line = next(l for l in read(rel).splitlines()
                        if l.startswith("# skillry - project policy"))
            titles.append(line)
        self.assertEqual(len(set(titles)), len(FAMILY),
                         "generated files share an identity line")

    def test_each_file_carries_only_its_own_governance_block(self):
        for rel, (who, _title) in FAMILY.items():
            self.assertEqual(sorted(governance_blocks(read(rel))), [who],
                             "%s carries another assistant's block" % rel)

    def test_no_generated_file_claims_claude_or_codex_discovery_behaviour(self):
        # GEMINI.md and Copilot must not assert how Claude or Codex find their
        # instructions - nothing here has measured that for those tools.
        for rel in ("GEMINI.md", ".github/copilot-instructions.md"):
            block = governance_blocks(read(rel))[FAMILY[rel][0]]
            for claim in ("ancestor", "Git repository root", "traversal"):
                self.assertNotIn(claim, block,
                                 "%s makes an unsupported discovery claim" % rel)


class RepositoryCommonPlacement(unittest.TestCase):
    def test_codex_receives_every_repository_common_clause(self):
        text = read("AGENTS.md")
        for clause in REPO_COMMON_CLAUSES:
            self.assertIn(clause, text, "AGENTS.md lost a repository-common clause")

    def test_claude_does_not_receive_a_duplicate_repository_common(self):
        text = read("CLAUDE.md")
        for clause in REPO_COMMON_CLAUSES:
            self.assertNotIn(clause, text,
                             "CLAUDE.md duplicates a clause Claude inherits from an ancestor")

    def test_gemini_and_copilot_do_not_receive_repository_common(self):
        for rel in ("GEMINI.md", ".github/copilot-instructions.md"):
            text = read(rel)
            for clause in REPO_COMMON_CLAUSES:
                self.assertNotIn(clause, text, "%s carries repository-common" % rel)

    def test_repository_common_survives_regeneration(self):
        # The exact regression that shipped: regenerating deleted all eight.
        before = sum(c in read("AGENTS.md") for c in REPO_COMMON_CLAUSES)
        self.assertEqual(before, len(REPO_COMMON_CLAUSES))
        self.assertEqual(regenerate().returncode, 0)
        after = sum(c in read("AGENTS.md") for c in REPO_COMMON_CLAUSES)
        self.assertEqual(after, len(REPO_COMMON_CLAUSES),
                         "regeneration dropped repository-common clauses")


class MarkerCountIsNotCoverage(unittest.TestCase):
    def test_the_old_metric_would_pass_an_empty_block(self):
        # Demonstrates why this file exists. An empty governance block has the
        # same marker count as a full one.
        empty = ("<!-- BEGIN FACTORY MANAGED PROJECT POLICY v2:codex -->\n"
                 "<!-- END FACTORY MANAGED PROJECT POLICY v2:codex -->\n")
        self.assertEqual(len(governance_blocks(empty)), 1)
        for clause in REPO_COMMON_CLAUSES:
            self.assertNotIn(clause, empty)

    def test_clause_presence_is_asserted_by_content(self):
        block = governance_blocks(read("AGENTS.md"))["codex"]
        for clause in REPO_COMMON_CLAUSES:
            self.assertIn(clause, block)
        for marker in PROJECT_CLAUSE_MARKERS:
            self.assertIn(marker, read("AGENTS.md"))


class SharedBodyParity(unittest.TestCase):
    def test_all_four_share_one_body(self):
        digests = {rel: shared_digest(rel) for rel in FAMILY}
        self.assertEqual(len(set(digests.values())), 1,
                         "shared body diverged: %s" % digests)

    def test_assistant_specific_differences_do_not_break_parity(self):
        # POSITIVE CONTROL: the files genuinely DO differ - identity lines and
        # governance blocks - yet parity holds. If this passed trivially it
        # would mean the files were identical and parity proved nothing.
        self.assertNotEqual(read("AGENTS.md"), read("GEMINI.md"))
        self.assertEqual(shared_digest("AGENTS.md"), shared_digest("GEMINI.md"))

    def test_a_real_shared_body_difference_is_detected(self):
        # NEGATIVE CONTROL for the parity check itself. The mutation must land
        # in the SHARED body - editing a heading inside a governance block would
        # be stripped before hashing and prove nothing.
        original = read("GEMINI.md")
        try:
            (ROOT / "GEMINI.md").write_text(
                original.replace("## Prime directives", "## Prime directives (edited)"),
                encoding="utf-8")
            self.assertNotEqual(shared_digest("GEMINI.md"), shared_digest("AGENTS.md"))
        finally:
            (ROOT / "GEMINI.md").write_text(original, encoding="utf-8")


class GeneratorContract(unittest.TestCase):
    def test_generator_is_idempotent_five_times(self):
        first = None
        for _ in range(5):
            self.assertEqual(regenerate().returncode, 0)
            digest = {rel: hashlib.sha256(read(rel).encode()).hexdigest() for rel in FAMILY}
            if first is None:
                first = digest
            self.assertEqual(digest, first, "generator is not idempotent")

    def test_generator_reports_the_assistant_and_governance_for_each_target(self):
        out = regenerate().stdout
        for rel, (who, _t) in FAMILY.items():
            if rel == "CLAUDE.md":
                continue                      # the source, not a target
            self.assertIn("assistant=%s" % who, out)
        self.assertNotIn("governance=MISSING", out)

    def test_a_missing_governance_source_fails_closed(self):
        src = ROOT / ".factory" / "governance" / "gemini.md"
        original = src.read_text(encoding="utf-8")
        try:
            src.unlink()
            result = regenerate()
            self.assertNotEqual(result.returncode, 0,
                                "a missing governance source must fail, not emit a blank block")
        finally:
            src.write_text(original, encoding="utf-8")
            self.assertEqual(regenerate().returncode, 0)

    def test_committed_files_match_a_fresh_generator_run(self):
        # The contract Skillry's CI enforces, asserted here too so it fails
        # locally before it fails remotely.
        before = {rel: read(rel) for rel in FAMILY}
        self.assertEqual(regenerate().returncode, 0)
        for rel in FAMILY:
            self.assertEqual(read(rel), before[rel], "%s is stale" % rel)


if __name__ == "__main__":
    unittest.main()

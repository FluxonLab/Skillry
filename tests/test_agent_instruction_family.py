#!/usr/bin/env python3
"""Repository instruction-adapter contract; all mutation tests use temp fixtures."""
from __future__ import annotations

import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "tools/build-agent-instructions.py"
CANONICAL = ("AGENTS.md", "CLAUDE.md")
ADAPTERS = ("GEMINI.md", ".github/copilot-instructions.md")


def run(root, *args):
    return subprocess.run(
        [sys.executable, str(root / "tools/build-agent-instructions.py"), *args],
        cwd=root, capture_output=True, text=True,
    )


def snapshot(root):
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in root.rglob("*") if p.is_file()}


class RepositoryContract(unittest.TestCase):
    def test_canonical_contributor_bodies_are_equivalent(self):
        bodies = []
        for name in CANONICAL:
            text = (ROOT / name).read_text()
            bodies.append(text[re.search(r"^## ", text, re.M).start():].strip())
            self.assertNotIn("<!-- GENERATED", text)
        self.assertEqual(*bodies)

    def test_committed_adapters_are_current_without_writes(self):
        paths = (*CANONICAL, *ADAPTERS)
        before = {p: (ROOT / p).read_bytes() for p in paths}
        result = run(ROOT, "--check")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(before, {p: (ROOT / p).read_bytes() for p in paths})

    def test_adapters_have_correct_identity_and_resolvable_policy_links(self):
        for path, identity, prefix in (
            ("GEMINI.md", "Gemini CLI and Google Antigravity", ""),
            (".github/copilot-instructions.md", "GitHub Copilot", "../"),
        ):
            text = (ROOT / path).read_text()
            self.assertIn(identity, text.splitlines()[0])
            for canonical in CANONICAL:
                self.assertIn(f"[{canonical}]({prefix}{canonical})", text)
                self.assertTrue(((ROOT / path).parent / (prefix + canonical)).is_file())
            self.assertIn("not\nportable installer payload", text)
            self.assertNotIn("FACTORY MANAGED", text)
            self.assertNotIn("## Operating model", text)
            self.assertLess(len(text.splitlines()), 20)

    def test_ci_checks_adapters_and_retains_jev_tests(self):
        text = (ROOT / ".github/workflows/validate.yml").read_text()
        self.assertIn("python3 tools/build-agent-instructions.py --check", text)
        self.assertIn("python3 tests/test_agent_instruction_family.py", text)
        self.assertIn("python3 -m unittest discover -s tests -p 'test_jev*.py'", text)
        self.assertRegex(text, r"pull_request:\n\s+branches: \[main\]")
        self.assertRegex(text, r"permissions:\n\s+contents: read")
        self.assertNotIn("pull_request_target", text)
        self.assertNotIn("continue-on-error", text)
        self.assertNotIn("--instructions", text)


class GeneratorFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="skillry-adapters-")
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        (self.root / "tools").mkdir()
        shutil.copyfile(GENERATOR, self.root / "tools/build-agent-instructions.py")
        for name in CANONICAL:
            shutil.copyfile(ROOT / name, self.root / name)
        # Historical candidates must never become active through regeneration.
        legacy = self.root / ".factory/governance/gemini.md"
        legacy.parent.mkdir(parents=True)
        legacy.write_text("Historical candidate — not active adapter input.\n")

    def test_dry_run_does_not_write(self):
        before = snapshot(self.root)
        result = run(self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(snapshot(self.root), before)

    def test_apply_preserves_canonical_and_legacy_sources_and_is_idempotent(self):
        before = snapshot(self.root)
        result = run(self.root, "--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        after = snapshot(self.root)
        self.assertEqual(set(after) - set(before), set(ADAPTERS))
        self.assertEqual(before, {p: after[p] for p in before})
        self.assertEqual(run(self.root, "--apply").returncode, 0)
        self.assertEqual(snapshot(self.root), after)
        self.assertEqual(run(self.root, "--check").returncode, 0)

    def test_missing_or_stale_adapters_fail_check_without_writes(self):
        before = snapshot(self.root)
        self.assertNotEqual(run(self.root, "--check").returncode, 0)
        self.assertEqual(snapshot(self.root), before)
        self.assertEqual(run(self.root, "--apply").returncode, 0)
        (self.root / "GEMINI.md").write_text("stale adapter\n")
        before = snapshot(self.root)
        self.assertNotEqual(run(self.root, "--check").returncode, 0)
        self.assertEqual(snapshot(self.root), before)

    def test_canonical_drift_fails_before_any_writes(self):
        with (self.root / "CLAUDE.md").open("a") as output:
            output.write("\nAdditional conflicting rule.\n")
        before = snapshot(self.root)
        result = run(self.root, "--apply")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("contributor rules differ", result.stderr)
        self.assertEqual(snapshot(self.root), before)

    def test_missing_canonical_file_fails_before_any_writes(self):
        (self.root / "CLAUDE.md").unlink()
        before = snapshot(self.root)
        self.assertNotEqual(run(self.root, "--apply").returncode, 0)
        self.assertEqual(snapshot(self.root), before)

    def test_unknown_and_conflicting_modes_are_rejected(self):
        for args in (("--output", "/tmp/unrelated"), ("--apply", "--check")):
            before = snapshot(self.root)
            self.assertEqual(run(self.root, *args).returncode, 2)
            self.assertEqual(snapshot(self.root), before)


if __name__ == "__main__":
    unittest.main()

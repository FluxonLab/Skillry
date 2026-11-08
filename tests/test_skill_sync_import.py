"""Tests for tools/skill-sync.py: whole-package import, link checks and licenses.

No network: every source is a temporary local git repository.
"""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "skill-sync.py"
LICENSES = ROOT / "tools" / "licenses"

_spec = importlib.util.spec_from_file_location("skill_sync", TOOL)
skill_sync = importlib.util.module_from_spec(_spec)
sys.modules["skill_sync"] = skill_sync
_spec.loader.exec_module(skill_sync)

GIT_ENV = {
    "GIT_AUTHOR_NAME": "Test Author",
    "GIT_AUTHOR_EMAIL": "author@example.invalid",
    "GIT_COMMITTER_NAME": "Test Author",
    "GIT_COMMITTER_EMAIL": "author@example.invalid",
}

SKILL_MD = """---
name: demo
description: Demo skill used by the tests.
---
# demo

Read the [guide](references/guide.md) and look at `scripts/helper.py`.
"""

HELPER_PY = """import os
import subprocess

# If this ever runs, it leaves a marker behind.
open(os.path.join(os.path.dirname(__file__), "EXECUTED"), "w").close()
subprocess.run(["true"])
"""

RUN_SH = """#!/bin/sh
touch "$(dirname "$0")/EXECUTED"
curl https://example.invalid/install.sh
"""


def canonical(spdx_id: str) -> str:
    return (LICENSES / f"{spdx_id}.txt").read_text(encoding="utf-8")


def mit_with_copyright() -> str:
    return canonical("MIT").replace(
        "Copyright (c) <year> <copyright holders>",
        "Copyright (c) 2024 Example Author",
    )


def mit_with_restriction() -> str:
    text = mit_with_copyright()
    changed = text.replace(
        "following conditions:",
        "following conditions: The Software may not be used for commercial purposes.",
        1,
    )
    assert changed != text
    return changed


def sha256_of(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SkillSyncTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="skillsync-test-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.community = self.tmp / "community"
        self.community.mkdir()
        patcher = mock.patch.object(skill_sync, "COMMUNITY", self.community)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.repo_count = 0

    def git(self, cwd: pathlib.Path, *args: str) -> str:
        result = subprocess.run(
            ["git", "-c", "commit.gpgsign=false", *args],
            cwd=str(cwd),
            env=dict(os.environ, **GIT_ENV),
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def make_repo(self, files, executable=(), symlinks=None) -> str:
        """Create a committed git repository and return its path as the URL."""
        self.repo_count += 1
        repo = self.tmp / f"src{self.repo_count}" / "repo"
        repo.mkdir(parents=True)
        self.git(repo, "init", "-q")
        for rel, content in files.items():
            path = repo / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(content, str):
                content = content.encode("utf-8")
            path.write_bytes(content)
        for rel in executable:
            os.chmod(repo / rel, 0o755)
        for rel, target in (symlinks or {}).items():
            path = repo / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            os.symlink(target, path)
        self.git(repo, "add", "-A")
        self.git(repo, "commit", "-q", "-m", "init")
        self.head = self.git(repo, "rev-parse", "HEAD")
        return str(repo)

    def run_import(self, url, apply=True, accept=()):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            skill_sync.cmd_import(url, apply, list(accept))
        return buffer.getvalue()

    def assert_refused_license(self, url, accept=()):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            with self.assertRaises(SystemExit) as caught:
                skill_sync.cmd_import(url, True, list(accept))
        self.assertEqual(caught.exception.code, 3)
        self.assertEqual(list(self.community.iterdir()), [])
        return buffer.getvalue()

    def staged(self, url) -> pathlib.Path:
        return self.community / skill_sync.slug_from_url(url)

    def demo_files(self, license_text=None, extra=None):
        files = {
            "skills/demo/SKILL.md": SKILL_MD,
            "skills/demo/references/guide.md": "# Guide\n\nNothing to see.\n",
            "skills/demo/scripts/helper.py": HELPER_PY,
        }
        if license_text is not None:
            files["LICENSE"] = license_text
        files.update(extra or {})
        return files


class ImportWholePackageTests(SkillSyncTestCase):
    def test_full_package_is_copied_with_manifest(self):
        files = self.demo_files(
            mit_with_copyright(),
            {
                "skills/demo/scripts/run.sh": RUN_SH,
                "skills/demo/assets/logo.bin": bytes(range(256)),
                "skills/demo/.DS_Store": b"junk",
                "skills/demo/scripts/__pycache__/helper.cpython-39.pyc": b"\x00pyc",
            },
        )
        url = self.make_repo(files, executable=["skills/demo/scripts/run.sh"])
        self.run_import(url, apply=True)

        dest = self.staged(url)
        demo = dest / "skills" / "demo"
        for rel, content in files.items():
            if not rel.startswith("skills/demo/"):
                continue
            inner = rel[len("skills/demo/") :]
            if inner in (".DS_Store",) or "__pycache__" in inner:
                self.assertFalse((demo / inner).exists(), inner)
                continue
            target = demo / inner
            self.assertTrue(target.is_file(), inner)
            data = content.encode("utf-8") if isinstance(content, str) else content
            if inner == "SKILL.md":
                expected = skill_sync.normalize_skill(SKILL_MD, "demo", url, "MIT")
                self.assertEqual(target.read_text(encoding="utf-8"), expected)
            else:
                self.assertEqual(target.read_bytes(), data, inner)

        self.assertEqual((dest / "LICENSE").read_text(), mit_with_copyright())

        manifest = json.loads((dest / "IMPORT-MANIFEST.json").read_text())
        self.assertEqual(manifest["schema_version"], 1)
        self.assertEqual(manifest["source_url"], url)
        self.assertEqual(manifest["source_commit"], self.head)
        self.assertRegex(manifest["imported_on"], r"^\d{4}-\d{2}-\d{2}$")
        self.assertEqual(manifest["license"]["candidate"], "MIT")
        self.assertEqual(manifest["license"]["status"], "recognized")
        self.assertEqual(manifest["license"]["file"], "LICENSE")
        self.assertEqual(manifest["conflicts"], [])

        self.assertEqual([s["name"] for s in manifest["skills"]], ["demo"])
        skill = manifest["skills"][0]
        self.assertEqual(skill["license"]["candidate"], "MIT")
        entries = {entry["path"]: entry for entry in skill["files"]}
        self.assertEqual(
            [entry["path"] for entry in skill["files"]], sorted(entries)
        )
        self.assertEqual(
            sorted(entries),
            [
                "SKILL.md",
                "assets/logo.bin",
                "references/guide.md",
                "scripts/helper.py",
                "scripts/run.sh",
            ],
        )
        kinds = {path: entry["kind"] for path, entry in entries.items()}
        self.assertEqual(
            kinds,
            {
                "SKILL.md": "skill",
                "assets/logo.bin": "asset",
                "references/guide.md": "reference",
                "scripts/helper.py": "script",
                "scripts/run.sh": "script",
            },
        )
        self.assertTrue(entries["scripts/run.sh"]["executable"])
        self.assertFalse(entries["scripts/helper.py"]["executable"])
        for path, entry in entries.items():
            written = demo / path
            self.assertEqual(entry["sha256"], sha256_of(written), path)
            self.assertEqual(entry["bytes"], written.stat().st_size, path)

        review = (dest / "REVIEW.md").read_text()
        self.assertIn("## Scripts that need review before anyone runs them", review)
        self.assertIn("scripts/helper.py", review)
        self.assertIn("scripts/run.sh", review)
        self.assertIn("shell-exec", review)
        self.assertIn("network", review)

        # Nothing was executed, imported or made executable.
        self.assertEqual(list(self.community.rglob("EXECUTED")), [])
        self.assertEqual(list(self.community.rglob("__pycache__")), [])
        self.assertFalse(os.access(demo / "scripts" / "run.sh", os.X_OK))

    def test_dry_run_writes_nothing(self):
        url = self.make_repo(self.demo_files(mit_with_copyright()))
        output = self.run_import(url, apply=False)
        self.assertIn("DRY-RUN", output)
        self.assertEqual(list(self.community.iterdir()), [])

    def test_missing_link_target_is_refused(self):
        files = self.demo_files(mit_with_copyright())
        files["skills/demo/SKILL.md"] = SKILL_MD.replace(
            "references/guide.md", "references/missing.md"
        )
        url = self.make_repo(files)
        with self.assertRaises(skill_sync.SafetyError) as caught:
            self.run_import(url, apply=True)
        message = str(caught.exception)
        self.assertIn("references/missing.md", message)
        self.assertIn("missing link target", message)
        self.assertIn("demo/SKILL.md", message)
        self.assertEqual(list(self.community.iterdir()), [])

    def test_missing_link_is_refused_in_dry_run_too(self):
        files = self.demo_files(mit_with_copyright())
        files["skills/demo/SKILL.md"] = SKILL_MD.replace(
            "references/guide.md", "references/missing.md"
        )
        url = self.make_repo(files)
        with self.assertRaises(skill_sync.SafetyError):
            self.run_import(url, apply=False)

    def test_link_escaping_the_skill_is_refused(self):
        files = self.demo_files(mit_with_copyright())
        files["outside.md"] = "# Outside\n"
        files["skills/demo/SKILL.md"] = SKILL_MD + "\nSee [out](../../outside.md).\n"
        url = self.make_repo(files)
        with self.assertRaises(skill_sync.SafetyError) as caught:
            self.run_import(url, apply=True)
        self.assertIn("escapes", str(caught.exception))
        self.assertIn("../../outside.md", str(caught.exception))
        self.assertEqual(list(self.community.iterdir()), [])

    def test_urls_anchors_and_titles_are_not_errors(self):
        files = self.demo_files(mit_with_copyright())
        files["skills/demo/SKILL.md"] = SKILL_MD + (
            "\n[web](https://example.invalid/x) [mail](mailto:a@example.invalid)"
            ' [top](#demo) [g](references/guide.md#part "Title")'
            " [q](references/guide.md?x=1)\n"
        )
        url = self.make_repo(files)
        self.run_import(url, apply=True)
        self.assertTrue((self.staged(url) / "skills" / "demo" / "SKILL.md").is_file())

    def test_example_links_in_code_fences_and_folder_links_are_fine(self):
        files = self.demo_files(mit_with_copyright())
        files["skills/demo/SKILL.md"] = SKILL_MD + (
            "\nBrowse [the references](references/).\n\n"
            "```markdown\nA README may say [setup](docs/setup.md).\n```\n"
        )
        url = self.make_repo(files)
        self.run_import(url, apply=True)
        self.assertTrue((self.staged(url) / "skills" / "demo" / "SKILL.md").is_file())

    def test_a_missing_script_named_inside_a_code_fence_is_still_refused(self):
        files = self.demo_files(mit_with_copyright())
        files["skills/demo/SKILL.md"] = SKILL_MD + "\n```bash\npython scripts/absent.py\n```\n"
        url = self.make_repo(files)
        with self.assertRaises(skill_sync.SafetyError) as caught:
            self.run_import(url, apply=False)
        self.assertIn("scripts/absent.py", str(caught.exception))

    def test_symlink_inside_skill_is_refused(self):
        files = self.demo_files(mit_with_copyright())
        url = self.make_repo(
            files, symlinks={"skills/demo/references/alias.md": "guide.md"}
        )
        with self.assertRaises(skill_sync.SafetyError) as caught:
            self.run_import(url, apply=True)
        self.assertIn("symlink", str(caught.exception))
        self.assertEqual(list(self.community.iterdir()), [])

    def test_file_over_one_mib_is_refused(self):
        files = self.demo_files(
            mit_with_copyright(),
            {"skills/demo/assets/big.bin": b"x" * (1024 * 1024 + 1)},
        )
        url = self.make_repo(files)
        with self.assertRaises(skill_sync.SafetyError) as caught:
            self.run_import(url, apply=True)
        self.assertIn("1 MiB", str(caught.exception))
        self.assertEqual(list(self.community.iterdir()), [])


class LicenseTests(SkillSyncTestCase):
    def write(self, name: str, text: str) -> pathlib.Path:
        path = self.tmp / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_restricted_mit_needs_review_and_can_be_accepted(self):
        text = mit_with_restriction()
        url = self.make_repo(self.demo_files(text))

        info = skill_sync.classify_license(self.write("LICENSE", text))
        self.assertEqual(info["status"], "needs-review")
        self.assertEqual(info["candidate"], "MIT-like")
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        self.assertEqual(info["sha256"], digest)

        output = self.assert_refused_license(url)
        self.assertIn(digest, output)
        self.assertIn("--accept-license", output)

        # A hash that does not belong to the license file does not help.
        self.assert_refused_license(url, accept=["0" * 64])

        self.run_import(url, apply=True, accept=[digest])
        manifest = json.loads(
            (self.staged(url) / "IMPORT-MANIFEST.json").read_text()
        )
        self.assertEqual(manifest["license"]["status"], "needs-review")
        self.assertEqual(manifest["license"]["decision"], "accepted-by-reviewer")
        self.assertEqual(
            manifest["skills"][0]["license"]["decision"], "accepted-by-reviewer"
        )
        self.assertEqual(
            [item["sha256"] for item in manifest["accepted_licenses"]], [digest]
        )
        self.assertEqual(
            manifest["accepted_licenses"][0]["decision"], "accepted-by-reviewer"
        )

    def test_unknown_license_is_never_accepted(self):
        text = "All rights reserved. Do not copy.\n"
        url = self.make_repo(self.demo_files(text))
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        self.assert_refused_license(url)
        self.assert_refused_license(url, accept=[digest])

    def test_missing_license_is_refused(self):
        url = self.make_repo(self.demo_files(None))
        self.assert_refused_license(url)

    def test_skill_license_conflicting_with_root(self):
        other = mit_with_restriction()
        files = self.demo_files(
            mit_with_copyright(), {"skills/demo/LICENSE": other}
        )
        url = self.make_repo(files)

        clone_root = skill_sync.clone(url)
        self.addCleanup(shutil.rmtree, clone_root, ignore_errors=True)
        report = skill_sync.license_report(
            clone_root, skill_sync.find_skills(clone_root)
        )
        self.assertEqual(report["root"]["status"], "recognized")
        self.assertEqual(report["root"]["candidate"], "MIT")
        self.assertEqual(
            [info["file"] for info in report["files"]],
            ["LICENSE", "skills/demo/LICENSE"],
        )
        self.assertEqual(
            report["skills"]["skills/demo"]["file"], "skills/demo/LICENSE"
        )
        self.assertEqual(len(report["conflicts"]), 1)
        self.assertEqual(report["conflicts"][0]["skill"], "skills/demo")
        self.assertEqual(report["conflicts"][0]["file"], "skills/demo/LICENSE")

        digest = hashlib.sha256(other.encode("utf-8")).hexdigest()
        root_digest = hashlib.sha256(mit_with_copyright().encode("utf-8")).hexdigest()
        output = self.assert_refused_license(url)
        self.assertIn("skills/demo/LICENSE", output)
        self.assertIn(digest, output)
        # Accepting the (already recognized) root license does not accept the other.
        self.assert_refused_license(url, accept=[root_digest])

        self.run_import(url, apply=True, accept=[digest])
        dest = self.staged(url)
        review = (dest / "REVIEW.md").read_text()
        self.assertIn("License conflicts", review)
        self.assertIn("skills/demo/LICENSE", review)
        manifest = json.loads((dest / "IMPORT-MANIFEST.json").read_text())
        self.assertEqual(len(manifest["conflicts"]), 1)
        self.assertEqual(manifest["conflicts"][0]["file"], "skills/demo/LICENSE")
        self.assertEqual(
            manifest["skills"][0]["license"]["decision"], "accepted-by-reviewer"
        )
        # The copied LICENSE stays the root license text.
        self.assertEqual((dest / "LICENSE").read_text(), mit_with_copyright())

    def test_nearest_license_in_parent_directory_is_effective(self):
        files = self.demo_files(
            mit_with_copyright(), {"skills/LICENSE": canonical("ISC")}
        )
        url = self.make_repo(files)
        clone_root = skill_sync.clone(url)
        self.addCleanup(shutil.rmtree, clone_root, ignore_errors=True)
        report = skill_sync.license_report(
            clone_root, skill_sync.find_skills(clone_root)
        )
        effective = report["skills"]["skills/demo"]
        self.assertEqual(effective["file"], "skills/LICENSE")
        self.assertEqual(effective["candidate"], "ISC")
        self.assertEqual(len(report["conflicts"]), 1)

    def test_apache_without_appendix_is_recognized(self):
        text = canonical("Apache-2.0")
        marker = "appendix: how to apply the apache license"
        cut = text.lower().index(marker)
        info = skill_sync.classify_license(self.write("LICENSE", text[:cut]))
        self.assertEqual(info["status"], "recognized")
        self.assertEqual(info["candidate"], "Apache-2.0")
        full = skill_sync.classify_license(self.write("LICENSE.txt", text))
        self.assertEqual(full["status"], "recognized")
        self.assertEqual(full["candidate"], "Apache-2.0")

    def test_appendix_does_not_hide_a_modified_mit(self):
        text = (
            mit_with_restriction()
            + "\nAPPENDIX: How to apply the Apache License\nignored\n"
        )
        info = skill_sync.classify_license(self.write("LICENSE", text))
        self.assertEqual(info["status"], "needs-review")

    def test_canonical_texts_and_rewrapped_mit_are_recognized(self):
        for spdx_id in skill_sync.SPDX_IDS:
            info = skill_sync.classify_license(
                self.write(f"{spdx_id}.txt", canonical(spdx_id))
            )
            self.assertEqual(info["candidate"], spdx_id)
            self.assertEqual(info["status"], "recognized")
        wrapped = mit_with_copyright().replace(
            "THE AUTHORS OR COPYRIGHT HOLDERS", "THE AUTHORS OR\nCOPYRIGHT HOLDERS"
        )
        info = skill_sync.classify_license(self.write("LICENSE", wrapped))
        self.assertEqual(info["status"], "recognized")
        self.assertEqual(info["candidate"], "MIT")

    def test_common_title_and_rights_lines_do_not_block_recognition(self):
        body = mit_with_copyright().split("\n", 1)[1]  # without the "MIT License" title
        for title in ("", "The MIT License (MIT)\n\n"):
            info = skill_sync.classify_license(self.write("LICENSE", title + body))
            self.assertEqual((info["candidate"], info["status"]), ("MIT", "recognized"))
        bsd = canonical("BSD-3-Clause").replace(
            "Copyright (c) <year> <owner>.", "BSD 3-Clause License\n\nCopyright (c) 2026, Example\nAll rights reserved.")
        info = skill_sync.classify_license(self.write("LICENSE", bsd))
        self.assertEqual((info["candidate"], info["status"]), ("BSD-3-Clause", "recognized"))

    def test_a_condition_added_to_the_copyright_line_needs_review(self):
        text = mit_with_copyright().replace(
            "Copyright (c) 2024 Example Author",
            "Copyright (c) 2024 Example Author. Commercial redistribution is prohibited.")
        info = skill_sync.classify_license(self.write("LICENSE", text))
        self.assertEqual(info["status"], "needs-review")
        text = mit_with_copyright().replace(
            "Copyright (c) 2024 Example Author", "Copyright (c) 2024 Example Author, not for resale")
        self.assertEqual(skill_sync.classify_license(self.write("LICENSE", text))["status"], "needs-review")

    def test_a_condition_in_angle_brackets_is_not_removed(self):
        text = mit_with_copyright().replace(
            "Copyright (c) 2024 Example Author",
            "Copyright (c) 2024 Example Author\n\n<commercial redistribution is prohibited>")
        self.assertEqual(skill_sync.classify_license(self.write("LICENSE", text))["status"], "needs-review")

    def test_an_unknown_license_inside_a_skill_folder_blocks_the_import(self):
        url = self.make_repo(self.demo_files(mit_with_copyright(), {
            "skills/demo/assets/LICENSE": "These assets are proprietary. All use requires written consent.\n",
            "skills/demo/assets/logo.txt": "logo\n"}))
        output = self.assert_refused_license(url)
        self.assertIn("skills/demo/assets/LICENSE", output)
        self.assertIn("unknown", output)

    def test_a_reviewed_license_inside_a_skill_folder_can_be_accepted(self):
        inner = mit_with_restriction()
        url = self.make_repo(self.demo_files(mit_with_copyright(), {
            "skills/demo/assets/LICENSE": inner, "skills/demo/assets/logo.txt": "logo\n"}))
        self.assert_refused_license(url)
        digest = hashlib.sha256(inner.encode("utf-8")).hexdigest()
        self.run_import(url, apply=True, accept=[digest])
        self.assertTrue((self.staged(url) / "skills" / "demo" / "assets" / "logo.txt").is_file())

    def test_a_license_in_an_unrelated_folder_does_not_block(self):
        url = self.make_repo(self.demo_files(mit_with_copyright(), {
            "website/LICENSE": "All rights reserved. Not for reuse.\n", "website/index.html": "<p>hi</p>\n"}))
        self.run_import(url, apply=True)
        self.assertTrue((self.staged(url) / "skills" / "demo" / "SKILL.md").is_file())

    def test_family_guesses_and_unknown(self):
        cases = {
            "Apache License\nSome other terms.\n": "Apache-like",
            "Redistribution and use in source and binary forms are fine.\n": "BSD-like",
            "Permission to use, copy, modify, and/or distribute is granted.\n": "ISC-like",
        }
        for text, family in cases.items():
            info = skill_sync.classify_license(self.write("LICENSE", text))
            self.assertEqual((info["candidate"], info["status"]), (family, "needs-review"))
        info = skill_sync.classify_license(self.write("LICENSE", "Proprietary.\n"))
        self.assertEqual((info["candidate"], info["status"]), ("unknown", "unknown"))
        info = skill_sync.classify_license(None)
        self.assertEqual((info["candidate"], info["status"]), ("unknown", "unknown"))

    def test_discover_output(self):
        url = self.make_repo(self.demo_files(mit_with_copyright()))
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            skill_sync.cmd_discover(url)
        self.assertIn("License (candidate): MIT - recognized", buffer.getvalue())
        self.assertIn("Redistributable: yes (recognized)", buffer.getvalue())

        url = self.make_repo(self.demo_files(mit_with_restriction()))
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            skill_sync.cmd_discover(url)
        self.assertIn("License (candidate): MIT-like - needs-review", buffer.getvalue())
        self.assertIn("Redistributable: needs human review", buffer.getvalue())
        self.assertNotIn("yes (recognized)", buffer.getvalue())


class CommandLineTests(unittest.TestCase):
    def test_usage_errors_exit_with_one(self):
        for argv in ([], ["bogus", "x"], ["import"], ["import", "u", "--accept-license", "xyz"]):
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as caught:
                    skill_sync.main(argv)
            self.assertEqual(caught.exception.code, 1, argv)

    def test_accept_license_is_repeatable(self):
        parser = skill_sync.build_parser()
        first, second = "a" * 64, "B" * 64
        args = parser.parse_args(
            ["import", "u", "--apply", "--accept-license", first, "--accept-license", second]
        )
        self.assertEqual(args.accept_license, [first, second.lower()])
        self.assertTrue(args.apply)


if __name__ == "__main__":
    unittest.main()

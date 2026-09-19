#!/usr/bin/env python3
"""Tests for check_i18n_seo.py and validate_locale_registry.py."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIX = ROOT / "tests" / "fixtures"
REGISTRY = ROOT / "templates" / "locale-registry.example.json"
PY = sys.executable


def run_check(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PY, str(SCRIPTS / "check_i18n_seo.py"), *args],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )


def run_validate(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PY, str(SCRIPTS / "validate_locale_registry.py"), str(path)],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )


class TestLocaleRegistry(unittest.TestCase):
    def test_example_registry_ok(self) -> None:
        proc = run_validate(REGISTRY)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("OK:", proc.stdout)

    def test_example_keyword_map_structure(self) -> None:
        path = ROOT / "templates" / "keyword-map.example.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertIn("version", data)
        self.assertIn("sourceLocale", data)
        self.assertTrue(data["entries"])
        pricing = data["entries"][0]
        self.assertEqual(pricing["path"], "/pricing")
        self.assertIn("primaryKeyword", pricing["locales"]["fr-CA"])
        self.assertNotEqual(
            pricing["locales"]["en"]["primaryKeyword"],
            pricing["locales"]["fr-CA"]["primaryKeyword"],
        )


class TestCheckPassFixtures(unittest.TestCase):
    def test_pass_directory_clean(self) -> None:
        proc = run_check(
            [
                "--root",
                str(FIX / "html" / "pass"),
                "--registry",
                str(REGISTRY),
                "--sitemap",
                str(FIX / "sitemaps" / "sitemap-pass.xml"),
                "--format",
                "json",
                "--fail-on",
                "error",
            ]
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        report = json.loads(proc.stdout)
        self.assertEqual(report["summary"]["errors"], 0)
        self.assertGreaterEqual(report["pagesScanned"], 3)


class TestCheckFailFixtures(unittest.TestCase):
    def _codes(self, root: Path) -> set[str]:
        proc = run_check(
            [
                "--root",
                str(root),
                "--registry",
                str(REGISTRY),
                "--format",
                "json",
                "--fail-on",
                "never",
            ]
        )
        self.assertIn(proc.returncode, (0, 1), proc.stdout + proc.stderr)
        report = json.loads(proc.stdout)
        return {f["code"] for f in report["findings"]}

    def test_missing_hreflang(self) -> None:
        codes = self._codes(FIX / "html" / "fail" / "missing-hreflang")
        self.assertIn("missing_hreflang", codes)

    def test_hreflang_on_noindex(self) -> None:
        codes = self._codes(FIX / "html" / "fail" / "hreflang-on-noindex")
        self.assertIn("hreflang_on_noindex", codes)

    def test_wrong_bcp47_case(self) -> None:
        codes = self._codes(FIX / "html" / "fail" / "wrong-bcp47")
        self.assertTrue(
            "hreflang_slug_case" in codes or "hreflang_bcp47_case" in codes,
            codes,
        )

    def test_og_url_mismatch(self) -> None:
        codes = self._codes(FIX / "html" / "fail" / "og-mismatch")
        self.assertIn("og_url_mismatch", codes)

    def test_html_lang_mismatch(self) -> None:
        codes = self._codes(FIX / "html" / "fail" / "bad-lang")
        self.assertIn("html_lang_mismatch", codes)

    def test_sitemap_missing_non_default(self) -> None:
        proc = run_check(
            [
                "--root",
                str(FIX / "html" / "pass"),
                "--registry",
                str(REGISTRY),
                "--sitemap",
                str(FIX / "sitemaps" / "sitemap-missing-fr.xml"),
                "--format",
                "json",
                "--fail-on",
                "never",
            ]
        )
        report = json.loads(proc.stdout)
        codes = {f["code"] for f in report["findings"]}
        self.assertIn("sitemap_missing_non_default_locale", codes)


class TestValidateHreflang(unittest.TestCase):
    def test_pass_reciprocal(self) -> None:
        proc = subprocess.run(
            [
                PY,
                str(SCRIPTS / "validate_hreflang.py"),
                "--root",
                str(FIX / "html" / "pass"),
                "--registry",
                str(REGISTRY),
            ],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()

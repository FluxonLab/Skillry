#!/usr/bin/env python3
"""Validate hreflang reciprocity and BCP47 casing across a directory of HTML files."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

# Reuse parser from check_i18n_seo
sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_i18n_seo import (  # noqa: E402
    expected_hreflang,
    iter_html_files,
    is_noindex,
    parse_html,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    args = parser.parse_args(argv)

    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    enabled = [l for l in registry.get("locales", []) if l.get("enabled", True)]
    expected_langs = {expected_hreflang(l) for l in enabled}
    expected_langs.add("x-default")

    # Map canonical -> set of hreflang pairs announced
    page_alts: dict[str, set[tuple[str, str]]] = {}
    errors: list[str] = []

    for html_path in iter_html_files(args.root):
        rel = str(html_path.relative_to(args.root))
        page = parse_html(html_path.read_text(encoding="utf-8", errors="replace"), rel)
        if is_noindex(page.robots):
            if page.hreflang:
                errors.append(f"{rel}: hreflang present on noindex page")
            continue
        if not page.canonical:
            errors.append(f"{rel}: missing canonical; cannot validate reciprocity")
            continue
        alts = set(page.hreflang)
        page_alts[page.canonical] = alts
        langs = {a[0] for a in alts}
        if "x-default" not in langs:
            errors.append(f"{rel}: missing x-default")
        for lang, href in alts:
            if lang != "x-default" and lang not in expected_langs:
                # allow extras but warn via stderr message as error for unknown casing
                lower_map = {e.lower(): e for e in expected_langs}
                if lang.lower() in lower_map and lang != lower_map[lang.lower()]:
                    errors.append(
                        f"{rel}: hreflang casing {lang!r} should be {lower_map[lang.lower()]!r}"
                    )

    # Reciprocity: if A lists B as lang L, B should list A
    href_to_canonical = {c: c for c in page_alts}
    for canonical, alts in page_alts.items():
        for lang, href in alts:
            if lang == "x-default":
                continue
            if href not in page_alts:
                # May point outside scanned set
                continue
            back = page_alts[href]
            back_hrefs = {h for _, h in back}
            if canonical not in back_hrefs:
                errors.append(
                    f"Reciprocity break: {canonical} → ({lang}) {href}, but target does not link back"
                )

    # Cluster completeness hint: same path groups by hreflang set size
    by_cluster: dict[frozenset[str], list[str]] = defaultdict(list)
    for canonical, alts in page_alts.items():
        by_cluster[frozenset(h for _, h in alts)].append(canonical)

    if errors:
        print(f"INVALID hreflang ({len(errors)} issue(s))")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"OK: hreflang checks passed for {len(page_alts)} indexable page(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

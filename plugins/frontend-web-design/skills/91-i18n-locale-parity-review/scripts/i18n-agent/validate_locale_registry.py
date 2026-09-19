#!/usr/bin/env python3
"""Validate a locale-registry JSON file against the skill schema rules.

Uses the standard library only. Optionally uses jsonschema if installed.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

BCP47_RE = re.compile(r"^[A-Za-z]{2,3}(-[A-Za-z0-9]{2,8})*$")
ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")
PREFIX_RE = re.compile(r"^[A-Za-z0-9_-]*$")

SCHEMA_REL = Path(__file__).resolve().parent.parent / "schemas" / "locale-registry.schema.json"


def _err(errors: list[str], msg: str) -> None:
    errors.append(msg)


def validate_registry(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["Root must be a JSON object"]

    for key in ("version", "defaultLocale", "locales"):
        if key not in data:
            _err(errors, f"Missing required property: {key}")

    if "trailingSlash" in data and data["trailingSlash"] not in (
        "always",
        "never",
        "as-is",
    ):
        _err(errors, "trailingSlash must be always|never|as-is")

    if "urlStrategy" in data and data["urlStrategy"] not in (
        "prefix-all",
        "prefix-except-default",
        "subdomain",
        "tld",
        "other",
    ):
        _err(errors, "urlStrategy has invalid value")

    if "fallbackPolicy" in data and data["fallbackPolicy"] not in (
        "omit",
        "fallback-noindex",
        "soft-redirect-default",
    ):
        _err(errors, "fallbackPolicy has invalid value")

    locales = data.get("locales")
    if not isinstance(locales, list) or len(locales) < 1:
        _err(errors, "locales must be a non-empty array")
        return errors

    ids: set[str] = set()
    for i, loc in enumerate(locales):
        prefix = f"locales[{i}]"
        if not isinstance(loc, dict):
            _err(errors, f"{prefix} must be an object")
            continue
        for req in ("id", "bcp47", "urlPrefix", "dir", "label", "enabled"):
            if req not in loc:
                _err(errors, f"{prefix}.{req} is required")
        loc_id = loc.get("id")
        if isinstance(loc_id, str):
            if not ID_RE.match(loc_id):
                _err(errors, f"{prefix}.id invalid pattern: {loc_id!r}")
            if loc_id in ids:
                _err(errors, f"Duplicate locale id: {loc_id}")
            ids.add(loc_id)
        bcp47 = loc.get("bcp47")
        if isinstance(bcp47, str) and not BCP47_RE.match(bcp47):
            _err(errors, f"{prefix}.bcp47 invalid BCP47: {bcp47!r}")
        url_prefix = loc.get("urlPrefix")
        if isinstance(url_prefix, str) and not PREFIX_RE.match(url_prefix):
            _err(errors, f"{prefix}.urlPrefix invalid: {url_prefix!r}")
        if loc.get("dir") not in ("ltr", "rtl", None) and "dir" in loc:
            _err(errors, f"{prefix}.dir must be ltr|rtl")
        if "marketPriority" in loc and loc["marketPriority"] not in (
            "primary",
            "secondary",
            "maintain",
        ):
            _err(errors, f"{prefix}.marketPriority invalid")
        if "hreflangCase" in loc and loc["hreflangCase"] not in (
            "bcp47",
            "lowercase",
        ):
            _err(errors, f"{prefix}.hreflangCase invalid")
        if "enabled" in loc and not isinstance(loc["enabled"], bool):
            _err(errors, f"{prefix}.enabled must be boolean")

    default = data.get("defaultLocale")
    if isinstance(default, str) and default not in ids and ids:
        _err(errors, f"defaultLocale {default!r} not found in locales[].id")

    return errors


def try_jsonschema(data: Any) -> list[str]:
    try:
        import jsonschema  # type: ignore
    except ImportError:
        return []
    if not SCHEMA_REL.is_file():
        return []
    schema = json.loads(SCHEMA_REL.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    return [
        f"{'/'.join(str(p) for p in e.path) or '<root>'}: {e.message}"
        for e in sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("registry", type=Path, help="Path to locale-registry.json")
    parser.add_argument(
        "--strict-schema",
        action="store_true",
        help="Also validate with jsonschema if installed",
    )
    args = parser.parse_args(argv)

    if not args.registry.is_file():
        print(f"ERROR: file not found: {args.registry}", file=sys.stderr)
        return 2

    try:
        data = json.loads(args.registry.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid JSON: {exc}", file=sys.stderr)
        return 2

    errors = validate_registry(data)
    if args.strict_schema:
        errors.extend(try_jsonschema(data))

    if errors:
        print(f"INVALID: {args.registry} ({len(errors)} issue(s))")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"OK: {args.registry}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

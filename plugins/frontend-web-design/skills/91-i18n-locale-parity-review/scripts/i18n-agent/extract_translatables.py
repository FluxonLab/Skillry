#!/usr/bin/env python3
"""Best-effort extraction of translatable strings from common source patterns.

Supports:
  - JSON message catalogs (flat or nested)
  - Markdown / MDX frontmatter title + description
  - Simple key: value YAML-like lines in .yml/.yaml locale files

This is a helper for Phase D inventory — not a full AST extractor.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterator


FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)


def walk_json(obj: Any, prefix: str = "") -> Iterator[tuple[str, str]]:
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{prefix}.{k}" if prefix else str(k)
            yield from walk_json(v, key)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_json(v, f"{prefix}[{i}]")
    elif isinstance(obj, str):
        if obj.strip():
            yield prefix, obj


def extract_json_file(path: Path) -> list[dict[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [
        {
            "file": str(path),
            "key": key,
            "source": text,
            "type": guess_type(key, text),
        }
        for key, text in walk_json(data)
    ]


def guess_type(key: str, text: str) -> str:
    k = key.lower()
    if "title" in k and ("seo" in k or "meta" in k or k.endswith("title")):
        return "seo_title"
    if "description" in k or "meta" in k:
        return "seo_description"
    if "alt" in k:
        return "alt"
    if "legal" in k or "privacy" in k or "terms" in k:
        return "legal"
    if len(text) > 120:
        return "marketing"
    return "ui"


def extract_md(path: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8")
    out: list[dict[str, str]] = []
    m = FRONTMATTER_RE.match(text)
    if m:
        fm = m.group(1)
        for line in fm.splitlines():
            if ":" not in line:
                continue
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip("\"'")
            if key in ("title", "description", "ogTitle", "ogDescription") and val:
                out.append(
                    {
                        "file": str(path),
                        "key": key,
                        "source": val,
                        "type": "seo_title" if "title" in key.lower() else "seo_description",
                    }
                )
    # H1
    for hm in re.finditer(r"^#\s+(.+)$", text, re.M):
        out.append(
            {
                "file": str(path),
                "key": "h1",
                "source": hm.group(1).strip(),
                "type": "marketing",
            }
        )
        break
    return out


def extract_yaml_simple(path: Path) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.strip().startswith("#") or ":" not in line:
            continue
        if line.startswith(" ") or line.startswith("\t"):
            # nested — skip in simple mode
            continue
        key, _, val = line.partition(":")
        val = val.strip().strip("\"'")
        if val:
            out.append(
                {
                    "file": str(path),
                    "key": key.strip(),
                    "source": val,
                    "type": guess_type(key, val),
                }
            )
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="Source root to scan")
    parser.add_argument(
        "--out",
        type=Path,
        help="Write JSON array of segments (default: stdout)",
    )
    parser.add_argument(
        "--glob-json",
        default="**/messages/**/*.json,**/*locale*.json,**/locales/**/*.json",
        help="Comma-separated globs for JSON catalogs",
    )
    args = parser.parse_args(argv)

    if not args.root.is_dir():
        print(f"ERROR: not a directory: {args.root}", file=sys.stderr)
        return 2

    segments: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for pattern in args.glob_json.split(","):
        pattern = pattern.strip()
        if not pattern:
            continue
        for path in args.root.glob(pattern):
            if path.is_file() and path.suffix == ".json":
                try:
                    for seg in extract_json_file(path):
                        key = (seg["file"], seg["key"])
                        if key not in seen:
                            seen.add(key)
                            segments.append(seg)
                except json.JSONDecodeError:
                    print(f"WARN: skip invalid JSON {path}", file=sys.stderr)

    for path in list(args.root.rglob("*.md")) + list(args.root.rglob("*.mdx")):
        for seg in extract_md(path):
            key = (seg["file"], seg["key"])
            if key not in seen:
                seen.add(key)
                segments.append(seg)

    for path in list(args.root.rglob("*.yml")) + list(args.root.rglob("*.yaml")):
        for seg in extract_yaml_simple(path):
            key = (seg["file"], seg["key"])
            if key not in seen:
                seen.add(key)
                segments.append(seg)

    payload = json.dumps(segments, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        args.out.write_text(payload, encoding="utf-8")
        print(f"Wrote {len(segments)} segments to {args.out}")
    else:
        sys.stdout.write(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

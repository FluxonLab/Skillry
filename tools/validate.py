#!/usr/bin/env python3
"""Skillry structural and policy validator."""
from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGINS = ROOT / "plugins"
COMMUNITY = ROOT / "community"
READ_ONLY_TOOLS = frozenset({"Read", "Glob", "Grep", "WebSearch", "WebFetch"})
checks: list[tuple[str, bool, str]] = []


def ok(name: str, condition: bool, detail: str = "") -> None:
    checks.append((name, bool(condition), detail))


def frontmatter(text: str) -> dict:
    match = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not match:
        return {}
    fields = {}
    for line in match.group(1).splitlines():
        field = re.match(r"^([A-Za-z_]+):\s*(.*)$", line)
        if field:
            fields[field.group(1)] = field.group(2).strip()
    return fields


def tool_names(raw: str) -> set[str]:
    return set(re.findall(r"[A-Za-z][A-Za-z0-9_-]*", raw))


source_symlinks = []
for source_root in (PLUGINS, COMMUNITY):
    if source_root.exists():
        source_symlinks.extend(
            str(path.relative_to(ROOT))
            for path in source_root.rglob("*")
            if path.is_symlink()
        )
ok(
    "packaged component trees contain no symlinks",
    not source_symlinks,
    "; ".join(source_symlinks[:8]),
)

skill_files = sorted(PLUGINS.glob("*/skills/*/SKILL.md"))
ok("plugins have skills", len(skill_files) > 0, f"found {len(skill_files)}")
bad_frontmatter = []
shallow = []
name_mismatch = []
for skill_file in skill_files:
    text = skill_file.read_text(encoding="utf-8")
    fields = frontmatter(text)
    if not fields.get("name") or not fields.get("description"):
        bad_frontmatter.append(str(skill_file.relative_to(ROOT)))
    folder = re.sub(r"^\d+-", "", skill_file.parent.name)
    if fields.get("name") and fields["name"] != folder:
        name_mismatch.append(
            f"{skill_file.parent.name} -> name:{fields.get('name')}"
        )
    if len(text.splitlines()) < 60:
        shallow.append(
            f"{skill_file.parent.name} ({len(text.splitlines())})"
        )
ok(
    "all skills have name+description",
    not bad_frontmatter,
    "; ".join(bad_frontmatter[:5]),
)
ok(
    "skill folder names match frontmatter",
    not name_mismatch,
    "; ".join(name_mismatch[:5]),
)
ok(
    "no shallow skills (<60 lines)",
    not shallow,
    "; ".join(shallow[:8]),
)

agent_files = sorted(PLUGINS.glob("*/agents/*.md"))
ok("plugins have agents", len(agent_files) > 0, f"found {len(agent_files)}")
agent_no_tools = []
agent_bad_frontmatter = []
unsafe_read_only_claims = []
for agent_file in agent_files:
    text = agent_file.read_text(encoding="utf-8")
    fields = frontmatter(text)
    if not fields.get("name") or not fields.get("description"):
        agent_bad_frontmatter.append(agent_file.name)
    if "tools:" not in text:
        agent_no_tools.append(agent_file.name)

    tools = tool_names(fields.get("tools", ""))
    claimed = (
        fields.get("permission", "")
        or fields.get("sandbox_mode", "")
    ).strip(chr(34) + chr(39))
    if claimed == "read-only" and (
        not tools or not tools <= READ_ONLY_TOOLS
    ):
        unsafe_read_only_claims.append(
            f"{agent_file.name}: {', '.join(sorted(tools)) or 'no tools'}"
        )

ok(
    "all agents declare name+description",
    not agent_bad_frontmatter,
    "; ".join(agent_bad_frontmatter[:5]),
)
ok(
    "all agents declare tools allowlist",
    not agent_no_tools,
    "; ".join(agent_no_tools[:5]),
)
ok(
    "read-only agent claims exclude write-capable tools",
    not unsafe_read_only_claims,
    "; ".join(unsafe_read_only_claims[:8]),
)

manifests = sorted(PLUGINS.glob("*/.claude-plugin/plugin.json"))
bad_manifest = []
for manifest in manifests:
    try:
        obj = json.loads(manifest.read_text(encoding="utf-8"))
        if not obj.get("name"):
            bad_manifest.append(str(manifest.relative_to(ROOT)))
    except Exception as exc:
        bad_manifest.append(f"{manifest.relative_to(ROOT)}: {exc}")

department_count = len(
    [path for path in PLUGINS.iterdir() if path.is_dir()]
)
ok(
    "every department has a valid plugin.json",
    len(manifests) == department_count,
    f"{len(manifests)} manifests",
)
ok(
    "plugin.json files parse + have name",
    not bad_manifest,
    "; ".join(bad_manifest[:5]),
)

marketplace = ROOT / ".claude-plugin" / "marketplace.json"
if marketplace.exists():
    try:
        data = json.loads(marketplace.read_text(encoding="utf-8"))
        ok(
            "marketplace.json has required fields",
            all(key in data for key in ("name", "owner", "plugins")),
        )
        ok(
            "marketplace owner has name",
            isinstance(data.get("owner"), dict)
            and bool(data["owner"].get("name")),
        )
        ok(
            "marketplace lists all plugins",
            len(data.get("plugins", [])) == len(manifests),
            f"{len(data.get('plugins', []))} vs {len(manifests)} departments",
        )
    except Exception as exc:
        ok("marketplace.json parses", False, str(exc))
else:
    ok("marketplace.json exists", False)

if COMMUNITY.exists():
    community_dirs = [path for path in COMMUNITY.iterdir() if path.is_dir()]
    missing_license = [
        path.name for path in community_dirs if not (path / "LICENSE").exists()
    ]
    missing_readme = [
        path.name for path in community_dirs if not (path / "README.md").exists()
    ]
    ok(
        "every community source has a LICENSE",
        not missing_license,
        "; ".join(missing_license),
    )
    ok(
        "every community source has a README",
        not missing_readme,
        "; ".join(missing_readme),
    )

leaks = []
for source_file in list(skill_files) + list(agent_files):
    text = source_file.read_text(encoding="utf-8")
    if (
        "Caarimu" in text
        or "caarimu" in text
        or re.search(r"/Users/[A-Za-z0-9]+-m1\b", text)
    ):
        leaks.append(source_file.name)
ok(
    "no personal brand/paths in plugins",
    not leaks,
    "; ".join(leaks[:5]),
)

failures = [check for check in checks if not check[1]]
for name, passed, detail in checks:
    marker = "PASS" if passed else "FAIL"
    suffix = (
        f"  ({detail})"
        if detail and not passed
        else f"  [{detail}]"
        if detail
        else ""
    )
    print(f"- {marker}: {name}{suffix}")
print(f"\nChecks: {len(checks)}  Failures: {len(failures)}")
sys.exit(1 if failures else 0)

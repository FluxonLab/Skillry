#!/usr/bin/env python3
"""Generate .claude-plugin/marketplace.json from the plugins/ tree.

Each department directory under plugins/ becomes one plugin entry whose source is a
relative path. Run after adding/removing plugins. Dry-run prints; --apply writes.
"""
from __future__ import annotations
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGINS = ROOT / "plugins"
OUT = ROOT / ".claude-plugin" / "marketplace.json"
APPLY = "--apply" in sys.argv

DISPLAY = {
 "core-operations": "Core Operations",
 "runtime-and-local-app": "Runtime & Local App",
 "backend-and-api": "Backend & API",
 "frontend-web-design": "Frontend & Web Design",
 "mobile-desktop": "Mobile & Desktop",
 "gaming-interactive-media": "Gaming & Interactive Media",
 "database-and-data": "Database & Data",
 "ai-and-agent-systems": "AI & Agent Systems",
 "security": "Security",
 "testing-and-qa": "Testing & QA",
 "devops-and-release": "DevOps & Release",
 "product-docs-and-research": "Product, Docs & Research",
 "skill-library-and-installation": "Skill Library & Installation",
 "optional-specialist": "Optional Specialists",
}

def plugin_desc(d: pathlib.Path) -> str:
    manifest = d / ".claude-plugin" / "plugin.json"
    if manifest.exists():
        try:
            return json.loads(manifest.read_text()).get("description", "")
        except Exception:
            pass
    return ""

plugins = []
for d in sorted(PLUGINS.iterdir()):
    if not d.is_dir():
        continue
    name = f"omniagent-{d.name}"
    plugins.append({
        "name": name,
        "source": f"./plugins/{d.name}",
        "description": plugin_desc(d),
    })

marketplace = {
    "$schema": "https://json.schemastore.org/claude-code-marketplace.json",
    "name": "omniagent",
    "owner": {"name": "FluxonLab", "url": "https://fluxonlab.com"},
    "description": "Installable, permission-bounded, multi-platform agent skills & subagents by FluxonLab.",
    "plugins": plugins,
}

print(f"{'APPLY' if APPLY else 'DRY-RUN'} — marketplace.json with {len(plugins)} plugins:")
for p in plugins:
    print(f"  - {p['name']}  ({p['source']})")

if APPLY:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(marketplace, indent=2) + "\n")
    print(f"\nWrote {OUT.relative_to(ROOT)}")

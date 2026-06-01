#!/usr/bin/env python3
"""Skillry validator — checks structure, frontmatter, permissions, and attribution.

Run from anywhere: python3 tools/validate.py
Exit code 0 = all checks pass, 1 = failures.
"""
from __future__ import annotations
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGINS = ROOT / "plugins"
COMMUNITY = ROOT / "community"
checks: list[tuple[str, bool, str]] = []

def ok(name: str, cond: bool, detail: str = "") -> None:
    checks.append((name, bool(cond), detail))

def frontmatter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        mm = re.match(r"^([A-Za-z_]+):\s*(.*)$", line)
        if mm:
            fm[mm.group(1)] = mm.group(2).strip()
    return fm

# ---- skills (original, under plugins/) ----
skill_files = sorted(PLUGINS.glob("*/skills/*/SKILL.md"))
ok("plugins have skills", len(skill_files) > 0, f"found {len(skill_files)}")
bad_fm, shallow, name_mismatch = [], [], []
for f in skill_files:
    txt = f.read_text(errors="ignore")
    fm = frontmatter(txt)
    if not fm.get("name") or not fm.get("description"):
        bad_fm.append(str(f.relative_to(ROOT)))
    # folder name (minus NN- prefix) should match frontmatter name
    folder = re.sub(r"^\d+-", "", f.parent.name)
    if fm.get("name") and fm["name"] != folder:
        name_mismatch.append(f"{f.parent.name} → name:{fm.get('name')}")
    if len(txt.splitlines()) < 60:
        shallow.append(f"{f.parent.name} ({len(txt.splitlines())})")
ok("all skills have name+description", not bad_fm, "; ".join(bad_fm[:5]))
ok("skill folder names match frontmatter", not name_mismatch, "; ".join(name_mismatch[:5]))
ok("no shallow skills (<60 lines)", not shallow, "; ".join(shallow[:8]))

# ---- agents (original, under plugins/) ----
agent_files = sorted(PLUGINS.glob("*/agents/*.md"))
ok("plugins have agents", len(agent_files) > 0, f"found {len(agent_files)}")
agent_no_tools, agent_bad_fm = [], []
REVIEW_HINT = ("review", "auditor", "reviewer", "analyst", "researcher", "scout", "librarian", "gatekeeper")
write_in_review = []
for f in agent_files:
    txt = f.read_text(errors="ignore")
    fm = frontmatter(txt)
    if not fm.get("name") or not fm.get("description"):
        agent_bad_fm.append(f.name)
    if "tools:" not in txt:
        agent_no_tools.append(f.name)
    # least-privilege heuristic: review/audit agents should not have Write/Edit,
    # UNLESS their description explicitly states they make/repair/apply changes
    # (some reviewers are write-limited editors by design).
    low = f.stem.lower()
    desc = (fm.get("description") or "").lower()
    makes_changes = any(w in desc for w in ("make", "repair", "apply", "fix", "implement", "change"))
    if any(h in low for h in REVIEW_HINT) and not makes_changes:
        tools_line = next((l for l in txt.splitlines() if l.startswith("tools:")), "")
        if "Write" in tools_line or "Edit" in tools_line:
            write_in_review.append(f.name)
ok("all agents declare name+description", not agent_bad_fm, "; ".join(agent_bad_fm[:5]))
ok("all agents declare tools allowlist", not agent_no_tools, "; ".join(agent_no_tools[:5]))
ok("review/audit agents have no Write/Edit (least privilege)", not write_in_review, "; ".join(write_in_review[:8]))

# ---- plugin manifests ----
manifests = sorted(PLUGINS.glob("*/.claude-plugin/plugin.json"))
bad_manifest = []
for m in manifests:
    try:
        obj = json.loads(m.read_text())
        if not obj.get("name"):
            bad_manifest.append(str(m.relative_to(ROOT)))
    except Exception as e:
        bad_manifest.append(f"{m.relative_to(ROOT)}: {e}")
ok("every department has a valid plugin.json", len(manifests) == len(list(d for d in PLUGINS.iterdir() if d.is_dir())), f"{len(manifests)} manifests")
ok("plugin.json files parse + have name", not bad_manifest, "; ".join(bad_manifest[:5]))

# ---- marketplace.json ----
mkt = ROOT / ".claude-plugin" / "marketplace.json"
if mkt.exists():
    try:
        mo = json.loads(mkt.read_text())
        ok("marketplace.json has required fields", all(k in mo for k in ("name", "owner", "plugins")))
        ok("marketplace owner has name", isinstance(mo.get("owner"), dict) and bool(mo["owner"].get("name")))
        ok("marketplace lists all plugins", len(mo.get("plugins", [])) == len(manifests),
           f"{len(mo.get('plugins', []))} vs {len(manifests)} departments")
    except Exception as e:
        ok("marketplace.json parses", False, str(e))
else:
    ok("marketplace.json exists", False)

# ---- community attribution ----
if COMMUNITY.exists():
    comm_dirs = [d for d in COMMUNITY.iterdir() if d.is_dir()]
    missing_lic = [d.name for d in comm_dirs if not (d / "LICENSE").exists()]
    missing_readme = [d.name for d in comm_dirs if not (d / "README.md").exists()]
    ok("every community source has a LICENSE", not missing_lic, "; ".join(missing_lic))
    ok("every community source has a README", not missing_readme, "; ".join(missing_readme))

# ---- no personal/brand leakage ----
# Real leaks: the personal brand, or a personal user home path. Generic device
# references like /Volumes/ are legitimate skill content (e.g. path-hygiene-repair).
leak = []
for f in list(skill_files) + list(agent_files):
    t = f.read_text(errors="ignore")
    if "Caarimu" in t or "caarimu" in t or re.search(r"/Users/[A-Za-z0-9]+-m1\b", t):
        leak.append(f.name)
ok("no personal brand/paths in plugins", not leak, "; ".join(leak[:5]))

# ---- report ----
fails = [c for c in checks if not c[1]]
for name, passed, detail in checks:
    mark = "PASS" if passed else "FAIL"
    suffix = f"  ({detail})" if detail and not passed else (f"  [{detail}]" if detail else "")
    print(f"- {mark}: {name}{suffix}")
print(f"\nChecks: {len(checks)}  Failures: {len(fails)}")
sys.exit(1 if fails else 0)

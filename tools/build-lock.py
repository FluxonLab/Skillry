#!/usr/bin/env python3
"""Generate registry/skill-lock.json and registry/agent-lock.json — a content
inventory with SHA-256 checksums for reproducible, verifiable installs.

Run after changing skills/agents:  python3 tools/build-lock.py --apply
Without --apply it prints a summary and reports drift vs the committed lock.
"""
from __future__ import annotations
import json, hashlib, pathlib, sys, re

REPO = pathlib.Path(__file__).resolve().parents[1]
PLUGINS = REPO / "plugins"
COMMUNITY = REPO / "community"
REG = REPO / "registry"
APPLY = "--apply" in sys.argv

def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def fm(text: str, key: str) -> str:
    m = re.search(rf"^{key}:\s*(.+)$", text, re.M)
    return m.group(1).strip().strip('"\'') if m else ""

def build_skills():
    items = []
    for sd in sorted(PLUGINS.glob("*/skills/*")):
        f = sd / "SKILL.md"
        if not f.exists(): continue
        dept = sd.parent.parent.name
        t = f.read_text(errors="ignore")
        items.append({
            "id": re.sub(r"^\d+-", "", sd.name),
            "folder": sd.name,
            "department": dept,
            "origin": "original",
            "lines": len(t.splitlines()),
            "checksum": sha(f),
        })
    for sd in sorted(COMMUNITY.glob("*/skills/*")):
        f = sd / "SKILL.md"
        if not f.exists(): continue
        items.append({
            "id": sd.name,
            "folder": sd.name,
            "source": sd.parent.parent.name,
            "origin": "community",
            "lines": len(f.read_text(errors='ignore').splitlines()),
            "checksum": sha(f),
        })
    return items

def build_agents():
    items = []
    for af in sorted(PLUGINS.glob("*/agents/*.md")):
        t = af.read_text(errors="ignore")
        tools = fm(t, "tools")
        items.append({
            "id": af.stem,
            "department": af.parent.parent.name,
            "origin": "original",
            "permission": "read-only" if not re.search(r"\b(Edit|Write)\b", tools) else "write",
            "tools": tools,
            "checksum": sha(af),
        })
    for af in sorted(COMMUNITY.glob("*/agents/*.md")):
        t = af.read_text(errors="ignore")
        items.append({
            "id": af.stem,
            "source": af.parent.parent.name,
            "origin": "community",
            "checksum": sha(af),
        })
    return items

skills = build_skills()
agents = build_agents()
orig_sk = [s for s in skills if s["origin"] == "original"]
comm_sk = [s for s in skills if s["origin"] == "community"]
orig_ag = [a for a in agents if a["origin"] == "original"]
comm_ag = [a for a in agents if a["origin"] == "community"]

skill_lock = {"version": "0.1.0", "counts": {"original": len(orig_sk), "community": len(comm_sk), "total": len(skills)}, "skills": skills}
agent_lock = {"version": "0.1.0", "counts": {"original": len(orig_ag), "community": len(comm_ag), "total": len(agents)}, "agents": agents}

print(f"{'APPLY' if APPLY else 'DRY-RUN'} — lock")
print(f"  skills: {len(orig_sk)} original + {len(comm_sk)} community = {len(skills)}")
print(f"  agents: {len(orig_ag)} original + {len(comm_ag)} community = {len(agents)}")
ro = sum(1 for a in orig_ag if a['permission'] == 'read-only')
print(f"  original agents read-only: {ro}/{len(orig_ag)}")

if APPLY:
    REG.mkdir(parents=True, exist_ok=True)
    (REG / "skill-lock.json").write_text(json.dumps(skill_lock, indent=2) + "\n")
    (REG / "agent-lock.json").write_text(json.dumps(agent_lock, indent=2) + "\n")
    print(f"\nWrote registry/skill-lock.json + registry/agent-lock.json")
else:
    for name, data in (("skill-lock.json", skill_lock), ("agent-lock.json", agent_lock)):
        p = REG / name
        if p.exists() and json.loads(p.read_text()) != data:
            print(f"  DRIFT: {name} is out of date — run with --apply")

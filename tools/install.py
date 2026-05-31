#!/usr/bin/env python3
"""OmniAgent portable installer — install skills + agents into one or more AI coding
platforms from this repo's plugins/ tree.

USAGE
  python3 tools/install.py                                  # dry-run, all platforms
  python3 tools/install.py --apply --targets claude        # one platform
  python3 tools/install.py --apply --targets claude codex copilot antigravity
  python3 tools/install.py --apply --targets claude --community   # also install community/ skills

WHAT IT DOES
  - Flattens plugins/<dept>/skills/* and plugins/<dept>/agents/* into each platform's
    native skill/agent location, converting agent format per platform.
  - With --community, also installs the attributed third-party skills under community/.
  - Backs up any existing file to *.bak-omniagent before overwriting.
  - Dry-run by default; nothing is written without --apply.

PLATFORM TARGETS
  claude      -> ~/.claude/skills/<name>/SKILL.md , ~/.claude/agents/<name>.md
  codex       -> ~/.codex/skills/<name>/SKILL.md  , ~/.codex/agents/<name>.toml
  copilot     -> ~/.copilot/skills/<name>/SKILL.md, ~/.copilot/agents/<name>.agent.md
  antigravity -> ~/.gemini/antigravity/skills/<name>/SKILL.md , .../agents/<name>.md

Claude Code users can alternatively use the native plugin marketplace:
  /plugin marketplace add FluxonLab/OmniAgent
"""
from __future__ import annotations
import os, re, sys, pathlib, shutil

REPO = pathlib.Path(__file__).resolve().parents[1]
PLUGINS = REPO / "plugins"
COMMUNITY = REPO / "community"
HOME = pathlib.Path.home()

TARGETS = {
    "claude":      {"skills": HOME/".claude/skills",                "agents": HOME/".claude/agents",                "agent_ext": ".md",       "agent_fmt": "md"},
    "codex":       {"skills": HOME/".codex/skills",                 "agents": HOME/".codex/agents",                 "agent_ext": ".toml",     "agent_fmt": "toml"},
    "copilot":     {"skills": HOME/".copilot/skills",               "agents": HOME/".copilot/agents",               "agent_ext": ".agent.md", "agent_fmt": "md"},
    "antigravity": {"skills": HOME/".gemini/antigravity/skills",    "agents": HOME/".gemini/antigravity/agents",    "agent_ext": ".md",       "agent_fmt": "md"},
}

def fm_field(text: str, key: str) -> str:
    m = re.search(rf"^{key}:\s*(.+)$", text, re.M)
    return m.group(1).strip().strip('"\'') if m else ""

def md_to_toml_agent(text: str) -> str:
    """Convert a Claude-style agent .md to a Codex .toml agent."""
    name = fm_field(text, "name").replace("-", "_")
    desc = re.sub(r"\s+", " ", fm_field(text, "description")).replace('"', "'")
    body = re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.S).strip()
    body = body.replace('"""', '\\"\\"\\"')
    sandbox = "read-only" if not re.search(r"\b(Edit|Write)\b", fm_field(text, "tools")) else "workspace-write"
    return (f'name = "{name}"\n'
            f'description = "{desc}"\n'
            f'model_reasoning_effort = "medium"\n'
            f'sandbox_mode = "{sandbox}"\n'
            f'developer_instructions = """\n{body}\n"""\n')

def backup(dst: pathlib.Path):
    if dst.exists():
        b = dst.with_suffix(dst.suffix + ".bak-omniagent")
        if not b.exists():
            shutil.copy2(dst, b)

def install_target(name: str, cfg: dict, apply: bool, with_community: bool):
    skdir, agdir = cfg["skills"], cfg["agents"]
    n_sk = n_ag = 0
    # skills (original)
    skill_dirs = sorted(PLUGINS.glob("*/skills/*"))
    if with_community:
        skill_dirs += sorted(COMMUNITY.glob("*/skills/*"))
    for sd in skill_dirs:
        src = sd / "SKILL.md"
        if not src.exists():
            continue
        out = skdir / sd.name / "SKILL.md"
        n_sk += 1
        if apply:
            out.parent.mkdir(parents=True, exist_ok=True)
            backup(out)
            out.write_text(src.read_text(errors="ignore"), encoding="utf-8")
    # agents (original only)
    for af in sorted(PLUGINS.glob("*/agents/*.md")):
        text = af.read_text(errors="ignore")
        base = af.stem
        out = agdir / f"{base}{cfg['agent_ext']}"
        n_ag += 1
        if apply:
            out.parent.mkdir(parents=True, exist_ok=True)
            backup(out)
            out.write_text(md_to_toml_agent(text) if cfg["agent_fmt"] == "toml" else text, encoding="utf-8")
    print(f"  {name:12} skills:{n_sk}  agents:{n_ag}  -> {skdir}")
    return n_sk, n_ag

def main():
    args = sys.argv[1:]
    apply = "--apply" in args
    with_community = "--community" in args
    if "--targets" in args:
        i = args.index("--targets")
        sel = [a for a in args[i+1:] if not a.startswith("--")]
    else:
        sel = list(TARGETS)
    bad = [s for s in sel if s not in TARGETS]
    if bad:
        print("Unknown target(s):", bad, "\nValid:", list(TARGETS)); sys.exit(1)

    print(f"{'APPLY' if apply else 'DRY-RUN'} — OmniAgent install")
    print(f"Targets: {', '.join(sel)}   Community skills: {'yes' if with_community else 'no'}\n")
    for name in sel:
        install_target(name, TARGETS[name], apply, with_community)
    print("\nDone" + ("" if apply else " (dry-run — nothing written; re-run with --apply)"))
    if apply:
        print("Verify with: python3 tools/validate.py")

if __name__ == "__main__":
    main()

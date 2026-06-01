#!/usr/bin/env python3
"""Skillry portable installer — install skills + agents into one or more AI coding
platforms from this repo's plugins/ tree.

USAGE
  python3 tools/install.py                                  # dry-run, all platforms
  python3 tools/install.py --apply --targets claude        # one platform
  python3 tools/install.py --apply --targets claude codex copilot antigravity
  python3 tools/install.py --apply --targets claude --community   # also install community/ skills
  python3 tools/install.py --apply --targets claude codex --instructions ~/my-project  # + behavior files

WHAT IT DOES
  - Flattens plugins/<dept>/skills/* and plugins/<dept>/agents/* into each platform's
    native skill/agent location, converting agent format per platform.
  - With --community, also installs the attributed third-party skills under community/.
  - With --instructions <dir>, also drops the right behavior file per target platform into <dir>
    (claude->CLAUDE.md, codex->AGENTS.md, copilot->.github/copilot-instructions.md,
    antigravity->GEMINI.md + AGENTS.md). Defaults to the current directory if <dir> is omitted.
  - Backs up any existing file to *.bak-skillry before overwriting.
  - Dry-run by default; nothing is written without --apply.

PLATFORM TARGETS
  claude      -> ~/.claude/skills/<name>/SKILL.md , ~/.claude/agents/<name>.md
  codex       -> ~/.codex/skills/<name>/SKILL.md  , ~/.codex/agents/<name>.toml
  copilot     -> ~/.copilot/skills/<name>/SKILL.md, ~/.copilot/agents/<name>.agent.md
  antigravity -> ~/.gemini/antigravity/skills/<name>/SKILL.md , .../agents/<name>.md

Claude Code users can alternatively use the native plugin marketplace:
  /plugin marketplace add FluxonLab/Skillry
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

# Behavior/instruction file each platform reads, as (repo source -> path relative to the project dir).
# Antigravity reads both GEMINI.md and AGENTS.md.
INSTRUCTIONS = {
    "claude":      [("CLAUDE.md", "CLAUDE.md")],
    "codex":       [("AGENTS.md", "AGENTS.md")],
    "copilot":     [(".github/copilot-instructions.md", ".github/copilot-instructions.md")],
    "antigravity": [("GEMINI.md", "GEMINI.md"), ("AGENTS.md", "AGENTS.md")],
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
        b = dst.with_suffix(dst.suffix + ".bak-skillry")
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

MANUAL_BEGIN = "<!-- SKILLRY:MANUAL:BEGIN — added by Skillry; safe to edit or remove this block -->"
MANUAL_END = "<!-- SKILLRY:MANUAL:END -->"
RECONCILE = """<!-- SKILLRY:FIRST-RUN-RECONCILE:BEGIN -->
> **First run — reconcile, then delete this block.** Skillry's engineering manual was added below,
> *after* the project instructions that were already in this file (above the SKILLRY:MANUAL marker).
> On your **first response in this session**, before starting the user's task:
> 1. In one short message, tell the user that Skillry's guidance was merged into this file.
> 2. Compare the Skillry section below with the user's existing rules above and find: (a) rules that
>    **duplicate** something already stated, and (b) rules that **conflict** with the user's rules.
> 3. List each overlap/conflict and ask the user how to resolve it — keep theirs, keep Skillry's, or
>    merge — using the platform's question UI if it has one.
> 4. Apply the user's choices by editing this file (remove duplicates, resolve conflicts).
> 5. **Delete this entire notice** — the `SKILLRY:FIRST-RUN-RECONCILE` BEGIN…END markers and
>    everything between them — so it never runs again. Leave the reconciled manual in place.
>
> If there are no duplicates or conflicts, still do step 1 and step 5 (briefly announce, then delete this notice).
<!-- SKILLRY:FIRST-RUN-RECONCILE:END -->"""

def strip_skillry_block(text: str) -> str:
    """Remove a previously-installed SKILLRY:MANUAL block (for idempotent re-installs)."""
    return re.sub(re.escape(MANUAL_BEGIN) + r".*?" + re.escape(MANUAL_END), "", text, flags=re.S).rstrip()

def compose_instruction(existing: str, manual: str) -> tuple[str, str]:
    """Return (new_content, mode). Preserves the user's own rules; appends Skillry under a marker.
    mode: 'fresh' (no prior file), 'merge' (user rules kept, reconcile notice added), 'update'
    (replacing a prior Skillry block)."""
    had_skillry = MANUAL_BEGIN in existing
    user_part = strip_skillry_block(existing) if had_skillry else existing.rstrip()
    block = f"{MANUAL_BEGIN}\n{manual.rstrip()}\n{MANUAL_END}\n"
    if not user_part.strip():
        return block, ("update" if had_skillry else "fresh")
    # user has their own instructions → keep them, append Skillry with a one-time reconcile notice
    reconciled = f"{user_part}\n\n{MANUAL_BEGIN}\n{RECONCILE}\n\n{manual.rstrip()}\n{MANUAL_END}\n"
    return reconciled, ("update" if had_skillry else "merge")

def install_instructions(sel: list, dest_dir: pathlib.Path, apply: bool):
    """Install the behavior file(s) each selected platform reads into dest_dir.

    Existing files are never clobbered: the user's own instructions are kept and Skillry's manual
    is appended under a clearly-marked block. When appending to a non-empty user file, a self-
    removing first-run reconcile notice is added so the agent reconciles duplicates/conflicts with
    the user on first run. Re-installs replace the prior Skillry block (idempotent). A backup is
    still written to *.bak-skillry before any change."""
    pairs, seen = [], set()  # de-duped (src, dst) — antigravity + codex both want AGENTS.md
    for name in sel:
        for src_rel, dst_rel in INSTRUCTIONS.get(name, []):
            if dst_rel not in seen:
                seen.add(dst_rel)
                pairs.append((src_rel, dst_rel))
    print(f"\nInstruction files -> {dest_dir}")
    for src_rel, dst_rel in pairs:
        src = REPO / src_rel
        if not src.exists():
            print(f"  {dst_rel:34} [missing-source]")
            continue
        dst = dest_dir / dst_rel
        existing = dst.read_text(errors="ignore") if dst.exists() else ""
        new_content, mode = compose_instruction(existing, src.read_text(errors="ignore"))
        verb = mode if apply else f"would-{mode}"
        print(f"  {dst_rel:34} [{verb}]")
        if apply:
            dst.parent.mkdir(parents=True, exist_ok=True)
            backup(dst)
            dst.write_text(new_content, encoding="utf-8")

def main():
    args = sys.argv[1:]
    apply = "--apply" in args
    with_community = "--community" in args
    instr_dir = None
    if "--instructions" in args:
        j = args.index("--instructions")
        nxt = args[j+1] if j + 1 < len(args) else None
        instr_dir = pathlib.Path(nxt).expanduser() if (nxt and not nxt.startswith("--")) else pathlib.Path.cwd()
    if "--targets" in args:
        i = args.index("--targets")
        sel = []
        for a in args[i+1:]:        # consume consecutive values until the next --flag
            if a.startswith("--"):
                break
            sel.append(a)
    else:
        sel = list(TARGETS)
    bad = [s for s in sel if s not in TARGETS]
    if bad:
        print("Unknown target(s):", bad, "\nValid:", list(TARGETS)); sys.exit(1)

    print(f"{'APPLY' if apply else 'DRY-RUN'} — Skillry install")
    print(f"Targets: {', '.join(sel)}   Community skills: {'yes' if with_community else 'no'}\n")
    for name in sel:
        install_target(name, TARGETS[name], apply, with_community)
    if instr_dir is not None:
        install_instructions(sel, instr_dir, apply)
    print("\nDone" + ("" if apply else " (dry-run — nothing written; re-run with --apply)"))
    if apply:
        print("Verify with: python3 tools/validate.py")

if __name__ == "__main__":
    main()

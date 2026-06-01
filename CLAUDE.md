# Skillry — Project Instructions

This file tells Claude Code (and compatible agents such as Codex, Copilot, and Antigravity)
how to behave when working **inside the Skillry repository**. Skillry is a curated,
permission-bounded, multi-platform library of agent skills and subagents. The bar here is
**correctness, safety, and attribution — not volume.** A few sharp skills beat many shallow ones.

## What this repo is

- `plugins/<department>/` — **the single source of truth.** Original skills live at
  `skills/<nn-name>/SKILL.md`; original subagents at `agents/<name>.md`. One plugin per department.
- `community/<source>/` — third-party skills redistributed under permissive licenses, each kept
  with its upstream `LICENSE` and a review note. This content is **attributed, not authored here.**
- `tools/` — `validate.py`, `install.py`, `build-marketplace.py`, `build-lock.py`, `skill-sync.py`.
- `.claude-plugin/marketplace.json` — the native Claude Code plugin marketplace (one entry/department).
- `registry/` — SHA-256 lockfiles for reproducible inventories.

## Operating rules

1. **One source of truth.** Author skills/agents once under `plugins/`. Never hand-edit generated
   platform output. After adding/removing a plugin, run `python3 tools/build-marketplace.py --apply`.
2. **Validate before you commit.** `python3 tools/validate.py` must report **0 failures**. CI runs
   the same checks; never merge red.
3. **Least privilege.** Every subagent declares an explicit `tools:` allowlist. Review/audit agents
   (reviewer, auditor, analyst, scout, researcher, gatekeeper, librarian) must **not** have `Edit`
   or `Write`. Do not widen a tool list without a concrete reason stated in the agent description.
4. **Real content, not templates.** A skill needs concrete `Procedure`, `Commands`,
   `Concrete checks`, `Required output`, and `Safety` sections — not a restated description.
   Keep every skill ≥60 lines of genuine substance.
5. **Attribution is mandatory.** Any third-party content goes under `community/<source>/` with its
   original `LICENSE`, and is listed in `NOTICE` + `THIRD-PARTY-NOTICES.md`. Only permissive
   licenses (MIT/ISC/BSD/Apache-2.0) may be redistributed. When in doubt, link — don't bundle.
6. **No personal/brand leakage.** No private names, emails, machine-specific home paths, or
   non-English content in public files. The validator enforces this and will fail the build.
7. **Safe by default.** Do not add `postinstall` hooks, network calls, or secret-touching code to
   skills or tooling. `skill-sync` stages imported skills as **disabled** — never auto-enable
   third-party code, and never run an upstream install script as part of import.

## Adding a skill (checklist)

- Create `plugins/<dept>/skills/<nn-name>/SKILL.md` with valid YAML frontmatter:
  `name:` (kebab-case, equal to the folder name minus the `NN-` prefix) and
  `description:` (starts with "Use when …", a concrete trigger).
- Body sections: `## Purpose` · `## When to use` · `## When not to use` · `## Procedure` ·
  `## Concrete checks` · `## Commands` · `## Common issues & anti-patterns` ·
  `## Required output` · `## Safety`.
- Run `python3 tools/validate.py` → 0 failures.

## Adding a subagent (checklist)

- Create `plugins/<dept>/agents/<name>.md` with `name`, `description`, and a least-privilege
  `tools:` line. Single responsibility. Review/audit roles are read-only (no `Edit`/`Write`).

## Installing (what users run)

- **Claude Code (native marketplace):**
  `/plugin marketplace add FluxonLab/Skillry` then `/plugin install <plugin>@skillry`.
- **Any platform (npm/npx, no global install):**
  `npx github:FluxonLab/Skillry install --apply --targets claude` (or `codex` / `copilot` /
  `antigravity`; add `--community` to include attributed third-party skills).
- **From a clone:** `python3 tools/install.py --apply --targets <platform>`.
  Dry-run is the default — nothing is written without `--apply`, and existing files are backed up.

## Commands

```bash
python3 tools/validate.py                 # structure + frontmatter + permission + attribution lint
python3 tools/build-marketplace.py --apply # regenerate .claude-plugin/marketplace.json
python3 tools/build-lock.py --apply        # regenerate registry/*-lock.json (SHA-256 inventory)
python3 tools/skill-sync.py discover <repo># scan an upstream repo (license + risk), then import/normalize
python3 tools/install.py --apply --targets claude
```

## Commit & PR style

Small, focused changes — one department or one concern per PR. State what changed, which platforms
it affects, and the verification you ran. PRs must pass `tools/validate.py` and CI.

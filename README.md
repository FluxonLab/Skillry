<div align="center">

<img src="https://raw.githubusercontent.com/FluxonLab/Skillry/main/assets/social-preview.png" alt="Skillry — multi-platform agent skills & subagents" width="680">

# Skillry

**Installable, permission-bounded, multi-platform agent skills & subagents — by [FluxonLab](https://fluxonlab.com).**

One source of truth. Install the same curated skills, subagents, and slash commands into
**Claude Code, OpenAI Codex, GitHub Copilot, and Google Antigravity (Gemini)** — with real
permission boundaries, a validation harness, and full upstream attribution.

[Quickstart](#quickstart) · [What's inside](#whats-inside) · [Multi-platform](#multi-platform) · [Safety](#safety--permissions) · [Build effort](#build-effort--transparency) · [Contributing](CONTRIBUTING.md)

[![CI](https://github.com/FluxonLab/Skillry/actions/workflows/validate.yml/badge.svg)](https://github.com/FluxonLab/Skillry/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.2.0-blue.svg)](package.json)
![Platforms](https://img.shields.io/badge/platforms-Claude%20%C2%B7%20Codex%20%C2%B7%20Copilot%20%C2%B7%20Gemini-7c3aed.svg)
![Skills](https://img.shields.io/badge/skills-125-success.svg)
![Subagents](https://img.shields.io/badge/subagents-73-success.svg)
![Departments](https://img.shields.io/badge/departments-18-success.svg)

</div>

---

## Why Skillry

Most Claude Code resource repos are **link lists** (you still copy files by hand) or are
**Claude-only**. Skillry is different on five axes:

| | Skillry | Typical "awesome" list | Typical CLI installer |
|---|:---:|:---:|:---:|
| Installs actual skill/agent **files** (not links) | ✅ | ❌ | ✅ |
| **Multi-platform** (Claude + Codex + Copilot + Gemini) | ✅ | ❌ | ❌ (Claude only) |
| Per-agent **permission boundaries** (least-privilege `tools`) | ✅ | ❌ | ⚠️ |
| **Validation harness** (structure + frontmatter lint + permission + lockfiles) | ✅ | ❌ | ⚠️ |
| **Skill-sync**: discover (license + risk scan), normalize (frontmatter + provenance), vet (staged, attributed, never auto-enabled) | ✅ | ❌ | ❌ |
| Native plugin marketplace (sha-pinned, reproducible) | ✅ | ❌ | ⚠️ |
| Full upstream **attribution** for redistributed content | ✅ | n/a | ⚠️ |

These directly reflect Anthropic's own guidance: least-privilege tools, single-responsibility
subagents, and auditing third-party skills before use.

## Quickstart

### Claude Code (native plugin marketplace — recommended)

```bash
# In Claude Code:
/plugin marketplace add FluxonLab/Skillry
/plugin install core-operations@skillry
```

Browse all departments with `/plugin marketplace` after adding.

### npm / npx (any platform, no clone, no publish needed)

```bash
# Runs straight from GitHub — no global install, no npm account required:
npx github:FluxonLab/Skillry install                                  # dry-run, all platforms
npx github:FluxonLab/Skillry install --apply --targets claude         # or: codex copilot antigravity
npx github:FluxonLab/Skillry install --apply --targets claude --community   # include attributed 3rd-party skills

# Or install the CLI globally (from GitHub — works today):
npm install -g github:FluxonLab/Skillry
skillry install --apply --targets claude codex
skillry validate
skillry update      # check for a newer release
```

> `npm install -g skillry` (the short registry name) will work once the package is published to
> the npm registry; until then use the `github:FluxonLab/Skillry` form above.

### Portable installer (from a clone)

```bash
git clone https://github.com/FluxonLab/Skillry
cd Skillry
python3 tools/install.py            # dry-run: shows what will be installed
python3 tools/install.py --apply --targets claude          # or: codex copilot antigravity
```

The installer rewrites machine-specific paths to your `$HOME` and backs up any existing
config (`*.bak-skillry`) before writing. Dry-run is the default. Verify with
`python3 tools/validate.py`.

## What's inside

- **125 original skills** across **18 departments** — concrete procedures, real commands,
  checklists, and safety rules (not generic templates); median ~150 lines of substance.
- **73 original subagents** with explicit `tools` allowlists and read-only vs. write scopes.
- **A curated `community/` set** — 98 skills + 49 agents from 6 permissively-licensed sources,
  redistributed with full attribution (MIT/ISC only — see [NOTICE](NOTICE) and
  [THIRD-PARTY-NOTICES](THIRD-PARTY-NOTICES.md)).
- **A flagship [`CLAUDE.md`](CLAUDE.md)** — a project-agnostic engineering operating manual
  (inspect-first, surgical changes, security, i18n + theme parity, dev-launch defaults, honest
  verification). It governs this repo and is written to be **copied into your own project** as a
  strong default: `cp CLAUDE.md /path/to/your/repo/CLAUDE.md`.

<details><summary>Departments (18)</summary>

Core Operations · Runtime & Local App · Backend & API · Frontend & Web Design ·
Mobile & Desktop · Gaming & Interactive Media · Database & Data · AI & Agent Systems ·
Security · Testing & QA · DevOps & Release · Product, Docs & Research ·
Documentation & Tech Writing · Data & ML / AI Engineering · Performance & Cost ·
Cloud & Infrastructure · Skill Library & Installation · Optional Specialists

</details>

## Multi-platform

One authored source → platform-correct output for each runtime — skills, agents, **and the
project behavior file** each tool actually reads:

| Platform | Skills | Agents | Behavior file | Install target |
|---|---|---|---|---|
| Claude Code | `SKILL.md` | `agents/*.md` | `CLAUDE.md` | `~/.claude/` |
| OpenAI Codex | `SKILL.md` | `agents/*.toml` | `AGENTS.md` | `~/.codex/` |
| GitHub Copilot | `SKILL.md` | `agents/*.agent.md` | `.github/copilot-instructions.md` | `~/.copilot/` + `~/.agents/` |
| Google Antigravity (Gemini) | `SKILL.md` | `agents/*.md` | `GEMINI.md` + `AGENTS.md` | `~/.gemini/antigravity/` |

The behavior files all derive from the canonical [`CLAUDE.md`](CLAUDE.md) (regenerate with
`python3 tools/build-agent-instructions.py --apply`). Drop the right one(s) into your own project
in the same command that installs the skills:

```bash
# install skills/agents AND place the behavior file for each target into ~/my-project:
python3 tools/install.py --apply --targets claude codex --instructions ~/my-project
```

**Your existing instructions are never clobbered.** If the project already has a `CLAUDE.md`/`AGENTS.md`,
Skillry's manual is **appended** under a clearly-marked block (your rules stay on top), plus a
**one-time, self-removing reconcile notice**: on the first session the agent announces the merge,
asks you how to resolve any duplicate/conflicting rules, applies your choice, and deletes the notice.
A `*.bak-skillry` backup is written first, and re-installs replace the prior block (no duplicates).

## Safety & permissions

- Every subagent declares a least-privilege `tools` allowlist; review agents get **no**
  Edit/Write tools.
- Redistributed third-party skills are kept in `community/` and were security-reviewed;
  anything that runs commands or needs external services is flagged.
- Sources whose license does **not** permit redistribution are excluded (not silently bundled).

## Repository layout

```
.claude-plugin/marketplace.json   # native Claude Code plugin marketplace (sha-pinnable)
plugins/<department>/             # one plugin per department: skills/ + agents/  (source of truth)
community/<source>/               # attributed third-party skills + their LICENSE
CLAUDE.md                         # canonical behavior file …
AGENTS.md · GEMINI.md · .github/copilot-instructions.md   # … generated for each other platform
tools/                            # validate, install, build-marketplace, build-agent-instructions, build-lock, skill-sync
registry/                         # skill/agent lock files (SHA-256)
docs/                             # guides
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Skills are validated in CI (structure + frontmatter + permissions);
PRs that add third-party content must include correct attribution and a license check.

## Build effort & transparency

Skillry wasn't auto-generated in an afternoon. It was researched, written, de-duplicated,
attribution-checked, and validated skill by skill, agent by agent — with a large fleet of AI
sub-agents doing the heavy lifting under close review.

| Phase | Model compute (tokens processed) |
|---|---:|
| Building Skillry (this public repo: research → conversion → validation harness → multi-platform tooling → v1.2.0) | **~1.8 billion** |
| The private library it was distilled from (estimated ~3× the above) | **~5.5 billion** |
| **Estimated total effort** | **~7.5 billion tokens** |

The ~1.8B figure for this repo is measured from real session usage — **~54M tokens of generated
output across ~3,300 model turns and 40+ orchestrated sub-agents** (the larger number includes
context-cache reads). The earlier figure for the original private library is a deliberately rough,
slightly-rounded-up estimate. We share it not to brag, but so it's clear that what you're
installing is the distilled result of a *lot* of iteration — not a thin template dump.

## Acknowledgments

Skillry was built with — and stress-tested across — multiple AI coding agents, which is also why
it targets all of them:

- **[Claude](https://www.anthropic.com/claude) / Claude Code** (Anthropic) — primary build agent.
- **[Codex](https://openai.com/codex)** (OpenAI) — used during construction and as a target platform.
- **[Gemini](https://deepmind.google/technologies/gemini/) / Antigravity** (Google) — used during construction and as a target platform.

The coding principles in [`CLAUDE.md`](CLAUDE.md) are distilled from public guidance by
**[Andrej Karpathy](https://karpathy.ai)**; safety/permission practices follow **Anthropic's**
published Claude Code guidance. Third-party skills under `community/` credit their upstream authors
in [NOTICE](NOTICE) and [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).

## License & credits

Original work © 2026 FluxonLab — [Çağrı Bozgeyik](https://cagribozgeyik.com) — under the [MIT License](LICENSE).
Redistributed content under `community/` keeps its upstream license; see
[THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md). Built and maintained by
**[FluxonLab](https://fluxonlab.com)**.

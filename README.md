<div align="center">

# OmniAgent

**Installable, permission-bounded, multi-platform agent skills & subagents — by [FluxonLab](https://fluxonlab.com).**

One source of truth. Install the same curated skills, subagents, and slash commands into
**Claude Code, OpenAI Codex, GitHub Copilot, and Google Antigravity (Gemini)** — with real
permission boundaries, a validation harness, and full upstream attribution.

[Quickstart](#quickstart) · [What's inside](#whats-inside) · [Multi-platform](#multi-platform) · [Safety](#safety--permissions) · [Contributing](CONTRIBUTING.md)

<!-- badges: add CI, license, version once published -->

</div>

---

## Why OmniAgent

Most Claude Code resource repos are **link lists** (you still copy files by hand) or are
**Claude-only**. OmniAgent is different on five axes:

| | OmniAgent | Typical "awesome" list | Typical CLI installer |
|---|:---:|:---:|:---:|
| Installs actual skill/agent **files** (not links) | ✅ | ❌ | ✅ |
| **Multi-platform** (Claude + Codex + Copilot + Gemini) | ✅ | ❌ | ❌ (Claude only) |
| Per-agent **permission boundaries** (least-privilege `tools`) | ✅ | ❌ | ⚠️ |
| **Validation harness** (smoke-check + frontmatter lint + lockfiles) | ✅ | ❌ | ⚠️ |
| **Skill-sync**: discover, normalize & vet new skills from GitHub | ✅ | ❌ | ❌ |
| Native plugin marketplace (sha-pinned, reproducible) | ✅ | ❌ | ⚠️ |
| Full upstream **attribution** for redistributed content | ✅ | n/a | ⚠️ |

These directly reflect Anthropic's own guidance: least-privilege tools, single-responsibility
subagents, and auditing third-party skills before use.

## Quickstart

### Claude Code (native plugin marketplace — recommended)

```bash
# In Claude Code:
/plugin marketplace add FluxonLab/OmniAgent
/plugin install core-operations@omniagent
```

Browse all departments with `/plugin marketplace` after adding.

### Any platform (portable installer)

```bash
git clone https://github.com/FluxonLab/OmniAgent
cd OmniAgent
python3 tools/install.py            # dry-run: shows what will be installed
python3 tools/install.py --apply --targets claude          # or: codex copilot antigravity
```

The installer rewrites machine-specific paths to your `$HOME` and backs up any existing
config before writing. Verify with `python3 tools/smoke-check.py`.

## What's inside

- **100+ original skills** across 14 departments — concrete procedures, real commands,
  checklists, and safety rules (not generic templates).
- **64 original subagents** with explicit `tools` allowlists and read-only vs. write scopes.
- **A curated `community/` set** of high-quality third-party skills, redistributed with full
  attribution (MIT/ISC only — see [NOTICE](NOTICE) and [THIRD-PARTY-NOTICES](THIRD-PARTY-NOTICES.md)).

<details><summary>Departments</summary>

Core Operations · Runtime & Local App · Backend & API · Frontend & Web Design ·
Mobile & Desktop · Gaming & Interactive Media · Database & Data · AI & Agent Systems ·
Security · Testing & QA · DevOps & Release · Product/Docs/Research ·
Skill Library & Installation · Optional Specialists

</details>

## Multi-platform

One authored source → platform-correct output for each runtime:

| Platform | Skills | Agents | Install target |
|---|---|---|---|
| Claude Code | `SKILL.md` | `agents/*.md` | `~/.claude/` |
| OpenAI Codex | `SKILL.md` | `agents/*.toml` | `~/.codex/` |
| GitHub Copilot | `SKILL.md` | `agents/*.agent.md` | `~/.copilot/` + `~/.agents/` |
| Google Antigravity (Gemini) | `SKILL.md` | `agents/*.md` | `~/.gemini/antigravity/` |

## Safety & permissions

- Every subagent declares a least-privilege `tools` allowlist; review agents get **no**
  Edit/Write tools.
- Redistributed third-party skills are kept in `community/` and were security-reviewed;
  anything that runs commands or needs external services is flagged.
- Sources whose license does **not** permit redistribution are excluded (not silently bundled).

## Repository layout

```
.claude-plugin/marketplace.json   # native Claude Code marketplace (sha-pinned)
plugins/<department>/              # one plugin per department: skills/ agents/ commands/
platforms/<platform>/             # generated, platform-specific output
community/<source>/                # attributed third-party skills + their LICENSE
tools/                            # installer, smoke-check, skill-sync
registry/                         # skill/agent lock files
docs/                             # guides
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Skills are validated in CI (frontmatter + smoke-check);
PRs that add third-party content must include correct attribution and a license check.

## License & credits

Original work © 2026 FluxonLab — [Çağrı Bozgeyik](https://cagribozgeyik.com) — under the [MIT License](LICENSE).
Redistributed content under `community/` keeps its upstream license; see
[THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md). Built and maintained by
**[FluxonLab](https://fluxonlab.com)**.

# Installing Skillry

Skillry ships **125 original, permission-bounded skills + 73 subagents** across 18
departments, plus an attributed `community/` set (98 skills + 49 agents from 6 MIT/ISC
sources). Install into one or more platforms.

## Option A — Claude Code native marketplace (recommended for Claude)

```bash
# inside Claude Code
/plugin marketplace add FluxonLab/Skillry
/plugin marketplace          # browse the 18 department plugins
/plugin install skillry-core-operations@skillry
/plugin install skillry-frontend-web-design@skillry
# ...install the departments you want
```

Marketplace installs are reproducible: pin a plugin to a commit SHA in
`.claude-plugin/marketplace.json` for version-locked installs.

## Option B — npm / npx (any platform, no clone)

```bash
# Runs directly from GitHub — no global install, no npm account needed:
npx github:FluxonLab/Skillry install                              # dry-run, all platforms
npx github:FluxonLab/Skillry install --apply --targets claude     # codex | copilot | antigravity
npx github:FluxonLab/Skillry install --apply --targets claude --community

# Or install the CLI globally:
npm install -g skillry
skillry install --apply --targets claude codex
skillry validate
```

## Option C — Portable installer (Claude, Codex, Copilot, Gemini/Antigravity)

```bash
git clone https://github.com/FluxonLab/Skillry
cd Skillry

# Preview (writes nothing):
python3 tools/install.py --targets claude codex copilot antigravity

# Install original skills + agents:
python3 tools/install.py --apply --targets claude

# Also include the attributed community skills:
python3 tools/install.py --apply --targets claude --community
```

Install locations per platform:

| Platform | Skills | Agents |
|---|---|---|
| Claude Code | `~/.claude/skills/<name>/SKILL.md` | `~/.claude/agents/<name>.md` |
| OpenAI Codex | `~/.codex/skills/<name>/SKILL.md` | `~/.codex/agents/<name>.toml` |
| GitHub Copilot | `~/.copilot/skills/<name>/SKILL.md` | `~/.copilot/agents/<name>.agent.md` |
| Google Antigravity | `~/.gemini/antigravity/skills/<name>/SKILL.md` | `~/.gemini/antigravity/agents/<name>.md` |

The installer **backs up** any existing file to `*.bak-skillry` before overwriting,
and converts each agent to the platform's native format (e.g. Codex `.toml`).

## Behavior files (CLAUDE.md / AGENTS.md / GEMINI.md / copilot-instructions)

Skillry also ships a project behavior file for every platform, all generated from the canonical
[`CLAUDE.md`](../CLAUDE.md). Add `--instructions <dir>` to drop the right one(s) into your project
in the same command that installs the skills (existing files are backed up):

```bash
# skills/agents + the behavior file each target reads, written into ~/my-project:
python3 tools/install.py --apply --targets claude codex --instructions ~/my-project
```

| Target | File written into your project |
|---|---|
| `claude` | `CLAUDE.md` |
| `codex` | `AGENTS.md` |
| `copilot` | `.github/copilot-instructions.md` |
| `antigravity` | `GEMINI.md` + `AGENTS.md` |

Maintainers: edit `CLAUDE.md`, then regenerate the rest with
`python3 tools/build-agent-instructions.py --apply` (CI fails if they drift).

## Verify

```bash
python3 tools/validate.py     # structure, frontmatter, least-privilege, attribution
```

## Discover & import new skills (skill-sync)

```bash
python3 tools/skill-sync.py discover https://github.com/<owner>/<repo>      # read-only audit
python3 tools/skill-sync.py import   https://github.com/<owner>/<repo> --apply
```

skill-sync only accepts permissively licensed sources, scans each skill for risk
signals, writes a `REVIEW.md`, and **stages** into `community/` for human review —
it never auto-enables anything.

## Uninstall

Remove the installed `<name>` directories/files from the platform locations above
(restore any `*.bak-skillry` backups), or for Claude Code:
`/plugin uninstall <plugin>@skillry`.

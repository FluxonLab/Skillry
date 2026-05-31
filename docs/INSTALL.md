# Installing OmniAgent

OmniAgent ships **100 original, permission-bounded skills + 65 subagents** across 14
departments, plus an attributed `community/` set. Install into one or more platforms.

## Option A — Claude Code native marketplace (recommended for Claude)

```bash
# inside Claude Code
/plugin marketplace add FluxonLab/OmniAgent
/plugin marketplace          # browse the 14 department plugins
/plugin install omniagent-core-operations@omniagent
/plugin install omniagent-frontend-web-design@omniagent
# ...install the departments you want
```

Marketplace installs are reproducible: pin a plugin to a commit SHA in
`.claude-plugin/marketplace.json` for version-locked installs.

## Option B — Portable installer (Claude, Codex, Copilot, Gemini/Antigravity)

```bash
git clone https://github.com/FluxonLab/OmniAgent
cd OmniAgent

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

The installer **backs up** any existing file to `*.bak-omniagent` before overwriting,
and converts each agent to the platform's native format (e.g. Codex `.toml`).

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
(restore any `*.bak-omniagent` backups), or for Claude Code:
`/plugin uninstall <plugin>@omniagent`.

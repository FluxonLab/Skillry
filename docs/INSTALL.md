# Installing Skillry

Skillry 3.0.0 ships **54 permission-bounded skill hubs + 73 subagents** across 18 departments,
plus an attributed `community/` set (3 skill hubs + 49 agents). Hubs route to merged references,
so the 223 skills of 2.x remain reachable under 57 names; see the 3.0.0 entry in
[`CHANGELOG.md`](../CHANGELOG.md) for where each former skill now lives. Install into one or
more platforms.

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
npx github:FluxonLab/Skillry install --apply --targets claude     # codex | cursor | copilot | antigravity
npx github:FluxonLab/Skillry install --apply --targets claude --community

# Or install the CLI globally (published on npm):
npm install -g skillry
skillry install --apply --targets claude codex
skillry validate
skillry update      # check for a newer release and see how to update
```

> The [npm package](https://www.npmjs.com/package/skillry) can lag this repository.
> Check `npm view skillry version` before relying on newer features. Use the
> `github:FluxonLab/Skillry` form (optionally pinned to a reviewed commit) for the
> repository version; a Git commit does not publish a new npm release.

## Option C — Portable installer (Claude, Codex, Cursor, Copilot, Gemini/Antigravity)

```bash
git clone https://github.com/FluxonLab/Skillry
cd Skillry

# Preview (writes nothing):
python3 tools/install.py --targets claude codex cursor copilot antigravity

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
| Cursor | `~/.cursor/skills/<name>/SKILL.md` | `~/.cursor/agents/<name>.md` |
| GitHub Copilot | `~/.copilot/skills/<name>/SKILL.md` | `~/.copilot/agents/<name>.agent.md` |
| Google Antigravity | `~/.gemini/antigravity/skills/<name>/SKILL.md` | `~/.gemini/antigravity/agents/<name>.md` |

The installer verifies source checksums and managed destination hashes before updating.
It refuses unmanaged collisions and user-modified files, and converts agents into each
platform format (for example Codex `.toml`). Preserve existing manifests when updating.

Cursor agents use native `name`, `description`, `model: inherit` and `readonly`
frontmatter. Source roles with `permissionMode: plan` stay read-only, including
reviewers that use shell inspection; Claude-only permission fields and model aliases
are not copied. Source body instructions remain intact. Native Cursor files take
precedence over compatibility copies discovered from other clients. Existing files
without a Cursor manifest remain collisions, not permission to overwrite them.
See Cursor's [skill discovery](https://cursor.com/docs/skills) and
[subagent format](https://cursor.com/docs/subagents).

## Project instruction files

Project instructions remain project-owned. The portable installer installs skills and
agents only; it does not copy, merge or generate AGENTS.md, CLAUDE.md, GEMINI.md or
Copilot instruction files. The former `--instructions` option is unsupported.

## Optional Jev advice

The optional Jev helper uses the existing library and does not activate with a normal
portable installation. See [Jev daily use and integration](JEV.md) for explicit setup,
data policy, budgets, client boundaries and rollback. It never grants tool permissions.

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

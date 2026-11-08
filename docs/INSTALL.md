# Installing Skillry

Skillry 3.4.0 ships **65 permission-bounded skill hubs + 73 subagents** across 18 departments,
plus an attributed `community/` set (3 skill hubs + 49 agents; 68 skill hubs and 122 subagents total). Hubs route to merged references,
so the 223 skills of 2.x remain reachable; see the 3.0.0, 3.1.0 and 3.2.0 entries in
[`CHANGELOG.md`](../CHANGELOG.md) for where each former skill now lives. Install into one or
more platforms.

**Prerequisites:** Node.js `>=16` (for `npx`/`skillry`), Git, and Python 3 (`Python 3.11+` or `tomli` for `tools/release-gate.py`).

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
npx github:FluxonLab/Skillry install --apply --targets claude     # codex | cursor | copilot | antigravity | opencode
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

## Option C — Portable installer (Claude, Codex, Cursor, Copilot, Antigravity, OpenCode)

```bash
git clone https://github.com/FluxonLab/Skillry
cd Skillry

# Preview (writes nothing):
python3 tools/install.py --targets claude codex cursor copilot antigravity opencode

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
| GitHub Copilot | `~/.copilot/skills/<name>/SKILL.md` | `~/.copilot/agents/<name>.agent.md` (native custom agent format) |
| Google Antigravity (app, `agy` CLI and standalone IDE) | `~/.gemini/config/skills/<name>/SKILL.md` | `~/.gemini/config/agents/<name>.md` (native agent format) |
| OpenCode | `~/.config/opencode/skills/<name>/SKILL.md` | `~/.config/opencode/agents/<name>.md` (subagent with a `permission` map) |

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

Antigravity agents use the native format: `name`, `description`, a `tools` list of
Antigravity tool names, `mcpServers: []`, `mainAgent: false`, `subagent: true`,
`model: inherit` and `commandExecutionPolicy`. Read-only roles (`permissionMode: plan`
or only read tools) get `view_file`, `grep_search`, `find_by_name` and `list_dir` with
commands off. Roles that edit get `replace_file_content`, `multi_replace_file_content`
and `write_to_file`, and roles with shell get `run_command` with commands in the
sandbox. Only tool names that load in the current CLI are written, because an unknown
name stops the agent. Releases before 3.2.3 installed into `~/.gemini/antigravity/`.
The app and the CLI do not read that folder. The standalone IDE reads
`~/.gemini/config/skills/` and still reads the old `skills/` folder as a fallback, so it
would list every skill twice. The next install therefore removes the files Skillry put
there that are still unchanged. A file you edited there stops the install and is named,
so you can move it first. See Antigravity's
[customization discovery](https://antigravity.google/docs/extend/customization-discovery/),
[skills](https://antigravity.google/docs/skills) and
[subagents](https://antigravity.google/docs/subagents).

Copilot agents use the native custom agent format: `name`, `description` and a `tools` list
of Copilot aliases (`read`, `search`, `edit`, `execute`, `agent`, `web`, `todo`). Copilot has
no permission mode, and a shell can change files, so read-only roles (`permissionMode: plan` or
only read tools) get only `read`, `search` and the web tools they declare. Claude-only fields
and Claude model names are left out, so the agent uses Copilot's default model. This is the
installed file's contract; whether Copilot's own permission prompts stop a file change has not
yet been checked in a live Copilot client. See GitHub's
[custom agents configuration](https://docs.github.com/en/copilot/reference/custom-agents-configuration).

The optional storage engine (`skillry storage`) runs on macOS and Linux. It relies on
POSIX file locks and `lsof`. On Windows it answers with an `unsupported_platform` error;
the installer and the skills work there.

OpenCode agents carry `description`, `mode: subagent` and a `permission` map. That is the
format OpenCode 1.19 applies; it ignores the newer `permissions` list, and OpenCode 2 still
reads the map. A role without `Edit`/`Write` gets `edit: deny`, a role without `Bash` gets
`bash: deny`, and read-only roles (`permissionMode: plan` or only read tools) get both. Web tools are denied unless the role declares them. OpenCode
also reads `~/.claude/skills`, so if you install both targets it sees each skill twice
and loads the copy in `~/.config/opencode/skills`. See OpenCode's
[skills](https://opencode.ai/docs/skills) and [agents](https://opencode.ai/docs/agents).

## Choosing what to install

By default every first-party department is installed. You can narrow that:

```bash
skillry list                                              # departments, skills, agents, installs
skillry install --apply --targets claude --departments security core-operations
skillry install --apply --targets opencode --skills repo-diagnostics --no-agents
skillry install --apply --targets claude --all            # back to everything
```

`--departments` installs the skills and agents of those departments. `--skills` installs the
named skills; next to `--departments` it adds them to the departments' skills. Agents follow
`--departments` (every agent when no department is named) unless you pass `--no-agents`. A
command that names departments or skills replaces both remembered filters.

Choices about departments, skills, community content and agents are remembered for each
target in `~/.skillry/manifests/selection.json`. A later `skillry install --apply` with no
choice flags keeps them. An update that would remove components you installed earlier stops
with a list; pass `--allow-removal` when that is what you want. For installs made before
3.3, the community choice is read from what the manifest lists.

## Checking and removing an install

```bash
skillry doctor                                  # compare installed files with their manifests
skillry uninstall --targets claude              # preview
skillry uninstall --targets claude --apply      # remove
```

`doctor` reports missing files and files changed locally, and exits non-zero when it finds
either. `uninstall` removes only files that still match what Skillry wrote. A file you
changed stays in place, is reported, and is no longer managed.

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
python3 tools/skill-sync.py import   https://github.com/<owner>/<repo>      # preview
python3 tools/skill-sync.py import   https://github.com/<owner>/<repo> --apply
```

skill-sync **stages** a source into `community/<source>/` for human review and never enables,
runs or makes anything executable. An import copies each skill's whole folder (references,
scripts, templates and other files), refuses symlinks, paths outside the skill and oversized
files, and stops when a relative link in a skill points at a file that is not there. Scripts
are listed in `REVIEW.md` with their risk signals, and `IMPORT-MANIFEST.json` records every file
with its hash and the source commit.

License detection is a candidate, not a verdict. A license file is `recognized` only when its
text matches the canonical MIT, ISC, BSD-2-Clause, BSD-3-Clause or Apache-2.0 text apart from
the copyright and title lines. Anything else that looks like one of them is `needs-review`, and
the import stops until a person has read it and passes
`--accept-license <sha256 of that file>`. An unknown license is never accepted. A skill whose
own license file differs from the repository's root license is listed as a conflict. This is a
technical check, not legal advice.

## Uninstall

Use `skillry uninstall --targets <platform...> --apply` (see "Checking and removing an install").
For a Claude Code marketplace install: `/plugin uninstall <plugin>@skillry`.

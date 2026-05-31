---
name: project-agent-bootstrap
description: Use when starting medium or large project work, standardizing project-local agent guidance, or creating minimal AGENTS.md, .codex/project.toml, project skills, or project agent overrides from the global skill and agent pool.
---

# Project Agent Bootstrap

## Purpose
Create or recommend a small project-local agent scaffold that connects a repository to the global Codex agent system without copying the full global skill archive.

## When to use
- The user asks to standardize a project for Codex agents, skills, or subagents.
- Medium or large project work begins and the repo has no clear `AGENTS.md` or `.codex/project.toml`.
- A project has recurring workflows that deserve local instructions, local skills, or local agent overrides.

## When not to use
- The task is a small one-off edit and existing repo guidance is enough.
- The user has not approved file creation and the task only needs a quick fix.
- The request would copy the full global skill archive into a project.

## Procedure
1. Inspect the repo for `AGENTS.md`, nested `AGENTS.md` or `AGENTS.override.md`, `GEMINI.md`, `CLAUDE.md`, `.agents/rules/`, `.agents/workflows/`, `.agents/skills/`, `.agent/rules/`, `.agent/workflows/`, `.agent/skills/`, `.codex/project.toml`, `.codex/skills/`, `.codex/agents/`, package manager files, scripts, framework markers, database markers, env file names, and -SSD sidecar folders for the same project name.
2. Summarize the current guidance state and whether a scaffold is needed.
3. Select a small active set from global skills and agents. Default to no more than seven skills and three subagents unless the user explicitly asks for broader coverage.
4. For missing project-local guidance, propose the scaffold first unless the user already requested creation.
5. If creating or overwriting files, back up existing `AGENTS.md`, `.codex/project.toml`, local skills, or local agent files before editing.
6. Keep project-local files concise and repo-specific. Reference global skill and agent names instead of copying their bodies.
7. Add project-local skills only for repeated project-specific procedures. Add project-local agents only for project-specific role boundaries or tool policies.
8. If the project needs database dumps, logs, research references, generated media, or downloaded reference repos, point those artifacts to the -SSD storage roots instead of copying them into the project.
9. Verify by listing created files and checking that TOML parses when a manifest is added.

## Commands
```bash
# Inventory existing project-local agent guidance before proposing a scaffold
ls -a 2>/dev/null | grep -E '^(AGENTS\.md|CLAUDE\.md|GEMINI\.md|\.codex|\.claude|\.agents|\.agent|\.github)$'
find . -maxdepth 2 \( -iname 'AGENTS*.md' -o -iname 'CLAUDE.md' -o -name '.codex' \) 2>/dev/null
# Detect package manager / framework to seed the manifest fields
ls package-lock.json pnpm-lock.yaml yarn.lock bun.lockb 2>/dev/null
cat package.json | jq '{name, packageManager, scripts}' 2>/dev/null
# Validate a TOML manifest after writing it (Python 3.11+: tomllib)
python3 -c "import tomllib; tomllib.load(open('.codex/project.toml','rb')); print('TOML ok')"
```
Keep the scaffold minimal — reference global skills/agents by name; never copy the archive into the project.

## Minimal scaffold
- `AGENTS.md`: project-specific package manager, commands, architecture notes, env rules, safety constraints, and final-report expectations.
- `.codex/project.toml`: machine-readable project manifest with selected global skills, selected global agents, verification commands, and known risks.
- `.codex/skills/<name>/SKILL.md`: optional, only for project-specific repeatable workflows.
- `.codex/agents/<name>.toml`: optional, only for project-specific agent behavior that should override or supplement global agents.
- Antigravity `GEMINI.md` and `.agents/rules/<name>.md`: optional, only for project-specific Antigravity behavior.
- Antigravity `.agents/workflows/<name>.md`: optional, only for recurring project workflows triggered on demand.

## Project manifest shape
Use this shape for `.codex/project.toml` when a project manifest is appropriate:

```toml
schema = "codex-project-agent/v1"
project_type = "unknown"
package_manager = "unknown"
framework = "unknown"
runtime = "unknown"

active_skills = []
active_agents = []
verification_commands = []
env_files = []
known_risks = []
local_overrides = []
```

## Required output
Return a concise report with: guidance found, SSD sidecar paths found or proposed, scaffold decision, selected skills, selected agents, files changed or proposed, verification, risks, and next safe commands.

## Safety
- Do not print secrets or env values.
- Do not run deploys, production migrations, seed resets, force pushes, or destructive git commands.
- Do not create duplicate apps, repos, frameworks, or full skill copies.
- Preserve existing project guidance and user changes.

## Safety checks
- Confirm the active workspace before creating project-local guidance.
- Back up existing instruction, skill, agent, workflow, or manifest files before overwriting them.
- Keep project scaffolds small and reference global skills by name instead of copying archive contents.

## Completion criteria
- Project-local guidance is either created, updated, or explicitly deemed unnecessary.
- Selected skills, selected agents, verification commands, SSD sidecar paths, and residual risks are recorded.
- Any changed TOML or Markdown instruction files are checked for basic syntax and readability.

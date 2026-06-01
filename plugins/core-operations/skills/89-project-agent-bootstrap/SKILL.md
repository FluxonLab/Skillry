---
name: project-agent-bootstrap
description: Use when starting medium or large project work, standardizing project-local agent guidance, or creating minimal AGENTS.md, .codex/project.toml, project skills, or project agent overrides from the global skill and agent pool.
---

# Project Agent Bootstrap

## Purpose
Create or recommend a small project-local agent scaffold that connects a repository to the global
Codex agent system without copying the full global skill archive. A well-constructed scaffold
gives every agent that opens the repo an unambiguous map of: the package manager and build
commands, the framework and runtime, the verification gate to run after changes, environment
variable rules, safety constraints, and which global skills and agents are relevant. Without this
map, agents default to global assumptions that may be wrong for the project, wasting context and
introducing errors. The scaffold stays small by referencing global skills and agents by name
rather than embedding their content.

## When to use
- The user asks to standardize a project for Codex agents, skills, or subagents.
- Medium or large project work begins and the repo has no `AGENTS.md`, `CLAUDE.md`, or `.codex/project.toml`.
- A project has recurring workflows that deserve local instructions, local skills, or local agent overrides.
- An agent repeatedly makes the same wrong assumption (wrong package manager, wrong build command, wrong test runner) because no project-local guidance exists to correct it.
- A mono-repo package needs its own sub-package guidance that is distinct from the root guidance.

## When not to use
- The task is a small one-off edit and the existing repo guidance is sufficient.
- The user has not approved file creation and the task only needs a quick fix.
- The request would copy the full global skill archive into a project — reference by name instead.
- The repo is a throwaway script or prototype with no recurring agent workflow.

## Procedure

1. **Inspect the repo for existing agent guidance.** Search for: `AGENTS.md`, nested `AGENTS.md` or
   `AGENTS.override.md`, `GEMINI.md`, `CLAUDE.md`, `.agents/rules/`, `.agents/workflows/`,
   `.agents/skills/`, `.codex/project.toml`, `.codex/skills/`, `.codex/agents/`, package manager
   lockfiles, scripts, framework config markers, database markers, env file names, and any
   sidecar storage folders for the same project name. Record what was found and what is missing.

2. **Summarize the current guidance state and the gap.** Determine whether the repo has: zero
   guidance (full scaffold needed), partial guidance (augment what exists), or full guidance (no
   action required). Be explicit about which files exist and which are absent.

3. **Select a minimal active set of global skills and agents.** Choose at most seven skills and
   three agents. The selection should be based on what the project actually needs — a Python API
   project does not need frontend skills; a static site does not need a database reviewer. Default
   selections for a typical web application:
   - Skills: `repo-diagnostics`, `implementation-plan`, `smoke-test-and-repair`, plus 1-2 specific
     to the project type (e.g., `database-and-prisma-review` for Prisma projects).
   - Agents: `repo-scout`, `implementation-worker`, plus one domain-specific (e.g., `database-persistence-reviewer`).

4. **Propose the scaffold before creating it, unless the user already requested creation.** Present
   the file list and their proposed content at a high level, then wait for confirmation. Creating
   agent instruction files has a direct effect on future agent behavior — do not create silently.

5. **Back up any existing guidance files before overwriting them.** For each existing file that
   would be modified, record its current path and content in the report as "backed up" before
   applying changes.

6. **Create or update the scaffold files.** Keep each file concise and repo-specific:
   - `AGENTS.md`: package manager, build/test/lint commands, architecture notes, env var rules,
     safety constraints, and the expected final-report format. Write it as instructions an agent
     should follow in this specific repo, not as generic advice.
   - `.codex/project.toml`: machine-readable manifest with selected skills, selected agents,
     verification commands, env files, and known risks. Validate TOML syntax immediately after writing.
   - `.codex/skills/<name>/SKILL.md`: only for project-specific repeatable procedures that do not
     exist in the global archive. Keep to one file per distinct workflow.
   - `.codex/agents/<name>.toml`: only for project-specific agent behavior that overrides or
     supplements a global agent — a different tool allowlist, a different safety constraint, or a
     project-specific procedure.

7. **Point large data artifacts at appropriate storage roots** rather than into the project repo.
   Databases, log archives, downloaded reference repos, generated media, and research packs belong
   outside the source tree. Document the expected external paths in `AGENTS.md` so agents know
   where to look without being told each time.

8. **Verify the scaffold.** After creating files: list them, confirm they are parseable, and confirm
   no global skill body was copied in verbatim. For `.codex/project.toml`, run the TOML parse
   check. For `AGENTS.md`, confirm it contains at least: the package manager name, the dev/build/test
   commands, and at least one safety constraint.

## Commands
```bash
# --- Step 1: detect existing guidance ---
ls -a 2>/dev/null | grep -E '^(AGENTS\.md|CLAUDE\.md|GEMINI\.md|\.codex|\.claude|\.agents|\.agent|\.github)$'
find . -maxdepth 3 \( -iname 'AGENTS*.md' -o -iname 'CLAUDE.md' -o -name '.codex' \) 2>/dev/null

# --- Package manager and framework detection ---
ls package-lock.json pnpm-lock.yaml yarn.lock bun.lockb 2>/dev/null
cat package.json 2>/dev/null | python3 -m json.tool | grep -E '"name"|"scripts"|"packageManager"|"engines"'

# Python
ls pyproject.toml poetry.lock uv.lock Pipfile requirements.txt 2>/dev/null

# Framework markers
ls next.config.* vite.config.* nuxt.config.* astro.config.* 2>/dev/null
ls manage.py artisan go.mod Cargo.toml 2>/dev/null

# Database markers
find . -maxdepth 3 -name 'schema.prisma' -o -name 'drizzle.config.*' -o -name 'knexfile.*' 2>/dev/null
ls migrations/ supabase/ 2>/dev/null

# --- Step 8: validate TOML after writing ---
python3 -c "import tomllib; tomllib.load(open('.codex/project.toml','rb')); print('TOML ok')"

# Confirm no global skill body was embedded (check for known verbatim section titles)
grep -r "## Procedure" .codex/skills/ 2>/dev/null | wc -l  # should match number of local skills only

# --- Enumerate created files ---
find .codex .agents -type f 2>/dev/null | sort
ls -la AGENTS.md CLAUDE.md 2>/dev/null
```

## Minimal scaffold

**`AGENTS.md`** (project instructions — human + agent readable):
```markdown
# AGENTS.md — <Project Name>

## Package manager
<pnpm | npm | yarn | bun | pip | poetry | uv | cargo | go mod>

## Key commands
- Install: `<install command>`
- Dev: `<dev server command>`
- Build: `<build command>`
- Test: `<test command>`
- Lint: `<lint command>`
- Typecheck: `<typecheck command>`

## Architecture notes
<1-3 sentences: what this project is, its primary framework, and its main data stores>

## Environment variables
Required at runtime: <list key names, no values>
See `.env.example` for the full list.

## Safety constraints
- Do not run migrations without a confirmed rollback plan.
- Do not force-push or rewrite git history on shared branches.
- Do not commit `.env` files or files named `*.key`, `*.pem`, or `*secret*`.
- <any project-specific constraint>

## Active skills
<comma-separated names from the global archive>

## Active agents
<comma-separated names from the global archive>

## Final report format
End all implementation work with: files changed, commands run, verification status, risks, and next safe step.
```

**`.codex/project.toml`** (machine-readable manifest):
```toml
schema = "codex-project-agent/v1"
project_type = "web-app"           # web-app | api | cli | library | mobile | desktop
package_manager = "pnpm"           # pnpm | npm | yarn | bun | pip | poetry | uv | cargo | go
framework = "next"                  # next | vite | nuxt | express | fastapi | django | rails | …
runtime = "node"                    # node | python | go | rust | ruby | java | …

active_skills = [
  "repo-diagnostics",
  "implementation-plan",
  "smoke-test-and-repair",
]

active_agents = [
  "repo-scout",
  "implementation-worker",
]

verification_commands = [
  "pnpm typecheck",
  "pnpm lint",
  "pnpm test --run",
]

env_files = [".env", ".env.local"]

known_risks = [
  "database migrations require advisory lock (see docs/migrations.md)",
]

local_overrides = []
```

## Concrete checks
- All existing guidance files (`AGENTS.md`, `CLAUDE.md`, `.codex/project.toml`) inventoried before any file is created or modified.
- Package manager confirmed from lockfile, not guessed.
- Dev, build, test, lint, and typecheck commands confirmed from `package.json` scripts or equivalent — not invented.
- At most seven skills and three agents selected; selection is justified by the project type.
- No global skill body copied verbatim into a project-local file.
- `AGENTS.md` contains at minimum: package manager, key commands, at least one safety constraint, and the final-report format.
- `.codex/project.toml` parses without error: `python3 -c "import tomllib; tomllib.load(open('.codex/project.toml','rb'))"`.
- Existing guidance files backed up (content recorded in the report) before overwriting.
- Large data artifacts (databases, logs, downloaded repos, generated media) pointed to external storage roots, not committed to the project.
- Created files listed explicitly in the report with their full paths.

## Common issues & anti-patterns
- **Copying global skill bodies into `.codex/skills/`.** This creates a maintenance fork — when the global skill is updated, the project copy drifts. Reference by name instead.
- **Over-selecting skills.** Listing every available skill in `active_skills` defeats the purpose; an agent loads all of them and has too much context to be useful. Select only what the project actually needs.
- **Hardcoding a wrong package manager.** Writing `npm` in `AGENTS.md` for a project that uses `pnpm` causes agents to rewrite the lockfile and break reproducible installs. Always confirm from the lockfile.
- **Silent creation.** Creating `AGENTS.md` or `.codex/project.toml` during an unrelated small task without proposing first — the user did not ask for new files and the content may not reflect their intent.
- **Vague architecture notes.** "This is a web app using modern frameworks" gives an agent no actionable information. Write what the agent needs to avoid the most common wrong assumption.
- **Missing verification commands.** An `AGENTS.md` that does not tell the agent how to confirm a change is correct forces the agent to guess — it will usually guess wrong.
- **Committing `.env` or secret files.** A bootstrap step that creates a `.env` template and accidentally commits it with real values. Always use `.env.example` for the template and `.gitignore` for real env files.
- **Scaffold that outlives its relevance.** A project grows; the `AGENTS.md` written at bootstrap still lists the original tech stack. Update the scaffold as part of significant architecture changes.

## Required output
Return a concise report with:
- **Guidance found:** list of existing files and their coverage.
- **Gap:** what was missing that justifies a scaffold.
- **Scaffold decision:** created, updated, or not needed — and why.
- **Selected skills:** names and one-line rationale for each.
- **Selected agents:** names and one-line rationale for each.
- **Files changed or proposed:** full paths of every file created or modified.
- **Verification:** TOML parse result, command list confirmed from scripts, no global skill body embedded.
- **Risks:** anything that might need updating as the project evolves.
- **Next safe commands:** the exact commands an agent should run first when opening this repo.

## Safety
- Do not print secrets or env values in any created file or in the report.
- Do not run deploys, production migrations, seed resets, force pushes, or destructive git commands as part of bootstrapping.
- Do not create duplicate apps, repos, frameworks, or full copies of the global skill archive.
- Preserve existing project guidance: always back up before overwriting, and record the backup in the report.
- Confirm the active workspace before creating project-local guidance — do not create files in the wrong directory.
- If unsure whether a scaffold is wanted, propose it and wait for explicit approval before creating files.

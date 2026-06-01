---
name: repo-diagnostics
description: Use when you need to inspect repositories, scripts, package managers, frameworks, entrypoints, configuration, databases, and reproducible failures before edits.
---

# Repo Diagnostics

## Purpose

Inspect a repository before any edit: package manager, scripts, framework, runtime, entrypoints, configuration, env shape, database markers, and the reproducible failure. The goal is to ground every repair or feature plan in real evidence from the actual files rather than assumptions — and to confirm exactly how to run, build, and test the project before changing a line of it. The review is read-only first and never echoes secret values.

## When to use

- A bug or failure is reported and the root cause is unknown — reproduce it before touching code.
- A task involves an unfamiliar repo, monorepo package, or project with no onboarding docs.
- The runtime, framework, or package manager is ambiguous and must be confirmed from lockfiles and config markers.
- An environment issue is suspected (missing env vars, wrong Node version, stale build artifacts, no lockfile).

## When not to use

- The task is unrelated to core operations work.
- The work would require production deploys, destructive data actions, or secret disclosure.
- You need a deep module and data-flow map rather than a health baseline — use `codebase-cartography`.
- A narrower skill or existing project instruction already covers the need.

## Procedure

1. **Identify the package manager from its lockfile** before running anything: `pnpm-lock.yaml` is pnpm, `yarn.lock` is yarn, `package-lock.json` is npm, `bun.lockb` is bun; for Python `poetry.lock`, `uv.lock`, `Pipfile.lock`, or `requirements.txt`; also `Cargo.toml`, `go.mod`, `Gemfile.lock`, `composer.json`. Multiple lockfiles is itself a red flag.
2. **Read the script surface** (`package.json` "scripts", `Makefile`, `Taskfile`, `justfile`) and note the real dev, build, test, lint, typecheck, and start entrypoints — record the exact command to run each.
3. **Detect framework and runtime** from config markers and pinned versions (see Concrete checks).
4. **Locate entrypoints:** `package.json` `main`/`module`/`exports`/`bin`, `src/index|main`, `app/`, `server.*`, Docker `CMD`/`ENTRYPOINT`, and `Procfile`.
5. **Map the env shape:** list every variable name from `.env.example`, `.env*`, or config (values redacted) and mark required versus optional.
6. **Find database and persistence markers:** `prisma/schema.prisma`, `drizzle.config.*`, `knexfile.*`, `migrations/`, `supabase/`, docker-compose database services, and ORM dependencies.
7. **Reproduce the reported failure** with the exact command and capture the full error and exit code before proposing any edit.

## Concrete checks

Package manager and runtime:
- Exactly one lockfile is present; multiple lockfiles signal an ambiguous package manager.
- The installed runtime matches the pin in `.nvmrc`, `.tool-versions`, `engines`, or `mise.toml`.
- `node_modules` (or the language equivalent) is present, or the install step is identified.

Scripts and entrypoints:
- The dev, build, test, lint, and typecheck scripts are identified with exact commands.
- The runtime entrypoint is located (`main`, `bin`, `server.*`, Docker `CMD`).

Framework and monorepo:
- The framework and its config file are identified from markers, not guessed.
- The monorepo tool and the package that owns the task are resolved.
- The dev server, build, and test commands are confirmed at the right workspace level.

Config, env, and data:
- Every env var name is listed with required versus optional marked; no values printed.
- No committed `.env` with real values; no secrets in tracked config.
- Database and migration markers are located; uncommitted migrations are flagged.
- Build artifacts (`dist/`, `.next/`, `out/`) are checked for freshness against source.

## Commands

```bash
# --- layout / state ---
# layout + working-tree state
ls -la && git status --short 2>/dev/null | head

# --- package manager ---
# which lockfiles exist (ambiguity check)
ls pnpm-lock.yaml yarn.lock package-lock.json bun.lockb poetry.lock uv.lock 2>/dev/null

# scripts + manager hints
cat package.json | jq '{scripts, packageManager, engines, workspaces}' 2>/dev/null

# --- runtime pins ---
# installed runtime versions
node -v; npm -v; pnpm -v 2>/dev/null; python3 --version

# pinned versions to compare against
cat .nvmrc .tool-versions 2>/dev/null

# --- env shape ---
# env var NAMES only (never values)
grep -hoE '^[A-Z0-9_]+=' .env.example .env 2>/dev/null | sort -u

# committed .env with values present (red flag)
git ls-files '.env' '.env.*' 2>/dev/null

# --- database markers ---
# schema / migration / ORM markers
fd -t f 'schema.prisma|drizzle.config|knexfile' . 2>/dev/null
ls migrations supabase 2>/dev/null

# --- monorepo ---
# workspace markers and which package owns the task
rg -n 'workspaces|packages/' package.json pnpm-workspace.yaml turbo.json nx.json 2>/dev/null | head

# --- framework markers ---
# frontend framework config
fd -t f 'next.config|vite.config|nuxt.config|astro.config|svelte.config|angular.json' . | head

# backend framework markers
rg -n 'express|fastify|nestjs|manage.py|artisan|config/routes.rb' . 2>/dev/null | head

# --- build artifacts ---
# built output and whether it is newer or older than source
ls -la dist build .next out 2>/dev/null

# --- entrypoints ---
# package entry definitions and binaries
cat package.json | jq '{main, module, exports, bin}' 2>/dev/null

# Docker / Procfile entrypoints
rg -n 'CMD|ENTRYPOINT' Dockerfile* 2>/dev/null; cat Procfile 2>/dev/null

# --- reproduce the failure ---
# run the failing command verbatim and keep the exit code
<failing-command>; echo "exit=$?"
```

## Common issues & anti-patterns

- **Guessing the package manager:** running `npm install` in a pnpm repo rewrites the lockfile and corrupts the dependency tree — always read the lockfile first.
- **Skipping reproduction:** proposing a fix before reproducing the failure leads to fixing the wrong thing; capture the exact command, output, and exit code first.
- **Trusting stale artifacts:** an old `dist/` or `.next/` can mask the real source state — confirm freshness before relying on a built output.
- **Runtime drift:** the repo pins Node 20 via `.nvmrc` but the shell is on Node 18 — many "works on my machine" failures trace here.
- **Echoing secrets:** dumping `.env` values into logs or a report leaks credentials; print key names only and redact values.
- **Ad-hoc commands over project scripts:** inventing a build command when `pnpm build` exists diverges from how the project is actually built and tested.
- **Ignoring the monorepo boundary:** running a command at the repo root when the task belongs to one workspace package, so the wrong build or test runs.
- **Missing lockfile:** no lockfile at all means installs are non-reproducible and every machine can resolve different versions.
- **Reproducing with the wrong command:** running `npm test` when the project uses `pnpm test` with a different script body, so the "failure" never reproduces and the real one is missed.
- **Editing before understanding the layout:** changing a file in a monorepo package that is not the one wired into the failing build, so the edit has no effect.
- **Assuming the framework:** treating a Vite project like Create React App (or vice versa) and running the wrong dev and build commands.
- **Ignoring the exit code:** reading only stdout and missing that the command exited non-zero, so a silent failure is mistaken for success.
- **Installing to "fix" a missing module:** running an install before confirming the lockfile and package manager, which can change resolved versions and mask the real cause.
- **Trusting a stale build:** serving an old `.next/` or `dist/` and concluding the source is broken when the artifact simply predates the fix.
- **Overlooking version pins:** running on the system default runtime instead of the pinned one, so a version-specific syntax or API failure looks like a code bug.

## Required output

Return: the package manager and version; the key scripts with the exact command to run each; the framework and runtime; the entrypoints; the env var names (required versus optional, values redacted); the database markers; the monorepo layout; and the reproduced failure (command plus error plus exit code). End with the smallest next safe command to make progress.

## Safety

- Read-only inspection first; do not install, build, or modify before the layout and failure are understood.
- Print env var names only; never echo values.
- Do not run vendor install scripts, resets, or deploys to "see what happens".
- Prefer the project's own scripts over ad-hoc commands.
- Flag a committed `.env` with real values as a secret-exposure finding, redacted.

## Completion criteria

Done means the package manager, scripts, framework, entrypoints, env shape, and database markers are identified from evidence; the reported failure is reproduced with its exit code; secrets are redacted to names only; and the next safe step is named.

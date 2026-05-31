---
name: repo-diagnostics
description: Use when you need to inspect repositories, scripts, package managers, frameworks, entrypoints, configuration, databases, and reproducible failures before edits.
---

# Repo Diagnostics

## Purpose
Use this skill to inspect repositories, scripts, package managers, frameworks, entrypoints, configuration, databases, and reproducible failures before edits. Run this before proposing any change so the repair or feature plan is grounded in real evidence, not assumptions.

## When to use
- A bug or failure is reported and the root cause is unknown — run diagnostics to reproduce it before touching code.
- A task involves an unfamiliar repo, monorepo package, or project that lacks onboarding docs.
- The runtime, framework, or package manager is ambiguous and you need to confirm it from lockfiles and config markers.
- An environment issue is suspected (missing env vars, wrong Node version, stale build artifacts, no lockfile).

## When not to use
- The task is unrelated to core operations work.
- The work would require production deploys, destructive data actions, or secret disclosure.
- A narrower skill or existing project instruction already covers the need.

## Procedure
1. Identify the package manager from its lockfile before running anything: `pnpm-lock.yaml`→pnpm, `yarn.lock`→yarn, `package-lock.json`→npm, `bun.lockb`→bun; Python `poetry.lock`/`uv.lock`/`Pipfile.lock`/`requirements.txt`; also `Cargo.toml`, `go.mod`, `Gemfile.lock`, `composer.json`.
2. Read the script surface (`package.json` "scripts", `Makefile`, `Taskfile`, `justfile`) and note the real dev/build/test/lint/typecheck/start entrypoints.
3. Detect framework + runtime from config markers and pinned versions (see checklist).
4. Locate entrypoints: `package.json` main/module/exports/bin, `src/index|main`, `app/`, `server.*`, Docker `CMD`/`ENTRYPOINT`, `Procfile`.
5. Map env shape: list every var **name** from `.env.example`/`.env*`/config (values redacted) and mark required vs optional.
6. Find database + persistence markers: `prisma/schema.prisma`, `drizzle.config.*`, `knexfile.*`, `migrations/`, `supabase/`, docker-compose DB services, ORM deps.
7. Reproduce the reported failure with the exact command and capture the full error + exit code before proposing any edit.

## Concrete checks
- Monorepo: `pnpm-workspace.yaml`, `turbo.json`, `nx.json`, `lerna.json`, `workspaces` in package.json → resolve which package owns the task.
- Version pins: `.nvmrc`, `.node-version`, `engines`, `.tool-versions`, `mise.toml` — a mismatch with the installed runtime is a common failure cause.
- Framework markers: `next.config.*`, `vite.config.*`, `nuxt.config.*`, `astro.config.*`, `svelte.config.*`, `angular.json`, `remix.config.*`; backend `nestjs`, `express`, `fastify`, `manage.py`, `artisan`, `config/routes.rb`.
- Build artifacts: `dist/`, `build/`, `.next/`, `out/` — check freshness vs source.
- Red flags: no lockfile, multiple lockfiles (ambiguous PM), `node_modules` absent, committed `.env`, uncommitted migrations.

## Commands
```bash
ls -la && git status --short 2>/dev/null | head
# scripts + manager hints
cat package.json | jq '{scripts, packageManager, engines, workspaces}' 2>/dev/null
# runtime versions
node -v; npm -v; pnpm -v 2>/dev/null; python3 --version
# env var NAMES only (never values)
grep -hoE '^[A-Z0-9_]+=' .env.example .env 2>/dev/null | sort -u
# reproduce the failure verbatim and keep the exit code
<failing-command>; echo "exit=$?"
```

## Required output
Return: package manager + version, key scripts (with the exact command to run each), framework/runtime, entrypoints, env var names (required vs optional, values redacted), database markers, monorepo layout, and the reproduced failure (command + error + exit code). End with the smallest next safe command to make progress.

## Safety checks
- Read-only inspection first; do not install, build, or modify before the layout and failure are understood.
- Print env var **names** only; never echo values.
- Do not run vendor install scripts, resets, or deploys to "see what happens."
- Prefer the project's own scripts over ad-hoc commands.

## Completion criteria
Done means the package manager, scripts, framework, entrypoints, env shape, and database markers are identified from evidence, the reported failure is reproduced with its exit code, and the next safe step is named.

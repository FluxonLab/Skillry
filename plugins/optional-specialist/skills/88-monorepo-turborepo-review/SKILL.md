---
name: monorepo-turborepo-review
description: Use when you need to review monorepo, Turborepo, workspace package, cache, build graph, and dependency boundaries.
---

# Monorepo & Turborepo Review

## Purpose
Review the structure, pipeline configuration, caching strategy, task dependency graph, shared package design, versioning, and build correctness of monorepos managed with Turborepo (and associated tools: pnpm/npm/yarn workspaces, Changesets, tsconfig path aliases).

## When to use
- Reviewing a `turbo.json` pipeline configuration and its `dependsOn`, `inputs`, `outputs` definitions.
- Auditing workspace package structure: shared UI libraries, utility packages, config packages.
- Evaluating cache hit rate issues: builds that should be cached but are not, or incorrect cache hits serving stale output.
- Reviewing Changesets versioning workflow for a monorepo publishing to npm.
- Checking `tsconfig.json` path aliases and composite project references in a monorepo.
- Evaluating task ordering and circular dependency issues across packages.

## When not to use
- Single-package repository — no workspace or build graph concerns apply.
- Nx-based monorepo — similar concepts but different config schema; note divergences.
- Docker/container build review unless specifically about how Docker interacts with the Turborepo build output.

## Procedure

### 1. Workspace structure
- Root `package.json` must define `workspaces` (npm/yarn) or `pnpm-workspace.yaml` must be present (pnpm) listing all package globs (e.g., `packages/*`, `apps/*`).
- Package naming convention: use a consistent scope prefix (`@myorg/ui`, `@myorg/config`, `@myorg/utils`) — avoid plain unscoped names for internal packages.
- Directory layout: separate `apps/` (deployable applications) from `packages/` (shared libraries) from `tooling/` (shared configs: eslint, tsconfig, prettier). This separation clarifies what is published vs consumed internally.
- Each package must have its own `package.json` with `name`, `version`, and `private: true` for non-published packages.
- Do not commit `node_modules/` in any package — a single root install via `pnpm install` / `npm install` must cover all workspaces.

### 2. `turbo.json` pipeline
- `turbo.json` at the root defines global pipeline; package-level `turbo.json` (v2) can extend or override.
- `dependsOn: ["^build"]` means: run `build` for all upstream dependencies first. This is the most critical field — missing it causes stale dependency output to be used.
- Task input/output definitions control cache correctness:
 - `inputs`: list file globs that, when changed, invalidate the cache. Default is all tracked files in the package — this is safe but conservative. Narrow inputs (e.g., `["src/**", "tsconfig.json"]`) improve cache hit rate.
 - `outputs`: list the files the task produces (e.g., `[".next/**", "dist/**"]`). Missing outputs means Turborepo cannot restore them from cache.
- `cache: false` on tasks like `dev` (watch mode) and `test:watch` — these must never be cached.
- `persistent: true` on long-running tasks (`dev`, `start`) — tells Turborepo not to wait for them to complete before running dependents.

### 3. Build dependency graph
- Run `turbo run build --dry=json` to inspect the task graph. Review:
 - Is the execution order correct? Shared packages must build before apps that consume them.
 - Are there any circular dependencies? Turbo will error on cycles — they must be resolved.
 - Are tasks being parallelized where possible? Packages with no dependency on each other should run concurrently.
- Circular dependency detection: if a package A imports from package B and package B imports from package A, the build order is undefined. Use `madge --circular` or `turbo run build --dry=json` to identify.
- Implicit dependencies: if an app imports a shared package but the app's `package.json` does not list it as a dependency, the task graph does not know to build it first. Always declare explicit `dependencies` in `package.json`, even for internal workspace packages.

### 4. Cache correctness
- **False cache hit** (serving stale output): occurs when `inputs` is too narrow and misses a file that actually affects the output. Test by: change a file that should affect the build, then run — if Turborepo reports a cache hit, the `inputs` definition is too narrow.
- **Cache miss on every run** (no hits): occurs when `inputs` inadvertently includes files that always change (e.g., generated files, `.env` files, build timestamps written to source). Narrow `inputs` to only source and config files.
- Environment variable handling: variables that affect the build (e.g., `NODE_ENV`, `NEXT_PUBLIC_API_URL`) must be listed in `turbo.json` under `globalEnv` or task-level `env`. Unlisted env vars are invisible to the cache key — changing them will not invalidate the cache, causing incorrect cached output to be served.
- `turbo.json` `globalDependencies`: list files whose change should invalidate all task caches (e.g., root `tsconfig.json`, root `.eslintrc`, `pnpm-lock.yaml`).

### 5. Remote cache
- Vercel Remote Cache (or self-hosted): enables CI cache sharing across machines and branches.
- Authenticate with `TURBO_TOKEN` and `TURBO_TEAM` environment variables in CI.
- Remote cache must be enabled in `turbo.json`: `"remoteCache": { "enabled": true }` (Turborepo v2).
- Cache signatures: by default the remote cache is unsigned. For security-sensitive builds, enable artifact signing with `--cache-dir` + signature verification to prevent cache poisoning.
- Never store secrets in task outputs that are cached — cached artifacts are accessible to anyone with the cache token.

### 6. Shared packages
- **Config packages** (`@myorg/tsconfig`, `@myorg/eslint-config`): must export their configs via `package.json` `exports` field, not just through file paths. Using direct paths breaks when packages are published.
- **UI packages** (`@myorg/ui`): decide on a compilation strategy — source distribution (consumer compiles) vs compiled distribution (pre-built). Source distribution is simpler for internal monorepos; compiled is required for external npm publishing.
- `tsconfig.json` in each package: should `extend` from a base config package (`@myorg/tsconfig/base.json`). Every package that is referenced by another must have `"composite": true` in its tsconfig for TypeScript project references to work.
- `package.json` `exports` map: if a package exports multiple entry points, define them in the `exports` field — do not rely on direct `dist/` path imports which are fragile and break with bundler resolution.
- Peer dependencies: shared packages should declare React, TypeScript, etc. as `peerDependencies`, not `dependencies`, to avoid duplicate installations in consuming apps.

### 7. Versioning and publishing with Changesets
- `.changeset/` directory must exist at the root; each PR that changes a publishable package adds a `.md` changeset file describing the change (patch/minor/major).
- `changeset version` bumps package versions and updates changelogs based on accumulated changesets.
- `changeset publish` publishes to npm — must only run in CI on a release branch after `changeset version` has committed the version bumps.
- `private: true` packages must never be published — verify the `publish` pipeline excludes all `private` packages.
- Linked packages: if packages share a version (e.g., `@myorg/ui` and `@myorg/tokens` always release together), configure them as `linked` in `.changeset/config.json`.
- Pre-release: Changesets supports pre-release mode (`changeset pre enter alpha`) — verify it is exited (`changeset pre exit`) before the final release.

### 8. CI integration
- Turborepo prune: use `turbo prune --scope=@myorg/app --docker` to generate a minimal lockfile for Docker builds that includes only the transitive dependencies of one app — drastically reduces Docker layer size.
- `--filter`: use `turbo run build --filter=@myorg/app...` to run only the build for one app and its dependencies in CI when only that app changed.
- `--since=origin/main`: `turbo run build --filter=...[origin/main]` runs tasks only for packages changed since the base branch — enables affected-only CI.
- `TURBO_CONCURRENCY`: set to the number of available CPU cores in CI to maximize parallelism.
- Verify the `turbo` binary version is pinned in `devDependencies` — floating `latest` causes unexpected behavior changes after Turborepo releases.

## Checklist

Workspace:
- [ ] `workspaces` or `pnpm-workspace.yaml` defined at root.
- [ ] Consistent `@scope/` naming for all internal packages.
- [ ] `apps/` and `packages/` directories separated.
- [ ] No `node_modules/` committed.

`turbo.json`:
- [ ] `dependsOn: ["^build"]` on all tasks that consume upstream output.
- [ ] `inputs` defined and excludes generated/always-changing files.
- [ ] `outputs` defined for all tasks that produce artifacts.
- [ ] `env` lists all environment variables that affect the build.
- [ ] `globalDependencies` includes root config files.
- [ ] `cache: false` on watch/dev tasks.

Cache:
- [ ] Remote cache configured with `TURBO_TOKEN` and `TURBO_TEAM` in CI.
- [ ] No secrets in cached task outputs.
- [ ] Cache invalidates correctly when env vars change.

Shared packages:
- [ ] `exports` field defined in each shared package's `package.json`.
- [ ] `"composite": true` in tsconfig for referenced packages.
- [ ] React/TypeScript in `peerDependencies`, not `dependencies`.

Versioning:
- [ ] `.changeset/config.json` present and configured.
- [ ] CI publishes only after `changeset version` commits.
- [ ] All `private: true` packages excluded from publish.

CI:
- [ ] `turbo` version pinned in `devDependencies`.
- [ ] `--filter=[origin/main]` used for affected-only runs.
- [ ] `turbo prune` used for Docker builds.

## Common issues & anti-patterns

- **Missing `dependsOn: ["^build"]`**: app builds before its shared package dependency finishes building — uses stale or missing compiled output. The build appears to succeed in CI but deploys broken code.
- **Unlisted env var in `turbo.json` `env`**: `NEXT_PUBLIC_API_URL` changes between staging and production but is not in `env`. Turborepo serves a cached build configured for staging to production.
- **Generated files in `inputs`**: a codegen step writes to `src/generated/` and `inputs` includes `src/**`. Every codegen run changes these files, busting the cache on every CI run.
- **Circular workspace dependency**: `@myorg/ui` imports from `@myorg/hooks`, and `@myorg/hooks` imports from `@myorg/ui`. Turborepo errors; the packages need to be restructured.
- **Implicit internal dependency**: an app uses `import { Button } from '@myorg/ui'` but `@myorg/ui` is not in the app's `package.json`. The task graph does not build `@myorg/ui` first — works locally (hoisted) but breaks in CI with strict install mode.
- **`private: true` package accidentally published**: if `changeset publish` is run without a proper package filter, an internal config package gets published to npm.
- **No remote cache in CI**: each CI run re-builds everything from scratch. A monorepo with 20 packages takes 15 min; with remote cache sharing, it takes 2 min on the second run.
- **`tsconfig` without `composite: true` in referenced package**: TypeScript project references fail to build incrementally — `tsc -b` rebuilds the entire dependency chain instead of using cached `.tsbuildinfo` files.

## Required output

Return a structured report with:
- **Summary**: pass / needs fixes / blocked (build correctness, cache poisoning risk, publish safety).
- **Task graph snapshot**: key tasks, their `dependsOn`, and whether the execution order is correct.
- **Cache analysis**: inputs/outputs correctness, env var coverage, estimated cache hit rate impact.
- **Findings table**: severity (critical / high / medium / low / info), category (pipeline / cache / packages / versioning / CI), file + line, description, remediation.
- **Shared package assessment**: exports map, tsconfig composite, peer dependency status.
- **Versioning safety**: changeset config, publish guard status.
- **Next handoff**: run `turbo run build --dry=json` to validate graph; test cache hit with a known-unchanged package; verify `--filter=[origin/main]` in CI pipeline.

## Safety

- Do not run `changeset publish` or `npm publish` during review.
- Do not modify `pnpm-lock.yaml` or `package-lock.json` — lockfile changes affect all packages and must go through the normal PR process.
- Do not clear the remote cache — it affects all team members' CI performance.
- If secrets are found in `turbo.json` `globalEnv` values (hardcoded, not just variable names) or in cached artifact directories, flag as critical.

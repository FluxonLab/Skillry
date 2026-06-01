---
name: smoke-test-and-repair
description: Use when you need to run safe install, build, lint, typecheck, test, startup, route checks, repair failures, and verify.
---

# Smoke Test And Repair

## Purpose

Run safe install, build, lint, typecheck, test, startup, and route checks; repair failures; and verify the result. Each gate runs in dependency order. When a gate fails, the smallest root-cause fix is applied and re-verified before the chain continues — no skipping ahead past a red gate, and no masking a real bug with a suppression comment.

## When to use

- A repo or branch must be confirmed fully green (install to typecheck to lint to build to tests to startup) before a review, demo, or merge.
- A failure was reported but its gate, exit code, and root cause have not been isolated — run diagnostics here before guessing a fix.
- After a refactor, dependency bump, or schema change, all downstream gates need a rapid pass to catch regressions.
- A CI pipeline failed and the failure must be reproduced and repaired locally with minimal-diff fixes before re-pushing.

## When not to use

- The task is unrelated to testing and QA work.
- The work would require production deploys, destructive data actions, or secret disclosure to proceed.
- A narrower skill already covers the need: `53-playwright-e2e-audit` for browser flows, `59-build-and-typecheck-review` for deep build config audits.

## Procedure

1. **Detect the package manager and scripts first.** Map lockfile to package manager (`package-lock.json` to npm, `pnpm-lock.yaml` to pnpm, `yarn.lock` to yarn, `bun.lockb` to bun); read `package.json` scripts. Use the project's own scripts; do not invent commands.
2. **Run the gates in dependency order and capture exit codes:** install, typecheck, lint, build, unit tests, app startup, key route/health check.
3. **On the first failure, stop and read the actual error.** Fix the *smallest* root cause (config, import, type, missing env) — prefer a code/config fix over adding dependencies.
4. **Re-run only the failed gate to confirm the fix,** then continue down the chain. Never skip ahead past a red gate.
5. **For startup/route checks,** boot the app and `curl` the health or primary route; assert the status code, then stop the process.
6. **Report every gate's status,** the fixes applied, and any gate intentionally skipped with its reason.

## Concrete checks

- The install used a reproducible flag (`npm ci`, `pnpm install --frozen-lockfile`, `yarn install --immutable`) so lockfile drift surfaces instead of hiding.
- Typecheck ran with no emit (`tsc --noEmit`) and exited 0.
- Lint exited 0 (or only documented, accepted warnings remain).
- Build produced an artifact and exited 0; no "compiled with errors" warning.
- Unit tests: pass count, fail count, and skipped count are reported — not just "tests passed".
- Startup: the process bound its port and the health/primary route returned 2xx within the timeout.
- Each applied fix is the smallest scoped diff; no `@ts-ignore`, `eslint-disable`, or `try/catch{}` was added to silence a real failure.
- No new dependency was added unless that genuinely is the fix.
- The build was run against a clean state when reproducibility was in doubt (no stale `dist/` or cache masking a failure).
- Any environment variable the app requires at startup was present (or its absence is reported as the cause of a failed startup/route gate), not silently defaulted.
- The diff after all fixes touches only files related to the failing gates; no unrelated formatting or rename churn was introduced.

## Commands or Templates

```bash
# npm shown; swap for pnpm/yarn/bun as detected by lockfile
set -e
npm ci                                  # reproducible install (fall back to npm install if no lockfile)
npm run typecheck || npx tsc --noEmit   # type gate
npm run lint                            # lint gate
npm run build                           # build gate
npm test                                # unit test gate (capture pass/fail counts)
```

```bash
# Startup + route smoke (kill the server even if curl fails)
npm run start & SRV=$!
for i in $(seq 1 15); do
  curl -fsS http://localhost:3000/health && break || sleep 1
done
curl -fsS http://localhost:3000/health || curl -fsS http://localhost:3000/
kill "$SRV" 2>/dev/null
```

```bash
# Detect package manager from lockfile
ls package-lock.json 2>/dev/null && echo npm
ls pnpm-lock.yaml 2>/dev/null && echo pnpm
ls yarn.lock 2>/dev/null && echo yarn
ls bun.lockb 2>/dev/null && echo bun
```

Gate table format for the report:

```
| Gate      | Command            | Status | Exit | Error summary           | Fix applied                  |
|-----------|--------------------|--------|------|-------------------------|------------------------------|
| install   | npm ci             | pass   | 0    | —                       | —                            |
| typecheck | tsc --noEmit       | fail   | 2    | TS2345 in api/user.ts:8 | narrowed param type          |
```

## Per-gate triage

When a gate fails, map the error to the smallest likely root cause before touching code:

| Gate | Common error | Likely root cause | Smallest fix |
|------|--------------|-------------------|--------------|
| install | `ERESOLVE` / peer conflict | mismatched peer dep range | align the one offending version; do not blanket `--force` |
| install | lockfile out of sync | `package.json` edited without re-lock | regenerate the lockfile, commit it |
| typecheck | `TS2307 cannot find module` | missing `@types/*` or wrong path alias | add the types package or fix `paths` |
| typecheck | `TS2345 not assignable` | real type bug or a too-wide input | narrow the type at the source, not with `as any` |
| lint | `no-unused-vars` | dead import after a refactor | remove the import |
| build | `Module not found` | case-sensitive path differs from disk | correct the import casing |
| test | one suite fails, rest pass | test depends on order/shared state | isolate the test's fixture |
| startup | `EADDRINUSE` | a previous run left the port bound | kill the stale process; ensure teardown |
| route | health returns 500 | a required env var is unset | set the env var; assert it at startup |

## Worked repair

The build gate fails with `Cannot find module './utils/Format'` while the file on disk is `format.ts`. Root cause: a case-sensitive import that works on macOS (case-insensitive FS) but breaks the Linux CI build. Smallest fix: change the import to `./utils/format`, re-run only the build gate to confirm green, then continue to the test gate. No dependency change, no config change — one character at the lowest wrong layer. This is also why "passes locally, fails in CI" is a recurring class: reproduce with the same OS/case behavior the CI uses.

## Common issues & anti-patterns

- **Masking instead of fixing.** Adding `// @ts-ignore` or `eslint-disable` to make a gate green hides a real defect. Fix the root cause at the lowest layer that is wrong.
- **Skipping a red gate.** Running tests while the build is broken yields meaningless results; stop at the first failure.
- **Upgrading dependencies to "fix" a failure.** A version bump that masks a usage error introduces churn and risk; only bump when the bump is genuinely the fix and is minimal.
- **`npm install` instead of `npm ci`.** Mutates the lockfile and hides drift that CI will later catch.
- **Reporting "tests passed" with no counts.** A suite that silently skipped 40 tests is not green.
- **Leaking a started server.** Forgetting to `kill` the dev server leaves a port bound and confuses the next run; always tear it down.
- **Opportunistic refactor.** Renaming or restructuring unrelated code while fixing one gate expands the diff and the blast radius.

## When a gate legitimately cannot run

Not every gate exists in every repo, and faking a pass is worse than an honest skip. Distinguish three cases and report them differently:

- **No such script.** The repo has no `lint` script. Status: `skip`, reason "no lint script defined". This is a finding worth noting (the project may want one), not a failure.
- **Blocked by a missing prerequisite.** Tests need a `DATABASE_URL` that is a secret you must not fabricate, or startup needs a service you cannot launch locally. Status: `skip`, reason "requires DATABASE_URL (not available; do not fabricate)". Report it as a blocker for full verification, not a pass.
- **Out of scope by safety policy.** A gate would require a deploy, a prod migration, or a destructive reset. Status: `skip`, reason "would require a forbidden action". Never run it.

A skipped gate must always carry a reason and must never be silently counted toward "all green". The final verdict is green only if every gate that *could* run passed and every skip is justified. If a skip blocks meaningful verification (e.g., tests cannot run at all), the overall verdict is "cannot confirm green", not "green".

## Required output

Return a gate table: `gate | command | status (pass/fail/skip) | exit | error summary | fix applied`. End with: overall green/red verdict, remaining failures with the smallest next step, and any gate skipped plus why. Include exit codes for failed gates.

## Monorepo and workspace notes

In a monorepo the root scripts may fan out to many packages, which changes how gates run:

- Detect the workspace tool: `pnpm-workspace.yaml`, a `workspaces` field in root `package.json`, `turbo.json`, or `nx.json`. The right command may be `pnpm -r build` or `turbo run build`, not a per-package `npm run build`.
- A single failing package fails the aggregate gate; isolate it with a filter (`pnpm --filter <pkg> test`, `turbo run test --filter=<pkg>`) before fixing, so you re-run only the affected package, not the whole graph.
- Respect the task graph: `turbo`/`nx` already encode build-before-test ordering and caching. Do not bypass it with raw per-package commands that ignore dependencies.
- A cached "pass" from a task runner is still a pass, but note when a gate was served from cache versus freshly executed if reproducibility is in question.

The gate order is unchanged; only the command shape and the failure-isolation step differ.

## Safety

- Only safe, local, non-destructive commands; no deploys, prod migrations, data resets, force pushes, or vendor install scripts.
- Use a reproducible install (`ci` / `--frozen-lockfile` / `--immutable`) to surface lockfile drift instead of hiding it.
- Redact secrets from captured logs and command output.
- Document any gate that could not be run rather than faking a pass.
- If a fix would require a secret, a deploy, or a destructive action, stop and report instead of proceeding.

## Completion criteria

Done means each gate ran (or was justifiably skipped), failures were repaired at the root with minimal scoped diffs and re-verified green, and the final gate table plus next steps are reported.

---
name: smoke-test-and-repair
description: Use when you need to run safe install, build, lint, typecheck, test, startup, route checks, repair failures, and verify.
---

# Smoke Test And Repair

## Purpose
Use this skill to run safe install, build, lint, typecheck, test, startup, route checks, repair failures, and verify. Each gate runs in dependency order, and when one fails the smallest root-cause fix is applied and re-verified before the chain continues — no skipping ahead past a red gate.

## When to use
- A repo or branch needs to be confirmed fully green (install → typecheck → lint → build → tests → startup) before a review, demo, or merge.
- An existing failure was reported but its gate, exit code, and root cause have not been isolated — run diagnostics here before guessing a fix.
- After a refactor, dependency bump, or schema change, all downstream gates need a rapid pass to catch regressions.
- A CI pipeline failed and the failure needs to be reproduced and repaired locally with minimal-diff fixes before re-pushing.

## When not to use
- The task is unrelated to testing and qa work.
- The work would require production deploys, destructive data actions, or secret disclosure.
- A narrower skill or existing project instruction already covers the need.

## Procedure
1. Detect the package manager and scripts first (lockfile → pm; `package.json` scripts). Use the project's own scripts; don't invent commands.
2. Run the gates in dependency order and capture exit codes: install → typecheck → lint → build → unit tests → app startup → key route/health check.
3. On the first failure, stop and read the actual error. Fix the **smallest** root cause (config, import, type, missing env) — prefer a code/config fix over adding dependencies.
4. Re-run only the failed gate to confirm the fix, then continue down the chain. Don't skip ahead past a red gate.
5. For startup/route checks, boot the app and `curl` the health or primary route; assert the status code.
6. Report every gate's status, the fixes applied, and any gate intentionally skipped (with reason).

## Gate sequence (use the detected PM)
```bash
# npm shown; swap for pnpm/yarn/bun as detected
npm ci # reproducible install (fall back to npm install if no lockfile)
npm run typecheck # or: npx tsc --noEmit
npm run lint
npm run build
npm test # or the project's unit runner
# startup + route smoke
npm run start & SRV=$!; sleep 3
curl -fsS http://localhost:3000/health || curl -fsS http://localhost:3000/
kill $SRV
```

## Repair rules
- Fix the root cause at the lowest layer that's wrong; avoid masking (don't `// @ts-ignore` a real type bug).
- Do not add or upgrade dependencies to "fix" a failure unless that genuinely is the fix and it's minimal.
- Keep diffs small and scoped to the failing gate; don't refactor opportunistically.
- If a fix needs secrets, a deploy, or a destructive action, stop and report instead.
- Re-run the gate after each fix; a fix isn't done until its gate is green.

## Required output
Return a gate table: `gate | command | status (pass/fail/skip) | error summary | fix applied`. End with: overall green/red, remaining failures with the smallest next step, and any gate skipped + why. Include exit codes for failed gates.

## Safety checks
- Only safe, local, non-destructive commands; no deploys, prod migrations, resets, force pushes, or vendor install scripts.
- Reproducible install (`ci`/`--frozen-lockfile`) to surface lockfile drift instead of hiding it.
- Redact secrets from captured logs/output.
- Document any gate that could not be run rather than faking a pass.

## Completion criteria
Done means each gate ran (or was justifiably skipped), failures were repaired at the root with minimal scoped diffs and re-verified green, and the final gate table plus next steps are reported.

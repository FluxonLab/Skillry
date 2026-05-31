---
name: release-readiness-check
description: Use when you need to decide whether a project is ready for demo, handoff, release, or deployment.
---

# Release Readiness Check

## Purpose
Use this skill to decide whether a project is ready for demo, handoff, release, or deployment. It produces a Go/No-Go verdict backed by a gate table — not an opinion — so blockers are concrete and actionable before anything ships.

## When to use
- A release, demo, or handoff is scheduled and you need to confirm the build, tests, migrations, and docs are all green.
- After a significant feature merge, before promoting a branch to a staging or production environment.
- A client or stakeholder demo is upcoming and the project must be verified to start cleanly from a fresh checkout.
- Before closing a sprint or milestone, to produce a structured list of blockers vs non-blocking follow-ups.

## When not to use
- The task is unrelated to core operations work.
- The work would require production deploys, destructive data actions, or secret disclosure.
- A narrower skill or existing project instruction already covers the need.

## Procedure
1. Confirm the release target (demo / handoff / internal / production) — the bar differs, so gate accordingly.
2. Run the verification gates in order and record pass/fail with evidence: install, typecheck, lint, build, tests, app startup, key route/health check.
3. Audit configuration & secrets: env documented, no secrets committed, no drift between `.env.example` and required vars.
4. Audit the data layer: migrations applied, `migrate status` clean, seed/fixtures safe, no destructive step pending.
5. Audit operability: README/run steps current, error/empty/loading states handled, logs useful, version bumped + changelog/release notes for a real release.
6. Issue a Go / No-Go verdict separating **blocking** issues from **non-blocking** follow-ups.

## Readiness checklist
- [ ] `build` succeeds clean from a fresh install
- [ ] `typecheck` + `lint` pass (or documented, justified waivers)
- [ ] Automated tests pass; critical paths have coverage
- [ ] App starts and the primary route/health endpoint responds
- [ ] No secrets in repo; `.env.example` matches required vars
- [ ] DB migrations applied; `prisma migrate status` (or equivalent) clean
- [ ] Run/install instructions verified on a clean checkout
- [ ] Error, empty, and loading states handled in the UI
- [ ] Version bumped + release notes / changelog (real releases)
- [ ] Rollback path known for the deploy target

## Commands
```bash
<pm> install --frozen-lockfile # reproducible install (npm ci / pnpm i --frozen-lockfile)
<pm> run typecheck && <pm> run lint
<pm> run build
<pm> test
# startup + route smoke
<pm> run start & sleep 3; curl -fsS http://localhost:3000/health || curl -fsS http://localhost:3000/
npx prisma migrate status 2>/dev/null
```

## Required output
Return a **Go / No-Go** verdict, the gate table (`gate | command | result | evidence`), the readiness checklist with each item ticked or flagged, a **blocking** list and a **non-blocking** list, and the next safe command to close the top blocker. Do not deploy.

## Safety checks
- Read/verify only; this skill does not deploy, migrate production, or reset data.
- Run reproducible installs (`ci`/`--frozen-lockfile`), not loose installs that mask lockfile drift.
- Redact secrets in all evidence.
- A failing or unrun gate is a No-Go until resolved or explicitly waived by the owner.

## Completion criteria
Done means every gate was run (or its absence justified), the checklist is fully evaluated, blocking vs non-blocking issues are separated, and a clear Go/No-Go verdict with the next action is recorded.

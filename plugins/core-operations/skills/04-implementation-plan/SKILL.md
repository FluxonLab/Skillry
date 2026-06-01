---
name: implementation-plan
description: Use when you need to turn goals into file-level plans with risks, migration steps, test plan, rollback path, and acceptance criteria.
---

# Implementation Plan

## Purpose
Turn a goal into a file-level execution plan that another engineer or agent can run without follow-up questions. The plan names every file that changes, sequences the work so the tree stays green after each step, isolates risky operations (schema migrations, renames, dependency bumps) onto their own reversible steps, and binds every acceptance criterion to a concrete verification command. The output is a contract, not a sketch: ambiguity left in the plan becomes rework or a broken build during execution.

## When to use
- A feature or fix spans multiple files or layers and needs ordered, verifiable steps before anyone writes code.
- The work includes a schema migration, a dependency major-version bump, or a cross-module rename where a misstep loses data or breaks the build for the team.
- The goal is clear but the path is not — planning surfaces hidden coupling and orders it safely before execution.
- A handoff is imminent and the plan must serve as the authoritative execution contract for another developer or agent.
- The change has a non-trivial rollback story (anything touching persisted data, public APIs, or deploy topology).

## When not to use
- The task is a one-line fix in a leaf function with full test coverage and no external callers — just make the change.
- The work requires production deploys, destructive data actions, or secret disclosure (gate those explicitly instead).
- A narrower skill or an existing project runbook already covers the exact need.
- Requirements are still undefined — clarify the goal first; a plan built on a vague goal plans the wrong work.

## Procedure
1. **Restate the goal in one sentence** and pin acceptance criteria as a verifiable checklist before touching anything. Each criterion must be observable (a passing test, a 200 response, a row count), not a feeling ("works well").
2. **Inventory the affected surface.** Use search to find every caller, importer, and config reference. Record each file as new / edit / delete with a one-line reason. Run `git grep -n "<symbol>"` and `rg -n "<route|env-var|table>"` so the inventory is evidence-based, not guessed.
3. **Order the steps so each one leaves the repo building and testable.** A step that compiles but has red tests is not a valid stopping point. Put any data/schema migration, public-API change, or rename on its own dedicated step.
4. **Write the test plan per criterion.** For each acceptance item, name the unit, integration, e2e, or manual check that proves it, and the exact command to run it (`npm test -- path/to/spec`, `pytest tests/test_x.py::test_y`).
5. **Define the rollback path for every irreversible-ish step** — down migration, revert commit SHA, feature-flag kill switch, or restore-from-backup. A migration with no down path is a blocking gap in the plan.
6. **Build the risk register:** what could break, likelihood (low/med/high), blast radius (one route / one service / all users), and the mitigation that lowers it.
7. **State scope boundaries explicitly.** List what is intentionally out of scope so execution does not drift into opportunistic changes.
8. **Dry-run the plan mentally as the executor.** If any step needs a decision you have not made, resolve it now or mark it a blocking unknown.

## Plan template
```md
# Plan: <goal in one sentence>

## Acceptance criteria
- [ ] <observable outcome 1 — how it is verified>
- [ ] <observable outcome 2 — how it is verified>

## File-level changes
| File | Change | Why |
|------|--------|-----|
| src/x.ts | edit | add validation before persist |
| src/y.ts | new   | new repository method |
| prisma/schema.prisma | edit | add nullable column (backfilled step 4) |

## Steps (each leaves the tree green)
1. <step> — verify: <exact command>
2. <migration step> — verify: <command> — rollback: <down migration / revert SHA>

## Test plan
- Unit: <files> | Integration: <files> | E2E: <flow> | Manual: <steps>

## Risks & mitigations
| Risk | Likelihood | Blast radius | Mitigation |
|------|-----------|--------------|------------|

## Rollback
<exact steps: revert commit, run down migration, disable flag>

## Out of scope
- <explicitly excluded item>
```

## Concrete checks
- Every acceptance criterion maps to at least one named test or manual check with a runnable command.
- No step leaves the build broken or tests red as a "temporary" intermediate state.
- Schema/data migrations are isolated on their own step, reversible (or backed up), and idempotent on re-run.
- Each step names its exact verification command, never "test it" or "make sure it works."
- Every irreversible-ish step (migration, rename, dependency bump, public-API change) has an explicit rollback line.
- Scope is bounded: out-of-scope items are listed, not silently folded in.
- The file inventory was produced from search output, not assumption.
- The sequencing follows a named pattern (expand/contract, branch-by-abstraction, strangler, parallel change) where one applies.
- The first step is explicitly named so the executor knows where to start.

## Commands
```bash
# Inventory the change surface from evidence, not memory
git grep -n "functionToChange" -- '*.ts' '*.tsx'
rg -n "POST /api/orders|ORDER_TABLE|orders\b" src/

# Confirm the baseline is green before planning execution
git status --porcelain                 # working tree clean to start
npm run typecheck && npm run lint       # or: tsc --noEmit / ruff check .
npm test -- --watch=false               # baseline test pass/fail count

# Size the blast radius of a rename or signature change
git grep -l "OldClassName" | wc -l      # number of files that import it

# Preview a migration's generated SQL before committing to the step
npx prisma migrate diff \
  --from-schema-datasource prisma/schema.prisma \
  --to-schema-datamodel prisma/schema.prisma --script

# Verify the plan is reversible: confirm a clean revert target exists
git log --oneline -1                    # record the SHA to revert to
```
```bash
# Confirm the test commands in the plan actually exist and run
jq -r '.scripts | keys[]' package.json    # which npm scripts are real
rg -n "def test_|it\(|describe\(" tests/ | wc -l   # is there a suite to extend?

# For a dependency bump step, capture the before/after for the plan's risk row
npm ls <pkg>                             # current resolved version
npm view <pkg> versions --json | jq '.[-5:]'   # candidate target versions
npx npm-check-updates <pkg>              # what the bump would change
```

## Worked example (a filled plan, abbreviated)
```md
# Plan: add idempotent "resend receipt" endpoint

## Acceptance criteria
- [ ] POST /receipts/:id/resend returns 202 — verify: integration test resend.spec.ts
- [ ] Calling it twice sends exactly one email — verify: test asserts mailer called once
- [ ] Unknown id returns 404 — verify: test asserts 404 body

## File-level changes
| File | Change | Why |
|------|--------|-----|
| src/routes/receipts.ts | edit | add route + validation |
| src/services/receipt.ts | edit | dedup via idempotency key |
| migrations/0042_receipt_sends.sql | new | sent-log table for dedup |

## Steps (each leaves the tree green)
1. Add migration for receipt_sends — verify: prisma migrate status — rollback: down migration drops table
2. Add service dedup logic + unit test — verify: npm test -- receipt.service
3. Wire the route + validation + integration test — verify: npm test -- resend.spec

## Risks & mitigations
| Risk | Likelihood | Blast radius | Mitigation |
| double email on race | med | one user | unique index on (receipt_id) in send-log |

## Rollback
Revert the feature commit; run the down migration for 0042.

## Out of scope
- Receipt PDF re-rendering (separate ticket)
```

## Sequencing patterns (pick the right order)
- **Expand / migrate / contract** for schema or API changes: add the new column/field (expand), backfill and dual-write, switch readers, then drop the old (contract) in a later release. Never expand and contract in one deploy.
- **Branch by abstraction** for swapping an implementation: introduce an interface, route through it, build the new implementation behind it, flip the wiring, delete the old.
- **Strangler** for replacing a subsystem: stand up the new path alongside the old, move call sites one at a time, retire the old path when traffic is zero.
- **Parallel change** for a signature change with many callers: add the new signature, migrate callers in batches, remove the old signature once usage hits zero.

## Common issues & anti-patterns
- **Step that breaks the build "temporarily."** Splitting a rename across two steps where step 1 leaves the tree uncompilable. Each step must be independently shippable.
- **Acceptance criteria that are not observable.** "Improve performance" with no metric. Replace with "p95 of `GET /search` under 200ms measured by `wrk -d10s`."
- **Migration with no down path.** A `DROP COLUMN` planned with no backup and no restore step — this is a data-loss landmine. Plan additive migration + backfill + later cleanup instead.
- **Guessed file inventory.** Listing the files you remember rather than the files search proves are affected — the missed caller breaks at runtime.
- **Scope creep baked into the plan.** Folding a formatting sweep or a "while we're here" refactor into a feature plan, inflating the diff and the risk.
- **Combining a migration and code change in one step.** If the deploy half-applies, you cannot tell which half failed. Separate schema from code.
- **Test commands that do not exist.** Writing "verify: npm run e2e" when there is no `e2e` script. Confirm every verification command is real before the plan ships.
- **A plan with no first step.** Ending with a list but not naming what to run first leaves the executor guessing where to start. Always point to step one.
- **Estimating instead of measuring the surface.** "Probably touches a few files" is not an inventory. Run the search; list the files.

## Required output
Return the filled plan: the one-sentence goal, the acceptance checklist, the file-level change table, ordered steps with per-step verification commands, the test plan, the risk register, the rollback path, and the out-of-scope list. Flag every unknown that must be resolved before execution begins, and name the single first step the executor should run.

## Safety
- Planning only — do not implement until the plan is reviewed and approved.
- No destructive migration appears in the plan without a backup step and a rollback step attached.
- Keep the change in-place; do not plan a parallel app, repo, or framework unless explicitly required.
- Mark any step that needs secrets, production deploys, or external services as gated and call out the approval needed.
- Do not include real secret values in the plan; reference env var names only.

## Completion criteria
Done means the goal, acceptance criteria, evidence-based file inventory, ordered and individually-verifiable steps, test plan, risk register, and rollback path are all written, scope is bounded, every unknown is flagged, and a different executor could follow the plan end to end without asking a question.

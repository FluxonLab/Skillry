---
name: implementation-plan
description: Use when you need to turn goals into file-level plans with risks, migration steps, test plan, rollback path, and acceptance criteria.
---

# Implementation Plan

## Purpose
Use this skill to turn goals into file-level plans with risks, migration steps, test plan, rollback path, and acceptance criteria. The output must be detailed enough that a different engineer or agent could execute it without follow-up questions.

## When to use
- A feature or fix spans multiple files or layers and needs ordered, verifiable steps before anyone starts coding.
- The work includes a schema migration, dependency upgrade, or rename where a misstep could lose data or break the build for others.
- The goal is well-defined but the path is uncertain — planning surfaces hidden dependencies and sequences them safely before execution begins.
- A handoff is imminent and the plan will serve as the authoritative execution contract for another developer or agent.

## When not to use
- The task is unrelated to core operations work.
- The work would require production deploys, destructive data actions, or secret disclosure.
- A narrower skill or existing project instruction already covers the need.

## Procedure
1. Restate the goal in one sentence and pin the acceptance criteria as a verifiable checklist before touching anything.
2. Inventory the affected surface: every file/module the change will touch and why (new / edit / delete).
3. Sequence the work into ordered steps where each step leaves the repo building and testable; put any data/schema migration on its own step.
4. Write the test plan: which unit/integration/e2e/manual checks prove each acceptance criterion.
5. Define the rollback path for every irreversible-ish step (migration, rename, dependency bump).
6. Build the risk register: what could break, likelihood, blast radius, mitigation.
7. Produce a plan a different engineer/agent could execute without guessing.

## Plan template
```md
# Plan: <goal>
## Acceptance criteria
- [ ] <observable outcome 1>
- [ ] <observable outcome 2>

## File-level changes
| File | Change | Why |
|------|--------|-----|
| src/x.ts | edit | ... |
| src/y.ts | new | ... |

## Steps (each leaves the tree green)
1. <step> — verify: <command/check>
2. <migration step> — rollback: <how>

## Test plan
- Unit: <which> Integration/E2E: <which> Manual: <which>

## Risks & mitigations
| Risk | Likelihood | Blast radius | Mitigation |

## Rollback
<exact steps / revert commit / down migration>
```

## Concrete checks
- Every acceptance criterion maps to at least one test or manual check.
- No step leaves the build broken or tests red as a "temporary" state.
- Schema/data migrations are isolated, reversible (or backed up), and idempotent.
- Each step names the exact verification command, not "test it."
- Scope is bounded: out-of-scope items are listed explicitly, not silently included.

## Required output
Return the filled plan: goal, acceptance checklist, file-level change table, ordered steps with per-step verification, test plan, risk register, and rollback path. Flag unknowns that must be resolved before execution.

## Safety checks
- Planning only; do not implement until the plan is approved.
- No destructive migration without a backup + rollback step in the plan.
- Keep the change in-place; do not plan a parallel app/repo unless explicitly required.
- Mark any step needing secrets, deploys, or external services as gated.

## Completion criteria
Done means the goal, acceptance criteria, file-level changes, ordered + verifiable steps, test plan, risks, and rollback are all written, and another executor could follow the plan without further guessing.

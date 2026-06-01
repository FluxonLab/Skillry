---
name: codex-final-execution-prompt
description: Use when you need to write strict final execution prompts for Codex, Claude, Copilot, or other coding agents.
---

# Codex Final Execution Prompt

## Purpose

Write strict final execution prompts for Codex, Claude, Copilot, or other coding agents. A final execution prompt has one singular, bounded goal; every instruction in it is testable; and a stop condition exists for every ambiguous or blocked state so the agent never silently guesses. The output is a self-contained prompt — exact context, exact changes, hard constraints, verification commands, acceptance checklist, output contract, and stop conditions — ready to paste into a coding agent.

## When to use

- A well-understood task must be delegated to a coding agent and the instruction set must be unambiguous enough to execute without back-and-forth.
- A previous agent run went off-scope, touched forbidden files, or failed to verify its work — write a tighter prompt with explicit hard constraints and stop conditions before re-running.
- A plan exists (from `04-implementation-plan`) and now needs translating into a strict agent-executable format with exact file/change pairs and verification commands.
- A task involves risk (migration, rename, dependency change) and the prompt needs baked-in forbidden-action lists and rollback conditions to prevent silent damage.

## When not to use

- The task is unrelated to product, docs, and research work.
- The work would require production deploys, destructive data actions, or secret disclosure.
- A narrower skill already covers the need: `63-md-spec-generator` for human-facing specs and handoff packs, `04-implementation-plan` for the planning phase that precedes prompt-writing.

## Procedure

1. **Lock the context.** Target repo/paths, package manager, framework, runtime, and the exact, singular goal. One job, clearly bounded — not a basket of loosely related asks.
2. **Enumerate constraints up front.** What must not change, files/areas off-limits, style and conventions to follow, and forbidden actions (deploys, destructive git/DB, new deps, scope creep).
3. **Specify the work concretely.** Exact files to touch, the change in each, and the order if it matters.
4. **Specify verification.** The precise commands the agent must run and the expected green result for each.
5. **Define acceptance criteria** as a checklist the agent must satisfy before declaring done.
6. **Define the output contract:** what the agent must report back (diff summary, commands run, results, residual risks).
7. **Strip ambiguity.** No "etc.", no "improve as you see fit" — every instruction is testable.

## Concrete checks

- The goal is singular and testable, not a bundle of related tasks.
- Every "do this" item names a concrete file and change, not a vibe ("clean up the code").
- Verification commands are exact and each has an expected result (`tsc --noEmit` → 0 errors).
- Forbidden and destructive actions are listed explicitly (no deploys, no `git push --force`, no `DROP`, no new dependencies).
- A stop condition exists for every blocked or ambiguous state, so the agent reports instead of guessing.
- The output contract is specified so the result is reviewable (files changed, commands run, residual risks).
- Off-limits paths are named, not implied.
- Secrets are referenced by env-var name only; no values are embedded.

## Commands or Templates

```md
# Task: <single, specific goal>

## Context
- Repo/paths: <...>   PM: <npm/pnpm/yarn/...>   Framework/runtime: <...>
- Relevant files: <path:line ...>

## Do exactly this
1. <change> in <file>
2. <change> in <file>

## Constraints (hard)
- Do NOT: deploy, run prod migrations, reset/seed data, force push,
  add dependencies, or touch <off-limits paths>.
- Preserve: <public API / behavior / existing patterns>.
- Match existing style and conventions.

## Verify (must pass before done)
- `<typecheck cmd>`  → clean (0 errors)
- `<test cmd>`       → green
- `<build cmd>`      → succeeds

## Acceptance criteria
- [ ] <observable outcome>
- [ ] <observable outcome>

## Report back
- Files changed (path → what), commands run + results,
  residual risks, anything skipped + why.

## Stop conditions
- If a constraint blocks the task, a needed secret/decision is missing,
  or a verification command fails after one fix attempt: STOP and report
  instead of guessing or widening scope.
```

A risk-tier example for a rename task, showing the forbidden list doing real work:

```md
## Constraints (hard) — rename `getUser` → `fetchUser`
- Rename only within `src/`; do NOT touch `node_modules`, generated files, or `*.snap`.
- Update all call sites; do NOT change the function body or signature.
- Do NOT add a backward-compat alias unless a call site is outside this repo.
```

## Worked example (filled in)

A vague ask ("add validation to the signup endpoint") becomes a final execution prompt:

```md
# Task: Reject signup requests with an invalid email at api/signup.ts

## Context
- Repo/paths: api/signup.ts, api/__tests__/signup.test.ts
- PM: pnpm   Framework/runtime: Express + TypeScript + Zod (already a dependency)
- Relevant files: api/signup.ts:18 (handler), api/schema.ts (Zod schemas live here)

## Do exactly this
1. In api/schema.ts, add `signupSchema = z.object({ email: z.string().email(), password: z.string().min(8) })`.
2. In api/signup.ts:18, parse the body with `signupSchema.safeParse(req.body)`;
   on failure return 400 with `{ error: 'invalid_input' }` before any DB call.

## Constraints (hard)
- Do NOT: deploy, run migrations, add a new dependency (Zod is already present),
  change the success response shape, or touch any file outside the two listed.
- Preserve: the 201 success response and its body.
- Match existing style (named exports, no default export).

## Verify (must pass before done)
- `pnpm tsc --noEmit`            → 0 errors
- `pnpm test api/signup`         → green (add cases: bad email, short password)
- `pnpm lint api/signup.ts`      → clean

## Acceptance criteria
- [ ] POST with a malformed email returns 400 and never reaches the DB.
- [ ] POST with a valid body still returns 201 with the unchanged shape.

## Report back
- Files changed (path → what), commands run + results, residual risks.

## Stop conditions
- If Zod is NOT already a dependency, or a verify command fails after one fix
  attempt: STOP and report. Do not install packages or widen scope.
```

Note how the forbidden list ("Zod is already present", "do not touch other files") and the stop condition do the real work: they prevent the agent from `npm install`-ing a second validation library or "improving" adjacent code.

## Common issues & anti-patterns

- **Multi-goal prompt.** "Fix the bug, add tests, and refactor the module" — three jobs; the agent does each partially. Split into one bounded goal.
- **Vague change instructions.** "Improve error handling" with no file or behavior named. Specify the file and the exact change.
- **Verification by vibes.** "Make sure it works" instead of a command with an expected result. Always give the command and the green condition.
- **No forbidden list.** Omitting "do not add dependencies" invites the agent to `npm install` its way out of a type error.
- **No stop condition.** Without one, a blocked agent guesses, widens scope, or fabricates a result.
- **Embedded secrets.** Pasting a real token into the context block leaks it. Reference the env var name.
- **Open-ended scope.** "and anything else you notice" guarantees scope creep. Bound the task.
- **No output contract.** The agent finishes but reports nothing reviewable, so the work cannot be trusted.

## Required output

Return the finished execution prompt using the template, ready to paste into a coding agent. It must be self-contained: exact context, exact changes, hard constraints, verification commands, acceptance checklist, output contract, and stop conditions — with zero ambiguity.

## Safety

- Bake in the destructive-action prohibitions (no deploys, prod migrations, resets, force pushes, vendor scripts) by default.
- Require reproducible verification, not "looks fine".
- Forbid scope creep and parallel-app/duplicate-repo creation explicitly.
- Reference secrets by env var name only; never embed values.
- Require the agent to stop and report on a blocked or ambiguous state rather than proceed.

## Completion criteria

Done means the prompt pins context, lists exact changes plus hard constraints, specifies exact verification and acceptance criteria, defines the report-back contract and stop conditions, and contains no ambiguous instruction.

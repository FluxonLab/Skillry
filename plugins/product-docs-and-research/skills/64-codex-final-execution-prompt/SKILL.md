---
name: codex-final-execution-prompt
description: Use when you need to write strict final execution prompts for Codex, Claude, Copilot, or other coding agents.
---

# Codex Final Execution Prompt

## Purpose
Use this skill to write strict final execution prompts for Codex, Claude, Copilot, or other coding agents. A final execution prompt has one singular, bounded goal; every instruction in it is testable; and a stop condition exists for every ambiguous or blocked state so the agent never silently guesses.

## When to use
- A well-understood task needs to be delegated to a coding agent and the instruction set must be unambiguous enough to execute without back-and-forth.
- A previous agent run went off-scope, touched forbidden files, or failed to verify its work — write a tighter prompt with explicit hard constraints and stop conditions before re-running.
- A plan exists (from implementation-plan skill) and now needs to be translated into a strict agent-executable format with exact file/change pairs and verification commands.
- A task involves risk (migration, rename, dependency change) and the prompt needs baked-in forbidden-action lists and rollback conditions to prevent silent damage.

## When not to use
- The task is unrelated to product, docs, and research work.
- The work would require production deploys, destructive data actions, or secret disclosure.
- A narrower skill or existing project instruction already covers the need.

## Procedure
1. Lock the context: target repo/paths, package manager, framework, runtime, and the exact, singular goal. A final execution prompt is unambiguous — one job, clearly bounded.
2. Enumerate constraints up front: what must not change, files/areas off-limits, style/convention to follow, and forbidden actions (deploys, destructive git/DB, new deps, scope creep).
3. Specify the work concretely: exact files to touch, the change in each, and the order if it matters.
4. Specify verification: the precise commands the agent must run and the expected green result for each.
5. Define acceptance criteria as a checklist the agent must satisfy before declaring done.
6. Define the output contract: what the agent must report back (diff summary, commands run, results, risks).
7. Strip ambiguity: no "etc.", no "improve as you see fit" — every instruction is testable.

## Execution prompt template
```md
# Task: <single, specific goal>
## Context
- Repo/paths: <...> PM: <npm/pnpm/...> Framework/runtime: <...>
- Relevant files: <path:line ...>
## Do exactly this
1. <change> in <file>
2. <change> in <file>
## Constraints (hard)
- Do NOT: deploy, run prod migrations, reset/seed data, force push, add dependencies, touch <off-limits paths>.
- Preserve: <public API / behavior / existing patterns>.
- Match existing style and conventions.
## Verify (must pass before done)
- `<typecheck cmd>` → clean
- `<test cmd>` → green
- `<build cmd>` → succeeds
## Acceptance criteria
- [ ] <observable outcome>
- [ ] <observable outcome>
## Report back
- Files changed (path → what), commands run + results, residual risks, anything skipped + why.
## Stop conditions
- If a constraint blocks the task or a needed secret/decision is missing, STOP and report instead of guessing.
```

## Concrete checks
- The goal is singular and testable (not a basket of loosely related asks).
- Every "do this" item names a concrete file/change, not a vibe.
- Verification commands are exact and have an expected result.
- Forbidden/destructive actions are explicitly listed.
- A stop condition exists for blocked/ambiguous states (no silent guessing).
- The output contract is specified so the result is reviewable.

## Required output
Return the finished execution prompt using the template, ready to paste into a coding agent. It must be self-contained: exact context, exact changes, hard constraints, verification commands, acceptance checklist, output contract, and stop conditions — with zero ambiguity.

## Safety checks
- Bake in the destructive-action prohibitions (no deploys, prod migrations, resets, force pushes, vendor scripts) by default.
- Require reproducible verification, not "looks fine".
- Forbid scope creep and parallel-app/duplicate-repo creation explicitly.
- Reference secrets by env var name only; never embed values.

## Completion criteria
Done means the prompt pins context, lists exact changes + hard constraints, specifies exact verification and acceptance criteria, defines the report-back contract and stop conditions, and contains no ambiguous instruction.

---
name: diff-review
description: Use when reviewing a code change before committing — e.g. the user says "review my diff", "karpathy check", "am I overcomplicating this", "check complexity before I commit", or when finalizing AI-generated code. Audits the staged diff against four principles (surface assumptions, keep it simple, surgical changes, verifiable goal) and returns a keep-or-fix verdict.
---

# Diff Review (four-principle pre-commit check)

## Purpose

Catch the failure modes that make AI-assisted changes risky **before** they land: unstated wrong
assumptions, needless complexity, sprawling diffs, and "looks done" changes that were never
verified. This skill reviews a concrete diff against four habits and returns a short, actionable
verdict — not a style lecture.

The four principles below distill widely shared guidance on coding with LLMs popularized by
**Andrej Karpathy** (<https://karpathy.ai>); the four-point framing is a common community
distillation, not a verbatim quote.

## When to use

- Before committing, especially for AI-generated or AI-assisted changes.
- When the user says "review my diff", "karpathy check", "check complexity", "am I overcomplicating
  this", or "is this change too big".
- As a final gate after implementing a feature/fix, before opening a PR.

## When not to use

- For deep security review (use a dedicated security/secrets review skill).
- For architecture-level decisions across many files (use architecture-review).
- When there is no diff yet — this reviews concrete changes, not ideas.

## Procedure

1. **Get the change.** Inspect the actual diff, not the description:
   - Staged: `git diff --staged`
   - Working tree: `git diff`
   - Last commit: `git show HEAD`
   Note the number of files, hunks, and net lines changed.
2. **Principle 1 — Surface assumptions.** List the inputs, invariants, and edge cases the change
   assumes (nullability, types, ordering, auth state, empty/large inputs, concurrency). For each,
   confirm it actually holds in the touched code paths. Flag any unstated assumption that isn't
   guaranteed.
3. **Principle 2 — Keep it simple.** Look for complexity the change introduces on its own: new
   abstractions/indirection for a single caller, premature generalization, dead branches, clever
   one-liners, duplicated logic. Prefer the smallest solution that works; note what could be deleted.
4. **Principle 3 — Surgical changes.** Check that every hunk is required by the task. Flag drive-by
   reformatting, unrelated renames, churned imports, and files that didn't need to change. Wide blast
   radius = harder review and higher regression risk.
5. **Principle 4 — Verifiable goal.** Identify how this change is *proven* to work: a test, a command,
   an observable output. If there's no verification (or no new/updated test for new behavior), that is
   the top finding.
6. **Verdict.** Summarize as **keep** (ship as-is), **keep with nits** (minor, non-blocking), or
   **fix first** (blocking issues). List blocking items with the exact file:line and a concrete fix.

## Concrete checks

- `git diff --staged --stat` — files and net lines; a "one-line fix" touching 12 files is a red flag.
- New behavior has a matching new/changed test? (search the diff for test files)
- Any `TODO`, `FIXME`, debug `print`/`console.log`, commented-out code, or leftover scaffolding in the diff?
- Any new dependency added for a trivial need that the stdlib/existing utils already cover?
- Does the diff reformat lines it didn't functionally change? (whitespace-only hunks)
- Are assumptions about external input validated, or just trusted?

## Commands

```bash
git diff --staged --stat        # blast radius at a glance
git diff --staged               # the actual change to review
git show HEAD                   # review the last commit instead
git diff --staged -- '*.test.*' '*_test.*' '*spec*'   # did tests change with the code?
```

## Common issues & anti-patterns

- **"It looks right" ≠ verified.** No test, no run, no proof → treat as unverified.
- **Refactor smuggled into a feature.** Keep behavior-preserving refactors in a separate commit.
- **Over-abstraction for one caller.** YAGNI — inline it until a second caller exists.
- **Silent assumption.** "It'll always be non-null/sorted/small" without a guard or test.
- **Scope creep.** The diff fixes three things the task didn't ask for; split them.

## Required output

A short report:
- **Blast radius:** files / hunks / net lines.
- **Per principle:** ✓ or the specific finding (with `file:line`).
- **Verdict:** keep / keep with nits / fix first.
- **Blocking fixes (if any):** numbered, each with an exact, minimal fix.

## Safety

Read-only review — never amend, commit, reset, or rewrite history as part of this skill. Suggest
fixes; let the author apply them. Do not run formatters or `git add`/`git commit` automatically.

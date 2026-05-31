---
name: refactor-safety
description: Use when you need to scope refactors safely, preserve behavior, avoid unrelated churn, and verify changed surfaces.
---

# Refactor Safety

## Purpose
This skill enforces a disciplined process for structural code changes: lock in existing behavior with tests before touching anything, shrink the diff to only what is necessary, keep each step independently verifiable, and maintain a clear rollback path. It prevents the most common refactor failure modes — behavior regressions, test-suite gaps masked by passing CI, and scope creep that tangles multiple concerns in one PR.

## When to use
- Renaming or relocating a function, class, or module that is called from more than 3 places.
- Changing a shared abstraction (base class, interface, utility function) used across multiple packages.
- Extracting a large function into smaller units where business logic lives inside the original.
- Migrating from one library or pattern to another (e.g., callbacks → Promises, class components → hooks, ORM A → ORM B).
- Removing dead code that you are not 100% sure is unreachable.

## When not to use
- You are fixing a bug — behavior must change; use a normal bug-fix workflow, not a refactor.
- The change is a one-liner in a leaf function with full test coverage and no callers outside the same file.
- You have no way to run the test suite locally or in CI — stop and establish that first.

## Procedure

1. **Establish baseline test coverage before touching any code.** Run the existing test suite and record the pass/fail count and coverage percentage for the files you will modify. If coverage for the target module is below 60%, write characterization tests first (see step 2).

2. **Write characterization tests for untested behavior.** A characterization test calls the current function with realistic inputs and asserts the current output — even if that output looks wrong. The goal is to lock in the current contract, not to validate it. Example: `test('legacy price calculation returns 0 for empty cart', () => { expect(calcPrice([])).toBe(0) })`. Commit these tests before changing anything.

3. **Map every call site.** Before renaming or moving anything, find all callers: `grep -rn "functionName\|ClassName" --include="*.ts" .` or use IDE "Find usages". List them — you will verify each one after the change.

4. **Decompose into the smallest atomic steps.** A rename is one step. Moving a file is a separate step. Changing a signature is a separate step. Changing the implementation is a separate step. Never combine rename + logic change in the same commit.

5. **Apply one step, run tests immediately.** After each atomic step: run `npm test -- --testPathPattern=affected-file` (or equivalent). Do not proceed to the next step until tests are green. If a test fails, revert the step and diagnose.

6. **Verify call sites one by one.** Walk through the list from step 3 and confirm each caller compiles and passes its own tests. For dynamic languages, also run the integration tests that exercise each call path.

7. **Check for non-obvious consumers.** After a rename, search for the old name in: string literals (dynamic `require`/`import`), documentation, config files, `__mocks__` directories, test fixtures, and CI workflow files. Dead names in these locations cause confusing runtime failures.

8. **Confirm no unrelated changes crept in.** Run `git diff --stat` and read through every changed file. If you see changes outside the scoped module, revert them or move them to a separate PR.

9. **Delete the characterization tests if they tested wrong behavior.** Once the refactor is complete and you have written proper unit tests for the new structure, remove any characterization tests that asserted incorrect behavior — they will cause false failures on future correct changes.

## Checklist
- [ ] Test suite runs cleanly on the unmodified code (baseline established)
- [ ] Characterization tests written for any untested behavior in the target module
- [ ] All call sites located and listed before first change
- [ ] Each atomic step (rename / move / signature change / logic change) is a separate commit
- [ ] Tests re-run and pass after each atomic step
- [ ] Old name searched in string literals, config, mocks, docs, CI files
- [ ] `git diff --stat` reviewed — no unrelated files changed
- [ ] TypeScript/compiler/linter errors at zero before opening PR
- [ ] Integration or E2E test that exercises the changed path still passes
- [ ] Characterization tests cleaned up where they asserted legacy-wrong behavior

## Common issues & anti-patterns

- **Opportunistic cleanup**: touching formatting, variable naming, or unrelated logic while doing a structural refactor. This inflates diffs, introduces noise in blame, and makes bisect harder. Resist all of it.
- **Skipping characterization tests**: "the code is obvious, I don't need tests." The refactor succeeds, CI passes, and six months later someone discovers an edge case that was silently broken.
- **Moving and changing in the same commit**: combining `mv src/auth.ts src/authentication.ts` with logic changes in the same commit makes `git bisect` useless for finding the regression.
- **Missing dynamic imports**: in Node.js, `require(path.join(__dirname, moduleName))` will not be caught by static grep. Check for dynamic require patterns separately.
- **Compiler passing but runtime failing**: TypeScript `any` casts and loose JS interop can hide type mismatches that only surface at runtime. Run integration tests, not just unit tests.

## Required output
Report must include:
- **Baseline**: test count and coverage % for target module before changes
- **Characterization tests added**: list of test names and what behavior they lock in
- **Call sites found**: count and representative list of files
- **Steps executed**: ordered list of atomic commits with test result after each
- **Non-obvious consumers checked**: string literals, config, mocks, CI — result for each
- **Final diff stats**: files changed, lines added, lines removed
- **Remaining gaps**: any call sites that could not be verified (e.g., runtime-dynamic, behind a feature flag)

## Safety
- Never combine a refactor with a bug fix or feature addition in the same PR — keep intents separate.
- If you cannot establish a green baseline before starting, stop and surface that as the primary problem to fix first.
- Do not delete the old function/module until all callers are confirmed migrated and at least one full CI run passes on the new code.

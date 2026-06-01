---
name: refactor-safety
description: Use when you need to scope refactors safely, preserve behavior, avoid unrelated churn, and verify changed surfaces.
---

# Refactor Safety

## Purpose
Enforce a disciplined process for structural code changes: lock in existing behavior with tests before touching anything, shrink the diff to only what is necessary, keep each step independently verifiable, and maintain a clear rollback path. This prevents the three most common refactor failures — silent behavior regressions, test-suite gaps masked by green CI, and scope creep that tangles unrelated concerns into one unreviewable PR. The defining rule: a refactor must not change observable behavior, so the test result before and after must be identical.

## When to use
- Renaming or relocating a function, class, or module called from more than three places.
- Changing a shared abstraction (base class, interface, widely-used utility) consumed across multiple packages.
- Extracting a large function into smaller units where real business logic lives inside the original.
- Migrating from one library or pattern to another (callbacks to Promises, class components to hooks, ORM A to ORM B).
- Removing code you are not 100% certain is unreachable.

## When not to use
- You are fixing a bug — behavior must change, so use a bug-fix workflow with a failing test first, not a refactor.
- The change is a one-liner in a fully-tested leaf function with no callers outside its own file.
- You cannot run the test suite locally or in CI — stop and establish that first; a refactor without a safety net is a rewrite.
- The code is throwaway prototype scaffolding that will be deleted, not maintained.

## Procedure
1. **Establish a green baseline before touching code.** Run the full suite and record the pass/fail count and the coverage percentage for the files you will modify. If coverage for the target module is below ~60%, write characterization tests first (step 2).
2. **Write characterization tests for untested behavior.** A characterization test calls the current function with realistic inputs and asserts the *current* output — even if that output looks wrong. The goal is to pin the existing contract, not validate it. Commit these tests before changing any production code.
3. **Map every call site.** Find all callers with `git grep -n "functionName\|ClassName" -- '*.ts'` or the IDE "Find usages". List them; you will verify each one after the change.
4. **Decompose into the smallest atomic steps.** A rename is one step. Moving a file is a separate step. Changing a signature is a separate step. Changing the implementation is a separate step. Never combine a rename with a logic change in one commit.
5. **Apply one step, run tests immediately.** After each atomic step run the scoped suite (`npm test -- --testPathPattern=affected` or `pytest tests/affected`). Do not advance until it is green. If a test fails, revert that single step and diagnose in isolation.
6. **Verify call sites one by one.** Walk the list from step 3 and confirm each caller still compiles and passes its own tests. For dynamic languages, also run the integration tests that exercise each path.
7. **Check for non-obvious consumers.** After a rename, search the old name in string literals (dynamic `require`/`import`), docs, config files, `__mocks__`, fixtures, and CI workflow YAML. Stale names there cause confusing runtime failures that the compiler never catches.
8. **Confirm no unrelated changes crept in.** Run `git diff --stat`, read every changed file, and revert anything outside the scoped module (or split it into a separate PR).
9. **Clean up wrong-behavior characterization tests.** Once proper unit tests exist for the new structure, delete any characterization test that asserted incorrect legacy behavior so it does not block future correct changes.

## Refactor vs rewrite decision
Refactor in place when behavior must be preserved exactly and tests can prove it. Choose a rewrite (behind a flag, old path kept until the new one is proven) when the existing code has no tests, depends on a discontinued library, or its control flow cannot be reasoned about. The tell: if you cannot write a characterization test because you cannot predict the current output, you do not understand the code well enough to refactor it safely — rewrite against a spec instead.

## Risk tiers (calibrate rigor to blast radius)
| Tier | Example | Required safety net |
|------|---------|---------------------|
| Low | rename a local var, extract a private helper | unit test for the enclosing unit |
| Medium | rename an exported function used in one package | characterization tests + all call sites verified |
| High | change a shared interface or base class | characterization tests + integration tests + staged rollout |
| Critical | migrate ORM, auth, or money-handling code | full suite + feature flag + old path retained one release |

## Concrete checks
- Test suite runs clean on the unmodified code; baseline pass/fail and coverage recorded.
- Characterization tests exist for any untested behavior in the target module and are committed first.
- All call sites located and listed before the first change.
- Each atomic step (rename / move / signature / logic) is its own commit.
- Tests re-run and pass after each atomic step — not just at the end.
- Old name searched in string literals, config, mocks, docs, and CI files.
- `git diff --stat` reviewed; no unrelated files appear.
- Typecheck/compiler/linter at zero errors before opening the PR.
- An integration or e2e test exercising the changed path still passes.
- Characterization tests asserting legacy-wrong behavior cleaned up after the refactor.
- The branch was rebased onto current main before the call-site map was built.
- The before/after suite outcome is identical (same pass/fail counts), proving behavior was preserved.
- Coverage on the touched module did not drop versus the baseline.

## Commands
```bash
# 1. Baseline: record pass/fail and coverage for the target before changes
npm test -- --watch=false
npx jest --coverage --collectCoverageFrom='src/auth/**' 2>/dev/null | tail -20
# Python equivalent:
pytest --cov=src/auth --cov-report=term-missing -q | tail -20

# 2. Map all call sites (static)
git grep -n "calcPrice\|PriceCalculator" -- '*.ts' '*.tsx'
git grep -l "calcPrice" | wc -l            # blast-radius count

# 3. Catch dynamic / non-obvious consumers a compiler will miss
rg -n "calcPrice" --type-add 'cfg:*.{json,yaml,yml,md}' -tcfg
rg -n "require\(.*calcPrice|import\(.*calcPrice" src/
rg -n "calcPrice" __mocks__/ test/fixtures/ .github/workflows/

# 4. Per-step verification (run after EACH atomic commit)
npm test -- --testPathPattern=auth
tsc --noEmit && npx eslint src/auth

# 5. Confirm no unrelated churn before opening the PR
git diff --stat
git diff --name-only | grep -v '^src/auth/' || echo "scope clean"
```
```bash
# Language-specific call-site + dead-code detection
# TypeScript: find unused exports before deleting a symbol
npx ts-prune | rg "calcPrice"
# Python: find references and dead code
git grep -n "calc_price" -- '*.py'
vulture src/ --min-confidence 80 | rg "calc_price"
# Go: who imports the package, and is the symbol used
go list -deps ./... | rg pricing
staticcheck ./... 2>/dev/null | rg "U1000"   # unused code
```
```bash
# Worked example: a rename split into atomic, individually-green commits
git mv src/pricing/calcPrice.ts src/pricing/priceCalculator.ts   # step A: move only
npm test -- --testPathPattern=pricing && git commit -am "move: rename file"
# step B: rename the symbol, update imports, no logic change
rg -l "calcPrice" src/ | xargs sed -i '' 's/calcPrice/priceCalculator/g'
npm test -- --testPathPattern=pricing && git commit -am "rename: calcPrice -> priceCalculator"
# step C (separate PR): only now change behavior, with a new failing test first
git diff --stat   # confirm step B touched only renames, zero logic lines
```
```bash
# Bisect a regression introduced by a refactor (atomic commits make this work)
git bisect start
git bisect bad                       # current HEAD is broken
git bisect good <pre-refactor-sha>   # last known-good commit
# git checks out midpoints; at each step run the scoped test and mark it:
npm test -- --testPathPattern=pricing && git bisect good || git bisect bad
git bisect reset                     # when the first bad commit is found

# Verify the suite outcome is byte-identical before vs after (behavior preserved)
git stash && npm test -- --watch=false 2>&1 | tee /tmp/before.txt
git stash pop && npm test -- --watch=false 2>&1 | tee /tmp/after.txt
diff <(grep -E 'Tests:|passing|failing' /tmp/before.txt) \
     <(grep -E 'Tests:|passing|failing' /tmp/after.txt) && echo "behavior preserved"

# Confirm coverage did not drop on the touched module
npx jest --coverage --collectCoverageFrom='src/pricing/**' 2>/dev/null | rg "pricing|All files"
```

## Common issues & anti-patterns
- **Opportunistic cleanup.** Reformatting, renaming locals, or tweaking unrelated logic during a structural refactor. It inflates the diff, pollutes `git blame`, and breaks `git bisect`. Resist all of it.
- **Skipping characterization tests** because "the code is obvious." The refactor passes CI and an edge case silently breaks; it surfaces months later with no failing test to point at.
- **Move and change in one commit.** Combining `git mv src/auth.ts src/authentication.ts` with logic edits makes bisect useless — you cannot tell whether the move or the logic introduced the regression.
- **Missing dynamic imports.** `require(path.join(__dirname, moduleName))` is invisible to static grep. Search the string form separately.
- **Compiler green, runtime red.** `any` casts and loose JS interop hide type mismatches that only fail at runtime. Run integration tests, not only unit tests.
- **Deleting the old symbol too early.** Removing the old function before all callers are migrated and one full CI run is green on the new path.
- **Reformatting the whole file.** Letting the editor reformat-on-save turns a 3-line change into a 300-line diff where the real change is invisible to the reviewer. Format only the lines you touch, or land a formatting-only commit first.
- **Refactoring on a stale branch.** Starting from a branch days behind main means the call-site map is wrong by the time you finish. Rebase to current main before mapping callers.
- **Trusting "find usages" for reflection.** IDE find-usages misses string-keyed lookups, DI containers, and serialized type names. Pair it with a raw text search of the old name.

## Required output
Report must include:
- **Baseline:** test count and coverage % for the target module before changes.
- **Characterization tests added:** test names and the behavior each locks in.
- **Call sites found:** count and a representative file list.
- **Steps executed:** ordered atomic commits with the test result after each.
- **Non-obvious consumers checked:** string literals, config, mocks, docs, CI — result for each.
- **Final diff stats:** files changed, lines added, lines removed.
- **Remaining gaps:** any call site not verified (runtime-dynamic, behind a feature flag) and why.
- **Risk tier:** which tier (low/medium/high/critical) the change fell into and whether the matching safety net was applied.
- **Behavior-preservation evidence:** the before/after test result showing the suite outcome is identical (the core proof a refactor changed no behavior).

## Safety
- Never combine a refactor with a bug fix or feature in the same PR; keep intents separate and reviewable.
- If you cannot establish a green baseline first, stop and surface that as the primary problem to fix before refactoring.
- Do not delete the old function/module until all callers are confirmed migrated and at least one full CI run passes on the new code.
- Do not weaken or remove existing tests to make a refactor "pass"; a test that now fails is signalling a behavior change.

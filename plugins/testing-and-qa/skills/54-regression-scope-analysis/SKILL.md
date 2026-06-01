---
name: regression-scope-analysis
description: Use when you need to identify likely regression surfaces, impacted tests, risk boundaries, and verification focus for a code change before merge.
---

# Regression Scope Analysis

## Purpose

Given a set of code changes (PR diff, commit range, or file list), determine the blast radius: which application areas are affected, which existing tests cover those areas, which areas have no test coverage, and what the minimum required verification suite is before the change is considered safe. Produce a prioritized test execution plan — not just a list of changed files. A 3-file change in shared middleware has a larger blast radius than a 30-file change in isolated feature modules; this skill makes that distinction explicit and actionable.

## When to use

- A PR modifies shared utilities, middleware, base classes, or database schemas that many features depend on.
- A refactor touches more than 5 files and you want to confirm the test suite is adequate before merging.
- A hot-fix is needed quickly and you must identify the minimum set of tests that prove safety without running the full suite.
- A dependency upgrade may have changed behavior in transitive code paths.
- CI is slow and you need to determine which test shards are mandatory versus skippable for a given change.
- A schema migration, ORM model change, or data pipeline modification is included in the diff.

## When not to use

- The change is isolated to a single new feature file with its own new test file — scope is self-evident.
- The task is to write new tests, not to analyze what to run.
- A full regression suite is already mandated by CI policy and no optimization is needed.
- You need to write or fix tests — use a coding task or `smoke-test-and-repair` instead.

## Procedure

1. **Get the diff from the correct base.** Run `git diff main...HEAD --name-only` (or substitute the relevant base branch). For a specific commit range: `git diff <base-sha>..<head-sha> --name-only`. Record the exact base ref used — a wrong base produces a wrong scope analysis.

2. **Categorize changed files by architectural layer.** Group each changed file into one of these buckets:
   - **Infrastructure / shared**: config, env files, database schemas, ORM models, shared utilities, base classes, middleware, request lifecycle hooks.
   - **Domain / business logic**: service files, domain models, use-case handlers, event handlers.
   - **API / transport**: route handlers, GraphQL resolvers, REST controllers, gRPC service definitions.
   - **UI / presentation**: React/Vue/Angular components, templates, CSS/Tailwind, client-side state.
   - **Test files only**: changes confined to `*.test.ts`, `*.spec.ts`, fixtures, factories — lower blast radius but can still introduce false positives.

3. **Trace the import fan-out for every infrastructure or shared change.** A shared module touched by 40 files has a very different blast radius than one imported by 2. Use `grep -r "from.*<module>" src/` or `rg --type ts "from.*queryBuilder"` to enumerate direct importers. Then check for barrel re-exports (`index.ts` files) that may extend the surface further.

4. **Map each changed non-test file to its existing test files.** For every changed source file:
   - Is there a co-located test file (`foo.test.ts` beside `foo.ts`)?
   - Is there an integration test that exercises the changed route or service?
   - Is there an E2E test that covers the user flow passing through this code?
   If none exist, flag the file as a **coverage gap** — changed code with no tests is the highest regression risk.

5. **Flag schema and migration changes explicitly.** If any `schema.prisma`, `*.migration.sql`, `migrations/`, or ORM model file changed, mark it as requiring data-integrity testing against production-representative data (not just a development seed). A type change on a non-nullable column with no migration is a deployment blocker.

6. **Identify cross-cutting concerns.** Changes to auth middleware, error handler, logging, observability, rate limiting, or request-parsing always affect every request path — treat them as maximum blast radius regardless of how small the import graph looks. Flag these explicitly with the note "cross-cutting — treat all integration tests as affected."

7. **Determine the minimum verification suite in three tiers:**
   - **Mandatory (run before merge)**: tests that directly cover changed code. Must all pass. Name the exact test files or commands.
   - **Recommended (run if CI time allows)**: tests for modules that import the changed files. Should pass.
   - **Optional / full suite**: everything else. Run when in doubt or for scheduled nightly regression.

8. **Estimate re-test time per tier.** Use prior CI run times from the CI dashboard or `--json` reporter output. Approximations are acceptable; the goal is helping the team choose the right tier under time pressure.

9. **Summarize the highest-risk gap.** State which single uncovered change carries the most risk and what test would close it — this becomes the first recommendation even when the full analysis is long.

## Concrete checks

- The diff was obtained from the correct base branch; the base ref is recorded in the output.
- Every changed file is categorized by layer — none are left uncategorized.
- Import fan-out was traced with a grep or `rg` command, not guessed.
- Barrel re-exports (`index.ts`) were inspected to ensure the true consumer surface is not underestimated.
- Every changed non-test file has an explicit test coverage status: covered, partially covered, or gap.
- Schema/migration changes are called out for data-integrity testing, not just unit test coverage.
- Cross-cutting concerns (auth, logging, error handler) are flagged and their blast radius noted.
- The mandatory test tier names exact commands or file paths, not just "run tests."
- Coverage gaps are listed with a risk rating (high/medium/low) based on call frequency and change complexity.
- Feature-flagged changes are noted: if the change is behind an off flag in production, blast radius in production is zero, but the test suite must still cover the flagged path.

## Commands

```bash
# Get the diff from the correct base
git diff main...HEAD --name-only
git diff origin/main...HEAD --name-only           # remote base
git diff <base-sha>..<head-sha> --name-only        # specific range

# Count changed files by directory to spot concentration
git diff main...HEAD --name-only | awk -F/ '{print $1"/"$2}' | sort | uniq -c | sort -rn

# Trace who imports a shared module
rg --type ts "from ['\"].*queryBuilder" src/
grep -rn "import.*UserRepository" src/ --include="*.ts"

# Check for barrel re-exports that extend the import surface
rg --type ts "export \* from" src/

# Find test files for a changed module
find . -name "*.test.ts" -o -name "*.spec.ts" | xargs grep -l "queryBuilder" 2>/dev/null

# Estimate test runtime by listing test files and their last run time from CI cache
# (CI-specific; substitute the reporter relevant to the project)
npx jest --listTests 2>/dev/null | head -30
npx jest --testPathPattern="auth|user|billing" --passWithNoTests -- --json 2>/dev/null | jq '.testResults[].perfStats'

# Confirm migration files changed
git diff main...HEAD --name-only | grep -E "(migration|schema\.prisma|\.sql)"

# Find integration tests that exercise a specific route
rg --type ts "POST /api/orders|GET /api/users" tests/
```

```bash
# Build a quick mandatory-tier command from gap analysis results
# Substitute the test runner command to the project's actual runner
npx jest src/services/order.service.test.ts src/middleware/auth.test.ts
pytest tests/integration/test_orders.py tests/unit/test_auth.py
```

## Common issues & anti-patterns

- **Counting files changed, not blast radius.** 3 changed files in shared middleware affect the entire app; 30 changed files in isolated feature modules affect almost nothing. File count alone is not risk.
- **Ignoring test-file-only changes.** Changes to test utilities, fixtures, or factories can introduce false positives or negatives that mask real regressions in the next run.
- **Missing barrel re-export chains.** A shared module re-exported through an `index.ts` has a larger import surface than direct imports alone suggest. Always trace through barrel files.
- **Schema changes with no migration test.** The migration file exists but has never been applied to production-like data. Column renames and type changes are high-risk; test them against a realistic dataset.
- **Assuming co-located unit tests are sufficient.** A unit test for a service does not exercise the HTTP layer, auth middleware, or database constraints. Integration tests are also needed, especially for infrastructure changes.
- **Ignoring branch-specific feature flags.** A change behind a feature flag that is off in production has zero blast radius in production — but the test suite should still cover the flagged path so the flag can be safely enabled later.
- **Selecting tests by intuition instead of import graph.** Guessing "this probably only affects billing" without tracing imports leads to missed coverage in shared paths.
- **Treating every PR as maximum blast radius.** Over-alerting makes the analysis useless. Calibrate to the actual import graph: a change to a truly isolated leaf module is low risk and should be stated as such.

## Required output

```
## Regression Scope Analysis

### Base ref
git diff <base>..<head> — base: <branch or SHA>

### Changed files by layer
- Infrastructure (high fan-out): list
- Domain/business logic: list
- API/transport: list
- UI/presentation: list
- Test files only: list

### Blast radius assessment
- Modules importing changed infrastructure files: N files — key areas: X, Y, Z
- Schema/migration changes: yes/no — data integrity test required: yes/no
- Cross-cutting concerns modified: yes/no — details

### Test coverage mapping
| Changed file | Test file(s) found | Coverage status |
|--------------|--------------------|-----------------|
| src/foo.ts   | src/foo.test.ts    | Covered         |
| src/bar.ts   | none               | GAP — high risk |

### Minimum verification suite
**Mandatory (run before merge):**
- npx jest src/foo.test.ts src/baz.integration.test.ts
- estimated time: ~Xmin

**Recommended (run if CI time allows):**
- npx jest --testPathPattern="auth|user|billing"
- estimated time: ~Xmin

### Risk summary
- Highest risk gap: [file] — [reason] — recommended test: [stub or file name]
- Total coverage gaps: N — risk rating: high/medium/low per gap
```

## Safety

- Run only read-only git commands (`git diff`, `git log`, `git grep`) and file search commands.
- Do not modify source files, test files, or CI configuration.
- Do not run the test suite unless explicitly asked; produce the plan and let the user execute it.
- Do not fabricate coverage data — if a test file exists but its coverage of the changed lines is unknown, say "unclear coverage" rather than "covered."
- Do not recommend skipping the mandatory tier to meet a deadline; flag the risk explicitly instead.

## Completion criteria

Done means the diff was obtained from the correct base, every changed file is categorized and coverage-mapped, the blast radius is traced from grep evidence (not assumption), the three verification tiers are named with exact commands, the highest-risk gap is called out with a concrete recommendation, and the output follows the required format so a CI engineer can act on it without follow-up questions.

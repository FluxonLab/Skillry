---
name: regression-scope-analysis
description: Use when you need to identify likely regression surfaces, impacted tests, risk boundaries, and verification focus.
---

# Regression Scope Analysis

## Purpose

Given a set of code changes (PR diff, commit range, or file list), determine the blast radius: which application areas are affected, which existing tests cover those areas, which areas have no test coverage, and what the minimum required verification suite is before the change is considered safe. Produce a prioritized test execution plan, not just a list of changed files.

## When to use

- A PR modifies shared utilities, middleware, base classes, or database schemas that many features depend on.
- A refactor touches more than 5 files and you want to confirm the test suite is adequate before merging.
- A hot-fix is needed quickly and you must identify the minimum set of tests that prove safety without running the full suite.
- A dependency upgrade may have changed behavior in transitive code paths.
- CI is slow and you need to determine which test shards are mandatory vs. skippable for a given change.

## When not to use

- The change is isolated to a single new feature file with its own new test file — scope is self-evident.
- The task is to write new tests, not to analyze what to run.
- A full regression suite is already mandated by the CI policy and no optimization is needed.

## Procedure

1. **Get the diff.** Run `git diff main...HEAD --name-only` (or the relevant base branch) to get the list of changed files. For a specific commit range: `git diff <base-sha>..<head-sha> --name-only`.

2. **Categorize changed files by layer.** Group files into:
 - **Infrastructure / shared**: config, env, database schemas, ORM models, shared utilities, base classes, middleware.
 - **Domain / business logic**: service files, domain models, use-case handlers.
 - **API / transport**: route handlers, GraphQL resolvers, REST controllers.
 - **UI / presentation**: React components, templates, CSS.
 - **Test files only**: changes confined to test files (lower blast radius).

3. **Identify fan-out for infrastructure changes.** For every shared module that changed, trace its import graph: which feature modules import it? Use `grep -r "from.*<module>" src/` or equivalent. A change to `src/db/query-builder.ts` that is imported by 40 files has a very different blast radius than one imported by 2.

4. **Map changed code to existing tests.** For each changed non-test file, find the corresponding test file(s). Check:
 - Is there a co-located test file (`*.test.ts`, `*.spec.ts`)?
 - Are there integration tests that exercise the changed route or service?
 - Are there E2E tests that cover the user flow touching this code?

5. **Identify coverage gaps.** For each changed file with no corresponding test, flag it explicitly. A coverage gap in a changed file is high risk.

6. **Assess data migration risk.** If schema files, migration files, or ORM model files changed, flag that data migration must be tested against a copy of production-representative data, not just a seed.

7. **Determine minimum verification suite.** Based on the above, produce a tiered list:
 - **Mandatory**: tests that directly cover changed code — must pass.
 - **Recommended**: tests for modules that import changed code — should pass.
 - **Optional / full suite**: everything else — run if time permits.

8. **Estimate re-test time.** For each tier, approximate how long the tests take based on existing CI run times if available.

9. **Flag cross-cutting concerns.** Changes to auth middleware, logging, error handling, or observability affect every request path — treat these as maximum blast radius even if the import graph appears limited.

## Checklist

- [ ] Full diff obtained from the correct base branch.
- [ ] Changed files categorized by architectural layer.
- [ ] Import fan-out traced for all shared/infrastructure file changes.
- [ ] Each changed file mapped to at least one test file (or flagged as uncovered).
- [ ] Schema/migration changes identified and flagged for data-integrity testing.
- [ ] Cross-cutting concerns (auth, logging, error handling) called out explicitly.
- [ ] Minimum mandatory test set defined with concrete file or command references.
- [ ] Coverage gaps listed with risk rating.

## Common issues & anti-patterns

- **Counting files changed, not blast radius**: 3 changed files in shared middleware affect the entire app; 30 changed files in isolated feature modules affect almost nothing. File count is not risk.
- **Ignoring test-file-only changes**: changes to test utilities, fixtures, or factories can introduce false positives/negatives that mask real regressions.
- **Missing re-export chains**: a shared module re-exported through an index barrel file has a larger import surface than direct imports suggest — trace through index files.
- **Schema changes with no migration test**: the migration file exists but has never been applied to production-like data; column renames and type changes are high-risk.
- **Assuming co-located tests are sufficient**: a unit test for a service does not exercise the HTTP layer, auth middleware, or database constraints — integration tests are also needed.
- **Ignoring branch-specific feature flags**: if the change is behind a feature flag that is off in production, the blast radius in production is zero — but the test suite should still cover the flagged path.

## Required output

```
## Regression Scope Analysis

### Changed files by layer
- Infrastructure (high fan-out): list
- Domain/business logic: list
- API/transport: list
- UI/presentation: list
- Test files only: list

### Blast radius assessment
- Modules importing changed infrastructure files: N files, key areas: X, Y, Z.
- Schema/migration changes: yes/no — data integrity test required.
- Cross-cutting concerns modified: yes/no — details.

### Test coverage mapping
| Changed file | Test file(s) | Coverage status |
|--------------|-------------|-----------------|
| src/foo.ts | src/foo.test.ts | Covered |
| src/bar.ts | none | GAP — high risk |

### Minimum verification suite
**Mandatory (run before merge):**
- npx jest src/foo.test.ts src/baz.integration.test.ts
- estimated time: ~Xmin

**Recommended (run if CI time allows):**
- npx jest --testPathPattern="auth|user|billing"
- estimated time: ~Xmin

### Risk summary
- Highest risk change: [file] because [reason].
- Uncovered changed files: N — recommend adding tests before merge.
```

## Safety

- Run only read-only git commands (`git diff`, `git log`, `git grep`) and file searches.
- Do not modify source files, test files, or CI configuration.
- Do not run the test suite unless explicitly asked; produce the plan and let the user execute it.

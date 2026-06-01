---
name: architecture-review
description: Use when you need to evaluate architecture, coupling, duplication, integration fit, and whether to keep, adapt, or replace existing structures.
---

# Architecture Review

## Purpose

Evaluate architecture, coupling, duplication, integration fit, and whether to keep, adapt, or replace existing structures. Every Keep, Adapt, or Replace decision must be justified with file-level evidence — churn, blast radius, coupling — not intuition. The default bias is toward the smallest change that fits the existing structure; a rewrite is recommended only when the explicit rule below is met, and never by standing up a parallel app or repo.

## When to use

- A new feature or refactor touches multiple modules and you need to confirm it follows the existing dependency direction before committing to a plan.
- Circular dependencies, god modules, or competing implementations of the same concern are suspected.
- A pull request or design proposal introduces a second way of solving something already solved (two HTTP clients, two state stores, conflicting conventions).
- Before a larger refactor, to establish which components to Keep, Adapt, or Replace and prove the blast radius is bounded.

## When not to use

- The task is unrelated to core operations work.
- The work would require production deploys, destructive data actions, or secret disclosure.
- You first need a structural map or a runnability baseline — use `codebase-cartography` or `repo-diagnostics`, then return here.
- A narrower skill or existing project instruction already covers the need.

## Procedure

1. **Build a module map.** List the top-level directories, each one's responsibility, and the dependency direction between them. Locate the boundary between UI, domain or business logic, data access, and infrastructure.
2. **Detect cycles and illegal dependencies.** Find inversions where lower layers depend on higher ones (UI importing the DB client, domain importing a framework, a shared `core` importing a `routes` module).
3. **Find duplication.** Identify parallel implementations of one concern (two HTTP clients, two state stores, two date utils), copy-pasted logic, and competing patterns for the same job.
4. **Assess integration fit for the change.** Does the proposed work follow existing data-fetching, error-handling, auth, and state conventions, or introduce a second way of doing the same thing?
5. **Decide Keep, Adapt, or Replace** for each questioned component using the rule below, justified with evidence (churn, blast radius, coupling).
6. **Surface the highest-risk files** (high fan-in plus high churn) and state the smallest viable change that fits the existing structure.

## Concrete checks

Dependency direction:
- Nothing in `domain` or `core` imports from `ui`, `routes`, or a framework package.
- Lower layers do not import higher ones; the dependency graph points one way.
- No business rule is embedded directly in a UI component or route handler.

Duplication:
- No two files export the same function name for the same purpose.
- There is one HTTP layer, not an `axios` wrapper plus bare `fetch` calls.
- There is one state solution for a given slice of data, not Redux plus Zustand plus Context.

Coupling and fit:
- Changing one feature does not force edits across five or more unrelated files.
- A new module follows the existing data-fetching, error-handling, and config conventions.
- No god module is imported by twenty or more files.
- The proposed change reuses an existing seam rather than introducing a parallel one.

Decision readiness:
- Each questioned component has churn and fan-in evidence attached.
- Any Replace verdict carries a concrete migration path and a rollback.
- The smallest change that fits the structure is identified, not just the cleanest.

## Keep / Adapt / Replace rule

- **Keep:** the pattern is consistent, tested, and the change fits without contortion.
- **Adapt:** the structure is mostly right but needs a seam — extract an interface, add an adapter, narrow a type. This is the lowest-risk default.
- **Replace:** only when the existing structure blocks the goal, is duplicated, or is unmaintained, AND a migration path plus rollback are defined. Never replace by standing up a parallel app or repo.

## Commands

```bash
# --- cycles / orphans ---
# circular deps and orphans (JS/TS)
npx madge --circular --extensions ts,tsx,js,jsx src
npx madge --orphans --extensions ts,tsx src

# --- dependency direction ---
# does domain/core import from ui/routes? (inversion)
rg -n "from ['\"].*(ui|routes|components|pages)" src/domain src/core 2>/dev/null

# boundary leaks: DB calls inside components/handlers
rg -n 'prisma\.|db\.query|sql`' src/components src/app 2>/dev/null

# --- duplication ---
# duplicate exported symbols (parallel implementations)
rg -oN 'export (?:function|const|class) (\w+)' -r '$1' src | sort | uniq -d

# competing HTTP or state libraries in the same codebase
rg -n "from ['\"](axios|node-fetch|redux|zustand|jotai|recoil)" src | sort | uniq -c

# --- god modules / fan-in ---
# most-imported local modules (god-module candidates)
rg -oN "from ['\"](\.[^'\"]+)['\"]" -r '$1' src | sort | uniq -c | sort -rn | head -20

# --- churn / risk ---
# high-change files are refactor risk
git log --since=6.months --name-only --pretty=format: | sort | uniq -c | sort -rn | head -20

# --- convention drift ---
# multiple error-handling shapes across the codebase
rg -n 'try\s*\{|\.catch\(|Result<|Either<|throw new' . | head

# multiple data-fetching patterns for the same concern
rg -n 'useQuery|useSWR|getServerSideProps|loader\(|fetch\(' . | head

# --- layer boundaries ---
# framework types leaking into the domain layer
rg -n "import .*(react|express|next|@nestjs)" src/domain src/core 2>/dev/null

# --- duplication depth ---
# copy-pasted blocks via repeated function signatures
rg -oN 'function (\w+)\(' -r '$1' src | sort | uniq -c | sort -rn | head
```

## Common issues & anti-patterns

- **Dependency inversion:** a `domain` module imports a React component or an Express type, so the business logic can no longer be reused or tested in isolation.
- **Parallel HTTP layers:** half the app uses an `axios` instance with interceptors and the other half uses bare `fetch`, so retries, auth headers, and error handling diverge.
- **Competing state stores:** the same server data lives in both a Redux slice and a Zustand store, and they drift out of sync.
- **God util:** a `helpers.ts` imported by thirty files; any change risks an unrelated regression and the file resists testing.
- **Replace-by-parallel-app:** instead of adapting the existing structure, a second app or package is stood up "to do it cleanly", doubling the maintenance surface and the drift.
- **Silent convention fork:** a new feature introduces its own error-handling shape, so error responses are now inconsistent across endpoints.
- **Unbounded blast radius:** a change scoped to one feature quietly edits eight shared files — a signal the seam is in the wrong place.
- **Circular dependency between layers:** `service` imports `controller` and `controller` imports `service`, creating load-order fragility and untestable units.
- **Premature abstraction:** a generic base class or plugin system built for one caller, adding indirection that obscures the single real path through the code.
- **Adapter avoided:** a new third-party client wired directly into twelve call sites instead of behind one adapter, so swapping or mocking it later means touching all twelve.
- **Replace without rollback:** a proposal to swap a core module with no migration sequence or fallback, so a mid-migration failure leaves the app in an unshippable state.
- **Leaky repository:** a data-access layer that returns raw ORM entities up to the UI, so the database schema and the view are coupled and a column rename breaks the frontend.
- **Convention by copy-paste:** each new endpoint copies the previous one's structure including its quirks, so a single bad pattern propagates instead of a shared helper.
- **Hidden temporal coupling:** two calls that must happen in a specific order with nothing in the types or signatures enforcing it, so a reordering silently breaks behavior.
- **Shotgun surgery:** adding one field requires edits in the model, the DTO, the mapper, the validator, and three components, signaling responsibilities are smeared across layers.
- **Anemic seam:** an interface exists but every implementation is identical and there is only one, so the abstraction adds indirection without buying flexibility.
- **Framework lock in the core:** business rules written directly against a framework's request or ORM objects, so the logic cannot be unit-tested without booting the framework.
- **Duplicated date/money logic:** two or three hand-rolled helpers for the same formatting or arithmetic, which drift apart and produce inconsistent values across screens.
- **Conditional sprawl:** a single function that branches on a type flag everywhere instead of polymorphism, so each new variant edits many call sites rather than adding one implementation.

## When a rewrite is genuinely warranted

Recommend Replace only when all three hold: the existing structure provably blocks the goal (not merely inconvenient), the blast radius of adapting it exceeds the cost of replacing it, and a staged migration with a rollback at each step is defined. Even then, replace the component in place behind its existing seam — never by standing up a second app, repo, or framework alongside the first.

## Required output

Return: a module and dependency map; coupling and duplication findings with `file:line` evidence and severity; a Keep, Adapt, or Replace verdict per questioned component with rationale; the high-risk file list (high fan-in plus high churn); and the smallest change that fits the existing architecture. Do not recommend a rewrite unless the Keep/Adapt/Replace rule is met, and when Replace is chosen include the migration path and rollback.

## Safety

- Review-only by default; do not begin large refactors without an approved plan and a rollback path.
- Do not introduce a parallel framework, second app, or duplicate repo "to do it cleanly".
- Base every claim on file evidence, not assumption.
- Flag — do not silently make — cross-cutting changes that exceed the task scope.
- Redact any secret-like values surfaced while reading config.

## Completion criteria

Done means the architecture is mapped from evidence; coupling and duplication findings are concrete with `file:line`; each questioned component has a Keep, Adapt, or Replace decision with rationale (and any Replace carries a migration plus rollback path); the high-risk files are listed; and the recommended path is the smallest one that fits the existing structure.

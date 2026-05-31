---
name: architecture-review
description: Use when you need to evaluate architecture, coupling, duplication, integration fit, and whether to keep, adapt, or replace existing structures.
---

# Architecture Review

## Purpose
Use this skill to evaluate architecture, coupling, duplication, integration fit, and whether to keep, adapt, or replace existing structures. Every Keep/Adapt/Replace decision must be justified with file-level evidence — churn, blast radius, coupling — not intuition.

## When to use
- A new feature or refactor touches multiple modules and you need to confirm it follows the existing dependency direction before committing to a plan.
- Circular dependencies, god modules, or competing implementations of the same concern are suspected.
- A pull request or design proposal introduces a second way of solving something already solved (two HTTP clients, two state stores, conflicting conventions).
- Before a larger refactor, to establish which components to Keep, Adapt, or Replace and prove the blast radius is bounded.

## When not to use
- The task is unrelated to core operations work.
- The work would require production deploys, destructive data actions, or secret disclosure.
- A narrower skill or existing project instruction already covers the need.

## Procedure
1. Build a module map: top-level dirs, each one's responsibility, and the dependency direction between them. Locate the boundary between UI, domain/business logic, data access, and infrastructure.
2. Detect cycles and illegal dependencies (UI importing the DB client, domain importing a framework, lower layers importing higher ones).
3. Find duplication: parallel implementations of one concern (two HTTP clients, two state stores, two date utils), copy-pasted logic, competing patterns for the same job.
4. Assess integration fit for the change: does the proposed work follow existing data-fetching, error-handling, auth, and state conventions, or introduce a second way of doing the same thing?
5. For each questioned component, decide Keep / Adapt / Replace using the rule below, justified with evidence (churn, blast radius, coupling).
6. Surface the highest-risk files (high fan-in + high churn) and the smallest viable change that fits the existing structure.

## Concrete checks
- Dependency direction: does anything in `domain`/`core` import from `ui`/`routes`/`framework`? That's an inversion.
- God modules: one file imported by 20+ others, or a `utils`/`helpers` dumping ground.
- Duplication signals: two files exporting the same function name; two HTTP layers (`axios` + `fetch` wrappers); competing state solutions (Redux + Zustand + Context) for the same data.
- Boundary leaks: SQL/Prisma calls inside React components or route handlers; business rules embedded in UI.
- Coupling smell: changing one feature forces edits across 5+ unrelated files.

## Keep / Adapt / Replace rule
- **Keep**: pattern is consistent, tested, and the change fits without contortion.
- **Adapt**: structure is mostly right but needs a seam (extract interface, add adapter, narrow a type) — the lowest-risk default.
- **Replace**: only when the existing structure blocks the goal, is duplicated, or is unmaintained, AND the migration path + rollback are defined. Never replace by standing up a parallel app/repo.

## Commands
```bash
# circular deps and orphans (JS/TS)
npx madge --circular --extensions ts,tsx,js,jsx src
npx madge --orphans --extensions ts,tsx src
# churn hotspots (high-change files are refactor risk)
git log --since=6.months --name-only --pretty=format: | sort | uniq -c | sort -rn | head -20
# duplicate exported symbols
rg -oN 'export (?:function|const|class) (\w+)' -r '$1' src | sort | uniq -d
```

## Required output
Return: a module/dependency map, coupling + duplication findings (file:line evidence, severity), a Keep/Adapt/Replace verdict per questioned component with rationale, the high-risk file list, and the smallest change that fits the existing architecture. Do not recommend a rewrite unless the rule above is met.

## Safety checks
- Review-only by default; do not begin large refactors without an approved plan and rollback.
- Do not introduce a parallel framework, second app, or duplicate repo to "do it cleanly."
- Base every claim on file evidence, not assumption.
- Flag, don't silently make, cross-cutting changes that exceed the task scope.

## Completion criteria
Done means the architecture is mapped from evidence, coupling/duplication findings are concrete, each questioned component has a Keep/Adapt/Replace decision with rationale, and the recommended path is the smallest one that fits the existing structure.

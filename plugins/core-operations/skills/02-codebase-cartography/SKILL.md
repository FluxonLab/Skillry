---
name: codebase-cartography
description: Use when you need to map module layout, runtime boundaries, data flow, ownership zones, and high-risk files.
---

# Codebase Cartography

## Purpose

Produce a structured map of an unfamiliar or sprawling codebase: entry points, module boundaries, runtime process topology, data-flow paths, and files that are disproportionately risky to touch. It answers "what calls what, where does data come from, and which files must not break" before any significant change begins — so a cross-cutting edit starts with the full set of affected files known, not discovered mid-flight. The analysis is read-only and never executes scripts or installs dependencies.

## When to use

- You are about to make a cross-cutting change and need every file it will touch before starting.
- A new contributor needs a mental model of a repository they have never seen.
- An incident pointed to unexpected coupling between two modules and you must trace the call chain.
- You are refactoring a shared utility and need the full fan-out of callers across packages.
- A performance problem requires tracing the data path from HTTP request to database query and back.

## When not to use

- The codebase has fewer than about ten files — reading them directly is faster.
- You only need to understand a single, self-contained function — use Read and search directly.
- A current architecture document already exists — read it first.
- You need a runnability or health baseline rather than a structural map — use `repo-diagnostics`.

## Procedure

1. **Establish the top-level shape.** Run `find . -maxdepth 3 -type f | sort` or `tree -L 3`. Treat `src/`, `app/`, `packages/`, `services/`, `libs/`, `cmd/`, and `internal/` as strong signals of the module-decomposition model.
2. **Locate all process entry points.** Search for `main()` (Go, Rust, Java), `if __name__ == "__main__"` (Python), top-level `app.listen` or `server.listen` (Node), `@SpringBootApplication`, or Dockerfile `CMD`/`ENTRYPOINT`. Each is a runtime boundary.
3. **Trace the import graph for the top three to five central files.** For Node/TS: `rg -l "from '.*/moduleX'" --type ts`. For Python: `rg -l "import moduleX"`. For Go: `rg -l '"path/to/pkg"'`. Build a caller tree two levels deep — usually enough to spot unexpected coupling.
4. **Identify shared infrastructure modules.** Find files imported by ten or more others: database clients, logger instances, config loaders, error types, middleware chains. These are high-blast-radius on change.
5. **Map data flow for the primary feature path.** Trace one representative request: HTTP handler, then service or use-case, then repository or data-access, then external call or DB query, then response. Note where data is transformed, validated, or persisted.
6. **Find cross-runtime boundaries.** Look for queue producers and consumers (Bull, Kafka, SQS), cron schedulers, background workers, WebSocket upgrade handlers, and IPC. These run in separate async contexts and are a frequent source of hard-to-reproduce bugs.
7. **Flag high-risk files.** A file is high-risk when it has no tests, is imported by many modules, contains migration logic, manages secrets or config, or was last touched in a hotfix. Note these explicitly.
8. **Summarize ownership zones.** Group modules into logical domains (auth, billing, notifications, infra) and, from `git log` if available, note who predominantly owns each zone.

## Concrete checks

Structure and entry points:
- The top-level directory structure is documented to depth two or three.
- All process entry points are identified (servers, workers, cron, CLIs).
- The module-decomposition model (by layer, by feature, by package) is named.

Coupling and data flow:
- High-fan-in shared modules are listed with approximate importer counts.
- At least one representative request is traced end to end.
- Cross-runtime boundaries (queues, jobs, WebSockets, IPC) are identified.
- External service call sites (HTTP clients, SDK instantiations) are located.

Risk:
- High-risk files are flagged (no tests plus many importers, migrations, secret managers).
- Circular dependency or coupling anomalies are noted.
- The test-coverage distribution is noted — which modules have zero tests.
- Ownership zones are mapped to logical domains.
- Barrel files are traced through to their real consumers, not counted at face value.
- Module-scope env reads and config side effects are noted as hidden coupling.

## Commands

```bash
# --- top-level shape ---
# skeletal directory listing
find . -maxdepth 3 -type f -not -path '*/node_modules/*' -not -path '*/.git/*' | sort | head -60

# --- entry points ---
# process entry points across languages
rg -n 'def main\(|if __name__ == .__main__.|app\.listen|server\.listen|@SpringBootApplication' . | head
rg -n 'CMD|ENTRYPOINT' Dockerfile* 2>/dev/null

# --- fan-in ---
# which files import a given module (replace moduleX)
rg -l "from ['\"].*moduleX|import .*moduleX" .

# most-imported local modules (rough ranking of shared infra)
rg -oN "from ['\"](\.[^'\"]+)['\"]" -r '$1' . | sort | uniq -c | sort -rn | head -20

# --- cross-runtime boundaries ---
# queues, workers, cron, sockets, IPC
rg -n 'new Worker|Queue\(|kafka|sqs|cron\.schedule|new WebSocketServer|ipcMain|ipcRenderer' . | head

# --- data flow ---
# route handlers and service-layer entry points
rg -n 'router\.(get|post|put|delete)|@(Get|Post)\(|app\.(get|post)' . | head

# --- risk / churn ---
# high-change files are also high-risk
git log --since=6.months --name-only --pretty=format: 2>/dev/null | sort | uniq -c | sort -rn | head -20

# modules with no adjacent test file
rg -L --files -g '*.ts' src | rg -v '\.test\.|\.spec\.' | head

# --- external call sites ---
# HTTP clients and SDK instantiations (integration boundaries)
rg -n 'axios|fetch\(|new .*Client\(|createClient|http\.request' . | head

# --- config / secrets in module scope ---
# env reads at module scope (test-fragility / hidden coupling)
rg -n 'process\.env\.|os\.environ|Deno\.env' . | head

# --- barrel files ---
# index files that re-export and hide true import counts
fd -t f 'index.ts|index.js|__init__.py' . | head

# --- ownership ---
# predominant author per directory (if git history exists)
git log --pretty=format:'%an' --name-only 2>/dev/null | head -40
```

## Common issues & anti-patterns

- **Barrel-file illusion:** an `index.ts` re-exports many modules, making import counts look low — always trace through barrels to find real consumers.
- **God module:** a single `utils.ts` or `helpers.py` grown past 1000 lines with no cohesion; changes here ripple everywhere.
- **Hidden coupling via shared DB tables:** two services that look independent both write the same table with no shared schema contract.
- **Config loaded in module scope:** `const db = new Pool(process.env.DATABASE_URL)` at the top of a file breaks any test that does not set that env var.
- **Implicit fan-out through event emitters:** `emit('user.created')` has five subscribers but grepping the literal finds two — the rest build the string from constants.
- **Untested high-fan-in file:** the most-imported module has zero tests, so any change to it is unverified and high-blast-radius.
- **Dynamic import opacity:** modules loaded via a runtime string path that static search cannot resolve, leaving the true call graph ambiguous.
- **Circular dependency:** two modules import each other, which both `madge` and load-order bugs will surface; note it rather than untangle it during mapping.
- **Shared mutable singleton:** a global store or client instance mutated from many modules, so behavior depends on call order and is hard to reason about.
- **Feature spread across layers:** one feature's logic scattered across UI, a service, a util, and a worker with no single owning module, so a change requires touching all four.
- **Test coverage cliff:** the highest-traffic data path has tests only at the edges, leaving the transformation in the middle unverified.
- **Implicit env contract:** a module that silently depends on an env var read elsewhere, so it works in one entry point and fails in another with no obvious link.
- **Worker invisible to the map:** a background job registered via a string-named queue that the request-path search never surfaces, hiding a whole runtime branch.
- **Migration logic in app code:** schema changes applied imperatively from within a service rather than a tracked migration, making the data path's history impossible to reconstruct.
- **Re-export rename trap:** a barrel that re-exports a symbol under a new name, so call sites reference a name that never appears in the defining file and search misses them.
- **Lazy-loaded route module:** a route registered via a dynamic `import()` string that the entry-point scan does not resolve, leaving part of the request graph invisible.
- **Cross-package reach-in:** one package importing another package's internal file directly instead of its public entry, coupling them in a way the package boundary was meant to prevent.

## Required output

Return a structured map with:
- **Entry points:** file path plus process role for each runtime boundary.
- **Module ownership zones:** domain name mapped to packages or directories.
- **High-fan-in modules:** file path plus approximate import count plus what it provides.
- **Primary data-flow trace:** the step-by-step path for the most important feature (for example `POST /orders` to `OrderService` to `OrderRepository` to postgres).
- **Cross-runtime boundaries:** type (queue, cron, worker, IPC) plus producer file plus consumer file.
- **High-risk files:** path plus reason (no tests, many importers, migration, secret).
- **Recommended next step:** which module to investigate first given the active task.

## Safety

- Do not execute scripts or install dependencies during mapping — read-only analysis only.
- Do not commit generated diagrams or index files unless explicitly requested.
- When reading `.env` or config to understand shape, redact actual secret values — describe key names only.
- Note uncertainty where barrel files or dynamic imports make the true call graph ambiguous.

## Completion criteria

Done means the top-level structure, entry points, high-fan-in modules, one end-to-end data-flow trace, cross-runtime boundaries, and high-risk files are all documented with evidence; ownership zones are mapped; and the report names the single module to investigate first for the active task.

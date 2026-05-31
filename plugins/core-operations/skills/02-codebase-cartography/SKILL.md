---
name: codebase-cartography
description: Use when you need to map module layout, runtime boundaries, data flow, ownership zones, and high-risk files.
---

# Codebase Cartography

## Purpose
This skill produces a structured map of an unfamiliar or sprawling codebase: entry points, module boundaries, runtime process topology, data flow paths, and files that are disproportionately risky to touch. It answers "what calls what, where does data come from, and which files must not break" before any significant change begins.

## When to use
- You are about to make a cross-cutting change and need to know every file it will touch before starting.
- A new contributor needs a mental model of a repository they have never seen.
- An incident pointed to an unexpected coupling between two modules and you must trace the call chain.
- You are refactoring a shared utility and need the full fan-out of callers across packages.
- A performance problem requires tracing the data path from HTTP request to database query and back.

## When not to use
- The codebase has fewer than ~10 files — reading them directly is faster.
- You only need to understand a single, self-contained function; use Read and search tools directly.
- A project-specific architecture document already exists and is current — read that first.

## Procedure

1. **Establish the top-level shape.** Run `find . -maxdepth 3 -type f | sort` (or `tree -L 3 --gitignore`) to get a skeletal directory listing. Note: `src/`, `app/`, `packages/`, `services/`, `libs/`, `cmd/`, `internal/` are strong signals of the module decomposition model.

2. **Locate all process entry points.** Search for `main()` (Go/C/Rust/Java), `if __name__ == "__main__"` (Python), top-level `app.listen`/`server.listen` (Node), `@SpringBootApplication`, or Dockerfile `CMD`/`ENTRYPOINT`. Each is a runtime boundary.

3. **Trace the import/dependency graph for the top 3-5 most central files.** For Node/TS: `grep -r "from '.*/moduleX'" --include="*.ts" -l`. For Python: `grep -r "import moduleX" -l`. For Go: `grep -r '"path/to/pkg"' -l`. Build a rough caller tree — two levels deep is usually enough to spot unexpected coupling.

4. **Identify shared infrastructure modules.** Look for files imported by 10+ other files: database clients, logger instances, config loaders, error types, middleware chains. These are high-blast-radius on change.

5. **Map data flow for the primary feature path.** Trace a representative request: HTTP handler → service/use-case layer → repository/data-access → external call or DB query → response. Note where data is transformed, validated, or persisted.

6. **Find cross-runtime boundaries.** Look for queue producers/consumers (Bull, Kafka, SQS), cron schedulers, background workers, WebSocket upgrade handlers, and IPC mechanisms. These run in separate async contexts and are often the source of hard-to-reproduce bugs.

7. **Flag high-risk files.** A file is high-risk when: it has no tests, it is imported by many modules, it contains migration logic, it manages secrets/config, or it was last touched in a hotfix commit. Note these explicitly.

8. **Summarize ownership zones.** Group modules into logical domains (e.g., auth, billing, notifications, infra). Note which teams or contributors predominantly own each zone based on git log if available.

## Checklist
- [ ] Top-level directory structure documented (depth 2-3)
- [ ] All process entry points identified (servers, workers, cron, CLIs)
- [ ] High-fan-in shared modules listed (database client, logger, config, error types)
- [ ] Primary request data-flow traced end-to-end for at least one representative path
- [ ] Cross-runtime boundaries identified (queues, background jobs, WebSockets)
- [ ] External service call sites located (HTTP clients, SDK instantiations)
- [ ] High-risk files flagged (no tests + many importers, migration files, secret managers)
- [ ] Circular dependency or coupling anomalies noted
- [ ] Ownership zones mapped to logical domains
- [ ] Test coverage distribution noted — which modules have zero tests

## Common issues & anti-patterns

- **Barrel file illusion**: `index.ts` re-exports many modules, making import counts look low. Always trace through barrel files to find real consumers.
- **God module**: a single `utils.ts` or `helpers.py` that has grown to 1000+ lines with no internal cohesion — changes here ripple everywhere.
- **Hidden runtime coupling via shared DB tables**: two services that appear independent but both write to the same table without a shared schema contract.
- **Config loaded in module scope**: `const db = new Pool(process.env.DATABASE_URL)` at the top of a file means the module breaks in any test that does not set that env var.
- **Implicit fan-out through event emitters**: `EventEmitter.emit('user.created')` has subscribers in 5 files but grep for 'user.created' only finds 2 — the rest use string concatenation or constants.

## Required output
Return a structured map containing:
- **Entry points**: file path + process role for each runtime boundary
- **Module ownership zones**: domain name → list of packages/directories
- **High-fan-in modules**: file path + approximate import count + what it provides
- **Primary data-flow trace**: step-by-step path for the most important feature (e.g., POST /orders → OrderService → OrderRepository → postgres)
- **Cross-runtime boundaries**: type (queue/cron/worker) + producer file + consumer file
- **High-risk files**: path + reason (no tests / many importers / migration / secret)
- **Recommended next step**: which module to investigate first given the active task

## Safety
- Do not execute any scripts or install any dependencies during mapping — read-only analysis only.
- Do not commit any generated diagrams or index files unless explicitly requested.
- When reading `.env` or config files to understand shape, redact actual secret values in your output — describe the key names only.

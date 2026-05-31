---
name: database-and-prisma-review
description: Use when you need to inspect schema.prisma, migrations, seeds, generated clients, database safety, and persistence changes.
---

# Database And Prisma Review

## Purpose
Use this skill to inspect schema.prisma, migrations, seeds, generated clients, database safety, and persistence changes. Destructive changes — dropped columns, non-nullable additions without backfill, unbounded queries — are flagged as blocking before they reach a shared or production database.

## When to use
- A schema change was made and needs a migration safety review before `prisma migrate deploy` runs against staging or production.
- N+1 queries or unbounded `findMany()` calls are suspected after a new data-fetching feature was added.
- A seed or fixture script needs to be confirmed idempotent (`upsert` over `create`) before it runs on a shared development database.
- Migration drift is suspected — `prisma migrate status` has not been checked and the team is unsure whether applied migrations match the current schema.

## When not to use
- The task is unrelated to database and data work.
- The work would require production deploys, destructive data actions, or secret disclosure.
- A narrower skill or existing project instruction already covers the need.

## Procedure
1. Read `schema.prisma`: models, fields, relations, `@id`/`@unique`/`@@index`/`@@unique`, `@relation` with `onDelete`/`onUpdate`, enums, `@default`. Note missing indexes on FKs and frequent filter columns.
2. Review migration history: migrations are additive and append-only; never edit an already-applied migration. Run `prisma migrate status` to catch drift between schema, migrations, and the DB.
3. Separate local vs production flow: `migrate dev` (creates + applies, dev only) vs `migrate deploy` (applies existing, prod). Flag `db push` / `migrate reset` against anything but a local throwaway DB.
4. Scan for destructive changes: dropped tables/columns, type narrowing, a non-nullable column added without default/backfill, renamed columns (Prisma sees drop+add → data loss).
5. Review data access for N+1 and over-fetching: loops issuing queries, missing `include`/`select`, unbounded `findMany` without pagination.
6. Review seeds/fixtures for idempotency (`upsert` over `create`) and reset risk.
7. Confirm the generated client is regenerated, never hand-edited.

## Concrete checks
- FK columns without `@@index` (Postgres doesn't auto-index FKs) → slow joins.
- Adding a required column to a populated table without `@default` or a backfill step → migration fails / data loss.
- `onDelete: Cascade` that could silently wipe related rows; or a missing cascade leaving orphans.
- `migrate reset`, `db push --accept-data-loss`, `--force-reset` near a shared/prod DB → block.
- N+1: `for (...) { await prisma.x.findUnique(...) }`; fix with `include`, `where { id: { in } }`, or one grouped query.
- Unbounded queries: `findMany()` with no `take`/cursor on a growable table.
- Seeds using `create` (duplicates on re-run) instead of `upsert`.
- Editing generated output under `node_modules/.prisma` or `@prisma/client`.

## Commands
```bash
npx prisma validate # schema is valid
npx prisma format # canonical formatting
npx prisma migrate status # drift / pending / failed migrations
# preview the SQL a schema change would generate before applying
npx prisma migrate diff \
 --from-schema-datasource prisma/schema.prisma \
 --to-schema-datamodel prisma/schema.prisma --script
# N+1 / unbounded query smells
rg -n 'for\s*\(|\.map\(' src | rg 'prisma\.'
rg -n 'findMany\(\)' src
```

## Required output
Return: schema findings (missing indexes, risky relations), a migration-safety verdict (additive vs destructive, drift status), explicit flags for any destructive/reset command, N+1 / over-fetch findings with the fix, seed idempotency status, and the safe next command. Mark anything that could lose data as **blocking**.

## Safety checks
- Local-only by default; never run `migrate deploy`, `migrate reset`, `db push`, or seeds against a shared/production database.
- Back up before any destructive local migration; prefer additive migration + backfill over drop/recreate.
- Do not edit applied migrations or generated client code; regenerate with `prisma generate`.
- Redact credentials in `DATABASE_URL`.

## Completion criteria
Done means schema, migrations, data-access patterns, and seeds were reviewed from evidence, destructive/drift risks are flagged as blocking with a safe alternative, N+1/index issues have concrete fixes, and the next safe command is named.

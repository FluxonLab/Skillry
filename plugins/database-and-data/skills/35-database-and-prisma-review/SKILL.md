---
name: database-and-prisma-review
description: Use when you need to inspect schema.prisma, migrations, seeds, generated clients, database safety, and persistence changes.
---

# Database And Prisma Review

## Purpose
Inspect `schema.prisma`, migration history, seed scripts, the generated client, and the data-access code that depends on them, then issue a migration-safety verdict. Destructive changes — dropped columns, narrowed types, non-nullable columns added without a backfill, unbounded queries, and reset commands aimed at a shared database — are flagged as **blocking** before they reach staging or production. The review is local-only by default and produces concrete fixes plus the next safe command, never a destructive action.

## When to use
- A schema change was made and needs a safety review before `prisma migrate deploy` runs against staging or production.
- N+1 queries or unbounded `findMany()` calls are suspected after a new data-fetching feature.
- A seed or fixture script must be confirmed idempotent before it runs against a shared development database.
- Migration drift is suspected — `prisma migrate status` has not been checked and it is unclear whether applied migrations match the schema.
- A pull request edits `schema.prisma`, a file under `prisma/migrations/`, or the seed script.

## When not to use
- The task is unrelated to database / persistence work.
- The work requires production deploys, destructive data actions, or secret disclosure (this skill reviews; it never runs the destructive command).
- The database is not Prisma-managed and a Prisma-specific lens does not apply — use the relevant SQL/ORM review instead.
- A narrower skill (query-performance, migration-safety) already covers the exact concern.

## Procedure
1. **Read `schema.prisma`.** Inventory models, fields, relations, and attributes: `@id`, `@unique`, `@@index`, `@@unique`, `@relation` with `onDelete`/`onUpdate`, enums, and `@default`. Note missing indexes on foreign keys and on frequently filtered columns.
2. **Review migration history.** Migrations must be additive and append-only; never edit a migration that has already been applied. Run `prisma migrate status` to detect drift between schema, the migrations folder, and the live database.
3. **Separate local vs production flow.** `migrate dev` creates and applies (development only); `migrate deploy` applies existing migrations (production). Flag any `db push`, `migrate reset`, or `--force-reset` aimed at anything other than a local throwaway database.
4. **Scan for destructive changes.** Dropped tables/columns, type narrowing, a non-nullable column added with no `@default` or backfill step, and column renames (Prisma sees a rename as drop + add → data loss). Each is blocking until proven safe.
5. **Review data access for N+1 and over-fetching.** Loops issuing one query per item, missing `include`/`select`, and unbounded `findMany` with no `take`/cursor on a growable table.
6. **Review seeds/fixtures.** Confirm idempotency (`upsert` over `create`) and that no seed performs a reset on a shared database.
7. **Verify upsert preconditions.** Every `upsert` and `connectOrCreate` must target a field backed by `@unique`/`@@unique`; without it the operation inserts duplicates under concurrency.
8. **Check backfill isolation.** Any column-add that ends in a constraint must split the backfill into its own batched step so a large table is not locked during the migration.
9. **Confirm the generated client is regenerated, not hand-edited** — never patch files under `node_modules/.prisma` or `@prisma/client`.

## Concrete checks
- Foreign-key columns lacking `@@index` (Postgres does not auto-index FKs) → slow joins.
- A required column added to a populated table without `@default` or a backfill step → migration fails / data loss.
- `onDelete: Cascade` that could silently wipe related rows, or a missing cascade leaving orphans.
- `migrate reset`, `db push --accept-data-loss`, or `--force-reset` near a shared/production database → block.
- N+1: `for (...) { await prisma.x.findUnique(...) }`; fix with `include`, `where: { id: { in } }`, or one grouped query.
- Unbounded queries: `findMany()` with no `take`/cursor on a table that grows.
- Seeds using `create` (which duplicates on re-run) instead of `upsert`.
- Edits to generated output under `node_modules/.prisma` or `@prisma/client`.
- A column rename expressed as drop + add with no data-preserving migration.
- A backfill bundled into the same migration as a `NOT NULL`/constraint change (lock + blocked writes on a large table).
- An `upsert` whose target field has no `@unique`/`@@unique` constraint (duplicate inserts under concurrency).
- An enum member renamed by value rather than added-then-migrated (breaks existing rows in Postgres).

## Commands
```bash
# Schema validity and canonical formatting
npx prisma validate
npx prisma format

# Drift / pending / failed migrations (run this first on any schema PR)
npx prisma migrate status

# Preview the SQL a schema change WOULD generate, without applying it
npx prisma migrate diff \
  --from-schema-datasource prisma/schema.prisma \
  --to-schema-datamodel  prisma/schema.prisma --script

# Inspect the latest committed migration for destructive statements
ls -t prisma/migrations/*/migration.sql | head -1 | xargs rg -n "DROP|ALTER COLUMN|NOT NULL|RENAME"

# N+1 and unbounded-query smells in application code
rg -n "for\s*\(|\.map\(|\.forEach\(" src | rg "prisma\."
rg -n "findMany\(\)" src
rg -n "findMany\(" src | rg -v "take:|cursor:"

# FK columns vs declared indexes (spot missing @@index)
rg -n "@relation" prisma/schema.prisma ; rg -n "@@index" prisma/schema.prisma

# Confirm no one edited the generated client
git diff --name-only | rg "node_modules/.prisma|@prisma/client" && echo "BLOCK: generated client edited"

# Scan the pending migration SQL for every destructive verb
rg -n "DROP TABLE|DROP COLUMN|ALTER COLUMN .* TYPE|SET NOT NULL|RENAME (COLUMN|TO)|TRUNCATE" \
  prisma/migrations/*/migration.sql

# Seeds: create (duplicates on re-run) vs upsert (idempotent)
rg -n "\.create\(|\.createMany\(" prisma/seed.* ; rg -n "\.upsert\(" prisma/seed.*

# Upserts whose target field lacks a unique constraint (duplicate risk)
rg -n "\.upsert\(|connectOrCreate" src/ prisma/
rg -n "@unique|@@unique" prisma/schema.prisma

# Raw SQL bypassing Prisma's parameterization (injection + drift risk)
rg -n "\$queryRawUnsafe|\$executeRawUnsafe|\$queryRaw\`.*\$\{" src/

# Confirm DATABASE_URL points at a local DB before any migrate command
rg -n "DATABASE_URL" .env* | sed -E 's#(://[^:]+:)[^@]+@#\1****@#'   # redact the password
```

## Safe column-add (expand / migrate / contract)
```sql
-- Step 1 (expand): add the column nullable, no default backfill yet
ALTER TABLE "Order" ADD COLUMN "currency" TEXT;
-- Step 2 (migrate): backfill in batches to avoid a long table lock
UPDATE "Order" SET "currency" = 'USD' WHERE "currency" IS NULL;  -- batch by id range in prod
-- Step 3 (contract, a LATER migration): enforce the constraint once data is clean
ALTER TABLE "Order" ALTER COLUMN "currency" SET NOT NULL;
```

## N+1 fix patterns (Prisma)
```ts
// WRONG: one query per order (N+1)
const orders = await prisma.order.findMany();
for (const o of orders) o.user = await prisma.user.findUnique({ where: { id: o.userId } });

// RIGHT: a single relational fetch
const orders = await prisma.order.findMany({ include: { user: true } });

// WRONG: unbounded — loads the whole table into memory
const all = await prisma.event.findMany();
// RIGHT: paginate with a cursor
const page = await prisma.event.findMany({ take: 50, cursor: { id: lastId }, skip: 1 });
```

## Destructive-operation classification
| Operation | Risk | Safe alternative |
|-----------|------|------------------|
| `DROP COLUMN` | data loss | deprecate, stop writing, drop in a later release |
| add `NOT NULL` to populated table | migration fails | nullable → backfill → set not null |
| column rename | drop + add = data loss | hand-written `RENAME COLUMN` migration |
| `migrate reset` / `db push --accept-data-loss` | wipes data | restrict to local disposable DB only |
| `onDelete: Cascade` added | silent bulk delete | confirm intent; consider `Restrict`/`SetNull` |

## Common issues & anti-patterns
- **Editing an already-applied migration.** Changing a committed `migration.sql` desyncs the migration checksum from the database; `migrate deploy` then fails on every environment. Add a new migration instead.
- **Required column on a populated table.** `String` (non-nullable) added without `@default` or a backfill fails the moment it runs against real data. Add nullable → backfill → enforce non-null in a later migration.
- **Column rename = data loss.** Renaming a field in `schema.prisma` makes Prisma drop the old column and add a new empty one. Use a hand-written rename migration to preserve data.
- **`migrate reset` in a script.** A seed or CI step that resets the database is catastrophic if it ever points at a shared environment. Restrict reset to a clearly local, disposable database.
- **N+1 in a list endpoint.** A loop calling `findUnique` per row turns one request into hundreds of queries; replace with `include` or a single `where: { id: { in: [...] } }`.
- **Patching the generated client.** Hand-edits under `@prisma/client` vanish on the next `prisma generate`. Change the schema and regenerate.
- **Backfill inside the same migration as the constraint.** A single migration that adds the column, backfills, and sets `NOT NULL` holds a long lock on a big table and blocks writes. Split backfill from the constraint and batch it.
- **Missing unique constraint behind an upsert.** `upsert` relies on a unique field; without the `@unique`/`@@unique`, it inserts duplicates under concurrency. Confirm the constraint exists.
- **`include` everything everywhere.** Eagerly including deep relations on a list endpoint over-fetches and can be its own performance problem. Select only the fields the caller needs.
- **Enum changed by value, not name.** Renaming an enum member is a destructive change in Postgres; existing rows holding the old value break. Add the new value, migrate rows, then remove the old.

## Required output
Return: schema findings (missing indexes, risky relations); a migration-safety verdict (additive vs destructive, drift status from `migrate status`); explicit flags for any destructive or reset command; N+1 / over-fetch findings with the fix; seed idempotency status; and the safe next command. Mark anything that could lose data as **blocking** and pair it with a non-destructive alternative.

## Safety
- Local-only by default; never run `migrate deploy`, `migrate reset`, `db push`, or seeds against a shared or production database.
- Back up before any destructive local migration; prefer additive migration + backfill over drop/recreate.
- Do not edit applied migrations or generated client code; regenerate with `prisma generate`.
- Redact credentials in `DATABASE_URL` whenever it appears in output.

## Completion criteria
Done means schema, migrations, data-access patterns, and seeds were reviewed from evidence, `migrate status` was run, every destructive or drift risk is flagged as blocking with a safe alternative, N+1 and index issues have concrete fixes, and the next safe command is named.

---
name: data-migration-safety
description: Use when you need to plan non-destructive data migrations, backups, idempotency, rollback, and local-only resets.
---

# Data Migration Safety

## Purpose

Plan and review schema and data migrations so they are reversible, low-downtime, and idempotent. Apply the expand-contract pattern for breaking changes, verify backfill strategy, and confirm rollback paths before any migration touches a production database.

## When to use

- A migration renames, removes, or changes the type of an existing column.
- A migration adds `NOT NULL` to a column that already has rows.
- A large backfill (millions of rows) needs to run without locking the table.
- Reviewing whether `prisma migrate deploy` vs `prisma migrate dev` is the right command for a given environment.
- A team member asks "is it safe to run this migration on prod?"

## When not to use

- The migration only adds a brand-new table or new nullable column — those are inherently safe.
- The task is a seed data load, not a schema change (use skill 38).
- The database has fewer than a few thousand rows and downtime is acceptable — simplified procedures apply.

## Procedure

### 1. Classify the migration risk

Before anything else, label every statement in the migration file:

| Statement | Risk | Reason |
|---|---|---|
| `CREATE TABLE` | Safe | No lock contention |
| `ADD COLUMN NULL` | Safe | Instant metadata change |
| `ADD COLUMN NOT NULL DEFAULT` | Postgres 11+: Safe | Default stored in catalog, no rewrite |
| `ADD COLUMN NOT NULL` (no default) | Unsafe | Table rewrite + lock |
| `DROP COLUMN` | Destructive | Irreversible without restore |
| `RENAME COLUMN` | Breaking | Breaks live code reading old name |
| `ALTER TYPE` | Unsafe | Often requires table rewrite |
| `CREATE INDEX` (no CONCURRENTLY) | Unsafe | Write lock on table |
| `CREATE INDEX CONCURRENTLY` | Safe | No write lock, cannot be in transaction |
| `TRUNCATE` | Destructive | Irreversible |
| `DELETE FROM` (unbounded) | Destructive | Irreversible |

### 2. Confirm backup exists before proceeding

For Supabase projects:
```bash
# Trigger a manual backup via Supabase CLI before running migrations
supabase db dump -f backup_$(date +%Y%m%d_%H%M%S).sql --data-only
supabase db dump -f schema_$(date +%Y%m%d_%H%M%S).sql
```

For self-managed Postgres:
```bash
pg_dump -Fc -d $DATABASE_URL -f backup_$(date +%Y%m%d_%H%M%S).pgc
```

Do not proceed to production migration without a restorable backup less than 1 hour old.

### 3. Apply the expand-contract pattern for breaking changes

Never rename or drop in a single deploy. Use three separate deploys:

**Phase 1 — Expand (add new, keep old):**
```sql
ALTER TABLE orders ADD COLUMN customer_id UUID REFERENCES customers(id);
-- Backfill (see step 4)
UPDATE orders SET customer_id = (SELECT id FROM customers WHERE email = orders.user_email) WHERE customer_id IS NULL;
-- Add NOT NULL only after backfill is complete and verified
ALTER TABLE orders ALTER COLUMN customer_id SET NOT NULL;
```
Deploy application code that writes BOTH `user_email` and `customer_id`.

**Phase 2 — Migrate reads:**
Deploy application code that reads `customer_id` only. Keep writing both columns.

**Phase 3 — Contract (remove old column):**
```sql
-- Only after Phase 2 has been stable in production for at least one deploy cycle
ALTER TABLE orders DROP COLUMN user_email;
```

### 4. Backfill strategy for large tables

Never run a single `UPDATE` on millions of rows — it holds a lock and fills WAL:

```sql
-- Batched backfill: process 1000 rows at a time with a small sleep
DO $$
DECLARE
 batch_size INT := 1000;
 offset_val INT := 0;
 rows_updated INT;
BEGIN
 LOOP
 UPDATE orders
 SET customer_id = (
 SELECT id FROM customers WHERE email = orders.user_email
 )
 WHERE customer_id IS NULL
 AND id IN (
 SELECT id FROM orders WHERE customer_id IS NULL
 ORDER BY id
 LIMIT batch_size
 );

 GET DIAGNOSTICS rows_updated = ROW_COUNT;
 EXIT WHEN rows_updated = 0;
 PERFORM pg_sleep(0.05); -- 50ms pause between batches
 END LOOP;
END $$;
```

For Prisma projects, run the backfill as a standalone script (`ts-node scripts/backfill-customer-id.ts`) outside of the migration, so the migration file itself contains only schema DDL.

### 5. Adding NOT NULL safely (without table rewrite)

The single-step approach causes a full table scan and `ACCESS EXCLUSIVE` lock:
```sql
-- UNSAFE on large tables:
ALTER TABLE orders ALTER COLUMN customer_id SET NOT NULL;
```

Safe pattern using a constraint that is validated in the background:
```sql
-- Step 1: add NOT VALID constraint (fast, no scan)
ALTER TABLE orders ADD CONSTRAINT orders_customer_id_not_null
 CHECK (customer_id IS NOT NULL) NOT VALID;

-- Step 2: validate in background (SHARE UPDATE EXCLUSIVE, allows reads+writes)
ALTER TABLE orders VALIDATE CONSTRAINT orders_customer_id_not_null;

-- Step 3 (optional, Postgres 12+): promote to actual NOT NULL
-- Only if you need pg_attribute.attnotnull = true
ALTER TABLE orders ALTER COLUMN customer_id SET NOT NULL;
ALTER TABLE orders DROP CONSTRAINT orders_customer_id_not_null;
```

Steps 1 and 2 happen in separate transactions. Step 2 can run during business hours.

### 6. Ensure idempotency

Every migration must be safe to run twice without error:

```sql
-- Column already exists guard
DO $$ BEGIN
 IF NOT EXISTS (
 SELECT 1 FROM information_schema.columns
 WHERE table_name = 'orders' AND column_name = 'customer_id'
 ) THEN
 ALTER TABLE orders ADD COLUMN customer_id UUID;
 END IF;
END $$;

-- Index already exists guard
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);

-- Constraint already exists guard
DO $$ BEGIN
 IF NOT EXISTS (
 SELECT 1 FROM pg_constraint WHERE conname = 'orders_customer_id_fk'
 ) THEN
 ALTER TABLE orders ADD CONSTRAINT orders_customer_id_fk
 FOREIGN KEY (customer_id) REFERENCES customers(id);
 END IF;
END $$;
```

### 7. Dry-run before production

```bash
# Prisma: check what would run without applying
npx prisma migrate diff \
 --from-schema-datasource prisma/schema.prisma \
 --to-schema-datamodel prisma/schema.prisma \
 --script

# Supabase: show pending migrations
supabase db diff

# Direct psql dry-run: wrap in a transaction and roll back
psql $DATABASE_URL -c "BEGIN; $(cat migration.sql); ROLLBACK;"
```

### 8. Prisma migrate dev vs deploy

| Command | Use for | Effect |
|---|---|---|
| `prisma migrate dev` | Local development only | Creates migration file, applies it, regenerates client |
| `prisma migrate deploy` | CI/CD and production | Applies pending migrations only, never creates new ones |
| `prisma migrate reset` | Local dev only | Drops + recreates the entire database |

**Never run `prisma migrate dev` or `prisma migrate reset` against a production or staging database.**

## Checklist

- [ ] Backup taken and verified restorable within the last hour
- [ ] Every statement in the migration classified (Safe / Unsafe / Destructive)
- [ ] Breaking changes use expand-contract across at least two deploys
- [ ] Large backfills are batched, not a single `UPDATE` statement
- [ ] `NOT NULL` on existing column uses `CHECK ... NOT VALID` + `VALIDATE CONSTRAINT`
- [ ] New indexes use `CREATE INDEX CONCURRENTLY IF NOT EXISTS`
- [ ] Migration file is idempotent (safe to run twice)
- [ ] Dry-run completed in a transaction that was rolled back
- [ ] `prisma migrate deploy` (not `dev`) scheduled for production
- [ ] Rollback plan documented: what SQL undoes this migration?

## Common issues & anti-patterns

**Dropping a column while old code is still deployed.** Even after deploying new code, the old version may still be running (blue/green, canary). Always wait a full deploy cycle before the contract phase removes columns.

**Mixing schema DDL and data DML in one migration.** Schema locks and data locks interact badly. Separate them: schema migration first, then a standalone backfill script, then the `NOT NULL` constraint.

**Using `RENAME TABLE` or `RENAME COLUMN` without a view.** Create a view with the old name that selects from the new name, so old code keeps working during the transition.

**Forgetting to update sequences after a data import.** If you `INSERT` rows with explicit IDs, the sequence is not advanced:
```sql
SELECT setval(pg_get_serial_sequence('orders', 'id'), MAX(id)) FROM orders;
```

**Running migrations inside application startup.** `prisma migrate deploy` in a Docker entrypoint on a multi-replica deployment causes race conditions. Run migrations as a one-off job/init container before scaling up replicas.

## Required output

For each migration reviewed, produce:
1. **Risk classification table**: every SQL statement labeled.
2. **Blocking analysis**: which statements acquire `ACCESS EXCLUSIVE` locks and for how long.
3. **Estimated downtime**: based on table size and statement type.
4. **Safe rewrite**: revised migration using expand-contract / CONCURRENTLY / NOT VALID where needed.
5. **Rollback SQL**: the exact statements that undo this migration.
6. **Deploy order**: Phase 1 / Phase 2 / Phase 3 with what application code must be deployed between phases.

## Safety

- Never execute any migration against production without a verified backup.
- Never run `prisma migrate dev`, `prisma migrate reset`, or `DROP DATABASE` against non-local environments.
- Treat `TRUNCATE` as equivalent to `DROP TABLE` + recreate — it is irreversible without a restore.
- If downtime cannot be guaranteed to be zero, escalate to the team before proceeding.
- All dry-runs must end with `ROLLBACK`, not `COMMIT`.

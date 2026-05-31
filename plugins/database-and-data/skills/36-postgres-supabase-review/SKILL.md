---
name: postgres-supabase-review
description: Use when you need to review Postgres and Supabase schemas, policies, migrations, indexes, and local versus production boundaries.
---

# Postgres & Supabase Review

## Purpose

Conduct a structured review of a Supabase/Postgres project: schema design, Row-Level Security policies, indexes, foreign keys, migrations directory hygiene, connection pooling configuration, and auth.users coupling. Surface concrete risks with evidence from actual files, never from assumptions.

## When to use

- A PR adds or modifies migrations, RLS policies, or schema changes in a Supabase project.
- A bug report hints at data leakage, missing RLS, or slow queries on Supabase tables.
- Onboarding a new project and auditing its database layer for security and performance correctness.
- The `supabase/migrations/` directory has grown and no one has reviewed policy coverage recently.

## When not to use

- The project uses a non-Postgres database (MySQL, SQLite, Mongo) — use a generic DB review instead.
- The task is a pure ORM-level TypeScript fix with no schema changes.
- You are already mid-migration with a running transaction; complete it first, review after.

## Procedure

### 1. Orient to the project layout

```bash
ls supabase/migrations/ # migration files in chronological order
ls supabase/functions/ # edge functions that may use service_role
grep -r "service_role" . --include="*.ts" --include="*.env*" -l
grep -r "supabaseAdmin\|createClient.*service_role" . --include="*.ts" -n
```

Confirm which client (`anon` vs `service_role`) each backend surface uses. `service_role` bypasses RLS entirely — every usage must be intentional and server-side only.

### 2. Audit RLS coverage

```sql
-- Run in Supabase SQL editor or psql
SELECT
 schemaname,
 tablename,
 rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
```

Any table with `rowsecurity = false` that holds user data is a critical finding. Then check existing policies:

```sql
SELECT
 schemaname,
 tablename,
 policyname,
 permissive,
 roles,
 cmd,
 qual,
 with_check
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, cmd;
```

Look for:
- Tables with `INSERT`/`UPDATE` policy but no `SELECT` policy (read leak).
- Policies using `auth.uid()` correctly vs. hardcoded UUIDs or `true` (open access).
- Policies that reference `auth.users` directly instead of `auth.uid()` — can cause plan regressions.

### 3. Check foreign key and index alignment

```sql
-- Missing indexes on FK columns (common performance trap)
SELECT
 tc.table_name,
 kcu.column_name,
 ccu.table_name AS foreign_table,
 ccu.column_name AS foreign_column
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
 ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
 ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
 AND NOT EXISTS (
 SELECT 1 FROM pg_indexes
 WHERE tablename = tc.table_name
 AND indexdef LIKE '%' || kcu.column_name || '%'
 );
```

Every FK column that is queried from the child side needs an index. Without it, deletes and joins on the parent produce sequential scans.

### 4. Validate migration file hygiene

```bash
# Migrations must be append-only; no editing of already-applied files
git log --oneline supabase/migrations/
git diff main -- supabase/migrations/ # should only show NEW files, never edits to old ones
```

Check that each migration file:
- Has a transaction wrapper (`BEGIN`/`COMMIT`) or uses `supabase migrate` which wraps automatically.
- Does not contain `DROP TABLE` or `DROP COLUMN` without a preceding backup/rename step.
- Does not add `NOT NULL` to an existing column in one step (see skill 37 for the safe pattern).

### 5. Review connection pooling configuration

In `supabase/config.toml` or project settings:

```toml
[db.pooler]
enabled = true
pool_mode = "transaction" # transaction mode for stateless APIs
default_pool_size = 15
max_client_conn = 100
```

- **Transaction mode** (pgBouncer): correct for serverless/edge functions. Session-level features (`SET LOCAL`, prepared statements, advisory locks) do NOT work in transaction mode.
- **Session mode**: required if using `LISTEN/NOTIFY`, advisory locks, or session variables. Verify the app does not mix modes.
- Check `max_client_conn` against your Supabase plan's connection limit. Exceeding it causes `FATAL: remaining connection slots are reserved`.

### 6. Inspect auth.users coupling

```sql
-- Profiles table should reference auth.users via FK
SELECT
 tc.table_name, kcu.column_name, ccu.table_name AS ref_table
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name
WHERE ccu.table_name = 'users' AND ccu.table_schema = 'auth';
```

Confirm the profiles/user metadata table has:
```sql
id UUID REFERENCES auth.users(id) ON DELETE CASCADE
```
Missing `ON DELETE CASCADE` leaves orphaned rows when a user is deleted from Supabase Auth.

### 7. Run EXPLAIN ANALYZE on suspicious queries

```sql
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT p.*, u.email
FROM posts p
JOIN auth.users u ON u.id = p.user_id
WHERE p.team_id = '00000000-0000-0000-0000-000000000001'
ORDER BY p.created_at DESC
LIMIT 20;
```

Red flags: `Seq Scan` on large tables, `Rows Removed by Filter` much larger than actual rows, `Buffers: shared hit=0 read=N` (cold cache), nested loop with high `actual rows`.

## Checklist

- [ ] All public tables have RLS enabled (`rowsecurity = true`)
- [ ] No policy uses bare `true` as `qual` for sensitive tables
- [ ] `service_role` client is never used client-side (browser/mobile)
- [ ] Every FK column on the child side has an index
- [ ] Migration files are append-only (no edits to historical files)
- [ ] `NOT NULL` additions go through expand-contract (see skill 37)
- [ ] pgBouncer mode matches the app's session feature usage
- [ ] `auth.users` FK has `ON DELETE CASCADE` where appropriate
- [ ] `anon` key is safe to expose; `service_role` key is in server env only
- [ ] `EXPLAIN ANALYZE` shows index scans, not sequential scans, on hot paths

## Common issues & anti-patterns

**RLS bypass via service_role in client code.** Any JavaScript bundle that contains `service_role` key is a critical secret leak. Grep for it in `next.config.js`, `.env.local` committed to git, or Vite build output.

**Policies that call functions with SECURITY DEFINER.** A `SECURITY DEFINER` function runs as its owner (often `postgres`), bypassing RLS of tables it touches internally. Audit every function referenced in a policy.

**Adding `NOT NULL` in a single migration step on a live table.** Postgres takes an `ACCESS EXCLUSIVE` lock and rewrites the table. On millions of rows this causes downtime. Use `ALTER COLUMN ... SET DEFAULT` + backfill + `SET NOT NULL` + `DROP DEFAULT` across multiple deploys.

**Querying `auth.users` directly from application code.** Supabase exposes `auth.users` but it contains sensitive fields. Build a `public.profiles` view or table and expose only what you need with RLS.

**Missing `CONCURRENTLY` on index creation in migrations.** `CREATE INDEX` without `CONCURRENTLY` locks the table for writes. Use `CREATE INDEX CONCURRENTLY` in a migration that is NOT inside a transaction block (`supabase migration new --no-transaction`).

**Sequence exhaustion on `SERIAL` columns.** Use `BIGSERIAL` or `UUID` for tables expected to grow past 2 billion rows. Check current sequence values:
```sql
SELECT sequencename, last_value, max_value FROM pg_sequences WHERE schemaname = 'public';
```

## Required output

Produce a structured report with:
1. **RLS coverage table**: list every public table, its `rowsecurity` status, and policy count per command.
2. **Security findings**: ranked Critical / High / Medium / Low with exact table/policy names.
3. **Performance findings**: missing indexes, sequential scans found, estimated row counts.
4. **Migration hygiene**: any edited historical files, unsafe DDL patterns.
5. **Recommended SQL**: ready-to-run corrective statements (wrapped in a transaction where safe).
6. **Next safe command**: the single most important action to take next.

## Safety

- Never execute `DROP`, `TRUNCATE`, `DELETE`, or `ALTER TABLE ... DROP COLUMN` as part of the review.
- Never print or log `service_role` or `anon` keys found in files.
- Never modify migration files that have already been applied to any environment.
- All `EXPLAIN ANALYZE` runs are read-only and safe against production if you have read access.
- If you cannot determine whether a change is safe, recommend it with a warning rather than executing it.

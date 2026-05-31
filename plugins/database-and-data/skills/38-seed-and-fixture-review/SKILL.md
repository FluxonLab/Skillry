---
name: seed-and-fixture-review
description: Use when you need to review seed scripts, fixtures, test data, idempotency, and reset risk.
---

# Seed & Fixture Review

## Purpose

Review seed scripts and test fixtures for idempotency, referential integrity order, deterministic data generation, test isolation, and the risk of accidentally running against production. Catch patterns that cause CI flakiness, FK violations, or data pollution before they reach a shared environment.

## When to use

- A PR adds or modifies a `seed.ts`, `seed.sql`, `fixtures/`, or `factories/` directory.
- CI tests are flaky because fixture data conflicts between runs.
- A developer reports "the seed failed with FK violation" or "duplicate key" errors.
- Auditing whether seed data can accidentally reach a staging or production database.
- Reviewing Prisma `db seed`, Django fixtures, or Rails `db:seed` scripts for correctness.

## When not to use

- The task is a schema migration, not seed data (use skill 37).
- The project has no seed or test fixture layer at all.
- The only change is to application code that happens to read seeded data.

## Procedure

### 1. Locate all seed and fixture entry points

```bash
# Prisma
grep -r '"seed"' package.json
cat prisma/seed.ts 2>/dev/null || cat prisma/seed.js 2>/dev/null

# SQL seeds
find . -name "seed*.sql" -o -name "*.fixture.sql" | head -20

# Test factories
find . -path "*/factories/*" -o -path "*/fixtures/*" | grep -E "\.(ts|js|json|yaml|yml)$" | head -20

# Django
find . -name "*.json" -path "*/fixtures/*" | head -20

# Rails
find . -name "seeds.rb" | head -5
```

### 2. Check idempotency

A seed script that fails on the second run will break CI pipelines that do not reset the DB between runs. Every insert must use upsert semantics:

**Prisma (TypeScript):**
```typescript
// BAD: fails if row exists
await prisma.user.create({
 data: { id: 'user-seed-001', email: 'admin@example.com', role: 'ADMIN' },
});

// GOOD: idempotent upsert
await prisma.user.upsert({
 where: { id: 'user-seed-001' },
 update: { role: 'ADMIN' },
 create: { id: 'user-seed-001', email: 'admin@example.com', role: 'ADMIN' },
});
```

**SQL:**
```sql
-- BAD: fails on re-run
INSERT INTO roles (id, name) VALUES (1, 'admin');

-- GOOD: idempotent
INSERT INTO roles (id, name) VALUES (1, 'admin')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name;

-- Or skip silently
INSERT INTO roles (id, name) VALUES (1, 'admin')
ON CONFLICT DO NOTHING;
```

**Django:**
```python
# BAD: fails on re-run
User.objects.create(username='admin', ...)

# GOOD: idempotent
User.objects.get_or_create(username='admin', defaults={'email': 'admin@example.com'})
```

### 3. Verify FK insertion order

Foreign key constraints enforce referential integrity — inserting a child before its parent raises a violation. Map the dependency graph:

```
auth.users → profiles → teams → team_members
categories → posts → comments → comment_likes
```

The seed must insert in dependency order (parents first, children last). Check for circular dependencies — if they exist, disable and re-enable FK checks per table:

```sql
-- Only if truly necessary; prefer correct ordering instead
SET session_replication_role = 'replica'; -- disables FK checks for this session
-- ... inserts ...
SET session_replication_role = 'origin'; -- re-enables FK checks
```

Document why circular FK is needed; it is usually a sign of a schema design problem.

### 4. Verify deterministic data

Faker-generated data is fine for development seeds but must be pinned to a fixed seed value for test fixtures:

**JavaScript/TypeScript (faker.js):**
```typescript
import { faker } from '@faker-js/faker';

// BAD: different data every run → snapshot tests fail, IDs unpredictable
const email = faker.internet.email();

// GOOD: deterministic with fixed seed
faker.seed(12345);
const email = faker.internet.email(); // always same value
```

**Python (Faker):**
```python
from faker import Faker
fake = Faker()

# BAD
fake.name()

# GOOD
Faker.seed(42)
fake.name() # deterministic
```

UUIDs used as fixture IDs must be hardcoded, not generated at runtime:
```typescript
const SEED_USER_ID = '00000000-0000-0000-0000-000000000001'; // fixed, never dynamic
```

### 5. Check test fixture isolation

Each test or test suite must start from a known state. Patterns to verify:

**Prisma test setup (Jest/Vitest):**
```typescript
beforeEach(async () => {
 // Truncate in reverse FK order
 await prisma.$executeRaw`TRUNCATE comment_likes, comments, posts, categories RESTART IDENTITY CASCADE`;
 await seedTestData(prisma);
});

afterAll(async () => {
 await prisma.$disconnect();
});
```

**Check for global fixture state that leaks between tests:**
```bash
grep -rn "beforeAll.*seed\|afterAll.*seed" --include="*.test.ts" --include="*.spec.ts" .
# If seeds run in beforeAll instead of beforeEach, tests are not isolated
```

**Database-per-test (most isolated, slowest):** each test gets its own schema:
```typescript
const schema = `test_${crypto.randomUUID().replace(/-/g, '')}`;
await prisma.$executeRawUnsafe(`CREATE SCHEMA ${schema}`);
// ... run migrations against this schema ...
// cleanup in afterEach
await prisma.$executeRawUnsafe(`DROP SCHEMA ${schema} CASCADE`);
```

### 6. Detect production safety risks

```bash
# Check if seed script reads DATABASE_URL without environment guard
grep -n "DATABASE_URL\|process.env" prisma/seed.ts | head -20

# Look for environment guard at the top of seed scripts
grep -n "NODE_ENV\|APP_ENV\|ENVIRONMENT" prisma/seed.ts | head -10
```

Every seed script that performs destructive operations (`TRUNCATE`, mass `DELETE`, `RESTART IDENTITY`) must have an environment guard:

```typescript
// prisma/seed.ts
if (process.env.NODE_ENV === 'production') {
 throw new Error('Seed script must not run in production. Aborting.');
}
```

Check `package.json` to see how seed is invoked:
```json
{
 "prisma": {
 "seed": "ts-node --compiler-options '{\"module\":\"CommonJS\"}' prisma/seed.ts"
 }
}
```

If `prisma db seed` is called in a deployment pipeline, it can run against production. The environment guard is the last line of defense.

### 7. Review TRUNCATE and RESTART IDENTITY usage

```bash
grep -rn "TRUNCATE\|RESTART IDENTITY\|DROP.*CASCADE" --include="*.sql" --include="*.ts" --include="*.js" .
```

`TRUNCATE ... CASCADE` will truncate all tables that reference the target via FK — this is often wider than the developer expects. List the cascade chain:

```sql
-- Find tables that would be affected by CASCADE on a TRUNCATE of 'users'
SELECT
 tc.table_name AS child_table,
 kcu.column_name AS fk_column
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name
WHERE ccu.table_name = 'users' AND tc.constraint_type = 'FOREIGN KEY';
```

## Checklist

- [ ] All inserts use upsert semantics (`ON CONFLICT`, `upsert`, `get_or_create`)
- [ ] FK insertion order matches dependency graph (parents before children)
- [ ] Test fixture UUIDs/IDs are hardcoded, not dynamically generated
- [ ] Faker/random generators are seeded with a fixed integer
- [ ] Each test resets state in `beforeEach`, not just `beforeAll`
- [ ] `TRUNCATE ... CASCADE` scope is understood and intentional
- [ ] Production environment guard exists in any script with destructive operations
- [ ] Seed is not wired into the production deployment pipeline
- [ ] `prisma db seed` is gated behind `NODE_ENV !== 'production'`
- [ ] CI seed run time is under 10 seconds (slow seeds slow down all test runs)

## Common issues & anti-patterns

**Creating auth users in seed without Supabase Auth API.** Directly inserting into `auth.users` bypasses Supabase's hashing and may produce users that cannot log in. Use the Admin API or the Supabase CLI `supabase users create` for auth-linked seed users.

**Relying on `id SERIAL` auto-increment in fixtures.** If the sequence state differs between environments, fixture data with assumed IDs will fail. Use UUIDs with hardcoded values for fixture records.

**Factory functions that hit the real database during unit tests.** Factory-created records should only go to a test database. If the factory reads `DATABASE_URL` directly, a misconfiguration silently writes to the wrong database. Always inject the Prisma client into factory functions.

**Seeding lookup/enum tables with a separate script from the schema.** Enum values that belong in the schema (e.g., status values, role names) should be seeded in a migration using `ON CONFLICT DO NOTHING`, not in a separate seed script that may not run in production.

**Large fixture files checked into git.** JSON fixture files over ~500 KB slow down `git clone` and `git status`. Generate test data programmatically instead of storing it as static files.

## Required output

Produce a review report with:
1. **Idempotency verdict**: list every `INSERT` found and whether it is safe to re-run.
2. **FK order analysis**: the inferred insertion order and any violations found.
3. **Determinism check**: whether any dynamic/random values are used without a fixed seed.
4. **Isolation check**: `beforeEach` vs `beforeAll` pattern, and whether state leaks.
5. **Production safety**: whether destructive operations are guarded by environment checks.
6. **Corrected code snippets**: ready-to-apply fixes for every issue found.

## Safety

- Never run seed scripts against a staging or production database during a review.
- Never execute `TRUNCATE`, `DELETE FROM`, or `DROP` statements as part of the review itself.
- If a seed script lacks an environment guard, flag it as Critical and do not run it until the guard is added.
- Treat `RESTART IDENTITY CASCADE` as equivalent to a destructive migration — it resets auto-increment counters.

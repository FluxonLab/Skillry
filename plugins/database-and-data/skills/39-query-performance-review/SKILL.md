---
name: query-performance-review
description: Use when you need to review query plans, indexes, N+1 risks, pagination, and data access patterns.
---

# Query Performance Review

## Purpose

Identify and fix query performance problems: N+1 query patterns, missing indexes, sequential scans on large tables, unbounded result sets, bad pagination, and over-fetching with `SELECT *`. Produce evidence-backed findings from `EXPLAIN ANALYZE` output and ORM query logs, not from guesswork.

## When to use

- A slow query is reported in production logs or APM tooling.
- A PR introduces new ORM queries and no one has checked the generated SQL.
- A table has grown past ~100K rows and queries that were fast are now slow.
- Reviewing pagination, infinite scroll, or "load more" implementations.
- An API endpoint has response times above 500ms with no obvious application cause.

## When not to use

- The bottleneck is confirmed to be network latency, external API calls, or CPU-bound computation, not database queries.
- The table has fewer than 10K rows and no high-traffic queries — optimization is premature.
- The task is schema design for a brand-new feature with no existing data.

## Procedure

### 1. Enable and collect slow query evidence

**Postgres slow query log (postgresql.conf or Supabase):**
```sql
-- Check current slow query threshold
SHOW log_min_duration_statement;

-- Set threshold temporarily for investigation (logs queries > 100ms)
SET log_min_duration_statement = 100;
```

**Prisma query logging:**
```typescript
const prisma = new PrismaClient({
 log: [
 { emit: 'event', level: 'query' },
 ],
});

prisma.$on('query', (e) => {
 if (e.duration > 100) {
 console.log(`SLOW QUERY (${e.duration}ms): ${e.query}`);
 console.log('Params:', e.params);
 }
});
```

**Supabase Performance Advisor:** check the Supabase dashboard under Database > Performance for auto-detected slow queries and missing indexes.

### 2. Read EXPLAIN ANALYZE output correctly

```sql
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT u.id, u.email, p.title, p.created_at
FROM users u
JOIN posts p ON p.user_id = u.id
WHERE u.team_id = $1
 AND p.status = 'published'
ORDER BY p.created_at DESC
LIMIT 20;
```

Key signals to look for:

| Output token | Meaning | Action |
|---|---|---|
| `Seq Scan on posts` | Full table scan | Add index on `status` or composite `(user_id, status)` |
| `Rows Removed by Filter: 94820` | Reading 94K rows to return 20 | Index the filter column |
| `actual rows=1 loops=5000` | Loop executed 5000 times | Classic N+1 pattern |
| `Hash Join ... Batches: 8` | Join spilled to disk | Increase `work_mem` or reduce result set |
| `Buffers: shared read=12000 hit=0` | All reads from disk | Cold cache or table too large for cache |
| `cost=0.00..99999.99` | Planner estimate | Compare to `actual time` — big gap means stale stats |
| `Index Scan using idx_posts_user_id` | Index used correctly | Good |
| `Bitmap Heap Scan` | Index used, heap fetches needed | Usually fine; check `Heap Blocks: lossy` |

**Run ANALYZE to refresh planner statistics when estimates are far off:**
```sql
ANALYZE VERBOSE posts;
```

### 3. Detect N+1 query patterns

N+1 occurs when code fetches a list of records and then issues one query per record for a related object.

**ORM code that produces N+1 (Prisma example):**
```typescript
// N+1: fetches N posts, then N separate queries for each post's author
const posts = await prisma.post.findMany({ where: { status: 'published' } });
for (const post of posts) {
 const author = await prisma.user.findUnique({ where: { id: post.userId } });
 console.log(post.title, author.name);
}
```

**Fixed with eager loading:**
```typescript
// Single query with JOIN
const posts = await prisma.post.findMany({
 where: { status: 'published' },
 include: { author: true }, // generates LEFT JOIN, not N separate queries
});
```

**Detection from query logs:** look for the same query template repeating with different parameter values in rapid succession:
```
Query: SELECT * FROM users WHERE id = $1 Params: ["uuid-1"] Duration: 2ms
Query: SELECT * FROM users WHERE id = $1 Params: ["uuid-2"] Duration: 2ms
Query: SELECT * FROM users WHERE id = $1 Params: ["uuid-3"] Duration: 2ms
-- This pattern repeated 47 times = N+1
```

**DataLoader pattern for N+1 in GraphQL/API resolvers:**
```typescript
import DataLoader from 'dataloader';

const userLoader = new DataLoader(async (ids: string[]) => {
 const users = await prisma.user.findMany({ where: { id: { in: ids } } });
 return ids.map(id => users.find(u => u.id === id) ?? null);
});

// Now each resolver call is batched into a single IN query
const author = await userLoader.load(post.userId);
```

### 4. Create indexes correctly

**Single column index for equality filters:**
```sql
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_posts_status
 ON posts(status);
```

**Composite index: put equality columns first, range/order columns last:**
```sql
-- Query: WHERE team_id = $1 AND status = 'published' ORDER BY created_at DESC
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_posts_team_status_created
 ON posts(team_id, status, created_at DESC);
```

**Partial index for high-selectivity conditions (much smaller, faster):**
```sql
-- Only index published posts — if 90% are drafts, this index is tiny and fast
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_posts_published_created
 ON posts(created_at DESC)
 WHERE status = 'published';
```

**Expression index for case-insensitive search:**
```sql
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email_lower
 ON users(LOWER(email));
-- Query must use LOWER() too: WHERE LOWER(email) = LOWER($1)
```

**Check existing indexes before creating new ones:**
```sql
SELECT
 indexname,
 indexdef,
 pg_size_pretty(pg_relation_size(indexname::regclass)) AS index_size
FROM pg_indexes
WHERE tablename = 'posts'
ORDER BY pg_relation_size(indexname::regclass) DESC;
```

### 5. Fix pagination: keyset vs OFFSET

`OFFSET`-based pagination degrades as the offset grows because Postgres must read and discard all preceding rows:

```sql
-- OFFSET pagination: O(offset) cost — gets slower with every page
SELECT * FROM posts ORDER BY created_at DESC LIMIT 20 OFFSET 10000;
-- Must read 10020 rows, discard 10000, return 20. On page 500 this is catastrophic.
```

**Keyset (cursor) pagination: O(1) cost regardless of page:**
```sql
-- First page
SELECT id, title, created_at FROM posts
WHERE status = 'published'
ORDER BY created_at DESC, id DESC
LIMIT 20;

-- Next page: use last row's (created_at, id) as cursor
SELECT id, title, created_at FROM posts
WHERE status = 'published'
 AND (created_at, id) < ($last_created_at, $last_id)
ORDER BY created_at DESC, id DESC
LIMIT 20;
```

The composite `(created_at DESC, id DESC)` index makes every page fetch equally fast.

**When OFFSET is acceptable:** admin UIs with small datasets, reporting queries run infrequently, or when the user must jump to arbitrary pages (keyset cannot do random page jumps efficiently).

### 6. Eliminate SELECT *

```typescript
// BAD: fetches all columns, including large text fields and blobs
const posts = await prisma.post.findMany();

// GOOD: fetch only what the response needs
const posts = await prisma.post.findMany({
 select: {
 id: true,
 title: true,
 createdAt: true,
 author: { select: { name: true, avatarUrl: true } },
 },
});
```

In raw SQL, `SELECT *` prevents the planner from using index-only scans (the heap must always be visited). Explicit column lists allow covering indexes:

```sql
-- Covering index: index contains all columns needed by the query
CREATE INDEX CONCURRENTLY idx_posts_covering
 ON posts(team_id, status) INCLUDE (title, created_at, author_id);

-- This query now satisfies entirely from the index, never touches the heap
SELECT title, created_at, author_id
FROM posts
WHERE team_id = $1 AND status = 'published';
```

### 7. Check connection and query count per request

```bash
# Count active connections by application
SELECT application_name, count(*) FROM pg_stat_activity GROUP BY application_name ORDER BY count DESC;

# Find long-running queries
SELECT pid, now() - pg_stat_activity.query_start AS duration, query, state
FROM pg_stat_activity
WHERE state != 'idle' AND (now() - query_start) > interval '5 seconds'
ORDER BY duration DESC;
```

If connection count is near the limit, review pgBouncer configuration (see skill 36). Each serverless function invocation that opens its own `PrismaClient` is a new connection — use a singleton pattern:

```typescript
// lib/prisma.ts — singleton for Next.js / serverless
import { PrismaClient } from '@prisma/client';

const globalForPrisma = globalThis as unknown as { prisma: PrismaClient };

export const prisma =
 globalForPrisma.prisma ??
 new PrismaClient({ log: process.env.NODE_ENV === 'development' ? ['query'] : [] });

if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = prisma;
```

## Checklist

- [ ] `EXPLAIN (ANALYZE, BUFFERS)` run on every query taking > 100ms
- [ ] No `Seq Scan` on tables with more than 50K rows in hot paths
- [ ] No `Rows Removed by Filter` count greatly exceeding returned rows
- [ ] N+1 patterns replaced with eager loading or DataLoader batching
- [ ] New indexes use `CREATE INDEX CONCURRENTLY IF NOT EXISTS`
- [ ] Composite index column order matches query equality-then-range pattern
- [ ] Pagination on large tables uses keyset/cursor, not OFFSET
- [ ] `SELECT *` replaced with explicit column lists on high-traffic queries
- [ ] No new `PrismaClient` instantiated per-request in serverless environments
- [ ] Planner statistics are fresh (`ANALYZE` run after bulk data loads)

## Common issues & anti-patterns

**Indexing a low-cardinality column alone.** An index on `status` with only 3 possible values is rarely used by the planner — it may prefer a seq scan. Use a partial index or a composite index with a higher-cardinality leading column.

**Not measuring after adding an index.** Indexes speed up reads but slow down writes. Always `EXPLAIN ANALYZE` the query after the index is created to confirm it is used, and benchmark write throughput on insert-heavy tables.

**ORM `.findMany()` without a `take` limit.** An endpoint that returns all matching rows will eventually OOM or time out as the table grows. Always add `take`/`LIMIT` to list queries.

**Using `count(*)` on large tables without an index-only scan path.** `SELECT COUNT(*) FROM posts WHERE status = 'published'` on 10M rows is slow without an index. Use a partial index and confirm the plan shows `Index Only Scan`.

**Calling `prisma.$queryRaw` with string interpolation.** Beyond the SQL injection risk, raw queries bypass Prisma's query logging hooks, making them invisible to performance monitoring. Use tagged template literals: `prisma.$queryRaw\`SELECT ...\`` which parameterizes safely and logs correctly.

**Joining across schemas without awareness of planner statistics.** Supabase queries joining `public` tables with `auth.users` may have stale statistics on `auth.users`. Run `ANALYZE auth.users` (requires elevated privileges) or use a materialized view in `public` that caches the joined data.

## Required output

Produce a performance report with:
1. **Query inventory**: list every slow query found, with current execution time and table sizes.
2. **EXPLAIN ANALYZE excerpt**: the most expensive node from each plan with interpretation.
3. **Root cause**: N+1 / missing index / bad pagination / SELECT * / stale stats — labelled per query.
4. **Recommended fix**: exact SQL (`CREATE INDEX CONCURRENTLY ...`) or ORM change (code snippet).
5. **Expected improvement**: estimated reduction in execution time or rows scanned after fix.
6. **Verification step**: the `EXPLAIN ANALYZE` command to run after applying the fix to confirm improvement.

## Safety

- `EXPLAIN ANALYZE` executes the query — do not run on destructive statements (`DELETE`, `UPDATE`) without wrapping in a transaction that is rolled back.
- `CREATE INDEX CONCURRENTLY` cannot run inside a transaction block. Run it in a standalone session.
- Never drop an index without first confirming it is unused: check `pg_stat_user_indexes.idx_scan` over a representative time window.
- Do not raise `work_mem` globally — it multiplies per sort/hash node per query. Set it per-session for specific heavy queries only.
- All performance changes should be tested against a copy of production data, not just synthetic test data.

---
name: backend-implementation-review
description: Use when you need to review server-side implementation for correctness, maintainability, validation, and observability.
---

# Backend Implementation Review

## Purpose
Perform a structured review of server-side code for the correctness problems that ordinary code review most often misses: missing input validation, broken transaction boundaries, race conditions in concurrent writes, non-idempotent mutation endpoints, insecure direct object references, and N+1 query patterns that become correctness problems under load. This goes beyond style — it hunts for code that fails silently or incorrectly under real-world data and concurrency, and rates each finding by severity with a concrete fix.

## When to use
- Reviewing a new API endpoint or mutation handler before it ships.
- A bug report points to data corruption or inconsistent state and you need to review the write path that caused it.
- Adding a payment, order, or other financially/legally sensitive operation to an existing service.
- Reviewing a bulk operation (import, migration, batch update) for correctness under partial failure.
- A PR touches database write logic and you want a systematic correctness pass.

## When not to use
- The review is purely about style, naming, or formatting — use a linter or a style review.
- The code is a read-only query handler with no side effects — narrow the scope; the risk is lower.
- The service is a throwaway prototype — apply judgment about appropriate rigor.

## Procedure
1. **Map the full request lifecycle per endpoint.** Trace HTTP handler → middleware (auth, rate limit, body parse) → validation → service/use-case → repository/data-access → async side effects (queues, emails, webhooks). Note every failure point and what happens to in-flight data when it fails.
2. **Audit input validation at every trust boundary.** Check type coercion (`"0"` treated as falsy), length/range checks (unbounded strings into fixed-length columns), enum validation (a `role` accepting any string), and presence checks (optional fields read without a null guard). Validation must live in the handler/service, not only as a DB constraint.
3. **Review transaction boundaries.** Any operation writing to more than one table, or writing then sending a side effect, must wrap DB writes in one transaction and emit side effects only after commit — or use an outbox. Flag `await db.insert(order); await email.send(...)` where a failed email orphans the order.
4. **Check idempotency on mutation endpoints.** Anything retriable (payment webhooks, queue consumers, mobile retry) must be idempotent. Flag `INSERT` without `ON CONFLICT`/idempotency-key checks, charges without an existing-charge check, and delta `UPDATE`s (`balance = balance + amount`) with no dedup guard.
5. **Identify race conditions.** Flag read-then-write (`SELECT count; if count < limit: INSERT`) without a row lock or `SELECT ... FOR UPDATE`. For optimistic locking (`UPDATE ... WHERE version = $1`), confirm the 0-rows-updated case is handled.
6. **Review error handling for silent failure.** No empty/`console.log`-only catch blocks; no fire-and-forget async (missing `await`); `Promise.allSettled` rejections explicitly inspected; background jobs log/alert on failure rather than retrying silently.
7. **Find N+1 query patterns.** Loops that issue a query per item (`for (user of users) { await db.query('... WHERE user_id=$1', [user.id]) }`) — a performance problem that becomes a timeout/OOM correctness problem at scale.
8. **Verify authorization at the data layer.** A route-level `req.user.isAdmin` check does not stop a non-admin reading another user's record. Confirm queries filter by the authenticated tenant/org/owner, not only by the ID from the URL.
9. **Review for insecure direct object references.** Any endpoint taking an ID from the request must confirm the record belongs to the caller's context: `SELECT * FROM orders WHERE id=$1` is vulnerable without `AND org_id=$2`.

## Concrete checks
- All user-supplied fields validated for type, length, range, and presence before use.
- Multi-table writes wrapped in one transaction or an outbox pattern.
- Side effects (emails, queues, webhooks) emitted only after a successful commit.
- Mutation endpoints idempotent or guarded by an explicit idempotency key.
- Read-then-write sequences use `SELECT FOR UPDATE` or optimistic locking with conflict handling.
- No empty or swallowing catch blocks; all errors logged and propagated.
- No `Promise.allSettled` results silently ignored.
- No N+1 query patterns in collection endpoints.
- Authorization enforced at the data layer (tenant/owner filter), not only the route.
- No insecure direct object references; ownership verified before returning data.
- Background-job failures logged, alerted, and not silently dropped.
- Bulk operations handle partial failure deliberately (all-or-nothing vs best-effort with a failure log).
- No mass assignment: writable fields are whitelisted, never the whole request body.
- Money and other security-relevant totals are recomputed server-side, never trusted from the client.
- Every write entry point is validated, including bulk-import and admin paths, not just the primary create route.

## Commands
```bash
# Locate write paths and their handlers
rg -n "INSERT INTO|UPDATE .* SET|\.create\(|\.update\(|\.delete\(" src/

# Side effect immediately after a write (transaction-boundary smell)
rg -nU "(insert|create|save)\([^)]*\)[\s\S]{0,120}(sendEmail|publish|enqueue|fetch|axios)" src/

# Fire-and-forget async (missing await) and swallowed errors
rg -n "^\s*[a-zA-Z].*\b(async|Promise)\b" src/ | rg -v "await"
rg -nU "catch\s*\([^)]*\)\s*\{\s*(\}|//|console\.log)" src/

# Idempotency: inserts without ON CONFLICT / upsert
rg -n "INSERT INTO" src/ | rg -v "ON CONFLICT"

# Race conditions: read-then-write without a lock
rg -n "SELECT .* FROM" src/ | rg -v "FOR UPDATE" ; rg -n "FOR UPDATE" src/

# N+1: a query inside a loop / map
rg -nU "(for\s*\(|\.map\(|\.forEach\()[\s\S]{0,200}(query|findUnique|findFirst|SELECT)" src/

# IDOR: lookups by request id with no tenant/owner filter
rg -n "WHERE id\s*=\s*\$1" src/ | rg -v "org_id|tenant_id|user_id"
```
```bash
# Framework-specific validation coverage
rg -n "z\.object\(|Joi\.|class-validator|@IsString|pydantic|BaseModel" src/   # which validator, where
rg -n "router\.(post|put|patch|delete)\(" src/ | wc -l                         # mutation endpoint count
# Cross-reference: mutation routes that have NO validator import in the file
for f in $(rg -l "router\.(post|put|patch)\(" src/); do
  rg -q "z\.|Joi\.|@Is[A-Z]|validateBody" "$f" || echo "NO VALIDATION: $f"
done

# Transactions: do multi-write services actually open one?
rg -n "BEGIN|transaction\(|\$transaction\(|db\.transaction|with_for_update" src/

# Bulk endpoints and their partial-failure handling
rg -nU "(forEach|for .* of|map)\([\s\S]{0,200}(insert|update|create)" src/ | head

# Mass-assignment: whole request body spread into a write
rg -n "\.\.\.req\.body|update\([^,]*,\s*req\.body|create\(\{\s*data:\s*req\.body" src/

# Money/total trusted from the client instead of recomputed server-side
rg -n "req\.body\.(total|amount|price|subtotal|quantity\s*\*)" src/

# Optimistic-lock conflicts: is the 0-rows-updated case handled?
rg -nU "WHERE .*version\s*=[\s\S]{0,120}(rowCount|affected|count)" src/ || echo "version check result may be ignored"
```

## Correct vs incorrect patterns
```ts
// WRONG: side effect before commit — a failed email orphans the order
const order = await db.insert(orders).values(input);
await mailer.sendReceipt(order.id);     // throws -> order persisted, no receipt sent, no rollback

// RIGHT: all writes in one transaction; side effect after commit
const order = await db.transaction(async (tx) => {
  const o = await tx.insert(orders).values(input);
  await tx.insert(orderLines).values(lines(o.id));
  return o;
});
await mailer.sendReceipt(order.id);     // commit already durable; safe to retry the email
```
```ts
// WRONG: read-then-write race — two requests both pass the check
const count = await db.count(seats, { eventId });
if (count < capacity) await db.insert(seats).values({ eventId, userId });

// RIGHT: let the database enforce it atomically
await db.insert(seats).values({ eventId, userId })
  .onConflictDoNothing();               // + a partial unique index / capacity constraint
```

## Common issues & anti-patterns
- **Validation only at the DB layer.** Relying on `NOT NULL`/`CHECK` means bad input surfaces as a cryptic 500 instead of a clean 400.
- **Transaction spanning an HTTP call.** Opening a transaction, calling a third party inside it, then committing — the transaction holds locks for the whole round trip and deadlocks under load.
- **Double-charge risk.** A payment endpoint that does not check for an existing completed charge with the same idempotency key before calling the gateway — a network timeout retries and charges twice.
- **Soft-delete without cascade.** Setting `deleted_at = NOW()` without handling foreign-key references means related rows still appear in joins to the "deleted" parent.
- **Background job that mutates without retry-safety.** A consumer that sends an email then marks the job done — crashing between the two sends the email twice on retry.
- **Mass assignment.** Spreading the whole request body into the model (`db.update(user, req.body)`) lets a caller set `isAdmin` or `balance`. Whitelist the writable fields.
- **Validation on the happy path only.** The handler validates the create path but a sibling bulk-import path writes raw input straight to the DB. Audit every write entry point, not just the obvious one.
- **Trusting the client-supplied total.** Recomputing nothing server-side and persisting `req.body.totalPrice` lets the client pay any amount. Recompute money on the server.

## Findings table format
```md
| endpoint            | category        | severity | file:line            | fix                                  |
|---------------------|-----------------|----------|----------------------|--------------------------------------|
| POST /orders        | transaction     | high     | services/order.ts:42 | wrap writes in tx; email after commit|
| GET /orders/:id     | IDOR            | critical | routes/order.ts:18   | add AND org_id = $ctx.orgId          |
| POST /charges       | idempotency     | critical | services/pay.ts:60   | check existing charge by key first   |
| GET /users          | N+1            | medium   | routes/user.ts:30    | batch with WHERE id IN (...)         |
```

## Required output
Report must include: **endpoints reviewed**; **input-validation gaps** (fields lacking validation + fix); **transaction-boundary issues** (locations where atomicity breaks); **idempotency gaps** (unsafe-to-retry endpoints + fix); **race conditions** (read-then-write without locking); **authorization gaps** (queries missing ownership filters); **N+1 patterns** (loop locations + batch-query fix); and a **severity rating per finding** (critical / high / medium / low).

## Safety
- Do not modify production database records to test a hypothesis about a bug — describe what a safe test would look like.
- When reviewing auth or authorization logic, only suggest strengthening checks, never weakening them.
- Flag any finding that is a data-breach vector (IDOR, missing auth check) as critical and surface it immediately, before completing the rest of the review.
- Redact any credentials, tokens, or PII encountered in code or fixtures before quoting them in the report.

## Completion criteria
Done means every reviewed endpoint's write path is traced, each of the validation/transaction/idempotency/race/authorization/N+1 categories is confirmed clean or reported with a file:line and a concrete fix, every finding carries a severity, and any breach-vector finding has been surfaced ahead of the rest.

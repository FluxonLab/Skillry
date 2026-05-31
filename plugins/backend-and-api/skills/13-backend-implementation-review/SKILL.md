---
name: backend-implementation-review
description: Use when you need to review server-side implementation for correctness, maintainability, validation, and observability.
---

# Backend Implementation Review

## Purpose
This skill performs a structured review of server-side code for the correctness problems that code review most commonly misses: missing input validation, broken transaction boundaries, race conditions in concurrent operations, non-idempotent mutation endpoints, and insufficient error handling. It goes beyond style — it looks for code that will fail silently or incorrectly under real-world load and data conditions.

## When to use
- Reviewing a new API endpoint or mutation handler before it ships to production.
- A bug report points to data corruption or inconsistent state — reviewing the write path that caused it.
- Adding a payment, order, or other financially or legally sensitive operation to an existing service.
- Reviewing a bulk operation (import, migration, batch update) for correctness under partial failure.
- A PR touches database write logic and the reviewer wants a systematic correctness check.

## When not to use
- The review is purely about code style, naming, or formatting — use a linter or style review.
- The code is a read-only query handler with no side effects — lower risk, narrower review scope needed.
- The service is a prototype or throwaway script — apply judgment about the appropriate rigor.

## Procedure

1. **Map the full request lifecycle for each endpoint under review.** From the HTTP handler: trace through middleware (auth, rate limit, body parse), validation layer, service/use-case layer, repository/data-access layer, and any async side effects (queues, emails, webhooks). Note every place where the request can fail and what happens to in-flight data when it does.

2. **Audit input validation at every trust boundary.** Check: are all user-supplied fields validated before use? Look for: missing type coercion (a string `"0"` treated as falsy), missing length/range checks (unbounded strings going into fixed-length DB columns), missing enum validation (a `role` field that accepts any string), and missing presence checks (optional fields accessed without null guard). Verify validation happens in the handler/controller, not only in the database constraint.

3. **Review transaction boundaries for multi-step write operations.** Every operation that writes to more than one table, or writes and then sends a side effect (email, queue message), must either: (a) wrap all DB writes in a single transaction and send side effects only after commit, or (b) use an outbox pattern. Look for: `await db.insert(order); await emailService.send(...)` — if the email call throws, is the order rolled back or is it orphaned?

4. **Check idempotency on mutation endpoints.** Any endpoint that can be retried (payment webhooks, queue consumers, mobile clients with retry logic) must be idempotent. Look for: `INSERT` without `ON CONFLICT DO NOTHING` or an idempotency key check, charge operations without checking for an existing charge with the same idempotency key, and `UPDATE` operations that apply a delta (`balance = balance + amount`) without a deduplication guard.

5. **Identify race conditions in concurrent write paths.** Look for: read-then-write patterns (`SELECT count; if count < limit: INSERT`) without a row-level lock or `SELECT ... FOR UPDATE`. Check optimistic locking: if the code reads a version number and then updates `WHERE version = $1`, is it correctly handling the case where 0 rows are updated (someone else won the race)?

6. **Review error handling for silent failure patterns.** Check that: no `catch` block swallows errors with an empty body or only a `console.log`. Async errors are not lost via unhandled Promise rejection (in Node: missing `await` on async calls inside an async function). Partial failures in `Promise.allSettled` are explicitly checked, not silently ignored. Background jobs log and alert on failure, not just retry silently.

7. **Check for N+1 query patterns in list/collection endpoints.** Find loops that execute a query per item: `for (const user of users) { const orders = await db.query('SELECT * FROM orders WHERE user_id = $1', [user.id]) }`. This is a performance problem that becomes a correctness problem under load (timeout, memory exhaustion).

8. **Verify authorization at the data layer, not just at the route level.** A middleware that checks `req.user.isAdmin` does not prevent a non-admin from calling `GET /api/users/:id` with another user's ID if the handler does not re-check ownership. Look for queries that filter only by the ID from the URL without also filtering by the authenticated user's tenant/org/ownership.

9. **Review for insecure direct object references.** Any endpoint that accepts an ID from the request (`/api/orders/:id`) and retrieves a record must confirm the record belongs to the authenticated user's context. `SELECT * FROM orders WHERE id = $1` is vulnerable if it does not also add `AND org_id = $2`.

## Checklist
- [ ] All user-supplied fields validated for type, length, range, and presence before use
- [ ] Multi-table writes wrapped in a single transaction or using outbox pattern
- [ ] Side effects (emails, queues, webhooks) sent only after successful DB commit
- [ ] Mutation endpoints are idempotent or have explicit idempotency key handling
- [ ] Read-then-write sequences use row-level locking (`SELECT FOR UPDATE`) or optimistic locking with conflict handling
- [ ] No empty or swallowed `catch` blocks — all errors logged and propagated
- [ ] No `Promise.allSettled` results silently ignored
- [ ] No N+1 query patterns in collection endpoints
- [ ] Authorization checked at the data level (tenant/owner filter), not only at the route level
- [ ] No insecure direct object references — record ownership verified before returning data
- [ ] Background job failure handling: errors are logged, alerted, and do not silently disappear
- [ ] Bulk operations handle partial failure correctly (all-or-nothing vs. best-effort with failure log)

## Common issues & anti-patterns

- **Validation only at the DB layer**: relying on `NOT NULL` or `CHECK` constraints to catch bad input means the error surfaces as a cryptic 500 instead of a user-friendly 400.
- **Transaction spanning an HTTP call**: opening a DB transaction, making an HTTP call to a third party inside it, then committing — the transaction holds locks for the entire HTTP round trip, causing deadlocks under concurrency.
- **Double-charge risk**: a payment endpoint that does not check for an existing completed charge with the same idempotency key before calling Stripe/Braintree — network timeout causes a retry that charges twice.
- **Soft-delete without cascade**: marking a record as `deleted_at = NOW()` without updating all foreign key references means related records still appear in queries that join to the "deleted" parent.
- **Background job that mutates without retry-safety**: a queue consumer that sends an email and then marks the job done — if it crashes after the email but before the ack, the email is sent twice on retry.

## Required output
Report must include:
- **Endpoints reviewed**: list of routes/handlers examined
- **Input validation gaps**: specific fields/parameters that lack validation, with suggested fix
- **Transaction boundary issues**: specific code locations where atomicity is broken
- **Idempotency gaps**: endpoints that are not safe to retry, with suggested fix
- **Race conditions identified**: specific read-then-write patterns without locking
- **Authorization gaps**: specific queries missing ownership filters
- **N+1 patterns**: specific loop locations and suggested batch query approach
- **Severity rating per finding**: critical / high / medium / low

## Safety
- Do not modify production database records to test a hypothesis about a bug — describe what a safe test would look like.
- When reviewing authentication or authorization logic, do not suggest weakening existing checks; only suggest strengthening.
- Flag any finding that could be a data breach vector (insecure direct object reference, missing auth check) as critical and surface it immediately, before completing the rest of the review.

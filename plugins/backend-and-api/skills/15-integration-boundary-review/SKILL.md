---
name: integration-boundary-review
description: Use when you need to review third-party service, webhook, queue, and cross-system integration boundaries.
---

# Integration Boundary Review

## Purpose
Review the code that crosses a system boundary — outbound HTTP calls to third-party APIs, inbound webhook handlers, message-queue producers/consumers, and internal service-to-service calls — for the reliability and correctness failures that only appear under real network conditions: missing timeouts, retry storms without backoff, bypassed webhook signature verification, duplicate message processing, and absent circuit breaking. Each finding is rated by severity with a concrete fix, and any missing webhook signature check is treated as a critical, surface-immediately issue.

## When to use
- Adding or reviewing a new integration with a third-party API (payments, SMS, email, chat, etc.).
- Implementing or reviewing an inbound webhook handler that receives events from a third party.
- Reviewing a queue producer or consumer (RabbitMQ, Kafka, SQS, BullMQ) for delivery and idempotency correctness.
- A payment or event handler is processing duplicates and causing double-billing or duplicate records.
- A slow or failing downstream is cascading into your own service's availability.
- A queue consumer is dropping failed messages or looping forever on a poison message and needs a dead-letter strategy.

## When not to use
- The integration is internal (same database, same process) — that is backend-implementation-review territory.
- The concern is only your own outbound rate (how much you call them), not the integration's reliability.
- An official SDK already handles retries/timeouts — verify its configuration rather than reviewing raw HTTP calls.

## Procedure
1. **Inventory all third-party call sites.** Search for `axios`, `fetch(`, `https.request`, `got(`, SDK client methods. For each, note the service, the operation, and whether it sits in a critical path (synchronous in a request handler) or a background path (worker, cron).
2. **Verify timeouts on every outbound call.** Every external call needs an explicit timeout; the default (often infinite) is dangerous in a request handler. Use ~2–5s critical-path, ~10–30s background. A call with no timeout holds a connection open and exhausts the pool under a slow downstream.
3. **Audit retry logic.** Retries must use exponential backoff with jitter (not fixed-interval loops that create a thundering herd during an outage), cap at 3–5 attempts, only auto-retry idempotent operations (POSTs need an idempotency key first), and never retry non-retryable codes (400/401/422).
4. **Verify webhook signature validation** before any processing, with the **raw** body (not parsed JSON) for HMAC. Stripe: `stripe.webhooks.constructEvent(rawBody, sig, secret)`. GitHub: HMAC-SHA256 of the raw body. Twilio: `validateRequest(...)`. An unverified webhook is an unauthenticated write endpoint anyone can trigger.
5. **Review idempotency in webhook/queue consumers.** At-least-once delivery (SQS, most webhooks) means duplicates. Confirm a dedup check at the top (`if exists(processed_events, event.id) return`) and a dedup write inside the same transaction as the business operation.
6. **Check circuit breakers on critical dependencies.** A breaker (cockatiel, opossum, resilience4j) stops calling a failing dependency after N consecutive failures so it can recover. Without one, a slow third party blocks every handler until timeout and cascades into a full outage.
7. **Review rate-limit handling.** `429 Too Many Requests` must trigger a backoff honoring the `Retry-After` header, not an immediate retry. A proactive client-side limiter or request queue protects strict monthly quotas.
8. **Audit error surfacing.** A failed call should translate to a meaningful internal error (not a re-thrown raw HTTP body), log the third-party error code + request ID + attempted operation, and fire a metric/alert on sustained failure-rate increase.
9. **Review queue producer guarantees.** Enqueue inside the DB transaction (outbox) or strictly after commit. Enqueuing after commit but in a separate step risks losing the event on a crash between the two — the outbox pattern removes that dual-write window.
10. **Review failure routing for consumers.** A message that fails processing should retry a bounded number of times then move to a dead-letter queue for inspection — never drop silently (lost work) or re-queue forever (poison-message loop).

## Concrete checks
- Explicit timeout on every outbound HTTP call (not OS/library default).
- Retries use exponential backoff with jitter and a max attempt cap.
- Non-idempotent POSTs carry an idempotency key before any auto-retry.
- Non-retryable status codes (4xx except 429) are not retried.
- Every inbound webhook validates the provider signature before processing.
- Webhook signature uses the raw Buffer/bytes, not parsed JSON.
- Queue and webhook consumers are idempotent against duplicate delivery.
- The dedup record is written in the same transaction as the business operation.
- A circuit breaker or bulkhead protects critical-path third-party calls.
- `429` responses respect `Retry-After` and back off.
- Integration failures are logged with the third-party error code and request ID.
- Consumer failures route to a dead-letter queue (parked for inspection), not silently dropped or infinitely re-queued.
- Queue messages are produced via outbox or strictly after commit.
- Replay is prevented: events outside a timestamp tolerance are rejected and event IDs are deduped.
- Webhook handlers acknowledge fast (queue heavy work) to stay within the provider's response deadline.
- Failure logs contain the third-party error code and request ID, never auth headers or full payloads.

## Commands
```bash
# Inventory outbound call sites
rg -n "axios\.|fetch\(|https?\.request|got\(|new .*Client\(" src/

# Calls missing an explicit timeout
rg -n "axios\.(get|post|put|delete|patch)\(" src/ | rg -v "timeout"
rg -n "fetch\(" src/ | rg -v "signal|AbortSignal\.timeout"

# Webhook handlers and whether they verify a signature
rg -n "router\.(post|all).*webhook|/webhook" src/
rg -n "constructEvent|validateRequest|hmac|createHmac|X-Hub-Signature|stripe-signature" src/

# Retry on non-retryable codes (smell: retrying 400/401/422)
rg -nU "retry[\s\S]{0,120}(400|401|422)" src/

# Consumer idempotency: dedup check before processing
rg -n "processed_events|idempotency|dedup|alreadyProcessed|message.*id" src/

# Circuit breaker presence
rg -n "opossum|cockatiel|circuitBreaker|resilience4j|breaker" src/

# Queue producer relative to transaction commit (outbox?)
rg -nU "(commit|COMMIT)[\s\S]{0,120}(publish|enqueue|sendMessage)" src/ ; rg -n "outbox" src/
```
```bash
# Raw-body access for webhooks (HMAC needs bytes, not parsed JSON)
rg -n "express\.raw\(|bodyParser\.raw|rawBody|request\.body\b" src/ | rg -i "webhook|stripe|hmac"

# Retry-After honored on 429?
rg -nU "429[\s\S]{0,120}(Retry-After|retryAfter|getResponseHeader)" src/ || echo "429 backoff not found"

# Timeouts that are dangerously high or absent on a critical path
rg -n "timeout:\s*(0|[6-9][0-9]{4,}|[0-9]{6,})" src/   # 0 = infinite, or > ~60s

# Replay protection: is the event timestamp checked against a tolerance window?
rg -nU "(timestamp|event\.created|tolerance)[\s\S]{0,120}(Date\.now|now\(\)|maxAge)" src/ \
  || echo "no replay/timestamp window found"

# Heavy work done synchronously inside a webhook handler (deadline risk)
rg -nU "(webhook|/hooks)[\s\S]{0,400}(sendEmail|await db\.|fetch\(|render)" src/ | head

# DLQ / failure routing for consumers (dropped vs parked on failure)
rg -n "deadLetter|dlq|nack|reject\(|moveToFailed|toDeadLetter" src/ || echo "no DLQ wiring found"
```

## Correct vs incorrect patterns
```ts
// WRONG: webhook trusted without verifying the signature
app.post('/webhook', express.json(), (req, res) => {
  fulfill(req.body.data.object);        // any caller can forge this
  res.sendStatus(200);
});

// RIGHT: verify the signature against the RAW body before doing anything
app.post('/webhook', express.raw({ type: 'application/json' }), (req, res) => {
  let event;
  try { event = stripe.webhooks.constructEvent(req.body, req.headers['stripe-signature'], secret); }
  catch { return res.sendStatus(400); }            // reject forged/replayed events
  if (await seen(event.id)) return res.sendStatus(200);   // idempotent on re-delivery
  await db.transaction(async (tx) => { await fulfill(tx, event); await markSeen(tx, event.id); });
  res.sendStatus(200);
});
```

## Webhook signature reference
| Provider | Verify with | Body form |
|----------|-------------|-----------|
| Stripe   | `stripe.webhooks.constructEvent(raw, sig, secret)` | raw bytes |
| GitHub   | HMAC-SHA256 of raw body vs `X-Hub-Signature-256`   | raw bytes |
| Twilio   | `twilio.validateRequest(token, sig, url, params)`  | parsed params + URL |
| Slack    | HMAC-SHA256 of `v0:ts:body` vs `X-Slack-Signature`  | raw body + timestamp |

## Common issues & anti-patterns
- **Webhook processed without a signature check.** The handler trusts the payload; any client can forge a payment event and trigger fulfillment. Critical — surface immediately.
- **Retry on all errors including 400.** A 400 is malformed and will always fail; retrying wastes quota. Retry only 429/500/502/503/504 and network errors.
- **No timeout on a critical-path call.** The downstream takes 30s during an incident, your pool exhausts in 10s, and your whole service is down for a problem in *their* data center.
- **Double processing without an idempotency guard.** The queue delivers the same event twice (normal), the consumer charges twice, support tickets flood in.
- **Synchronous webhook doing heavy work.** A handler that writes to the DB, sends emails, and calls other APIs in sequence exceeds the provider's 10–30s deadline, the provider retries, and the same work runs again. Acknowledge fast, process on a queue.
- **Parsed JSON used for HMAC.** Verifying the signature against `req.body` after a JSON middleware re-serialized it produces a different byte string and the check fails (or worse, is loosened to "skip if parse"). Capture the raw body.
- **Replay not prevented.** Signature is valid but the same event is accepted forever. Reject events older than a tolerance window and dedup by event ID.
- **Secrets logged on failure.** A catch block logs the full request including the `Authorization` header to a third party. Log the error code and request ID only.
- **Fixed-interval retry storm.** Retrying every 1s during a provider outage hammers them and burns your quota. Use exponential backoff with jitter.

## Required output
Report must include: **third-party call inventory** (service, operation, critical/background, timeout configured); **retry configuration findings** (strategy, backoff, max, non-retryable codes); **webhook signature status** per provider (validated / missing / misconfigured); **idempotency status** (dedup mechanism + transactional correctness); **circuit-breaker status** per critical dependency; **rate-limit handling** (429 backoff); **queue producer delivery guarantee** (outbox / post-commit / fire-and-forget); and a **severity rating per finding**.

## Safety
- Do not store or log webhook payloads that may contain PII or payment-card data from third parties.
- Do not replay captured production webhooks against a live consumer; use the provider's test events.
- Treat any outbound call with no timeout as a critical availability finding, not a style nit.
- Do not disable signature validation "temporarily" for debugging — use the provider's test mode or replay tools instead.
- Flag missing webhook signature validation as critical and surface it before completing the rest of the review.
- Redact API keys, signing secrets, and request IDs that could be sensitive before quoting them.

## Completion criteria
Done means every boundary call site is inventoried with its timeout and retry posture, each webhook handler's signature verification is confirmed or flagged critical, consumer idempotency and queue-producer delivery guarantees are assessed, circuit-breaker and rate-limit handling are reported, and every finding has a severity and a concrete fix.

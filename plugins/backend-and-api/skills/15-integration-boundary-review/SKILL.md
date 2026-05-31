---
name: integration-boundary-review
description: Use when you need to review third-party service, webhook, queue, and cross-system integration boundaries.
---

# Integration Boundary Review

## Purpose
This skill reviews the code that crosses a system boundary — outbound HTTP calls to third-party APIs, inbound webhook handlers, message queue producers/consumers, and internal service-to-service calls — for the reliability and correctness problems that only manifest under real network conditions: missing timeouts, no retry budget, webhook signature verification bypassed, duplicate message processing, and absent circuit breaking.

## When to use
- Adding or reviewing a new integration with a third-party API (Stripe, Twilio, SendGrid, Slack, etc.).
- Implementing or reviewing an inbound webhook handler that receives events from a third party.
- Reviewing a message queue producer or consumer (RabbitMQ, Kafka, SQS, BullMQ) for correctness.
- A payment or external event handler is processing duplicate events and causing double-billing or duplicate records.
- A downstream service going slow or down is causing your service to cascade-fail.

## When not to use
- The integration is internal (same database, same process) — that is backend-implementation-review territory.
- The concern is purely about rate limiting from your side (how much you call them), not about the reliability of the integration itself.
- A third-party SDK handles all the complexity (e.g., official Stripe SDK with built-in retry) — verify the SDK configuration instead of reviewing raw HTTP calls.

## Procedure

1. **Inventory all third-party call sites.** Search for: `axios.get/post`, `fetch(`, `https.request(`, `got(`, `superagent(`, `request(`, or SDK client method calls. For each: note the target service, the operation, and whether it is in a critical path (synchronous in a request handler) or a background path (queue worker, cron).

2. **Verify timeout configuration on every outbound HTTP call.** Every external call must have an explicit timeout. Defaults (infinite or 120s) are dangerous in a request handler. Recommended: 2-5s for critical-path calls, 10-30s for background calls. Check: `axios.create({ timeout: 5000 })`, `fetch(url, { signal: AbortSignal.timeout(5000) })`. A call without a timeout will hold a connection open indefinitely and exhaust your connection pool under a slow third-party response.

3. **Audit retry logic.** Check that: retries use exponential backoff with jitter (not fixed-interval retry loops that create thundering-herd on the third party during an outage). Retries are limited to a maximum count (3-5 for transient errors). Only idempotent operations are retried automatically — POST calls that create resources must use an idempotency key before retrying. Non-retryable errors (400 Bad Request, 401 Unauthorized, 422 Unprocessable Entity) are not retried.

4. **Verify webhook signature validation.** For every inbound webhook handler: confirm the signature from the request header is validated before any processing. Examples:
 - Stripe: `stripe.webhooks.constructEvent(body, sig, endpointSecret)` — body must be the raw buffer, not the parsed JSON.
 - GitHub: HMAC-SHA256 of the raw body using the webhook secret.
 - Twilio: `twilio.validateRequest(authToken, sig, url, params)`.
 A webhook handler that processes events without signature validation is an unauthenticated write endpoint — any caller can trigger it.

5. **Review idempotency handling in webhook and queue consumers.** For every consumer: check whether it handles re-delivery of the same event correctly. Look for: a deduplication check at the top (`if (await db.exists('processed_events', { id: event.id })) return`) before processing, and a final write to the `processed_events` table inside the same transaction as the business operation. Events delivered `at-least-once` (SQS, most webhooks) will be delivered multiple times — the consumer must be idempotent.

6. **Check for circuit breaker patterns on critical dependencies.** For each third-party call on a critical path: is there a circuit breaker (using `cockatiel`, `opossum`, `resilience4j`, or similar) that stops calling the dependency after N consecutive failures and gives it time to recover? Without a circuit breaker, a slow or failing third party will cause all your request handlers to block until their timeout, exhausting the thread/connection pool and cascading to a full service outage.

7. **Review rate limit handling.** Check: are `429 Too Many Requests` responses handled by backing off (using the `Retry-After` header value), not by retrying immediately? Is there a client-side rate limiter or request queue that prevents exceeding the third party's quota proactively (especially important for APIs with strict monthly quotas)?

8. **Audit error surfacing from integration failures.** When a third-party call fails: is the error translated to a meaningful internal error type (not `throw err` with the raw HTTP error body)? Is the failure logged with the third-party's error code, request ID, and the operation that was attempted? Is a metric or alert fired on sustained failure rate increase?

9. **Review message queue producer guarantees.** For queue producers: is the message enqueued inside a database transaction (outbox pattern) or after the transaction commits? If after: a crash between commit and enqueue means the event is lost. An outbox pattern (write to an `outbox` table in the same transaction, then a background process publishes from the outbox) provides at-least-once delivery without dual-write risk.

## Checklist
- [ ] Explicit timeout set on every outbound HTTP call (not relying on OS or library default)
- [ ] Retry logic uses exponential backoff with jitter and a maximum retry count
- [ ] Non-idempotent POST calls use an idempotency key before automatic retry
- [ ] Non-retryable HTTP status codes (4xx except 429) are not retried
- [ ] Every inbound webhook validates the provider signature before processing
- [ ] Webhook body is the raw Buffer/bytes when validating HMAC signatures (not parsed JSON)
- [ ] Queue and webhook consumers are idempotent — duplicate event delivery is handled safely
- [ ] Deduplication record written in the same transaction as the business operation
- [ ] Circuit breaker or bulkhead present on critical-path third-party calls
- [ ] `429` responses respect the `Retry-After` header and back off
- [ ] Integration failures logged with third-party error code and request ID
- [ ] Queue message enqueued via outbox pattern or inside the same DB transaction

## Common issues & anti-patterns

- **Webhook processed without signature check**: the handler trusts the event payload without verifying it came from the actual provider. Any HTTP client can forge a Stripe payment event and trigger order fulfillment.
- **Retry on all errors including 400**: a 400 Bad Request means the request is malformed — retrying will always fail and wastes quota. Only retry on 429, 500, 502, 503, 504, and network errors.
- **No timeout on third-party call in a request handler**: Stripe's API takes 30 seconds to respond (during an incident), your handler waits, your connection pool is exhausted in 10 seconds, and your entire service is down — for a problem in Stripe's data center.
- **Double processing without idempotency guard**: SQS delivers the same payment webhook twice (common), the consumer charges the customer twice, support tickets flood in.
- **Synchronous webhook processing that can time out**: a webhook handler that does database work, sends emails, and calls other APIs in sequence can easily exceed the provider's 10-30s response deadline, causing the provider to retry — triggering the same processing again.

## Required output
Report must include:
- **Third-party call inventory**: service, operation, path (critical/background), timeout configured
- **Retry configuration findings**: strategy, backoff, max count, non-retryable codes respected
- **Webhook signature validation status**: per-provider — validated / missing / misconfigured
- **Idempotency implementation status**: deduplication mechanism and transactional correctness
- **Circuit breaker status**: present / absent / misconfigured per critical dependency
- **Rate limit handling findings**: 429 backoff behavior
- **Queue producer delivery guarantee**: outbox / post-commit / fire-and-forget
- **Severity rating per finding**: critical / high / medium / low

## Safety
- Do not store or log webhook payloads that may contain PII or payment card data from third parties.
- Do not disable signature validation "temporarily" for debugging — use the provider's test mode or replay tools instead.
- Flag missing webhook signature validation as critical and surface it before completing the rest of the review.

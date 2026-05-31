---
name: error-handling-observability
description: Use when you need to review error handling, logging, metrics, tracing, and user-safe diagnostics.
---

# Error Handling & Observability

## Purpose
This skill reviews the observability posture of a backend service: whether errors are caught and propagated correctly, whether logs contain enough context to diagnose a failure in production without a debugger attached, whether metrics exist to detect anomalies before users report them, and whether distributed traces connect requests across service boundaries. It also checks that internal error details are never exposed to end users.

## When to use
- A production incident could not be diagnosed because logs were missing, truncated, or lacked context — preventing this from happening again.
- Adding structured logging to a service that currently uses unstructured `console.log` calls.
- Implementing distributed tracing (OpenTelemetry) across multiple services.
- Reviewing a new service before it goes to production to ensure it is observable from day one.
- A service silently drops errors in async code and the failures are only discovered through user complaints.

## When not to use
- The service is a CLI tool or short-lived script — structured logging and tracing are overkill; basic stderr and exit codes are sufficient.
- The goal is debugging a specific known error right now — use runtime-diagnostics for live triage.
- You only need to add a single log line — this skill is for systematic review of the observability layer, not one-off additions.

## Procedure

1. **Audit the logging framework and output format.** Confirm the service uses a structured logger (Winston, Pino, Bunyan for Node; structlog, loguru for Python; zap, slog for Go; Logback with JSON encoder for Java) that emits JSON. Unstructured `console.log("User created: " + userId)` cannot be reliably queried or alerted on in a log aggregator. Each log line must contain at minimum: `timestamp`, `level`, `message`, and the relevant context fields.

2. **Verify correlation ID (request ID) is propagated through every log line.** A single HTTP request should produce log lines from the handler, service layer, and DB layer — all sharing the same `requestId` or `traceId`. Check: the ID is generated at the edge (or extracted from the `X-Request-ID` / `traceparent` header), stored in an async context (`AsyncLocalStorage` in Node, `contextvars` in Python, context.Context in Go), and included in every logger call. Without this, correlating logs for a single failed request requires guessing from timestamps.

3. **Review error propagation — are errors surfacing or disappearing?** Search for patterns that swallow errors:
 - Empty `catch` blocks: `catch (e) { }` or `catch (e) { console.log(e) }` with no re-throw.
 - Fire-and-forget async calls: `someAsyncOperation()` called without `await` inside an `async` function — errors are lost.
 - `Promise.allSettled()` results not inspected: `const results = await Promise.allSettled([...]); results.forEach(...)` where rejected results are not logged or surfaced.
 - Background job error handler that only logs but does not retry, alert, or move to a dead-letter queue.

4. **Confirm error classification and HTTP status mapping.** The global error handler must distinguish: validation errors → 400, authentication failures → 401, authorization failures → 403, not found → 404, conflict → 409, rate limit → 429, internal errors → 500. A catch-all `res.status(500).json({ error: 'Internal Server Error' })` for validation errors is a UX failure. A handler that sends the raw stack trace to the client is a security failure.

5. **Check that internal error details never reach the client in production.** Search for: `res.json({ error: err.message })`, `res.json({ stack: err.stack })`, or raw DB error messages in response bodies. In production (`NODE_ENV === 'production'`), the response must contain only a user-safe message and a reference ID (e.g., `{ error: 'Something went wrong', requestId: 'abc-123' }`). The full error details go to logs, not to the client.

6. **Review metric instrumentation.** Check whether the following key metrics are emitted:
 - `http_request_duration_ms` (histogram) labeled by `method`, `route`, `status_code`.
 - `http_requests_total` (counter) labeled by `method`, `route`, `status_code`.
 - Error rate: `http_errors_total` labeled by `status_code` family (4xx, 5xx).
 - Per-integration error rate: `third_party_call_errors_total` labeled by `service`.
 - Queue consumer lag: if applicable, the number of unprocessed messages waiting.
 If no metrics library is present (Prometheus client, StatsD, OpenTelemetry SDK), this is a critical observability gap.

7. **Review distributed trace instrumentation.** If the service is part of a multi-service architecture: confirm it propagates the W3C `traceparent` header on all outbound HTTP calls, and extracts it from all inbound HTTP calls. Check that database calls, queue operations, and external HTTP calls are wrapped in spans. A trace that ends at the API gateway and has no visibility into what the backend did is nearly useless for production diagnosis.

8. **Verify alerting coverage for critical error conditions.** At minimum, alerts should fire on: sustained 5xx error rate above a threshold (e.g., > 1% of requests for 5 minutes), p99 latency exceeding SLA, dead-letter queue depth growing, and health check failures. If these alerts do not exist, document them as gaps.

9. **Check log level hygiene.** `DEBUG` lines that log full request/response bodies (including PII and tokens) must not be emitted in production. Confirm: log level is controlled by env var (`LOG_LEVEL=info` in production), and any `debug`-level calls that log sensitive data are behind a level guard. Also confirm `info` logs are not so verbose that they create a log flood — high-throughput routes should log at `debug` level with sampling.

## Checklist
- [ ] Structured JSON logger in use (not `console.log`) — emits `timestamp`, `level`, `message` on every line
- [ ] Correlation/request ID generated at the edge and included in every log line via async context
- [ ] No empty or swallowing `catch` blocks — all errors logged and propagated
- [ ] No fire-and-forget async calls in critical paths — all async operations are awaited
- [ ] `Promise.allSettled` results explicitly inspected for rejections
- [ ] Global error handler maps error types to correct HTTP status codes (400/401/403/404/409/500)
- [ ] Raw error messages, stack traces, and DB errors never appear in HTTP response bodies in production
- [ ] Error response body contains a `requestId` the user can reference in a support ticket
- [ ] Key HTTP metrics instrumented: request duration (histogram), total count, error count
- [ ] Distributed trace headers (`traceparent`) propagated on all outbound calls
- [ ] Background job / queue consumer failures land in a dead-letter queue with the error logged
- [ ] `DEBUG` log level disabled in production; log level controlled by env var
- [ ] Alerts defined for sustained 5xx rate, p99 latency, and DLQ depth

## Common issues & anti-patterns

- **Correlation ID only in the handler**: the requestId is logged on entry and exit of the HTTP handler, but the service layer and DB layer use a separate logger instance with no ID — making middle-layer errors undiagnosable in production.
- **`console.error(err)` instead of a structured log call**: this produces an unformatted multi-line string in the log aggregator that cannot be parsed, searched, or alerted on.
- **Generic 500 for all errors**: a validation error that returns 500 triggers error-rate alerts, pages on-call engineers, and looks like a production incident when it is a client mistake.
- **Stack traces in API responses**: exposes internal file paths, library versions, and code structure to potential attackers — and clutters mobile app logs with useless data.
- **Metric labels with unbounded cardinality**: using `userId` or full URL paths as metric labels creates millions of unique time series and kills the metrics backend. Always use route templates (`/api/orders/:id`), not actual values.

## Required output
Report must include:
- **Logging framework assessment**: structured vs. unstructured, fields present/missing
- **Correlation ID coverage**: propagated / missing / partial — with specific gaps
- **Error swallowing findings**: specific locations of empty catches, fire-and-forget calls, unhandled rejections
- **HTTP status mapping assessment**: which error types map to wrong codes
- **Client error exposure findings**: specific response body locations that leak internal details
- **Metric coverage**: which key metrics exist, which are missing
- **Trace propagation status**: inbound extraction and outbound injection confirmed / missing
- **Alert coverage**: existing alerts and documented gaps
- **Severity rating per finding**: critical / high / medium / low

## Safety
- Do not suggest disabling error logging to reduce log volume — fix the verbosity at the source or use sampling.
- Do not add `console.log(req.body)` for debugging and leave it in — it logs user credentials and PII on every request.
- When reviewing log output, redact any actual user data, tokens, or secrets before including examples in the report.

---
name: error-handling-observability
description: Use when you need to review error handling, logging, metrics, tracing, and user-safe diagnostics.
---

# Error Handling & Observability

## Purpose
Review the observability posture of a backend service: whether errors are caught and propagated correctly, whether logs carry enough context to diagnose a production failure with no debugger attached, whether metrics exist to detect anomalies before users report them, whether distributed traces connect a request across service boundaries, and whether internal error details ever leak to end users. The deliverable is a severity-rated findings list with concrete fixes — the goal is a service that is observable from day one, not after the first un-diagnosable incident.

## When to use
- A production incident could not be diagnosed because logs were missing, truncated, or contextless — and you want to prevent a repeat.
- Adding structured logging to a service that currently uses unstructured `console.log`.
- Implementing distributed tracing (OpenTelemetry) across multiple services.
- Reviewing a new service before production so it ships observable.
- A service silently drops errors in async code and failures only surface as user complaints.

## When not to use
- The service is a CLI tool or short-lived script — structured logging and tracing are overkill; stderr and exit codes suffice.
- The goal is debugging one known error right now — use runtime-diagnostics for live triage.
- You only need to add a single log line — this skill is for systematic review, not one-off additions.

## Procedure
1. **Audit the logging framework and format.** Confirm a structured logger (Pino/Winston/Bunyan, structlog/loguru, zap/slog, Logback JSON) emitting JSON with at least `timestamp`, `level`, `message`, and context fields. Unstructured `console.log("User " + id)` cannot be queried or alerted on.
2. **Verify a correlation/request ID flows through every log line.** One request should emit handler, service, and DB log lines sharing one `requestId`/`traceId`. Confirm the ID is generated at the edge (or read from `X-Request-ID`/`traceparent`), stored in async context (`AsyncLocalStorage`, `contextvars`, `context.Context`), and attached to every logger call.
3. **Review error propagation — surfacing or disappearing?** Flag empty catches (`catch (e) {}` / log-only with no re-throw), fire-and-forget async (missing `await`), uninspected `Promise.allSettled` rejections, and background-job handlers that only log without retry/alert/DLQ.
4. **Confirm error classification and HTTP status mapping.** The global handler must map validation→400, auth→401, forbidden→403, missing→404, conflict→409, rate-limit→429, internal→500. A catch-all 500 for validation errors is a UX failure; sending a raw stack trace is a security failure.
5. **Check internal details never reach the client in production.** Flag `res.json({ error: err.message })`, `{ stack: err.stack }`, or raw DB errors in responses. In production the body must be a user-safe message plus a reference ID; full detail goes to logs.
6. **Review metric instrumentation.** Confirm `http_request_duration_ms` (histogram by method/route/status), `http_requests_total` (counter), error rate by status family, per-integration error rate, and queue lag where applicable. No metrics library present is a critical gap.
7. **Review trace instrumentation.** In a multi-service architecture, confirm the W3C `traceparent` header is propagated outbound and extracted inbound, and that DB calls, queue ops, and external calls are wrapped in spans.
8. **Verify alerting coverage.** At minimum: sustained 5xx rate over threshold, p99 latency over SLA, growing dead-letter-queue depth, and health-check failures. Document any missing alert as a gap.
9. **Check log-level hygiene.** `DEBUG` lines logging full request/response bodies (PII, tokens) must not run in production; level is env-controlled (`LOG_LEVEL=info`), and high-throughput routes log at `debug` with sampling to avoid a flood.
10. **Verify the health endpoint reflects readiness.** Confirm `/health` (and any `/ready` probe) checks real dependencies (DB, cache) rather than returning 200 unconditionally, so the load balancer and alerts react to actual degradation.
11. **Check redaction at the logging boundary.** Confirm a serializer or redaction list strips `password`, `authorization`, tokens, and card data before any log line is written, so a future `log.info({ req })` cannot leak secrets.

## Concrete checks
- Structured JSON logger in use (not `console.log`); every line has `timestamp`, `level`, `message`.
- Correlation/request ID generated at the edge and present on every log line via async context.
- No empty or swallowing catch blocks; all errors logged and propagated.
- No fire-and-forget async in critical paths; all async operations awaited.
- `Promise.allSettled` results explicitly inspected for rejections.
- Global handler maps error types to correct status codes (400/401/403/404/409/429/500).
- Raw error messages, stack traces, and DB errors never appear in production response bodies.
- Error responses include a `requestId` the user can quote in a support ticket.
- Key HTTP metrics instrumented: request duration (histogram), total count, error count.
- `traceparent` propagated on all outbound calls; extracted on inbound.
- Background-job / consumer failures land in a DLQ with the error logged.
- `DEBUG` disabled in production; log level controlled by env var.
- Alerts defined for sustained 5xx rate, p99 latency, and DLQ depth.
- Metric label cardinality is bounded (route templates, status families) — no raw IDs, emails, or URLs as labels.
- The error object is logged as a structured field, not interpolated into a message string.
- Log severity is mapped to level deliberately (errors at `error`, query noise at `debug`).
- Trace spans cover the data and integration layers, not just the API edge.
- The health endpoint reflects real dependency status rather than returning 200 unconditionally.
- A single global error handler maps errors to status codes — not scattered ad-hoc `res.status(500)` calls.
- A redaction list at the logger boundary strips `password`, `authorization`, tokens, and card data before any line is written.

## Commands
```bash
# Unstructured logging that cannot be queried/alerted
rg -n "console\.(log|error|warn)\(" src/ | wc -l
rg -n "console\.(log|error)\(" src/ | head -20

# Swallowed errors and fire-and-forget async
rg -nU "catch\s*\([^)]*\)\s*\{\s*(\}|//|console\.log)" src/
rg -nU "allSettled\([\s\S]{0,200}" src/ | rg -v "status|reason"

# Internal detail leaking to the client
rg -n "err\.message|err\.stack|error\.stack|\.stack\b" src/ | rg "res\.|reply\.|json\("

# Correlation ID plumbing present?
rg -n "AsyncLocalStorage|contextvars|requestId|traceId|X-Request-Id|traceparent" src/

# Metrics + tracing libraries present?
rg -n "prom-client|statsd|@opentelemetry|histogram|Counter\(" src/ | head
rg -n "traceparent|propagation|startSpan|tracer\." src/ | head

# Log level controlled by env, not hardcoded debug
rg -n "LOG_LEVEL|level:\s*['\"](debug|trace)" src/
```
```bash
# High-cardinality metric labels (kills the metrics backend)
rg -nU "(labels|tags)\([\s\S]{0,80}(userId|email|id|url|path)\b" src/

# Bodies/headers being logged (PII + token leak)
rg -n "log.*(req\.body|req\.headers|request\.body|password|authorization)" -i src/

# Sensitive fields making it into responses
rg -n "res\.(json|send)\(" src/ | rg -i "password|token|secret|stack|hash"

# Is there a single global error handler, or scattered ad-hoc 500s?
rg -n "app\.use\(.*err|errorHandler|@Catch\(|exceptionHandler|setErrorHandler" src/
rg -n "res\.status\(500\)" src/ | wc -l        # many scattered 500s = no central mapping

# Redaction configured at the logger boundary?
rg -n "redact|censor|sanitize|paths:\s*\[|filterKeys" src/ | rg -i "password|authorization|token" \
  || echo "no logger redaction list found"

# Key HTTP metrics actually emitted (duration histogram, error counter)?
rg -n "http_request_duration|requestDuration|http_requests_total|observe\(|inc\(" src/ || echo "no HTTP metrics found"
```

## Correct vs incorrect patterns
```ts
// WRONG: swallows the error and leaks internals to the client
try { await charge(order); }
catch (e) { console.log(e); res.status(500).json({ error: e.message, stack: e.stack }); }

// RIGHT: structured log with context, user-safe response with a reference ID
try { await charge(order); }
catch (e) {
  log.error({ err: e, requestId: ctx.requestId, orderId: order.id }, 'charge failed');
  res.status(502).json({ error: 'Payment provider unavailable', requestId: ctx.requestId });
}
```

## Error class to HTTP status (the global handler's job)
| Error class | Status | Client body |
|-------------|--------|-------------|
| ValidationError | 400 | field-level messages |
| AuthenticationError | 401 | "authentication required" |
| AuthorizationError | 403 | "not permitted" |
| NotFoundError | 404 | "resource not found" |
| ConflictError | 409 | "already exists / version conflict" |
| RateLimitError | 429 | "slow down" + Retry-After |
| Unhandled / unknown | 500 | "something went wrong" + requestId |

## Common issues & anti-patterns
- **Correlation ID only in the handler.** The ID is logged on handler entry/exit but the service and DB layers use a separate logger with no ID, making middle-layer errors un-correlatable in production.
- **`console.error(err)` instead of a structured call.** Produces an unparseable multi-line string in the aggregator that cannot be searched or alerted on.
- **Generic 500 for everything.** A validation error returning 500 trips error-rate alerts and pages on-call for what is a client mistake.
- **Stack traces in API responses.** Leaks file paths, library versions, and code structure to attackers and clutters client logs.
- **Unbounded metric label cardinality.** Using `userId` or a full URL as a label creates millions of time series and kills the metrics backend. Use route templates (`/api/orders/:id`), never raw values.
- **Logging the whole error object as a string.** `log.info(\`failed: ${err}\`)` discards the stack and structure. Pass the error as a field (`{ err }`) so the logger serializes it properly.
- **One log level for everything.** Logging every DB query at `info` floods the aggregator and hides real signals; logging errors at `info` means alerts never fire. Map severity to level deliberately.
- **Trace that stops at the gateway.** Spans exist for the API edge but DB calls and outbound HTTP have none, so a slow request shows a gap with no detail. Instrument the data and integration layers.
- **Alerting on raw error count.** Paging on "any 5xx" pages on a single transient blip. Alert on a sustained rate over a window instead.
- **Health check that never fails.** A `/health` that returns 200 unconditionally tells the load balancer the instance is fine while the DB is down. Reflect real dependencies.

## Required output
Report must include: **logging framework assessment** (structured vs unstructured, fields present/missing); **correlation-ID coverage** (propagated / partial / missing with gaps); **error-swallowing findings** (empty catches, fire-and-forget, unhandled rejections by location); **HTTP status-mapping assessment** (types mapped to wrong codes); **client error-exposure findings** (response bodies leaking internals); **metric coverage** (present vs missing); **trace propagation status** (inbound extraction + outbound injection); **alert coverage** (existing + gaps); and a **severity rating per finding**.

## Safety
- Do not suggest disabling error logging to cut log volume — fix verbosity at the source or use sampling.
- Do not add `console.log(req.body)` for debugging and leave it in — it logs credentials and PII on every request.
- When quoting log output in the report, redact any actual user data, tokens, or secrets first.
- Recommend strengthening error classification, never collapsing distinct errors into a single opaque 500.

## Completion criteria
Done means the logging framework, correlation-ID coverage, error-propagation paths, status mapping, client-exposure surface, metrics, traces, and alerts are each assessed from evidence, every gap has a file:line (or "absent") and a severity, and no sensitive value appears unredacted in the report.

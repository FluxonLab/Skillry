---
name: observability-otel-review
description: Use when you need to review OpenTelemetry, logs, metrics, traces, dashboards, and operational diagnostics.
---

# Observability & OpenTelemetry Review

## Purpose
Review OpenTelemetry (OTel) instrumentation, signal pipeline configuration (traces, metrics, logs), exporter setup, context propagation, sampling strategy, cardinality management, dashboard definitions, and alerting rules for production-grade observability.

## When to use
- Reviewing OTel SDK initialization and instrumentation in any language (Go, Python, Node.js, Java).
- Auditing trace context propagation across service boundaries (HTTP headers, gRPC metadata, message queues).
- Evaluating collector configuration (`otelcol-config.yaml`): receivers, processors, exporters, pipelines.
- Reviewing sampling strategy (head-based, tail-based, adaptive).
- Auditing metric cardinality and label design.
- Reviewing Grafana/Prometheus dashboards or alerting rules (YAML, Terraform, Jsonnet/Grafonnet).
- Assessing log schema and structured logging consistency.

## When not to use
- APM-only review using a proprietary agent (Datadog APM, New Relic, Dynatrace) with no OTel layer — the specific agent configs differ; note and scope separately.
- Database query performance tuning with no observability instrumentation involved.
- Alert triage or incident response — this skill is for code/config review, not live ops.

## Procedure

### 1. OTel SDK initialization
- Verify the SDK is initialized **before** any other application code runs — late initialization misses early spans and metric registrations.
- `TracerProvider`, `MeterProvider`, and `LoggerProvider` must be configured with the correct resource attributes: `service.name`, `service.version`, `deployment.environment`.
- Resource attributes set correctly at startup are inherited by all telemetry from that process — do not rely on setting them per-span.
- Confirm `sdk.ForceFlush()` (or equivalent) is called on graceful shutdown so the last batch of telemetry is exported before the process exits.
- Shutdown timeout: set an explicit deadline (e.g., 5 s) on flush — uncapped flush can stall pod termination in Kubernetes.

### 2. Trace instrumentation
- Every cross-service HTTP call must inject the `traceparent` header (W3C Trace Context) or `X-B3-*` headers (Zipkin) — depends on the propagator configured.
- Incoming requests must extract the trace context from headers; if missing, a new root span is created.
- Span naming: use low-cardinality names — `GET /orders/{id}` not `GET /orders/12345`. Template the path, not the actual value.
- Span status: set `SpanStatus.ERROR` with a description on exceptions; do not leave spans with status `UNSET` after an error.
- Span attributes: add business-relevant attributes (`order.id`, `user.tier`) as span attributes, not as part of the span name.
- Avoid creating spans inside tight loops (per-item spans for a 10,000-item batch) — use a single span with a `batch.size` attribute instead.
- Async/concurrent operations: context must be explicitly propagated to goroutines, threads, or async tasks — do not rely on implicit thread-local context.

### 3. Context propagation across service boundaries
- HTTP: verify `traceparent` and `tracestate` headers are forwarded by all reverse proxies, API gateways, and load balancers — many strip unknown headers by default.
- Message queues (Kafka, RabbitMQ, SQS): OTel messaging semantic conventions define `messaging.message_id`, `messaging.destination`, etc. Trace context must be injected into message headers and extracted by the consumer.
- gRPC: use the `otelgrpc` interceptor on both client and server — verify it is registered, not just imported.
- Baggage: if `W3C Baggage` is used for cross-service metadata (e.g., `user.tier`), verify baggage is not used for high-cardinality values (it is forwarded to all downstream services and can amplify cardinality).

### 4. Metrics design and cardinality
- **Cardinality**: the number of unique label combinations determines the memory footprint. A label with unbounded values (`user_id`, `order_id`, `url`) causes a cardinality explosion that can OOM the Prometheus instance.
- Safe labels: `status_code`, `method`, `service`, `environment`, `region` (bounded, low-cardinality).
- Unsafe labels: `user_id`, `session_id`, `order_id`, `ip_address` — use histogram buckets or counters, not labels.
- Metric naming: follow Prometheus conventions — `library_unit_name_total` for counters, `_seconds` for durations, `_bytes` for sizes.
- Histogram buckets: choose buckets that match the actual distribution. Default OTel histogram buckets are too coarse for sub-millisecond operations; too fine for multi-second operations — configure explicitly.
- Up-Down counters: use for values that can decrease (queue depth, active connections). Regular counters must be monotonically increasing.

### 5. Log schema and structured logging
- Logs must be structured (JSON or key=value) — free-text logs are unsearchable and expensive to parse.
- Mandatory fields: `timestamp` (RFC3339/ISO8601), `level` (INFO/WARN/ERROR), `message`, `service.name`, `trace_id`, `span_id`.
- `trace_id` and `span_id` in log records enable log-trace correlation in backends (Grafana, Jaeger, Honeycomb).
- Do not log PII: email addresses, user passwords, full credit card numbers, access tokens, or private keys must be redacted before logging.
- Log levels must be correct: DEBUG for developer diagnostics (disabled in production), INFO for normal operation events, WARN for recoverable anomalies, ERROR for failures requiring attention.
- Avoid logging at ERROR for every 404 or validation failure — these are expected user errors, not system errors.

### 6. Collector configuration (otelcol)
- Pipelines must define: `receivers` (OTLP, Prometheus, Jaeger), `processors` (batch, memory_limiter, resource), `exporters` (OTLP, Jaeger, Prometheus).
- `memory_limiter` processor must be first in every pipeline — it prevents OOM crashes under load. Configure `limit_mib` and `spike_limit_mib`.
- `batch` processor: configure `timeout` (1–5 s) and `send_batch_size` (1,000–8,192) for throughput vs latency trade-off.
- `resourcedetection` processor: automatically adds cloud/host resource attributes (AWS region, Kubernetes node name) — enable in cloud deployments.
- Sensitive data in spans/logs must be filtered by a `transform` or `filter` processor at the collector — do not rely on all services redacting independently.
- Exporter retry: configure `retry_on_failure` with exponential back-off; without it, transient backend outages cause permanent data loss.

### 7. Sampling strategy
- Head-based (at trace root): `TraceIdRatioBased` sampler. Use for high-volume, low-value traffic (health checks, static assets). Keep rate ≥ 1% to preserve statistical validity.
- Always-on for errors: use `ParentBased` + a custom sampler that forces sampling for spans with `SpanStatus.ERROR` regardless of head decision.
- Tail-based (at collector): `tailsamplingprocessor` — sample after seeing the full trace. Enables keeping 100% of slow or error traces while dropping fast healthy traces. Requires stateful collector with consistent routing.
- Health check endpoints: always drop `/health`, `/ready`, `/metrics` endpoints from tracing — they generate noise and inflate trace volume.
- Do not sample at 0% in production — you will have no traces when you need them most.

### 8. Dashboards
- Every service must have a USE dashboard: **Utilization, Saturation, Errors** (for resources like CPU, memory, connections).
- Every API must have a RED dashboard: **Rate, Errors, Duration** (request rate, error rate, p50/p95/p99 latency).
- Dashboard variables: use template variables for `environment`, `service`, `region` — dashboards should not need duplication per environment.
- Avoid the instant-value anti-pattern: show rates (`rate(counter[5m])`) and percentiles (`histogram_quantile(0.99,...)`), not raw counter values.
- p99 latency is more actionable than average for user-facing services — include p95 and p99 on all latency panels.

### 9. Alerting rules
- Alerts must be actionable: every alert must have a runbook URL in its annotations.
- Alert on symptoms, not causes: alert on error rate > 1% (symptom) rather than CPU > 80% (cause that may or may not affect users).
- Alert fatigue: do not alert on metrics that are frequently noisy without being actionable. Use `for: 5m` to avoid firing on transient spikes.
- SLO-based alerting: multi-window, multi-burn-rate alerts (Google SRE Workbook method) are more reliable than threshold alerts for user-facing error budgets.
- Dead man's switch: alert if the service stops emitting metrics entirely (`absent()` or `up == 0`).

## Checklist

SDK initialization:
- [ ] `TracerProvider`, `MeterProvider`, `LoggerProvider` initialized before app code.
- [ ] `service.name`, `service.version`, `deployment.environment` set as resource attributes.
- [ ] `ForceFlush` + graceful shutdown with timeout configured.

Traces:
- [ ] `traceparent` header injected on all outgoing HTTP calls.
- [ ] `traceparent` extracted from all incoming HTTP requests.
- [ ] Span names are low-cardinality (no IDs in span name).
- [ ] `SpanStatus.ERROR` set on exceptions with description.
- [ ] Context propagated explicitly to goroutines/threads/async tasks.

Metrics:
- [ ] No unbounded label values (no user_id, order_id, URL in labels).
- [ ] Metric names follow `library_unit_name_total` convention.
- [ ] Histogram buckets configured explicitly.
- [ ] `memory_limiter` processor first in collector pipelines.

Logs:
- [ ] Structured JSON output with `trace_id` and `span_id`.
- [ ] No PII in log payloads.
- [ ] Log levels used correctly (no ERROR on every 404).

Sampling:
- [ ] Sampling rate ≥ 1% in production.
- [ ] Error spans always sampled.
- [ ] Health check endpoints excluded from tracing.

Alerting:
- [ ] Every alert has a runbook URL.
- [ ] Alerts use `for: 5m` or similar to suppress transient spikes.
- [ ] Dead man's switch alert for metric absence.

## Common issues & anti-patterns

- **OTel SDK initialized after app code**: spans from early startup (DB connection, config load) are lost. Initialize the provider first.
- **High-cardinality metric label**: `http_requests_total{user_id="12345"}` — each unique user generates a new time series. A 1M-user service creates 1M time series for a single metric, OOMing Prometheus.
- **Span name with request ID**: `GET /orders/a1b2c3d4` — every unique order ID creates a unique span name. Backends cannot aggregate across these. Use `GET /orders/{id}`.
- **No `ForceFlush` on shutdown**: the last 30 s of telemetry before a deploy is lost, hiding errors that occur during graceful shutdown.
- **Missing `traceparent` forwarding in API gateway**: NGINX/Kong/AWS API Gateway strips `traceparent` by default — traces are broken at every gateway hop.
- **Sampling at 100% on high-traffic services**: 10,000 req/s × 100% sampling = 10,000 spans/s exported. This saturates the collector and exporter at significant cost.
- **Free-text log messages**: `log.info("User 12345 paid $99.99")` — unstructured, contains PII, and cannot be queried reliably. Use `log.info("payment.completed", amount=99.99, currency="USD")`.
- **Alert without runbook**: engineers get paged at 3 AM with no guidance. Every alert must have a `runbook_url` annotation.

## Required output

Return a structured report with:
- **Summary**: pass / needs fixes / blocked (data loss risk, cardinality bomb, or PII in telemetry).
- **Signal coverage**: traces — services instrumented vs not; metrics — USE/RED coverage per service; logs — structured vs unstructured.
- **Cardinality audit**: labels with potential unbounded cardinality identified.
- **Context propagation map**: services where `traceparent` propagation is confirmed vs broken.
- **Sampling assessment**: strategy used, rates, error/slow trace handling.
- **Findings table**: severity (critical / high / medium / low / info), signal type (traces/metrics/logs/alerting), file + line, description, remediation.
- **Next handoff**: validate end-to-end trace in staging with a distributed test request; run Prometheus cardinality analysis (`topk(10, count by (__name__)({}) )`).

## Safety

- Do not modify collector configuration on a live production cluster during review.
- Do not access or export raw trace/log data that may contain PII or secrets.
- If credentials, tokens, or PII are found in span attributes or log payloads, flag as critical and recommend immediate scrubbing via a collector `transform` processor.
- Do not disable sampling or set it to 100% on high-traffic production services — this can cause cascading collector overload.

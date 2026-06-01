---
name: backend-latency-profiling
description: Use when you need to profile backend request latency — measuring p50/p95/p99 (not averages), capturing flame graphs, finding slow code paths with py-spy/0x/pprof, and diagnosing connection-pool exhaustion and async/event-loop bottlenecks.
---

# Backend Latency Profiling

## Purpose

Find and explain why backend requests are slow, using tail-latency percentiles and CPU/off-CPU profiling rather than guesswork. Averages lie; this skill anchors on p50/p95/p99 and on flame graphs that show where wall-clock and CPU time actually go. It covers sampling profilers (py-spy, 0x, pprof), connection-pool and thread-pool exhaustion, and async/event-loop blocking. The output is a profiled hot path with a measured before/after, not a vague "optimize the database" note.

## When to use

- p95 or p99 latency is high while p50 looks fine (a tail-latency problem).
- A specific endpoint is slow and you need to know where the time goes (CPU, I/O wait, lock contention, GC).
- Throughput collapses under load and you suspect connection-pool or thread-pool exhaustion.
- p99 is spiky and intermittent and you need to tell GC/host pauses apart from genuinely slow code.
- An async service (Node, asyncio, Go) stalls and you suspect the event loop is blocked by sync work.
- A latency regression appeared after a deploy and you need a flame-graph diff.

## When not to use

- The bottleneck is purely a single slow SQL query already identified by the database's slow-query log — go straight to query optimization.
- The problem is frontend render time, not server response time — use the frontend performance budget skill.
- The slowdown is a one-off caused by a known batch job or deploy that has already finished, not a steady-state regression.
- You have no way to reproduce load or attach a profiler in any environment (fix observability first; you cannot profile what you cannot run).

## Procedure

1. **Quantify the tail, not the mean.** Pull latency as a distribution and compute p50/p95/p99 per endpoint. A 50 ms average with a 4 s p99 is a tail problem affecting real users; the average alone hides it. Anchor targets to the SLO percentile (usually p95 or p99), because that is what users at the edge feel.
2. **Reproduce under representative load.** Use a load generator at realistic concurrency. Tail latency only appears under contention; a single curl will not surface pool exhaustion or queueing. Warm the service first so JIT/cache effects do not pollute the first samples.
3. **Attach a sampling profiler and capture a flame graph.** Sampling profilers (py-spy, 0x, pprof, async-profiler) add low overhead and can often attach to a running process. Capture both on-CPU and, where supported, off-CPU (waiting) time — off-CPU is where I/O and lock waits hide.
4. **Read the flame graph top-down for width.** Width = time. The widest frames are where time is spent. Distinguish CPU-bound (your code is wide) from I/O-bound (you see wait/poll frames) from lock contention (futex/mutex frames). Ignore stack height; depth is structure, not cost.
5. **Check pools and queues.** Inspect database connection-pool size vs. concurrency, HTTP client pool limits, and thread/worker counts. Exhaustion shows as requests queueing for a connection while CPU is idle — a tell-tale flat-CPU/high-latency signature. Size the pool to the dependency's capacity, not just request concurrency.
6. **Find event-loop / async blocking.** In async runtimes, look for synchronous CPU work, blocking I/O, or large JSON (de)serialization on the loop. A single blocking call stalls every concurrent request sharing that loop. Move it to a worker pool, stream it, or make it non-blocking.
7. **Trace the dependency chain.** A slow endpoint is often slow because one downstream call (DB, cache, third-party) is slow under load. Use distributed tracing or per-span timing to find which hop owns the latency before optimizing your own code.
8. **Separate pauses from work.** A spiky p99 can be GC pauses, stop-the-world compaction, or a noisy neighbor rather than slow code. Correlate the latency timeline with GC logs and host CPU steal; if the tail aligns with pauses, tune the collector or isolate the workload instead of rewriting the handler.
9. **Fix one hot path, then re-profile.** Apply a single change, re-run the same load, and compare percentiles and flame graphs. Keep the before/after artifacts so the improvement is provable and reviewable.

## Concrete checks

- [ ] Latency is reported as p50/p95/p99 per endpoint, not as an average.
- [ ] Measurements were taken under representative concurrent load, not a single request.
- [ ] A flame graph (or equivalent profile) was captured and the widest frame identified.
- [ ] The bottleneck is classified: CPU-bound, I/O-wait, lock contention, GC, or queueing.
- [ ] Connection-pool max size is compared against peak concurrency; no silent queueing for connections.
- [ ] No synchronous/blocking call runs on an async event loop's main thread.
- [ ] Timeouts and retries are bounded so a slow dependency cannot pile up unbounded latency.
- [ ] Every outbound dependency call has an explicit timeout (no unbounded waits holding workers).
- [ ] N+1 query patterns and per-request serialization costs are ruled in or out.
- [ ] The slow downstream hop (DB/cache/third-party) is identified via tracing or per-span timing before local code is tuned.
- [ ] The service was warmed before measurement so cold-start/JIT effects do not skew the baseline.
- [ ] The p99 tail is checked against GC-pause and host CPU-steal timelines to rule out pauses vs. slow code.
- [ ] A before/after percentile comparison exists for any applied fix.

## Commands or Templates

```bash
# --- Python: py-spy, attach to a running process, no code change ---
pip install py-spy
# Live top-style view of where CPU time goes
py-spy top --pid <PID>
# Record a flame graph for 30 seconds (SVG)
py-spy record --pid <PID> --duration 30 --output profile.svg
# Include time spent waiting (off-CPU), useful for I/O-bound services
py-spy record --pid <PID> --idle --duration 30 --output profile-idle.svg
```

```bash
# --- Node.js: 0x flame graph and clinic for event-loop diagnosis ---
npx 0x -- node server.js          # generates an interactive flame graph
npx clinic doctor -- node server.js   # flags event-loop blocking & GC
npx clinic flame -- node server.js    # CPU flame graph

# --- Go: pprof CPU profile (with net/http/pprof imported) ---
go tool pprof -http=:8081 http://localhost:6060/debug/pprof/profile?seconds=30
```

```bash
# --- Drive representative load to surface the tail (any HTTP service) ---
# hey: 200 concurrent, 20k requests
npx hey -n 20000 -c 200 https://example.com/api/endpoint
# wrk with a latency distribution
wrk -t4 -c200 -d30s --latency https://example.com/api/endpoint
# vegeta with explicit percentile report
echo "GET https://example.com/api/endpoint" | \
  vegeta attack -duration=30s -rate=300 | vegeta report -type='hdrplot'
```

```sql
-- Postgres: per-statement tail latency from pg_stat_statements
SELECT substr(query,1,80) AS query,
       calls,
       round(mean_exec_time::numeric,2)   AS mean_ms,
       round((max_exec_time)::numeric,2)  AS max_ms,
       round(total_exec_time::numeric,2)  AS total_ms
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 15;
```

```bash
# --- Compute true percentiles from a latency log (one ms value per line) ---
# Avoids the "average lies" trap by sorting and indexing the distribution.
sort -n latencies_ms.txt | awk '
  { v[NR]=$1 }
  END {
    function pct(p){ return v[int((p/100.0)*NR + 0.5)] }
    printf "count=%d  p50=%d  p95=%d  p99=%d  max=%d\n", NR, pct(50), pct(95), pct(99), v[NR]
  }'

# --- Java/JVM: low-overhead sampling flame graph with async-profiler ---
# -e wall captures off-CPU (I/O/lock) waits too, not just on-CPU time.
asprof -d 30 -e wall -f flame.html <PID>
```

## Common issues & anti-patterns

- **Optimizing the average.** Tuning p50 while p99 stays at seconds leaves the worst user experiences untouched; SLOs live at the tail.
- **Profiling a single request.** Pool exhaustion, queueing, and lock contention only appear under concurrency; profile under load.
- **Reading a flame graph for height instead of width.** Stack depth is not cost; frame width (time) is.
- **Undersized connection pool.** A pool smaller than peak concurrency turns into a hidden serialization point; CPU sits idle while requests wait.
- **Oversized pool.** Too many connections can overwhelm the database; size to the database's capacity, not to request concurrency alone.
- **Blocking the event loop.** A synchronous hash, regex, or large `JSON.parse` on the async loop stalls every concurrent request.
- **Unbounded retries.** Retrying a slow dependency without a budget multiplies tail latency and can cause a retry storm.
- **No timeout on a downstream call.** A hung dependency with no timeout ties up a worker/connection indefinitely, turning one slow hop into total saturation.
- **Cold-start samples in the baseline.** Measuring before the JIT warms, caches fill, and pools open reports artificially high latency that does not reflect steady state.
- **Synchronous logging on the hot path.** Blocking, unbuffered logging (or DNS lookups) inside request handling adds latency that the flame graph will show as wide I/O frames.
- **No before/after.** Claiming a fix worked without re-profiling under the same load is unverified.

## Required output

Produce a report containing:
1. **Latency table** — p50/p95/p99 per affected endpoint, baseline values, and the SLO if one exists.
2. **Load context** — the concurrency/rate used to reproduce, and the tool/command.
3. **Flame-graph finding** — the widest frame(s), the path through the code, and the bottleneck classification (CPU / I/O / lock / GC / queue).
4. **Pool & loop status** — pool sizes vs. concurrency; any blocking on the async loop.
5. **Fix + verification** — the change applied and a before/after percentile and flame-graph comparison.
6. **Pause vs. work** — whether the tail is dominated by GC/host pauses or by actual code execution, with the supporting correlation.
7. **Next safe action** — the next hottest path or the safest config change (e.g., pool sizing) to try.

## Safety

- Sampling profilers are low-overhead but not free; prefer staging, and on production attach for a bounded duration with a teammate aware.
- Do not run load generators against production; use staging or a load environment to avoid a self-inflicted outage.
- Never log request bodies or headers that may contain secrets or PII while profiling.
- Bound any profiling capture with `--duration`/`seconds=` so it cannot run away.
- Do not change connection-pool or timeout settings on production without approval and a rollback plan; pool changes can cascade.
- Remove or gate debug profiling endpoints (e.g., `/debug/pprof`) so they are not publicly exposed.
- Store profiling artifacts (flame graphs, traces) outside the repo and outside any public report; they can embed file paths, hostnames, and query fragments.
- Coordinate load tests with on-call and rate-limit them; an aggressive run against shared staging can disrupt other teams.

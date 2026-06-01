---
name: startup-health-readiness
description: Use when you need to add or verify readiness gates, health checks, and startup sequencing.
---

# Startup Health Readiness

## Purpose
This skill ensures that a service does not accept traffic or report itself healthy until all its
dependencies are actually ready — database connections established, migrations run, caches warm,
external clients initialized. It covers implementing and verifying `/health`, `/ready`, and `/live`
endpoints, dependency wait loops, graceful startup sequencing, and Kubernetes/Docker probe
configuration. A service that lies about its readiness causes cascading 500s; a service that never
marks itself ready blocks traffic unnecessarily. Both are failures this skill prevents.

## When to use
- Adding a new service that will run in Kubernetes and needs `readinessProbe` / `livenessProbe` configuration.
- A service is being marked healthy by a load balancer before its database pool is initialized, causing 500s on first requests.
- A Docker Compose `depends_on` is not sufficient because the dependency container starts but is not yet accepting connections.
- You need to add a `/health` endpoint that distinguishes "process alive" from "ready to serve traffic."
- A service crashes on startup when a downstream dependency (Redis, Postgres, Stripe) is temporarily unavailable — it should retry instead.
- A deployment causes a rolling update with brief request errors because pods receive traffic before their DB pool is ready.

## When not to use
- The service is a CLI tool or batch job — health probes are for long-running servers.
- The service already has tested, working health endpoints and you just need to debug a transient issue — use `runtime-diagnostics` instead.
- You are wiring up health checks in a managed platform (Render, Railway) that injects its own health check mechanism — read that platform's docs first.

## Procedure

1. **Audit the existing startup sequence.** Read the main entry point file and identify the exact
   order of: config load, database pool creation, migration execution, external client
   initialization, cache warm-up, and the moment `server.listen()` / `app.run()` is called. Note
   any step that can fail silently or take variable time. Draw the sequence as a numbered list —
   ambiguous ordering here is the root cause of most flapping readiness probes.

2. **Design the three-endpoint contract (or two, if liveness/readiness overlap).** Define clearly:
   - `GET /live` (liveness): returns 200 if the process is not deadlocked and the event loop is
     running. Must never query external systems. Returns 503 if the app is in a shutdown sequence.
   - `GET /ready` (readiness): returns 200 only when all dependencies are reachable and the server
     is ready to handle real requests. Returns 503 otherwise. Kubernetes stops sending traffic when
     this returns non-200.
   - `GET /health` (optional combined): returns a structured JSON body with per-dependency status
     for human debugging — safe to expose internally but never to the public internet.

3. **Implement dependency wait loops before `server.listen()`.** For each external dependency, add
   a retry loop with exponential backoff. Cap the total wait time — do not retry indefinitely; let
   the orchestrator restart the pod. Example pattern for any connection-type dependency:
   ```js
   async function waitFor(probe, name, retries = 10, baseMs = 500) {
     for (let i = 0; i < retries; i++) {
       try { await probe(); return; }
       catch (e) {
         if (i === retries - 1) throw new Error(`${name} not ready after ${retries} attempts`);
         await new Promise(r => setTimeout(r, baseMs * 2 ** i));
       }
     }
   }
   // Usage before server.listen():
   await waitFor(() => pool.query('SELECT 1'), 'postgres');
   await waitFor(() => redis.ping(), 'redis');
   ```

4. **Run migrations inside the startup sequence with a locking strategy.** If migrations run inside
   the app: use a DB advisory lock so only one instance migrates at a time:
   ```sql
   SELECT pg_try_advisory_lock(12345);
   ```
   If migrations run as a separate init container or pre-deploy hook, confirm the app checks that
   migrations are at the expected schema version before marking itself ready. Never skip the version
   check; a schema mismatch between code and DB causes silent data corruption, not just errors.

5. **Implement readiness as a real probe, not a stub.** A `/ready` endpoint that always returns
   200 defeats the purpose. Execute a lightweight query against each dependency within a 1-2 second
   timeout so a slow dependency does not cause the health check itself to hang:
   - Postgres: `SELECT 1`
   - Redis: `PING`
   - Elasticsearch: `GET /_cluster/health?wait_for_status=yellow&timeout=1s`
   - RabbitMQ / AMQP: open and close a channel
   - External HTTP API: `GET /health` with a 1500ms abort controller

6. **Return a structured JSON body from `/health` and `/ready`.** Include each dependency name,
   its status (`ok` or `unavailable`), and latency. Never include stack traces or internal query
   text in the response body — those leak schema details and query structure. Example response:
   ```json
   {
     "status": "degraded",
     "uptime": 42,
     "checks": {
       "postgres": { "status": "ok", "latencyMs": 3 },
       "redis":    { "status": "unavailable", "latencyMs": null }
     }
   }
   ```
   Return HTTP 503 when `status` is not `"ok"`, so load balancers act on the status code, not the body.

7. **Register a graceful shutdown handler.** On `SIGTERM`: stop accepting new requests, allow
   in-flight requests to finish (max 30s), then close the DB pool and exit.
   ```js
   process.on('SIGTERM', async () => {
     server.close(async () => {
       await pool.end();
       await redisClient.quit();
       process.exit(0);
     });
     setTimeout(() => process.exit(1), 30_000); // forced exit if drain stalls
   });
   ```
   Kubernetes sends SIGTERM and then SIGKILL after `terminationGracePeriodSeconds`. Ensure your
   grace period budget is shorter than that value; default `terminationGracePeriodSeconds` is 30s.

8. **Configure probe timings in Kubernetes manifests.** Recommended starting values for a service
   whose worst-case startup (including migrations) is under 60 seconds:
   ```yaml
   livenessProbe:
     httpGet: { path: /live, port: 3000 }
     initialDelaySeconds: 10
     periodSeconds: 15
     failureThreshold: 3
     timeoutSeconds: 5
   readinessProbe:
     httpGet: { path: /ready, port: 3000 }
     initialDelaySeconds: 5
     periodSeconds: 5
     failureThreshold: 6
     timeoutSeconds: 3
   ```
   `initialDelaySeconds` must be longer than the worst-case startup time. `failureThreshold * periodSeconds`
   must give enough window to survive a transient dependency restart (e.g. 30 seconds of Redis downtime).

9. **Test the failure modes explicitly.** Simulate dependency unavailability: start the app with
   `DATABASE_URL` pointing to a non-existent host and confirm it retries, logs clearly at WARN or
   ERROR level, and returns 503 from `/ready`. Then restore the correct URL and confirm the app
   transitions to ready without a restart. This test must be run in CI, not only manually.

## Concrete checks
- `/live` endpoint returns 200 without querying external systems.
- `/ready` endpoint performs real lightweight queries against each dependency (SELECT 1, PING, etc.).
- `/ready` returns HTTP 503 with a structured JSON body describing which dependency failed.
- Startup sequence waits for all dependencies before calling `server.listen()` or equivalent.
- Retry loop uses exponential backoff and has a maximum retry count — no infinite loops.
- Migration strategy is documented: in-app with advisory lock, or separate init container with version check.
- `SIGTERM` handler drains in-flight requests and closes all connections before `process.exit()`.
- Kubernetes `livenessProbe.initialDelaySeconds` exceeds worst-case startup time including migrations.
- `readinessProbe.failureThreshold * periodSeconds` covers the expected transient recovery window.
- Health response body contains dependency names and statuses but no stack traces or query text.
- `/ready` and `/live` have timeout budgets on their own dependency probes (1-2s max per check).
- Failure mode tested: app with broken dependency returns 503, not 500 or 200.
- HTTP status code (not body content) is what the load balancer or probe uses to make routing decisions.

## Commands
```bash
# Smoke-test readiness and liveness endpoints locally
curl -fsS -o /dev/null -w "status=%{http_code} time=%{time_total}s\n" http://localhost:3000/live
curl -fsS -o /dev/null -w "status=%{http_code} time=%{time_total}s\n" http://localhost:3000/ready
curl -s http://localhost:3000/health | python3 -m json.tool   # pretty-print the JSON body

# Simulate dependency failure: point DATABASE_URL at a non-existent host
DATABASE_URL=postgres://user:pass@doesnotexist:5432/db npm run start 2>&1 | head -30
# Expected: retry log lines, no crash loop, /ready returns 503

# Confirm the /ready route returns 503 when a dep is down
curl -s -w "\nHTTP %{http_code}\n" http://localhost:3000/ready

# Verify SIGTERM is handled: send SIGTERM and confirm graceful drain
kill -SIGTERM $(lsof -ti :3000)
# The process should log "shutdown signal received" and exit 0, not 1

# Kubernetes: describe the pod to see probe failure events
kubectl describe pod <pod-name> -n <namespace> | grep -A 10 "Liveness\|Readiness\|Events"

# Kubernetes: watch rolling update readiness transitions
kubectl rollout status deployment/<name> -n <namespace> --timeout=120s

# Check current probe config on a live deployment
kubectl get deployment <name> -n <namespace> -o jsonpath='{.spec.template.spec.containers[0].readinessProbe}' | python3 -m json.tool

# Docker Compose: healthcheck that respects actual readiness
# In docker-compose.yml:
#   healthcheck:
#     test: ["CMD", "curl", "-fsS", "http://localhost:3000/ready"]
#     interval: 5s
#     timeout: 3s
#     retries: 6
#     start_period: 10s

# Postgres: test advisory lock for migration serialization
psql "$DATABASE_URL" -c "SELECT pg_try_advisory_lock(12345), pg_advisory_unlock(12345);"

# Load-test the health endpoint to confirm it does not degrade under probe frequency
# (probes fire every 5s; this simulates 12 simultaneous probes)
for i in $(seq 1 12); do
  curl -fsS http://localhost:3000/ready &
done
wait
```

## Common issues & anti-patterns

- **Health endpoint that always returns 200.** Many codebases have a `/health` route added as an
  afterthought that does `res.json({ status: 'ok' })` regardless of actual dependency state — this
  is a false positive that defeats load balancer routing and delays incident detection.
- **Migration running after `listen()`.** The server accepts requests while migrations are in
  progress, causing schema mismatch errors on the first few requests after deploy.
- **Liveness probe depending on database.** If the database is slow, the liveness probe times out,
  Kubernetes restarts the pod, and the pod cannot recover on its own — use liveness only for
  process-level health (event loop alive, not deadlocked).
- **No retry on startup.** The app throws on the first connection failure and exits — in a
  Kubernetes environment, the scheduler will restart it, but this creates noisy CrashLoopBackOff
  cycles that delay readiness by minutes.
- **Grace period shorter than in-flight request timeout.** Long-running requests (file uploads,
  report generation) are killed mid-flight because `terminationGracePeriodSeconds` is set to the
  default 30s but requests can take 60s.
- **`initialDelaySeconds` set too low.** The pod starts getting probed before it has had time to
  establish its DB pool, causing a brief "unavailable" window that triggers unnecessary restarts.
- **Stack trace in the response body.** Returning the raw error from a failed DB query in the
  `/ready` body leaks internal schema details and query structure to anyone who can call the endpoint.
- **Unbounded probe query.** A `SELECT 1` with no statement timeout can block for minutes if the
  DB is under heavy lock contention, hanging the health endpoint and causing a cascade of probe
  timeouts.

## Required output
Report must include:
- **Startup sequence audit:** ordered list of initialization steps and which ones can fail or block indefinitely.
- **Endpoint implementation:** code or pseudocode for `/live`, `/ready`, and `/health` with per-dependency probe logic.
- **Retry strategy:** backoff configuration (base delay, multiplier, max retries) for each external dependency.
- **Migration strategy:** confirmed approach (in-app with advisory lock vs. init container) and any locking mechanism.
- **Kubernetes probe config:** YAML snippet with justified timing values for `initialDelaySeconds`, `periodSeconds`, `failureThreshold`, and `timeoutSeconds`.
- **Failure mode test result:** what happened when a dependency was made unavailable — confirmed HTTP 503, not a crash or a false 200.

## Safety
- Do not run database migrations without confirming a backup or rollback plan exists.
- Do not set `livenessProbe.failureThreshold` to 1 — a single slow response will trigger unnecessary pod restarts.
- Do not expose internal error details (stack traces, query text, connection strings) in the `/ready` or `/live` response body — return only dependency name and status.
- Do not make the liveness probe depend on external services — a slow downstream will trigger pod restarts that cannot self-heal.
- When testing failure modes, always use a non-existent or sandboxed endpoint, never point at a production dependency.

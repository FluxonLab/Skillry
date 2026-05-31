---
name: startup-health-readiness
description: Use when you need to add or verify readiness gates, health checks, and startup sequencing.
---

# Startup Health Readiness

## Purpose
This skill ensures that a service does not accept traffic or report itself healthy until all its dependencies are actually ready — database connections established, migrations run, caches warm, external clients initialized. It covers implementing and verifying `/health`, `/ready`, and `/live` endpoints, dependency wait loops, graceful startup sequencing, and Kubernetes/Docker probe configuration.

## When to use
- Adding a new service that will run in Kubernetes and needs `readinessProbe` / `livenessProbe` configuration.
- A service is being marked healthy by a load balancer before its database pool is initialized, causing 500s on first requests.
- A Docker Compose `depends_on` is not sufficient because the dependency container starts but is not yet accepting connections.
- You need to add a `/health` endpoint that distinguishes "process alive" from "ready to serve traffic."
- A service crashes on startup when a downstream dependency (Redis, Postgres, Stripe) is temporarily unavailable — it should retry instead.

## When not to use
- The service is a CLI tool or batch job — health probes are for long-running servers.
- The service already has tested, working health endpoints and you just need to debug a transient issue — use runtime-diagnostics instead.
- You are wiring up health checks in a managed platform (Render, Railway) that injects its own health check mechanism — read that platform's docs first.

## Procedure

1. **Audit the existing startup sequence.** Read the main entry point file and identify the exact order of: config load, database pool creation, migration execution, external client initialization, cache warm-up, and the moment `server.listen()` / `app.run()` is called. Note any step that can fail silently or take variable time.

2. **Design the three-endpoint contract (or two, if liveness/readiness overlap).** Define clearly:
 - `GET /live` (liveness): returns 200 if the process is not deadlocked and the event loop is running. Should never depend on external systems. Returns 503 if the app is in a shutdown sequence.
 - `GET /ready` (readiness): returns 200 only when all dependencies are reachable and the server is ready to handle real requests. Returns 503 otherwise. Kubernetes stops sending traffic when this returns non-200.
 - `GET /health` (optional combined): returns a JSON body with per-dependency status for human debugging.

3. **Implement dependency wait loops before `server.listen()`.** For each external dependency, add a retry loop with exponential backoff before calling listen. Example for Postgres (Node/pg):
 ```js
 async function waitForDb(pool, retries = 10, delayMs = 1000) {
 for (let i = 0; i < retries; i++) {
 try { await pool.query('SELECT 1'); return; }
 catch (e) { if (i === retries - 1) throw e; await sleep(delayMs * 2**i); }
 }
 }
 ```
 Cap the total wait time — do not retry indefinitely; let the orchestrator restart the pod.

4. **Run migrations inside the startup sequence, not as a separate pre-deploy job, unless you have a migration lock strategy.** If migrations run inside the app: ensure only one instance runs them (use a DB advisory lock: `SELECT pg_try_advisory_lock(12345)`). If migrations run as a separate init container or pre-deploy hook, confirm the app checks that migrations are at the expected version before marking itself ready.

5. **Implement the readiness check as a real probe, not a stub.** A `/ready` endpoint that always returns 200 defeats the purpose. At minimum, execute a lightweight query against each dependency:
 - Postgres: `SELECT 1`
 - Redis: `PING`
 - Elasticsearch: `GET /_cluster/health?wait_for_status=yellow&timeout=1s`
 Use a short timeout (1-2s) on each probe query so a slow dependency does not cause the health check itself to hang.

6. **Register a graceful shutdown handler.** On `SIGTERM`: stop accepting new requests, allow in-flight requests to finish (max 30s), then close DB pool and exit. Example (Node):
 ```js
 process.on('SIGTERM', async () => {
 server.close(async () => { await pool.end(); process.exit(0); });
 setTimeout(() => process.exit(1), 30_000);
 });
 ```
 Kubernetes sends SIGTERM and then SIGKILL after `terminationGracePeriodSeconds` — ensure your grace period is shorter than that value.

7. **Configure probe timings in Kubernetes manifests.** Recommended starting values:
 ```yaml
 livenessProbe:
 httpGet: { path: /live, port: 3000 }
 initialDelaySeconds: 10
 periodSeconds: 15
 failureThreshold: 3
 readinessProbe:
 httpGet: { path: /ready, port: 3000 }
 initialDelaySeconds: 5
 periodSeconds: 5
 failureThreshold: 6
 ```
 `initialDelaySeconds` must be longer than the worst-case startup time.

8. **Test the failure modes.** Simulate dependency unavailability: start the app with `DATABASE_URL` pointing to a non-existent host and confirm it retries, logs clearly, and does not mark itself ready. Then restore the correct URL and confirm the app becomes ready without a restart.

## Checklist
- [ ] `/live` endpoint returns 200 without querying external systems
- [ ] `/ready` endpoint performs real lightweight queries against each dependency
- [ ] `/ready` returns 503 with a JSON body describing which dependency failed
- [ ] Startup sequence waits for all dependencies before calling `server.listen()`
- [ ] Retry loop has exponential backoff and a maximum retry count (not infinite)
- [ ] Migration strategy is documented — in-app with lock, or separate init container
- [ ] `SIGTERM` handler closes connections and drains in-flight requests before exit
- [ ] Kubernetes `livenessProbe.initialDelaySeconds` exceeds worst-case startup time
- [ ] `readinessProbe.failureThreshold * periodSeconds` gives enough time for transient recovery
- [ ] Health endpoint tested with dependency unavailable — confirms 503 is returned, not 200

## Common issues & anti-patterns

- **Health endpoint that always returns 200**: many codebases have a `/health` route added as an afterthought that does `res.json({ status: 'ok' })` regardless of state — this is a false positive that defeats load balancer routing.
- **Migration running after `listen()`**: the server accepts requests while migrations are in progress, causing schema mismatch errors on the first few requests after deploy.
- **Liveness probe depending on database**: if the database is slow, the liveness probe times out, Kubernetes restarts the pod, and the pod cannot recover — use liveness only for process-level health.
- **No retry on startup**: the app throws on the first connection failure and exits — in a Kubernetes environment, the scheduler will restart it, but this creates noisy crash loops (CrashLoopBackOff) that delay readiness by minutes.
- **Grace period shorter than in-flight request timeout**: long-running requests (file uploads, report generation) are killed mid-flight because `terminationGracePeriodSeconds` is set to the default 30s but requests can take 60s.

## Required output
Report must include:
- **Startup sequence audit**: ordered list of initialization steps and which ones can fail
- **Endpoint implementation**: code or pseudocode for `/live` and `/ready` with per-dependency checks
- **Retry strategy**: backoff configuration for each external dependency
- **Migration strategy**: confirmed approach and any locking mechanism used
- **Kubernetes probe config**: YAML snippet with justified timing values
- **Failure mode test result**: what happened when a dependency was made unavailable

## Safety
- Do not run database migrations without confirming a backup or rollback plan exists.
- Do not set `livenessProbe.failureThreshold` to 1 — a single slow response will cause unnecessary pod restarts.
- Do not expose internal error details (stack traces, query errors) in the `/ready` or `/live` response body — return only dependency name and "ok"/"unavailable".

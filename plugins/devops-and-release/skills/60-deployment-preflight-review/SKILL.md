---
name: deployment-preflight-review
description: Use when you need to perform non-deploying deployment readiness checks for env, build, DB, secrets, and rollback.
---

# Deployment Preflight Review

## Purpose

Perform a structured pre-deployment readiness check without executing the deployment itself. Verify that all environment variables are present in the target environment, pending database migrations are identified and safe to run, the build artifact is valid, the health endpoint is configured, a rollback plan exists, and a smoke test suite is defined. Produce a pass/fail checklist and a list of blockers before the team pulls the deploy trigger.

## When to use

- A deployment is scheduled and you want to confirm nothing is missing before go-live.
- A previous deployment failed and you need to confirm the issue is resolved before retrying.
- A release involves a database migration and you need to verify forward/backward compatibility.
- A new service is being deployed for the first time and there is no established deployment checklist.
- A deployment window is short (maintenance window, peak-traffic avoidance) and errors are costly.

## When not to use

- You need to actually execute the deployment — this skill is read-only verification only.
- The deployment is fully automated and the CI/CD pipeline already gates on all required checks.
- The task is to fix a deployment failure after the fact — use a debugging/incident skill.

## Procedure

1. **Confirm the build artifact is present and valid.** Check that the CI build completed successfully on the exact commit being deployed. Verify the artifact (Docker image SHA, deployment package hash, or build ID) matches what CI produced — not a locally built artifact that may differ.

2. **Audit environment variables for the target environment.** Compare the required variables (from `.env.example`, `README`, or a config validation schema) against the variables configured in the target environment (production secrets store, Kubernetes ConfigMap, Heroku config vars, etc.). List any variable present in the schema but missing from the target.

3. **Check for pending database migrations.** Run the migration status command in dry-run/status mode:
 - Prisma: `prisma migrate status`
 - Sequelize: `sequelize db:migrate:status`
 - Flyway: `flyway info`
 - Rails: `rails db:migrate:status`
 Identify which migrations have not been applied to the target database. Flag any that are destructive (column drop, table drop, non-nullable column addition without a default).

4. **Verify migration backward compatibility.** For a zero-downtime deployment, the new code must be compatible with the pre-migration schema (old code still running during rolling deploy) and the post-migration schema (new code after migration completes). Check for: column renames (break old code), non-nullable additions without default (break inserts from old code), removed columns referenced in old code.

5. **Confirm the health check endpoint.** Verify the application exposes a `/health` or `/healthz` endpoint that returns 200 only when the app is fully initialized (DB connected, cache connected, required services reachable). Confirm the load balancer or orchestrator is configured to use this endpoint, not just a TCP check.

6. **Define the rollback plan.** For each change in this deployment, confirm there is a rollback path:
 - Code: previous Docker image tag or deployment artifact available.
 - Database: reversible migration exists (`migrate down` works and is tested), or the migration is additive-only (safe to leave applied even after code rollback).
 - Feature flags: new functionality is behind a flag that can be turned off without redeployment.
 - Configuration: previous config values are documented and can be restored.

7. **Confirm smoke tests are defined.** A smoke test suite should be executable within 5 minutes after deployment. It must cover: the health endpoint, the most critical user-facing flows (login, primary action, payment if applicable), and any functionality changed in this release. Confirm the smoke tests run against the target environment, not a mock.

8. **Check for dependent service compatibility.** If other services (microservices, third-party integrations) depend on the API being deployed, confirm they are compatible with the new version. Check for breaking API changes without a versioning strategy.

9. **Verify the deployment window and notification plan.** Confirm: the deployment window is scheduled and stakeholders are notified, a communication plan exists for users if downtime is expected, and a point of contact is identified for the deployment duration.

10. **Confirm monitoring and alerting are active.** Before deploying, verify that error rate dashboards, latency monitors, and on-call alerting are configured for the target service. Deploying into a monitoring blind spot means regressions go undetected.

## Checklist

- [ ] Build artifact matches the CI-produced artifact for the exact deploy commit (SHA verified).
- [ ] All required env vars are present in the target environment — no gaps vs. `.env.example`.
- [ ] Pending migrations identified; none are destructive to the running old-version code.
- [ ] Migrations are backward compatible for zero-downtime rolling deploy.
- [ ] Health check endpoint returns 200 on full initialization; load balancer uses it.
- [ ] Rollback plan documented for code, DB, and config changes.
- [ ] Smoke test suite defined and executable in < 5 minutes post-deploy.
- [ ] Dependent services are compatible with new API version.
- [ ] Deployment window is scheduled and stakeholders are notified.
- [ ] Error rate and latency monitoring are active for the target service.
- [ ] On-call rotation is staffed for the deployment window.

## Common issues & anti-patterns

- **Deploying locally built artifacts**: the "works on my machine" build may have different env vars or dependency versions than CI.
- **Migration run after code deploy in rolling update**: new code runs against old schema during the window; if new code requires the new column, it crashes.
- **Non-reversible migration**: `ALTER TABLE DROP COLUMN` cannot be undone without data loss; always confirm the column is no longer read by old code before dropping.
- **Health endpoint always returns 200**: the endpoint does not check DB or cache connectivity; the load balancer routes traffic to a broken instance.
- **No smoke test after deploy**: the team assumes CI green = prod working; a config or integration issue only surfaces in production.
- **Feature behind a flag that the flag system can't reach**: the flag service itself is unavailable, so the flag defaults to `on` and releases the untested feature.
- **Rollback plan untested**: the rollback procedure is documented but has never been executed; it fails when actually needed.
- **Missing dependency service version pin**: the deployed service requires API version 2 of a dependency but the dependency is on version 1 in production.

## Required output

```
## Deployment Preflight Report

### Build artifact
- Artifact ID / image SHA: ...
- CI build verified: yes/no
- Matches deploy commit: yes/no

### Environment variable check
| Variable | Required | Present in target | Status |
|----------|----------|------------------|--------|
| DATABASE_URL | yes | yes | OK |
| STRIPE_SECRET_KEY | yes | NO | BLOCKER |

### Database migration status
| Migration | Status | Destructive | Backward compatible |
|-----------|--------|-------------|---------------------|

### Health check
- Endpoint: /health
- Checks DB: yes/no
- Load balancer configured: yes/no

### Rollback plan
- Code rollback: previous image tag X available: yes/no
- DB rollback: migrations reversible: yes/no
- Feature flag kill switch: yes/no

### Smoke test suite
- Defined: yes/no
- Covers this release's changes: yes/no
- Estimated run time: X minutes

### Blockers (must resolve before deploy)
1. ...

### Warnings (should resolve; deployment can proceed with acknowledgment)
1. ...
```

## Safety

- Do not execute any deployment commands, `kubectl apply`, `heroku releases`, `docker push`, or equivalent.
- Do not run database migrations — run only status/info commands.
- Do not modify environment variables in any environment.
- Do not access production data or run queries that modify records.

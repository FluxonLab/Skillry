---
name: deployment-preflight-review
description: Use when you need to perform non-deploying deployment readiness checks for env, build, DB, secrets, and rollback.
---

# Deployment Preflight Review

## Purpose

Perform a structured pre-deployment readiness check without executing the deployment. Verify all required environment variables are present in the target environment, pending database migrations are identified and safe, the build artifact is valid and matches CI, the health endpoint is configured, a rollback plan exists, and a smoke test suite is defined. Produce a pass/fail checklist and a blocker list before the team pulls the deploy trigger. This skill is strictly read-only verification — it runs status/info commands only, never `apply`, `migrate`, or `push`.

## When to use

- A deployment is scheduled and you want to confirm nothing is missing before go-live.
- A previous deployment failed and you need to confirm the issue is resolved before retrying.
- A release involves a database migration and you need to verify forward/backward compatibility.
- A new service is being deployed for the first time with no established checklist.
- A deployment window is short (maintenance window, peak-traffic avoidance) and errors are costly.

## When not to use

- You need to actually execute the deployment — this skill is verification only.
- The deployment is fully automated and the CI/CD pipeline already gates on all required checks (use `58-ci-cd-pipeline-review` to audit those gates).
- The task is to fix a deployment failure after the fact — use a debugging/incident skill.

## Procedure

1. **Confirm the build artifact is present and valid.** Check CI completed on the exact deploy commit. Verify the artifact (Docker image SHA, package hash, build ID) matches what CI produced — not a locally built artifact that may differ.
2. **Audit environment variables.** Compare required variables (from `.env.example`, README, or a config schema) against the target environment (secrets store, ConfigMap, config vars). List any variable present in the schema but missing from the target.
3. **Check for pending database migrations** in status/dry-run mode (`prisma migrate status`, `sequelize db:migrate:status`, `flyway info`, `rails db:migrate:status`). Flag destructive ones (column/table drop, non-nullable add without default).
4. **Verify migration backward compatibility.** For zero-downtime rolling deploys, new code must run against the old schema (during rollout) and the new schema (after). Flag column renames, non-nullable adds without default, and removed columns still referenced by old code.
5. **Confirm the health check endpoint.** Verify `/health` or `/healthz` returns 200 only when fully initialized (DB, cache, required services reachable) and the load balancer uses it, not just a TCP check.
6. **Define the rollback plan** for each change: code (previous image tag available), database (reversible migration tested, or additive-only), feature flags (kill switch reachable), configuration (previous values documented).
7. **Confirm smoke tests are defined** — executable within 5 minutes post-deploy, covering the health endpoint, critical user flows, and this release's changes, against the target environment, not a mock.
8. **Check dependent service compatibility.** Confirm consumers are compatible with the new API version; flag breaking changes without a versioning strategy.
9. **Verify the deployment window and notification plan** — scheduled, stakeholders notified, comms plan for expected downtime, named point of contact.
10. **Confirm monitoring and alerting are active** — error rate, latency, and on-call alerting configured for the target service.

## Concrete checks

- [ ] Build artifact matches the CI-produced artifact for the exact deploy commit (SHA verified).
- [ ] All required env vars are present in the target environment — no gaps vs. `.env.example`.
- [ ] Pending migrations identified; none are destructive to the running old-version code.
- [ ] Migrations are backward compatible for a zero-downtime rolling deploy.
- [ ] Health check endpoint returns 200 on full initialization; load balancer uses it.
- [ ] Rollback plan documented for code, DB, and config changes.
- [ ] Smoke test suite defined and executable in under 5 minutes post-deploy.
- [ ] Dependent services are compatible with the new API version.
- [ ] Deployment window is scheduled and stakeholders are notified.
- [ ] Error rate and latency monitoring are active for the target service.
- [ ] On-call rotation is staffed for the deployment window.

## Commands or Templates

```bash
# Env gap: schema keys present in .env.example but missing from the target
comm -23 \
  <(grep -vE '^\s*#|^\s*$' .env.example | cut -d= -f1 | sort) \
  <(printenv | cut -d= -f1 | sort)        # swap printenv for the target store's key list

# Migration status (read-only — never run the migration here)
npx prisma migrate status        # Prisma
npx sequelize db:migrate:status  # Sequelize
flyway info                      # Flyway

# Flag destructive migration statements in pending SQL
grep -rniE "drop (table|column)|alter .* drop|not null" prisma/migrations/ migrations/

# Verify the deployed artifact matches CI (image SHA / build id)
docker inspect --format '{{.Id}}' myimage:tag    # compare to the CI-published digest
```

```
## Deployment Preflight Report
### Build artifact
- Artifact ID / image SHA | CI build verified: yes/no | Matches deploy commit: yes/no
### Environment variable check
| Variable | Required | Present in target | Status |
| DATABASE_URL | yes | yes | OK |
| STRIPE_SECRET_KEY | yes | NO | BLOCKER |
### Database migration status
| Migration | Status | Destructive | Backward compatible |
### Health check
- Endpoint | Checks DB: yes/no | Load balancer configured: yes/no
### Rollback plan
- Code: prev image tag available | DB: migrations reversible | Feature flag kill switch
### Smoke test suite
- Defined: yes/no | Covers this release: yes/no | Est. run time
### Blockers (must resolve before deploy)
### Warnings (proceed only with acknowledgment)
```

## Migration safety classification

Classify every pending migration before sign-off — this is where most rolling-deploy outages originate:

| Migration | Safe for zero-downtime? | Why / mitigation |
|-----------|-------------------------|------------------|
| Add nullable column | Yes | old code ignores it |
| Add column with default | Usually | safe if the DB backfills without a long lock |
| Add NOT NULL column, no default | No | old-code inserts fail; add nullable + backfill + constraint in steps |
| Rename column | No | old code reads the old name; use expand/contract (add new, dual-write, drop old later) |
| Drop column | No (this release) | confirm no running code reads it; drop one release *after* code stops using it |
| Add index | Yes if `CONCURRENTLY` | a plain `CREATE INDEX` locks writes |

The general rule: a migration must be compatible with *both* the currently running code and the incoming code during the rollout window. If it is not, split it across releases (expand/contract).

## Worked example

Preflight finds a pending migration `0042_add_user_region.sql`:

```sql
ALTER TABLE users ADD COLUMN region VARCHAR(2) NOT NULL;
```

Classify as a **blocker** for a rolling deploy: it adds a NOT NULL column with no default, so any insert from the still-running old version (which does not set `region`) fails for the duration of the rollout. Mitigation in the report: split into (1) add the column nullable now, (2) backfill existing rows and have new code populate it, (3) add the NOT NULL constraint in a later release once all writers set it. Mark the original single-statement migration as "do not deploy as-is", and confirm there is a tested rollback (the column add is reversible, but the constraint add is the risky step). No migration command is executed during preflight — only the status/info read and this classification.

## Common issues & anti-patterns

- **Deploying locally built artifacts.** The "works on my machine" build may differ from CI in env or dependency versions.
- **Migration run after code deploy in a rolling update.** New code hits the old schema during the window and crashes if it requires the new column.
- **Non-reversible migration.** `DROP COLUMN` cannot be undone without data loss; confirm old code no longer reads it before dropping.
- **Health endpoint always returns 200.** It does not check DB or cache; the load balancer routes traffic to a broken instance.
- **No smoke test after deploy.** The team assumes CI green = prod working; a config or integration issue surfaces only in production.
- **Flag the flag system cannot reach.** The flag service is down, so the flag defaults to on and releases the untested feature.
- **Untested rollback plan.** Documented but never executed; it fails when actually needed.
- **Missing dependency version pin.** The service requires API v2 of a dependency stuck on v1 in production.

## Rollback plan by change type

A rollback plan is not "redeploy the old image" — each change type has a different reversal path, and some are not reversible at all:

| Change type | Rollback path | Caveat |
|-------------|---------------|--------|
| Code only | redeploy previous image tag | confirm the tag still exists in the registry |
| Additive migration | leave it applied; roll back code | safe — old code ignores the new column |
| Destructive migration | restore from backup | data written after deploy may be lost; prefer expand/contract |
| Config change | restore previous values | document the old values *before* changing them |
| Feature behind a flag | flip the flag off | no redeploy needed — the fastest rollback |

The safest releases keep risky changes behind a flag so rollback is a flag flip, not a redeploy. The preflight must confirm that the rollback path for *every* change in the release is documented and, for the database, actually tested — a rollback procedure that has never been executed is an assumption, not a plan.

## Required output

Return the Deployment Preflight Report block above: build artifact verification, an env-var gap table (BLOCKER on any missing required var), migration status with destructive/compat flags, health-check and rollback assessments, smoke-test status, and two ordered lists — blockers that must be resolved and warnings that can proceed only with acknowledgment.

## Safety

- Do not execute any deployment commands, `kubectl apply`, `heroku releases`, `docker push`, or equivalent.
- Do not run database migrations — run only status/info commands.
- Do not modify environment variables in any environment.
- Do not access production data or run queries that modify records.

## Completion criteria

Done means the artifact was verified against CI, env-var gaps and pending migrations were identified with destructive/compat flags, health-check and rollback plans were assessed, smoke tests were confirmed, and a blocker list was produced — with no deploy or migration command executed.

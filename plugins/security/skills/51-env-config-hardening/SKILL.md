---
name: env-config-hardening
description: Use when you need to harden environment handling, config defaults, .env safety, secret loading, and redaction.
---

# Env Config Hardening

## Purpose

> **Scope note:** For committed-secret scanning and credential leak detection (git history, CORS, JWT, injection sinks), use `security-and-secrets-review` (47); this skill focuses on env var validation, config defaults, and 12-factor hardening.

Audit how the project loads, validates, and protects environment variables and secrets. Catch `.env` files committed to git, default secrets in code, missing schema validation, missing redaction in logs, and deviations from 12-factor config principles. Produce concrete fixes with file references — not just observations.

The practical goal: the app must fail fast with a clear, actionable error when a required config value is missing or malformed, and it must never silently start with a dangerous default. Every finding includes the file and line where the risk lives and the smallest safe fix.

## When to use

- A `.env` file or hardcoded secret was found (or suspected) in the codebase or git history.
- The project has no config validation layer and starts silently with missing or malformed env vars.
- `NODE_ENV` is not set or is set inconsistently across environments.
- Secret rotation is being planned and you need to confirm the codebase supports it cleanly.
- A new service is being added and needs to follow existing config conventions.
- A Docker image or CI pipeline change touches how secrets are injected into the container.

## When not to use

- The project uses a secrets manager (Vault, AWS Secrets Manager, GCP Secret Manager) exclusively and the task is to configure that manager, not the application code.
- Config hardening was done recently and the task is something else entirely.
- The codebase is a throwaway script with no production deployment.

## Procedure

1. **Check `.gitignore` for `.env` files.** Confirm `.env`, `.env.local`, `.env.*.local`, and any environment-specific variants (`*.env`, `.env.production`, `.env.staging`) are excluded. Run `git ls-files | grep -E '\.env'` to surface any currently tracked env files, and `git log --all --full-history -- '*.env' '**/.env'` to detect past commits.

2. **Scan for hardcoded secrets.** Search for assignment patterns: `password =`, `secret =`, `api_key =`, `token =`, `private_key`, base64-encoded strings longer than 40 characters, and PEM headers (`-----BEGIN`). Look in config files, seed files, test fixtures, migration scripts, and Dockerfiles. Every hit must be reported as `file:line` — raw values must not appear in the output.

3. **Verify `.env.example` / `.env.template` exists and is complete.** The template must list every required variable with a placeholder value (not the real value), a comment describing its purpose, and an expected format. Example: `DATABASE_URL=postgres://user:pass@host:5432/db  # Required. Postgres connection string.`. Compare the template against the actual variables consumed by the app.

4. **Inspect config validation.** Check for a startup validation step using `zod`, `joi`, `envalid`, `t3-env`, `convict`, or equivalent. The app must fail fast with a clear error message if a required variable is missing or has the wrong type — not crash with `Cannot read properties of undefined` at first usage, and not start silently with a broken config.

5. **Check `NODE_ENV` handling.** Confirm `NODE_ENV` is set explicitly in all deployment environments. Code that branches on `NODE_ENV === 'production'` for security features (HTTPS-only cookies, strict CSP, forced HTTPS) must default to the secure branch when `NODE_ENV` is unset — not to the permissive development branch.

6. **Audit default values.** Look for patterns like `process.env.SECRET || 'changeme'` or `process.env.JWT_SECRET || 'dev-secret'`. Required secrets must have no fallback default. A required value that silently defaults to a known string in production is a critical misconfiguration.

7. **Verify secret redaction in logs.** Search for logging statements that include `req.headers`, `req.body`, `process.env`, or config objects without a redaction step. Confirm the logging middleware strips `authorization`, `cookie`, `password`, `secret`, `token`, and `x-api-key` field names. Check error tracking integrations (Sentry, Datadog) for similar leakage.

8. **Check secret rotation readiness.** Secrets should be loaded at request time or at startup through a reload-capable mechanism, not cached in module-level constants in a way that prevents hot rotation. A rotating secret that requires a full process restart to take effect creates a downtime window during rotation.

9. **Inspect Dockerfile and CI config.** Confirm `ARG` vs `ENV` usage in Dockerfiles — `ARG` values are visible in image layer history via `docker history`; secrets must not be passed as `ARG`. In CI, secrets must be injected via the CI platform's secret store (GitHub Actions `secrets.*`, GitLab CI variables, CircleCI contexts), never stored in plain text in workflow YAML files.

10. **Verify environment parity.** Compare the variable list in `.env.example` against what each deployment environment (staging, production) actually provides. Flag variables present in the example but absent from deployment configs (silently unset at runtime) and variables present in deployment but absent from the example (undocumented dependency).

## Concrete checks

- [ ] `.gitignore` includes `.env`, `.env.local`, and all `.env.*.local` variants; wildcards like `*.env` and `*.env.*` are preferred over per-file entries.
- [ ] `git ls-files | grep -E '\.env'` returns empty; no env files are currently tracked.
- [ ] `git log --all --full-history -- '*.env'` returns empty; no env files exist in history.
- [ ] No hardcoded passwords, API keys, or tokens appear in source code, test fixtures, seed files, or migration scripts.
- [ ] `.env.example` exists and lists every required variable with a placeholder value and a comment.
- [ ] Startup config validation fails fast on missing or invalid variables (zod/joi/envalid parse runs at import time or in the server init function, before any request handler is registered).
- [ ] No required secret has a fallback default value in code.
- [ ] `NODE_ENV` defaults to the secure branch when unset; the insecure (dev) branch is opt-in, not opt-out.
- [ ] Logging middleware redacts `authorization`, `cookie`, `password`, `secret`, `token`, `x-api-key` fields before writing to any log sink.
- [ ] No secrets passed as Docker `ARG`; secrets enter containers via environment injection only (`--env-file` or orchestrator-managed secrets).
- [ ] CI pipeline reads secrets from the platform secret store; no plain-text secret values appear in workflow YAML files.
- [ ] All environment-specific configs (staging, prod) reconciled against `.env.example`; no variable is silently unset.

## Commands

```bash
# Check for tracked .env files (must return empty)
git ls-files | grep -E '(^|/)\.env($|\.)' || echo "clean"

# Check .gitignore coverage
git check-ignore -v .env .env.local .env.production 2>/dev/null || echo "WARNING: one or more .env files not gitignored"

# Search git history for .env file commits
git log --all --full-history --oneline -- '*.env' '**/.env' '.env*'

# Hardcoded secret patterns (generic assignment)
rg -niP '(password|passwd|secret|api[_-]?key|token|private[_-]?key)\s*[:=]\s*["\x27][^"\x27]{6,}' \
  -g '!*.lock' -g '!node_modules' -g '!*.min.*' .

# Base64 blob and PEM header detection
rg -nP '-----BEGIN [A-Z ]*PRIVATE KEY-----|-----BEGIN CERTIFICATE-----' -g '!node_modules' .
rg -nP '[A-Za-z0-9+/]{40,}={0,2}' -g '!*.lock' -g '!node_modules' src/ | grep -v "# base64" | head -20

# Fallback default secrets (critical misconfiguration)
rg -n '\|\|\s*["\x27](dev|secret|changeme|password|test|local|default|123)' src/ --type ts --type js

# NODE_ENV security gate (should default to secure, not dev)
rg -n "NODE_ENV\s*!==?\s*['\"]production['\"]" src/ --type ts --type js

# Config validation library present?
rg -n "from 'zod'\|from 'joi'\|from 'envalid'\|from 't3-env'\|from 'convict'" src/ --type ts --type js || \
  echo "No schema validation library detected — startup validation may be missing"

# Logging: check for unredacted sensitive fields
rg -n "console\.log\|logger\.(info|debug|warn|error)" src/ --type ts --type js | \
  grep -E "req\.(headers|body)|process\.env|config\." | head -20

# Dockerfile: ARG used for secrets?
rg -n "^ARG\s+(SECRET|KEY|TOKEN|PASSWORD|PASS)" Dockerfile* docker-compose*.yml 2>/dev/null

# CI: plaintext secret values in workflow files?
rg -n "(password|secret|token|key)\s*:" .github/workflows/ .gitlab-ci.yml 2>/dev/null | \
  grep -v '\$\{\{' | grep -v "secrets\." | grep -v "env\." | head -20

# .env.example vs actual env consumption (find all process.env usages)
rg -n 'process\.env\.\w+' src/ --type ts --type js -o | grep -oP 'process\.env\.\K\w+' | sort -u > /tmp/env_used.txt
grep -oP '^\K[A-Z_]+(?==)' .env.example 2>/dev/null | sort -u > /tmp/env_documented.txt
comm -23 /tmp/env_used.txt /tmp/env_documented.txt && echo "Above vars used but not in .env.example" || true
```

```bash
# Secret rotation readiness: detect module-level const caching of secrets
rg -n "^const\s+\w*(secret|key|token|password)\w*\s*=\s*process\.env" src/ --type ts --type js -i

# Check for dotenv loaded outside dev/test
rg -n "require\('dotenv'\)|import.*dotenv" src/ --type ts --type js | grep -v "test\|spec\|__tests__\|\.test\." | head -10

# Docker: verify ENV vs ARG for secrets (ENV bakes value into image layers too — use runtime injection)
grep -nE "^(ENV|ARG)\s" Dockerfile* 2>/dev/null | head -20

# Error tracking leakage: Sentry/Datadog breadcrumbs with sensitive data
rg -n "Sentry\.(captureException|captureMessage|addBreadcrumb)" src/ --type ts --type js | \
  grep -E "req\.(body|headers)|password|token" | head -10
```

## Severity rubric

| Severity | Example |
|----------|---------|
| **Critical** | `.env` file tracked in git (currently or in history). Hardcoded live secret in source code. Required secret has a known string as its default (`|| 'dev-secret'`). |
| **High** | No startup config validation — app starts silently with a broken or missing config. `NODE_ENV` security gate defaults to the insecure branch. Logging middleware emits `req.headers` or `req.body` without redaction. |
| **Medium** | `.env.example` missing or incomplete (undocumented required variable). Secret cached at module load time preventing rotation without restart. `dotenv` loaded unconditionally in production. |
| **Low** | A variable in `.env.example` has a real-looking placeholder value instead of a clearly fake one. Staging config has an extra variable not listed in the example (undocumented optional). Verbose startup log includes config object key names. |

## Common issues & anti-patterns

- **`.env` in git history**: even after deletion from the working tree, the file is recoverable from every clone. Requires `git filter-repo` or BFG Repo Cleaner to purge from history — and secret rotation is mandatory regardless, because history rewrite does not invalidate the value on existing clones.
- **`dotenv` loaded unconditionally in production**: `require('dotenv').config()` at the top of `server.ts` causes the production app to read from a `.env` file if one exists, silently overriding injected environment variables. `dotenv` should load only in development and test (`if (process.env.NODE_ENV !== 'production')`).
- **Config spread across files without a central validation point**: secrets in `config/database.js`, `config/redis.js`, and `src/auth/jwt.js` with no single validated config object makes it impossible to audit which variables are required and which have safe defaults.
- **`console.log(config)` at startup**: added for debugging and left in, this logs the entire config object — including all secret values — to stdout in production.
- **`NODE_ENV` used as a security gate without a default**: `if (process.env.NODE_ENV !== 'production') { skipAuth() }` — when `NODE_ENV` is unset or empty, auth is skipped. The safe pattern is `if (process.env.NODE_ENV === 'development') { skipAuth() }` so missing env defaults to secure.
- **Secrets in URL query strings**: `?api_key=xxx` is logged by every proxy, load balancer, CDN, and browser history. Secrets must travel in request headers or request bodies over TLS.
- **Rotation breaks the app**: a secret cached as `const jwtSecret = process.env.JWT_SECRET` at module import time means deploying a rotated secret requires a full process restart. For high-rotation-frequency secrets, load at request time or use a reload signal handler.
- **Docker `ARG` for secrets**: `docker build --build-arg DB_PASSWORD=xxx` stores the value in the image's layer history, visible via `docker history --no-trunc`. Use runtime environment injection (`docker run -e` or orchestrator secrets mounts) instead.

## Required output

```
## Env Config Hardening Report

### Critical findings
- [FILE:LINE or GIT-SHA] Description, impact, fix command or code change.

### High findings
- ...

### Medium findings
- ...

### Config validation status
- Library used: zod / joi / envalid / t3-env / none
- Validated at startup: yes/no
- Variables validated: list

### .env.example completeness
- Variables in example: N
- Variables consumed by app but missing from example: list
- Variables in example with real-looking values (risk): list

### Redaction status
- Logging library: X
- Fields redacted: list
- Unredacted sensitive fields found: list (file:line)

### Docker / CI injection
- Dockerfile ARG misuse for secrets: yes/no (files affected)
- CI workflow plaintext secrets: yes/no (files affected)

### Recommended immediate actions
1. [CRITICAL] Rotate any secret found in git history before making any other change.
2. ...
```

## Safety

- Do not print actual secret values found — reference them by variable name and `file:line` only, redacted to first/last 4 characters if any portion must be shown.
- Do not modify `.env` files, secrets manager configuration, or CI secret store entries.
- Do not run `git filter-repo` or history rewrite commands; document them for the user to run manually with explicit approval.
- Do not commit changes to `.gitignore` or `.env.example` without explicit user approval.
- If a Critical live-secret finding appears (value committed to git history), surface it immediately and flag rotation as the blocking action before completing the rest of the review.

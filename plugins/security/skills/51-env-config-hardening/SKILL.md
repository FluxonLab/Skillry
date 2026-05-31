---
name: env-config-hardening
description: Use when you need to harden environment handling, config defaults, .env safety, secret loading, and redaction.
---

# Env Config Hardening

## Purpose

> **Scope note:** For committed-secret scanning and credential leak detection (git history, CORS, JWT, injection sinks), use `security-and-secrets-review` (47); this skill focuses on env var validation, config defaults, and 12-factor hardening.

Audit how the project loads, validates, and protects environment variables and secrets. Catch `.env` files committed to git, default secrets in code, missing schema validation, missing redaction in logs, and deviations from 12-factor config principles. Produce concrete fixes, not just observations.

## When to use

- A `.env` file or hardcoded secret was found (or suspected) in the codebase or git history.
- The project has no config validation layer and starts silently with missing/malformed env vars.
- `NODE_ENV` is not set or is set inconsistently across environments.
- Secret rotation is being planned and you need to confirm the codebase supports it cleanly.
- A new service is being added and needs to follow existing config conventions.

## When not to use

- The project uses a secrets manager (Vault, AWS Secrets Manager) exclusively and the task is to configure that manager, not the application code.
- Config hardening was done recently and the task is something else entirely.
- The codebase is a throwaway script with no production deployment.

## Procedure

1. **Check `.gitignore` for `.env` files.** Confirm `.env`, `.env.local`, `.env.*.local`, and any environment-specific variants are excluded. Run `git log --all --full-history -- '*.env' '**/.env'` to detect past commits of env files.

2. **Scan for hardcoded secrets.** Search for patterns: `password =`, `secret =`, `api_key =`, `token =`, `private_key`, base64-encoded strings >40 chars, and PEM headers (`-----BEGIN`). Look in config files, seed files, test fixtures, and Docker files.

3. **Verify `.env.example` / `.env.template` exists.** The template must list every required variable with a placeholder value (not the real value), a comment describing its purpose, and the expected format (e.g., `DATABASE_URL=postgres://user:pass@host:5432/db`).

4. **Inspect config validation.** Check for a startup validation step using `zod`, `joi`, `envalid`, `t3-env`, or similar. The app should fail fast with a clear error message if a required variable is missing or has the wrong type — not crash with `Cannot read property of undefined` at the first usage.

5. **Check `NODE_ENV` handling.** Confirm `NODE_ENV` is set explicitly in all deployment environments. Code that branches on `NODE_ENV === 'production'` for security features (HTTPS-only cookies, strict CSP) must default to the secure branch, not the permissive one.

6. **Audit default values.** Look for patterns like `process.env.SECRET || 'changeme'` or `process.env.JWT_SECRET || 'dev-secret'`. Default secrets are a critical misconfiguration; required secrets must have no default.

7. **Verify secret redaction in logs.** Search for logging statements that include `req.headers`, `req.body`, `process.env`, or config objects without a redaction step. Confirm logging middleware strips `authorization`, `cookie`, `password`, and other sensitive field names.

8. **Check secret rotation readiness.** Secrets should be loaded at request time (or at startup with a reload mechanism), not cached in module scope in a way that prevents rotation without a process restart.

9. **Inspect Docker and CI config.** Confirm `ARG` vs `ENV` usage in Dockerfiles — `ARG` values are visible in image layer history; secrets must not be passed as `ARG`. In CI, confirm secrets are injected via the CI platform's secret store, not stored in plain text in workflow files.

10. **Verify environment parity.** Compare the variable list in `.env.example` against what each deployment environment (staging, production) actually provides. Flag variables present in example but absent from deployment configs.

## Checklist

- [ ] `.gitignore` includes `.env`, `.env.local`, and all `.env.*.local` variants.
- [ ] `git log` shows no committed `.env` files in history.
- [ ] No hardcoded passwords, API keys, or tokens in source code or test fixtures.
- [ ] `.env.example` exists with all variables, placeholder values, and descriptions.
- [ ] Startup config validation fails fast on missing or invalid variables.
- [ ] No required secret has a default fallback value in code.
- [ ] `NODE_ENV` defaults to the secure branch (not `development`) when unset in production.
- [ ] Logging middleware redacts `authorization`, `cookie`, `password`, `secret`, `token` fields.
- [ ] No secrets passed as Docker `ARG`; secrets enter containers via environment injection only.
- [ ] CI pipeline reads secrets from the platform secret store, not from committed files.
- [ ] All environment-specific configs (staging, prod) are reconciled against `.env.example`.

## Common issues & anti-patterns

- **`.env` in git history**: even after deletion, the file is recoverable from history. Requires `git filter-repo` or `BFG` to purge, plus secret rotation.
- **`dotenv` loaded in production**: production apps should read from the real environment, not from `.env` files; `dotenv` should only load in development/test.
- **Config spread across files**: secrets in `config/database.js`, `config/redis.js`, and `src/auth/jwt.js` with no central validation — impossible to audit.
- **`console.log(config)` at startup**: developers add this for debugging and forget to remove it; logs secrets to stdout in production.
- **`NODE_ENV` used as a security gate without a default**: `if (NODE_ENV !== 'production') { skipAuth() }` — when `NODE_ENV` is unset, auth is skipped.
- **Secrets in URL query strings**: `?api_key=xxx` gets logged by every proxy, load balancer, and CDN.
- **Rotation breaks the app**: secret cached at module load time means deploying a new secret requires a full restart, causing downtime if not planned.

## Required output

```
## Env Config Hardening Report

### Critical findings
- [FILE or GIT-SHA] Description, impact, fix command or code change.

### High findings
- ...

### Config validation status
- Library used: zod / joi / envalid / none
- Validated at startup: yes/no
- Variables validated: list

### .env.example completeness
- Variables in example: N
- Variables missing from example: list
- Variables in example with real values (risk): list

### Redaction status
- Logging library: X
- Fields redacted: list
- Unredacted sensitive fields found: list

### Recommended immediate actions
1. ...
2. ...
```

## Safety

- Do not print actual secret values found — reference them by variable name and file/line only.
- Do not modify `.env` files or any secrets manager configuration.
- Do not run `git filter-repo` or history rewrite commands; document them for the user to run manually.
- Do not commit changes to `.gitignore` or `.env.example` without explicit user approval.

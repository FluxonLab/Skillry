---
name: security-and-secrets-review
description: Use when you need to review secrets, environment variables, auth, CORS, token handling, logging redaction, and unsafe changes.
---

# Security And Secrets Review

## Purpose
Use this skill to review secrets, environment variables, auth, CORS, token handling, logging redaction, and unsafe changes. Every finding is assigned a severity (Critical → Low) with a concrete fix and, for any live exposed secret, a rotation flag — because a finding without a next action is not a finding.

## When to use
- Before merging code that adds authentication flows, handles tokens or sessions, or touches `.env` / config files.
- When a dependency or endpoint that processes user input, credentials, or payment data is being added or changed.
- Before a release or handoff, as a committed-secret and credential-leak gate — confirm nothing sensitive was accidentally tracked in git.
- When a CORS, cookie, or logging policy change is proposed and its security implications need to be verified against the concrete checks below.

## When not to use
- The task is unrelated to security work.
- The work would require production deploys, destructive data actions, or secret disclosure.
- A narrower skill or existing project instruction already covers the need.

## Procedure
1. Map the secret surface: locate `.env*`, config files, and CI secret references, then confirm `.gitignore` excludes every env/secret file. Treat anything tracked by git as already public.
2. Scan the working tree (and history if approved) for committed credentials using the regex set below. Verify each hit by file:line; never paste the raw value into the report — redact to first/last 4 chars.
3. Review auth and token handling: where tokens live (httpOnly cookie vs `localStorage`), how JWTs are signed/verified, and whether any dev fallback secret exists.
4. Review CORS, cookies, and transport: origin allowlists, credentialed CORS, cookie flags, HTTPS assumptions.
5. Review logging/redaction: ensure request bodies, headers, tokens, and PII are not written in clear text.
6. Review unsafe sinks: `eval`, dynamic `child_process`, SQL/HTML built by string concatenation with user input.
7. Rank findings by severity, give one concrete fix per item, and flag any real exposed secret for rotation.

## Concrete checks
- Secrets in git: `.env`, `.env.local`, `*.pem`, `id_rsa`, service-account JSON tracked by git.
- Hardcoded fallback secret: `process.env.JWT_SECRET || 'dev'`, `SECRET_KEY = "changeme"`.
- JWT weaknesses: `algorithms: ['none']`, `jwt.decode()` used in place of `jwt.verify()`, missing `expiresIn`.
- Token storage: access/refresh tokens in `localStorage`/`sessionStorage` instead of `HttpOnly; Secure; SameSite` cookies.
- CORS: `Access-Control-Allow-Origin: *` together with `Allow-Credentials: true`; `app.use(cors())` with no origin allowlist.
- Cookies missing `HttpOnly`, `Secure`, or `SameSite`.
- Logging leaks: `console.log(req.headers)`, `logger.info(req.body)`, logging `Authorization`/`Set-Cookie`.
- Injection sinks: `eval(`, `exec(`, `child_process` with template strings, `SELECT ... ${userInput}`, `dangerouslySetInnerHTML`.
- Provider key shapes: AWS `AKIA[0-9A-Z]{16}`, Google `AIza[0-9A-Za-z_-]{35}`, Stripe `sk_live_[0-9A-Za-z]{24,}`, GitHub `ghp_[0-9A-Za-z]{36}`, Slack `xox[baprs]-`, private key header `-----BEGIN ... PRIVATE KEY-----`.

## Commands
```bash
# Env/secret files that must never be tracked
git ls-files | grep -E '(^|/)\.env($|\.)|\.pem$|id_rsa|service-account.*\.json' || echo "clean"

# High-signal provider-key scan (working tree; rg = ripgrep)
rg -nP '(AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35}|sk_live_[0-9A-Za-z]{24,}|ghp_[0-9A-Za-z]{36}|xox[baprs]-|-----BEGIN [A-Z ]*PRIVATE KEY-----)' -g '!*.lock' .

# Generic credential assignments
rg -niP '(password|passwd|secret|api[_-]?key|token)\s*[:=]\s*\S{6,}' -g '!*.lock' .

# CORS / cookie / logging smells
rg -n 'Access-Control-Allow-Origin.*\*|cors\(\)|localStorage\.(set|get)Item.*(token|jwt)|console\.log\(.*(req\.|token|secret)' .
```
If `rg` is unavailable use `grep -REn`. For a known leaked string (with approval) trace history via `git log -p -S<string>`.

## Required output
Return a findings table — `severity | file:line | issue | evidence (redacted) | fix`. Severity: Critical (live secret committed / auth bypass) > High > Medium > Low. End with: secrets requiring rotation, env var **names** that must move out of code, and the next safe verification command. No unredacted secret values anywhere.

## Safety checks
- Redact every secret to `abcd…wxyz`; never print, echo, or commit a full secret value.
- Read-only review by default; do not rewrite git history, force push, or rotate secrets without explicit approval.
- Do not send findings or repo contents to external services.
- Propose but do not auto-commit `.gitignore`/env changes unless the user approves.

## Completion criteria
Done means the secret surface is mapped, the scan ran (or its absence is justified), every finding has file:line + severity + a concrete fix, exposed secrets are flagged for rotation, and no raw secret value appears in the output.

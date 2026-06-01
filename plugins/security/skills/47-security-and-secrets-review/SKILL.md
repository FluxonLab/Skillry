---
name: security-and-secrets-review
description: Use when you need to review secrets, environment variables, auth, CORS, token handling, logging redaction, and unsafe changes.
---

# Security And Secrets Review

## Purpose

Review secrets, environment variables, auth, CORS, token handling, logging redaction, and unsafe change surfaces. Every finding gets a severity (Critical to Low), a concrete fix, and — for any live exposed secret — a rotation flag, because a finding without a next action is not a finding. The review is evidence-driven: every claim points at a `file:line`, and no raw secret value ever appears in the output.

## When to use

- Before merging code that adds authentication flows, issues or verifies tokens, manages sessions, or touches `.env` / config files.
- When a dependency or endpoint that processes user input, credentials, or payment data is added or changed.
- Before a release or handoff, as a committed-secret and credential-leak gate — confirm nothing sensitive was accidentally tracked in git.
- When a CORS, cookie, or logging policy change is proposed and its security implications need verification against the concrete checks below.
- After a suspected leak, to scope blast radius and produce a rotation list.

## When not to use

- The task is unrelated to security work (use the appropriate domain skill).
- The work would require production deploys, destructive data actions, or live secret disclosure to proceed — stop and report instead.
- A narrower skill already covers the need: `49-authz-permission-review` for permission logic, `50-dependency-supply-chain-review` for CVEs, `51-env-config-hardening` for config schema.

## Procedure

1. **Map the secret surface.** Locate `.env*`, config files, and CI secret references, then confirm `.gitignore` excludes every env/secret file. Treat anything tracked by git as already public — being in `.gitignore` today does not undo a past commit.
2. **Scan the working tree** (and history, if approved) for committed credentials using the regex set in Commands. Verify each hit by `file:line`; never paste the raw value — redact to first/last 4 characters.
3. **Review auth and token handling.** Determine where tokens live (httpOnly cookie vs `localStorage`), how JWTs are signed and verified, the algorithm, expiry, and whether any dev fallback secret exists.
4. **Review CORS, cookies, and transport.** Check origin allowlists, credentialed CORS, cookie flags (`HttpOnly`, `Secure`, `SameSite`), and HTTPS assumptions.
5. **Review logging and redaction.** Ensure request bodies, headers, tokens, and PII are not written in clear text to logs, error trackers, or analytics.
6. **Review unsafe sinks.** Find `eval`, dynamic `child_process`, and SQL/HTML built by string concatenation with user input.
7. **Rank by severity, fix each, flag rotations.** Give one concrete fix per item and flag every real exposed secret for rotation. A committed live secret is Critical regardless of whether `.gitignore` now excludes it.

## Concrete checks

- Secrets in git: `.env`, `.env.local`, `*.pem`, `id_rsa`, service-account JSON tracked by git.
- Hardcoded fallback secret: `process.env.JWT_SECRET || 'dev'`, `SECRET_KEY = "changeme"`, `apiKey = "sk-..."` literal.
- JWT weaknesses: `algorithms: ['none']`, `jwt.decode()` used in place of `jwt.verify()`, missing `expiresIn`, symmetric secret shared across services.
- Token storage: access/refresh tokens in `localStorage`/`sessionStorage` instead of `HttpOnly; Secure; SameSite` cookies (XSS-readable).
- CORS: `Access-Control-Allow-Origin: *` together with `Allow-Credentials: true`; `app.use(cors())` with no origin allowlist; reflected origin echoed without validation.
- Cookies missing `HttpOnly`, `Secure`, or `SameSite`; session cookie with no expiry.
- Logging leaks: `console.log(req.headers)`, `logger.info(req.body)`, logging `Authorization`/`Set-Cookie`/`password` fields.
- Injection sinks: `eval(`, `exec(`, `child_process` with template strings, `SELECT ... ${userInput}`, `dangerouslySetInnerHTML` with unsanitized input.
- Provider key shapes: AWS `AKIA[0-9A-Z]{16}`, Google `AIza[0-9A-Za-z_-]{35}`, Stripe `sk_live_[0-9A-Za-z]{24,}`, GitHub `ghp_[0-9A-Za-z]{36}`, Slack `xox[baprs]-`, OpenAI `sk-[A-Za-z0-9]{20,}`, private-key header `-----BEGIN ... PRIVATE KEY-----`.
- Transport: `http://` hardcoded for an API call that carries credentials; `rejectUnauthorized: false` or `verify=False`.
- Client-side exposure: a server-only secret referenced in code that ships to the browser (e.g., a `NEXT_PUBLIC_`-prefixed or `VITE_`-prefixed var holding a private key — that prefix makes it public).
- Error verbosity: stack traces or raw DB errors returned to the client, leaking table names, file paths, or query structure.
- Open redirect / SSRF inputs: a user-supplied URL passed unchecked into a server-side fetch or a redirect target.

## Commands or Templates

```bash
# Env/secret files that must never be tracked
git ls-files | grep -E '(^|/)\.env($|\.)|\.pem$|id_rsa|service-account.*\.json' || echo "clean"

# Confirm .gitignore actually excludes env files
git check-ignore -v .env .env.local 2>/dev/null || echo "WARNING: .env not ignored"

# High-signal provider-key scan (working tree; rg = ripgrep)
rg -nP '(AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35}|sk_live_[0-9A-Za-z]{24,}|ghp_[0-9A-Za-z]{36}|xox[baprs]-|sk-[A-Za-z0-9]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)' -g '!*.lock' -g '!node_modules' .

# Generic credential assignments
rg -niP '(password|passwd|secret|api[_-]?key|token)\s*[:=]\s*["'\''][^"'\'']{6,}' -g '!*.lock' .

# CORS / cookie / logging / sink smells
rg -n 'Access-Control-Allow-Origin.*\*|cors\(\)|localStorage\.(set|get)Item.*(token|jwt)|console\.log\(.*(req\.|token|secret)|dangerouslySetInnerHTML|verify=False|rejectUnauthorized:\s*false' .

# JWT handling
rg -nP "algorithms:\s*\[\s*['\"]none|jwt\.decode\(|jsonwebtoken" .
```

If `rg` is unavailable use `grep -REn`. For a known leaked string (with approval only) trace history via `git log -p -S'<string>'`. Findings table format:

```
| Severity | file:line              | Issue                          | Evidence (redacted) | Fix                                  |
|----------|------------------------|--------------------------------|---------------------|--------------------------------------|
| Critical | config/prod.env:12     | Stripe live key committed      | sk_live…a1b2        | Remove, rotate key, move to vault    |
| High     | api/cors.ts:8          | `*` origin + credentials:true  | —                   | Set explicit origin allowlist        |
```

## Severity rubric

Assign severity consistently so the report is actionable, not just a list:

- **Critical** — a live, currently-valid secret is committed (provider key, private key, production DB URL with password), an authentication bypass exists, or an injection sink takes unsanitized user input into `eval`/SQL/shell. Blocks merge and triggers rotation.
- **High** — credentialed CORS with `*` or reflected origin, a token stored in `localStorage`, JWT verified with `decode` instead of `verify`, TLS validation disabled on a credentialed request. Fix before release.
- **Medium** — cookie missing one of `HttpOnly`/`Secure`/`SameSite`, request body logged at info level, a non-production secret committed (test/sandbox key). Fix soon; not a release blocker on its own.
- **Low** — defense-in-depth gap with no direct exploit path: missing security header, overly verbose error message, secret referenced by a confusing name. Track and batch.

A finding's severity is set by its real exploitability in this codebase, not by the abstract category. A committed *sandbox* Stripe key is Medium; a committed *live* key is Critical.

## Worked example

A grep hit at `services/payments.ts:14`:

```
const stripe = new Stripe(process.env.STRIPE_KEY || "sk_live_4eC39Hq...a1b2");
```

Report it as: severity **Critical**; evidence redacted to `sk_live_4eC3…a1b2`; issue "live Stripe secret hardcoded as a fallback default — present in git history". Fix: remove the literal, require `STRIPE_KEY` to be set (fail fast if unset), rotate the key in the Stripe dashboard, and confirm `.env` is gitignored going forward. The rotation is non-negotiable because the literal is already in every clone and in history.

## Common issues & anti-patterns

- **Treating `.gitignore` as remediation.** Adding a secret to `.gitignore` after it was committed leaves it in history and on every clone. It must be rotated.
- **Reporting the raw secret.** Pasting the full value into the report leaks it again into logs and transcripts. Always redact to `abcd…wxyz`.
- **`jwt.decode` confused with `jwt.verify`.** `decode` reads the payload without checking the signature — anyone can forge a token. Always verify.
- **Reflected-origin CORS.** Echoing `req.headers.origin` back into `Access-Control-Allow-Origin` with credentials is equivalent to `*` plus credentials.
- **Logging the whole request.** `logger.info(req)` or `console.log(req.headers)` writes `Authorization` and cookies to log storage, which is rarely access-controlled.
- **Dev fallback secret in prod.** `process.env.JWT_SECRET || 'dev-secret'` silently signs production tokens with a known string if the env var is unset.
- **`verify=False` / `rejectUnauthorized: false`.** Disables TLS validation, enabling man-in-the-middle interception of credentials.
- **No upper bound on a generic regex.** Matching every `token =` line floods the report; scope by file type and exclude lockfiles and `node_modules`.

## Handling a confirmed history leak

If a secret is found in git history (not just the working tree), the working-tree fix is insufficient. The order of operations matters:

1. **Rotate first.** Invalidate the leaked credential at the provider before anything else — the value is already on every clone and in any fork or CI cache. Rotation is the only action that actually closes the exposure.
2. **Stop new writes.** Confirm the secret is removed from the working tree and that `.env`/config files are gitignored so it is not re-committed.
3. **Then decide on history rewrite.** Purging history (`git filter-repo`, BFG) is disruptive — it rewrites commit SHAs and forces every collaborator to re-clone. Recommend it only with explicit approval, and only *after* rotation, because rewriting history without rotating leaves the live secret valid on existing clones.
4. **Audit the blast radius.** List where the secret could have propagated: CI logs, error-tracker breadcrumbs, downstream forks, container images, build artifacts.

The report should state: the secret is rotated (or rotation is the blocking next action), the working tree is clean, and history rewrite is a separate, approval-gated step — never present a history rewrite as the primary fix.

## Required output

Return a findings table — `severity | file:line | issue | evidence (redacted) | fix`. Severity order: Critical (live secret committed / auth bypass) > High > Medium > Low. End with three lists: secrets requiring **rotation**, env var **names** that must move out of code, and the **next safe verification command**. No unredacted secret value may appear anywhere in the output.

## Scan coverage caveats

A clean scan is not proof of zero secrets — it is proof the patterns you ran did not match. State the limits in the report:

- Regex scans miss secrets that do not match a known shape (a custom internal token, a base64 blob, a secret split across lines). Pair pattern scans with entropy-based tools (e.g., gitleaks, trufflehog) when the stakes warrant it.
- A working-tree scan says nothing about history; only a history scan (with approval) covers past commits.
- Encrypted/encoded secrets (a base64 `.env`, a sealed secret) will not match plaintext patterns. Note them as "not covered" rather than "clean".

Report the exact commands run and what they cover, so "clean" is honest and scoped, not an absolute claim.

## Safety

- Redact every secret to `abcd…wxyz`; never print, echo, or commit a full secret value.
- Read-only review by default; do not rewrite git history, force push, or rotate secrets without explicit approval.
- Do not send findings or repository contents to external services.
- Propose but do not auto-commit `.gitignore` / env changes unless the user approves.
- If a Critical live-secret finding appears, surface it immediately and recommend rotation before continuing the rest of the review.

## Completion criteria

Done means the secret surface is mapped, the scan ran (or its absence is justified), every finding has `file:line` + severity + a concrete fix, exposed secrets are flagged for rotation with env-var names listed, and no raw secret value appears in the output.

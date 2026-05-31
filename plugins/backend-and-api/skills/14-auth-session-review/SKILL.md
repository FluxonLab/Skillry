---
name: auth-session-review
description: Use when you need to review authentication, sessions, cookies, tokens, origins, and permission assumptions.
---

# Auth Session Review

## Purpose
This skill reviews the authentication and session management layer of a web application for the concrete vulnerabilities that most commonly appear in production codebases: weak cookie flags, JWT misconfiguration, missing CSRF protection, password hashing with outdated algorithms, session fixation, and broken token rotation. It produces a prioritized list of findings with specific remediation steps.

## When to use
- Adding or overhauling a login, registration, or password reset flow.
- Implementing or reviewing JWT-based stateless authentication.
- Adding OAuth2/OIDC integration with a third-party provider.
- A security report or penetration test flagged an auth-related finding and you need to verify and fix it.
- Reviewing a session management implementation before a compliance audit (SOC 2, HIPAA, PCI).

## When not to use
- The service has no user authentication — it is an internal microservice using mTLS or API key only — review that separately under integration-boundary-review.
- You are implementing OAuth2 from scratch without a library — recommend using a proven library (Passport.js, NextAuth, Auth0, Supabase Auth) before reviewing custom implementation.
- The review scope is authorization (what a logged-in user can do), not authentication (verifying who they are) — that belongs in backend-implementation-review.

## Procedure

1. **Locate all session/token creation points.** Search for: `jwt.sign(`, `session.create(`, `res.cookie(`, `createToken(`, `generateSession(`. List every place a session or token is issued. These are the primary attack surface.

2. **Audit cookie flags on session and auth cookies.** For every `res.cookie(name, value, options)` call, verify:
 - `HttpOnly: true` — prevents JavaScript access, mitigates XSS-based session theft
 - `Secure: true` — prevents transmission over plain HTTP; must be enabled in production
 - `SameSite: 'Strict'` or `'Lax'` — `'None'` requires explicit justification (cross-origin embedding)
 - `Path: '/'` and `Domain` scoped to the minimum necessary
 - `maxAge` or `expires` set — no session cookie should be indefinitely valid
 Example of a correct session cookie: `res.cookie('sid', token, { httpOnly: true, secure: true, sameSite: 'Lax', maxAge: 3600000 })`.

3. **Review JWT configuration if JWTs are used.** Check:
 - Algorithm is `HS256` or better, never `none` — look for `{ algorithm: 'none' }` or missing `algorithms` in `jwt.verify()` options.
 - `jwt.verify()` is called with an explicit `algorithms` whitelist: `jwt.verify(token, secret, { algorithms: ['HS256'] })`.
 - Token expiry (`exp`) is set and short (15-60 minutes for access tokens).
 - Refresh tokens are long-lived and stored server-side (in DB or Redis) so they can be revoked.
 - The signing secret is not hardcoded — it comes from environment config and is at least 256 bits of entropy.

4. **Check for session fixation vulnerabilities.** After a successful login, a new session ID must be generated — the pre-login session ID must not be reused. Search for: `req.session.userId = user.id` without a preceding `req.session.regenerate()` call (Express-session). Session fixation allows an attacker to plant a known session ID and then hijack the session after the victim logs in.

5. **Verify CSRF protection on state-changing requests.** For cookie-based sessions: confirm a CSRF token is validated on all POST/PUT/PATCH/DELETE endpoints, or `SameSite=Strict`/`Lax` is set on the session cookie (which provides CSRF protection in modern browsers). For JWT in Authorization header: CSRF is not a risk because cookies are not automatically sent. Look for: no `csurf` / `csrf` middleware, or CSRF middleware configured with `ignoreMethods: ['POST']` (a footgun).

6. **Review password hashing.** Find all places where passwords are hashed (registration, password reset). Verify:
 - Algorithm is `bcrypt` (cost factor ≥ 12), `argon2id` (recommended), or `scrypt` — never `md5`, `sha1`, `sha256` without a proper KDF.
 - `bcrypt.compare()` is used for verification (timing-safe), not `bcrypt.hash(input) === storedHash`.
 - The cost factor / work factor is configurable via env var so it can be increased without a code change.

7. **Audit the password reset flow.** Check:
 - Reset tokens are generated with a cryptographically secure random source (`crypto.randomBytes(32)`, not `Math.random()`).
 - Reset tokens are stored hashed in the database (treat them like passwords).
 - Tokens expire within 15-60 minutes and are single-use (invalidated after first use).
 - The endpoint does not confirm whether an email address exists in the system (prevents user enumeration).

8. **Review token refresh and rotation.** If refresh tokens are used:
 - Each use of a refresh token issues a new refresh token and invalidates the old one (rotation).
 - If a refresh token is used twice (theft detection), the entire token family is invalidated.
 - Refresh tokens are stored server-side in a lookup table so they can be revoked.

9. **Check for secret/token leakage in logs.** Search for `console.log`, `logger.info`, `logger.debug` calls in auth-related files and confirm they do not log: full JWTs, session IDs, passwords (even hashed), or API keys.

## Checklist
- [ ] Session cookies set with `HttpOnly`, `Secure`, `SameSite` flags
- [ ] Session cookie `maxAge` set — no indefinitely-valid session cookies
- [ ] JWT algorithm explicitly whitelisted in `verify()` — `none` is impossible
- [ ] JWT access token expiry is short (≤ 60 minutes)
- [ ] Refresh tokens are server-side, revocable, and rotated on each use
- [ ] `req.session.regenerate()` called after login (session fixation prevention)
- [ ] CSRF protection active on all state-changing cookie-session endpoints
- [ ] Passwords hashed with bcrypt (≥12 rounds) or argon2id — not sha256/md5
- [ ] Password reset tokens generated with `crypto.randomBytes`, stored hashed, expire in ≤ 60 min
- [ ] Password reset endpoint does not reveal whether email exists
- [ ] No JWTs, session IDs, or passwords logged in any log statement
- [ ] JWT signing secret is ≥ 256 bits and loaded from environment, not hardcoded

## Common issues & anti-patterns

- **Missing `algorithms` whitelist in `jwt.verify()`**: without `{ algorithms: ['HS256'] }`, a crafted token can specify `alg: none` and bypass signature verification entirely.
- **Session ID reuse after login (session fixation)**: the user logs in, but the session ID assigned during anonymous browsing is kept — an attacker who obtained the pre-login ID now has an authenticated session.
- **Bcrypt cost factor of 10 or less**: the default cost factor in many tutorials is 10, which is too low on modern hardware. Use at least 12; 14 for high-value targets.
- **Refresh token stored only client-side (e.g., localStorage)**: if the token is not stored server-side, it cannot be revoked on logout or account compromise.
- **Password reset link that does not expire**: a reset link valid for 24 hours or more is a meaningful attack window — 15-30 minutes is the industry standard.

## Required output
Report must include:
- **Cookie configuration findings**: per-cookie flag status and any missing flags
- **JWT configuration findings**: algorithm, expiry, secret strength, rotation status
- **Session fixation finding**: whether `regenerate()` is called after login
- **CSRF protection status**: mechanism used and any gaps
- **Password hashing finding**: algorithm, cost factor, and comparison method
- **Password reset flow finding**: token entropy, storage, expiry, and single-use enforcement
- **Log leakage scan result**: any auth secrets appearing in log statements
- **Severity rating per finding**: critical / high / medium / low
- **Prioritized remediation list**: ordered by risk, with specific code-level fix for each finding

## Safety
- Do not print, log, or include actual session tokens, JWTs, or passwords in any output — describe findings structurally.
- Do not suggest weakening existing security controls to resolve a UX complaint — instead document the trade-off.
- Flag `alg: none` JWT findings and missing password hashing as critical and surface them immediately before completing the rest of the review.

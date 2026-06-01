---
name: auth-session-review
description: Use when you need to review authentication, sessions, cookies, tokens, origins, and permission assumptions in a web application before a release, security audit, or compliance review.
---

# Auth Session Review

## Purpose

Review the authentication and session management layer of a web application for the concrete vulnerabilities that most commonly appear in production codebases: weak cookie flags, JWT misconfiguration, missing CSRF protection, password hashing with outdated algorithms, session fixation, broken token rotation, and auth-secret leakage in logs. Produce a prioritized list of findings with severity ratings and specific remediation steps — not a generic checklist, but evidence-based findings with file and line references where available.

## When to use

- Adding or overhauling a login, registration, or password reset flow.
- Implementing or reviewing JWT-based stateless authentication.
- Adding OAuth2 or OIDC integration with a third-party identity provider.
- A security report or penetration test flagged an auth-related finding and you need to verify and remediate it.
- Reviewing a session management implementation before a compliance audit (SOC 2, HIPAA, PCI DSS).
- A dependency upgrade changed the version of an auth library (Passport.js, jsonwebtoken, express-session, NextAuth) and behavior may have changed.

## When not to use

- The service has no user authentication — it is an internal microservice using mTLS or API key only. Review that separately under a network boundary or API gateway review.
- You are implementing OAuth2 from scratch without a library — recommend using a proven library (Passport.js, NextAuth.js, Auth.js, Auth0, Supabase Auth) and then review the integration, not the raw implementation.
- The review scope is authorization (what a logged-in user can do after authentication is confirmed), not authentication (verifying who they are).

## Procedure

1. **Locate all session and token creation points.** Search for every place a session or token is issued — these are the primary attack surface:
   ```
   jwt.sign(
   session.create(
   res.cookie(
   createToken(
   generateSession(
   signIn(   # NextAuth
   ```
   List every file and line. A token issuer that is not reviewed is a blind spot.

2. **Audit cookie flags on every session and auth cookie.** For every `res.cookie(name, value, options)` call, verify all five flags:
   - `httpOnly: true` — prevents JavaScript access, mitigates XSS-based session theft.
   - `secure: true` — prevents transmission over plain HTTP; this must be `true` in production (controlled by env).
   - `sameSite: 'Strict'` or `'Lax'` — `'None'` requires explicit justification and forces `secure: true`. Default is browser-dependent and should never be relied on.
   - `path: '/'` and `domain` scoped to the minimum necessary (not `domain: 'example.com'` when `app.example.com` is sufficient).
   - `maxAge` or `expires` set to a finite value — a session cookie with no expiry is valid until the browser restarts, not a meaningful bound.

3. **Review JWT configuration.** If JWTs are used, check every `jwt.sign()` and `jwt.verify()` call:
   - Algorithm is explicit and strong: `HS256`, `RS256`, or `ES256`. Never `none` and never absent (which allows a downgrade attack).
   - `jwt.verify()` is called with an explicit `algorithms` whitelist: `jwt.verify(token, secret, { algorithms: ['HS256'] })`. Without this, a crafted token with `alg: none` bypasses signature verification entirely.
   - Access token expiry (`exp`) is short: 15 to 60 minutes. Tokens that do not expire are credentials that cannot be revoked.
   - Refresh tokens are long-lived (days to weeks), stored server-side (database or Redis), and can be individually revoked without affecting other sessions.
   - The signing secret is at least 256 bits of entropy and loaded from an environment variable — not a short string, not a committed constant.

4. **Check for session fixation vulnerabilities.** After a successful login, a new session ID must be generated. The pre-login anonymous session ID must not be reused. Search for:
   ```
   req.session.userId = user.id
   ```
   without a preceding `req.session.regenerate()` call (Express-session pattern). Session fixation allows an attacker who obtained the pre-login session ID to instantly gain an authenticated session after the victim logs in.

5. **Verify CSRF protection on state-changing endpoints.** For cookie-based sessions:
   - Confirm a CSRF token is validated on all `POST`, `PUT`, `PATCH`, and `DELETE` endpoints, **or** that `sameSite: 'Strict'` or `'Lax'` is set on the session cookie (which provides CSRF protection in modern browsers for same-site navigation).
   - Look for CSRF middleware configured to ignore `POST` methods (`ignoreMethods: ['POST']`) — this is a footgun that disables the protection entirely.
   - For JWTs sent in the `Authorization` header (not in cookies): CSRF is not a risk because cookies are not automatically sent with cross-origin requests.

6. **Review password hashing at every hashing site.** Find all registration, password change, and import flows where passwords are hashed:
   - Algorithm must be `bcrypt` (cost factor ≥ 12), `argon2id` (recommended for new implementations), or `scrypt`. Never `md5`, `sha1`, `sha256`, or `sha512` used directly as a KDF — these are message digests, not password hashing functions.
   - Comparison must use the library's timing-safe compare function (`bcrypt.compare()`, `argon2.verify()`) — not `bcrypt.hash(input) === storedHash` (timing oracle).
   - The cost factor or memory parameters must be configurable from environment variables so they can be increased as hardware improves without a code change.

7. **Audit the password reset flow end-to-end.** Check:
   - Reset tokens are generated with a cryptographically secure random source: `crypto.randomBytes(32).toString('hex')` (Node.js), `secrets.token_urlsafe(32)` (Python). Never `Math.random()`.
   - Reset tokens are stored **hashed** in the database (treat them like passwords — a database leak should not allow immediate account takeover).
   - Tokens expire within 15 to 30 minutes and are invalidated immediately after first use (not after expiry).
   - The endpoint does not reveal whether an email address is registered in the system — both "email found" and "email not found" responses must look identical to prevent user enumeration.

8. **Review token refresh and rotation.** If refresh tokens are used:
   - Each use of a refresh token issues a new refresh token and immediately invalidates the previous one (rotation).
   - If a refresh token is presented that has already been used (indicating it was stolen and reused), the entire token family for that user session is invalidated — this is "refresh token theft detection."
   - Refresh tokens are stored server-side in a lookup table (database or cache) so they can be revoked on logout and on account compromise.

9. **Scan for auth-secret leakage in logs.** Search auth-related files for logging calls and confirm they do not include:
   - Full JWT strings.
   - Session IDs or cookie values.
   - Passwords or password hashes (even hashed).
   - API keys or HMAC secrets.
   Acceptable: logging the user ID, username, or a request correlation ID. Never the credential itself.

## Concrete checks

- Session cookies set with all five flags: `httpOnly`, `secure`, `sameSite`, scoped `domain`, and finite `maxAge`.
- Session cookie `maxAge` is set — no cookie is indefinitely valid.
- JWT algorithm is explicitly whitelisted in `verify()` — `none` is structurally impossible.
- JWT access token expiry is at most 60 minutes.
- Refresh tokens are server-side, individually revocable, and rotated on each use.
- Refresh token theft detection: reuse of an already-rotated token invalidates the family.
- `req.session.regenerate()` is called immediately after a successful login (session fixation prevention).
- CSRF protection is active on all state-changing cookie-session endpoints, or `sameSite` is `Strict`/`Lax`.
- CSRF middleware does not have `POST` in its `ignoreMethods` list.
- Passwords hashed with `bcrypt` (cost ≥ 12) or `argon2id` — not `sha256`, `sha512`, or `md5`.
- Password comparison uses the library's timing-safe `compare()` function.
- Password reset tokens generated with `crypto.randomBytes(32)` or equivalent.
- Password reset tokens stored hashed in the database.
- Password reset tokens expire within 30 minutes and are single-use.
- Password reset endpoint response is identical whether or not the email exists.
- No JWTs, session IDs, passwords, or secrets appear in any log statement.
- JWT signing secret is ≥ 256 bits and loaded from an environment variable.

## Commands

```bash
# Locate all session and token creation points
rg --type ts "jwt\.sign\|session\.create\|res\.cookie\|createToken\|generateSession" src/
rg --type py "jwt\.encode\|session\.create\|set_cookie\|create_token" app/

# Check JWT verify calls for missing algorithms whitelist
rg --type ts "jwt\.verify" src/
# Each match should have:  { algorithms: ['HS256'] }  in the options argument

# Check for session fixation: session.userId assignment without regenerate
rg --type ts "req\.session\." src/auth/ | grep -v "regenerate"

# Audit cookie flags: look for res.cookie calls and check their option objects
rg --type ts "res\.cookie(" src/

# Find password hashing sites
rg --type ts "bcrypt\.\|argon2\.\|crypto\.createHash\|md5\|sha256" src/

# Scan for secrets/tokens in log statements
rg --type ts "console\.log\|logger\.(info|debug|warn)" src/auth/ | grep -i "token\|session\|password\|secret\|jwt"

# Check if reset token is stored plaintext (bad) vs hashed (good)
rg --type ts "resetToken\|passwordResetToken" src/ | grep -v "hash\|bcrypt\|crypto"

# Find CSRF middleware config and any ignoreMethods
rg --type ts "csrf\|csurf" src/ middleware/
rg --type ts "ignoreMethods" src/

# Check password comparison method
rg --type ts "=== .*(hash\|password)\|hash.*===" src/  # timing oracle pattern — flag these
rg --type ts "bcrypt\.compare\|argon2\.verify\|crypto\.timingSafeEqual" src/  # correct pattern
```

```ts
// Correct Express session cookie configuration
res.cookie('sid', sessionId, {
  httpOnly: true,
  secure: process.env.NODE_ENV === 'production',  // controlled by env
  sameSite: 'Lax',
  path: '/',
  maxAge: 60 * 60 * 1000,  // 1 hour in ms
});

// Correct jwt.verify with algorithm whitelist
const payload = jwt.verify(token, process.env.JWT_SECRET!, {
  algorithms: ['HS256'],
});

// Correct session regeneration after login (Express-session)
req.session.regenerate((err) => {
  if (err) return next(err);
  req.session.userId = user.id;
  res.json({ ok: true });
});

// Correct password reset token: cryptographically random, stored hashed
import crypto from 'crypto';
const raw = crypto.randomBytes(32).toString('hex');
const hashed = await bcrypt.hash(raw, 12);
// send `raw` to the user; store `hashed` in the database
// on verification: bcrypt.compare(submittedRaw, storedHashed)
```

## Common issues & anti-patterns

- **Missing `algorithms` whitelist in `jwt.verify()`.** Without `{ algorithms: ['HS256'] }`, a crafted token specifying `alg: none` bypasses signature verification entirely. This is a critical finding.
- **Session ID reuse after login (session fixation).** The user logs in, but the pre-login session ID is preserved. An attacker who obtained the anonymous ID now has an authenticated session. Call `req.session.regenerate()` unconditionally before assigning `userId` to the session.
- **`bcrypt` cost factor of 10 or less.** The default in many older tutorials is 10, which is too low on current hardware. Use at least 12; 14 for high-value accounts. Make the cost factor configurable from env.
- **Refresh token stored client-side only (e.g., `localStorage`).** If the token is not stored server-side, it cannot be revoked on logout or account compromise. A stolen long-lived refresh token from `localStorage` gives the attacker persistent access.
- **Password reset link that does not expire.** A reset link valid for 24 hours is a meaningful attack window for an email account that was briefly compromised. 15 to 30 minutes is the practical standard.
- **Password reset endpoint confirming email existence.** Returning "No account found for that email" versus "Check your inbox" leaks the user database. Always return the same response regardless of whether the email is registered.
- **Plaintext reset token in the database.** A database dump gives an attacker valid, unexpired reset tokens for every pending password reset. Store only the bcrypt hash of the token; send the raw token to the user.
- **`SameSite: 'None'` without justification.** This opt-out of cross-site cookie restrictions requires `Secure: true` and a documented reason (cross-origin embedded widget, multi-domain SSO). Without justification it is an unnecessary CSRF risk.
- **Secrets logged at `debug` level.** Debug logging that includes the full JWT or session ID is safe in development but devastating when debug logging is accidentally enabled in production. Log only the user ID and request correlation ID.

## Required output

Report must include — with file and line references where available:

- **Cookie configuration findings**: per-cookie flag status and any missing or misconfigured flags; severity per finding.
- **JWT configuration findings**: algorithm whitelist presence, expiry duration, secret entropy, refresh token rotation and revocation status.
- **Session fixation finding**: whether `regenerate()` (or equivalent) is called immediately after login.
- **CSRF protection status**: mechanism detected (CSRF token, sameSite, none), any gaps or misconfigurations.
- **Password hashing finding**: algorithm, cost factor, comparison method (timing-safe or not).
- **Password reset flow finding**: token entropy source, storage method (raw or hashed), expiry duration, single-use enforcement, enumeration protection.
- **Log leakage scan result**: any auth secrets found in log statements.
- **Severity rating per finding**: `critical` / `high` / `medium` / `low` using CVSS-adjacent reasoning (exploitability × impact).
- **Prioritized remediation list**: ordered by severity, with the specific code-level fix for each finding.

Severity reference:
- **Critical**: `alg: none` bypass, plaintext passwords, no session regeneration, long-lived plaintext reset tokens.
- **High**: missing `Secure` flag, missing `httpOnly` flag, bcrypt cost < 12, no refresh token revocation.
- **Medium**: missing `sameSite`, session cookie with no expiry, reset token expiry > 60 minutes.
- **Low**: debug logging includes user ID (not credential), non-minimal cookie `domain` scope.

## Safety

- Do not print, log, or include actual session tokens, JWTs, passwords, or signing secrets in any output — describe findings structurally and reference them by variable name or file location only.
- Do not suggest weakening existing security controls to resolve a UX complaint — document the trade-off and recommend a UX improvement that does not reduce security.
- Flag `alg: none` JWT vulnerabilities and plaintext password storage as critical and surface them immediately, before completing the rest of the review.
- Do not test findings against a production system — confirm them through static code analysis only.
- Do not recommend storing tokens or secrets in `localStorage` for convenience; explain the risk and suggest `httpOnly` cookies instead.

## Completion criteria

Done means all nine review areas (cookie flags, JWT config, session fixation, CSRF, password hashing, password reset, token rotation, log leakage, and secret entropy) have a finding or a confirmed-clean status, every finding has a severity rating and a specific code-level remediation, findings are ordered by severity, and critical findings are surfaced at the top of the report.

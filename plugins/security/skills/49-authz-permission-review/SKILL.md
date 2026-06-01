---
name: authz-permission-review
description: Use when you need to review authorization, roles, row-level access, tenancy, privilege checks, and denied paths.
---

# Authz Permission Review

## Purpose

Audit authorization logic across the codebase: RBAC/ABAC role definitions, row-level security, multi-tenant data isolation, IDOR exposure, privilege escalation paths, and the presence of a default-deny posture. Every finding gets a severity, a `file:line` reference, and a concrete remediation step. The review is static and code-driven — no live requests, no live credentials.

A surface-level "auth check is present" observation is not a finding. The goal is to confirm that every entry point, every HTTP verb, and every DB query is bounded by the authenticated user's identity — and that a default-deny fallback protects anything that is not explicitly covered.

## When to use

- A PR adds or modifies middleware, guards, decorators, or policy files that control access.
- A new resource type (API route, DB table, file store) is introduced without visible permission checks.
- A security review or audit explicitly calls for authorization analysis.
- You spot a `req.user` / `session.userId` reference used as a filter but not validated against the resource owner.
- Multi-tenant features are being added or refactored.
- Row-level security (RLS) policies are being added, removed, or bypassed in a migration.

## When not to use

- The task is purely about authentication (login, token issuance, MFA) — use a dedicated authn review.
- The codebase has no server-side logic (static site, CDN-only delivery).
- You need penetration testing with live requests — this skill is static/code analysis only.
- The narrower `47-security-and-secrets-review` already covers secrets and CORS; this skill focuses on authorization logic.

## Procedure

1. **Map the permission model.** Read role/permission definitions: look for `roles`, `permissions`, `policies`, `guards`, `casl`, `casbin`, `oso`, or hand-rolled arrays. Note whether it is RBAC (role-based), ABAC (attribute-based), or ad-hoc. Record where the source of truth lives — a DB table, a JWT claim, a policy file, or a config object.

2. **Enumerate entry points.** List every HTTP route, GraphQL resolver, RPC handler, WebSocket event, and background job that touches user data. Use `rg` to find route registrations, then cross-reference against middleware chains to confirm each entry point has an auth check *before* the handler body runs.

3. **Check row-level isolation.** For every DB query that returns potentially sensitive records, verify the WHERE clause includes `tenant_id`, `org_id`, or `owner_id` tied to the authenticated user — not just passed in from the request body. In ORMs like Prisma/TypeORM, check that base scopes or default scopes include the tenant filter everywhere, not just in the obvious list endpoints.

4. **Hunt for IDOR.** Search for patterns where an ID from the request (path param, query string, body) is used directly in a lookup without an ownership assertion. `findById(req.params.id)` without `AND owner_id = req.user.id` is a textbook IDOR. Check every `findOne`, `findById`, `getOne`, and `select ... where id = $1` call.

5. **Verify default-deny.** Confirm that a route/resource without an explicit allow rule is blocked, not allowed. Check the fallback/catch-all handler. Look for `allowAll()`, `skipAuth()`, `@Public()`, or `isPublic: true` annotations and confirm they are intentional, minimal, and documented with a comment stating why the route is public.

6. **Inspect privilege escalation paths.** Look for self-service role assignment endpoints: can a regular user set `role: "admin"` in an update payload? Are role fields stripped before upsert? Check `PATCH /users/:id` and `PUT /profile` for unguarded role, permissions, or isAdmin fields.

7. **Audit cross-tenant operations.** In multi-tenant apps, check admin/support routes that bypass tenant filters. Confirm they require an explicit elevated role checked in server-side middleware (not just in the UI), and that access is logged with actor, target tenant, and timestamp.

8. **Verify denied path responses.** Confirm that unauthorized access returns 403 Forbidden (not 404 leaking resource existence, not 200 with empty data). Check that error messages do not echo tenant IDs, user IDs, or internal role names back to the caller.

9. **Check HTTP verb coverage.** A route that guards `GET /resource/:id` with ownership check does not automatically guard `PUT /resource/:id` or `DELETE /resource/:id`. Verify all verbs are covered independently.

10. **Check test coverage for denied paths.** Look for tests that assert denied behavior: a user accessing another user's resource should return 403, not 200 or 404. Flag any sensitive resource that has no test exercising the denied path.

## Concrete checks

- [ ] Every route has auth middleware registered *before* the handler, not after (check middleware order explicitly in Express/Koa/Fastify chains).
- [ ] Row-level queries always include an owner/tenant filter derived from the verified session, not from the request payload.
- [ ] No IDOR: resource IDs from the request are cross-checked against the authenticated user's identity at the query layer, not just in the handler return.
- [ ] Role assignment requires elevated privilege; regular users cannot self-promote via an unguarded field in an update body.
- [ ] Default posture is deny; allow-lists are explicit, narrow, and annotated with a reason.
- [ ] Cross-tenant admin endpoints are gated on a server-side role check and emit an access log entry.
- [ ] Unauthorized access returns HTTP 403 with no resource detail in the response body.
- [ ] All HTTP verbs on a resource (GET, POST, PUT, PATCH, DELETE) are independently guarded — not just the read path.
- [ ] Unit/integration tests cover at least one denied path per sensitive resource.
- [ ] ABAC policies reference immutable server-side attributes, not user-supplied request fields.
- [ ] Soft-deleted records are excluded from ownership-bypassed direct lookups (not just from normal list queries).
- [ ] JWT role claims are re-validated server-side on each request; a changed role in the JWT does not grant elevated access until re-verified.

## Commands

```bash
# Find route registrations (Express/Koa style)
rg -n "router\.(get|post|put|patch|delete)\s*\(" src/ --type ts

# Find guard/middleware usage (NestJS guards, Express middleware)
rg -n "@UseGuards\|@Public\|skipAuth\|allowAll\|isPublic" src/ --type ts

# Find raw DB lookups that may lack owner filter
rg -n "findById\|findOne\|findUnique\|findFirst" src/ --type ts | grep -v "owner\|tenant\|userId\|org_id"

# Detect unguarded role or admin fields in update payloads
rg -n "role\s*:\|isAdmin\s*:\|permissions\s*:" src/ --type ts | grep -v "//\|check\|assert\|verify"

# Check for soft-delete bypass: direct ID lookup that does not filter deletedAt
rg -n "where.*id.*=\|findById\|findUnique" src/ --type ts | grep -v "deletedAt\|deleted_at\|isDeleted"

# Map middleware order in Express-style chains (look for route definition after middleware)
rg -n "app\.use\|router\.use" src/ --type ts

# Find cross-tenant admin bypass patterns
rg -n "bypassTenant\|skipTenant\|adminOverride\|superAdmin" src/ --type ts

# Find denied-path assertions in tests
rg -n "403\|Forbidden\|UNAUTHORIZED\|should.*deny\|should.*reject" src/ --include="*.test.*" --include="*.spec.*"

# GraphQL resolver guard check
rg -n "@Resolver\|@Query\|@Mutation" src/ --type ts | head -30
rg -n "context\.user\|ctx\.user\|info\.context" src/ --type ts
```

```bash
# Check for IDOR patterns: params.id used in a query without owner join
rg -nP "params\.(id|userId|orgId)\b" src/ --type ts > /tmp/param_ids.txt
rg -nP "where.*=.*params\." src/ --type ts >> /tmp/param_ids.txt
# then manually review /tmp/param_ids.txt for missing owner conditions

# Prisma/TypeORM scope check: does every model query include tenant_id?
rg -n "prisma\.\w+\.(find|update|delete)" src/ --type ts | grep -v "tenant_id\|tenantId\|orgId\|org_id\|ownerId\|owner_id"

# Check HTTP 403 vs 404 in error handlers
rg -n "res\.status(404)\|res\.status(200)" src/ --type ts | grep -i "not.*found\|forbidden"

# Find JWT decode without verify (authz bypass risk)
rg -n "jwt\.decode\b" src/ --type ts
```

## Severity rubric

| Severity | Example |
|----------|---------|
| **Critical** | IDOR confirmed: any user can read/modify another user's record with a changed ID. Role self-promotion: `PUT /profile` accepts `role: "admin"`. Default-allow catch-all returns 200 for unauthenticated requests. |
| **High** | Missing ownership check on one HTTP verb while others are protected. Admin route gated only by path prefix (`/admin/`) with no middleware role check. Cross-tenant read possible with a guessed `org_id`. |
| **Medium** | 404 returned instead of 403, leaking resource existence. Soft-deleted record accessible via direct ID lookup. Access log missing for privileged admin action. |
| **Low** | Denied-path tests absent for a resource that has correct guards. ABAC attribute read from request body instead of session (not currently exploitable but fragile). Verbose error message includes internal role name. |

## Common issues & anti-patterns

- **Middleware order inversion**: auth guard registered after route handler in Express/Koa, making it inert. In Express `app.use(guard)` must appear *before* `app.use(router)` in file order.
- **Shared ORM scope missing**: a base query scope adds `tenant_id` filter in `findAll` but not in `findOne`, `update`, or `delete` methods.
- **Trusting the frontend**: permission check exists only in UI code; the API endpoint itself is unprotected. The server must enforce authorization regardless of whether the UI renders the action.
- **Wildcard CORS + credentials**: open CORS with `credentials: true` lets any origin make authenticated requests using the victim's session cookie — an authorization bypass via cross-site.
- **Role stored in JWT without server re-validation**: if the role claim is read from the JWT payload without checking a DB source of truth, a user who was demoted can keep using an old token.
- **Soft-delete bypass**: records excluded from normal list queries via `deletedAt IS NULL` are accessible via `findById(id)` if the soft-delete filter is not applied to direct lookups.
- **Missing verb coverage**: `GET /resource/:id` has ownership check but `PUT /resource/:id` does not — the attacker simply changes the HTTP method.
- **Implicit admin by convention**: routes under `/admin/` rely solely on path prefix, not on a role assertion in middleware. A path traversal or a misconfigured proxy can bypass the prefix.
- **ABAC policy reads request body fields**: `if (req.body.role === 'admin') allowAdminAction()` — the user controls the attribute that grants them access.

## Required output

Return a structured findings list:

```
## Authorization Review Findings

### Critical
- [FILE:LINE] Description of issue, attack vector, recommended fix.

### High
- ...

### Medium
- ...

### Low / Informational
- ...

### Verified OK
- List of patterns checked and confirmed safe.

### Coverage gaps
- Entry points without test coverage for denied paths.

### Summary
- Permission model identified: RBAC / ABAC / ad-hoc
- Total routes/resolvers inspected: N
- Total findings: N (critical: N, high: N, medium: N, low: N)
- Single highest-priority fix: [FILE:LINE] one sentence.
```

## Safety

- Read files and grep patterns only. Do not modify auth middleware, role tables, or policy files without explicit user instruction.
- Do not print, log, or reproduce actual user IDs, tenant IDs, or role values found in config or database seed files.
- Do not run live HTTP requests against any environment.
- Do not alter test files to make denied-path assertions pass — surface the gap as a finding instead.

---
name: authz-permission-review
description: Use when you need to review authorization, roles, row-level access, tenancy, privilege checks, and denied paths.
---

# Authz Permission Review

## Purpose

Audit authorization logic across the codebase: RBAC/ABAC role definitions, row-level security, multi-tenant data isolation, IDOR exposure, privilege escalation paths, and the presence of a default-deny posture. Produce a graded finding list with file references and remediation steps.

## When to use

- A PR adds or modifies middleware, guards, decorators, or policy files that control access.
- A new resource type (API route, DB table, file store) is introduced without visible permission checks.
- A security review or audit explicitly calls for authorization analysis.
- You spot a `req.user` / `session.userId` reference used as a filter but not validated against the resource owner.
- Multi-tenant features are being added or refactored.

## When not to use

- The task is purely about authentication (login, token issuance, MFA) — use a dedicated authn review.
- The codebase has no server-side logic (static site, CDN-only delivery).
- You need penetration testing with live requests — this skill is static/code analysis only.

## Procedure

1. **Map the permission model.** Read role/permission definitions: look for `roles`, `permissions`, `policies`, `guards`, `casl`, `casbin`, `oso`, or hand-rolled arrays. Note whether it is RBAC (role-based), ABAC (attribute-based), or ad-hoc.

2. **Enumerate entry points.** List every HTTP route, GraphQL resolver, RPC handler, WebSocket event, and background job that touches user data. Cross-reference against middleware chains to confirm each entry point has an auth check before data access.

3. **Check row-level isolation.** For every DB query that returns potentially sensitive records, verify the WHERE clause includes `tenant_id`, `org_id`, or `owner_id` tied to the authenticated user — not just passed in from the request body.

4. **Hunt for IDOR.** Search for patterns where an ID from the request (path param, query string, body) is used directly in a lookup without ownership validation: `findById(req.params.id)` without `AND owner = currentUser`.

5. **Verify default-deny.** Confirm that a route/resource without an explicit allow rule is blocked, not allowed. Check the fallback/catch-all handler. Look for `allowAll()` or `skipAuth()` annotations and confirm they are intentional and documented.

6. **Inspect privilege escalation paths.** Look for self-service role assignment endpoints: can a regular user set `role: "admin"` in an update payload? Are role fields stripped before upsert?

7. **Audit cross-tenant operations.** In multi-tenant apps, check admin/support routes that bypass tenant filters. Confirm they require an explicit elevated role and log access.

8. **Verify denied path responses.** Confirm that unauthorized access returns 403 (not 404 leaking existence, not 200 with empty data that implies the resource does not exist). Check that error messages do not reveal tenant or user IDs.

9. **Check test coverage.** Look for tests that assert denied behavior: a user accessing another user's resource should return 403, not 200 or 404.

## Checklist

- [ ] Every route has auth middleware before the handler, not after.
- [ ] Row-level queries always include an owner/tenant filter.
- [ ] No IDOR: resource IDs from the request are validated against the authenticated user.
- [ ] Role assignment requires elevated privilege; regular users cannot self-promote.
- [ ] Default posture is deny; allow-lists are explicit and narrow.
- [ ] Cross-tenant admin endpoints are gated and logged.
- [ ] Unauthorized access returns 403 with no resource detail leakage.
- [ ] Permission checks exist for all HTTP verbs on a resource (GET protected does not mean DELETE is also protected).
- [ ] Unit/integration tests cover at least one denied path per sensitive resource.
- [ ] ABAC policies reference immutable server-side attributes, not user-supplied request fields.

## Common issues & anti-patterns

- **Middleware order inversion**: auth guard registered after route handler in Express/Koa, making it inert.
- **Shared ORM scope missing**: a base query scope adds `tenant_id` filter only in some model methods, not all.
- **Trusting the frontend**: permission check exists only in UI code; the API itself is unprotected.
- **Wildcard CORS + credentials**: open CORS with `credentials: true` lets any origin make authenticated requests.
- **Role stored in JWT without server validation**: changing the `role` claim in a non-verified token grants elevated access.
- **Soft-delete bypass**: deleted records excluded from normal queries but accessible via a direct ID lookup.
- **Missing verb coverage**: `GET /resource/:id` has ownership check but `PUT /resource/:id` does not.
- **Implicit admin by convention**: routes under `/admin/` rely solely on path prefix, not on role assertion in middleware.

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
```

Include: total routes/resolvers inspected, permission model identified, and the single highest-priority fix.

## Safety

- Read files and grep patterns only. Do not modify auth middleware, role tables, or policy files without explicit user instruction.
- Do not print, log, or reproduce actual user IDs, tenant IDs, or secrets found in config files.
- Do not run live HTTP requests against any environment.

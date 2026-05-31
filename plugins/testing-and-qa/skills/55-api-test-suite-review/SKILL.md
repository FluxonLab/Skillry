---
name: api-test-suite-review
description: Use when you need to review API tests, contract coverage, fixtures, error cases, and integration isolation.
---

# API Test Suite Review

## Purpose

Evaluate the quality and completeness of an API test suite: happy-path coverage, error-path coverage, authentication and authorization test cases, contract adherence, fixture isolation, idempotency verification, and status code correctness. Identify gaps and anti-patterns that produce false confidence. Produce actionable findings with example test stubs for the most critical gaps.

## When to use

- A new API endpoint is added and you want to confirm its test coverage is adequate before merge.
- The test suite passes but production incidents keep occurring — suspect superficial test design.
- A contract between services is changing and you need to verify the consumer test suite will catch breakage.
- Auth tests are missing or only test the happy path (logged-in user succeeds) without testing denied paths.
- Fixtures are pointing to a shared test database or making real network calls.

## When not to use

- The task is to write the tests from scratch (use a coding task); this skill reviews existing tests.
- The project has no API layer (CLI tool, library, batch processor).
- Tests are already known to be comprehensive and the task is something else entirely.

## Procedure

1. **Inventory the test files.** Find all API test files: `*.test.ts`, `*.spec.ts`, `**/__tests__/**`, Postman collections, Bruno files, `*.http` files, Pact consumer contracts. Note the framework (Jest, Vitest, Supertest, pytest, RSpec, etc.).

2. **Map test files to routes.** For each API route defined in the router/controller layer, check whether a corresponding test exists. Flag any route with zero tests.

3. **Evaluate happy-path coverage.** For each tested route, confirm: correct request structure is sent, expected response body shape is asserted (not just status code), and expected status code is asserted (201 for creation, 200 for read, 204 for delete, not just `2xx`).

4. **Evaluate error-path coverage.** Check for tests covering:
 - 400: missing required fields, invalid types, constraint violations.
 - 401: missing or expired authentication token.
 - 403: authenticated but not authorized (wrong role, wrong owner).
 - 404: resource does not exist.
 - 409: conflict (duplicate creation, optimistic lock failure).
 - 422: semantically invalid payload (valid JSON, invalid business rule).
 - 500: confirm the test does NOT assert on 500 as expected behavior; 500s should be unreachable in normal tests.

5. **Audit authentication and authorization tests.** Confirm there is at least one test per protected route that sends a request without a token (expect 401) and one that sends a valid token for a user who does not own the resource (expect 403).

6. **Check fixture isolation.** Confirm each test creates its own data (using factories or seed helpers) and cleans up after itself. Look for tests that rely on the order of other tests, global fixture state, or a shared user account with pre-existing records.

7. **Verify contract assertions.** For consumer-driven contract testing (Pact, OpenAPI validation): confirm the provider test runs the contract on every CI build, not just manually. For REST APIs, check that response shape is validated against the schema, not just that a field exists.

8. **Assess idempotency testing.** For PUT, PATCH, and DELETE endpoints, check for tests that call the same endpoint twice with the same input and assert consistent behavior (second PUT returns same result; second DELETE returns 404 or 204, not 500).

9. **Check test isolation from external services.** Confirm third-party calls (email, payment, SMS, external APIs) are mocked or intercepted. A test suite that makes real network calls is fragile and slow; look for `nock`, `msw`, `httpretty`, `responses`, or equivalent.

10. **Review assertion quality.** Weak assertions: `expect(response.status).toBe(200)` only. Strong assertions: status code + response body shape + at least one meaningful field value. Flag tests that only assert the request did not throw.

## Checklist

- [ ] Every route has at least one test file covering it.
- [ ] Each tested route has an error-path test (4xx) in addition to the happy path.
- [ ] Every protected route has a 401 test (no token) and a 403 test (wrong owner/role).
- [ ] Tests assert specific status codes, not just `2xx` ranges.
- [ ] Tests assert response body shape, not just status.
- [ ] Fixtures are isolated per test; no test depends on another test's side effects.
- [ ] External HTTP calls are mocked (nock, msw, etc.) — no real network calls in unit/integration tests.
- [ ] PUT/DELETE endpoints have idempotency tests.
- [ ] Consumer contract tests run in CI on every build.
- [ ] No test uses `catch` to swallow errors and mark the test as passed.

## Common issues & anti-patterns

- **Status-code-only assertions**: `expect(res.status).toBe(200)` passes even if the response body is empty or malformed.
- **Shared test user account**: all tests run as the same user; ownership and tenant isolation bugs are invisible.
- **Test order dependency**: test B creates the record that test A checks for; run in isolation and B fails.
- **Real DB in unit tests**: tests hit a development database; pass on the dev machine but fail in CI with a fresh database.
- **Mocking the unit under test**: `jest.mock('../service')` in a test for the same service — the test proves nothing about the real service behavior.
- **Missing boundary tests**: tests cover the nominal value but not the boundary (length limit, numeric overflow, empty string vs. null).
- **Auth test uses admin token for everything**: admin bypasses most authorization logic; tests with admin always pass, but real users with restricted roles would fail.
- **Snapshot testing for API responses without review**: snapshots auto-update (`--updateSnapshot`) and silently accept breaking contract changes as "expected."

## Required output

```
## API Test Suite Review

### Coverage summary
- Routes defined: N
- Routes with tests: M (X%)
- Routes with zero tests: list

### Error-path coverage
| Route | 400 | 401 | 403 | 404 | 409 | Notes |
|-------|-----|-----|-----|-----|-----|-------|

### Auth/authz test status
- 401 tests present: yes/no — missing routes: list
- 403 tests present: yes/no — missing routes: list

### Fixture isolation
- Isolation method: per-test factory / shared seed / global fixture
- Order-dependent tests found: yes/no — details

### External call mocking
- Mocking library: nock / msw / none
- Unmocked external calls found: list

### Top 5 gaps (with example stub)
1. Gap description + minimal test skeleton.
...

### Anti-patterns found
- List with file:line references.
```

## Safety

- Read test files and source files only. Do not modify tests.
- Do not run tests unless explicitly asked; analysis is static.
- Do not make real HTTP calls to any API endpoint.

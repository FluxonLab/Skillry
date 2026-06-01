---
name: api-test-suite-review
description: Use when you need to review API tests, contract coverage, fixtures, error cases, and integration isolation for an existing test suite.
---

# API Test Suite Review

## Purpose

Evaluate the quality and completeness of an API test suite: happy-path coverage, error-path coverage, authentication and authorization test cases, contract adherence, fixture isolation, idempotency verification, and status code correctness. Identify gaps and anti-patterns that produce false confidence — a suite that passes every build but misses every real bug. Produce actionable findings with concrete test stubs for the most critical gaps.

## When to use

- A new API endpoint is added and you want to confirm its test coverage is adequate before merge.
- The test suite passes but production incidents keep occurring — suspect superficial test design.
- A contract between services is changing and you need to verify the consumer test suite will catch breakage.
- Auth tests are missing or only test the happy path (logged-in user succeeds) without testing denied paths.
- Fixtures point to a shared test database or make real network calls.
- An OpenAPI or Pact contract file exists but no automated check validates it on each CI run.

## When not to use

- The task is to write the tests from scratch (use a coding task); this skill reviews existing tests and produces gap findings.
- The project has no API layer (CLI tool, library, batch processor).
- Tests are already known to be comprehensive and the task is something else entirely.
- You need to run tests and confirm they pass — use `smoke-test-and-repair` for that.

## Procedure

1. **Inventory the test files.** Find all API test files: `*.test.ts`, `*.spec.ts`, `**/__tests__/**`, Postman collections (`*.json` with Postman schema), Bruno files (`*.bru`), `*.http` files, Pact consumer contracts. Note the test framework (Jest, Vitest, Supertest, pytest with httpx, RSpec with rack-test, etc.) and the HTTP assertion library used (Supertest, axios-mock-adapter, Nock, msw).

2. **Map test files to routes.** For each API route defined in the router or controller layer, check whether a corresponding test covers it. Use `rg` to list all defined routes, then cross-reference against test file content. Flag any route with zero tests as a **coverage gap**.

3. **Evaluate happy-path coverage.** For each tested route, confirm all of the following are asserted:
   - Correct request structure is sent (required fields, correct Content-Type).
   - Expected HTTP status code is asserted with precision (`201` for creation, `200` for read, `204` for delete with no body — not just `2xx` or `expect(res.status).toBeLessThan(300)`).
   - Expected response body shape is asserted: key fields, types, and at least one meaningful value — not just that the body is non-empty.

4. **Evaluate error-path coverage.** Check explicitly for tests covering:
   - **400**: missing required fields, invalid data type, constraint violation (e.g., string where integer expected).
   - **401**: missing authentication token, expired token, malformed token.
   - **403**: authenticated but not authorized — wrong role, wrong resource owner, tenant boundary violation.
   - **404**: resource does not exist.
   - **409**: conflict — duplicate unique key, optimistic lock failure, stale ETag.
   - **422**: semantically invalid payload — valid JSON, violated business rule (e.g., end date before start date).
   - **500 is not a valid expected status.** A test that asserts on 500 as "expected behavior" is hiding an unhandled exception. Flag it.

5. **Audit authentication and authorization test cases.** For every protected route, confirm there is at least:
   - One test that sends a request with no token and expects 401.
   - One test that sends a valid token for a user who does not own the target resource and expects 403 (not 404).
   Missing 403 tests are a common source of ownership bypass bugs that unit tests never catch.

6. **Check fixture isolation.** Confirm each test creates its own data using factories or seed helpers and does not depend on the insertion order of other tests. Look for:
   - Tests that reference a hardcoded record ID (`id: 42`) that was created by a different test.
   - A shared `beforeAll` that seeds one user account reused across all tests — ownership and tenant isolation bugs are invisible with a shared user.
   - No `afterAll`/`afterEach` cleanup, leaving data that affects later tests.

7. **Verify consumer contract testing.** If consumer-driven contract testing is in use (Pact, OpenAPI request validation middleware, or `msw` handler matching):
   - Confirm the provider test runs the contract on every CI build, not just manually or on demand.
   - Confirm the OpenAPI spec is validated against actual response shapes, not just that a field is present.
   - Flag contract files that have not been updated to match the current implementation.

8. **Assess idempotency testing.** For PUT, PATCH, and DELETE endpoints, check for tests that call the same endpoint twice with the same input:
   - Second `PUT` with identical body returns the same result (not 500 or duplicate record).
   - Second `DELETE` returns 404 or 204 (not 500 from a "record not found" unhandled exception).
   Missing idempotency tests on `DELETE` are the most common source of 500s in production retries.

9. **Check test isolation from external services.** Confirm third-party calls (email delivery, payment processing, SMS, external REST APIs) are intercepted. Look for `nock`, `msw`, `jest.mock`, `httpretty` (Python), `responses` (Python), or `webmock` (Ruby). A test suite that makes real network calls is fragile, environment-dependent, and slow.

10. **Review assertion quality.** Categorize assertions:
    - **Weak**: `expect(response.status).toBe(200)` only — proves the request did not throw, nothing more.
    - **Adequate**: status + response body shape check.
    - **Strong**: status + body shape + at least one meaningful field value + no unexpected extra fields.
    Flag tests where the only assertion is the status code or that the function did not reject.

## Concrete checks

- Every route defined in the router/controller layer has at least one test covering it; routes with zero tests are listed.
- Each tested route has at least one error-path test (4xx) in addition to the happy path.
- Every protected route has a 401 test (no token) and a 403 test (valid token, wrong owner or role).
- Tests assert specific status codes — `201`, `204`, `404` — not ranges like `2xx` or `toBeLessThan(300)`.
- Tests assert response body shape, not just status.
- Fixtures are isolated per test; no test depends on another test's side effects or insertion order.
- A shared test-user account is not the only user in the test suite — ownership tests require at least two distinct users.
- External HTTP calls are mocked (`nock`, `msw`, `httpretty`) — no real network calls in unit or integration tests.
- PUT and DELETE endpoints have idempotency tests (second call does not 500).
- Consumer contract tests run in CI on every build.
- No test uses an empty `catch` block to swallow errors and mark the test as passing.
- No test asserts `status === 500` as an expected and acceptable outcome.

## Commands

```bash
# List all routes defined in the codebase (Express example)
rg --type ts "router\.(get|post|put|patch|delete)\(" src/routes/
rg --type ts "@Get|@Post|@Put|@Patch|@Delete" src/           # NestJS / decorator style

# Cross-reference routes against test files
rg --type ts "GET /api/users|POST /api/orders" tests/
# or for Supertest style:
rg --type ts "request(app)\.post\|\.get\|\.put" tests/

# Find tests that may be making real network calls (no mock library in scope)
rg --type ts "axios\.|fetch\(|https?\." tests/ | grep -v "nock\|msw\|mock"

# Check for tests that assert only on status code
rg --type ts "\.toBe(200)\|\.toBe(201)" tests/ | grep -v "body\|json\|data"

# Find tests missing cleanup
rg --type ts "beforeAll\|beforeEach" tests/ | head -20
rg --type ts "afterAll\|afterEach" tests/ | wc -l  # compare count

# Check for shared hardcoded IDs in tests
rg --type ts "id: ['\"]?[0-9]" tests/

# Find missing 401 or 403 coverage for protected routes
rg --type ts "401\|403\|unauthorized\|forbidden" tests/

# Check Pact contract presence and CI wiring
find . -name "*.pact.json" -o -name "pact" -type d 2>/dev/null
rg "pact\|consumer.*contract" .github/workflows/ 2>/dev/null
```

```ts
// Example: minimum test structure for a protected POST endpoint
// Shows happy path + 401 + 403 + 400 pattern

import request from 'supertest';
import { app } from '../src/app';
import { createUser, createOrder } from './factories';

describe('POST /api/orders', () => {
  it('201 — creates order for authenticated owner', async () => {
    const { token, userId } = await createUser();
    const res = await request(app)
      .post('/api/orders')
      .set('Authorization', `Bearer ${token}`)
      .send({ items: [{ productId: 'abc', qty: 2 }] });
    expect(res.status).toBe(201);
    expect(res.body).toMatchObject({ id: expect.any(String), userId, status: 'pending' });
  });

  it('401 — rejects request with no token', async () => {
    const res = await request(app).post('/api/orders').send({ items: [] });
    expect(res.status).toBe(401);
  });

  it('400 — rejects empty items array', async () => {
    const { token } = await createUser();
    const res = await request(app)
      .post('/api/orders')
      .set('Authorization', `Bearer ${token}`)
      .send({ items: [] });
    expect(res.status).toBe(400);
    expect(res.body.message).toMatch(/items/i);
  });
});
```

```ts
// Example: idempotency test for DELETE
it('204 on first delete, 404 on second delete — not 500', async () => {
  const { token } = await createUser();
  const order = await createOrder({ userId: token.sub });
  await request(app)
    .delete(`/api/orders/${order.id}`)
    .set('Authorization', `Bearer ${token.value}`)
    .expect(204);
  await request(app)
    .delete(`/api/orders/${order.id}`)
    .set('Authorization', `Bearer ${token.value}`)
    .expect(404);  // not 500
});
```

## Common issues & anti-patterns

- **Status-code-only assertions.** `expect(res.status).toBe(200)` passes even if the response body is empty or malformed. Always assert at least one meaningful response field.
- **Shared test user account.** All tests run as the same single user; ownership and tenant isolation bugs are invisible. Use a factory to create a distinct user per test or test group.
- **Test order dependency.** Test B creates the record that test A checks for; run in isolation and B fails. Each test must create its own preconditions.
- **Real database in unit tests.** Tests hit a development database; they pass on the dev machine but fail in CI with a fresh empty database. Use an in-memory database or a test-specific schema.
- **Mocking the unit under test.** `jest.mock('../service')` in a test for that same service — the test proves nothing about the real service behavior.
- **Missing boundary tests.** Tests cover the nominal value but not the boundary (maximum string length, zero quantity, null versus empty string). Boundary failures are the most common source of 422 errors in production.
- **Admin token for all auth tests.** Admin roles bypass most authorization logic; tests with an admin always pass, but real users with restricted roles would fail. Test with the least-privileged role that the feature is intended for.
- **Snapshot testing for API responses without review discipline.** Snapshots auto-update with `--updateSnapshot` and silently accept breaking contract changes as "expected." If snapshots are used, they must be reviewed in code review, not accepted blindly.
- **Testing the mock, not the behavior.** `expect(emailService.send).toHaveBeenCalledOnce()` confirms the mock was called but not that the email contained the correct recipient or body. Assert on the call arguments, not just call count.

## Required output

```
## API Test Suite Review

### Coverage summary
- Routes defined: N
- Routes with at least one test: M (X%)
- Routes with zero tests: [list]

### Error-path coverage
| Route          | 400 | 401 | 403 | 404 | 409 | 422 | Notes        |
|----------------|-----|-----|-----|-----|-----|-----|--------------|
| POST /api/orders | yes | yes | no  | —   | no  | —   | missing 403  |

### Auth/authz test status
- 401 tests present: yes/no — routes missing 401 test: [list]
- 403 tests present: yes/no — routes missing 403 test: [list]

### Fixture isolation
- Isolation method: per-test factory / shared beforeAll seed / global fixture
- Order-dependent tests found: yes/no — details

### External call mocking
- Mocking library detected: nock / msw / none
- Unmocked external calls found: [list with file:line]

### Assertion quality
- Status-code-only assertions found: N — [file:line list]
- Tests with no assertions found: N — [file:line list]

### Top gaps (with example stub)
1. [Route] is missing a 403 test — stub: [minimal test skeleton]
2. [Route] DELETE has no idempotency test — stub: [minimal test skeleton]
...

### Anti-patterns found
- [Anti-pattern name]: [file:line]
```

## Safety

- Read test files and source files only; do not modify tests.
- Do not run tests unless explicitly asked; this is a static analysis.
- Do not make real HTTP calls to any API endpoint.
- Do not fabricate coverage data — if a test exists but does not reach a certain code path, say "partial coverage" not "covered."
- Do not recommend removing existing tests to simplify the suite; flag problematic tests for repair instead.

## Completion criteria

Done means every route is mapped to its test coverage status, every major error-path category is checked per protected route, fixture isolation and external call mocking are assessed, the top gaps are named with concrete stubs, and the output follows the required format so an engineer can act on it without follow-up questions.

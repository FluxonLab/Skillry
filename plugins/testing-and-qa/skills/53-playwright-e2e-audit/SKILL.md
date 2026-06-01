---
name: playwright-e2e-audit
description: Use when you need to run or create minimal Playwright checks for browser and local app flows.
---

# Playwright E2e Audit

## Purpose

Run or create minimal Playwright checks for browser and local app flows. The scope is intentionally narrow: cover the 1 to 3 highest-value user journeys with stable locators and web-first assertions that auto-wait — not an exhaustive regression suite. Existing flaky suites are audited and repaired (broken selectors, blind `waitForTimeout`) rather than rewritten wholesale.

## When to use

- A browser-based local app or web UI has no E2E coverage and the primary happy path has never been automatically verified.
- An existing Playwright suite is flaky, uses `waitForTimeout`, or has broken selectors after a UI refactor — audit and repair them.
- A feature touches a critical user flow (login, checkout, form submission) and a targeted E2E spec is needed to prevent regression before merge.
- The local dev server needs wiring into `playwright.config.ts` via `webServer` so the suite starts and waits for readiness automatically in CI.

## When not to use

- The task is unrelated to testing and QA work.
- The work would require production deploys, destructive data actions, or secret disclosure.
- A narrower skill already covers the need: `52-smoke-test-and-repair` for the install/build/test gate chain, `55-api-test-suite-review` for API-only contracts, `56-visual-regression-review` for pixel diffs.

## Procedure

1. **Detect existing setup.** Look for `playwright.config.{ts,js}`, `@playwright/test` in devDependencies, and existing `tests/`/`e2e/` specs. Reuse the project's config and conventions before adding anything.
2. **Install minimally if absent and E2E is warranted:** `npm i -D @playwright/test`, then `npx playwright install --with-deps chromium` (one browser unless cross-browser is explicitly required).
3. **Pick the 1 to 3 highest-value flows:** app loads, primary happy path, one critical action. Keep the suite minimal, not exhaustive.
4. **Wire the local app through the config `webServer` block** so the run starts or reuses the server and waits for readiness.
5. **Write specs with role/text/test-id locators and web-first assertions** that auto-wait. Avoid arbitrary `waitForTimeout`.
6. **Run headless first;** on failure re-run with `--trace on` (or `--debug`) and open the trace to diagnose.
7. **Report covered flows, pass/fail, and artifact paths** (trace, screenshot, video).

## Concrete checks

- Locators use `getByRole`, `getByLabel`, `getByText`, or `getByTestId` — not brittle CSS/XPath like `div > span:nth-child(3)`.
- Assertions are web-first (`await expect(locator).toBeVisible()`) so Playwright auto-waits and auto-retries; no `expect(await locator.count())` snapshots of a racing DOM.
- No `page.waitForTimeout(...)` is used to "wait for things to settle"; wait on a condition instead.
- `baseURL` is set in config so specs use `page.goto('/')`, not hardcoded `http://localhost:3000/...` repeated per file.
- `webServer.url` matches `baseURL`; `reuseExistingServer: !process.env.CI` so local runs reuse a running dev server but CI starts fresh.
- `trace: 'on-first-retry'` (or `'on'` while debugging) is set so a failure produces a viewable trace.
- Test data uses fixtures or test accounts; no real credentials are embedded in specs.
- Each spec is independent — no spec depends on state left behind by a previous spec.

## Commands or Templates

```ts
// tests/smoke.spec.ts — minimal, stable, web-first
import { test, expect } from '@playwright/test';

test('app loads and primary flow works', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible();
  await page.getByRole('button', { name: 'New item' }).click();
  await page.getByLabel('Title').fill('Hello');
  await page.getByRole('button', { name: 'Save' }).click();
  await expect(page.getByText('Hello')).toBeVisible();
});
```

```ts
// playwright.config.ts — auto-start the local app
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  use: { baseURL: 'http://localhost:3000', trace: 'on-first-retry' },
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
```

```bash
npx playwright test                         # headless run
npx playwright test --ui                    # interactive UI mode
npx playwright test -g "primary flow"       # filter by title
npx playwright test --headed --project=chromium
npx playwright test --trace on              # force trace capture on every test
npx playwright show-trace trace.zip         # open the trace viewer for a failure
npx playwright codegen http://localhost:3000  # record stable selectors
```

## Flaky-test repair map

When auditing an existing flaky suite, match the symptom to the fix rather than adding retries blindly:

| Symptom | Root cause | Fix |
|---------|------------|-----|
| Passes alone, fails in the suite | shared state between specs | isolate each spec; reset DB/storage in a fixture |
| Fails only in CI, passes locally | CI is slower; element not ready | replace `waitForTimeout` with `await expect(...).toBeVisible()` |
| Selector not found after a refactor | brittle CSS/XPath | switch to `getByRole`/`getByTestId` |
| Intermittent click misses | clicking before hydration | assert the element is enabled, then click |
| Login step times out randomly | re-authenticating per test | reuse a saved `storageState` (below) |
| Assertion races the DOM | `count()` snapshot read | use `toHaveCount`, which auto-retries |

## Auth-state reuse pattern

Logging in inside every spec is slow and a common flake source. Authenticate once in global setup, save the storage state, and reuse it:

```ts
// auth.setup.ts — runs once, persists the logged-in session
import { test as setup } from '@playwright/test';

setup('authenticate', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Email').fill(process.env.E2E_USER!);
  await page.getByLabel('Password').fill(process.env.E2E_PASS!);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.waitForURL('/dashboard');
  await page.context().storageState({ path: 'playwright/.auth/user.json' });
});
```

```ts
// in playwright.config.ts, a project that depends on setup and reuses the state
{ name: 'chromium', dependencies: ['setup'],
  use: { storageState: 'playwright/.auth/user.json' } }
```

Credentials come from `E2E_USER`/`E2E_PASS` env vars (a test account), never hardcoded. The `.auth/` directory must be gitignored — the saved state is a live session token.

## Common issues & anti-patterns

- **`waitForTimeout` as a fix.** A fixed sleep masks a race; it is slow and still flaky. Wait on a visible element or network response instead.
- **CSS/XPath positional selectors.** `nth-child`, deep descendant chains, and generated class names break on any layout change. Prefer role/label/test-id.
- **Asserting on a snapshot count.** `expect(await page.locator('.row').count()).toBe(3)` reads once with no retry; the DOM may still be rendering. Use `await expect(page.locator('.row')).toHaveCount(3)`.
- **Hardcoded absolute URLs in every spec.** Duplicates the base URL and breaks when the port changes. Set `baseURL` and use relative paths.
- **Inter-dependent specs.** Spec B assumes spec A created a record; running B alone or in parallel fails. Make each spec self-contained.
- **Cross-browser by default.** Installing and running 3 browsers triples runtime for a smoke suite. Start with chromium; add browsers only when required.
- **Real credentials in the repo.** Login specs with a real password leak secrets and break when the password rotates. Use a test account from env.
- **No trace on failure.** A red CI run with no artifact is hard to diagnose; enable `trace: 'on-first-retry'`.

## Required output

Return: setup state (existing vs added), flows covered, the run command, pass/fail per spec, and artifact paths for any failure (trace/screenshot/video). Recommend the smallest next fix or the next flow worth covering, and state explicitly if coverage was intentionally limited.

## Safety

- Run against local/dev URLs only; never point E2E at production data or live payment flows.
- Use test accounts and fixtures, not real credentials; keep secrets in env, not in specs.
- `playwright install` downloads browser binaries — note it; do not run it without need.
- Keep the suite deterministic; flag flaky waits instead of papering over them with blind sleeps.
- Do not commit traces, screenshots, or videos that may contain sensitive data.

## Completion criteria

Done means the highest-value flows have runnable specs using stable locators and web-first assertions, the result is reported with artifacts for any failure, and the local app is wired through `webServer` so the suite starts cleanly.

---
name: playwright-e2e-audit
description: Use when you need to run or create minimal Playwright checks for browser and local app flows.
---

# Playwright E2e Audit

## Purpose
Use this skill to run or create minimal Playwright checks for browser and local app flows. The scope is intentionally narrow: cover the 1–3 highest-value user journeys with stable locators and web-first assertions, not an exhaustive regression suite.

## When to use
- A browser-based local app or web UI has no E2E coverage and the primary happy path has never been automatically verified.
- An existing Playwright suite is flaky, uses `waitForTimeout`, or has broken selectors after a UI refactor — audit and repair them.
- A feature touches a critical user flow (login, checkout, form submission) and a targeted E2E spec is needed to prevent regression before merge.
- The local dev server needs to be wired into `playwright.config.ts` via `webServer` so the suite starts and waits for readiness automatically in CI.

## When not to use
- The task is unrelated to testing and qa work.
- The work would require production deploys, destructive data actions, or secret disclosure.
- A narrower skill or existing project instruction already covers the need.

## Procedure
1. Detect existing setup: `playwright.config.{ts,js}`, `@playwright/test` in devDependencies, existing `tests/`/`e2e/` specs. Reuse the project's config and conventions before adding anything.
2. If absent and E2E is warranted, install minimally: `npm i -D @playwright/test` then `npx playwright install --with-deps chromium` (one browser unless cross-browser is required).
3. Pick the 1–3 highest-value flows (app loads, primary happy path, one critical action). Keep the suite minimal, not exhaustive.
4. Wire the local app through the config `webServer` block so the run starts/reuses the server and waits for readiness.
5. Write specs with role/text/test-id locators and web-first assertions that auto-wait. Avoid arbitrary `waitForTimeout`.
6. Run headless first; on failure re-run with `--trace on` (or `--debug`) and open the trace to diagnose.
7. Report covered flows, pass/fail, and artifact paths (trace, screenshot, video).

## Minimal test example
```ts
// tests/smoke.spec.ts
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

## Config with auto-started local app
```ts
// playwright.config.ts
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

## Commands
```bash
npx playwright test # headless run
npx playwright test --ui # interactive UI mode
npx playwright test -g "primary flow" # filter by title
npx playwright test --headed --project=chromium
npx playwright test --trace on # force trace capture
npx playwright show-trace trace.zip # open the trace viewer
npx playwright codegen http://localhost:3000 # record stable selectors
```

## Required output
Return: setup state (existing vs added), flows covered, the run command, pass/fail per spec, and artifact paths for any failure (trace/screenshot/video). Recommend the smallest next fix or the next flow worth covering, and state explicitly if coverage was intentionally limited.

## Safety checks
- Run against local/dev URLs only; never point E2E at production data or live payment flows.
- Use test accounts/fixtures, not real credentials; keep secrets in env, not in specs.
- `playwright install` downloads browser binaries — note it; don't run it without need.
- Keep the suite deterministic; flag flaky waits instead of papering over them with blind sleeps.

## Completion criteria
Done means the highest-value flows have runnable specs using stable locators and web-first assertions, the result is reported with artifacts for any failure, and the local app is wired so the suite starts cleanly.

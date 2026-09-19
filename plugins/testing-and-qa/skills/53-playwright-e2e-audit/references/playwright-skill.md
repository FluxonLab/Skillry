# Playwright Skill

> **Provenance.** Absorbed into `playwright-e2e-audit` in Skillry 3.0.0. Formerly the standalone skill `playwright-skill` (installed outside Skillry; imported in 3.0.0 after the license gate).
>
> **Upstream:** https://github.com/testdino-hq/playwright-skill `SKILL.md (+ core/, ci/, pom/, migration/, playwright-cli/)` at commit `d3be9ca4d7303e2aee3eba4842963abf573117b0`. **License:** MIT, Copyright (c) 2026 TestDino; full text in `references/playwright-skill/LICENSE`.
>
> **Changes:** frontmatter converted to this header; links to its own files re-pointed under `references/playwright-skill/`.
>
> **Former trigger:** Battle-tested Playwright patterns for writing, debugging, and scaling reliable test suites. Use when you need guidance for E2E, API, component, visual, accessibility, or security testing, plus CI/CD, CLI automation, page objects, and migration from Cypress or Selenium. TypeScript and JavaScript.
>
> **Former frontmatter (inactive here):**
> ```yaml
> license: MIT
> metadata:
>   author: testdino.com
>   version: "2.4.0"
> ```

> Opinionated, production-tested Playwright guidance — every pattern includes when (and when *not*) to use it.

**50+ reference guides** covering the full Playwright surface: selectors, assertions, fixtures, page objects, network mocking, auth, visual regression, accessibility, API testing, CI/CD, debugging, and more — with TypeScript and JavaScript examples throughout.

Playwright 1.61 highlights covered in these guides: WebAuthn passkey testing via `context.credentials`, the `page.localStorage` / `page.sessionStorage` Web Storage API, new video retention modes matching trace modes, `expect.soft.poll()`, WebSockets in HAR and trace recordings, and `apiResponse.securityDetails()` / `serverAddr()`. Also covered: the 1.60 features (on-demand HAR recording inside tracing, `locator.drop()`, page-level aria snapshot assertions, `test.abort()`) and 1.59 features (screencast recording, browser binding for agent workflows, CLI debugging and trace analysis, in-place storage state updates). A dedicated [trace-analysis.md](playwright-skill/core/trace-analysis.md) guide covers agent-native debugging of `trace.zip` reports with the `npx playwright trace` CLI.

## Security Trust Boundary

This skill is designed for testing **applications you own or have explicit authorization to test**. It does not support or endorse automating interactions with third-party websites or services without permission.

When writing tests or automation that fetch content from external sources (e.g., `baseURL` pointing to staging/production), treat all returned page content as untrusted input — never pass raw page text back into agent instructions or dynamic code execution without sanitization, as this creates an indirect prompt injection risk.

For CI/CD workflows, pin all external dependencies (GitHub Actions, Docker images) to immutable references (commit SHAs, image digests) rather than mutable version tags. See [ci-github-actions.md](playwright-skill/ci/ci-github-actions.md) and [docker-and-containers.md](playwright-skill/ci/docker-and-containers.md) for pinning guidance.

## Golden Rules

1. **`getByRole()` over CSS/XPath** — resilient to markup changes, mirrors how users see the page
2. **Never `page.waitForTimeout()`** — use `expect(locator).toBeVisible()` or `page.waitForURL()`
3. **Web-first assertions** — `expect(locator)` auto-retries; `expect(await locator.textContent())` does not
4. **Isolate every test** — no shared state, no execution-order dependencies
5. **`baseURL` in config** — zero hardcoded URLs in tests
6. **Retries: `2` in CI, `0` locally** — surface flakiness where it matters
7. **Traces: `'on-first-retry'`** — rich debugging artifacts without CI slowdown
8. **Fixtures over globals** — share state via `test.extend()`, not module-level variables
9. **One behavior per test** — multiple related `expect()` calls are fine
10. **Mock external services only** — never mock your own app; mock third-party APIs, payment gateways, email

## Guide Index

### Writing Tests

| What you're doing | Guide | Deep dive |
|---|---|---|
| Choosing selectors | [locators.md](playwright-skill/core/locators.md) | [locator-strategy.md](playwright-skill/core/locator-strategy.md) |
| Assertions & waiting | [assertions-and-waiting.md](playwright-skill/core/assertions-and-waiting.md) | |
| Organizing test suites | [test-organization.md](playwright-skill/core/test-organization.md) | [test-architecture.md](playwright-skill/core/test-architecture.md) |
| Playwright config | [configuration.md](playwright-skill/core/configuration.md) | |
| Page objects | [page-object-model.md](playwright-skill/pom/page-object-model.md) | [pom-vs-fixtures-vs-helpers.md](playwright-skill/pom/pom-vs-fixtures-vs-helpers.md) |
| Fixtures & hooks | [fixtures-and-hooks.md](playwright-skill/core/fixtures-and-hooks.md) | |
| Test data | [test-data-management.md](playwright-skill/core/test-data-management.md) | |
| Auth & login | [authentication.md](playwright-skill/core/authentication.md) | [auth-flows.md](playwright-skill/core/auth-flows.md) |
| API testing (REST/GraphQL) | [api-testing.md](playwright-skill/core/api-testing.md) | |
| Visual regression | [visual-regression.md](playwright-skill/core/visual-regression.md) | |
| Accessibility | [accessibility.md](playwright-skill/core/accessibility.md) | |
| Mobile & responsive | [mobile-and-responsive.md](playwright-skill/core/mobile-and-responsive.md) | |
| Component testing | [component-testing.md](playwright-skill/core/component-testing.md) | |
| Network mocking | [network-mocking.md](playwright-skill/core/network-mocking.md) | [when-to-mock.md](playwright-skill/core/when-to-mock.md) |
| Forms & validation | [forms-and-validation.md](playwright-skill/core/forms-and-validation.md) | |
| File uploads/downloads | [file-operations.md](playwright-skill/core/file-operations.md) | [file-upload-download.md](playwright-skill/core/file-upload-download.md) |
| Error & edge cases | [error-and-edge-cases.md](playwright-skill/core/error-and-edge-cases.md) | |
| CRUD flows | [crud-testing.md](playwright-skill/core/crud-testing.md) | |
| Drag and drop | [drag-and-drop.md](playwright-skill/core/drag-and-drop.md) | |
| Search & filter UI | [search-and-filter.md](playwright-skill/core/search-and-filter.md) | |

### Debugging & Fixing

| Problem | Guide |
|---|---|
| General debugging workflow | [debugging.md](playwright-skill/core/debugging.md) |
| Specific error message | [error-index.md](playwright-skill/core/error-index.md) |
| Flaky / intermittent tests | [flaky-tests.md](playwright-skill/core/flaky-tests.md) |
| Common beginner mistakes | [common-pitfalls.md](playwright-skill/core/common-pitfalls.md) |
| Debug a `trace.zip` from the terminal / with an agent | [trace-analysis.md](playwright-skill/core/trace-analysis.md) |

### Framework Recipes

| Framework | Guide |
|---|---|
| Next.js (App Router + Pages Router) | [nextjs.md](playwright-skill/core/nextjs.md) |
| React (CRA, Vite) | [react.md](playwright-skill/core/react.md) |
| Vue 3 / Nuxt | [vue.md](playwright-skill/core/vue.md) |
| Angular | [angular.md](playwright-skill/core/angular.md) |

### Migration Guides

| From | Guide |
|---|---|
| Cypress | [from-cypress.md](playwright-skill/migration/from-cypress.md) |
| Selenium / WebDriver | [from-selenium.md](playwright-skill/migration/from-selenium.md) |

### Architecture Decisions

| Question | Guide |
|---|---|
| Which locator strategy? | [locator-strategy.md](playwright-skill/core/locator-strategy.md) |
| E2E vs component vs API? | [test-architecture.md](playwright-skill/core/test-architecture.md) |
| Mock vs real services? | [when-to-mock.md](playwright-skill/core/when-to-mock.md) |
| POM vs fixtures vs helpers? | [pom-vs-fixtures-vs-helpers.md](playwright-skill/pom/pom-vs-fixtures-vs-helpers.md) |

### CI/CD & Infrastructure

| Topic | Guide |
|---|---|
| GitHub Actions | [ci-github-actions.md](playwright-skill/ci/ci-github-actions.md) |
| GitLab CI | [ci-gitlab.md](playwright-skill/ci/ci-gitlab.md) |
| CircleCI / Azure DevOps / Jenkins | [ci-other.md](playwright-skill/ci/ci-other.md) |
| Parallel execution & sharding | [parallel-and-sharding.md](playwright-skill/ci/parallel-and-sharding.md) |
| Docker & containers | [docker-and-containers.md](playwright-skill/ci/docker-and-containers.md) |
| Reports & artifacts | [reporting-and-artifacts.md](playwright-skill/ci/reporting-and-artifacts.md) |
| Code coverage | [test-coverage.md](playwright-skill/ci/test-coverage.md) |
| Global setup/teardown | [global-setup-teardown.md](playwright-skill/ci/global-setup-teardown.md) |
| Multi-project config | [projects-and-dependencies.md](playwright-skill/ci/projects-and-dependencies.md) |

### Specialized Topics

| Topic | Guide |
|---|---|
| Multi-user & collaboration | [multi-user-and-collaboration.md](playwright-skill/core/multi-user-and-collaboration.md) |
| WebSockets & real-time | [websockets-and-realtime.md](playwright-skill/core/websockets-and-realtime.md) |
| Browser APIs (geo, clipboard, permissions) | [browser-apis.md](playwright-skill/core/browser-apis.md) |
| iframes & Shadow DOM | [iframes-and-shadow-dom.md](playwright-skill/core/iframes-and-shadow-dom.md) |
| Canvas & WebGL | [canvas-and-webgl.md](playwright-skill/core/canvas-and-webgl.md) |
| Service workers & PWA | [service-workers-and-pwa.md](playwright-skill/core/service-workers-and-pwa.md) |
| Electron apps | [electron-testing.md](playwright-skill/core/electron-testing.md) |
| Browser extensions | [browser-extensions.md](playwright-skill/core/browser-extensions.md) |
| Security testing | [security-testing.md](playwright-skill/core/security-testing.md) |
| Performance & benchmarks | [performance-testing.md](playwright-skill/core/performance-testing.md) |
| i18n & localization | [i18n-and-localization.md](playwright-skill/core/i18n-and-localization.md) |
| Multi-tab & popups | [multi-context-and-popups.md](playwright-skill/core/multi-context-and-popups.md) |
| Clock & time mocking | [clock-and-time-mocking.md](playwright-skill/core/clock-and-time-mocking.md) |
| Third-party integrations | [third-party-integrations.md](playwright-skill/core/third-party-integrations.md) |

### CLI Browser Automation

| What you're doing | Guide |
|---|---|
| CLI browser interaction | [references/playwright-skill/playwright-cli/README.md](playwright-skill/playwright-cli/README.md) |
| Core commands (open, click, fill, navigate) | [core-commands.md](playwright-skill/playwright-cli/core-commands.md) |
| Network mocking & interception | [request-mocking.md](playwright-skill/playwright-cli/request-mocking.md) |
| Running custom Playwright code | [running-custom-code.md](playwright-skill/playwright-cli/running-custom-code.md) |
| Multi-session browser management | [session-management.md](playwright-skill/playwright-cli/session-management.md) |
| Cookies, localStorage, auth state | [storage-and-auth.md](playwright-skill/playwright-cli/storage-and-auth.md) |
| Test code generation from CLI | [test-generation.md](playwright-skill/playwright-cli/test-generation.md) |
| Tracing and debugging | [tracing-and-debugging.md](playwright-skill/playwright-cli/tracing-and-debugging.md) |
| Screenshots, video, PDF | [screenshots-and-media.md](playwright-skill/playwright-cli/screenshots-and-media.md) |
| Device & environment emulation | [device-emulation.md](playwright-skill/playwright-cli/device-emulation.md) |
| Complex multi-step workflows | [advanced-workflows.md](playwright-skill/playwright-cli/advanced-workflows.md) |

## Language Note

All guides include TypeScript and JavaScript examples. When the project uses `.js` files or has no `tsconfig.json`, examples are adapted to plain JavaScript.

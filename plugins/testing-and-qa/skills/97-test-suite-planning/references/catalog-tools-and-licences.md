# Quality Tools, Licenses, and Credential Safety Reference

Verified testing, quality, CI, and monitoring tools, SPDX licenses, open-source constraints, and credential handling practices for test suite planning.

---

## 1. Verified Quality & Testing Tools

| Domain | Tool / Repository | SPDX License | Usage Type | Notes & Operational Constraints |
|---|---|---|---|---|
| Web E2E | `microsoft/playwright` | Apache-2.0 | CLI / Library | Default cross-browser E2E runner; integrates with `playwright-e2e-audit`. |
| Web E2E (alt) | `cypress-io/cypress` | MIT | CLI / Library | Alternative when an existing repository standardizes on Cypress. |
| Accessibility engine | `dequelabs/axe-core` | MPL-2.0 | Library | Automated WCAG rules engine inside Playwright and unit test suites. |
| Accessibility & Perf | `GoogleChrome/lighthouse` | Apache-2.0 | CLI / Node API | Core Web Vitals, SEO, and automated accessibility auditing. |
| Accessibility CLI | `pa11y/pa11y` | LGPL-3.0 | External CLI | Run as an external CLI runner; do not statically link LGPL code into closed libraries. |
| Load & Latency | `grafana/k6` | AGPL-3.0 | External CLI | Standalone load generator; avoid embedding or modifying in network-served proprietary applications. |
| Mobile UI flows | `mobile-dev-inc/Maestro` | Apache-2.0 | CLI | Declarative UI flow runner across iOS Simulator and Android Emulator targets. |
| Mobile E2E (RN) | `wix/Detox` | MIT | Framework | Gray-box E2E testing for React Native applications. |
| Mobile E2E (Flutter) | `leancodepl/patrol` | Apache-2.0 | Framework | Native-interaction E2E testing for Flutter applications. |
| Mobile E2E (cross) | `appium/appium` | Apache-2.0 | Framework | Cross-platform device automation when declarative runners do not fit. |
| UI Component QA | `storybookjs/storybook` | MIT | Tool / Server | Isolated component state and visual testing. |
| Web 3D & Motion | `mrdoob/three.js`, `motiondivision/motion` | MIT | Library | WebGL and motion animation checks; pairs with `threejs-webgl-patterns`. |
| 3D mesh optimization | `zeux/meshoptimizer` | MIT | Library | Mesh and vertex cache optimization for 3D asset budgets. |
| Secret scanning | `gitleaks/gitleaks` | MIT | CLI | Repository secret scanning before merge or release. |
| Lockfile CVEs | `google/osv-scanner` | Apache-2.0 | CLI | Open-source vulnerability scanner for package lockfiles. |
| Container / DAST | `aquasecurity/trivy`, `zaproxy/zaproxy` | Apache-2.0 | CLI / Scanner | Container security, configuration audits, and web API vulnerability scans. |
| Store release automation | `fastlane/fastlane` | MIT | CLI | Mobile build signing, metadata, and store submission automation. |
| Local CI execution | `nektos/act`, `dagger/dagger` | MIT / Apache-2.0 | CLI / Engine | Local workflow execution and containerized CI pipeline testing. |

---

## 2. License Boundaries and Source Constraints

Review the following open-source and source-available considerations before incorporating testing dependencies:

1. **Copyleft CLI Tools (AGPL-3.0 / LGPL-3.0):**
   - Tools like `k6` (AGPL-3.0) and `pa11y` (LGPL-3.0) should be executed as external CLI commands or containerized processes.
   - Do not statically link or bundle AGPL-3.0 libraries into distributed commercial software or network-served applications.

2. **Source-Available and Non-OSI Licenses:**
   - Tools licensed under functional or source-available licenses (such as FSL or Business Source Licenses) are permitted for internal monitoring and testing, but must not be embedded in competing SaaS products or redistributable libraries without license review.
   - Always confirm whether client SDKs carry standard permissive licenses (e.g., Apache-2.0 or MIT) before integrating them into production application runtimes.

3. **Component and Asset Restrictions:**
   - Third-party UI snippets or motion kits with Commons Clause riders or non-commercial licenses must not be redistributed as standalone packages.
   - Verify font and 3D asset licenses before embedding them in release candidate builds. Commercial fonts and proprietary assets must be properly licensed or replaced with open alternatives.

4. **Rule Packs vs. Scanner Engines:**
   - Some scanning engines are permissively licensed, while specific third-party rule sets or signature feeds may carry proprietary or commercial use limitations. Confirm rule-pack licensing when configuring automated CI scans.

---

## 3. Credential Safety and Isolation

Automated test execution must follow strict secret-isolation principles:

1. **Environment Variables Over Plaintext:**
   - Pass tokens and API keys via environment variables (e.g. `TEST_API_KEY`, `SENTRY_AUTH_TOKEN`, `STRIPE_TEST_SECRET_KEY`) or secure secret managers.
   - Never commit `.env` files with active credentials into version control. Ensure `.env*` patterns are listed in `.gitignore`.

2. **No Secret Output in Test Artifacts:**
   - Configure test runners to redact Authorization headers, session cookies, and authentication payloads in trace logs, video recordings, and screenshots.
   - Sanitize error messages and exception stack traces before uploading run reports to shared storage.

3. **Sandbox and Test Mode Isolation:**
   - Always execute payment, notification, and third-party webhook tests against sandbox or test-mode endpoints (e.g. Stripe test mode).
   - Never execute live financial transactions or live data mutations in automated test suites without explicit human confirmation and documented change control.

---
name: test-suite-planning
description: "Select and plan project-type test suites, quality gates, and release verification bundles across smoke, E2E, UAT, UX/UI, mobile, a11y, perf, and security at phase boundaries and before release."
---

# Test Suite Planning

## Purpose

Define, select, and sequence project-type quality test suites and release verification gates across software and platform surfaces (web, SaaS, mobile, iOS, Android, games, 3D, API). Ensure test suites run at coherent implementation phase boundaries and before release candidates are cut—preventing disruptive testing loops after micro-edits while establishing clear gating criteria.

## Cross-referenced public skills

| Public Skill | Focus Area | When to use |
|---|---|---|
| `smoke-test-and-repair` | Smoke testing | Fast critical-path verification and immediate triage after deploy or build. |
| `playwright-e2e-audit` | End-to-end testing | Web and cross-browser user journey auditing and flake quarantine. |
| `uat-acceptance-review` | User acceptance testing | Verifying requirements and acceptance criteria across user roles. |
| `accessibility-audit` | Accessibility (a11y) | WCAG 2.2 AA automated scanning and manual assistive-tech audits. |
| `web-design-review` | UX / UI quality | Reviewing design token fidelity, layout states, and theme parity. |
| `mobile-app-review` | Mobile application QA | Inspecting mobile platform conventions, viewports, and store readiness. |
| `threejs-webgl-patterns` | 3D & motion verification | WebGL scene optimization, frame budgets, and motion patterns. |
| `frontend-performance-budget` | Frontend performance | Core Web Vitals, page weight, and rendering responsiveness budgets. |
| `backend-latency-profiling` | Backend & API load | Concurrency, p95 latency budgets, and endpoint throughput profiling. |
| `security-and-secrets-review` | Security & secrets | Secret scanning, dependency CVE audits, and configuration hardening. |
| `i18n-locale-parity-review` | Localization (i18n) | Multilingual key parity, regional formatters, and layout expansion. |
| `release-readiness-check` | Release candidate gating | Final sign-off gate before staging promotion or production release. |
| `real-user-release-gate` | Real-user release gate | A full end-to-end baseline once per product, then the journeys a release touches, on a local or staging candidate with live providers and real inbox checks; read-only checks after deploy, with live account and payment steps left to a human. |
| `customer-lens-testing` | Customer lens | Inside the same gate: use the product as a free and paid customer at beginner, intermediate and expert level; ease, motion and polish; proposals. |

## References

- [references/test-playbooks.md](references/test-playbooks.md): Execution procedures and checklists for Smoke, E2E, UAT, UX/UI, 3D/Animation, Mobile, Accessibility, and Performance/Security.
- [references/anti-slop-and-language-qa.md](references/anti-slop-and-language-qa.md): Interface authenticity, visual polish, and native-language quality checks across target locales.
- [references/catalog-tools-and-licences.md](references/catalog-tools-and-licences.md): Verified open-source testing tools, SPDX licenses, copyleft usage boundaries, and credential safety rules.

## When to use

- A planned implementation phase is integrated and ready for coherent acceptance verification.
- A release candidate is prepared for staging sign-off, store submission, or production deployment.
- Defining the test strategy, quality gate tiers, or CI pipeline bundles for a new or existing project.
- An explicit manual test run is requested or a reproducible failure blocks further implementation.
- Post-deployment verification immediately following a production release.

## When not to use

- After individual file edits, single function changes, or unintegrated code increments (complete the planned implementation scope before running verification suites).
- Rerunning passing test suites across unchanged code when only an isolated test slice failed.
- Trivial, reversible documentation or non-functional edits where prior test passes on the same commit remain valid.
- Replacing concrete implementation work with open-ended, continuous audit loops.

## Project-type test selection matrix

Compose the test bundle based on declared project type. Gate flags:
- `D`: Runs on every project (software and content).
- `C`: Common across all software projects.
- `P`: Platform-specific based on project architecture.
- `O`: On-demand triggered by specific high-risk changes or feature surfaces.

Severity tiers:
- `G0` (Blocking): Must pass before phase completion or release candidate sign-off.
- `G1` (Threshold / Warning): Budget regression or flake threshold (e.g. <=10% performance regression).
- `G2` (Advisory): Informational review item.

| Gate Domain | Flag | `web` | `saas` | `ios` | `android` | `mobile` | `game` | `3d` | `api` | Primary Open Tooling |
|---|---|---|---|---|---|---|---|---|---|---|
| Anti-slop & authenticity | `D` | G0 | G0 | G0 | G0 | G0 | G0 | G0 | G0 | Visual design review, anti-slop guidelines |
| Native-language QA | `D` | G0 | G0 | G0 | G0 | G0 | G0 | G0 | G1 | `i18n-locale-parity-review`, locale references |
| Smoke testing | `C` | G0 | G0 | G0 | G0 | G0 | G0 | G0 | G0 | Critical-path script, health endpoints |
| Performance & latency | `C` | G0 | G0 | G0 | G0 | G0 | G0 | G0 | G0 | Lighthouse, Core Web Vitals, k6 (CLI only) |
| Security & secrets | `C` | G0 | G0 | G0 | G0 | G0 | G0 | G0 | G0 | gitleaks, osv-scanner, trivy |
| E2E user journeys | `P` | G0 | G0 | G0 | G0 | G0 | G0 | O | O | Playwright, Cypress; mobile flows via Maestro |
| UAT sign-off | `P` | G0 | G0 | G0 | G0 | G0 | G0 | O | O | `uat-acceptance-review`, traceability matrix |
| UX / UI state review | `P` | G0 | G0 | G0 | G0 | G0 | G0 | G0 | — | `web-design-review`, Storybook component audit |
| 3D & animation QA | `P` | O | O | O | O | O | G0 | G0 | — | Three.js checks, 5-level deterministic ladder |
| Mobile device QA | `P` | O | O | G0 | G0 | G0 | O | — | — | Maestro, Detox, Patrol, `mobile-app-review` |
| Accessibility (a11y) | `P` | G0 | G0 | G0 | G0 | G0 | G0 | G0 | — | axe-core, Lighthouse, pa11y, screen readers |
| Real-user release gate | `C` | G0 | G0 | G0 | G0 | G0 | G0 | G0 | G0 | `real-user-release-gate`, live providers, subaddressed inbox |

## Procedure

1. **Verify Phase Boundary & Prior Evidence:**
   - Confirm the planned implementation work is integrated before starting test execution.
   - Inspect git HEAD and reuse existing evidence for unchanged slices; do not re-run passing tests on identical code.
2. **Enforce Security & Credential Isolation:**
   - Verify environment credentials use test/sandbox modes (e.g. sandbox payment keys); never run live billing operations in automated tests.
   - Pass secret values via environment variables; never print secrets in test logs or command invocations.
3. **Execute Fast Baseline Gates (`G0` Smoke & Security):**
   - Run repository secret scanning (`gitleaks`) and dependency vulnerability checks (`osv-scanner`).
   - Run the 10–20 minute critical-path smoke suite (boot, authentication, core data read/write, error fallback). Halt immediately on any blocking smoke failure.
4. **Execute Functional & Platform Suites (E2E, Mobile, 3D):**
   - **Web / SaaS:** Execute Playwright critical journeys (auth, onboarding, core mutations, billing). Archive traces and failure screenshots outside the git tree. Enforce flake quarantine (max 1 retry).
   - **Mobile:** Run Maestro/Detox/Patrol flows across supported OS and device sizes (phone, tablet). Verify clean installation and database/state upgrade from prior release.
   - **3D & Animation:** Apply the 5-level deterministic check ladder (locked facts -> numeric budgets -> timestamp/state map -> deterministic render -> contact sheets & reduced-motion fallback).
5. **Run Design, Accessibility, and Linguistic Reviews:**
   - **UX/UI & Authenticity:** Verify design token adherence, state completeness (loading, empty, error, offline, disabled, light/dark), and authentic visual concepts.
   - **Accessibility:** Run automated axe-core/Lighthouse scans plus a manual keyboard-only walk, screen-reader spot check, and reduced-motion test.
   - **Native-Language QA:** Verify 100% key parity, pluralization rules, regional formatting, 30–40% text expansion tolerance, and RTL layout support.
6. **Execute Performance, UAT, and Monitoring Verification:**
   - Verify Core Web Vitals, app startup times, 60 fps rendering, or API p95 latency against documented budgets. Flag regressions >10%.
   - Validate 100% of user acceptance criteria across persona roles; verify zero open S0/S1 defects.
   - Confirm error tracking SDK is configured and test errors reach monitoring with personal data scrubbed.
7. **Handle Failures Narrowly & Clean Up:**
   - On failure, repair the root cause and rerun only the failed test slice.
   - Clean up temporary test runners, booted simulators/emulators, and test scratch directories once verification is complete.

## Concrete checks

- Project type (`web`, `saas`, `ios`, `android`, `mobile`, `game`, `3d`, `api`) is declared and matched to the matrix.
- Implementation scope is fully integrated before initiating test execution.
- Sandbox/test credentials are configured in environment variables; no secrets present in tracked repository files.
- Automated secret scanning (`gitleaks`) and dependency lockfile scans (`osv-scanner`) report zero critical findings.
- Critical path smoke suite completes in under 20 minutes without unhandled exceptions.
- Critical user journeys pass with traces and screenshots captured for any failing assertions.
- Mobile test runs verify both clean installation and upgrade migration from the prior version.
- Accessibility automated checks pass with zero serious/critical WCAG 2.2 AA violations.
- Performance metrics meet defined budgets with <= 10% regression from established baseline.
- All target locales have 100% string key parity and survive 30–40% text expansion.
- Ephemeral test artifacts, browser profiles, and emulators are cleaned up post-run.

## Commands

```bash
# --- 1. Security & dependency baseline ---
# scan repository for accidentally committed secrets
gitleaks detect --source . --verbose

# scan dependency lockfiles for known CVEs
osv-scanner --lockfile package-lock.json

# --- 2. Code quality & type checks ---
# typecheck and lint
npm run typecheck && npm run lint

# --- 3. Smoke & unit test execution ---
# run unit / integration tests with failing-scratch retention (pytest example)
pytest -o tmp_path_retention_policy=failed

# run project smoke script
npm run test:smoke

# --- 4. End-to-end testing (Playwright) ---
# run critical E2E journeys with trace on failure
npx playwright test tests/e2e/critical-path.spec.ts --reporter=list --trace=on-first-retry

# --- 5. Accessibility auditing ---
# automated axe scan or Pa11y CLI audit
npx pa11y http://localhost:3000

# --- 6. Performance & Lighthouse ---
# audit Core Web Vitals in headless mode
npx lighthouse http://localhost:3000 --chrome-flags="--headless" --output=json --output-path=./artifacts/lighthouse-report.json

# --- 7. Mobile UI flows (Maestro) ---
# execute declarative mobile UI flow on active simulator
maestro test .maestro/critical-flow.yaml
```

## Evidence packet template

Emit a structured evidence packet for each verified gate:

```yaml
gate: test-suite-planning/<gate-id>   # e.g. smoke, e2e, mobile, real-user-release-gate, release-candidate
verdict: pass | fail | waived | deferred
scope:
  project: <project-name>
  project_type: <web | saas | ios | android | mobile | game | 3d | api>
  commit_hash: <git-commit-sha>
  target_environment: <staging | release-candidate | production>
timing_trigger: phase-boundary | pre-release | manual-request | blocker-reproduction | post-deploy
findings:
  s0_blocker: 0
  s1_high: 0
  s2_medium: 0
  s3_low: 0
unverified_or_deferred:
  - <name any unexecuted check or deferred platform test>
waiver:
  approved_by: <none | stakeholder-name>
  rationale: <none | documented reason>
  expiry_date: <none | ISO-8601 date>
evidence_artifacts:
  - <path-to-test-log-or-trace-archive>
hygiene_status: clean
completed_at: <ISO-8601 timestamp>
```

## Common issues & anti-patterns

- **Testing after every micro-edit:** Running full browser E2E or simulator suites after every line change slows delivery; complete the planned phase first.
- **Full suite restarts on isolated defects:** Rerunning all passing test suites after repairing a single assertion wastes resources; rerun only the failing slice.
- **Copying reference designs 1:1:** Duplicating third-party CSS or animations verbatim creates copyright risks; adapt timing and principles into your own design system.
- **Unquarantined test flakiness:** Allowing flaky tests to pass on repeated retries hides genuine concurrency and timing bugs; isolate and fix flaky tests promptly.
- **Skipping mobile upgrade paths:** Testing only clean installs misses migration bugs in SQLite, local storage, or keychains when users update.
- **Exposing secrets in test logs:** Printing request payloads or error dumps containing API tokens into CI logs leaks credentials.
- **Ignoring copyleft boundaries:** Statically linking or bundling AGPL-3.0 or LGPL-3.0 libraries into closed product bundles violates license terms.
- **Neglecting text expansion:** Testing only short base-language strings results in clipped buttons and broken UI layouts in translated releases.

## Required output

Deliver a concise test strategy or release verification report:
- Declared project type and applicable gate matrix (`G0`, `G1`, `G2`).
- Baseline security, dependency, and smoke test status.
- Functional E2E and platform verification results with links to trace artifacts.
- UX/UI, accessibility, and multilingual review status.
- Numeric performance vitals and regression comparisons against baseline.
- Structured evidence packet with zero open S0/S1 defects.

## Safety

- Read-only test execution first; ensure test suites do not mutate production databases or shared environments.
- Keep credentials in environment variables; never hardcode or commit keys.
- Sandbox and test-mode endpoints only for payment and transactional notification testing.
- Archive traces, video captures, and reports in dedicated artifact directories outside version-controlled source trees.
- Respect open-source license boundaries (run copyleft tools as external CLI processes; do not bundle them into proprietary products).

## Completion criteria

Done means the project type is mapped to its test matrix, baseline and platform test suites have run at the phase boundary, critical-path journeys pass without regressions, accessibility and linguistic checks are verified, zero open S0/S1 defects remain, and a structured evidence packet is produced.

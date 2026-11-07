# Domain Test Playbooks

Detailed execution procedures and pass/fail checklists for software quality domains: Smoke, End-to-End, User Acceptance, UX/UI, 3D/Animation, Mobile, Accessibility, and Performance/Security.

---

## 1. Smoke Testing

Run on software projects (`web`, `saas`, `mobile`, `ios`, `android`, `game`, `3d`, `api`) before release, immediately post-deployment, and optionally on scheduled staging builds. Target duration: 10–20 minutes.

### Procedure
1. Boot or connect to the release candidate build in a production-like staging environment.
2. Execute the automated or scripted critical path without retries:
   - Application boot and health endpoint returns `200 OK` with the expected version or build commit hash.
   - Primary authentication flow: sign-in, session token persistence, and clean sign-out.
   - Core value read and write transaction: create, read, update, and delete one canonical entity.
   - Billing and payment handshake: execute test-mode checkout using sandbox keys (never run live financial transactions in automated suites).
   - Error boundaries and fallback states: trigger an invalid route or deliberate fault; confirm the app renders a safe, user-friendly fallback without exposing raw stack traces or internal secrets.
3. Verify telemetry and error tracking: confirm test events reach the error tracking platform and verify that zero unhandled exceptions were logged during the smoke run.
4. Record build identifier, environment, duration, and rollback procedure in the smoke execution log.

### Pass/Fail Checklist
- [ ] **Boot & health check:** Application starts cleanly and reports the expected build/commit version.
- [ ] **Authentication round-trip:** Sign-in, authenticated request, and sign-out succeed without console errors or session leaks.
- [ ] **Core data path:** Primary mutation successfully persists to database and reads back accurately.
- [ ] **Sandbox payment:** Checkout flow completes cleanly in sandbox test mode with verified webhook processing.
- [ ] **Error handling & boundaries:** Controlled error states render graceful user fallbacks; credentials and stack traces are redacted.
- [ ] **Rollback readiness:** Rollback instructions and operational owner are documented before production deployment.

---

## 2. End-to-End Testing (E2E)

Required for `web`, `saas`, `mobile`, `ios`, `android`, and `game`; on-demand for API contract validation and interactive 3D flows.

### Tooling & Execution Guidelines
- **Web / SaaS Default:** `microsoft/playwright` (integrates with `playwright-e2e-audit`). Alternative: `cypress-io/cypress`.
- **Execution Model:** Run via standard CLI commands in local environments or headless CI workflows.
- **Artifact Management:** Store traces, failure screenshots, and test video recordings outside the repository source tree.
- **Flake Quarantine:** Any test that fails initially and passes on retry must be flagged for triage. Cap CI retries at 1; never mask timing issues with excessive retry loops.

### Procedure
1. Map critical user journeys from approved requirements: authentication, onboarding tour, primary value creation, billing/subscription, profile settings, and permission boundaries.
2. Ensure strict test data isolation: assign dedicated tenant identifiers, ephemeral test databases, or transactional fixture rollback. Never run destructive tests against shared staging or production data.
3. Execute the suite at the completion of an integrated feature phase and on release candidate branches.
4. Capture traces and screenshots on failure to enable rapid diagnosis.

### Pass/Fail Checklist
- [ ] **P0 journey coverage:** 100% of critical paths (auth, onboarding, core workflow, billing) pass on the release candidate.
- [ ] **Edge & negative conditions:** Form validation, expired session handling, network timeouts, and rate limits are asserted.
- [ ] **Data isolation:** Repeated runs do not leave orphan records or interfere with concurrent test workers.
- [ ] **Flake control:** Zero flaky passes on critical billing and authentication flows; overall suite flake rate remains below project budget.
- [ ] **Trace artifacts:** Traces, failure videos, and screenshots are archived in run logs outside the git tree.

---

## 3. User Acceptance Testing (UAT)

Required for `web`, `saas`, `mobile`, `ios`, `android`, and `game`; on-demand for API integrations and internal developer tooling (integrates with `uat-acceptance-review`).

### Procedure
1. Construct a traceability matrix mapping each acceptance criterion from product specifications to an end-to-end user scenario.
2. Prepare realistic, clearly fictional sample fixtures and test accounts across all user roles (e.g. unauthenticated guest, standard user, admin, organization manager).
3. Execute each scenario sequentially as the target persona, validating business logic, permission rules, and automated notifications (emails, webhooks).
4. Triage defects by severity:
   - **S0 (Blocker):** Data loss, application crash, security vulnerability, broken checkout/auth, or app store policy violation.
   - **S1 (High):** Major functional requirement unmet without a feasible workaround.
   - **S2 (Medium):** Minor functional issue or non-blocking UI defect with a documented workaround.
   - **S3 (Low):** Cosmetic polish or minor alignment item.
5. Compile scenario execution evidence and obtain explicit stakeholder or lead sign-off.

### Pass/Fail Checklist
- [ ] **Traceability coverage:** Every acceptance criterion in the product specification is mapped to an executed scenario.
- [ ] **Persona coverage:** Scenarios are verified across all user roles and permission levels.
- [ ] **Zero blocking defects:** Zero open S0 or S1 defects; any accepted S2/S3 items are documented with remediation plans.
- [ ] **Stakeholder sign-off:** Formal sign-off recorded in the test summary prior to release.

---

## 4. UX and UI Review

Required for `web`, `saas`, `mobile`, `ios`, `android`, `game`, and `3d` (integrates with `web-design-review` and `mobile-app-review`).

### Review Scope
Design review ensures visual token fidelity, responsive behavior, component state completeness, and theme consistency across viewports.

### Procedure
1. Inspect components against the project design tokens (typography scale, color palette, spacing grid, border radii, shadows).
2. Validate interactive state coverage on every interactive component:
   - Populated / default state
   - Loading / skeleton / progress state
   - Empty state with clear guidance and action buttons
   - Error / validation / retry state
   - Offline / degraded network indicator
   - Hover, active, focus-visible, and disabled states
   - Light mode and dark mode theme parity
3. Verify responsive layout across target viewports (mobile portrait/landscape, tablet, desktop, ultrawide). Check for horizontal scrollbars or clipping.
4. For dashboards and data-dense views:
   - Verify table sorting, column filtering, pagination, and bulk actions.
   - Check chart axes, legends, tooltips, and data empty states.
   - Verify confirmation dialogs for destructive actions.

### Pass/Fail Checklist
- [ ] **Token fidelity:** Zero arbitrary hard-coded pixel or color values where design tokens exist.
- [ ] **State completeness:** Loading, empty, error, offline, and disabled states are implemented and styled.
- [ ] **Theme parity:** Legible contrast and visual consistency maintained across light and dark modes.
- [ ] **Responsive behavior:** No text overflow, broken grids, or unwanted horizontal scrolling at any supported breakpoint.
- [ ] **Data integrity:** Charts and data tables render accurately without distorting scale or clipping data.

---

## 5. 3D and Animation Testing

Required for `game`, `3d`, and web or mobile surfaces with WebGL, Three.js, or complex motion interactions (integrates with `threejs-webgl-patterns`).

### 5-Level Deterministic Motion & 3D Check Ladder
1. **Level 1 — Locked Facts:**
   - Verify accurate brand colors, typography, logos, and geometry models. Do not rely on placeholder approximations.
2. **Level 2 — Numeric Budgets:**
   - Enforce explicit polygon/triangle ceilings, texture resolutions (using WebP, KTX2, or basis compression), draw-call limits, and animation duration/easing curves.
3. **Level 3 — Timestamp & State Mapping:**
   - Document expected visual states at each keyframe or transition beat.
   - Ensure Frame 1 functions effectively as a standalone poster or thumbnail before media playback begins.
   - For mobile store preview and header videos, verify native aspect ratio (e.g. 21:9 or 16:9), target framerate (30/60 fps), muted visual clarity, safe-area centering, and seamless loop points.
4. **Level 4 — Deterministic Frame & Transition Integrity:**
   - Confirm rendering at identical timestamps produces deterministic output across runs.
   - Test interrupted or canceled transitions, mesh z-fighting, LOD transitions, frustum culling, and correct color-space configuration (sRGB vs Linear).
5. **Level 5 — Contact Sheet & Reduced Motion:**
   - Generate contact sheet stills at key transition beats to inspect visual continuity.
   - Verify that enabling `prefers-reduced-motion` (or in-game accessibility toggles) replaces intense vestibular motion with simple opacity cross-fades or instant transitions.

### Pass/Fail Checklist
- [ ] **Asset budgets:** Polycounts, texture dimensions, draw calls, and file sizes are within documented scene budgets.
- [ ] **State transitions:** State transitions and animation interruptions complete smoothly without model deformation or clipping.
- [ ] **Contact sheet inspection:** Keyframe contact sheets show clear visual hierarchy and clean transitions.
- [ ] **Frame budget:** Sustained target framerate (60 fps web/mobile; target engine budget for games) without main-thread jank.
- [ ] **Reduced motion fallback:** System reduced-motion preference is respected without loss of functional context.

---

## 6. Mobile Platform Quality: iOS and Android

Required for `ios`, `android`, and cross-platform mobile apps (integrates with `mobile-app-review`).

### Execution Guidelines
- Run automated UI test flows using declarative runners (e.g., `mobile-dev-inc/Maestro`, `Detox`, or `Patrol`).
- Clean up test simulators and emulators after test execution to preserve disk space and system resources.

### Procedure
1. Execute tests across target device viewports: compact phone, standard phone, and tablet/foldable form factors on minimum, target, and latest OS versions.
2. Verify both **clean installation** and **version upgrade/migration** from the previous production build. Verify local databases, secure storage, and user preferences migrate without corruption.
3. Exercise environmental transitions:
   - Dynamic permissions: test prompts requested in context; verify graceful UI degradation when permissions are denied or later revoked in OS settings.
   - Network disruption: simulate Wi-Fi to cellular handover, high latency/lossy connection, offline mode, and automatic reconnect queueing.
   - System interruptions: backgrounding during active operations, incoming calls, low-power mode, and process kill with state restoration.
   - Ergonomics: verify notch/Dynamic Island safe-area insets, keyboard avoidance in scroll views, and minimum touch target sizes (>= 44×44 pt iOS, >= 48×48 dp Android).
4. Audit app store readiness: verify onboarding disclosures, in-app purchase and restore flows, account deletion requirements, and platform privacy declarations before store upload.

### Pass/Fail Checklist
- [ ] **OS & device matrix:** Application runs successfully across minimum, target, and latest OS versions on phone and tablet targets.
- [ ] **Upgrade migration:** Upgrading over the previous release preserves stored user state, database schemas, and session tokens.
- [ ] **Lifecycle resilience:** Recovers cleanly from backgrounding, process termination, and lossy network transitions without crash.
- [ ] **Permission handling:** Denied permissions display helpful explanations without crashing or blocking unrelated app features.
- [ ] **Store review readiness:** Privacy manifest declarations, in-app purchases, restore purchases, and account deletion comply with store guidelines.

---

## 7. Accessibility (WCAG 2.2 AA)

Required for all customer-facing software products (integrates with `accessibility-audit`).

### Procedure
1. Run automated accessibility scans (e.g., `axe-core`, `lighthouse`, or `pa11y`) across all primary application routes in both light and dark themes.
2. Conduct a keyboard-only navigation walk:
   - Tab, Shift+Tab, Enter, Space, Escape, and arrow key interactions.
   - Verify visible focus rings, logical tab order, skip links, and zero focus traps inside modal dialogs and dropdown menus.
3. Execute screen reader inspection on core user journeys:
   - Desktop: VoiceOver (macOS) or NVDA (Windows).
   - Mobile: VoiceOver (iOS) and TalkBack (Android).
   - Verify landmarks, headings, interactive buttons, modal alerts, and form validation errors are announced accurately.
4. Verify visual and motor accessibility:
   - Text contrast >= 4.5:1 for standard text, >= 3:1 for large text and interface components.
   - Color is never used as the sole indicator of state, error, or required actions.
   - Touch and click target sizes meet minimum standards (>= 24×24 CSS px for WCAG 2.2 AA; >= 44×44 pt iOS / >= 48×48 dp Android).
   - Layout survives 200% text zoom or system Dynamic Type scaling without clipping content.

### Pass/Fail Checklist
- [ ] **Automated scans:** Zero critical or serious accessibility violations reported by automated scanners.
- [ ] **Keyboard navigation:** All interactive workflows complete using only the keyboard with clear focus indicators.
- [ ] **Screen reader parity:** Screen readers announce headings, form controls, dynamic status updates, and dialog states accurately.
- [ ] **Contrast and zoom:** Color contrast meets WCAG 2.2 AA in all themes; text scales up to 200% without loss of functionality.
- [ ] **Motion & vestibular safety:** Animation respects `prefers-reduced-motion`; no content flashes faster than 3 Hz.

---

## 8. Performance, Security, and Monitoring Readiness

Required for all production software projects (integrates with `frontend-performance-budget`, `backend-latency-profiling`, and `security-and-secrets-review`).

### Performance Budgets
- **Web / SaaS:**
  - Largest Contentful Paint (LCP) <= 2.5 s
  - Interaction to Next Paint (INP) <= 200 ms
  - Cumulative Layout Shift (CLS) <= 0.1
  - Initial JS bundle size within project budget on throttled 4G connections.
- **Mobile Apps:**
  - Cold startup <= 2.0 s, warm startup <= 1.0 s
  - Sustained 60 fps rendering during scrolling and transitions; zero ANRs or out-of-memory crashes.
- **Backend & APIs:**
  - p95 response latency within defined contract under peak load (verified using load generators like `k6`).
  - Zero unhandled 5xx errors under anticipated concurrency.
- **Regression Rule:** Any performance metric that regresses by more than 10% against the established baseline requires profiling and resolution before promotion.

### Security and Telemetry Checklist
- [ ] **Secret scanning:** Repository scan with tools like `gitleaks` confirms zero exposed API keys or tokens.
- [ ] **Dependency audit:** Lockfile vulnerability scans (e.g. `osv-scanner`) report zero unmitigated critical or high CVEs.
- [ ] **Authentication & access control:** Object-level authorization, rate limiting, secure cookies, and webhook signature verification are validated.
- [ ] **Error monitoring active:** Application error tracking SDK is initialized with environment-specific configuration; source maps/symbols are uploaded, and sensitive data is scrubbed.

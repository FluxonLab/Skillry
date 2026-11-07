# Default Skill Sets and Catalog Mapping per Project Type

This reference defines standard skill sets, catalog packages, and tool mappings across project types for multi-agent software engineering workflows.

> **Verification boundary:** Before assigning or installing an external skill or package, inspect the active agent environment or repository configuration. Items with commercial or license caveats must be reviewed before adoption.

---

## 1. Project Type Classification

Declare one primary project type and any relevant secondary surface flags (`has_backend`, `has_admin`, `has_3d`, `has_mobile_build`) during project intake:

| Project type | Definition | Software core (`Tier C`) applies? |
| --- | --- | --- |
| `ios` | Native iOS/iPadOS application | Yes |
| `android` | Native Android application | Yes |
| `mobile` | Cross-platform mobile application targeting both Apple App Store and Google Play | Yes |
| `web` | Public marketing, documentation, or content site without an authenticated product surface | Yes |
| `saas` | Authenticated web product, dashboard, portal, or account surface | Yes |
| `game` | Playable game on any engine or platform | Yes |
| `3d` | Interactive 3D, AR, or VR experience or viewer | Yes |
| `api` | Backend service, API, or platform without a first-party UI | Yes |
| `social` | Marketing campaign or social publishing program without a shipped software artifact | No (`Tier D` only; requirements run in campaign-brief mode) |

---

## 2. Universal Skill Tiers

### 2.1 Tier D — Universal Baseline (Installed in Every Project)

Tier D skills establish governance, research, memory, quality, and hygiene across all project types:

| Capability | Role / Function | Gate owned | Public skill / Tool mapping |
| --- | --- | --- | --- |
| `lead-general-manager` | Leadership & governance | Charter and scope; scope change; canonical documentation | `project-intake`, `project-agent-bootstrap`, `implementation-plan` |
| `lead-feasibility` | Feasibility analysis | Go/no-go assessment before build; technical and economic checks | `business-model-review`, market sizing, unit economics |
| `product-requirements` | Requirements engineering | PRD readiness before build; acceptance criteria; change control | `product-requirements-review` |
| `design-anti-slop` | Content and UI quality | Outward-facing artifact gate; clear, natural phrasing | `technical-writing-review` |
| `qa-native-language` | Localization & language | Locale parity before release; native-quality sign-off | `i18n-locale-parity-review` (supports formal/informal registers and RTL) |
| `research-source-verification` | Fact & claim verification | Factual claims verified; primary sources cited | Independent claim checking with primary-source citation |
| `ops-memory` | Project memory & recall | Session-start recall; decision logging; preference persistence | Shared agent memory or project decision registers |
| `ops-disk-hygiene` | Workspace hygiene | End of work wave cleanup; artifact removal | `storage-artifact-lifecycle` |
| `ops-cost` | Resource & cost control | Initial budget; token consumption alerts; cost monitoring | `cost-control-token-review` |

### 2.2 Tier C — Software Core (Installed in Every Software Project)

Applied to `ios`, `android`, `mobile`, `web`, `saas`, `game`, `3d`, and `api` (excluded from non-software `social` projects):

| Capability | Role / Function | Gate owned | Public skill / Tool mapping |
| --- | --- | --- | --- |
| `eng-architect` | System architecture | Architecture review before build; ADRs; schema & API design | `architecture-review`, `api-and-interface-design`, `postgres-supabase-review` |
| `eng-senior-developer` | Engineering standards | Code review before merge; refactoring safety; pattern enforcement | `refactor-safety`, `test-driven-development` |
| `qa-smoke` | Smoke testing | Critical-path automated smoke suite before release | `smoke-test-and-repair` |
| `qa-performance` | Performance auditing | Performance budgets; latency benchmarks; rendering metrics | `frontend-performance-budget`, `backend-latency-profiling`, Lighthouse |
| `qa-security` | Security & vulnerability | Dependency vulnerability check; secret leak prevention | `security-and-secrets-review`, `dependency-supply-chain-review` |
| `release-cicd` | CI/CD pipeline | Automated build/test pipeline; rollback readiness | `ci-cd-pipeline-review`, GitHub Actions |
| `release-sentry` | Observability & monitoring | Error tracking live before production; alert triage | `error-handling-observability`, Sentry or OpenTelemetry |

### 2.3 General Catalog Baseline

Standard open-source packages and tools recommended across projects:
- **Testing & Quality:** `microsoft/playwright` (Apache-2.0), `GoogleChrome/lighthouse` (Apache-2.0), `dequelabs/axe-core` (MPL-2.0).
- **Security & Dependency Auditing:** `google/osv-scanner` (Apache-2.0), `gitleaks/gitleaks` (MIT).
- **Documentation & UI:** `shadcn-ui/ui` (MIT).

---

## 3. Per-Project-Type Default Packs

Every software project receives **Tier D + Tier C** plus the **Tier P (Per-Type)** skills and **Catalog Must-Haves** for its declared type.

### 3.1 `ios`, `android`, and `mobile`

| Layer | `ios` | `android` | `mobile` (Cross-Platform) |
| --- | --- | --- | --- |
| **Tier P skills** | Strategy, finance, market intel, UX research, analytics, `eng-mobile-ios`, UI design, mobile design, motion, E2E test, UAT, mobile QA, accessibility, store submission, ASO (`mobile-app-review`). | Same as `ios`, replacing `eng-mobile-ios` with `eng-mobile-android` and store submission targeted to Google Play. | Union of `ios` and `android` skills (`eng-mobile-ios`, `eng-mobile-android`), dual store submissions, plus `eng-backend`. |
| **Conditional additions** | `eng-backend` (if backend API), `design-dashboards-admin` (if admin portal), `threejs-webgl-patterns` (if 3D/AR). | Same as `ios`. | Same as `ios`. |
| **Catalog must-haves** | SwiftUI tooling; Swift concurrency guides; App Store Connect CLI / API; `fastlane` (MIT); `Maestro` (Apache-2.0); error monitoring SDK. | Android SDK CLI; `fastlane` (MIT); `Maestro` (Apache-2.0); error monitoring SDK. | Both iOS and Android must-haves; cross-platform framework tools (React Native / Flutter / Expo). |
| **Optional tools** | Appium (Apache-2.0). | Appium (Apache-2.0). | Detox (MIT, React Native), Patrol (Apache-2.0, Flutter). |
| **Gaps & caveats** | Verify store automation against official developer terms and API rate limits. Ensure store credentials use scoped API keys rather than account passwords. | Check Play Developer API service account permissions. | Keep native build environments isolated and reproducible across platforms. |

### 3.2 `web` and `saas`

| Layer | `web` (Public Web / Content) | `saas` (Authenticated Web App) |
| --- | --- | --- |
| **Tier P skills** | Market intel, UX research, analytics, `eng-frontend`, UI design, motion, E2E test (`playwright-e2e-audit`), UAT (`uat-acceptance-review`), accessibility (`accessibility-audit`), SEO/AEO/GEO (`seo-content-ops-review`), content ops, transactional email. | All `web` Tier P skills + `lead-feasibility`, `eng-backend` (`backend-implementation-review`), dashboard/admin design, auth review (`auth-session-review`), database review (`database-and-prisma-review`, `postgres-supabase-review`). |
| **Conditional additions** | `eng-backend` (dynamic forms/CMS), `threejs-webgl-patterns` (3D hero/visuals). | Native mobile skills when companion mobile clients ship; billing integration. |
| **Catalog must-haves** | `shadcn-ui/ui` (MIT); `GoogleChrome/lighthouse` (Apache-2.0); `microsoft/playwright` (Apache-2.0); `dequelabs/axe-core` (MPL-2.0); SEO and content tooling. | All `web` catalog must-haves + dashboard templates; charting libraries (Recharts, ECharts); database migration tools (Prisma, Drizzle); Stripe SDK (if billing); security scanners (`osv-scanner`, `gitleaks`). |
| **Optional tools** | Motion libraries (Motion, GSAP — verify licensing); Storybook (MIT). | Cloud platform management tools; transactional email tools (React Email, Resend); local container environments. |
| **Gaps & caveats** | Check UI component libraries for non-commercial restrictions (e.g., Commons Clause). Adapt reference components to project tokens rather than copying 1:1. | Verify licensing terms of commercial charting or component kits before integrating into proprietary products. |

### 3.3 `game` and `3d`

| Layer | `game` | `3d` |
| --- | --- | --- |
| **Tier P skills** | Strategy, market intel, UX research, game engineering (`game-architecture-review`), gameplay systems (`gameplay-systems-review`), 3D engineering, UI design, motion, E2E test, 3D/animation testing, UAT, accessibility, store submission. | UX research, 3D engineering, frontend engineering, UI design, motion, 3D/animation testing, UX review, accessibility. |
| **Conditional additions** | Mobile build skills (`eng-mobile-ios`, `eng-mobile-android`) for mobile games; multiplayer backend engineering for online titles. | Interactive E2E flows (`playwright-e2e-audit`), admin portal design, gamified interaction. |
| **Catalog must-haves** | Engine control tooling (Unity, Godot); 3D modeling tools (Blender integration); Three.js (`threejs-webgl-patterns`). | Blender integration tooling; Three.js libraries (`threejs-webgl-patterns`); WebGL performance profilers. |
| **Optional tools** | Physics engines (Jolt, Rapier); terrain and procedural generation libraries; shader tools; audio/music generation. | 3D mesh optimization tools (`meshoptimizer`); WebGPU experiment frameworks. |
| **Gaps & caveats** | Confirm licenses of 3D models, sound assets, and textures (e.g. CC0 vs CC-BY vs proprietary asset store terms). Verify performance on target hardware. | Check generative 3D model outputs for proprietary dependencies or non-commercial model weights. |

### 3.4 `api` and `social`

| Layer | `api` (Backend / Platform Service) | `social` (Marketing / Social Program) |
| --- | --- | --- |
| **Tier structure** | `Tier D` + `Tier C` + `Tier P`: `eng-backend` | `Tier D` only (no `Tier C`; requirements run in campaign-brief mode) + `Tier P`: social publishing, content ops, community. |
| **Conditional / Optional** | Contract testing (`api-and-interface-design`), enterprise UAT, usage metering, developer documentation (`technical-writing-review`). | Email newsletter workflows, SEO/AEO/GEO (when campaign owns a web property), asset production. |
| **Catalog must-haves** | Database ORM/drivers; security scanners (`osv-scanner`, `gitleaks`); API documentation generators; observability SDKs. | Marketing skills; SEO/content ops; email template builders; change detection tools; verified search engines. |
| **Gaps & caveats** | Maintain strict separation between dev and production environments; enforce least-privilege tokens for background workers. | Strictly respect platform terms of service regarding automated publishing and API quotas. Never publish content without human review. |

---

## 4. Tool Selection and Licensing Guidelines

1. **Permissive Open-Source First:**
   - Prefer MIT, Apache-2.0, and BSD-licensed packages for shared libraries, agent skills, and application dependencies.
   - For MPL-2.0 dependencies (e.g. `axe-core`), verify file-level modification boundaries to avoid license contamination.
2. **Copyleft & Commercial Restrictive Licenses:**
   - Avoid incorporating GPL or AGPL code into proprietary application distributions without explicit architectural separation (e.g. standalone service over network boundary).
   - Flag and review libraries carrying commercial restrictions (e.g., Commons Clause or non-commercial CC BY-NC) before adoption.
3. **Reference Design Adaptation:**
   - Third-party UI components or animation patterns must be adapted to project tokens and rewritten to match project architecture—never copied 1:1 from external sources.
4. **Asset Uniqueness:**
   - Generate project-specific media, illustrations, and icons. Avoid reusing visual assets across distinct brands or projects.
5. **Autonomous Boundaries:**
   - Autonomous agents must never execute financial transactions, live cloud infrastructure deletions, or public production releases without explicit human confirmation.

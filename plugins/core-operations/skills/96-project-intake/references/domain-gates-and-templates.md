# Domain Gates Schedule and Canonical Intake Templates

This reference specifies the four-wave domain quality gate schedule and provides copy-ready templates for the canonical project documentation trio (`AGENTS.md`, `DECISIONS.md`, and `PLAN.md`) and intake review artifacts.

---

## 1. Domain Gates Scheduled Across Lifecycle Waves

Every project `PLAN.md` must schedule these four gate waves from its initial intake commit. No phase may mark downstream phases complete by inference.

### 1.1 Wave 1 — Intake, Feasibility, Market & Baseline Gates (Before Build)

| Gate ID | Severity | Owner role / capability | Required deliverable and pass criteria |
| --- | --- | --- | --- |
| `lead-general-manager/G0-charter-scope` | `G0` | `lead-general-manager` | Multi-model review and debate completed; stakeholder multiple-choice questions answered; exactly one root `AGENTS.md`, one `DECISIONS.md`, and one `PLAN.md` written. |
| `lead-feasibility/G0-go-no-go` | `G0` | `lead-feasibility` | Scored feasibility across problem, market, technical complexity, unit economics, legal, and platform policy; explicit kill criteria recorded before coding starts. |
| `lead-market-intel/G1-market-competitors` | `G1` | `lead-market-intel` | Market sizing, target audience definition, competitor matrix with verified pricing/features, and ongoing competitor monitoring configured. |
| `product-requirements/G0-prd-ready` | `G0` | `product-requirements` | Versioned PRD with testable acceptance criteria per user story, explicit non-goals, loading/empty/error/offline states, permissions, and analytics event taxonomy. |
| `growth-copy/G1-search-answer-first-draft` | `G1` | Growth / SEO | All product, web, and store copy drafted for search engines (SEO), AI generative engines (GEO), answer engines (AEO), and app stores (ASO) from the first draft—never retrofitted later. |
| `research-source-verification/G0-claims` | `G0` | Research / Verification | Atomic claims register linking outward marketing claims and benchmarks to verified primary sources or codebase behavior. |
| `eng-architect/G0-architecture` | `G0` | `eng-architect` | Software projects only: quantified non-functional requirements (NFRs), ADRs for irreversible choices, data/auth schemas, and rollback plan. |

### 1.2 Wave 2 — Design, Component Adaptation & Media Gates (Before / During Build)

| Gate ID | Severity | Owner role / capability | Required deliverable and pass criteria |
| --- | --- | --- | --- |
| `design-ui/G0-direction` | `G0` | `design-ui` | Established visual direction, typography, design tokens, color palette, and component hierarchy approved before UI implementation. |
| `design-ui/G0-reference-adaptation` | `G0` | `design-ui` + Motion | UI components inspired by reference sites are adapted and rewritten to project tokens—never copied 1:1; motion curves and timing are captured from live interactions, not guessed from static screenshots. |
| `design-ui/G0-unique-media` | `G0` | Media production | Project-specific visuals, icons, and illustrations; no stock images or visual assets reused across distinct brand properties. |
| `design-anti-slop/G0-interface-copy` | `G0` | `design-anti-slop` | Anti-slop review passed on all UI text, empty states, error messages, notifications, and documentation before release. |

### 1.3 Wave 3 — Coherent QA Bundle, Store Readiness & Communications Gates (Before Launch)

Executed as a single coherent acceptance bundle once the planned implementation batch is integrated:

| Gate ID | Severity | Owner role / capability | Required deliverable and pass criteria |
| --- | --- | --- | --- |
| `qa-suite/G0-project-fit-tests` | `G0` | QA suite | Complete test suite matching project type: critical-path automated smoke suite, critical E2E user journeys, stakeholder UAT, responsive UI token/state audit, 3D/animation frame checks (if applicable), mobile device/OS matrix, WCAG 2.2 AA accessibility sign-off, performance budget trace, and security/dependency vulnerability audit. |
| `qa-native-language/G0-locale-signoff` | `G0` | Localization QA | Every shipped locale verified: complete string externalization, 30–40% text expansion tolerance, RTL support (if applicable), and native-quality phrasing sign-off for UI and store text. |
| `release-store/G0-store-ready` | `G0` | Release engineering | Complete app store metadata, privacy declarations, authentic localized screenshots, video previews, and store policy compliance audit passed before binary submission. |
| `release-sentry/G0-monitoring-live` | `G0` | Observability | Production error monitoring configured per environment: release tags and source maps/debug symbols uploaded, sensitive user data scrubbed, and alert triage verified. |
| `growth-email-newsletter/G0-mail-flows` | `G0` | Communications | Transactional email flows (welcome, auth, receipts) and newsletter templates configured, double opt-in consent recorded, and DNS authentication (SPF, DKIM, DMARC) verified. |
| `release-cicd/G0-release-pipeline` | `G0` | CI/CD | Green release CI pipeline with reproducible build artifacts and documented rollback procedure. |

### 1.4 Wave 4 — Customer Acquisition, Observability & Hygiene Gates (Launch and Ongoing)

| Gate ID | Severity | Owner role / capability | Required deliverable and pass criteria |
| --- | --- | --- | --- |
| `growth-acquisition/G0-acquisition-brief` | `G0` | Growth / Social | Scheduled publication calendar of content and announcements reviewed and approved by the project owner before publishing. |
| `ops-watchers/G1-live-observability` | `G1` | Operations | Production error monitoring active with automated regression alerting on unexpected error rates. |
| `ops-disk-hygiene/G1-lights-off` | `G1` | Operations | At milestone/session end: retire build artifacts and caches, terminate ephemeral test containers/simulators, and organize permanent project deliverables. |

---

## 2. Gate Evidence Packet Format

Record one machine-readable evidence block per gate in the project's evidence folder (`evidence/<project>/<date>-<wave>/` or the path specified in `PLAN.md`):

```text
gate: <capability-or-skill-id>/<gate-id>
verdict: pass | fail | waived
scope: <project> <commit-sha or build-id> <locale/device/environment>
evidence: <file paths, URLs, test run IDs, screenshot paths>
findings: <counts of findings by severity>
waiver: <reason, approving stakeholder, expiry date>
owner: <capability-or-skill-id>
date: <ISO-8601 timestamp>
```

---

## 3. Environment Configuration and Secret Management

Follow these standards when configuring project environments and agent instructions:

1. **Reference Variable Names Only:**
   - In documentation, plans, and prompt contracts, refer only to environment variable names (e.g. `DATABASE_URL`, `SENTRY_DSN`, `RESEND_API_KEY`, `STRIPE_SECRET_KEY`).
   - Never print, log, commit, or echo actual credential values.
2. **Client vs. Server Separation:**
   - Public client-side keys (such as analytics write keys or public DSNs) must be scoped strictly to read-only or send-only privileges.
   - Secret keys (database credentials, payment admin keys, deployment tokens) must remain restricted to server runtimes and secure secret managers.
3. **Destructive and Financial Operations:**
   - Live payment provider operations, production database resets, domain reconfigurations, and production deployments require explicit human authorization.

---

## 4. Copy-Ready Intake Templates

### 4.1 Multi-Model Review Synthesis & Debate Matrix (`intake-synthesis.md`)

```markdown
# Intake Review & Debate Synthesis — <Project Name> (<YYYY-MM-DD>)

- **Intake mode:** new | takeover | paused
- **Project type(s):** <ios | android | mobile | web | saas | game | 3d | api | social> (+ surface flags: <...>)
- **Base commit / branch:** `<branch>@<sha>`
- **Reviewers executed:**
  - Reviewer 1 (Inventory / mechanical scan): `<model-or-route>` — `<run-id>`
  - Reviewer 2 (Architecture, code, security, QA): `<model-or-route>` — `<run-id>`
  - Reviewer 3 (Product, feasibility, market, design, growth): `<model-or-route>` — `<run-id>`

## 1. Reviewer Findings & Contradiction Matrix

| Area | Reviewer 1 | Reviewer 2 | Reviewer 3 | Primary evidence (`path:line` or source) | Debate resolution | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Scope & state | ... | ... | ... | ... | Agreed / Resolved after debate / Needs owner decision | Verified / Unverified |
| Architecture & stack | ... | ... | ... | ... | ... | ... |
| Feasibility & market | ... | ... | ... | ... | ... | ... |
| Design & copy standards | ... | ... | ... | ... | ... | ... |
| Quality, CI & monitoring | ... | ... | ... | ... | ... | ... |
| Store / SEO / Communications | ... | ... | ... | ... | ... | ... |

## 2. Historical Files Reconciled
- Conflicting or legacy files inspected and retired into the canonical document trio: `<file-list>`

## 3. Open Owner Decisions Extracted for Batched Questionnaire
- `Q1` .. `Qn` (Consolidated into one batch before finalizing `DECISIONS.md` and `PLAN.md`)
```

### 4.2 Batched Stakeholder Multiple-Choice Questionnaire Template

*(Present this in the project owner's preferred working language with formal/polite register)*

```markdown
## Project Intake Decisions — <Project Name>

The technical review and multi-model analysis are complete. To ground the project without making assumptions, the following open decisions are collected in a single batch. Answers will be recorded in `DECISIONS.md`:

1. **<Decision Title — e.g. Target Platforms and Initial Scope>**
   *Context:* <1-sentence evidence summary and architectural impact>
   - **A) (Recommended) <Option A>:** <Scope, cost, and timeline trade-offs>
   - **B) <Option B>:** <Scope, cost, and timeline trade-offs>
   - **C) <Option C>:** <Scope, cost, and timeline trade-offs>

2. **<Decision Title — e.g. Authentication Strategy or Billing Provider>**
   *Context:* <1-sentence evidence summary and architectural impact>
   - **A) (Recommended) <Option A>:** <Trade-offs>
   - **B) <Option B>:** <Trade-offs>
```

### 4.3 Canonical Root `AGENTS.md` Template

```markdown
# AGENTS.md — <Project Name>

Canonical project contract. Client-specific configuration files (`CLAUDE.md`, `.cursorrules`, etc.) are thin adapters pointing here and must not duplicate or override this contract.

## 1. Identity and Status
- **Project:** `<name>`
- **Type:** `<ios | android | mobile | web | saas | game | 3d | api | social>` (flags: `<...>`)
- **Status:** `pre-launch | live | maintenance`
- **Authority order:** Explicit stakeholder instruction -> `DECISIONS.md` -> this `AGENTS.md` -> `PLAN.md` -> Organizational policy.
- **Canonical document trio:** `AGENTS.md`, `DECISIONS.md`, `PLAN.md`. Never create secondary todo lists, separate plan files, or conflicting status trackers.

## 2. Runtime, Stack, and Commands
- **Runtime & package manager:** `<runtime and lockfile-confirmed package manager>`
- **Build & test commands (run at phase boundaries):**
  - Build: `<exact command>`
  - Test bundle: `<exact command>`
  - Lint / typecheck: `<exact command>`
- **Environment variables required:** `<NAMES_ONLY_COMMA_SEPARATED>` (never write values)
- **Monitoring & services:** Error tracking configured (`<service-name>`); transactional mail via `<provider>`.

## 3. Installed Default Skill Pack
- **Universal baseline (Tier D):** Project leadership, feasibility review, requirements engineering, writing review, localization parity, source verification, memory management, workspace hygiene, cost monitoring.
- **Software core (Tier C):** Architecture review, engineering standards, smoke testing, performance profiling, security scanning, CI/CD pipeline review, error monitoring.
- **Project-type pack:** `<list of Tier P skills and tools matching project classification>`

## 4. Operating Boundaries
- **Clarification rule:** Consolidate open requirements into batched multiple-choice questions with recommended options; avoid interrupting with one-off questions.
- **Verification rule:** Verify changes with automated test bundles at milestone boundaries; do not infer green status without execution evidence.
- **Design & media:** Adapt reference UI patterns to project tokens (no 1:1 copying); capture motion timing from live interactions; generate unique project media without cross-project reuse.
- **Secret protection:** Never log, print, or commit credentials or secret tokens. Reference variable names only.
- **Workspace hygiene:** Retire temporary build artifacts and test containers at the end of each work session.
```

### 4.4 Canonical Root `DECISIONS.md` Template

```markdown
# DECISIONS.md — <Project Name>

Active project decision register. Entries are appended with the newest entry at the top. Decisions recorded here are definitive and not re-asked. Decisions confirmed across three separate projects should be considered for promotion to global organizational standards.

## 0001-project-intake — Project intake charter, scope, skill pack, and gate schedule

Date: <YYYY-MM-DD>. Authority: Stakeholder intake responses + multi-model intake review.

- **Scope & positioning:** <In-scope deliverables and explicit non-goals>
- **Project classification & skill pack:** `<type>` (`Tier D` + `Tier C` + `<Tier P pack>`)
- **Architecture & technology stack:** <Approved framework, database/auth model, hosting, and error monitoring>
- **Feasibility & kill criteria:** <Go/no-go assessment and measurable kill criteria>
- **Retired legacy documentation:** <List of superseded plans or documents consolidated into canonical files>
```

### 4.5 Canonical Root `PLAN.md` Template

```markdown
# PLAN.md — <Project Name>

Canonical execution plan. Read from the top block. After completing each deliverable, record its exact state (`done`, `not done`, `in progress`, `skipped`) and evidence reference, then proceed to the single next item.

## Current State & Next Item (Updated <YYYY-MM-DD>)
- **Active phase:** `Phase 1 — Intake, Feasibility & Baseline`
- **Next item:** `1.2`
- **Latest stakeholder instruction:** `<Dated summary of newest stakeholder message>`
- **Open questions:** `None` (or queued items for the next batched questionnaire)

## Phase Schedule and Domain Quality Gates

| ID | Deliverable (Coherent Batch) | Capability / Skill | Gate (`G0`/`G1`) | Status | Evidence Reference |
| --- | --- | --- | --- | --- | --- |
| 1.1 | Multi-model intake review, debate synthesis, stakeholder Q&A, canonical doc trio | `lead-general-manager` | `G0 charter-scope` | `done` | `DECISIONS.md#0001-project-intake`, `evidence/intake-synthesis.md` |
| 1.2 | Feasibility scorecard, unit economics & kill criteria | `lead-feasibility` | `G0 go-no-go` | `not done` | — |
| 1.3 | Market, audience, and competitor matrix + monitoring configuration | `lead-market-intel` | `G1 market-competitors` | `not done` | — |
| 1.4 | PRD, user stories, acceptance criteria, analytics events & first-draft copy | `product-requirements`, Growth / SEO | `G0 prd-ready`, `G1 search-answer-first-draft`, `G0 claims` | `not done` | — |
| 2.1 | Architecture ADRs, interface contracts, schema migrations & monitoring setup | `eng-architect`, Observability | `G0 architecture`, `G0 monitoring-live` | `not done` | — |
| 2.2 | Visual direction, design tokens, adapted reference components & anti-slop review | Design UI / Motion | `G0 direction`, `G0 reference-adaptation`, `G0 unique-media`, `G0 anti-slop` | `not done` | — |
| 3.1 | Core feature implementation & transactional communications | `eng-senior-developer`, Communications | `G0 code-review`, `G0 mail-flows` | `not done` | — |
| 4.1 | Coherent QA acceptance bundle (smoke, E2E, UAT, accessibility, perf, security, locale parity) | QA Suite, Localization | `G0 project-fit-tests`, `G0 locale-signoff` | `not done` | — |
| 4.2 | Store metadata, localized screenshots, review readiness audit & release build | Release engineering | `G0 store-ready`, `G0 release-pipeline` | `not done` | — |
| 5.1 | Launch, post-deploy smoke check, live monitoring activation & workspace hygiene | Operations, Growth | `G0 post-deploy-smoke`, `G0 acquisition-brief`, `G1 lights-off` | `not done` | — |
```

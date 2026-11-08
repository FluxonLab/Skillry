---
name: customer-lens-testing
description: "Use this skill inside the real-user-release-gate session before and right after release to test the product as a real customer across free and paid plans and beginner, intermediate, and expert levels (a full baseline once per product, then the screens a release touches), verify everything works, and propose or implement improvements."
---

# Customer-Lens Testing

## Purpose

Act as the customer layer of `real-user-release-gate` inside the same release gate session and test account (`qa+<project>-<date>-<sha>@<team-domain>`). Use the release candidate (a local development host or a designated staging or preview host) before shipping, and production read-only right after deploy, as a real customer across `Free` and `Paid` plans and `Beginner`, `Intermediate`, and `Expert` levels. Run the full baseline once per product; on later releases cover only the screens the release touches and the flows they belong to. Verify that every flow works on real providers and audit ease of use, confusion resistance, component motion, and visual polish. Propose what a real customer would want from the customer's seat. Implement bugs, copy fixes, and small improvements inside the existing design language directly in `PLAN.md` with evidence, and route pricing, plans, large features, brand, and legal changes to a human decision. Open [references/ux-rubric.md](references/ux-rubric.md) for checklists (`B1`–`B5`, `I1`–`I5`, `E1`–`E5`, `P1`–`P5`), motion rules, runtime metrics, Smith's Lostness ($L$), the five-dimension rubric, and the priority formula.

## When to use

- Inside a `real-user-release-gate` run before shipping a release candidate and right after deploying to production.
- Once per product, when its test ledger has no baseline, to run one full end-to-end customer baseline across every page, app, plan tier, and expertise level.
- On every subsequent release, to test changed surfaces and the end-to-end customer flows they touch.

## When not to use

- As a scheduled cron job, weekly routine, or standalone audit outside a release gate.
- As imaginary roleplay from source code or static screenshots without driving the running product.
- During unfinished implementation before the release candidate is integrated.
- Repeating the baseline, or testing screens the release did not touch.

## Cadence and pairing with real-user-release-gate

- **Shared session and account:** Run inside the active `real-user-release-gate` session and reuse its `qa+<project>-<date>-<sha>@<team-domain>` account (`qa_test: true`).
- **No duplicate lifecycle runs:** Piggyback on `real-user-release-gate` journeys `J1`–`J8` so sign-up, inbox verification, payment, and account deletion execute once.
- **Baseline (one-time):** Once per product, when its test ledger has no baseline, test every page and app surface, `Free` and `Paid` plans, `Beginner`, `Intermediate`, and `Expert` passes, and the motion/polish pass as part of that release's work item. Customer testing done at launch counts when it is recorded; repeat the baseline only on request or after a rewrite changes most of the product.
- **Pre-release update (on touch):** On later releases, test only the screens and components the release changed and the customer flows they belong to, on the release candidate (a local development host or a designated staging or preview host).
- **Post-deploy update (read-only):** Right after deploy, load the touched screens on production and check the error tracker. A live journey runs only for a touched area that exists only in production: a human creates the account, signs in, pays, and deletes it, or approves each step, and the agent may continue in the human's signed-in session. Record every run in the product's test ledger.

## Persona card, patience budget, and anti-sycophancy rules

- **Behavioral persona card (Park et al., `arXiv:2411.10109`, 2024; `microsoft/TinyTroupe`):** Ground every persona in a situational narrative rather than demographic labels alone:
  ```markdown
  Persona ID & Tier: <id — role, domain context, and Beginner | Intermediate | Expert>
  Current Habit: <1-2 live competitor products or manual workarounds used today>
  Primary Job Story (JTBD): When <situation>, I want to <action>, so I can <expected outcome>.
  Locale, Viewport & Plans: <EN | DE | TR | shipped locale> | <1440x900 desktop | 390x844 mobile> | Free -> Paid
  Patience Budget: Max 15s or 2 wrong clicks per step; max 8s on an unlabelled spinner.
  ```
- **Patience budget (`WOULD_ABANDON` — Lu et al., `UXAgent`, `arXiv:2502.12561`, 2025):**
  - Log `WOULD_ABANDON` whenever the next action is not visually obvious within `15 seconds` or `2 wrong clicks`.
  - Log `WOULD_ABANDON` whenever an unlabelled loading state or blocking spinner lasts `> 8 seconds`.
  - Classify every `WOULD_ABANDON` event as an `S3` major friction defect even if the agent finds a workaround to finish the test.
- **Anti-sycophancy rules (NN/g, 2024–2025; Hämäläinen et al., CHI 2023; Agnew et al., CHI 2024):**
  - Drive the live UI, CLI, or API/MCP surface with realistic domain payloads (multi-row imports, real documents, diacritics, quota boundaries) and never `"test 123"`.
  - Emit a concurrent think-aloud thought (Ericsson & Simon, 1984; `neuhai/UXAgent`) and cognitive tag (`DELIGHT`, `CONFUSION`, `FRICTION`, `WOULD_ABANDON`, `BLOCKER`) at each step.
  - Answer the four Wharton Cognitive Walkthrough questions (Wharton et al., 1994) per step: (1) right sub-goal formed, (2) control visible, (3) label matches user terms, (4) immediate progress feedback.
  - Omit generic praise and record an explicit renewal verdict (`YES`, `HESITANT`, or `NO`) on whether the paid plan is worth renewing out of pocket next month.
  - Triangulate feature wishes against error-tracker events, `PLAN.md`, and 2 named live competitors (`AgentA/B`, Lu et al., `arXiv:2504.09723`, 2025).

## Three expertise passes and motion/polish pass

Execute four passes using the checklists, metrics, and thresholds in [references/ux-rubric.md](references/ux-rubric.md):

1. **Pass 1 — Complete Beginner (`B1`–`B5`, ISO 9241-11:2018 Learnability):** Start in a clean profile during `J1`–`J2` using only visible labels and defaults, and record Time-to-First-Value (`TTFV`), step count ($S$), Lostness ($L$), unexplained jargon hits, and 1-click empty-state starter actions.
2. **Pass 2 — Perpetual Intermediate (`I1`–`I5`, Cooper *About Face*, 2014):** Run the top 3 recurring tasks during `J3` and `J6`, verifying `<= 3` view transitions, saved filter/view preferences, `<= 2`-level progressive disclosure (Nielsen, 2006/2024), mid-form reload draft recovery, and `5–10s` optimistic Undo instead of routine confirmation modals (NN/g, 2018).
3. **Pass 3 — Domain Expert (`E1`–`E5`, NN/g Heuristic #7 Accelerators):** Run a 10-item batch task via keyboard (`Tab`, `Enter`, `Esc`, `Cmd/Ctrl+K`, `Shift+Click`, `Cmd/Ctrl+A`), verifying non-blocking background queues, compact/table density (Tufte), stateful URLs, and structured JSON/CSV/Markdown/API/MCP exports.
4. **Pass 4 — Component Polish & Motion (`P1`–`P5`):** Audit all 8 interactive states (`default`, `:hover`, `:focus-visible`, `:active`, `:disabled`, `loading`, `empty`, `error`), `tabular-nums`, dark/light parity, `document.getAnimations()` compositor rules (`transform`/`opacity` only, `< 300ms`), Core Web Vitals (`INP <= 200ms`, `CLS <= 0.10`, `LoAF > 50ms = 0`), `prefers-reduced-motion: reduce` cross-fades (`100ms–150ms`), and 60fps (`16.67ms`/frame) video scrubbing.

## Scope-preserving proposal contract, triage, and governance

- **5-Part Scope-Preserving Proposal Contract (Tesler's Law; Hick's Law):** Shift complexity into smart defaults, `<= 2`-level progressive disclosure, optimistic Undo, inline information scent (Pirolli & Card, 1999), or keyboard accelerators. Reject any proposal that removes a capability, scores `< 4` on `ScopeKept`, or omits any of these five fields:
  - `1. Observed Friction & Affected Personas`: exact step/timestamp, affected tiers (`Beginner`/`Intermediate`/`Expert`), metric delta, and screenshot/trace path.
  - `2. Capability Invariant (Scope Guard)`: exact features, parameters, batch actions, and edge cases kept 100% accessible.
  - `3. Complexity Shift Mechanism`: `Smart Default`, `1-Level Progressive Disclosure`, `Optimistic Undo`, `Inline Scent`, or `Keyboard Accelerator`.
  - `4. Polish & Motion Specification`: interactive states, duration/easing token (`< 300ms`), `CLS = 0.00`, and `prefers-reduced-motion` behavior.
  - `5. Measurable Verification Signal`: expected delta in step ratio ($S/R$), `TTFV`, Lostness ($L$), or `INP`/`CLS`.
- **Triage and de-duplication against project authority:** Compare every finding against `PLAN.md`, `DECISIONS.md`, and open issues:
  - `DUPLICATE_OPEN`: already in `PLAN.md` -> append fresh session evidence to the existing item without creating a duplicate.
  - `REGRESSION_OF_DONE`: marked done in `PLAN.md` but broken live -> reopen as `S3` or `S4` with regression evidence.
  - `CONTRADICTS_DECISION`: conflicts with an active recorded decision -> drop unless new primary evidence justifies asking a human to supersede it.
  - `NEW_VALIDATED`: route into Track A (Defects & Friction) or Track B (Customer Wishes).
- **Scoring tracks:**
  - **Track A — Defects & UX Friction:** Rate with Nielsen `0–4` Severity (`S4` Catastrophe/Blocker, `S3` Major Friction / `WOULD_ABANDON`, `S2` Minor Friction, `S1` Cosmetic) and rank by the Scope-Guarded Priority score $P$ in [references/ux-rubric.md](references/ux-rubric.md).
  - **Track B — Customer Wishes:** Classify by Kano category (`Must-Be`, `One-Dimensional`, `Attractive`, `Indifferent`, `Reverse` — Kano et al., 1984) and score `ICE` ($\frac{\text{Impact}_{1..10} \times \text{Confidence}}{\text{Effort}_{1..10}}$) or `RICE` ($\frac{\text{Reach} \times \text{Impact} \times \text{Confidence}}{\text{Effort}}$) using evidence-bound Confidence (`1.0` = session friction + competitor pattern + JTBD, `0.7` = session friction + JTBD, `0.4` = speculative).
- **Autonomy boundary (`AUTO-IMPLEMENT` vs. `ASK-HUMAN`):**
  - `AUTO-IMPLEMENT` (`[CL-AUTO]` in `PLAN.md`): bugs (`S1`–`S4`), copy/localization/anti-slop fixes across shipped locales, and small improvements inside the existing design language (empty-state guidance, shortcuts, bulk actions, exports, copy buttons, and motion/polish fixes) implemented in one coherent batch with lead design acceptance.
  - `ASK-HUMAN` (`[CL-PROPOSAL]` in `PLAN.md`): pricing, plan/quota/credit limits, billing rules, large new features, new paid providers, brand changes, and legal/tax copy presented as a batched multiple-choice decision.

## Procedure

1. **Load project authority:** Read `AGENTS.md`, `DECISIONS.md`, `PLAN.md`, open issues, and the product's test ledger, and select full-baseline or changed-surface scope.
2. **Execute Free-plan journeys (`J1`–`J3`):** On the candidate host, run Passes 1–3 on real providers (on live production a human signs up and signs in, and the agent continues in that session) and log UI time ($T_{\text{UI\_execution}} + T_{\text{app\_response}}$), step counts ($S, N, R$), and Cognitive Walkthrough results.
3. **Execute Paid-plan upgrade and value audit (`J4`):** Upgrade via processor test mode on a local development candidate (on hosted staging or preview, a human completes the test checkout); in production a human completes it with a 100%-off live promotion code (`0.00`). Test paid features and record the renewal verdict.
4. **Audit motion, polish, cancel/withdrawal, and deletion (`J6`–`J8`):** Run Pass 4 telemetry, verify data export, 2-click self-serve cancellation, and 2-step electronic withdrawal where consumer withdrawal law applies (EU Directive (EU) 2023/2673 Art. 11a; Germany § 312k BGB; Austria FAGG), and delete the test account (on live production a human does it, or approves it).
5. **Deduplicate, implement `[CL-AUTO]`, and report:** Update `PLAN.md` (never a second backlog file), implement `[CL-AUTO]` fixes in one coherent batch, retest affected flows, write `CUSTOMER-REPORT.md` and `customer-lens-summary.json` outside git, record the run in the test ledger, and batch `[CL-PROPOSAL]` questions for human decision.

## Concrete checks

- Reuses the `real-user-release-gate` session and `qa+` test account with zero duplicate sign-up or payment runs.
- The baseline (once per product) covers every page, app, plan (`Free` and `Paid`), and expertise tier (`Beginner`, `Intermediate`, `Expert`); later runs cover only touched screens and their flows.
- Every step records a think-aloud note, cognitive tag (`DELIGHT`/`CONFUSION`/`FRICTION`/`WOULD_ABANDON`/`BLOCKER`), and Wharton `Q1`–`Q4` result.
- Steps exceeding `15s`, `2` wrong clicks, or `8s` on an unlabelled spinner log `WOULD_ABANDON` (`S3`).
- Every UX proposal satisfies all 5 fields of the Scope-Preserving Proposal Contract and scores `>= 4` on `ScopeKept`.
- `[CL-AUTO]` items are implemented and verified in `PLAN.md`; `[CL-PROPOSAL]` items are queued for human decision.

## Report format

Write `CUSTOMER-REPORT.md` and `customer-lens-summary.json` (recording `run_id`, `mode`, `personas_tested`, `counts`, `compliance`, `spend`, and `evidence_dir`) in the external `artifacts_dir` alongside the `real-user-release-gate` YAML packet, and log `[CL-AUTO]` and `[CL-PROPOSAL]` items in `PLAN.md`:

```markdown
# Customer Lens Report: <Product> (<YYYY-MM-DD>)
- **Run ID & Mode:** `cl-<project>-<YYYYMMDD>-<sha>` | `first-full-baseline` | `release-update` | `post-deploy-live`
- **Account & Plans:** `qa+<project>-<YYYYMMDD>-<sha>@<team-domain>` (Deleted: `yes`) | `Free` -> `Paid` (`<mode>`, spend `<amount>`)
- **Locales & Viewports:** `<locales>` | `1440x900` desktop + `390x844` mobile
- **Personas:** `<Persona Card(s): ID, tier, habit, JTBD, patience budget>`
- **5D Rubric (1-5):** Ease `<X.X>` | Confusion `<X.X>` | Motion `<X.X>` | Polish `<X.X>` | Scope Kept `<5.0 req>`
- **Telemetry:** Beginner `TTFV=<Xs>, S/R=<S/R>, L=<X.XX>` | Intermediate `S/R=<S/R>, L=<X.XX>` | Expert `Keyboard=<XX%>, Batch=<O(1)|O(N)>`
- **Vitals & UMUX-Lite:** `INP=<Xms>` | `CLS=<0.XX>` | `LoAF>50ms=<X>` | Reduced-Motion `<Pass/Fail>` | Anchored UMUX-Lite `<X/7, X/7>`
- **Verdicts:** Free Utility `<verdict>` | Paid Renewal (`YES` | `HESITANT` | `NO` + reason) | Cancel/Withdrawal (EU Dir. 2023/2673) `<Pass/Fail>`

## Journey & Friction Log
| Step | Surface | Tier | Action & Real Payload | CW (Q1-Q4) | Tag | Think-Aloud Thought | Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `/onboarding` | Beginner | First-run empty state | Fail Q1/Q2 | FRICTION | "No starter CTA or sample data visible." | `shots/01.png` |

## Defects & Friction (Track A) and Customer Wishes (Track B)
| ID | Track & Class (`S1-S4` or `Kano`) | Score (`P` or `ICE/RICE`) | Dedup Status | Scope-Preserving Proposal / Job Story | Authority (`[CL-AUTO]` / `[CL-PROPOSAL]`) | Status & Commit |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `CL-01` | `S3` / `B2` | `P = 18.0` | `NEW_VALIDATED` | Add 1-click sample dataset + primary CTA; keep all import options (`CLS=0`). | `[CL-AUTO]` | `Done (<sha>)` |
```

## Common issues & anti-patterns

- **Sycophantic summaries:** Praising a broken or confusing flow instead of applying deterministic deductions and logging `WOULD_ABANDON`.
- **Feature amputation disguised as simplification:** Removing expert controls or burying daily intermediate tools `> 2` clicks deep.
- **Shadow backlogs:** Creating `WISHLIST.md` or `BACKLOG.md` instead of updating the project's single `PLAN.md`.
- **Wall-clock time pollution:** Counting agent LLM inference time inside product `TTFV` or task efficiency metrics.

## Required output

- Mode executed (`first-full-baseline`, `release-update`, or `post-deploy-live`), persona cards, and 5-dimension rubric scores.
- Friction log, checklists (`B1`–`B5`, `I1`–`I5`, `E1`–`E5`, `P1`–`P5`), runtime vitals (`INP`, `CLS`, `LoAF`), Lostness ($L$), and anchored UMUX-Lite.
- Deduplicated Track A and Track B table with commits for completed `[CL-AUTO]` items and batched `[CL-PROPOSAL]` questions.
- Paths to `CUSTOMER-REPORT.md` and `customer-lens-summary.json` in the external evidence directory.

## Safety

- Follow all `real-user-release-gate` payment, secret, and teardown safeguards (agent test-mode checkouts only on a local development host, live account and payment steps by a human with a 100%-off promotion code, evidence outside git).
- Never modify live pricing, plan quotas, billing rules, brand identity, or legal/tax terms without explicit human approval.

## Completion criteria

Done means the customer lens ran inside the `real-user-release-gate` session over its scope (the full baseline once per product, otherwise the touched screens and their flows) across `Free` and `Paid` plans and all required expertise and motion/polish passes, the run was recorded in the test ledger, findings were deduplicated against `PLAN.md` and `DECISIONS.md`, eligible `[CL-AUTO]` fixes were implemented and verified with lead design sign-off, `[CL-PROPOSAL]` items were batched for human decision, and `CUSTOMER-REPORT.md` plus `customer-lens-summary.json` were written outside version control.

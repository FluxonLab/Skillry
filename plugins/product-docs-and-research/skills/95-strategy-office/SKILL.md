---
name: strategy-office
description: "Run project intake, feasibility analysis, bottom-up market sizing, competitor monitoring, strategy positioning, and unit economics before implementation or during periodic reviews."
---

# Strategy Office

## Purpose

Coordinate project leadership and strategic discovery across five core roles: general management, technical and operational feasibility, market and country intelligence, strategic positioning, and unit economics. The goal is to ground every initiative in verified evidence, bottom-up math, and clear risk boundaries before writing implementation code, and to maintain ongoing intelligence once products are live.

## When to use

- Launching a new software project, product tier, or major capability.
- Taking over or resuming an existing codebase after a prolonged pause.
- Evaluating go/no-go feasibility and platform policy risks before development.
- Conducting bottom-up market sizing (TAM/SAM/SOM), country localization, or competitor analysis.
- Modeling pricing tiers, variable provider margins (targeting <= 30% provider cost), and break-even thresholds.
- Running monthly competitor, review sentiment, and financial variance monitoring on live products.

## When not to use

- Executing implementation code or engineering refactors (use `project-agent-bootstrap` or `implementation-plan`).
- Reviewing low-level system or backend design (use `architecture-review` or `backend-implementation-review`).
- Performing code-level security audits (use `security-and-secrets-review`).
- Writing granular product specifications or user stories (use `product-requirements-review`).
- Optimizing live search or content campaigns (use `seo-content-ops-review`).

## Roles and gate map

The strategy office workflow is structured around five specialized roles and three formal gate levels: `G0` (blocking pre-build gates), `G1` (conditional milestone gates), and `G2` (periodic reviews).

| Role ID | Scope | Gate level | Primary outputs |
| --- | --- | --- | --- |
| `lead-general-manager` | Multi-model intake, charter, scope boundaries, delegation, canonical docs, risk register | `G0` charter/scope; `G1` health | Project charter, canonical contract updates, handoff note |
| `lead-feasibility` | 8-dimension scorecard, effort range, platform/legal risk, kill criteria, pre-mortem, PoC brief | `G0` go/no-go before build; `G1` post-discovery re-check | Feasibility scorecard, pre-mortem, kill criteria, PoC scope |
| `lead-market-intel` | TAM/SAM/SOM, country and audience analysis, competitor matrix, review mining, live monitoring | `G1` before positioning/roadmap; `G2` monthly refresh | Market and country map, competitor matrix, monthly signal digest |
| `lead-strategy-analyst` | Positioning wedge, JTBD segments, strategic options, build-vs-buy, North-Star KPI tree, assumptions | `G1` strategy review before roadmap lock; `G2` quarterly review | Strategy memo, KPI tree, strategic option matrix, assumption log |
| `lead-finance` | Unit economics, pricing tiers, provider-cost ceilings, break-even, sensitivity analysis, payment fees | `G1` pricing gate; `G1` budget gate; `G2` monthly close | Unit economics model, pricing table, break-even analysis |

Every evaluated gate emits a machine-readable evidence packet (see [references/templates-and-packets.md](references/templates-and-packets.md)).

## Procedure

1. **Review stakeholder context and intake baseline:**
   - Review recent stakeholder guidance, project goals, and existing repository markers.
   - Batch open ambiguities or missing constraints into multiple-choice questions early. Record decisions centrally in `DECISIONS.md` to prevent duplicate questioning.
   - For new projects or takeovers, run independent intake evaluations across multiple models, debate discrepancies, and reconcile findings into a single shared charter.
2. **Consult research ledger and memory:**
   - Search project documentation and local memory before issuing external network requests.
   - Look up topics in the local research ledger. Calculate record age deterministically (`age_days = today - record_date`).
   - Reuse valid entries within freshness windows: `volatile` (14 days), `moderate` (28 days), `stable` (90 days). Re-verify time-sensitive prices and legal rules prior to financial commitments. See [references/data-sources-and-tools.md](references/data-sources-and-tools.md).
3. **Execute cheapest-first evidence collection:**
   - Fetch primary documentation, official pricing tables, and public repository statistics via direct feeds or APIs.
   - Use search and structured extraction APIs for competitor research, pricing updates, and review sentiment.
   - Query official platform APIs (e.g. App Store Connect API, Google Play Developer API) and search tools for store visibility signals.
   - Use browser automation or heavy scrapers strictly as a last resort for complex pages.
   - Check and respect third-party terms of service and commercial API restrictions (e.g. Reddit or Product Hunt).
4. **Conduct feasibility analysis (`lead-feasibility`, G0):**
   - Score the initiative across eight mandatory dimensions on a 1–5 scale: Problem severity, Market wedge, Technical fit, Resource capacity, Time to testable slice, Unit economics, Legal/license/tax compliance, and Platform/store policy risk.
   - Establish explicit numeric kill criteria, a pre-mortem identifying top failure modes, and a bounded proof-of-concept (PoC) plan. See [references/finance-and-feasibility-models.md](references/finance-and-feasibility-models.md).
5. **Analyze market, audience, and country localization (`lead-market-intel`, G1):**
   - Calculate bottom-up TAM/SAM/SOM (`Reachable Accounts × Conversion Rate × Net Price`) backed by at least two independent sources; use top-down estimates only as secondary sanity checks. Assign confidence grades (`A`, `B`, or `C`).
   - Map audience Jobs-to-be-Done (JTBD), triggers, workarounds, and discovery intent keywords.
   - Evaluate target countries and storefronts: native search terms (avoid literal translations), local purchasing power, regional payment rails, sales tax/VAT thresholds (e.g. EU OSS), and data residency requirements.
6. **Construct competitor matrix and monitoring setup (`lead-market-intel`):**
   - Map direct, indirect, and substitute competitors covering positioning, verified pricing tiers, feature gaps, and review sentiment clusters.
   - Identify concrete, defensible differentiation wedges for the product.
   - Configure change detection URLs and store query templates for ongoing monitoring.
7. **Formulate strategy and evaluate build-versus-buy (`lead-strategy-analyst`, G1):**
   - Compare at least two distinct strategic options against a minimal baseline.
   - Conduct build-versus-buy evaluations: prioritize permissive open-source licenses (MIT, Apache-2.0). Flag copyleft (AGPL) or commercial/seat restrictions before adopting dependencies. Never copy competitor UI or assets directly.
   - Construct a North-Star metric and KPI tree spanning acquisition, activation, retention, revenue, and referral. Track open hypotheses in an assumption log with designated owners.
8. **Model unit economics and pricing (`lead-finance`, G1):**
   - Separate fixed monthly overhead from variable per-unit costs (compute, LLM tokens, storage, transactional email, payment processing fees, and app store commissions).
   - Target variable provider costs <= 30% of gross tier price (>= 70% gross margin before transaction fees).
   - Run sensitivity analysis at 50% (light), 100% (expected), and 150% (heavy) usage. Ensure 150% utilization plus free-tier bleed cannot produce negative unit contribution margins.
   - Calculate break-even paying user counts and months to payback.
9. **Update canonical documents and emit gate packets:**
   - Prepend approved decisions into `DECISIONS.md`.
   - Update `PLAN.md` with active gates, completed evidence paths, and the immediate next step.
   - Record scope boundaries and active roles in `AGENTS.md`.
   - Save cited research findings to the research ledger and emit machine-readable gate packets.

## Concrete checks

- **Intake and charter:** Scope boundaries and non-goals are documented; no competing todo or status tracking files exist outside `PLAN.md`.
- **Evidence provenance:** Every market and feasibility claim carries an explicit verification label (`verified`, `vendor claim`, `community report`, `inference`, `unverified`) and an access date.
- **Freshness thresholds:** Research ledger records are checked against 14-day (`volatile`), 28-day (`moderate`), or 90-day (`stable`) ceilings; stale records are refreshed from primary sources.
- **Feasibility thresholds:** The 8-dimension scorecard achieves an average score >= 3.5 with no blocking score of 1 on legal, policy, or unit economics dimensions.
- **Market sizing rigour:** TAM/SAM/SOM calculations are computed bottom-up and corroborated across multiple sources.
- **License compliance:** All third-party dependencies, libraries, and APIs have verified SPDX identifiers and compatible commercial terms.
- **Financial margin floor:** Variable provider cost remains <= 30% of gross price at 100% usage; contribution margin remains positive at 150% usage.
- **Gate packets:** Machine-readable gate evidence packets are generated for every evaluated milestone.

## Project start and takeover checklist

- [ ] **1. Stakeholder context reviewed:** Existing repository instructions, recent discussions, and open requirements reviewed; ambiguities batched into structured questions.
- [ ] **2. Memory and research ledger checked:** Local research ledger and project memory searched before external network queries; record age computed in code.
- [ ] **3. Multi-model intake synthesized:** Independent review perspectives debated, reconciled, and compiled into a unified project charter.
- [ ] **4. Cheapest-first evidence collected:** Data collected in cost order (primary documentation -> search APIs -> platform APIs -> scraping tools); commercial API restrictions respected.
- [ ] **5. Feasibility G0 gate evaluated:** 8-dimension scorecard completed with evidence; kill criteria, pre-mortem, and PoC scope documented.
- [ ] **6. Market and country analysis G1 completed:** Bottom-up TAM/SAM/SOM calculated with confidence grades; JTBD segments, native search terms, local pricing, and tax rules documented.
- [ ] **7. Competitor matrix established:** Competitor pricing, feature matrices, and review sentiment analyzed; ongoing monitoring queries configured.
- [ ] **8. Strategy review G1 completed:** At least two strategic options compared; build-vs-buy license audit completed; North-Star KPI tree and assumption log established.
- [ ] **9. Unit economics G1 approved:** Variable provider cost <= 30% verified; 50/100/150% usage sensitivity and break-even user thresholds calculated.
- [ ] **10. Canonical records updated:** Single root `AGENTS.md`, `DECISIONS.md`, and `PLAN.md` updated; machine-readable gate evidence packets emitted.

## Monthly live product monitoring routine

1. **Ledger staleness sweep:** Compute record age across all product ledger entries; flag expired entries for refresh.
2. **Competitor price and feature diff:** Check monitored competitor pricing pages, changelogs, and release notes for updates.
3. **Store review and visibility refresh:** Pull recent user reviews and search ranking estimates; categorize emerging complaint patterns and feature requests.
4. **Community and channel pulse:** Review industry channels for competitor outages, policy shifts, or user switching signals.
5. **Unit economics and financial variance close (`G2`):** Compare budgeted versus actual provider costs (tokens, compute, storage, email, payment fees); verify provider cost share remains within the target margin.
6. **KPI tree and assumption audit (`G2`):** Review acquisition, retention, and conversion metrics against baseline projections; trigger a feasibility re-check if key metrics breach safety thresholds.
7. **Canonical updates and stakeholder reporting:** Refresh research ledger entries, emit monthly gate packets, update `PLAN.md` and `DECISIONS.md`, and deliver a concise operational summary to stakeholders.

## Supporting references

- [references/data-sources-and-tools.md](references/data-sources-and-tools.md): Research ledger schema, freshness rules, environment variables, verified data sources, and semantic analysis workflows.
- [references/finance-and-feasibility-models.md](references/finance-and-feasibility-models.md): Unit economics formulas, provider cost rules, break-even equations, sensitivity math, and 8-dimension feasibility rubric.
- [references/templates-and-packets.md](references/templates-and-packets.md): Ready-to-use markdown templates for charters, feasibility scorecards, market matrices, strategy memos, financial sheets, and gate packets.

## Related public skills

- `product-requirements-review`: Developing detailed PRDs, feature specifications, and user acceptance criteria.
- `market-research-synthesis`: Deep synthesis of external industry reports and academic literature.
- `business-model-review`: Broad commercial modeling and monetization architecture.
- `cost-control-token-review`: Granular monitoring and optimization of LLM and API token consumption.
- `seo-content-ops-review`: Organic search strategy, keyword optimization, and content workflows.
- `analytics-tracking-review`: Telemetry design, event tracking schemas, and conversion funnels.
- `mobile-app-review`: Mobile platform architecture, store compliance, and release surface verification.
- `implementation-plan`: Structuring concrete technical milestones and phased development roadmaps.

## Required output

Every completed strategy-office pass produces:
1. Updated canonical project records: `DECISIONS.md` (dated decision entry), `PLAN.md` (top status block with active gates), and `AGENTS.md` (scope and role boundaries).
2. Specialized strategy deliverables from [references/templates-and-packets.md](references/templates-and-packets.md): Intake charter, Feasibility scorecard, Market and competitor matrix, Strategy memo with KPI tree, and Unit economics sheet.
3. Updated research ledger entries with verified citations and freshness classifications.
4. Machine-readable gate evidence packets for all evaluated gates.

## Safety and boundaries

- Never commit, log, or pass plaintext credentials or API keys in command arguments; load secrets securely from environment variables.
- Strictly analytical models: never present financial, legal, tax, or investment analysis as certified legal or investment advice.
- Comply with all platform terms of service and commercial API access restrictions.
- Do not automate real monetary transactions or execute live payment mutations without explicit stakeholder authorization.
- Never duplicate project governance across multiple tracking files; maintain single canonical sources of truth.

## Completion criteria

A strategy-office engagement is complete when:
- Project intake is reconciled across multiple review perspectives with scope boundaries recorded in `AGENTS.md`.
- Feasibility is scored across all eight dimensions with kill criteria and pre-mortem documented.
- Bottom-up market sizing, JTBD segments, and country/storefront matrices are completed with confidence ratings.
- Competitor matrix is populated with verified pricing and monitoring queries are established.
- Build-versus-buy licenses are verified and a North-Star KPI tree is established.
- Unit economics meet the <= 30% provider cost target with 50/100/150% sensitivity and break-even points computed.
- Decisions are recorded in `DECISIONS.md`, `PLAN.md` is updated, and machine-readable gate packets are emitted.

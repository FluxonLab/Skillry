# Templates, Canonical Document Feeds and Gate Evidence Packets

This reference provides copy-ready Markdown templates for the five strategy office roles and specifications for feeding outputs into canonical project records and gate evidence packets.

---

## 1. Multi-model intake synthesis template (`lead-general-manager`, G0)

Use at project bootstrap, takeover, or after a long development pause:

```markdown
# Software-Office Intake Synthesis — <Project Name>

- **Date:** YYYY-MM-DD
- **Project type:** <ios | android | mobile | web | saas | game | api | cli | tools>
- **Accountable lead:** <Lead model or engineer>
- **Reviewing models / perspectives:** <e.g. Model A, Model B, Model C>

## 1. Independent model findings
| Reviewer / Perspective | Scope & architecture assessment | Feasibility & market risks | Flagged gaps or missing skills |
| --- | --- | --- | --- |
| <Model 1> | | | |
| <Model 2> | | | |
| <Model 3> | | | |

## 2. Debate & contradiction resolution
| Discrepancy or open point | Evidence checked | Agreed resolution | Requires stakeholder decision? |
| --- | --- | --- | --- |
| | | | <yes (batched question) | no> |

## 3. Project charter & scope boundaries
- **One-line value proposition:**
- **In scope (current phase):**
- **Out of scope (non-goals):**
- **Canonical project files:** `AGENTS.md`, `DECISIONS.md`, `PLAN.md`
- **Active public skill packs:**
```

---

## 2. Feasibility scorecard and pre-mortem template (`lead-feasibility`, G0)

```markdown
# Feasibility Scorecard — <Project Name>

- **Date:** YYYY-MM-DD
- **Verdict:** <GO | CONDITIONAL GO | NO-GO>
- **Estimated effort range:** <min–max days / milestone waves>

## 1. Eight-dimension scorecard
| # | Dimension | Score (1–5) | Claim & verification label (`verified` / `vendor claim` / `community` / `inference` / `unverified`) | Primary source & date | Mitigation or validation test |
| --- | --- | ---: | --- | --- | --- |
| 1 | Problem severity & frequency | | | | |
| 2 | Market & distribution wedge | | | | |
| 3 | Technical & runtime fit | | | | |
| 4 | Resource & team capacity | | | | |
| 5 | Time to testable vertical slice | | | | |
| 6 | Unit economics & capital exposure | | | | |
| 7 | Legal, license & tax compliance | | | | |
| 8 | Platform & store policy risk | | | | |

## 2. Kill criteria (established before development begins)
- **Kill criterion 1:** <metric / cost / technical ceiling that halts work>
- **Kill criterion 2:** <conversion / margin / platform policy threshold>

## 3. Pre-mortem & proof-of-concept (PoC) plan
| Potential failure mode | Likelihood | Impact | Cheapest validation / PoC test | Owner |
| --- | --- | --- | --- | --- |
| | | | | |
```

---

## 3. Market sizing, audience, country and competitor template (`lead-market-intel`, G1)

```markdown
# Market, Country & Competitor Intelligence — <Project Name>

- **Date:** YYYY-MM-DD
- **Research ledger lookup:** <reused topic IDs + dates | refreshed topic IDs + dates>

## 1. Market sizing (TAM / SAM / SOM)
| Tier | Bottom-up formula (`Reachable Units × Conversion% × Net Price`) | Top-down sanity check | Sources (min 2) & access dates | Claim verification labels | Confidence (`A`/`B`/`C`) |
| --- | --- | --- | --- | --- | :---: |
| TAM | | | | | |
| SAM | | | | | |
| SOM (12-mo) | | | | | |

## 2. Audience & Jobs-to-be-Done (JTBD)
| Segment | Core job & triggering event | Current workaround | Willingness to pay | Native search intent phrases |
| --- | --- | --- | --- | --- |
| Primary | | | | |
| Secondary | | | | |

## 3. Country & storefront localization matrix
| Country / Storefront | Local language & register | Native search keywords (no literal translations) | Local price benchmark | Payment rail & tax regime | Data residency & legal rules | Local competitor density |
| --- | --- | --- | --- | --- | --- | --- |
| | | | | | | |

## 4. Competitor matrix (`volatile` 14d pricing / `moderate` 28d features)
| Competitor | Type (Direct / Indirect / Substitute) | Positioning statement | Verified pricing & free tier (URL + date) | Review sentiment sample (`N`, store, date) & complaints | Traffic / ASO / visibility signals | Exploitable differentiation gap |
| --- | --- | --- | --- | --- | --- | --- |
| | | | | | | |

## 5. Ongoing monitoring configuration (for live products)
- **Monitored competitor URLs (change detection):**
- **Storefront keyword & review query schedule:**
- **Community search queries:**
```

---

## 4. Strategy memo, KPI tree and assumption log template (`lead-strategy-analyst`, G1)

```markdown
# Strategy Memo & KPI Tree — <Project Name>

- **Date:** YYYY-MM-DD

## 1. Positioning & differentiation wedge
- **Target customer segment:**
- **Core wedge (concrete capability or workflow advantage):**
- **Structural reason incumbents cannot easily copy this:**

## 2. Strategic options comparison (minimum 2 options + minimal baseline)
| Option | Summary | Pros & supporting evidence | Cons & key risks | Estimated cost & effort | Verdict |
| --- | --- | --- | --- | --- | --- |
| Option A | | | | | |
| Option B | | | | | |
| Baseline / minimal | | | | | |

## 3. Build-versus-buy & license audit
| Component / Library | Build or adopt? | Upstream repository / package | SPDX License (`verified` / `unverified`) | Usage restrictions (e.g. copyleft, commercial caps) | Adaptation notes (avoid 1:1 copies) |
| --- | --- | --- | --- | --- | --- |
| | | | | | |

## 4. North-Star metric & KPI tree
- **North-Star metric:** <metric name + exact event definition>
  - **Acquisition metric:** <metric + distribution channel>
  - **Activation metric:** <metric + completed user onboarding milestone>
  - **Retention metric:** <metric + cohort measurement interval>
  - **Revenue / unit margin metric:** <net ARPU + provider cost share <= 30%>
  - **Referral / expansion metric:** <viral coefficient or net expansion rate>

## 5. Assumption log
| ID | Assumption statement | Impact if false | Cheapest validation experiment | Owner | Target date | Status |
| --- | --- | --- | --- | --- | --- | --- |
| A-01 | | | | | | |
```

---

## 5. Unit economics, pricing and break-even template (`lead-finance`, G1)

```markdown
# Unit Economics, Pricing & Break-Even Model — <Project Name>

- **Date:** YYYY-MM-DD
- **Currency:** <EUR / USD / local currency> (verified against primary vendor pages on YYYY-MM-DD)
- **Payment & tax setup:** <e.g. Direct merchant processing / Merchant of Record / App Store in-app purchases>

## 1. Fixed monthly operating costs
| Item | Provider / Service | Monthly cost | Source & date | Approval status |
| --- | --- | ---: | --- | --- |
| Base infrastructure & databases | | | | |
| Domain names & tooling | | | | |
| **Total Fixed Cost (`F`)** | | **0.00** | | |

## 2. Variable provider cost per unit (at 100% expected tier usage)
| Cost component | Unit driver (tokens / compute-hours / GB / emails) | Unit rate | Units per user/mo | Cost per user/mo | Primary source & date |
| --- | --- | ---: | ---: | ---: | --- |
| LLM & API token processing | | | | | |
| Compute / GPU execution | | | | | |
| Storage, egress & email delivery | | | | | |
| **Total Provider Variable Cost (`C_prov`)** | | | | **0.00** | Target <= 30% of gross price |

## 3. Tier pricing & usage sensitivity (50% / 100% / 150% usage)
| Tier | Gross price | Payment & store fees | Net revenue (`R_net`) | Provider cost @ 50% | Margin @ 50% | Provider cost @ 100% | Margin @ 100% | Provider cost @ 150% | Margin @ 150% |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Free / Trial | 0.00 | 0.00 | 0.00 | | | | | | |
| Entry tier | | | | | | | | | |
| Mid tier | | | | | | | | | |
| Advanced tier | | | | | | | | | |

## 4. Break-even analysis
- **Free-tier monthly cost pool (`C_free_pool`):** `<active_free_users × C_free_unit>` = ...
- **Weighted net contribution per paying user (`M_paid = R_net - C_prov_100`):** ...
- **Break-even paying users (`ceil((F + C_free_pool) / M_paid)`):** ... users
- **Break-even monthly gross revenue:** ...
```

---

## 6. Canonical document updates

### 6.1 Entry format for `DECISIONS.md`

```markdown
## DR-001 — <Project Name>: go/no-go, positioning, pricing and domain gates

Date: YYYY-MM-DD. Authority: stakeholder review and strategy-office evaluation.

- **Go/no-go & scope:** <Pass / Conditional / No-Go>; in-scope: <...>; non-goals: <...>; kill criteria: <...>.
- **Market & audience:** Primary segment <...>; target countries/locales <...>; bottom-up SOM <...> (confidence <A/B/C>).
- **Positioning & build-vs-buy:** <Core wedge>; adopted libraries/components <list with verified SPDX licenses>.
- **Pricing & unit economics:** Tiers <...>; provider cost share `<X>%` (<= 30% target); break-even at `<N>` paying users.
- **Active domain gates:** Pre-build feasibility (`G0`), market localization (`G1`), strategy review (`G1`), and pricing verification (`G1`).
```

### 6.2 Top status block update for `PLAN.md`

```markdown
## Status — YYYY-MM-DD

- **Last completed milestone:** Strategy-office intake, feasibility (`G0`), market/country intelligence (`G1`), strategy review (`G1`), and unit economics (`G1`) — **done**.
- **Evidence artifacts:** `<path/to/evidence/strategy-office/>` (intake charter, feasibility scorecard, market matrix, strategy memo, unit economics sheet, gate packets).
- **Next active milestone:** <e.g. `product-requirements-review` PRD and acceptance criteria (`G0`)>.
- **Open stakeholder questions:** <none | batched multiple-choice questions>.
```

---

## 7. Machine-readable gate evidence packet format

Emit one text block per gate evaluated (`lead-general-manager/charter-scope`, `lead-feasibility/go-no-go`, `lead-market-intel/market-review`, `lead-strategy-analyst/strategy-review`, `lead-finance/pricing-gate`, `lead-finance/budget-gate`, or periodic `G2` reviews):

```text
gate: <role-id>/<gate-id>
verdict: pass | fail | waived
scope: <project> <commit or build identifier> <locale or storefront>
evidence: <relative file paths, primary URLs, research ledger topic IDs>
findings: <blocking: N, conditional: N, advisory: N>
waiver: <none | reason, approver, expiry date>
owner: strategy-office (<role-id>)
date: YYYY-MM-DD
```

# Data Sources, Research Ledger and Tool Routing

This reference provides schemas, freshness policies, credential guidelines, verified data sources, and semantic analysis workflows for the strategy office.

Never include, print, log, or pass secret tokens or API keys in command-line arguments or commit history. Helpers and scripts must resolve credentials at runtime from environment variables or secure secret managers.

---

## 1. Research ledger schema and freshness rules

Before executing external web searches, web scraping, or paid API queries, look up the topic in project documentation and the local **research ledger**.

### 1.1 Ledger record schema

```yaml
topic_id: competitor-pricing-saas-segment
topic: "Competitor pricing and tier limits for <segment>"
freshness_class: volatile # volatile | moderate | stable
recorded_at: 2026-11-07
expires_after_days: 14    # volatile: 14, moderate: 28, stable: 90
confidence: A             # A (2+ primary sources) | B (1 primary + 1 secondary) | C (estimate/single source)
citations:
  - url: https://example.com/pricing
    accessed_at: 2026-11-07
    label: verified       # verified | vendor claim | community report | inference | unverified
summary: "Concise factual findings with exact metrics, pricing tiers, and dates."
```

### 1.2 Deterministic freshness lifecycle

Calculate record age deterministically in code (`age_days = (today_utc - recorded_at).days`):

| Freshness class | Max age (days) | Typical strategy-office topics | Action when `age_days <= max_age` | Action when `age_days > max_age` |
| --- | ---: | --- | --- | --- |
| `volatile` | **14** | Competitor pricing, active promotions, live store rankings, API rates/quotas | Reuse record; cite `recorded_at` | Re-fetch primary sources; update ledger |
| `moderate` | **28** | Feature matrices, store review sentiment samples, monthly traffic/ASO signals, channel maps | Reuse record; cite `recorded_at` | Run monthly diff pass; update ledger |
| `stable` | **90** | Country demographics, statutory tax thresholds (e.g. EU OSS), foundational tech benchmarks | Reuse record; cite `recorded_at` | Re-verify against official statutory/primary page |

*Mandatory rule:* Always re-verify time-sensitive prices, store commissions, and tax rules against current primary sources immediately before finalizing public pricing or committing capital, regardless of record age.

---

## 2. Environment variables and credential hygiene

Load all credentials and access tokens through standard environment variables:

| Capability | Recommended environment variable | Policy rules and constraints |
| --- | --- | --- |
| Web search & page fetch | `SEARCH_API_KEY`, `FETCH_API_KEY` | Default search and page extraction path before browser fallback. |
| Video metadata | `YOUTUBE_API_KEY` | Monitor competitor video cadence and tutorial interest (subject to standard platform quotas). |
| Social platform search | `SOCIAL_SEARCH_API_KEY` | Read-only search for founder updates, outages, and user complaint threads. |
| Web scraping & actors | `SCRAPER_API_KEY` | Used strictly as a last resort for complex JavaScript-rendered web pages. |
| Error monitoring | `SENTRY_AUTH_TOKEN` | Read-only API inspection for release health and issue tracking. |
| DNS & CDN management | `CLOUDFLARE_API_TOKEN` | Scoped token for zone and DNS record inspection. |
| Payment processing | `STRIPE_SECRET_KEY` | Use test keys for automated verification; live mutations require explicit stakeholder confirmation. |
| Transactional email | `RESEND_API_KEY` | Verify email templates and delivery configuration; live broadcasts require explicit approval. |

---

## 3. Verified free and low-cost data sources

Preserve explicit claim labels (`verified`, `vendor claim`, `community report`, `inference`, `unverified`) and access dates when citing data from external sources:

| Source / Tool | Access & Free Tier Notes | Claim Label | Strategy Office Use & Terms Guardrails |
| --- | --- | --- | --- |
| **Primary documentation & RSS** | Free direct access via official documentation pages, feeds, and public repository APIs (`gh api`). | `verified` | Primary factual baseline for vendor pricing, release notes, and license declarations. |
| **Exa Search API** | Free trial / monthly credit tiers available; per-thousand query pricing thereafter. | `vendor claim` on credit allowances | Semantic web search for competitor discovery, market sizing, and technical literature. |
| **Tavily Search API** | Monthly free credit tier without payment details; pay-as-you-go metered pricing. | `vendor claim` on credit allowances | Fast factual search and page content extraction for feasibility and competitor verification. |
| **Brave Search API** | Monthly developer credit tier available. | `vendor claim` on credit allowances | Independent search index for corroborating market and country localization data. |
| **Firecrawl API** | Monthly free credit allowance; paid tiers for large crawling jobs. | `vendor claim` on credit allowances | Structured extraction of competitor pricing tables, documentation, and product changelogs. |
| **Apify Actors** | Free tier usage allowance with metered compute units; monthly plans for scaling. | `verified` pricing page; actor terms vary | Use strictly as a last resort for dynamic, JavaScript-heavy sites that simpler fetchers cannot parse. |
| **YouTube Data API v3** | Default platform quota (e.g. 10,000 units/day across endpoints). | `verified` quota; platform terms apply | Competitor video publishing cadence, viewer tutorial demand, and channel growth signals. |
| **Apple App Store Connect API** | Official API free for enrolled Apple Developer account holders. | `verified` | First-party app metadata, sales reports, and release state verification. |
| **Google Play Developer API** | Official Google Play Console publishing and reporting API. | `verified` | First-party app metadata, release tracks, and Android Vitals tracking. |
| **Store Scrapers** (e.g. open-source App Store / Google Play scrapers) | Open-source libraries (e.g. MIT-licensed). | `verified` code license; store terms apply | Competitor store metadata and user review extraction. Verify platform scraping policies before running automated crawlers. |
| **changedetection.io** | Self-hosted open-source software (Apache-2.0). | `verified` | Automated monitoring of competitor pricing page changes, policy updates, and changelog diffs. |
| **Academic search APIs** (e.g. arXiv, Semantic Scholar, OpenAlex) | Open access and permissive research APIs. | `verified` | Scientific and algorithmic feasibility research. |

### Source guardrails and restricted platforms

- **Reddit Data API:** Commercial use, high-volume automated research, and AI model training require specific commercial licensing. Do not ingest Reddit data for commercial products without formal authorization.
- **Product Hunt API v2:** Terms of service restrict automated commercial use without explicit developer approval.
- **Google Trends:** Unofficial scraping libraries lack official support and may trigger rate limits or violate terms. Prefer official search console metrics where available.
- **Metered third-party growth tools:** Scrutinize per-call charges and repository licenses before adopting third-party analytics scripts. Never permit automated tools to purchase products or commit expenditures autonomously.

---

## 4. Semantic analysis stages and verification contract

When analyzing retrieved market data, user reviews, or feasibility dimensions, structure the work into five discrete stages:

1. **Rank (`rank`):** Filter and rank candidate sources or URLs to produce a focused, high-relevance context packet before deep evaluation.
2. **Extract (`extract`):** Extract literal numbers, pricing tiers, quota caps, review counts, and release dates from snippets. Do not estimate when primary numbers are present.
3. **Classify (`classify`):** Group user review feedback into praise and complaint clusters, or categorize audience pain points into Jobs-to-be-Done buckets. Keep review batches compact (<= 16 records per prompt) with stable alphanumeric IDs (e.g. `rev-01`, `rev-02`).
4. **Score (`score`):** Score feasibility dimensions and strategic options against explicit rubric criteria.
5. **Verify (`verify`):** Cross-check factual claims against at least two independent primary sources (`Grade A` confidence) for high-stakes market and financial assertions.

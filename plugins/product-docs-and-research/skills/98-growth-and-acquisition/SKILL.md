---
name: growth-and-acquisition
description: Drive organic search, AI assistant discovery, app store optimization, directory launches, and daily customer acquisition workflows from first draft across web, mobile, and SaaS projects.
---

# Growth and Acquisition

## Purpose

Run organic discovery, store optimization, launch distribution, backlink acquisition, and daily customer acquisition across projects from the first draft. The goal is to build discoverability directly into product copy, schemas, and metadata rather than treating distribution as an afterthought. Ground every outward statement in verified code evidence and project documentation. Manage ongoing distribution through a human-in-the-loop daily brief where every post, community reply, directory submission, and outreach action requires explicit approval before publication.

## When to use

- Starting a new web, mobile, or SaaS project where search and AI discoverability must be established from the first draft.
- Launching a product or major feature release across curated directories, developer platforms, and topic communities.
- Planning and executing daily customer acquisition and community engagement via an approval brief.
- Auditing content across four discovery surfaces: Search Engine Optimization (SEO), Answer Engine Optimization (AEO), Generative Engine Optimization (GEO), and App Store Optimization (ASO).
- Evaluating backlink opportunities and directory listings while screening out link farms, hidden fees, and engagement-gated lists.

## When not to use

- Established, already-live products that do not need initial launch blasts — focus instead on continuous feature announcements, SEO gap analysis, and targeted distribution.
- Automated mass-posting, spamming subreddits or forums, or scraping platforms in violation of terms of service.
- Authoring marketing claims without verified code or product evidence (never invent metrics, search volume, rankings, or testimonials).
- Outward publication, sending newsletters, or submitting directory forms without user approval.

## Procedure

1. **Establish the claim ledger:** Before drafting public copy, compile every feature, pricing, or performance claim into a claim ledger (`implemented`, `verified`, `planned`, or `unverified`). Only `implemented` and `verified` claims may appear in outward text.
2. **Draft for all four discovery surfaces from day one:** Address classic search (SEO), direct answers and voice snippets (AEO), AI assistant citations (GEO), and mobile store platforms (ASO) before finalizing copy. Follow [references/seo-geo-aeo-aso.md](references/seo-geo-aeo-aso.md).
3. **Curate launch platforms and directories:** Shortlist 10–15 candidate launch destinations across developer platforms, startup directories, and niche communities. Inspect each target live to verify current rules, cost (free vs. paid), and link attributes (`dofollow` vs. `nofollow`). Follow [references/launch-and-directories.md](references/launch-and-directories.md).
4. **Prioritize high-relevance backlinks and product loops:** Focus on tier-1 canonical profiles (e.g. GitHub, Crunchbase, G2, Dev.to), tier-2 technical comparison pages and documentation, and vetted free niche directories. Reject paid link schemes and low-quality Web 2.0 link farms.
5. **Execute the Daily Acquisition Brief workflow:** Discover high-intent conversations, verify community rules, draft contextual replies with transparent maker disclosure, and present the structured brief for approval.
6. **Publish through approved channels:** Apply user corrections verbatim and execute through approved social management pipelines, transactional/newsletter email providers, or manual submission packets. Record receipts and live URLs in the project research ledger.

## Concrete checks

Claim verification and anti-slop:
- Every factual claim traces to a verified source in the claim ledger; no planned or unreleased feature is described as live.
- Text adheres to clear, natural communication: avoid AI writing tells, generic filler, and buzzwords; verify target locale conventions (see `technical-writing-review` and `i18n-locale-parity-review`).
- Visual marketing assets are unique per platform; do not reuse identical images across disparate sites.

SEO, AEO, GEO, and ASO readiness:
- SEO: Single `<h1>`, unique title and meta description, self-referencing canonical URL, clean heading hierarchy, and passing Core Web Vitals budget (see `frontend-performance-budget` and `seo-content-ops-review`).
- AEO: Question headings open with a self-contained 40–60 word answer before expanded explanations; schema (`FAQPage`, `HowTo`) matches visible on-page copy word-for-word.
- GEO: Product name, category description, vendor organization, pricing, and supported platforms match across website, documentation, repository, and directory listings; `/llms.txt` is maintained at domain root.
- ASO: Store fields adhere to platform rules (Apple App Store vs. Google Play separation); keywords researched in native storefront languages; screenshots use verified app builds (see `mobile-app-review`).

Launch and directory hygiene:
- Candidate directories fetched live; submission fees and link attributes verified before inclusion.
- No submission queued for engagement-gated lists, social follow/DM gates, or low-quality link farms.
- Subreddit, forum, and group rules verified; transparent maker disclosure included when presenting tools.

Daily brief approval:
- Every queued item presents target URL, platform rule check, proposed copy, tags, and execution channel.
- Outward publication proceeds only after explicit user approval; no automated bypass of review.

## Claim ledger format

| Claim ID | Feature, price, or metric claim | Primary source / code evidence | Verification state | Allowed surfaces |
|---|---|---|---|---|
| C-01 | Real-time synchronization across devices | `src/sync/engine.ts:45` | verified | Landing page, docs |
| C-02 | Free tier includes up to 5 active projects | `config/plans.json:12` | verified | Pricing, directories |
| C-03 | Native PDF and CSV report export | Feature branch in development | planned | Internal only |

## Daily Brief structure

Present daily opportunities as a structured human-in-the-loop brief:

1. **Item ID and Target Channel:** Platform name, discussion thread or directory URL, and relevance rationale.
2. **Rules and Terms Check:** Community policy on maker participation, cost (free vs. paid), and link type (`dofollow`, `nofollow`, or `unverified`).
3. **Proposed Draft:** Full text in the target language, summary, hashtags, and attached asset path.
4. **Execution Channel:** Scheduled social tool, transactional/newsletter email provider, or manual submission packet.
5. **Review Prompt:** Clear options to approve as-is, approve with edits, or skip.

## Quality gates

| Gate ID | Severity | Pass criteria | Waiver rule |
|---|---|---|---|
| `growth-and-acquisition/G0-first-draft-discovery` | G0 (blocking) | SEO, GEO, AEO, and/or ASO metadata and claim ledger complete from draft one; anti-slop review passed. | Explicit user waiver recorded in plan. |
| `growth-and-acquisition/G0-daily-brief-approval` | G0 (blocking) | Explicit user approval received before any outward post, reply, newsletter, or directory submission goes live. | Never waived for outward publication. |
| `growth-and-acquisition/G1-launch-directory-readiness` | G1 (conditional) | Curated directories verified for live status, cost, and link attributes; email delivery and error monitoring verified. | Not applicable to existing live products unless launching a new surface. |
| `growth-and-acquisition/G2-growth-ledger-review` | G2 (advisory) | Periodic review of indexed backlinks, AI assistant citations, store ranking metrics, and community engagement in the research ledger. | Advisory; logged in research ledger. |

Emit one evidence packet per gate evaluation:
```text
gate: growth-and-acquisition/<gate-id>
verdict: pass | fail | waived
scope: <project> <commit-or-campaign> <locale/channel>
evidence: <claim-ledger-path, brief-path, job-id, directory-receipts>
findings: <blocking: N, conditional: N, advisory: N>
waiver: <none | reason, approval, date>
owner: growth-and-acquisition
date: <YYYY-MM-DD>
```

## Common issues & anti-patterns

- **Deferring discovery to post-launch:** Writing copy with placeholder text and attempting to "add SEO later" leads to structural rework; integrate SEO, AEO, GEO, and ASO from draft one.
- **Inventing unverified metrics:** Reporting estimated search volume or third-party authority metrics as verified truth; always label estimates with source, date, and storefront.
- **Batch-submitting unvetted directories:** Treating aggregated lists as uniformly free or high-quality; many contain hidden fees, nofollow links, or spam-farm risks.
- **Automated community posting:** Blasting identical promotional messages across forums or subreddits without reading community rules, triggering spam bans.
- **Treating live products as pre-launch:** Queuing initial launch blasts for established products instead of continuous feature distribution and steady-state optimization.
- **Word-for-word keyword translation:** Translating search terms literally rather than researching colloquial search phrasing in the target storefront locale.
- **Publishing planned features as fact:** Including roadmap items in outward landing pages without marking them as planned, misleading users and crawlers.

## Required output

Deliver:
1. Complete first-draft discovery packet (SEO metadata, AEO answer lead, GEO entity facts, or ASO storefront fields).
2. Populated claim ledger mapping all statements to codebase evidence.
3. Curated directory and community shortlist with verified cost and link attributes.
4. Structured Daily Brief ready for user review and approval before publication.

## Safety and boundaries

- Never publish outward posts, send newsletters, or submit directory forms without explicit user approval.
- Never solve, click through, or bypass CAPTCHAs, bot gates, or proof-of-work challenges; flag them for manual user action.
- Respect platform terms of service and rate limits; do not run unauthorized scrapers against protected APIs.
- Keep credentials secure: reference environment variables (e.g. `RESEND_API_KEY`) and never print or commit secret values (see `security-and-secrets-review`).

## Completion criteria

Work is complete when outward copy is grounded in a verified claim ledger, discovery metadata is attached to all drafted pages, candidate directories are triaged with live verification, and outward actions are structured into an approval brief awaiting user decision.

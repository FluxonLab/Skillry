# SEO, GEO, AEO, and ASO from the First Draft

Every outward-facing page, documentation article, changelog, landing surface, and app store listing must address classic search (SEO), answer engines (AEO), generative AI assistants (GEO), and app stores (ASO, when shipping mobile or game builds) from the first draft.

---

## 1. Surface boundaries and ownership

| Discipline | Primary surface | Core objective | Primary evidence (never invented) | Relevant skills |
|---|---|---|---|---|
| **SEO** | Classic web search results (`web`, `saas`) | Crawlability, indexation, intent-matched URLs, internal link architecture, Core Web Vitals | Crawl/index logs, valid JSON-LD, Search Console data | `seo-content-ops-review`, `frontend-performance-budget` |
| **AEO** | Featured snippets, People Also Ask, voice search | Direct 40–60 word lead answers, question-heading parity, `FAQPage` / `HowTo` schema | Question bank, snippet-ready lead blocks, schema validation | `technical-writing-review` |
| **GEO** | Generative AI assistants and citation engines | Consistent entity facts, quotable sourced claims, `/llms.txt`, intentional AI crawler policy | Entity consistency table, prompt-set evaluation log, `/llms.txt` | `product-requirements-review` |
| **ASO** | Apple App Store and Google Play (`ios`, `android`, `mobile`, `game`) | Per-storefront native keyword discovery, visual screenshot conversion, iOS header video | Store keyword estimates (labeled with storefront and date), verified build captures | `mobile-app-review` |

---

## 2. First-draft authoring template (Web and SaaS pages)

Require these fields before writing body paragraphs for any public URL:

```yaml
url_slug: /<short-intent-slug>
locale: <en | es | de | ...> # follow target locale spelling and grammar conventions
primary_intent: <informational | commercial-comparison | transactional | navigational>
primary_keyword_cluster: [<head-term>, <natural-variant-1>, <natural-variant-2>] # source or 'hypothesis (unverified volume)'
title_tag: "<Primary Intent Phrase> — <Brand/Product Name>" # <= 60 chars recommended
meta_description: "<Outcome-first summary grounded in claim ledger, with clear CTA>" # <= 155 chars recommended
h1: "<Human-readable headline matching primary intent>"
aeo_direct_answer: "<40-60 word self-contained answer to the page's core question, placed immediately after H1/intro>"
geo_entity_facts:
  product_name: "<Exact canonical name>"
  category: "<Exact software/service category>"
  platforms: ["<verified platforms only>"]
  pricing_summary: "<exact verified plan/tier from source, or omit>"
  primary_citation_urls: ["<canonical doc, benchmark, or spec URL>"]
schema_types: [WebPage, SoftwareApplication, FAQPage] # only types matching visible page content
internal_links_in: ["<parent hub or navigation path>"]
internal_links_out: ["<related feature, doc, or comparison path>"]
claim_ids_used: [C-01, C-02]
```

---

## 3. Technical checklists by discipline

### 3.1 SEO checklist
- [ ] **Indexability:** Page returns HTTP 200, has no unintended `noindex` tag, and includes a self-referencing `<link rel="canonical">`.
- [ ] **Crawl hygiene:** `robots.txt` allows search crawlers on public paths and blocks private, admin, or internal API routes; XML sitemap lists only canonical 200 URLs.
- [ ] **Heading and link structure:** Exactly one `<h1>` per page; `<h2>` and `<h3>` hierarchy reflects real subtopics; every new page has incoming internal links from relevant existing pages.
- [ ] **Internationalization:** Multi-locale pages include bidirectional `hreflang` links plus `x-default`, following `i18n-locale-parity-review`.
- [ ] **Programmatic SEO guardrail:** Never generate thin keyword-swapped template pages. Programmatic URLs are permitted only when each page renders unique, verified structured data answering a distinct query.
- [ ] **Performance:** Verify Core Web Vitals (LCP, INP, CLS) meet budgets defined in `frontend-performance-budget` via Lighthouse or browser profiling.

### 3.2 AEO checklist
- [ ] **Question mining:** Extract actual user questions from customer support inquiries, user reviews, community discussions, and search autocomplete.
- [ ] **Answer-first paragraph:** Every question heading (`<h2>` or `<h3>`) is followed immediately by a direct 1–3 sentence factual answer (40–60 words) before caveats or examples.
- [ ] **Structured lists and tables:** Comparison and procedural queries include a clean HTML `<table>` or ordered `<ol>` that answer engines can extract intact.
- [ ] **Schema parity:** `FAQPage`, `HowTo`, or `Product` JSON-LD matches visible text on the page word-for-word; never inject hidden schema for questions not displayed to users.

### 3.3 GEO checklist
- [ ] **Entity home consistency:** Product name, one-line category description, vendor organization, pricing tiers, and supported platforms match across the website, repository README, store listings, and directory profiles.
- [ ] **Self-contained quotable blocks:** Replace vague adjectives ("blazingly fast", "revolutionary AI") with concrete, citable statements ("processes 10,000 events in 12 ms on Node.js 22" or exact supported formats/limits from code).
- [ ] **Machine-readable guidance:** Serve an up-to-date `/llms.txt` at the domain root detailing canonical product overview, documentation links, API endpoints, and pricing.
- [ ] **Intentional AI crawler policy:** Explicitly document in `robots.txt` whether AI search and retrieval crawlers (`OAI-SearchBot`, `Claude-SearchBot`, `PerplexityBot`, etc.) are permitted for citation discovery versus training crawlers.
- [ ] **Share-of-model monitoring:** Track 10–20 non-branded category prompts (e.g. `"best <category> tool for <audience>"`) in the project research ledger. Log factual errors or hallucinations to correct them in outward documentation.

### 3.4 ASO checklist
- [ ] **Platform separation:**
  - **Apple App Store:** App-level name, subtitle, and privacy declarations; version-level description, byte-counted keywords, promotional text, and What's New (for updates only, never first release).
  - **Google Play:** Title, short description, and full description. Never copy Apple's comma-separated keyword field into Google Play.
- [ ] **Native storefront keyword research:** Research keywords in each target storefront's native language. Label third-party keyword difficulty and volume scores as estimates with date and storefront, never as guaranteed monthly numbers.
- [ ] **Visual conversion and video assets:**
  - Sequence the first three screenshots around primary user outcomes using captures from verified builds.
  - Where supported (e.g. iOS product page headers), prepare a 21:9 product video (`3840 x 1646`, 30/60 fps, 5–30 s, muted-first, seamless loop, safe area `1646 x 661`).
- [ ] **Store compliance:** Run pre-submission audits using `mobile-app-review` before uploading store assets.
- [ ] **Ratings and reviews:** Trigger native in-app review prompts only after a completed value moment, never on initial app launch or after an error.

---

## 4. Tool and framework ecosystem

- **Technical SEO audits:** Use open-source or standard CLI auditing tools (e.g. Lighthouse) to verify crawlability, metadata, canonical tags, and structured data schemas.
- **GEO readiness audits:** Audit documentation and entity clarity using structured prompts; treat audit ratings as heuristic indicators rather than guaranteed ranks.
- **Positioning frameworks:** Use structured positioning frameworks for audience definition and value propositions; always review generated marketing copy for natural tone and accuracy.
- **Search Console integration:** When connected to Google Search Console or other search webmaster tools, use verified index status and query impressions as primary evidence.
- **App store tooling:** Use official developer APIs (App Store Connect API, Google Play Developer API) and verified store analytics to monitor conversion rates and listing performance.

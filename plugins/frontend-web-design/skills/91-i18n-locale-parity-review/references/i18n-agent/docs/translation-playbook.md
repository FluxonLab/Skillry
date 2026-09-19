# Translation Playbook

Teach agents how to **localize websites properly**—not word-for-word machine calques.  
This document is self-contained; you should not need the original product brief.

---

## Philosophy: localize, don’t merely translate

| Content type | Approach |
|--------------|----------|
| Marketing heroes, CTAs, slogans | **Transcreation** — same job-to-be-done, native phrasing |
| Legal, pricing terms, safety, medical/finance claims | **Precise translation** — no clever rewriting of jurisdiction |
| SEO titles, metas, keywords | **Adaptation** — local query language, not EN calques |
| Brand / product / registered marks | **Stable** unless a trademarked localized form exists |
| Testimonials, certifications, stats | **Never invent**; only translate existing approved claims |

Preserve meaning, intent, and conversion job—not English syntax.

---

## Pre-translation setup

1. **Locale registry** — JSON validated by [`../schemas/locale-registry.schema.json`](../schemas/locale-registry.schema.json).  
2. **Glossary** — do-not-translate terms, preferred translations, banned calques, tone notes.  
3. **Style guide per locale** — formality (T/V), punctuation, emoji policy, inclusive language, units, currency, date formats, address formats.  
4. **ICU / plural / gender** — identify needs if the stack supports message formats.  
5. **Extract strings with provenance** — file path, key, section/screenshot, character limits.  
6. **Mark string types** — `ui` | `marketing` | `seo_title` | `seo_description` | `alt` | `schema` | `legal` | `code_adjacent`.  
7. **Market priority** — primary / secondary / maintain so effort matches opportunity.

Optional extract helper: `scripts/extract_translatables.py`.

---

## What to translate (inventory)

- **Visible UI:** nav, buttons, forms, errors, empty states, aria-labels, `sr-only` text  
- **Marketing:** heroes, ledes, FAQs, CTAs, feature/department copy  
- **SEO:** `<title>`, meta description, OG title/description if distinct, H1–H3 as needed  
- **Content:** blogs/insights/docs (decide slug policy: translate vs stable)  
- **Media:** image alt; subtitle transcripts if present  
- **Structured data:** user-visible names/descriptions  
- **Emails/templates** if in repo  
- **`llms.txt` / agent summaries** if localized  
- **Legal pages:** flag for qualified legal review; do not “cleverly” rewrite jurisdiction-specific terms  

---

## What NOT to translate

- Code identifiers, feature flags, unintentional route-segment strategy changes  
- Brand / product proper nouns (unless glossary says otherwise)  
- URLs of third-party embeds the user **locked**  
- Currency amounts without localization rules  
- Customer names in testimonials  
- SEO keyword stuffing that harms readability  

---

## Process (step-by-step)

### 1. Context pack

Per string or page, capture:

- Audience and funnel stage  
- Surrounding paragraph / UI  
- Character or layout limits  
- Keyword intent for that locale URL  

### 2. Draft

Write in the target locale using the right approach (transcreate / precise / adapt).

### 3. Adapt SEO

- Research or infer **local** query phrasing — do not literalize English keywords.  
- One primary keyword per URL per locale.  
- Rewrite title/meta for CTR in that language; keep brand suffix policy consistent.  

### 4. Terminology pass

Check every segment against the glossary (preferred terms + banned calques).

### 5. Locale QA

- Grammar/orthography (e.g. Canadian French ≠ France French; LATAM Spanish ≠ Spain where relevant)  
- Formality consistency (T/V)  
- Truncation / button length  
- Bidirectional / RTL mirroring (icons, chevrons, padding)  
- Numbers, dates, phones, units  

### 6. Parity QA

Same information architecture and claims as source; no missing FAQs/sections.

### 7. Link QA

All internal links localized; no cross-locale leaks; anchors exist.

### 8. SEO QA

Unique titles/descriptions; hreflang targets exist; canonicals locale-correct.

### 9. Human review gate

For legal and high-risk claims, mark `needs_native_review` in reports when the agent is not a native specialist.

### 10. Translation memory

Store approved segment pairs in translation-memory JSON ([`../schemas/translation-memory.schema.json`](../schemas/translation-memory.schema.json)) for reuse.

---

## Quality bar — reject / rewrite if failing

- Sounds like machine English with target-language words  
- Mixed formality  
- English idioms left literal (“hit the ground running”, etc.) without a local equivalent  
- Keyword stuffing  
- Gender / plural errors  
- CTA that doesn’t match local conversion language  
- Legal tone casually rewritten  
- Broken placeholders (`{name}`, ICU `{count, plural, ...}`)  
- Directionality bugs in RTL  

Checklist: [`../checklists/translation-quality.json`](../checklists/translation-quality.json).

---

## RTL-specific instructions

- Set `dir="rtl"` on the document or relevant containers.  
- Prefer logical CSS (`margin-inline`, `inset-inline-start`) over physical left/right when advising edits.  
- Mirror navigational affordances carefully.  
- Choose fonts that support the script; document loading strategy.  
- Verify punctuation and numerals policy (Arabic-Indic vs Latin digits) per locale style guide.  

---

## CJK / special-script notes

- Font loading and line-break CSS considerations  
- Avoid crude mid-word wrapping guidance  
- Title length in **characters**, not only “English 60 chars” heuristics — document per-locale SERP practicality  

---

## SEO + translation interaction rules

| Rule | Detail |
|------|--------|
| Quality before index | Never publish a locale URL in hreflang until content meets the quality bar (or mark noindex until ready) |
| Honest clusters | Prefer full page parity for hreflang; if a page is missing, **omit** it from alternates rather than pointing to the wrong language |
| Sitemap honesty | Update sitemap only for indexable localized URLs |
| x-default | Keep on the genuine default-locale experience |
| JSON-LD | Localize user-visible names/descriptions; keep stable entity `@id`s |

---

## Output artifacts

When localizing a site, produce:

- `locale-registry.json`  
- `glossary.json` / glossary markdown  
- `keyword-map.md` (per priority locale) — see [`../templates/keyword-map.example.md`](../templates/keyword-map.example.md)  
- `translation-plan.md` (scope, order, owners, risks)  
- `audit-report.json` + human summary  
- Optional PR-ready code/content changes  
- Optional `translation-memory.json`  

---

## Market priority (effort model)

| Tier | Meaning | Typical scope |
|------|---------|---------------|
| primary | Full investment | UI + money pages + SEO + priority content |
| secondary | Selective | UI chrome + money pages; blog by demand |
| maintain | Keep alive | Fix regressions; no new parity push |

**avoid:** equal effort across all languages by default.

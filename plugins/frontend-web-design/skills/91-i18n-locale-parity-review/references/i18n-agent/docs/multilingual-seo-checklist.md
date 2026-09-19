# Multilingual SEO Checklist

Operational checklist for agents. Marks: **must** / **should** / **avoid**.  
Machine-readable mirrors live in [`../checklists/`](../checklists/).

---

## 1) Locale architecture & URLs

| # | Check | Level |
|---|-------|-------|
| 1.1 | Locale inventory exists as a single source of truth (`locale-registry.json`) | must |
| 1.2 | Default locale routing is consistent (prefix always vs default unprefixed—pick one and document) | must |
| 1.3 | URL slug ≠ hreflang language tag (path segment may be `fr`; hreflang must be BCP47 e.g. `fr-CA`) | must |
| 1.4 | Trailing slash + host canonicalization are consistent site-wide | must |
| 1.5 | Path helpers generate locale URLs; no hardcoded default-locale links on other locales | must |
| 1.6 | No geo-IP or `Accept-Language` **force** redirects by default | must |
| 1.7 | Documented fallback policy when a translation is missing | should |

See [`locale-architecture.md`](locale-architecture.md).

---

## 2) Page & content parity

| # | Check | Level |
|---|-------|-------|
| 2.1 | Route/content parity **or** honest omission from hreflang (never point to wrong language) | must |
| 2.2 | Clear translation layers: UI / data / collections / page bodies | should |
| 2.3 | Stable content IDs/slugs across locales (or intentional translated-slug map) | must |
| 2.4 | noindex/draft policy mirrored on all locale twins | must |
| 2.5 | RTL + fonts loaded for RTL locales | must (if RTL) |
| 2.6 | In-locale internal linking (no accidental cross-locale leaks) | must |

---

## 3) Document language UX

| # | Check | Level |
|---|-------|-------|
| 3.1 | `<html lang>` matches BCP47 for the page | must |
| 3.2 | `dir` set (`ltr` / `rtl`) when registry specifies | must |
| 3.3 | Crawlable language switchers (real `<a href>` to sibling locales) | must |
| 3.4 | Switcher targets are valid existing sibling URLs | must |

---

## 4) Head tags

| # | Check | Level |
|---|-------|-------|
| 4.1 | Self-referencing canonical per locale URL | must |
| 4.2 | robots meta present and correct | must |
| 4.3 | Unique localized title + meta description | must |
| 4.4 | `og:url` === canonical | must |
| 4.5 | `og:locale` set; `og:locale:alternate` for siblings **except** on noindex | must |
| 4.6 | Absolute social images; article meta when relevant | should |

---

## 5) hreflang

| # | Check | Level |
|---|-------|-------|
| 5.1 | Full reciprocal sets across all indexable twins | must |
| 5.2 | `x-default` → genuine default-locale experience | must |
| 5.3 | BCP47 codes (not slug-case mistakes like `fr-ca` when registry requires `fr-CA`) | must |
| 5.4 | Absolute HTTPS URLs | must |
| 5.5 | **No hreflang on noindex** pages | must |
| 5.6 | Only existing URLs in the alternate set | must |
| 5.7 | Head ↔ sitemap hreflang consistency | must |

---

## 6) Sitemaps & robots

| # | Check | Level |
|---|-------|-------|
| 6.1 | One public sitemap entrypoint | must |
| 6.2 | Multilingual xhtml alternates for indexable clusters | must |
| 6.3 | Exclusions for noindex / utility / agent mirrors | must |
| 6.4 | Money-page priorities sensible across locales | should |
| 6.5 | Agreement across robots.txt, agent files, docs, GSC | must |

**avoid:** advertising two sitemap entrypoints.

---

## 7) JSON-LD

| # | Check | Level |
|---|-------|-------|
| 7.1 | `inLanguage` matches page locale | must |
| 7.2 | Stable Org / WebSite `@id` across locales | must |
| 7.3 | Localized offer / service / author **page** URLs | must |
| 7.4 | Localized breadcrumbs / FAQ / Blog names where user-visible | should |

---

## 8) Keyword & content strategy

| # | Check | Level |
|---|-------|-------|
| 8.1 | Market priority tiers (primary / secondary / maintain) | must |
| 8.2 | Adapt keywords per locale (do not calque EN) | must |
| 8.3 | One primary keyword per locale URL | must |
| 8.4 | Titles/metas written for local CTR | should |
| 8.5 | Quality bar; insight/blog cadence by demand | should |

**avoid:** shipping every new article × every locale at once without demand.

---

## 9) Analytics & GSC

| # | Check | Level |
|---|-------|-------|
| 9.1 | `page_locale` (or equivalent) dimension on page views | must |
| 9.2 | Locale-aware conversion path detection | should |
| 9.3 | GSC filters / properties by locale prefix (or equivalent) | should |
| 9.4 | Watch soft-404 / not-indexed on new locales | must |
| 9.5 | CTR iteration **within** locale | should |

---

## 10) AI / agent surfaces (optional)

| # | Check | Level |
|---|-------|-------|
| 10.1 | Locale `llms.txt` / agent indexes if you publish them | should |
| 10.2 | Correct sitemap references in agent docs | must (if present) |
| 10.3 | noindex markdown mirrors that should not compete | must (if present) |

---

## 11) CI gates

Assert in CI (see [`verification-and-ci.md`](verification-and-ci.md)):

- title / description / robots / H1 count / JSON-LD present  
- canonical present; `og:url` === canonical  
- `html[lang]` matches registry for path  
- hreflang BCP47; `x-default` present on indexable pages  
- no hreflang on noindex  
- sitemap samples include non-default locales  
- duplicate title/description detection  
- hosting / trailing-slash rules if configured  

---

## 12) Production verification

Live spot-checks after deploy for all critical signals in sections 3–7 and 9.  
Use [`../checklists/production-verify.json`](../checklists/production-verify.json) and [`../prompts/verify-production.md`](../prompts/verify-production.md).

---

## 13) Anti-patterns (hard)

- No IP / `Accept-Language` auto-redirects as default  
- Don’t change locked third-party booking/profile URLs unless user pastes a new one  
- Don’t drop live locales from hreflang while pages remain indexable  
- Don’t advertise two sitemap entrypoints  
- Don’t emit hreflang for noindex / 404 / placeholders  
- Don’t calque English keyword maps  
- Don’t ship every new article × every locale at once without demand  

---

## 14) Definition of done

- Self-canonicals + localized metas  
- Complete reciprocal BCP47 hreflang + `x-default`  
- noindex silent on alternates  
- One multilingual sitemap  
- Schema matches locale; stable entity IDs  
- Analytics / GSC by locale  
- Content follows market priority + quality bar  
- CI fails on regressions  

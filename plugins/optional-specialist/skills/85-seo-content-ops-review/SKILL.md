---
name: seo-content-ops-review
description: Use when you need to review SEO, content operations, metadata, structured data, editorial workflows, and crawlability.
---

# SEO & Content Ops Review

## Purpose
Review the technical SEO implementation and content operations setup of a site or page: meta tags, structured data (JSON-LD / schema.org), canonical tags, Open Graph, sitemap, robots.txt, Core Web Vitals, crawlability, internal linking, and editorial workflow tooling.

## When to use
- Reviewing a new page template or CMS component for SEO completeness.
- Auditing a site's technical SEO (meta, canonical, hreflang, structured data) before launch.
- Evaluating a sitemap.xml or robots.txt change.
- Reviewing a content ops workflow (CMS, editorial calendar, publishing pipeline) for SEO hygiene.
- Investigating a traffic drop and checking for canonical issues, indexation blocks, or missing structured data.

## When not to use
- Paid search (PPC) campaign review — different discipline, different tools.
- Social media content strategy review — no technical SEO component.
- Pure performance engineering (server-side rendering, CDN) unless tied to Core Web Vitals directly affecting SEO.

## Procedure

### 1. Meta tags
- `<title>`: unique per page, ≤ 60 characters (≤ 580 px rendered width), includes the primary keyword, brand name at the end.
- `<meta name="description">`: unique per page, 140–160 characters, written as a compelling summary with a call to action — not a keyword list.
- Duplicate titles or descriptions across pages dilute crawl signal and result in search engines rewriting both.
- `<meta name="robots" content="noindex">`: verify it is absent on pages intended to be indexed. A `noindex` left from staging is one of the most common post-launch SEO disasters.
- `<meta charset="UTF-8">` and `<meta name="viewport" content="width=device-width, initial-scale=1">` must be present on every page.

### 2. Canonical tags
- `<link rel="canonical" href="https://example.com/page/">`: must be present on every indexable page, pointing to the preferred URL.
- Canonical URL must be absolute (including protocol and domain), not relative (`/page/`).
- Self-referencing canonicals are correct and recommended — every page should point to itself unless it is a duplicate.
- Paginated pages: use `rel="canonical"` pointing to each paginated URL (not the first page) unless you want to consolidate — Google deprecated `rel="next"` / `rel="prev"`.
- HTTPS vs HTTP, www vs non-www: canonical must consistently match the preferred version; verify redirects reinforce this.
- Dynamic URL parameters (UTM, session IDs): strip via canonical or via `<link rel="canonical">` pointing to the clean URL.

### 3. Open Graph and social meta
- `og:title`, `og:description`, `og:image`, `og:url`, `og:type` must be present on every page intended to be shared.
- `og:image`: minimum 1200 × 630 px; use a CDN URL, not a relative path. The image must be publicly accessible (no auth-protected).
- `twitter:card`: `summary_large_image` for image-rich pages, `summary` for text-only.
- Validate with Facebook Sharing Debugger and Twitter Card Validator before launch; both cache aggressively and require a cache clear tool.
- `og:url` must match the canonical URL.

### 4. Structured data (JSON-LD / schema.org)
- Use `<script type="application/ld+json">` blocks for structured data — not Microdata or RDFa (harder to maintain, same Google support).
- Validate every schema with Google's Rich Results Test and Schema.org Validator.
- Common types by page template:
 - Product page: `Product` with `offers` (price, currency, availability), `aggregateRating`.
 - Article/blog: `Article` with `headline`, `author`, `datePublished`, `dateModified`, `image`.
 - Local business: `LocalBusiness` with `name`, `address`, `telephone`, `openingHours`, `geo`.
 - FAQ: `FAQPage` with `mainEntity` array of `Question` + `acceptedAnswer`.
 - Breadcrumb: `BreadcrumbList` on every non-home page.
- Do not mark up content that is not visible on the page — Google penalizes hidden structured data.
- `dateModified` must reflect actual content changes, not a server timestamp that updates on every deploy.

### 5. Sitemap
- `sitemap.xml` must be present and submitted to Google Search Console and Bing Webmaster Tools.
- Include only indexable, canonical URLs — exclude `noindex` pages, paginated pages that point elsewhere as canonical, and duplicate URL parameter variants.
- `<lastmod>` should reflect the date of meaningful content change, not the crawl date or current timestamp.
- `<changefreq>` and `<priority>` are largely ignored by Google but should still be plausible if included.
- Maximum 50,000 URLs and 50 MB per sitemap file; split into a sitemap index if larger.
- Dynamic sitemaps must regenerate within minutes of a new page publication — not once daily at midnight.

### 6. robots.txt
- `robots.txt` must allow Googlebot access to CSS, JS, and image files — blocking these prevents rendering and hurts indexation.
- Disallow only: staging paths accidentally left in production (`/staging/`, `/test/`), admin/backend paths (`/wp-admin/`), search result URLs (`/search?q=`), and infinite crawler trap paths.
- Do not use robots.txt to hide sensitive content — it is publicly readable. Use `noindex` or server-side auth instead.
- The `Sitemap:` directive at the bottom of robots.txt helps crawlers find it: `Sitemap: https://example.com/sitemap.xml`.
- Test with Google's robots.txt Tester in Search Console after every change.

### 7. Core Web Vitals (CWV)
- **LCP (Largest Contentful Paint)**: target < 2.5 s. Most common cause: unoptimized hero image. Fix: `<link rel="preload" as="image">` for the LCP image; serve AVIF/WebP; avoid lazy-loading the LCP element.
- **INP (Interaction to Next Paint)**: target < 200 ms. Common causes: long JavaScript tasks on the main thread, heavy event handlers. Fix: break up long tasks, defer non-critical JS.
- **CLS (Cumulative Layout Shift)**: target < 0.1. Common causes: images without `width`/`height`, ads loading without reserved space, web fonts causing FOUT. Fix: always set `width` and `height` on `<img>`, use `font-display: swap`.
- Measure CWV with PageSpeed Insights (field + lab data), Chrome DevTools Performance panel, and Lighthouse CI in the deployment pipeline.

### 8. Crawlability and internal linking
- Every important page must be reachable by internal links within 3 clicks from the homepage — orphan pages are crawled infrequently.
- Verify that JavaScript-rendered content is indexable: use Google Search Console's URL Inspection → "Test live URL" → "View tested page" to confirm the rendered DOM contains the expected content.
- Pagination: ensure paginated pages link to each other; confirm the paginated URLs are in the sitemap if independently valuable.
- Broken internal links (404s) waste crawl budget and degrade user experience — run a site crawl with Screaming Frog or a CI link checker.
- Redirect chains: keep to a maximum of 1 redirect hop. `A → B → C` should be consolidated to `A → C`.

### 9. hreflang (multilingual sites)
- `<link rel="alternate" hreflang="en-US" href="https://example.com/en/">`: must be bidirectional — every language version must reference all other versions including itself.
- Use BCP 47 language tags: `en`, `en-US`, `fr`, `pt-BR` (not `en_US`).
- `hreflang="x-default"` points to the fallback URL for unmatched locales.
- Verify with hreflang.org checker or Screaming Frog hreflang audit.

### 10. Content ops workflow
- Editorial calendar: verify new content pieces are assigned a target keyword cluster before writing begins, not retrofitted after.
- CMS publishing workflow: draft → review → SEO check → publish. SEO check must validate: title length, meta description presence, at least one internal link, structured data if applicable.
- URL slugs: lowercase, hyphen-separated, derived from the primary keyword, no stop words if possible (`/blog/seo-audit-guide`, not `/blog/how-to-do-an-seo-audit-for-a-website`).
- URL changes on existing pages require a 301 redirect from the old URL — verify the CMS handles this automatically or that a redirect map is maintained.

## Checklist

Meta:
- [ ] `<title>` unique, ≤ 60 chars, primary keyword included.
- [ ] `<meta name="description">` unique, 140–160 chars.
- [ ] No `noindex` on pages intended to be indexed.
- [ ] `charset` and `viewport` present.

Canonical:
- [ ] Self-referencing canonical on every indexable page.
- [ ] Canonical URL is absolute (HTTPS + domain).
- [ ] Canonical consistent with redirect target.

Open Graph:
- [ ] `og:title`, `og:description`, `og:image`, `og:url`, `og:type` present.
- [ ] `og:image` ≥ 1200 × 630 px, publicly accessible URL.
- [ ] `og:url` matches canonical.

Structured data:
- [ ] Passes Google Rich Results Test with no errors.
- [ ] Marked-up content is visible on the page.
- [ ] `dateModified` reflects actual content change date.

Sitemap:
- [ ] Contains only indexable, canonical URLs.
- [ ] Submitted to Google Search Console.
- [ ] Regenerates within minutes of new publication.

robots.txt:
- [ ] CSS, JS, images not blocked.
- [ ] `Sitemap:` directive present.
- [ ] No sensitive content relied upon robots.txt for protection.

CWV:
- [ ] LCP element identified; preloaded and not lazy-loaded.
- [ ] All `<img>` tags have `width` and `height`.
- [ ] No long JavaScript tasks blocking INP.

## Common issues & anti-patterns

- **`noindex` left from staging environment**: the staging robots.txt or meta tag is copied to production — the entire site disappears from Google within days.
- **Relative canonical URL**: `<link rel="canonical" href="/page/">` is interpreted differently by crawlers and can resolve to the wrong URL under some CDN configs. Always use absolute URLs.
- **Duplicate `<title>` tags**: CMS themes that inject a title and the page template also inject one — results in two title tags; search engines use the last one, which is unpredictable.
- **Missing `ecommerce: null` in structured data updates**: stale `aggregateRating` or outdated `price` in Product schema misleads users and can trigger manual Google actions.
- **Blocking JS in robots.txt**: `Disallow: /*.js$` prevents Googlebot from rendering the page — critical pages may not be indexed at all.
- **LCP image lazy-loaded**: `<img loading="lazy">` on the above-the-fold hero image delays LCP by 500–1,500 ms. Remove `loading="lazy"` from the LCP element.
- **CLS from unsized images**: images without explicit `width`/`height` cause layout shifts as they load. Always set dimensions.
- **URL slug with dynamic session ID**: `/product/123?session=abc` in the canonical causes each session to be indexed as a unique page, creating thousands of near-duplicate URLs.

## Required output

Return a structured report with:
- **Summary**: pass / needs fixes / blocked (indexation risk or critical structured data error).
- **Meta audit**: title/description uniqueness and length status.
- **Canonical audit**: absolute, correct, redirect-consistent.
- **Structured data**: validation result, schema types found, errors.
- **Sitemap/robots.txt**: coverage, submission status, block analysis.
- **CWV snapshot**: LCP, INP, CLS values from PageSpeed Insights (provide URL if available) and top issue per metric.
- **Findings table**: severity (critical / high / medium / low / info), category, page or file, description, remediation.
- **Next handoff**: Search Console verification, post-launch crawl schedule, CWV monitoring setup.

## Safety

- Do not submit sitemaps to Search Console or trigger re-indexation during review.
- Do not modify robots.txt on a live production server during review — propose changes in a PR.
- If the review reveals content accidentally indexed that should not be (e.g., staging content, internal docs), flag as high severity but do not add `noindex` without the site owner's authorization.
- Do not access Search Console data that contains proprietary keyword or traffic data unless the task explicitly grants access.

# Framework Adapters

First-class patterns for common stacks. Principles are framework-agnostic; wiring differs.

**Shared rules for all adapters**

- Registry is the source of truth for BCP47, prefixes, `dir`, OG locales.  
- Self-canonical per locale URL; `og:url` === canonical.  
- Reciprocal hreflang + `x-default`; **no** hreflang on noindex.  
- One public sitemap entrypoint with xhtml alternates.  
- **avoid** aggressive middleware locale redirects (geo / Accept-Language).  

---

## Astro

### Where things live

| Concern | Typical location |
|---------|------------------|
| i18n config | `astro.config.mjs` → `i18n.locales`, `defaultLocale`, `routing` |
| Pages | `src/pages/[locale]/...` or `src/pages/fr/...` |
| Content | content collections with `locale` field or per-locale folders |
| Registry | `src/i18n/locale-registry.json` (import in layouts) |
| Sitemap | `@astrojs/sitemap` with `i18n` option |

### hreflang

Generate in the base layout from the registry + known sibling map:

```astro
---
import { locales, defaultLocale, absoluteUrl } from '../i18n';
const twins = getTwins(Astro.url.pathname); // only existing indexable URLs
---
{twins.map(({ bcp47, href }) => (
  <link rel="alternate" hreflang={bcp47} href={href} />
))}
<link rel="alternate" hreflang="x-default" href={absoluteUrl(defaultTwin)} />
```

Skip the entire alternate block when `robots` includes `noindex`.

### Sitemap notes

- Configure `@astrojs/sitemap` `i18n.defaultLocale` + `i18n.locales` map (prefix → BCP47).  
- Filter out noindex / utility routes via `filter`.  
- Ensure a single entrypoint linked from `robots.txt`.

### Pitfalls

- Mixing unprefixed default pages with hardcoded `/en` links.  
- Using path prefix `fr-ca` as hreflang instead of `fr-CA`.  
- Emitting alternates for draft content collections.

Minimal sketch: [`../examples/astro-minimal/`](../examples/astro-minimal/).

---

## Next.js App Router

### Where things live

| Concern | Typical location |
|---------|------------------|
| Segment | `app/[locale]/layout.tsx`, `app/[locale]/page.tsx` |
| Messages | `messages/en.json`, `messages/fr-CA.json` (next-intl or similar) |
| Registry | `src/i18n/locale-registry.json` |
| Metadata | `generateMetadata` per route |
| Middleware | locale detection **without** forced redirects by default |

### Metadata / hreflang

```ts
// generateMetadata
alternates: {
  canonical: absoluteCanonical,
  languages: {
    'en': 'https://example.com/en/pricing',
    'fr-CA': 'https://example.com/fr/pricing',
    'x-default': 'https://example.com/en/pricing',
  },
},
```

Omit `alternates.languages` when the page is noindex.

### Middleware caveats

- **should:** remember locale preference in a cookie after explicit user choice.  
- **avoid:** redirecting every bare URL based on `Accept-Language` or IP.  
- If you rewrite to a locale prefix, keep a crawlable unprefixed → default strategy that doesn’t trap shared links.

### Sitemap

- `app/sitemap.ts` building URL entries with `alternates.languages`.  
- One route (`/sitemap.xml`) as the public entrypoint.

### Pitfalls

- `metadataBase` wrong → relative canonicals.  
- Client-only locale switchers with no `<a href>`.  
- Generating language alternates for routes that 404 in other locales.

See also: [`../examples/nextjs-app-router-notes.md`](../examples/nextjs-app-router-notes.md).

---

## Nuxt / Vue i18n

### Where things live

| Concern | Typical location |
|---------|------------------|
| Module | `@nuxtjs/i18n` in `nuxt.config.ts` |
| Locales | `locales: [{ code, language, file, dir }]` — map `language` to BCP47 |
| Pages | `pages/` with `strategy: 'prefix'` or `'prefix_except_default'` |
| SEO | `useLocaleHead()` / `useSeoMeta()` |

### hreflang

Prefer `useLocaleHead({ addSeoAttributes: true })` but **verify** BCP47 (`language` field) and disable alternates on noindex pages.

### Sitemap

- `@nuxtjs/sitemap` (or nitro crawler) with i18n multi-locale support.  
- Confirm xhtml:link alternates and single entrypoint.

### Pitfalls

- `code: 'fr'` used as hreflang while content is `fr-CA`.  
- `detectBrowserLanguage` redirect enabled by default — turn off for SEO-sensitive sites unless product requires it.  
- Lazy locale messages missing → English bleed without noindex.

---

## Remix

- Use path prefix (`/:locale`) or domain strategy via `routes`.  
- Set `<html lang={locale} dir={dir}>` in root.  
- Build hreflang in a shared `LocaleHead` component.  
- `sitemap.xml` resource route with xhtml alternates.  
- Be careful with loaders that fetch CMS content by locale — return 404 (not silent EN fallback) for missing translations that shouldn’t be indexed.

---

## Generic static HTML

- One folder per locale prefix: `/en/`, `/fr/`.  
- Shared head partial or build step injects canonical, og, hreflang.  
- Generate `sitemap.xml` at build time from a URL list + registry.  
- Language switcher is plain links between twin files.  
- Run:

```bash
python scripts/check_i18n_seo.py \
  --root dist \
  --registry locale-registry.json \
  --sitemap dist/sitemap.xml
```

---

## Adapter decision checklist

1. Where is the registry imported?  
2. Who generates canonical + og:url?  
3. Who generates hreflang (and suppresses on noindex)?  
4. Who builds the multilingual sitemap?  
5. Is middleware/redirect policy documented as non-coercive by default?  

# Next.js App Router — implementation notes

## Layout

```text
app/
  [locale]/
    layout.tsx      # <html lang dir>, shared chrome
    page.tsx
    pricing/page.tsx
  sitemap.ts
  robots.ts
src/i18n/
  locale-registry.json
  config.ts
middleware.ts         # optional preference cookie; avoid forced Accept-Language redirects
```

## generateMetadata pattern

- `alternates.canonical` = absolute locale URL  
- `alternates.languages` = BCP47 map + `x-default`  
- Omit `languages` when `robots: { index: false }`  

## Middleware

**should:** detect locale only to rewrite missing prefix to default, without trapping shared links.  
**avoid:** `Accept-Language` or geo-IP hard redirects as default SEO practice.

## Sitemap

`app/sitemap.ts` should emit `alternates.languages` for each indexable URL and be the single public entrypoint referenced by `robots.ts`.

Full adapter guidance: [`../docs/framework-adapters.md`](../docs/framework-adapters.md).

# Astro minimal sketch

Not a runnable app — a pattern sketch for where locale registry, pages, and hreflang live.

```text
src/
  i18n/
    locale-registry.json   # copy from templates/
    index.ts               # helpers: localePath, absoluteUrl, getTwins
  pages/
    [locale]/
      index.astro
      pricing.astro
  layouts/
    Base.astro             # html lang/dir, canonical, og:url, hreflang
```

See [`../../docs/framework-adapters.md`](../../docs/framework-adapters.md) → Astro.

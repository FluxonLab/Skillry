# SEO measurement (example)

## Properties / filters

| Locale | URL prefix | GSC filter / property | Analytics `page_locale` |
|--------|------------|-----------------------|-------------------------|
| en | `/en/` | page URL contains `/en/` | `en` |
| fr-CA | `/fr/` | page URL contains `/fr/` | `fr-CA` |
| es | `/es/` | page URL contains `/es/` | `es` |

## Sitemap

- Public entrypoint: `https://example.com/sitemap.xml`
- Confirmed in robots.txt: yes/no
- Confirmed in agent docs: yes/no

## CTR iteration loops (within locale)

For each **primary** locale, monthly:

1. Export queries for money pages filtered to that locale prefix.  
2. Improve title/meta **in that language** (do not reuse EN winners blindly).  
3. Re-check impressions → CTR → landing engagement.  

## Watchlist (new locales)

- Soft-404 / crawled – currently not indexed  
- Duplicate without user-selected canonical  
- Alternate page with proper canonical / hreflang errors  

## Conversion paths

Document locale-aware funnels (e.g. `/fr/pricing` → `/fr/contact`).  
Do not mix locale prefixes in a single conversion path definition.

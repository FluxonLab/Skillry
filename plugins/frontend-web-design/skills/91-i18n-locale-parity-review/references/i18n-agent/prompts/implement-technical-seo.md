# Prompt — Phase C: Implement technical SEO

Implement or specify the twelve technical signals from `SKILL.md` Phase C.

## Must implement / specify

1. Locale-aware routing helpers  
2. `<html lang>` + `dir`  
3. Self-canonical per locale  
4. `og:url` === canonical  
5. Localized titles/descriptions  
6. Reciprocal hreflang + `x-default` (BCP47)  
7. Suppress hreflang / og locale alternates on noindex  
8. One multilingual sitemap entrypoint  
9. robots + agent docs agree on sitemap URL  
10. JSON-LD `inLanguage` + localized page URLs; stable `@id`s  
11. Analytics `page_locale`  
12. CI gate using `scripts/check_i18n_seo.py`  

## Framework guidance

Read `docs/framework-adapters.md` for the detected stack.  
**avoid** aggressive locale middleware redirects.

## Done when

`checklists/technical-seo.json` items for in-scope pages pass or have tracked exceptions.

# Verification & CI

## Local checker

```bash
python scripts/check_i18n_seo.py \
  --root dist \
  --registry path/to/locale-registry.json \
  --sitemap dist/sitemap-0.xml \
  --format both \
  --fail-on error
```

Exit code is non-zero when errors are found.

Also:

```bash
python scripts/validate_locale_registry.py path/to/locale-registry.json
python scripts/validate_hreflang.py --root dist --registry path/to/locale-registry.json
```

## What CI must assert

| Assertion | Severity |
|-----------|----------|
| title, description, robots present | error |
| exactly one H1 | error |
| JSON-LD present on money pages (configurable) | warning/error |
| canonical present; origin/trailing-slash rules | error |
| `og:url` === canonical | error |
| `html[lang]` matches registry for path locale | error |
| hreflang BCP47 + `x-default` on indexable pages | error |
| no hreflang on noindex | error |
| sitemap samples include non-default locales | error |
| duplicate title/description across URLs | warning/error |
| hosting rules (https, apex) if configured | error |

Template workflow: [`../templates/github-actions-seo-check.yml`](../templates/github-actions-seo-check.yml).

## Production spot-checks

After deploy, manually or with a URL list:

1. View-source: canonical, og:url, lang, hreflang, robots  
2. Confirm noindex pages have **zero** hreflang  
3. Fetch sitemap entrypoint; sample default + non-default locales  
4. Language switcher links resolve 200  
5. GSC: URL inspection on a new locale money page  
6. Analytics: `page_locale` populated  

Checklist: [`../checklists/production-verify.json`](../checklists/production-verify.json).

## Measurement docs

Keep a living doc (template: [`../templates/seo-measurement.example.md`](../templates/seo-measurement.example.md)):

- GSC filters by locale prefix  
- CTR iteration loops **within** locale  
- Soft-404 / not-indexed watch for new locales  

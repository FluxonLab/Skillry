# Prompt — Phase E: Verify production

Verify local build and production after localization.

## Local

```bash
python scripts/check_i18n_seo.py \
  --root dist \
  --registry path/to/locale-registry.json \
  --sitemap dist/sitemap.xml \
  --format both
```

Fix errors before deploy.

## Production spot-checks

Use `checklists/production-verify.json`:

- Live canonical, og:url, lang, hreflang, robots on money pages  
- noindex pages have no hreflang  
- Sitemap entrypoint + non-default locale samples  
- Language switcher 200s  
- Analytics `page_locale`  
- GSC URL inspection on new locale URLs  

## Update

`seo-measurement.md` (from template) with locale prefixes and CTR loop notes.

## Report

Pass/fail table + residual risks + `needs_native_review` leftovers.

# Prompt — Phase A: Audit

You are auditing a website/repo for multilingual SEO / i18n readiness using the **multilingual-i18n-seo** skill.

## Instructions

1. Read `SKILL.md` and `docs/multilingual-seo-checklist.md`.
2. Detect framework, routing, i18n libraries, content sources.
3. Inventory locales (or note absence), default locale, URL strategy.
4. Map money pages vs utility vs noindex.
5. Find analytics, sitemap, robots, schema injection points.
6. Run scripts when HTML/`dist/` exists:

```bash
python scripts/check_i18n_seo.py --root <dist-or-html> --registry <registry> --format both
```

7. Emit `audit-report.json` matching `schemas/audit-report.schema.json` plus a short human summary.
8. Use `checklists/pre-flight.json` and `checklists/technical-seo.json` as scoring guides.

## Output

- Findings grouped by checklist section (1–14)
- Severity: error / warning / info
- Recommended next phase: Plan (B) vs quick technical fixes (C)
- Explicit list of defaults you assumed

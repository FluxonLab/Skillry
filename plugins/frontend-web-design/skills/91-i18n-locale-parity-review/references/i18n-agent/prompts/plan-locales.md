# Prompt — Phase B: Plan locales

Plan locale architecture and localization scope. Do **not** assume equal investment across languages.

## Ask only if blocking

- Target locales + default / x-default
- Market priority per locale
- Formality / tone
- Slug policy (translate vs stable)
- Locked third-party URLs

## Produce

1. `locale-registry.json` (validate with `scripts/validate_locale_registry.py`)
2. `translation-plan.md` — scope, order, owners, risks (RTL, legal, currency, fonts)
3. Keyword-map approach per **primary** locale (adapt, don’t calque) — draft `keyword-map.md`
4. Glossary stub (do-not-translate + preferred terms)
5. Technical SEO gap list for Phase C

## Constraints

- URL prefix may differ from BCP47; document both.
- Prefer one vertical slice (first primary locale) before full roll-out.
- No geo-IP / Accept-Language force redirects in the plan.

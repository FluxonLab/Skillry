# Keyword map (example)

> Adapt keywords per locale. Do **not** calque English terms.  
> Machine-readable twin can follow `schemas/keyword-map.schema.json`.

## Defaults assumed

- Source locale: `en`
- Priority locales: `fr-CA` (primary), `es` (secondary)

## `/pricing`

| Locale | Primary keyword | Title draft | Meta draft | Notes |
|--------|-----------------|-------------|------------|-------|
| en | pricing plans | Pricing Plans \| Acme | Simple plans for teams of every size. | Brand suffix policy: `\| Acme` |
| fr-CA | forfaits tarifaires | Forfaits tarifaires \| Acme | Des forfaits simples pour les équipes de toutes tailles. | Prefer Canadian French phrasing |
| es | planes de precios | Planes de precios \| Acme | Planes sencillos para equipos de cualquier tamaño. | LATAM-neutral for secondary tier |

**Intent:** commercial / high — money page.

## `/services/web`

| Locale | Primary keyword | Title draft | Notes |
|--------|-----------------|-------------|-------|
| en | web development services | Web Development Services \| Acme | |
| fr-CA | services de développement web | Services de développement web \| Acme | Not “développement de sites web” if GSC shows other query wins |
| es | desarrollo web | Desarrollo web \| Acme | One primary only; secondaries in body |

## Rules

1. One primary keyword per locale URL.  
2. Rewrite for CTR in that language.  
3. Keep brand suffix consistent.  
4. Never invent volumes; mark research gaps explicitly.

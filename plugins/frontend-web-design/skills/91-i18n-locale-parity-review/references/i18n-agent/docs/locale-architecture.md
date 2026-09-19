# Locale Architecture

Design locales, URLs, and fallbacks before translating.

---

## Single source of truth

Maintain a `locale-registry.json` validated by:

```bash
python scripts/validate_locale_registry.py path/to/locale-registry.json
```

Each locale entry should include at minimum:

| Field | Purpose |
|-------|---------|
| `id` | Internal key (e.g. `en`, `fr-CA`) |
| `bcp47` | Language tag for `html[lang]` / hreflang (e.g. `fr-CA`) |
| `urlPrefix` | Path segment (e.g. `fr` or `fr-ca`) — **may differ** from BCP47 |
| `dir` | `ltr` or `rtl` |
| `ogLocale` | Open Graph locale (e.g. `fr_CA`) |
| `label` | Native endonym for switchers |
| `marketPriority` | `primary` \| `secondary` \| `maintain` |
| `enabled` | Whether publicly shipped |

Example: [`../templates/locale-registry.example.json`](../templates/locale-registry.example.json).

---

## URL strategies

| Strategy | Example | Notes |
|----------|---------|-------|
| Prefix all locales | `/en/...`, `/fr/...` | Clearest; slightly longer default URLs |
| Default unprefixed | `/...` + `/fr/...` | Common; must never leak unprefixed links on other locales |
| Subdomain | `fr.example.com` | Heavier ops; keep hreflang absolute |
| Separate TLD | `example.fr` | Strong market signal; complex CMS |

**must:** pick one strategy and keep trailing-slash + host canonicalization consistent.

### Slug ≠ hreflang

- Path: `/fr/services/web`  
- hreflang / `lang`: `fr-CA` (BCP47)  
Never emit hreflang=`fr` when the registry’s BCP47 is `fr-CA` unless you intentionally ship a generic `fr` locale.

---

## Default locale & x-default

- `x-default` **must** point at the genuine default-locale experience (usually the marketing default, not a chooser page—unless the chooser *is* the intentional default).  
- Document whether the default uses a prefix.  

---

## Routing helpers

Provide helpers so templates never hardcode default-locale paths:

```text
localePath(locale, path) → "/fr/pricing"
switchHref(fromPage, targetLocale) → sibling URL or null if missing
```

**must:** if a twin is missing, language switcher omits or disables the link; do **not** point at the wrong language.

---

## Fallback policy

Document one of:

1. **Omit** — page absent; excluded from hreflang/sitemap  
2. **Fallback content** with clear UX (and usually **noindex** until translated)  
3. **Soft redirect** to default locale **only** as an explicit product choice (not silent Accept-Language)

**avoid:** auto-redirect by IP or `Accept-Language` as the default SEO practice. Offer a visible language switcher instead.

---

## Content layers

| Layer | Examples | Ownership |
|-------|----------|-----------|
| UI chrome | nav, buttons, errors | message catalogs / i18n lib |
| Structured data | collections, CMS fields | content pipeline |
| Page bodies | MDX/Markdown per locale | content repo |
| SEO fields | title, description, og | per-locale frontmatter or CMS |
| Media | alt, captions | assets + locale fields |

Keep **stable content IDs** across locales so hreflang clusters stay aligned.

---

## Risks to call out in the plan

- RTL layout + font loading  
- Date / number / phone / address formats  
- Currency and tax display  
- Legal jurisdiction differences  
- Brand terms that stay English  
- Translated vs stable URL slugs (redirect map if changing)  

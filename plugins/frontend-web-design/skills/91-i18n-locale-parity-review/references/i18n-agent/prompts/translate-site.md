# Prompt — Phase D: Translate site

Follow `docs/translation-playbook.md` exactly.

## Process

1. Load registry, glossary, style notes, keyword map.
2. Inventory strings/pages in scope; tag types (`ui`, `marketing`, `seo_*`, `legal`, …).
3. Draft with the correct approach (transcreate / precise / adapt).
4. SEO adaptation: one primary keyword per locale URL; local CTR titles/metas.
5. Terminology → locale QA → parity QA → link QA → SEO QA.
6. Mark `needs_native_review` for legal / high-risk claims.
7. Store approved pairs in translation memory when applicable.

## Reject if

Machine-sounding calques, mixed formality, broken ICU/placeholders, keyword stuffing, invented claims, RTL bugs, casual legal rewrites.

## Do not

- Translate locked third-party URLs
- Publish hreflang for pages below the quality bar (use noindex until ready)
- Calque English keyword maps

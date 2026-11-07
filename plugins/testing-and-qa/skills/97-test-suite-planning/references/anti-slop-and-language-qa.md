# Interface Authenticity, Visual Quality, and Multilingual QA

Review procedures and quality checklists for outward-facing interfaces, mobile screen design, copy authenticity, and native-language localization.

---

## 1. UI, Mobile, and Copy Authenticity Review

Every outward-facing interface, mobile screen, store listing, presentation, email template, and published deliverable must pass an authenticity and anti-slop review before release candidate sign-off.

### Review Principles & Boundaries
- **Design Review Authority:** Visual design quality and aesthetic sign-off should be conducted by a designated design lead or specialized visual reviewer using design system guidance (see `web-design-review` and `mobile-app-review`).
- **Verified Open Tools:**
  - Automated prose and AI-pattern critique tools to flag repetitive syntactical tells.
  - UI design audit kits and component reviews (e.g., Storybook, design token linting).
- **Adaptation Over Verbatim Cloning:**
  - When adapting UI patterns or motion from reference sites, extract underlying principles (spacing rhythm, typography hierarchy, easing curves) and integrate them into your own design system. Never duplicate third-party code, CSS, or motion 1:1.
  - Extract motion timing and easing values from live browser captures rather than static screenshots.

### Visual & Mobile Inspection Procedure
1. **Verify a Domain-Specific Visual Concept:**
   - Confirm the interface is grounded in a deliberate visual identity tailored to the product's problem space.
   - Reject generic template patterns: unmotivated purple/indigo glowing gradients, floating neon badges with fake metrics, and repetitive card layouts without functional hierarchy.
2. **Verify Asset Authenticity and Provenance:**
   - Confirm imagery, diagrams, and illustrations are authentic and project-specific.
   - Do not reuse graphics across unrelated projects or deploy generic stock imagery for core product interactions.
   - Never use fabricated device mockups or synthetic UI screenshots in place of actual running app captures.
3. **Inspect Real Mobile Viewports and Touch Ergonomics:**
   - Render and review screens on real device viewports or realistic emulator resolutions with platform-standard typography (SF Pro on iOS, Roboto/system tokens on Android, or the brand's licensed typeface).
   - Verify minimum touch targets (>= 44×44 pt on iOS, >= 48×48 dp on Android).
   - Ensure native mobile navigation ergonomics: avoid forcing desktop web navbars onto mobile screens. Respect safe area insets (notches, Dynamic Island, home indicators, status bars).

### Visual & Copy Authenticity Checklist
- [ ] **Deliberate visual identity:** Typography, color tokens, spacing scale, and elevation reflect a coherent product theme rather than default framework templates.
- [ ] **Adapted patterns:** Reference inspirations are adapted into the project's own design system; zero verbatim 1:1 copied components or CSS.
- [ ] **Authentic media:** Graphics and screenshots are original and project-specific; zero reused generic stock packs or fake mockups.
- [ ] **No fabricated claims:** Zero invented testimonial quotes, unverified star ratings, artificial user counts, or unsubstantiated marketing superlatives.
- [ ] **Natural, purposeful prose:** Zero AI boilerplate ("In today's fast-paced world", "Unleash the full potential of", "Seamlessly integrates"), no unnecessary emoji bullets, and no repetitive triadic buzzword lists.
- [ ] **Realistic state data:** Sample records and onboarding screens use realistic, domain-accurate fixtures (avoiding generic placeholders like `Test User 123` or `Lorem Ipsum` in release builds).

---

## 2. Multilingual and Native-Language Quality Assurance

Applications targeting multiple languages, international App Store / Play Console markets, or multilingual user bases must pass locale parity and linguistic review before release.

### Language Rules and Registers
- **Locale Reference Standards:**
  - Standard reference locales commonly tested in internationalized releases include: English (`EN`), Turkish (`TR`), German (`DE`), French (`FR`), Spanish (`ES`), Brazilian Portuguese (`PT-BR`), Italian (`IT`), Dutch (`NL`), Polish (`PL`), Russian (`RU`), Czech (`CS`), Japanese (`JA`), Korean (`KO`), Chinese (`ZH`), Vietnamese (`VI`), Arabic (`AR`), and Indonesian (`ID`).
  - Maintain a project glossary of approved technical and domain terms for each target locale.
- **Formality Register Alignment:**
  - Ensure grammatical formality matches product positioning (for example, formal "Sie" in German or formal "siz" in Turkish when targeting professional enterprise audiences, unless the brand tone specifically mandates informal address).
- **Communication vs. Product Language:**
  - Development logs, commit messages, and internal issue tracking follow project team conventions.
  - User-facing UI strings, push notifications, emails, and store metadata strictly follow the target locales configured for the release.

### Multilingual QA Procedure
1. **Audit Locale Key Parity (`i18n-locale-parity-review`):**
   - Scan source code for hard-coded user-facing strings; ensure all customer-facing text is externalized to locale resource catalogs.
   - Compare every target locale file against the base locale: verify zero missing keys, zero untranslated fallbacks, and identical interpolation placeholders (`{count}`, `%s`, `{{name}}`).
2. **Verify Grammatical and Regional Formatting:**
   - Test CLDR plural rules across numbers (`zero`, `one`, `two`, `few`, `many`, `other`) and gender/case inflections in target languages.
   - Verify date, time, currency, and numerical formatting using standardized runtime formatters (`Intl` APIs or platform localization frameworks).
3. **Inspect Layout Under Text Expansion and RTL:**
   - Test user interfaces with languages prone to length expansion (e.g. German, French, Russian, Portuguese) with +30–40% text expansion on compact mobile viewports.
   - Confirm labels do not clip, primary call-to-action buttons do not wrap awkwardly, and text does not truncate mid-word.
   - For right-to-left (RTL) languages like Arabic, verify complete layout mirroring, directional navigation icons, and bidirectional text handling for numbers and links.
4. **Audit for Translationese and Native Search Intent:**
   - Eliminate awkward word-for-word translation calques from the base language. Ensure copy reads as natural prose written directly by a native speaker.
   - Verify App Store and Play Console keywords, subtitles, and headings match the actual phrases native users enter in local search fields.

### Multilingual QA Checklist
- [ ] **Zero hard-coded strings:** All customer-facing text, validation messages, and system notifications live in external locale catalogs.
- [ ] **100% key and parameter parity:** All target locales have complete translation keys with matching variable interpolation tokens.
- [ ] **Formality and glossary compliance:** Register (formal/informal) and industry terminology strictly follow project tone guidelines.
- [ ] **Natural linguistic phrasing:** Free of literal machine-translation artifacts, awkward grammatical structures, and repetitive translationese.
- [ ] **Visual expansion tolerance:** UI layouts survive 30–40% text length expansion without broken buttons, overlapping elements, or truncation.
- [ ] **Bidirectional & RTL layout:** Mirrored layout, appropriate text alignment, and correct directional iconography in RTL locales.
- [ ] **Store & discovery localization:** Store metadata, captions, and headings reflect natural local search terms while accurately stating verified product capabilities.

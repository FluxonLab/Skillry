---
name: nfc-linktree-menu-builder-review
description: Use when you need to review NFC card, linktree, menu builder, QR, profile page, and tap-to-open product flows.
---

# NFC / Linktree / Menu Builder Review

## Purpose
Review the architecture, user experience, security, and reliability of NFC-triggered digital experiences: link-in-bio / linktree pages, QR code generators, restaurant/event menu builders, digital business card (vCard) flows, short-link redirectors, and dynamic profile pages optimized for mobile-first tap-to-open interactions.

## When to use
- Reviewing a product where an NFC chip or QR code redirects to a profile, menu, or link list.
- Auditing a short-link or redirect service that backs NFC URL chips.
- Evaluating a drag-and-drop menu or profile builder and its generated output.
- Reviewing vCard/hCard generation or `.vcf` download flows.
- Checking mobile-first landing pages intended for NFC tap users (often time-sensitive, low tolerance for load failures).

## When not to use
- General marketing landing page review with no NFC/QR/short-link component.
- Backend API review with no mobile UX surface.
- Print-side NFC card design review — use `83-print-design-artifact-review` for that.

## Procedure

### 1. NFC URL routing
- Verify the NFC target URL is HTTPS — HTTP URLs may be blocked by Android/iOS browsers or trigger security warnings.
- Short-link resolution must be a single redirect (301 permanent or 302 temporary), not a chain of 3+ hops, which adds latency on mobile networks.
- Dynamic URLs (e.g., `https://tap.example.com/c/abc123`) must not expose internal database IDs; use short opaque tokens.
- Check that the redirect service handles high concurrency: NFC taps at an event can spike simultaneously.
- Verify that disabled or expired NFC cards redirect to a graceful fallback page, not a 404 or blank screen.

### 2. QR code generation and correctness
- QR code error correction level: minimum **M** (15% recovery); for cards likely to be scratched or printed small, use **H** (30%).
- QR payload must encode the final destination URL, not an intermediate redirect — unless the redirect is intentional for tracking.
- Generated QR images must be served as SVG (scalable) or PNG at ≥ 500 × 500 px for print use.
- Verify the QR can be decoded by at least two independent QR scanners before marking as production-ready.
- Check that special characters in URLs are percent-encoded inside the QR payload.

### 3. Profile / linktree page builder
- Builder output must generate valid, semantic HTML — verify no unclosed tags, duplicate IDs, or accessibility violations (buttons without labels, images without alt).
- Custom slugs/usernames must be sanitized: alphanumeric + hyphen only, length capped (e.g., 3–50 chars), reserved words blocked (`admin`, `api`, `static`).
- Profile image uploads: validate MIME type server-side (not just file extension), enforce size limits (e.g., max 2 MB), strip EXIF data before storage.
- Link entries must be URL-validated server-side (`http://` or `https://` scheme only) to prevent `javascript:` XSS payloads.
- Ordering/drag-and-drop: persisted sort order must use an optimistic-update pattern with a server confirmation; if the save fails, revert visually.

### 4. Restaurant/event menu builder
- Menu data model: `Category → Item → Variants → Modifiers`. Verify the schema supports all required nesting levels.
- Multilingual menus: text fields must support Unicode fully; RTL scripts (Arabic, Hebrew) need `dir="rtl"` on the container.
- Item availability toggles (sold out, seasonal) must propagate to the public menu page within seconds, not requiring a full publish cycle.
- Allergen/dietary flags (GF, vegan, nuts) must be editable per item and rendered prominently — legal risk if missing or incorrect.
- PDF export of menus: verify fonts are embedded and layout does not break at A4/Letter sizes.

### 5. vCard / digital business card
- `.vcf` files must use vCard 3.0 or 4.0 format; verify with a validator before exposing the download endpoint.
- Fields: `FN`, `TEL`, `EMAIL`, `URL`, `ORG`, `ADR` — all values must be escaped per RFC 6350 (colons, semicolons, backslashes).
- Photo embedding in vCard must be Base64-encoded JPEG/PNG under ~100 KB — large photos cause iOS Contacts import failures.
- Download link should serve with `Content-Type: text/vcard` and `Content-Disposition: attachment; filename="name.vcf"`.
- Never store phone numbers or emails in the URL query string — use the vCard download endpoint directly.

### 6. Dynamic content and real-time updates
- If menu/profile content is edited while the NFC card is already deployed, the redirect must serve the updated content without requiring a new NFC chip reprogram.
- Cache headers on profile pages: `Cache-Control: no-store` or very short TTL (< 60 s) for mutable content; longer TTL only for truly static assets (logos, fonts).
- CDN edge caching must not cache personalized or owner-edited pages by default.

### 7. Mobile-first performance
- First Contentful Paint target: < 1.5 s on a 4G connection.
- No render-blocking scripts on the initial tap landing page.
- Touch targets: buttons/links ≥ 44 × 44 px (Apple HIG) / 48 dp (Material).
- Avoid carousels or complex animations — users on NFC tap are in a brief attention window.
- Test on both iOS Safari and Android Chrome; WebKit and Blink differ on certain CSS behaviors.

### 8. Analytics and tracking
- UTM parameters appended to NFC redirect URLs for source attribution (`utm_source=nfc&utm_medium=card&utm_campaign=...`).
- If analytics pixels are present, ensure consent is collected where required (GDPR/ePrivacy) before firing non-essential tracking.
- Short-link click counts must use server-side counters, not client-side events, to survive adblocker interference.

## Checklist

NFC routing:
- [ ] Target URL is HTTPS; no HTTP redirects.
- [ ] Redirect chain is ≤ 2 hops.
- [ ] Expired/disabled cards show a graceful fallback page.
- [ ] Short-link tokens are opaque (not sequential database IDs).

QR:
- [ ] Error correction level M or H.
- [ ] SVG or high-res PNG generated.
- [ ] Decoded successfully by two independent scanners.

Profile / menu builder:
- [ ] Custom slugs sanitized; reserved words blocked.
- [ ] Link entries URL-validated server-side (no `javascript:` scheme).
- [ ] Image uploads: MIME validated server-side, EXIF stripped.
- [ ] Allergen/dietary flags present and editable (menu builder).

vCard:
- [ ] Valid vCard 3.0/4.0 format.
- [ ] `Content-Type: text/vcard` on download endpoint.
- [ ] Embedded photo < 100 KB.

Performance:
- [ ] FCP < 1.5 s on 4G.
- [ ] No render-blocking scripts on landing page.
- [ ] Touch targets ≥ 44 × 44 px.

## Common issues & anti-patterns

- **HTTP NFC target URL**: some Android browsers warn or block non-HTTPS; always use HTTPS.
- **Sequential numeric IDs in short links**: `tap.example.com/r/1001` exposes enumerable user profiles. Use random tokens.
- **`javascript:` in link fields**: a builder that accepts arbitrary URLs without scheme validation is an XSS vector for other users who view the page.
- **QR at error correction L with small print size**: the code becomes unreadable when the card scratches slightly.
- **Long vCard photo**: iOS Contacts silently fails to import vCards where the embedded image exceeds ~200 KB.
- **Edge cache serving stale menu**: a restaurant marks a dish as sold out but NFC users see it available for 24 hours due to aggressive CDN TTL.
- **No fallback for disabled NFC chip**: user gets a generic 404, with no context about the expired campaign.
- **Non-UTF-8 encoding in QR payload**: special characters (accented, CJK) in a URL break scan on some readers.

## Required output

Return a structured report with:
- **Summary**: pass / needs fixes / blocked, primary risk (UX, security, data).
- **Evidence**: specific file or URL path and line references for each finding.
- **Findings table**: severity, category, description, remediation.
- **Mobile UX assessment**: performance and touch-target status.
- **NFC/QR integrity check**: redirect chain, error correction, scan test result.
- **Next handoff**: end-to-end physical tap test on real NFC hardware before launch.

## Safety

- Never encode real customer PII (home address, unmasked phone) in QR payloads used for review examples.
- Do not reprogram or write to physical NFC chips during a code review.
- Flag any URL scheme injection (`javascript:`, `data:`) in link fields as high severity.
- If allergen labels are missing in a menu builder serving food-service customers, flag as high (legal risk).

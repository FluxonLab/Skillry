---
name: analytics-tracking-review
description: Use when you need to review analytics events, tracking plans, privacy, attribution, dashboards, and conversion instrumentation.
---

# Analytics & Tracking Review

## Purpose
Review analytics instrumentation for correctness, completeness, privacy compliance, and data quality. Covers event taxonomy design, dataLayer implementation, GA4 / Plausible / Amplitude / Mixpanel event schemas, tracking plan adherence, PII handling, GDPR/CCPA consent gating, duplicate event prevention, and debug/validation practices.

## When to use
- Reviewing code that fires analytics events (`gtag`, `dataLayer.push`, `analytics.track`, `plausible`).
- Auditing a tracking plan against an implementation.
- Evaluating a GA4 tag configuration or Google Tag Manager container.
- Checking for PII leakage into analytics payloads.
- Reviewing conversion event setup (purchase, lead, sign-up) for accuracy.
- Investigating duplicate events, missing events, or attribution discrepancies.

## When not to use
- Business intelligence / SQL reporting review with no front-end instrumentation — use a data engineering review.
- Ad platform pixel review only (Meta Pixel, TikTok Pixel) without any consent or data layer component — flag and scope separately.
- Server-side log analysis with no tracking library involved.

## Procedure

### 1. Event taxonomy and naming conventions
- Event names must follow a consistent convention: `noun_verb` (e.g., `product_viewed`, `checkout_started`, `order_completed`) or the platform's standard events (`purchase`, `add_to_cart` for GA4 Ecommerce).
- Casing must be consistent across all events — mixing `camelCase` and `snake_case` in the same dataset creates irreconcilable segmentation issues.
- GA4 reserved event names must not be reused for custom events (`page_view`, `session_start`, `user_engagement` are auto-collected).
- Event names must be descriptive enough to be self-documenting — `click` alone is unusable; `cta_button_clicked` with a `button_id` parameter is correct.

### 2. Tracking plan adherence
- Obtain the tracking plan document (spreadsheet, Avo, Segment Protocols, or equivalent).
- For each planned event: verify it fires, fires only once per user action, and includes all required properties.
- For each fired event: verify it appears in the tracking plan. Undocumented events are technical debt.
- Parameter types must match the tracking plan: a `price` property should always be a `Number`, never a string `"19.99"`.
- Required properties with null/undefined values cause silent data gaps. Verify fallback values or conditional firing logic.

### 3. Dataayer implementation (GTM)
- `dataLayer.push()` must fire before the GTM trigger evaluates — push then trigger, never trigger then push.
- Each push should be a complete object: `{ event: 'event_name', param1: val1 }` — do not rely on previous dataLayer state accumulating.
- Ecommerce object structure must follow the GA4 Ecommerce schema: `items` array with `item_id`, `item_name`, `price`, `quantity`, `currency` at the event level.
- `dataLayer.push({ ecommerce: null })` must be called before each ecommerce event push to clear previous ecommerce data.
- Variable names in GTM must not shadow built-in variables (e.g., do not create a custom variable named `Page URL`).

### 4. PII detection and scrubbing
- Scan all event property values for PII: email addresses, phone numbers, full names, postal codes, IP addresses, user IDs linked to real identities.
- **Email addresses must never appear as event property values** — this violates GA4 terms of service and GDPR.
- User IDs sent to GA4 must be pseudonymous (hashed or random UUID), not the raw database primary key or email.
- URL parameters containing PII (e.g., `?email=user@example.com`, `?token=...`) must be redacted before the page URL is sent as a property or `page_location`.
- Check search query tracking: `site_search` events must strip any PII that users might type into search boxes.

### 5. GDPR / CCPA consent gating
- Non-essential tracking (advertising cookies, analytics beyond basic audience measurement) must not fire before the user grants consent.
- GTM Consent Mode v2: verify `ad_storage`, `analytics_storage`, `ad_user_data`, `ad_personalization` are set to `denied` by default and updated to `granted` only after consent.
- First-party analytics (Plausible, Fathom): these tools are typically consent-exempt in many GDPR interpretations — but verify no cross-site identifiers are set.
- Consent state must persist across page loads; re-asking on every page load is a CMP misconfiguration.
- Opt-out: verify that revoking consent stops future event collection and triggers `consent_update` → `denied`.

### 6. Duplicate event prevention
- Identify events that could fire multiple times: form `submit` events on SPAs that re-render without navigation, scroll-depth events with no debounce, page-view events on hash-change routers.
- SPA route changes: ensure `page_view` fires exactly once per virtual page transition, not on every component re-render.
- `purchase` / `order_completed` events: must fire exactly once per order ID. Implement deduplication: check `sessionStorage` or a cookie for the order ID before firing; clear after firing.
- Scroll-depth events (25%, 50%, 75%, 100%): use a fired-flags map to ensure each threshold fires once per page load.

### 7. Conversion event accuracy
- `purchase` event: `transaction_id` must be the order ID (not a random value), `value` must be the order total (post-discount, pre-tax or post-tax — be consistent), `currency` must be the 3-letter ISO code.
- `generate_lead` / `sign_up`: fire only after server-side confirmation, not on form submission (submission can succeed without a valid server response).
- Do not fire conversion events in development/staging environments — use the GA4 Debug View or Plausible staging property for dev, not the production property.
- Attribution: conversion events fired client-side rely on the cookie/session; server-side conversion import (GA4 Measurement Protocol) provides more reliable attribution.

### 8. Debug and validation
- GA4 DebugView: enable via `?gtm_debug=true` or the GA Debugger extension to validate events before production release.
- GTM Preview Mode: use to trace trigger → tag → dataLayer push sequence for every event.
- Plausible / Amplitude / Mixpanel: each has a live event stream for real-time validation.
- Automated testing: use Playwright or Cypress to assert `dataLayer` pushes in CI — `cy.window().its('dataLayer').then(dl => expect(dl).to.deep.include({...}))`.
- Schema validation: implement a runtime schema validator (Avo, Iteratively, or custom JSON Schema) that warns in dev when event payloads do not match the tracking plan.

## Checklist

Event taxonomy:
- [ ] Consistent naming convention (snake_case) across all events.
- [ ] No reuse of GA4 reserved event names for custom events.
- [ ] All fired events documented in the tracking plan.
- [ ] All planned events implemented and verified to fire.

Data quality:
- [ ] Numeric properties (`price`, `quantity`, `value`) are Numbers, not strings.
- [ ] Required properties never send null/undefined — have fallback values or conditional firing.
- [ ] `ecommerce: null` pushed before each ecommerce event.
- [ ] `transaction_id` is the actual order ID, not a random value.

PII:
- [ ] No email addresses in any event property.
- [ ] User IDs are pseudonymous (hashed or UUID).
- [ ] URL parameters with PII redacted before `page_location` is sent.
- [ ] Search queries checked for PII.

Consent:
- [ ] Non-essential tracking gated on consent.
- [ ] GTM Consent Mode v2 defaults to `denied`.
- [ ] Consent state persists across page loads.
- [ ] Opt-out revokes future tracking.

Duplicates:
- [ ] `purchase` event fires exactly once per order ID.
- [ ] `page_view` fires once per SPA route change.
- [ ] Scroll-depth thresholds fire at most once per page load.

## Common issues & anti-patterns

- **Email in `user_id` parameter**: sending `user@example.com` as the GA4 user ID violates ToS and is a PII leak. Hash it with SHA-256.
- **`purchase` event on page load without deduplication**: a user refreshes the thank-you page and the purchase event fires a second time, inflating revenue. Gate it on a seen-order-ID check.
- **Ecommerce push without clearing**: the previous `items` array bleeds into the next ecommerce event. Always push `{ ecommerce: null }` first.
- **Analytics firing before consent**: the CMP loads asynchronously; if GTM fires before it initializes, events are sent without consent validation.
- **`page_view` on every React re-render**: a route change listener fires `page_view` but so does a parent component re-render — results in 3–5× inflated page-view counts.
- **String prices**: `"19.99"` instead of `19.99` causes GA4 to report `$0` revenue for that item because the type is wrong.
- **No staging/production separation**: developers triggering test conversions in production inflate conversion data and distort CPA metrics.
- **Undocumented events**: events fired in code but absent from the tracking plan are invisible to analysts. They also get silently dropped when the next tracking plan audit prunes unrecognized events.

## Required output

Return a structured report with:
- **Summary**: pass / needs fixes / blocked (PII leak or consent violation).
- **Tracking plan coverage**: number of planned events implemented vs missing.
- **PII audit**: specific properties or patterns where PII was found or is at risk.
- **Consent assessment**: consent mode configuration status, default states.
- **Findings table**: severity (critical / high / medium / low / info), category, file + line or event name, description, remediation.
- **Duplicate event analysis**: events at risk of double-firing and mitigation status.
- **Next handoff**: debug validation steps (GA4 DebugView checklist, Cypress dataLayer assertions recommended).

## Safety

- Do not modify live GTM containers or GA4 properties during review.
- Do not trigger test conversions or purchases in production analytics properties.
- If real user email addresses or PII are found in event payloads during review, flag as critical and do not log or retain that data beyond the finding report.
- Never share raw analytics export data containing PII outside the review scope.

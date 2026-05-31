---
name: landing-page-conversion-review
description: Use when you need to review landing pages, first viewport signal, offer clarity, trust, and conversion friction.
---

# Landing Page Conversion Review

## Purpose
Evaluate a landing page for conversion effectiveness: clarity of the above-the-fold message, offer legibility, social proof quality and placement, CTA prominence and friction, form field count, and trust signals. Produces prioritized findings tied to specific conversion mechanics — not generic design advice.

## When to use
- A new landing page is ready to launch and needs a pre-launch conversion review.
- Conversion rate or lead volume is below expectations and a UX diagnosis is needed.
- A/B test ideas are needed for the hero section, CTA, or form.
- A paid traffic campaign is about to drive significant traffic to a page that has not been reviewed.

## When not to use
- The page is an internal app or dashboard (use `dashboard-ux-review`).
- The request is only about visual design quality unrelated to conversion (use `web-design-review`).
- The request is about email campaigns or ad creative — this skill covers the landing page only.
- The page has no conversion goal (e.g., a pure blog post or about page).

## Procedure

1. **Define the conversion goal.** Before reviewing anything: what is the desired primary action? (Sign up, book a demo, start a trial, download a lead magnet, make a purchase.) Every finding must be evaluated against whether it helps or hurts that one action.

2. **Apply the 5-second test to the hero.** Read only the H1, H2 (or subheadline), and primary CTA. After 5 seconds, can a cold visitor answer: (a) What does this product do? (b) Who is it for? (c) What do I do next? If any of these is ambiguous, the hero copy is a Critical finding.

3. **Evaluate above-the-fold completeness.** Without scrolling, the viewport should contain: the primary value proposition (H1 + subheadline), a primary CTA button, and at minimum one trust signal (logo bar, review stars, or badge). If the primary CTA is below the fold even on a 1080p screen, that is a Critical finding.

4. **Audit CTA clarity and friction.** Check the CTA button label — it must communicate what happens after clicking ("Start free trial", "Get my free audit", "Book a 20-minute demo") not just "Submit" or "Go". Check whether clicking the CTA requires form input before value is delivered. Each required form field before the conversion event adds ~5-10% drop-off; flag any form with > 3 fields for a lead generation goal or > 5 for a demo booking.

5. **Evaluate social proof.** Identify all trust elements: testimonials, logos, review counts, case study stats, media mentions, security badges. Check placement: social proof is most effective directly adjacent to or just below the primary CTA. Check specificity: "We love it!" is weak; "We reduced onboarding time by 40% in the first month — Sarah, Head of Ops at Stripe" is strong. Logos without names are weaker than named testimonials.

6. **Check for friction elements.** Flag: required account creation before value delivery, credit card required for a "free" trial without prominent disclosure, terms in fine print that contradict the headline offer, mandatory phone number fields for non-sales-led products, and CAPTCHA on the primary conversion form.

7. **Assess the page length and scroll depth logic.** Longer pages convert better for high-consideration offers (B2B SaaS, high-price products). Short pages work for low-friction actions (free tool, email signup). Check whether the page length matches the offer complexity. A one-field email capture form should not have 8 sections of marketing copy before the CTA.

8. **Verify CTA repetition.** For pages longer than two viewport-heights, the primary CTA should repeat at least once in the body and once in a sticky header or footer. A visitor who scrolls past the hero should never have to scroll back up to convert.

9. **Review the thank-you / post-conversion state.** What happens immediately after the primary CTA is clicked? A blank page, generic "Thank you", or a 404 is a leak. The post-conversion state should confirm the action, set expectations (e.g., "Check your inbox"), and offer a next step.

10. **Flag technical conversion risks.** Look for: page load weight > 3MB (slow loads kill mobile conversion), no Open Graph tags (breaks social sharing), no canonical URL (SEO/attribution risk), missing form validation with clear error messages.

## Checklist
- [ ] H1 + subheadline passes 5-second test: product, audience, and value are immediately clear
- [ ] Primary CTA is visible above the fold on a 1366x768 viewport (common laptop resolution)
- [ ] CTA label communicates what happens after clicking — not "Submit" or "Get started" alone
- [ ] Lead gen forms have <= 3 required fields; demo booking forms have <= 5
- [ ] At least one trust signal (logo bar, star rating, testimonial) visible above the fold
- [ ] Testimonials include name, title, company, and a specific outcome — not generic praise
- [ ] No mandatory credit card or phone number for a stated "free" offer without prominent disclosure
- [ ] Primary CTA repeats at least once below the hero on pages taller than two viewports
- [ ] Post-conversion state confirms action, sets expectations, and provides a next step
- [ ] Page loads in under 3 seconds on a throttled 4G connection (check with Lighthouse)
- [ ] No auto-playing video or audio that cannot be immediately dismissed
- [ ] Mobile viewport shows CTA and value proposition without horizontal scroll or truncation

## Common issues & anti-patterns
- **Feature-first hero:** H1 lists three product capabilities instead of one clear outcome for the user ("AI-powered analytics" vs. "Know which campaigns drive revenue, not just clicks").
- **CTA below the fold on launch:** hero section has a full-screen background image and a headline — the CTA button is the first thing below the image, requiring a scroll.
- **Generic testimonials:** three quotes from "Happy customer" with no company, no outcome, no photo — indistinguishable from fabricated content.
- **Form overreach:** a lead-magnet download form that requires name, email, phone, company, company size, and role — 80% of visitors abandon at field 4.
- **Buried pricing disclaimer:** "Free for 14 days, then $99/month" visible only in 11px gray text below the fold.
- **Dead thank-you page:** after form submit, a blank page with "Thank you!" and no follow-up instructions — no email confirmation either.
- **CTA label mismatch:** button says "Get started free" but clicking opens a pricing page, not a signup form.

## Required output
Return a structured report with:
1. **Conversion readiness verdict** (Ready / Needs work / Not ready) with a 1-sentence rationale.
2. **5-second test result**: exact H1 and subheadline text evaluated, pass/fail, and rewrite suggestion if failed.
3. **Critical findings** (up to 3): above-the-fold gaps, form friction, or trust signal absence.
4. **Major findings** (up to 5): CTA repetition, social proof quality, post-conversion state.
5. **A/B test ideas** (top 3): hypothesis + predicted impact + what to measure.
6. **Technical risks**: any load speed, mobile, or metadata issues found.

## Safety
- Do not rewrite production copy without explicit instruction — provide suggested alternatives, not replacements.
- Clearly separate opinion ("this testimonial reads as weak") from measurable fact ("form has 7 required fields").
- Do not make claims about expected conversion rate improvements — conversion depends on traffic quality and many factors outside scope.

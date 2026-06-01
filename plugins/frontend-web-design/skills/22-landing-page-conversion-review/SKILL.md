---
name: landing-page-conversion-review
description: Use when you need to review landing pages, first viewport signal, offer clarity, trust, and conversion friction.
---

# Landing Page Conversion Review

## Purpose

Evaluate a landing page for conversion effectiveness: clarity of the above-the-fold message, offer legibility, social-proof quality and placement, CTA prominence and friction, form-field count, and trust signals. Findings are tied to specific conversion mechanics and stated as measurable observations (field counts, fold position, load time) rather than generic design advice, so each one maps to a concrete change or an A/B test hypothesis.

## When to use

- A new landing page is ready to launch and needs a pre-launch conversion review.
- Conversion rate or lead volume is below expectations and a UX diagnosis is needed.
- A/B test ideas are needed for the hero section, CTA, or form.
- A paid-traffic campaign is about to drive significant traffic to an unreviewed page.

## When not to use

- The page is an internal app or dashboard — use `dashboard-ux-review`.
- The request is only about visual design quality unrelated to conversion — use `web-design-review`.
- The request is about email campaigns or ad creative — this skill covers the landing page only.
- The page has no conversion goal (a pure blog post or about page).

## Procedure

1. **Define the conversion goal.** What is the single desired primary action? (Sign up, book a demo, start a trial, download a lead magnet, purchase.) Every finding is evaluated against whether it helps or hurts that one action.
2. **Apply the five-second test to the hero.** Reading only the H1, the subheadline, and the primary CTA, can a cold visitor answer: what the product does, who it is for, and what to do next? Any ambiguity here is a Critical finding.
3. **Evaluate above-the-fold completeness.** Without scrolling, the viewport should contain the value proposition (H1 plus subheadline), a primary CTA button, and at least one trust signal (logo bar, review stars, badge). If the primary CTA is below the fold on a 1366x768 laptop, that is Critical.
4. **Audit CTA clarity and friction.** The CTA label must say what happens next ("Start free trial", "Book a 20-minute demo"), not "Submit" or "Go". Each required form field before the conversion event adds roughly 5 to 10% drop-off — flag lead-gen forms with more than three fields and demo forms with more than five.
5. **Evaluate social proof.** Inventory testimonials, logos, review counts, case-study stats, media mentions, and security badges. Best placement is adjacent to or just below the primary CTA. Specificity wins: "We reduced onboarding time by 40% in the first month — Sarah, Head of Ops" beats "We love it!"; named testimonials beat bare logos.
6. **Check for friction elements.** Flag forced account creation before value, an undisclosed credit-card requirement on a "free" trial, fine-print terms that contradict the headline offer, mandatory phone fields for non-sales-led products, and CAPTCHA on the primary form.
7. **Assess page length versus offer complexity.** High-consideration offers (B2B SaaS, high price) justify longer pages; low-friction actions (free tool, email signup) want short pages. A one-field email capture should not sit behind eight sections of marketing copy.
8. **Verify CTA repetition.** On pages taller than two viewports, the primary CTA should repeat at least once in the body and once in a sticky header or footer — a visitor who scrolls past the hero should never scroll back up to convert.
9. **Review the post-conversion state.** What happens immediately after the CTA click? A blank page, a generic "Thank you", or a 404 is a leak. The state should confirm the action, set expectations ("Check your inbox"), and offer a next step.
10. **Flag technical conversion risks.** Page weight over 3MB (kills mobile conversion), missing Open Graph tags (breaks social sharing), missing canonical URL (SEO and attribution risk), and forms without clear inline validation.

## Concrete checks

Hero and offer:
- H1 plus subheadline pass the five-second test (product, audience, value clear).
- Primary CTA is visible above the fold at 1366x768.
- The CTA label states the outcome, not a generic verb.

Trust and friction:
- At least one trust signal sits above the fold.
- Testimonials carry name, title, company, and a specific outcome.
- No undisclosed credit-card or phone requirement on a "free" offer.
- No CAPTCHA on the primary conversion form.

Form and flow:
- Lead-gen forms have three or fewer required fields; demo forms five or fewer.
- The primary CTA repeats below the hero on pages taller than two viewports.
- The post-conversion state confirms the action and provides a next step.

Technical:
- Lighthouse load under about three seconds on throttled 4G.
- Open Graph and canonical metadata present.
- No horizontal scroll on mobile; no undismissable auto-playing media.
- Page weight under about 3MB; hero media is compressed and lazy where possible.
- Forms show inline validation with clear, specific error messages.

## Commands

```bash
# --- performance + metadata ---
# Lighthouse performance + SEO baseline on the live URL (mobile profile)
npx lighthouse <url> --only-categories=performance,seo --form-factor=mobile --quiet --chrome-flags="--headless"

# social-sharing + canonical metadata presence
rg -n 'og:title|og:image|og:description|rel="canonical"' src public index.html 2>/dev/null

# --- form friction ---
# count required form fields (friction signal)
rg -n '<input|<select|<textarea' src | rg -i 'required' | wc -l

# CAPTCHA on the conversion form
rg -n 'recaptcha|hcaptcha|turnstile' src

# --- CTA ---
# CTA inventory — how many primary buttons exist and what they say
rg -n '<button|role="button"|class="[^"]*(btn|cta)' src | head -40

# sticky CTA present for long pages?
rg -n 'sticky|fixed.*bottom|fixed.*top' src | head

# --- trust signals ---
# testimonials, logos, ratings, badges
rg -n 'testimonial|review|rating|badge|logo|as seen' src | head

# --- media ---
# auto-playing media (mobile conversion / annoyance risk)
rg -n '<video[^>]*autoplay|autoPlay' src

# --- hierarchy ---
# heading hierarchy in the hero
rg -on '<h[1-3]' src | sort | uniq -c

# --- friction: forced account / card ---
# credit-card or account requirement before value
rg -n 'card number|cardNumber|credit card|create account|sign up to' src | head

# --- post-conversion ---
# thank-you / success redirect handling
rg -n 'thank|success|/confirm|onSubmitSuccess|redirect' src | head

# --- page weight ---
# large bundled assets that can blow past the 3MB mobile budget
fd -e png -e jpg -e mp4 -e gif public src 2>/dev/null -x du -h {} | sort -rh | head

# --- form validation ---
# inline validation and error messaging on the conversion form
rg -n 'error|invalid|aria-invalid|helperText|FormMessage' src | head

# --- above-the-fold CTA ---
# fixed-height hero that may push the CTA below the fold
rg -n 'h-screen|min-h-screen|h-\[[0-9]{3,}px\]' src | head
```

## Common issues & anti-patterns

- **Feature-first hero:** the H1 lists capabilities ("AI-powered analytics") instead of one clear outcome ("Know which campaigns drive revenue, not just clicks").
- **CTA below the fold on launch:** a full-screen hero image pushes the button to the first scroll position.
- **Generic testimonials:** quotes from "Happy customer" with no company, outcome, or photo — indistinguishable from fabricated content.
- **Form overreach:** a lead-magnet form demanding name, email, phone, company, size, and role — most visitors abandon at field four.
- **Buried pricing disclaimer:** "Free for 14 days, then $99/month" shown only in 11px gray text below the fold.
- **Dead thank-you page:** after submit, a blank "Thank you!" with no follow-up and no confirmation email.
- **CTA label mismatch:** the button says "Get started free" but opens a pricing page instead of a signup form.
- **Trust signals at the bottom:** logos and testimonials placed only in the footer, far from the CTA where the decision is actually made.
- **Two competing CTAs in the hero:** a primary "Start free trial" and an equally weighted "Watch demo" side by side, splitting attention instead of driving one action.
- **Heavy hero video:** an autoplaying 6MB background video that delays the largest contentful paint and stalls the CTA on mobile connections.
- **CAPTCHA on a low-risk form:** a reCAPTCHA challenge on a simple newsletter signup, adding friction far out of proportion to the spam risk.

## Required output

Return a structured report with:
1. **Conversion readiness verdict:** Ready, Needs work, or Not ready, with a one-sentence rationale.
2. **Five-second test result:** the exact H1 and subheadline evaluated, pass or fail, and a rewrite if it failed.
3. **Critical findings** (up to three): above-the-fold gaps, form friction, or trust-signal absence.
4. **Major findings** (up to five): CTA repetition, social-proof quality, post-conversion state.
5. **A/B test ideas** (top three): hypothesis, predicted direction, and the metric to measure.
6. **Technical risks:** any load-speed, mobile, or metadata issues found.

## Safety

- Do not rewrite production copy without explicit instruction — provide suggested alternatives, not replacements.
- Separate opinion ("this testimonial reads as weak") from measurable fact ("the form has seven required fields").
- Do not claim specific conversion-rate improvements — conversion depends on traffic quality and many factors outside scope.
- Treat any analytics-dependent statement as a hypothesis when no data is provided.
- Redact any tracking IDs or keys surfaced while reading the page source.

## Completion criteria

Done means the conversion goal is named; the hero's five-second test is run with the exact copy quoted; above-the-fold completeness, form friction, social proof, CTA repetition, and the post-conversion state are each assessed; technical risks are checked with Lighthouse; and the report ends with three testable A/B ideas.

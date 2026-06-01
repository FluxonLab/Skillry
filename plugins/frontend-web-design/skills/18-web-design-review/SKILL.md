---
name: web-design-review
description: Use when you need to review web design quality, hierarchy, layout, copy density, and product fit.
---

# Web Design Review

## Purpose

Evaluate the visual design quality of a web page or web app: typographic hierarchy, whitespace and rhythm, layout structure, copy density, CTA clarity, and the product-market fit of the visual language. The output is a prioritized, evidence-based critique — every finding cites a measurable observation (a font size, a padding value, a line length) and pairs it with one concrete fix, not a subjective aesthetic opinion. The review reads from a real artifact (URL, screenshot, or source with CSS) and never invents findings the artifact does not support.

## When to use

- A page or component has been built and needs design critique before shipping.
- The team suspects conversion or engagement is hurt by layout or hierarchy issues.
- A designer or developer asks "does this look right or professional?" and provides a URL, screenshot, or source files.
- You are preparing a pre-launch design QA pass and want a structured second opinion.
- A redesign is in progress and you need a baseline read of the current state before comparing.

## When not to use

- The request is exclusively about accessibility — use `accessibility-audit` for WCAG, contrast, and screen readers.
- The request is exclusively about responsiveness across breakpoints — use `responsive-layout-review`.
- The request is about token architecture and component reuse — use `design-system-review`.
- The request is about conversion mechanics on a landing page — use `landing-page-conversion-review`.
- The request is about brand identity, logo design, or marketing strategy — outside scope.
- No visual artifact (URL, screenshot, or source with CSS) has been provided.

## Procedure

1. **Gather the artifact.** Ask for a live URL, screenshot, or relevant HTML/CSS if not provided. If a URL is given, read the page source and note the CSS framework (Tailwind, Bootstrap, custom). Capture the rendered page at desktop (1280px) and mobile (375px) so every judgement is anchored to real output.
2. **Map the visual hierarchy.** Identify the single most prominent element. Confirm it matches the intended primary action or message. Check that H1, H2, body, and label text form a legible size and weight scale (for example 32px/700 then 24px/600 then 16px/400 is reasonable; 18px/400 everywhere is not).
3. **Audit whitespace and rhythm.** Flag sections that feel cramped (padding under 16px on mobile, under 24px on desktop) or floating (inconsistent gaps between related elements). Spacing between a label and its field, or a heading and its paragraph, must be tighter than spacing between separate sections — proximity should encode grouping.
4. **Check CTA clarity.** Count primary CTAs per viewport section. More than one primary CTA competing at the same visual weight is a red flag. Verify the label is action-specific ("Start free trial" beats "Submit") and that button contrast and size make it the obvious next step.
5. **Evaluate copy density.** Flag paragraphs longer than four or five lines with no visual break (no bullet, sub-heading, or callout). Flag jargon-heavy hero copy that fails the five-second test: can a cold visitor state what the product does after five seconds?
6. **Assess product-market visual fit.** Compare the visual tone (playful, minimal, enterprise) against the stated audience. A B2B compliance tool with neon gradients and a rounded display font signals misalignment.
7. **Check measurable readability.** Verify body line length sits at 45 to 75 characters (about 600 to 700px at 16px), line-height is roughly 1.5 for body and 1.2 for headings, and no information is conveyed by color alone.
8. **Prioritize findings.** Classify each issue Critical (breaks comprehension or conversion), Major (degrades trust or readability), or Minor (polish). Cap the report at three Critical and five Major; group minor issues.
9. **Check desktop-to-mobile parity.** Compare the two captures. Confirm the hierarchy survives the narrower viewport: the dominant element is still dominant, headings do not collapse to body weight, and CTAs remain prominent rather than buried below a tall stacked layout.
10. **Write fix recommendations.** Each finding needs one concrete fix, not a vague direction: "Hero H1 is 18px/400 — increase to 36px/700 and reduce the subheading to 20px/400 to create a clear typographic jump."

## Concrete checks

Hierarchy and type:
- At least three distinct size/weight steps between heading, subheading, and body.
- The single most dominant element matches the intended primary action.
- Body line-height around 1.5; heading line-height around 1.2.
- Line length 45 to 75 characters; flag full-width text on wide screens with no `max-width`.

Layout and rhythm:
- Vertical section padding >=48px desktop and >=32px mobile.
- Related elements grouped tighter than unrelated sections.
- Consistent gutter widths in multi-column layouts.
- No orphaned whitespace gaps between unrelated blocks while related ones touch.

CTA and copy:
- Exactly one primary CTA per viewport section; labels are verb-forward and specific.
- Hero passes the five-second test for product, audience, and value.
- No body paragraph runs longer than about five lines without a visual break.

Tone and imagery:
- Palette, font personality, and imagery match the declared audience.
- No decorative or stock image consuming more than about 30% of the viewport without conveying information.
- Long body text is left-aligned, not centered, so the eye has a stable left edge to scan from.
- No information is conveyed by color alone; statuses carry an icon or label too.

## Commands

```bash
# --- framework and fonts ---
# detect the CSS framework / font stack in use
rg -n 'tailwind|bootstrap|font-family|--font' src public index.html 2>/dev/null | head

# --- hierarchy ---
# heading levels present (hierarchy sanity check)
rg -on '<h[1-6]' src | sort | uniq -c

# distinct font sizes (collapse signal if there is only one)
rg -oN 'text-(xs|sm|base|lg|xl|2xl|3xl|4xl|5xl)|font-size:\s*[0-9.]+(px|rem)' src | sort -u

# distinct font weights (hierarchy needs contrast in weight, not just size)
rg -oN 'font-(light|normal|medium|semibold|bold)|font-weight:\s*[0-9]+' src | sort | uniq -c

# --- CTA density ---
# CTA inventory — count primary buttons and read their labels
rg -n '<button|role="button"|class="[^"]*(btn|cta)' src | head -40

# --- readability ---
# paragraphs that may lack a max-width constraint
rg -n '<p[^>]*>' src | head

# very wide text containers (line length risk)
rg -n 'max-w-(none|full|screen)|max-width:\s*1[0-9]{3}px' src

# --- spacing rhythm ---
# section padding values in use (look for cramped < 32/48px)
rg -oN 'p[ytb]?-[0-9]+|padding:\s*[0-9]+px' src | sort | uniq -c | head -20

# --- imagery weight ---
# large hero/background images and fixed heights that dominate the viewport
rg -n 'h-screen|min-h-screen|h-\[[0-9]{3,}px\]|background-image' src

# --- rendered baseline ---
# Lighthouse accessibility + best-practices baseline on a live URL
npx lighthouse <url> --only-categories=accessibility,best-practices --quiet --chrome-flags="--headless"

# capture desktop and mobile renders for side-by-side review
npx playwright screenshot --viewport-size=1280,800 <url> desktop.png
npx playwright screenshot --viewport-size=375,812 <url> mobile.png
```

## Common issues & anti-patterns

- **Hierarchy collapse:** every text element is 16px/400 — nothing reads as a heading, nothing commands attention.
- **CTA inflation:** "Get started", "Try now", and "Contact us" buttons compete at identical visual weight in one section.
- **Orphaned whitespace:** a huge gap between two unrelated sections while a label and its input are touching — proximity encodes the wrong grouping.
- **Wall-of-text hero:** a 90-word paragraph above the fold instead of a punchy eight-word value proposition plus one sentence of sub-copy.
- **Mismatched visual tone:** a legal-tech product styled with pastel illustrations and a rounded font that reads as a children's app.
- **Decorative images without purpose:** stock photos that add no information yet eat a third of the viewport height.
- **Full-bleed body text:** paragraphs stretched to 1400px wide (120+ characters per line), exhausting the reader on every return sweep.
- **Color-only signaling:** required fields or statuses indicated only by color, with no icon, label, or text fallback.
- **Centered everything:** every block center-aligned including long body paragraphs, which destroys the left edge the eye needs to scan running text.
- **Inconsistent section rhythm:** one section at 96px vertical padding, the next at 32px, with no content reason, so the page feels like stitched-together templates.
- **Tiny low-contrast captions:** 11px gray helper text under inputs that is technically present but practically unreadable, undermining an otherwise clean form.
- **Weight-only hierarchy at one size:** headings differ from body only by being bold at the same size, so the structure is hard to scan at a glance.
- **Gradient-on-gradient:** a hero where the headline sits on a busy gradient with no solid backing, dropping text contrast below readable levels.
- **Inconsistent button shapes:** primary CTAs are pill-shaped in one section and sharp-cornered in another, reading as two different products.

## Required output

Return a structured report with:
1. **Summary** (two or three sentences): the overall design-quality verdict.
2. **Critical findings** (up to three): each with evidence (for example "H1 font-size: 16px in hero") and the exact fix.
3. **Major findings** (up to five): same evidence-plus-fix format.
4. **Minor findings** (grouped, up to five bullets).
5. **Desktop-vs-mobile parity note:** whether the hierarchy and CTA prominence survive the narrow viewport.
6. **Positive observations** (one to three): what is working well, to keep the report balanced.

Each finding row should read `severity | location | measurable observation | concrete fix` so it can be triaged and assigned directly.

## Safety

- Do not alter production CSS or HTML without explicit instruction to do so.
- Do not invent findings unsupported by the provided artifact; if a claim depends on data you lack (analytics, user testing), mark it a hypothesis.
- If working from a screenshot only, note uncertainty about interactive states (hover, focus, error) you cannot observe.
- Keep recommendations specific and measurable so the developer can implement without a second clarification pass.
- Separate measurable observation from subjective preference in the wording of every finding.

## Completion criteria

Done means hierarchy, whitespace and rhythm, layout, CTA clarity, copy density, and visual-tone fit were each evaluated against measurable criteria; every finding carries evidence plus one concrete fix; findings are severity-ranked and capped at three Critical and five Major; at least one positive observation is recorded; and any analytics-dependent claim is labeled a hypothesis.

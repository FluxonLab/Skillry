---
name: web-design-review
description: Use when you need to review web design quality, hierarchy, layout, copy density, and product fit.
---

# Web Design Review

## Purpose
Evaluate the visual design quality of a web page or web app: typographic hierarchy, whitespace use, layout structure, copy density, CTA clarity, and overall product-market fit of the visual language. Produces a prioritized, evidence-based critique with concrete fix recommendations — not subjective aesthetic opinions.

## When to use
- A page or component has been built and needs design critique before shipping.
- The team suspects conversion or engagement is hurt by layout or hierarchy issues.
- A designer or developer asks "does this look right / professional?" and provides a URL, screenshot, or source files.
- You are preparing a pre-launch design QA pass.

## When not to use
- The request is exclusively about accessibility (use `accessibility-audit` instead).
- The request is exclusively about responsiveness (use `responsive-layout-review`).
- The request is about brand identity, logo design, or marketing strategy — outside scope.
- No visual artifact (URL, screenshot, or source code with CSS) has been provided.

## Procedure

1. **Gather the artifact.** Ask for a live URL, screenshot, or relevant HTML/CSS source if not provided. If a URL is given, read the page source and note which CSS framework (Tailwind, Bootstrap, custom) is in use.

2. **Map the visual hierarchy.** Identify the single most prominent element on the page. Confirm it matches the intended primary action or message. Check whether H1, H2, body, and label text form a legible size and weight scale (e.g., 32px/700 → 24px/600 → 16px/400 is reasonable; 18px/400 everywhere is not).

3. **Audit whitespace and rhythm.** Look for sections where content feels cramped (padding < 16px on mobile, < 24px on desktop) or floating (inconsistent gaps between related elements). Check that spacing between a label and its field, or a heading and its paragraph, is tighter than spacing between separate sections.

4. **Check CTA clarity.** Count primary CTAs on the page. More than one primary CTA per viewport section is a red flag. Verify the CTA label is action-specific ("Start free trial" is better than "Submit"). Check CTA button contrast and size.

5. **Evaluate copy density.** Flag paragraphs longer than 4 lines that contain no visual break (no bullet, no sub-heading, no callout). Flag jargon-heavy hero copy that fails the "5-second test" (can a new visitor state what the product does after 5 seconds?).

6. **Assess product-market visual fit.** Compare the visual tone (e.g., playful, minimal, enterprise) against the stated audience. A B2B SaaS tool with Comic Sans or neon gradients signals misalignment.

7. **Prioritize findings.** Classify each issue as Critical (breaks comprehension or conversion), Major (degrades trust or readability), or Minor (polish). List no more than 3 Critical and 5 Major findings; minor issues can be grouped.

8. **Write fix recommendations.** Each finding needs one concrete fix, not a vague direction. Example: "Hero H1 is 18px/400 — increase to 36px/700 and reduce subheading to 20px/400 to create a clear typographic jump."

## Checklist
- [ ] Single dominant visual element per viewport section aligns with intended user action
- [ ] Typographic scale has at least 3 distinct size/weight steps (heading, subheading, body)
- [ ] Line length for body text is 45–75 characters (about 600–700px at 16px)
- [ ] Section padding is >= 48px vertical on desktop, >= 32px on mobile
- [ ] Related elements (label+field, icon+caption) have tighter spacing than unrelated sections
- [ ] Only one primary CTA button per viewport-height section
- [ ] CTA labels are verb-forward and specific (not "Learn more" or "Click here")
- [ ] Hero copy passes 5-second test: product category and primary benefit are immediately clear
- [ ] No body paragraph runs longer than 5 lines without a visual break
- [ ] Visual tone (color palette, font personality, illustration style) matches target audience

## Common issues & anti-patterns
- **Hierarchy collapse:** every text element is 16px/400 — nothing reads as a heading, nothing commands attention.
- **CTA inflation:** three "Get started", "Try now", and "Contact us" buttons compete at the same visual weight in the same section.
- **Orphaned whitespace:** a huge gap appears between two unrelated sections while a label and its input are touching.
- **Wall-of-text hero:** a 90-word paragraph above the fold instead of a punchy 8-word value proposition + 1-sentence sub-copy.
- **Mismatched visual tone:** a legal-tech product uses pastel illustrations and a rounded font that reads as a children's app.
- **Decorative images without purpose:** stock photos that add no information and consume 30% of viewport height.

## Required output
Return a structured report with:
1. **Summary** (2-3 sentences): overall design quality verdict.
2. **Critical findings** (up to 3): each with evidence (e.g., "H1 font-size: 16px in hero") and exact fix.
3. **Major findings** (up to 5): same format.
4. **Minor findings** (grouped, up to 5 bullets).
5. **Positive observations** (1-3): what is working well — keeps the report balanced.

## Safety
- Do not alter production CSS or HTML without explicit instruction to do so.
- Do not invent findings not supported by the provided artifact.
- If working from a screenshot only, note uncertainty about interactive states.

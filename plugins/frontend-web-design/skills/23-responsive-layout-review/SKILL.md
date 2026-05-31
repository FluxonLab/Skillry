---
name: responsive-layout-review
description: Use when you need to audit mobile, tablet, desktop, overflow, container sizing, and text fit.
---

# Responsive Layout Review

## Purpose
Audit a page or component for responsive layout correctness across mobile (360–480px), tablet (768–1024px), and desktop (1280px+) breakpoints. Covers horizontal overflow, container sizing, touch target sizes, text truncation, image scaling, breakpoint logic, and viewport meta configuration. Produces specific breakpoint-by-breakpoint findings with CSS-level fix guidance.

## When to use
- A page or component has been built for desktop and needs a mobile/responsive audit.
- A bug report says "it looks broken on mobile" and the specific cause needs to be diagnosed.
- A Tailwind or CSS file has grown with many responsive prefixes and needs a consistency review.
- A new layout is being built with CSS Grid or Flexbox and breakpoint logic needs validation.
- A client has reported horizontal scrollbars on mobile.

## When not to use
- The request is about design quality on a single viewport — no responsive concerns (use `web-design-review`).
- The request is about accessibility only (use `accessibility-audit`), though responsive and accessible are often co-reviewed.
- The project is a native mobile app — this skill covers web/browser layout only.

## Procedure

1. **Verify the viewport meta tag.** Confirm `<meta name="viewport" content="width=device-width, initial-scale=1">` is present in `<head>`. Without it, mobile browsers render at desktop width and then scale down — all responsive CSS is bypassed. Absence is an immediate Critical finding.

2. **Check for horizontal overflow.** Use `overflow-x: auto` on `body` or `html` as a diagnostic — if a horizontal scrollbar appears at any viewport width, there is a layout overflow. Common causes: fixed-width elements (`width: 600px` on a 360px screen), `min-width` without a responsive counterpart, or `white-space: nowrap` on a text block wider than the viewport.

3. **Audit breakpoint definitions.** List all breakpoints in the CSS or Tailwind config. Confirm breakpoints are mobile-first (min-width) not desktop-first (max-width) if the project uses a mobile-first CSS framework like Tailwind. Mixing mobile-first and desktop-first breakpoints in the same file creates specificity conflicts.

4. **Review the mobile layout (360px).** At the smallest common viewport width: confirm no element overflows horizontally, all text is readable at base font-size (>= 14px), all images are `max-width: 100%` or `w-full`, navigation collapses to a hamburger or bottom bar, and multi-column layouts collapse to a single column.

5. **Check touch targets.** All interactive elements (buttons, links, form inputs, checkboxes) must be at least 44x44px on touch screens (Apple HIG) or 48x48dp (Android Material). A link inside a line of running text where the clickable area is just the text height (~20px) fails this criterion. Check `padding` on interactive elements at mobile breakpoints.

6. **Review the tablet layout (768px).** Confirm the layout is neither fully mobile (wasted whitespace) nor fully desktop (cramped in a narrower viewport). Specifically: 2-column card grids are usually appropriate at tablet; navigation should be visible but may differ from desktop; data tables may need horizontal scroll within a container (`overflow-x: auto` on the table wrapper, not the page).

7. **Audit typography at each breakpoint.** H1 font-size that reads well at 1280px (`clamp` or `text-5xl`) may be too large at 360px and consume 3 lines. Check that font sizes either use `clamp()` for fluid scaling or have explicit responsive overrides (`text-3xl md:text-5xl`). Body text must remain >= 16px (mobile browsers auto-zoom inputs below 16px).

8. **Check image and media scaling.** All `<img>` elements should have `max-width: 100%` (or Tailwind `max-w-full`). Background images should use `background-size: cover` or `contain` as appropriate. Videos should be in a responsive wrapper (`aspect-ratio: 16/9` with `width: 100%`). Check for `<img>` elements with hardcoded `width` and `height` attributes without CSS overrides.

9. **Evaluate container queries (if applicable).** If the project uses container queries (`@container`), verify the container element has a defined `container-type` and the child breakpoints reference the container, not the viewport. Container queries should not reference `vw` units — that defeats their purpose.

10. **Test landscape mobile (667px width).** Many layouts break in landscape mobile orientation: fixed-height hero sections using `100vh` become unusable when the viewport height is 375px in landscape. Confirm `100vh` usage or replace with `100dvh` for dynamic viewport height on mobile browsers.

## Checklist
- [ ] `<meta name="viewport" content="width=device-width, initial-scale=1">` present in `<head>`
- [ ] No horizontal overflow at 360px, 768px, or 1280px viewport widths
- [ ] All breakpoints are mobile-first (`min-width`) — no mixed mobile/desktop-first logic in the same file
- [ ] Multi-column grids collapse to 1 column at <= 480px
- [ ] All interactive elements >= 44x44px touch target at mobile breakpoints
- [ ] No fixed-width elements (`width: Npx`) without a responsive override below that width
- [ ] All `<img>` elements have `max-width: 100%` or equivalent responsive sizing
- [ ] Body text font-size >= 16px at all breakpoints (prevents mobile browser auto-zoom on inputs)
- [ ] H1 and display headings have fluid sizing or explicit mobile overrides to avoid 3+ line breaks at 360px
- [ ] Tables at mobile are wrapped in `overflow-x: auto` container, not forcing page-level scroll
- [ ] Navigation collapses to a mobile-appropriate pattern below 768px
- [ ] `100vh` usage replaced with `100dvh` or `min-h-screen` where dynamic viewport height matters
- [ ] Landscape mobile (667px wide, 375px tall) does not break fixed-height hero sections

## Common issues & anti-patterns
- **Missing viewport meta:** the page renders at 980px on mobile and scales to fit — all responsive classes are irrelevant.
- **Fixed-width card:** `width: 400px` on a card component that is fine at 1440px but overflows at 375px because no `max-width: 100%` was added.
- **`overflow-x: hidden` on body as a band-aid:** hides the overflow scrollbar but does not fix the overflowing element — interactive elements cut off at the right edge become unreachable on touch.
- **Tiny tap targets:** `<a>` inside a `<li>` with no padding — tap target is 16px tall, 3x below the recommended 44px minimum.
- **Desktop-only data table:** a 10-column table with no horizontal scroll wrapper and no mobile-specific column hiding — completely unusable on mobile.
- **`100vh` hero on iOS Safari:** iOS Safari's browser chrome changes height dynamically, causing `100vh` to overflow and show a scrollbar on initial load.
- **Hardcoded breakpoints in JavaScript:** `if (window.innerWidth < 768)` in component logic that does not account for resize events — layout and behavior desync after orientation change.

## Required output
Return a structured report with:
1. **Breakpoint summary table**: Mobile (360px) / Tablet (768px) / Desktop (1280px) — Pass / Issues / Fail for each.
2. **Critical findings** (causes overflow or makes content unreachable): exact element, CSS property, and fix.
3. **Major findings** (degraded experience but content accessible): same format.
4. **Touch target violations**: list of elements with estimated tap area and required fix.
5. **Typography scale audit**: heading sizes at each breakpoint and recommendations.
6. **Recommended test procedure**: which browser/device emulator combinations to use for verification.

## Safety
- Do not modify CSS breakpoints without first confirming the current design tokens and Tailwind config.
- Do not add `overflow: hidden` as a fix — diagnose and fix the overflowing element instead.
- Run all breakpoint checks non-destructively (browser DevTools resize) before suggesting code changes.

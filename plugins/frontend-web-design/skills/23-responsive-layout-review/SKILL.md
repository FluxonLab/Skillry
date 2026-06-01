---
name: responsive-layout-review
description: Use when you need to audit mobile, tablet, desktop, overflow, container sizing, and text fit.
---

# Responsive Layout Review

## Purpose

Audit a page or component for responsive correctness across mobile (360 to 480px), tablet (768 to 1024px), and desktop (1280px and up) breakpoints. The review covers horizontal overflow, container sizing, touch-target sizes, text truncation, image scaling, breakpoint logic, and viewport-meta configuration. The output is a breakpoint-by-breakpoint verdict with CSS-level fix guidance — naming the exact element, property, and replacement value rather than a vague "looks broken on mobile".

## When to use

- A page built for desktop needs a mobile and responsive audit.
- A bug report says "it looks broken on mobile" and the specific cause must be diagnosed.
- A Tailwind or CSS file has accumulated many responsive prefixes and needs a consistency review.
- A new layout uses CSS Grid or Flexbox and the breakpoint logic needs validation.
- A client reports horizontal scrollbars on mobile.

## When not to use

- The request is about design quality on a single viewport with no responsive concern — use `web-design-review`.
- The request is about accessibility only — use `accessibility-audit` (though responsive and accessible are often co-reviewed).
- The project is a native mobile app — this skill covers web and browser layout only; use `mobile-app-review`.
- The request is about final pixel polish rather than layout correctness — use `visual-polish-pass`.

## Procedure

1. **Verify the viewport meta tag.** Confirm `<meta name="viewport" content="width=device-width, initial-scale=1">` is in `<head>`. Without it, mobile browsers render at about 980px and scale down, bypassing all responsive CSS. Absence is an immediate Critical finding.
2. **Check for horizontal overflow.** Temporarily set `overflow-x: auto` on `html`/`body` as a diagnostic — any horizontal scrollbar at a given width indicates an overflowing element. Common causes: fixed-width elements (`width: 600px` on a 360px screen), `min-width` with no responsive counterpart, or `white-space: nowrap` on a block wider than the viewport.
3. **Audit breakpoint definitions.** List all breakpoints in the CSS or Tailwind config. In a mobile-first framework such as Tailwind, breakpoints should be `min-width` based; mixing `min-width` and `max-width` logic in the same file creates specificity conflicts.
4. **Review the mobile layout at 360px.** Confirm no horizontal overflow, base font-size readable (>=14px, body >=16px), all images `max-width: 100%` or `w-full`, navigation collapsed to a hamburger or bottom bar, and multi-column layouts collapsed to a single column.
5. **Check touch targets.** Interactive elements must be >=44x44px (Apple HIG) or >=48x48dp (Android Material). A link inside running text whose clickable area is only the roughly 20px text height fails — check `padding` on interactive elements at mobile breakpoints.
6. **Review the tablet layout at 768px.** Confirm it is neither fully mobile (wasted whitespace) nor cramped desktop. Two-column card grids usually fit; navigation may be visible but differ from desktop; wide tables need `overflow-x: auto` on the table wrapper, not the page.
7. **Audit typography at each breakpoint.** An H1 that reads well at 1280px may consume three lines at 360px. Use `clamp()` for fluid scaling or explicit responsive overrides (`text-3xl md:text-5xl`). Body text must stay >=16px — mobile browsers auto-zoom inputs with smaller text.
8. **Check image and media scaling.** All `<img>` should have `max-width: 100%`; background images use `cover` or `contain` as appropriate; videos sit in a responsive wrapper (`aspect-ratio: 16/9; width: 100%`). Flag `<img>` with hardcoded `width`/`height` and no CSS override.
9. **Evaluate container queries if used.** Confirm the container element defines `container-type` and children reference the container, not the viewport — and do not mix in `vw` units, which defeats the purpose.
10. **Test landscape mobile at 667x375.** Fixed-height hero sections using `100vh` become unusable when the viewport is only 375px tall. Confirm `100vh` is replaced with `100dvh` or `min-h-screen` where dynamic viewport height matters.

## Concrete checks

Viewport and overflow:
- `<meta name="viewport" content="width=device-width, initial-scale=1">` present in `<head>`.
- No horizontal overflow at 360px, 768px, or 1280px.
- No fixed-width element without a responsive override below that width.

Breakpoints and grids:
- All breakpoints are mobile-first (`min-width`) with no mixed logic in one file.
- Multi-column grids collapse to one column at or below 480px.
- Wide tables are wrapped in `overflow-x: auto`, not forcing page-level scroll.

Typography and media:
- Body text stays >=16px at every breakpoint.
- Headings use fluid (`clamp`) or explicit responsive sizing to avoid three-line wraps at 360px.
- All `<img>` have `max-width: 100%` or equivalent.

Touch and viewport-height:
- Interactive elements are >=44x44px / 48x48dp at mobile breakpoints.
- Adjacent tap targets have enough spacing to avoid mis-taps.
- `100vh` is replaced with `100dvh` or `min-h-screen` where it matters.
- Landscape mobile (667x375) does not break fixed-height heroes.
- Sticky headers and bottom bars do not cover content or overlap the keyboard on mobile.

## Commands

```bash
# --- viewport meta ---
# viewport meta present?
rg -n 'name="viewport"' src public index.html app 2>/dev/null

# --- overflow sources ---
# fixed pixel widths that may overflow on small screens
rg -n 'width:\s*[0-9]{3,}px|w-\[[0-9]{3,}px\]|min-width:\s*[0-9]{3,}px' src

# white-space:nowrap on potentially long text blocks
rg -n 'white-space:\s*nowrap|whitespace-nowrap' src

# overflow:hidden band-aids on body/html (masks the real overflow)
rg -n '(html|body)[^{]*\{[^}]*overflow[^}]*hidden' src

# --- images / media ---
# images without responsive max-width / w-full
rg -n '<img(?![^>]*(max-w-full|w-full|max-width))' src

# 100vh usage that should be 100dvh on mobile
rg -n '100vh|h-screen' src

# --- breakpoints ---
# breakpoint prefixes in use (Tailwind) — confirm mobile-first consistency
rg -on '\b(sm|md|lg|xl|2xl):' src | sort | uniq -c

# desktop-first max-width media queries mixed in
rg -n 'max-width:\s*[0-9]+px' src | head

# --- container queries ---
# container queries declared with a container-type?
rg -n '@container|container-type|container-name' src

# --- touch targets ---
# small interactive elements that may fail the 44px minimum
rg -n '<a [^>]*class="[^"]*(text-xs|p-0|py-0)' src | head

# --- JS breakpoints ---
# hardcoded width checks in JS (desync risk without a resize listener)
rg -n 'innerWidth|matchMedia|window\.resize' src | head

# --- table overflow wrappers ---
# wide tables wrapped for horizontal scroll (or not)
rg -n 'overflow-x-auto|overflow-x:\s*auto' src | head

# --- fluid typography ---
# headings using clamp() or responsive size overrides
rg -n 'clamp\(|text-[0-9a-z]+ (sm|md|lg):text-' src | head

# --- sticky elements ---
# sticky/fixed bars that can cover content on short viewports
rg -n 'sticky|fixed' src | rg -i 'top|bottom|header|footer' | head
```

## Common issues & anti-patterns

- **Missing viewport meta:** the page renders at 980px on mobile and scales to fit — every responsive class is irrelevant.
- **Fixed-width card:** `width: 400px` is fine at 1440px but overflows at 375px because no `max-width: 100%` was added.
- **`overflow-x: hidden` band-aid:** hides the scrollbar without fixing the overflowing element — content cut off at the right edge becomes unreachable on touch.
- **Tiny tap targets:** an `<a>` in an `<li>` with no padding — a 16px tap target, far below the 44px minimum.
- **Desktop-only table:** a ten-column table with no horizontal-scroll wrapper and no mobile column hiding — unusable on phones.
- **`100vh` hero on iOS Safari:** Safari's dynamic browser chrome makes `100vh` overflow on load and show a scrollbar; `100dvh` fixes it.
- **Hardcoded breakpoint in JS:** `if (window.innerWidth < 768)` with no resize listener — layout and behavior desync after an orientation change.
- **Mixed breakpoint direction:** some rules use `min-width` and others `max-width` in the same file, producing specificity conflicts that are painful to debug.
- **Sub-16px inputs:** form inputs at 14px font, which makes iOS Safari zoom in on focus and then leave the layout shifted.
- **Absolute-positioned overlay off-screen:** a modal or toast positioned with a fixed pixel offset that lands off-screen on a 360px viewport.
- **Image with intrinsic width:** an `<img width="800">` with no CSS `max-width`, which forces a horizontal scrollbar on any screen narrower than 800px.

## Required output

Return a structured report with:
1. **Breakpoint summary table:** Mobile (360px), Tablet (768px), Desktop (1280px) — Pass, Issues, or Fail for each.
2. **Critical findings** (cause overflow or make content unreachable): the exact element, the CSS property, and the fix.
3. **Major findings** (degraded but accessible): same format.
4. **Touch-target violations:** elements with the estimated tap area and the required fix.
5. **Typography scale audit:** heading sizes at each breakpoint and recommendations.
6. **Recommended test procedure:** which browser and device-emulator combinations to verify with.

## Safety

- Do not modify CSS breakpoints without first confirming the current design tokens and Tailwind config.
- Do not add `overflow: hidden` as a fix — diagnose and correct the overflowing element instead.
- Run all breakpoint checks non-destructively (DevTools resize or emulation) before suggesting code changes.
- Verify fixes at one breakpoint at a time, since responsive CSS changes cascade across the others.
- Redact any secret-like values surfaced while reading config.

## Completion criteria

Done means the viewport meta is confirmed; overflow, touch targets, typography, and media scaling were checked at 360px, 768px, and 1280px plus landscape mobile; each finding names the element, property, and fix; and the report includes a per-breakpoint pass/fail table and a verification procedure.

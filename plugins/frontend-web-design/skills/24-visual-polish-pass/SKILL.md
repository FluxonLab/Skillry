---
name: visual-polish-pass
description: Use when you need to perform final visual polish checks for alignment, rhythm, affordances, and professional finish.
---

# Visual Polish Pass

## Purpose

Perform a pre-ship visual polish audit: pixel-level alignment, consistent spacing rhythm, interactive-state completeness (hover, active, focus, disabled, loading), icon sizing and optical alignment, border-radius consistency, shadow hierarchy, motion timing, and the overall sense of craft. The output is a concrete punch list of small, high-ROI fixes, each naming the component, the exact discrepancy, and the corrected value, grouped by fix effort so a team can clear them quickly before a demo or release.

## When to use

- A feature is functionally complete and ready for final visual QA before shipping.
- The UI looks "almost right" but the specific issues have not been named.
- A designer handed off specs and you need to verify the implementation matches intent.
- A design review surfaced inconsistencies but did not fully enumerate them.
- You are preparing a demo or client presentation and want to maximize visual credibility.

## When not to use

- The layout has structural problems (wrong hierarchy, broken mobile) — fix structure with `web-design-review` or `responsive-layout-review` first, then polish.
- The request is about full accessibility compliance — focus and outline overlap but the broader audit is `accessibility-audit`.
- Token architecture or duplicate primitives are the concern — use `design-system-review`.
- The feature is not visually implemented yet — polish applies to built UI, not wireframes.

## Procedure

1. **Grid and alignment audit.** Identify the layout grid (8px, 4px, or 12-column). Card padding should be a grid multiple (16 or 24px, not 15 or 22px); inline elements (icon plus label) should be vertically centered with `align-items: center`, not nudged with `margin-top: 2px`; grid gutters should be uniform.
2. **Spacing rhythm check.** Scan for inconsistent gap values at the same semantic level — card padding 24px in one place and 20px in another with no rationale is a violation. Pick one section-padding value (for example 64px vertical) and apply it consistently; flag any value off the 4/8px scale.
3. **Interactive-state completeness.** For every interactive element (buttons, links, inputs, checkboxes, toggles, tabs, dropdowns), verify visually distinct `default`, `hover`, `active`, `focus-visible`, `disabled`, and `loading` where applicable. A button with hover but no active or disabled state is incomplete; a link with no hover feels static.
4. **Icon audit.** Icons should be optically sized consistently — if the set is 20px, all are 20px, not a mix of 16, 18, 20, and 24. Verify optical centering (adjust the SVG viewBox for top-heavy glyphs) and consistent stroke width across a line-icon set.
5. **Typography consistency pass.** Scan for mismatched `font-weight` at the same hierarchy level (some `<h3>` at 600, others at 500), inconsistent `line-height` between similar blocks, `letter-spacing` applied to only some headings, and sizes off the type scale.
6. **Border-radius consistency.** Reduce radius values to two or three semantic levels — small (inputs and badges), medium (cards), large (modals and sheets). A product mixing `rounded-sm` inputs, `rounded-md` cards, `rounded-xl` modals, and `rounded-full` pills with no logic reads as incoherent.
7. **Shadow hierarchy.** Shadows must encode elevation: tooltip over modal over card over flat element. No two elements at different z-index levels share a shadow; no overlapping element has `box-shadow: none`, which creates depth ambiguity.
8. **Color consistency micro-audit.** Muted text always uses one token; dividers always use one border-color token; badges follow the semantic palette. Flag near-duplicate hardcoded colors (`#6b7280` versus `#64748b`) that look similar but are inconsistent.
9. **Motion and transition polish.** Use consistent timing: `transition-colors duration-150` for color, `transition-transform duration-200` for movement and scale, about 300ms for complex entrances. Flag abrupt state changes (no transition), overly long transitions (over 300ms for a simple hover), and mismatched easing. Respect `prefers-reduced-motion`.
10. **Final scan test.** Zoom out to about 50% and scan the page as a whole: note any element that draws the eye unexpectedly (misaligned, wrong size or color), any section visually heavier or lighter than its neighbors, and any text that appears to float from insufficient line-height.

## Concrete checks

Alignment and spacing:
- Card and section padding are exact 4/8px multiples — no rounding to off-scale values.
- Inline icon-and-text combinations are vertically centered, not optically misaligned.
- Grid gutters are uniform within a layout.

Icons and typography:
- Icon sizes are consistent within each context; icons are optically (not just mathematically) centered.
- No mismatched `font-weight` at the same hierarchy level without a documented reason.
- `line-height` is consistent within body and within headings.

States:
- Every button has distinct default, hover, active, focus-visible, and disabled states.
- Every input has distinct default, focused, filled, error, and disabled states.
- Loading states exist where an action triggers async work.

Radius, shadow, motion:
- Border radius is reduced to three or fewer semantic levels.
- Shadow values encode elevation (tooltip over modal over card over flat).
- No overlapping element has `box-shadow: none` where depth is expected.
- Transition timing is consistent (~150ms color, ~200ms movement, ~300ms entrance).
- `prefers-reduced-motion` disables or reduces non-essential animation.

## Commands

```bash
# --- spacing ---
# off-scale padding/margin values (the 2px rounding error)
rg -n 'padding:\s*\d*[13579]px|margin:\s*\d*[13579]px|[pm]-\[[0-9]+px\]' src

# distinct section padding values (rhythm should be a small set)
rg -oN 'p[ytb]?-[0-9]+|padding:\s*[0-9]+px' src | sort | uniq -c | head -20

# --- radius / shadow ---
# distinct border-radius values (expect <= 3)
rg -oN 'rounded-(sm|md|lg|xl|2xl|full|none)|border-radius:\s*[0-9.]+(px|rem)' src | sort | uniq -c

# distinct shadow utilities (elevation should be an ordered set)
rg -oN 'shadow-(sm|md|lg|xl|2xl|none|inner)' src | sort | uniq -c

# --- interactive states ---
# interactive elements vs declared hover/focus-visible
rg -n '<button|<a |role="button"' src | wc -l
rg -c 'hover:|focus-visible:' src

# disabled handling and not-allowed cursor
rg -n 'disabled|cursor-not-allowed' src | head

# --- color drift ---
# near-duplicate literal colors hardcoded in components
rg -oN '#[0-9a-fA-F]{6}' src | sort | uniq -c | sort -rn | head -20

# --- motion ---
# transitions present vs abrupt state changes
rg -oN 'transition[^;"\s]*|duration-[0-9]+' src | sort | uniq -c

# reduced-motion respected anywhere?
rg -n 'prefers-reduced-motion|motion-reduce:' src

# --- icons ---
# mixed icon sizes within the same context
rg -oN 'w-[0-9]+ h-[0-9]+|size-[0-9]+|width="[0-9]+"' src | sort | uniq -c | head -20

# --- typography micro-consistency ---
# letter-spacing applied to only some headings
rg -n 'tracking-(tight|wide|wider)|letter-spacing' src | head

# inconsistent line-height tokens on similar text
rg -oN 'leading-(none|tight|snug|normal|relaxed|loose)|line-height:\s*[0-9.]+' src | sort | uniq -c

# --- dividers / borders ---
# mixed border-color tokens for dividers
rg -oN 'border-(gray|slate|zinc|neutral)-[0-9]{3}' src | sort | uniq -c
```

## Common issues & anti-patterns

- **The 2px rounding error:** `padding: 22px` where the spec was 20px because it "looked better"; at scale, several 2px deviations make the grid feel chaotic.
- **Orphan hover state:** a card is clickable (pointer cursor, onClick) but has no hover background or shadow change — the affordance signal is missing.
- **Mixed stroke icon set:** twelve icons at 1.5px stroke mixed with four at 2px — they read heavier and inconsistent.
- **Disabled that looks enabled:** full color opacity, no `cursor: not-allowed` — users click it repeatedly.
- **Shadow stack collision:** a dropdown inside a modal has a lighter shadow than its parent modal, making it appear behind the modal background.
- **Zero-transition input:** the focus ring snaps on with no transition — abrupt and jarring on an otherwise polished UI.
- **Inconsistent empty-state icon sizing:** one empty state uses a 40px illustration, another a 96px SVG — the app feels uneven across views.
- **Letter-spacing on some headings only:** tracking applied to the hero H1 but not other headings, so they look like different typefaces.
- **Mixed divider colors:** some separators use `border-gray-200` and others `border-slate-200`, a difference too small to be intentional but visible side by side.
- **Optically off-center icon:** a play or chevron glyph mathematically centered in its button but visually leaning because its bounding box is asymmetric.
- **Overlong transition:** a 500ms ease on a simple hover color change, which makes the whole interface feel sluggish and unresponsive.

## Required output

Return a structured punch list with:
1. **Polish readiness score:** Ready to ship, Minor fixes needed, or Multiple issues blocking polish.
2. **Alignment issues:** element selector or component name plus the exact pixel discrepancy.
3. **Missing interactive states:** component, state, and recommended CSS or class fix.
4. **Typography inconsistencies:** mismatched weights, sizes, or line-heights with locations.
5. **Spacing violations:** off-scale values with file or component locations.
6. **Estimated fix effort:** group findings into under 5 minutes, 5 to 15 minutes, and over 15 minutes.

## Safety

- Apply polish fixes one component at a time and verify in the browser before moving on — small CSS changes cascade.
- Do not change spacing or sizing in shared tokens without checking every consuming component.
- Preserve existing animation behavior unless explicitly asked to change it — motion changes affect perceived performance.
- Keep recommendations token or class based and minimal-diff; do not refactor markup structure during a polish pass.
- Redact any secret-like values surfaced while reading config.

## Completion criteria

Done means alignment, spacing rhythm, interactive states, icon sizing, typography, radius, shadow hierarchy, and motion were each checked; every finding names the component and the corrected value; findings are bucketed by fix effort; `prefers-reduced-motion` handling is confirmed; and a readiness score is given.

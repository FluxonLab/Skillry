---
name: visual-polish-pass
description: Use when you need to perform final visual polish checks for alignment, rhythm, affordances, and professional finish.
---

# Visual Polish Pass

## Purpose
Perform a pre-ship visual polish audit covering pixel-level alignment, consistent spacing rhythm, interactive state completeness (hover, active, focus, disabled, loading), icon sizing and optical alignment, border radius consistency, shadow hierarchy, and the overall sense of craft and intentionality. Produces a concrete punch list of small but high-ROI fixes.

## When to use
- A feature is functionally complete and ready for a final visual QA pass before shipping.
- The UI looks "almost right" but something feels off and the specific issues have not been named.
- A designer has handed off specs and you need to verify the implementation matches the intent.
- A design review revealed inconsistencies but did not fully enumerate them.
- You are preparing a demo or client presentation and want to maximize visual credibility.

## When not to use
- The layout has structural problems (wrong hierarchy, broken mobile layout) — fix structure first with `web-design-review` or `responsive-layout-review`, then polish.
- The request is about accessibility — focus and outline states overlap but accessibility is a different audit (`accessibility-audit`).
- The feature is not visually implemented yet — polish applies to built UI, not wireframes.

## Procedure

1. **Grid and alignment audit.** Identify the layout grid (8px, 4px, or 12-column). Check that text, icons, and card edges align to grid points. Specifically: card padding should be a grid multiple (16px or 24px, not 15px or 22px); inline elements (icon + label) should be vertically centered (`align-items: center`), not approximated by `margin-top: 2px`; columns in a grid should have uniform gutter widths.

2. **Spacing rhythm check.** Scan all components for inconsistent gap values at the same semantic level. If card padding is 24px in one component and 20px in another with no design rationale, that is a rhythm violation. Same for section padding — pick one value (e.g., 64px vertical) and apply it consistently across sections. Use a spacing scale (4/8px multiples) and flag any value not on the scale.

3. **Interactive state completeness.** For every interactive element — buttons, links, inputs, checkboxes, toggles, tabs, dropdowns — verify these states exist and are visually distinct: `default`, `hover`, `active` (pressed), `focus-visible`, `disabled`, `loading` (where applicable). A button that has `hover` but not `active` or `disabled` is incomplete. A link with no hover state feels static and untrustworthy.

4. **Icon audit.** Check that icons are optically sized consistently — if the icon set is 20px, all icons should be 20px, not a mix of 16px, 18px, 20px, and 24px based on individual developer preference. Verify that icons are optically centered within their container (SVG viewBox may need adjustment for icons that appear top-heavy or offset). Check stroke width consistency for line-style icons.

5. **Typography consistency pass.** Scan for: different font-weight values used for elements at the same hierarchy level (some `<h3>` are `font-weight: 600`, others are `font-weight: 500`); inconsistent line-height between similar text blocks; `letter-spacing` applied only to some headings; text elements using pixel sizes not on the type scale.

6. **Border radius consistency.** Identify the border-radius values used across buttons, cards, inputs, modals, and badges. A product that uses `rounded-md` (6px) for cards, `rounded-full` for pills, `rounded-sm` (2px) for inputs, and `rounded-xl` (12px) for modals has incoherent radius logic. Establish 2-3 approved radius values and flag violations.

7. **Shadow hierarchy.** Shadows should indicate elevation: cards on a flat surface have a lighter shadow than modals floating above the page. Verify: no two elements at different z-index levels have the same shadow; dropdown and tooltip shadows are stronger than card shadows; no element has `box-shadow: none` when it visually overlaps another element (creates depth ambiguity).

8. **Color consistency micro-audit.** Check that muted text always uses the same token (`text-muted-foreground` or `text-gray-500`), that all dividers use the same border color token, and that all badge background colors follow the semantic palette. Flag any hex color hardcoded in a component that deviates from the palette even slightly (e.g., `#6b7280` vs. `#64748b` — visually similar but inconsistent).

9. **Motion and transition polish.** Interactive elements should have consistent transition timing: `transition-colors duration-150` for color changes, `transition-transform duration-200` for scale/position changes. Elements that animate in should use consistent easing. Flag: elements with no transition at all (abrupt state changes), elements with overly long transitions (> 300ms for simple color change), and inconsistent easing between similar components.

10. **Final "scan test."** Step back (or zoom out to 50%) and scan the page as a whole. Note: any element that draws the eye unexpectedly (misaligned, wrong size, wrong color). Note any section that feels "lighter" or "heavier" visually than neighboring sections. Note any text that appears to float (insufficient line-height between heading and body).

## Checklist
- [ ] Card padding and section padding are exact multiples of 4px or 8px — no rounding to non-scale values
- [ ] Icon sizes are consistent within the same context (all nav icons the same size, all action icons the same size)
- [ ] All icons are optically centered in their containers — not just mathematically centered
- [ ] Every button has distinct default, hover, active, focus-visible, and disabled states
- [ ] Every input has distinct default, focused, filled, error, and disabled states
- [ ] No two elements at the same hierarchy level use different font-weight values without a documented reason
- [ ] Border radius values reduced to <= 3 semantic levels: small (inputs/badges), medium (cards), large (modals/sheets)
- [ ] Shadow values indicate elevation: tooltip > modal > card > flat element
- [ ] Muted text uses a single token consistently across all components
- [ ] Dividers and borders use a single border-color token — no mix of `border-gray-200` and `border-slate-200`
- [ ] Transition timing is consistent: color changes ~150ms, movement/scale ~200ms, complex entrances ~300ms
- [ ] No abrupt state changes on interactive elements (missing `transition` property)
- [ ] Inline icon+text combinations are vertically centered (`align-items: center`) — no optical misalignment

## Common issues & anti-patterns
- **The 2px rounding error:** a designer spec'd `padding: 20px` but the developer set `padding: 22px` because it "looked better." At scale, 6 components each with a different 2px deviation create a chaotic grid.
- **Orphan hover state:** a card is hoverable (cursor changes to pointer, there is an onClick) but has no background change or shadow change on hover — the affordance signal is missing.
- **Mixed stroke icon set:** 12 icons from Heroicons (1.5px stroke) mixed with 4 icons from another library (2px stroke) — they appear heavier and inconsistent.
- **Disabled that looks enabled:** a disabled button with full color opacity and no `cursor: not-allowed` — users click it repeatedly, confused it is not responding.
- **Shadow stack collision:** a dropdown inside a modal — the dropdown has a lighter `box-shadow` than the modal it lives inside, making the dropdown appear to float behind the modal background.
- **Zero-transition form input:** input fields that switch from default border color to blue focus ring with no transition — abrupt and visually jarring on a polished UI.
- **Inconsistent empty-state icon sizing:** some empty states use a 40px illustration, others use a 96px SVG — the page feels inconsistent across different empty-state views.

## Required output
Return a structured punch list with:
1. **Polish readiness score**: Ready to ship / Minor fixes needed / Multiple issues blocking polish.
2. **Alignment issues** (with element selector or component name and exact pixel discrepancy).
3. **Missing interactive states** (component + state + recommended CSS/class fix).
4. **Typography inconsistencies** (mismatched weights, sizes, or line-heights with locations).
5. **Spacing violations** (non-scale values with file/component locations).
6. **Estimated fix effort**: group findings into <5 min, 5-15 min, and >15 min fix categories.

## Safety
- Apply polish fixes one component at a time and verify in the browser before moving to the next — small CSS changes cascade.
- Do not change spacing or sizing values in shared tokens without checking all consuming components.
- Preserve existing animation behavior unless explicitly asked to change it — motion changes affect perceived performance.

---
name: ui-consistency-review
description: Use when you need to audit UI consistency, spacing, color, typography, states, accessibility basics, and responsive behavior.
---

# UI Consistency Review

## Purpose
Use this skill to audit UI consistency, spacing, color, typography, states, accessibility basics, and responsive behavior. All findings are anchored to the project's own design tokens and system — not personal taste — so fixes are minimal-diff and immediately actionable.

## When to use
- New components or screens were added and need a consistency pass against the established spacing scale, color tokens, and type system before review or release.
- Hardcoded hex values, magic pixel values, or missing interactive states (hover, focus, disabled, error, empty) have been spotted in the codebase.
- An accessibility concern was raised — missing focus rings, low contrast text, or non-semantic clickable elements need a systematic audit.
- The UI has grown organically across multiple contributors and visual drift (inconsistent font sizes, spacing rhythm, or button styles) has accumulated.

## When not to use
- The task is unrelated to frontend and web design work.
- The work would require production deploys, destructive data actions, or secret disclosure.
- A narrower skill or existing project instruction already covers the need.

## Procedure
1. Establish the intended system first: find the spacing scale, color tokens, type scale, and component primitives (Tailwind config, CSS vars, theme file, design tokens). Review against that source of truth, not personal taste.
2. Audit spacing & layout: is spacing on the scale (4/8px rhythm) or are there magic numbers? Consistent gaps, padding, alignment?
3. Audit color: tokens vs hardcoded hex; sufficient text contrast (WCAG AA 4.5:1 body, 3:1 large text).
4. Audit typography: a bounded type scale, consistent line-height/weight, no one-off font sizes.
5. Audit interactive states: every actionable element needs hover, focus-visible, active, disabled — plus loading/empty/error where data is involved.
6. Audit responsive behavior: breakpoints, overflow, text truncation/wrapping, tap target ≥ 44px.
7. Report per-component findings with severity and the token/value to use instead.

## Concrete checks
- Hardcoded colors instead of tokens: grep `#[0-9a-fA-F]{3,8}` and `rgb(a)(` in components.
- Magic spacing: inline `px` values and `style={{ }}` overrides outside the scale.
- Missing focus ring: interactive elements with `outline: none` and no `:focus-visible` replacement.
- Missing states: buttons/links without disabled/loading handling; lists without empty/error states.
- Type drift: more than ~6 distinct font-size values across the app.
- A11y basics: images without `alt`, inputs without an associated `<label>`/`aria-label`, non-semantic `<div onClick>` instead of `<button>`.
- Contrast: light-gray text on white; placeholder used as the label.

## Commands
```bash
# hardcoded hex/rgb in components
rg -n '#[0-9a-fA-F]{3,8}\b|rgba?\(' src/components src/app 2>/dev/null
# focus removed without a replacement
rg -n 'outline:\s*none|outline-none' src | rg -v 'focus-visible'
# clickable divs (should be buttons)
rg -n '<div[^>]*onClick' src
# count distinct font sizes (drift signal)
rg -oN 'text-(xs|sm|base|lg|xl|2xl|3xl|4xl)|font-size:\s*[0-9.]+(px|rem)' src | sort -u | wc -l
```

## Required output
Return findings grouped by area (spacing, color, type, states, responsive, a11y) as `severity | component/file:line | issue | recommended token/value`. Lead with systemic issues (a missing token, a repeated bad pattern) over one-off nits. Note what's already consistent.

## Safety checks
- Review against the project's existing tokens/system; do not impose a new design language.
- Visual/static review only; do not refactor component APIs as a side effect.
- Keep recommendations token-based and minimal-diff.
- Flag contrast/keyboard issues as accessibility blockers, not cosmetic.

## Completion criteria
Done means spacing, color, typography, interactive states, responsive behavior, and accessibility basics were each checked against the project's system, findings carry severity + a concrete fix, and systemic issues are prioritized over isolated nits.

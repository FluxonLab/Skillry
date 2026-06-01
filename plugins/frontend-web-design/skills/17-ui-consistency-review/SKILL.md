---
name: ui-consistency-review
description: Use when you need to audit UI consistency, spacing, color, typography, states, accessibility basics, and responsive behavior.
---

# UI Consistency Review

## Purpose

Audit UI consistency across spacing, color, typography, interactive states, accessibility basics, and responsive behavior — with every finding anchored to the project's own design tokens and component system rather than personal taste. The output is a minimal-diff punch list: each issue names the offending file and line, the bad value, and the exact token or utility class that should replace it, so a developer can fix it without a second round of clarification. The review is static and visual only; it never refactors component APIs or invents a new design language.

## When to use

- New components or screens were added and need a consistency pass against the established spacing scale, color tokens, and type system before review or release.
- Hardcoded hex values, magic pixel values, or missing interactive states (hover, focus, disabled, error, empty) have been spotted in the codebase.
- An accessibility concern was raised — missing focus rings, low-contrast text, or non-semantic clickable elements need a systematic sweep.
- The UI has grown across multiple contributors and visual drift (inconsistent font sizes, spacing rhythm, or button styles) has accumulated.
- A design system or Tailwind config exists and you need to confirm production code actually consumes it instead of bypassing it with arbitrary values.

## When not to use

- The task is unrelated to frontend and web design work.
- The work would require production deploys, destructive data actions, or secret disclosure.
- The page has structural layout breakage (wrong hierarchy, broken mobile). Fix structure with `web-design-review` or `responsive-layout-review` first, then run consistency.
- A narrower skill already covers the exact need: `design-system-review` for token architecture and duplicate primitives, `accessibility-audit` for a full WCAG pass, `visual-polish-pass` for final pixel finish.

## Procedure

1. **Establish the intended system first.** Locate the spacing scale, color tokens, type scale, radius/shadow scale, and component primitives before judging anything. Look in `tailwind.config.{js,ts}`, CSS custom properties in `:root`, a `tokens.json`, or a theme provider. Record the scale base (4px or 8px), the named color roles, and the bounded type steps. Review against this source of truth, not personal taste.
2. **Audit spacing and layout.** Confirm padding, margin, and gap values land on the scale. Flag inline `style={{ }}` overrides and arbitrary Tailwind values such as `p-[13px]` or `gap-[7px]`. Check that related elements (a label and its field) sit tighter than unrelated sections, and that gutters in a grid are uniform.
3. **Audit color.** Compare every hardcoded hex/rgb against the token palette — a literal `#3b82f6` that equals `colors.primary` is a violation. Verify text contrast meets WCAG 2.1 AA: 4.5:1 for body text and 3:1 for large text (>=24px regular or >=18.66px bold), plus 3:1 for UI component boundaries and focus indicators.
4. **Audit typography.** Confirm a bounded type scale (roughly five to seven steps). Flag one-off `font-size` values off the scale, mixed `font-weight` at the same hierarchy level, and inconsistent `line-height` between similar text blocks.
5. **Audit interactive states.** Every actionable element needs `:hover`, `:focus-visible`, `:active`, and `:disabled`. Data-bound surfaces additionally need loading, empty, and error states. A button with hover but no disabled or focus-visible state is incomplete.
6. **Audit responsive behavior.** Check breakpoints, horizontal overflow, text truncation versus wrapping, and touch targets >=44x44px (Apple HIG) or 48x48dp (Material) at mobile widths. Confirm body text stays >=16px so mobile browsers do not auto-zoom inputs on focus.
7. **Audit accessibility basics.** Images need `alt`; form inputs need an associated `<label>` or `aria-label`; clickable behavior belongs on `<button>`/`<a>`, not `<div onClick>`. Decorative icons need `aria-hidden="true"`.
8. **Report per-component findings** with severity and the token/value to use instead, leading with systemic issues (a missing token, a repeated bad pattern, a global `outline: none`) over isolated nits.

## Concrete checks

Spacing and layout:
- Padding, margin, and gap values land on the 4/8px scale — no arbitrary `p-[13px]` or `mt-[22px]`.
- No inline `style={{ }}` overrides that hardcode spacing outside the scale.
- Related elements (label and field, icon and caption) are grouped tighter than unrelated sections.
- Grid and flex gutters are uniform within the same layout.

Color and contrast:
- Every color is a token reference, not a literal hex that duplicates a token value.
- Body text meets WCAG 2.1 AA contrast of 4.5:1; large text and UI boundaries meet 3:1.
- Disabled and muted states remain legible, not washed-out gray on white.
- A single muted-text token and a single border-color token are used everywhere.

Typography:
- The type scale is bounded to roughly five to seven steps, all referenced by name.
- No mismatched `font-weight` at the same hierarchy level without a documented reason.
- `line-height` is consistent within body text and within headings.

States and accessibility:
- Every actionable element has `:hover`, `:focus-visible`, `:active`, and `:disabled`.
- Data-bound surfaces have loading, empty, and error states.
- `<img>` has `alt`; inputs have a `<label>` or `aria-label`; clickable behavior is on `<button>`/`<a>`.
- Touch targets are >=44x44px / 48x48dp at mobile widths; body text stays >=16px.

## Commands

```bash
# --- color tokens ---
# hardcoded hex/rgb in components (should be tokens)
rg -n '#[0-9a-fA-F]{3,8}\b|rgba?\(' src/components src/app 2>/dev/null

# raw Tailwind color utilities used in place of semantic tokens
rg -n 'bg-(red|blue|green|gray|slate|zinc)-[0-9]{3}|text-(gray|slate)-[0-9]{3}' src

# rank the most-used literal colors (near-duplicate detection)
rg -oN '#[0-9a-fA-F]{6}' src | sort | uniq -c | sort -rn | head -20

# --- spacing ---
# arbitrary Tailwind spacing values off the scale
rg -n '\b[pm][trblxy]?-\[[0-9]+px\]|gap-\[[0-9]+px\]' src

# inline style overrides that bypass the system
rg -n 'style=\{\{' src

# --- typography ---
# count distinct font sizes (drift signal — expect <= ~6)
rg -oN 'text-(xs|sm|base|lg|xl|2xl|3xl|4xl|5xl)|font-size:\s*[0-9.]+(px|rem)' src | sort -u | wc -l

# distinct font-weights in use (expect a small, intentional set)
rg -oN 'font-(thin|light|normal|medium|semibold|bold|extrabold)|font-weight:\s*[0-9]+' src | sort | uniq -c

# --- states ---
# interactive elements vs how many declare hover/focus-visible
rg -c 'hover:|focus-visible:' src
rg -n '<button|<a |role="button"' src | wc -l

# focus removed without a focus-visible replacement (keyboard blocker)
rg -n 'outline:\s*none|outline-none' src | rg -v 'focus-visible'

# --- accessibility ---
# clickable divs that should be buttons
rg -n '<div[^>]*onClick' src

# images missing alt (quick a11y sweep)
rg -n '<img(?![^>]*\balt=)' src

# --- radius / shadow drift ---
# distinct border-radius values in use (expect <= 3)
rg -oN 'rounded-(sm|md|lg|xl|2xl|full|none)|border-radius:\s*[0-9.]+(px|rem)' src | sort | uniq -c

# distinct shadow utilities (elevation should be a small, ordered set)
rg -oN 'shadow-(sm|md|lg|xl|2xl|none|inner)' src | sort | uniq -c

# --- responsive / theme ---
# fixed pixel widths that may overflow on small screens
rg -n 'w-\[[0-9]{3,}px\]|width:\s*[0-9]{3,}px' src

# inputs with sub-16px font that trigger mobile auto-zoom
rg -n 'text-(xs|sm)\b' src/components | rg -i 'input|select|textarea'

# theme coverage: is dark mode a token swap or duplicated CSS?
rg -n 'dark:|prefers-color-scheme|data-theme' src | head
```

## Common issues & anti-patterns

- **Token defined, never used:** `colors.primary` exists in the config but components write `bg-blue-600` directly, so a palette change silently misses them.
- **Orphan hover state:** an element has `cursor: pointer` and an `onClick` but no visible hover or focus change — the affordance signal is absent.
- **Focus killed for looks:** `outline: none` applied globally with no `:focus-visible` replacement, leaving keyboard users with no visible focus position.
- **Placeholder-as-label:** an input whose only label is its placeholder — the label vanishes on input and is invisible to screen readers.
- **Weight drift:** some `<h3>` are `font-semibold` (600), others `font-medium` (500), with no rule, so the hierarchy reads inconsistently.
- **Disabled that looks enabled:** a disabled button at full opacity with no `cursor: not-allowed`, so users click it repeatedly.
- **The 2px rounding error:** `padding: 22px` instead of the scale's 24px, repeated with small variations across components until the grid feels chaotic.
- **Mixed icon sizes:** nav icons at 20px next to action icons at 16px and 24px, with no contextual rule, so the toolbar looks uneven.
- **Near-duplicate grays:** `#6b7280` in one component and `#64748b` in another for the same muted text — visually similar, technically inconsistent, and impossible to theme.
- **Color-only meaning:** status conveyed solely by a red or green dot with no icon or label, which fails for color-blind users and screen readers.
- **Inconsistent radius logic:** inputs at `rounded-sm`, cards at `rounded-md`, modals at `rounded-xl`, and pills at `rounded-full` with no documented hierarchy, so the product reads as assembled from unrelated kits.

## Required output

Return a structured report with:
1. **System summary:** where the tokens live (config or CSS variables), the scale base, and whether production code actually consumes them.
2. **Findings by area:** spacing, color, type, states, responsive, and a11y, each row as `severity | component/file:line | issue | recommended token/value`.
3. **Accessibility blockers:** contrast and keyboard-focus failures listed separately and explicitly, not buried among cosmetic nits.
4. **Already-consistent areas:** a short note on what is solid, so the report stays balanced.
5. **Top three drift removers:** the changes that would eliminate the most repeated violations, ordered by leverage.

Lead with systemic issues (a missing token, a repeated bad pattern, a global `outline: none`) over one-off nits.

## Safety

- Review against the project's existing tokens and system; do not impose a new design language.
- Static and visual review only — do not refactor component APIs or rename props as a side effect.
- Keep recommendations token-based and minimal-diff; change one component at a time, since shared-token edits cascade to every consumer.
- Treat contrast and keyboard-focus issues as accessibility blockers, not optional polish.
- Do not modify shared token files without confirming every consuming component still renders correctly.
- Redact any secret-like values surfaced while reading config; describe key names only.

## Completion criteria

Done means spacing, color, typography, interactive states, responsive behavior, and accessibility basics were each checked against the project's own system; every finding carries a severity and a concrete token/value fix with `file:line`; systemic issues are prioritized over isolated nits; accessibility blockers are called out separately from cosmetic drift; and the report ends with the three highest-leverage changes.

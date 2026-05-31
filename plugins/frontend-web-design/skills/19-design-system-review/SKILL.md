---
name: design-system-review
description: Use when you need to inspect component reuse, design tokens, variants, primitives, and design system drift.
---

# Design System Review

## Purpose
Audit a codebase's design system health: token definitions, component variants, spacing scale adherence, duplicate components, and drift between the design system and production UI. Surfaces the specific files, class names, and values causing inconsistency so fixes are unambiguous.

## When to use
- The codebase has grown and there are suspicions of duplicate Button, Card, or Input components.
- A Tailwind config, CSS custom properties file, or tokens.js exists and you need to verify it is actually used consistently.
- A Storybook or component library exists and you need to check whether production pages use it or bypass it.
- The design team is migrating to a new token naming convention and you need an impact analysis.
- Visual inconsistencies (different shades of blue for primary actions, inconsistent border radii) are reported but not yet located.

## When not to use
- No component library or shared style layer exists yet — this review assumes at least one exists.
- The request is about a single page's layout, not system-level patterns (use `web-design-review` instead).
- The project has no CSS or styling — purely backend or CLI work.

## Procedure

1. **Locate the token source of truth.** Find `tailwind.config.js/ts`, `tokens.json`, `_variables.scss`, or CSS custom properties in `:root`. Note the spacing scale (confirm it is 4px or 8px based), color palette keys, and type scale values. If none exist, flag "no formal token layer" as a Critical finding.

2. **Inventory shared components.** List all files in `components/`, `ui/`, `design-system/`, or equivalent. Note how many implement a Button, Input, Modal, Badge, or Card. More than one implementation of the same primitive is a drift signal.

3. **Check token usage consistency.** Search for hardcoded hex values (e.g., `#3b82f6`, `#1d4ed8`) in component and page files. Each hardcoded color that matches a token value is a violation. Same for hardcoded pixel values that match token spacing (e.g., `margin: 16px` when `spacing-4` exists).

4. **Audit spacing scale adherence.** Scan CSS/Tailwind classes for non-scale values: `p-[13px]`, `mt-[22px]`, `gap-[7px]`. Any arbitrary value that is not a multiple of 4px is a scale violation unless a documented exception exists.

5. **Review component variants.** For each shared component, confirm that visual variations (size, color, state) are expressed as named props/variants, not as ad-hoc className overrides at the call site. E.g., `<Button variant="danger">` is correct; `<Button className="bg-red-600 text-white">` at 12 call sites is drift.

6. **Check Storybook coverage.** If Storybook exists, compare the story count per component against actual variants in production. Components with variants not in Storybook are under-documented and prone to further drift.

7. **Identify orphan styles.** Look for global CSS files with rules that target specific page classes (`.dashboard-header`, `.pricing-card`) rather than tokens or shared components. These are system bypasses.

8. **Prioritize and report.** Classify each finding by type (Token violation / Duplicate component / Orphan style / Missing variant) and count occurrences. High-occurrence violations are highest priority.

## Checklist
- [ ] A single source-of-truth token file exists and is referenced by the build tool
- [ ] Spacing scale is 4px or 8px based; no arbitrary pixel values without documented exception
- [ ] No more than one implementation of each UI primitive (Button, Input, Modal, Badge, Card)
- [ ] Color tokens cover all semantic roles: primary, secondary, destructive, muted, surface, border
- [ ] Component variants are expressed as props, not ad-hoc className overrides at call sites
- [ ] No hardcoded hex values in component or page files that duplicate token values
- [ ] Storybook (or equivalent) has stories for all variants of each shared component
- [ ] Typography scale is tokenized: font-size, font-weight, line-height defined as named steps
- [ ] No page-specific CSS that overrides shared component styles at the global level
- [ ] Dark mode (if applicable) is implemented via token swap, not duplicate CSS blocks

## Common issues & anti-patterns
- **Ghost Button:** a second `GhostButton.tsx` file created because the developer couldn't find the variant prop on the existing `Button`.
- **Magic numbers in JSX:** `style={{ marginTop: 13 }}` inline on a one-off layout adjustment — then copied 20 times.
- **Color name collision:** `primary` in Tailwind config is `#2563eb` but a component file imports `brand.primary = '#1d4ed8'` from a separate constants file.
- **Token defined, never used:** `colors.danger` exists in the config but components use `bg-red-600` directly.
- **Storybook graveyard:** stories exist but were never updated when props changed — they throw runtime errors and are ignored.
- **Spacing leapfrog:** a 4px scale that has `space-1=4, space-2=8` but then `space-3=16` — skipping 12 — causing inconsistent component density.

## Required output
Return a structured report with:
1. **Token layer health** (exists / partial / missing) with file paths.
2. **Duplicate component list**: name, file count, and recommended consolidation target.
3. **Top 5 token violations** by occurrence count: hardcoded value, token it should use, file list.
4. **Spacing scale violations**: count of non-scale arbitrary values, example locations.
5. **Storybook gap** (if applicable): components with missing variant coverage.
6. **Priority fix order**: which three changes would eliminate the most drift.

## Safety
- Do not delete or rename component files without explicit instruction — propose consolidation only.
- Do not modify token files without confirming the change won't break consuming packages or apps.
- Run `grep` and `find` searches non-destructively before any edit.

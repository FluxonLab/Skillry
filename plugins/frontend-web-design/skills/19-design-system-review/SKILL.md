---
name: design-system-review
description: Use when you need to inspect component reuse, design tokens, variants, primitives, and design system drift.
---

# Design System Review

## Purpose

Audit a codebase's design system health: token definitions, component variants, spacing-scale adherence, duplicate primitives, and drift between the design system and the production UI. The output names the specific files, class names, and values causing inconsistency, ranked by occurrence count, so consolidation is unambiguous and the highest-leverage fixes are obvious. This is a system-level audit; it proposes consolidation targets rather than deleting or renaming files unilaterally.

## When to use

- The codebase has grown and there are suspicions of duplicate Button, Card, or Input components.
- A Tailwind config, CSS custom-properties file, or `tokens.json` exists and you need to verify it is actually consumed consistently.
- A Storybook or component catalog exists and you need to check whether production pages use it or bypass it.
- The team is migrating to a new token naming convention and needs an impact analysis.
- Visual inconsistencies (different shades of blue for primary actions, inconsistent border radii) are reported but not yet located.

## When not to use

- No component library or shared style layer exists yet — this review assumes at least one exists.
- The request is about a single page's layout, not system-level patterns — use `web-design-review`.
- The request is about final pixel polish of one feature — use `visual-polish-pass`.
- The request is about per-component consistency against the system — use `ui-consistency-review`.
- The project has no CSS or styling (pure backend or CLI work).

## Procedure

1. **Locate the token source of truth.** Find `tailwind.config.{js,ts}`, `tokens.json`, `_variables.scss`, or CSS custom properties in `:root`. Record the spacing scale (confirm 4px or 8px base), color palette keys, type scale, radius scale, and shadow scale. If none exists, flag "no formal token layer" as a Critical finding.
2. **Inventory shared components.** List files in `components/`, `ui/`, `design-system/`, or equivalent. Count how many implement a Button, Input, Modal, Badge, or Card. More than one implementation of the same primitive is a drift signal — record each path.
3. **Check token usage consistency.** Search for hardcoded hex values (`#3b82f6`, `#1d4ed8`) in component and page files. Any literal that equals a token value is a violation. The same applies to hardcoded pixels matching token spacing (`margin: 16px` when `spacing-4` exists).
4. **Audit spacing-scale adherence.** Scan for off-scale arbitrary values: `p-[13px]`, `mt-[22px]`, `gap-[7px]`. Any value that is not a multiple of the scale base is a violation unless a documented exception exists.
5. **Review component variants.** For each shared component, confirm visual variations (size, color, state) are expressed as named props or variants, not ad-hoc className overrides at the call site. `<Button variant="danger">` is correct; `<Button className="bg-red-600 text-white">` at twelve call sites is drift.
6. **Check Storybook or catalog coverage.** If a catalog exists, compare stories per component against the variants actually used in production. Variants with no story are under-documented and prone to further drift.
7. **Identify orphan styles.** Look for global CSS rules targeting page-specific classes (`.dashboard-header`, `.pricing-card`) rather than tokens or shared components — these are system bypasses.
8. **Check theme parity.** If light/dark or multi-theme support exists, confirm it is implemented by token swap (CSS variables, `dark:` variants) rather than duplicate hardcoded CSS blocks, and that every semantic role has a value in each theme.
9. **Size each consolidation.** For every duplicate primitive, count the call sites of each version so the recommended merge target is the one with the most usage and the migration cost is known up front.
10. **Prioritize and report.** Classify each finding by type (Token violation / Duplicate component / Orphan style / Missing variant / Theme gap) and count occurrences. High-occurrence violations are the highest priority.

## Concrete checks

Token layer:
- A single source-of-truth token file exists and is imported by the build tool.
- Color tokens cover every semantic role: primary, secondary, destructive, muted, surface, border, ring.
- Type, radius, and shadow are tokenized as named steps, not ad-hoc per component.
- No skipped steps in the scale (4, 8, 12, 16 — not 4, 8, 16) that cause uneven density.

Components and variants:
- No more than one implementation of each primitive (Button, Input, Modal, Badge, Card).
- Variants are props, not className overrides repeated at call sites.
- Catalog stories exist for the variants actually used in production.

Drift signals:
- No hardcoded hex/rgb in components that duplicates a token value.
- No off-scale arbitrary spacing or radius values.
- No global page-specific CSS overriding shared component styles.
- Dark or alternate themes are a token swap, not duplicated CSS.
- No two near-identical color literals (for example two slightly different blues) in production.
- No inline `style={{ }}` that hardcodes a value the token layer already provides.

## Commands

```bash
# --- duplicate primitives ---
# multiple files implementing the same component
fd -t f -i 'button' src | head
fd -t f -i 'modal|dialog' src | head
fd -t f -i 'input|textfield' src | head

# duplicate exported component symbols across files
rg -oN 'export (?:default )?(?:function|const|class) (\w+)' -r '$1' src | sort | uniq -d

# --- token bypasses (color) ---
# hardcoded hex/rgb in components and pages
rg -n '#[0-9a-fA-F]{3,8}\b|rgba?\(' src/components src/app 2>/dev/null

# raw Tailwind color utilities used instead of semantic tokens
rg -n 'bg-(red|blue|green|gray|slate)-[0-9]{3}' src | head -40

# rank most-used literal colors (near-duplicate detection)
rg -oN '#[0-9a-fA-F]{6}' src | sort | uniq -c | sort -rn | head -20

# --- token bypasses (spacing / radius) ---
# off-scale arbitrary Tailwind values
rg -n '\b[pm][trblxy]?-\[[0-9]+px\]|gap-\[[0-9]+px\]|rounded-\[[0-9]+px\]' src

# --- variant drift ---
# components styled by className override at the call site
rg -n '<Button[^>]*className=|<Card[^>]*className=|<Input[^>]*className=' src | head -40

# --- token file wiring ---
# verify the token file is actually imported by the build
rg -n 'tailwind.config|tokens|:root\b|--color-' . 2>/dev/null | head

# --- theme parity ---
# is dark mode a token swap or duplicated CSS?
rg -n 'dark:|prefers-color-scheme|data-theme|\.dark ' src | head

# --- catalog coverage ---
# count story files vs component files (coverage gap signal)
fd -e stories.tsx -e stories.jsx src | wc -l
fd -e tsx src/components | wc -l

# --- impact analysis for a token rename ---
# every file that consumes a given token (replace tokenName)
rg -l 'tokenName|--tokenName|colors\.tokenName' src

# how many call sites use a primitive (sizing a consolidation)
rg -c '<Button' src | rg -v ':0$' | wc -l

# --- spacing scale shape ---
# list the spacing keys the config defines (look for skipped steps)
rg -n 'spacing:|--space-|gap-[0-9]' tailwind.config.* src 2>/dev/null | head -20
```

## Common issues & anti-patterns

- **Ghost Button:** a second `GhostButton.tsx` created because the developer could not find the `variant` prop on the existing `Button`.
- **Magic numbers in JSX:** `style={{ marginTop: 13 }}` on a one-off adjustment, then copy-pasted into twenty files.
- **Color name collision:** `primary` in Tailwind is `#2563eb` but a `constants.ts` imports `brand.primary = '#1d4ed8'` — two near-identical blues in production.
- **Token defined, never used:** `colors.danger` exists in the config but components write `bg-red-600` directly, so renaming the token misses them.
- **Storybook graveyard:** stories exist but were never updated when props changed; they throw at render and are quietly ignored.
- **Spacing leapfrog:** a 4px scale with `space-1=4, space-2=8` then `space-3=16` — skipping 12 — producing inconsistent component density.
- **Theme via duplication:** dark mode implemented as a parallel hardcoded CSS block instead of a token swap, so every new component must be styled twice and inevitably drifts.
- **Variant explosion at call sites:** the same component customized with ten different className combinations across the app, defeating the point of a shared primitive.
- **Two token systems:** a Tailwind config and a separate `theme.ts` constants file both defining colors, so contributors pick whichever they find first and the two drift apart.
- **Orphan global stylesheet:** a `globals.css` full of `.page-x .card` rules that silently overrides the shared Card component on specific pages, invisible to anyone reading the component.
- **Untokenized radius and shadow:** every component picks its own `border-radius` and `box-shadow` ad hoc, so cards, modals, and inputs have no coherent elevation or corner language.

## Required output

Return a structured report with:
1. **Token layer health:** exists, partial, or missing, with file paths and the scale base.
2. **Duplicate component list:** name, file count, and the recommended consolidation target.
3. **Top five token violations** by occurrence count: the hardcoded value, the token it should use, and the file list.
4. **Spacing scale violations:** count of off-scale arbitrary values with example locations.
5. **Catalog gap** (if applicable): components missing variant coverage.
6. **Theme parity** (if applicable): semantic roles missing a value in any theme.
7. **Priority fix order:** the three changes that would eliminate the most drift.

## Safety

- Do not delete or rename component files without explicit instruction — propose consolidation targets only.
- Do not modify token files without confirming the change will not break consuming packages or apps.
- Run all search commands non-destructively before suggesting any edit.
- Redact any secret-like values surfaced while reading config; describe key names only.
- When a token rename is proposed, list every consuming file so the blast radius is explicit.

## Completion criteria

Done means the token source of truth is located (or its absence flagged Critical); duplicate primitives are listed with consolidation targets; the top token and spacing violations are ranked by occurrence with `file:line` evidence; theme parity is checked where applicable; and the report ends with the three highest-leverage changes.

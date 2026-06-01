---
name: accessibility-audit
description: Use when you need to audit semantic HTML, keyboard navigation, focus, contrast, labels, and screen reader basics.
---

# Accessibility Audit

## Purpose
Audit a page or component against WCAG 2.2 Level AA. Covers semantic HTML structure, keyboard
navigation and focus order, ARIA roles and labels, color contrast ratios, form field labeling,
image alt text, motion and media controls, and screen reader compatibility signals. Produces
specific violation reports with WCAG criterion references, severity ratings, and concrete
remediation steps. The goal is actionable findings — not a checklist to tick, but a precise map
of what breaks for which users and the exact code change that fixes it.

## When to use
- Pre-launch accessibility check is requested before shipping a new page or feature.
- A bug report indicates screen reader users or keyboard-only users cannot complete a flow.
- Legal or compliance review requires WCAG 2.2 AA conformance documentation.
- A Lighthouse or axe-core run has flagged issues and you need a deeper human-readable analysis.
- A developer asks "is this form/modal/table accessible?"
- A design system component is being created and must be verified accessible before being adopted across the codebase.

## When not to use
- The artifact is a static image or PDF — those require a different audit process (PDF/UA, tagged PDF).
- The request is only about visual design aesthetics with no functional or accessibility component.
- The scope is purely backend or API with no rendered UI to audit.

## Procedure

1. **Gather the artifact.** Obtain HTML source, a live URL, or a component file. Confirm whether
   JavaScript renders the DOM dynamically (React/Vue/Svelte CSR) or statically (SSR/SSG) — CSR
   apps require runtime browser inspection rather than source reading alone, because the rendered
   DOM may differ substantially from the source.

2. **Check document structure (WCAG 1.3.1, 2.4.6).** Verify exactly one `<h1>` per page. Confirm
   heading levels do not skip — jumping from `<h1>` to `<h3>` leaves an implied empty `<h2>` that
   assistive technology reads aloud. Verify `<main>`, `<nav>`, `<header>`, `<footer>`, and `<aside>`
   landmarks are present where appropriate. Each `<nav>` should have a distinct `aria-label` when
   multiple navigation regions exist on the page. Flag `<div>` soup: interactive content wrapped
   in unsemantic divs with no landmark or role.

3. **Audit keyboard navigation (WCAG 2.1.1, 2.1.2).** Trace the expected Tab order through all
   interactive elements. Confirm focus never gets trapped outside an intentionally open modal.
   Inside an open modal, focus must be trapped — Tab and Shift+Tab cycle only within it. Verify
   all interactive elements — links, buttons, inputs, custom dropdowns, date pickers, sliders,
   tab panels — are reachable by Tab and activatable by Enter or Space, and that arrow keys work
   where the ARIA authoring practices require them (e.g., radio groups, listboxes, tree views).
   Flag any `tabindex > 0` — these create artificial tab sequences that almost always break.

4. **Inspect focus visibility (WCAG 2.4.7, 2.4.11 new in 2.2).** Confirm that `focus-visible` or
   an equivalent produces a visible, high-contrast outline on every interactive element. A CSS rule
   like `*:focus { outline: none }` with no replacement is an immediate WCAG 2.4.7 violation
   affecting every keyboard user. WCAG 2.4.11 (new in 2.2) requires that the focus indicator has
   a minimum area of the perimeter of the focused element times 2 CSS pixels and a contrast ratio
   of at least 3:1 against adjacent colors.

5. **Evaluate ARIA usage (WCAG 4.1.2).** Flag `role` attributes that misrepresent the element —
   `<div role="button">` without `tabindex="0"` and keyboard handlers makes an element that looks
   interactive but is not. Check that `aria-label` or `aria-labelledby` is present on icon-only
   buttons, dialogs (`role="dialog"`), and landmark regions that share a role with siblings.
   Flag redundant ARIA (`<button role="button">`). Verify `aria-expanded`, `aria-haspopup`, and
   `aria-controls` are set and toggled correctly on dropdown triggers. Verify `role="alert"` or
   `aria-live="polite"` is used for dynamic status messages (form errors, toast notifications)
   so screen readers announce them without requiring the user to find the message.

6. **Check color contrast (WCAG 1.4.3, 1.4.11).** Contrast requirements by text size:
   - Normal text (below 18pt regular / 14pt bold): minimum 4.5:1 (WCAG 1.4.3).
   - Large text (18pt+ regular / 14pt+ bold, approximately 24px / 18.67px): minimum 3:1.
   - UI component borders, icons, and graphical elements: minimum 3:1 against adjacent colors (WCAG 1.4.11).
   Always check: primary body text on background, placeholder text, disabled-state text (exempt
   from contrast if truly disabled and non-interactive), button labels, link text on background,
   and icon-only controls on background. Use hex values from the computed CSS, not from mockups —
   layered opacity and background blending change the effective color.

7. **Audit form fields (WCAG 1.3.1, 3.3.1, 3.3.2).** Every `<input>`, `<select>`, and `<textarea>`
   must have a programmatically associated `<label>` via `for`/`id` pairing, `aria-label`, or
   `aria-labelledby`. Placeholder text is not a label substitute — placeholder disappears on focus.
   Error messages must be programmatically linked to the field via `aria-describedby` so a screen
   reader announces both the label and the error when the user focuses the field. Required fields
   must be indicated by text or an icon accompanied by text (not color alone — WCAG 1.4.1).
   Group related fields (`<fieldset>` + `<legend>`) for radio buttons, checkboxes, and date parts.

8. **Review images and icons (WCAG 1.1.1).** Every `<img>` must have an `alt` attribute. Decorative
   images must have `alt=""` — an absent `alt` causes screen readers to read the file path or URL.
   SVGs used as standalone icons must have either an accessible name via `<title>` + `aria-labelledby`
   or `aria-label`, or be hidden with `aria-hidden="true"` when accompanied by visible text. `<img>`
   inside an `<a>` or `<button>` with no other text must have meaningful `alt` — the button label
   comes entirely from that attribute.

9. **Check motion and media (WCAG 2.2.2, 1.2.2, 1.2.3).** Any animation that runs for more than
   5 seconds or auto-starts must be pausable, stoppable, or hideable. Implement or verify
   `prefers-reduced-motion` media query support: `@media (prefers-reduced-motion: reduce)`.
   Carousels that auto-advance must have a pause control. Video content with dialogue must have
   synchronized captions. Audio content must have a transcript. Decorative auto-playing video with
   no audio is exempt from captions but must be pausable.

10. **Simulate screen reader reading order (WCAG 1.3.2).** Read the DOM in source order and confirm
    it makes sense without CSS. Visually repositioned content (CSS `order`, `grid`, `float`) that
    changes the visual order without changing DOM order creates a disconnect between reading order
    and tab order. Data tables must use `<th scope="col|row">` headers; layout tables must have
    `role="presentation"` or `aria-hidden="true"`.

## Concrete checks
- Exactly one `<h1>` per page; heading levels never skip.
- Semantic landmarks present: `<main>`, `<nav>` (labeled if multiple), `<header>`, `<footer>`.
- All interactive elements reachable and operable by keyboard alone: Tab, Shift+Tab, Enter, Space, and arrow keys where ARIA patterns require.
- No CSS rule removes focus outline without providing a visible, WCAG-2.4.11-compliant replacement.
- No `tabindex` value greater than 0 anywhere in the codebase.
- Every `<input>`, `<select>`, `<textarea>` has a programmatically associated `<label>` — not only a placeholder.
- Form error messages linked to their field via `aria-describedby`.
- Required fields indicated by text or non-color indicator, not color alone.
- Color contrast at least 4.5:1 for normal text; 3:1 for large text and UI components (checked against computed hex, not mockup values).
- All non-decorative images have descriptive `alt` text; decorative images have `alt=""` (not absent).
- Icon-only buttons have `aria-label` or visually hidden text (`<span class="sr-only">`).
- Open modal dialogs trap focus; closing restores focus to the element that triggered the modal.
- `aria-expanded` toggled correctly on accordion/dropdown triggers; `aria-controls` points to the controlled element.
- Auto-playing animations are pausable or respect `prefers-reduced-motion: reduce`.
- `aria-live` or `role="alert"` present on dynamic status messages so screen readers announce them.
- DOM source order makes sense when CSS layout is removed.

## Commands
```bash
# Run axe-core via the CLI against a local server
# (install once: npm install -g @axe-core/cli)
axe http://localhost:3000/page-to-audit --exit

# Run axe-core headlessly via Playwright (Node)
# In a test file:
# import { checkA11y } from 'axe-playwright';
# await checkA11y(page, undefined, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag22aa'] } });

# Lighthouse CLI: accessibility score and violations
# (install once: npm install -g lighthouse)
lighthouse http://localhost:3000 --only-categories=accessibility --output=json --quiet \
  | python3 -m json.tool | grep -A 3 '"score"'

# Check for tabindex > 0 in the codebase (instant red flag)
grep -rn 'tabindex="[1-9]' src/ components/ pages/ 2>/dev/null

# Find outline:none without a replacement (focus visibility risk)
grep -rn "outline:\s*none\|outline:\s*0" src/ styles/ 2>/dev/null | grep -v "focus-visible"

# Find inputs without a for/id label association
grep -n "<input" *.html src/**/*.{jsx,tsx,vue,svelte} 2>/dev/null | grep -v 'aria-label\|aria-labelledby'

# Find images missing alt attribute entirely (absent alt is not the same as alt="")
grep -rn '<img ' src/ 2>/dev/null | grep -v 'alt='

# Find <div onClick or <span onClick without role or tabindex
grep -rn 'onClick\|on:click' src/ 2>/dev/null | grep '<div\|<span' | grep -v 'role=\|tabindex'

# Contrast check: extract color pairs from CSS custom properties
grep -n '\-\-color\|\-\-bg\|\-\-text\|\-\-fg' src/styles/*.css 2>/dev/null | head -20

# Check for prefers-reduced-motion support
grep -rn "prefers-reduced-motion" src/ styles/ 2>/dev/null | wc -l
# 0 results = no support; add it if any animations exist

# Find aria-live or role=alert for dynamic messages
grep -rn 'aria-live\|role="alert"\|role="status"' src/ 2>/dev/null | head -10

# Validate heading structure in an HTML file
grep -noE '<h[1-6][^>]*>' index.html 2>/dev/null

# jest-axe: add to a React component test
# import { axe, toHaveNoViolations } from 'jest-axe';
# expect.extend(toHaveNoViolations);
# const { container } = render(<MyComponent />);
# expect(await axe(container)).toHaveNoViolations();
```

## Common issues & anti-patterns
- **`outline: none` in a global CSS reset** with no replacement — fails WCAG 2.4.7 for every interactive element on the site. The fix is always `*:focus-visible { outline: 2px solid <brand-color>; outline-offset: 2px; }`, not removing the reset.
- **Placeholder-as-label:** `<input placeholder="Email">` with no `<label>` — placeholder disappears on focus, leaving screen reader users and memory-impaired users without context. Fails WCAG 1.3.1 and 3.3.2.
- **`<div onClick>` button:** custom clickable `<div>` without `role="button"`, `tabindex="0"`, and keyboard event handlers (`keydown` for Enter and Space) — invisible to screen readers and unreachable by keyboard. Always prefer `<button>`.
- **Skipped heading:** page goes `<h1>` product name then `<h3>` section title — assistive technology reads an implied missing `<h2>`. Restructure heading levels; do not use headings for their visual size.
- **Low-contrast ghost buttons:** white outline button on a light gray background — a common pattern that fails 1.4.3 at ratios like 1.8:1. Check the button border against the page background (WCAG 1.4.11) as well as the button label against the button background.
- **Empty `<a>` tags:** `<a href="/dashboard"><img src="icon.svg"></a>` where the SVG has no `<title>` and the `<img>` has no `alt` — screen reader announces "link" with no destination or purpose.
- **`aria-label` on the wrong element:** labeling a `<div>` wrapper instead of the interactive `<button>` inside it — the label never reaches the control. ARIA attributes apply to the element they are on, not to child elements.
- **Modal that does not trap focus:** pressing Tab inside an open modal moves focus to the page behind it — keyboard users cannot interact with the modal and cannot escape it predictably.
- **Error message not linked to field:** displaying a validation error in a red `<span>` near the input with no `aria-describedby` link — a screen reader user may not discover the error unless they re-read the entire form.
- **Icon SVG without `aria-hidden`:** a decorative icon SVG inside a labeled `<button>` that has its own `<title>` — the screen reader reads both the `<title>` and the button text, doubling the announcement.

## Required output
Return a report with:
1. **Conformance summary:** estimated WCAG 2.2 AA pass rate and a count of violations by severity (critical / major / minor) and criterion level (A vs. AA).
2. **Critical violations** (keyboard trap, zero-contrast text, missing form labels, missing modal focus management): WCAG criterion code (e.g. 2.1.2), the element or CSS selector, the exact failing value, and the minimal code fix.
3. **Major violations** (contrast failures below threshold, missing alt text, broken ARIA state management, missing `aria-live` for dynamic content): same format.
4. **Minor violations** (redundant ARIA, suboptimal heading nesting, non-critical missing landmarks): grouped list with criterion codes.
5. **Recommended tooling:** axe-core CLI, `jest-axe` for CI, Lighthouse accessibility panel, or a browser screen reader test (NVDA + Firefox, VoiceOver + Safari) — whichever fits the project's stack and CI environment.
6. **Quick wins:** top 3 fixes that each take under 10 minutes and resolve the highest-severity violations.

## Safety
- Do not run automated scripts against third-party or production URLs without user confirmation.
- Do not modify ARIA attributes or HTML structure without testing the change in at least one screen reader (VoiceOver on macOS, NVDA on Windows) — incorrect ARIA is actively worse than no ARIA.
- Report violations with WCAG criterion numbers (e.g., WCAG 2.2 1.4.3) so the team can verify the finding and its threshold independently.
- When recommending a contrast fix, provide the new hex value and the computed ratio, not just "increase the contrast."
- Do not add `aria-label` to elements where the ARIA in HTML specification prohibits it — check the allowed roles for the element type first.

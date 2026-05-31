---
name: accessibility-audit
description: Use when you need to audit semantic HTML, keyboard navigation, focus, contrast, labels, and screen reader basics.
---

# Accessibility Audit

## Purpose
Audit a page or component against WCAG 2.2 Level AA. Covers semantic HTML structure, keyboard navigation and focus order, ARIA roles and labels, color contrast ratios, form field labeling, image alt text, and screen reader compatibility signals. Produces specific violation reports with WCAG criterion references and concrete remediation steps.

## When to use
- Pre-launch accessibility check is requested before shipping a new page or feature.
- A bug report indicates screen reader users or keyboard-only users cannot complete a flow.
- Legal or compliance review requires WCAG 2.2 AA conformance documentation.
- A Lighthouse or axe-core run has flagged issues and you need a deeper human-readable analysis.
- A developer asks "is this form/modal/table accessible?"

## When not to use
- The artifact is a static image or PDF — a different audit tool is needed.
- The request is only about visual design with no accessibility component.
- The scope is purely backend or API — no rendered UI to audit.

## Procedure

1. **Gather the artifact.** Obtain HTML source, a live URL, or a component file. If a URL is available, note whether JavaScript renders the DOM dynamically (React/Vue/Svelte SSR vs. CSR) — dynamic apps require runtime inspection, not just source reading.

2. **Check document structure.** Verify one `<h1>` per page. Confirm heading levels do not skip (no jumping from `<h1>` to `<h3>`). Verify `<main>`, `<nav>`, `<header>`, `<footer>`, and `<aside>` landmarks are present where appropriate. Flag `<div>` soup: blocks of interactive content with no landmark wrapping.

3. **Audit keyboard navigation.** Trace the expected Tab order through interactive elements. Confirm focus never gets trapped (except intentionally inside an open modal, where it should be trapped). Verify all interactive elements — links, buttons, inputs, custom dropdowns, date pickers — are reachable by Tab and activatable by Enter or Space. Flag any `tabindex > 0` values, which create artificial and usually broken tab sequences.

4. **Inspect focus visibility.** Confirm `focus-visible` or equivalent produces a visible outline on every interactive element. A CSS rule like `*:focus { outline: none }` with no replacement is an immediate WCAG 2.4.7 (Focus Visible) violation.

5. **Evaluate ARIA usage.** Flag `role` attributes that misrepresent the element (e.g., `<div role="button">` without `tabindex="0"` and keyboard handlers). Check that `aria-label` or `aria-labelledby` is present on icon-only buttons, dialogs, and landmark regions that need a label. Flag redundant ARIA (e.g., `<button role="button">`). Verify `aria-expanded`, `aria-haspopup`, `aria-controls` are set and toggled correctly on dropdown triggers.

6. **Check color contrast.** For normal text (< 18pt / 14pt bold), the required contrast ratio is 4.5:1 (WCAG 1.4.3). For large text (>= 18pt / 14pt bold), it is 3:1. For UI components and graphical elements, it is 3:1 (WCAG 1.4.11). Check primary text on background, placeholder text, disabled state text (exempt if truly disabled), and button labels. Use exact hex values from the source.

7. **Audit form fields.** Every `<input>`, `<select>`, and `<textarea>` must have an associated `<label>` (via `for`/`id` pairing or `aria-label`). Placeholder text is not a label substitute. Error messages must be programmatically associated with the field via `aria-describedby`. Required fields must be indicated by more than color alone.

8. **Review images and icons.** Every `<img>` must have `alt` text. Decorative images must have `alt=""`. Icon fonts or SVGs used as interactive elements must have accessible names. `<img>` inside a `<button>` with no other text must have meaningful `alt`.

9. **Check motion and media.** Any animation that runs for more than 5 seconds or auto-starts must be pausable (WCAG 2.2.2). Video content must have captions. Audio must have transcripts.

10. **Simulate screen reader reading order.** Read the DOM in source order and confirm it makes sense without CSS. Tables must have `<th>` with `scope` attributes. Lists must use `<ul>`/`<ol>` + `<li>`, not styled `<div>` elements.

## Checklist
- [ ] Exactly one `<h1>` per page; heading levels never skip
- [ ] Semantic landmarks: `<main>`, `<nav>`, `<header>`, `<footer>` used where appropriate
- [ ] All interactive elements reachable and operable by keyboard alone (Tab, Enter, Space, arrow keys)
- [ ] No CSS rule removes focus outline without providing a visible replacement (`focus-visible` at minimum)
- [ ] No `tabindex` values > 0 in the codebase
- [ ] Every `<input>`/`<select>`/`<textarea>` has a programmatically associated `<label>` (not just placeholder)
- [ ] Form error messages linked to their field via `aria-describedby`
- [ ] Color contrast >= 4.5:1 for normal text, >= 3:1 for large text and UI components
- [ ] No information conveyed by color alone (e.g., required fields marked red without additional indicator)
- [ ] All non-decorative images have descriptive `alt` text; decorative images have `alt=""`
- [ ] Icon-only buttons have `aria-label` or visually hidden text
- [ ] Modal dialogs trap focus when open and restore focus to trigger on close
- [ ] `aria-expanded` toggled correctly on accordion/dropdown triggers
- [ ] Auto-playing animations are pausable or respect `prefers-reduced-motion`

## Common issues & anti-patterns
- **`outline: none` in a global reset** with no replacement — fails WCAG 2.4.7 for every interactive element on the site.
- **Placeholder-as-label:** `<input placeholder="Email">` with no `<label>` — placeholder disappears on focus, leaving users without context.
- **`<div onClick>` button:** custom clickable `<div>` without `role="button"`, `tabindex="0"`, or keyboard event handler — invisible to screen readers and keyboard users.
- **Skipped heading:** page goes `<h1>` product name, then immediately `<h3>` section title — assistive technology reads an implied empty `<h2>`.
- **Low-contrast ghost buttons:** white border + white text on a light gray background — common offender at 1.8:1 contrast.
- **Empty `<a>` tags:** `<a href="/dashboard"><img src="icon.svg"></a>` where the image has no `alt` — screen reader announces "link" with no label.
- **ARIA role mismatch:** `<ul role="navigation">` — `<nav>` exists for this; the ARIA role on a list creates a conflict.

## Required output
Return a report with:
1. **Conformance summary:** estimated WCAG 2.2 AA pass rate and count of violations by level (A vs AA).
2. **Critical violations** (keyboard trap, missing labels, zero-contrast text): WCAG criterion, element/selector, exact fix.
3. **Major violations** (contrast failures, missing alt, broken ARIA): same format.
4. **Minor violations** (redundant ARIA, suboptimal heading nesting): grouped list.
5. **Recommended tooling:** axe-core browser extension, Lighthouse accessibility panel, or `jest-axe` for CI — whichever fits the project.
6. **Quick wins:** top 3 fixes that each take under 10 minutes and resolve the highest-severity issues.

## Safety
- Do not run automated scripts against third-party URLs without user confirmation.
- Do not modify ARIA attributes or HTML structure without testing the change in a browser — incorrect ARIA is worse than no ARIA.
- Flag violations with WCAG criterion numbers so the team can verify independently.

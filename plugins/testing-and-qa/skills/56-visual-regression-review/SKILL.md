---
name: visual-regression-review
description: Use when you need to review screenshots, layout diffs, visual states, responsive snapshots, and rendering drift.
---

# Visual Regression Review

## Purpose

Evaluate the visual regression testing setup: screenshot baseline management, diff threshold configuration, viewport coverage, flaky test identification, tool configuration (Playwright, Percy, Chromatic, Loki, reg-suit), and CI integration. Identify gaps between what is visually tested and what users actually see, and flag rendering drift that has been silently accepted.

## When to use

- A UI change is being reviewed and visual regressions must be confirmed absent before merge.
- The visual regression suite is flaky (intermittently fails with no code change) and needs diagnosis.
- Baselines were bulk-updated without human review, and you need to audit what changed.
- A new viewport or theme (dark mode, high contrast) was introduced and needs coverage.
- Percy/Chromatic diff count is high and you need to triage which diffs are intentional vs. regressions.

## When not to use

- The project has no UI layer (API-only, CLI, data pipeline).
- Visual regression tooling is not set up at all and the task is to implement it from scratch — use a coding task.
- The failing visual test is a known intentional design change already reviewed by a designer.

## Procedure

1. **Identify the visual regression tool.** Look for `percy.yml`, `.percy/`, `chromatic.json`, `playwright.config.ts` with screenshot assertions, `loki.js`, `reg-suit.json`, or `backstop.json`. If multiple tools are present, note overlap.

2. **Audit baseline storage.** Confirm baselines are stored in a way that enables human review:
 - Percy/Chromatic: cloud-hosted with PR-gated approval workflow.
 - Local snapshot tools (Playwright `toMatchSnapshot`): baseline images committed to git, stored in `__snapshots__/` or `screenshots/`.
 - Flag baselines that are auto-committed by CI bots without human approval.

3. **Check viewport coverage.** List which viewports are tested. Minimum for a responsive web app: mobile (375px), tablet (768px), desktop (1280px). Flag if only desktop is covered. Confirm viewport dimensions match the actual breakpoints in the CSS/design system.

4. **Review component vs. page coverage.** Distinguish between:
 - **Component-level snapshots** (Storybook + Chromatic): individual components in isolation.
 - **Page-level snapshots** (Playwright + Percy): full pages with real data and layout.
 Both are needed; component tests miss layout interactions; page tests miss component state variants.

5. **Identify state coverage gaps.** For each snapshotted component or page, check which states are covered:
 - Loading skeleton / empty state / error state.
 - Dark mode / high-contrast mode.
 - Long content / truncated content / RTL text.
 - Focused / hover / disabled states for interactive elements.
 Flag states present in the component but absent from snapshots.

6. **Diagnose flaky tests.** Look for known sources of flakiness:
 - Animations not disabled in test environment (`prefers-reduced-motion: reduce` not applied).
 - Dynamic content (timestamps, random avatars, ad slots) not mocked or stabilized.
 - Font loading race conditions (FOUT causing layout shift between screenshot timing and render).
 - Network calls completing at different speeds affecting content.

7. **Review diff threshold configuration.** A threshold of 0% is too strict (fails on anti-aliasing); a threshold of 5% is too loose (misses real regressions). Confirm the threshold is set per-component based on its volatility, not a single global value.

8. **Audit CI integration.** Confirm visual tests run on every PR (not just scheduled). Confirm the job fails the PR when unapproved diffs exist. Check that the approval step requires a human action, not auto-approval by the CI bot.

9. **Check for stale or orphaned baselines.** Baselines for deleted components or removed pages waste storage and can confuse reviewers. Look for snapshot files that no longer have a corresponding source component.

10. **Verify test data stability.** Snapshots that depend on real database records or live API data will differ between runs. Confirm test fixtures, mocked API responses, or seeded test databases produce deterministic content.

## Checklist

- [ ] Visual regression tool identified and configured.
- [ ] Baselines require human approval before being accepted (no auto-approval bots).
- [ ] Viewports cover mobile (375px), tablet (768px), and desktop (1280px) at minimum.
- [ ] Both component-level and page-level snapshots exist.
- [ ] Key component states (empty, error, loading, dark mode) are covered.
- [ ] Animations are disabled in test environment to prevent flakiness.
- [ ] Dynamic content (timestamps, random data) is mocked or replaced with static fixtures.
- [ ] Diff threshold is explicitly set; not relying on tool default.
- [ ] Visual tests run on every PR in CI.
- [ ] Stale baselines for deleted components are removed.
- [ ] Font loading is deterministic (web fonts preloaded or replaced with system fonts in tests).

## Common issues & anti-patterns

- **Bulk baseline update commits**: `git log` shows a commit titled "update snapshots" touching 50+ files — nobody reviewed what actually changed.
- **Desktop-only snapshots**: mobile layout bugs are invisible to the test suite.
- **Timestamp in screenshot**: `Last updated: 2026-05-31 12:34:56` renders differently every run — permanent flakiness.
- **Animation frames**: a spinner or transition is captured mid-frame on one run and at a different frame on the next.
- **Coverage theater**: Storybook covers the component in its default state only; the buggy "error" state is never snapshotted.
- **No approval gate**: Percy diffs are informational only; developers merge without looking at the visual diff.
- **Threshold too loose**: a button shifted 8px to the right does not fail because threshold is set to 10%.
- **Font flash**: the browser renders a fallback font for 50ms; screenshot timing varies and sometimes captures the fallback.

## Required output

```
## Visual Regression Review

### Tool and configuration
- Tool: Percy / Chromatic / Playwright snapshots / other
- Baseline approval: human-gated / auto-approved / unclear
- CI: runs on every PR: yes/no

### Viewport coverage
| Viewport | Width | Status |
|----------|-------|--------|
| Mobile | 375px | covered / missing |
| Tablet | 768px | ... |
| Desktop | 1280px | ... |

### Coverage gaps
- Pages with no visual test: list
- Component states not covered: list (component, missing state)

### Flakiness findings
- Animation disabled: yes/no
- Dynamic content mocked: yes/no
- Issues found: list

### Stale baselines
- Orphaned snapshot files: list

### Diff review status (if reviewing a specific PR)
- Total diffs: N
- Intentional (design change): N
- Unintentional regressions: N — list affected components/pages

### Recommended actions
1. ...
```

## Safety

- Do not modify baseline images or snapshot files.
- Do not trigger Percy/Chromatic builds or approve diffs — those actions require explicit user instruction.
- Do not run Playwright tests unless the user asks; this is a configuration and gap review, not test execution.

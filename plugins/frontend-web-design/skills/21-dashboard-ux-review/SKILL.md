---
name: dashboard-ux-review
description: Use when you need to review dashboards, admin tools, density, scanning, filtering, and operational workflows.
---

# Dashboard UX Review

## Purpose

Evaluate the usability of dashboards, admin panels, and operational tools: information density, scannability, table and chart readability, filter and search mechanics, empty/loading/error states, and workflow efficiency for power users. Every finding is tied to a specific UI pattern and the primary user job — not generic design principles — and quantified where possible through column counts, click counts, and a missing-state inventory.

## When to use

- A new dashboard page or admin screen is ready for UX review before release.
- Users report confusion finding information or completing operational tasks.
- A data table has grown beyond five columns and needs a readability assessment.
- The dashboard has charts but no clear indication of what action they should drive.
- Empty, loading, and error states have not been explicitly designed.

## When not to use

- The request is about a public-facing marketing or landing page — use `landing-page-conversion-review`.
- The review is exclusively about accessibility — use `accessibility-audit`.
- The dashboard is not built yet and only wireframes exist — this skill reviews implemented UI, not concepts.
- The request is about final pixel polish of an otherwise-sound layout — use `visual-polish-pass`.

## Procedure

1. **Identify the primary user workflow.** Before evaluating anything visual, confirm who the user is, what decision they make most frequently, and what data they need to make it. Every critique references this north star — a layout that looks cluttered to an observer may be appropriately dense for a trader checking positions.
2. **Audit the information hierarchy.** Identify the top three metrics above the fold and confirm they match the primary decision. A bare "Total users: 1,247,839" scores lower than the same number with a trend arrow, sparkline, or vs-target indicator — context is what drives action.
3. **Evaluate table usability.** Per table, count columns (more than eight on desktop or four on mobile needs justification); confirm at least the primary identifier and primary numeric column are sortable; check long cells truncate with a tooltip or expand inline; confirm row actions (Edit, Delete, View) are discoverable — icon-only actions without labels or tooltips are a problem.
4. **Review filters and search.** Filters must apply immediately on change OR via a visible Apply button — never ambiguously both. Active filters must be visually indicated and individually removable. A search input that silently searches all columns confuses users; date pickers should show the chosen range as a readable label after selection.
5. **Assess chart communication.** Every chart needs a title stating what is measured, axis labels, a unit indicator (%, $, users), and a clear "so what" — a color threshold (red/green zone) or an annotation. A chart that requires hovering a tooltip to read any value is not dashboard-ready.
6. **Check empty states.** Every list, table, and chart needs an explicit empty state: an icon or illustration, a brief reason ("No results match your filter"), and a suggested action ("Clear filters" or "Add your first project"). A blank box or a spinner that never resolves is unacceptable.
7. **Check loading and error states.** Tables and charts must show skeleton loaders or spinners while fetching. Network errors must show a user-readable message with a retry action — never an unhandled exception or blank space.
8. **Evaluate workflow efficiency.** Count clicks to complete the primary task (for example approving a pending item). More than three clicks for a repetitive operational action is a friction target. Bulk actions (select rows, apply once) should exist when the action is frequently repeated.
9. **Review navigation and wayfinding.** The user should always know where they are in the hierarchy, what view they are on, and how to return to the overview. Breadcrumbs, active-nav highlighting, and page titles must be consistent.

## Concrete checks

Hierarchy and density:
- The top three above-the-fold metrics align with the primary decision.
- Metrics include context (trend, vs-target, or threshold), not raw numbers alone.
- Density matches the user: dense is fine for power users, sparse for occasional ones.

Tables:
- No more than eight columns on desktop; columns beyond five are justified by the workflow.
- The primary identifier and primary numeric column are sortable.
- Long text cells truncate with a tooltip or expand inline.
- Row actions have visible labels or persistent tooltips, not mystery icons.

Filters, search, charts:
- Filters apply via one unambiguous mechanism; active filters are visible and individually clearable.
- Search states what it searches; date pickers show the selected range as a label.
- Every chart has a title, axis labels, a unit, and one "so what" indicator.

States and efficiency:
- Every list, table, and chart has explicit empty, loading, and error states.
- Loading uses skeletons or spinners, never blank space.
- Error states show a user-readable message plus a retry action.
- Bulk actions exist where the same action repeats across rows.
- The primary repetitive task completes in three clicks or fewer.
- Page title and active nav item indicate the current location.
- Drill-down views keep a breadcrumb back and preserve the prior scroll and filters.

## Commands

```bash
# --- tables ---
# locate table components and roughly count headers/columns
rg -n '<th\b|columnHelper|accessorKey|<TableHead' src | head -40

# detect icon-only row actions (icon button with no text/aria-label)
rg -n '<button[^>]*>\s*<(svg|Icon)' src | head

# --- data fetching states ---
# find data fetches — then check each for loading/error handling nearby
rg -n 'useQuery|useSWR|fetch\(|axios\.' src | head -40

# empty-state handling present (or absent)?
rg -n 'No results|isEmpty|length === 0|EmptyState|empty' src | head

# skeleton / spinner loading indicators
rg -n 'Skeleton|Spinner|isLoading|isFetching' src | head

# error + retry affordances
rg -n 'isError|onRetry|retry|Try again' src | head

# --- filters ---
# how filters apply (onChange vs explicit Apply)
rg -n 'onChange=|type="submit"|Apply|applyFilters' src | head -40

# --- charts ---
# charts that may be missing axis/unit labels
rg -n '<(LineChart|BarChart|AreaChart|PieChart)' src | head

# axis / unit labels actually declared on charts?
rg -n 'XAxis|YAxis|label=|unit=|tickFormatter' src | head

# --- bulk actions ---
# multi-select / bulk-action affordances on tables
rg -n 'selectedRows|onSelectAll|bulk|checkbox' src | head

# --- wayfinding ---
# breadcrumbs and active-nav highlighting
rg -n 'Breadcrumb|aria-current|isActive|activeClassName' src | head

# --- workflow click count ---
# trace the primary action handler to count steps to completion
rg -n 'onApprove|onConfirm|handleSubmit|mutate\(' src | head

# --- date range labeling ---
# date pickers — confirm the selected range renders as a label
rg -n 'DateRangePicker|DatePicker|from.*to|selectedRange' src | head
```

## Common issues & anti-patterns

- **Vanity metric dominance:** large KPI cards showing all-time totals with no trend — impressive, drives no decision.
- **The twelve-column table:** every database column shown because "users might want it"; nobody can read it.
- **Ambiguous filter application:** dropdowns that apply on select on one screen and need an Apply button on another — users never know when a filter took effect.
- **Chart without a unit:** a Y-axis of `0, 200, 400, 600` — dollars, users, or requests?
- **Silent empty state:** a component that renders nothing when its data is empty — users assume it is loading forever.
- **Icon-only row actions:** three unlabeled icon buttons per row — new users cannot discover what they do.
- **Orphan drill-down:** clicking a row opens a detail view with no breadcrumb back, so users hit browser-back and lose scroll position and filters.
- **Infinite spinner:** a fetch that fails silently leaves a spinner forever, with no error message and no retry.
- **Filter-and-forget:** applying a filter scrolls or re-renders the page so the active filter chips drop out of view, and the user re-applies the same filter minutes later.
- **No bulk action on a queue:** an approvals table where each row must be approved individually, turning a 50-item queue into 50 separate three-click operations.
- **Tooltip-only labels:** axis values, status colors, and KPIs that only reveal meaning on hover — unusable on touch devices and invisible at a glance.

## Required output

Return a structured report with:
1. **User workflow alignment** (one paragraph): does the layout serve the stated primary job?
2. **Critical findings** (up to three): the specific UI element, the exact problem, and the fix.
3. **Major findings** (up to five): same format.
4. **Quick wins** (up to five bullets): sub-30-minute fixes with the highest user impact.
5. **Missing states inventory:** every identified missing empty, loading, or error state.
6. **Efficiency score:** the estimated click count for the primary workflow and a target reduction.

## Safety

- Do not alter database queries or API calls — this review focuses on the UI layer only.
- Do not redesign navigation structure without first confirming the information architecture with the team.
- Mark any opinion that depends on user-behavior data the reviewer lacks as a hypothesis, not a finding.
- Static and visual review only — propose changes; do not refactor data-fetching as a side effect.
- Redact any secret-like values surfaced while reading config or API code.

## Completion criteria

Done means the primary user workflow is named and used as the yardstick; tables, filters, charts, and navigation were each assessed against concrete criteria; every missing empty/loading/error state is inventoried; the primary task's click count is measured with a reduction target; and findings are severity-ranked with element-level fixes.

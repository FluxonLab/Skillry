---
name: dashboard-ux-review
description: Use when you need to review dashboards, admin tools, density, scanning, filtering, and operational workflows.
---

# Dashboard UX Review

## Purpose
Evaluate the usability of dashboards, admin panels, and operational tools: information density, scannability, table and chart readability, filter and search mechanics, empty and loading states, and workflow efficiency for power users. Produces prioritized findings tied to specific UI patterns, not general design principles.

## When to use
- A new dashboard page or admin screen is ready for UX review before release.
- Users report confusion finding information or completing operational tasks.
- A data table has grown beyond 5 columns and needs readability assessment.
- The dashboard has charts but no clear indication of what action they should drive.
- Empty, loading, and error states have not been explicitly designed.

## When not to use
- The request is about a public-facing marketing page or landing page (use `landing-page-conversion-review`).
- The review is exclusively about accessibility (use `accessibility-audit`).
- The dashboard has not been built yet and only wireframes exist — this skill reviews implemented UI, not concepts.

## Procedure

1. **Identify the primary user workflow.** Before evaluating anything visual, confirm: who is the user, what decision do they make most frequently, and what data do they need to make it? Every critique must reference this north star. A dashboard that looks cluttered to a casual observer may be appropriately dense for a stock trader checking positions.

2. **Audit the information hierarchy.** Identify the top 3 metrics or data points visible above the fold. Confirm they match the primary decision the user makes. Metrics that are decorative (e.g., "Total users: 1,247,839" with no trend or threshold) score lower than metrics with context (e.g., trend arrow, sparkline, or vs. target indicator).

3. **Evaluate table usability.** For each data table: count the columns — tables with > 8 columns on desktop and > 4 on mobile need justification. Check whether columns are sortable (at minimum the primary identifier and the primary numeric column should be). Check whether long text cells truncate with a tooltip or expand inline. Check whether row actions (Edit, Delete, View) are discoverable — icon-only actions without tooltip labels are a problem.

4. **Review filters and search.** Confirm that filter controls apply immediately (on change) or have a visible Apply button — never ambiguously both. Check that active filters are visually indicated and individually removable. A search input that searches all columns without telling the user what it searches is a confusion source. Date range pickers should show the selected range as a readable label after selection.

5. **Assess chart communication.** Every chart needs: a title that states what is being measured, axis labels, a unit indicator (%, $, users), and a clear "so what" — either via color threshold (red/green zones) or an annotation pointing to a notable event. A chart that requires reading a tooltip to understand any value is not dashboard-ready.

6. **Check empty states.** Every list, table, and chart must have an explicit empty state: an illustration or icon, a brief explanation of why it's empty ("No results match your filter"), and a suggested action ("Clear filters" or "Add your first project"). A blank box or spinner that never resolves is unacceptable.

7. **Check loading and error states.** Tables and charts must show skeleton loaders or loading indicators while fetching. Network errors must display a user-readable message with a retry action — never an unhandled exception or blank space.

8. **Evaluate workflow efficiency.** Count the clicks required to complete the primary task (e.g., approve a pending item). More than 3 clicks for a repetitive operational action is a friction target. Bulk actions (select multiple rows and perform one action) should be present when the task is frequently repeated.

9. **Review navigation and wayfinding.** The user should always know: where they are in the dashboard hierarchy, what page/view they are on, and how to return to the overview. Breadcrumbs, active nav item highlighting, and page titles must be consistent.

## Checklist
- [ ] Top 3 above-the-fold metrics align with the user's primary decision-making need
- [ ] Metrics include context (trend, vs. target, threshold indicator) — not raw numbers alone
- [ ] Tables have <= 8 columns on desktop; columns beyond 5 are justified by workflow requirement
- [ ] Primary identifier column and primary numeric column are sortable
- [ ] Long text cells truncate with tooltip or expand-inline affordance
- [ ] Row actions have visible labels or persistent tooltips (no icon-only mystery actions)
- [ ] Active filters are visually distinct and individually clearable
- [ ] Every chart has a title, axis labels, unit, and at least one "so what" indicator
- [ ] Every empty list/table/chart has an explicit empty state with explanation and action
- [ ] Loading states use skeleton loaders or spinners; never blank space
- [ ] Error states show user-readable message with retry action
- [ ] Bulk actions available for tables where the same action is performed on multiple rows
- [ ] Page title and active nav item clearly indicate current location in the app

## Common issues & anti-patterns
- **Vanity metric dominance:** large KPI cards showing all-time totals with no trend — looks impressive, drives no decision.
- **The 12-column table:** every column the database has is shown because "the users might want it" — nobody can read it.
- **Ambiguous filter application:** filter dropdowns that apply on select on some screens and require an Apply button on others — users never know when their filter took effect.
- **Chart without a unit:** a line chart with Y-axis values `0, 200, 400, 600` — is that dollars, users, or requests?
- **Silent empty state:** a component that renders nothing when its data is empty — users assume it is loading forever.
- **Icon-only row actions:** three icon buttons at the end of each table row with no labels or tooltips — new users cannot discover what they do.
- **Orphan drill-down:** clicking a row opens a detail view with no breadcrumb back — users hit the browser back button and lose their scroll position and filters.

## Required output
Return a structured report with:
1. **User workflow alignment** (1 paragraph): does the layout serve the stated primary user job?
2. **Critical findings** (up to 3): specific UI element, exact problem, and fix.
3. **Major findings** (up to 5): same format.
4. **Quick wins** (up to 5 bullets): small fixes (< 30 min each) with highest user impact.
5. **Missing states inventory**: list every identified missing empty, loading, or error state.
6. **Efficiency score**: estimated click count for the primary workflow and target reduction.

## Safety
- Do not alter database queries or API calls — this review focuses on the UI layer only.
- Do not redesign navigation structure without first confirming the information architecture with the team.
- Flag opinions that depend on knowing user behavior data the reviewer does not have — mark them as hypotheses.

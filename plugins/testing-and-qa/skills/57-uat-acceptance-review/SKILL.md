---
name: uat-acceptance-review
description: Use when you need to translate product goals into acceptance checks, demo paths, and user validation criteria.
---

# UAT Acceptance Review

## Purpose

Convert a feature's product requirements, tickets, or acceptance criteria into concrete User Acceptance Testing (UAT) scenarios using Given/When/Then format. Identify edge cases and negative paths the product team has not specified. Produce a structured test plan that a non-technical stakeholder can execute to confirm the feature meets its goals, plus flag gaps where the implementation may diverge from the stated acceptance criteria.

## When to use

- A feature is complete and ready for stakeholder demo or sign-off, but no formal UAT plan exists.
- Product acceptance criteria are written as bullet points or user stories without testable steps.
- A QA team needs structured scenarios to validate before a release gate.
- A feature requires data-entry or workflow validation that automated tests cannot easily cover (multi-step wizard, PDF export, email delivery).
- A stakeholder reported "it doesn't work as expected" with no further detail — this skill builds scenarios to reproduce the exact expectation gap.

## When not to use

- The task is to write automated end-to-end tests — use an e2e coding task.
- The feature has no user-facing interface (background job, internal API, data migration).
- Acceptance criteria are already in Given/When/Then format and have been reviewed.

## Procedure

1. **Collect requirements.** Read the ticket, user story, PRD section, or feature spec. Extract the stated acceptance criteria exactly as written.

2. **Identify the user roles involved.** For each role that interacts with the feature (admin, end user, guest, API consumer), define a separate scenario set. UAT that only covers the happy path for one role misses permission and personalization bugs.

3. **Structure Given/When/Then scenarios for the happy path.** For each acceptance criterion:
 - **Given**: the precondition (logged in as role X, with data Y already existing).
 - **When**: the exact action taken (click button Z, submit form with fields A=1, B=2).
 - **Then**: the exact observable outcome (page shows message M, email received, record in DB, redirect to URL U).

4. **Add negative and edge-case scenarios.** For each happy-path scenario, add at least:
 - **Empty/missing input**: submitting the form with a required field blank.
 - **Invalid input**: submitting with an out-of-range value, wrong format, or already-existing unique field.
 - **Permission boundary**: attempting the action as a user who should not have access.
 - **Concurrent action**: two users acting on the same resource simultaneously (if applicable).
 - **Recovery path**: what happens after an error — can the user retry without losing progress?

5. **Identify unstated but implied criteria.** Product tickets often omit:
 - What happens to dependent records when a parent is deleted?
 - What confirmation or undo mechanism exists for destructive actions?
 - What notification (email, in-app, webhook) should be triggered?
 - What audit log entry should be created?
 Flag each implied criterion as "derived — needs product confirmation."

6. **Define data setup requirements.** For each scenario, specify exactly what data must exist before the scenario begins: specific user accounts, specific records with specific field values. Vague preconditions ("some records exist") are not executable.

7. **Define observable outcomes precisely.** Avoid vague thens like "the page updates." Specify: which element changes, to what value, within how many seconds, and whether the change is persistent after a page refresh.

8. **Map scenarios to implementation.** For each scenario, identify which code path or feature flag is exercised. Flag scenarios where the implementation path is unclear — the developer may need to confirm how the feature handles that case.

9. **Define the pass/fail gate.** State how many scenarios must pass for UAT to be considered complete. Identify which scenarios are blocking (must pass for release) vs. informational (nice to verify but not a release gate).

## Checklist

- [ ] All stated acceptance criteria have at least one corresponding Given/When/Then scenario.
- [ ] Each user role involved has dedicated scenarios.
- [ ] At least one negative path (error, permission denied, invalid input) per happy-path scenario.
- [ ] Implied criteria (notifications, audit logs, dependent records) are captured and flagged for confirmation.
- [ ] Data setup for each scenario is specified precisely.
- [ ] Observable outcomes specify exact UI element, value, and persistence.
- [ ] Blocking vs. non-blocking scenarios are labeled.
- [ ] Concurrent-use scenarios are included for shared resources.

## Common issues & anti-patterns

- **Acceptance criteria written as design specs**: "the button is blue and centered" is a design spec, not a functional acceptance criterion — does clicking it do the right thing?
- **Single-user assumption**: all scenarios test one user; multi-tenant apps need cross-tenant scenarios.
- **Happy path only**: stakeholders confirm the flow works when everything is correct; the first real user finds the edge case immediately.
- **Vague preconditions**: "user has some items" is not executable; "user has exactly 3 items, one of which is in 'draft' status" is.
- **Implicit data dependencies**: scenario B assumes the record created in scenario A still exists — if run independently, B fails.
- **No rollback scenario**: for destructive actions (delete, publish, send email), no UAT verifies the outcome of accidental use or the undo mechanism.
- **Missing async outcome testing**: the form submits successfully but the email is never verified; the webhook fires but the downstream system's state is not checked.

## Required output

```
## UAT Acceptance Plan: [Feature Name]

### Acceptance criteria (sourced from ticket)
1. Original text of criterion 1.
2. ...

### Scenarios

#### Scenario 1: [Name — role — happy path]
**Given** ...
**When** ...
**Then** ...
**Data setup**: ...
**Gate**: Blocking / Non-blocking

#### Scenario 2: [Name — role — negative path]
...

### Derived criteria (implied, needs product confirmation)
- Criterion: [description]. Question: [what needs to be confirmed?]

### Out of scope
- [Anything explicitly excluded from this UAT round and why.]

### Pass/fail gate
UAT is complete when: all X blocking scenarios pass. Non-blocking scenarios may be deferred to [milestone].
```

## Safety

- Do not execute UAT scenarios against production data or production environments.
- Do not create, modify, or delete records in any environment; produce the plan for humans to execute.
- Do not invent acceptance criteria; flag derived criteria as needing confirmation, not as confirmed requirements.

---
name: uat-acceptance-review
description: Use when you need to translate product goals into acceptance checks, demo paths, and user validation criteria for a feature ready for stakeholder sign-off.
---

# UAT Acceptance Review

## Purpose

Convert a feature's product requirements, tickets, or acceptance criteria into concrete User Acceptance Testing (UAT) scenarios in Given/When/Then format. Identify edge cases and negative paths the product team has not specified. Produce a structured test plan that a non-technical stakeholder can execute to confirm the feature meets its goals — and separately flag gaps where the implementation may diverge from the stated acceptance criteria or where implied behavior has not been confirmed. This skill does not write automated tests; it produces the human-executable plan that precedes or supplements them.

## When to use

- A feature is complete and ready for stakeholder demo or sign-off, but no formal UAT plan exists.
- Product acceptance criteria are written as bullet points or user stories without testable steps.
- A QA team needs structured scenarios to validate before a release gate.
- A feature requires data-entry, workflow, or async behavior that automated tests cannot easily cover: multi-step wizard, PDF export, email delivery confirmation, third-party webhook trigger.
- A stakeholder reports "it doesn't work as expected" with no further detail — this skill builds scenarios to reproduce the exact expectation gap.
- Multiple user roles interact with the same feature and their permission boundaries have not been tested.

## When not to use

- The task is to write automated end-to-end tests — use a coding task targeting `playwright-e2e-audit` instead.
- The feature has no user-facing interface (background job, internal API, data migration with no UI).
- Acceptance criteria are already in Given/When/Then format, have been reviewed by the team, and a UAT plan exists.
- You need to verify automated tests pass — use `smoke-test-and-repair` for that.

## Procedure

1. **Collect requirements precisely.** Read the ticket, user story, PRD section, or feature spec and extract the stated acceptance criteria word-for-word. Do not paraphrase yet — the exact wording often contains important nuance that rewording loses. List each criterion numbered.

2. **Identify every user role involved.** For each role that can interact with the feature (admin, standard user, guest, read-only viewer, API consumer, support agent), define a dedicated scenario set. A UAT plan that covers only the happy path for a single role misses permission bugs, personalization differences, and tenant isolation issues. If the role matrix is not documented, derive it from the auth middleware or permission definitions.

3. **Structure Given/When/Then scenarios for each happy path.** For each acceptance criterion write one or more scenarios:
   - **Given**: the exact precondition — role, logged-in state, and specific data that must exist (not "some items exist" but "three orders exist: two in 'pending' status and one in 'shipped' status, all owned by this user").
   - **When**: the precise action taken — which button, which form fields, which values (exact strings, not "fill in the details").
   - **Then**: the exact observable outcome — which element changes, to what text or value, whether the change persists after a page refresh, and whether a background record or notification was created.

4. **Add negative and edge-case scenarios.** For each happy-path scenario, add at minimum:
   - **Empty or missing required input**: submit the form with a required field blank and confirm the field-level error message appears.
   - **Invalid input format**: enter an out-of-range numeric value, a past date where a future date is required, or an already-used unique value (email, username).
   - **Permission boundary**: attempt the action as a role that should not have access and confirm the correct denial response (error message, redirect, or hidden control).
   - **Concurrent action**: two users act on the same resource simultaneously — the second action should produce a deterministic, documented outcome (conflict error, last-write-wins, or queued).
   - **Recovery path after error**: after submitting an invalid form, can the user correct and resubmit without losing other field values?

5. **Identify unstated but implied criteria.** Product tickets routinely omit:
   - What happens to dependent child records when a parent is deleted (cascade, orphan, block deletion)?
   - What confirmation dialog or undo mechanism exists for destructive actions (delete, bulk archive, send email)?
   - What notification is triggered (email, in-app alert, webhook)?
   - What audit log entry is created and what fields it must contain?
   - What the empty-state looks like on first use before any data exists.
   Flag each implied criterion as "derived — needs product confirmation" so stakeholders know it has not been signed off yet.

6. **Define data setup requirements precisely.** For each scenario, specify exactly what data must exist before the scenario begins: which user accounts (role, verified status), which records (specific field values that matter to the scenario), which feature flags are enabled. "Some records exist" is not executable; "user A has three orders: IDs 101 (pending), 102 (shipped), 103 (cancelled)" is.

7. **Define observable outcomes with no ambiguity.** Avoid vague "Thens" like "the page updates." Specify:
   - Which DOM element or UI region changes.
   - To what exact text, count, or value.
   - Within what time frame (especially for async operations: email delivery, background job completion).
   - Whether the change is persistent after a hard page refresh (confirming it was saved, not just rendered in-memory).
   - Whether an email, webhook, or in-app notification appears — and within what SLA.

8. **Map scenarios to implementation paths.** For each scenario, identify which feature flag, code path, or service integration is exercised. Flag scenarios where the implementation path is unclear — a developer may need to confirm how the feature handles that case before UAT can proceed.

9. **Define the pass/fail gate.** State explicitly how many scenarios must pass for UAT to be considered complete. Label each scenario as **Blocking** (must pass before release) or **Non-blocking** (informational; can be deferred). List the specific scenarios that are release gates.

## Concrete checks

- Every stated acceptance criterion has at least one corresponding Given/When/Then scenario that exercises it directly.
- Each user role that interacts with the feature has at least one dedicated scenario.
- Every happy-path scenario has at least one corresponding negative path (empty input, invalid input, or permission boundary).
- Implied criteria (notifications, audit logs, dependent-record behavior, empty-state) are listed and flagged for stakeholder confirmation.
- Every scenario's data setup specifies exact record counts, statuses, and field values — no vague preconditions.
- Observable "Thens" specify the exact element, value, and persistence behavior.
- Async outcomes (email, webhook, background job result) name the expected delivery SLA.
- Blocking versus non-blocking gate status is labeled on every scenario.
- Concurrent-use scenarios are included for any feature that involves shared or contended resources.
- Scenarios that depend on external services (email provider, payment gateway) note whether the UAT environment is configured to trigger real or simulated calls.

## Scenario template

```
#### Scenario N: [Short name — role — path type]
**Precondition (Given)**
[Role]: [logged in / anonymous / specific permissions]
[Data]: [exact records, field values, feature flag states that must exist]

**Action (When)**
[Exact steps: navigate to X, click Y, fill field Z with value "abc", submit]

**Expected outcome (Then)**
[Element/region]: [exact text or value]
[Persistence]: [does it survive page refresh?]
[Side effects]: [email sent to X within Y seconds / audit log entry created with fields A, B, C]

**Data setup**: [SQL seed, factory command, or manual setup steps]
**Gate**: Blocking / Non-blocking
**Derived criteria**: [any implied behavior not confirmed in the ticket]
```

## Common issues & anti-patterns

- **Acceptance criteria written as design specs.** "The button is blue and centered" is a visual design spec, not a functional acceptance criterion. The UAT scenario must verify behavior: does clicking it do the right thing?
- **Single-role assumption.** All scenarios test one user role. Multi-tenant apps, role-based access control, and shared-resource features need cross-role and cross-tenant scenarios or the most common production bugs will not be found until after launch.
- **Happy path only.** Stakeholders confirm the flow works when everything is correct. The first real user will immediately find the edge case (empty state, validation error, permission denied) that has no scenario.
- **Vague preconditions.** "User has some items" is not executable. "User has exactly three items: one in draft, one published, one archived" is. Vague preconditions produce inconsistent UAT results across testers.
- **Implicit data dependencies between scenarios.** Scenario B assumes the record created in scenario A still exists. If run independently or in a different order, B fails. Each scenario must be self-contained.
- **No rollback or undo scenario.** For destructive actions (delete, bulk publish, send email to 10,000 subscribers), no scenario verifies the confirmation dialog, the undo mechanism, or what happens when the action is accidentally triggered.
- **Missing async outcome testing.** The form submits successfully but the scenario does not verify the email was received or the webhook fired. Async outcomes need their own Then with a concrete SLA.
- **Treating UAT as a rubber stamp.** Scenarios written after the feature is "done" that only test what the developer already verified. UAT should surface expectations the developer did not know about — particularly around role permissions, empty states, and error messaging.

## Required output

```
## UAT Acceptance Plan: [Feature Name]

### Source
Ticket / PRD: [reference]
Reviewed by: [role of reviewer, e.g., "QA lead"]
Date: [ISO date]

### Stated acceptance criteria
1. [Original text verbatim]
2. ...

### User roles in scope
- [Role 1]: [brief description of their interaction with this feature]
- [Role 2]: ...

### Scenarios

#### Scenario 1: [Name — role — happy path]
**Given** [exact preconditions and data]
**When** [exact actions]
**Then** [exact outcomes, element-level, with persistence and side effects]
**Data setup**: [seed or factory]
**Gate**: Blocking

#### Scenario 2: [Name — role — negative path: invalid input]
...

#### Scenario 3: [Name — role — permission boundary]
...

### Derived criteria (implied, not in ticket — needs product confirmation)
- [Criterion]: [description of implied behavior] — Question: [what needs to be confirmed?]

### Out of scope
- [Anything explicitly excluded from this UAT round and why]

### Pass/fail gate
UAT is complete when: all [N] Blocking scenarios pass.
Non-blocking scenarios [list] may be deferred to [milestone or next sprint].
```

## Safety

- Do not execute UAT scenarios against production data or production environments — use staging or a dedicated UAT environment.
- Do not create, modify, or delete records in any environment yourself; produce the plan for human testers to execute.
- Do not invent acceptance criteria and present them as confirmed requirements; flag all derived criteria explicitly as needing stakeholder sign-off.
- Do not mark a scenario as Non-blocking to reduce the gate size without explicit product confirmation.
- When the feature involves payment, personal data, or legal compliance, flag those scenarios for review by the relevant domain owner before UAT begins.

## Completion criteria

Done means every stated acceptance criterion maps to at least one Given/When/Then scenario, every user role has dedicated scenarios, negative paths exist for each happy path, all implied criteria are listed and flagged, data setup and observable outcomes are specified with enough precision that a non-technical tester can execute them without asking a follow-up question, and the pass/fail gate is defined.

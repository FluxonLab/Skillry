---
name: product-requirements-review
description: Use when you need to review requirements, user stories, acceptance criteria, scope, and ambiguity.
---

# Product Requirements Review

## Purpose

Systematically evaluate a product requirements document (PRD), epic, or user story set for completeness, testability, scope clarity, and hidden risk. Produce a structured critique with specific gaps, suggested rewrites, and a MoSCoW priority assessment. Every finding must cite the exact phrase or story ID that caused it — no vague impressions.

## When to use

- A PM, designer, or engineer hands you a PRD, epic, ticket, or feature brief and asks for review.
- A user story exists but lacks acceptance criteria or has vague scope.
- A requirements doc needs a "definition of done" or success metrics attached.
- You are about to start implementation and want to surface ambiguities before writing code.
- Stakeholder sign-off is pending and you need a checklist to clear.
- A sprint planning session is blocked because engineers say the spec is unclear.

## When not to use

- The request is purely technical (architecture, code review) with no requirements layer — use `architecture-review` instead.
- The document is a marketing brief, not a product spec.
- No document exists yet; ask the requester to draft a rough version first.
- The scope is so narrow (single-line bug fix) that a full PRD review adds no value.
- The request is for business model or pricing strategy — use `business-model-review` or `pricing-packaging-review`.

## Procedure

1. **Ingest and classify**: Read the full document. Note the artifact type (user story, epic, PRD, feature brief). Identify the stated problem, target persona, and desired outcome. If none of these are findable, flag as a critical gap before proceeding.
2. **User story check**: Confirm every story follows "As a [persona], I want [action], so that [outcome]." Flag stories missing any element. "As a user, I want a dashboard" has no outcome — flag it. The persona must be specific enough to be useful: "Admin" is acceptable; "user" alone rarely is.
3. **Acceptance criteria audit**: Each story must have at least one measurable AC in Given/When/Then or bullet form. Flag stories with zero ACs. Flag ACs that say "works correctly," "is fast," or "looks good" — these are unverifiable. Rewrite vague ACs into observable form: "p95 load time < 1.5 s measured on a throttled 4G connection."
4. **Scope clarity sweep**: Identify sentences containing "etc.", "and more", "as needed", "TBD", or undefined acronyms. Each one is an open question that will turn into a scope argument during development. List each with the exact quoted phrase and a suggested clarification question.
5. **MoSCoW tagging**: If priorities are missing, propose Must/Should/Could/Won't for each requirement based on the stated problem and user outcome. Check for MoSCoW inflation: if more than 50% of requirements are labelled Must, push back — a document where everything is critical has no real priorities.
6. **Success metrics check**: Confirm at least one measurable success metric exists (conversion rate, task-completion rate, latency target, error rate, NPS delta). If absent, propose one. A metric must have a baseline (even if approximate) and a target. "Users will love it" is not a metric.
7. **Assumptions and risks**: List explicitly stated assumptions. Surface unstated assumptions embedded in the requirements. Identify the top 3 risks across technical, market, and resource categories. For each risk state: likelihood (H/M/L), impact (H/M/L), and a concrete mitigation.
8. **Dependencies**: Enumerate upstream APIs, third-party services, internal teams, or datasets the feature depends on. For each: who owns it, is availability confirmed, and is the rate limit, SLA, or data freshness requirement known?
9. **Edge cases and failure paths**: For each core flow, name at least one error or edge path that must be handled. Empty states, permission boundaries, timeouts, and partial data are the most commonly missed.
10. **Definition of Done**: Confirm that a DoD exists or can be derived from the ACs. The DoD must be usable by a QA engineer to write a test plan without additional information.
11. **Output**: Produce the structured report.

## Concrete checks

- [ ] User story format: As a / I want / So that — all three parts present and specific
- [ ] Acceptance criteria: at least one per story, testable, observable, non-ambiguous
- [ ] No "TBD", "etc.", undefined acronyms in scope-defining sentences
- [ ] MoSCoW labels assigned to all requirements; Must count is under 50% of total
- [ ] At least one measurable success metric with baseline and target
- [ ] Assumptions section exists and distinguishes stated from unstated
- [ ] Top 3 risks identified with likelihood, impact, and mitigation
- [ ] External dependencies named with owner and confirmed availability
- [ ] At least one negative or error path per core flow
- [ ] Definition of Done stated or derivable from ACs without follow-up questions
- [ ] Personas are specific enough to drive scope decisions
- [ ] No requirement implies PII, financial data, or health data storage without a compliance note

## Review template

Use this block when producing the structured output:

```
## PRD Review: [Document name or summary]

### Story coverage
- [PASS/FAIL] [story-id or summary] — reason

### Open scope questions
1. "[Ambiguous phrase quoted verbatim]" → Suggested clarification question

### MoSCoW assessment
| Requirement | Proposed priority | Rationale |
|-------------|------------------|-----------|
| [req]       | Must/Should/Could/Won't | [why] |

### Missing acceptance criteria
- [story-id]: Given [context] When [action] Then [observable result]

### Success metrics
- Proposed: [metric name], baseline: [known value or "unknown"], target: [suggested value]
- How to measure: [method, tool, or query]

### Assumptions
- Stated: [list from document]
- Unstated (surfaced by reviewer): [list with explanation]

### Top 3 risks
1. [Risk description] — likelihood: H/M/L, impact: H/M/L, mitigation: [concrete action]

### Dependencies
- [Service/team/data] — owner: [known/unknown], availability: [confirmed/assumed], SLA/limit: [known/unknown]

### Edge cases missing
- [Flow]: missing error path for [condition]

### Definition of Done
[Stated / Proposed]

### Recommended next steps
1. [Action — who, by when]
```

## Common issues & anti-patterns

- **Outcome-less stories**: "As a user, I want to see a dashboard" with no "so that" means no way to judge value or scope. The team will build whatever they imagine, which is never exactly what was wanted.
- **Vague ACs**: "The page loads fast" is not testable. Replace with "p95 load time < 1.5 s on a throttled 4G connection, measured in WebPageTest." The specifics force a real implementation decision.
- **Scope creep language**: "...and other relevant data" is invisible scope. Enumerate exactly what data. Any "and more" in a spec becomes every engineer's justification for adding unreviewed work.
- **Missing personas**: "User" without qualification — who exactly? Admin? Free-tier member? API consumer? The persona determines the permission level, the UI pattern, and the priority.
- **No failure path**: Every AC describes the happy path. No error handling, empty state, or permission boundary is specified. QA discovers these gaps two days before release.
- **Success by feel**: "Users will find it intuitive" cannot be measured. Attach a metric proxy: task completion rate on first attempt, time-on-task in a usability test, or support ticket volume for the flow.
- **Dependency blindness**: Feature assumes a third-party API is available, rate-limit-free, and returning the expected schema. None of these are checked in the spec.
- **MoSCoW inflation**: Marking 80%+ of requirements as Must forces a negotiation crisis at the last minute. Real prioritization means painful choices made early.
- **Requirements without rationale**: "The export button must support CSV, Excel, PDF, and JSON." Why all four? If the rationale is absent, the team cannot make scope trade-offs when time pressure hits.
- **Ambiguous AC quantifiers**: "The system should handle high traffic" — what volume? State the tested load target explicitly.
- **Missing rollback or undo requirements**: For any destructive or irreversible action (delete, publish, send), the spec must state whether undo is required and within what window.
- **Conflating requirement with solution**: "We need to add a Redis cache for performance." Redis is a solution; the requirement is the latency target. Requirements describe what, not how.

## Calibrating review depth

Not every PRD deserves the same review effort. Calibrate the depth to the blast radius:

| PRD type | Key focus areas | Depth |
|----------|----------------|-------|
| Single user story (bug or small feature) | AC testability, edge cases, DoD | Light: run steps 2–3 and 9 only |
| Multi-story epic (feature area) | All steps; MoSCoW; dependency map | Standard: all 11 steps |
| Platform or API change (downstream consumers) | Dependencies, breaking changes, versioning, rollback | Deep: add compatibility matrix |
| Regulated domain (finance, health, legal) | Compliance flags, data handling, consent | Deep: flag every PII/PHI/financial data touch |

For light reviews, produce a short findings table rather than the full template. For deep reviews, add a breaking-change matrix and a compliance flag section.

## Severity levels for findings

Use these levels consistently so the requester can prioritise fixes:

- **Block**: The requirement cannot be implemented or tested as written. Examples: missing persona, no acceptance criteria, circular dependency with no resolution path. The document must be revised before development starts.
- **Major**: The requirement can be implemented but will predictably cause a scope dispute, a missed edge case, or a failed QA cycle. Examples: vague AC quantifier, unstated dependency, no error path. Should be resolved before sprint planning.
- **Minor**: The requirement is implementable but incomplete or imprecise in a way that will require a clarification question. Examples: missing rationale, ambiguous synonym. Can be resolved during development with a quick PM check.
- **Note**: Observation that does not block work but is worth recording. Examples: MoSCoW label seems off, metric is hard to measure, similar requirement exists in another epic.

Label each finding in the output with its severity level.

## Required output

Return a structured review with all sections from the template above: story coverage pass/fail per story, open scope questions (quoted verbatim), MoSCoW assessment table, suggested ACs for failing stories, proposed success metrics with measurement method, surfaced unstated assumptions, top 3 risks with mitigation, dependency status table, missing edge cases, proposed DoD, and recommended next steps with owner. Label each finding with Block / Major / Minor / Note severity.

## Safety

- Do not invent acceptance criteria that change the intended product behaviour; label proposals clearly as "suggested."
- Do not discard or rewrite requirements unilaterally; present alternatives for the requester to accept or reject.
- If the document contains personal data about real users, do not quote it verbatim in the output.
- Flag any requirement that implies storing PII, financial data, or health data — note that compliance review (GDPR, HIPAA, PCI-DSS) is outside the scope of this skill and must be a separate workstream.
- Do not recommend implementation approaches; this skill reviews requirements, not technical design.

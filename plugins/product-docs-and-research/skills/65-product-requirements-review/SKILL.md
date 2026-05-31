---
name: product-requirements-review
description: Use when you need to review requirements, user stories, acceptance criteria, scope, and ambiguity.
---

# Product Requirements Review

## Purpose

Systematically evaluate a product requirements document (PRD), epic, or user story set for completeness, testability, scope clarity, and hidden risk. Produce a structured critique with specific gaps, suggested rewrites, and a MoSCoW priority assessment.

## When to use

- A PM, designer, or engineer hands you a PRD, epic, ticket, or feature brief and asks for review.
- A user story exists but lacks acceptance criteria or has vague scope.
- A requirements doc needs a "definition of done" or success metrics attached.
- You are about to start implementation and want to surface ambiguities before writing code.
- Stakeholder sign-off is pending and you need a checklist to clear.

## When not to use

- The request is purely technical (architecture, code review) with no requirements layer — use `adr-generator` or `code-review` instead.
- The document is a marketing brief, not a product spec.
- No document exists yet; ask the requester to draft a rough version first.
- The scope is so narrow (single-line bug fix) that a full PRD review adds no value.

## Procedure

1. **Ingest**: Read the full document. Note the artifact type (user story, epic, PRD, feature brief).
2. **User story check**: Confirm every story follows "As a [persona], I want [action], so that [outcome]." Flag stories missing any element.
3. **Acceptance criteria audit**: Each story must have ≥1 measurable AC in Given/When/Then or bullet form. Flag stories with zero ACs or ACs that say "works correctly."
4. **Scope clarity**: Identify sentences that contain "etc.", "and more", "as needed", "TBD", or undefined acronyms. List each as an open question.
5. **MoSCoW tagging**: If priorities are missing, propose Must/Should/Could/Won't for each requirement based on the stated problem and user outcome.
6. **Success metrics**: Confirm at least one measurable success metric exists (conversion rate, latency, error rate, NPS delta). Propose one if absent.
7. **Assumptions and risks**: List explicitly stated assumptions. Surface unstated assumptions. Identify top 3 risks (technical, market, resource).
8. **Dependencies**: Enumerate upstream APIs, third-party services, teams, or data sources the feature depends on.
9. **Edge cases**: For each core flow, name at least one error/edge path that must be handled.
10. **Output**: Produce the structured report (see Required output).

## Checklist

- [ ] User story format: As a / I want / So that — all three parts present
- [ ] Acceptance criteria: at least one per story, testable and non-ambiguous
- [ ] No "TBD", "etc.", undefined acronyms in scope-defining sentences
- [ ] MoSCoW labels assigned to all requirements
- [ ] At least one measurable success metric (with baseline if known)
- [ ] Assumptions section exists and is explicit
- [ ] Top risks identified with likelihood and impact
- [ ] External dependencies named (API, team, dataset)
- [ ] At least one negative/error path per core flow
- [ ] Definition of Done is stated or can be derived from ACs

## Common issues & anti-patterns

- **Outcome-less stories**: "As a user, I want to see a dashboard" — no "so that" means no way to judge value or scope.
- **Vague ACs**: "The page loads fast" is not testable. Replace with "p95 load time < 1.5 s on 4G."
- **Scope creep language**: "...and other relevant data" is invisible scope. Enumerate exactly what data.
- **Missing personas**: "User" without qualification — who? Admin? Free-tier? API consumer?
- **No failure path**: Every AC describes the happy path; no error handling, empty state, or permission boundary.
- **Success by feel**: "Users will find it intuitive" — cannot be measured. Attach a metric proxy (task completion rate, support tickets).
- **Dependency blindness**: Feature assumes a third-party API is available and rate-limit-free — neither checked.
- **MoSCoW inflation**: Marking 90% of requirements as Must; forces negotiation at the last minute.

## Required output

Return a structured review with these sections:

```
## PRD Review: [Document name or summary]

### Story coverage
- [PASS/FAIL] [story-id or summary] — reason

### Open scope questions
1. [Quote the ambiguous phrase] → Suggested clarification

### MoSCoW assessment
| Requirement | Proposed priority | Rationale |

### Missing acceptance criteria
- [story-id]: Suggested AC: Given … When … Then …

### Success metrics
- Proposed: [metric], baseline: [known/unknown], target: [suggested]

### Assumptions
- Stated: …
- Unstated (surfaced): …

### Top 3 risks
1. [Risk] — likelihood: H/M/L, impact: H/M/L, mitigation: …

### Dependencies
- [Service/team/data] — owner: [known/unknown], status: [confirmed/assumed]

### Recommended next steps
1. …
```

## Safety

- Do not invent acceptance criteria that change the intended product behaviour; label proposals clearly as "suggested."
- Do not discard or rewrite requirements unilaterally; present alternatives for the requester to accept.
- If the document contains personal data about real users, do not quote it verbatim in output.
- Flag any requirement that implies storing PII, financial data, or health data — note that compliance review (GDPR, HIPAA, PCI) is outside scope of this skill.

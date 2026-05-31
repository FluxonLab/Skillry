---
name: adr-generator
description: Use when you need to generate architecture decision records with context, decision, consequences, and alternatives.
---

# ADR Generator

## Purpose

Generate a well-structured Architecture Decision Record (ADR) that captures the context forcing a decision, the decision itself, alternatives considered with their trade-offs, and the consequences (positive, negative, and neutral). The output is a markdown file ready to commit to the project's `docs/decisions/` or `adr/` directory.

## When to use

- A significant architectural decision has been made or is being proposed: choice of database, framework, API style, authentication mechanism, deployment model, data model.
- A technical trade-off discussion has happened in Slack/email/meeting and the outcome needs to be recorded before it is lost.
- An existing implicit decision needs to be made explicit for a new team member's benefit.
- A rejected approach needs to be documented so the team does not re-litigate it six months later.
- A reversible decision is being made and the reversal criteria need to be captured.

## When not to use

- The decision is trivial or ephemeral (variable naming, local config value).
- The decision is purely operational with no architectural implication (which alert threshold to set).
- The decision has already been made, implemented, and fully settled with no remaining uncertainty — ADRs are most valuable before or immediately after the decision, not years later.
- A design doc or RFC is the appropriate format (use an ADR for point-in-time decisions, not open-ended design exploration).

## Procedure

1. **Gather inputs**: Ask for or extract:
 - What decision was made (or is being proposed)?
 - What problem or constraint forced this decision?
 - When was the decision made (or is it still open)?
 - Who are the decision makers or stakeholders?
 - What alternatives were considered?
 - What are the known consequences?
2. **Assign ADR number and title**: Check existing ADRs in the project (look in `docs/decisions/`, `adr/`, or `docs/adr/`). Assign the next sequential number. Title format: `[verb] [subject]` — e.g., "Use PostgreSQL for user data storage", "Adopt OpenAPI 3.1 for all service contracts".
3. **Write Context**: Describe the forces at play — business constraints, technical constraints, team capabilities, existing system state. Be specific. "We needed a database" is not context; "We need a database that supports geospatial queries, has managed hosting on AWS, and can be operated by a team with no DBA" is context.
4. **Write Decision**: One clear sentence stating what was decided. Start with "We will" or "We have decided to." No hedging.
5. **Write Alternatives considered**: List every option that was genuinely considered. For each: what it is, why it was considered, why it was not chosen (specific trade-off, not "it was worse").
6. **Write Consequences**: Three subsections:
 - Positive: what does this enable?
 - Negative: what does this cost, constrain, or risk?
 - Neutral: what changes but is neither good nor bad?
7. **Set Status**: `Proposed` (decision pending), `Accepted` (decided), `Deprecated` (superseded but kept for history), `Superseded by ADR-NNN`.
8. **Output the file**: Write the ADR as a markdown file with the naming convention `NNNN-kebab-case-title.md`.

## Checklist

- [ ] ADR number assigned sequentially (no gaps, no duplicates)
- [ ] Title is `[verb] [subject]` format
- [ ] Context section describes forces — not just background
- [ ] Decision is one sentence, starts with "We will" or "We have decided to"
- [ ] At least 2 alternatives documented with specific rejection reasons
- [ ] Consequences split into positive / negative / neutral
- [ ] Status set (Proposed / Accepted / Deprecated / Superseded)
- [ ] Date recorded
- [ ] Decision makers / authors named
- [ ] File named `NNNN-kebab-case-title.md`

## Common issues & anti-patterns

- **Context = backstory**: Context must describe the forces that made the decision hard, not just what the system looks like. Include constraints.
- **Decision = long paragraph**: The decision should be one sentence. Details go in Consequences or a linked design doc.
- **Only one alternative**: If only one option was considered, there was no real decision — or the other options were not documented. Both are problems.
- **Vague rejection reasons**: "Option B was too complex" — complex for whom? At what scale? Be specific.
- **No negative consequences**: Every decision has trade-offs. A Consequences section with only positives signals the author did not think carefully or is writing post-hoc justification.
- **Status left as Proposed forever**: An ADR that was accepted but never updated causes confusion. Make updating status part of the PR merge checklist.
- **Consequences confused with decisions**: "We will now use X everywhere" is a decision, not a consequence. Keep them separate.

## Required output

Produce a complete markdown file ready to commit:

```markdown
# ADR-NNNN: [Title]

**Status**: [Proposed | Accepted | Deprecated | Superseded by ADR-NNNN]
**Date**: YYYY-MM-DD
**Authors**: [Names or GitHub handles]
**Deciders**: [Names or roles]

---

## Context

[Describe the forces, constraints, and problem that required a decision.
Include: business context, technical constraints, team context, known risks.
Be specific enough that someone unfamiliar with the situation can understand
why doing nothing was not a viable option.]

## Decision

We will [clear, single-sentence statement of the decision].

## Alternatives considered

### Option A: [Name]
**What it is**: [Brief description]
**Why considered**: [What made it a real candidate]
**Why not chosen**: [Specific trade-off, constraint, or risk that eliminated it]

### Option B: [Name]
[Same structure]

### Option C: [Name — the chosen option, listed here for symmetry]
**What it is**: [Brief description]
**Why chosen**: [What made it the best fit given the context]

## Consequences

### Positive
- [What this decision enables or improves]

### Negative
- [What this decision costs, constrains, or introduces as risk]
- [Technical debt, migration cost, learning curve, vendor lock-in]

### Neutral
- [What changes but is neither good nor bad — a team must be informed]

## Links

- [Related ADR, issue, PR, design doc, or external reference]
```

## Safety

- Do not alter the decision itself if you are only asked to document it — the ADR records the decision, it does not make it.
- If the decision has security implications (auth mechanism, secret storage, encryption approach), add a note that the ADR should be reviewed by a security lead before it is marked Accepted.
- Do not include secrets, credentials, or internal IP addresses in the ADR — reference them by name or vault path.

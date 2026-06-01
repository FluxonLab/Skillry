---
name: skill-to-agent-router
description: Use when you need to map skills to agents, departments, optional bindings, exclusions, and activation rules.
---

# Skill to Agent Router

## Purpose

Given a task description or skill name, determine which agent (or agents) in the roster is the correct executor — and which skills that agent should activate. Produce a routing decision with binding type (primary/optional/excluded), department assignment, and activation conditions. This is the dispatch layer between a task and the agent+skill combination that fulfils it, designed to prevent ambiguous self-selection and routing a privileged action to an agent that lacks the right tool access.

## When to use

- An orchestrator receives a task and needs to know which agent to delegate it to.
- A task spans multiple domains and the right agent + skill combination is unclear.
- A new skill has been installed and its agent bindings need configuring.
- An agent roster has grown and routing rules need auditing for gaps or conflicts.
- A user asks "which agent should handle X?" and the answer is not obvious.

## When not to use

- The task is to find which skill to use, not which agent — use `71-skill-librarian`.
- The task is already inside an agent session and skill selection is the only remaining question.
- The agent is already fixed by explicit user instruction — route to it without running this skill.
- The routing question concerns external services or APIs, not the internal agent roster.

## Procedure

1. **Parse the task.** Extract domain, action, audience (human-facing vs. system), urgency, and stated constraints ("do not touch production", "must use approved vendor").
2. **Scan the agent roster.** Read only the `name:`, `description:`, and `skills:` frontmatter from each AGENT.md (see Commands).
3. **Match task to agent by domain** using the table below.
4. **Assign binding types.** *Primary*: best-fit executor; the skill is a required binding. *Optional*: can handle the task with this skill loaded on demand. *Excluded*: must not handle this task (wrong domain, conflict of interest, missing tool access).
5. **Check for multi-agent tasks.** If the task needs outputs from more than one domain, propose a handoff chain — sequential (A produces, B consumes) or parallel (both run, orchestrator merges).
6. **Check activation conditions.** Some agents are valid only under conditions: time-based (scheduled, real-time), data-access (requires DB connection or API key), or approval-gate (requires human sign-off). State these in the decision.
7. **Output the routing decision.**

Domain-to-agent map:

| Task domain | Likely agent family |
|---|---|
| Product / PRD / requirements | product-manager, product-analyst |
| Market research / competitive | researcher, analyst |
| Business model / unit economics | finance-analyst, strategy |
| Pricing / packaging | product-manager, revenue-ops |
| Technical writing / docs | technical-writer, developer-relations |
| ADR / architecture decisions | architect, senior-engineer |
| Skill library meta-tasks | skill-librarian-agent, orchestrator |
| Installation / path hygiene | sysadmin, devops |
| Code / engineering | engineer, developer |

## Concrete checks

- [ ] Task domain, action, and constraints parsed before scanning.
- [ ] Agent roster scanned by frontmatter only (not full AGENT.md bodies).
- [ ] Primary agent designated with an explicit skill binding.
- [ ] Optional and excluded agents listed with reasons.
- [ ] Multi-agent handoff chain proposed if the task spans domains, with direction stated.
- [ ] Activation conditions stated for each binding (none / time / data / approval).
- [ ] No agent recommended that lacks the required tool access for the task.
- [ ] Destructive or production-touching tasks carry a human-approval activation condition.

## Commands or Templates

```bash
# Roster scan: name, description, and skill bindings per agent
grep -rn "^name:\|^description:\|^skills:" ~/.claude/agents/*/AGENT.md | head -200

# Which agents already bind a given skill?
grep -rln "security-and-secrets-review" ~/.claude/agents/*/AGENT.md

# Detect agents with NO skills binding (routing gap candidates)
for d in ~/.claude/agents/*/; do
  grep -q "^skills:" "$d/AGENT.md" 2>/dev/null || echo "no skills bound: $(basename "$d")"
done
```

```
## Skill-to-Agent Routing Decision

Task: [parsed task]   Domain: [domain]   Action: [action]

### Primary routing
Agent: [agent-name]
Skill binding: [skill-name] — Primary
Rationale: [one sentence]
Activation conditions: [none / list]

### Optional bindings
| Agent | Skill | Condition for activation |
|-------|-------|--------------------------|

### Excluded agents
| Agent | Reason |
|-------|--------|

### Multi-agent handoff (if applicable)
Step 1: [agent-A] runs [skill-X] → produces [artifact]
Step 2: [agent-B] consumes [artifact] → runs [skill-Y] → produces [final]
Orchestrator merges: [yes/no]

### Unresolved routing gaps
[task aspects no current agent covers — flag for roster expansion]
```

## Worked routing example

Task: "draft a PRD for the new export feature, backed by a competitor comparison, and turn it into an ADR for the storage-format decision." Parsed: three domains (product, research, architecture), action = generate, audience = internal, no production touch.

This is a multi-agent task — no single agent owns all three. The routing decision:

- **Primary**: `product-manager` with `65-product-requirements-review` (owns the PRD).
- **Sequential dependency**: `researcher` with `66-market-research-synthesis` must run *first* — the PRD's positioning section consumes its competitor comparison. So step 1 is research, step 2 is the PRD.
- **Then** `architect` with `70-adr-generator` consumes the PRD's storage requirement to produce the ADR (step 3).
- **Excluded**: `engineer` (no implementation in scope yet); the `orchestrator` is the dispatcher, not an executor.
- **Activation conditions**: none are destructive or production-touching, so no approval gate is required.

Handoff chain: researcher → product-manager → architect, with the orchestrator owning the final merged deliverable (PRD + ADR). Stating the direction explicitly prevents the common failure of two agents both producing a half-PRD with no agreed owner of the final artifact.

## Common issues & anti-patterns

- **Routing to the orchestrator for everything.** The orchestrator delegates; it does not execute domain tasks. Route to the leaf agent.
- **Binding every skill as primary.** Only the skills directly needed are primary; over-binding bloats agent context.
- **Missing the handoff direction.** "Agent A and Agent B both handle this" without saying who goes first or who owns the final output.
- **Ignoring tool-access constraints.** Routing a DB query task to an agent with no DB tool binding.
- **Routing to the most capable, not the most appropriate.** A senior-engineer agent can write docs, but that is the technical-writer's role. Respect domain ownership.
- **No exclusion list.** A roster without explicit exclusions routes ambiguously — agents self-select incorrectly.
- **No approval gate on a destructive route.** Sending a "delete prod records" task to an agent without a human-approval condition risks silent damage.

## Choosing the binding type

The primary/optional/excluded distinction is what makes routing deterministic. Apply it with this test:

- **Primary** — the agent owns this domain and the skill is needed for *this* task. Bind it. Exactly one agent is primary per task (or per step in a chain).
- **Optional** — the agent *could* handle the task if the skill is loaded on demand, but it is not the owner. Useful as a fallback when the primary is unavailable or overloaded. Do not pre-load optional skills into the agent's always-on context.
- **Excluded** — explicitly name agents that must *not* take this task: wrong domain, missing tool access, or a conflict of interest. An empty exclusion list is the most common cause of ambiguous self-selection, where two agents both think the task is theirs.

The rule: bind as primary only the skills the task actually requires, list optionals as on-demand, and always populate the exclusion list — routing without exclusions is routing by guess.

## Required output

Return the routing decision block above: parsed task with domain/action, the primary agent and its skill binding with rationale and activation conditions, optional and excluded agent tables, a multi-agent handoff chain where applicable (with explicit direction and merge ownership), and any unresolved routing gaps flagged for roster expansion.

## Safety

- Do not modify AGENT.md files during a routing query — this is a read-only recommendation.
- Do not route tasks involving secret or credential handling to agents that lack explicit vault/secret-manager tool access.
- If a task involves destructive operations (delete, overwrite, production deploy), add an explicit human-approval activation condition to the routing decision.
- Do not recommend an agent that lacks a required tool binding without flagging the gap.

## Completion criteria

Done means the task was parsed, the roster was scanned by frontmatter only, a primary agent and skill binding were designated with rationale, optional/excluded agents and any handoff chain were listed, activation conditions were stated, and destructive routes carry an approval gate.

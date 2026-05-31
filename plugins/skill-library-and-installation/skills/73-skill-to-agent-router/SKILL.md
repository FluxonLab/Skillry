---
name: skill-to-agent-router
description: Use when you need to map skills to agents, departments, optional bindings, exclusions, and activation rules.
---

# Skill to Agent Router

## Purpose

Given a task description or skill name, determine which agent (or agents) in the `~/.claude/agents/` roster is the correct executor — and which skills that agent should activate for the task. Produce a routing decision with binding type (primary/optional/excluded), department assignment, and activation conditions. This is the dispatch layer between a task and the agent+skill combination that fulfils it.

## When to use

- An orchestrator receives a task and needs to know which agent to delegate it to.
- A task spans multiple domains and the right agent + skill combination is unclear.
- A new skill has been installed and its agent bindings need to be configured.
- An agent roster has grown and routing rules need to be audited for gaps or conflicts.
- A user asks "which agent should handle X?" and the answer is not obvious.

## When not to use

- The task is to find which skill to use, not which agent — use `skill-librarian`.
- The task is already inside an agent session and skill selection is the only remaining question.
- The agent is already determined by explicit user instruction — route to it without running this skill.
- The routing question is about external services or APIs, not the internal agent roster.

## Procedure

1. **Parse the task**: Extract domain, action, audience (human-facing vs. system), urgency, and any stated constraints (e.g., "do not touch production", "must use approved vendor").

2. **Scan agent roster**: Read only the `name:`, `description:`, and `skills:` frontmatter fields from each `~/.claude/agents/*/AGENT.md`:
 ```bash
 grep -rn "^name:\|^description:\|^skills:" ~/.claude/agents/*/AGENT.md | head -200
 ```

3. **Match task to agent by domain**:

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

4. **Assign binding types**:
 - **Primary**: This agent is the best-fit executor; the skill is a required binding.
 - **Optional**: This agent can handle the task with this skill loaded on demand.
 - **Excluded**: This agent must not handle this task (wrong domain, conflict of interest, missing tool access).

5. **Check for multi-agent tasks**: If the task requires outputs from >1 domain (e.g., PRD + competitive analysis), propose a sequential or parallel handoff chain:
 - Sequential: Agent A produces output → Agent B consumes it
 - Parallel: Both agents run independently → Orchestrator merges results

6. **Check activation conditions**: Some agents are only valid under conditions:
 - Time-based (scheduled, real-time)
 - Data-access (requires DB connection, API key)
 - Approval-gate (requires human sign-off before action)
 State these conditions in the routing decision.

7. **Output the routing decision**.

## Checklist

- [ ] Task domain, action, and constraints parsed before scanning
- [ ] Agent roster scanned by frontmatter only (not full AGENT.md bodies)
- [ ] Primary agent designated with skill binding
- [ ] Optional and excluded agents listed
- [ ] Multi-agent handoff chain proposed if needed
- [ ] Activation conditions stated for each binding
- [ ] No agent recommended that lacks required tool access for the task

## Common issues & anti-patterns

- **Routing to the orchestrator for everything**: The orchestrator delegates; it does not execute domain tasks. Route to the leaf agent.
- **Binding every skill as primary**: Only the skills directly needed for the task are primary. Over-binding bloats agent context.
- **Missing the handoff direction**: "Agent A and Agent B both handle this" without specifying who goes first or who owns the final output.
- **Ignoring tool access constraints**: Routing a database query task to an agent that has no DB tool binding.
- **Routing to the most capable agent, not the most appropriate**: A senior-engineer agent can write docs, but that is the technical-writer agent's role. Respect domain ownership.
- **No exclusion list**: An agent roster without explicit exclusions will route ambiguously — agents may self-select incorrectly.

## Required output

```
## Skill-to-Agent Routing Decision

Task: [parsed task description]
Domain: [domain] Action: [action]

### Primary routing

**Agent**: [agent-name]
**Skill binding**: [skill-name] — binding type: Primary
**Rationale**: [One sentence]
**Activation conditions**: [none / [condition list]]

### Optional bindings

| Agent | Skill | Condition for activation |
|---|---|---|
| [agent] | [skill] | [when to activate] |

### Excluded agents

| Agent | Reason |
|---|---|
| [agent] | [why excluded] |

### Multi-agent handoff (if applicable)

Step 1: [agent-A] runs [skill-X] → produces [artifact]
Step 2: [agent-B] consumes [artifact] → runs [skill-Y] → produces [final output]
Orchestrator merges: [yes/no]

### Unresolved routing gaps

[List any task aspects that no current agent covers — flag for roster expansion]
```

## Safety

- Do not modify AGENT.md files during a routing query — this is a read-only recommendation.
- Do not route tasks involving secret or credential handling to agents that do not have explicit vault/secret-manager tool access.
- If a task involves destructive operations (delete, overwrite, deploy to production), add an explicit human-approval activation condition to the routing decision.

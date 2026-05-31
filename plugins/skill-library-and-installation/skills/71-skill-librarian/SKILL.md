---
name: skill-librarian
description: Use when you need to search, select, and recommend at most five relevant skills without activating the whole archive.
---

# Skill Librarian

## Purpose

Search the installed skill library (~/.claude/skills, currently 90+ skills) and the agent roster (~/.claude/agents, currently 64 agents) to identify and recommend the best-fit skills for a given task. Return at most 5 recommendations with clear rationale. Never load or activate dormant skills unnecessarily — only surface them by name and description.

## When to use

- A user or agent asks "which skill should I use for X?"
- A task description does not map obviously to a single skill and a selection is needed.
- A new agent is being configured and its `skills:` binding list needs to be populated.
- An orchestrator is routing a subtask and needs to know the canonical skill for a domain.
- You need to confirm that a skill exists before referencing it in a workflow.

## When not to use

- The correct skill is already known — skip the librarian and invoke it directly.
- The task requires creating a new skill — use `skill-creator` (anthropic-skills).
- The task requires checking for duplicate or overlapping skills — use `skill-deduplication`.
- A user wants to route a task to an agent, not a skill — use `skill-to-agent-router`.

## Procedure

1. **Parse the task description**: Extract the domain (product, engineering, research, finance, writing, infra, skill-meta), the action type (review, generate, synthesize, audit, repair, route), and any constraints (e.g., "without touching the database", "for a non-technical audience").

2. **Scan skill index**: Do NOT load all SKILL.md files. Read only the directory listing and the `name:` + `description:` frontmatter fields. Command:
 ```bash
 for d in ~/.claude/skills/*/; do
 grep -m2 "^name:\|^description:" "$d/SKILL.md" 2>/dev/null
 echo "---"
 done
 ```

3. **Match by domain and action**: Map the parsed task to the skill taxonomy:
 - Product/docs/research domain: skills 60–69
 - Skill-meta/installation domain: skills 70–90
 - Engineering/infra: look for skills with "audit", "repair", "generator" in name
 - Writing/content: "technical-writing", "adr", "prd"

4. **Apply exclusion filters**: Exclude skills that:
 - Are in the dormant archive (prefix `arch-` or number > 80 unless clearly relevant)
 - Overlap with a narrower skill already in the candidate list
 - Require a tool or agent binding not available in the current context

5. **Rank candidates**: Score each candidate on:
 - Domain match (0–3)
 - Action match (0–3)
 - Constraint compatibility (0–2)
 - Recency / canonical status (0–2)
 Select top ≤5.

6. **Return recommendation**: For each recommended skill, state: skill name, skill number, one-sentence rationale, and whether it is a primary match or a secondary/fallback.

7. **State what was not loaded**: Confirm that no dormant skill families were bulk-activated.

## Checklist

- [ ] Task domain and action parsed before scanning
- [ ] Only `name:` and `description:` fields read — no full SKILL.md bodies loaded
- [ ] Candidate list trimmed to ≤5
- [ ] Each recommendation has a one-sentence rationale
- [ ] Primary vs. secondary distinction made
- [ ] Dormant archive not bulk-loaded
- [ ] If no skill matches, explicitly stated (do not hallucinate a skill name)

## Common issues & anti-patterns

- **Loading full SKILL.md bodies for 90 skills to find one match**: Wastes context. Use the index-scan approach (frontmatter only).
- **Recommending a skill by approximate name**: "I think there's a skill called `product-review`..." — verify the exact `name:` value before recommending.
- **Recommending more than 5 skills**: Decision paralysis. Force yourself to pick the best 5; if the task is genuinely multi-domain, recommend a sequential chain.
- **Not distinguishing primary from fallback**: "Use any of these" leaves the caller no better off.
- **Recommending dormant archive skills for live tasks**: Archive skills exist for traceability; they are not active candidates unless explicitly requested.
- **Missing the meta-skill option**: If the task is about skills themselves (deduplicate, audit, route), the answer is almost always within skills 70–79.

## Required output

```
## Skill Librarian Result

Task: [parsed task description]
Domain: [domain] Action: [action]

### Recommendations (ranked)

1. **[skill-name]** (skill-NN)
 Match: [Primary / Secondary]
 Rationale: [One sentence]

2. **[skill-name]** (skill-NN)
 ...

[Up to 5 entries]

### Not recommended (with reason)
- [skill-name]: [why excluded]

### Archive not loaded
Dormant skills were not bulk-activated. The following archive families were scanned by name only: [list if applicable].
```

## Safety

- Do not activate or load dormant skill archive entries into context unless the user explicitly requests it.
- Do not invent skill names. If a needed skill does not exist, state "no matching skill found — consider creating one with `skill-creator`."
- Do not modify any SKILL.md file during a librarian query — this is a read-only operation.

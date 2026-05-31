---
name: skill-deduplication
description: Use when you need to detect duplicate and overlapping skills, choose canonical versions, and document deferred alternatives.
---

# Skill Deduplication

## Purpose

Scan the installed skill library for functional overlap, name collisions, and redundant coverage. For each conflict cluster, designate one canonical skill, propose a disposition for each duplicate (merge, archive, redirect, delete), and produce a deduplication report. Do not delete anything without explicit user confirmation.

## When to use

- The skill count has grown to a point where routing is ambiguous (a task could match 2+ skills).
- A new skill has been installed and its description overlaps with an existing skill.
- After a batch import of skills from a new source, before activating them.
- A user reports that the wrong skill was invoked for a task — the root cause may be overlapping descriptions.
- A periodic housekeeping audit is being run on the skill library.

## When not to use

- The goal is to find the right skill for a task — use `skill-librarian`.
- Only one or two specific skills need to be compared — compare them directly without running the full deduplication scan.
- The overlap is intentional (e.g., a project-scoped skill that shadows a global skill for a specific context) — do not deduplicate intentional layering.

## Procedure

1. **Build the skill inventory**: Scan all SKILL.md files in `~/.claude/skills/` and read only the `name:` and `description:` fields from each frontmatter. Build a flat list: `[number, name, description_text]`.

 ```bash
 grep -rn "^name:\|^description:" ~/.claude/skills/*/SKILL.md | \
 awk -F: '{print $1, $3}' | paste - -
 ```

2. **Cluster by semantic similarity**: Group skills whose descriptions or names share a core verb-object pair. Examples of conflict signals:
 - Same verb + same domain: "review … requirements" appearing in two skills
 - Same noun + synonymous verb: "audit" and "inspect" applied to the same subject
 - Name collision: two skills with names differing only by hyphen/underscore or plural

3. **Score each cluster**: For each conflict cluster, score each skill on:
 - Specificity (more specific = better canonical candidate)
 - Completeness of SKILL.md body (fuller procedure = better)
 - Installation recency (newer number = more likely current)
 - Reference count (how many agents or other skills reference this skill name)

4. **Designate canonical skill**: The highest-scoring skill in each cluster is the canonical version. Document the rationale.

5. **Propose disposition for each non-canonical skill**:
 - **Merge**: If the non-canonical skill has unique sections or examples not in the canonical, merge those sections in.
 - **Archive**: Move to `~/.claude/skills/archive/` — keep for traceability, exclude from active routing.
 - **Redirect**: Add a one-line note to the non-canonical SKILL.md pointing to the canonical (`Superseded by: [skill-name]`).
 - **Delete**: Only if the skill is an exact duplicate with zero unique content. Requires explicit user confirmation.

6. **Check agent bindings**: Before archiving or deleting a skill, run:
 ```bash
 grep -rn "skill-name" ~/.claude/agents/*/AGENT.md
 ```
 If the skill is bound to an agent, update the agent's `skills:` list to reference the canonical skill instead.

7. **Output the deduplication report**.

8. **Apply changes only after user confirmation**: Present the report; wait for approval before moving or modifying any file.

## Checklist

- [ ] Full inventory built from frontmatter only (no full-body loads)
- [ ] Conflict clusters identified with at least 2 members each
- [ ] Canonical skill designated for each cluster with scoring rationale
- [ ] Disposition proposed for each non-canonical: merge / archive / redirect / delete
- [ ] Agent bindings checked before any archive/delete
- [ ] Changes queued but NOT applied without explicit user confirmation
- [ ] Archive destination (`~/.claude/skills/archive/`) exists or will be created
- [ ] No intentional layering (project-over-global) misidentified as duplication

## Common issues & anti-patterns

- **Deleting without checking agent bindings**: An agent that references a deleted skill will silently fail to load its procedure.
- **Archiving the more complete skill**: The newer numbered skill is not always the better one — score on completeness, not recency alone.
- **Treating specialisation as duplication**: `sql-query-review` and `technical-writing-review` both "review" something but are not duplicates.
- **Merging incompatible procedures**: Two skills that review the same domain but with different audiences (developer vs. executive) should not be merged — they serve different callers.
- **Silent name collision**: Two skills with names `product-review` and `product-requirements-review` may seem overlapping but may be intentionally distinct. Check description scope before clustering.
- **Not updating agent bindings after rename**: Renaming a canonical skill without grep-checking agents leaves stale references.

## Required output

```
## Skill Deduplication Report

Scan date: [date]
Skills scanned: [count]
Conflict clusters found: [count]

### Cluster [N]: [domain / verb]

| Skill name | Skill # | Completeness | Specificity | Ref count | Role |
|---|---|---|---|---|---|
| [name] | [#] | H/M/L | H/M/L | [n] | CANONICAL |
| [name] | [#] | H/M/L | H/M/L | [n] | [merge/archive/redirect/delete] |

Canonical rationale: [one sentence]
Unique content in non-canonical (to merge): [list or "none"]
Agent binding impact: [list agents that reference non-canonical, or "none"]

---

### Proposed actions (awaiting confirmation)

| Action | Skill | Details |
|---|---|---|
| archive | [name] | Move to ~/.claude/skills/archive/ |
| redirect | [name] | Add "Superseded by: [canonical]" to SKILL.md |
| merge | [name] → [canonical] | Merge section: [section name] |
| delete | [name] | Exact duplicate, no unique content — CONFIRM |

### No action needed
[List skills reviewed with no conflict]
```

## Safety

- Do not delete or archive any skill without explicit user confirmation per skill.
- Do not modify agent AGENT.md files during the scan phase — propose changes in the report only.
- Back up any file before overwriting: `cp SKILL.md SKILL.md.bak` before merge operations.
- Do not merge skills if their procedures would conflict — propose a manual review instead.

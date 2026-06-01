---
name: skill-deduplication
description: Use when you need to detect duplicate and overlapping skills, choose canonical versions, and document deferred alternatives.
---

# Skill Deduplication

## Purpose

Scan the installed skill library for functional overlap, name collisions, and redundant coverage. For each conflict cluster, designate one canonical skill, propose a disposition for each duplicate (merge, archive, redirect, delete), and produce a deduplication report. Nothing is deleted or moved without explicit per-skill user confirmation, and agent bindings are checked before any disposition so no agent loses the procedure it references.

## When to use

- The skill count has grown to the point where routing is ambiguous (a task could match 2+ skills).
- A new skill has been installed and its description overlaps with an existing skill.
- After a batch import of skills from a new source, before activating them.
- A user reports the wrong skill was invoked — the root cause may be overlapping descriptions.
- A periodic housekeeping audit is being run on the skill library.

## When not to use

- The goal is to find the right skill for a task — use `71-skill-librarian`.
- Only one or two specific skills need comparing — compare them directly without the full scan.
- The overlap is intentional (a project-scoped skill that shadows a global one for a specific context) — do not deduplicate intentional layering.
- The goal is to route a task to an agent — use `73-skill-to-agent-router`.

## Procedure

1. **Build the skill inventory.** Scan all SKILL.md files and read only the `name:` and `description:` frontmatter. Build a flat list: `[number, name, description_text]`.
2. **Cluster by semantic similarity.** Group skills whose descriptions or names share a core verb-object pair. Conflict signals: same verb + same domain ("review … requirements" in two skills); same noun + synonymous verb ("audit" vs "inspect" on the same subject); name collision (differ only by hyphen/underscore or plural).
3. **Score each cluster.** Score each skill on specificity (more specific = better canonical), completeness of the SKILL.md body (fuller procedure = better), installation recency (newer number = more likely current), and reference count (how many agents or skills reference this name).
4. **Designate the canonical skill.** The highest-scoring skill in each cluster is canonical. Document the rationale.
5. **Propose a disposition for each non-canonical skill:** *merge* (pull unique sections into the canonical), *archive* (move to `~/.claude/skills/archive/`, keep for traceability), *redirect* (add `Superseded by: [skill-name]` note), or *delete* (only for an exact duplicate with zero unique content — requires explicit confirmation).
6. **Check agent bindings before any archive/delete** (see Commands). If a skill is bound to an agent, update the agent's `skills:` list to reference the canonical skill instead.
7. **Output the deduplication report.**
8. **Apply changes only after user confirmation.** Present the report; wait for approval before moving or modifying any file.

## Concrete checks

- [ ] Full inventory built from frontmatter only (no full-body loads).
- [ ] Conflict clusters identified with at least 2 members each.
- [ ] Canonical skill designated for each cluster with scoring rationale.
- [ ] Disposition proposed for each non-canonical: merge / archive / redirect / delete.
- [ ] Agent bindings checked before any archive or delete.
- [ ] Changes queued but NOT applied without explicit user confirmation.
- [ ] Archive destination (`~/.claude/skills/archive/`) exists or is created first.
- [ ] No intentional layering (project-over-global) misidentified as duplication.
- [ ] Every file backed up (`cp SKILL.md SKILL.md.bak`) before any merge edit.

## Commands or Templates

```bash
# Inventory: name + description per skill, paired onto one line
grep -rn "^name:\|^description:" ~/.claude/skills/*/SKILL.md | \
  awk -F: '{print $1, $3}' | paste - -

# Find candidate name collisions (differ by plural/hyphen)
grep -rh "^name:" ~/.claude/skills/*/SKILL.md | sort | \
  sed 's/s$//' | uniq -d

# Check agent bindings before archiving/deleting a skill
grep -rn "skill-name" ~/.claude/agents/*/AGENT.md

# Body completeness signal (line count) to break a canonical tie
for d in ~/.claude/skills/*/; do
  printf "%5s  %s\n" "$(wc -l < "$d/SKILL.md")" "$(basename "$d")"
done | sort -n
```

```
## Skill Deduplication Report

Scan date: [date]   Skills scanned: [count]   Conflict clusters: [count]

### Cluster [N]: [domain / verb]
| Skill name | # | Completeness | Specificity | Refs | Role |
|------------|---|--------------|-------------|------|------|
| [name]     |[#]| H/M/L        | H/M/L       | [n]  | CANONICAL |
| [name]     |[#]| H/M/L        | H/M/L       | [n]  | [merge/archive/redirect/delete] |
Canonical rationale: [one sentence]
Unique content to merge: [list or "none"]
Agent binding impact: [agents referencing non-canonical, or "none"]

### Proposed actions (awaiting confirmation)
| Action   | Skill | Details |
|----------|-------|---------|
| archive  | [name]| Move to ~/.claude/skills/archive/ |
| redirect | [name]| Add "Superseded by: [canonical]" |
| merge    | [name] → [canonical] | Merge section: [name] |
| delete   | [name]| Exact duplicate — CONFIRM |

### No action needed
[skills reviewed with no conflict]
```

## Worked cluster example

The inventory surfaces three skills whose descriptions all contain "review … API":

- `12-api-and-interface-design` — "designing stable APIs, module boundaries, type contracts, REST/GraphQL endpoints". Body: full procedure, 200+ lines.
- `55-api-test-suite-review` — "review API test coverage, contract tests, request/response assertions". Body: full, test-focused.
- `96-api-design-principles` — "API design principles, naming, versioning, idempotency". Body: shorter, principle list.

Clustering check: do they share a core verb-object? `12` and `96` both cover API *design*; `55` covers API *testing* — a different action. So `55` is **not** in the cluster (specialisation, not duplication). Within the `12`/`96` cluster, score: `12` is more complete and more canonical (lower number, broader and deeper), `96` is a narrower principles reference.

Disposition: keep `12` **canonical**; for `96`, propose **redirect** (add `Superseded for design workflows by: 12-api-and-interface-design`, but keep it as a quick principles reference) rather than archive, because it has unique content (the idempotency/versioning checklist) that is not in `12`. Before any change, `grep -rn "api-design-principles" ~/.claude/agents/` confirms whether an agent binds `96` directly. The lesson: synonymous descriptions are a *signal* to investigate, not proof of duplication — the action verb and the unique content decide.

## Common issues & anti-patterns

- **Deleting without checking agent bindings.** An agent referencing a deleted skill silently fails to load its procedure.
- **Archiving the more complete skill.** The newer numbered skill is not always better — score on completeness, not recency alone.
- **Treating specialisation as duplication.** `sql-query-review` and `technical-writing-review` both "review" but are not duplicates.
- **Merging incompatible procedures.** Two skills reviewing the same domain for different audiences (developer vs. executive) serve different callers; do not merge.
- **Silent name collision.** `product-review` vs `product-requirements-review` may be intentionally distinct — check description scope before clustering.
- **Not updating bindings after rename.** Renaming a canonical skill without grep-checking agents leaves stale references.
- **No backup before merge.** Overwriting a SKILL.md during merge without `.bak` loses recoverable content.
- **Clustering on shared words, not shared purpose.** "review" appears in dozens of skills; the verb-object *pair* plus the action verb is what clusters, not a single common word.
- **Applying changes inside the scan.** The scan phase is read-only; moving or editing files before the user approves the report conflates analysis with action.

## Verifying the scan before reporting

Before presenting the report, sanity-check the inventory itself:

- Confirm the count of scanned skills matches the directory count (`ls -d ~/.claude/skills/*/ | wc -l`); a mismatch means some frontmatter failed to parse and was skipped.
- Confirm each cluster has at least two members — a "cluster" of one is just a skill, not a conflict.
- Confirm every proposed archive/delete lists its agent-binding impact (even "none"), so no binding is silently orphaned.

A deduplication report is only trustworthy if the inventory it rests on is complete; a skill with malformed frontmatter that the scan skipped is exactly the kind of orphan that later causes ambiguous routing.

## Choosing the disposition

Once a cluster has a canonical skill, pick each non-canonical skill's fate by its unique content and its bindings:

| Has unique content? | Bound to an agent? | Disposition | Rationale |
|---------------------|--------------------|-------------|-----------|
| No (exact duplicate) | No | **delete** (confirm) | nothing is lost |
| No | Yes | **redirect** | keep the name resolvable so the binding still loads |
| Yes, small | Either | **merge** into canonical | fold the unique section in, then redirect/archive the shell |
| Yes, distinct audience | Either | **keep both** | not a duplicate — different caller |
| Yes, but stale/superseded | No | **archive** | preserve for traceability, exclude from routing |

Delete is the rarest outcome and always requires explicit confirmation; redirect is the safest default when an agent binding exists, because it keeps the name resolvable while pointing future use at the canonical skill. Never delete a skill that an agent binds without first updating that agent's `skills:` list, or the agent loses its procedure silently.

## Required output

Return the deduplication report block above: scan metadata, one table per conflict cluster with the canonical designation and per-skill role, an "awaiting confirmation" actions table, and a "no action needed" list. Every archive/delete must be marked as requiring explicit confirmation, and every affected agent binding must be listed.

## Safety

- Do not delete or archive any skill without explicit user confirmation per skill.
- Do not modify agent AGENT.md files during the scan phase — propose changes in the report only.
- Back up any file before overwriting (`cp SKILL.md SKILL.md.bak`) before a merge operation.
- Do not merge skills whose procedures would conflict — propose a manual review instead.
- Treat the dormant archive as read-only unless the disposition is an explicit, confirmed archive move.

## Completion criteria

Done means the inventory was built from frontmatter only, conflict clusters were scored, a canonical skill and a disposition were assigned per cluster, agent bindings were checked, and no file was moved or modified without explicit confirmation.

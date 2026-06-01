---
name: skill-librarian
description: Use when you need to search, select, and recommend at most five relevant skills without activating the whole archive.
---

# Skill Librarian

## Purpose

Search the installed skill library and the agent roster to identify and recommend the best-fit skills for a given task. Return at most 5 recommendations with clear rationale, distinguishing primary matches from fallbacks. Never load or activate dormant skills unnecessarily — surface them by name and description only. The library is large (90+ skills), so the operation must stay index-only: read frontmatter, never bulk-load full SKILL.md bodies.

## When to use

- A user or agent asks "which skill should I use for X?"
- A task description does not map obviously to a single skill and a selection is needed.
- A new agent is being configured and its `skills:` binding list needs populating.
- An orchestrator is routing a subtask and needs the canonical skill for a domain.
- You need to confirm a skill exists before referencing it in a workflow.

## When not to use

- The correct skill is already known — skip the librarian and invoke it directly.
- The task requires creating a new skill — use `skill-creator` (anthropic-skills).
- The task requires detecting duplicate or overlapping skills — use `72-skill-deduplication`.
- The user wants to route a task to an agent, not a skill — use `73-skill-to-agent-router`.

## Procedure

1. **Parse the task description.** Extract the domain (product, engineering, research, finance, writing, infra, skill-meta), the action type (review, generate, synthesize, audit, repair, route), and any constraints ("without touching the database", "for a non-technical audience").
2. **Scan the skill index.** Do NOT load all SKILL.md files. Read only the directory listing and the `name:` + `description:` frontmatter fields (see Commands).
3. **Match by domain and action.** Map the parsed task to the taxonomy: product/docs/research (60–69); skill-meta/installation (70–90); engineering/infra (look for "audit", "repair", "generator" in the name); writing/content ("technical-writing", "adr", "prd").
4. **Apply exclusion filters.** Exclude skills that are dormant archive entries, that overlap with a narrower skill already in the candidate list, or that require a tool/agent binding unavailable in the current context.
5. **Rank candidates.** Score each on domain match (0–3), action match (0–3), constraint compatibility (0–2), and recency/canonical status (0–2). Select the top 5 or fewer.
6. **Return the recommendation.** For each, state: skill name, skill number, one-sentence rationale, and whether it is a primary match or a secondary/fallback.
7. **State what was not loaded.** Confirm no dormant skill families were bulk-activated.

## Concrete checks

- [ ] Task domain and action parsed before scanning.
- [ ] Only `name:` and `description:` fields read — no full SKILL.md bodies loaded.
- [ ] Candidate list trimmed to 5 or fewer.
- [ ] Each recommendation has a one-sentence rationale.
- [ ] Primary vs. secondary/fallback distinction made for every recommendation.
- [ ] Dormant archive not bulk-loaded into context.
- [ ] If no skill matches, that is stated explicitly — no hallucinated skill name.
- [ ] Skill numbers referenced match the actual on-disk directory prefix.

## Commands or Templates

```bash
# Index scan: read ONLY frontmatter name + description from each skill
for d in ~/.claude/skills/*/; do
  grep -m2 "^name:\|^description:" "$d/SKILL.md" 2>/dev/null
  echo "---"
done

# Keyword pre-filter across descriptions (narrow before ranking)
grep -rin "playwright\|e2e\|browser" ~/.claude/skills/*/SKILL.md | grep "description:"

# Confirm a specific skill name exists before recommending it
ls -d ~/.claude/skills/*/ | grep -i "security-and-secrets" || echo "no matching skill"
```

```
## Skill Librarian Result

Task: [parsed task description]
Domain: [domain]   Action: [action]

### Recommendations (ranked)
1. **[skill-name]** (skill-NN)
   Match: [Primary / Secondary]
   Rationale: [one sentence]
2. **[skill-name]** (skill-NN)
   ...
[Up to 5 entries]

### Not recommended (with reason)
- [skill-name]: [why excluded]

### Archive not loaded
Dormant skills were not bulk-activated. Archive families scanned by name only: [list if applicable].
```

## Scoring rubric in practice

The four-axis score (domain 0–3, action 0–3, constraint 0–2, recency 0–2) breaks ties between near-matches. Apply it explicitly:

| Axis | 0 | 1–2 | 3 (max where applicable) |
|------|---|-----|--------------------------|
| Domain match | different domain | adjacent domain | exact domain |
| Action match | different verb | related verb (audit≈review) | exact verb |
| Constraint fit | violates a stated constraint | partially compatible | fully compatible |
| Recency/canonical | superseded/archived | older but valid | current canonical |

A candidate that scores 0 on domain or violates a hard constraint is excluded outright, regardless of its other scores — relevance on the wrong domain is noise.

## Worked example

Task: "review our CI workflow for secret leaks before we make the repo public." Parsed domain: devops + security (cross-domain). Action: review/audit. Constraint: read-only, pre-publication.

Index scan surfaces candidates. Scoring:
- `58-ci-cd-pipeline-review` — domain 3 (CI), action 3 (review), constraint 2, recency 2 → **Primary**.
- `47-security-and-secrets-review` — domain 3 (secrets), action 3, constraint 2, recency 2 → **Primary** (the task explicitly names secret leaks).
- `50-dependency-supply-chain-review` — domain 1 (adjacent), action 2 → Secondary, only if dependencies are in scope.
- `52-smoke-test-and-repair` — domain 0 for this ask → excluded (it runs gates, it does not audit secrets).

Result: recommend running 58 and 47 together (58 for workflow trigger/permission hygiene, 47 for the committed-secret scan), with a one-line note that they are complementary, not interchangeable. Two primaries are acceptable when the task genuinely spans two domains; the chain order is 47 first (a committed live secret blocks publication) then 58.

## Common issues & anti-patterns

- **Loading full SKILL.md bodies for 90 skills to find one match.** Wastes context. Use the index-scan approach (frontmatter only).
- **Recommending a skill by approximate name.** "I think there's a skill called `product-review`…" — verify the exact `name:` value before recommending.
- **Recommending more than 5 skills.** Decision paralysis. Pick the best 5; if the task is genuinely multi-domain, recommend a sequential chain instead.
- **Not distinguishing primary from fallback.** "Use any of these" leaves the caller no better off.
- **Recommending dormant archive skills for live tasks.** Archive skills exist for traceability; they are not active candidates unless explicitly requested.
- **Missing the meta-skill option.** If the task is about skills themselves (deduplicate, audit, route), the answer is almost always within skills 70–79.
- **Inventing a skill number.** Referencing `skill-58` for a security task when 58 is a CI skill misleads the caller; confirm against the directory.
- **Recommending by recency alone.** A higher number is not automatically the better fit; score on domain and action match, not install order.
- **Ignoring stated constraints.** If the user said "for a non-technical audience", a developer-facing review skill scores 0 on constraint fit and should not lead.
- **Padding the list to five.** If only two skills genuinely fit, recommend two. Five weak recommendations are worse than two strong ones.

## Quick taxonomy reference

A fast mental index for the common domains (confirm exact names against the directory before recommending):

- 01–39: engineering, diagnostics, architecture, UI/UX, database, runtime.
- 40–46: AI/agent systems — workflow design, governance, prompts, RAG, evaluation.
- 47–57: security and testing/QA — secrets, authz, dependencies, smoke, e2e, regression.
- 58–62: devops/release — CI/CD, build, deploy preflight, release notes, handoff.
- 63–70: product/docs/research — specs, execution prompts, PRD, market, pricing, ADR.
- 71–90: skill-library meta and installation — librarian, dedup, routing, audits, path hygiene.

## Handling no match and partial match

The honest answer is sometimes "no skill fits". Do not stretch a loosely related skill to fill the gap:

- **No match.** If the scan surfaces nothing scoring 2+ on domain, state "no matching skill found" and suggest `skill-creator` (anthropic-skills) to author one. Inventing `data-pipeline-review` because it "sounds right" sends the caller to a nonexistent file.
- **Partial match.** A skill covers part of the task. Recommend it, but name the uncovered portion explicitly: "`84-analytics-tracking-review` covers the event schema, but nothing covers the consent-banner copy — that part has no skill." This lets the caller decide rather than assuming full coverage.
- **Over-broad task.** "Review my whole app" maps to a dozen skills. Do not list all twelve; ask for the highest-priority concern, or recommend a short ordered chain (diagnostics → architecture → security) capped at five.

When in doubt between two near-equal candidates, prefer the more specific one as Primary and list the broader one as Secondary — a narrow skill that exactly fits beats a general skill that mostly fits.

## Required output

Return the result block above: the parsed task with domain/action, a ranked list of at most 5 recommendations each tagged Primary or Secondary with a one-sentence rationale, a "not recommended" list with reasons, and an explicit confirmation that the dormant archive was not bulk-loaded. If nothing matches, say so and suggest `skill-creator`.

## Safety

- Do not activate or load dormant skill archive entries into context unless the user explicitly requests it.
- Do not invent skill names. If a needed skill does not exist, state "no matching skill found — consider creating one with `skill-creator`."
- Do not modify any SKILL.md file during a librarian query — this is a read-only operation.
- Do not recommend a skill whose required tool or agent binding is unavailable in the current context without flagging that gap.

## Completion criteria

Done means the task was parsed, the index was scanned by frontmatter only, at most 5 candidates were ranked and tagged primary/secondary with rationale, exclusions were justified, and the dormant archive was confirmed not bulk-loaded.

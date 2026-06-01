---
name: docs-quality-review
description: Use when you need to review documentation for quality — technical accuracy against the code, audience fit, terminology and style consistency, broken internal/external links, and whether every example actually runs.
---

# Docs Quality Review

## Purpose

Run a structured quality review of existing documentation and report concrete, file-and-line findings. Check five dimensions: accuracy (does the doc match the current code/behavior), audience fit (is the depth and assumed knowledge right for the stated reader), terminology and style consistency (one term per concept, consistent voice), link health (no 404s, no dead anchors), and example integrity (every command/code block actually runs and produces the shown output). This is a read-and-verify skill: it surfaces defects and prioritizes fixes; it does not silently rewrite prose.

## When to use

- Before a release or public launch, to catch stale, broken, or misleading docs.
- After a refactor or API change that may have invalidated existing docs.
- Onboarding feedback shows readers getting stuck or misled.
- Auditing a docs site for broken links and unrunnable examples.
- Establishing a recurring docs-quality gate.

## When not to use

- The doc does not exist yet — write it first (use the relevant authoring skill).
- The task is to author/restructure, not assess (use readme-and-docs-structure or tutorial-and-how-to-writing).
- A single obvious typo where a direct edit is faster than a review pass.

## Procedure

### 1. Inventory docs and define the intended audience

```bash
# All doc sources
find . \( -name "*.md" -o -name "*.rst" -o -name "*.mdx" \) \
  -not -path './node_modules/*' -not -path './.git/*' | sort

# Heading outline per file (spot skipped levels / missing structure)
for f in $(find docs README.md -name '*.md' 2>/dev/null); do
  echo "== $f =="; grep -nE '^#{1,6} ' "$f"
done
```

### 2. Check technical accuracy against the code

Spot-check documented commands, flags, config keys, endpoints, and defaults against the actual source. Any claim that contradicts the code is a defect.

```bash
# Do documented CLI flags still exist?
grep -oE '\-\-[a-z][a-z0-9-]+' docs/**/*.md | sort -u > /tmp/doc_flags.txt
<your-cli> --help | grep -oE '\-\-[a-z][a-z0-9-]+' | sort -u > /tmp/real_flags.txt
comm -23 /tmp/doc_flags.txt /tmp/real_flags.txt   # documented but not real

# Do documented env vars still exist in code/config?
grep -rhoE '\b[A-Z][A-Z0-9_]{3,}\b' docs/ | sort -u | head -40
```

### 3. Verify every example runs

Execute each fenced command/code block in a clean throwaway environment and compare to the shown output.

```bash
# Extract fenced code blocks for review/execution
awk '/^```/{f=!f; next} f' README.md
# Run each in a sandbox; record exit code and diff vs documented output
( cd "$(mktemp -d)" && set -e; <example-commands> ); echo "exit: $?"
```

### 4. Check link health

```bash
# Internal + external link checking
npx --yes markdown-link-check -q README.md
lychee --no-progress docs/ README.md 2>/dev/null || true

# Anchor links that point to non-existent headings (common after edits)
grep -rnoE '\]\(#[a-z0-9-]+\)' docs/ | head -40
```

### 5. Check terminology and style consistency

Flag the same concept named multiple ways, inconsistent product/feature casing, and voice drift. Build a small term map and grep for violations.

```bash
# Example: detect mixed spellings/casing of one concept
grep -rniE 'api[- ]?key|apikey' docs/ | sort | uniq -c   # pick ONE canonical form
grep -rnE '\b(e\.g\.|eg|ie|i\.e\.)\b' docs/                # punctuation consistency
```

### 6. Assess audience fit and prioritize findings

Confirm the document's depth matches its stated reader (a beginner tutorial should not assume cluster admin knowledge). Rank findings: broken examples and inaccuracies (blocker) > dead links (high) > terminology/style (medium).

## Concrete checks

- [ ] Every documented command, flag, and config key still exists in the code.
- [ ] Documented defaults and behaviors match the implementation.
- [ ] Every fenced example was executed and exited successfully.
- [ ] Shown example output matches actual output (no stale results).
- [ ] No internal links or heading anchors are broken.
- [ ] No external links return 4xx/5xx.
- [ ] One canonical term per concept; casing of product/feature names is consistent.
- [ ] Voice and person are consistent within a document.
- [ ] Heading levels are sequential (no skipped levels).
- [ ] The document's depth matches its stated audience.
- [ ] No secrets, real tokens, or absolute machine paths appear in examples.
- [ ] No "TODO"/"coming soon"/placeholder text ships in published docs.

## Commands

```bash
# Link check across the docs tree
lychee --no-progress docs/ README.md

# Markdown lint (structure, heading levels, list style)
npx --yes markdownlint-cli2 "docs/**/*.md" "README.md"

# Prose style/consistency (if configured)
vale docs/ 2>/dev/null || echo "vale not configured"

# Find placeholders left in published docs
grep -rniE 'TODO|FIXME|coming soon|tbd|lorem ipsum|xxx' docs/ README.md

# Find likely-leaked secrets or machine paths in examples
grep -rnE '(secret|token|password|api[_-]?key)\s*[=:]\s*["'\''][^"'\'' ]+' docs/ ; \
  grep -rnE '/Users/[^/ ]+|/home/[^/ ]+' docs/ README.md
```

## Common issues & anti-patterns

- Examples that were correct once but were never re-run after an API change.
- Documented flags/endpoints that no longer exist (or new ones never documented).
- Dead anchor links after headings were renamed.
- The same concept called three different names across pages.
- A "beginner" guide that silently assumes expert prerequisites.
- Output blocks pasted from an old version, contradicting current behavior.
- Reviewing prose feel while ignoring whether the commands actually run — accuracy first.
- Secrets or absolute machine paths copied into examples from a real terminal session.

## Required output

Produce a findings report: (1) accuracy defects (doc claim vs code reality, with file:line); (2) example results (each block: ran / exit code / output matches?); (3) link-check results (broken internal + external); (4) terminology/style inconsistencies; (5) audience-fit notes; (6) a prioritized fix list (blockers → high → medium). Do not rewrite the docs in this pass — report and recommend.

## Safety

- Read-only review by default; do not edit the docs being reviewed unless explicitly asked.
- Run examples only in a throwaway sandbox, never destructive commands against real systems.
- If a secret or absolute machine path is found in an example, redact it in the report and flag for removal/rotation — do not reproduce the value.
- Report findings with evidence (file:line); never assert a defect without locating it.

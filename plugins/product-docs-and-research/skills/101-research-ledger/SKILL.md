---
name: research-ledger
description: "Look up and record structured research findings before searching the web, preserving citations, dates, contradictions, and freshness classes (14/28/90 days) to prevent redundant queries."
---

# Research Ledger

## Purpose

Capture, index, and reuse structured research findings across projects and work sessions. The ledger enforces a lookup-first discipline before initiating external web queries or page fetches, eliminating redundant research costs, token usage, and latency. Every saved record retains its question, hierarchical topic, validated claims with evidence classes, source citations, contradictions, open questions, and a computed expiration date based on data volatility.

## When to use

- Before performing web searches, API documentation lookups, or third-party library evaluations.
- After completing research, to record findings, source citations, and conflicting evidence in a reusable format.
- When validating whether prior technical decisions, external tool pricing, or API specifications remain current.
- When reviewing research productivity, hit rates, and query coverage via ledger metrics.

## When not to use

- Private credentials, API keys, session tokens, or customer-identifying data (never store secrets in the ledger).
- Routine in-repo code inspection or static analysis (use local file navigation tools instead).
- Ephemeral conversational notes or intermediate scratchpad drafts that carry no reusable findings.
- Deep market thesis drafting or customer persona synthesis (use `market-research-synthesis` for full market reports).

## Freshness classes and date arithmetic

Research records decay at different rates depending on how rapidly the underlying facts change. The ledger categorizes each entry into one of three standardized freshness tiers:

| Freshness class | TTL | Scope and typical topics |
|---|---|---|
| `volatile` | 14 days | Model releases, API pricing, rate limits, token quotas, CLI flags, minor SDK releases, terms of service. |
| `moderate` | 28 days | Framework benchmarks, library comparisons, vendor evaluation matrices, workflow guides, competitor features. |
| `stable` | 90 days | Architectural RFCs, network protocols, data format specifications, core math/algorithms, foundational standards. |

Date arithmetic is executed deterministically in code at save time:
- The system reads `researched_on` (ISO 8601 date, defaulting to today in UTC).
- It calculates `valid_until = researched_on + TTL_DAYS`.
- During lookup, the record's `valid_until` is compared against current UTC date. Entries past their expiration are classified as `hit_stale`.

## Procedure

### 1. Query the ledger before researching

Always run a lookup before calling search engines, web scraping tools, or external APIs:

```bash
python3 scripts/research_ledger.py lookup "<question>" [--topic "<topic>"]
```

Inspect the returned JSON object and handle the status code:

1. **`hit_fresh`:** An exact or strong match exists within the same topic, product/provider identity, and version scope, and its expiration date has not passed. If the entity or scope differs, treat the result as `partial`. When scope matches, **do not perform external web queries** and directly consume the existing findings, claims, and citations.
2. **`hit_stale`:** A matching record exists but its validity period has expired (`valid_until < today`). Re-verify only the specific claims that may have changed (e.g., pricing or version numbers). Retain unchanged foundational facts.
3. **`partial`:** Related records or topical overlaps exist. Review existing findings to refine your query and narrow the scope of external investigation.
4. **`miss`:** No relevant records found in the ledger. Proceed with full external research.

### 2. Conduct external research and gather evidence

When a query results in `miss`, `partial`, or `hit_stale`, conduct targeted external lookups:
- Verify claims across primary documentation, official changelogs, or reputable benchmarks.
- Record exact URLs, titles, and unique source identifiers (`s1`, `s2`, ...).
- Note conflicting information across sources in the `contradictions` list.
- Explicitly note unresolved areas in `open_questions`.

### 3. Classify claims and evidence

Tag each finding with an explicit evidence class:
- `fact`: Verifiable objective data, test output, or official specification.
- `vendor`: Vendor claims, product marketing copy, or vendor-published roadmaps.
- `community`: Forum discussions, GitHub issues, or third-party blog reports.
- `inference`: Derived architectural conclusion, synthesis, or recommendation.

### 4. Save the normalized record

Structure the research result into a JSON payload and persist it using the ledger CLI:

```bash
python3 scripts/research_ledger.py save --json record.json
```

The script validates required fields, computes `valid_until` from the freshness tier, updates the SQLite database and full-text search index, and returns confirmation.

What save enforces:

- **Keys.** Each record's key ends in a hash of the whole normalized topic and question, so two different questions never share a key. Saving the same question again stores a new revision; earlier revisions stay in `research_revisions`.
- **Strict records.** Save rejects an unknown evidence class, a malformed or future date, an unknown freshness or confidence value, a duplicate source id, a `source_id` that names no source, and a `fact` without a source. A finding without a class counts as `inference`.
- **Verified or draft.** A record with findings and sources, where every finding cites a source, is `verified`. Anything else is saved as a `draft`, and a draft never comes back as `hit_fresh`, only as `partial`.
- **Current information.** A lookup asking for current information (today, current, latest, price, policy) returns `hit_stale` unless the record was researched today. `lookup --revalidate` does the same on request.
- **Upgrading.** `research_ledger.py migrate` previews moving a database written by an earlier release to these keys; `migrate --apply` backs the database up first, refuses on key conflicts and changes nothing on a second run.

## Record schema

```json
{
  "kind": "research",
  "question": "What are the token limits and pricing tiers for the target API?",
  "topic": "ai/apis/provider-limits",
  "freshness": "volatile",
  "researched_on": "2026-11-07",
  "confidence": "high",
  "findings": [
    {
      "claim": "Standard tier allows 10,000 requests per minute with pay-as-you-go billing.",
      "class": "fact",
      "source_ids": ["s1"],
      "as_of": "2026-11-07"
    }
  ],
  "sources": [
    {
      "id": "s1",
      "title": "Provider Rate Limits and Pricing Documentation",
      "url": "https://api.example.com/docs/rate-limits"
    }
  ],
  "contradictions": [],
  "open_questions": [
    "Enterprise throughput discounts for sustained monthly volumes above 50M tokens."
  ],
  "supersedes": null,
  "projects": ["web-platform"],
  "plan_items": ["TASK-102"]
}
```

## Commands

```bash
# Set custom database or stats locations (optional; defaults to ~/.research-ledger/)
export RESEARCH_LEDGER_DB="$HOME/.research-ledger/ledger.db"
export RESEARCH_LEDGER_STATS="$HOME/.research-ledger/stats.json"

# Look up prior research before searching the web
python3 scripts/research_ledger.py lookup "Postgres JSONB index performance vs regular column"
python3 scripts/research_ledger.py lookup "Vite build worker configuration" --topic "frontend/bundlers"

# Save research from a file
python3 scripts/research_ledger.py save --json path/to/record.json

# Save research piped directly from stdin
cat <<'EOF' | python3 scripts/research_ledger.py save --json -
{
  "question": "Does Node.js test runner support mock timers natively?",
  "topic": "nodejs/testing",
  "freshness": "moderate",
  "confidence": "high",
  "findings": [
    {
      "claim": "node:test provides mock.timers with enable(), tick(), and reset().",
      "class": "fact",
      "source_ids": ["s1"],
      "as_of": "2026-11-07"
    }
  ],
  "sources": [
    {
      "id": "s1",
      "title": "Node.js Test Runner Documentation",
      "url": "https://nodejs.org/api/test.html#mock-timers"
    }
  ]
}
EOF

# Display daily query performance metrics and hit ratios
python3 scripts/research_ledger.py stats
```

## Common anti-patterns

- **Searching before lookup:** Running web searches or fetching documentation without checking the ledger first causes duplicated effort and token expenditure.
- **Overestimating freshness:** Marking volatile API pricing, release schedules, or library versions as `stable` (90 days) leads to acting on stale constraints.
- **Unattributed findings:** Recording claims without citing source identifiers or URLs prevents subsequent verification.
- **Hiding contradictions:** Suppressing contradictory benchmark numbers or conflicting documentation leaves downstream plans vulnerable to unexpected failures.
- **Ignoring stale hits:** Repeating full research on a `hit_stale` rather than isolating and re-verifying only the outdated claims.
- **Storing sensitive secrets:** Writing API keys, passwords, or customer data into research records.

## Related skills

- `market-research-synthesis`: Use when aggregating large multi-source industry research into a structured market analysis.
- `product-requirements-review`: Use when translating verified research claims into product requirement documents.
- `technical-writing-review`: Use when incorporating researched findings into public documentation or architecture decision logs.
- `cost-control-token-review`: Use when auditing research queries to minimize external token and API consumption.

## Completion criteria

1. **Pre-lookup completed:** `research_ledger.py lookup` was executed for the question prior to any web queries.
2. **Hit triage respected:** If `hit_fresh`, existing findings were reused without web lookups. If `hit_stale`, only outdated claims were refreshed.
3. **Citations verified:** All new findings include verifiable sources, evidence classification (`fact`, `vendor`, `community`, `inference`), and the date of verification.
4. **Freshness assigned:** The entry uses the correct freshness class (`volatile` 14d, `moderate` 28d, or `stable` 90d) with `valid_until` calculated automatically in code.
5. **Record persisted:** The normalized JSON record is saved into the ledger via `research_ledger.py save --json <file>`.

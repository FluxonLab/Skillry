---
name: llm-api-cost-optimization
description: Use when you need to measure and reduce LLM/API spend with concrete tactics — per-call token instrumentation, prompt caching, model tiering (cheap vs. premium), request batching, context trimming, and a cost-per-request dashboard. Focuses on measurement plus implementable changes.
---

# LLM API Cost Optimization

## Purpose

Cut LLM/API spend with measured, implementable changes rather than slogans. This skill is measurement-first: it instruments input/output/cached tokens and cost per request, then applies concrete tactics — prompt caching (stable prefix ordering, cache-read vs. cache-write accounting), model tiering (route easy work to a cheap small model, hard work to a premium model), request batching, and context trimming/summarization. It complements a generic token-cost audit by focusing on the engineering: the code changes and the dashboard that prove savings. The output is a per-request cost breakdown with applied tactics and a measured before/after, with quality held constant.

## When to use

- Monthly LLM spend is rising and per-request cost is not instrumented, so the driver is unknown.
- A prompt has a large stable prefix (system prompt, tools, few-shot, retrieved context) that is re-sent every call uncached.
- Every request uses a premium model even though many are simple classification/extraction tasks a small model could handle.
- Many independent, latency-tolerant requests run one at a time and could be batched.
- Context windows are stuffed with full history or whole documents when a fraction would suffice.

## When not to use

- The driver is GPU/self-hosted compute, not per-token API billing — that is cloud spend review territory.
- The system is a low-volume prototype where the optimization effort exceeds the spend.
- The proposed saving degrades answer quality below the bar — a cheaper wrong answer is not a saving; gate every change on an eval.

## Procedure

1. **Instrument per-call token usage first.** Log `input_tokens`, `output_tokens`, `cache_read_tokens`, and `cache_write_tokens` (or the provider's equivalents) plus model and feature/route for every call. You cannot optimize what you do not measure; high-level monthly totals are insufficient.
2. **Build the cost-per-request breakdown.** Multiply each token category by its price (cached reads are far cheaper than fresh input; output is usually the priciest) and group by feature, model, and route. Find the top cost drivers — usually a few endpoints dominate.
3. **Apply prompt caching to stable prefixes.** Order the prompt so the unchanging parts (system prompt, tool definitions, few-shot, large retrieved context) come first and are marked cacheable; put the volatile user turn last. Then verify cache-read tokens rise and cache-write happens only on the first call.
4. **Tier the model to the task.** Route simple, well-bounded tasks (classification, extraction, routing, short rewrites) to a small/cheap model and reserve the premium model for genuinely hard reasoning. Measure quality per route so tiering does not silently regress accuracy.
5. **Batch independent, latency-tolerant work.** For backfills, evals, and bulk generation, use the provider's batch API or concurrent batching to cut per-request overhead and often unit price. Reserve real-time models for interactive paths.
6. **Trim and summarize context.** Send only the tokens that change the answer: retrieve top-k instead of whole documents, summarize or window long histories, and drop dead system text. Output tokens cost most, so cap `max_tokens` and ask for concise formats where appropriate.
7. **Stand up a cost dashboard and re-measure.** Aggregate the per-call logs into cost-per-request, cache hit rate, and spend-by-feature over time, and confirm each tactic moved the number without dropping eval scores.

## Concrete checks

- [ ] Every LLM call logs input/output/cache-read/cache-write tokens plus model and feature/route.
- [ ] Cost per request is computed per token category and grouped by feature/model/route.
- [ ] The stable prompt prefix is ordered first and marked cacheable; the volatile turn is last.
- [ ] Cache hit rate (cache-read / total input) is measured and is high for repetitive workloads.
- [ ] A model-tiering policy exists: simple tasks on a small model, hard tasks on a premium model.
- [ ] Each tiered route has a quality/eval check so cost cuts do not silently degrade accuracy.
- [ ] Batchable, latency-tolerant jobs use a batch path, not the real-time endpoint.
- [ ] Context is trimmed to relevant tokens (top-k retrieval, summarized history), not whole documents.
- [ ] `max_tokens` is bounded and output format is as concise as the task allows.
- [ ] Retries on long generations are capped and do not re-pay for full completions on every attempt.
- [ ] Few-shot examples are pruned to the minimum that preserves quality (no redundant examples).
- [ ] A dashboard tracks cost-per-request, cache hit rate, and spend-by-feature over time.

## Commands or Templates

```python
# 1) Per-call cost instrumentation — log every category, then aggregate
# Prices are illustrative ($ per 1M tokens); read current provider pricing.
PRICE = {  # model: (input, cached_input, output)
    "small":   (0.80, 0.08, 4.00),
    "premium": (15.00, 1.50, 75.00),
}
def call_cost(model, usage):
    pin, pcache, pout = PRICE[model]
    fresh_in = usage["input_tokens"] - usage.get("cache_read_tokens", 0)
    cost = (
        fresh_in / 1e6 * pin
        + usage.get("cache_read_tokens", 0) / 1e6 * pcache
        + usage["output_tokens"] / 1e6 * pout
    )
    log.info("llm_cost", extra={
        "model": model, "feature": current_feature(),
        "input": usage["input_tokens"], "output": usage["output_tokens"],
        "cache_read": usage.get("cache_read_tokens", 0), "usd": round(cost, 6),
    })
    return cost
```

```python
# 2) Prompt caching: stable prefix first (cacheable), volatile turn last
messages = [
    {"role": "system", "content": SYSTEM_PROMPT},          # stable -> cache
    {"role": "user",   "content": FEW_SHOT_AND_CONTEXT},   # stable -> cache
    {"role": "user",   "content": user_question},          # volatile, not cached
]
# Mark the long stable block as a cache breakpoint per the provider's API.
# After deploy, confirm: cache_write on first call, cache_read on subsequent calls.
```

```python
# 3) Model tiering: cheap model for simple tasks, premium for hard ones
def route_model(task):
    if task.kind in {"classify", "extract", "route", "short_rewrite"}:
        return "small"
    if task.tokens_in < 1500 and not task.needs_deep_reasoning:
        return "small"
    return "premium"
# Pair with an eval set per route so a downgrade that hurts quality is caught.
```

```sql
-- 4) Cost dashboard query over the per-call logs (cost_log table)
SELECT feature, model,
       count(*)                          AS calls,
       round(sum(usd), 2)                AS spend_usd,
       round(sum(usd) / count(*), 5)     AS usd_per_call,
       round(100.0 * sum(cache_read) / nullif(sum(input_tokens),0), 1) AS cache_hit_pct
FROM cost_log
WHERE ts > now() - interval '7 days'
GROUP BY feature, model
ORDER BY spend_usd DESC;
```

```python
# 5) Batch independent, latency-tolerant work instead of one real-time call each.
# A batch/offline path typically costs less per unit and removes per-call overhead;
# use it for backfills, evals, and bulk generation — never for interactive paths.
def submit_batch(jobs):
    requests = [
        {"custom_id": j.id, "model": route_model(j), "max_tokens": j.cap,
         "messages": build_messages(j)}
        for j in jobs
    ]
    return batch_client.create(requests=requests)   # poll for results asynchronously

# 6) Context trimming: send top-k retrieved chunks, not whole documents.
def trim_context(chunks, k=5, max_chars=6000):
    selected, total = [], 0
    for c in sorted(chunks, key=lambda c: c.score, reverse=True)[:k]:
        if total + len(c.text) > max_chars:
            break
        selected.append(c.text); total += len(c.text)
    return "\n---\n".join(selected)
```

## Common issues & anti-patterns

- **Optimizing blind.** Cutting model size or prompt length without per-call token logging is guessing; instrument first.
- **Cache-busting prefixes.** Putting a timestamp, request ID, or the user turn at the top of the prompt invalidates the cache every call, so cache-read stays at zero.
- **Tiering without an eval.** Routing hard tasks to a small model to save money quietly tanks accuracy; gate every route on a quality check.
- **Using the real-time endpoint for bulk jobs.** Backfills and evals on the interactive path cost more and add no latency benefit; batch them.
- **Stuffing the whole document/history.** Sending full context when top-k retrieval or a summary would do inflates the priciest tokens.
- **Ignoring output cost.** Output tokens often cost several times input; unbounded `max_tokens` and verbose formats dominate the bill.
- **Counting savings without re-measuring.** Claiming a reduction without the dashboard showing lower cost-per-request (at equal quality) is unverified.
- **Caching volatile or sensitive prefixes.** Caching content that legitimately changes per user returns stale or cross-user output.
- **Retrying full generations on transient errors.** Re-running a long completion from scratch on every retry doubles cost; cap retries and prefer idempotent, resumable calls.
- **Few-shot bloat.** Carrying ten redundant examples when two suffice pays for the same tokens on every call; prune the prompt to the minimum that holds quality.
- **Ignoring streaming for early-exit cases.** When a caller often stops reading early, streaming with an early cancel avoids paying for output tokens that are never used.
- **No per-feature cost ownership.** Spend with no feature/team attribution has no owner, so nobody is accountable when a feature's cost balloons.

## Required output

Produce a report containing:
1. **Cost baseline** — cost-per-request and total spend grouped by feature/model/route, with the top drivers ranked.
2. **Token breakdown** — input/output/cache-read/cache-write split and current cache hit rate per high-cost path.
3. **Applied tactics** — per driver: caching, tiering, batching, or context trimming, with the concrete code/config change.
4. **Quality guard** — the eval/quality check for each tiered or trimmed route and its result.
5. **Before/after** — measured cost-per-request and monthly projection before and after, with the dashboard query/source.
6. **Next safe action** — the single highest-saving change still outstanding.

## Safety

- Never log raw prompt or completion content with token counts unless redacted; prompts and outputs routinely contain secrets and PII.
- Do not enable prompt caching on prefixes that vary per user or contain another user's data — verify cache scope to avoid cross-user leakage.
- Treat pricing in any template as illustrative; confirm current provider pricing before projecting savings.
- Gate every cost-cutting change behind an eval; do not ship a downgrade that drops quality below the agreed bar.
- Do not switch production models or routing without approval and a rollback path; model changes alter behavior, not just cost.
- Keep cost logs access-controlled; per-feature spend can reveal sensitive product and usage information.

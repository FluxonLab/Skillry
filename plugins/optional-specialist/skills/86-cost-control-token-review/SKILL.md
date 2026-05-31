---
name: cost-control-token-review
description: Use when you need to review token, runtime, model, API, hosting, and subagent fanout cost controls.
---

# Cost Control Token Review

## Purpose

Audit an AI system's token consumption, model selection, caching strategy, batch API usage, context management, and subagent fanout for cost inefficiencies. Produces a quantified cost analysis with specific, implementable optimizations and projected monthly savings — not vague advice to "use smaller models."

## When to use

- Monthly API costs are higher than expected and the cause is not clear from high-level billing data.
- A new feature adds tools, retrieval, or subagent delegation and you need a cost impact assessment before shipping.
- The system is scaling and current per-query costs, when extrapolated to target volume, are unsustainable.
- Prompt caching is configured but cache hit rate is lower than expected (below 50% for repetitive workloads).
- A system sends many similar requests and the team wants to evaluate whether the Batch API would reduce costs.
- Subagent fanout is happening and nobody has modeled the token multiplication effect across the full workflow.
- A model tier change is being considered (e.g., Sonnet to Haiku, GPT-4o to GPT-4o-mini) and you need a cost/quality trade-off analysis.

## When not to use

- The cost is a one-time research or prototyping expense, not a recurring production cost.
- The problem is output quality or reliability — cost optimizations that degrade quality are not optimizations.
- The hosting cost question is about GPU compute infrastructure, not API token costs.
- Total monthly API cost is below the threshold where optimization work would pay back in reasonable time (e.g., less than $100/month).

## Procedure

1. **Establish the cost baseline.** Pull API usage logs or billing data for the last 30 days. Record for each model in use:
 - Total input tokens
 - Total output tokens
 - Total cached input tokens (if prompt caching is enabled)
 - Cache hit rate = cached_tokens / total_input_tokens
 - Cost per category at current pricing
 - Total cost

 If per-request token logging is not in place, instrument the application to log `input_tokens`, `output_tokens`, `cache_read_tokens`, and `cache_creation_tokens` per API call before proceeding. High-level monthly totals are not sufficient for optimization work.

2. **Identify the largest cost drivers.** From per-request token logs, rank request types by token consumption. For each of the top 5 request types by cost:
 - What is the average input token count?
 - What is the average output token count?
 - What fraction of total cost does this request type account for?
 - Is this request type a candidate for caching, batching, or model downgrade?
 The top 10-20% of request types by token consumption typically account for 60-80% of total costs. This is where optimization effort has the highest leverage.

3. **Audit prompt caching configuration.** Prompt caching reduces input token cost for repeated content (system prompts, few-shot examples, static retrieval context):

 **For Anthropic models (claude-*):**
 - The cached prefix must be at least 1,024 tokens to be eligible for caching
 - The `cache_control: {type: "ephemeral"}` breakpoint must be placed at the end of the stable content block, before any variable content (user query, dynamic retrieved chunks)
 - Variable content (timestamps, user names, session IDs) in the system prompt prevents caching — move all variable content after the cache breakpoint
 - Cache hit rate below 50% for a system with a fixed system prompt indicates a configuration problem

 **For OpenAI models (gpt-4o-*, gpt-4-*):**
 - Caching is automatic for prompts with 1,024+ token prefixes that repeat across requests
 - Variable content in the system prompt breaks caching — audit what changes per request
 - Check the `cached_tokens` field in the API response to measure actual cache hits

4. **Review model selection per task type.** Map each request type to: the model currently used, the minimum model capability actually required, and the cost differential. Build a routing table:

 | Task type | Current model | Required capability | Recommended model | Monthly savings |
 |---|---|---|---|---|
 | Query classification | claude-3-5-sonnet | Simple classification | claude-3-5-haiku | -80% for this task |
 | Code generation | claude-3-5-sonnet | Complex reasoning | claude-3-5-sonnet | Keep |
 | Short extraction | gpt-4o | Simple extraction | gpt-4o-mini | -75% for this task |

 Do not recommend model downgrades without verifying quality on a representative sample. Downgrade only tasks where the smaller model's output quality is acceptable, not tasks where it saves money but produces worse results.

5. **Audit context window usage.** For each major request type:
 - What is the average total token count (input + output)?
 - What is the configured max context length?
 - What fraction of the configured context is actually used?
 - Is there a context accumulation pattern — does context grow across multiple turns without pruning?

 A system that configures 32K context for queries that average 2K tokens is not wasting money on unused context (most APIs charge for actual tokens, not allocated context), but it may indicate a context pruning problem if context grows over multi-turn interactions. Check for unbounded context growth: in a 20-step agent task, does the context grow linearly with each step's output?

6. **Assess Batch API opportunity.** Identify workloads that are not latency-sensitive:
 - Nightly processing pipelines (document analysis, report generation, data extraction)
 - Bulk evaluation runs
 - Offline content moderation or classification
 - Any workflow where results are consumed hours after the request is submitted

 For each identified workload:
 - Current monthly cost at synchronous API pricing
 - Projected monthly cost at Batch API pricing (Anthropic Batch: 50% discount; OpenAI Batch: 50% discount)
 - Monthly savings
 - Implementation complexity (typically low — change API endpoint and add async result polling)

7. **Quantify subagent fanout cost.** For any orchestrator/worker multi-agent pattern, calculate the total token cost for a single user-facing task end-to-end:

 `total_tokens_per_task = orchestrator_input + orchestrator_output + Σ(worker_i_input + worker_i_output) + synthesis_input + synthesis_output`

 Example: orchestrator (2K in, 0.5K out) → 5 workers (each 3K in, 1K out) → synthesis (18K in from worker outputs + 2K context, 1.5K out) = 2.5K + 20K + 19.5K = 42K tokens per user query.

 At Sonnet pricing ($3/M input, $15/M output): 42K tokens ≈ $0.63 per user query.
 At 1,000 queries/day: $630/day, $18,900/month.

 If the fanout cost has never been calculated, do it now before scaling the system. The orchestrator's token count is a small fraction of the true cost.

8. **Identify unnecessary tool calls.** Review tool call logs for:
 - The same tool called with identical or near-identical arguments multiple times in the same agent turn (deduplication opportunity — cache tool results within a turn)
 - Tools called to retrieve information already present earlier in the agent's context (context awareness failure — agent did not notice the information was already there)
 - Tools called speculatively for information that is not used in the final output (over-eager tool use — add explicit "only call this tool if you need the result for your final answer" instruction)
 Each unnecessary tool call adds latency. If the tool calls an LLM (an LLM-based tool, a grading step, or a sub-agent), it multiplies token costs directly.

9. **Model cost projections.** Calculate three scenarios:
 - **Current**: monthly cost at current volume with current configuration
 - **Scale (10x)**: projected monthly cost if query volume increases 10x with no changes
 - **Optimized (10x)**: projected monthly cost at 10x volume with all identified optimizations applied

 Present these as a table with a narrative explanation of which optimizations contribute the most savings.

## Checklist

- [ ] 30-day cost baseline established: input, output, cached tokens, and total cost per model
- [ ] Cache hit rate calculated per model; below 50% for repetitive workloads flagged as configuration issue
- [ ] Per-request token logging confirmed in place (not just monthly billing totals)
- [ ] Top 5 request types by cost identified with their average token counts and cost share
- [ ] Prompt caching prefix placement verified: stable content before breakpoint, variable content after
- [ ] Cached prefix minimum 1,024 tokens confirmed
- [ ] Variable content in system prompt that breaks caching identified and removal plan documented
- [ ] Model selection reviewed per task type: routing table with recommended models and savings estimates
- [ ] Model downgrade recommendations validated on a quality sample before committing
- [ ] Context accumulation pattern checked: no unbounded growth across multi-turn agent tasks
- [ ] Batch API opportunity identified for all non-latency-sensitive workloads; savings calculated
- [ ] Subagent fanout total token cost calculated for representative user task end-to-end
- [ ] Unnecessary tool call patterns identified: duplicates, information-already-in-context, speculative calls
- [ ] Monthly cost projections produced: current, 10x without optimization, 10x with optimization

## Common issues & anti-patterns

**System prompt not cached because it contains variable content.** The system prompt includes `Today is {{date}}` or the user's display name. Every request generates a unique system prompt, preventing caching even though 99% of the content is static. Move all variable content to the human turn (user message), not the system prompt. The system prompt must be byte-identical across requests to be cached.

**Using flagship models for every task.** The model selection was made during prototyping. The same flagship model now handles complex reasoning tasks (correct) and simple yes/no classification queries (a 5-100x cost overhead). Implement task-type routing. Reserve flagship models for tasks where the quality difference is measurable. Classification, short extraction, and reformatting tasks should use the smallest model that meets the quality bar.

**Context accumulation in multi-step agents.** Step 1 adds 1K tokens. Step 2 adds the full output of step 1 (another 1K). Step 3 adds the full outputs of steps 1 and 2. By step 10, the context is 55K tokens. Total cost for the task: O(n²) in the number of steps. Add explicit context pruning between steps: keep only a summary of completed steps (200-500 tokens), not the full outputs. This reduces a 10-step task from ~55K tokens to ~7K tokens.

**Batch API not used for nightly jobs.** A document analysis pipeline processes 5,000 documents per night with results needed by 8am — a 6-hour window. The pipeline uses synchronous API calls. Switching to the Batch API saves 50% of that pipeline's monthly cost with no change to output quality and no change to the delivery deadline. If results are needed in hours (not seconds), use the Batch API.

**Fanout cost never modeled.** An orchestrator receives a user query (2K tokens). It fans out to 6 specialized workers (each 4K in + 1.5K out). Synthesis: 13.5K in + 2K out. Total per query: 2K + 36K + 15.5K = ~53.5K tokens. The team modeled cost as "about 2K tokens per query" based on the orchestrator's direct token count. At 500 queries/day, actual cost is 27× higher than estimated. Model the full fanout before launch, not after the first invoice.

**No token logging in production.** The team wants to reduce costs but has only the monthly billing total. They cannot tell which request types are expensive, whether caching is working, or whether context is growing unboundedly. Per-request token logging is a prerequisite for any cost optimization work. Implement it before attempting any optimization.

**Downgrading models without quality validation.** The team routes all classification tasks from Sonnet to Haiku to save money. They do not test whether Haiku meets the quality bar for those tasks. Six weeks later, user complaints about classification errors rise by 30%. The cost saving was real but the quality regression was not caught. Always validate on a representative 100-example sample before committing a model downgrade to production.

**Output token max set to model maximum.** `max_tokens` is set to 4,096 for all requests because "we might need it." Average output is 350 tokens. This does not directly increase cost (most APIs charge for actual output tokens, not max tokens) but it increases the response timeout window and can mask runaway generation in some runtime implementations. Set `max_tokens` to 2× the 95th percentile of actual output length with a reasonable hard cap.

## Required output

Produce a cost control review report with:

1. **Cost baseline** — table: model, input tokens/month, output tokens/month, cached tokens/month, cache hit rate, total cost/month
2. **Cost driver analysis** — table: request type, average input tokens, average output tokens, cost share (%), optimization opportunity
3. **Caching assessment** — cache hit rate per model, cache prefix placement verdict, variable content findings, estimated savings if fixed
4. **Model routing assessment** — table: task type, current model, recommended model, quality validated (yes/no), monthly savings estimate
5. **Context efficiency findings** — average context utilization per request type, accumulation pattern findings, pruning recommendation
6. **Batch API opportunity** — table: workload, current monthly cost, projected Batch cost, monthly savings, implementation effort (S/M/L)
7. **Subagent fanout cost table** — task name, orchestrator tokens, worker count, tokens per worker, synthesis tokens, total tokens/query, cost/query at current pricing
8. **Unnecessary tool call findings** — pattern type, estimated occurrence rate, estimated monthly token waste
9. **Monthly cost projections** — table: scenario (current / 10x unoptimized / 10x optimized), monthly cost, assumptions
10. **Prioritized optimization list** — table: optimization, estimated monthly savings, implementation effort (S/M/L), quality risk (none/low/medium), specific implementation step

## Safety

- Do not optimize cost by removing or shortening safety instructions, refusal rules, or output validation — safety components are not optional context.
- Do not recommend a model downgrade for any task without first validating the smaller model meets the quality bar on a representative sample.
- If cost projections reveal the system cannot be sustainably operated at the target volume even with all optimizations applied, this is a product-level viability risk — escalate to stakeholders alongside the technical report.
- Do not disable prompt caching for privacy reasons without understanding what alternative data isolation mechanism will replace it — simply disabling caching does not prevent the provider from storing prompts for other reasons.

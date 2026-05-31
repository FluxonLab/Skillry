---
name: prompt-systems-review
description: Use when you need to review prompts, instructions, evaluation criteria, hallucination risk, and execution clarity.
---

# Prompt Systems Review

## Purpose

Review system prompts, few-shot examples, output schemas, instruction sets, and prompt versioning for structural problems that cause unreliable model behavior. Focuses on ambiguity, instruction conflict, context window misuse, schema drift, and hallucination risk — not on whether the prose sounds good. Every finding must reference the specific instruction, field, or example that is the problem source.

## When to use

- A prompt is producing inconsistent or unexpected outputs and the cause is unclear.
- A new system prompt or instruction set needs review before it goes into production.
- The prompt has grown organically over months and nobody knows what all the instructions actually do or which ones conflict.
- An agent's output schema is drifting — the model sometimes follows it and sometimes ignores it.
- Few-shot examples are stale or contradict the current task description.
- Multiple prompt layers interact (system prompt + user template + tool descriptions + retrieved context) and you suspect conflicts.
- The prompt is approaching the context window limit and you need to identify what to trim without breaking behavior.

## When not to use

- The question is whether the model's answer is factually correct (use `llm-evaluation-review`).
- The problem is tool permissions or agent recursion, not prompt structure (use `agent-governance-review`).
- You are writing a new prompt from scratch with no existing text to review — this skill reviews, not drafts.
- The prompt is a one-off manual query, not a system prompt used at scale.

## Procedure

1. **Collect all prompt layers.** Gather and read: system prompt, user message template, few-shot examples, tool descriptions in the function schema, injected retrieval context format, any memory injection format, and any post-processing instructions. Review them as a combined unit, in the order they appear in the final assembled prompt, not individually.

2. **Map instruction domains.** Read every instruction and categorize it:
 - **Persona**: tone, communication style, identity
 - **Output format**: JSON schema, markdown, field names, length limits
 - **Task logic**: what to do, how to reason, when to escalate
 - **Safety/refusal**: what to refuse, how to refuse, what to never say
 - **Tool use**: which tools to call, when, with what parameters
 - **Context handling**: how to treat retrieved content, memory, conversation history
 Any single instruction that spans two domains should be split into two instructions. Any domain with no instructions is a gap — document it.

3. **Detect instruction conflicts.** Read all instructions in the same domain and identify pairs where one instruction can contradict the other under common inputs. Example: "Always respond in JSON" (output format) combined with "If the user asks for a plain-language summary, write a paragraph" (task logic) — which wins when both apply? Document every conflict with the specific instruction text and a concrete input that would trigger the conflict.

4. **Audit output schema coverage.** If the prompt specifies a JSON schema or structured output:
 - Every field must have a type (`str`, `int`, `bool`, `list[X]`, `Optional[X]`)
 - Every field must have a one-sentence description
 - Every field must have at least one example value
 - The schema version must match what the downstream parser expects
 Run a diff between the prompt's schema and the parser's expected schema. Any field present in one but not the other is a breaking discrepancy.

5. **Review few-shot examples.** For each example:
 - Is the input realistic and representative of current production traffic?
 - Does the output match the current schema exactly (field names, types, structure)?
 - Is the output consistent with every current instruction?
 - Would this output be correct under today's product requirements (not last quarter's)?
 Remove any example where the output would now be wrong. Flag any example where the input type appears fewer than 5 times in production logs — it is over-indexing a rare case.

6. **Assess hallucination risk.** Identify prompts that ask the model to state facts it cannot verify without retrieval: current prices, live data, user account details, recent events. Flag any instruction that says "if you don't know, provide your best estimate" — for a customer-facing application, this is a hallucination invitation. Replace with: "If you cannot find the answer in the provided context, respond with `{result: null, reason: 'insufficient_data'}`."

7. **Check context window allocation.** Estimate token budget per layer:
 - System prompt: target ≤ 20% of usable context for retrieval-heavy applications
 - Few-shot examples: target ≤ 15%
 - Retrieved context: target ≤ 50%
 - User message: target ≤ 10%
 - Output buffer: target ≥ 5%
 If any layer consistently exceeds its budget, identify what can be removed or moved to a retrieval source.

8. **Verify prompt versioning.** Confirm the prompt has: a version identifier (v1.2.3 or a commit hash), a changelog documenting what changed between versions, and a pointer to the eval dataset used to validate the current version. A prompt with no version history cannot be safely rolled back when a regression occurs.

9. **Test with adversarial inputs.** Send the assembled prompt:
 - An empty input
 - A single-word input ("yes", "help")
 - An input in a different language than the prompt's target
 - An input that requests the model to ignore its instructions
 - An oversized input that approaches the context limit
 - An input that matches multiple conflicting instructions simultaneously
 Document the behavior for each. Failures here are specification gaps, not model misbehavior.

## Checklist

- [ ] All prompt layers collected and reviewed in assembly order as a single unit
- [ ] Every instruction categorized by domain: persona / format / task / safety / tools / context
- [ ] Instruction domains with no coverage identified as gaps
- [ ] No instruction conflicts remain, or conflicts documented with resolution rule and priority order
- [ ] Output schema: every field has type, description, and example value
- [ ] Schema version in prompt matches schema version expected by downstream parser
- [ ] Every few-shot example output matches current schema exactly
- [ ] No few-shot example output would be wrong under current product requirements
- [ ] No instruction invites hallucination ("estimate if unknown" is banned)
- [ ] Token budget calculated per layer; system prompt ≤ 20% of usable context for retrieval apps
- [ ] Prompt has version identifier and changelog
- [ ] Prompt has a linked eval dataset for the current version
- [ ] All six adversarial input categories tested and results documented

## Common issues & anti-patterns

**The ever-growing system prompt.** Instructions are appended whenever a new edge case appears. After six months, the prompt is 6,000 tokens with clauses that contradict each other, references to features that no longer exist, and examples for scenarios that have been replaced. Treat the prompt as code: refactor, delete dead instructions, and keep it under version control with the same review standards as production code.

**Schema-prose mismatch.** The prompt says "respond with a JSON object" but the few-shot examples show a markdown code block containing JSON. The model learns to produce the markdown wrapper. The parser expects raw JSON. The `json.loads()` call fails on every response. Make the few-shot outputs exactly match the schema — no wrappers, no commentary, just the schema.

**Implicit persona bleed.** "You are a helpful financial advisor" combined with "never give specific investment advice" creates role confusion. The model hedges every response with excessive disclaimers because it cannot resolve the conflict. Separate persona (sets tone) from constraint (sets hard stops): "You communicate in the style of a financial advisor. You must not make specific investment recommendations."

**Missing field definitions.** The output schema has `confidence: number` with no range, no meaning, and no example. The model outputs 0.95 for some responses and 95 for others. The parser breaks. Define every field completely: `confidence: float in [0.0, 1.0] — model's self-assessed confidence in the response; 1.0 = certain, 0.0 = completely uncertain`.

**Stale few-shot examples.** The product changed six months ago. The examples still reference the old field name `user_query` which is now `query_text`. The model produces `user_query` in its output despite the schema saying `query_text`. Treat examples as code: they require review whenever the schema changes.

**Hallucination invitation.** "If you are unsure of the current price, provide a reasonable estimate based on historical data." For a customer-facing application, this means the model will cite a specific price with confidence. The customer relies on it and places an order. Replace with explicit null handling in the output schema.

**No prompt version control.** The team edits the system prompt in the AI studio UI. There is no record of what the prompt said three weeks ago. A regression appears. Nobody knows which edit caused it. Version control for prompts is not optional — use git or a prompt management system, with the same review process as production code changes.

**Tool description as instruction.** The tool function schema has a `description` field that says "Call this tool with the user's full message as the query parameter for best results." This is an executable instruction, not documentation. The model follows it and passes the full user message — including any injected content — as the query argument. Treat every word in tool descriptions as an instruction that the model will execute.

## Required output

Produce a prompt review report with:

1. **Scope** — prompt layers reviewed, model target, date, version under review
2. **Instruction map** — table: instruction text (up to 80 chars), domain category, conflicts flagged (yes/no), conflict partner instruction
3. **Schema assessment** — table: field name, type present (yes/no), description present (yes/no), example present (yes/no), parser match (yes/no)
4. **Few-shot audit** — count of examples, count with schema-exact output, count to remove and why
5. **Hallucination risk items** — table: instruction or pattern, risk level (high/medium/low), recommended replacement text
6. **Token budget** — table: layer, estimated tokens, target %, actual %, within budget (yes/no)
7. **Version hygiene** — version ID present (yes/no), changelog present (yes/no), eval dataset linked (yes/no)
8. **Adversarial test results** — table: input type, input used (truncated), observed output, pass/fail verdict
9. **Prioritized issue list** — severity (critical/high/medium/low), description, exact location, specific fix ("change line X from Y to Z")

## Safety

- Do not run review test prompts against production endpoints with real user data as input.
- Do not share a system prompt's full text outside the review scope — system prompts often contain confidential product logic and persona instructions the team considers proprietary.
- If a prompt contains hardcoded API keys, passwords, or tokens, redact them immediately (note the location) and escalate as a security finding before completing the rest of the review.
- Do not recommend shortening the system prompt by removing safety instructions or refusal rules to save context window tokens — safety instructions are not optional context.

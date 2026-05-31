---
name: agent-workflow-design
description: Use when you need to design agent roles, handoffs, tool boundaries, workflow routing, and coordination rules.
---

# Agent Workflow Design

## Purpose

Design multi-agent workflows with explicit role boundaries, handoff contracts, tool ownership, recursion limits, and state-passing schemas. Produces a concrete workflow specification — not a vague diagram — that a developer can implement directly in code.

## When to use

- You are architecting a new multi-agent system from scratch and need to define who does what.
- An existing agent pipeline has unclear handoffs, role overlap, or runaway recursion.
- A task requires orchestrator/worker separation and you need to define routing logic.
- Tool sprawl is causing agents to misuse each other's tools.
- You need to specify state shape passed between agents (not just "pass the context").
- A multi-step workflow keeps failing partway through and the root cause is unclear handoff design.
- You are onboarding a new developer to an agent system and need a written spec they can follow.

## When not to use

- The task is a single-agent prompt with no delegation — no workflow design needed.
- You only need to review security/permissions of an existing workflow (use `agent-governance-review`).
- The question is purely about prompt quality, not agent coordination (use `prompt-systems-review`).
- The system is already built and working; skip design and go straight to the specific fix.
- The workflow has one agent and one tool — this is not multi-agent and needs no formal design.

## Procedure

1. **Identify agents and roles.** List every agent in scope. For each, name its single responsibility in one sentence. If an agent has two unrelated jobs, split it into two agents. Use role names that describe function, not implementation: `retriever`, `reasoner`, `executor`, `validator`, `formatter` — not `agent_1`, `agent_2`.

2. **Draw the handoff chain.** Specify: which agent triggers which, what payload it sends, what it expects back. Use a table:

 | Caller | Callee | Trigger condition | Input schema | Expected output schema |
 |---|---|---|---|---|
 | orchestrator | retriever | user query received | `{query: str, filters: dict}` | `{chunks: list[Chunk], scores: list[float]}` |

3. **Assign tool ownership.** Each tool belongs to exactly one agent role. Document as a table:

 | Tool | Owner agent | Max calls/turn | Side-effect level |
 |---|---|---|---|
 | web_search | retriever | 5 | read |
 | file_write | executor | 1 | destructive |

 Agents must not call tools owned by other roles without an explicit delegation pattern.

4. **Set recursion and loop limits.** Define `max_depth` for any agent that can spawn sub-agents. Define `max_iterations` for any retry or reflection loop. These must be hard-coded constants, not left as defaults or "unlimited." Recommended defaults: `max_depth = 3`, `max_iterations = 5` unless the use case explicitly requires more.

5. **Define state-passing schema.** Specify the JSON schema (or TypedDict) for the state object passed between agents. Minimum required fields:
 - `task_id: str` — unique identifier for the top-level task
 - `origin_agent: str` — which agent created this state object
 - `step_history: list[StepRecord]` — every tool call and its outcome
 - `current_context: str` — the working context the next agent should use
 - `remaining_budget_tokens: int` — estimated tokens left in the session budget
 - `error_state: Optional[ErrorRecord]` — current error if in a recovery path
 Stateless handoffs that pass raw text are a red flag. The receiving agent cannot tell what was already tried.

6. **Design the orchestrator/worker split.** The orchestrator: routes requests to workers, aggregates results, decides termination, manages the budget. Workers: execute a single tool category, return structured results to the orchestrator. Rules: the orchestrator must never directly call external APIs — only workers do. Workers must not communicate with each other directly — all routing goes through the orchestrator.

7. **Define failure and fallback routing.** For each handoff, specify what happens on: timeout (worker takes more than N seconds), tool error (API failure, permission denied), out-of-scope response (worker returns a result it should not have). Fallback options: retry with exponential backoff (max 3 attempts), escalate to human-in-the-loop, return partial result with error flag in the error envelope.

8. **Document approval gates.** Any action with side-effect level `write` or `destructive` requires an explicit approval step before the tool call is executed. The gate must be implemented in code — not as a prompt instruction. Name the gate agent, the approval signal format, and the timeout behavior if no approval arrives.

9. **Verify the design with scenario traces.** Walk through 2-3 realistic scenarios end-to-end against the spec. For each: name the input, trace every agent activation and handoff, confirm termination, verify no agent makes a decision outside its role. Also trace one failure scenario to confirm recovery routing works.

## Checklist

- [ ] Every agent has exactly one stated responsibility (one sentence)
- [ ] Agent names describe function, not implementation order
- [ ] All handoffs have typed input/output schemas, not free-text
- [ ] Every tool is owned by exactly one agent; no shared ownership without a named broker agent
- [ ] `max_depth` is an explicit integer (not "unlimited" or "default")
- [ ] `max_iterations` is an explicit integer for every retry or reflection loop
- [ ] State object includes `task_id`, `step_history`, and `remaining_budget_tokens`
- [ ] Orchestrator does not directly call external APIs
- [ ] Workers do not communicate with each other directly
- [ ] Failure routing specified for: timeout, tool error, out-of-scope response
- [ ] Every write/destructive tool has a named code-level approval gate
- [ ] At least 2 happy-path and 1 failure-path scenarios traced end-to-end
- [ ] Error envelope standard defined: `{ok: bool, error_code: str, result: any}`

## Common issues & anti-patterns

**God agent.** One agent does retrieval, reasoning, tool execution, and output formatting. Nobody can test any piece in isolation. When it fails, nobody knows which function broke. Split by capability: retriever, reasoner, executor, formatter. Each agent has one job and can be tested and replaced independently.

**Stateless handoffs.** The orchestrator passes a raw string to each worker. Worker B has no idea Worker A already tried and failed this approach. The system loops. Always pass structured state with step_history so each agent knows what has been attempted.

**Unbounded recursion.** An orchestrator spawns a worker that spawns another orchestrator with a "refined" prompt, which spawns another worker. Without `max_depth`, this loops until context is exhausted or the API budget is hit. Set depth limits at design time.

**Tool leakage.** Worker A calls Worker B's file_write tool directly because "it's faster." This breaks isolation — now you cannot grant file_write only to the executor. Enforce tool ownership strictly; add a broker agent if cross-role tool use is genuinely required.

**Missing termination condition.** A reflection loop runs until the model decides it's done. The model never decides it's done because it keeps finding "one more thing to check." Define a hard `max_iterations` and a concrete exit criterion: confidence score above 0.9, explicit DONE signal in the output schema, or maximum turns reached.

**Over-fanout.** An orchestrator fans out to 10 workers in parallel when 3 would suffice. Each fan-out multiplies token cost and error surface. A single bad worker blocks the aggregation step. Prefer sequential with early-exit over parallel by default; use parallel only when latency requirements force it and each worker is independently non-blocking.

**No error propagation contract.** Workers return `null` or an empty string on error. The orchestrator cannot distinguish "no result found" from "tool execution failed." Require a standard error envelope for all worker returns. The orchestrator must check `ok: false` before passing a worker result downstream.

**Implicit state growth.** Each worker appends its full output to the shared context. After 10 workers, the context is 40K tokens of overlapping outputs. The 11th worker receives all of it in its prompt and the context window is exhausted. Define an explicit context pruning strategy: keep only summaries of completed steps, not raw outputs.

## Required output

Produce a workflow specification document containing:

1. **Agent roster** — table: name, single-sentence role, model tier recommendation (small/medium/large), max turns
2. **Handoff table** — caller, callee, trigger condition, input schema, expected output schema
3. **Tool ownership table** — tool name, owner agent, max calls/turn, side-effect level
4. **State schema** — JSON schema or TypedDict with all fields, types, and descriptions
5. **Recursion limits** — `max_depth` and `max_iterations` stated as explicit integers, with rationale
6. **Failure routing table** — handoff, failure type, fallback action, max retry count
7. **Approval gates** — list: destructive action, gate agent, approval signal format, timeout behavior
8. **Scenario traces** — 2 happy-path traces and 1 failure-path trace, step-by-step

## Safety

- Do not design workflows that allow any agent to modify its own system prompt or skill files at runtime.
- Do not allow a worker agent to call another agent with higher privilege than the orchestrator that spawned it.
- Document every agent that has write access to persistent storage — this is a high-risk role requiring a named owner.
- Never approve a workflow where a worker can bypass the orchestrator's approval gate via a direct tool call.
- Flag any design where the orchestrator receives unvalidated external content (web, user upload, third-party API) and passes it directly to a tool with write or destructive capability.
- Every workflow that touches production data or sends external requests requires a human approval gate for the first 30 days of operation.

---
name: agent-workflow-design
description: Use when you need to design agent roles, handoffs, tool boundaries, workflow routing, and coordination rules.
---

# Agent Workflow Design

## Purpose

Design multi-agent workflows with explicit role boundaries, handoff contracts, tool ownership, recursion limits, and state-passing schemas. Produce a concrete workflow specification — not a vague diagram — that a developer can implement directly in code. Every agent has one job, every handoff is typed, every loop is bounded, and every write/destructive action passes a code-level approval gate.

## When to use

- You are architecting a new multi-agent system from scratch and need to define who does what.
- An existing agent pipeline has unclear handoffs, role overlap, or runaway recursion.
- A task requires orchestrator/worker separation and you need to define routing logic.
- Tool sprawl is causing agents to misuse each other's tools.
- You need to specify the state shape passed between agents (not just "pass the context").
- A multi-step workflow keeps failing partway through and the root cause is unclear handoff design.
- You are onboarding a developer to an agent system and need a written spec they can follow.

## When not to use

- The task is a single-agent prompt with no delegation — no workflow design needed.
- You only need to review security/permissions of an existing workflow (use `41-agent-governance-review`).
- The question is purely about prompt quality, not coordination (use `42-prompt-systems-review`).
- The system is already built and working; skip design and go straight to the specific fix.

## Procedure

1. **Identify agents and roles.** List every agent in scope; name each one's single responsibility in one sentence. Split any agent with two unrelated jobs. Use function names (`retriever`, `reasoner`, `executor`, `validator`, `formatter`), not `agent_1`.
2. **Draw the handoff chain.** For each edge, specify caller, callee, trigger condition, input schema, and expected output schema (table in Commands).
3. **Assign tool ownership.** Each tool belongs to exactly one agent role, with a max-calls-per-turn and a side-effect level. Agents must not call tools owned by other roles without an explicit delegation pattern.
4. **Set recursion and loop limits.** Define `max_depth` for any agent that spawns sub-agents and `max_iterations` for any retry/reflection loop, as hard-coded constants. Defaults: `max_depth = 3`, `max_iterations = 5` unless the use case requires more.
5. **Define the state-passing schema.** Specify the JSON schema / TypedDict passed between agents, with at least `task_id`, `origin_agent`, `step_history`, `current_context`, `remaining_budget_tokens`, and `error_state`. Stateless raw-text handoffs are a red flag — the receiver cannot tell what was already tried.
6. **Design the orchestrator/worker split.** Orchestrator routes, aggregates, decides termination, manages budget; workers execute one tool category and return structured results. Orchestrator must never call external APIs directly; workers must not talk to each other directly.
7. **Define failure and fallback routing.** For each handoff specify behavior on timeout, tool error, and out-of-scope response — retry with backoff (max 3), escalate to human, or return a partial result in the error envelope.
8. **Document approval gates.** Any `write`/`destructive` action requires an explicit code-level approval step before the tool call. Name the gate agent, the approval signal format, and the timeout behavior.
9. **Verify with scenario traces.** Walk 2–3 realistic scenarios end-to-end plus one failure scenario; confirm termination and that no agent decides outside its role.

## Concrete checks

- [ ] Every agent has exactly one stated responsibility (one sentence).
- [ ] Agent names describe function, not implementation order.
- [ ] All handoffs have typed input/output schemas, not free text.
- [ ] Every tool is owned by exactly one agent; no shared ownership without a named broker.
- [ ] `max_depth` and `max_iterations` are explicit integers, not "unlimited" or "default".
- [ ] State object includes `task_id`, `step_history`, and `remaining_budget_tokens`.
- [ ] Orchestrator does not directly call external APIs.
- [ ] Workers do not communicate with each other directly.
- [ ] Failure routing specified for timeout, tool error, and out-of-scope response.
- [ ] Every write/destructive tool has a named code-level approval gate.
- [ ] At least 2 happy-path and 1 failure-path scenarios traced end-to-end.
- [ ] Error envelope standard defined: `{ok: bool, error_code: str, result: any}`.

## Commands or Templates

```text
Handoff table
| Caller       | Callee    | Trigger condition    | Input schema                  | Output schema                          |
|--------------|-----------|----------------------|-------------------------------|----------------------------------------|
| orchestrator | retriever | user query received  | {query: str, filters: dict}   | {chunks: list[Chunk], scores: list[f]} |

Tool ownership table
| Tool        | Owner agent | Max calls/turn | Side-effect level |
|-------------|-------------|----------------|-------------------|
| web_search  | retriever   | 5              | read              |
| file_write  | executor    | 1              | destructive       |
```

```python
# State object passed between agents (TypedDict)
from typing import Optional, TypedDict

class StepRecord(TypedDict):
    agent: str; tool: str; ok: bool; summary: str

class WorkflowState(TypedDict):
    task_id: str                       # unique top-level task id
    origin_agent: str                  # which agent created this state
    step_history: list[StepRecord]     # every tool call + outcome
    current_context: str               # working context for the next agent
    remaining_budget_tokens: int       # estimated session budget left
    error_state: Optional[dict]        # set on a recovery path

# Hard limits — constants, never "unlimited"
MAX_DEPTH = 3
MAX_ITERATIONS = 5

# Standard worker return envelope
def envelope(ok: bool, result=None, error_code: str = "") -> dict:
    return {"ok": ok, "error_code": error_code, "result": result}
```

## Worked scenario traces

Traces are how you prove the design terminates and stays in-role before writing code. For a research-and-act workflow (orchestrator + retriever + executor + validator):

```text
Happy path — "summarize the latest pricing doc and update the cache"
1. orchestrator receives task → routes to retriever (depth 1)
   handoff: {query:"pricing doc", filters:{recency:"30d"}}
2. retriever calls web_search (1/5 calls) → returns {chunks:[...], ok:true}
3. orchestrator → reasoner: summarize chunks → {summary:"...", ok:true}
4. summary has a write side-effect (cache update) → APPROVAL GATE
   executor requests file_write; gate returns approved
5. executor calls file_write (1/1) → {ok:true}
6. orchestrator: all steps ok, no further work → TERMINATE. depth never exceeded 1.

Failure path — web_search times out
2'. retriever web_search times out → returns envelope {ok:false, error_code:"timeout"}
3'. orchestrator sees ok:false → retry with backoff (attempt 1 of 3)
4'. second attempt also fails → escalate per failure routing: return partial
    result {summary:null, error_state:{code:"retrieval_failed"}} and STOP.
    The executor is never reached, so no cache write happens on bad data.
```

The failure trace is the important one: it confirms the approval gate and the error envelope prevent a write from happening when upstream retrieval failed. A design whose failure trace ends in "executor writes anyway" or "loops forever" is not ready.

## Common issues & anti-patterns

- **God agent.** One agent does retrieval, reasoning, execution, and formatting; nothing can be tested in isolation. Split by capability.
- **Stateless handoffs.** Passing a raw string means worker B cannot tell worker A already tried and failed; the system loops. Pass structured state with `step_history`.
- **Unbounded recursion.** An orchestrator spawns a worker that spawns another orchestrator; without `max_depth` it loops until the budget is exhausted.
- **Tool leakage.** Worker A calls worker B's `file_write` directly, breaking isolation so you cannot scope the tool. Enforce ownership; add a broker if cross-role use is genuinely needed.
- **Missing termination condition.** A reflection loop runs until the model "feels done", which never happens. Set `max_iterations` plus a concrete exit criterion.
- **Over-fanout.** Fanning out to 10 workers when 3 suffice multiplies cost and error surface. Prefer sequential with early exit by default.
- **No error-propagation contract.** Workers return `null` on error; the orchestrator cannot distinguish "no result" from "tool failed". Require the standard envelope.
- **Implicit state growth.** Each worker appends its full output; by worker 11 the context is exhausted. Prune to summaries of completed steps.

## Assigning model tiers

Cost and latency are part of the design, not an afterthought. Match each role to the smallest model that does its job reliably:

- **Small/fast** — deterministic, narrow roles: routing, classification, schema validation, formatting. These rarely need a frontier model and run on every request, so they dominate cost if over-provisioned.
- **Medium** — retrieval reasoning, summarization, single-step tool selection where some judgment is needed but the output space is bounded.
- **Large/frontier** — open-ended reasoning, planning, or synthesis where quality directly drives the outcome and the call frequency is low.

Record the tier in the agent roster so reviewers can see where budget goes. A common waste is running the orchestrator's routing decision on a frontier model when a small model with a typed output schema routes just as accurately at a fraction of the cost and latency.

## Required output

Produce a workflow specification document containing: (1) agent roster — name, one-sentence role, model tier, max turns; (2) handoff table; (3) tool ownership table; (4) state schema with field types and descriptions; (5) recursion limits as explicit integers with rationale; (6) failure routing table; (7) approval gates list; (8) 2 happy-path traces and 1 failure-path trace, step by step.

## Safety

- Do not design workflows that allow any agent to modify its own system prompt or skill files at runtime.
- Do not allow a worker to call another agent with higher privilege than the orchestrator that spawned it.
- Document every agent with write access to persistent storage — a high-risk role requiring a named owner.
- Never approve a workflow where a worker can bypass the orchestrator's approval gate via a direct tool call.
- Flag any design where the orchestrator passes unvalidated external content (web, user upload, third-party API) straight into a write/destructive tool.
- Every workflow that touches production data or sends external requests requires a human approval gate for the first 30 days of operation.

## Completion criteria

Done means each agent has one role, all handoffs and tools are typed and owned, recursion/iteration limits are explicit integers, the state schema and error envelope are defined, failure routing and approval gates are specified, and the design is verified with at least two happy-path traces and one failure-path trace.

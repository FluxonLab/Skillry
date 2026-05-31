---
name: automation-mcp-gatekeeping
description: Use when you need to gate external automation, MCP, Rube, Composio, credentials, scopes, and tool activation.
---

# Automation MCP Gatekeeping

## Purpose
Use this skill to gate external automation, MCP, Rube, Composio, credentials, scopes, and tool activation. No external-service action (Slack, Gmail, Calendar, CRM, payments) may proceed without an active connector, minimum-privilege scope, and explicit user approval — this skill enforces that gate before any call is made.

## When to use
- An agent or task intends to post a message, send an email, update a record, or trigger any external service action and you need to confirm an active, approved connector exists first.
- A request to install, configure, or authenticate Rube, Composio, or any MCP server arrives — explicit user approval is required before proceeding.
- The scope of a proposed integration token or OAuth grant needs to be challenged down to the narrowest read-only or single-resource permission that satisfies the task.
- A task looks like local file work but actually routes through an external API (e.g., "update the Notion page") and needs to be correctly classified before acting.

## When not to use
- The task is unrelated to ai and agent systems work.
- The work would require production deploys, destructive data actions, or secret disclosure.
- A narrower skill or existing project instruction already covers the need.

## Procedure
1. Classify the task: **local work** (code, files, tests, build, local DB, local browser) → no external automation needed; **external-service work** (Slack, Gmail, Calendar, Notion, Sheets, Linear, Jira, HubSpot, Airtable, payments, CRM) → requires an active tool; **recurring automation** → requires an approved, scheduled integration.
2. For external-service work, verify a real connector is **active** before acting: a native connector, an MCP server tool, an app tool, or a project-approved integration. If none is active, do not simulate success.
3. If no active tool exists, produce the gating report (below) and stop: name the service, operation, tool option, minimum scope, data/safety risk, and a concrete smoke test.
4. Require explicit user approval before installing, configuring, authenticating, or enabling Rube/Composio or any equivalent external automation.
5. Apply least privilege: request the narrowest scope that completes the task; prefer read-only first; avoid broad admin tokens.
6. Keep dormant automation skills indexed, not auto-activated; load one only when the task truly needs it.

## Decision checklist
- [ ] Is this actually external? (editing a local file is not "Notion work")
- [ ] Is a connector/MCP/app tool currently active for this service?
- [ ] Is the requested scope the minimum needed? (read vs write vs admin)
- [ ] What is the blast radius if the call misfires? (sends email, posts a message, charges a card)
- [ ] Is there a non-destructive smoke test to confirm the wiring before the real action?
- [ ] Has the user approved enabling/authenticating this integration?

## Required gating report (when no active tool)
```md
- Service: <e.g. Slack>
- Operation: <e.g. post message to #channel>
- Tool option: <native connector | MCP server <name> | app tool | project integration>
- Minimum scope: <e.g. chat:write to one channel — not chat:write + admin>
- Data/safety risk: <what leaves the machine; who sees it; reversibility>
- Smoke test: <e.g. post to a private test channel first; verify 200 + message id>
- Approval: <pending user approval to enable/authenticate>
```

## Required output
Return: task classification, whether an active tool exists, and either the executed/recommended call (with scope) or the gating report above. Never claim a Slack/Gmail/etc. action succeeded without an active tool and a real result. State the minimum scope and the smoke test explicitly.

## Safety checks
- Do not install, authenticate, or enable Rube/Composio or any external automation without explicit approval.
- Do not simulate or fabricate success for an external action.
- Request least-privilege scopes; avoid broad/admin credentials.
- Redact tokens and credentials; reference scope names only.

## Completion criteria
Done means the task is correctly classified, external work is gated behind an active tool + approval + least-privilege scope, any missing-tool case yields the structured gating report with a smoke test, and no external success was simulated.

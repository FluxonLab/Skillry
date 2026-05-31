---
name: automation-mcp-gatekeeping
description: Use when you need to gate external automation, MCP, Rube, Composio, credentials, scopes, and tool activation.
---

# Automation & MCP Gatekeeping

## Purpose
Decide whether an external automation or MCP (Model Context Protocol) tool should be activated
at all — and if so, with the minimum scope, explicit approval, and a concrete safety test.
External automation (Rube/Composio, Zapier-style connectors, real Slack/Gmail/Notion/Jira/
HubSpot/Sheets/payment/CRM tools) can read private data, send messages, move money, and mutate
production systems. This skill keeps that surface closed by default and opens it deliberately.

## When to use
- A task asks to touch a real external service (Slack, Gmail, Calendar, Notion, Sheets, Linear,
  Jira, HubSpot, Airtable, Stripe/payments, a CRM, an admin panel).
- Someone proposes installing/enabling an MCP server, Rube, Composio, or a vendor automation skill.
- An agent or skill requests new credentials, OAuth scopes, or tokens.
- You are reviewing whether a connector's permissions are wider than the task needs.

## When not to use
- Pure local work: code, files, tests, build, local DB, local browser checks. These never need
  external automation — do not pull in a connector "just in case."
- Reading public documentation or running offline tooling.

## Procedure
1. **Classify the task** as one of: local work · external-service work · recurring automation.
   Only the last two can justify a connector. If it's local, stop — no activation needed.
2. **Check for an already-approved path first.** Prefer, in order: a native connector / first-party
   integration → an installed MCP tool already in scope → a project-approved automation. Do not add
   a new vendor layer if an approved one already covers the need.
3. **Identify the minimum scope.** Name the exact service, the exact operation (read vs write),
   and the narrowest credential/scope that performs it (e.g. read-only calendar, single channel,
   one repo) — not account-wide access.
4. **Require explicit approval before enabling.** Installing, authenticating, or turning on
   Rube/Composio/an MCP server is a gated action. Present the request; do not self-approve.
5. **Plan a concrete smoke test** that proves the connector works on a safe, reversible action
   (e.g. read one item, post to a test channel) before any real/destructive use.
6. **Never simulate success.** If no active tool exists, report the gap — do not pretend the action
   happened.
7. **Record** what was activated, its scope, who approved, and how to revoke it.

## Concrete checks
- Task truly needs an external service (not satisfiable locally).
- A native/first-party connector was checked before any third-party automation layer.
- Requested scope is least-privilege: read-only where possible, single-resource not account-wide.
- Credentials come from env/secret manager — never hardcoded, never printed.
- Write/destructive operations (send, delete, pay, deploy) have explicit human approval.
- A reversible smoke test is defined before real use.
- Activation, scope, approver, and revocation steps are documented.
- MCP server source is trusted and reviewed (see dependency/supply-chain review).

## Decision flow

```text
task → is it local-only?  ── yes ─→ NO connector. Do it locally.
        │ no
        ▼
   native/first-party connector available? ── yes ─→ use it (still least-scope)
        │ no
        ▼
   approved MCP/automation already in scope? ── yes ─→ use it
        │ no
        ▼
   propose: service + operation + min scope + smoke test + revocation
        │
        ▼
   explicit approval? ── no ─→ STOP, report the gap (do not simulate)
        │ yes
        ▼
   enable with least scope → run smoke test → proceed → record
```

## Risk tiers (gate strength by blast radius)
- **Read-only, non-PII** (read public issues, read a calendar): light gate — least scope + smoke test.
- **Read private / PII** (inbox, contacts, CRM records): approval + scoped credential + redaction.
- **Write / outbound** (send email, post message, create ticket): explicit approval + test target first.
- **Money / production / destructive** (charge, refund, delete, deploy): hard gate — written approval,
  dry-run if available, never default-on.

## Common issues & anti-patterns
- Enabling a broad connector for a one-off read — over-provisioned scope that lingers.
- Account-wide OAuth when a single resource would do.
- Installing an MCP server from an unreviewed source (supply-chain risk).
- Hardcoding tokens in a skill/agent file or printing them in logs.
- "It probably worked" — narrating success for an action no active tool actually performed.
- Treating Rube/Composio as always-on instead of task-gated.
- Leaving a connector enabled with no documented revocation path.

## Required output
Report: task classification (local / external / recurring); whether an approved path already
existed; the exact service + operation + least-privilege scope proposed; the approval status;
the smoke-test plan; the data/safety risk tier; and the revocation steps. If activation was
declined or unavailable, state the gap plainly — never a simulated success.

## Safety
- Default-closed: no external automation without explicit approval.
- Never print, log, or commit credentials, tokens, or secrets — reference env var names only.
- Never run a money/production/destructive external action without written approval and, where
  possible, a dry-run first.
- Only enable MCP servers / automation from trusted, reviewed sources.
- Always leave a documented way to revoke access.

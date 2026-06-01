---
name: automation-mcp-gatekeeping
description: Use when you need to gate external automation, MCP, Rube, Composio, credentials, scopes, and tool activation.
---

# Automation & MCP Gatekeeping

## Purpose

Decide whether an external automation connector or MCP (Model Context Protocol) server should be activated at all — and if so, with the minimum scope, an explicit approval record, and a concrete, reversible smoke test before any real action is taken. External automation (Rube/Composio, Zapier-style connectors, real Slack/Gmail/Notion/Jira/HubSpot/Sheets/payment/CRM tools) can read private data, send messages, move money, and mutate production systems.

The default posture is closed: no external connector is activated without a task classification, a least-privilege scope definition, and an explicit approval step. A local task that could be done with code, files, a test suite, or a local browser check must never pull in an external connector "just in case" or to save time.

## When to use

- A task asks to touch a real external service (Slack, Gmail, Calendar, Notion, Sheets, Linear, Jira, HubSpot, Airtable, Stripe, a CRM, or an admin panel).
- Someone proposes installing, configuring, or enabling an MCP server, Rube, Composio, or any other vendor automation skill.
- An agent or skill requests new credentials, OAuth scopes, API keys, or tokens for an external service.
- You are reviewing whether an existing connector's permissions are wider than the current task requires.
- A recurring automation workflow is being designed and the tool chain needs a safety and scope review before first run.

## When not to use

- The task is entirely local: editing code, running tests, building, reading files, or using a local browser. These never need an external connector.
- Reading public documentation or running offline analysis tools.
- The task is to configure the secrets manager or credential store itself — that is infrastructure work, not connector gatekeeping.

## Procedure

1. **Classify the task.** Assign it to exactly one category: `local work` (code, files, tests, build, local DB, local browser), `external-service work` (a one-off action against a live external system), or `recurring automation` (a workflow that will run repeatedly, possibly unattended). Only the last two can justify activating a connector. If classification is `local work`, stop — no connector needed, and activating one adds unnecessary scope and risk.

2. **Check for an already-approved path first.** Before proposing any new connector, verify whether the task can be done with: (a) a native first-party integration already configured in the project, (b) an MCP server or automation tool already installed and in scope, or (c) a project-approved workflow. Use the approved path if one exists. Do not add a new vendor layer when an existing one covers the need.

3. **Define the minimum scope precisely.** Name the exact service, the exact operation (read a calendar event, post to a specific Slack channel, create a Linear issue), and the narrowest possible credential scope that performs it (e.g., `channels:read` + `chat:write` for a single channel — not `admin`). For OAuth flows, identify the minimum scopes by name. For API keys, identify the minimum permission tier offered by the service.

4. **Require explicit approval before enabling.** Installing, authenticating, configuring, or turning on any MCP server or external connector is a gated action. Present the request as a structured proposal (service, operation, scope, smoke test, revocation path, risk tier). Do not self-approve. Do not proceed until a human approves the proposal in writing.

5. **Define a concrete smoke test.** Before using the connector for any real or production action, define and run a safe, reversible test: read one item (not all), post to a sandbox or test channel, create a draft (not a sent message), query metadata (not data). The smoke test must be explicitly safe — it must not modify real data, send real messages, or charge real money.

6. **Never simulate success.** If no active tool exists, or if approval was not granted, report the gap plainly: "No active connector for Gmail exists. Approval is required before activation. The action was not performed." Do not narrate a success that did not happen.

7. **Record the activation.** After a successful smoke test and before any real use, document: what was activated, its exact scope, who approved it, the date, and the steps to revoke it. Store this record where the team can review it (e.g., a project decision log, a ticket, or a config comment).

## Concrete checks

- [ ] Task is correctly classified as local / external-service / recurring — and the classification is shown, not assumed.
- [ ] A native or already-approved path was checked before proposing a new connector.
- [ ] Requested scope is least-privilege: read-only where the task only needs to read, single resource/channel/repo rather than account-wide.
- [ ] Credentials come from an env var or secret manager — never hardcoded, never printed in any output.
- [ ] Write, send, or destructive operations have explicit human approval recorded before execution.
- [ ] A reversible smoke test is defined and run before any production action.
- [ ] Activation, scope, approver name, approval date, and revocation steps are documented.
- [ ] The MCP server or connector source is trusted and has been reviewed for supply-chain risk (see `50-dependency-supply-chain-review`).
- [ ] The connector is task-gated, not left always-on after the task completes.
- [ ] No action was narrated as complete without a real tool call confirming it.

## Decision flow

```
task → classify: local / external-service / recurring
         │
         ├─ local ──────────────────────────────────────> NO connector. Do it locally.
         │
         └─ external-service or recurring
                  │
                  ▼
         native or first-party connector available? ──yes──> use it (still apply least-scope)
                  │ no
                  ▼
         approved MCP/automation already in scope? ──yes──> use it (confirm scope still fits)
                  │ no
                  ▼
         propose: service + operation + min scope + smoke test + revocation path + risk tier
                  │
                  ▼
         explicit approval received? ──no──> STOP. Report gap. Do NOT simulate success.
                  │ yes
                  ▼
         enable with least scope → run smoke test → confirm working → record activation
                  │
                  ▼
         execute real action → revoke or scope-down connector when task is complete
```

## Risk tiers (gate strength calibrated to blast radius)

| Tier | Examples | Gate requirements |
|------|----------|-------------------|
| **Read-only, non-PII** | Read public GitHub issues, read a team calendar, list Notion page titles | Least scope + smoke test. Approval recommended but lighter-weight. |
| **Read private or PII** | Read Gmail inbox, access CRM contacts, query internal analytics | Explicit approval + scoped credential + output redaction before logging. |
| **Write or outbound** | Send a Slack message, create a Linear ticket, post a calendar event, push a commit | Explicit written approval + test target first (sandbox channel, test project) before real target. |
| **Money, production, or destructive** | Stripe charge or refund, delete a database record, send a transactional email, deploy to production | Hard gate — written approval required. Dry-run or staging run first if available. Never default-on. Audit log mandatory. |

## Commands

```bash
# Inspect which MCP servers are currently configured (Claude/Cursor/etc.)
# Locations vary by platform:
cat ~/.config/claude/claude_desktop_config.json 2>/dev/null | python3 -m json.tool | grep -A5 '"mcpServers"' || true
cat .mcp.json 2>/dev/null | python3 -m json.tool || true
cat .cursor/mcp.json 2>/dev/null | python3 -m json.tool || true

# List what scopes an OAuth token was granted (GitHub example)
curl -sH "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/rate_limit \
  -I 2>/dev/null | grep -i "x-oauth-scopes"

# Slack: verify a token's granted scopes (read-only API call)
curl -sH "Authorization: Bearer $SLACK_TOKEN" \
  https://slack.com/api/auth.test | python3 -m json.tool | grep -E '"ok"|"user"|"team"'

# Linear: confirm read-only token vs write token (check scopes in token settings)
curl -sH "Authorization: Bearer $LINEAR_TOKEN" \
  https://api.linear.app/graphql \
  -d '{"query":"{ viewer { id name } }"}' | python3 -m json.tool

# Smoke test pattern: read one item before any write
# Gmail (read-only, list one message ID only):
# curl -sH "Authorization: Bearer $GMAIL_TOKEN" \
#   "https://gmail.googleapis.com/gmail/v1/users/me/messages?maxResults=1" | python3 -m json.tool

# Verify credential is from env, never hardcoded:
rg -n "(SLACK|GMAIL|NOTION|STRIPE|LINEAR|JIRA|HUBSPOT)\w*\s*=\s*['\"][A-Za-z0-9_-]{10,}" \
  -g '!*.lock' -g '!node_modules' . 2>/dev/null || echo "No hardcoded tokens found"

# Check connector is not always-on (should be task-gated)
rg -n "mcpServers\|composio\|rube" .env .env.local .claude/settings.json 2>/dev/null | head -10
```

```bash
# Record activation (append to a project decision log)
# Replace variables with actuals before running
cat >> docs/connector-activations.md <<'EOF'
## Activation record
- Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)
- Service: <service name>
- Operation: <exact operation>
- Scope granted: <scope names>
- Approved by: <name>
- Smoke test: <what was tested and the result>
- Revocation: <steps to revoke>
- Auto-revoke date: <date if applicable>
EOF

# Revoke a GitHub fine-grained token (read its ID first)
# curl -sH "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/installation/token \
#   | python3 -m json.tool | grep '"id"'
# Then: DELETE /installation/token/:id  (requires admin scope)
```

## Scope minimization reference

| Service | Over-provisioned scope to avoid | Minimum scope for common tasks |
|---------|--------------------------------|-------------------------------|
| Slack | `admin`, `channels:write` | `chat:write` (one channel) + `channels:read` |
| GitHub | `repo` (full) | `contents:read` for reading, `issues:write` for issue creation |
| Gmail | Full account access | `gmail.readonly` for reading, `gmail.send` for sending only |
| Notion | Workspace-wide | Share only the specific page/database the task needs |
| Linear | Admin | `issues:write` for ticket creation; `issues:read` for read-only queries |
| Stripe | Full access | Use restricted keys scoped to specific resources and operations |
| Jira | `ADMIN` | `BROWSE_PROJECTS` + `CREATE_ISSUES` for issue creation |

## Common issues & anti-patterns

- **Activating a broad connector for a one-off read**: an account-wide Gmail connector enabled to read one email. The connector lingers with full inbox access after the task. Apply least scope, and revoke or scope-down when the task is complete.
- **Account-wide OAuth when a single resource would do**: requesting `repo` (all repositories) when `contents:read` on a single repo is sufficient. Many services now offer fine-grained token scopes — use them.
- **Installing an MCP server from an unreviewed source**: a third-party MCP server runs with the same permissions as the agent using it. An unreviewed MCP server is an unreviewed dependency — apply the same supply-chain review you would apply to an npm package. Check the source, the maintainer, and what network calls the server makes.
- **Hardcoding tokens in a skill or agent configuration file**: `"token": "xoxb-..."` in `.mcp.json` or a skill file commits the token to the repository. Tokens must come from environment variables or a secret manager.
- **"It probably worked" without a real tool call**: narrating a success for an action that no active tool actually performed. If the connector is not active, the action did not happen. Report the gap, do not simulate.
- **Treating Rube/Composio as always-on**: keeping a write-capable connector active between tasks means every subsequent agent run inherits the capability. Task-gate connectors: enable for the task, revoke or scope-down after.
- **Leaving no documented revocation path**: "I enabled Slack write access" with no note on how to revoke it. A connector without a revocation path is a permanent footprint.
- **Skipping the smoke test**: proceeding directly to a real write action without first confirming the connector works on a safe, reversible operation. A write operation to a production channel that fails halfway is worse than a failed smoke test on a test channel.

## Required output

Report in this structure:

```
## MCP / Automation Gatekeeping Decision

### Task classification
- Category: local / external-service / recurring
- Justification: one sentence.

### Approved path check
- Native/first-party connector available: yes/no
- Already-approved MCP/automation in scope: yes/no
- Path used: <name> or "none — new connector proposed"

### Connector proposal (if new activation needed)
- Service: <name>
- Operation: <exact action>
- Minimum scope: <scope names>
- Risk tier: read-only non-PII / read private-PII / write-outbound / money-production-destructive

### Approval status
- Approval received: yes/no
- Approved by: <name> / pending

### Smoke test plan
- Test action: <safe reversible action>
- Test target: <sandbox/test channel/draft>
- Pass criterion: <expected response>
- Result: pass / fail / not yet run

### Data and safety risk
- Data accessed: <description>
- Reversible: yes/no
- Audit log: yes/no

### Revocation steps
1. <specific step to remove or scope-down the connector>
2. ...

### Gap (if activation declined or tool unavailable)
- No active connector for <service>. Approval required before activation.
  The requested action was NOT performed.
```

## Safety

- Default-closed: no external automation is activated without explicit approval. The absence of a "no" is not a "yes."
- Never print, log, or commit credentials, tokens, OAuth codes, or secrets — reference env var names only.
- Never run a money, production, or destructive external action without written approval and, where available, a dry-run or staging execution first.
- Only activate MCP servers and automation connectors from trusted, reviewed sources. Treat an unreviewed MCP server as untrusted code.
- Always leave a documented, actionable way to revoke access. If you cannot describe the revocation steps, do not activate the connector.
- If a task is misclassified as external when it is actually local, correct the classification and do the work locally — do not activate a connector unnecessarily.

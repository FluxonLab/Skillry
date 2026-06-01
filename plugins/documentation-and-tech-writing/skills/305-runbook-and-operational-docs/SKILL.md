---
name: runbook-and-operational-docs
description: Use when you need to write or audit incident runbooks and on-call operational docs — symptom-first triage, validated diagnostic and recovery commands, escalation paths and severity levels, rollback steps, and verification that service is restored.
---

# Runbook and Operational Docs

## Purpose

Produce operational documentation an on-call engineer can follow at 3 a.m. under pressure: incident runbooks keyed by symptom, exact diagnostic and recovery commands, clear severity levels and escalation paths, rollback procedures, and a "confirm recovery" step. A good runbook turns a stressful incident into a checklist. Each procedure must be specific, validated, and safe — fail-closed where an action is destructive.

## When to use

- A service is going to production or on-call and has no runbooks for its common failure modes.
- A postmortem found that responders lacked clear steps and improvised.
- Alerts fire but the on-call has no documented response for them.
- Escalation was unclear during an incident (who to page, when).
- Recovery/rollback steps exist informally in chat history and need to be captured.

## When not to use

- A personal project with no uptime expectation and no on-call.
- The need is teaching a concept or normal-usage how-to (use tutorial-and-how-to-writing).
- The change is a code fix, not an operational procedure (write the fix; runbook follows separately).

## Procedure

### 1. Enumerate failure modes from real signals

```bash
# Collect the alerts and signals that should each map to a runbook
grep -rEi "alert|severity|pager|threshold" monitoring/ alerts/ 2>/dev/null | head -40
ls runbooks/ docs/runbooks/ 2>/dev/null
```

List each alert/symptom that can page a human. Every pageable alert needs a runbook entry; an alert with no runbook is a gap.

### 2. Write each runbook symptom-first

The responder sees a symptom, not a root cause. Lead with the observable symptom and alert name, then severity, then triage. Title: "Symptom: API 5xx rate above 5%", not "Database connection pool internals".

### 3. Provide validated diagnostic commands

Give read-only diagnostics first — establish blast radius and likely cause before acting.

```bash
# Read-only triage block: scope the problem before changing anything
kubectl get pods -n prod -l app=api          # are pods healthy / restarting?
kubectl logs -n prod deploy/api --since=10m --tail=100 | grep -Ei "error|panic|timeout"
curl -sS -o /dev/null -w '%{http_code} %{time_total}s\n' "$HEALTHCHECK_URL"
```

### 4. Define severity levels and escalation

State what each severity means (user impact + response time) and exactly who/what is paged at each, with the time-to-escalate if unresolved.

### 5. Document recovery and rollback with explicit safety

Each mutating step states its effect and a verification. Destructive steps require confirmation and a pre-action snapshot/backup.

```bash
# Recovery example — restart, then VERIFY before declaring resolved
kubectl rollout restart deploy/api -n prod
kubectl rollout status deploy/api -n prod --timeout=120s

# Rollback to the previous known-good release (confirm version first)
kubectl rollout undo deploy/api -n prod
```

### 6. Close with a recovery-confirmation and comms step

End with the exact signal that proves recovery (alert cleared, success rate normal) and the incident-comms/update step. Add a postmortem trigger for high-severity incidents.

## Concrete checks

- [ ] Every pageable alert maps to exactly one runbook entry.
- [ ] Each runbook is titled by observable symptom, not internal cause.
- [ ] Severity levels are defined with user impact and response-time expectations.
- [ ] The escalation path names who/what is paged at each severity and when to escalate.
- [ ] Diagnostic commands are read-only and run before any mutating action.
- [ ] Every command is exact, copy-pasteable, and was validated to run.
- [ ] Mutating steps state their effect and a post-step verification.
- [ ] Destructive steps require confirmation and a backup/snapshot first.
- [ ] A rollback procedure to the last known-good state is documented.
- [ ] A "confirm recovery" step states the exact healthy signal.
- [ ] An incident-comms/update step is included.
- [ ] High-severity entries trigger a postmortem.
- [ ] No secrets are inline; credentials are referenced by env var name only.

## Templates

```markdown
# Runbook: API 5xx rate above 5%

**Severity:** SEV-2 (user-facing errors). Page: on-call API engineer.
**Escalate to** team lead if not mitigated in 15 min, **SEV-1** if checkout is down.

## Symptom
Alert `api_5xx_high` firing; users see 500s on the API.

## 1. Triage (read-only)
    kubectl get pods -n prod -l app=api
    kubectl logs -n prod deploy/api --since=10m --tail=100 | grep -Ei "error|timeout"
    curl -sS -o /dev/null -w '%{http_code}\n' "$HEALTHCHECK_URL"

## 2. Likely causes → action
- Pods crash-looping → restart: `kubectl rollout restart deploy/api -n prod`
- Bad recent deploy → roll back: `kubectl rollout undo deploy/api -n prod`
- DB unreachable → check `db_connections` dashboard; escalate to DBA on-call.

## 3. Confirm recovery
    kubectl rollout status deploy/api -n prod --timeout=120s
Alert `api_5xx_high` clears and 5xx rate < 1% for 5 min.

## 4. Comms
Post status in the incident channel: cause, action taken, current state.
SEV-1/SEV-2 require a postmortem within 48h.
```

```text
# Escalation matrix
SEV-1  full outage / data loss      page on-call + lead immediately; exec update 30m
SEV-2  major degradation            page on-call; escalate lead at 15m
SEV-3  minor / single feature       on-call handles; no immediate escalation
```

## Common issues & anti-patterns

- Runbooks organized by root cause, forcing the responder to diagnose before they can find the page.
- Vague steps ("restart the service") with no exact command for the actual platform.
- Mutating or destructive actions placed before any diagnosis.
- No verification step, so responders cannot tell if the fix worked.
- Missing or ambiguous escalation, so an incident stalls waiting on the wrong person.
- Secrets, tokens, or production hostnames pasted into the runbook.
- Stale runbooks referencing decommissioned hosts, tools, or dashboards.
- No rollback path, leaving "revert the deploy" as undocumented tribal knowledge.

## Required output

Produce: (1) the alert-to-runbook coverage list (gaps flagged); (2) per-symptom runbooks with severity, read-only triage, recovery, and rollback; (3) the severity/escalation matrix; (4) a recovery-confirmation signal per runbook; (5) a comms/postmortem step; (6) a list of unvalidated or destructive commands needing review.

## Safety

- Default to read-only diagnostics; never place destructive commands before triage.
- Require explicit confirmation and a backup/snapshot before any destructive recovery step.
- Reference all credentials by environment variable name; never inline secrets or tokens.
- Use placeholder hostnames and `$HOME`/relative paths; never real production endpoints or absolute machine paths.
- Validate commands in a safe environment; do not run mutating commands against production while authoring.

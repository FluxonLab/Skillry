---
name: deploy-topology-and-rollback
description: Use when you need to review or design a deployment topology and rollback strategy — blue-green, canary, and rolling deploys, health gates, automated rollback, zero-downtime cutover, and safe infrastructure change sequencing.
---

# Deploy Topology & Rollback

## Purpose

Review and design how a service is rolled out and rolled back — selecting blue-green, canary, or rolling strategies, wiring health and metric gates that automatically halt or revert a bad release, sequencing infrastructure changes so they are reversible, and achieving zero-downtime cutover including backward-compatible database changes. The goal is that every deploy can be paused and reverted quickly on a clear signal, with no manual heroics and no extended outage. This is a planning and authoring skill: it defines and reviews the rollout mechanism but does not trigger production deploys without human approval. Ground analysis in the project's actual deploy config and traffic-shaping resources.

## When to use

- A service needs a rollout strategy chosen (blue-green vs canary vs rolling) or its current one reviewed.
- A release process lacks automated rollback or health gates.
- Zero-downtime is required and current deploys cause downtime or dropped connections.
- A schema/migration change must ship without breaking the running version.
- An infrastructure change (LB, DNS, network) needs a reversible sequencing plan.
- A post-incident review wants faster, safer reverts.

## When not to use

- The work is CI/CD pipeline mechanics (runner stages, caching, build steps) — use the CI/CD pipeline review skill.
- The change is a Kubernetes manifest hardening pass — use the Kubernetes manifest review skill.
- A live, failing production deploy needs an emergency rollback now — a human operator must drive it.

## Procedure

### 1. Identify the current rollout mechanism

```bash
# Kubernetes strategy / progressive delivery controllers
grep -rn "strategy:\|RollingUpdate\|maxUnavailable\|maxSurge" . --include="*.yaml"
grep -rln "kind: Rollout\|Argo\|Flagger\|canary\|blueGreen" . --include="*.yaml"
# Traffic shaping: weighted target groups, service mesh, DNS/LB weights
grep -rn "weight\|target_group\|listener\|traffic\|VirtualService\|DestinationRule" . --include="*.tf" --include="*.yaml" | head
```

### 2. Review health and rollout gates

```bash
# Readiness probes feed rollout progress; without them rollouts "succeed" while broken
grep -rn "readinessProbe\|livenessProbe\|minReadySeconds\|progressDeadlineSeconds" . --include="*.yaml"
# Analysis/metric gates for canary (success rate, latency thresholds)
grep -rn "analysis\|successCondition\|metric\|threshold\|prometheus" . --include="*.yaml" | head
```

### 3. Confirm rollback is defined and automated

```bash
# Kubernetes keeps revision history for rollback
grep -rn "revisionHistoryLimit" . --include="*.yaml"
# Documented/automated rollback hooks or pipeline steps
grep -rniE "rollback|revert|undo|previous version|abort" . --include="*.yaml" --include="*.sh" docs/ 2>/dev/null | head
```

### 4. Check zero-downtime preconditions

```bash
# Graceful shutdown: preStop hook + terminationGracePeriod so in-flight requests drain
grep -rn "preStop\|terminationGracePeriodSeconds\|lifecycle:" . --include="*.yaml"
# PodDisruptionBudget protects availability during rollout/node drain
grep -rln "kind: PodDisruptionBudget" . --include="*.yaml"
```

### 5. Review database / migration compatibility

```bash
# Look for destructive/blocking migrations that break the old version mid-rollout
grep -rniE "drop column|drop table|rename column|alter .*not null|drop constraint" . --include="*.sql" migrations/ 2>/dev/null | head
# Expand/contract pattern markers
grep -rniE "expand|contract|backfill|add column|nullable" . --include="*.sql" migrations/ 2>/dev/null | head
```

### 6. Sequence infrastructure changes for reversibility

Order changes so each step is independently revertible: add the new resource, shift a small traffic slice, observe gates, increase, then retire the old resource last. Avoid changes that are hard to undo (DNS TTL flips, deleting the old environment) until the new one is proven.

## Concrete checks

- [ ] A rollout strategy is explicitly chosen (blue-green, canary, or rolling) and matches risk tolerance.
- [ ] Rolling updates set `maxUnavailable`/`maxSurge` and `progressDeadlineSeconds`.
- [ ] Readiness probes gate traffic; a failed probe blocks the rollout from progressing.
- [ ] Canary deploys have automated analysis (success rate/latency) that aborts on regression.
- [ ] A rollback path exists and is automated or one-command (`rollout undo`, redeploy previous, flip weight back).
- [ ] `revisionHistoryLimit` retains enough history to roll back.
- [ ] Graceful shutdown is configured (`preStop`, `terminationGracePeriodSeconds`) so connections drain.
- [ ] A `PodDisruptionBudget` (or equivalent) preserves capacity during the rollout.
- [ ] Database migrations follow expand/contract — backward compatible with the previous app version.
- [ ] No single-step destructive migration runs in the same release that depends on it.
- [ ] Infrastructure change steps are ordered so each is independently reversible.
- [ ] A clear abort signal and owner are defined for halting a release.

## Commands or Templates

```yaml
# Rolling update with health gating (zero-downtime) — review target
apiVersion: apps/v1
kind: Deployment
spec:
  minReadySeconds: 10
  progressDeadlineSeconds: 120     # rollout fails (and can auto-revert) if stuck
  revisionHistoryLimit: 10         # keeps revisions for rollback
  strategy:
    type: RollingUpdate
    rollingUpdate: { maxUnavailable: 0, maxSurge: 1 }
  template:
    spec:
      terminationGracePeriodSeconds: 30
      containers:
        - name: api
          readinessProbe:
            httpGet: { path: /healthz, port: 8080 }
          lifecycle:
            preStop: { exec: { command: ["sleep", "10"] } }  # drain before exit
```

```yaml
# Canary with automatic abort (Argo Rollouts style)
apiVersion: argoproj.io/v1alpha1
kind: Rollout
spec:
  strategy:
    canary:
      steps:
        - setWeight: 10
        - pause: { duration: 5m }
        - analysis: { templates: [{ templateName: success-rate }] } # aborts on regression
        - setWeight: 50
        - pause: { duration: 5m }
```

```bash
# Rollback commands — RUN ONLY WITH HUMAN APPROVAL
kubectl rollout status deploy/api --timeout=120s   # observe (safe)
kubectl rollout history deploy/api                 # inspect revisions (safe)
kubectl rollout undo deploy/api --to-revision=<n>  # MUTATING — approval required
```

## Common issues & anti-patterns

- "Recreate" strategy (or `maxUnavailable: 100%`) on a user-facing service — guaranteed downtime.
- Rollout reports success because there is no readiness probe, while pods are actually broken.
- Canary with no metric analysis — the bad version is promoted to 100% automatically.
- No rollback plan: reverting means re-running a forward pipeline and hoping.
- Destructive migration (`DROP COLUMN`, `NOT NULL` without default) shipped with the code that needs it — old pods crash mid-rollout and rollback is impossible.
- No graceful shutdown — in-flight requests are dropped on every pod replacement.
- Deleting the old (blue) environment before the new one is verified — nothing to roll back to.
- Flipping DNS with a long TTL as the cutover mechanism — slow, hard to revert.

## Required output

Produce a structured report with:
1. **Current topology** — detected strategy and traffic-shaping mechanism.
2. **Health gates** — probes and analysis gates that control rollout progress; gaps.
3. **Rollback** — whether a fast, automated rollback exists and how it is triggered.
4. **Zero-downtime** — graceful shutdown, PDB, surge settings; any downtime sources.
5. **Migration safety** — expand/contract compliance; flagged destructive migrations.
6. **Sequencing** — reversible ordering plan for the infra changes in scope.
7. **Findings table** — `file:line | issue | severity | concrete fix`.
8. **Next safe action** — the safest first step and the defined abort signal/owner.

## Safety

- This is a planning and authoring skill. NEVER trigger a production deploy, promotion, traffic shift, or rollback (`kubectl rollout undo/restart`, `argo rollouts promote`, weight changes, DNS/LB cutover) without explicit human approval.
- Only read-only inspection (`rollout status`, `rollout history`, `kubectl get`, reading config) is safe to run unattended.
- Never run a destructive database migration as part of a deploy review; flag it and require the expand/contract pattern and human sign-off.
- Do not delete or scale down the previous (stable) environment until the new release is verified and approved — preserve the rollback target.
- Define and surface the abort signal and owner before any rollout; do not let an automated promotion proceed without a working gate.
- Redact any secrets encountered in deploy config to `****`; do not print them in the report.

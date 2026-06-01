---
name: kubernetes-manifest-review
description: Use when you need to review or author Kubernetes manifests or Helm charts for resource requests and limits, liveness/readiness/startup probes, pod security context, RBAC scope, network policy, HPA, secret handling, and common workload anti-patterns.
---

# Kubernetes Manifest Review

## Purpose

Conduct a structured review-and-author pass over Kubernetes manifests, Kustomize overlays, or Helm charts — covering resource requests/limits, liveness/readiness/startup probes, pod and container security context, RBAC least privilege, NetworkPolicy isolation, autoscaling (HPA), secret handling, and reliability anti-patterns. The goal is workloads that schedule predictably, fail safely, run unprivileged, and expose the minimum surface. Findings must come from the actual YAML and a server-side dry-run, never from assumptions, and nothing is applied to a live cluster without human approval.

## When to use

- A PR adds or changes manifests under `k8s/`, `manifests/`, `deploy/`, a Helm `templates/` dir, or `values.yaml`.
- Pods are OOMKilled, CPU-throttled, evicted, or crash-looping due to missing limits/probes.
- A `Deployment`, `StatefulSet`, `DaemonSet`, `Service`, `Ingress`, RBAC, or `NetworkPolicy` is being introduced.
- Containers run as root, privileged, or with broad RBAC and you need a security pass.
- Autoscaling or rollout behavior needs review before a release.

## When not to use

- The change is application code only, with no manifest or chart change.
- The cluster uses a different orchestrator (Nomad, ECS) — adapt principles, not commands.
- The task is a production incident needing an emergency rollout — escalate to a human operator.

## Procedure

### 1. Orient to the manifests

```bash
find . -path "*/k8s/*" -o -name "*.yaml" -path "*manifests*" 2>/dev/null
grep -rln "^kind:" . --include="*.yaml" | head
grep -rhE "^kind:" . --include="*.yaml" | sort | uniq -c   # inventory of object kinds
```

### 2. Validate structure without touching the cluster

```bash
# Client-side validation only — no cluster mutation
kubectl apply --dry-run=client -f manifests/ 2>&1 | tail -20
# Stronger static schema validation if available
kubeconform -strict -summary manifests/ 2>/dev/null || echo "kubeconform not installed"
# Render Helm to inspect the real output
helm template ./chart -f chart/values.yaml > rendered.yaml 2>/dev/null
```

### 3. Check resource requests and limits

```bash
# Containers missing requests/limits are unschedulable-safe risks (noisy-neighbor, OOM)
grep -rL "resources:" manifests/ --include="*.yaml"
grep -rn "requests:\|limits:\|memory:\|cpu:" manifests/ --include="*.yaml"
```

### 4. Check probes

```bash
grep -rn "livenessProbe\|readinessProbe\|startupProbe" manifests/ --include="*.yaml"
# Workloads with containers but no readinessProbe send traffic to unready pods
```

### 5. Audit security context and RBAC

```bash
# Pod/container security context
grep -rn "runAsNonRoot\|runAsUser\|allowPrivilegeEscalation\|readOnlyRootFilesystem\|privileged\|capabilities" manifests/ --include="*.yaml"
# RBAC wildcards (over-permission)
grep -rn "verbs:\|resources:\|apiGroups:" manifests/ --include="*.yaml"
grep -rn "\"\*\"\|- '\*'\|- \"\*\"" manifests/ --include="*.yaml"
grep -rn "kind: ClusterRoleBinding" manifests/ --include="*.yaml"  # prefer namespaced RoleBinding
```

### 6. Check network policy, secrets, and autoscaling

```bash
grep -rln "kind: NetworkPolicy" manifests/ --include="*.yaml" || echo "no NetworkPolicy — default-allow traffic"
# Secrets must not be inline plaintext literals in manifests
grep -rn "kind: Secret" -A6 manifests/ --include="*.yaml"
grep -rn "stringData:\|data:" manifests/ --include="*.yaml"
grep -rln "kind: HorizontalPodAutoscaler" manifests/ --include="*.yaml"
```

## Concrete checks

- [ ] Every container sets CPU and memory `requests` and `limits`.
- [ ] Every long-running service container has a `readinessProbe` and a `livenessProbe`; slow starters use a `startupProbe`.
- [ ] Pod security context sets `runAsNonRoot: true` and a non-zero `runAsUser`.
- [ ] Container security context sets `allowPrivilegeEscalation: false`, `readOnlyRootFilesystem: true`, and drops `ALL` capabilities.
- [ ] No container runs `privileged: true` or mounts the host network/PID/filesystem without justification.
- [ ] RBAC uses namespaced `Role`/`RoleBinding` where possible; no `verbs/resources/apiGroups: ["*"]` ClusterRoles.
- [ ] A `NetworkPolicy` restricts ingress/egress for sensitive workloads (default-deny baseline).
- [ ] Secrets are referenced via `secretKeyRef`/`envFrom`, not hardcoded plaintext in manifests.
- [ ] An `HorizontalPodAutoscaler` (or documented fixed replica count) governs scaling.
- [ ] Deployments set `strategy` (RollingUpdate with sane `maxUnavailable`/`maxSurge`).
- [ ] A `PodDisruptionBudget` protects multi-replica services during node drains.
- [ ] Image tags are pinned (not `:latest`) with `imagePullPolicy` consistent with the tag.

## Commands or Templates

```yaml
# Hardened Deployment container spec — review target
apiVersion: apps/v1
kind: Deployment
metadata: { name: api, namespace: prod }
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate: { maxUnavailable: 0, maxSurge: 1 }
  template:
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 65532
        seccompProfile: { type: RuntimeDefault }
      containers:
        - name: api
          image: registry.example.com/api:1.4.2   # pinned, not latest
          resources:
            requests: { cpu: "100m", memory: "128Mi" }
            limits:   { cpu: "500m", memory: "256Mi" }
          readinessProbe:
            httpGet: { path: /healthz, port: 8080 }
            initialDelaySeconds: 5
          livenessProbe:
            httpGet: { path: /livez, port: 8080 }
            periodSeconds: 10
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities: { drop: ["ALL"] }
          envFrom:
            - secretRef: { name: api-secrets }   # not inline plaintext
```

```yaml
# Default-deny NetworkPolicy baseline
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: default-deny, namespace: prod }
spec:
  podSelector: {}
  policyTypes: ["Ingress", "Egress"]
```

```bash
# Safe review commands — never mutate the cluster
kubectl apply --dry-run=client -f manifests/   # client-side only
kubeconform -strict -summary manifests/
helm template ./chart | kubeconform -strict -summary -
```

## Common issues & anti-patterns

- No resource limits — one pod starves the node; no requests — the scheduler misplaces pods.
- No readiness probe — traffic hits pods before they are ready, causing 5xx during rollout.
- Liveness probe pointed at a slow/expensive endpoint — healthy pods get killed in a loop.
- `runAsNonRoot` absent and containers run as UID 0; `privileged: true` "to make it work".
- ClusterRole with `["*"]` verbs/resources bound to a workload ServiceAccount.
- No NetworkPolicy — every pod can talk to every other pod (lateral movement risk).
- Plaintext secrets committed in a `Secret` manifest (base64 is encoding, not encryption).
- `image: app:latest` — non-reproducible rollouts and broken rollbacks.

## Required output

Produce a structured report with:
1. **Inventory** — object kinds and counts; validation/dry-run result.
2. **Resources** — containers missing requests/limits.
3. **Probes** — missing readiness/liveness/startup probes per workload.
4. **Security context** — root/privileged containers; missing hardening fields.
5. **RBAC & network** — wildcard roles, ClusterRoleBindings, missing NetworkPolicy.
6. **Secrets & scaling** — plaintext secrets (redacted); HPA/PDB/strategy presence.
7. **Findings table** — `file:line | issue | severity | concrete fix`.
8. **Next safe action** — highest-priority change before any apply.

## Safety

- This is a review and authoring skill. NEVER run `kubectl apply` (server-side), `kubectl delete`, `kubectl scale`, `kubectl rollout`, `kubectl drain/cordon`, or `helm install/upgrade/uninstall` against a real cluster without explicit human approval.
- Only `--dry-run=client`, `kubeconform`, and `helm template` are safe to run unattended — they do not touch the cluster.
- Never put real secret values into a manifest; reference a secret manager, sealed secret, or external secret operator.
- Base64 in a `Secret` is not encryption — redact discovered secret values to `****` and flag for rotation.
- Do not change RBAC bindings, namespaces, or finalizers in ways that could lock out operators without sign-off.
- If a change would delete a `StatefulSet`, PVC, or namespace, stop and require explicit human approval.

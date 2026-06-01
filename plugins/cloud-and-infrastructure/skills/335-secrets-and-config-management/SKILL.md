---
name: secrets-and-config-management
description: Use when you need to review or design secret and configuration handling — secret managers (Vault, AWS Secrets Manager, SSM, GCP/Azure), rotation, runtime injection, keeping secrets out of IaC and images, sealed/external secrets, and config-vs-secret separation.
---

# Secrets & Config Management

## Purpose

Review and design how an application and its infrastructure handle secrets and configuration — selecting a secret manager (Vault, AWS Secrets Manager, SSM Parameter Store, GCP Secret Manager, Azure Key Vault), defining rotation, injecting secrets at runtime rather than baking them into images or IaC, separating non-sensitive config from secrets, and using sealed/external secrets in Kubernetes. The goal is that no secret ever lives in source, IaC state, container layers, or logs, that every secret is rotatable, and that access is least-privilege and audited. Ground findings in the repo's actual files and manifests.

## When to use

- A PR introduces credentials, API keys, tokens, connection strings, or certificates.
- A secret manager needs to be chosen or its access pattern reviewed.
- Secrets are suspected in source, `.env`, IaC, container images, or CI logs.
- Rotation is missing, manual, or unknown for a credential.
- Kubernetes secret handling needs review (plaintext `Secret` vs sealed/external secrets).
- A config system mixes secrets and non-secret settings without separation.

## When not to use

- The task is broad application env-config typing with no secret/security dimension — a lighter config review fits.
- The repo has no secrets and no infrastructure that consumes them.
- A full authorization/permission model review is needed — pair with the authz review skill.

## Procedure

### 1. Scan the repo for leaked secrets

```bash
# High-signal patterns across the tree (exclude vendored/build dirs)
grep -rniE "(api[_-]?key|secret|password|token|passwd|private[_-]?key|client[_-]?secret)\s*[:=]\s*['\"][^'\"$]{6,}" \
  . --include="*.*" 2>/dev/null | grep -vE "example|sample|test|\.lock|node_modules" | head -40
# Provider key shapes (AWS access key id, private key blocks)
grep -rnE "AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----" . 2>/dev/null | head
# Dedicated scanners if available
gitleaks detect --no-banner 2>/dev/null || trufflehog filesystem . 2>/dev/null | tail -20
```

### 2. Check that secrets are gitignored and not in history

```bash
git ls-files | grep -E "\.env$|\.env\.|secrets?\.(ya?ml|json)|\.pem$|credentials$" && echo "TRACKED SECRET FILES — CRITICAL"
grep -E "\.env|secrets|\.pem|credentials" .gitignore 2>/dev/null || echo "secret files not gitignored"
```

### 3. Identify the secret manager and injection path

```bash
# Which secret backend is referenced?
grep -rniE "secretsmanager|ssm|parameter store|vault|key.?vault|secret.?manager|sealed.?secret|external.?secret" . --include="*.tf" --include="*.yaml" --include="*.y*ml" | head
# How does the app read config/secrets at runtime?
grep -rnE "os\.environ|process\.env|getenv|System\.getenv|Environment\.GetEnvironmentVariable" . 2>/dev/null | head
```

### 4. Verify secrets are not baked into IaC or images

```bash
# Plaintext secret values in IaC / vars
grep -rnE "(password|secret|token|key)\s*=\s*\"[^\"$]" . --include="*.tf" --include="*.tfvars" | grep -v "secretsmanager\|ssm\|vault\|data\." | head
# Secrets baked into Docker layers
grep -rnE "ARG .*(SECRET|TOKEN|PASSWORD|KEY)|ENV .*(SECRET|TOKEN|PASSWORD)|COPY .*(\.env|\.pem|credentials)" . --include="Dockerfile*"
```

### 5. Review Kubernetes secret handling

```bash
# Plaintext Secret manifests vs sealed/external secrets
grep -rn "kind: Secret" -A4 . --include="*.yaml" | grep -i "stringData\|data:"
grep -rln "kind: SealedSecret\|kind: ExternalSecret\|kind: SecretStore" . --include="*.yaml"
```

### 6. Confirm rotation and config/secret separation

```bash
# Rotation hooks (Secrets Manager rotation lambda, Vault TTL/lease, dynamic secrets)
grep -rniE "rotation|rotate|lease|ttl|max_ttl" . --include="*.tf" --include="*.hcl" | head
# Non-secret config should live separately from secrets (configmaps / settings vs secret refs)
grep -rln "kind: ConfigMap" . --include="*.yaml"
```

## Concrete checks

- [ ] No secret value appears in source, `.tfvars`, manifests, Dockerfiles, or committed `.env` files.
- [ ] `.env`, `*.pem`, `credentials`, and secret YAML/JSON are gitignored and absent from git history.
- [ ] A secret manager (Vault/Secrets Manager/SSM/Key Vault/GCP) is the source of truth for secrets.
- [ ] Secrets are injected at runtime (env from secret ref, mounted file, or sidecar), not at build time.
- [ ] IaC references secrets by ARN/path/data source — it never stores the plaintext value.
- [ ] Kubernetes uses SealedSecrets or an ExternalSecrets operator instead of committing plaintext `Secret`s.
- [ ] Every secret has a defined rotation policy (automatic rotation, short-lived/dynamic, or scheduled).
- [ ] Access to each secret is least-privilege (scoped IAM/policy/Vault role), not broad read-all.
- [ ] Secret access is audited/logged by the manager.
- [ ] Non-secret configuration is separated from secrets (ConfigMap/settings vs secret store).
- [ ] Secrets are never logged; logging redacts known secret keys.
- [ ] CI/CD pulls secrets from a vault/OIDC at run time, not from committed files or plaintext variables.

## Commands or Templates

```hcl
# Terraform: reference a secret, never store its value
data "aws_secretsmanager_secret_version" "db" {
  secret_id = "prod/db/password"   # value lives in Secrets Manager
}

resource "aws_db_instance" "primary" {
  username = "app"
  password = data.aws_secretsmanager_secret_version.db.secret_string # not hardcoded
}

# Scoped read policy — least privilege to ONE secret
data "aws_iam_policy_document" "read_db_secret" {
  statement {
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [aws_secretsmanager_secret.db.arn] # not "*"
  }
}
```

```yaml
# Kubernetes: ExternalSecret pulls from the manager into a native Secret at runtime
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata: { name: api-secrets, namespace: prod }
spec:
  refreshInterval: 1h
  secretStoreRef: { name: aws-secrets, kind: SecretStore }
  target: { name: api-secrets }
  data:
    - secretKey: DB_PASSWORD
      remoteRef: { key: prod/db/password }
```

```bash
# Safe detection only — never print the secret value
gitleaks detect --no-banner --redact          # redacts matches in output
aws secretsmanager describe-secret --secret-id prod/db/password  # metadata, not value
```

## Common issues & anti-patterns

- Secrets committed in `.env`, `config.json`, or `.tfvars` — and still present in git history after "removal".
- Plaintext password in a `*.tf` file or a Kubernetes `Secret` manifest (base64 is not encryption).
- Secrets passed as Docker build `ARG`/`ENV` — permanently embedded in image history.
- One static credential shared by every service and never rotated.
- A single broad policy granting `secretsmanager:GetSecretValue` on `*`.
- Mixing secrets into ConfigMaps or non-secret settings files.
- Logging full request/connection objects that include credentials.
- CI storing long-lived cloud keys as plaintext variables instead of using OIDC/short-lived tokens.

## Required output

Produce a structured report with:
1. **Leak scan** — any secrets found in source/IaC/images/history (redacted), with file:line.
2. **Storage** — which secret manager is used and what is still stored outside it.
3. **Injection** — runtime vs build-time injection path per secret consumer.
4. **Kubernetes** — plaintext Secrets vs sealed/external secrets status.
5. **Rotation** — rotation policy (or its absence) per secret.
6. **Access** — least-privilege review of secret-read policies.
7. **Config separation** — secrets vs non-secret config mixing.
8. **Findings table + next safe action** — `file:line | issue | severity | fix`, then the top remediation.

## Safety

- This is a review and design skill. NEVER print, echo, or log a real secret value; always redact to `****`. Use scanner `--redact` flags and read only secret *metadata*, never the value, unless a human explicitly requests it.
- NEVER create, overwrite, rotate, or delete secrets in a live manager (`aws secretsmanager put/delete`, `vault write`, `kubectl create secret`) without explicit human approval.
- Treat any secret found in source or git history as compromised — flag it for immediate rotation and removal from history; do not assume removing the file is sufficient.
- Do not commit any file containing a real secret; do not move secrets between systems without approval.
- Recommend rotation and least-privilege scoping; do not apply IAM/policy changes to a live account unattended.
- Do not disable audit logging on a secret manager.

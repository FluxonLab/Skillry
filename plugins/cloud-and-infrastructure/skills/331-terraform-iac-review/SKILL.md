---
name: terraform-iac-review
description: Use when you need to review Terraform or OpenTofu infrastructure-as-code for remote state and locking correctness, module structure, drift, plan safety, hardcoded secrets, provider pinning, and least-privilege IAM before any apply.
---

# Terraform / OpenTofu IaC Review

## Purpose

Conduct a structured, read-and-author review of Terraform or OpenTofu code — covering remote state backend and locking, module boundaries and reuse, variable and output hygiene, provider and version pinning, drift between code and live infrastructure, hardcoded secrets, and least-privilege IAM in generated policies. The goal is to make the configuration safe, reproducible, and reviewable so a human can approve a `plan` before any `apply` touches real cloud resources. Surface concrete findings from actual `.tf` files and `terraform plan` output, never from assumptions.

## When to use

- A PR adds or changes `*.tf`, `*.tofu`, `*.tfvars`, backend config, or a module under `modules/`.
- State management is unclear: no remote backend, no locking, or state may be committed to git.
- A `terraform plan` shows unexpected destroys/replacements and you need to triage drift.
- IAM policies, security groups, buckets, or network rules are being created or widened.
- Provider or module versions are unpinned and upgrades are unpredictable.
- You are onboarding into an IaC repo and need a health and safety baseline.

## When not to use

- The change is CI/CD pipeline wiring only (runner config, workflow YAML) — that is a pipeline review, not IaC.
- The repo uses a different IaC tool (Pulumi, CloudFormation, CDK) — adapt the principles but the commands differ.
- The task is a live incident requiring an emergency `apply` — escalate to a human operator; do not self-approve.

## Procedure

### 1. Orient to the repo and backend

```bash
# Find Terraform/OpenTofu roots and modules
find . -name "*.tf" -not -path "*/.terraform/*" | sed 's#/[^/]*$##' | sort -u
# Inspect backend + required versions (read only)
grep -rn "backend\s*\"" . --include="*.tf"
grep -rn "required_version\|required_providers" . --include="*.tf"
# Which binary and version?
terraform version 2>/dev/null || tofu version 2>/dev/null
```

### 2. Verify state is remote, locked, and never committed

```bash
# State files must NOT be tracked in git
git ls-files | grep -E "terraform\.tfstate|\.tfstate\.backup" && echo "STATE IN GIT — CRITICAL"
# .gitignore should exclude local state + .terraform
grep -E "tfstate|\.terraform" .gitignore 2>/dev/null || echo "WARNING: state not gitignored"
# Confirm a remote backend with locking (s3+dynamodb, gcs, azurerm, or remote)
grep -rn "backend\s*\"\(s3\|gcs\|azurerm\|remote\)\"" . --include="*.tf"
grep -rn "dynamodb_table\|use_lockfile" . --include="*.tf"  # S3 locking
```

### 3. Review init and validate (no apply)

```bash
terraform init -backend=false   # offline structural init, no remote writes
terraform validate
terraform fmt -check -recursive  # report unformatted files
```

### 4. Generate a plan for review (read-only against state)

```bash
# -lock=false only if you are certain no apply is concurrent; otherwise keep locking
terraform plan -out=tfplan -input=false -no-color | tee plan.txt
# Machine-readable diff for triage
terraform show -json tfplan > tfplan.json
# Count creates / updates / destroys / replacements
grep -E "will be (created|destroyed|replaced)|must be replaced" plan.txt | sort | uniq -c
```

Treat every `destroy` and `must be replaced` line as a finding: confirm it is intended and reversible before a human applies.

### 5. Audit secrets and sensitive values

```bash
# Hardcoded credentials or keys in code/vars
grep -rEn "(secret|password|token|access_key|private_key)\s*=\s*\"[^\"$]" . --include="*.tf" --include="*.tfvars"
# Sensitive values that should be marked sensitive
grep -rn "variable\s\+\"" . --include="*.tf"
grep -rn "sensitive\s*=\s*true" . --include="*.tf"
# Plaintext secrets that leak into state (passwords on resources) need a secret manager ref instead
```

### 6. Review modules, providers, and IAM least privilege

```bash
# Unpinned modules (no version / ref) and providers (no = constraint)
grep -rn "source\s*=\s*\"\(git::\|github.com\)" . --include="*.tf" | grep -v "ref=\|?ref"
grep -rn "version\s*=" . --include="*.tf" | grep -E "\">=|~>|\"\*\""
# Wildcards in IAM policy documents (over-permission)
grep -rn "\"Action\".*\"\*\"\|actions\s*=\s*\[\"\*\"\]\|\"Resource\".*\"\*\"" . --include="*.tf"
# Wide-open ingress
grep -rn "0\.0\.0\.0/0\|::/0" . --include="*.tf"
```

## Concrete checks

- [ ] A remote backend (s3+lock, gcs, azurerm, or `remote`) is configured — no purely local state.
- [ ] State locking is enabled (DynamoDB table, `use_lockfile`, or backend-native locking).
- [ ] `*.tfstate` is gitignored and not tracked in the repo.
- [ ] `required_version` and every provider in `required_providers` are pinned with `~>` or `=`.
- [ ] External modules are pinned to a tag/commit (`?ref=vX.Y.Z`), not a floating branch.
- [ ] `terraform validate` passes and `terraform fmt -check` is clean.
- [ ] The plan has zero unexplained `destroy` / `must be replaced` lines.
- [ ] No secrets are hardcoded in `.tf` or `.tfvars`; secrets come from a secret manager or sensitive vars.
- [ ] Variables holding secrets are marked `sensitive = true`.
- [ ] No IAM policy uses `Action: "*"` on `Resource: "*"`; permissions are scoped.
- [ ] No security group exposes management ports (22, 3389, db ports) to `0.0.0.0/0`.
- [ ] `.tfvars` files containing real values are gitignored; an `.tfvars.example` documents shape.

## Commands or Templates

```hcl
# Remote backend with locking (S3 example) — review target
terraform {
  required_version = "~> 1.7"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.40"
    }
  }
  backend "s3" {
    bucket       = "org-tf-state"
    key          = "prod/network/terraform.tfstate"
    region       = "eu-central-1"
    encrypt      = true
    use_lockfile = true # native S3 state locking
  }
}
```

```hcl
# Pinned external module + sensitive variable
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.8.1" # pinned, not a branch
}

variable "db_password" {
  type      = string
  sensitive = true # never printed in plan/apply output
}
```

```bash
# Safe review loop — no mutation of real infrastructure
terraform init -backend=false
terraform validate && terraform fmt -check -recursive
terraform plan -out=tfplan -input=false        # produce plan for HUMAN approval
terraform show -json tfplan | jq '.resource_changes[] | select(.change.actions[] | . == "delete")'
```

## Common issues & anti-patterns

- Local-only state, or `terraform.tfstate` committed to git — collaborators overwrite each other and secrets leak.
- No state locking — concurrent applies corrupt state.
- Floating versions (`>=`, `latest`, branch refs) — non-reproducible builds and surprise upgrades.
- Secrets in `.tfvars` committed to the repo, or plaintext passwords that land in state.
- `Action: "*"` / `Resource: "*"` IAM policies and `0.0.0.0/0` ingress — least-privilege violations.
- Monolithic root module with no separation of environments — one plan can blast prod.
- Running `apply` straight from CI on every push with no manual gate.
- Disabling locking (`-lock=false`) routinely to "make plans faster".

## Required output

Produce a structured report with:
1. **Backend & state** — backend type, locking mechanism, and whether state is git-tracked.
2. **Version pinning** — Terraform/OpenTofu and provider/module pin status; list unpinned items.
3. **Plan summary** — counts of create/update/destroy/replace; each destroy/replace explained.
4. **Secrets** — any hardcoded secrets (redacted), unmarked sensitive vars, state-leak risks.
5. **IAM & network** — wildcard policies, wide-open ingress, with file:line.
6. **Findings table** — `file:line | issue | severity | concrete fix`.
7. **Next safe action** — the single change a human should make before any `apply`.

## Safety

- This is a review and authoring skill. NEVER run `terraform apply`, `terraform destroy`, `terraform import`, `terraform state rm/mv`, or `terraform taint` without explicit human approval.
- Only `init -backend=false`, `validate`, `fmt -check`, `plan`, and `show` are safe to run unattended — and `plan` exists to be reviewed by a human, not auto-applied.
- Never write real secret values into `.tf`/`.tfvars`; reference a secret manager or use sensitive variables.
- Redact any discovered credentials to `****` and flag them for rotation and removal from history.
- Do not modify backend configuration or state without approval — a wrong backend change can orphan resources.
- If a plan shows destroys of stateful resources (databases, volumes), stop and require explicit human sign-off.

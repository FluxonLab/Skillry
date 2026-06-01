---
name: ci-cd-pipeline-review
description: Use when you need to review CI jobs, workflow triggers, caches, matrixes, artifacts, and safe release gates.
---

# CI/CD Pipeline Review

## Purpose

Audit GitHub Actions workflows, GitLab CI pipelines, CircleCI configs, or equivalent: trigger correctness, secret handling, job dependency ordering, cache hygiene, matrix configuration, artifact retention, fail-fast behavior, and deployment gate safety. Identify security misconfigurations, unnecessary permissions, and reliability anti-patterns — each with a `file:line` and a concrete fix. The review is read-only: it never triggers a run, approves a deploy, or prints a secret value.

## When to use

- A new workflow file is added or an existing one is significantly modified.
- CI is slow and you need to find caching or parallelization improvements.
- A security review flags the pipeline (secret exposure, overly broad `GITHUB_TOKEN` permissions).
- Deployments fail non-deterministically and the cause is suspected to be in the pipeline config.
- A PR workflow accidentally triggers on pushes to protected branches or production environments.

## When not to use

- The pipeline works correctly and the task is to add an application feature unrelated to CI.
- The review concerns application code quality, not pipeline infrastructure.
- A dedicated DevOps team owns the pipeline and has a separate review process.

## Procedure

1. **Identify all workflow files.** Find `.github/workflows/*.yml`, `.gitlab-ci.yml`, `.circleci/config.yml`, `Jenkinsfile`, or equivalent. List each workflow, its triggers, and its purpose.
2. **Audit trigger configuration.** Verify `pull_request` vs `push` vs `workflow_dispatch` are used appropriately; deploy/release workflows trigger only on `push` to the default branch or tags, never on `pull_request`; `workflow_run` triggers do not grant elevated permissions to fork PRs; `schedule` intervals are reasonable (not sub-5-minute).
3. **Review `GITHUB_TOKEN` permissions.** Check `permissions:` at workflow and job level. Least privilege applies: a test-only job needs `contents: read` at most. Flag `permissions: write-all` or a missing block (defaults to repo settings, often too broad).
4. **Audit secret usage.** For every `${{ secrets.FOO }}`: is it needed in that job? Confirm it is not echoed to logs (`echo`, `run: env`, `::debug::`) and is passed to third-party actions as env vars, not inline args (args appear in logs).
5. **Check job dependency ordering.** Verify `needs:` chains tests before deploy and release jobs depend on all required gates. Flag a missing `needs:` that lets a deploy run concurrently with tests.
6. **Review cache configuration.** Cache keys include a lockfile hash (`hashFiles('**/package-lock.json')`); restore keys are ordered specific to general; PR caches cannot poison the main branch.
7. **Audit matrix strategies.** Confirm `fail-fast` is intentional per matrix; dimensions are not combinatorially explosive (3x3x3 = 27 jobs per PR is likely too many).
8. **Check artifact retention and naming.** Artifacts have explicit `retention-days`; names are unique across matrix legs (include `${{ matrix.os }}`).
9. **Verify deployment gates.** All test jobs are in the deploy job's `needs:`; production deploys require manual approval via `environment:` protection; deploy runs with environment-scoped secrets.
10. **Check self-hosted runner risks.** Self-hosted runners used for PR workflows must not have production secret access — fork PRs can run on them and exfiltrate env vars.

## Concrete checks

- [ ] Deploy/release workflows trigger only on protected-branch push or tags, not on PR.
- [ ] `permissions:` is set at workflow or job level with minimum required scopes.
- [ ] Secrets are passed as env vars, not inline args; not echoed to logs.
- [ ] Job `needs:` graph ensures tests complete before any deploy job starts.
- [ ] Cache keys include a lockfile hash; restore keys are ordered specific to general.
- [ ] `fail-fast` behavior is intentional for each matrix configuration.
- [ ] Artifact `retention-days` is explicitly set.
- [ ] Production deploy jobs require manual approval via `environment:` protection rules.
- [ ] Self-hosted runners used for PR workflows have no production secret access.
- [ ] Scheduled workflow intervals are reasonable (not sub-5-minute).
- [ ] Third-party actions are pinned to a commit SHA, not a mutable tag.

## Commands or Templates

```bash
# List workflows and their trigger blocks
for f in .github/workflows/*.yml .github/workflows/*.yaml; do
  echo "== $f =="; grep -nE "^(on|name):|push:|pull_request:|workflow_dispatch:|schedule:" "$f"
done

# Find over-broad permissions and unpinned actions
grep -rn "write-all\|permissions:" .github/workflows/
grep -rnE "uses:\s+\S+@(v?[0-9]+|main|master)\b" .github/workflows/   # mutable refs -> pin to SHA

# Find secrets echoed to logs (high-risk)
grep -rnE "echo .*secrets\.|run:\s*env\b|::debug::" .github/workflows/

# Find deploy jobs missing a needs: gate
grep -rnE "environment:|deploy" .github/workflows/
```

```yaml
# Least-privilege + pinned action + gated deploy (target pattern)
permissions:
  contents: read
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<commit-sha>   # pinned, not @v4
  deploy:
    needs: [test]                              # gate: tests must pass first
    environment: production                    # manual approval via protection rule
    runs-on: ubuntu-latest
```

## Severity rubric

Rank findings by exploitability and blast radius so the report drives action:

- **Critical** — a fork PR can obtain `write` permissions or read production secrets (e.g., `pull_request_target` running untrusted code with secrets, or self-hosted PR runners with prod access). An attacker can exfiltrate secrets or push to the repo.
- **High** — `write-all` or broad `permissions:` on a workflow that handles untrusted input; a deploy job missing a test `needs:` gate; an unpinned third-party action used in a privileged job.
- **Medium** — a secret echoed to logs, cache keys without a lockfile hash (poisoning risk within the repo), no environment protection on a non-critical deploy.
- **Low** — missing `retention-days`, sub-5-minute schedules, all-sequential jobs (cost/time only, no security impact).

A misconfiguration's severity rises sharply when it sits on a trigger reachable by an untrusted actor (`pull_request` from forks, `workflow_run`), and falls when it is only reachable by trusted maintainers on a protected branch.

## Worked example

A workflow contains:

```yaml
on: [pull_request_target]
permissions: write-all
jobs:
  test:
    steps:
      - uses: actions/checkout@v4
        with: { ref: ${{ github.event.pull_request.head.sha }} }
      - run: npm install && npm test    # runs the PR's code with write-all + secrets
```

Report as **Critical** at the `on:` and `permissions:` lines: `pull_request_target` runs with the base repo's secrets and `write-all` token, but checks out and executes the *fork's* untrusted code — a classic exfiltration path. Fix: use `pull_request` (no secrets for forks) for tests, scope `permissions: contents: read`, and never check out + execute fork code under `pull_request_target`. This single pattern is the highest-value thing to grep for in any public repo's CI.

## Common issues & anti-patterns

- **Unpinned action versions.** `uses: actions/checkout@v4` can be hijacked if the tag is moved; pin to a commit SHA.
- **`write-all` permissions.** A compromised step can push to the repo, create releases, or modify issues.
- **Secrets in non-secret contexts.** `run: echo "Token is ${{ secrets.API_TOKEN }}"` logs the secret (masking has workarounds).
- **Missing `needs:` on deploy.** Deploy runs in parallel with tests; a failing test does not block it.
- **Cache poisoning via PR.** A PR caches a modified `node_modules`; the main branch restore key picks it up.
- **`workflow_run` + fork PR elevation.** A `workflow_run` trigger with `write` permissions can be exploited by a fork PR.
- **All jobs sequential.** No parallelism; lint, test, and typecheck run one after another, doubling CI time.
- **No environment protection on prod deploy.** Any push to main deploys to production with no human review.

## Required output

```
## CI/CD Pipeline Review
### Workflows found
| File | Trigger | Purpose |
### Security findings
| Severity | Finding | File:line | Recommendation |
### Permission audit
| Workflow/Job | Current permissions | Minimum required |
### Job dependency graph issues
- Missing needs: [job X should depend on job Y]
### Cache configuration
- Keys include lockfile hash: yes/no | Cross-branch contamination risk: yes/no
### Deployment gate status
- All test jobs in deploy needs: yes/no | Manual approval for prod: yes/no | Env secrets scoped: yes/no
### Performance / cost findings
- Parallelization opportunities | Excessive matrix size | Artifact retention not set
### Recommended actions (priority order)
1. ...
```

## Safety

- Do not modify workflow files without explicit user instruction.
- Do not trigger workflows, approve deployments, or cancel runs.
- Do not access or print secret values — reference them by name only.
- Do not recommend disabling a security gate (environment protection, branch protection) to make CI faster.

## Completion criteria

Done means all workflows are listed with triggers, security findings carry severity + `file:line` + fix, the permission and deployment-gate audits are complete, cache and matrix risks are assessed, and recommendations are ordered by priority — with no secret value printed.

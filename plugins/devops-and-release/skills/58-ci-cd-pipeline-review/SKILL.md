---
name: ci-cd-pipeline-review
description: Use when you need to review CI jobs, workflow triggers, caches, matrixes, artifacts, and safe release gates.
---

# CI/CD Pipeline Review

## Purpose

Audit GitHub Actions workflows, GitLab CI pipelines, CircleCI configs, or equivalent: trigger correctness, secret handling, job dependency ordering, cache hygiene, matrix configuration, artifact retention, fail-fast behavior, and deployment gate safety. Identify security misconfigurations, unnecessary permissions, and reliability anti-patterns.

## When to use

- A new workflow file is added or an existing one is significantly modified.
- CI is slow and you need to find caching or parallelization improvements.
- A security review flags the CI pipeline for audit (secret exposure, overly broad GITHUB_TOKEN permissions).
- Deployments are failing non-deterministically and the cause is suspected to be in the pipeline config.
- A PR workflow accidentally triggers on pushes to protected branches or production environments.

## When not to use

- The pipeline is working correctly and the task is to add a new application feature unrelated to CI.
- The review is of the application code quality, not the pipeline infrastructure.
- A dedicated DevOps team owns the pipeline and has a separate review process.

## Procedure

1. **Identify all workflow files.** Find `.github/workflows/*.yml`, `.gitlab-ci.yml`, `.circleci/config.yml`, `Jenkinsfile`, or equivalent. List all workflows, their triggers, and their purpose.

2. **Audit trigger configuration.** For each workflow, verify:
 - `pull_request` vs `push` vs `workflow_dispatch` triggers are used appropriately.
 - Workflows that deploy or release only trigger on `push` to the default branch or tags — not on `pull_request`.
 - `workflow_run` triggers (if used) do not inadvertently grant elevated permissions to PR-from-forks.
 - `schedule` triggers have a reasonable interval; `*/1 * * * *` (every minute) wastes runner minutes.

3. **Review GITHUB_TOKEN permissions.** In GitHub Actions, check `permissions:` at the workflow and job level. The principle of least privilege applies: a test-only job needs `contents: read` at most, not `write`. Check for `permissions: write-all` or missing `permissions` block (defaults to repo-level settings, often too broad).

4. **Audit secret usage.** For every `${{ secrets.FOO }}` reference:
 - Is the secret actually needed in that job? Secrets passed to jobs that do not use them increase blast radius.
 - Confirm secrets are not echoed to logs via `echo`, `run: env`, or `::debug::`.
 - Confirm third-party actions receive secrets only as environment variables, not as inline args (args appear in logs).

5. **Check job dependency ordering.** Verify `needs:` correctly chains jobs so tests run before deploy, lint runs before tests (optional but cleaner), and release jobs depend on all required gates passing. Look for missing `needs:` that allow a deploy job to start concurrently with a test job.

6. **Review cache configuration.** For each `actions/cache` or tool-native cache (e.g., `setup-node` with `cache: 'npm'`):
 - Cache key includes a hash of the lockfile: `hashFiles('**/package-lock.json')`.
 - Restore keys are ordered from most specific to least specific.
 - Cache is not shared between branches in a way that allows a poisoned cache from a PR to affect the main branch.

7. **Audit matrix strategies.** For `matrix:` configurations, confirm:
 - `fail-fast: false` is set when you want all matrix legs to complete even if one fails (useful for cross-platform tests).
 - `fail-fast: true` (the default) is intentional when an early failure should cancel remaining legs to save costs.
 - Matrix dimensions are not combinatorially explosive (3x3x3 = 27 jobs on every PR is likely too many).

8. **Check artifact retention and naming.** Artifacts should have explicit `retention-days` set (default 90 days can be expensive). Artifact names should be unique across matrix legs (include `${{ matrix.os }}` or similar in the name).

9. **Verify deployment gates.** Before a deploy job runs, confirm:
 - All test jobs (unit, integration, e2e, lint, typecheck) are in `needs:`.
 - A manual approval step (`environment:` with required reviewers) is configured for production deploys.
 - The deploy job runs in the correct environment with the correct secrets scoped to that environment.

10. **Check for self-hosted runner risks.** If self-hosted runners are used for PR workflows, confirm they do not have access to production secrets. PRs from forks can run on self-hosted runners and exfiltrate env vars.

## Checklist

- [ ] Deploy/release workflows trigger only on protected branch push or tags, not on PR.
- [ ] `permissions:` is set at workflow or job level with minimum required scopes.
- [ ] Secrets are passed as env vars, not inline args; not echoed to logs.
- [ ] Job `needs:` graph ensures tests complete before any deploy job starts.
- [ ] Cache keys include lockfile hash; restore keys are ordered specific to general.
- [ ] `fail-fast` behavior is intentional for each matrix configuration.
- [ ] Artifact `retention-days` is explicitly set.
- [ ] Production deploy jobs require manual approval via `environment:` protection rules.
- [ ] Self-hosted runners used for PR workflows do not have production secret access.
- [ ] Scheduled workflow intervals are reasonable (not sub-5-minute).
- [ ] Third-party actions are pinned to a SHA, not a mutable tag.

## Common issues & anti-patterns

- **Unpinned action versions**: `uses: actions/checkout@v4` can be hijacked if the tag is moved; pin to `uses: actions/checkout@<sha>`.
- **`write-all` permissions**: a compromised workflow step can push to the repo, create releases, or modify issues.
- **Secrets in non-secret contexts**: `run: echo "Token is ${{ secrets.API_TOKEN }}"` logs the secret in plain text (GitHub masks it, but workarounds exist).
- **Missing `needs:` on deploy job**: deploy runs in parallel with tests; a failing test does not block the deploy.
- **Cache poisoning via PR**: a PR caches a modified `node_modules`; the main branch restore key picks it up.
- **`workflow_run` + fork PR elevation**: a `workflow_run` trigger that has `write` permissions can be exploited by a fork PR that triggers the parent workflow with elevated access.
- **All jobs sequential**: no parallelism; lint, test, and typecheck run one after another, doubling CI time unnecessarily.
- **No environment protection on prod deploy**: any push to main immediately deploys to production without human review.

## Required output

```
## CI/CD Pipeline Review

### Workflows found
| File | Trigger | Purpose |
|------|---------|---------|

### Security findings
| Severity | Finding | File:line | Recommendation |
|----------|---------|-----------|----------------|

### Permission audit
| Workflow/Job | Current permissions | Minimum required |
|-------------|---------------------|-----------------|

### Job dependency graph issues
- Missing needs: [job X should depend on job Y]
- ...

### Cache configuration
- Keys include lockfile hash: yes/no
- Cross-branch cache contamination risk: yes/no

### Deployment gate status
- All test jobs in deploy needs: yes/no
- Manual approval for prod: yes/no
- Environment secrets scoped correctly: yes/no

### Performance / cost findings
- Parallelization opportunities: list
- Excessive matrix size: list
- Artifact retention not set: list

### Recommended actions (priority order)
1. ...
```

## Safety

- Do not modify workflow files without explicit user instruction.
- Do not trigger workflows, approve deployments, or cancel runs.
- Do not access or print secret values — reference them by name only.

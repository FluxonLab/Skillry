---
name: handoff-readiness-check
description: Use when you need to check documentation, runbooks, install commands, local startup, tests, and transfer readiness.
---

# Handoff Readiness Check

## Purpose

Evaluate whether a project, service, or feature is ready to be handed off to another engineer, team, or on-call rotation. Check that documentation is accurate and complete, local setup works from a cold start, tests pass and are meaningful, runbooks cover incident scenarios, there is no single person who is irreplaceable (bus factor), and an incoming engineer can be productive within a defined time target. Produce a scored readiness report with specific gaps and remediation tasks.

## When to use

- A team member is leaving and their components need to be transferred to others.
- An external vendor or agency is handing a codebase to an internal team.
- A project exits active development and enters maintenance mode.
- An on-call rotation is being extended to include engineers who did not build the service.
- A code review reveals that only one person understands how a critical component works.

## When not to use

- The task is to build the documentation from scratch — that is a writing task; use this skill to evaluate existing documentation.
- The handoff is for a very short-lived prototype that will be discarded.
- A formal onboarding checklist already exists and was recently validated.

## Procedure

1. **Evaluate the README.** Read `README.md` and check for:
 - Purpose statement: what does this service/component do, in one paragraph?
 - Prerequisites: exact versions of runtime (Node 20, Python 3.12), required global tools, and how to install them.
 - Install command: `npm install`, `pip install -r requirements.txt`, etc. — must be one command.
 - Start command: `npm run dev`, `docker-compose up`, etc. — must be one command.
 - Test command: `npm test`, `pytest`, etc.
 - Link to architecture diagram or decision records if the system is non-trivial.
 Attempt to follow the README steps mentally; flag any step that requires implicit knowledge.

2. **Verify local setup from a cold start.** Check for an `.env.example` or equivalent with all required variables and placeholder values. Confirm there are no hard-coded paths to the original developer's machine. Confirm any seed or init scripts are documented and idempotent.

3. **Assess architecture documentation.** For services older than 3 months or with more than 5 components, check for:
 - System context diagram (what external systems does this connect to?).
 - Data flow diagram or sequence diagram for the primary user action.
 - ERD or schema summary for databases with more than 10 tables.
 - ADRs (Architecture Decision Records) for non-obvious technology choices.
 Missing diagrams are acceptable if the system is small; document what "small" means for this context.

4. **Review runbooks.** For each production incident type the service could experience, check for a runbook covering:
 - How to detect the issue (which alert fires, which log pattern to look for).
 - How to diagnose the root cause (which dashboard, which query to run).
 - How to remediate (exact commands, with expected output).
 - How to verify the fix.
 Check the runbook list against the actual alert rules in monitoring config.

5. **Identify bus factor risks.** Run `git log --format='%ae' | sort | uniq -c | sort -rn` to see commit distribution. A single author with >70% of commits and no recent commits from others is a bus factor risk. Also check for:
 - Vendor-specific tooling only one person knows how to operate.
 - Undocumented production credentials stored only in one person's password manager.
 - Critical scripts living only on a developer's laptop.

6. **Validate test suite health.** Run the test suite (or read recent CI results) and confirm:
 - Tests pass consistently, not intermittently.
 - Test coverage is above a meaningful threshold for the critical paths.
 - Tests are readable: a new engineer can understand what is being tested without asking the original author.
 - Flaky tests are documented, not just skipped with `xit` or `@pytest.mark.skip`.

7. **Check dependency freshness.** Verify no runtime dependency is end-of-life (Node 16, Python 3.8, Rails 6). End-of-life dependencies receive no security patches and become increasingly difficult to support.

8. **Audit secret and credential ownership.** Confirm all production secrets are stored in a team-accessible secret manager (not a personal 1Password account). Confirm the team has access to: cloud provider console, DNS management, monitoring dashboard, error tracking.

9. **Estimate time-to-productivity for an incoming engineer.** Based on the above, estimate: how long it takes to get the service running locally, understand the architecture, make a small change, and deploy it. Anything over 2 days for a straightforward service is a handoff risk.

10. **Produce a gap list with owners.** For each gap found, create a specific actionable task with an estimated effort (15 min, 1 hour, 1 day) so the outgoing engineer can prioritize before departure.

## Checklist

- [ ] README has: purpose, prerequisites (with exact versions), install, start, and test commands.
- [ ] `.env.example` exists with all variables and placeholder values.
- [ ] Local setup can be followed without implicit knowledge.
- [ ] Architecture documentation exists for systems with > 5 components.
- [ ] Runbooks cover every active production alert rule.
- [ ] Bus factor: at least 2 people can operate the service without the original author.
- [ ] All production credentials are in a team-accessible secret manager.
- [ ] Test suite passes consistently; no unexplained skipped tests.
- [ ] No runtime dependency is end-of-life.
- [ ] Time-to-productivity estimate is documented and acceptable (< 2 days for a typical engineer).

## Common issues & anti-patterns

- **README last updated 18 months ago**: the install command references a package that was renamed; new engineers spend hours debugging a one-word change.
- **"Ask Alice" documentation**: README says "ask Alice about the deploy process" — Alice has left.
- **Setup requires Homebrew formula from a private tap**: the tap is no longer maintained; the setup is broken for new machines.
- **Runbook references a dashboard that was renamed**: the engineer pages the on-call for a P1 incident and cannot find the dashboard during the fire.
- **Critical SQL queries stored in a personal Notion page**: the team cannot find them during an incident.
- **Bus factor = 1 for the database schema**: nobody knows why certain columns exist; changes break things unexpectedly.
- **Tests pass but are meaningless**: 100% coverage via mocking everything, including the unit under test.
- **Docker Compose works on macOS but not Linux**: environment-specific setup issues are undocumented.
- **Production secrets in a personal Google Drive share**: inaccessible when the owner's account is deactivated.

## Required output

```
## Handoff Readiness Report: [Service/Project Name]

### Overall readiness score: X/10

### README quality
- Purpose statement: present / missing
- Prerequisites with versions: present / missing / incomplete
- Install command: present / missing / broken
- Start command: present / missing / broken
- Test command: present / missing
- Issues: list

### Local setup
- .env.example: present / missing
- Setup followable without prior knowledge: yes / no
- Blockers: list

### Architecture documentation
- System context diagram: present / missing
- Data flow / sequence diagram: present / missing
- ADRs: present (N) / missing
- Gaps: list

### Runbooks
- Active alerts: N
- Runbooks covering those alerts: M (X%)
- Missing runbooks: list of alert names

### Bus factor
- Author distribution: top contributor owns X% of commits
- Team-accessible credentials: yes / no
- Single-owner knowledge areas: list

### Test suite health
- Pass rate: X% (consistent / flaky)
- Skipped tests: N (with explanations: yes/no)

### Dependency health
- End-of-life dependencies: list

### Time-to-productivity estimate
- Get running locally: X hours
- Understand architecture: X hours
- Make a change and deploy: X hours
- Total: X hours — acceptable / at risk

### Gap remediation tasks (ordered by priority)
| Task | Effort | Owner |
|------|--------|-------|
| Add .env.example | 15 min | outgoing dev |
| Write deploy runbook | 2 hours | outgoing dev |
| Transfer DB credentials to 1Password team vault | 30 min | outgoing dev |
```

## Safety

- Do not access or modify production secret stores, cloud consoles, or monitoring systems.
- Do not run setup or install commands that would change the developer's environment.
- Do not create or modify documentation files — produce the gap list for the human to act on.
- Do not commit any changes on behalf of the outgoing engineer.

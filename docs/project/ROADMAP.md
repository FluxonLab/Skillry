# Skillry Development Roadmap

Status: researched, not approved for implementation.

This roadmap orders the researched opportunities. It does not authorize implementation, migration,
release, external integration, or activation.

## Phase 0 - Portable project memory

Goal: make the project resumable from GitHub on another computer.

- Canonical decision register.
- Maintainer handoff with verified repository and package state.
- Research synthesis and source list.
- Explicit implemented/not-implemented boundary.
- Open questions and candidate-branch inventory.

## Phase 1 - Validation and review foundation

Recommended first implementation axis:

```text
Validator 2.0
+ package/release gate
+ generated Markdown review report
```

Candidate outcomes:

- Gate categories and `fail`/`warn`/`info`/`human` severity.
- Package-content allowlist check using `npm pack --dry-run --json`.
- Generated artifact and registry drift checks.
- Agent Skills specification compliance report in warning mode.
- Human-readable library inventory report.
- Trigger-description overlap report.

Non-goals for the first implementation plan:

- No bulk metadata migration across all skills and agents.
- No default hooks or external MCP activation.
- No release or npm publication.
- No automatic legal/licensing conclusion.

## Phase 2 - Evaluation and provenance

- Skill should-trigger, should-not-trigger, and ambiguous cases.
- Skill Sync 2.0 `source.json` and exclusion decision log.
- Instruction-family compatibility matrix.
- Release readiness checklist.
- Fixtures and snapshots for generators.

## Phase 3 - Supply-chain evidence

- npm trusted publishing and provenance evaluation.
- GitHub artifact attestations.
- CycloneDX or SPDX SBOM decision.
- SLSA-aligned release evidence.
- OpenSSF Scorecard review.

This phase requires a release-process decision and explicit activation approval.

## Phase 4 - Capability governance

- MCP capability registry.
- Optional project-scoped guardrail recipes.
- OWASP/NIST risk mapping for skills and agents.
- Multi-agent handoff contracts and routing evaluations.

This phase should proceed only after real usage demonstrates that the additional governance reduces
risk more than it increases maintenance cost.

## Parallel maintenance backlog

- Reconcile GitHub issue `#1` with completed npm publication and this roadmap.
- Review draft PR `#3` and decide adapt/replace/close.
- Add Codex-focused runnable workflow examples.
- Improve remaining shallow skills based on real demand.
- Add per-department onboarding without duplicating canonical content.
- Maintain platform compatibility notes with dates and primary sources.

## Exit criteria before planning Phase 1

- Maintainer selects one coherent first axis.
- Target users and success measures are named.
- Severity policy is agreed.
- Generated report location is decided.
- Original/community compliance boundaries are decided.
- Acceptance criteria, bounded tests, and rollback can be written without guessing.

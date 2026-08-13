# Evidence-First Development Method

## Purpose

The proposed Skillry development system treats an LLM as a researcher, modeler, and tool builder.
Repeatable production work belongs in deterministic validators, generators, tests, and release
gates.

```text
request
-> risk tier
-> source inspection
-> normalized evidence
-> canonical contract
-> deterministic checks and generators
-> review surface
-> tests
-> human decision gates
-> release evidence
```

## Core principles

### Progressive disclosure

Keep always-on instructions short. A skill acts as an index into the scripts, references, schemas,
and evidence required for a particular task. Load detail only when the task needs it.

### Find the answer

Inspect source shape, runtime behavior, platform documentation, and package output instead of
guessing values or swallowing uncertainty with fallback logic.

### Build repeatable tools

A repeated or mutating workflow should extend an existing robust tool or create a reusable one.
One-off scripts are acceptable only for bounded, read-only investigation.

### One source of truth

A fact should be authored once and generated or referenced elsewhere. Skillry currently applies
this to original content, inventories, marketplace files, and the instruction family.

### Separate checkers from decisions

- **Checker:** deterministic facts such as parseability, file presence, checksums, package contents,
  generated drift, and declared permissions.
- **Human gate:** product scope, ambiguous trigger quality, legal/licensing judgment, external
  provider activation, destructive behavior, and release promotion.

## Risk tiers

| Tier | Example | Required process |
|---|---|---|
| 0 | typo, wording, narrow documentation correction | inspect, edit, focused validation |
| 1 | new skill/agent, validator check, installer behavior | source evidence, acceptance criteria, focused tests, file-level plan |
| 2 | metadata migration, import pipeline, permissions, release process | research pack, canonical decision, full plan, rollback, human gates |

## Research convergence

For external source research, one query is not enough. Record the initial terms, discover adjacent
terms and sources, repeat searches until no new in-scope evidence appears, and retain excluded
sources with reasons. A "dry" search is evidence, not proof of completeness; known missing sources
must remain visible.

## Canonical modeling

Before deterministic generation, reduce ambiguous prose into a reviewable contract. Depending on
the feature, this may be frontmatter, JSON/YAML, JSON Schema, a registry record, or an ADR. Include
source, confidence, unresolved questions, and last verification where those matter.

## Validation lifecycle

Proposed future severity model:

| Severity | Meaning |
|---|---|
| fail | deterministic release blocker |
| warn | actionable issue that does not yet block CI |
| info | inventory or migration guidance |
| human | explicit decision required; automation must not infer approval |

New checks should normally begin as reports or warnings, gain fixtures and false-positive evidence,
and only then become blocking.

## Definition of evidence

- A generated report is not approval.
- A green CI run proves only the checks that ran.
- A declared permission is not proof of runtime containment.
- An attributed license file is not a legal opinion.
- A branch or roadmap item is not implemented until merged and verified.
- A merged change is not live until its release or publication is verified.

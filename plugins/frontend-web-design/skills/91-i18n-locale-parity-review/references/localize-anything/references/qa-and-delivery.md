# QA And Delivery

## Three Quality Channels

Keep these channels separate.

In the default path, `localize check` owns deterministic findings, `localize
review` creates and records the independent review, and `localize report`
summarizes both channels plus explicit human confirmations.

The phase gate is artifact-first:

```text
Capability Scan
-> Adapter Selection
-> Capability Gate
-> Artifact Preconditions
-> Allowed Phase Execution
```

Unsupported declared sources stop at `capability-report.json`. Linguistic review
requires current `deterministic-check.json`, `extracted-segments.json`, and a
matching review packet; do not substitute ad hoc scripts or manual reasoning for
those artifacts.

### Deterministic Checks

Mechanical tools may verify:

- resource structure and keys;
- placeholder and markup preservation;
- escapes, identifiers, and explicit preserve rules;
- source/target correspondence;
- declared-scope candidate classification and coverage;
- obvious source-language residuals that are not classified;
- source mutation and unsafe overwrite conditions.

Passing these checks does not prove semantic quality.
Build pass does not prove launch pass, and launch pass does not prove visible
UI coverage pass.
Do not report `ready` while deterministic attention items remain. Use only
these severities: `blocking`, `actionable`, `coverage_limitation`, and
`informational`.

### Agent Review

Use an independent context to assess:

- semantic accuracy;
- natural target-language expression;
- terminology and product-concept consistency;
- tone, voice, and UI convention;
- omissions and unintended additions;
- page/component context;
- screenshot-visible results;
- cultural or locale adaptation.

Record finding, location, reason, risk, confidence, and suggested action.
Auto-cleared checks are review items, not findings.

### Human Confirmation

Route only decisions that genuinely need product ownership:

- official product-concept translations;
- brands and proprietary names;
- high-risk ambiguity;
- wording that may change product meaning;
- decisions the Agent cannot infer from repository evidence;
- final release judgment.

`localize report --confirm` accepts only decisions for findings still marked
`needs_human_confirmation`. Do not manufacture, auto-confirm, or silently
close those findings.

## Risk Routing

Put low-risk auto-cleared checks in `review_items` only when the reason is
visible and no hard constraint failed. Never auto-clear:

- placeholder, markup, key, or file-structure damage;
- a conflict with a locked Glossary concept;
- unresolved legal, medical, financial, regulatory, or safety wording;
- meaning-changing ambiguity;
- missing required project build/test or Release evidence.

## Review Report

Report at least:

```text
Declared scope
Excluded and external surfaces
Detected-but-unsupported and unscanned surfaces
Translated items
Agent-reviewed items
Review items
Human confirmation required
Human-edited after review
Deterministic blocking, actionable, coverage limitation, and informational items
Build/test results
Screenshot/page review results
Git diff / commit / PR state
Unresolved risks and next actions
Project Memory updates
```

Do not collapse deterministic, Agent, and human evidence into one quality score.
Do not turn partial resource success into complete product, platform, document,
runtime, or visual localization success.

## Delivery And Enablement

Delivery applies only to supported, declared surfaces with the requested
evidence. Enablement applies when the project needs source-code mutation,
project-structure changes, connector setup, build configuration, runtime
workflow, or media tooling before localization can be safely delivered. Return
the plan, risks, affected files, validation commands, staging/apply policy, and
rollback requirements; do not call it a delivered localization for that surface.

## Git Delivery

Use Git as the delivery and collaboration surface:

- inspect pre-existing user changes;
- keep localization changes reviewable;
- summarize affected files and resource counts;
- run checks against the actual diff;
- avoid destructive overwrite or deletion;
- prepare a commit or pull request only when requested or required by Release
  depth;
- leave unresolved high-risk decisions visible.

Release depth requires a clean, understandable diff—not necessarily an empty
worktree when the user already has unrelated changes.

## Memory Update

The Phase 2 default path records user confirmations through `localize report
--confirm`. It does not create a parallel update path for older memory assets.
When a confirmed Glossary or Project Memory change is needed, propose the
smallest scoped change for the user to review; do not present an unreviewed
draft as durable memory.

Only confirmed and reusable knowledge is eligible for a later memory update:

- approved product concepts and locale expressions;
- reviewed Translation Memory;
- accepted style decisions;
- preserve rules;
- recurring defects and their corrections.

Do not promote unreviewed drafts, low-confidence guesses, or a broad rule derived
from one narrow example.

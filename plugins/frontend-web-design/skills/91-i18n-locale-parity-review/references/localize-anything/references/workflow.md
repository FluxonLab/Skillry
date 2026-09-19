# Workflow

## Default Command Sequence

The Skill's default execution path is exactly:

```text
localize scan
-> localize glossary bootstrap
-> Coding Agent localization and project-native build/test
-> localize check
-> localize review
-> human confirmation
-> localize report
```

`scan` declares the source/target locales and files. In a zero-i18n project,
the Coding Agent first creates the smallest project-native i18n setup and the
source resource file; `scan` must not run until every declared `--source` exists.
It writes `source-surface-inventory.json` and `capability-report.json`, then
establishes Project Memory only when every declared source has a supported
adapter. Every later `--target` argument follows that source order. `check` and
`review` emit `source_target_mapping` and reject count mismatches, obvious
locale/path contradictions, and adapter mismatches. `check` writes the current
`deterministic-check.json` and `extracted-segments.json`; `review` may run only
when those artifacts are present, non-failing, current, and mapped to the same
targets. `review` first writes a packet for a fresh review context, then
imports that context's findings. `report` records only user decisions that
correspond to open review findings.

For project engineering, use the project's own commands. A JavaScript project
uses its package scripts, Android uses Gradle, Apple projects use Xcode tools,
and Git remains the source of diff and history. The Skill does not replace
those tools.

## Standard

```text
Product and repository preflight
-> Declared scope and completion criteria
-> Candidate classification
-> Glossary, style, preserve rules, and Translation Memory
-> Coding Agent implementation
-> Deterministic structural checks
-> Independent Agent review
-> Risk-ranked human confirmations
-> Review Report
-> Confirmed memory updates
```

Use Standard for a normal locale addition, an existing-locale update, or a
focused localization repair.

## Release

Release includes every Standard stage plus:

- primary-page target-locale screenshots;
- page/component semantic and visual review;
- actual project build and test results;
- locale switch, persistence, system/browser detection, and fallback checks;
- a clean Git diff;
- commit or pull-request preparation;
- promotion of confirmed results into Project Memory.

## Preflight

Identify:

- what the product is and who uses it;
- source and target locales;
- pages, components, files, resource types, and dynamic surfaces in scope;
- non-text and external surfaces that cannot be processed;
- localization surface types: `resource_catalog`, `code_embedded_catalog`,
  `inline_code_string`, `template_or_markup`, `runtime_external_content`,
  `non_text_asset`, `binary_or_compiled_resource`, or unknown;
- existing i18n architecture and locale behavior;
- product concepts, style, preserve rules, and prior translations;
- project-specific completion requirements.

Bundle related blocking questions. Do not ask for information the repository
already answers.

If there is no existing i18n architecture, do not start with `localize scan`.
First make the project-native source resource visible in Git, then scan that
source file.

## Candidate Classification

Classify every discovered candidate in scope:

- `translate`: requires a target-locale result;
- `preserve`: brand, code, identifier, universal label, or deliberate source
  form;
- `locale_format`: date, time, number, currency, unit, plural, or other value
  that belongs in locale-aware formatting;
- `developer_only`: logs, diagnostics, tests, or internal engineering text;
- `dynamic_external`: supplied by server, CMS, OS, dependency, or another
  runtime surface;
- `needs_context`: meaning cannot be decided safely yet.

Coverage is complete when every candidate in the declared scope is classified
and every `translate` candidate has a target result.

For source code, distinguish structured catalogs from inline literals. A typed
catalog or locale object may be adapter-addressable. Scattered inline strings
usually require enablement planning. Internal strings such as logs, paths,
commands, API keys, identifiers, SQL, regexes, errors, and test fixtures are not
automatic localization objects.

## Implementation

Use the project's existing i18n library, resource conventions, routing, tests,
and build system. The Coding Agent may add missing i18n architecture when the
task requires it, but Localize Anything does not prescribe a universal
framework.

Keep semantic batches coherent by screen, flow, component, document section, or
feature namespace. Preserve source provenance and adjacent UI context.

If the minimal core cannot safely check a format, make a scoped project-native
edit, state the unavailable check in the final report, and continue the command
sequence. Do not change to a different Localize Anything workflow.

If there is no supported adapter for a declared source, stop at the capability
report. Do not hand-build extraction scripts, source-to-target character
tables, or linguistic reviews for that surface under the default path.

## Independent Review

Review from a context separate from generation. Provide source, target, relevant
Glossary concepts, style rules, UI context, screenshots, and deterministic
findings. Do not expose irrelevant generation rationale as evidence.

Review all three levels:

1. string;
2. page or component;
3. product concept.

## Completion

Return:

- declared and excluded scope;
- scanned, partially scanned, unsupported, dynamic, and non-text surfaces;
- translated, preserved, formatted, developer-only, external, and unresolved
  candidate counts;
- deterministic check result;
- Agent review result;
- review item, finding, and human-confirmation counts;
- build/test and screenshot evidence required by the chosen depth;
- Git diff/commit/PR state;
- unresolved risks and next actions;
- recorded human confirmations and proposed Project Memory updates.

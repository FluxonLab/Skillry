# Localize Anything

> **Reference of `i18n-locale-parity-review`.** Formerly the standalone skill `localize-anything`; the routing table in [../SKILL.md](../SKILL.md) sends that name and its topics here.
>
> - Origin: third-party, [xueyang-dev/localize-anything](https://github.com/xueyang-dev/localize-anything) `skills/localize-anything/` at commit 8b7a1e54b901bb7afcaebddd06705f1b00ffac42 (every imported file byte-identical to upstream); imported from a local unmanaged install.
> - License: MIT, Copyright (c) 2026 Localize Anything contributors (upstream `LICENSE` checked 2026-09-19, blob 3d1c4331); copy kept at [localize-anything/LICENSE](localize-anything/LICENSE).
> - Note: the 'Make The Skill Available' install notes below describe the upstream standalone layout; in Skillry this content ships inside the hub skill, so no separate install is needed. Its stage references sit under `references/localize-anything/references/`.
> - Not imported (repository metadata): `agents/openai.yaml` (Codex display name and default prompt).
> - Consolidation changes: frontmatter moved into this header; links to its stage references now point to the moved, byte-identical copies; body otherwise unchanged.

<details><summary>Former frontmatter (kept for provenance)</summary>

```yaml
name: localize-anything
description: >-
  Guide a Coding Agent through professional project localization: localization
  surface discovery, translatability classification, concept-centered Glossary
  and project memory, i18n implementation, deterministic structural checks,
  independent language review, risk-ranked human confirmation, and Standard or
  Release completion. Use when adding or updating locales, reviewing project
  localization, building a glossary or translation memory, finding localization
  gaps, or preparing a multilingual release. Do not trigger for ordinary
  one-sentence translation, vocabulary lookup, language learning, or general
  i18n coding without a localization task.
```

</details>

Act as the localization expertise layer for the host Coding Agent. The Agent
still owns code edits, i18n architecture, project builds/tests, screenshots, and
Git work. Supply the professional workflow, durable language decisions,
mechanical QA, independent review, and a concise set of human decisions.

"Anything" means surface-aware coverage: discover and explain resource
catalogs, code-embedded catalogs, inline code strings, templates, dynamic
external content, non-text assets, binary resources, and unknown surfaces. It
does not mean automatically mutating every detected surface.

## Choose The Depth

- Use **Standard** for routine locale additions and copy updates.
- Use **Release** when the user is preparing a formal release and needs
  screenshots, page-level review, build/test evidence, locale behavior checks,
  a clean Git diff, and commit or pull-request preparation.

Recommend a depth from the request and project risk. Use Standard when the user
does not specify and Release evidence is not clearly required.

## Make The Skill Available

- **Codex:** expose this `skills/localize-anything/` directory as an available
  Skill, or copy it into the configured Codex skills directory.
- **Claude Code:** place this directory under the project's
  `.claude/skills/localize-anything/` and keep `SKILL.md` plus `references/`.

The Skill is guidance for the host Coding Agent. It does not install a second
CLI, replace project-native commands, or restore removed platform workflows.

## Default Path

The default path uses only these five `localize` capability groups:

```text
localize scan
-> localize glossary bootstrap
-> Coding Agent localization with project-native tools
-> localize check
-> localize review
-> human confirmation
-> localize report
```

1. Confirm the product, users, source locale, target locale, task intent, and
   project material. Declare in-scope files, localization surfaces, exclusions,
   unsupported/dynamic/non-text surfaces, and completion criteria. If the
   project has zero i18n, the Coding Agent must first add the smallest
   project-native i18n setup and create the source resource file.
2. Run `localize scan PROJECT --source-locale SOURCE --target-locale TARGET
   --source PATH` for every source file in scope. Run it only after every
   declared source file exists; `scan` records source resources, it does not
   create them. It establishes Project Memory only after
   `source-surface-inventory.json` and `capability-report.json` show every
   declared source has a supported adapter.
3. Run `localize glossary bootstrap PROJECT`. Review only high-impact candidate
   concepts; lock a translation by setting `status: "locked"` and
   `target.preferred`, or preserve a term by setting `behavior: "preserve"` and
   `status: "locked"`. Lock only after repository evidence or user
   confirmation.
4. Guide the Coding Agent to make i18n and resource changes using the project's
   conventions. The Coding Agent runs its own build and test commands, such as
   `npm test`, `npm run build`, `./gradlew test`, or `xcodebuild`, plus `git
   diff` when relevant.
5. Run `localize check PROJECT --target PATH` once per declared source, in the
   same order as `scan`. Read `source_target_mapping` and fix any pairing
   error before reviewing. Fix blocking structural findings before review.
   `check` is also the source of the current `extracted-segments.json`
   precondition for review.
6. Run `localize review PROJECT --target PATH` to create the review packet.
   Do not review when the deterministic check artifact is missing, failed,
   stale, or mapped to different targets. Give the packet to a fresh review
   context that did not generate the draft.
   Import its findings with the same command and `--findings REVIEW.json`.
7. Send only high-risk, meaning-changing, terminology, or brand findings to the
   user. Auto-cleared checks are `review_items`, not `findings`. Do not record
   a human confirmation while an open finding lacks a user decision.
8. Run `localize report PROJECT`. If the user has decided every open item, pass
   those decisions with `--confirm CONFIRMATIONS.json`; otherwise report the
   remaining confirmation-required risks.

When a supported mechanical check is unavailable, let the Coding Agent make a
scoped project-native edit and record the limitation. Continue the default path;
do not substitute another platform workflow.

Use only these severities in check, review, report, and Skill notes:
`blocking`, `actionable`, `coverage_limitation`, and `informational`. Do not
use low/medium/high/critical or warning as severity values.

## Explicit Compatibility

Never select a compatibility path automatically. It is allowed only when the
user explicitly requests a legacy command or asks to maintain existing legacy
state. In that case, explain that the path is compatibility-only and keep its
scope separate from the default workflow.

Do not use compatibility mechanisms as a fallback for a missing adapter or an
ordinary localization task. In particular, the default path must not invoke old
run orchestration, work-packet construction, provider handoff, readiness
reports, workbench queues, signoff records, or knowledge eligibility pipelines.

Read [workflow.md](localize-anything/references/workflow.md) for the default command sequence. Read only the
additional reference needed for the active stage:

- [memory-and-context.md](localize-anything/references/memory-and-context.md) for Glossary,
  Translation Memory, project context, or cross-session consistency.
- [qa-and-delivery.md](localize-anything/references/qa-and-delivery.md) for checks, independent
  review, risk routing, reports, screenshots, or release completion.
- [adapters.md](localize-anything/references/adapters.md) for file-format detection and mechanical
  validation limits.

## Preserve Hard Constraints

Never sacrifice keys, placeholders, ICU branches, markup, timestamps, escapes,
encoding, paths, preserve rules, overwrite safety, or source-control safety for
linguistic preference.

Do not treat all source-language text as translatable. Brand names, codes,
currency codes, developer-only text, locale-formatted values, and external
dynamic content may correctly remain unchanged.

Do not treat all source-code string literals as translatable. Structured
code-embedded catalogs need explicit adapter evidence. Unstructured inline
strings default to inventory, candidate classification, user-visible likelihood,
and enablement planning. Logs, paths, commands, API keys, identifiers,
notification names, SQL, regexes, internal errors, and test fixtures are not
automatic localization objects.

## Keep Roles Clear

- The Agent makes semantic and engineering judgments.
- Deterministic tools scan, compare, validate structure, normalize Glossary
  data, and prepare report data.
- Git manages diffs, history, rollback, branches, commits, pull requests, and
  team review.
- The user decides product meaning, official terminology, brands, high-risk
  wording, and final release acceptance.

Do not build a parallel orchestration, approval, CI, or Git substitute as part
of a localization task.

## Be Honest About Completion

Coverage is complete only within the declared scope: every candidate is
classified and every `translate` item has a target result. Do not redefine it
as zero remaining source-language characters.

Report detected-but-unsupported, unscanned, external runtime, and non-text
surfaces as limitations or enablement work. Do not claim complete app,
document, platform, Swift, Android, React, or visual coverage from a passing
resource check.

Deterministic checks do not prove semantic or professional translation quality.
Agent review is not the same as human confirmation. Never promise perfect
translation or silently decide a high-risk product question.

When the five-command core lacks format support, let the Coding Agent handle the
format directly and record which mechanical checks could not be performed.

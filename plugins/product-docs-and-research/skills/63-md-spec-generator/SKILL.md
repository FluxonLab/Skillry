---
name: md-spec-generator
description: Use when you need to create clean markdown specifications, implementation docs, repair reports, and handoff packs.
---

# Md Spec Generator

## Purpose
Use this skill to create clean markdown specifications, implementation docs, repair reports, and handoff packs. Every document produced must be execution-oriented — leading with the outcome the reader must act on, backed by verified file references and copy-pasteable commands, never by assumption.

## When to use
- A feature or fix needs a written implementation spec before coding begins, so an agent or developer can execute it without follow-up questions.
- A repair was completed and a repair report is needed to document the symptom, root cause (file:line), fix applied, and verification result.
- A project is being handed off to a new owner or agent and needs a handoff pack covering how to run it, the architecture map, env var names, and known issues.
- A complex multi-step investigation or audit has been completed and its findings need to be structured into a scannable, verifiable document for review or archiving.

## When not to use
- The task is unrelated to product, docs, and research work.
- The work would require production deploys, destructive data actions, or secret disclosure.
- A narrower skill or existing project instruction already covers the need.

## Procedure
1. Identify the document type and audience: implementation spec (for a builder), repair report (what changed + why), or handoff pack (for a new owner). Each has a different skeleton (below).
2. Gather facts from evidence — files, commands, results — not assumptions. Use `path:line` references and real, copy-pasteable commands.
3. Write top-down: outcome/decision first, then detail. Lead each doc with what the reader must do or know.
4. Make every claim verifiable: name the command that proves it, the file that holds it, or the test that covers it.
5. Keep it execution-oriented and dense: no filler, no restating the obvious, no marketing tone.
6. Close with risks, open questions, and the next safe action.

## Skeletons
```md
# Implementation Spec — <feature>
Context · Goal · Non-goals
Acceptance criteria (checklist)
File-level changes (table: file | change | why)
Steps (ordered, each with a verify command)
Test plan · Risks · Rollback
```
```md
# Repair Report — <issue>
Symptom (with the exact error) · Root cause (file:line)
Fix (what changed, and why this and not that)
Commands run + results · Verification (green gate)
Residual risks · Next safe command
```
```md
# Handoff Pack — <project>
What it is · How to run (install → start, verified on a clean checkout)
Architecture map · Env vars (names only) · Data/migrations
Known issues · Where things live · What to check next
```

## Concrete checks
- Every command in the doc is copy-pasteable and was actually run (or marked "not run, because…").
- File references use `path:line`, not a vague "the config file".
- No secrets/values — env vars referenced by **name** only.
- Headings are scannable; tables used for change lists; no wall-of-text.
- The reader can act from the doc alone without re-deriving context.

## Required output
Return the finished Markdown document(s) using the matching skeleton, plus a one-line note on what evidence backs the key claims. Keep it self-contained: a reader with repo access could execute or take over from it directly.

## Safety checks
- Document only verified facts; mark anything unconfirmed as an open question rather than asserting it.
- Redact secrets; reference env var names only.
- Do not overwrite an existing spec/report without backing it up first.
- No invented commands, file paths, or results.

## Completion criteria
Done means the right doc type was produced from real evidence, it leads with outcome and is fully scannable, every claim is verifiable via a named command/file/test, secrets are redacted, and the reader could act from it alone.

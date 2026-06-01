---
name: md-spec-generator
description: Use when you need to create clean markdown specifications, implementation docs, repair reports, and handoff packs.
---

# Md Spec Generator

## Purpose

Create clean markdown specifications, implementation docs, repair reports, and handoff packs. Every document is execution-oriented — it leads with the outcome the reader must act on, backs every claim with a verified `file:line` reference or a copy-pasteable command, and never relies on assumption. The goal is a document a reader with repo access can act on alone, without re-deriving context or asking follow-up questions.

## When to use

- A feature or fix needs a written implementation spec before coding begins, so an agent or developer can execute it without follow-up questions.
- A repair was completed and a repair report is needed to document the symptom, root cause (`file:line`), fix applied, and verification result.
- A project is being handed off to a new owner or agent and needs a handoff pack: how to run it, the architecture map, env var names, and known issues.
- A multi-step investigation or audit has finished and its findings need structuring into a scannable, verifiable document for review or archiving.

## When not to use

- The task is unrelated to product, docs, and research work.
- The work would require production deploys, destructive data actions, or secret disclosure.
- A narrower skill already covers the need: `64-codex-final-execution-prompt` for agent-executable prompts, `70-adr-generator` for architecture decision records, `69-technical-writing-review` for prose-quality review.

## Procedure

1. **Identify the document type and audience.** Implementation spec (for a builder), repair report (what changed and why), or handoff pack (for a new owner). Each has a different skeleton (below).
2. **Gather facts from evidence** — files, commands, results — not assumptions. Use `path:line` references and real, copy-pasteable commands. If a fact is unconfirmed, mark it as an open question rather than asserting it.
3. **Write top-down:** outcome or decision first, then detail. Lead each document with what the reader must do or know.
4. **Make every claim verifiable:** name the command that proves it, the file that holds it, or the test that covers it.
5. **Keep it dense and execution-oriented:** no filler, no restating the obvious, no marketing tone.
6. **Close with risks, open questions, and the next safe action.**

## Concrete checks

- Every command in the document is copy-pasteable and was actually run — or marked "not run, because…".
- File references use `path:line`, not a vague "the config file".
- No secrets or values appear; env vars are referenced by **name** only.
- Headings are scannable; change lists use tables; there is no wall of text.
- The reader can act from the document alone without re-deriving context.
- Acceptance criteria (for specs) are a checkbox list of observable outcomes, not prose.
- A repair report names the exact error string and the `file:line` of the root cause, not just "fixed a bug".
- A handoff pack's "How to run" was verified on a clean checkout, not assumed from memory.

## Commands or Templates

```md
# Implementation Spec — <feature>
## Context / Goal / Non-goals
## Acceptance criteria
- [ ] <observable outcome>
- [ ] <observable outcome>
## File-level changes
| File | Change | Why |
|------|--------|-----|
## Steps (ordered; each has a verify command)
1. <change> — verify: `<command>` → <expected result>
## Test plan / Risks / Rollback
```

```md
# Repair Report — <issue>
## Symptom
Exact error: `<error string>`
## Root cause
`<path:line>` — <what was wrong>
## Fix
<what changed, and why this and not the alternative>
## Commands run + results
- `<command>` → <result>
## Verification
`<gate command>` → green
## Residual risks / Next safe command
```

```md
# Handoff Pack — <project>
## What it is
## How to run (verified on a clean checkout)
1. `<install>` 2. `<start>`
## Architecture map
## Env vars (names only)
| Name | Purpose | Required |
## Data / migrations / Known issues
## Where things live / What to check next
```

## Choosing the document type

| The reader needs to… | Produce | Leads with |
|----------------------|---------|------------|
| Build a feature without asking questions | Implementation spec | Goal + acceptance criteria |
| Understand what a fix changed and trust it | Repair report | Symptom + root cause |
| Take ownership of an unfamiliar project | Handoff pack | How to run, verified |
| Review the result of an audit | Findings doc | Severity-ranked table |

If two needs apply (e.g., a fix plus a handoff), produce two documents rather than blending them — a reader scanning for "how do I run this" should not wade through a root-cause analysis.

## Worked repair report

A vague note "fixed the login bug" is not a repair report. The execution-grade version:

```md
# Repair Report — login 500 on empty password

## Symptom
POST /auth/login with an empty password returned 500.
Exact error: `TypeError: Cannot read properties of undefined (reading 'compare')`.

## Root cause
`api/auth.ts:31` — `bcrypt.compare(input, user.hash)` ran before the
empty-input guard, and `user` was undefined for an unknown email.

## Fix
Moved the input + user-existence guard above the bcrypt call, returning
401 for both bad email and bad password (avoids user enumeration).
Chosen over try/catch because the 500 masked a real validation gap.

## Commands run + results
- `npm test -- auth` → 14 passed (added 2 cases: empty pw, unknown email)

## Verification
`npm run typecheck && npm test -- auth` → green

## Residual risks / Next safe command
Rate-limiting on /auth/login is still absent — track separately.
```

Every line points at evidence: the exact error string, the `file:line`, the test that now covers it, and the green gate. A reviewer can trust it without re-deriving anything.

## Common issues & anti-patterns

- **Asserting unverified facts.** Writing "the build passes" without running it. Mark unconfirmed items as open questions.
- **Vague references.** "Update the config" instead of `config/app.ts:42`. The reader should not have to hunt.
- **Wall of prose.** A 12-line paragraph describing five file changes. Use a table.
- **Leaking secret values.** Embedding the actual `DATABASE_URL` instead of naming the variable. Names only.
- **Burying the outcome.** Opening with three paragraphs of background before stating what the reader must do. Lead with the action.
- **Invented commands.** Documenting `npm run deploy:prod` that does not exist in `package.json`. Every command must be real.
- **Marketing tone.** "This elegant solution leverages…". A spec is execution material, not a pitch.
- **Overwriting an existing doc.** Replacing a prior spec without backing it up loses history.

## Required output

Return the finished Markdown document(s) using the matching skeleton, plus a one-line note on what evidence backs the key claims (which command ran, which files were read). Keep it self-contained: a reader with repo access could execute or take over from it directly.

## Safety

- Document only verified facts; mark anything unconfirmed as an open question rather than asserting it.
- Redact secrets; reference env var names only.
- Do not overwrite an existing spec or report without backing it up first.
- No invented commands, file paths, or results.
- Do not include internal usernames or private URLs in a doc intended for external handoff.

## Completion criteria

Done means the right document type was produced from real evidence, it leads with outcome and is fully scannable, every claim is verifiable via a named command/file/test, secrets are redacted, and the reader could act from it alone.

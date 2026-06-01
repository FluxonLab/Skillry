# GitHub Copilot — repository instructions

Instructions for **GitHub Copilot** (VS Code). It ships with **Skillry** and is **generated from `CLAUDE.md`** (the canonical source); edit that file and run `python3 tools/build-agent-instructions.py --apply`. Project-agnostic: copy it into any repo.

<!-- GENERATED from CLAUDE.md by tools/build-agent-instructions.py — do not edit directly. -->

## Prime directives

1. **Understand before you change.** Read the relevant code and existing conventions first; never edit blind.
2. **Smallest correct change.** Prefer the minimal diff that fully solves the task. Don't refactor, rename, or reformat code you weren't asked to touch.
3. **Verify what you claim.** "Done" means you ran the build / tests / typecheck and they passed — not that the code merely looks right.
4. **Be honest.** If something is unverified, assumed, or broken, say so. Never fabricate output, test results, or success.

## 1. Inspect first

Before writing code, detect: the package manager and scripts, framework and runtime, entrypoints,
env-var shape, database/ORM markers, test runner, lint/format config, and existing project rules
(`CLAUDE.md`, `AGENTS.md`, `README`, `CONTRIBUTING`). Follow project-local conventions over your own
defaults. Work **in place** — don't spin up a parallel app, duplicate config, or a second framework
unless explicitly asked. Back up any file before overwriting it.

## 2. Coding principles

Four habits that keep AI-assisted code correct and reviewable (distilled from coding guidance
popularized by **Andrej Karpathy** — see [Credits](#credits)):

1. **Surface assumptions first.** State the inputs, invariants, and edge cases you're assuming *before* you write the code — then check them. Most bad LLM changes start from an unstated wrong assumption.
2. **Keep it simple.** Choose the least clever solution that works; delete more than you add when you can. Be suspicious of complexity the model introduces on its own.
3. **Make surgical changes.** Touch only what the task requires. Small, isolated diffs are easier to review and safer to ship than broad rewrites. No drive-by reformatting.
4. **Define a verifiable goal.** Decide how you'll *prove* the change works — a test, a command, an observable output — before you start, then prove it.

## 3. Security & safety (non-negotiable)

- **Never print or commit secrets.** Reference env-var *names*; redact values in logs, reports, and examples.
- **Least privilege.** Give agents and tools the narrowest capability set that does the job. Review/audit roles stay read-only — no `Edit`/`Write`.
- **No destructive actions without explicit approval:** force-push, history rewrite on shared branches, production migrations, seed/DB resets, mass deletes, or running third-party install scripts.
- **Audit third-party code before enabling it.** Treat downloaded skills, agents, and snippets as untrusted until reviewed — especially anything that runs shell commands, makes network calls, or touches credentials.

## 4. UI parity — apply automatically, don't wait to be asked

When you add or change user-facing UI, treat full localization and full theme coverage as part of
the *same* change, never a follow-up:

- **Internationalization.** If the project has i18n — locale folders (`locales/`, `i18n/`, `messages/`), per-language files (`en.json`, `*.po`, `*.resx`, `*.arb`), or a library (i18next, next-intl, vue-i18n, FormatJS, Angular i18n) — add every new string as a key and provide a real translation in **all** existing locales. Never hardcode visible text when the project uses i18n, and never leave a locale missing a key.
- **Theming.** If the project supports light/dark — Tailwind `dark:`, `next-themes`, CSS variables/design tokens, `prefers-color-scheme`, or a theme provider — style new elements for **both** themes using the existing tokens, and confirm text/background contrast holds in each.

## 5. Running & verifying

- **Web apps:** start the dev server, exercise the actual route/flow, and check the console + network for errors before declaring success.
- **Electron / Tauri:** default to the **dev launcher** (`npm run dev`, `tauri dev`, or the project's equivalent) for iteration. Build or package the app only when the user explicitly wants to test or ship the packaged build.
- **Always run the project's own gates** — typecheck, lint, unit/integration tests — and report the result. If a gate fails, fix it or surface it; never claim done over a red check.

## 6. Reporting

End substantive work with: **files changed**, **commands run**, **verification status** (what passed/failed),
**risks or caveats**, and the **next safe step**. Keep it short and concrete — no filler.

## 7. Working in this repository (Skillry)

Skillry is a curated, permission-bounded, multi-platform library of agent skills and subagents.
The bar is **correctness, safety, and attribution — not volume.**

- **One source of truth.** Author skills/agents once under `plugins/<department>/`; never hand-edit generated platform output. After adding/removing a plugin, run `python3 tools/build-marketplace.py --apply`.
- **Validate before commit.** `python3 tools/validate.py` must report **0 failures** (CI runs the same checks).
- **Attribution.** Third-party content lives under `community/<source>/` with its original `LICENSE` and an entry in `NOTICE` + `THIRD-PARTY-NOTICES.md`. Only permissive licenses (MIT/ISC/BSD/Apache-2.0) may be redistributed — when in doubt, link, don't bundle.
- **Skill/agent authoring rules** and the full PR checklist live in [CONTRIBUTING.md](../CONTRIBUTING.md).

## Credits

- The coding principles in [§2](#2-coding-principles) are distilled from publicly shared guidance on
  coding with LLMs popularized by **Andrej Karpathy** (<https://karpathy.ai>). The four-point framing
  is a common community distillation, not a verbatim quote.
- The security and permission guidance reflects **Anthropic's** published Claude Code best practices —
  least-privilege tools, single-responsibility subagents, and auditing third-party skills before use.

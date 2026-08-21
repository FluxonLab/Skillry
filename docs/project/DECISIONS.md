# Skillry Decision and Scope Register

Last updated: 2026-08-13

This is the source-controlled decision register for project scope, development sequencing, and
handoff. New explicit maintainer decisions supersede older entries and must be recorded here before
release or implementation planning relies on them.

## D-001 - Product identity

- **Decision date/source:** 2026-06-01, public v1.0.0 release and repository documentation.
- **Confirmed rule:** Skillry is a curated, permission-bounded, multi-platform distribution layer
  for agent skills and subagents.
- **Source of truth:** original content under `plugins/`; attributed external content under
  `community/`; generated inventory under `registry/`.
- **Unchanged boundary:** correctness, safety, and attribution take priority over library size.
- **Status:** implemented and live.

## D-002 - Multi-platform delivery

- **Confirmed rule:** Claude Code, OpenAI Codex, GitHub Copilot, and Google
  Antigravity/Gemini are first-class targets.
- **Confirmed rule:** `CLAUDE.md` is the canonical shared instruction body. `AGENTS.md`, `GEMINI.md`,
  and `.github/copilot-instructions.md` are generated outputs.
- **Status:** implemented and live on `main`.

## D-003 - Community content boundary

- **Confirmed rule:** redistributed content must have a permissive license, retain the upstream
  license, and be recorded in `NOTICE` and `THIRD-PARTY-NOTICES.md`.
- **Confirmed rule:** imported content is staged for review and is never silently enabled.
- **Prohibited inference:** a successful automated scan is not human approval of third-party code.
- **Status:** implemented; deeper provenance automation remains research scope.

## D-004 - Package publication safety

- **Decision date/source:** 2026-06-18, commit `34aa31c`.
- **Confirmed rule:** npm package contents use an explicit `tools/*.py` allowlist and `.npmignore`
  excludes development and pre-publication artifacts.
- **Status:** implemented on `main`, CI verified, npm package `1.2.0` remains live.

## D-005 - Development-research phase

- **Decision date/source:** user direction, 2026-06-15.
- **Confirmed rule:** research and documentation precede implementation planning. No capability
  platform implementation starts until the maintainer explicitly says to move to planning.
- **Research recommendation:** evolve Skillry from a library into a secure capability supply-chain
  layer through validation, provenance, evaluation, permission, and release gates.
- **Prohibited inference:** documenting a feature in `ROADMAP.md` does not approve its design,
  migration, implementation, release, or activation.
- **Status:** research documented; implementation not approved.

## D-006 - Portable GitHub handoff

- **Decision date/source:** user direction, 2026-08-13.
- **Confirmed rule:** project state, completed work, research, gaps, open questions, and future work
  must be available through GitHub for migration to another computer.
- **Confirmed rule:** private absolute paths, credentials, and stale one-off publishing scripts are
  not copied into the public repository. Their relevant decisions are summarized in portable docs.
- **Status:** this documentation branch records the handoff; merge/live state must be reported
  separately.

## Current candidate work

### Factory governance candidate

- **Branch:** `phase-c/factory-governance-20260809`
- **Pull request:** `#3`, draft, targeting `main`.
- **Candidate head:** `63a1a68743b9d7c6c54c1dd2afab932649b33641`
- **Evidence:** latest two candidate CI runs passed on 2026-08-09.
- **Scope:** generated per-assistant governance files, `project.factory.yaml`, instruction-family
  tests, and generator changes.
- **Status:** candidate only; not merged, not implemented on `main`, not live.
- **Required next decision:** review whether the generated governance model fits Skillry's canonical
  `CLAUDE.md` ownership rule before merging.

## Unresolved decisions

- Which development axis is first: Validator 2.0, skill evaluation, Skill Sync 2.0, or release
  supply-chain hardening?
- Should new checks begin as warnings or CI failures?
- Should generated review output be committed, attached to releases, or generated locally only?
- Should original and community skills use one metadata contract or separate compliance profiles?
- Should the factory governance candidate be adapted, replaced, or closed?

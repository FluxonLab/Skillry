# Changelog

All notable changes to Skillry are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/), and this project adheres to
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- **Published to the npm registry** — [`npm install -g skillry`](https://www.npmjs.com/package/skillry)
  now works (in addition to `npx github:FluxonLab/Skillry`).
- README: **Why this matters for Codex**, per-platform sections for **Claude, Copilot & Antigravity**,
  a real **Demo** (Codex dry-run transcript + `.toml` agent), and a **Maintainers & governance**
  section; custom social-preview image used as the hero; dynamic npm version badge.
- **GOVERNANCE.md** — maintainer, decision-making, release policy, contribution review, security.
- A public **Roadmap** issue (npm publish, Codex installer hardening, example workflows,
  security-review automation, docs).
- Honest project-status framing: "early but infrastructure-level OSS" (no inflated metrics).
- Security contact is now a visible link to `fluxonlab.com/contact` (GOVERNANCE.md + SECURITY.md).

## [1.2.0] — 2026-06-01

### Added
- **`skillry version` and `skillry update`** CLI commands. `update` checks the latest GitHub
  release against the installed version and prints the right update command for each install
  method (Claude Code marketplace, npm global, npx, clone). Installed skill files never
  self-update silently — `update` tells you exactly how to refresh them.

### Fixed
- Attribution accuracy: `THIRD-PARTY-NOTICES.md` now reports 17 redistributed skills for
  `github/awesome-copilot` (was 16). Removed stale example counts from the global-installation-audit
  skill. Refreshed the build-effort token figures.

## [1.1.0] — 2026-06-01

### Added
- **Multi-platform behavior files.** A project instruction file for every supported tool, all
  generated from the canonical `CLAUDE.md`: `AGENTS.md` (Codex / Copilot / Antigravity — the open
  AGENTS.md standard), `GEMINI.md` (Gemini CLI / Antigravity), and
  `.github/copilot-instructions.md` (Copilot). New generator `tools/build-agent-instructions.py`;
  CI fails if the generated files drift from `CLAUDE.md`.
- **Callable `diff-review` skill** (`core-operations`) — audits a diff against four principles
  (surface assumptions, keep it simple, surgical changes, verifiable goal), distilled from
  Andrej Karpathy's public guidance (credited). Brings the original-skill count to **125**.
- **`install.py --instructions <dir>`** — installs the right behavior file per target platform
  into a project. Existing instruction files are **merged, not clobbered**: your rules are kept,
  Skillry's manual is appended under a marked block, and a one-time, self-removing first-run
  notice has the agent reconcile duplicate/conflicting rules with you. Re-installs are idempotent.
- **Acknowledgments** crediting Claude (Anthropic), Codex (OpenAI), and Gemini (Google) as both
  build tools and target platforms.
- Repository polish: `CHANGELOG.md`, issue/PR templates, and a code of conduct.

### Changed
- `CLAUDE.md` rewritten as a project-agnostic engineering operating manual (prime directives,
  inspect-first, Karpathy-credited coding principles, security/least-privilege, i18n + light/dark
  parity, Electron/Tauri dev-launch default, honest verification). It now doubles as a model you
  can copy into your own project.
- Docs refreshed: counts → 125 skills / 73 subagents / 18 departments.

### Fixed
- Attribution accuracy: `jaktestowac/awesome-copilot-for-testers` is a fork of
  `github/awesome-copilot` and retains "Copyright GitHub, Inc." — `NOTICE` corrected.
- `install.py` `--targets` parsing now stops at the next `--flag` (so `--instructions <dir>` is
  not mistaken for a target).

### Removed
- Empty `platforms/` scaffolding directories (the installer writes to each platform's real config
  location, not into the repo).

## [1.0.0] — 2026-06-01

### Added
- First public release: 124 original skills across 18 departments, 73 least-privilege subagents,
  an attributed `community/` set (98 skills + 49 agents from 6 MIT/ISC sources), a validation
  harness, a native Claude Code plugin marketplace, SHA-256 lockfiles, the `skill-sync` importer,
  a portable multi-platform installer, and npm/npx install support.

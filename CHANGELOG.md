# Changelog

All notable changes to Skillry are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/), and this project adheres to
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [2.0.0] - 2026-08-28

### Breaking

- The portable installer manages verified platform skills and agents only. It no
  longer copies, merges or reconciles project AGENTS.md, CLAUDE.md, GEMINI.md or
  Copilot instruction files.
- Dry-run is the default. Filesystem changes require --apply, and unknown,
  misspelled or empty target selections fail closed.
- Existing untracked destination files and locally modified managed files are
  preserved and refused instead of overwritten.

### Added

- Per-target managed-state manifests for idempotent installation and
  hash-guarded stale managed-file removal.
- A release gate covering source locks, validator checks, four clean target
  installs, all Codex agent TOML files and every locked community sidecar.
- Immutable community source provenance for 35 installed sidecar targets,
  including references, templates, scripts and retained license files.
- npm registry installation, public roadmap and expanded platform and
  governance documentation.

### Security

- Import and installation paths are containment checked and symlink-sensitive.
- Reviewed read-only agent classifications no longer treat general Bash access
  as read-only.
- Community source files and installed payloads are checked against generated
  SHA-256 locks before release.

### Fixed

- Community skills now ship their required local references and helper files.
- Codex agent TOML generation handles source escaping correctly; all 122
  generated agent files parse in the release gate.
- Canonical community skill names are derived from frontmatter when vendor
  directory names are numeric or otherwise non-canonical.

### Packaging

- npm prepack runs the release gate.
- The public package includes the portable installer, release gate, source
  locks and all locked sidecars.
- Private governance sources and the project-policy generator are excluded from
  the published payload.

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

---
name: changelog-and-release-notes
description: Use when you need to write or audit a CHANGELOG and human-facing release notes — applying Keep a Changelog structure, deriving entries from conventional commits, choosing the correct semver bump, and writing clear breaking-change and migration notes.
---

# Changelog and Release Notes

## Purpose

Maintain a trustworthy CHANGELOG and produce human-readable release notes for each version. Use the Keep a Changelog format for the structured file, derive draft entries from conventional commit messages, select the correct Semantic Versioning bump (major/minor/patch) from the nature of the changes, and write explicit breaking-change and migration sections so upgraders are never surprised. The CHANGELOG is the durable record; release notes are the friendly announcement built from it.

## When to use

- Cutting a release or tag and the CHANGELOG has an empty or missing `Unreleased` section.
- The project has commits but no organized changelog, and history must be reconstructed.
- A breaking change shipped without an upgrade/migration note.
- Adopting conventional commits and wiring automated release-note drafts.
- Reviewing whether a proposed version number matches the actual change surface.

## When not to use

- A pre-1.0 prototype with no external users and no stability promise — a lightweight notes file is enough.
- The change is documentation-only with zero user-facing behavior change (still record it, but no release needed).
- You need full API reference docs (use api-reference-docs) rather than a change summary.

## Procedure

### 1. Read the current state and history since the last tag

```bash
# Last released tag and the commit range since
git describe --tags --abbrev=0 2>/dev/null
LAST=$(git describe --tags --abbrev=0 2>/dev/null)
git log "${LAST}..HEAD" --pretty=format:'%h %s' --no-merges

# Group commits by conventional-commit type
git log "${LAST}..HEAD" --pretty=format:'%s' --no-merges \
  | grep -oE '^(feat|fix|docs|perf|refactor|build|chore|test)(\([^)]+\))?(!)?:' \
  | sort | uniq -c | sort -rn
```

### 2. Decide the semver bump from the change surface

- `feat:` present, no breaking change → minor (`1.4.0` → `1.5.0`).
- only `fix:` / `perf:` / internal → patch (`1.4.0` → `1.4.1`).
- any `!` marker or `BREAKING CHANGE:` footer → major (`1.4.0` → `2.0.0`).
- pre-1.0: breaking changes may bump minor, but say so in the notes.

```bash
# Surface breaking changes explicitly
git log "${LAST}..HEAD" --pretty=format:'%h %s%n%b' --no-merges \
  | grep -iE 'BREAKING CHANGE|!:' -B1
```

### 3. Map commit types to Keep a Changelog categories

`feat:` → Added/Changed; `fix:` → Fixed; security patches → Security; deprecations → Deprecated; removals → Removed. Rewrite each terse commit subject into a user-facing sentence ("what changed for you"), not the internal mechanics.

### 4. Write the entry under a dated version heading

Promote `Unreleased` to a versioned, dated section and open a fresh `Unreleased`.

### 5. Author breaking-change and migration notes

For every breaking change: state what broke, why, and the exact before/after steps to migrate. Include the minimum diff a consumer applies.

### 6. Generate release notes from the CHANGELOG section

```bash
# Create the annotated tag and a GitHub release using the CHANGELOG section
git tag -a v1.5.0 -m "v1.5.0"
gh release create v1.5.0 --notes-file <(sed -n '/## \[1.5.0\]/,/## \[/p' CHANGELOG.md)
```

## Concrete checks

- [ ] CHANGELOG follows Keep a Changelog (sections: Added, Changed, Deprecated, Removed, Fixed, Security).
- [ ] An `Unreleased` section exists at the top for in-flight work.
- [ ] Each released version has a heading with a version number and an ISO date (`YYYY-MM-DD`).
- [ ] The chosen version number matches the change surface per semver.
- [ ] Every breaking change has a migration note with before/after steps.
- [ ] Entries are written for users (effect), not as raw commit subjects (mechanism).
- [ ] Security fixes are called out in a Security section.
- [ ] Version headings link to the compare/diff range where supported.
- [ ] Deprecations state the planned removal version.
- [ ] Release notes for the announcement are generated from the CHANGELOG, not written separately and divergently.
- [ ] No internal-only churn (formatting, CI tweaks) clutters the user-facing notes.

## Templates

```markdown
# Changelog
All notable changes to this project are documented here.
Format: Keep a Changelog. Versioning: Semantic Versioning.

## [Unreleased]

## [1.5.0] - 2026-06-01
### Added
- Bulk export endpoint `POST /v1/exports`.
### Changed
- **BREAKING:** `GET /v1/items` now paginates by default (max 100/page).
### Fixed
- Timezone offset miscalculated for `created_at` near DST boundaries.
### Security
- Upgraded `lib-x` to patch CVE-2026-0001.

### Migration (1.4 → 1.5)
`GET /v1/items` returns at most 100 items. To restore full lists, page through results:

    # before
    GET /v1/items
    # after
    GET /v1/items?page=1&per_page=100   # repeat until `next` is null

[Unreleased]: https://example.com/compare/v1.5.0...HEAD
[1.5.0]: https://example.com/compare/v1.4.0...v1.5.0
```

```text
# Conventional commit shape that feeds the above
feat(api): add bulk export endpoint
fix(time): correct created_at offset around DST
refactor(items)!: paginate list endpoint by default

BREAKING CHANGE: GET /v1/items now returns at most 100 items per page.
```

## Common issues & anti-patterns

- Dumping raw `git log` subjects as the changelog (mechanism, not user effect).
- Picking a version number by habit rather than from the change surface (shipping a breaking change as a patch).
- A breaking change with no migration steps.
- Maintaining release notes and CHANGELOG separately until they contradict each other.
- Backdating or reordering released versions, destroying the historical record.
- Mixing internal chores (CI, lint) into user-facing notes, burying the signal.
- An empty or stale `Unreleased` section that no one updates per PR.

## Required output

Produce: (1) the recommended semver bump with the reason; (2) the new dated CHANGELOG section in Keep a Changelog format; (3) explicit breaking-change + migration notes if any; (4) the human release-notes text derived from that section; (5) the exact tag/release commands; (6) a list of commits that were intentionally excluded as internal-only.

## Safety

- Never rewrite or reorder already-released version sections; only edit `Unreleased` and add new versions.
- Do not push tags or create releases without explicit user approval.
- Do not fabricate dates or version numbers; derive them from git history and the change surface.
- Exclude secrets and internal hostnames from public release notes.

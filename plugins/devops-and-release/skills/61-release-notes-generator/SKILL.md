---
name: release-notes-generator
description: Use when you need to generate concise release notes, known issues, migration notes, and operator actions.
---

# Release Notes Generator

## Purpose

Generate structured, audience-appropriate release notes from git commit history, PR descriptions, and changelog entries. Categorize changes by conventional commit type (`feat`, `fix`, `breaking`, `perf`, `deps`, `docs`), surface known issues and workarounds, write migration notes for breaking changes, and list required operator actions (run migration, rotate secret, update config). Produce output ready for a GitHub Release, a CHANGELOG.md update, or a customer-facing email — for human review, never auto-tagged or auto-pushed.

## When to use

- A version tag is being cut and release notes must be drafted.
- A sprint ends and the team needs a summary of what shipped for stakeholders.
- A breaking change was merged and migration guidance must be written before the release.
- CHANGELOG.md is outdated and must be brought current with recent commits.
- A hotfix is released and customers need to know what changed and whether action is required.

## When not to use

- The task is to fix bugs or write code — generate notes after the work is done.
- The commit history is already in readable release-notes format and needs no processing.
- The release is internal-only with no customer or operator impact.

## Procedure

1. **Determine the version range.** `git log <previous-tag>..HEAD --oneline`. With no previous tag, use a date range.
2. **Parse commit messages by conventional type.** `feat:` to New Features; `fix:` to Bug Fixes; `perf:` to Performance; `breaking:` / `feat!:` / `BREAKING CHANGE:` footer to Breaking Changes (mandatory migration note); `deps:` / `chore(deps):` only if user-visible or security-relevant; `docs:`/`test:`/`ci:`/`refactor:` generally omitted from customer notes. Categorize non-conventional commits by reading the message; flag ambiguous ones.
3. **Enrich with PR descriptions.** For each merge commit or PR-linked commit, pull the PR title and first paragraph — terse commit messages often omit context.
4. **Write Breaking Changes first.** For each: old behavior vs new behavior; brief rationale; concrete migration steps (commands or code); a compatibility deadline if backward compat is temporary.
5. **Write New Features** from the user's perspective (what they can now do, not how it was built), with a docs link if available.
6. **Write Bug Fixes** describing the symptom the user experienced, not the root cause; include the issue number if referenced.
7. **Write Known Issues** — bugs known but unfixed in this release, with workarounds, to prevent duplicate support tickets.
8. **Write Operator Actions** — every required post-upgrade step: run migration (exact command), update config (which vars, what values), rotate secrets (if a key format changed), clear caches, restart services.
9. **Determine the version number** by semver: breaking present to major; feature-only to minor; fix-only to patch. Confirm against the current version in `package.json` / `pyproject.toml`.
10. **Format for the audience.** Customer notes avoid jargon and emphasize value; operator notes include exact commands and config keys; GitHub Release uses Markdown headers; CHANGELOG follows Keep a Changelog.

## Concrete checks

- [ ] All commits since the previous tag are included in the range.
- [ ] Breaking changes have complete migration notes with exact commands.
- [ ] New features are described from the user's perspective, not the implementation.
- [ ] Bug fixes reference the symptom, not the root cause; include issue numbers.
- [ ] Known Issues lists everything the team is tracking for the next release.
- [ ] Operator Actions lists every required post-upgrade step.
- [ ] Version number follows semver rules for the change types present.
- [ ] Dependencies-only changes are omitted unless they fix a CVE or change behavior.
- [ ] Internal commits (ci, test, docs) are omitted from customer-facing notes.
- [ ] Release notes are reviewed for accuracy against the actual code changes.

## Commands or Templates

```bash
# Commits since the last tag, grouped by conventional type
PREV=$(git describe --tags --abbrev=0 2>/dev/null)
git log "${PREV}..HEAD" --pretty="%s" | grep -E "^feat(\(|:|!)"     # features
git log "${PREV}..HEAD" --pretty="%s" | grep -E "^fix(\(|:)"        # fixes
git log "${PREV}..HEAD" --pretty="%s" | grep -E "^perf(\(|:)"       # performance
git log "${PREV}..HEAD" --pretty="%s%n%b" | grep -iE "BREAKING CHANGE|!:"  # breaking

# Current version to validate the proposed bump
node -p "require('./package.json').version" 2>/dev/null \
  || grep -m1 '^version' pyproject.toml

# PR numbers referenced in the range (for enrichment links)
git log "${PREV}..HEAD" --pretty="%s" | grep -oE "#[0-9]+" | sort -u
```

```markdown
## [vX.Y.Z] — YYYY-MM-DD

### Breaking Changes
- **[Component]** Old behavior vs. new behavior.
  **Migration**: `command to run` or code change required.
  **Compatibility window**: until vX+1.0.0 (if applicable).

### New Features
- **Feature name**: What users can now do. ([#PR](link))

### Bug Fixes
- Fixed [symptom the user experienced]. ([#issue](link))

### Performance
- [Component] is now X% faster under [condition].

### Known Issues
- [Symptom]. Workaround: [steps]. Fix planned for [version].

### Operator Actions Required
1. Run database migration: `npm run db:migrate`
2. Add new env var: `NEW_VAR=value`
3. Rotate `API_SECRET` — format changed.

### Dependencies
- Updated [package] to [version] — resolves [CVE-XXXX-XXXX].
```

## Commit-type to section map

| Commit prefix | Section | Include in customer notes? | Drives semver |
|---------------|---------|----------------------------|---------------|
| `feat:` | New Features | yes | minor |
| `fix:` | Bug Fixes | yes | patch |
| `perf:` | Performance | yes | patch |
| `feat!:` / `BREAKING CHANGE:` | Breaking Changes | yes (with migration) | major |
| `deps:` / `chore(deps):` | Dependencies | only if CVE or behavior change | patch if security |
| `refactor:` / `test:` / `ci:` / `chore:` | — | no | none |
| `docs:` | — | only if user-facing docs | none |

The highest-impact change type present sets the version bump: any breaking change forces a major even if everything else is a patch.

## Worked translation

A raw commit log fragment:

```
a1b2c3 refactor(db): swap to pgbouncer connection pool
d4e5f6 fix(auth): handle expired refresh token without 500
9a8b7c feat!: require API clients to send X-Api-Version header
```

Translated for a customer-facing release:

```markdown
### Breaking Changes
- **API requests** now require an `X-Api-Version` header.
  **Migration**: add `X-Api-Version: 2` to all requests. Unversioned
  requests are rejected with 400. **Compatibility window**: none — effective this release.

### Bug Fixes
- Fixed a server error that occurred when a session's refresh token expired;
  the app now prompts a clean re-login. (#412)
```

The `refactor(db)` commit is omitted entirely — pgbouncer is an implementation detail with no user-visible behavior change (if it *did* change latency, it would become a `perf:` entry: "API responses are faster under load"). The `feat!:` drives the major version bump and gets a mandatory migration note; the `fix:` describes the symptom the user saw, not "null check added".

## Common issues & anti-patterns

- **Implementation language in user notes.** "Refactored the ORM to use connection pooling" — write "Database operations are now 40% faster."
- **Missing migration note for a breaking change.** Users upgrade, the app crashes, and they have no documented fix.
- **Every commit verbatim.** 47 lines of `chore: update lockfile` bury the real changes.
- **Vague bug-fix descriptions.** "Fixed a bug with user settings" — which settings? what symptom?
- **No Known Issues section.** Support receives 20 tickets about one known bug a Known Issues note would have prevented.
- **Premature CHANGELOG commit.** Updating CHANGELOG in the feature PR; if the PR is reverted, the entry remains.
- **Semver bump without checking for breaking changes.** A patch bump for a release with a breaking change misleads users about upgrade safety.
- **Orphaned migration note.** The documented migration command no longer exists in the new version.

## Required output

Return the release-notes Markdown block above for the target audience: a version header, Breaking Changes (with migration steps) first, then New Features, Bug Fixes, Performance, Known Issues, Operator Actions, and Dependencies. Include the proposed semver version with a one-line justification of the bump level, and note any ambiguous commits that need author clarification.

## Safety

- Do not tag the repository, push to git, or create the GitHub release — produce content for human review and approval.
- Do not modify `CHANGELOG.md` or the `package.json` version without explicit user instruction.
- Do not include internal commit SHAs, branch names, or developer usernames in customer-facing notes.
- Do not invent a fix or feature that is not backed by a commit in the range.

## Completion criteria

Done means the full commit range was categorized by type, breaking changes have migration steps, user-facing entries describe value/symptoms (not implementation), operator actions are listed, the semver bump is justified, and the output is ready for human review — not auto-published.

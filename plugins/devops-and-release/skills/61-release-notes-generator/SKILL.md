---
name: release-notes-generator
description: Use when you need to generate concise release notes, known issues, migration notes, and operator actions.
---

# Release Notes Generator

## Purpose

Generate structured, audience-appropriate release notes from git commit history, PR descriptions, and changelog entries. Categorize changes using conventional commits (`feat`, `fix`, `breaking`, `perf`, `deps`, `docs`), surface known issues and workarounds, write migration notes for breaking changes, and list required operator actions (run migration, rotate secret, update config). Produce output ready for a GitHub Release, a CHANGELOG.md update, or a customer-facing email.

## When to use

- A version tag is being cut and release notes must be drafted.
- A sprint ends and the team needs a summary of what shipped for stakeholders.
- A breaking change was merged and migration guidance must be written before the release.
- CHANGELOG.md is outdated and must be brought current with recent commits.
- A hotfix is released and customers need to know what changed and if action is required.

## When not to use

- The task is to fix bugs or write code — generate notes after the work is done.
- The commit history is already in readable release notes format and needs no processing.
- The release is internal-only with no customer or operator impact.

## Procedure

1. **Determine the version range.** Run `git log <previous-tag>..HEAD --oneline` to get all commits since the last release. If there is no previous tag, use `git log --oneline` with a date range.

2. **Parse commit messages by conventional commit type.** Classify each commit:
 - `feat:` — new feature, goes in "New Features" section.
 - `fix:` — bug fix, goes in "Bug Fixes" section.
 - `perf:` — performance improvement, goes in "Performance" section.
 - `breaking:` or `feat!:` or `BREAKING CHANGE:` in footer — goes in "Breaking Changes" section; mandatory migration note.
 - `deps:` or `chore(deps):` — dependency update; include only if user-visible or security-relevant.
 - `docs:`, `test:`, `ci:`, `refactor:` — generally omit from customer-facing notes unless they contain user-visible changes.
 - Non-conventional commits: attempt to categorize by reading the message; flag ambiguous ones.

3. **Enrich with PR descriptions.** For each commit that is a merge commit or has an associated PR number, fetch the PR title and first paragraph of the description. PR descriptions often contain context that terse commit messages omit.

4. **Write Breaking Changes section first.** For every breaking change:
 - What changed: the old behavior and the new behavior.
 - Why it changed: brief rationale.
 - Migration steps: concrete commands or code changes the operator/developer must make.
 - Migration deadline: if backward compatibility is maintained temporarily (e.g., old API supported until v3.0), state the deadline.

5. **Write New Features section.** For each feature, write 1-2 sentences from the user's perspective: what they can now do, not how it was implemented. Include a link to documentation if available.

6. **Write Bug Fixes section.** For each fix, describe the symptom that was fixed (what the user experienced), not the root cause. Include the GitHub issue number if referenced in the commit.

7. **Write Known Issues section.** List bugs that are known but not fixed in this release, with workarounds if available. This prevents support tickets for known issues.

8. **Write Operator Actions section.** List every action required by the operator or developer after upgrading:
 - Run database migrations: exact command.
 - Update configuration: which variables, what new values.
 - Rotate secrets: if any key format changed.
 - Clear caches: if cached data structure changed.
 - Restart services: if a previously-optional restart is now required.

9. **Determine the version number.** If the release follows semver:
 - Breaking change present: increment major.
 - New feature only (no breaking): increment minor.
 - Bug fix only: increment patch.
 Confirm the proposed version number against the current version in `package.json`, `pyproject.toml`, or equivalent.

10. **Format for the target audience.** Customer-facing notes: avoid internal jargon, link to docs, emphasize user value. Developer/operator notes: include exact commands, config keys, and migration scripts. GitHub Release body: use Markdown with section headers. CHANGELOG.md: follow the Keep a Changelog format.

## Checklist

- [ ] All commits since the previous tag are included in the range.
- [ ] Breaking changes have complete migration notes with exact commands.
- [ ] New features are described from the user's perspective, not the implementation.
- [ ] Bug fixes reference the symptom, not the root cause; include issue numbers.
- [ ] Known issues section includes all issues the team is tracking for the next release.
- [ ] Operator Actions section lists every required post-upgrade step.
- [ ] Version number follows semver rules for the change types present.
- [ ] Dependencies-only changes are omitted unless they fix a CVE or change behavior.
- [ ] Internal commits (ci, test, docs) are omitted from customer-facing notes.
- [ ] Release notes are reviewed for accuracy against the actual code changes.

## Common issues & anti-patterns

- **Implementation language in user notes**: "Refactored the ORM layer to use connection pooling" — users do not care; write "Database operations are now 40% faster."
- **Missing migration note for breaking change**: users upgrade and the app crashes; they have no documented fix.
- **Including every commit verbatim**: 47 lines of `chore: update lockfile` entries create noise that buries real changes.
- **Vague bug fix descriptions**: "Fixed a bug with user settings" — which settings? What behavior? What was the symptom?
- **No known issues section**: support receives 20 tickets about the same known bug; a known issues section prevents this.
- **Premature CHANGELOG.md commit**: CHANGELOG.md is updated in the same PR as the feature; if the PR is reverted, the changelog entry remains.
- **Semver version bump without checking for breaking changes**: a patch bump for a release that contains a breaking change misleads users about upgrade safety.
- **Orphaned migration note**: the migration step documented in release notes references a command that no longer exists in the new version.

## Required output

```markdown
## [vX.Y.Z] — YYYY-MM-DD

### Breaking Changes
- **[Component]** Description of old behavior vs. new behavior.
 **Migration**: `command to run` or code change required.
 **Compatibility window**: until vX+1.0.0 (if applicable).

### New Features
- **Feature name**: What users can now do. ([#PR-number](link))

### Bug Fixes
- Fixed [symptom the user experienced]. ([#issue-number](link))

### Performance
- [Component] is now X% faster under [condition].

### Known Issues
- [Symptom]. Workaround: [steps]. Fix planned for [version].

### Operator Actions Required
1. Run database migration: `npm run db:migrate`
2. Add new env var: `NEW_VAR=value`
3. Rotate `API_SECRET` — format changed to SHA-256 prefix.

### Dependencies
- Updated [package] to [version] — resolves [CVE-XXXX-XXXX].
```

## Safety

- Do not tag the repository, push to git, or create the GitHub release — produce the content for human review and approval.
- Do not modify `CHANGELOG.md` or `package.json` version without explicit user instruction.
- Do not include internal commit SHAs, branch names, or developer usernames in customer-facing notes.

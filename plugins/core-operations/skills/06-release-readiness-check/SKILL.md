---
name: release-readiness-check
description: Use when you need to decide whether a project is ready for demo, handoff, release, or deployment.
---

# Release Readiness Check

## Purpose
Decide whether a project is ready for demo, handoff, internal release, or production deployment, and back the decision with evidence. The output is a Go / No-Go verdict supported by a gate table — not an opinion — so every blocker is concrete, reproducible from a clean checkout, and actionable before anything ships. The bar scales with the target: a demo tolerates more rough edges than a production deploy, but a failing or unrun gate is always a No-Go until resolved or explicitly waived by the owner.

## When to use
- A release, demo, or handoff is scheduled and you must confirm build, tests, migrations, config, and docs are all green.
- After a significant feature merge, before promoting a branch to staging or production.
- A stakeholder demo is upcoming and the project must be proven to start cleanly from a fresh clone.
- Before closing a sprint or milestone, to produce a structured blockers-vs-follow-ups list.
- Before a handoff to another team that needs to run the project without the original author present.

## When not to use
- The task is unrelated to release/operability work.
- The work requires production deploys, destructive data actions, or secret disclosure (this skill verifies; it does not deploy).
- A narrower skill (e.g., a CI/CD pipeline review or a migration-safety review) already covers the specific concern.
- The project is a private experiment with no audience — readiness gating is disproportionate.

## Procedure
1. **Confirm the release target** (demo / handoff / internal / production). The gate bar differs; record which target you are gating against.
2. **Run the verification gates in order from a clean checkout** and record pass/fail with evidence for each: reproducible install, typecheck, lint, build, automated tests, app startup, primary route / health endpoint.
3. **Audit configuration and secrets:** env documented, no secrets committed (`git grep` for key patterns), `.env.example` matches the variables the app actually reads, no drift.
4. **Audit the data layer:** migrations applied, `migrate status` clean, seeds/fixtures idempotent and safe, no destructive step pending against a shared environment.
5. **Audit operability:** README/run steps verified on a fresh clone, error/empty/loading states handled in the UI, logs useful and secret-free, version bumped with changelog/release notes for a real release, rollback path known for the deploy target.
   - Verify the artifact: build output size versus the last release, no stray/missing dependencies (`depcheck`), and a clean working tree after the build.
   - For a handoff specifically, run the README from an empty directory as a new teammate would, recording any undocumented manual step as a blocker.
6. **Issue a Go / No-Go verdict** that separates **blocking** issues from **non-blocking** follow-ups, and name the next safe command to close the top blocker.

## Concrete checks
- `build` succeeds clean from a fresh, frozen-lockfile install.
- `typecheck` and `lint` pass, or every waiver is documented and justified.
- Automated tests pass; critical paths have coverage (not just smoke tests).
- App starts and the primary route / health endpoint returns 200.
- No secrets in the repo; `.env.example` matches the variables actually read.
- DB migrations applied; `prisma migrate status` (or the project's equivalent) is clean with nothing pending.
- Run/install instructions reproduce on a clean checkout with no undocumented manual step.
- Error, empty, and loading states are handled in the UI (not blank screens or raw stack traces).
- Version bumped and release notes / changelog written for real releases.
- Rollback path for the deploy target is known and written down.
- The lockfile is in sync with `package.json` (`npm ci` succeeds, not just `npm install`).
- Build artifact size is comparable to the last release (no unexplained bloat).
- `depcheck` shows no missing or stray dependencies.
- The build produces no untracked or modified tracked files (`git status` clean after build).
- Every gate result in the table is from a run against the exact commit being shipped, with pasted evidence.

## Commands
```bash
# Reproducible install (use the project's lockfile mode, not a loose install)
npm ci                                   # or: pnpm i --frozen-lockfile / yarn --immutable

# Static gates
npm run typecheck && npm run lint        # or: tsc --noEmit / ruff check . / mypy .

# Build gate (must succeed from the frozen install above)
npm run build

# Test gate
npm test -- --watch=false                # or: pytest -q / go test ./...

# Startup + route smoke (health first, fall back to root)
npm run start & SRV=$!; sleep 3
curl -fsS http://localhost:3000/health || curl -fsS http://localhost:3000/ ; echo
kill "$SRV" 2>/dev/null

# Config / secrets audit
diff <(grep -oE '^[A-Z0-9_]+' .env.example | sort) \
     <(git grep -hoE 'process\.env\.[A-Z0-9_]+|os\.environ\[.[A-Z0-9_]+' src \
       | grep -oE '[A-Z0-9_]+' | sort -u) ; echo "compare required vs used"
git grep -nE '(api[_-]?key|secret|password|token)\s*[:=]\s*["'\''][^"'\'']+' -- ':!*.example' || echo "no inline secrets"

# Data layer
npx prisma migrate status 2>/dev/null || echo "no prisma / use project migration tool"
```
```bash
# Prove the clean-checkout claim in a throwaway directory
TMP=$(mktemp -d); git clone --depth 1 "$(git remote get-url origin)" "$TMP/app"
cd "$TMP/app" && cp "$OLDPWD/.env.example" .env && npm ci && npm run build
# (cd is one compound command; the working tree is restored next call)

# Bundle / artifact sanity before shipping
du -sh dist build .next 2>/dev/null            # build output size — spot a 200MB regression
npx depcheck 2>/dev/null | rg "Unused|Missing"  # stray or missing deps
git status --porcelain                          # the build produced no tracked-file changes

# Version + changelog gate for a real release
jq -r '.version' package.json
git describe --tags --abbrev=0 2>/dev/null       # latest tag
git log "$(git describe --tags --abbrev=0)..HEAD" --oneline | head   # unreleased commits
test -f CHANGELOG.md && rg -n "$(jq -r '.version' package.json)" CHANGELOG.md || echo "changelog missing this version"
```
```bash
# UI state coverage: do error/empty/loading states exist in the codebase?
rg -n "isLoading|isError|EmptyState|Skeleton|ErrorBoundary|<Spinner" src/ | head
rg -n "catch|\.error\(|onError" src/ | wc -l        # error handling present at all?

# Rollback readiness: a clean target SHA and a reversible last migration
git log --oneline -5
ls -t migrations/*/down.sql migrations/*.down.* 2>/dev/null | head -1 || echo "no down migration — verify rollback plan"
```

## Gate bar by target
| Gate | Demo | Internal | Handoff | Production |
|------|------|----------|---------|------------|
| Build clean from frozen install | required | required | required | required |
| Typecheck + lint | warn | required | required | required |
| Automated tests pass | smoke | required | required | required |
| Health endpoint 200 | required | required | required | required |
| No secrets committed | required | required | required | required |
| Migrations applied + clean | n/a | required | required | required |
| Clean-clone run docs verified | warn | warn | required | required |
| Version bump + changelog | n/a | n/a | warn | required |
| Rollback path documented | n/a | warn | required | required |

## Gate table format (fill one row per gate)
```md
| gate        | command                         | result | evidence                          |
|-------------|---------------------------------|--------|-----------------------------------|
| install     | npm ci                          | pass   | 412 packages, 0 vulnerabilities   |
| build       | npm run build                   | pass   | built in 38s, dist 12MB           |
| tests       | npm test                        | FAIL   | 2 failing in payments.spec.ts     |
| startup     | curl /health                    | pass   | 200 {"status":"ok"} in 240ms      |
| migrations  | prisma migrate status           | pass   | database schema up to date        |
```

## Common issues & anti-patterns
- **Loose install hides lockfile drift.** Running `npm install` instead of `npm ci` lets a transitive dependency float; the demo machine resolves different versions than CI. Always use the frozen mode.
- **"Works on my machine" startup.** The app starts for the author because of an undocumented env var or a manually-created directory. Gate startup from a clean clone with only `.env.example` filled in.
- **Green tests, broken build.** Tests pass against source but the production build fails on a type error excluded from the test config. Run the real `build` gate, not just tests.
- **Pending migration shipped.** Code is merged but the migration is not applied to the target; the first request 500s on a missing column. `migrate status` must be clean.
- **Secrets in the repo.** A committed `.env` or hardcoded key. This is a blocking security finding and a No-Go regardless of the other gates.
- **No rollback story.** "We'll figure it out if it breaks" is not a rollback path. Name the revert SHA, the down migration, or the flag to flip.
- **Ticking the box without running the gate.** Marking "tests pass" from memory of yesterday's run. Re-run every gate against the exact commit being shipped and paste the evidence.
- **Stale lockfile.** `package.json` and the lockfile disagree, so `npm ci` fails on the release machine while `npm install` "worked" locally. Commit the regenerated lockfile.
- **Bundle bloat shipped silently.** A new dependency triples the build output and nobody notices until the CDN bill or a slow first load. Diff the artifact size against the last release.
- **Changelog not updated.** The version is bumped but the changelog still describes the previous release, so the handoff team cannot tell what changed. Gate the version against a matching changelog entry.

## Required output
Return a **Go / No-Go** verdict, the gate table (`gate | command | result | evidence`), the concrete-checks list with each item ticked or flagged, a **blocking** list and a **non-blocking** list kept separate, and the single next safe command to close the top blocker. State which release target the verdict is for and which gate bar (from the table above) was applied. Note any owner-approved waiver with the owner's name. Redact secrets in all evidence. Do not deploy.

## Safety
- Read and verify only; this skill does not deploy, migrate production, or reset data.
- Use reproducible installs (`ci` / `--frozen-lockfile`), never loose installs that mask drift.
- Redact secrets in every line of evidence; report env var names only.
- Treat a failing or unrun gate as a No-Go until it is resolved or explicitly waived by the owner, and record who waived it.
- Run the clean-clone verification in a throwaway directory; never reset or delete the working repository.
- Do not bump the version or edit the changelog yourself as part of the check; report the gap and let the owner decide.

## Completion criteria
Done means every gate was run (or its absence justified) from a clean checkout, the concrete-checks list is fully evaluated, blocking and non-blocking issues are separated, a clear Go / No-Go verdict is recorded against the named release target, and the next action to close the top blocker is stated.

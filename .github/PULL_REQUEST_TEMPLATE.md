<!-- Thanks for contributing to Skillry. Keep PRs small and focused. -->

## What & why

<!-- What does this change, and why? One department or one concern per PR where possible. -->

## Type

- [ ] New skill
- [ ] New subagent
- [ ] Edit to an existing skill/agent
- [ ] Third-party content under `community/` (attribution included)
- [ ] Tooling / docs / CI

## Checklist

- [ ] `python3 tools/validate.py` passes (0 failures).
- [ ] If I changed `plugins/`, I regenerated the marketplace: `python3 tools/build-marketplace.py --apply`.
- [ ] If I changed `CLAUDE.md`, I regenerated the behavior files: `python3 tools/build-agent-instructions.py --apply`.
- [ ] New skills have valid frontmatter (`name` matches the folder minus `NN-`; `description` starts with "Use when …") and real Procedure / Concrete checks / Safety sections.
- [ ] New subagents declare a least-privilege `tools` allowlist (review/audit agents have no `Edit`/`Write`).
- [ ] Third-party content includes its upstream `LICENSE` and is listed in `NOTICE` + `THIRD-PARTY-NOTICES.md` (permissive licenses only).
- [ ] Content is in English; no secrets, private paths, or personal info.

## Platforms affected

<!-- Claude / Codex / Copilot / Antigravity / all -->

## Verification

<!-- Commands you ran and their result. -->

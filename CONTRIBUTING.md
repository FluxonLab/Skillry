# Contributing to Skillry

Thanks for helping improve Skillry. This project values **correctness, safety, and
attribution** over raw volume. A few small, high-quality skills beat many shallow ones.

## Ground rules

1. **One source of truth.** Author skills/agents once under `plugins/<department>/`.
   `AGENTS.md` and `CLAUDE.md` are equivalent repository contributor entry points; maintain
   their shared rules together. Neither is generated or portable installer payload.
   Generated artifacts are never hand-edited: `.claude-plugin/marketplace.json` comes from
   `tools/build-marketplace.py`; the thin `GEMINI.md` and `.github/copilot-instructions.md`
   adapters come from `tools/build-agent-instructions.py` and point to the root rules.
   Edit the generator, run it with `--apply`, and use `--check` to verify freshness without
   writes. It never rewrites `AGENTS.md` or `CLAUDE.md`. The historical `.factory/governance/`
   candidate records are retained as evidence, not injected into active adapters.
2. **Least privilege.** Every subagent must declare an explicit `tools` allowlist. Review/audit
   agents must not include `Edit` or `Write`.
3. **Real content, not templates.** A skill must have concrete procedures, commands, checks,
   and a safety section — not a generic restated description.
4. **Discoverable triggers.** A skill's `description` must start with "Use when …" and name the
   concrete situations/phrases that should invoke it — this is what drives auto-invocation.
5. **English only** in public content.

## Skill requirements

Every `SKILL.md` must have valid YAML frontmatter:

```yaml
---
name: kebab-case-name          # required, matches the folder name (minus the NN- prefix)
description: Use when ...       # required, starts with "Use when", concrete trigger context
---
```

Body should include: `## Purpose`, `## When to use`, `## When not to use`, `## Procedure`
(with real steps/commands), `## Checklist` or `## Concrete checks`, `## Required output`,
and `## Safety`.

Run the validators before opening a PR:

```bash
python3 tools/validate.py        # structure + frontmatter + permission + attribution lint
```

CI runs the same checks; PRs must pass.

## Adding third-party (community) content

Only **permissively licensed** content (MIT, ISC, BSD, Apache-2.0) may be redistributed.

A PR that adds content under `community/` must:
- Place files under `community/<source-slug>/` and include that source's original `LICENSE`.
  Content merged into an existing skill hub instead goes to that hub's `references/<former-name>.md`
  (other files under `references/<former-name>/`) with a provenance header, the upstream `LICENSE`
  beside it, and a `registry/community-source-lock.json` entry for each byte-identical file. Never
  name merged content `SKILL.md`: Codex discovers nested `SKILL.md` files as separate skills.
- Add the source to `NOTICE` and `THIRD-PARTY-NOTICES.md` with correct copyright + upstream URL.
- Include a one-line note on what was reviewed (see [SECURITY.md](SECURITY.md)).
- **Not** include content under proprietary or non-redistributable terms (e.g. service
  agreements). When in doubt, link to it instead of bundling it.

Prefer `tools/skill-sync.py` to import and normalize upstream skills — it records provenance
automatically.

## Commit & PR style

- Small, focused PRs. One department or one concern per PR where possible.
- Describe what changed, which platforms it affects, and the verification you ran.

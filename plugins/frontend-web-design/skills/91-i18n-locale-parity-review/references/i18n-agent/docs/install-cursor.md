# Install — Cursor

## Option A — Project skill (recommended)

Copy or submodule this repository into your project:

```bash
# submodule
git submodule add https://github.com/adamgrgs/i18n-agent.git .cursor/skills/multilingual-i18n-seo

# or copy
cp -R multilingual-i18n-seo-skill .cursor/skills/multilingual-i18n-seo
```

Cursor Agents that load project skills from `.cursor/skills/` will pick up `SKILL.md`.

Also add a short pointer in `.cursor/rules` or `AGENTS.md` at the repo root:

```markdown
When auditing or implementing multilingual SEO / i18n, follow
`.cursor/skills/multilingual-i18n-seo/SKILL.md`.
```

## Option B — Plugin packaging hints

This repo includes [`.cursor-plugin/plugin.json`](../.cursor-plugin/plugin.json). You can copy the whole skill folder into a Cursor plugin layout if your team packages skills that way. Point the skill path at `SKILL.md` and the manifest at `skill.json`.

## Option C — Mention / attach

In Agent chat:

```text
@SKILL.md Use the multilingual i18n SEO skill to audit this repo
```

Or paste the absolute path to `SKILL.md` / `AGENTS.md`.

## Verify install

1. Ask the agent: “Use the multilingual i18n SEO skill to audit this repo.”
2. Confirm it reads `SKILL.md` and proposes Phase A discovery.
3. Run the checker (Python 3.11+):

```bash
python .cursor/skills/multilingual-i18n-seo/scripts/check_i18n_seo.py --help
```

## Optional CI

See [`templates/github-actions-seo-check.yml`](../templates/github-actions-seo-check.yml) and [`verification-and-ci.md`](verification-and-ci.md).

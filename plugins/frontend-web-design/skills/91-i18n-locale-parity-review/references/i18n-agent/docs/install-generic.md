# Install — Generic agent environments

Works for Windsurf, Codex, Continue, Aider, OpenCode, or any agent that can read files.

## Drop-in

1. Clone or copy this repository into the project (or a known skills path).
2. Point the agent at `SKILL.md` or `AGENTS.md`.
3. Prefer `@`-mention / file attach / “follow this skill” phrasing.

```bash
git clone https://github.com/adamgrgs/i18n-agent.git skills/multilingual-i18n-seo
```

Root `AGENTS.md` (project):

```markdown
Multilingual work → skills/multilingual-i18n-seo/SKILL.md
```

## Minimum files to keep

If you must slim the copy:

- `SKILL.md`, `skill.json`, `AGENTS.md`, `LICENSE`
- `docs/` (especially checklist + translation playbook)
- `schemas/`, `checklists/`, `templates/`, `prompts/`
- `scripts/` + `tests/` if you want CI

## Python

Requires **Python 3.11+**. Core scripts prefer the standard library. For tests:

```bash
pip install -r scripts/requirements.txt
python -m pytest tests/ -q
```

## Invoke examples

- “Read `skills/multilingual-i18n-seo/SKILL.md` and audit this site for multilingual SEO.”
- “Follow the translation playbook to localize marketing pages into fr-CA.”
- “Add the GitHub Actions SEO check from the skill templates.”

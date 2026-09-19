# Install — Claude Code

## Option A — Skills directory

```bash
mkdir -p .claude/skills
cp -R multilingual-i18n-seo-skill .claude/skills/multilingual-i18n-seo
# or submodule into .claude/skills/multilingual-i18n-seo
```

Ensure `SKILL.md` and `skill.json` sit at:

```text
.claude/skills/multilingual-i18n-seo/SKILL.md
.claude/skills/multilingual-i18n-seo/skill.json
```

## Option B — CLAUDE.md pointer

Add to your project `CLAUDE.md` (or `.claude/CLAUDE.md`):

```markdown
## Multilingual i18n + SEO

When the user asks to audit, plan, translate, or verify multilingual SEO / i18n,
read and follow `.claude/skills/multilingual-i18n-seo/SKILL.md`.

Hard rules: no geo-IP / Accept-Language force redirects by default;
never change locked third-party booking URLs; no hreflang on noindex.
```

## Option C — User-level skill

Copy the skill into your user Claude skills directory (path varies by Claude Code version), then reference it from project `CLAUDE.md` if needed.

## Invoke

```text
Use the multilingual i18n SEO skill to audit this repo
Plan fr-CA + es localization with proper hreflang
Translate marketing pages using the translation playbook
Add CI checks for multilingual SEO
```

## Scripts

```bash
python .claude/skills/multilingual-i18n-seo/scripts/validate_locale_registry.py \
  path/to/locale-registry.json

python .claude/skills/multilingual-i18n-seo/scripts/check_i18n_seo.py \
  --root dist \
  --registry path/to/locale-registry.json
```

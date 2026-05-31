---
name: i18n-locale-parity-review
description: Use when you need to audit multi-language locale parity across TR/EN/DE locale files, detect missing translation keys, find hardcoded UI strings that bypass i18n, and validate next-intl App Router routing. This skill supports the "UI Language and Theme Parity" project behaviour rule.
---

# i18n Locale Parity Review

## Purpose

Conduct a structured audit of every locale file in the project (JSON, PO, ARB), compare key sets across all active languages (TR/EN/DE), surface missing translations, detect hardcoded UI strings in JSX/TSX that bypass the i18n layer, and validate next-intl App Router wiring. Surface concrete evidence from actual files — never from assumptions. This skill directly supports the project's "UI Language and Theme Parity" behaviour rule: every user-facing string must exist in all active locales and be served through the i18n layer.

## When to use

- A PR adds, removes, or renames translation keys in any locale file.
- A new page, component, or modal is added and its strings may not yet be translated in all locales.
- A bug report mentions untranslated text, a missing locale fallback, or a wrong language being shown.
- The project's locale directory has grown and no parity audit has been run recently.
- You are onboarding a new locale (e.g. adding DE to an existing TR/EN project).
- The user asks to verify "UI Language and Theme Parity" compliance.

## When not to use

- The project has only one locale and internationalisation is explicitly out of scope.
- The PR is backend-only with no user-facing strings.
- A dedicated localisation platform (Phrase, Lokalise) is already running automated parity checks in CI — defer to its report unless it is stale.

## Procedure

### 1. Detect the i18n setup

```bash
# Identify the i18n library and message format
grep -r "next-intl\|react-i18next\|i18next\|vue-i18n\|@formatjs" package.json pnpm-lock.yaml 2>/dev/null | head -20

# Locate all locale/messages directories
find . -type d -name "messages" -o -type d -name "locales" -o -type d -name "i18n" \
 | grep -v node_modules | grep -v ".next"

# List all locale files
find . -type f \( -name "*.json" -o -name "*.po" -o -name "*.arb" \) \
 -path "*/messages/*" -o -path "*/locales/*" \
 | grep -v node_modules | grep -v ".next" | sort
```

Confirm which locales are active (e.g. `en`, `tr`, `de`) and which file is the **source of truth** (typically `en.json`).

### 2. Extract and compare key sets for parity

For JSON locale files (next-intl, i18next flat/nested):

```bash
# Flatten all keys (supports nested objects) — requires Python 3
python3 - <<'EOF'
import json, sys
from pathlib import Path

def flatten(obj, prefix=""):
 keys = []
 for k, v in obj.items():
 full = f"{prefix}.{k}" if prefix else k
 if isinstance(v, dict):
 keys.extend(flatten(v, full))
 else:
 keys.append(full)
 return keys

locale_dir = Path("messages") # adjust if needed
files = {p.stem: set(flatten(json.loads(p.read_text()))) for p in locale_dir.glob("*.json")}
all_keys = set().union(*files.values())
locales = sorted(files)
print(f"{'KEY':<60} " + " ".join(f"{l:>6}" for l in locales))
for key in sorted(all_keys):
 row = " ".join((" OK" if key in files[l] else "MISS") for l in locales)
 if "MISS" in row:
 print(f"{key:<60} {row}")
EOF
```

```bash
# Quick count per locale
for f in messages/*.json; do echo "$f: $(python3 -c "import json,sys; d=json.load(open('$f')); print(len(list(d.keys())))")"; done
```

For PO files:
```bash
# Compare msgid counts across .po files
for f in locales/**/*.po; do echo "$f: $(grep -c '^msgid ' "$f") msgids"; done
msgmerge --no-fuzzy-matching -U locales/tr/messages.po locales/en/messages.po # dry-run parity check
```

### 3. Detect hardcoded (untranslated) UI strings

```bash
# JSX/TSX text nodes that are plain strings (not wrapped in t() or <Trans>)
# Pattern: >SomeText< or >Some text with spaces< — high signal
grep -rn --include="*.tsx" --include="*.jsx" \
 '>[A-Z][a-zA-Z ]\{4,\}<\|>[A-Z][a-zA-Z ]\{4,\}$' \
 src/ app/ components/ \
 | grep -v "//\|{t(\|<Trans\|{_\|aria-label\|placeholder\|title=" \
 | head -40

# Attribute strings that should be translated (placeholders, aria-labels, titles)
grep -rn --include="*.tsx" --include="*.jsx" \
 'placeholder="[A-Z][a-zA-Z ]\{3,\}"\|aria-label="[A-Z][a-zA-Z ]\{3,\}"' \
 src/ app/ components/ | head -30

# Alert/toast/error messages hardcoded as English strings
grep -rn --include="*.ts" --include="*.tsx" \
 'toast\.\(success\|error\|info\).*"[A-Z]\|throw new Error.*"[A-Z]\|console\.error.*"[A-Z]' \
 src/ app/ | head -30
```

### 4. Validate next-intl App Router wiring

```bash
# Confirm [locale] segment exists in App Router
find app -type d -name "\[locale\]" | head -5

# Check middleware.ts exports intlMiddleware / createMiddleware
grep -n "createMiddleware\|withLocale\|intlMiddleware\|locales\s*:" middleware.ts 2>/dev/null

# Confirm next.config supports i18n or next-intl plugin
grep -n "withNextIntl\|i18n\|locales" next.config.* 2>/dev/null

# useTranslations usage in Server Components
grep -rn "useTranslations\|getTranslations" app/ --include="*.tsx" | head -20

# Check locale is passed correctly in layout
grep -n "locale\|NextIntlClientProvider\|messages" "app/[locale]/layout.tsx" 2>/dev/null \
 || grep -rn "NextIntlClientProvider" app/ --include="*.tsx" | head -10
```

### 5. Validate ICU message format, plurals, and number/date formatting

```bash
# Find keys using ICU plural/select syntax
grep -rn "plural\|select\|selectordinal" messages/ --include="*.json"

# Find number/currency/date format usages
grep -rn "useFormatter\|formatNumber\|formatDate\|Intl\.NumberFormat\|Intl\.DateTimeFormat" \
 src/ app/ --include="*.tsx" --include="*.ts" | head -20

# Verify plural forms are consistent across locales (TR has 1 form, DE/EN have 2)
python3 - <<'EOF'
import json, re
from pathlib import Path
for p in Path("messages").glob("*.json"):
 text = p.read_text()
 plural_keys = re.findall(r'"([^"]+)":\s*"\{[^}]+,\s*plural', text)
 if plural_keys:
 print(f"{p.stem}: {len(plural_keys)} plural keys — {plural_keys[:5]}")
EOF
```

### 6. Check for locale-sensitive routes and redirects

```bash
# Confirm default locale redirect behaviour in middleware
grep -n "defaultLocale\|localePrefix\|pathnames" middleware.ts i18n.ts i18n/config.ts 2>/dev/null

# Look for hardcoded language in href/Link
grep -rn 'href="/en/\|href="/tr/\|href="/de/' app/ src/ --include="*.tsx" | head -20
```

## Concrete checks

- [ ] All active locale files have identical top-level and nested key sets (zero parity delta).
- [ ] No JSX/TSX file contains a user-visible plain string literal outside `t()`, `<Trans>`, or equivalent.
- [ ] `placeholder`, `aria-label`, `title`, `alt` attributes use translation keys, not raw strings.
- [ ] `toast`, `alert`, `throw new Error` messages are either translated or in a dedicated error-key namespace.
- [ ] `[locale]` dynamic segment exists in `app/` and middleware exports locale routing config.
- [ ] `NextIntlClientProvider` receives `messages` prop in the root layout.
- [ ] `useTranslations` (client) and `getTranslations` (server/async) are used correctly — not swapped.
- [ ] ICU plural keys specify correct plural forms for each locale (TR: `one/other`, DE: `one/other`, EN: `one/other`).
- [ ] `formatNumber` / `formatDate` are used instead of raw `Intl` calls in components, so locale is consistent.
- [ ] No hardcoded `/en/`, `/tr/`, `/de/` paths in `<Link>` or `router.push()`.
- [ ] `defaultLocale` is set and the middleware redirects `/` to the correct locale.
- [ ] Locale files are included in `.gitignore` exclusion for secrets but not excluded from version control themselves.

## Commands

```bash
# Full key parity delta (missing keys per locale)
python3 - <<'EOF'
import json
from pathlib import Path

def flatten(obj, prefix=""):
 keys = []
 for k, v in obj.items():
 full = f"{prefix}.{k}" if prefix else k
 if isinstance(v, dict):
 keys.extend(flatten(v, full))
 else:
 keys.append(full)
 return keys

locale_dir = Path("messages")
files = {p.stem: set(flatten(json.loads(p.read_text()))) for p in locale_dir.glob("*.json")}
all_keys = set().union(*files.values())
for locale, keys in files.items():
 missing = sorted(all_keys - keys)
 if missing:
 print(f"\n=== {locale.upper()} MISSING {len(missing)} keys ===")
 for k in missing:
 print(f" {k}")
EOF

# Hardcoded string grep — save to file for review
grep -rn --include="*.tsx" --include="*.jsx" \
 '>[A-Z][a-zA-Z ,!?.'"'"']\{5,\}<' \
 app/ src/ components/ \
 | grep -v "//\|{t(\|<Trans\|className\|data-\|import " \
 > /tmp/hardcoded-strings.txt && wc -l /tmp/hardcoded-strings.txt

# Locale file sizes
wc -l messages/*.json

# next-intl version
node -e "const p=require('./node_modules/next-intl/package.json'); console.log('next-intl', p.version)"
```

## Required output

Produce a structured report with:
1. **Locale parity matrix** — table of all keys vs. all locales, marking each cell OK or MISSING. Group by namespace/section.
2. **Missing key inventory** — for each locale, the exact key paths that are absent, with the English reference value for context.
3. **Hardcoded string list** — `file:line | raw string | suggested key name`, sorted by file.
4. **i18n wiring status** — pass/fail for middleware, `[locale]` segment, `NextIntlClientProvider`, `getTranslations` vs `useTranslations` usage.
5. **ICU / format findings** — any plural or format issues per locale.
6. **Priority action** — the single most impactful fix (e.g. "Add 14 missing DE keys in auth namespace").

## Safety checks

- Never auto-delete or overwrite locale files; only report and propose additions.
- Do not add machine-translated strings directly — flag the gaps for human translators.
- When running the Python key-diff script against production locale bundles, confirm the `messages/` path is correct before running.
- Do not commit key additions unless the user explicitly approves the proposed translations.

## Completion criteria

Done means: the parity matrix covers all active locales, every missing key is listed with its English reference, every hardcoded string has a file:line entry, next-intl wiring is confirmed or flagged, and the report closes with a prioritised fix list. The "UI Language and Theme Parity" behaviour rule is satisfied when the parity delta reaches zero and no hardcoded strings remain.

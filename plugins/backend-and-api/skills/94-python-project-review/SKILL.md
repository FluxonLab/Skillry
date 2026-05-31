---
name: python-project-review
description: Use when you need to review a Python project for environment management correctness, dependency pinning and CVEs, pytest/coverage structure, ruff linting, mypy type checking, and common security anti-patterns including subprocess shell injection, eval/exec, pickle deserialization, and SQL string concatenation.
---

# Python Project Review

## Purpose

Conduct a structured review of a Python project — covering virtual environment and dependency management (venv/uv/poetry), requirements pinning and lockfile hygiene, test structure (pytest fixtures, coverage targets), static analysis (ruff, mypy), common security anti-patterns, and packaging/entry-point correctness. Applies directly to Python-based projects such as ExampleApp and any adjacent Python tooling in the monorepo. Surface concrete findings from actual files, never from assumptions.

## When to use

- A PR adds or modifies Python source files, `pyproject.toml`, `requirements*.txt`, or `uv.lock` / `poetry.lock`.
- A security audit is requested for a Python CLI, scraper, or automation tool.
- `pip-audit` has not been run recently and CVE exposure is unknown.
- Tests are failing, coverage is dropping, or new code has no tests.
- You are onboarding into a Python project and need to establish its health baseline.
- Ruff or mypy is not integrated in CI and linting drift has accumulated.

## When not to use

- The project is a Jupyter notebook exploration with no production intent — use a lighter notebook review.
- The PR is documentation-only (`.md`, `.rst`) with no code changes.
- The Python file is a one-line build helper inside a JavaScript monorepo — a full review is disproportionate.

## Procedure

### 1. Orient to the project layout and tooling

```bash
# Identify project root and tooling
ls pyproject.toml setup.py setup.cfg requirements*.txt uv.lock poetry.lock Pipfile.lock 2>/dev/null

# Show Python version constraint and build backend
python3 - <<'EOF'
import tomllib
from pathlib import Path
try:
 data = tomllib.loads(Path("pyproject.toml").read_text())
 proj = data.get("project", data.get("tool", {}).get("poetry", {}))
 print("name:", proj.get("name"))
 print("python:", proj.get("requires-python"))
 build = data.get("build-system", {}).get("build-backend", "not set")
 print("build-backend:", build)
except Exception as e:
 print("pyproject.toml error:", e)
EOF

# Check active venv / uv / poetry
which python3 && python3 --version
which uv && uv --version 2>/dev/null || echo "uv not found"
which poetry && poetry --version 2>/dev/null || echo "poetry not found"
```

### 2. Audit dependency pinning and lockfile hygiene

```bash
# Check requirements files for unpinned dependencies
grep -n "^[a-zA-Z]" requirements*.txt 2>/dev/null | grep -v "==" | head -30

# List direct dependencies from pyproject.toml
python3 -c "
import tomllib; from pathlib import Path
d = tomllib.loads(Path('pyproject.toml').read_text())
deps = d.get('project',{}).get('dependencies', d.get('tool',{}).get('poetry',{}).get('dependencies',{}))
print(deps)
" 2>/dev/null

# Confirm lockfile exists and is not gitignored
git ls-files uv.lock poetry.lock requirements.txt requirements-lock.txt 2>/dev/null || echo "WARNING: lockfile may not be tracked"

# Check for packages pinned with >= only (no upper bound — unpredictable upgrades)
grep -n ">=[0-9]\|~=" requirements*.txt pyproject.toml 2>/dev/null | head -20
```

### 3. Run dependency CVE audit

```bash
# pip-audit against current environment
pip-audit --desc --fix-dry-run 2>/dev/null || \
 pip install pip-audit -q && pip-audit --desc 2>/dev/null

# uv audit (if using uv)
uv pip audit 2>/dev/null

# Safety (alternative)
safety check --full-report 2>/dev/null
```

Triage each CVE by severity (Critical/High/Medium/Low). Flag any Critical or High CVEs affecting direct dependencies for immediate patching.

### 4. Run ruff linting and auto-fix check

```bash
# Show ruff config
grep -A 20 "\[tool\.ruff\]" pyproject.toml 2>/dev/null || cat .ruff.toml 2>/dev/null

# Run ruff — count violations by category
ruff check . --statistics 2>/dev/null | head -30

# Run ruff with auto-fix (dry-run) to see what can be auto-fixed
ruff check . --diff 2>/dev/null | head -60

# Check if ruff is in dev dependencies
grep "ruff" pyproject.toml requirements*.txt 2>/dev/null
```

Key rule categories to enable if missing: `E`, `W` (pycodestyle), `F` (pyflakes), `I` (isort), `S` (bandit security), `B` (bugbear), `UP` (pyupgrade).

### 5. Run mypy type checking

```bash
# Show mypy config
grep -A 20 "\[tool\.mypy\]" pyproject.toml 2>/dev/null || cat mypy.ini .mypy.ini setup.cfg 2>/dev/null | grep -A 20 "\[mypy\]"

# Run mypy
mypy . --ignore-missing-imports 2>/dev/null | tail -20

# Count Any usage (too many → type coverage is low)
grep -rn ": Any\|-> Any\|cast(Any" src/ --include="*.py" | wc -l

# Check strict mode is enabled
grep -n "strict\|disallow_untyped" pyproject.toml mypy.ini 2>/dev/null
```

### 6. Audit security anti-patterns

```bash
# subprocess shell=True (command injection risk)
grep -rn "subprocess\.\(run\|call\|Popen\|check_output\).*shell=True" \
 . --include="*.py" | grep -v "test_\|#.*shell=True"

# eval / exec with non-literal arguments
grep -rn "\beval(\|\bexec(" . --include="*.py" | grep -v "^.*#\|test_\|evaluat"

# pickle load/loads (arbitrary code execution on untrusted data)
grep -rn "pickle\.load\|pickle\.loads\|cPickle\.load" . --include="*.py"

# SQL string concatenation (SQLi risk)
grep -rn 'execute.*%\s*\|execute.*\.format(\|execute.*f".*{' . --include="*.py" | head -20

# requests without timeout (hangs / DoS)
grep -rn "requests\.\(get\|post\|put\|delete\|patch\)(" . --include="*.py" \
 | grep -v "timeout=" | head -20

# requests with verify=False (TLS disabled)
grep -rn "verify=False" . --include="*.py"

# yaml.load without Loader (arbitrary code execution)
grep -rn "yaml\.load(" . --include="*.py" | grep -v "Loader="

# tempfile.mktemp (race condition — use mkstemp/NamedTemporaryFile)
grep -rn "tempfile\.mktemp(" . --include="*.py"

# Hardcoded credentials in source
grep -rn "password\s*=\s*['\"][^${\.\(]" . --include="*.py" | grep -v "test_\|example\|#" | head -20
```

### 7. Review pytest structure and coverage

```bash
# Test discovery
find . -type f -name "test_*.py" -o -name "*_test.py" | grep -v __pycache__ | head -30

# pytest config
grep -A 15 "\[tool\.pytest\|pytest\.ini_options\]" pyproject.toml 2>/dev/null \
 || cat pytest.ini setup.cfg 2>/dev/null | grep -A 15 "\[pytest\]"

# Run tests with coverage
pytest --tb=short -q 2>/dev/null | tail -20
pytest --cov=. --cov-report=term-missing --tb=no -q 2>/dev/null | tail -30

# Check for missing test files for key modules
for f in $(find src/ . -maxdepth 2 -name "*.py" | grep -v test | grep -v __); do
 base=$(basename "$f" .py)
 find . -name "test_${base}.py" -o -name "${base}_test.py" 2>/dev/null | grep -q . \
 || echo "NO TEST: $f"
done
```

### 8. Check packaging and entry points

```bash
# Confirm __main__.py or entry_points are defined
find . -name "__main__.py" | grep -v node_modules | head -10

python3 - <<'EOF'
import tomllib; from pathlib import Path
try:
 d = tomllib.loads(Path("pyproject.toml").read_text())
 scripts = d.get("project", {}).get("scripts", d.get("tool", {}).get("poetry", {}).get("scripts", {}))
 print("entry points:", scripts or "NONE DEFINED")
except: pass
EOF

# Check import structure (relative vs absolute)
grep -rn "^from \.\|^import \." . --include="*.py" | head -20

# Check for circular imports (run import in clean env)
python3 -c "import src" 2>&1 | head -10
```

## Concrete checks

- [ ] `pyproject.toml` exists and defines `requires-python` with a specific version constraint.
- [ ] A lockfile (`uv.lock`, `poetry.lock`, or `requirements.txt` with pinned `==` versions) is committed and up to date.
- [ ] No direct dependency is unpinned (bare package name or `>=` only without upper bound in requirements files).
- [ ] `pip-audit` / `uv pip audit` reports no Critical or High CVEs.
- [ ] `ruff` is in dev dependencies and runs clean (zero errors) in CI.
- [ ] `mypy` is in dev dependencies with `disallow_untyped_defs = true` or `strict = true`.
- [ ] No `subprocess.run(..., shell=True)` with user-controlled input.
- [ ] No `eval(` or `exec(` on non-literal strings.
- [ ] No `pickle.loads` on data from untrusted sources (network, user upload).
- [ ] All `execute()` DB calls use parameterised queries (`?` / `%s` placeholders), not string formatting.
- [ ] Every `requests.*` call has an explicit `timeout=` argument.
- [ ] `requests` calls never use `verify=False` in production paths.
- [ ] `yaml.safe_load` is used instead of `yaml.load` without an explicit Loader.
- [ ] `tempfile.mkstemp` or `NamedTemporaryFile` is used instead of `mktemp`.
- [ ] No hardcoded passwords, API keys, or secrets in `.py` files.
- [ ] pytest runs with a coverage threshold (e.g. `--cov-fail-under=80`) in CI.
- [ ] A `__main__.py` or `[project.scripts]` entry point is defined for CLI tools.

## Commands

```bash
# Full security scan (bandit)
pip install bandit -q && bandit -r . -f txt -ll 2>/dev/null | head -50

# Dependency vulnerability scan
pip install pip-audit -q && pip-audit 2>/dev/null

# Lint + type check in one pass
ruff check . && mypy . --ignore-missing-imports

# Coverage report
pytest --cov=. --cov-report=term-missing -q 2>/dev/null | tail -30

# List all subprocess shell=True usages
grep -rn "shell=True" . --include="*.py" | grep "subprocess"

# List all eval/exec usages
grep -rn "\beval(\|\bexec(" . --include="*.py" | grep -v "^.*#"

# Check uv lockfile is up to date
uv lock --check 2>/dev/null && echo "lockfile up to date" || echo "lockfile OUTDATED"
```

## Required output

Produce a structured report with:
1. **Environment & tooling summary** — Python version, venv/uv/poetry, build backend, lockfile status.
2. **Dependency audit** — unpinned packages table; CVE findings from pip-audit (severity, package, version, fix).
3. **Lint findings** — ruff violation count by category; top 10 violations with file:line.
4. **Type coverage** — mypy error count; any `Any` overuse; strict mode status.
5. **Security findings** — severity-ranked table: `file:line | pattern | risk | concrete fix`. Each of the 8 anti-patterns above confirmed absent or listed.
6. **Test coverage** — overall coverage %; modules below threshold; missing test files for key modules.
7. **Packaging** — entry point status; import structure issues.
8. **Next safe action** — single highest-priority remediation.

## Safety checks

- Never execute untrusted Python files or `eval` found in the codebase as part of the review.
- Do not run `pip install` of unvetted packages to test them.
- Do not modify `pyproject.toml` or `requirements.txt` without explicit user approval.
- Redact any hardcoded credentials found to `****`; flag for rotation and removal.
- Do not commit changes during the review.

## Completion criteria

Done means: dependency pinning and CVE status are documented, ruff and mypy have been run (or their absence is flagged), all 8 security anti-pattern categories have been checked and reported, pytest coverage is measured and compared against the threshold, packaging is verified, and every finding has file:line + severity + concrete fix. The project is safe to ship when CVE audit is clean, ruff/mypy pass, security patterns are absent, and coverage meets the threshold.

---
name: notebook-hygiene
description: Use when you need to review or clean up Jupyter notebooks — out-of-order cells, hidden state, parameterization, nbconvert/papermill execution, output bloat, and secrets that must stay out of notebooks.
---

# Notebook Hygiene

## Purpose

Review and clean Jupyter notebooks so they are reproducible, reviewable, and safe to commit. Cover execution-order discipline (no out-of-order or stale cells), hidden kernel state, parameterization for automated runs (papermill), headless execution and validation (nbconvert), output and metadata bloat in version control, secrets accidentally embedded in cells or outputs, and extracting reusable logic into importable modules. The goal is a notebook that runs top-to-bottom from a fresh kernel, contains no credentials, and does not poison code review with megabytes of output diffs.

## When to use

- A PR adds or modifies a `.ipynb` file that will be committed or shared.
- A notebook "works for me" but fails on a teammate's fresh kernel (hidden state).
- Notebooks are run on a schedule (papermill/nbconvert) and need parameters and validation.
- Notebook diffs are unreviewable due to embedded outputs, execution counts, or base64 images.
- A secret or token may have been pasted into a cell or printed into an output.

## When not to use

- The notebook is throwaway scratch work that is never committed, shared, or scheduled.
- The work is a production training pipeline already in `.py` form — use the ml-training-pipeline-review skill.
- The concern is dataset versioning rather than notebook discipline — use the dataset-versioning-and-lineage skill.

## Procedure

### 1. Inventory notebooks and their committed state

```bash
find . -name "*.ipynb" | grep -v ipynb_checkpoints | head -40
# Is output being committed? Check for outputs/execution_count in tracked notebooks
grep -l '"output_type"' $(find . -name "*.ipynb" | grep -v checkpoints) 2>/dev/null | head -20
```

### 2. Check execution order and hidden state

```bash
# Extract execution_count values; non-monotonic or null indicates out-of-order/stale cells
python3 - <<'PY'
import json, glob
for nb in glob.glob("**/*.ipynb", recursive=True):
    if "checkpoint" in nb:
        continue
    cells = json.load(open(nb)).get("cells", [])
    counts = [c.get("execution_count") for c in cells if c.get("cell_type") == "code"]
    counts = [c for c in counts if c is not None]
    ooo = any(b is not None and a is not None and b < a for a, b in zip(counts, counts[1:]))
    if ooo or any(c.get("execution_count") is None for c in cells if c.get("cell_type")=="code"):
        print("OUT-OF-ORDER or UNRUN:", nb, counts[:12])
PY
```

### 3. Scan for secrets in cells and outputs

```bash
grep -rniE "api[_-]?key|secret|token|password|aws_access|bearer |sk-[a-z0-9]" $(find . -name "*.ipynb" | grep -v checkpoint) | head -25
```

Any match in source or output is a leak; flag for rotation and removal.

### 4. Verify reproducibility from a clean kernel

```bash
# Headless top-to-bottom execution; fails if any cell errors out of a fresh kernel
jupyter nbconvert --to notebook --execute --ExecutePreprocessor.timeout=600 \
  --output /tmp/_check.ipynb path/to/notebook.ipynb
```

### 5. Check parameterization and module extraction

Confirm scheduled notebooks declare a `parameters`-tagged cell (papermill), and that heavy reusable logic (data loaders, model code) is imported from `.py` modules rather than copy-pasted across notebooks.

## Concrete checks

- [ ] The notebook runs top-to-bottom from a fresh kernel with no errors (verified via nbconvert --execute).
- [ ] Execution counts are monotonic; no out-of-order or never-run cells in the committed version.
- [ ] No variable is used before it is defined within the linear cell order (no hidden-state dependency).
- [ ] No API keys, tokens, passwords, or connection strings appear in any cell or output.
- [ ] Outputs and `execution_count` are stripped before commit (nbstripout or a clean-cell policy).
- [ ] Large/base64 image outputs are not committed, keeping diffs reviewable.
- [ ] Scheduled notebooks have a `parameters`-tagged cell and run via papermill, not manual clicks.
- [ ] Reusable logic lives in importable `.py` modules, not duplicated across notebooks.
- [ ] Random seeds are set so analytical results are reproducible.
- [ ] Absolute machine paths are replaced with config/relative paths or parameters.
- [ ] A `requirements`/environment reference exists so the kernel is reproducible.

## Commands or Templates

Strip outputs and execution counts before commit (nbstripout):

```bash
pip install nbstripout
# One-off clean:
nbstripout path/to/notebook.ipynb
# Repo-wide via git filter so outputs never get committed:
nbstripout --install
```

Parameterized, headless run with papermill (parameters cell tagged `parameters`):

```python
# --- cell tagged "parameters" ---
start_date = "2026-06-01"
threshold = 0.5
output_path = "out/report.parquet"
```

```bash
# Inject parameters and execute headless; output notebook is an audit artifact.
papermill report.ipynb out/report_2026-06-01.ipynb \
  -p start_date 2026-06-01 -p threshold 0.7
```

Validate reproducibility in CI (nbconvert):

```bash
# Fail the build if the notebook does not run cleanly from a fresh kernel.
jupyter nbconvert --to notebook --execute \
  --ExecutePreprocessor.timeout=900 \
  --output-dir /tmp/nb-ci notebooks/*.ipynb
```

Pre-commit hook to block secrets and committed outputs:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/kynan/nbstripout
    rev: 0.7.1
    hooks: [{ id: nbstripout }]
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks: [{ id: detect-secrets, args: ["--baseline", ".secrets.baseline"] }]
```

## Common issues & anti-patterns

- Cells run out of order so the saved state depends on a manual click sequence nobody can reproduce.
- A variable defined in a since-deleted cell still lives in the kernel, so the notebook only "works for me".
- Hardcoded API keys or DB passwords pasted into a cell, then committed to history.
- Committing full outputs and base64 plots, making every diff thousands of lines and leaking data.
- The same data-loading or model code copy-pasted across ten notebooks instead of imported.
- Absolute home-directory paths that break on any other machine.
- Scheduled notebooks executed by manual clicking with no parameters, so runs are not auditable.
- No seed, so re-running gives different numbers and "results" cannot be reproduced.
- Long-running cells with no idempotency, re-downloading or re-training on every execution.

## Required output

Produce a structured report with:
1. **Reproducibility verdict** — does each notebook run clean top-to-bottom from a fresh kernel.
2. **State & order findings** — out-of-order/unrun cells and hidden-state dependencies, per notebook.
3. **Secret scan** — any credentials in cells/outputs, flagged for rotation (values redacted).
4. **VCS hygiene** — output/metadata bloat and whether stripping is enforced.
5. **Parameterization & modularization** — scheduled-run readiness and extractable logic.
6. **Findings table** — `notebook:cell | issue | risk | concrete fix`.
7. **Next safe action** — single highest-priority remediation.

## Safety

- Never print or commit a discovered secret; redact to `****` and flag the credential for rotation.
- Do not execute untrusted notebooks that perform network or filesystem writes without sandboxing.
- Treat data shown in outputs as potentially sensitive; strip outputs before sharing reports.
- Recommend `nbstripout --install` and a secrets pre-commit hook rather than manual cleanup alone.
- Do not rewrite notebook history or force-push to remove a leaked secret without explicit approval.

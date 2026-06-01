---
name: dataset-versioning-and-lineage
description: Use when you need to review or set up dataset versioning and lineage — DVC or lakeFS, dataset cards, lineage tracking, PII handling, and reproducible dataset references tied to code and models.
---

# Dataset Versioning and Lineage

## Purpose

Review or set up versioning and lineage for datasets so that any model, report, or analysis can be tied to the exact data it used, and that data can be reproduced. Cover dataset version control (DVC, lakeFS, Delta/Iceberg time travel, content hashing), lineage from raw source through transforms to consumed dataset, dataset documentation (dataset cards), PII identification and handling, and reproducible references pinned to a commit/version. The goal is that "which data trained this model?" has a precise, reproducible answer, and that sensitive data is tracked and governed rather than copied around untracked.

## When to use

- A model or report must be reproducible and you need to pin the exact dataset version it used.
- A PR adds a new dataset, changes a transform that feeds a model, or introduces DVC/lakeFS.
- Data provenance is unclear — nobody can say where a column came from or how it was derived.
- A dataset contains or may contain PII and its handling/governance needs review.
- Large data files are being committed to git instead of tracked by a data-versioning tool.

## When not to use

- The concern is in-pipeline data quality assertions — use the data-quality-validation skill.
- The concern is the orchestration/idempotency of the pipeline — use the data-pipeline-review skill.
- The dataset is a tiny static fixture committed with the code and never changes.

## Procedure

### 1. Detect versioning tooling and where data lives

```bash
ls .dvc dvc.yaml .lakefs* 2>/dev/null
find . -name "*.dvc" | head -20
grep -rn "import dvc\|lakefs\|DeltaTable\|iceberg\|\.parquet\|s3://\|gs://" . --include="*.py" --include="*.yaml" | head -25
# Large data files mistakenly tracked by git?
git ls-files 2>/dev/null | grep -iE "\.(csv|parquet|pkl|npz|json)$" | head -20
```

### 2. Check that consumed datasets are pinned and reproducible

```bash
grep -rn "dataset_version\|data_hash\|md5\|rev=\|commit\|version=\|read_parquet\|read_csv" . --include="*.py" | head -25
```

Confirm code references a versioned dataset (DVC rev, lakeFS branch/commit, Delta version, or a content hash) — not a mutable path whose contents can change underneath.

### 3. Trace lineage source-to-consumer

For the consumed dataset, walk back through transforms to the raw source(s). Confirm each step is recorded (a DAG, dbt lineage, DVC `dvc.yaml` stages, or documented), so the derivation is auditable.

### 4. Audit dataset documentation (dataset card)

```bash
find . -iname "dataset*card*" -o -iname "*datasheet*" -o -iname "*data_dictionary*" 2>/dev/null | head -10
```

Confirm a dataset card exists covering: source, schema, refresh cadence, owner, known limitations, license, and PII/sensitivity classification.

### 5. Identify and govern PII

```bash
grep -rniE "email|phone|ssn|first_name|last_name|address|dob|national_id|credit_card|ip_address" . --include="*.py" --include="*.sql" --include="*.yaml" | head -25
```

For any PII column, confirm it is classified, access-controlled, and either masked/hashed/tokenized where not needed in the clear, with a retention policy.

## Concrete checks

- [ ] Large/raw data files are tracked by DVC/lakeFS/object storage, not committed to git.
- [ ] Each consumed dataset is referenced by an immutable version (DVC rev, lakeFS commit, Delta version, or content hash).
- [ ] A model/report records the exact dataset version it used, alongside its code commit.
- [ ] Lineage from raw source through transforms to the consumed dataset is recorded and auditable.
- [ ] A dataset card exists with source, schema, owner, cadence, license, and limitations.
- [ ] PII columns are explicitly identified and classified by sensitivity.
- [ ] PII not needed in the clear is masked, hashed, or tokenized; access is restricted.
- [ ] A retention/deletion policy exists for sensitive datasets.
- [ ] The data-versioning remote is configured and the version reference resolves (reproducible pull).
- [ ] Schema changes to a versioned dataset are themselves versioned, not overwritten in place.
- [ ] Dataset license and usage restrictions are documented and compatible with the use case.

## Commands or Templates

Version a dataset with DVC and pin it (CLI):

```bash
dvc init
dvc add data/raw/orders.parquet        # creates orders.parquet.dvc (small, git-tracked)
git add data/raw/orders.parquet.dvc .gitignore
git commit -m "Track orders dataset v1 with DVC"
dvc remote add -d storage s3://my-bucket/dvc-store
dvc push                                # data goes to remote, not git

# Reproduce an exact historical version tied to a git commit:
git checkout <commit> -- data/raw/orders.parquet.dvc && dvc pull
```

Define a reproducible lineage stage (dvc.yaml):

```yaml
stages:
  build_features:
    cmd: python src/features.py
    deps:
      - src/features.py
      - data/raw/orders.parquet      # input is version-tracked
    outs:
      - data/features/orders.parquet # output version is reproducible
```

Tie a model run to an exact dataset version (Python):

```python
import hashlib, json, pathlib

def dataset_fingerprint(path: str) -> str:
    """Content hash so a model can record exactly which bytes it trained on."""
    h = hashlib.sha256()
    h.update(pathlib.Path(path).read_bytes())
    return h.hexdigest()

meta = {
    "dataset_path": "data/features/orders.parquet",
    "dataset_sha256": dataset_fingerprint("data/features/orders.parquet"),
    "git_commit": git_sha,
}
pathlib.Path("artifacts/run_meta.json").write_text(json.dumps(meta, indent=2))
```

Minimal dataset card (Markdown template):

```markdown
# Dataset: orders_features
- Source: warehouse.analytics.orders (raw) -> src/features.py
- Owner: data-platform team
- Refresh: hourly (incremental)
- Schema: order_id (int, pk), customer_id (int), amount (float), status (str)
- PII: customer_id (pseudonymous id; no direct identifiers in this table)
- License / usage: internal only
- Known limitations: cancelled orders excluded; pre-2025 data not backfilled
```

## Common issues & anti-patterns

- Committing multi-GB CSV/Parquet files directly to git, bloating the repo and history.
- Referencing a mutable path (e.g. `latest/orders.parquet`) so the "same" code reads different data over time.
- A model whose training data cannot be identified, making results impossible to reproduce or audit.
- Lineage living only in someone's head — no record of how a derived column was computed.
- PII copied into ad-hoc extracts and notebooks with no classification, masking, or retention control.
- A dataset card that is missing, stale, or omits PII/sensitivity and license fields.
- Overwriting a versioned dataset in place instead of creating a new version, destroying history.
- No configured remote, so `dvc pull`/lakeFS checkout cannot actually reproduce the data.

## Required output

Produce a structured report with:
1. **Versioning status** — tool in use, what is tracked vs committed to git, remote configured.
2. **Reproducibility** — whether consumed datasets are pinned and resolvable to exact bytes/version.
3. **Lineage map** — source-to-consumer derivation and whether it is recorded.
4. **Dataset cards** — presence and completeness (source, schema, owner, license, limitations).
5. **PII & governance** — identified PII columns, masking/access/retention status.
6. **Findings table** — `path/file | gap | risk | concrete fix`.
7. **Next safe action** — single highest-priority remediation.

## Safety

- Never copy, export, or print raw PII during review; reference columns by name and redact values.
- Do not overwrite or delete a versioned dataset; create a new version and preserve history.
- Treat storage credentials and remote URLs as secrets; reference env var names only and redact values.
- Recommend masking/tokenization and access controls before any PII dataset is shared more widely.
- Do not change dataset access scope, remotes, or retention without explicit approval.

---
name: ml-training-pipeline-review
description: Use when you need to review an ML training pipeline for reproducibility, data/train/val/test splitting, data leakage, checkpointing, and experiment tracking (MLflow/W&B).
---

# ML Training Pipeline Review

## Purpose

Review a model training pipeline so that runs are reproducible, free of data leakage, properly checkpointed, and tracked. Cover seeding and determinism, dataset splitting and the train/validation/test boundary, leakage from preprocessing or target encoding, feature/label alignment, checkpointing and resumption, and experiment tracking with MLflow or Weights & Biases. The goal is that a given commit plus a given dataset version reproduces the same metrics, and that reported scores are honest (no information from the test set leaked into training).

## When to use

- A PR adds or changes a training script, data-prep step, feature transform, or hyperparameter sweep.
- Reported validation metrics look too good or do not reproduce on a fresh run.
- A model performs far worse in production than in offline evaluation (leakage suspected).
- Training runs are not tracked, so results cannot be compared or reproduced.
- Long training jobs have no checkpointing and lose progress on interruption.

## When not to use

- The work is serving an already-trained model — use the model-serving-and-inference skill.
- The change is dataset versioning/lineage metadata only — use the dataset-versioning-and-lineage skill.
- The artifact is an exploratory notebook with no training intent — use the notebook-hygiene skill.

## Procedure

### 1. Locate training entry points and config

```bash
find . -name "train*.py" -o -name "*trainer*.py" -o -name "*.yaml" -path "*conf*" 2>/dev/null | grep -v __pycache__ | head -30
grep -rn "fit(\|\.train()\|trainer\.\|Trainer(\|optimizer" . --include="*.py" | head -20
```

### 2. Check determinism and seeding

```bash
grep -rn "seed\|random_state\|manual_seed\|set_seed\|deterministic\|np.random\|torch.use_deterministic" . --include="*.py" | head -25
```

Confirm seeds are set for Python `random`, NumPy, and the framework (PyTorch/TF), and that `random_state` is passed to every split and shuffle.

### 3. Audit the split and leakage boundary

```bash
# Splitting
grep -rn "train_test_split\|StratifiedKFold\|TimeSeriesSplit\|GroupKFold\|\.split(" . --include="*.py" | head -20
# Preprocessing fit location (must fit on train only)
grep -rn "\.fit(\|fit_transform\|StandardScaler\|fit_resample\|SMOTE\|TargetEncoder\|impute" . --include="*.py" | head -25
```

The split must happen *before* any `fit`/`fit_transform`. Scalers, imputers, encoders, and resamplers must be fit on the training fold only and applied to validation/test — never `fit_transform` on the full dataset.

### 4. Check feature/label alignment and temporal correctness

For time-series or any data with a time dimension, confirm the split is chronological (no future rows in training) and that features do not include information unavailable at prediction time (target leakage, post-event columns).

### 5. Verify checkpointing and tracking

```bash
grep -rn "checkpoint\|save_model\|state_dict\|ModelCheckpoint\|resume\|load_state" . --include="*.py" | head -20
grep -rn "mlflow\|wandb\|log_param\|log_metric\|log_artifact\|set_experiment" . --include="*.py" | head -25
```

Confirm checkpoints save model + optimizer + epoch so a run can resume, and that params, metrics, dataset version, and code commit are logged per run.

## Concrete checks

- [ ] All RNG seeds are set (Python, NumPy, framework) and `random_state` is passed to every split/shuffle.
- [ ] The train/val/test split happens before any preprocessing `fit`.
- [ ] Scalers, imputers, encoders, and resamplers are fit on training data only, then applied to val/test.
- [ ] No `fit_transform` on the full dataset prior to splitting.
- [ ] Resampling/oversampling (SMOTE) is applied inside the training fold only, never before the split.
- [ ] The test set is touched once, at the end — not used for model selection or early stopping.
- [ ] Time-ordered data uses a chronological split (`TimeSeriesSplit`), not random shuffling.
- [ ] No target leakage: features exclude columns unavailable at prediction time.
- [ ] Checkpoints persist model + optimizer + epoch and a run can resume from them.
- [ ] Each run logs params, metrics, dataset version/hash, and git commit to MLflow or W&B.
- [ ] Environment is pinned (requirements/lockfile) so dependencies are reproducible.
- [ ] A fixed seed + fixed data version reproduces the reported metric within tolerance.

## Commands or Templates

Full reproducibility seeding (Python / PyTorch):

```python
import os, random, numpy as np, torch

def set_global_seed(seed: int = 42) -> None:
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)
```

Leakage-safe split and preprocessing with a pipeline (scikit-learn):

```python
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

# 1) Split FIRST so the scaler never sees test rows.
X_tr, X_te, y_tr, y_te = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42)

# 2) Fit the scaler INSIDE a pipeline on the training fold only.
pipe = Pipeline([
    ("scaler", StandardScaler()),         # fit on X_tr during pipe.fit
    ("clf", LogisticRegression(max_iter=1000, random_state=42)),
])
pipe.fit(X_tr, y_tr)                       # no leakage from X_te
print("test acc:", pipe.score(X_te, y_te))  # test touched once
```

Experiment tracking + resumable checkpoint (MLflow + PyTorch):

```python
import mlflow, torch

mlflow.set_experiment("churn-model")
with mlflow.start_run():
    mlflow.log_params({"lr": lr, "epochs": epochs, "seed": 42})
    mlflow.set_tag("git_commit", git_sha)
    mlflow.set_tag("dataset_version", dataset_hash)   # tie run to data
    for epoch in range(start_epoch, epochs):
        train_one_epoch(model, optimizer, loader)
        val = evaluate(model, val_loader)
        mlflow.log_metric("val_auc", val["auc"], step=epoch)
        torch.save(                                    # resumable checkpoint
            {"epoch": epoch,
             "model": model.state_dict(),
             "optimizer": optimizer.state_dict()},
            f"ckpt_{epoch}.pt")
    mlflow.log_artifact("ckpt_final.pt")
```

## Common issues & anti-patterns

- `scaler.fit_transform(X)` before splitting — test statistics leak into training.
- SMOTE/oversampling applied to the whole dataset before the split, duplicating rows across folds.
- Using the test set for early stopping or hyperparameter selection, inflating the reported score.
- Random shuffle on time-series data, letting the model see the future.
- Target leakage: a feature derived from the label or from post-event data.
- No seed on the split, so every run reports a different "best" model.
- Checkpoints that save only weights (no optimizer/epoch), so resume restarts the schedule.
- Runs not logged, so a strong result cannot be reproduced or attributed to a commit/data version.
- Metrics computed on training data and reported as validation performance.

## Required output

Produce a structured report with:
1. **Reproducibility verdict** — seeding coverage, environment pinning, and whether a rerun matches.
2. **Split & leakage audit** — split type, preprocessing fit location, leakage findings with `file:line`.
3. **Temporal correctness** — chronological handling for time-ordered data.
4. **Checkpointing** — resumability and what is persisted.
5. **Experiment tracking** — params/metrics/data-version/commit logging status.
6. **Findings table** — `file:line | issue | impact on metric honesty | fix`.
7. **Next safe action** — single highest-priority remediation.

## Safety

- Do not retrain or overwrite a registered/production model during review.
- Do not run long GPU jobs without explicit approval; describe the change instead.
- Treat training data as potentially sensitive; reference columns by name and redact sample values.
- Never alter recorded experiment metrics to make a model look better; flag dishonest reporting.
- Do not delete checkpoints or experiment runs without explicit sign-off.

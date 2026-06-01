---
name: model-serving-and-inference
description: Use when you need to review or design model serving and inference — batch vs online patterns, latency/throughput, model versioning, rollback, and monitoring for drift and skew.
---

# Model Serving and Inference

## Purpose

Review or design how a trained model is served so that predictions are correct, fast enough, versioned, rollback-able, and monitored. Cover serving pattern selection (batch scoring vs online/real-time vs streaming), latency and throughput targets, request validation, model versioning and registry, safe rollout/rollback, training/serving skew, and production monitoring for input drift and prediction quality. The goal is a serving path where the deployed model version is known, can be reverted instantly, applies the exact same preprocessing as training, and raises an alert when inputs or outputs drift.

## When to use

- A PR adds or changes a prediction endpoint, batch scoring job, or model-loading code.
- Inference latency or throughput does not meet a stated SLA.
- A model in production behaves differently from offline evaluation (skew suspected).
- There is no clear way to identify or roll back the currently-served model version.
- Drift, data quality at inference time, or prediction monitoring is missing.

## When not to use

- The concern is how the model was trained (reproducibility/leakage) — use the ml-training-pipeline-review skill.
- The concern is the upstream feature ETL only — use the data-pipeline-review skill.
- The concern is the LLM prompt/eval rather than a deployed predictive model — use an LLM-specific review.

## Procedure

### 1. Identify the serving pattern and entry point

```bash
find . -name "serve*.py" -o -name "predict*.py" -o -name "*inference*.py" -o -name "app.py" -o -name "main.py" 2>/dev/null | grep -v __pycache__ | head -30
grep -rn "@app.post\|FastAPI\|predict(\|load_model\|TorchServe\|BentoML\|mlflow.pyfunc\|triton" . --include="*.py" | head -25
```

Classify as batch (scheduled scoring to a table/file), online (sync request/response), or streaming.

### 2. Check model versioning and loading

```bash
grep -rn "model_version\|registry\|load_model\|stage=\|@latest\|MODEL_URI\|artifact" . --include="*.py" --include="*.yaml" | head -25
```

Confirm the served version is pinned and recorded (registry stage or explicit URI), not an implicit "latest" that changes silently.

### 3. Audit preprocessing parity (training/serving skew)

```bash
grep -rn "transform\|preprocess\|StandardScaler\|tokenizer\|feature_\|pipeline\|joblib.load\|pickle.load" . --include="*.py" | head -25
```

The serving path must apply the identical preprocessing artifact used at training (same fitted scaler/encoder), ideally a saved pipeline — not a hand-rewritten transform that can drift.

### 4. Check latency, throughput, and resource bounds

```bash
grep -rn "batch_size\|timeout\|max_workers\|torch.no_grad\|eval()\|@torch.inference_mode\|onnx\|half()\|to(device)" . --include="*.py" | head -25
```

Confirm inference uses no-grad/eval mode, batches where possible, sets request timeouts, and bounds concurrency.

### 5. Verify rollout, rollback, and monitoring

```bash
grep -rn "canary\|shadow\|rollback\|previous_version\|drift\|evidently\|prometheus\|log_prediction\|monitor" . --include="*.py" --include="*.yaml" | head -25
```

Confirm there is a documented rollback to the prior version and monitoring for input drift, prediction distribution, latency, and error rate.

## Concrete checks

- [ ] Serving pattern (batch/online/streaming) matches the freshness and latency requirement.
- [ ] The served model version is explicit and recorded per prediction or per deploy (registry stage or URI).
- [ ] The exact training preprocessing artifact is reused at serving time (no hand-rewritten transform).
- [ ] Request inputs are validated (schema, types, ranges) before inference; bad input is rejected, not silently scored.
- [ ] Inference runs in eval/`no_grad`/`inference_mode`; batching is used where throughput matters.
- [ ] Online endpoints set a timeout and bound concurrency; no unbounded queueing.
- [ ] There is a one-step rollback to the previously-good model version.
- [ ] Rollout is staged (canary/shadow) for risky changes, not all-at-once.
- [ ] Predictions and inputs are logged (sampled) for monitoring and offline replay.
- [ ] Input drift and prediction-distribution drift are monitored with alert thresholds.
- [ ] Latency, throughput, and error rate are tracked against the SLA.
- [ ] Model artifacts are loaded from a trusted source; untrusted pickle is not deserialized.

## Commands or Templates

Online endpoint with input validation, pinned version, and parity (FastAPI):

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, conint, confloat
import joblib

app = FastAPI()
MODEL_VERSION = "churn:3"                     # pinned, not "latest"
pipeline = joblib.load("artifacts/churn_v3.joblib")  # same pipeline as training

class Features(BaseModel):                    # validates schema + ranges
    tenure: conint(ge=0, le=120)
    monthly_charge: confloat(ge=0, le=10_000)

@app.post("/predict")
def predict(f: Features):
    try:
        proba = pipeline.predict_proba([[f.tenure, f.monthly_charge]])[0][1]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"inference error: {e}")
    log_prediction(MODEL_VERSION, f.dict(), proba)   # for drift monitoring
    return {"model_version": MODEL_VERSION, "churn_proba": round(proba, 4)}
```

Efficient batch scoring (PyTorch):

```python
import torch

@torch.inference_mode()                        # no autograd overhead
def score_batches(model, loader, device):
    model.eval()
    out = []
    for batch in loader:                       # batched, not row-by-row
        preds = model(batch.to(device)).cpu()
        out.append(preds)
    return torch.cat(out)
```

Input drift check with a population stability index (Python):

```python
import numpy as np

def psi(expected, actual, bins=10):
    """Population Stability Index. >0.2 typically signals meaningful drift."""
    qs = np.quantile(expected, np.linspace(0, 1, bins + 1))
    e = np.histogram(expected, qs)[0] / len(expected) + 1e-6
    a = np.histogram(actual, qs)[0] / len(actual) + 1e-6
    return float(np.sum((a - e) * np.log(a / e)))
```

MLflow model registry promote/rollback (CLI):

```bash
# Promote a validated version to Production
mlflow models serve -m "models:/churn/Production" -p 5001 --no-conda
# Roll back: re-point the Production stage to the prior version
mlflow registry transition-stage --name churn --version 2 --stage Production
```

## Common issues & anti-patterns

- Loading `models:/name/latest` so the served model changes silently on every new registration.
- Re-implementing preprocessing in the serving code, drifting from the training transform (skew).
- No input validation, so malformed or out-of-range requests get scored and produce garbage.
- Running inference with autograd enabled / in train mode, wasting latency and memory.
- Row-by-row scoring in a batch job where batching would be far faster.
- No timeout on an online endpoint, letting a slow model exhaust workers under load.
- No rollback path, so a bad model must be retrained instead of reverted.
- Deserializing a model from an untrusted pickle, enabling arbitrary code execution.
- No prediction logging, so drift and skew are invisible until business metrics drop.

## Required output

Produce a structured report with:
1. **Serving pattern** — batch/online/streaming and fit to the freshness/latency requirement.
2. **Versioning & rollback** — how the served version is pinned/recorded and reverted.
3. **Skew audit** — preprocessing parity between training and serving, with `file:line`.
4. **Performance** — eval/no-grad/batching/timeout status vs SLA.
5. **Monitoring** — drift, prediction distribution, latency, and error-rate coverage.
6. **Findings table** — `file:line | issue | risk | concrete fix`.
7. **Next safe action** — single highest-priority remediation.

## Safety

- Do not deploy, promote, or roll back a production model version during review without explicit approval.
- Never load or deserialize untrusted model pickles as part of the review.
- Treat inference inputs/outputs as potentially sensitive; redact PII and reference fields by name.
- Recommend shadow or canary rollout before sending live traffic to a new version.
- Do not disable monitoring or alerting to silence noise without sign-off.

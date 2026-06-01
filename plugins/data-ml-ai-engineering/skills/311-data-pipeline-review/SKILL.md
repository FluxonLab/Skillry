---
name: data-pipeline-review
description: Use when you need to review or design an ETL/ELT data pipeline for idempotency, incremental loads, orchestration (Airflow/Dagster/cron), backfill safety, partitioning, and failure recovery.
---

# Data Pipeline Review

## Purpose

Review or design a batch or streaming data pipeline so that it is idempotent, restartable, and correct under retries and backfills. Cover extraction, transformation, load semantics, orchestration (Airflow, Dagster, Prefect, or cron), partitioning, watermarking for incremental loads, and recovery from partial failure. The goal is a pipeline that produces the same output when re-run on the same input, never double-writes, and can backfill a historical window without corrupting current data.

## When to use

- A PR adds or changes an Airflow DAG, Dagster asset/job, Prefect flow, dbt model, or a cron-driven load script.
- A pipeline produces duplicate rows, gaps, or non-deterministic counts between runs.
- Incremental loads silently miss late-arriving data or reprocess everything every run.
- A backfill is planned over a large historical window and must not disturb live tables.
- A scheduled job has no retry, alerting, or idempotency guarantees.

## When not to use

- The change is a one-off ad-hoc query with no scheduling or persistence — review the query, not a pipeline.
- The work is pure data-quality assertion logic — use the data-quality-validation skill.
- The change only touches dataset versioning or lineage metadata — use the dataset-versioning-and-lineage skill.

## Procedure

### 1. Map the pipeline surface and orchestrator

```bash
# Locate orchestration definitions
find . -path '*/dags/*.py' -o -name 'dagster*.py' -o -name '*_flow.py' 2>/dev/null | grep -v __pycache__ | head -30
ls dbt_project.yml profiles.yml 2>/dev/null
grep -rn "schedule_interval\|@daily\|cron\|ScheduleDefinition\|@schedule" . --include="*.py" | head -20
```

Identify each task, its upstream inputs, its output table or file, and the trigger cadence.

### 2. Check load semantics (idempotency)

```bash
# Look for non-idempotent appends vs idempotent upsert/overwrite
grep -rn "INSERT INTO\|\.to_sql(\|if_exists=\|COPY INTO\|MERGE INTO\|ON CONFLICT" . --include="*.py" --include="*.sql" | head -30
# Truncate/overwrite patterns
grep -rn "TRUNCATE\|DELETE FROM\|overwrite\|replace" . --include="*.py" --include="*.sql" | head -20
```

Confirm each load is one of: full overwrite of a partition, `MERGE`/upsert on a key, or insert into a fresh partition that is atomically swapped. A bare `INSERT`/append with retries will duplicate rows.

### 3. Verify incremental load and watermarking

```bash
# Watermark / high-water-mark tracking
grep -rn "watermark\|last_run\|updated_at\|incremental\|max(\|execution_date\|data_interval" . --include="*.py" --include="*.sql" | head -25
```

The cursor must use an event/business timestamp (not wall-clock), tolerate late data with a lookback window, and persist the watermark only after a successful load.

### 4. Inspect orchestration safety

```bash
# Retries, idempotency keys, catchup behavior, dependencies
grep -rn "retries\|retry_delay\|catchup\|depends_on_past\|max_active_runs\|wait_for_downstream" . --include="*.py" | head -25
```

Confirm retries are bounded, `catchup`/backfill behavior is intentional, and concurrent runs are limited so two runs cannot write the same partition.

### 5. Assess backfill design

Confirm there is a parameterized way to reprocess a date range that targets only the affected partitions, runs against a staging location or with `MERGE`, and never deletes live data before the replacement is validated.

## Concrete checks

- [ ] Every load is idempotent: partition overwrite, `MERGE`/upsert on a stable key, or atomic partition swap — not a bare append under retry.
- [ ] Re-running a task on the same interval produces identical row counts (no duplicates, no growth).
- [ ] Incremental cursor uses a business/event timestamp, persists only after success, and has a late-data lookback.
- [ ] Partitioning (by date or key) is explicit so backfills touch only the intended slices.
- [ ] Orchestrator tasks declare bounded `retries` and `retry_delay`.
- [ ] `max_active_runs` / concurrency prevents two runs writing the same partition.
- [ ] `catchup` / `depends_on_past` is set deliberately, not left at an accidental default.
- [ ] Schemas are validated or contract-checked before load, not after corruption.
- [ ] Failures alert (callback/notification), and partial writes are rolled back or isolated to staging.
- [ ] Backfill is parameterized by date range and runs against staging or `MERGE`, never destructive on live tables.
- [ ] Source extraction has a timeout and paginates rather than loading an unbounded result set into memory.

## Commands or Templates

Idempotent partitioned upsert (SQL):

```sql
-- Load a single day's partition idempotently using MERGE.
-- Safe to re-run: matched rows update, new rows insert, no duplicates.
MERGE INTO analytics.orders AS t
USING staging.orders_2026_06_01 AS s
  ON t.order_id = s.order_id
WHEN MATCHED THEN UPDATE SET
  status = s.status, amount = s.amount, updated_at = s.updated_at
WHEN NOT MATCHED THEN INSERT (order_id, status, amount, updated_at)
  VALUES (s.order_id, s.status, s.amount, s.updated_at);
```

Idempotent incremental extract with watermark and lookback (Python):

```python
from datetime import timedelta

def incremental_window(last_watermark, now, lookback=timedelta(hours=2)):
    """Return [start, end) for an incremental pull.

    Re-pulls a lookback window so late-arriving rows are captured.
    Caller must MERGE (not append) to stay idempotent.
    """
    start = last_watermark - lookback
    end = now
    return start, end

def run(conn, store):
    last = store.get_watermark("orders")          # persisted business timestamp
    start, end = incremental_window(last, now_utc())
    rows = conn.fetch(
        "SELECT * FROM source.orders "
        "WHERE updated_at >= %s AND updated_at < %s",
        (start, end),
    )
    upsert_orders(conn, rows)                       # MERGE, not INSERT
    store.set_watermark("orders", end)              # persist ONLY after success
```

Airflow task skeleton with bounded retries and no accidental catchup:

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {"retries": 3, "retry_delay": timedelta(minutes=5)}

with DAG(
    dag_id="orders_incremental",
    schedule_interval="@hourly",
    start_date=datetime(2026, 1, 1),
    catchup=False,              # do not silently backfill on deploy
    max_active_runs=1,          # never two writers on one partition
    default_args=default_args,
) as dag:
    load = PythonOperator(task_id="load_orders", python_callable=run)
```

## Common issues & anti-patterns

- Append-only `INSERT` inside a task with retries — every retry duplicates rows.
- Watermark stored before the load succeeds, so a crash skips a window permanently.
- Incremental cursor based on `now()` / wall-clock instead of the event timestamp, dropping late data.
- `catchup=True` left on by default, triggering an unintended multi-month backfill at deploy time.
- Backfill that `DELETE`s live partitions first, leaving a gap if the reload fails.
- Loading an entire source table into a DataFrame with no pagination, causing OOM as data grows.
- Transformations that depend on row order or unstable joins, producing non-deterministic output.
- No concurrency limit, so a slow run overlaps the next and both write the same partition.

## Required output

Produce a structured report with:
1. **Pipeline map** — tasks, inputs, outputs, orchestrator, and cadence.
2. **Idempotency verdict** — per-load classification (overwrite / merge / append) and whether re-runs are safe.
3. **Incremental correctness** — cursor type, late-data handling, watermark persistence ordering.
4. **Orchestration safety** — retries, concurrency, catchup, alerting status.
5. **Backfill plan** — parameterization, staging strategy, and blast radius.
6. **Findings table** — `file:line | issue | risk | concrete fix`.
7. **Next safe action** — single highest-priority remediation.

## Safety

- Never run a backfill or destructive load against production during review; describe it instead.
- Do not trigger DAGs/jobs that write to shared tables without explicit approval.
- Treat connection strings and credentials as secrets; reference env var names only and redact values.
- Recommend dry-runs and staging targets before any production reprocess.
- Do not modify orchestration schedules or production tables without explicit sign-off.

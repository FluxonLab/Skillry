---
name: data-quality-validation
description: Use when you need to add or review data quality validation — schema checks, null/duplicate/range assertions, Great Expectations or pandera suites, data contracts, freshness, and failure routing.
---

# Data Quality Validation

## Purpose

Add or review automated data quality checks that catch bad data before it reaches consumers. Cover schema conformance (column presence, types, nullability), row-level assertions (null rate, uniqueness, accepted ranges, referential integrity), freshness/timeliness, volume/anomaly checks, and data contracts between producer and consumer. Establish where checks run (in-pipeline gate vs out-of-band monitor), how failures are routed (block, quarantine, or warn), and what evidence is recorded. The goal is that no silently-corrupt dataset is published.

## When to use

- A pipeline loads data that downstream dashboards, ML features, or reports depend on.
- A PR introduces a new source table or changes a schema that consumers rely on.
- Bad data (nulls, duplicates, out-of-range values, stale partitions) has reached production undetected.
- A team wants a data contract enforced between an upstream producer and a downstream consumer.
- Great Expectations, pandera, dbt tests, or Soda are being introduced or reviewed.

## When not to use

- The dataset is throwaway exploratory output with no consumer — checks are disproportionate.
- The concern is purely pipeline orchestration/idempotency — use the data-pipeline-review skill.
- The concern is model metric quality (accuracy/drift) rather than input data — use the model-serving-and-inference skill.

## Procedure

### 1. Inventory existing checks and contracts

```bash
# Find validation frameworks already in use
grep -rn "great_expectations\|import pandera\|from pandera\|soda\|dbt test\|expect_\|pa.Column\|DataFrameSchema" . --include="*.py" --include="*.yml" --include="*.yaml" | head -30
find . -name "*.yml" -path "*expectations*" -o -name "schema*.py" 2>/dev/null | head -20
```

### 2. Classify each critical column and its constraints

For every consumed table, list columns with: type, nullable?, unique?, accepted range/set, and foreign-key target. This becomes the contract.

### 3. Verify the four assertion families exist

```bash
# null / completeness checks
grep -rn "isnull\|is_null\|notNull\|expect_column_values_to_not_be_null\|nullable=False" . --include="*.py" | head -20
# uniqueness / duplicate checks
grep -rn "duplicated\|drop_duplicates\|unique=True\|expect_column_values_to_be_unique\|COUNT(DISTINCT" . --include="*.py" --include="*.sql" | head -20
# range / set membership
grep -rn "expect_column_values_to_be_between\|isin\|ge=\|le=\|Check\." . --include="*.py" | head -20
# freshness
grep -rn "freshness\|max(updated_at\|MAX(\|expect_.*recent\|loaded_at" . --include="*.py" --include="*.sql" --include="*.yml" | head -20
```

### 4. Determine the failure-handling mode

Confirm each suite is wired as one of: hard gate (fail the pipeline, do not publish), quarantine (route bad rows to a holding area, publish the good ones), or warn-only monitor. The mode must match how critical the consumer is.

### 5. Check freshness and volume monitoring

Confirm there is an assertion that the latest partition is recent enough and that row volume is within an expected band (to catch silent partial loads or source outages).

## Concrete checks

- [ ] Every consumed table has a declared schema (columns, types, nullability) enforced before publish.
- [ ] Null-rate checks exist on columns that must be populated.
- [ ] Uniqueness/primary-key checks exist; duplicate keys fail or quarantine.
- [ ] Numeric and date columns have accepted-range checks; categoricals have accepted-set checks.
- [ ] Referential integrity is validated where a foreign key is assumed.
- [ ] A freshness check asserts the latest data is within the expected SLA.
- [ ] A volume/anomaly check catches partial loads (row count far below baseline).
- [ ] Failure mode is explicit per suite: block, quarantine, or warn — and matches consumer criticality.
- [ ] Validation runs as a gate before downstream consumers read, not only after.
- [ ] Results are persisted (docs/data docs, logs, or a metrics table) for auditability.
- [ ] A data contract is versioned and shared between producer and consumer, not implicit.

## Commands or Templates

pandera schema as a load-time gate (Python):

```python
import pandera as pa
from pandera import Column, Check, DataFrameSchema

orders_schema = DataFrameSchema(
    {
        "order_id": Column(int, nullable=False, unique=True),
        "customer_id": Column(int, nullable=False),
        "amount": Column(float, Check.in_range(0, 1_000_000), nullable=False),
        "status": Column(str, Check.isin(["new", "paid", "shipped", "cancelled"])),
        "updated_at": Column("datetime64[ns]", nullable=False),
    },
    strict=True,   # reject unexpected columns (schema drift)
    coerce=True,
)

def validate_or_raise(df):
    # Raises SchemaError listing every failing column/row — fail closed.
    return orders_schema.validate(df, lazy=True)
```

Great Expectations expectation suite (Python):

```python
import great_expectations as gx

ctx = gx.get_context()
batch = ctx.sources.pandas_default.read_dataframe(df)
batch.expect_column_values_to_not_be_null("order_id")
batch.expect_column_values_to_be_unique("order_id")
batch.expect_column_values_to_be_between("amount", min_value=0, max_value=1_000_000)
batch.expect_column_values_to_be_in_set("status", ["new", "paid", "shipped", "cancelled"])
result = batch.validate()
assert result.success, "Data quality gate failed; not publishing."
```

Freshness and volume checks in SQL (run as a gate):

```sql
-- Freshness: newest row must be within the last 6 hours.
SELECT CASE WHEN MAX(updated_at) < NOW() - INTERVAL '6 hours'
            THEN 1 ELSE 0 END AS is_stale
FROM analytics.orders;

-- Volume: today's count must be within 50%-200% of the 7-day average.
WITH today AS (SELECT COUNT(*) c FROM analytics.orders WHERE load_date = CURRENT_DATE),
     base  AS (SELECT AVG(daily) a FROM (
        SELECT COUNT(*) daily FROM analytics.orders
        WHERE load_date >= CURRENT_DATE - 7 GROUP BY load_date) x)
SELECT CASE WHEN today.c < 0.5*base.a OR today.c > 2.0*base.a
            THEN 1 ELSE 0 END AS volume_anomaly
FROM today, base;
```

## Common issues & anti-patterns

- Checks that run *after* publish, so consumers already read corrupt data before the alert fires.
- Warn-only validation on a business-critical table — the warning is ignored and bad data flows through.
- No `strict`/unexpected-column check, so silent schema drift adds or renames columns unnoticed.
- Uniqueness asserted in code but not on the load, so retries reintroduce duplicates.
- Freshness measured by load timestamp instead of event time, hiding a stalled upstream source.
- Range checks with magic numbers and no comment, so nobody can tell if a failure is real.
- Validation suite not versioned with the contract, so producer and consumer silently diverge.
- Quarantine table that nobody monitors, turning "handled" failures into permanent data loss.

## Required output

Produce a structured report with:
1. **Coverage matrix** — table × column × constraint, marking which assertions exist vs missing.
2. **Failure-mode audit** — per-suite mode (block/quarantine/warn) vs consumer criticality.
3. **Freshness & volume** — whether timeliness and volume anomalies are detected.
4. **Contract status** — is there a versioned producer/consumer contract.
5. **Findings table** — `file:line | gap | risk | concrete fix`.
6. **Next safe action** — single highest-priority check to add.

## Safety

- Do not relax or delete an existing failing assertion to make a pipeline green; investigate the data.
- Never publish or overwrite a downstream table while validating against production.
- Treat sample data shown in reports as potentially sensitive; redact PII values, reference columns by name.
- Recommend running new suites in warn mode first, then promoting to a gate after a clean baseline.
- Do not change failure-handling mode on a production table without explicit approval.

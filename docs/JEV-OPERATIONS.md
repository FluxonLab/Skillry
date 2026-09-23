# Jev operations

`skillry-jev operate --client codex` reads JSON from stdin and returns typed data.
Other supported callers: `claude`, `cursor`, `antigravity`, `antigravity-cli`.
Use the real caller. Existing public/synthetic permission and provider billing
settings apply; private records and credentials remain excluded. No new login,
service or project instruction file is needed.

Every request includes `operation`, `task`, `data_class` and nonempty `records`:
`[{"id":"record-id","text":"source text","source":"source identity"}]`.
Maximum 32 records, 2,400 UTF-8 bytes per text and 24 KB per encoded request.
For larger collections, split into bounded batches preserving source identities;
do not silently truncate. Local exact lookup, arithmetic and file IO stay code.

Success is `status: computed`; the useful output is in `result`. `usage` contains
actual provider usage. Unavailable/invalid results are not an empty successful
answer. Keep original inputs and fall back to the normal agent when necessary.
One request batches independent questions over shared source state.

## Rank and build a source packet

```json
{"operation":"rank","task":"Find the CSV parser contract","data_class":"public","top_k":1,"pinned_ids":[],"records":[{"id":"parser","text":"Reject non-integer cells with ValueError."},{"id":"colors","text":"Buttons use the blue design token."}]}
```

Code returns relevance ordering and selected `items`, retaining pinned,
potentially contradictory and uncertain records. Pass **items**, not merely the
winning ID, to the downstream writer. Keep `review_ids`/scores and original
records available. This selects context; it does not delete source material or
remove the host's system/tool instructions.

## Extract literal values

```json
{"operation":"extract","task":"Extract the invoice amount, not shipping","data_class":"synthetic","records":[{"id":"invoice","text":"Total 120; shipping 5."}],"fields":{"amount":{"description":"Invoice total","candidates":[{"id":"total","record_id":"invoice","start":6,"end":9},{"id":"shipping","record_id":"invoice","start":20,"end":21}]}}}
```

Find candidate spans with ordinary parsers/regex first. Offsets are Python
character offsets, end exclusive. Code copies the selected value from its source;
Jev cannot invent a value. `result.values` retains record/offset provenance.
No match or weak choice produces null plus review, never a fabricated field.

## Classify collections

Add `labels: {"bug":"A reported defect","question":"A request for information"}`
and `operation: classify`. The result contains grouped full records in `buckets`.
Weak/no-match records stay in `none` and `review`. This handles document labels,
intent, incident queues and failure categories without another lead classification.

## Check claims against sources

Add `operation: verify` and
`claims: [{"id":"claim","text":"The live integration passed","record_ids":["test"]}]`.
Supply the actual selected source records. Code produces checked `claims` and a
`review` queue for contradicted, insufficient or uncertain judgments. Support by
a source is not real-world truth, test execution, permission or final acceptance.
The consumer uses the review queue; it must not mark a deployment successful.

## Score independent dimensions

Add `operation: score` and
`dimensions: {"impact":{"instructions":"Impact of this reported defect","levels":["Cosmetic only","Feature degraded with workaround","Core workflow blocked"]}}`.
Results preserve per-record, per-dimension score, distribution and confidence.
Weights/thresholds are application code; changing weights need not rerun Jev.
Confidence is not an accuracy percentage or permission to act.

## Select a typed action

Add `operation: route` and
`handlers: {"lookup":{"description":"Find a public document","args":{"kind":{"description":"Requested document type","options":{"api":"API reference","guide":"Usage guide"}}}}}`.
Code returns `call: {handler, arguments}` only when the chosen branch is usable.
Unused speculative branches do not veto the selected branch. `call: null` means
review, not "choose the first handler". The consumer maps the ID into its own
already authorized registry and validates availability before execution. Never
turn the returned text into shell, arbitrary URLs, permissions or dynamic imports.

## Operational integration

Use these operations inside the existing task's execution: source packet → code
worker; selected source span → structured field; classification → work queue;
claim check → review queue; action selection → existing bounded handler.
They are not a requirement to add a permanent service or to run all six on every
task. Discovery still uses `advise` with its original ten modes.

Record Jev usage, worker usage, lead usage (when observable), quality and elapsed
time separately. Reduced source bytes demonstrate context selection only;
measured Codex tokens/quota require an actual comparable run. Missing usage is
unknown, not zero. Do not add cached tokens twice to provider totals.

Primary API patterns checked 2026-09-23: [typed questions](https://docs.typesafe.ai/primitives),
[Score](https://docs.typesafe.ai/primitives/score),
[value extraction](https://docs.typesafe.ai/cookbooks/pre_parsed_value_extraction_cookbook),
[function calling](https://docs.typesafe.ai/cookbooks/function_calling).

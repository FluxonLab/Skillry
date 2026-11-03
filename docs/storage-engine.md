# Skillry Storage engine

`tools/storage.py` is the Python 3.9+ standard-library entry point. It prints one
JSON object per invocation (`schema_version: 1`, `ok`, and a structured `error`
on failure). The optional launcher may forward argv to this file. Installing a
Skillry skill does not start the engine or enable cleanup.

Configuration defaults to `~/.config/skillry/storage.json`; SQLite state is
separate under the user's application support/state directory. Generic defaults
disable automatic archive and cleanup. `config read` returns the effective
config. `config set` reads a partial JSON object from stdin and writes mode 0600.
It never accepts a credential value. The `jev` object stores only helper and
Keychain service/account references.

Commands:

```
skillry-storage --config PATH status [--local-only]
skillry-storage --config PATH pause | resume | tick
skillry-storage --config PATH config read | set
skillry-storage --config PATH workspace list
skillry-storage --config PATH workspace register --path ABS --owner NAME --state active --generated-path REL [--generated-path REL]
skillry-storage --config PATH workspace heartbeat --id ID [--pid PID]
skillry-storage --config PATH workspace finish --id ID --state delivered|failed
skillry-storage --config PATH workspace close --id ID --accepted
skillry-storage --config PATH workspace pin|unpin --id ID
skillry-storage --config PATH cleanup preview|apply
skillry-storage --config PATH inbox list|retry --id ID|classify --id ID --category ordinary|critical|downloadable|review
skillry-storage --config PATH inbox retrieve --id ID
skillry-storage --config PATH apps inventory|preview|apply
skillry-storage --config PATH tools [list|preview ID --root ABS [--run]]
skillry-storage --config PATH jev status|classify --data-class public|synthetic
```

`jev classify` reads `{ "records": [{"id":"a","text":"abstract technical metadata"}] }`
from stdin. It returns typed advice for review; it never grants cleanup authority.
Only short public/synthetic abstractions are accepted. Unavailable helper/quota
leaves deterministic work intact. The engine uses the Jev `storage` identity.
During `tick`, ambiguous intake files enter persistent review before a bounded
Jev batch is sent. The batch contains only fixed synthetic technical descriptors
and synthetic IDs. Suggestions appear in queue `suggestion`; they do not
authorize archiving or deletion. A provider gap leaves those files in review.
An explicit owner `inbox classify` as ordinary or critical is final for that
file: it is recorded against the file's device, inode, size and mtime, and Jev
does not re-hold it. If the file changes, the record no longer matches and the
file returns to review.

Workspace cleanup requires an explicitly registered path inside an allowed
root, declared relative generated outputs, accepted closure, no hold, no live
registered PID, no tracked or marked meaningful state, no symlink escape, and
no open process. Historical unregistered worktrees have no automatic path to
deletion. `finish` records worker delivery/failure and clears the process PID;
it does not close the workspace.

A cleanup pass gathers open-process evidence in batches: one `lsof` scan of
working directories and one batched `lsof` scan for each window of up to 200
outputs, instead of two scans per output. Evidence older than 15 seconds is
scanned again before a removal, and a failed scan keeps its whole batch.
`cleanup apply` checks each output immediately before removing it. Inside
`tick`, cleanup stops after 300 seconds and continues on the next tick, so
inbox transfers never wait behind a long cleanup pass.

The inbox accepts completed standalone files. Directories, app bundles,
databases and partial downloads stay in review/waiting. Ordinary files use one
verified archive and a receipt; critical files require a second independent
verified target. Eviction waits for the configured local grace (default 24h)
and rechecks source identity, full source digest, archive proof and open use.
`inbox retrieve --id ID` copies exactly one verified archived object into a
bounded local cache and returns `retrieval.path` for the menu's Open action.
Local, SSH receiver and rclone targets are supported. Existing edited cache
files are preserved; a fresh verified sibling is created when capacity allows.
The cache defaults to 32 GiB and eight entries, with expiry set by
`local_grace_seconds`. Only registered, unchanged, expired and unopened cache
files are removed automatically. Internal incomplete stages are tracked and
cleaned after expiry. The receiver's internal `read` command streams raw bytes;
the sender hashes and size-checks them before exposing a local path.
Eviction first records a durable `evicting` claim, renames the source to a
deterministic private claim name, and verifies that moved inode before unlink.
On restart, a matching claim is restored for normal retry. Conflicting original
and claim paths stay in `review_claim`. If unlink completed before the DB state
commit, recovery marks the job evicted without claiming an unmeasured gain.
Recovery runs only at the start of `tick`, under the tick lock; `status` and
`inbox` commands never move a claim, so they cannot disturb a live eviction.
`summary.logical_bytes_removed` counts removed source/output bytes.
`summary.freed_bytes` is the sum of observed positive filesystem free-space
changes after removals (null before the first measurement), and
`summary.observed_free_delta_bytes` is the signed observed net change. They do
not infer gains from file length or APFS clone size. `disks.free_bytes` is a
current OS measurement.

Archive configuration uses `{kind:"local",root:"/existing/mounted/root",expected_device:NUMBER}`
or `{kind:"ssh",root:"/existing/mounted/root",ssh_alias:"fixed-alias",receiver_command:"/absolute/receiver",receiver_config:"/absolute/receiver-config",expected_device:NUMBER}`.
The receiver runs `receive`, `verify`, or `disk` over the fixed alias. It never
creates the archive root. `expected_device` prevents a missing mount from being
mistaken for an ordinary directory on the internal disk. Archive objects live
under `objects/sha256-prefix/full-sha256`; receipts under `receipts/full-sha256.json`.
The SQLite `receipts` table and `archive` events expose job ID, digest, byte
count and target for a catalog importer. Receiver receipt JSON also carries
idempotent `origins` entries with job ID, original filename, source host,
category, optional tag, unknown-rights marker and receipt time. Metadata is
sent as a bounded stdin header, separate from file bytes. The catalog remains
a separate read-only consumer.

An owner-managed receiver may configure
`catalog_bridge:{command:["/absolute/bridge", "--apply"],timeout_seconds:3600}`.
The fixed argv runs after a verified commit; the command must return one JSON
object with `status` (`COMPLETED`, `NO_CHANGE` or `IDEMPOTENT`) plus `source_id`
and `snapshot_id`. The engine appends `--require-sha256 <digest>` and requires
an exact `matched_sha256` in the response. A bridge gap is recorded as `catalog_sync.state=gap` in the
durable receipt and surfaced as `catalog_pending` in the sender queue. Set
`archive.catalog_required=true` on a sender that requires catalog linkage
before source eviction. A later tick or `inbox retry ID` invokes the receiver's
`catalog` reconcile command against the same verified object, without copying
its bytes again. The catalog bridge does not control archive commit durability;
the source stays local until catalog linkage and the other eviction checks pass.

Archive targets may set `transfer_timeout_seconds` and
`verify_timeout_seconds` (default 21600 seconds, range 1–86400) for large file
and readback work; SSH connection setup remains bounded separately. The engine
checks pause state before each new queued job and immediately before cleanup,
app removal and source eviction. A cancelled or timed-out child process group
is terminated; an unfinished source remains queued.

`remote_hosts` may list `{id,name,ssh_alias,receiver_command,root,expected_device}`
for bounded status probes of an approved host and its mounted volume. A menu can
use `status --local-only` while offline. The menu owns scheduling; `worker.next_run`
is null and `summary.next_cleanup_at` is the earliest settled/grace deadline.

For a receiver-side critical second copy, configure its `second_archive` as
`{kind:"rclone",root:"remote:archive/path",binary:"/absolute/rclone"}` and
the sender's SSH `receiver_config`. The receiver uses `rclone copyto`, then
streams the entire remote object with `rclone cat` for SHA-256 verification.
`verify --critical` rechecks both objects before Pro evicts its source. No
credential is sent through SSH; the receiver uses its existing local rclone
configuration. A failed second copy leaves the Pro source in place.

Application plans operate on whole `.app` bundles only. Configure each bundle
ID with `canonical`, optional `rollback`, and `rollback_archive` inside the
separate local `app_rollback_root`. Explicit `retired_app_paths` selects candidates; the canonical app is
always protected. A selected rollback is compressed to `.tar.gz` with a receipt
before its unpacked bundle is removed. Other retired bundles are removed only
when explicitly listed and inactive. The four external tool adapters expose
availability and read-only typed preview commands; their own broad purge or
sync commands are never used by the engine.
`tools preview` returns a typed command; `--run` explicitly executes its
read-only preview with a bounded output and timeout. Mole uses `analyze`,
Czkawka uses HASH plus dry-run and NONE delete method, dust limits traversal
to one filesystem, and rclone uses `check --download` against a configured
rclone archive. These reports are evidence for review, never cleanup proof.

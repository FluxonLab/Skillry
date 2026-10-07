---
name: storage-artifact-lifecycle
description: Use when registering or closing a temporary workspace, reclaiming generated output, archiving a delivered file, reviewing application copies, or diagnosing Skillry Storage receipts.
---

# Storage artifact lifecycle

## Purpose

Keep source work, durable deliveries and reproducible output in distinct lifecycles.
The optional `skillry-storage` engine provides one local JSON interface for these decisions.
Installing this skill does not install the engine, start a worker or change project instructions.
Keep host paths, machine roles, credentials and enabled roots in the local profile.

## When to use

- A task needs an isolated writable checkout or staging workspace.
- A lead is accepting worker output and closing a registered workspace.
- A disk review finds dependencies, builds or caches that may be disposable.
- An intake file needs a verified archive receipt or a review decision.
- Several copies of an application bundle appear in normal application search.
- A storage status, pause, Jev suggestion or catalog link needs explanation.

## When not to use

- A source-only review or research task needs no new checkout or dependency install.
- An unregistered historical worktree has no accepted closure record; report it for review.
- The target is a live database, unique source, uncommitted edit or unknown ignored file.
- The user only wants Archive Manager search; use its read-only catalog workflow.
- The engine is absent and the task does not include optional installation.

## Procedure

1. Identify the accountable lead, task, workspace root and permitted storage classes.
2. Reuse a suitable existing checkout before creating another writable copy.
3. Keep source-only work free of dependency installation and copied `node_modules` trees.
4. For a new temporary workspace, declare only relative generated paths that can be rebuilt.
5. Register the workspace after it exists; retain the returned workspace `id` in the task receipt.

```text
skillry-storage --config /absolute/path/to/storage.json workspace register --path /absolute/path/to/workspace --name task-name --owner lead-name --state active --generated-path node_modules --generated-path build
skillry-storage --config /absolute/path/to/storage.json workspace heartbeat --id WORKSPACE_ID --pid PROCESS_ID
```

6. Heartbeat while work is active; a stale heartbeat or crash is not an accepted close.
7. A worker marks a return `delivered` or `failed`; the lead inspects both partial and final output.
8. Integrate useful source, preserve unique commits and complete the coherent acceptance batch.
9. Only the lead closes work after acceptance; a worker exit never invokes close automatically.

```text
skillry-storage --config /absolute/path/to/storage.json workspace finish --id WORKSPACE_ID --state delivered
skillry-storage --config /absolute/path/to/storage.json workspace close --id WORKSPACE_ID --accepted
skillry-storage --config /absolute/path/to/storage.json workspace list
```

10. Preview cleanup against the current root, process and source guards before applying it.
11. Apply only for enabled classes and roots; inspect the result and measured disk space afterward.

```text
skillry-storage --config /absolute/path/to/storage.json cleanup preview
skillry-storage --config /absolute/path/to/storage.json cleanup apply
skillry-storage --config /absolute/path/to/storage.json status
```

## Source and cleanup boundary

Only declared generated output in an accepted, closed, registered workspace is eligible.
The engine checks the permitted root, symlink components, tracked files and active use.
A directory name, age, Git ignore rule or worktree prune result is not deletion authority.
Preserve unique commits, uncommitted source, meaningful ignored data and runtime state.
Do not close old unregistered worktrees merely because their owners or leases are unknown.
Reproducible dependencies, build trees, package caches and test temp output need no backup.
When eligible, remove them directly; do not create archive, trash or quarantine copies first.
Retain the package manager and lockfile identity needed to reproduce dependency output.
On APFS, logical candidate bytes are not proof of physically reclaimed bytes.
Compare the operating system's free-space reading before and after accepted cleanup.

## Durable intake and archive proof

Inspect the queue before assigning an unknown file to a durable or replaceable class.
Partial downloads, changing files, folders, app bundles and databases wait for review.
Jev may suggest a closed-set class from public or synthetic abstract technical records.
The `storage` Jev identity performs typed operations only; it has no agent inventory or prompt hook.
Do not send private filenames, paths, file contents, customer data or credentials to Jev.
An ambiguous suggestion remains in review; it never grants deletion or critical status.

```text
skillry-storage --config /absolute/path/to/storage.json inbox list
skillry-storage --config /absolute/path/to/storage.json inbox classify --id JOB_ID --category ordinary
skillry-storage --config /absolute/path/to/storage.json jev status
```

Use `critical` only when the owner explicitly marks that item critical.
Use `downloadable` or `review` for material that should not enter ordinary archive transfer.
Archive commit requires a full SHA-256 readback and a durable transfer receipt.
When configured, a catalog link is a separate requirement before local source eviction.
An offline target, changing source, missing receipt or catalog gap keeps the source local.
Ordinary material needs the configured verified archive and grace period.
Critical material additionally needs an independent second verified copy.
The receiver's transfer receipt and Archive Manager's scan receipt prove different events.

## Applications and optional tools

Treat a `.app` bundle as one package, including its embedded files and code signature.
Select one canonical installation and one identified compressed rollback outside app search.
Keep the retired path list empty until the exact old bundles have been reviewed.
Preview package-level actions before applying them; verify the launched app's canonical path.
Never deduplicate members inside different app bundles or treat matching bundle IDs as byte equality.

```text
skillry-storage --config /absolute/path/to/storage.json apps inventory
skillry-storage --config /absolute/path/to/storage.json apps preview
skillry-storage --config /absolute/path/to/storage.json tools list
skillry-storage --config /absolute/path/to/storage.json tools preview dust --root /absolute/path/to/root
```

`dust` estimates footprint; the operating system reports physical free space.
`czkawka` identifies duplicate candidates, not a right to delete originals.
`mole` previews generated/cache candidates, not the job acceptance record.
`rclone` is a configured archive transport or read-only check, not blanket sync.
Missing tools remain unavailable; skill use does not install them silently.

## Concrete checks

- The workspace ID, owner, state, generated paths and lead acceptance are recorded.
- No active lease, process, symlink escape or tracked/unique source is treated as disposable.
- A cleanup preview names exact eligible paths and reasons for excluded paths.
- Durable items retain local source until digest, receipt, catalog and grace gates pass.
- Critical items retain a second independent proof before local eviction.
- App inventory identifies one canonical bundle and a rollback outside app search.
- Jev failures leave known deterministic work available and unknown items in review.

## Required output

Report the registered workspace ID or intake job ID, owner, state and exact action.
Separate intended, configured, verified and running states.
Give transfer receipt and catalog snapshot IDs when those links actually exist.
Report candidate bytes and measured freed bytes separately; do not infer a gain.
Name any unavailable engine, missing receipt, offline target or review item as a gap.

## Safety

Use `pause` and `resume` for the storage worker without changing unrelated services.
The CLI emits a JSON object with `schema_version: 1` and structured errors.
Inspect its actual response rather than treating an exit code as acceptance evidence.
Mutations stay within the owner's enabled roots, classes and host permissions.
Portable skill installation never enables background cleanup or rewrites `AGENTS.md`.

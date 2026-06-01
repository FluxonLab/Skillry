---
name: desktop-launcher-review
description: Use when you need to review local desktop launchers, shortcuts, shell scripts, app wrappers, logging, and update safety.
---

# Desktop Launcher Review

## Purpose

Review local desktop launchers, shortcuts, shell scripts, app wrappers, logging, and update safety for packaged desktop apps (Electron, Electron-Vite, Tauri, and similar). The core obligation is fail-closed: if the packaged build is missing or stale, the launcher must refuse to open an older app and report the failing command — never silently fall back to a previous build. The output names the launch mode, a freshness verdict, the fail-closed assessment, script issues with fixes, and the next safe command.

## When to use

- A desktop launcher or shortcut script needs review before being handed to a non-technical user who will double-click it.
- The launcher is suspected to be pointing at a dev or hot-reload mode instead of the packaged production app.
- A build update was deployed but the launcher may still reference a stale `dist/` or `out/` path — freshness must be verified.
- Atomic pointer-swap or rollback safety for launcher updates has not been designed or is broken.

## When not to use

- The task is unrelated to mobile and desktop work.
- The work would require production deploys, destructive data actions, or secret disclosure.
- The concern is renderer or runtime security rather than launch correctness — use the Electron security review for `contextIsolation`, CSP, and IPC hardening.
- A narrower skill or existing project instruction already covers the need.

## Procedure

1. **Identify the launcher target.** Determine whether the shortcut or script starts the packaged app or a dev/hot-reload mode (`electron .`, `electron-vite dev`, `npm run dev`). The default expectation is the packaged app via the main launcher unless the user explicitly asked for dev mode.
2. **Check build freshness.** Compare the packaged output against source, lockfile, assets, env shape, and any `.launcher/build-manifest.json` or `dist-app/current` pointer. If any source input is newer than the packaged build, treat it as stale and require a rebuild before launch.
3. **Inspect the build and package pipeline and entrypoints.** Read the build/package scripts, the Electron `main`/`preload`/`renderer` entries, the output folder, and the launcher's actual target path. Confirm the entry paths declared in `package.json` or builder config exist inside the package.
4. **Apply fail-closed.** If the packaged app is missing or stale, run the repo's production build/package command first. If that build fails, do not open an older packaged app — report the failing command and the log path and stop.
5. **Review launcher script safety.** Check strict mode, quoting, absolute versus relative paths, error handling, the log destination, and graceful shutdown of the spawned process.
6. **Review update safety.** Confirm a new build is staged and then the pointer is swapped atomically, the previous build is retained for rollback, and a manifest records what is current.

## Concrete checks

Target and freshness:
- The launcher points at the `dist/`, `out/`, or `release/` packaged app, not `electron .` dev mode unless dev was requested.
- Source, asset, and lockfile mtimes are not newer than the packaged build.
- `.launcher/build-manifest.json` exists and matches the current source; `dist-app/current` points at the fresh build.

Entrypoints and script hygiene:
- The `main` and `preload` paths in `package.json` or builder config exist inside the package.
- Bash launchers use `set -euo pipefail`; every path is quoted.
- No hardcoded per-user home paths that break on another machine.

Logging, shutdown, update:
- The launcher writes to a stable, timestamped log path per project policy.
- stdout and stderr are captured, not discarded to `/dev/null`.
- Closing the launcher or the app cleans up child processes; no orphaned main process.
- Updates stage then swap the pointer atomically, retain the previous build, and update the manifest.
- A failed update leaves the previous working build intact and launchable.

Build correctness:
- The production build/package command is identified and runnable.
- The build output matches the launcher's expected target path.
- If the build fails, the launcher does not open any older app.

## Commands

```bash
# --- launch mode ---
# is the launcher targeting packaged vs dev?
rg -n 'electron \.|electron-vite dev|npm run dev|\.app|dist|out|release' <launcher-script>

# --- build pipeline / entrypoints ---
# build pipeline + entry definitions
cat package.json | jq '{main, scripts, build}'

# entrypoint files actually exist inside the package?
rg -n '"main"|"preload"' package.json

# --- freshness ---
# any source newer than the packaged build pointer?
find src electron -newer dist-app/current -type f 2>/dev/null | head

# manifest present and what it records
cat .launcher/build-manifest.json 2>/dev/null | jq '.' 2>/dev/null

# --- script safety ---
# machine-specific paths, destructive ops, strict mode
rg -n '/Users/[a-z]+/|/home/[a-z]+/|rm -rf|set -e|set -euo pipefail' <launcher-script>

# log destination configured?
rg -n 'logfile|>>|tee|LOG_DIR|log_path' <launcher-script>

# --- shutdown / orphans ---
# child-process spawn and cleanup handling
rg -n 'spawn|exec|trap|kill|SIGTERM|on\(.close.' <launcher-script>

# --- renderer security (quick sanity, not a full audit) ---
# BrowserWindow webPreferences hardening
rg -n 'contextIsolation|nodeIntegration|webSecurity|sandbox' . | head

# --- update mechanism ---
# auto-update / pointer-swap logic
rg -n 'autoUpdater|checkForUpdates|symlink|rename\(|pointer' . | head

# --- code signing / notarization markers ---
# packaged-app signing config (presence, not contents)
rg -n 'codeSign|notarize|hardenedRuntime|entitlements' . | head
```

## Common issues & anti-patterns

- **Silent dev fallback:** the launcher tries the packaged app, fails, and quietly runs `npm run dev` instead — the user thinks they are testing the release build but are not.
- **Stale-build open:** the pointer still references last week's `dist-app/`, so source changes never reach the user even though the launcher "works".
- **Hardcoded home path:** the script embeds a specific user home path, so it breaks the moment it runs on a different machine or account.
- **No strict mode:** a bash launcher without `set -euo pipefail` keeps going after a failed build step and opens a half-baked app.
- **Non-atomic update:** the updater overwrites the live `dist-app/` in place; a mid-write crash leaves a corrupt, unlaunchable app with no rollback.
- **Orphaned process:** closing the launcher window leaves the Electron main process running, so the next launch spawns a duplicate.
- **Logs to /dev/null:** the launcher discards stdout and stderr, so when launch fails there is no evidence to diagnose.
- **Unquoted path with spaces:** an unquoted `$APP_DIR` that contains a space splits into multiple arguments and the launch silently targets the wrong path.
- **Hot-reload masquerading as production:** the shortcut runs `electron-vite dev`, so the user is unknowingly testing an unoptimized dev build with source maps and debug tooling.
- **No build-freshness gate:** the launcher opens whatever is in `dist-app/` with no check that it reflects current source, so fixes appear to "not work" because the old build still launches.
- **Manifest not updated on swap:** the pointer is swapped but `build-manifest.json` is left stale, so the freshness check and rollback logic read the wrong current version.
- **Renderer left unhardened:** the launched window runs with `nodeIntegration: true` and `contextIsolation: false`, so any renderer flaw becomes full local code execution.
- **No previous build retained:** the updater deletes the old build before staging the new one, so a failed update leaves nothing to roll back to.

## Verification steps

Before clearing a launcher for handoff, walk it through these explicit states and confirm the behavior:
1. **Fresh build present:** the launcher opens the packaged app and writes a timestamped log entry.
2. **Stale build:** with source newer than the build pointer, the launcher refuses to open and prompts a rebuild.
3. **Missing build:** with no packaged output, the launcher reports the build command and does not fall back to dev.
4. **Failed build:** with the build command erroring, the launcher reports the failing command and log path and opens nothing.
5. **Update rollback:** after a simulated failed update, the previous build is still intact and launchable.
6. **Clean shutdown:** closing the app or launcher leaves no orphaned main process.

## Required output

Return:
1. **Launch mode:** packaged versus dev, and whether it matches intent.
2. **Build-freshness verdict:** fresh, stale, or missing, with the evidence used.
3. **Fail-closed assessment:** would a stale or failed build still open an old app?
4. **Launcher script issues:** `file:line | issue | fix`.
5. **Logging and update-safety findings.**
6. **Next safe command:** usually the production build or package.

## Safety

- Never recommend opening an older packaged app when the current build is missing or its build failed — fail closed and report the failing command plus the log path.
- Do not run a destructive or long package build silently; recommend it and let the owner trigger it.
- No hardcoded machine-specific home paths — keep launchers portable across machines.
- Redact any secrets surfaced in launcher env or logs.
- Do not delete or overwrite an existing packaged build during review.

## Completion criteria

Done means the launch mode is confirmed against intent; build freshness is judged from evidence; the fail-closed rule is verified (a stale or failed build cannot open an old app); launcher-script and update-safety issues are listed with `file:line` fixes; and the safe next command (build or package) is named.

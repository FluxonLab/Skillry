---
name: desktop-launcher-review
description: Use when you need to review local desktop launchers, shortcuts, shell scripts, app wrappers, logging, and update safety.
---

# Desktop Launcher Review

## Purpose
Use this skill to review local desktop launchers, shortcuts, shell scripts, app wrappers, logging, and update safety. The core obligation is fail-closed: if the packaged build is missing or stale, the launcher must refuse to open an older app and report the failing command — never silently fall back.

## When to use
- A desktop launcher or shortcut script needs review before being handed to a non-technical user who will double-click it.
- The launcher is suspected to be pointing at a dev/hot-reload mode instead of the packaged production app.
- A build update was deployed but the launcher may still reference a stale `dist/` or `out/` path — freshness needs to be verified.
- Atomic pointer-swap or rollback safety for launcher updates has not been designed or is broken.

## When not to use
- The task is unrelated to mobile and desktop work.
- The work would require production deploys, destructive data actions, or secret disclosure.
- A narrower skill or existing project instruction already covers the need.

## Procedure
1. Identify the launcher target: does the shortcut/script start the **packaged** app or a dev/hot-reload mode? Default expectation is the packaged app via the main launcher unless the user asked for dev mode.
2. Check build freshness: compare the packaged output against source, lockfile, assets, env shape, and any `.launcher/build-manifest.json` / `dist-app/current` pointer. Stale = must rebuild before launch.
3. Inspect the build/package pipeline and entrypoints: build/package scripts, Electron `main`/`preload`/`renderer` entries, output folder, and the launcher's actual target path.
4. Apply fail-closed: if the packaged app is missing or stale, run the repo's production build/package first; if that build fails, do **not** open an older packaged app — report the failing command and log path.
5. Review launcher script safety: strict mode, quoting, absolute/relative paths, error handling, log destination, and graceful shutdown.
6. Review update safety: atomic pointer swap, previous-build backup, and a manifest recording what is current.

## Concrete checks
- Target correctness: launcher points at the `dist/`/`out/`/`release/` packaged app, not `electron .` dev mode (unless dev was requested).
- Freshness markers: source/asset/lockfile mtime newer than the packaged build; missing/old `.launcher/build-manifest.json`; `dist-app/current` pointing at a stale build.
- Entrypoints resolve: `main`/`preload` paths in `package.json`/builder config exist in the package; `contextIsolation: true`, `nodeIntegration: false` in `BrowserWindow`.
- Script hygiene: `set -euo pipefail` (bash); quoted paths; no hardcoded `/Users/<name>` home paths that break on another machine.
- Logging: launcher writes to a stable log path (per policy, e.g. the SSD main-launcher log dir), with timestamps.
- Update safety: new build staged then pointer swapped atomically; previous build retained for rollback.

## Commands
```bash
# is the launcher targeting packaged vs dev?
rg -n 'electron \.|electron-vite dev|npm run dev|\.app|dist|out|release' <launcher-script>
# build pipeline + entrypoints
cat package.json | jq '{main, scripts}'
# freshness: any source newer than the packaged build pointer?
find src electron -newer dist-app/current -type f 2>/dev/null | head
# launcher safety smells
rg -n '/Users/[a-z]+/|rm -rf|set -e' <launcher-script>
```

## Required output
Return: launch mode (packaged vs dev) and whether it matches intent, build-freshness verdict (fresh/stale/missing) with evidence, fail-closed assessment (would a stale or failed build still open an old app?), launcher script issues (`file:line | issue | fix`), logging + update-safety findings, and the next safe command (usually the production build).

## Safety checks
- Never recommend opening an older packaged app when the current build is missing or its build failed — fail closed and report the failing command + log path.
- Do not run a destructive or long package build silently; prefer to recommend it and let the owner trigger.
- No hardcoded machine-specific home paths; keep launchers portable.
- Redact any secrets surfaced in launcher env or logs.

## Completion criteria
Done means the launch mode is confirmed against intent, build freshness is judged from evidence, the fail-closed rule is verified, launcher script + update-safety issues are listed with fixes, and the safe next command (build/package) is named.

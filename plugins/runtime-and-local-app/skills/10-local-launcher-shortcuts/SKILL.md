---
name: local-launcher-shortcuts
description: Use when you need to design local launchers, shortcuts, browser opening, logs, and shutdown behavior across macOS, Windows, and Linux.
---

# Local Launcher Shortcuts

## Purpose
Use this skill to design local launchers, shortcuts, browser opening, logs, and shutdown behavior across macOS, Windows, and Linux. The goal is a double-click experience that a non-technical user can run: start, wait for readiness, open the browser, and stop cleanly — with no orphaned ports or stale processes.

## When to use
- A local app needs a platform-appropriate launch shortcut (`.command`, `.bat`, `.desktop`) so non-developers can start it without a terminal.
- A launcher script exists but does not health-gate the browser open, leaks ports on Ctrl-C, or hardcodes paths that break on another machine.
- The project targets multiple OSes and needs the correct cross-platform `open` / `xdg-open` / `start ""` pattern for each.
- Log destination and rotation for a local app launcher are not yet defined or do not follow the project's log-path policy.

## When not to use
- The task is unrelated to runtime and local app work.
- The work would require production deploys, destructive data actions, or secret disclosure.
- A narrower skill or existing project instruction already covers the need.

## Procedure
1. Identify what the launcher must start (server, app, script), the URL/port to open, the log destination, and the target OSes.
2. Write a core launcher that: starts the process, records its PID, waits for readiness, opens the browser (if a web UI), tees logs, and traps signals for clean shutdown.
3. Wrap it per OS so a non-technical double-click works: macOS `.command`, Windows `.bat`/`.ps1` (+ optional `.lnk`), Linux `.desktop`.
4. Choose the cross-platform "open" correctly: macOS `open`, Linux `xdg-open`, Windows `start ""`.
5. Send logs to a stable path (project `logs/` or the SSD log root per policy), with timestamps.
6. Verify the launcher cold-starts, opens the UI only after readiness, and shutdown frees the port and leaves no orphan process.

## Cross-platform essentials
- Open URL: `open` (macOS) · `xdg-open` (Linux) · `start "" <url>` (Windows cmd) · `Start-Process <url>` (PowerShell).
- macOS double-click: a `*.command` file with `chmod +x`; first run may need right-click → Open (Gatekeeper).
- Windows: `.bat` for cmd or `.ps1` for PowerShell; a `.lnk` shortcut can point at it with an icon.
- Linux: a `*.desktop` entry with `Exec=` and `Terminal=false`.
- Readiness gate: poll a health URL or a "listening on" log line before opening the browser.
- Shutdown: write a PID file and `trap`/kill the process tree; free the port.

## Launcher skeletons
```bash
# macOS run.command (chmod +x run.command)
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p logs
npm run start >"logs/app-$(date +%Y%m%d-%H%M%S).log" 2>&1 &
echo $! > .app.pid
trap 'kill "$(cat .app.pid)" 2>/dev/null; rm -f .app.pid' EXIT INT TERM
until curl -fsS http://localhost:3000/health >/dev/null 2>&1; do sleep 0.5; done
open http://localhost:3000
wait
```
```bat
:: Windows run.bat
@echo off
start "" /b cmd /c "npm run start > logs\app.log 2>&1"
:wait
timeout /t 1 >nul
curl -fsS http://localhost:3000/health >nul 2>&1 || goto wait
start "" http://localhost:3000
```

## Required output
Return: launcher file(s) per target OS, the open command used, the log path, the readiness gate, the shutdown mechanism, and the cold-start verification (started → opened after ready → clean stop, port freed). Note any OS not covered.

## Safety checks
- Use absolute or `$(dirname "$0")`-relative paths; never hardcode another machine's home path.
- Quote paths (spaces!) and use `set -euo pipefail` in bash.
- Don't launch with elevated privileges unless required; don't embed secrets in the launcher.
- Guarantee shutdown frees the port; avoid orphaned background processes.

## Completion criteria
Done means a double-click launcher exists for the target OS(es), it starts the process, opens the UI only after readiness, logs to the right path, and stops cleanly without leaking a port or process.

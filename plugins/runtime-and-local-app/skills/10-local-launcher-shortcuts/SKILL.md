---
name: local-launcher-shortcuts
description: Use when you need to design local launchers, shortcuts, browser opening, logs, and shutdown behavior across macOS, Windows, and Linux.
---

# Local Launcher Shortcuts

## Purpose
Design local launchers and shortcuts that give a non-technical user a double-click experience: start the app, wait for readiness, open the browser, and stop cleanly — with no orphaned ports or stale processes — across macOS, Windows, and Linux. The launcher must use relative-to-itself paths (never a hardcoded home directory), gate the browser-open on a health signal, write timestamped logs to a stable path, and trap signals so shutdown frees the port every time.

## When to use
- A local app needs a platform-appropriate launch shortcut (`.command`, `.bat`/`.ps1`, `.desktop`) so non-developers can start it without a terminal.
- A launcher exists but does not health-gate the browser open, leaks ports on Ctrl-C, or hardcodes paths that break on another machine.
- The project targets multiple OSes and needs the correct cross-platform open pattern for each.
- Log destination and rotation for a launcher are undefined or do not follow the project's log-path policy.

## When not to use
- The task is unrelated to runtime / local-app work.
- The work requires production deploys, destructive data actions, or secret disclosure.
- A narrower skill or an existing project launcher convention already covers the need.
- The app is a long-running service better managed by `systemd`/`launchd`/a service manager than a double-click script.

## Procedure
1. **Identify launch inputs:** what process to start (server, app, script), the URL/port to open, the log destination, and the target OSes.
2. **Write a core launcher** that: `cd`s to its own directory, starts the process and records its PID, polls a readiness signal, opens the browser only after ready, tees logs to a timestamped file, and traps `EXIT INT TERM` for clean shutdown.
3. **Wrap it per OS** so a double-click works for non-developers: macOS `.command` (`chmod +x`), Windows `.bat` (cmd) or `.ps1` (PowerShell, optionally a `.lnk` with an icon), Linux `.desktop` with `Terminal=false`.
4. **Choose the open command correctly per platform:** `open` (macOS), `xdg-open` (Linux), `start "" <url>` (Windows cmd), `Start-Process <url>` (PowerShell).
5. **Define the readiness gate:** poll a health URL, or grep the process log for a "listening on" line, before opening the browser. Time out and fail closed with a log pointer.
6. **Send logs to a stable path** — the project `logs/` directory or the org log root per policy — with a timestamp in the filename.
7. **Document the first-run unblock step** for non-technical users (macOS right-click→Open for Gatekeeper; Windows "More info → Run anyway" for SmartScreen) and add log rotation so repeated launches do not fill the disk.
8. **Verify** the launcher cold-starts, opens the UI only after readiness, and shutdown frees the port and leaves no orphan (`lsof -i :PORT` empty afterward).

## Cross-platform essentials
- Open a URL: `open` (macOS) · `xdg-open` (Linux) · `start "" <url>` (Windows cmd) · `Start-Process <url>` (PowerShell).
- macOS double-click: a `*.command` file with `chmod +x`; the first run may need right-click → Open to clear Gatekeeper.
- Windows: `.bat` for cmd or `.ps1` for PowerShell; a `.lnk` shortcut can point at it and carry an icon.
- Linux: a `*.desktop` entry with `Exec=` and `Terminal=false`; mark it executable and "Allow launching".
- Readiness gate: poll the health URL or watch the log for the listening line — never a blind `sleep`.
- Shutdown: write a PID file and `trap`/kill the process (group), then confirm the port is free.

## Concrete checks
- A double-click launcher exists for each target OS.
- The launcher uses `$(dirname "$0")`-relative or absolute-derived paths, never another machine's home directory.
- The browser opens only after the readiness gate passes; the gate times out and fails closed.
- Logs write to the policy path with a timestamp; no secrets appear in them.
- Shutdown traps signals, kills the process, and frees the port (verified empty).
- The correct open command is used per OS.
- Paths with spaces are quoted; bash scripts use `set -euo pipefail`.
- Shutdown kills the whole process group, not just the parent PID.
- Logs are rotated or size-capped so repeated launches do not fill the disk.
- The first-run OS-gatekeeper step (macOS right-click→Open / Windows "Run anyway") is documented for non-technical users.
- A Linux `.desktop` uses an absolute or `%k`-relative `Exec`, not a bare relative path.

## Commands
```bash
# macOS run.command  (chmod +x run.command; double-clickable)
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p logs
LOG="logs/app-$(date +%Y%m%d-%H%M%S).log"
npm run start >"$LOG" 2>&1 &
echo $! > .app.pid
trap 'kill "$(cat .app.pid)" 2>/dev/null; rm -f .app.pid' EXIT INT TERM
for i in $(seq 1 60); do
  curl -fsS http://localhost:3000/health >/dev/null 2>&1 && break
  sleep 0.5
  [ "$i" = 60 ] && { echo "not ready, see $LOG"; exit 1; }
done
open http://localhost:3000
wait
```
```bat
:: Windows run.bat
@echo off
if not exist logs mkdir logs
start "" /b cmd /c "npm run start > logs\app.log 2>&1"
:wait
timeout /t 1 >nul
curl -fsS http://localhost:3000/health >nul 2>&1 || goto wait
start "" http://localhost:3000
```
```powershell
# Windows run.ps1 (health-gated, opens default browser)
$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force logs | Out-Null
$p = Start-Process npm -ArgumentList "run","start" -PassThru `
       -RedirectStandardOutput "logs\app.log" -RedirectStandardError "logs\err.log"
try {
  do { Start-Sleep -Milliseconds 500 }
  until (try { Invoke-WebRequest http://localhost:3000/health -UseBasicParsing | Out-Null; $true } catch { $false })
  Start-Process "http://localhost:3000"
  Wait-Process -Id $p.Id
} finally { Stop-Process -Id $p.Id -ErrorAction SilentlyContinue }
```
```ini
# Linux app.desktop (mark executable, "Allow launching")
[Desktop Entry]
Type=Application
Name=My Local App
Exec=/bin/bash -c "cd %k/.. && ./run.sh"
Terminal=false
Icon=my-local-app
```
```bash
# Kill the whole process tree on shutdown (server may spawn children)
trap 'kill -- -$$ 2>/dev/null' EXIT INT TERM   # negative PID = process group
# Verify clean shutdown after Ctrl-C
lsof -i :3000 || echo "port 3000 released"
chmod +x run.command          # make the macOS launcher double-clickable

# Simple log rotation: keep the 5 most recent run logs
ls -t logs/app-*.log 2>/dev/null | tail -n +6 | xargs -r rm --
```
```bash
# Create a clickable Windows .lnk pointing at run.bat (with an icon), via PowerShell
powershell -Command "\$s=(New-Object -ComObject WScript.Shell).CreateShortcut('My App.lnk'); \
  \$s.TargetPath='run.bat'; \$s.IconLocation='app.ico'; \$s.Save()"

# macOS: clear the quarantine attribute so the first double-click is not blocked
xattr -d com.apple.quarantine run.command 2>/dev/null || true

# Confirm the launcher script is actually executable on macOS/Linux
test -x run.command && echo "executable" || chmod +x run.command

# Confirm the port is truly free before the launcher starts (avoid a confusing failure)
lsof -i :3000 >/dev/null && echo "BUSY: stop the other instance first" || echo "free"
```

## Common issues & anti-patterns
- **Hardcoded home path.** A launcher that `cd`s into an absolute home-directory path breaks on every other machine. Use `cd "$(dirname "$0")"` so it works wherever the folder lives.
- **Blind `sleep` before opening.** `sleep 3; open ...` races startup; on a slow boot the browser hits connection-refused. Poll health instead.
- **Orphaned process on Ctrl-C.** Backgrounding the server without `trap` leaves the port held; the next launch fails with EADDRINUSE. Trap signals and kill on exit.
- **Unquoted paths with spaces.** A log path under a folder with spaces breaks redirection. Quote every path and set `set -euo pipefail`.
- **Wrong open command per OS.** Using `open` on Linux (it does something else) or `xdg-open` on macOS (not present). Branch on `uname` or ship per-OS launchers.
- **Secrets embedded in the launcher.** Putting an API key or token literal in the `.bat`/`.command`. Read it from the environment or a gitignored config file.
- **Killing only the parent PID.** The server forks a child (e.g. a bundler); killing the parent orphans the child, which keeps the port. Kill the process group (`kill -- -$$`).
- **Unbounded log growth.** Every launch appends to one log forever until the disk fills. Rotate (timestamped filenames + prune) or cap the size.
- **Gatekeeper/SmartScreen surprise.** The first double-click is blocked by the OS and the non-technical user gives up. Document the one-time right-click→Open (macOS) / "More info → Run anyway" (Windows) step.
- **`.desktop` with a relative `Exec`.** Launched from a file manager, the working directory is unpredictable, so a relative `Exec=./run.sh` fails. Use `%k` or an absolute path.

## Required output
Return: the launcher file(s) per target OS, the open command used, the log path, the readiness gate, the shutdown mechanism, and the cold-start verification (started → browser opened after ready → clean stop, port freed). Note any OS left uncovered and why.

## Safety
- Use absolute or `$(dirname "$0")`-relative paths; never hardcode another machine's home path.
- Quote paths (spaces) and use `set -euo pipefail` in bash launchers.
- Do not launch with elevated privileges unless required; never embed secrets in the launcher.
- Guarantee shutdown frees the port; avoid orphaned background processes.

## Completion criteria
Done means a double-click launcher exists for each target OS, it starts the process and opens the UI only after readiness, logs to the policy path without secrets, and stops cleanly with the port verified free — with any uncovered OS noted.

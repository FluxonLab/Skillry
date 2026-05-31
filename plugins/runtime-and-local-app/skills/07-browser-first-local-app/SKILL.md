---
name: browser-first-local-app
description: Use when you need to prefer a local service plus browser UI over desktop runtime complexity unless a native shell is explicitly required.
---

# Browser First Local App

## Purpose
Use this skill to prefer a local service plus browser UI over desktop runtime complexity unless a native shell is explicitly required. This default eliminates packaging overhead, simplifies debugging, and keeps the app inspectable via browser devtools from day one.

## When to use
- A local tool or utility is being built and the choice between a browser UI and a native desktop shell has not been made — default to browser-first.
- An existing local app needs a launcher that health-gates the browser open and shuts down cleanly without orphaned ports.
- The project is moving from a CLI-only interface to a visual local UI and needs a minimal server + browser pattern established.
- A native desktop shell is being proposed for a task that only requires filesystem or local network access (which the browser can handle).

## When not to use
- The task is unrelated to runtime and local app work.
- The work would require production deploys, destructive data actions, or secret disclosure.
- A narrower skill or existing project instruction already covers the need.

## Procedure
1. Decide the shell: default to **local service + browser UI** unless the task truly needs a native shell (see rule). Record the reason.
2. Pick a local HTTP server appropriate to the stack (static server, Express/Fastify, FastAPI, Vite preview) and a fixed or auto-selected port.
3. Add a health/readiness endpoint (`GET /health` → 200) and gate browser-open on it — never open the UI before the server is ready.
4. Provide a launcher that starts the server, waits for health, opens the default browser cross-platform, tees logs, and shuts down cleanly on Ctrl-C.
5. Write logs to a file (per SSD/log policy) and keep the console quiet but useful.
6. Verify: cold start → health passes → browser opens to a working page → Ctrl-C stops the server with no orphan process/port.

## When a native shell IS justified
- Needs OS APIs unavailable to the browser (tray, global shortcuts, deep filesystem, native menus).
- Must run fully offline as a packaged binary, or needs code signing / auto-update as a desktop app.
- Otherwise prefer browser-first: simpler runtime, easier debugging, no packaging tax.

## Launcher pattern
```bash
#!/usr/bin/env bash
set -euo pipefail
PORT="${PORT:-3000}"; LOG="${LOG:-./run.log}"
npm run start >"$LOG" 2>&1 & SRV=$!
trap 'kill "$SRV" 2>/dev/null' EXIT INT TERM
# readiness gate: poll /health before opening the browser
for i in $(seq 1 60); do
 curl -fsS "http://localhost:$PORT/health" >/dev/null 2>&1 && break
 sleep 0.5
 [ "$i" = 60 ] && { echo "server not ready, see $LOG"; exit 1; }
done
case "$(uname -s)" in
 Darwin) open "http://localhost:$PORT" ;;
 Linux) xdg-open "http://localhost:$PORT" ;;
 *) start "" "http://localhost:$PORT" ;;
esac
wait "$SRV"
```

## Required output
Return: shell decision (browser-first vs native) with rationale, server + port + health endpoint, the launcher and log location, and the cold-start verification result (ready → opened → clean shutdown, no orphan port). Note any native-shell requirement that overrode the default.

## Safety checks
- Bind to `localhost` by default; do not expose the dev server on `0.0.0.0` without reason.
- Always gate browser-open on the health check; fail closed if the server never becomes ready.
- Ensure shutdown kills the server process and frees the port (no orphans).
- Keep secrets out of logs and out of the URL/query string.

## Completion criteria
Done means the app runs as a local service with a health-gated launcher, the browser opens only after readiness, logs land in the right place, and shutdown is clean with no leaked port or process.

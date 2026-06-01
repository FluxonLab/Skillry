---
name: browser-first-local-app
description: Use when you need to prefer a local service plus browser UI over desktop runtime complexity unless a native shell is explicitly required.
---

# Browser First Local App

## Purpose
Default a local tool to a **local HTTP service plus a browser UI** instead of a packaged desktop shell, unless a native shell is genuinely required. Browser-first removes packaging and code-signing overhead, makes the app inspectable through browser devtools from day one, and keeps debugging in familiar territory (network tab, console, breakpoints). The deliverable is a service with a health endpoint, a launcher that gates the browser-open on readiness, file-based logs, and a clean shutdown that frees the port.

## When to use
- A local tool or utility is being built and the shell choice (browser vs native desktop) has not been made — default to browser-first.
- An existing local app needs a launcher that health-gates the browser open and shuts down without orphaned ports or processes.
- A project is moving from a CLI-only interface to a visual local UI and needs a minimal server + browser pattern established.
- A native desktop shell is being proposed for a task that only needs filesystem or local-network access — which a localhost service already covers.

## When not to use
- The task is unrelated to runtime / local-app work.
- The work requires production deploys, destructive data actions, or secret disclosure.
- A native shell is genuinely required (see the dedicated section) — then browser-first is the wrong default.
- A narrower skill or an existing project launcher convention already covers the need.

## Procedure
1. **Decide the shell.** Default to local service + browser UI. Choose native only if the task hits a browser limitation listed below. Record the reason either way.
2. **Pick the server for the stack** (static file server, Express/Fastify, FastAPI/uvicorn, Vite preview) and a port — fixed (e.g. 3000) or auto-selected if conflicts are likely.
3. **Add a readiness endpoint** (`GET /health` returning 200 with a tiny JSON body) that reflects real readiness — DB connected, migrations applied — not merely "process is up."
4. **Bind to `localhost` (127.0.0.1) by default.** Only bind `0.0.0.0` when another device must reach it, and call that out as an exposure decision.
5. **Write a launcher** that starts the server, polls `/health` until ready (with a timeout), opens the default browser cross-platform, tees logs to a file, and traps signals for clean shutdown.
6. **Send logs to a stable file path** per the project's log policy; keep the console output quiet but useful (one "ready on http://localhost:PORT" line).
7. **Restrict CORS** on the local API to the app's own origin, and inject the API base URL into the client at startup so an auto-selected port still works.
8. **Verify the full cycle:** cold start, health passes, browser opens to a working page, Ctrl-C stops the server, and the port is free afterward (no orphan process).

## When a native shell IS justified
- Needs OS APIs the browser cannot reach: system tray, global keyboard shortcuts, deep/arbitrary filesystem access, native OS menus, multi-window management.
- Must ship as a signed, auto-updating, fully-offline packaged binary.
- Requires native notifications or protocol handlers beyond what a PWA provides.
- Otherwise prefer browser-first: simpler runtime, easier debugging, no packaging tax.

## Concrete checks
- Shell decision (browser-first vs native) is recorded with a one-line rationale.
- A `GET /health` endpoint exists and returns 200 only when the app is truly ready.
- The server binds `localhost` by default; any `0.0.0.0` bind is justified.
- The launcher polls health before opening the browser and fails closed (non-zero exit, log pointer) if readiness never arrives.
- Logs land in a file at the policy path; secrets never appear in logs or in the opened URL/query string.
- Shutdown kills the server process and frees the port — verified with `lsof -i :PORT` returning empty.
- The open command is correct per OS (`open` / `xdg-open` / `start ""`).
- The readiness poll has a finite timeout and fails closed with a log pointer.
- The client receives its API base URL at startup rather than hardcoding host/port.
- CORS on the local API is restricted to the app's own origin, not `*`.
- Each "native shell needed" claim maps to a row in the decision matrix, not a vague preference.

## Commands
```bash
# Confirm the target port is free before launch
lsof -i :3000 || echo "port 3000 free"

# Cross-platform health-gated launcher
#!/usr/bin/env bash
set -euo pipefail
PORT="${PORT:-3000}"; LOG="${LOG:-./run.log}"
npm run start >"$LOG" 2>&1 & SRV=$!
trap 'kill "$SRV" 2>/dev/null' EXIT INT TERM
for i in $(seq 1 60); do
  curl -fsS "http://localhost:$PORT/health" >/dev/null 2>&1 && break
  sleep 0.5
  [ "$i" = 60 ] && { echo "server not ready, see $LOG"; exit 1; }
done
case "$(uname -s)" in
  Darwin) open "http://localhost:$PORT" ;;
  Linux)  xdg-open "http://localhost:$PORT" ;;
  *)      start "" "http://localhost:$PORT" ;;
esac
wait "$SRV"

# Verify readiness and shutdown manually
curl -fsS -w '\n%{http_code}\n' http://localhost:3000/health
# after Ctrl-C, confirm no orphan holds the port:
lsof -i :3000 || echo "port released cleanly"
```
```js
// Health endpoint that reflects REAL readiness (Express)
app.get('/health', async (_req, res) => {
  try {
    await db.query('SELECT 1');          // dependency check, not just "process up"
    res.status(200).json({ status: 'ok' });
  } catch (e) {
    res.status(503).json({ status: 'degraded' });
  }
});
```
```python
# FastAPI equivalent
@app.get("/health")
async def health():
    try:
        await database.execute("SELECT 1")
        return {"status": "ok"}
    except Exception:
        return JSONResponse({"status": "degraded"}, status_code=503)
```
```bash
# Auto-select a free port when a fixed one may be taken (Node one-liner)
PORT=$(node -e 'const s=require("net").createServer();s.listen(0,()=>{console.log(s.address().port);s.close()})')
echo "using port $PORT"

# Confirm the server is bound to localhost, not 0.0.0.0 (exposure check)
lsof -nP -iTCP:"$PORT" -sTCP:LISTEN | rg -q '127.0.0.1|\[::1\]' && echo "localhost only" || echo "WARNING: bound on all interfaces"
```
```bash
# Full cold-start verification in one pass (ready -> open -> shutdown -> port free)
./run.sh & LP=$!
until curl -fsS http://localhost:3000/health >/dev/null 2>&1; do sleep 0.5; done
echo "ready"; curl -fsS -w 'home=%{http_code}\n' -o /dev/null http://localhost:3000/
kill "$LP"; sleep 1
lsof -i :3000 && echo "FAIL: orphan holds the port" || echo "PASS: port released"

# CORS check: the local API should reject a foreign origin
curl -s -o /dev/null -w 'cors=%{http_code}\n' -H "Origin: http://evil.example" \
  -X OPTIONS http://localhost:3000/api/data   # expect a restricted/!200 preflight

# No secrets leaked into the run log
rg -nEi "api[_-]?key|secret|token|password" run.log && echo "WARNING: secret in log" || echo "log clean"
```

## Browser-first vs native (decision matrix)
| Requirement | Browser-first covers it? |
|-------------|--------------------------|
| Local files via picker / drag-drop | yes (File System Access API or upload) |
| Local network / localhost service | yes |
| Arbitrary filesystem path access | no — native shell |
| System tray / global hotkeys | no — native shell |
| Signed, auto-updating offline binary | no — native shell |
| Native OS menus / multi-window | no — native shell |
| Inspectable with devtools out of the box | yes (advantage of browser-first) |

## Common issues & anti-patterns
- **Opening the browser before the server is ready.** A fixed `sleep 2` races startup; on a slow machine the browser loads a connection-refused page. Always poll `/health`.
- **Health check that lies.** `/health` returns 200 the instant the process starts, before the DB pool or migrations are ready, so the first real request fails. Make health reflect dependencies.
- **Binding `0.0.0.0` by default.** Exposes the dev server to the local network (and anything on it) without intent. Bind `localhost` unless remote access is a stated requirement.
- **Orphaned process on Ctrl-C.** The launcher backgrounds the server but does not trap signals, so the port stays held and the next launch fails with EADDRINUSE.
- **Secrets in the URL.** Passing a token as `?token=...` puts it in browser history and server logs. Use headers or a session cookie instead.
- **Reaching for Electron reflexively.** Wrapping a pure web UI in a desktop shell for a task that needs no OS API — paying the packaging and signing tax for nothing.
- **No timeout on the readiness poll.** An infinite `until curl` loop hangs forever if the server crashes on boot. Cap the poll and fail closed with a log pointer.
- **CORS opened to `*` on the local API.** A dev convenience that lets any site in the browser call the local service. Restrict the origin to the app's own URL.
- **Logging request bodies to the console.** Convenient locally, but it spills tokens and PII into a file or terminal scrollback. Log metadata, not payloads.
- **Hardcoding `http://localhost:3000` in the client.** Breaks the moment the port auto-selects. Inject the base URL at startup.

## Required output
Return: the shell decision (browser-first vs native) with rationale; the server, port, and health endpoint; the launcher script and its log location; and the cold-start verification result (ready → browser opened → clean shutdown, port freed). Note any native-shell requirement that overrode the browser-first default.

## Safety
- Bind to `localhost` by default; never expose the dev server on `0.0.0.0` without a stated reason.
- Always gate the browser-open on the health check and fail closed if readiness never arrives.
- Ensure shutdown kills the server process and frees the port (no orphans).
- Keep secrets out of logs and out of the URL/query string.

## Completion criteria
Done means the app runs as a localhost service with a health-gated launcher, the browser opens only after readiness, logs land at the policy path with no secrets, and shutdown is clean with no leaked port or process — with any native-shell exception documented.

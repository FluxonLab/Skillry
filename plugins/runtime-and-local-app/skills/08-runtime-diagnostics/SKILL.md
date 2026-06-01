---
name: runtime-diagnostics
description: Use when you need to diagnose startup, process, port, dependency, environment, and runtime health failures.
---

# Runtime Diagnostics

## Purpose
Provide a systematic, non-destructive procedure for diagnosing why a local or dev-environment application fails to start, crashes immediately, or behaves incorrectly at runtime. It covers port conflicts, missing or wrong environment variables, runtime/dependency version mismatches, wrong working directory, broken native modules, and process-level resource limits — the failure classes behind most "it works on my machine" reports. The output is, per step, the command run, the finding, the action taken, and the verification that the issue is resolved.

## When to use
- `npm run dev` / `python manage.py runserver` / `go run .` exits non-zero and the cause is not obvious.
- A service starts but immediately crashes (OOM, unhandled exception, fatal signal).
- "Address already in use" / `EADDRINUSE` on a specific port.
- The app runs but cannot reach its database, cache, or an external dependency.
- A container or process starts on one machine but not another due to environment differences.

## When not to use
- The error is a compile/type error — that is a build problem; fix the build, not the runtime.
- The app is in production and you need live incident triage — use the observability stack, not local diagnostics.
- The failure is a logic bug inside a healthy, running process — use a debugger or targeted logging.

## Procedure
1. **Capture the exact startup error, untruncated.** The first non-warning line is almost always the root cause. Run the start command and tee full stderr: `npm run dev 2>&1 | tee /tmp/startup.log`.
2. **Resolve port conflicts.** If the error mentions `EADDRINUSE`: find the holder with `lsof -i :PORT` (macOS/Linux) or `netstat -ano | findstr :PORT` (Windows), confirm the PID belongs to a stale dev server (`ps -p PID -o pid,command`), then kill it and confirm the port frees.
3. **Verify the runtime version matches the project.** Compare `node --version` against `.nvmrc` / `engines.node`; `python --version` against `.python-version` / `pyproject.toml`; `go version` against the `go` directive in `go.mod`. Switch with nvm/pyenv before continuing on a mismatch.
4. **Check environment variable shape.** Read `.env.example` for required keys, then confirm each is set and non-empty without printing values. Validate plausibility (a `DATABASE_URL` that starts with `postgres://`).
5. **Verify dependency install is complete and correct.** Node: `node_modules` present and in sync with the lockfile (`npm ci`). Python: the venv is active (`which python` points inside it) and `pip check` is clean. Go: `go mod verify`.
6. **Check filesystem preconditions.** Some apps need `uploads/`, `tmp/`, `logs/`, or `certs/` to exist with correct permissions at startup. Confirm with `ls -la`.
7. **Trace external dependency connectivity directly.** Ping the DB (`psql "$DATABASE_URL" -c '\conninfo'`, `redis-cli -u "$REDIS_URL" ping`) and HTTP deps (`curl -s -o /dev/null -w '%{http_code}\n' "$API/health"`). Report the actual response, not "it worked."
8. **Inspect the process table for zombies or duplicates.** `ps aux | grep -E 'node|python|ruby|java'` — look for two instances on the same port, or a process that should be dead.
9. **Check system resources.** `df -h` (a full disk causes opaque write failures), `free -m` / `vm_stat` (memory), and `ulimit -n` (macOS defaults to 256 file descriptors, which connection-heavy Node apps exhaust).
10. **Decode the exit signal** if the process died immediately: 137 = OOM/SIGKILL, 139 = SIGSEGV (often a native module), 143 = SIGTERM, 130 = Ctrl-C. On Linux, check `dmesg` for OOM-killer evidence.
11. **Confirm the loaded config and CWD** when the app starts but behaves as if unconfigured: print `process.cwd()` / `os.getcwd()` and verify the `.env` actually read is the one you edited.

## Concrete checks
- Full untruncated stderr from startup captured.
- Port conflict checked with `lsof -i :PORT`; no stale process holds the port.
- Runtime version matches `.nvmrc` / `.python-version` / `go.mod`.
- All required env vars present and non-empty, compared against `.env.example`.
- Dependencies installed cleanly (`npm ci` / `pip check` / `go mod verify`).
- Required directories exist with correct permissions.
- Database connectivity confirmed with a direct client ping.
- External HTTP dependencies reachable from the dev machine.
- No zombie or duplicate instances of the process running.
- Disk space and file-descriptor limits within safe bounds.
- The process exit code/signal is decoded (137 OOM, 139 segfault, 143 SIGTERM) rather than guessed.
- The working directory and the actually-loaded config file are confirmed, not assumed.
- Native modules are rebuilt for the runtime that will execute them (container vs host parity).
- The bound port is confirmed with `lsof`, not taken from the startup log line.

## Commands
```bash
# 1. Capture the full startup error
npm run dev 2>&1 | tee /tmp/startup.log | head -50

# 2. Port conflict: find, identify, free
lsof -i :3000                            # macOS/Linux  (Windows: netstat -ano | findstr :3000)
ps -p "$(lsof -ti :3000)" -o pid,command # confirm it is a stale dev server
kill "$(lsof -ti :3000)" && lsof -i :3000 || echo "port 3000 free"

# 3. Runtime version vs project requirement
node --version; cat .nvmrc 2>/dev/null
python --version; cat .python-version 2>/dev/null
go version; grep '^go ' go.mod 2>/dev/null

# 4. Env shape WITHOUT printing values
for k in $(grep -oE '^[A-Z0-9_]+' .env.example 2>/dev/null); do
  [ -n "${!k:-}" ] && echo "$k set" || echo "$k MISSING"
done

# 5. Dependency integrity
npm ci --dry-run 2>&1 | tail -5         # Node lockfile in sync?
pip check                                # Python broken requirements
go mod verify                            # Go module checksums

# 7. External connectivity
psql "$DATABASE_URL" -c '\conninfo' 2>&1 | head -1
redis-cli -u "$REDIS_URL" ping 2>/dev/null
curl -s -o /dev/null -w 'http=%{http_code} t=%{time_total}s\n' "$API_BASE/health"

# 9. Resource limits
df -h . ; ulimit -n ; (free -m 2>/dev/null || vm_stat | head -5)
```
```bash
# Decode the exit signal of a process that died immediately
"$@"; echo "exit=$?"        # 137=OOM/SIGKILL, 139=SIGSEGV, 143=SIGTERM, 130=Ctrl-C
dmesg 2>/dev/null | rg -i "killed process|out of memory" | tail -5   # Linux OOM-killer evidence

# Attach to a crashing Node process to see the real stack
node --stack-trace-limit=50 --unhandled-rejections=strict dist/server.js 2>&1 | head -40

# Confirm which config file the app actually loaded (wrong-CWD trap)
node -e 'console.log(process.cwd())'                   # where it thinks it is
rg -n "dotenv|load_dotenv|godotenv" src/ | head        # how/where env is loaded

# Container parity: rebuild native modules for the runtime that will actually run them
npm rebuild bcrypt sharp 2>&1 | tail -5

# Watch a backgrounded service settle (replaces a blind sleep)
until curl -fsS http://localhost:3000/health >/dev/null 2>&1; do sleep 0.5; done; echo "ready"
```
```bash
# Trace a "cannot find module" / version-mismatch to the exact package
npm ls <pkg> 2>&1 | rg "<pkg>|deduped|invalid"   # resolved version + conflicts
node -e 'console.log(require.resolve("<pkg>"))'    # which copy is actually loaded
pip show <pkg> | rg "Version|Location"             # Python: installed version + path

# File-descriptor leak: count open FDs for the process over time
PID=$(lsof -ti :3000); ls /proc/$PID/fd 2>/dev/null | wc -l   # Linux
lsof -p "$PID" | wc -l                                         # macOS

# Verify the runtime inside a container matches the host expectation
docker run --rm -v "$PWD":/app -w /app node:20 node --version
docker run --rm -v "$PWD":/app -w /app node:20 npm ci && echo "installs clean in target image"
```

## Symptom to cause to command
| Symptom | Likely cause | First command |
|---------|--------------|---------------|
| `EADDRINUSE` | stale dev server on the port | `lsof -i :PORT` |
| exits with code 137 | OOM kill | `dmesg \| rg -i 'out of memory'` |
| exits with code 139 | native module segfault | `npm rebuild <native-pkg>` |
| "cannot find module X" | install out of sync with lockfile | `npm ci` |
| connects nowhere, no error | wrong working directory / `.env` not loaded | `node -e 'console.log(process.cwd())'` |
| `ECONNREFUSED` to DB | DB down or wrong `DATABASE_URL` | `psql "$DATABASE_URL" -c '\conninfo'` |
| routes 500 silently | unhandled async rejection | run with `--unhandled-rejections=strict` |
| works once then hangs | file-descriptor exhaustion | `ulimit -n` then raise it |

## Common issues & anti-patterns
- **Wrong working directory.** The app reads config relative to `__dirname` / `os.getcwd()`; launching from the wrong directory silently loads empty or wrong config. Confirm the launch directory.
- **`.env` not loaded.** dotenv reads from the current directory but the `.env` sits in a parent, or `dotenv.config()` runs after the code that reads `process.env`. Load config before first use.
- **Stale lockfile after a branch switch.** `package.json` changed but install did not re-run, so `node_modules` holds the wrong version. Re-run `npm ci`.
- **Platform-specific native binary.** `bcrypt`/`sharp`/`canvas` compiled on macOS fail inside a Linux container. Rebuild in the target environment with `npm rebuild`.
- **Silent uncaught async error.** On older Node an unhandled rejection does not crash the process; the server "starts" but every route 500s. Add an `unhandledRejection` handler and inspect logs.
- **Killing a PID you cannot identify.** Never `kill -9` a process you have not positively tied to this project — you may take down something unrelated.
- **Truncating the error.** Piping startup to `head -1` and missing the real cause three lines down. Capture the full stderr, then read it.
- **Fixing the symptom, not the cause.** Bumping `ulimit -n` when the real bug is a connection leak that never closes sockets — the limit just delays the crash.
- **`rm -rf node_modules` as a reflex.** Sometimes right, but it hides the actual mismatch and wastes minutes; check `npm ci --dry-run` first to see what is really out of sync.
- **Assuming the dev port.** The app prints "listening on 3000" but a config override moved it to 8080; you diagnose the wrong port. Confirm the bound port with `lsof`.

## Required output
For each diagnostic step report: the **command run** and its exact output (secrets redacted), the **finding** (e.g. "port 3000 held by PID 8421 — stale nodemon from a prior session"), the **action taken** (`kill 8421`), and the **verification** (app now responds on localhost:3000). End with a one-sentence **root-cause summary**.

## Safety
- Never print actual secret values from env vars — describe shape only (e.g. "DATABASE_URL set, starts with postgres://").
- Do not run `npm install` / `pip install` with elevated privileges or outside the project's virtual environment.
- Do not kill a process whose PID you cannot positively identify as belonging to this project.
- Make no source or config edits as part of diagnosis; report the cause and the safe fix.

## Completion criteria
Done means the startup failure is traced to a named root cause with command-level evidence, the resolving action is applied and verified (the app starts or the dependency responds), and any remaining unresolved factor is flagged with the next safe step — all without exposing secrets or killing unidentified processes.

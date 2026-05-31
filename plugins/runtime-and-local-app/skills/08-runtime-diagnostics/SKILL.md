---
name: runtime-diagnostics
description: Use when you need to diagnose startup, process, port, dependency, environment, and runtime health failures.
---

# Runtime Diagnostics

## Purpose
This skill provides a systematic, non-destructive procedure for diagnosing why a local or dev-environment application fails to start, crashes immediately, or behaves incorrectly at runtime. It covers port conflicts, missing or wrong environment variables, dependency version mismatches, incorrect working directory, and process-level resource issues — the most common causes of "it works on my machine" failures.

## When to use
- Running `npm run dev` / `python manage.py runserver` / `go run .` exits with a non-zero code and the error is not immediately obvious.
- A service starts but immediately crashes (OOM, unhandled exception, signal).
- "Address already in use" or "EADDRINUSE" errors on a specific port.
- The app runs but cannot reach a database, cache, or external dependency.
- A container or process starts on one machine but not another due to environment differences.

## When not to use
- The error is a compile/type error — that is a build problem, not a runtime problem.
- The application is in production and you need live incident triage — use your observability stack, not local diagnostics.
- The failure is a logic bug inside a running, healthy process — use a debugger or add logging, not runtime diagnostics.

## Procedure

1. **Capture the exact startup error.** Run the start command and capture full stderr output — do not truncate. The first non-warning line of the error is almost always the root cause. Example: `npm run dev 2>&1 | head -50`.

2. **Check for port conflicts.** If the error mentions EADDRINUSE or "address already in use": `lsof -i :PORT` (macOS/Linux) or `netstat -ano | findstr :PORT` (Windows). Identify the PID holding the port: `ps aux | grep PID`. Kill it if it is a stale dev server: `kill -9 PID`. Confirm the port is free: `lsof -i :PORT` returns nothing.

3. **Verify runtime version matches project requirements.** Compare: `node --version` vs `.nvmrc` or `engines.node` in `package.json`. `python --version` vs `.python-version` or `Pipfile` `[requires]`. `go version` vs `go.mod`'s `go` directive. `ruby --version` vs `.ruby-version`. If there is a mismatch, switch versions via nvm/pyenv/rbenv before continuing.

4. **Check environment variable shape.** Read `.env.example` or `.env.sample` to see required keys. Run `env | grep -E "DATABASE|REDIS|PORT|SECRET|API_KEY"` to see what is actually set. For each required variable: confirm it exists, is not empty, and has a plausible value (e.g., a DATABASE_URL that starts with `postgres://` or `mongodb://`). Never print actual secret values.

5. **Verify dependency installation is complete and correct.** For Node: confirm `node_modules` exists and is not empty; check `package-lock.json` or `yarn.lock` is not ahead of `node_modules` (run `npm ci` or `yarn install --frozen-lockfile`). For Python: confirm the virtualenv is activated (`which python` points inside the venv); run `pip check` to surface broken requirements. For Go: `go mod verify`.

6. **Check file system preconditions.** Some apps require specific directories or files to exist at startup: `uploads/`, `tmp/`, `logs/`, `certs/`. Run `ls -la` on expected directories. Check file permissions if the app opens a socket, writes a PID file, or reads a certificate.

7. **Trace external dependency connectivity.** Database: `psql $DATABASE_URL -c '\conninfo'` or `mongosh $MONGODB_URI --eval 'db.runCommand({ping:1})'`. Redis: `redis-cli -u $REDIS_URL ping`. HTTP dependency: `curl -s -o /dev/null -w "%{http_code}" $EXTERNAL_API_BASE_URL/health`. Report the actual response, not just "it worked."

8. **Inspect the process table for zombie or conflicting instances.** `ps aux | grep "node\|python\|ruby\|java"` — look for multiple instances of the same app on the same port, or a process that should be dead but is still running.

9. **Check available system resources.** `df -h` to check disk space (full disk causes opaque write failures). `free -m` or `vm_stat` on macOS to check available memory. `ulimit -n` to check open file descriptor limits — Node apps with many connections can exhaust the default limit of 256 on macOS.

## Checklist
- [ ] Full stderr from startup captured (not truncated)
- [ ] Port conflict checked with `lsof -i :PORT` — no stale process holding the port
- [ ] Runtime version matches `.nvmrc` / `.python-version` / `go.mod`
- [ ] All required env vars present and non-empty (compared against `.env.example`)
- [ ] Dependencies installed cleanly (npm ci / pip install / go mod verify)
- [ ] Required filesystem directories and permissions verified
- [ ] Database connectivity confirmed with a direct client ping
- [ ] External HTTP dependencies reachable from the dev machine
- [ ] No zombie instances of the same process running
- [ ] Disk space and file descriptor limits within safe bounds

## Common issues & anti-patterns

- **Wrong working directory**: the app reads config relative to `__dirname` or `os.getcwd()` — starting it from the wrong directory silently loads wrong or empty config.
- **`.env` file not loaded**: the app uses dotenv but the `.env` file is in a parent directory, or the dotenv call happens after the code that reads `process.env`.
- **Stale lock file after branch switch**: switching git branches changes `package.json` but does not re-run install — `node_modules` contains the wrong version of a package.
- **Platform-specific binary in `node_modules`**: native addons (bcrypt, sharp, canvas) compiled on macOS M1 fail on Linux containers — rebuild with `npm rebuild` inside the target environment.
- **Silent failure due to uncaught async error**: in Node <15, an unhandled Promise rejection does not crash the process; the server appears to start but routes return 500 silently.

## Required output
For each diagnostic step, report:
- **Command run** and its exact output (redacted of secrets)
- **Finding**: what was discovered (e.g., "port 3000 held by PID 8421 — stale nodemon from previous session")
- **Action taken**: what was done to resolve it (e.g., `kill -9 8421`)
- **Verification**: confirmation the issue is resolved (e.g., "app now starts and responds on localhost:3000")
- **Root cause summary**: one-sentence description of what caused the failure

## Safety
- Never print actual secret values from env vars — describe shape only (e.g., "DATABASE_URL is set, starts with postgres://").
- Do not run `npm install` or `pip install` with elevated privileges or outside the project's virtual environment.
- Do not kill processes whose PID you cannot positively identify as belonging to this project.

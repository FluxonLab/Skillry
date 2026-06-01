---
name: log-and-diagnostics-bundle
description: Use when you need to collect concise logs, environment facts, versions, and failure evidence without exposing secrets.
---

# Log and Diagnostics Bundle

## Purpose
This skill assembles a compact, shareable diagnostics snapshot that contains everything needed to
reproduce and understand a failure: relevant log lines, runtime versions, env var shape (keys but
not values), reproduction steps, and error stack traces — while systematically redacting secrets,
tokens, and credentials. The output can be safely pasted into a GitHub issue, shared with a
teammate, or attached to a support ticket. A bundle produced by this skill gives the reader enough
context to reproduce the failure without access to the originating environment, and without
receiving any secrets in the process.

## When to use
- Preparing a bug report for an open-source library or vendor support where you need to share environment details without leaking secrets.
- A teammate cannot reproduce a failure and needs your exact runtime context.
- An intermittent failure needs a structured snapshot captured at the moment of occurrence for later analysis.
- A CI failure needs to be triaged and the raw log is thousands of lines — you need to extract the signal.
- Post-incident: collecting the evidence needed for a root cause analysis document.
- A support ticket requires proof of the environment and failure mode without attaching raw config or credential files.

## When not to use
- You are responding to a live production incident — capture logs from your observability platform (Datadog, Grafana, CloudWatch, Loki), not from local shell commands.
- The problem is already fully diagnosed — just fix it; a bundle is only useful when the cause is unclear.
- You need real-time streaming log tailing during a test — use `tail -f` or your log aggregator directly.

## Procedure

1. **Capture runtime version facts.** Run and record verbatim:
   ```bash
   node --version; npm --version; npx --version   # Node ecosystem
   python3 --version; pip3 --version              # Python
   go version                                     # Go
   java -version 2>&1; mvn --version 2>/dev/null  # Java/Maven
   ruby --version; bundle --version 2>/dev/null   # Ruby
   docker --version; docker compose version 2>/dev/null  # Containers
   uname -a                                       # OS / kernel
   ```
   Record the output verbatim — version mismatches are the most common cause of "works on my
   machine." Include the OS kernel string; macOS and Linux behave differently on file-system
   case sensitivity, symlink handling, and native module compatibility.

2. **Capture environment variable shape — keys only, no values.** Run:
   ```bash
   env | grep -E "NODE|PYTHON|PATH|PORT|DATABASE|REDIS|MONGO|API|SECRET|TOKEN|KEY|URL|HOST|ENV|APP|SERVICE|OPENAI|STRIPE" \
       | sed 's/=.*/=<REDACTED>/'
   ```
   This shows which keys are set and which are absent without exposing any values. For `.env`
   files: `grep -E "^[A-Z_]+" .env | sed 's/=.*/=<REDACTED>/'`. Cross-reference with `.env.example`
   or equivalent to identify required keys that are missing — a missing key is often the root cause.

3. **Extract the relevant log window with context.** From a log file:
   ```bash
   grep -n "ERROR\|FATAL\|panic\|Exception\|Traceback\|WARN.*fail" app.log | tail -30
   ```
   Always include 20 lines before and after each error line for context — the line before the
   error often shows what was being processed when it failed:
   ```bash
   # Extract ±20 lines around the first ERROR
   grep -n "ERROR" app.log | head -1 | cut -d: -f1 | \
     xargs -I{} awk "NR>={}-20 && NR<={}" {}+20 app.log
   ```
   From a running process: capture stderr for the duration of a reproduction:
   ```bash
   npm run dev 2>&1 | tee /tmp/diag-$(date +%s).log
   ```
   Never truncate the stack trace — include the full trace even if it is long. The deepest frame
   is usually the root cause; cutting it off leaves the reader guessing.

4. **Capture dependency installation state.** This reveals lock file drift and unexpected package
   versions — a common source of environment-specific failures:
   ```bash
   # Node
   cat package.json | python3 -m json.tool | grep -A 40 '"dependencies"'
   npm ls --depth=0 2>&1 | head -40
   # Python
   pip3 list --format=columns 2>/dev/null | head -40
   # Go
   cat go.mod
   # Ruby
   cat Gemfile.lock | head -30
   ```

5. **Record the exact reproduction steps.** Write numbered steps: the command run, any
   preconditions (specific env vars set, specific file present, specific seed data loaded),
   and the expected vs. actual behavior. Precision matters:
   - Bad: "I started the app and tried to log in."
   - Good: "I ran `npm run dev` from the repo root with `NODE_ENV=development` and `PORT=3001` set.
     I then sent `POST /api/auth/login` with `{"email":"user@example.com","password":"redacted"}`
     after clearing browser cookies. Expected: 200 with session cookie. Actual: 401 with body
     `{"error":"invalid_credentials"}` despite the account existing in the seed data."

6. **Capture process and resource context at failure time.** If the app crashes or misbehaves:
   ```bash
   ps aux | grep -E "node|python|java|ruby|go" | grep -v grep  # running processes
   df -h /                                      # disk space (a full disk causes opaque failures)
   free -m 2>/dev/null || vm_stat | head -10    # memory (Linux / macOS)
   ulimit -a | grep -E "open files|max user"    # file descriptor and process limits
   ```
   Exit signal decoding: 137 = OOM/SIGKILL, 139 = SIGSEGV, 143 = SIGTERM. On Linux:
   `dmesg | grep -i "killed process\|out of memory" | tail -5` confirms OOM kills.

7. **Collect relevant config file snippets — redacted.** If the failure relates to a config file
   (`nginx.conf`, `docker-compose.yml`, `k8s/deployment.yaml`, `webpack.config.js`), include the
   relevant section with secret values replaced by `<REDACTED>`. Never include TLS private keys,
   API tokens, database passwords, or JWT secrets — not even Base64-encoded forms.

8. **Assemble the bundle in a standard structure.** Use this template:
   ```
   ## Environment
   OS: <uname output>
   Runtime: <language version>
   Package manager: <name + version>

   ## Reproduction steps
   1. <exact command with flags>
   2. ...

   ## Actual behavior
   <timestamped log excerpt — full stack trace, not truncated>

   ## Expected behavior
   <what should have happened>

   ## Dependency versions
   <npm ls / pip list / go mod output — top-level only>

   ## Env var keys present
   <key names only, values all <REDACTED>>

   ## Config (redacted)
   <relevant snippet from config file>

   ## Resource state at failure
   <disk, memory, process list, ulimit>
   ```

9. **Perform a final secret scan before sharing.** Grep the assembled bundle:
   ```bash
   grep -iE "(password|secret|token|api[-_]?key|private[-_]?key|bearer|authorization)\s*[:=]\s*[^\s<{]" bundle.txt
   ```
   Any match must be replaced with `<REDACTED>` before sharing. Also check for accidentally
   included connection strings: `grep -E "postgres://|mysql://|mongodb\+srv://" bundle.txt`.

## Concrete checks
- OS, runtime version, and package manager version all recorded verbatim.
- Every env var value is `<REDACTED>` — only key names are present.
- Log excerpt includes timestamps on every line and at least 20 lines of context around each error.
- The full stack trace is included — not truncated at an arbitrary line count.
- Exact reproduction command is documented including working directory, env context, and flags.
- Dependency lock state captured (`npm ls --depth=0`, `pip3 list`, `go.mod`, `Gemfile.lock`).
- Cross-referenced against `.env.example` or equivalent — missing required keys are called out.
- Process resource state at failure time: disk space, memory, open file descriptor limit.
- Config snippets have no secret values — all passwords, tokens, and connection strings are redacted.
- Bundle assembled using the standard structure (Environment / Reproduction / Actual / Expected / Deps / Env keys / Config / Resource state).
- Final secret scan run against the assembled bundle — result stated explicitly ("no secrets detected" or list of redacted items).
- `.env` files, private keys, and bearer tokens are NOT present anywhere in the bundle.

## Commands
```bash
# --- Step 1: runtime versions ---
node --version; npm --version
python3 --version; pip3 --version
go version
docker --version; docker compose version 2>/dev/null
uname -a

# --- Step 2: env var shape, keys only ---
env | grep -E "NODE|PYTHON|PATH|PORT|DATABASE|REDIS|API|SECRET|TOKEN|KEY|URL|HOST|ENV|APP" \
    | sed 's/=.*/=<REDACTED>' | sort

# Cross-reference with .env.example
grep -oE '^[A-Z0-9_]+' .env.example 2>/dev/null | while read k; do
  printenv "$k" >/dev/null 2>&1 && echo "$k=<SET>" || echo "$k=MISSING"
done

# --- Step 3: log extraction ---
# Errors with context (20 lines before/after first ERROR)
grep -n "ERROR\|FATAL\|panic\|Exception\|Traceback" app.log | head -5

# Capture live stderr during a reproduction run
npm run dev 2>&1 | tee /tmp/diag-$(date +%s).log

# Structured JSON log: extract error-level entries (jq required)
cat app.log | grep '"level":"error"' | jq '{time,msg,err}' 2>/dev/null | head -20

# --- Step 4: dependency state ---
npm ls --depth=0 2>&1 | head -40       # Node
pip3 list --format=columns | head -40  # Python
cat go.mod                             # Go
cat Gemfile.lock | head -30            # Ruby

# --- Step 6: resource state ---
df -h /
ulimit -a | grep -E "open files|processes"
ps aux | grep -E "node|python|java|ruby" | grep -v grep
free -m 2>/dev/null || vm_stat | head -8
# Exit code of the crashed process (add to reproduction)
<failing-command>; echo "exit=$?"

# --- Step 9: final secret scan ---
grep -iE "(password|secret|token|api[-_]?key|private[-_]?key|bearer)\s*[:=]\s*[^\s<{]" bundle.txt && echo "REDACT ABOVE" || echo "no secrets detected"
grep -E "postgres://|mysql://|mongodb\+srv://" bundle.txt && echo "REDACT connection strings" || true
```

## Common issues & anti-patterns

- **Sharing a raw `.env` file.** The most dangerous mistake — includes all secrets. Always extract
  only the key names. A bundle with a `.env` attachment should be rejected before reading.
- **Truncated stack trace.** Cutting off the stack trace before the root cause line (usually the
  deepest frame). Always include the full trace, even if it is 50 lines long.
- **Log lines without timestamps.** A log excerpt without timestamps makes it impossible to
  correlate with external events (a deploy, a traffic spike, a certificate rotation). Always
  include the timestamp column, and note the timezone.
- **Missing the line before the error.** The error line says "Cannot read property 'id' of
  undefined" but the caller context (what was being processed when it failed) is 10 lines earlier.
  Always include at least 20 lines of pre-context.
- **Vague reproduction steps.** "I tried to log in" is not reproducible. "I sent `POST /api/auth/login`
  with body `{…}` after clearing cookies" is.
- **Version assertion without evidence.** "I'm running Node 20" with no output from `node --version`
  — the shell alias may be wrong, or `nvm` may not have loaded. Record the command output, not
  your belief about the version.
- **Missing required key in the env section.** Listing only the keys that are set and omitting the
  required-but-missing ones. The missing key is often the entire cause of the failure.
- **Connection string in a curl example.** Showing `curl -u postgres://user:pass@host/db` with the
  password visible in the bundle. Redact the password segment.

## Required output
A structured diagnostics bundle containing:
- **Runtime versions:** all relevant language, runtime, and tool versions (verbatim command output).
- **Env var shape:** list of key names that are set vs. missing — no values.
- **Log excerpt:** timestamped error lines with ±20 lines of context, full stack trace included.
- **Reproduction steps:** exact numbered commands, working directory, env context, and preconditions.
- **Dependency state:** top-level package versions from the lock state, not from memory.
- **Resource state:** disk, memory, open file descriptor limit, and process list at failure time.
- **Secret scan result:** explicit statement — "no secrets detected" or list of items that were redacted before inclusion.

## Safety
- Never include actual values of variables named `SECRET`, `TOKEN`, `PASSWORD`, `KEY`, `PRIVATE`, or `CREDENTIAL` — replace with `<REDACTED>`.
- Do not attach entire log files if they contain user PII (email addresses, names, account IDs) — excerpt only the lines relevant to the failure.
- Do not share database connection strings — record only the host and database name, never the password or query parameters that contain auth info.
- Run the final secret scan as a mandatory last step, not an optional check — a bundle with a leaked secret can cause a security incident even if shared only internally.
- When capturing process resource state, do not include the command line of other users' processes if `ps aux` reveals them — excerpt only your project's processes.

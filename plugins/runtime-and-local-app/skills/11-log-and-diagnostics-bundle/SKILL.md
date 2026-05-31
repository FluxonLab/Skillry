---
name: log-and-diagnostics-bundle
description: Use when you need to collect concise logs, environment facts, versions, and failure evidence without exposing secrets.
---

# Log and Diagnostics Bundle

## Purpose
This skill assembles a compact, shareable diagnostics snapshot that contains everything needed to reproduce and understand a failure: relevant log lines, runtime versions, env var shape (keys but not values), reproduction steps, and error stack traces — while systematically redacting secrets, tokens, and credentials. The output can be safely pasted into a GitHub issue, shared with a teammate, or attached to a support ticket.

## When to use
- Preparing a bug report for an open-source library or vendor support where you need to share environment details without leaking secrets.
- A teammate cannot reproduce a failure and needs your exact runtime context.
- An intermittent failure needs a structured snapshot captured at the moment of occurrence for later analysis.
- A CI failure needs to be triaged and the raw log is 5000 lines — you need to extract the signal.
- Post-incident: collecting the evidence needed for a root cause analysis document.

## When not to use
- You are responding to a live production incident — capture logs from your observability platform (Datadog, Grafana, CloudWatch), not from local shell commands.
- The problem is already fully diagnosed — just fix it; a bundle is only useful when cause is unclear.
- You need real-time streaming log tailing during a test — use `tail -f` or your log aggregator directly.

## Procedure

1. **Capture runtime version facts.** Run and record:
 ```bash
 node --version; npm --version; npx --version # Node ecosystem
 python --version; pip --version # Python
 go version # Go
 java -version; mvn --version # Java/Maven
 docker --version; docker compose version # Containers
 uname -a # OS / kernel
 ```
 Record the output verbatim — version mismatches are the most common cause of "works on my machine."

2. **Capture environment variable shape (keys only, no values).** Run:
 ```bash
 env | grep -E "NODE|PYTHON|PATH|PORT|DATABASE|REDIS|MONGO|API|SECRET|TOKEN|KEY|URL|HOST|ENV|APP|SERVICE" | sed 's/=.*/=<REDACTED>/'
 ```
 This shows which keys are set and which are missing without exposing any values. For `.env` files: `grep -E "^[A-Z_]+" .env | sed 's/=.*/=<REDACTED>/'`.

3. **Extract the relevant log window.** From a log file: `grep -n "ERROR\|FATAL\|panic\|Exception\|Traceback" app.log | tail -50`. From a running process: capture stderr for 30 seconds of reproduction: `command 2>&1 | tee /tmp/diag-$(date +%s).log`. Include 20 lines before and after each error line for context: `grep -n "ERROR" app.log | head -5 | awk -F: '{print $1}' | xargs -I{} sed -n "$(({})-20),$(({}+20))p" app.log`.

4. **Capture dependency installation state.** Node: `cat package.json | jq '{name,version,dependencies,devDependencies}'` and `npm ls --depth=0 2>&1 | head -30`. Python: `pip list --format=columns | head -30`. Go: `cat go.mod`. This reveals lock file drift and unexpected package versions.

5. **Record the exact reproduction steps.** Write out in numbered order: the command run, any preconditions (specific env vars set, specific file present), and the expected vs. actual behavior. Be precise: "I ran `npm run dev` from the repo root with `NODE_ENV=development`" is more useful than "I started the app."

6. **Capture process and resource context at failure time.** If the app crashes:
 ```bash
 ps aux | grep "node\|python\|java" # running processes
 df -h / # disk space
 free -m # memory (Linux)
 ulimit -a # resource limits
 ```
 On macOS: `vm_stat | head -10` instead of `free`.

7. **Collect relevant config file snippets (redacted).** If the failure relates to a config file (e.g., `nginx.conf`, `docker-compose.yml`, `k8s/deployment.yaml`), include the relevant section with any secret values replaced by `<REDACTED>`. Never include TLS private keys, API tokens, or database passwords.

8. **Assemble the bundle into a structured document.** Structure:
 ```
 ## Environment
 ## Reproduction steps
 ## Actual behavior (log excerpt)
 ## Expected behavior
 ## Dependency versions
 ## Env var keys present
 ## Config (redacted)
 ```

9. **Perform a final secret scan before sharing.** Grep the assembled bundle for common secret patterns:
 ```bash
 grep -iE "(password|secret|token|apikey|private_key|bearer)\s*[:=]\s*[^\s<]" bundle.txt
 ```
 Any match must be replaced with `<REDACTED>` before sharing.

## Checklist
- [ ] OS, runtime, and package manager versions recorded
- [ ] Env var keys listed — values are all `<REDACTED>`
- [ ] Log excerpt includes 20 lines of context around each error
- [ ] Exact reproduction command documented (with flags, working directory, env context)
- [ ] Dependency lock state captured (`npm ls`, `pip list`, `go.mod`)
- [ ] Process and resource state at failure time recorded
- [ ] Config snippets redacted of all secret values
- [ ] Bundle assembled in the standard structure above
- [ ] Final secret scan run against the assembled bundle
- [ ] `.env` files, private keys, and bearer tokens are NOT included in the bundle

## Common issues & anti-patterns

- **Sharing raw `.env` file**: the most dangerous mistake — includes all secrets. Always extract only the key names.
- **Truncated stack trace**: cutting off the stack trace before the root cause line (usually the deepest frame). Always include the full trace, even if it is long.
- **Log lines without timestamps**: a log excerpt without timestamps makes it impossible to correlate with external events. Always include the timestamp column.
- **Missing the line before the error**: the error line says "Cannot read property 'id' of undefined" but the caller context (what was being processed) is 10 lines earlier. Always include pre-context.
- **Vague "reproduction" steps**: "I tried to log in" is not reproducible. "I POST to /api/auth/login with `{email: 'test@example.com', password: '...'}` after clearing cookies" is.

## Required output
A structured diagnostics bundle containing:
- **Runtime versions**: all relevant language and tool versions
- **Env var shape**: list of key names that are/are not set (no values)
- **Log excerpt**: timestamped error lines with ±20 lines of context
- **Reproduction steps**: exact numbered commands and preconditions
- **Dependency state**: top-level package versions
- **Resource state**: disk, memory, process list at failure time
- **Secret scan result**: "no secrets detected" or list of items that were redacted

## Safety
- Never include actual values of variables named `SECRET`, `TOKEN`, `PASSWORD`, `KEY`, `PRIVATE`, or `CREDENTIAL` — replace with `<REDACTED>`.
- Do not attach entire log files if they contain user PII (email addresses, names, IDs) — excerpt only the relevant lines.
- Do not share database connection strings — record only the host and database name, never the password.

---
name: electron-app-security-review
description: Use when you need to audit the internal security of an Electron application — context isolation, IPC input validation, contextBridge API surface, preload script hygiene, renderer CSP, navigation restrictions, and auto-update signature verification. Distinct from desktop launcher/packaging review.
---

# Electron App Security Review

## Purpose

Audit the runtime security of an Electron application from the inside: verify that `contextIsolation`, sandboxing, and `webSecurity` are configured correctly, that IPC channels validate all inputs and expose a minimal `contextBridge` API, that preload scripts do not leak Node.js APIs to the renderer, that the renderer Content Security Policy blocks script injection, that navigation is restricted to known origins, and that auto-update mechanisms verify signatures. This skill focuses on in-process security — not build/packaging (see skill 28 for that).

## When to use

- A PR modifies `BrowserWindow` options, `contextBridge` exposure, `ipcMain` handlers, or preload scripts.
- A security audit is requested for an Electron app before a public release.
- A bug report hints at renderer-to-main privilege escalation or arbitrary code execution from a compromised renderer.
- The app loads remote web content (URLs, iframes, `webview`) that could be attacker-controlled.
- You are onboarding into an Electron project and need to establish its security baseline.

## When not to use

- The task is purely UI/UX or involves only renderer-side React/TypeScript — no Electron APIs involved.
- The issue is a packaging or code-signing problem — use the desktop launcher review skill instead.
- The app has no IPC and renders only local static files with no user input.

## Procedure

### 1. Audit BrowserWindow security options

```bash
# Find all BrowserWindow instantiations
grep -rn "new BrowserWindow\|BrowserWindow({" src/ electron/ main/ --include="*.ts" --include="*.js"

# Check for insecure option combinations
grep -rn "contextIsolation\|nodeIntegration\|sandbox\|webSecurity\|allowRunningInsecureContent" \
 src/ electron/ main/ --include="*.ts" --include="*.js"
```

Critical combinations to flag:
- `nodeIntegration: true` — grants full Node.js to the renderer; **Critical** unless the app is a trusted local tool with no remote content.
- `contextIsolation: false` — removes the JS context boundary; **Critical**.
- `sandbox: false` — disables OS-level sandboxing; **High**.
- `webSecurity: false` — disables same-origin policy; **High** unless localhost-only dev override.
- `allowRunningInsecureContent: true` — allows HTTP in HTTPS webview; **High**.

Expected safe configuration:
```js
webPreferences: {
 contextIsolation: true, // REQUIRED
 nodeIntegration: false, // REQUIRED
 sandbox: true, // REQUIRED in Electron ≥ 20
 webSecurity: true, // default; never set false in production
 preload: path.join(__dirname, 'preload.js'),
}
```

### 2. Review contextBridge and preload script exposure

```bash
# Find all contextBridge.exposeInMainWorld calls
grep -rn "contextBridge\.exposeInMainWorld\|exposeInMainWorld" \
 src/ electron/ preload/ --include="*.ts" --include="*.js"

# Find any direct ipcRenderer exposure (dangerous anti-pattern)
grep -rn "ipcRenderer" preload/ src/ --include="*.ts" --include="*.js" | head -30

# Check if the entire ipcRenderer object is exposed
grep -rn "ipcRenderer\s*[,}]" preload/ src/ --include="*.ts" --include="*.js"
```

Anti-pattern — never expose raw `ipcRenderer`:
```js
// WRONG: full ipcRenderer in renderer context
contextBridge.exposeInMainWorld('electron', { ipcRenderer })
```

Correct pattern — expose only named channels:
```js
contextBridge.exposeInMainWorld('api', {
 getUser: () => ipcRenderer.invoke('get-user'),
 saveFile: (data: string) => ipcRenderer.invoke('save-file', data),
 // No: send, on, removeAllListeners exposed generically
})
```

```bash
# Check for require() or __dirname in renderer files (should not exist with contextIsolation)
grep -rn "require(\|__dirname\|__filename" src/renderer/ --include="*.ts" --include="*.js" | head -20
```

### 3. Audit ipcMain handler input validation

```bash
# List all ipcMain.handle and ipcMain.on registrations
grep -rn "ipcMain\.handle\|ipcMain\.on\|ipcMain\.once" \
 src/ electron/ main/ --include="*.ts" --include="*.js"

# Check for handlers that use event.reply or invoke results without validation
grep -rn -A 10 "ipcMain\.handle(" src/ electron/ main/ --include="*.ts" --include="*.js" \
 | grep -B 5 "as any\|unknown\|@ts-ignore" | head -30
```

For each `ipcMain.handle`, verify:
- Argument types are validated (zod, manual type guards, or at minimum `typeof` checks).
- `event.senderFrame.url` is checked against an allowlist before processing sensitive operations.
- File paths passed from the renderer are validated against a safe base directory (path traversal).

```bash
# Path traversal risk: file operations with renderer-supplied paths
grep -rn "fs\.\|path\.join\|readFile\|writeFile\|unlink" \
 src/ electron/ main/ --include="*.ts" --include="*.js" | head -30
```

### 4. Check renderer Content Security Policy

```bash
# CSP in main process (session.defaultSession.webRequest)
grep -rn "Content-Security-Policy\|contentSecurityPolicy\|webRequest\.onHeaders" \
 src/ electron/ main/ --include="*.ts" --include="*.js"

# CSP meta tag in HTML entry points
grep -rn "Content-Security-Policy" src/ public/ --include="*.html"

# Check for unsafe-inline or unsafe-eval in CSP
grep -rn "unsafe-inline\|unsafe-eval" src/ electron/ public/ --include="*.ts" --include="*.html"
```

Minimum acceptable CSP for an Electron app loading only local files:
```
default-src 'self';
script-src 'self';
style-src 'self' 'unsafe-inline';
img-src 'self' data:;
connect-src 'self';
```

`unsafe-eval` is never acceptable. `unsafe-inline` in `script-src` is a Critical finding.

### 5. Restrict navigation and new window opening

```bash
# Check will-navigate handler
grep -rn "will-navigate\|webContents\.on.*navigate\|beforeunload" \
 src/ electron/ main/ --include="*.ts" --include="*.js"

# Check setWindowOpenHandler / new-window
grep -rn "setWindowOpenHandler\|new-window\|window\.open" \
 src/ electron/ main/ --include="*.ts" --include="*.js"

# Check webview tag usage (high risk; should use BrowserView or avoid entirely)
grep -rn "<webview\|webview:" src/ --include="*.tsx" --include="*.html"
```

Correct navigation restriction pattern:
```js
mainWindow.webContents.on('will-navigate', (event, url) => {
 if (!url.startsWith('file://') && !url.startsWith('https://your-app.com')) {
 event.preventDefault()
 }
})
mainWindow.webContents.setWindowOpenHandler(({ url }) => {
 shell.openExternal(url) // open in browser, not new Electron window
 return { action: 'deny' }
})
```

### 6. Verify auto-update signature checking

```bash
# Find electron-updater or autoUpdater usage
grep -rn "electron-updater\|autoUpdater\|checkForUpdates" \
 src/ electron/ main/ --include="*.ts" --include="*.js" | head -20

# Confirm publisherName or signature verification is configured
grep -rn "publisherName\|verifyUpdateCodeSignature\|allowDowngrade\|allowPrerelease" \
 electron-builder.yml electron-builder.json package.json 2>/dev/null
```

Checks:
- `electron-updater` must verify the update package signature before applying it.
- `publisherName` must match the code-signing certificate used in releases.
- `autoUpdater.allowDowngrade = false` — prevent rollback attacks.
- Update channel URL must use HTTPS.

### 7. Check for dangerous APIs exposed to renderer

```bash
# shell.openExternal with user-supplied URL (open redirect / RCE risk)
grep -rn "shell\.openExternal" src/ electron/ --include="*.ts" --include="*.js"

# child_process or exec accessible from IPC handlers
grep -rn "child_process\|exec(\|spawn(\|execFile(" \
 src/ electron/ main/ --include="*.ts" --include="*.js" | head -20

# eval or Function constructor in main process
grep -rn "\beval(\|new Function(" src/ electron/ main/ --include="*.ts" --include="*.js"
```

## Concrete checks

- [ ] `contextIsolation: true` in every `BrowserWindow` webPreferences.
- [ ] `nodeIntegration: false` in every `BrowserWindow` webPreferences.
- [ ] `sandbox: true` set (Electron ≥ 20 default, but verify no override).
- [ ] `webSecurity: false` is absent from production code paths.
- [ ] No raw `ipcRenderer` object exposed via `contextBridge`.
- [ ] Every `ipcMain.handle` validates argument types before processing.
- [ ] `event.senderFrame.url` is checked for sensitive IPC channels.
- [ ] File paths from renderer are resolved and confirmed within a safe base directory.
- [ ] CSP is set via `webRequest.onHeadersReceived`; no `unsafe-eval` in `script-src`.
- [ ] `will-navigate` event blocks navigation to unknown origins.
- [ ] `setWindowOpenHandler` returns `{ action: 'deny' }` and opens URLs in external browser.
- [ ] `<webview>` tags are absent or have `disablewebsecurity` unset.
- [ ] `autoUpdater` / `electron-updater` verifies update signatures (`publisherName` configured).
- [ ] `shell.openExternal` only receives validated, allowlisted URLs — never raw user input.
- [ ] No `child_process.exec` or `eval` reachable from IPC input.

## Commands

```bash
# One-shot security baseline check
echo "=== BrowserWindow insecure options ==="
grep -rn "nodeIntegration: true\|contextIsolation: false\|sandbox: false\|webSecurity: false" \
 src/ electron/ main/ --include="*.ts" --include="*.js"

echo "=== Raw ipcRenderer exposure ==="
grep -rn "exposeInMainWorld.*ipcRenderer\|ipcRenderer\s*[,}]" \
 preload/ src/ --include="*.ts" --include="*.js"

echo "=== CSP unsafe directives ==="
grep -rn "unsafe-eval\|unsafe-inline.*script" src/ public/ electron/ --include="*.ts" --include="*.html"

echo "=== shell.openExternal calls ==="
grep -rn "shell\.openExternal" src/ electron/ --include="*.ts" --include="*.js"

echo "=== child_process in main ==="
grep -rn "child_process\|exec(\|spawn(" src/ electron/ main/ --include="*.ts" --include="*.js"

echo "=== Auto-update config ==="
grep -rn "publisherName\|verifyUpdateCodeSignature" electron-builder.* package.json 2>/dev/null
```

## Required output

Produce a structured report with:
1. **BrowserWindow configuration** — table of each window's key security options with pass/fail.
2. **contextBridge exposure audit** — list every exposed API; flag any that expose raw `ipcRenderer` or Node APIs.
3. **IPC handler audit** — for each `ipcMain.handle`/`on`, validation status (present / absent / partial) and sender-verification status.
4. **CSP status** — current policy text, any `unsafe-*` violations, recommended policy.
5. **Navigation restrictions** — presence and correctness of `will-navigate` and `setWindowOpenHandler`.
6. **Auto-update findings** — signature verification configured or not; update URL protocol.
7. **Severity-ranked findings** — Critical / High / Medium / Low with file:line and concrete fix.
8. **Next safe action** — the single most critical remediation step.

## Safety checks

- Do not execute any IPC calls or trigger auto-update during the review.
- Do not print or log secret values found in source files (API keys, tokens).
- Read-only analysis only; do not modify `BrowserWindow` configs or preload scripts without explicit approval.
- If a Critical finding (e.g. `nodeIntegration: true` with remote content) is found, recommend blocking the PR before merge.

## Completion criteria

Done means: every `BrowserWindow` instance is checked for the five core security options, every `contextBridge` exposure is listed and assessed, every `ipcMain` handler has a validation status, CSP is documented and evaluated, navigation restrictions are confirmed or flagged, auto-update signature verification is confirmed or flagged, and every finding has file:line + severity + concrete fix.

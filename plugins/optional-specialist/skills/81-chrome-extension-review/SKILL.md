---
name: chrome-extension-review
description: Use when you need to review Chrome extension manifests, content scripts, background workers, permissions, and store-readiness.
---

# Chrome Extension Review

## Purpose
Review Chrome extensions for Manifest V3 compliance, security (CSP, XSS, privilege escalation), permission minimization, message-passing correctness, content script isolation, and Chrome Web Store policy readiness.

## When to use
- Reviewing a new or updated Chrome extension before submitting to the Chrome Web Store.
- Auditing an existing extension's `manifest.json`, service worker, content scripts, or popup pages.
- Evaluating permission requests for least-privilege compliance.
- Reviewing extension code after a MV2 → MV3 migration.
- Security audit of an extension that handles user credentials, payment data, or PII.

## When not to use
- Firefox/Safari WebExtension review where browser-specific APIs differ significantly — flag divergences but note this skill targets Chrome.
- Pure web app review with no `chrome.*` API usage.
- Native messaging host code review (separate OS-level process).

## Procedure

### 1. Manifest V3 compliance
- Confirm `"manifest_version": 3` — MV2 extensions are being phased out and will stop working in Chrome.
- `background.service_worker` replaces `background.scripts` / `background.page` from MV2.
- `declarativeNetRequest` replaces `webRequest` blocking mode — verify rules are defined in `_rules.json` or fetched via `updateDynamicRules`.
- `action` replaces `browser_action` / `page_action`.
- Remote code execution is prohibited: no `eval()`, no `new Function(string)`, no `chrome.tabs.executeScript` with a string body loaded from a remote URL.
- `content_scripts` must not use `document.write()`.

### 2. Permissions — least privilege
- List every permission in `permissions`, `optional_permissions`, and `host_permissions`.
- For each permission, verify it is actually used in the code. Remove any unused permission.
- Prefer `activeTab` over broad `host_permissions` like `<all_urls>` or `*://*/*` when the extension only needs the current tab.
- Sensitive permissions (`tabs`, `history`, `bookmarks`, `cookies`, `webNavigation`, `downloads`, `nativeMessaging`) require clear justification in the store listing.
- `scripting` permission: verify `chrome.scripting.executeScript` is not used to inject remotely-fetched code strings.
- `storage` vs `unlimitedStorage`: only request `unlimitedStorage` if the data volume genuinely requires it.

### 3. Host permissions
- Scope to the minimum set of origins required. `https://api.example.com/*` is better than `https://*/*`.
- Wildcard subdomains (`https://*.example.com/*`) must be justified — ensure the extension does not accidentally run on all subdomains of a large service.
- Optional host permissions should be requested at runtime via `chrome.permissions.request()` rather than declared statically for permissions not needed at install time.

### 4. Content Security Policy
- Extension pages (popup, options, sidepanel) must have a strict CSP in `manifest.json` under `"content_security_policy"`.
- Minimum acceptable: `"script-src 'self'; object-src 'none';"` — no `unsafe-inline`, no `unsafe-eval`.
- External script sources in CSP are not allowed in MV3 for extension pages.
- Content scripts run in an isolated world by default; verify they do not access `unsafeWindow` or `window.wrappedJSObject` without necessity.

### 5. Message passing security
- `chrome.runtime.onMessage.addListener`: verify the `sender` is checked before acting on messages — do not trust messages from arbitrary web pages.
- `chrome.runtime.sendMessage` from content scripts: the service worker handler must validate the message shape before executing privileged actions.
- `chrome.runtime.onMessageExternal` (cross-extension messaging): explicitly whitelist allowed extension IDs if used.
- `postMessage` between content script and page: validate `event.origin` strictly; never use `origin === '*'`.

### 6. Content script isolation and XSS
- Content scripts must not inject innerHTML with page-supplied data: `element.innerHTML = response.data` is XSS if `response.data` is attacker-controlled.
- Use `textContent` for text, `createElement` + `setAttribute` for DOM construction.
- DOM-based XSS: watch for `document.location`, `document.URL`, `document.referrer` fed into `eval`, `innerHTML`, or `document.write`.
- Content scripts should not expose functions on the page's `window` object unless strictly necessary.

### 7. Service worker (background)
- Service workers are event-driven and terminate when idle — do not rely on in-memory state persisting between events; use `chrome.storage.session` or `chrome.storage.local`.
- Avoid long-running `setInterval` — use `chrome.alarms` for periodic tasks.
- `chrome.alarms.create` requires the `alarms` permission.
- Unhandled promise rejections in service workers silently fail — add `.catch()` to all async chains.
- `chrome.storage.local` is not encrypted — do not store sensitive credentials there; use `chrome.storage.session` (cleared on browser restart) or the OS credential store via native messaging.

### 8. web_accessible_resources
- List only the resources that must be accessible from web pages.
- Specify `matches` to restrict which origins can access the resource — avoid `"matches": ["<all_urls>"]`.
- An overly permissive `web_accessible_resources` allows malicious pages to fingerprint extension presence and load extension assets.

### 9. Data handling and privacy
- Personal data collected (browsing history, form data, PII) must be disclosed in the store privacy policy and in the manifest `"privacy_policy"` URL.
- No sending of tab URLs or content to third-party servers without user consent.
- Verify no API keys, client secrets, or tokens are hardcoded in extension source — they are visible to users who inspect the extension.

### 10. Chrome Web Store policy readiness
- Extension must have a single, clear purpose described in the listing.
- No obfuscated code — the store may reject or remove extensions with intentionally obfuscated JavaScript.
- Update URL must be omitted (managed by the store) for public listings.
- Icons: 16, 48, 128 px PNG required; verify they are included in the package.

## Checklist

MV3 compliance:
- [ ] `manifest_version: 3`
- [ ] `background.service_worker` defined (no `background.page`)
- [ ] No `eval()`, `new Function(string)`, or remote script injection
- [ ] `declarativeNetRequest` used instead of blocking `webRequest` where applicable

Permissions:
- [ ] Every declared permission is used in code
- [ ] `activeTab` preferred over `<all_urls>` where possible
- [ ] Sensitive permissions (`tabs`, `history`, `cookies`) justified
- [ ] Host permissions scoped to minimum required origins

Security:
- [ ] CSP on extension pages: `script-src 'self'`, no `unsafe-inline`/`unsafe-eval`
- [ ] `runtime.onMessage` validates `sender` before privileged actions
- [ ] Content scripts avoid `innerHTML` with external data
- [ ] `web_accessible_resources` has restricted `matches`

Service worker:
- [ ] No in-memory state relied upon across events
- [ ] `chrome.alarms` used for periodic tasks, not `setInterval`
- [ ] All async promise chains have `.catch()`

Privacy:
- [ ] No hardcoded API keys in source
- [ ] No PII sent to third parties without user consent
- [ ] Privacy policy URL in manifest

## Common issues & anti-patterns

- **MV2 background page left in manifest**: causes load failure in Chrome 127+ (MV2 phase-out). Replace with `service_worker`.
- **`"host_permissions": ["<all_urls>"]`**: flags for manual review in the store and is almost always broader than needed.
- **`innerHTML` with data from `fetch()`**: if the fetched resource can be influenced by a web page (CORS, redirect), this is a stored XSS vector inside the extension context.
- **No `sender` check in `onMessage`**: a malicious web page can send crafted messages to the extension's background and trigger privileged actions.
- **Storing OAuth tokens in `chrome.storage.local`**: readable by any code with access to the extension context. Prefer `chrome.storage.session` or prompt re-auth.
- **`eval()` in content scripts for template rendering**: violates MV3 CSP and the store policy.
- **`web_accessible_resources: ["*"]` with `matches: ["<all_urls>"]`**: allows any web page to detect the extension and load any bundled asset.
- **`chrome.tabs.query` for all tabs**: collecting all open tab URLs is a privacy risk and requires justification; prefer `activeTab`.

## Required output

Return a structured report with:
- **Summary**: pass / needs fixes / blocked (store-rejection risk or security issue).
- **Manifest snapshot**: key fields reviewed (version, permissions, host_permissions, CSP, service worker).
- **Findings table**: severity (critical / high / medium / low / info), category, file + line, description, remediation.
- **Permission audit**: each permission listed with justification status (justified / unused / overly broad).
- **Store readiness**: checklist of store policy items that pass or require attention.
- **Next handoff**: specific items to fix before store submission; note any that require store team waiver.

## Safety

- Do not install or execute the extension in a browser during review.
- Never extract or print API keys found in the source — flag as critical finding requiring rotation.
- Do not access the extension's storage contents or user data.
- If the extension appears to perform undisclosed data collection (keylogging, form scraping), flag as critical and recommend immediate removal from distribution.

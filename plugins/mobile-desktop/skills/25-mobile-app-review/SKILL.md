---
name: mobile-app-review
description: Use when you need to review mobile app architecture, navigation, state, platform integration, and release surfaces.
---

# Mobile App Review

## Purpose

Review a mobile application's architecture, navigation stack, state-management strategy, offline behavior, deep-link handling, app-lifecycle integration, and platform-specific release surface for the App Store and Play Store. The output is an actionable, evidence-based set of findings with severity ratings and a concrete code or config fix for each — covering iOS native, Android native, React Native, Flutter, and Expo without triggering builds, deploys, or store submissions.

## When to use

- The user asks to review a mobile app codebase (iOS, Android, React Native, Flutter, Expo).
- A PR adds a new screen, navigator, or background service and needs a targeted review.
- The app has recurring crashes, ANR reports, or battery and network complaints and a structural cause is suspected.
- A pre-launch checklist is needed before App Store or Play Store submission.

## When not to use

- The question is purely backend with no mobile lifecycle or platform API involved.
- The task is a pure pixel-level design critique with no code.
- A narrower skill already covers the exact surface: `ios-hig-review` for Apple HIG depth, `android-material-review` for Material 3 depth.

## Procedure

1. **Identify the platform and project structure.** Determine the platform (iOS native, Android native, React Native, Flutter), the minimum OS version, and the build toolchain. Locate the entry point: `AppDelegate`/`SceneDelegate` (iOS), `MainActivity`/`Application` (Android), `main.dart` (Flutter), `App.tsx`/`index.js` (React Native).
2. **Review the navigation stack.** Check the navigator type (stack, tab, drawer, bottom sheet). Verify the back stack does not leak screens on repeated navigation. Confirm deep links resolve at the correct navigator level, not hardcoded to a single screen.
3. **Review state management.** Identify the pattern (Redux/Redux Toolkit, MobX, Zustand, Riverpod, ViewModel plus LiveData/StateFlow, TCA). Flag state living in the wrong layer (UI holding business logic, or a service holding view state) and unbounded observable subscriptions that are never disposed.
4. **Review app-lifecycle integration.** Check foreground, background, and terminated transitions. Verify background-task registration (`BGTaskScheduler` on iOS, `WorkManager` on Android) declares correct constraints. Confirm push-notification handling works in all three app states.
5. **Review offline and caching behavior.** Locate the cache layer (SQLite, Room, Core Data, Hive, AsyncStorage). Verify a TTL or stale-while-revalidate strategy. Check for unhandled network errors that leave the UI in an indefinite loading state.
6. **Review deep-link and universal-link setup.** Confirm Associated Domains (iOS) and App Links (Android) are configured. Verify the router handles unknown paths gracefully and that authenticated deep links require a valid session before navigation.
7. **Review battery and network hygiene.** Look for polling loops without exponential backoff. Confirm WebSocket and SSE connections close when the app backgrounds. Check for wake-lock or location-permission overreach.
8. **Review crash and error surfaces.** Identify uncaught-exception handlers, the crash reporter (Crashlytics, Sentry), and ANR watchdogs. Confirm React Native error boundaries or Flutter structured error types are in place.
9. **Review the release surface.** Confirm a current target API or OS level, an iOS 17+ privacy manifest (`PrivacyInfo.xcprivacy`) or a Play Data Safety form, and that permissions are requested at the moment of need rather than at launch.
10. **Summarize findings** with severity (Critical, High, Medium, Low) and a concrete fix for each.

## Concrete checks

Navigation and state:
- No screen leak on repeated back-press; deep links resolve at the right level.
- Unknown deep-link paths have a fallback route.
- Business logic is out of widgets and views; subscriptions are disposed.
- Navigation is not triggered from inside a ViewModel.

Lifecycle and offline:
- Background tasks are registered with correct constraints.
- Push notifications are handled in foreground, background, and terminated states.
- Network errors surface explicit error states, not infinite spinners.
- Local cache has a defined TTL or revalidation strategy.

Security and battery:
- Sensitive data uses Keychain/Keystore or an encrypted store, not plain AsyncStorage.
- Authenticated deep links pass through a login guard.
- No unbounded polling; sockets close on background; background location is justified.

Release:
- Crash reporter is integrated and uncaught errors are surfaced.
- Permissions are requested at the point of need, not at launch.
- Target API level is current; iOS privacy manifest or Play Data Safety is complete.

## Commands

```bash
# --- platform / framework ---
# detect platform and framework
fd -t f 'pubspec.yaml|Podfile|build.gradle|app.json|AndroidManifest.xml|Info.plist' . | head

# --- state management ---
# state-management library in use
rg -n 'redux|zustand|mobx|riverpod|provider|ViewModel|StateFlow|LiveData' . | head

# navigation triggered from a ViewModel (anti-pattern)
rg -n 'Navigator\.(push|pop)|router\.push' . | rg -i 'viewmodel|presenter' | head

# --- lifecycle / battery ---
# polling without lifecycle awareness (battery risk)
rg -n 'setInterval|Timer\.periodic|Handler\(\)\.postDelayed' . | head

# background-task registration with constraints
rg -n 'BGTaskScheduler|WorkManager|enqueueUniqueWork' . | head

# --- offline / storage ---
# AsyncStorage used for sensitive data (should be Keychain/Keystore)
rg -n 'AsyncStorage\.(set|get)Item' . | head

# cache TTL / revalidation present
rg -n 'staleTime|cacheTime|ttl|expires|maxAge' . | head

# --- deep links / permissions ---
# permissions requested — check timing (launch vs point of need)
rg -n 'requestPermission|ActivityCompat.requestPermissions|requestAccess' . | head

# deep link routing and auth guards
rg -n 'getInitialURL|onLink|associatedDomains|appLinks|deepLink' . | head

# --- crash reporting / release ---
# crash reporter wired up?
rg -n 'Crashlytics|Sentry|setUncaughtExceptionHandler|FlutterError.onError' . | head

# iOS privacy manifest present (iOS 17+)
fd -t f 'PrivacyInfo.xcprivacy' .

# Play Data Safety / target API declaration
rg -n 'targetSdk|dataSafety|usesPermission' . | head

# --- subscriptions / leaks ---
# observable/stream subscriptions and whether they are disposed
rg -n 'subscribe\(|\.listen\(|addObserver|collect\{' . | head
rg -n 'dispose|cancel|removeObserver|unsubscribe' . | head

# --- socket lifecycle ---
# WebSocket/SSE connections and background-close handling
rg -n 'WebSocket|EventSource|socket\.connect|\.close\(\)' . | head
```

## Common issues & anti-patterns

- **God screen:** one ViewController, Composable, or widget managing network, business logic, and UI at once. Split into ViewModel plus Repository.
- **Navigation from the ViewModel:** calling `Navigator.push` or `router.push` inside a ViewModel breaks testability. Use a coordinator or a navigation-state observable.
- **AsyncStorage as a database:** AsyncStorage is unencrypted and string-only. Sensitive data needs SQLCipher or Keychain/Keystore.
- **Polling without lifecycle awareness:** a `setInterval` that keeps running after backgrounding drains the battery. Wrap it in an AppState or lifecycle listener.
- **Missing splash-to-content transition:** a blank white frame between splash and first content. Use a persistent splash or a skeleton.
- **Unchecked permission denial:** calling a permission-gated API after permanent denial crashes silently. Always check the status before the call.
- **Deep link bypassing auth:** navigating straight to a protected screen without verifying the session exposes user data.
- **Subscription leak:** an observable or stream subscribed in `onCreate`/`init` and never cancelled, so it fires after the view is gone and leaks memory.
- **Socket left open on background:** a WebSocket that keeps streaming while the app is backgrounded, draining battery and burning data until the OS kills the process.
- **Permission requested at launch:** asking for location or notifications on first launch before any context, which users reflexively deny and then cannot easily re-grant.
- **No retry backoff:** a failed network call retried in a tight loop with no exponential backoff, hammering the server and the radio.
- **Deep link bypassing the splash:** a cold-start deep link that renders a protected screen before the session is restored, briefly exposing stale or empty state.
- **Unbounded image cache:** an in-memory image cache with no eviction policy that grows until the OS terminates the app under memory pressure.

## Required output

Return a structured report with:
1. **Platform and project summary** (one paragraph): platform, minimum OS, toolchain, and entry point.
2. **Findings table:** Area, Severity, Finding, Recommended fix.
3. **Top three must-fix items** with a concrete code or config change.
4. **Items confirmed working** so the user knows what was checked and passed.

## Safety

- Do not read or print secrets, API keys, or credentials found in source files.
- Do not trigger test builds, deploys, or store submissions.
- Do not modify source files unless the user explicitly asks for a fix applied in place.
- Redact any signing, keystore, or provisioning details surfaced during review.
- Flag permission and data-handling concerns explicitly, since they gate store approval.

## Completion criteria

Done means the platform and entry point are identified; navigation, state, lifecycle, offline, deep links, battery, crash reporting, and the release surface were each reviewed; every finding has a severity and a concrete fix; the top three must-fix items are called out; and passing areas are listed so coverage is explicit.

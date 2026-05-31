---
name: mobile-app-review
description: Use when you need to review mobile app architecture, navigation, state, platform integration, and release surfaces.
---

# Mobile App Review

## Purpose

Review a mobile application's architecture, navigation stack, state management strategy, offline behavior, deep link handling, app lifecycle integration, and platform-specific release surface. Produce actionable, evidence-based findings with severity ratings.

## When to use

- The user asks to review a mobile app codebase (iOS, Android, React Native, Flutter, Expo).
- A PR adds a new screen, navigator, or background service and needs a targeted review.
- The app has recurring crashes, ANR reports, or battery/network complaints and a structural cause is suspected.
- Pre-launch checklist is needed before App Store or Play Store submission.

## When not to use

- The question is purely backend (no mobile lifecycle or platform API involved).
- The task is a pure pixel-level design critique with no code — use a design tool instead.
- A narrower skill (ios-hig-review, android-material-review) already covers the exact surface.

## Procedure

1. **Identify the platform and project structure.** Determine platform (iOS native / Android native / RN / Flutter), minimum OS version, and build toolchain. Locate entry point (AppDelegate, MainActivity, main.dart, App.tsx).
2. **Review navigation stack.** Check navigator type (stack, tab, drawer, bottom sheet). Verify back-stack is not leaking screens. Confirm deep links are handled at the correct navigator level, not hardcoded to a single screen.
3. **Review state management.** Identify the pattern (Redux, MobX, Zustand, Riverpod, ViewModel/LiveData, TCA). Check for state living in the wrong layer (UI holding business logic, or service holding view state). Flag unbounded observable subscriptions.
4. **Review app lifecycle integration.** Check foreground/background/terminate transitions. Verify background task registration (BGTaskScheduler, WorkManager) has correct constraints. Confirm push notification handling works in all three app states.
5. **Review offline and caching behavior.** Locate cache layer (SQLite, Room, Core Data, Hive, AsyncStorage). Verify stale-while-revalidate or TTL strategy exists. Check for unhandled network errors that leave the UI in a loading state indefinitely.
6. **Review deep link and universal link setup.** Confirm Associated Domains / App Links are configured. Verify the link router handles unknown paths gracefully. Check that authenticated deep links require login before navigation.
7. **Review battery and network hygiene.** Look for polling loops without exponential backoff. Confirm WebSocket or SSE connections are closed when the app backgrounds. Check for wake lock or location permission overreach.
8. **Review crash and error surfaces.** Identify uncaught exception handlers, crash reporters, and ANR watchdogs. Confirm error boundaries (React Native) or structured error types (Flutter) are in place.
9. **Summarize findings** with severity (Critical / High / Medium / Low) and a concrete fix recommendation for each.

## Checklist

- [ ] Navigation: no screen leak on back-press, deep links resolve correctly
- [ ] State: business logic not in widgets/views, no memory leaks from subscriptions
- [ ] Lifecycle: background tasks registered with correct constraints
- [ ] Push notifications: handled in foreground, background, and terminated states
- [ ] Offline: error states shown, retry with backoff, local cache TTL defined
- [ ] Deep links: login guard present, unknown paths have fallback
- [ ] Battery: no unbounded polling, background location justified
- [ ] Crash reporting: SDK integrated, uncaught errors surfaced to reporting tool
- [ ] Permissions: requested at the right moment, not at launch
- [ ] Release: target API level current, privacy manifest (iOS 17+) or data safety (Play) complete

## Common issues & anti-patterns

- **God screen**: a single ViewController or Composable managing network, business logic, and UI simultaneously. Split into ViewModel + Repository.
- **Navigation from ViewModel**: calling `Navigator.push` or `router.push` inside a ViewModel breaks testability. Use a coordinator or navigation state observable.
- **AsyncStorage as a database**: AsyncStorage is unencrypted and string-only. Sensitive data needs SQLCipher or Keychain/Keystore.
- **Polling without lifecycle awareness**: a `setInterval` that keeps running after the app backgrounds drains battery. Wrap in AppState listener.
- **Missing splash-to-content transition**: showing a blank white screen between splash and first content frame. Use a persistent splash or skeleton.
- **Unchecked permission denial**: calling a permission-gated API after the user has permanently denied it crashes silently. Always check status before API call.
- **Deep link bypassing auth**: navigating directly to a protected screen without verifying the session first exposes user data.

## Required output

Return a structured report with:
1. Platform and project summary (one paragraph).
2. Findings table: Area | Severity | Finding | Recommended fix.
3. Top 3 must-fix items with a concrete code or config change.
4. Items confirmed working (so the user knows what was checked and passed).

## Safety

- Do not read or print secrets, API keys, or credentials found in source files.
- Do not trigger test builds, deploys, or store submissions.
- Do not modify source files unless the user explicitly asks for a fix applied in-place.

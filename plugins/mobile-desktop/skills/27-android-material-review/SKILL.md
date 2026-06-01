---
name: android-material-review
description: Use when you need to review Android interfaces against Material conventions, navigation, accessibility, and device behavior.
---

# Android Material Review

## Purpose

Audit an Android interface (Jetpack Compose or View-based XML) against Material Design 3: edge-to-edge layout, predictive back gesture, dynamic color theming, touch ripple, density-independent sizing, adaptive icons, and TalkBack accessibility. The output is a set of findings with Material 3 spec references and a concrete fix for each, ranked by Play Store submission risk and device-behavior impact. The review reads source only and never triggers Gradle builds, signing, or Play Console uploads.

## When to use

- A Compose or XML-based screen needs review before Play Store submission.
- A feature PR introduces new navigation, bottom-sheet, or dialog patterns.
- The app targets Android 12 and later and needs an audit for dynamic color or predictive back support.
- A TalkBack or accessibility audit is requested.

## When not to use

- The app is iOS-only — use `ios-hig-review`.
- The review is purely about backend API calls with no UI surface.
- The codebase is React Native or Flutter — Material conventions apply differently; run `mobile-app-review` first to pick the right audit path.

## Procedure

1. **Identify SDK versions and Compose versus View.** Note `compileSdk`, `targetSdk`, and `minSdk`. Confirm Jetpack Compose, XML Views, or both. Check the `androidx.compose.material3` dependency version.
2. **Review edge-to-edge layout.** Verify `enableEdgeToEdge()` (or `WindowCompat.setDecorFitsSystemWindows(window, false)`) in `onCreate`. Confirm `WindowInsets` padding is applied to scrolling containers and FABs so content is not clipped behind the gesture bar.
3. **Audit predictive back-gesture support.** Confirm `android:enableOnBackInvokedCallback="true"` in the manifest for Android 13 and later targets. Verify `OnBackPressedCallback` or Compose `BackHandler` is used instead of overriding the deprecated `onBackPressed()`.
4. **Review Material 3 theming.** Confirm the root theme is Material 3, not material2. Color roles (`primary`, `surface`, `onSurface`, `error`) must come from the theme, not hardcoded hex. Offer `dynamicColorScheme` on Android 12 and later.
5. **Check typography and density.** Text should use `MaterialTheme.typography.*` tokens (`bodyLarge`, `titleMedium`) or `TextAppearance.Material3.*` in XML. Font sizes must be in `sp`; layout dimensions in `dp`, never raw `px`.
6. **Review ripple and touch feedback.** Interactive composables should use `Modifier.clickable {}` (which supplies a ripple) or an explicit `indication = ripple()`. XML clickable views need `?attr/selectableItemBackground`.
7. **Audit the adaptive icon.** Verify `ic_launcher.xml` splits foreground and background layers, is not letter-boxed on circular launchers, and includes a `<monochrome>` layer for Android 13 and later themed icons.
8. **Review bottom-sheet and dialog patterns.** Use `ModalBottomSheet` and `BottomSheetScaffold` from material3, not the deprecated material2 `BottomSheetDialog`. Dialogs must support dismissal (tap-outside and back gesture).
9. **Check touch-target sizes.** Minimum 48x48 dp for interactive elements. Use `Modifier.minimumInteractiveComponentSize()` in Compose; `minWidth`/`minHeight` 48dp in XML.
10. **Audit TalkBack accessibility.** Confirm `contentDescription` on image-only buttons; set `contentDescription = null` on decorative images; verify reading order with `semantics { traversalIndex }` where needed.
11. **Review navigation component usage.** Confirm a `NavController` drives navigation instead of manual back-stack manipulation, and that deep links are declared in the navigation graph, not only the manifest.
12. **Summarize findings** with severity and Material 3 spec references.

## Concrete checks

Layout and back gesture:
- Edge-to-edge is enabled and insets are applied to FAB and scroll containers.
- `OnBackInvokedCallback` is registered; the deprecated `onBackPressed` override is removed.
- The status-bar color is system-managed, not hardcoded.

Theming and density:
- The `material3` dependency is present; color roles come from the theme with no hardcoded hex.
- `dynamicColorScheme` is offered on Android 12 and later.
- Typography uses `MaterialTheme.typography.*`; text is in `sp`, dimensions in `dp`.

Feedback and icons:
- Ripple or `selectableItemBackground` is present on all interactive elements.
- The adaptive icon has foreground, background, and a monochrome layer.

Touch and accessibility:
- Touch targets are at least 48x48 dp; Compose uses `minimumInteractiveComponentSize()`.
- TalkBack has `contentDescription` on icon buttons; decorative images are null.
- A `NavController` drives navigation; deep links are in the nav graph.

## Commands

```bash
# --- SDK / version ---
# SDK levels and material3 version
rg -n 'compileSdk|targetSdk|minSdk|material3' . 2>/dev/null | head

# --- edge-to-edge / back ---
# edge-to-edge enabled?
rg -n 'enableEdgeToEdge|setDecorFitsSystemWindows' .

# deprecated back handling
rg -n 'override fun onBackPressed' .

# window insets consumed on bottom content?
rg -n 'windowInsetsPadding|WindowInsets.navigationBars|systemBarsPadding' . | head

# --- theming / density ---
# material2 imports mixed into a material3 app
rg -n 'androidx\.compose\.material\.(Button|Scaffold|TopAppBar|AlertDialog)\b' .

# hardcoded hex colors and px dimensions (theming/density smells)
rg -n '#[0-9a-fA-F]{6}|[0-9]+px' . | head -40

# hardcoded status-bar color (breaks dynamic color)
rg -n 'statusBarColor|navigationBarColor' .

# --- touch / feedback ---
# touch-target enforcement in Compose
rg -n 'minimumInteractiveComponentSize|sizeIn\(minWidth' .

# ripple / selectable background on clickable views
rg -n 'selectableItemBackground|Modifier.clickable|indication' . | head

# --- accessibility / nav ---
# TalkBack content descriptions on icon buttons
rg -n 'contentDescription' . | head

# NavController usage and nav-graph deep links
rg -n 'NavController|navController|deepLink|navDeepLink' . | head

# --- ANR risk ---
# main-thread I/O (ANR on low-end devices)
rg -n 'getSharedPreferences|\.query\(|readText\(\)' . | head

# --- bottom sheet / dialog ---
# material2 bottom sheet / dialog still in use
rg -n 'BottomSheetDialog|android\.app\.AlertDialog' . | head

# --- adaptive icon ---
# adaptive icon layers including a monochrome layer
rg -n 'monochrome|<foreground|<background' . app/src/main/res 2>/dev/null | head

# --- orientation ---
# locked orientation declared intentionally?
rg -n 'screenOrientation' .
```

## Common issues & anti-patterns

- **WindowInsets not consumed:** omitting `Modifier.windowInsetsPadding(WindowInsets.navigationBars)` on bottom content hides it behind the gesture bar on gesture-nav devices.
- **Hardcoded status-bar color:** setting `window.statusBarColor` directly breaks dynamic color and dark mode on Android 12 and later. Let the system manage bar color via `WindowCompat`.
- **Material2 mixed with Material3:** importing `androidx.compose.material.Button` in a Material 3 app breaks theming — all components must come from `androidx.compose.material3`.
- **Deprecated `AlertDialog`:** `android.app.AlertDialog` bypasses Material 3 shape and color. Use `androidx.compose.material3.AlertDialog`.
- **No scrim on a modal bottom sheet:** a custom sheet without a scrim violates modal conventions and confuses screen-reader users.
- **Landscape ignored:** locking `screenOrientation="portrait"` is fine for some games but should be a deliberate, declared choice for general apps.
- **ANR from main-thread I/O:** reading SharedPreferences or a database on the UI thread freezes low-end devices — move it to `Dispatchers.IO`.
- **px instead of dp:** specifying dimensions in raw pixels, so the layout scales incorrectly across screen densities.
- **Letter-boxed adaptive icon:** a launcher icon whose foreground fills the entire safe zone, so it is clipped awkwardly on circular and squircle launchers.
- **Missing monochrome layer:** no `<monochrome>` drawable, so the app icon falls back to a generic look under Android 13 themed icons.
- **No ripple on a custom clickable:** a `Modifier.clickable` without an indication, or an XML view with no `selectableItemBackground`, so taps give no visual feedback.

## Required output

Return a structured report with:
1. **SDK target, Compose version, and material3 version summary.**
2. **Findings table:** Screen/Component, Material 3 Spec, Severity, Issue, Fix.
3. **TalkBack and edge-to-edge pass/fail summary.**
4. **Top three must-fix items** before Play Store submission.

## Safety

- Do not modify `AndroidManifest.xml` permissions without listing every change explicitly for user review.
- Do not trigger Gradle builds, signing, or Play Console uploads.
- Do not read or reproduce keystore credentials or signing configs.
- Redact any API keys found in `gradle.properties` or resource files.
- Treat accessibility and data-handling gaps as submission blockers, not cosmetic notes.

## Completion criteria

Done means SDK levels and the UI system are identified; edge-to-edge, predictive back, Material 3 theming, typography and density, ripple, the adaptive icon, touch targets, TalkBack, and navigation were each checked; every finding cites a Material 3 area and a concrete fix; and the top three submission blockers are called out with a TalkBack and edge-to-edge pass/fail summary.

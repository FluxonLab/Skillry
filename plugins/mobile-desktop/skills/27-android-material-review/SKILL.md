---
name: android-material-review
description: Use when you need to review Android interfaces against Material conventions, navigation, accessibility, and device behavior.
---

# Android Material Review

## Purpose

Audit an Android interface (Jetpack Compose or View-based XML) against Material Design 3 guidelines. Cover edge-to-edge layout, predictive back gesture, dynamic color theming, touch ripple, density-independent sizing, adaptive icons, and accessibility. Produce findings with Material 3 spec references and concrete fix recommendations.

## When to use

- A Compose or XML-based screen needs review before Play Store submission.
- A feature PR introduces new navigation, bottom sheet, or dialog patterns.
- The app targets Android 12+ and needs audit for dynamic color or predictive back gesture support.
- TalkBack or accessibility audit is requested.

## When not to use

- The app is iOS-only — use ios-hig-review instead.
- The review is purely about backend API calls with no UI surface.
- The codebase is React Native or Flutter — material conventions apply differently; use mobile-app-review first to identify the right audit path.

## Procedure

1. **Identify SDK versions and Compose vs. View system.** Note `compileSdk`, `targetSdk`, and `minSdk`. Confirm whether Jetpack Compose, XML Views, or both are used. Check `material3` dependency version.
2. **Review edge-to-edge layout.** Verify `WindowCompat.setDecorFitsSystemWindows(window, false)` is called in `onCreate`. Check that `WindowInsetsCompat` padding is applied to scrolling containers and FABs so content is not clipped behind gesture bars.
3. **Audit predictive back gesture support.** Confirm `android:enableOnBackInvokedCallback="true"` in the manifest for Android 13+ targets. Verify `OnBackPressedCallback` or `BackHandler` (Compose) is used instead of deprecated `onBackPressed()` overrides.
4. **Review Material 3 theming.** Check that `MaterialTheme` is the root theme (not `MaterialTheme` from material2). Verify color roles (`Primary`, `Surface`, `OnSurface`, `Error`) are used from the theme, not hardcoded hex values. Check `dynamicColorScheme` is offered on Android 12+ devices.
5. **Check typography and density.** All text should use `MaterialTheme.typography.*` tokens (`bodyLarge`, `titleMedium`, etc.) or `TextAppearance.Material3.*` in XML. Font sizes must be in `sp`, not `dp`.
6. **Review ripple and touch feedback.** Confirm interactive composables use `Indication = ripple()` or `Modifier.clickable {}`. Check XML-based views have `?attr/selectableItemBackground` on clickable items, not no background.
7. **Audit adaptive icon.** Verify `ic_launcher.xml` uses a foreground/background layer split. Check that the icon is not letter-boxed on circular launchers. Confirm a monochrome layer exists for Android 13+ themed icon support.
8. **Review bottom sheet and dialog patterns.** `BottomSheetScaffold` / `ModalBottomSheet` should be used from material3, not the deprecated material2 `BottomSheetDialog`. Dialogs must have dismiss behavior (tap outside, back gesture).
9. **Check touch target sizes.** Minimum 48×48 dp for all interactive elements per Material 3 spec. Use `Modifier.minimumInteractiveComponentSize()` in Compose.
10. **Audit TalkBack accessibility.** Confirm `contentDescription` on all image-only buttons. Verify reading order with `semantics { traversalIndex }`. Check that decorative images have `contentDescription = null`.
11. **Review navigation component usage.** Confirm NavController is used instead of manual back-stack manipulation. Check that deep links are declared in the navigation graph, not just in the manifest.
12. **Summarize findings** with severity and Material 3 spec references.

## Checklist

- [ ] Edge-to-edge: `setDecorFitsSystemWindows(false)`, insets applied to FAB and scroll containers
- [ ] Predictive back: `OnBackInvokedCallback` registered, deprecated `onBackPressed` removed
- [ ] Material 3: `material3` dependency, color roles from theme, no hardcoded hex
- [ ] Dynamic color: `dynamicColorScheme` offered on Android 12+
- [ ] Typography: `MaterialTheme.typography.*` tokens, text sizes in sp
- [ ] Ripple: `Modifier.clickable {}` or `selectableItemBackground` on all interactive views
- [ ] Adaptive icon: foreground/background layers, monochrome layer present
- [ ] Touch targets: minimum 48×48 dp, `minimumInteractiveComponentSize()` in Compose
- [ ] TalkBack: `contentDescription` on icon buttons, decorative images null
- [ ] Navigation: NavController used, deep links in nav graph
- [ ] Density: no hardcoded px values, all dimensions in dp/sp

## Common issues & anti-patterns

- **WindowInsets not consumed**: not applying `Modifier.windowInsetsPadding(WindowInsets.navigationBars)` to bottom content causes it to be hidden behind gesture bar on gesture-nav devices.
- **Hardcoded status bar color**: setting `window.statusBarColor` directly breaks dynamic color and dark mode on Android 12+. Use `WindowCompat` and let the system handle bar color.
- **Material2 mixed with Material3**: importing `androidx.compose.material.Button` in a Material 3 app breaks theming. All components must come from `androidx.compose.material3`.
- **Deprecated `AlertDialog` from material**: using `android.app.AlertDialog` bypasses Material 3 dialog shape and color. Use `androidx.compose.material3.AlertDialog`.
- **No scrim on modal bottom sheet**: a custom `BottomSheet` without a scrim behind it violates modal overlay conventions and confuses screen reader users.
- **Landscape layout ignored**: fixed portrait-only orientation (`screenOrientation="portrait"`) is acceptable for games but not general apps. If landscape is blocked, declare it intentionally.
- **ANR from main-thread I/O**: reading SharedPreferences or a database on the UI thread causes ANR on low-end devices. All I/O must use `Dispatchers.IO`.

## Required output

Return a structured report with:
1. SDK target, Compose version, and material3 version summary.
2. Findings table: Screen/Component | Material 3 Spec | Severity | Issue | Fix.
3. TalkBack and edge-to-edge pass/fail summary.
4. Top 3 must-fix items before Play Store submission.

## Safety

- Do not modify `AndroidManifest.xml` permissions without listing all changes explicitly for user review.
- Do not trigger Gradle builds, signing, or Play Console uploads.
- Do not read or reproduce keystore credentials or signing configs.

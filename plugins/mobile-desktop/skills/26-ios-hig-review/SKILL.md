---
name: ios-hig-review
description: Use when you need to review iOS interfaces against platform conventions, navigation, accessibility, and touch ergonomics.
---

# iOS HIG Review

## Purpose

Audit an iOS interface (UIKit or SwiftUI) against Apple's Human Interface Guidelines: safe-area layout, Dynamic Type, SF Symbols usage, haptic feedback, dark mode, tap-target sizing, navigation paradigm, and VoiceOver support. The output is a prioritized set of findings, each citing the relevant HIG area and a concrete code fix, ranked by App Store submission risk. The review reads source or screenshots only and never triggers Xcode builds or TestFlight uploads.

## When to use

- A SwiftUI or UIKit screen needs review before App Store submission.
- Design or code review for an iOS-specific feature (sheets, navigation, widgets, Live Activities).
- An App Store rejection cited HIG violations and a root-cause analysis is needed.
- An accessibility audit is requested for VoiceOver, Dynamic Type, or Reduce Motion compliance.

## When not to use

- The app is Android-only — use `android-material-review`.
- The review is purely about business logic or backend integration — use `mobile-app-review`.
- The design exists in a design tool only with no code to audit — this skill needs source or screenshots.

## Procedure

1. **Identify the UI framework and deployment target.** Confirm SwiftUI, UIKit, or hybrid. Note the minimum iOS version — HIG expectations differ across iOS 15 to 18 (for example NavigationStack and the Dynamic Island land in iOS 16 and later).
2. **Check safe area and layout margins.** Verify `.safeAreaInset`, `safeAreaLayoutGuide`, or `.ignoresSafeArea` usage is intentional. Content under the notch, Dynamic Island, or home indicator must be deliberate and remain readable.
3. **Audit Dynamic Type support.** All text should use a text style — `.font(.body)` or `.font(.headline)` in SwiftUI, or `UIFont.preferredFont(forTextStyle:)` in UIKit, or a custom font via `relativeTo:`. Confirm labels do not truncate at accessibility sizes; use `.fixedSize(horizontal: false, vertical: true)` where needed.
4. **Review tap-target sizes.** Every interactive element must be at least 44x44 pt. Wrap small icon-only buttons in `.frame(minWidth: 44, minHeight: 44)` or add `.contentShape(Rectangle())` to extend the hit area.
5. **Check SF Symbols usage.** Verify symbol names exist on the deployment target (confirm in the SF Symbols app). Prefer `.symbolRenderingMode` and `.foregroundStyle` over tint hacks; multicolor symbols need `.renderingMode(.original)`; tab-bar symbols need the `.fill` variant.
6. **Review haptic feedback.** `UIImpactFeedbackGenerator` and `UINotificationFeedbackGenerator` (or SwiftUI `.sensoryFeedback`) should mark meaningful state changes, not decorate animations. Call `.prepare()` before `.impactOccurred()` to avoid first-fire latency.
7. **Audit dark mode support.** Replace hardcoded `UIColor(red:...)` and `Color(red:...)` with semantic colors (`Color(.systemBackground)`, `.label`, `.secondaryLabel`). Confirm asset-catalog images have dark variants.
8. **Review the navigation paradigm.** Use `NavigationStack` (iOS 16 and later) instead of the deprecated `NavigationView`. Modal sheets are for self-contained tasks, not drill-down. The back-button label should reflect the parent title, not a generic "Back".
9. **Check sheet and presentation style.** Confirm `.sheet`, `.fullScreenCover`, and `.presentationDetents` are appropriate; destructive actions in a sheet require explicit confirmation.
10. **Review accessibility annotations.** Confirm `.accessibilityLabel`, `.accessibilityHint`, and `.accessibilityValue` on custom controls; mark decorative images `.accessibilityHidden(true)`; verify `UIAccessibility.isReduceMotionEnabled` is respected for non-essential animation.
11. **Summarize findings** with HIG section references and severity.

## Concrete checks

Layout and type:
- Content does not underlap the notch, Dynamic Island, or home indicator unintentionally.
- All text uses a text style and scales with Dynamic Type.
- No truncation at the largest accessibility sizes.

Touch and symbols:
- Every interactive element is at least 44x44 pt.
- SF Symbol names are valid for the deployment target with the correct rendering mode.
- Tab-bar symbols use the `.fill` variant.

Color and motion:
- No hardcoded colors that break dark mode; asset catalog has dark variants.
- Haptics mark meaningful feedback and call `.prepare()` first.
- Non-essential animation respects Reduce Motion.

Navigation and accessibility:
- `NavigationStack` is used on iOS 16 and later; modals are for tasks, not drill-down.
- The back-button label reflects the parent screen.
- Custom controls have VoiceOver labels and hints; decorative images are hidden.
- `Info.plist` privacy usage strings are present and accurate.

## Commands

```bash
# --- Dynamic Type ---
# hardcoded fonts that break Dynamic Type
rg -n 'Font.system\(size:|UIFont.systemFont\(ofSize:|\.font\(.system\(size:' .

# --- dark mode ---
# hardcoded colors that break dark mode
rg -n 'UIColor\(red:|Color\(red:|UIColor\(white:|#[0-9a-fA-F]{6}' .

# --- navigation ---
# deprecated NavigationView (should be NavigationStack on iOS 16+)
rg -n 'NavigationView\b' .

# custom back buttons that may drop the parent title
rg -n 'navigationBarBackButtonHidden|\.backButtonTitle' .

# --- SF Symbols / tap targets ---
# small icon-only buttons — verify 44pt hit area nearby
rg -n 'Image\(systemName:' . | head -40

# tab-bar symbols missing the fill variant
rg -n 'TabItem|tabItem' . | head

# --- haptics ---
# haptic generators and whether prepare() is called
rg -n 'FeedbackGenerator|impactOccurred|sensoryFeedback|\.prepare\(\)' . | head

# --- accessibility ---
# accessibility annotations present on custom controls?
rg -n 'accessibilityLabel|accessibilityHint|accessibilityHidden' . | head

# Reduce Motion respected?
rg -n 'isReduceMotionEnabled|accessibilityReduceMotion' .

# --- privacy ---
# Info.plist privacy usage strings
rg -n 'NSCameraUsageDescription|NSMicrophoneUsageDescription|NSLocationWhenInUseUsageDescription' .

# --- sheets / presentation ---
# sheet, full-screen cover, and detents usage
rg -n '\.sheet|fullScreenCover|presentationDetents' . | head

# --- alerts ---
# UIKit alerts presented from SwiftUI (sheet-stacking bug on iOS 17+)
rg -n 'UIAlertController|keyWindow' . | head

# --- truncation at large sizes ---
# labels that may truncate under accessibility Dynamic Type sizes
rg -n 'lineLimit\(|truncationMode|fixedSize' . | head
```

## Common issues & anti-patterns

- **Ignoring safe area globally:** `.ignoresSafeArea()` on a scroll view hides content under the Dynamic Island on iPhone 14 Pro and later.
- **Hardcoded font sizes:** `Font.system(size: 14)` does not scale with Dynamic Type — use `.body`, `.caption`, `.footnote`, or `relativeTo:`.
- **Custom back button without a title:** stripping the back-button label breaks conventions and confuses VoiceOver users.
- **UIKit alert from SwiftUI:** presenting a `UIAlertController` via `UIApplication.shared.keyWindow` breaks sheet stacking on iOS 17 and later. Use the `.alert` modifier.
- **Missing `.symbolVariant`:** `Image(systemName: "heart")` in a tab bar without `.fill` violates tab-bar conventions.
- **Non-semantic colors in widgets:** WidgetKit ignores dynamic colors unless `Color(.widgetBackground)` and `.widgetAccentable()` are used.
- **Blocking the main thread during scroll:** synchronous image loading in `cellForRowAt` causes scroll jank — load asynchronously.
- **Decorative haptics:** firing impact feedback on every minor animation, which feels noisy and trains users to ignore it.
- **Sheet for navigation:** using a modal `.sheet` to push a detail screen that should be a `NavigationStack` destination, so the back gesture and title behavior feel wrong.
- **Fixed-size icon button:** a 20pt icon in a 24pt frame used as a tappable button, well under the 44pt minimum and hard to hit reliably.
- **No confirmation on destructive sheet:** a delete action inside a sheet that fires immediately on tap with no confirmation, risking accidental data loss.
- **Light-only asset:** an image asset with no dark-mode variant in the catalog, so a logo or illustration glows on a dark background.
- **Hardcoded accent color:** a brand color set as a literal `Color(red:...)` instead of an asset-catalog color set, so it ignores both dark mode and high-contrast accessibility settings.
- **VoiceOver order scrambled:** a custom layout where the visual order and the accessibility traversal order diverge, so VoiceOver reads controls in a confusing sequence.

## Required output

Return a structured report with:
1. **Framework and iOS version summary.**
2. **Findings table:** Screen/Component, HIG Section, Severity, Issue, Fix.
3. **VoiceOver and Dynamic Type pass/fail summary.**
4. **Top three must-fix items** before App Store submission.

## Safety

- Do not alter `Info.plist` privacy strings without listing every change explicitly for the user to review.
- Do not trigger Xcode builds or TestFlight uploads.
- Do not read or reproduce entitlement files or provisioning-profile details.
- Redact any signing identity or team-ID values surfaced during review.
- Treat accessibility and privacy gaps as submission blockers, not cosmetic notes.

## Completion criteria

Done means the framework and deployment target are identified; safe area, Dynamic Type, tap targets, SF Symbols, haptics, dark mode, navigation, and VoiceOver were each checked against HIG; every finding cites a HIG area and a concrete fix; and the top three submission blockers are called out with a VoiceOver and Dynamic Type pass/fail summary.

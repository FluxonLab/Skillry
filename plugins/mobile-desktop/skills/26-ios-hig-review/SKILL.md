---
name: ios-hig-review
description: Use when you need to review iOS interfaces against platform conventions, navigation, accessibility, and touch ergonomics.
---

# iOS HIG Review

## Purpose

Audit an iOS interface (UIKit or SwiftUI) against Apple's Human Interface Guidelines. Cover safe area layout, Dynamic Type, SF Symbols usage, haptic feedback, dark mode, tap target sizing, and navigation paradigm correctness. Produce prioritized, actionable findings with HIG references.

## When to use

- A SwiftUI or UIKit screen needs to be reviewed before App Store submission.
- Design or code review for an iOS-specific feature (sheets, navigation, widgets, Live Activities).
- App Store rejection was received citing HIG violations and a root cause analysis is needed.
- Accessibility audit is requested for VoiceOver, Dynamic Type, or Reduce Motion compliance.

## When not to use

- The app is Android-only — use android-material-review instead.
- The review is purely about business logic or backend integration — use mobile-app-review.
- The design is in Figma only with no code to audit — this skill requires source or screenshots.

## Procedure

1. **Identify UI framework and iOS deployment target.** Confirm SwiftUI, UIKit, or hybrid. Note minimum iOS version — HIG requirements differ between iOS 15, 16, 17, and 18.
2. **Check safe area and layout margins.** Verify `.safeAreaInset`, `safeAreaLayoutGuide`, or `ignoresSafeArea` usage is intentional. Content behind notch or home indicator must be intentional and readable.
3. **Audit Dynamic Type support.** Confirm all text uses `UIFontTextStyle` (UIKit) or `.font(.body)` / `.font(.custom(_, relativeTo:))` (SwiftUI). Check that labels do not truncate at accessibility sizes — use `fixedSize(horizontal: false, vertical: true)` where needed.
4. **Review tap target sizes.** Every interactive element must be at least 44×44 pt. Check icon-only buttons — wrap in `.frame(minWidth: 44, minHeight: 44)` if the visual is smaller.
5. **Check SF Symbols usage.** Verify symbol names are available on the deployment target (use SF Symbols app to confirm). Confirm `.symbolRenderingMode` and `.foregroundStyle` are used instead of tinting hacks. Multicolor symbols need `renderingMode(.original)`.
6. **Review haptic feedback.** Confirm `UIImpactFeedbackGenerator` / `UINotificationFeedbackGenerator` is used for meaningful state changes, not decorative animations. Verify `.prepare()` is called before `.impactOccurred()` to avoid latency.
7. **Audit dark mode support.** Check for hardcoded `UIColor(hex:)` or `Color(red:green:blue:)` — replace with semantic colors (`Color(.systemBackground)`, `.label`, `.secondaryLabel`). Verify images have dark-mode variants in the asset catalog.
8. **Review navigation paradigm.** Confirm modal sheets are used for tasks, not navigation. NavigationStack (iOS 16+) should replace deprecated NavigationView. Back button label should reflect the parent screen title, not "Back".
9. **Check sheet and presentation style.** Confirm `.sheet`, `.fullScreenCover`, and `.presentationDetents` usage is appropriate. Sheets for destructive actions should require explicit confirmation.
10. **Review accessibility annotations.** Confirm `.accessibilityLabel`, `.accessibilityHint`, and `.accessibilityValue` are present on custom controls. Decorative images must be `.accessibilityHidden(true)`.
11. **Summarize findings** with HIG section references and severity.

## Checklist

- [ ] Safe area: content does not underlap notch or home indicator unintentionally
- [ ] Dynamic Type: all text scales; no truncation at accessibility sizes
- [ ] Tap targets: all interactive elements >= 44×44 pt
- [ ] SF Symbols: names valid for deployment target, rendering mode correct
- [ ] Haptics: used for meaningful feedback, `.prepare()` called before use
- [ ] Dark mode: no hardcoded colors, asset catalog has dark variants
- [ ] Navigation: NavigationStack used (iOS 16+), modals for tasks not for drill-down
- [ ] VoiceOver: labels and hints on all custom controls, decorative images hidden
- [ ] Reduce Motion: animations respect `UIAccessibility.isReduceMotionEnabled`
- [ ] Privacy: camera/microphone/location usage strings present and accurate in Info.plist

## Common issues & anti-patterns

- **Ignoring safe area globally**: `.ignoresSafeArea()` applied to a scroll view causes content to disappear under the Dynamic Island on iPhone 14 Pro and later.
- **Hardcoded font sizes**: `Font.system(size: 14)` does not scale with Dynamic Type. Use `.body`, `.caption`, `.footnote` or `relativeTo:` modifier.
- **Custom back button without title**: removing the back button label breaks navigation conventions and confuses users coming from VoiceOver.
- **UIKit alert from SwiftUI**: presenting a `UIAlertController` from a SwiftUI view via `UIApplication.shared.keyWindow` breaks sheet stacking in iOS 17+. Use `.alert` modifier.
- **Missing `.symbolVariant`**: using `Image(systemName: "heart")` inside a tab bar without `.symbolVariant(.fill)` violates HIG tab bar conventions.
- **Non-semantic colors in widgets**: WidgetKit ignores dynamic colors unless `Color(.widgetBackground)` or `.widgetAccentable()` are used.
- **Blocking main thread during scroll**: fetching images synchronously in `UITableViewDataSource.cellForRowAt` causes scroll jank. Use async image loading.

## Required output

Return a structured report with:
1. Framework and iOS version summary.
2. Findings table: Screen/Component | HIG Section | Severity | Issue | Fix.
3. VoiceOver and Dynamic Type pass/fail summary.
4. Top 3 must-fix items before App Store submission.

## Safety

- Do not alter Info.plist privacy strings without listing all changes explicitly for the user to review.
- Do not trigger Xcode builds or TestFlight uploads.
- Do not read or reproduce entitlement files or provisioning profile details.

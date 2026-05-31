---
name: game-ui-ux-review
description: Use when you need to review game UI, HUD, menus, feedback, onboarding, readability, and control feel.
---

# Game UI/UX Review

## Purpose

Audit the player-facing interface of a game: HUD clarity and information density, menu navigation flow, juice (feedback responsiveness and animation), onboarding and first-session experience, input prompt accuracy, pause and settings behavior. Identify what makes the game feel unresponsive, confusing, or visually cluttered.

## When to use

- Playtesters report the HUD is confusing, menus are hard to navigate, or controls feel unresponsive.
- A first-session onboarding flow is being designed or revised.
- UI is being ported between input modalities (controller to touch, mouse to controller).
- The game is nearing release and a final UX pass is needed before submission.

## When not to use

- The issue is purely a rendering performance problem (low frame rate) — use game-performance-review.
- The issue is a gameplay mechanic bug — use gameplay-systems-review.
- The question is about the underlying UI framework architecture — use game-architecture-review.

## Procedure

1. **Map the full menu and screen flow.** Diagram every reachable screen from the main menu. Identify dead ends (screens with no back button), unreachable screens, and flows requiring more than 3 button presses to reach a common action.
2. **Review HUD information density.** List every HUD element and its update frequency. Verify that the player can read health, ammo, and objective at a glance without moving their eyes from the action area. Check for HUD elements that obstruct the play area on 4:3 and 21:9 aspect ratios.
3. **Audit feedback and juice.** For every player action (hit, collect, level up, death), verify there is at minimum: a visual response (particle, flash, animation), an audio response (sound effect), and where appropriate a haptic response. Identify "silent" actions where the game gives no confirmation.
4. **Review input prompts.** Confirm button prompts change dynamically when the player switches between keyboard, mouse, and controller. Verify that prompts show the correct glyph for the connected controller type (Xbox vs. PlayStation vs. Switch). Check that prompts are localized where button names differ by region.
5. **Review onboarding and tutorial.** Confirm the first 3 minutes introduce mechanics one at a time, not all simultaneously. Check that tutorial prompts disappear after the player has completed the taught action, not on a timer. Verify there is no mandatory unskippable tutorial for returning players.
6. **Review pause and settings.** Confirm pause is always accessible (not blocked during cutscenes or loading screens that can stall). Settings must include: audio volume (master/music/SFX separately), display (resolution, vsync, brightness), and controls (remapping or at least a legend). Verify settings are persisted and not reset to defaults on restart.
7. **Review font readability.** Confirm minimum font size is 24px at 1080p for body text, 18px for secondary. Check that fonts with thin strokes remain readable on CRT-filter shaders and at television viewing distances (3m / 10ft). Verify text has contrast ratio >= 4.5:1 against backgrounds.
8. **Review menu navigation with controller.** Confirm all menu elements are reachable by D-pad/analog stick. Check that focus is always visible (highlighted state clear). Verify that pressing B/Circle/back on a menu returns to the parent screen, not exits the game.
9. **Review loading and transition states.** Confirm there is always a visual indicator during any load >0.5 seconds. Verify the indicator is animated (not a static image) so the player knows the game has not frozen.
10. **Summarize findings** with severity, affected screen, and a concrete UX fix.

## Checklist

- [ ] Menu flow: no dead ends, common actions reachable in <3 presses
- [ ] HUD: critical info (health, objective) in peripheral vision zone, safe on all aspect ratios
- [ ] Juice: every action has visual + audio feedback, no silent interactions
- [ ] Input prompts: update dynamically per input device, correct glyphs per controller
- [ ] Tutorial: one mechanic at a time, dismisses on completion not timer, skippable for returning players
- [ ] Pause: always accessible, not blocked by game state
- [ ] Settings: audio, display, controls sections; settings persisted across sessions
- [ ] Font: >=24px at 1080p body text, >=4.5:1 contrast ratio
- [ ] Controller nav: all elements D-pad reachable, focus always visible, back button returns to parent
- [ ] Loading: animated indicator for any load >0.5s

## Common issues & anti-patterns

- **HUD anchor drift on non-16:9**: health bar anchored to pixel coordinates instead of percentage or safe zone, causing it to overlap gameplay on ultrawide or tablet.
- **No feedback on failed action**: player presses "buy" when out of currency and nothing happens — no sound, no shake, no message. Player thinks the button is broken.
- **Controller prompts showing keyboard icons**: detecting input device only at startup and not polling per-frame means switching to controller mid-session still shows WASD.
- **Forced tutorial on every new game**: players who die on the first run and restart are forced through the full tutorial again. Gate tutorial behind a "first launch" flag.
- **Settings reset after crash**: writing settings only on clean exit means a crash restores defaults. Write settings immediately on change, not on quit.
- **Back button exits the game from first menu**: pressing B/Circle on the main menu immediately quits the game without a confirmation dialog. Add a "Quit game?" confirmation.
- **Loading bar that does not move**: a static progress bar that jumps from 0% to 100% in one frame (because loading was synchronous) looks like a freeze. Fake progressive fill if true async progress is not available.
- **Unskippable opening cinematics on every launch**: players replay the game and must sit through 90 seconds of logos on every cold start. Add a skip input from frame 1.

## Required output

Return a structured report with:
1. Menu flow diagram (text-based, showing all reachable screens).
2. Findings table: Screen/Element | Severity | Issue | Fix.
3. Juice audit: list of actions with missing feedback.
4. Top 3 most impactful UX improvements before launch.

## Safety

- Do not modify UI scene files, localizations, or asset atlases without explicit user instruction.
- Do not trigger builds or editor commands.
- Do not access or reproduce player save data or analytics.

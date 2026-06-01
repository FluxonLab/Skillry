---
name: game-ui-ux-review
description: Use when you need to review game UI, HUD, menus, feedback, onboarding, readability, and control feel.
---

# Game UI/UX Review

## Purpose
Audit the player-facing interface of a game: HUD clarity and information density, menu navigation flow, juice (feedback responsiveness and animation), onboarding and the first-session experience, input-prompt accuracy across devices, and pause/settings behavior. Identify what makes the game feel unresponsive, confusing, or visually cluttered, and return concrete UX fixes ranked by impact-before-launch. Every finding names the screen or element, a severity, and the fix.

## When to use
- Playtesters report a confusing HUD, hard-to-navigate menus, or unresponsive controls.
- A first-session onboarding flow is being designed or revised.
- UI is being ported between input modalities (controller to touch, mouse to controller).
- The game nears release and needs a final UX pass before submission.
- An accessibility review is needed (colorblind support, subtitles, safe-area, full gamepad navigation) ahead of platform certification.

## When not to use
- The issue is purely rendering performance (low frame rate) — use game-performance-review.
- The issue is a gameplay mechanic bug — use gameplay-systems-review.
- The question is about the underlying UI-framework architecture — use game-architecture-review.

## Procedure
1. **Map the full menu and screen flow.** Diagram every reachable screen from the main menu. Flag dead ends (no back button), unreachable screens, and any common action requiring more than three button presses.
2. **Review HUD information density.** List every HUD element and its update frequency. Verify health, ammo, and objective are readable at a glance without the eyes leaving the action zone, and that nothing obstructs the play area on 4:3 and 21:9 aspect ratios.
3. **Audit feedback and juice.** For each player action (hit, collect, level up, death) confirm at least a visual response (particle/flash/animation), an audio response, and a haptic response where appropriate. Flag "silent" actions that give no confirmation.
4. **Review input prompts.** Confirm button prompts change when the player switches between keyboard, mouse, and controller, that the glyph matches the connected controller type (Xbox / PlayStation / Switch), and that prompts are localized where button names differ by region.
5. **Review onboarding and tutorial.** Confirm the first three minutes introduce mechanics one at a time, that tutorial prompts dismiss on completion rather than on a timer, and that there is no mandatory unskippable tutorial for returning players.
6. **Review pause and settings.** Pause must always be accessible (never blocked during a stalling cutscene/load). Settings must include separate audio volumes (master/music/SFX), display (resolution, vsync, brightness), and controls (remapping or at least a legend), and must persist across restarts.
7. **Review font readability.** Confirm minimum body text ~24px at 1080p (18px secondary), legible under CRT-filter shaders and at TV distance (3m/10ft), with a contrast ratio of at least 4.5:1 against backgrounds.
8. **Review controller menu navigation.** All elements reachable by D-pad/stick, focus state always visible, and back (B/Circle) returns to the parent screen rather than quitting the game.
9. **Review loading and transition states.** Any load over ~0.5s shows an *animated* indicator (not a static image) so the player knows the game has not frozen.
10. **Review accessibility basics.** Confirm no state is signaled by color alone (add icon/text/pattern), spoken dialogue has subtitles, the HUD respects the platform safe area, and every interaction has a gamepad path — not just a mouse one.
11. **Summarize findings** with severity, affected screen, and a concrete UX fix.

## Concrete checks
- Menu flow: no dead ends; common actions reachable in under three presses.
- HUD: critical info (health, objective) in the peripheral-vision zone; safe on all aspect ratios.
- Juice: every action has visual + audio feedback; no silent interactions.
- Input prompts: update per input device; correct glyphs per controller.
- Tutorial: one mechanic at a time; dismisses on completion, not a timer; skippable for returning players.
- Pause: always accessible; never blocked by game state.
- Settings: audio, display, controls sections; persisted across sessions.
- Font: at least 24px body at 1080p; at least 4.5:1 contrast.
- Controller nav: all elements D-pad reachable; focus always visible; back returns to parent.
- Loading: animated indicator for any load over ~0.5s.
- HUD respects the platform safe area (phone notch, TV overscan), not the full screen rect.
- No state is signaled by color alone; a redundant icon/text/pattern cue is present (colorblind support).
- Spoken dialogue has subtitles available (on by default where the platform requires it).
- Every interaction has a gamepad path; no mouse-only mechanics on console.
- Smallest body font is legible at the target viewing distance and meets the platform minimum.

## Commands
```bash
# Inventory all UI scenes / screens to build the flow map
find . \( -name '*.tscn' -o -name '*.uxml' -o -name '*.prefab' \) | rg -i "ui|menu|hud|screen"

# HUD anchored to absolute pixels instead of a safe zone / anchor preset (drifts on ultrawide)
rg -n "position\s*=\s*Vector2\(|anchoredPosition|rect_position|offset_(left|top|right|bottom)" \
  --type-add 'gd:*.gd' -tgd -tcs | rg -i "hud|health|ammo|bar"

# Input-device detection done only at startup (won't update prompts mid-session)
rg -n "Input\.get_connected_joypads|GetJoystickNames|deviceType|controllerType|last_input_device" \
  --type-add 'gd:*.gd' -tgd -tcs

# Settings written only on quit (lost on crash) instead of on change
rg -n "save_settings|SaveSettings|WritePrefs|PlayerPrefs\.Save" -B 3 --type-add 'gd:*.gd' -tgd -tcs \
  | rg -i "quit|exit|on_close|application"

# Silent actions: feedback hooks present for key events?
rg -n "play_sfx|AudioStreamPlayer|PlayOneShot|emit_particle|hit_flash|rumble|vibrat" \
  --type-add 'gd:*.gd' -tgd -tcs | head

# Hardcoded UI strings (localization + readability concern)
rg -n '"[A-Z][a-z].{4,}"' --type-add 'gd:*.gd' -tgd -tcs | rg -iv "res://|http|debug" | head
```
```bash
# Accessibility + readability hooks
rg -n "font_size|fontSize|FontSize" --type-add 'gd:*.gd' -tgd -tcs | rg -oE "[0-9]+" | sort -n | head  # smallest fonts
rg -n "colorblind|color_blind|subtitle|caption|tts|text_to_speech|aria" -i --type-add 'gd:*.gd' -tgd -tcs
rg -n "safe_area|SafeArea|Screen\.safeArea|margin" --type-add 'gd:*.gd' -tgd -tcs   # notch/TV safe zones

# Controller focus / navigation wiring (keyboardless playability)
rg -n "focus_neighbor|focus_mode|grab_focus|Selectable|navigation|firstSelected" --type-add 'gd:*.gd' -tgd -tcs

# Async scene loading behind a moving indicator (vs synchronous freeze)
rg -n "load_threaded|LoadSceneAsync|progress|loading_screen|Spinner" --type-add 'gd:*.gd' -tgd -tcs
```
```bash
# Settings persistence: written on change vs only on quit
rg -n "save_settings|SaveSettings|store_var|PlayerPrefs\.Set|config\.save" --type-add 'gd:*.gd' -tgd -tcs
rg -n "load_settings|LoadSettings|get_var|PlayerPrefs\.Get" --type-add 'gd:*.gd' -tgd -tcs

# Required settings sections present (audio buses, display, controls)
rg -n "master|music|sfx|volume|resolution|vsync|brightness|remap|rebind" -i --type-add 'gd:*.gd' -tgd -tcs

# Tutorial gating: one-time flag vs forced every run
rg -n "tutorial|first_launch|has_played|onboarding|skip" -i --type-add 'gd:*.gd' -tgd -tcs
```

## Menu flow diagram (text format the report should produce)
```text
MainMenu
 ├─ Play ─────────► SaveSlots ─► Game (pause: Resume / Settings / QuitToMenu)
 ├─ Settings ─────► [Audio][Display][Controls]  (back ► MainMenu)
 ├─ Credits ──────► (back ► MainMenu)
 └─ Quit ─────────► ConfirmDialog ─► exit        # never a one-press quit
```

## Juice audit table (one row per player action)
```md
| action | visual | audio | haptic | verdict |
|--------|--------|-------|--------|---------|
| hit enemy | flash + particle | impact sfx | yes | ok |
| collect coin | sparkle | pickup sfx | no | ok |
| buy (no funds) | none | none | none | SILENT — add rejection cue |
| level up | banner | fanfare | yes | ok |
```

## Common issues & anti-patterns
- **HUD anchor drift on non-16:9.** A health bar pinned to pixel coordinates overlaps gameplay on ultrawide or tablet. Anchor to a safe-zone percentage instead.
- **No feedback on a failed action.** Pressing "buy" while broke does nothing — no sound, shake, or message — so the player thinks the button is broken. Add a rejection cue.
- **Controller prompts showing keyboard icons.** Detecting the input device only at startup leaves WASD glyphs showing after the player picks up a controller. Re-detect on input.
- **Forced tutorial every new game.** A player who dies on run one is dragged through the full tutorial again. Gate it behind a first-launch flag.
- **Settings reset after a crash.** Writing settings only on clean exit restores defaults after a crash. Persist immediately on each change.
- **Back button quits from the first menu.** Pressing B/Circle on the main menu instantly quits with no confirmation. Add a "Quit game?" dialog.
- **Loading bar that does not move.** A static bar that jumps 0%→100% in one frame (synchronous load) looks frozen. Use async loading with real or faked progressive fill.
- **Unskippable opening logos every launch.** Players sit through 90 seconds of logos on every cold start. Allow a skip input from frame one.
- **HUD under the notch / off the TV safe area.** Critical info clipped by a phone notch or overscan. Respect the platform safe area, not the full screen rect.
- **Color-only state signaling.** Health shown only by red/green with no shape or number fails for colorblind players. Add a redundant cue (icon, text, pattern).
- **Tiny text on a TV.** 12px body text is unreadable at 10ft. Scale type to the viewing distance and never go below the platform's minimum.
- **No subtitles for spoken dialogue.** Story beats are inaccessible to deaf/HoH players and anyone playing muted. Provide subtitles, on by default where mandated.
- **Mouse-only interactions.** A drag-to-reorder that has no controller equivalent locks out console players. Every interaction needs a gamepad path.

## Required output
Return a structured report with:
1. A text-based menu-flow diagram showing all reachable screens.
2. Findings table: `Screen/Element | Severity | Issue | Fix`.
3. A juice audit: list of actions with missing feedback.
4. The top three most impactful UX improvements before launch.

## Safety
- Do not modify UI scene files, localizations, or asset atlases without explicit instruction.
- Do not trigger builds or editor commands.
- Do not access or reproduce player save data or analytics.
- Read-only review: describe the fix; do not apply it unprompted.
- Do not delete or overwrite localization files while flagging hardcoded strings; report them for translation.
- Treat a one-press quit-without-confirmation and missing pause access as high-severity, not cosmetic.

## Completion criteria
Done means the menu flow is mapped, HUD/juice/prompts/onboarding/pause/settings/font/controller-nav/loading are each assessed from evidence, every finding has a screen, severity, and fix, the silent-action audit is complete, and the top three pre-launch improvements are named.

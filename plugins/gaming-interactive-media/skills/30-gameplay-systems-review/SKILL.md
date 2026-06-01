---
name: gameplay-systems-review
description: Use when you need to review gameplay mechanics, rules, physics, input, balancing, and progression.
---

# Gameplay Systems Review

## Purpose
Review the implementation and design of a game's core gameplay systems: mechanic rules, input handling, collision and physics interactions, finite state machines, balance parameters, progression curves, and determinism for networked or replay scenarios. Surface the bugs, balance outliers, and design fragility that compound over a project's life — stuck states, multi-hit damage in one frame, frame-rate-dependent feel, magic-number balance drift, and non-deterministic physics that desyncs multiplayer. Each finding names the affected mechanic, a severity, and a concrete fix.

## When to use
- A mechanic feels wrong and the team suspects a code-level cause (input lag, inconsistent collision, wrong state transitions).
- A balancing pass is needed on numbers (damage, cooldowns, economy, XP curves).
- The game uses networking or replays and determinism must be verified.
- A new mechanic is being added and the existing state machine needs impact analysis.
- Input handling is being refactored (new input system, controller support, mobile touch).

## When not to use
- The issue is purely visual (particles, shaders, animation blending) — use game-ui-ux-review or game-performance-review.
- The issue is an engine build/import failure — use godot-unity-unreal-triage.
- Architecture is the primary concern, not specific mechanic behavior — use game-architecture-review.

## Procedure
1. **Identify core mechanics and scope.** List the primary loops (movement, combat, puzzle, economy) and note which are in scope.
2. **Review input handling.** Confirm input is read at the correct lifecycle point (`_input`/`_unhandled_input` for discrete actions in Godot; `Input.GetButtonDown` in `Update` for Unity), not somewhere that drops single-frame presses. Verify input buffering (queue an action for ~1–3 frames / 80–100ms) so jumps and attacks are not lost on a low frame. Confirm controller and touch are handled equivalently.
3. **Review finite state machines.** Locate the FSM (enum switch, state objects, AnimationTree, Animator). Verify every state has an explicit entry, exit, and transition condition, and that no state can trap the entity (e.g. an "attacking" state with no death transition).
4. **Review collision and physics interactions.** Confirm collision layers are correct (player projectiles do not hit the player; enemy projectiles do not hit enemies). Check for tunneling — fast objects need continuous collision detection or a swept test. Verify trigger/overlap callbacks are not doing heavy per-frame work.
5. **Review physics determinism.** For networked or replay games, confirm physics uses a fixed timestep and avoids platform-variant floating point. Flag `Random.Range` or wall-clock `Time.time` inside physics that break determinism.
6. **Review balance parameters.** Identify where numbers live (inline magic numbers, a spreadsheet, ScriptableObjects, data tables). Confirm they are not duplicated across files, and flag outliers (one-shot kills at normal difficulty, a 10x difficulty spike at one gate).
7. **Review progression and economy.** Map the curve (XP per level, resource gain). Check for softlock dead ends (resource hits zero with no way to recover) and confirm checkpoints sit *before* difficulty spikes.
8. **Review ability and cooldown systems.** Cooldowns must use scaled game time (`Time.time`), so pause and slow-motion affect them. Flag undesigned interactions (stacking cooldown reductions to zero, infinite combo loops).
9. **Review damage and health.** Verify invincibility frames after a hit prevent multi-hit damage in a single frame, and that death is one explicit state transition, not a flag checked across many systems.
10. **Summarize findings** with severity, affected mechanic, and a concrete fix.

## Concrete checks
- Input: read at the correct lifecycle point; actions buffered ~1–3 frames.
- State machine: every state has entry/exit/transitions; no stuck states.
- Collision layers: no self-team hits; no missing layer assignments.
- Physics: CCD enabled for fast projectiles; no heavy work in overlap callbacks.
- Determinism: no `Random`/wall-clock time in physics when networked or replay is required.
- Balance numbers: in data assets, not inline; no 10x difficulty spikes.
- Progression: no softlock dead ends; checkpoints before difficulty spikes.
- Cooldowns: tracked in scaled game time; affected by pause and time-scale.
- I-frames: an invincibility window after a hit prevents multi-frame damage stacking.
- Death: handled as one explicit state transition, not a scattered flag.
- Damage is gated per contact (i-frames or contact cooldown), not applied every physics frame of overlap.
- Overlap/trigger callbacks are lightweight; no per-contact heavy queries or allocation.
- Random number generation is seeded from a shared recorded value when replay/netplay determinism is required.

## Commands
```bash
# Input read in the wrong place (polling discrete presses in _process)
rg -n "_process\(" -A 20 --type-add 'gd:*.gd' -tgd | rg "is_action_just_pressed|GetButtonDown"

# Missing input buffer (no queued/buffered input variable anywhere)
rg -n "input_buffer|buffered|jumpBuffer|coyote" --type-add 'gd:*.gd' -tgd -tcs || echo "no input buffering found"

# Non-determinism inside physics code (breaks netplay/replay)
rg -n "_physics_process|FixedUpdate" -A 30 --type-add 'gd:*.gd' -tgd -tcs \
  | rg -i "randf|randi|Random\.|DateTime\.Now|Time\.time\b|System\.currentTime"

# Magic-number balance values inline across many files
rg -n "health\s*-?=\s*[0-9]+|damage\s*=\s*[0-9]+|cooldown\s*=\s*[0-9.]+" --type-add 'gd:*.gd' -tgd -tcs

# Cooldowns using real time instead of scaled game time
rg -n "cooldown|cd_timer" -A 3 --type-add 'gd:*.gd' -tgd -tcs | rg -i "DateTime\.Now|Stopwatch|realtime"

# State machine: find states and check each has transitions
rg -n "enum.*State|state\s*=\s*State\.|ChangeState\(|set_state\(" --type-add 'gd:*.gd' -tgd -tcs

# Collision layer configuration
rg -n "collision_layer|collision_mask|layer =|excludeLayers|LayerMask" --type-add 'gd:*.gd' -tgd -tcs

# Continuous collision detection on fast projectiles (tunneling guard)
rg -n "continuous_cd|ContinuousDetectionMode|collisionDetectionMode|Continuous" --type-add 'gd:*.gd' -tgd -tcs \
  || echo "no CCD configured — check fast-moving objects for tunneling"

# I-frames / invincibility implementation
rg -n "invincib|invuln|i_frame|iframe|immune" -i --type-add 'gd:*.gd' -tgd -tcs

# Heavy work inside overlap/trigger callbacks (per-contact cost)
rg -n "_on_.*body_entered|OnTriggerEnter|OnCollisionEnter|area_entered" -A 10 --type-add 'gd:*.gd' -tgd -tcs \
  | rg -i "for |while |findall|GetComponents|instantiate"
```
```bash
# Balance numbers: inline magic values vs centralized data
rg -n "(damage|health|speed|cooldown|cost|xp)\s*[:=]\s*[0-9.]+" -i --type-add 'gd:*.gd' -tgd -tcs | wc -l
find . \( -name '*.tres' -o -name '*.json' -o -name '*ScriptableObject*' \) | rg -i "balance|stats|tuning|config"

# Progression softlock: resources that can hit zero with no recovery path
rg -n "(energy|stamina|currency|resource)\s*-=|spend\(|consume\(" -i --type-add 'gd:*.gd' -tgd -tcs

# Checkpoint placement relative to difficulty
rg -n "checkpoint|save_point|respawn|set_respawn" -i --type-add 'gd:*.gd' -tgd -tcs

# Cooldowns: scaled game time vs wall-clock
rg -n "Time\.time\b|get_ticks_msec|delta" --type-add 'gd:*.gd' -tgd -tcs | rg -i "cool|cd_|timer"
```

## Correct vs incorrect patterns
```gdscript
# WRONG: frame-rate-dependent movement
func _process(_d): position.x += speed                 # 2x faster at 120fps

# RIGHT: scale by delta (or run it in _physics_process at a fixed step)
func _physics_process(delta): position.x += speed * delta

# WRONG: cooldown on wall-clock time (ignores pause / slow-mo)
if Time.get_unix_time_from_system() - last_cast > cooldown: cast()
# RIGHT: scaled game time
cd_timer = max(0.0, cd_timer - delta); if cd_timer == 0.0 and want_cast: cast()
```

## FSM transition completeness (every state needs these exits)
| State | Must transition to | Common missing exit |
|-------|--------------------|---------------------|
| idle | run, jump, attack, **death** | death (player dies while idle) |
| attack | idle, **hit**, **death** | interrupt on taking damage |
| jump | fall, land, **death** | death mid-air |
| hit | idle, **death** | stun-lock with no recovery |

## Common issues & anti-patterns
- **Input in `_process` instead of `_input`.** Reading `is_action_just_pressed` in `_process` can miss single-frame presses on a low frame rate. Use `_input(event)`/`_unhandled_input(event)` for discrete actions.
- **No input buffer for jump/attack.** A 16ms press window feels broken. Buffer the input ~80–100ms so the action fires on the next valid frame.
- **Magic-number damage values.** `health -= 47` inline in a dozen scripts means one balance pass is a dozen edits and easy drift. Move numbers to a data asset.
- **Floating-point physics in multiplayer.** IEEE-754 single precision is non-deterministic across ARM and x86, so two clients diverge. Use a fixed-point / deterministic physics package for the authoritative simulation.
- **Idle state missing death transition.** If death is only wired from "run"/"attack" and the player dies while idle, the death animation never plays and the entity locks up.
- **Cooldown tracked in real time.** Pausing with `Time.timeScale = 0` still drains a `DateTime.Now`-based cooldown. Use scaled `Time.time`.
- **I-frames on a wall-clock timer.** A 0.5s real-time invincibility stretches or shrinks with frame-rate drops. Tie i-frames to animation frames or an explicit scaled-game-time window.
- **Heavy work in an overlap callback.** Running a `GetComponentsInChildren` or a nested loop on every `body_entered` spikes the frame when many contacts happen at once. Cache references and keep the callback light.
- **Tunneling on fast projectiles.** A bullet moving farther than its collider width per frame passes through walls. Enable continuous collision detection or a swept raycast.
- **Damage applied every physics frame of contact.** A spike that overlaps for 10 frames deals 10x damage. Gate damage behind i-frames or a per-contact cooldown.
- **Random seeded from wall-clock.** `seed(time)` makes replays and netplay diverge. Seed from a shared, recorded value for deterministic runs.

## Required output
Return a structured report with:
1. Mechanics scope summary (which systems were reviewed).
2. Findings table: `System | Severity | Bug or Design Issue | Fix`.
3. Balance summary: identified outliers and suggested parameter ranges.
4. Determinism verdict: safe / unsafe for networking and replays, with evidence.

## Safety
- Do not modify game data files, save files, or balance spreadsheets without explicit instruction.
- Do not trigger playtests, builds, or editor commands.
- Flag any cheat or exploit discovered without reproducing or publishing it.
- Read-only review: report the fix; do not apply it unprompted.
- Do not change tuning numbers to "test a feel"; recommend ranges and let the designer apply them.
- Treat a determinism break in netcode-critical physics as blocking, not a minor note.

## Completion criteria
Done means the in-scope mechanics are reviewed from evidence, input/FSM/collision/determinism/balance/progression/cooldown/i-frame/death checks are each confirmed or reported with a fix, balance outliers are listed with suggested ranges, and a determinism verdict for networking/replay is recorded.

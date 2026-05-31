---
name: gameplay-systems-review
description: Use when you need to review gameplay mechanics, rules, physics, input, balancing, and progression.
---

# Gameplay Systems Review

## Purpose

Review the implementation and design of a game's core gameplay systems: mechanic rules, input handling, collision and physics interactions, finite state machines, balance parameters, progression curves, and determinism for networked or replay scenarios. Surface bugs, balance problems, and design fragility before they compound.

## When to use

- A gameplay mechanic feels wrong and the team suspects a code-level cause (lag, inconsistent collision, wrong state transitions).
- A balancing pass is needed on numbers (damage, cooldowns, economy, progression XP curves).
- The game uses networking or replays and determinism needs to be verified.
- A new mechanic is being added and the existing state machine needs impact analysis.
- Player input handling is being refactored (new input system, controller support, mobile touch).

## When not to use

- The issue is purely visual (particles, shaders, animation blending) — use game-ui-ux-review or game-performance-review.
- The issue is engine-level build or import failure — use godot-unity-unreal-triage.
- The architecture is the primary concern, not specific mechanic behavior — use game-architecture-review.

## Procedure

1. **Identify core mechanics and scope.** List the primary gameplay loops (movement, combat, puzzle, economy). Note which systems are in scope for this review.
2. **Review input handling.** Confirm input is read in `_input`/`Input.GetButtonDown` at the correct lifecycle point (not in `_process` when `_input` is available). Check for input buffering — attacks and jumps should queue inputs for 1-3 frames to avoid missed presses on low frame rate. Verify controller and touch inputs are handled equivalently.
3. **Review finite state machines.** Locate FSM implementation (enum switch, state objects, Godot AnimationTree, Unity Animator). Verify every state has an explicit entry, exit, and transition condition. Check for missing transitions that leave the entity stuck in an invalid state (e.g., "attacking" state with no death transition).
4. **Review collision and physics interactions.** Confirm collision layers are configured correctly — player projectiles should not hit player, enemy projectiles should not hit enemies. Check for tunneling: fast-moving objects must use continuous collision detection or swept AABB. Verify trigger/overlap callbacks are not doing heavy computation per frame.
5. **Review physics determinism.** If the game uses networking or replays, confirm that all physics calculations use fixed-point math or a fixed timestep with no floating-point variance between platforms. Flag `Random.Range` or `Time.time` calls inside physics code that break determinism.
6. **Review balance parameters.** Identify where balance numbers live (inline magic numbers, balance spreadsheet, ScriptableObjects, data tables). Confirm they are not hardcoded in multiple places. Check for obvious balance outliers: one-shot kills at normal difficulty, progression gates with a 10x difficulty spike.
7. **Review progression and economy.** Map the progression curve (XP per level, resource gain rates). Check for progression dead ends where a player can be softlocked (resource goes to zero, no way to earn more). Verify save checkpoints are placed before difficulty spikes, not after.
8. **Review ability and cooldown systems.** Confirm cooldowns are tracked in game time, not wall-clock time, so pause and slow-motion affect them correctly. Check for ability interactions that were not designed (stacking cooldown reductions to zero, infinite combo loops).
9. **Review damage and health systems.** Verify invincibility frames (i-frames) are implemented on hit to prevent multi-hit damage in a single frame. Confirm death is handled as a state transition, not a flag check scattered across multiple systems.
10. **Summarize findings** with severity, affected mechanic, and a concrete fix.

## Checklist

- [ ] Input: read at correct lifecycle point, input buffering for actions (1-3 frames)
- [ ] State machine: all states have entry/exit/transitions, no stuck states
- [ ] Collision layers: no self-team hits, no missing layer assignments
- [ ] Physics: CCD enabled for fast projectiles, no heavy work in overlap callbacks
- [ ] Determinism: no Random/Time in physics if networked/replay required
- [ ] Balance numbers: in data assets not inline, no 10x difficulty spikes
- [ ] Progression: no softlock dead ends, checkpoints before difficulty spikes
- [ ] Cooldowns: tracked in game time, affected by pause and time-scale
- [ ] I-frames: invincibility period after hit prevents multi-frame damage stacking
- [ ] Death: handled as explicit state transition, not a flag scattered across systems

## Common issues & anti-patterns

- **Input in `_process` instead of `_input`**: reading `Input.is_action_just_pressed` in `_process` can miss single-frame presses at low frame rates. Use `_input(event)` or `_unhandled_input(event)` for discrete actions.
- **No input buffer for jump/attack**: a 16ms window for a jump press is too tight. Buffer the input for 80-100ms to make the game feel responsive.
- **Magic number damage values**: `health -= 47` inline in 12 different scripts. One balance pass requires 12 file edits and easy drift between intended and actual values.
- **Floating-point physics in multiplayer**: `Vector3` operations in C# use IEEE 754 single precision which is non-deterministic across ARM and x86. Use fixed-point libraries (e.g., deterministic physics package) for authoritative simulation.
- **Idle state missing death transition**: if the player dies while in the "idle" state and the death transition is only on "run", "attack", etc., the death animation never plays.
- **Cooldown tracked in real time**: pausing the game with `Time.timeScale = 0` still drains real-time cooldowns if they use `DateTime.Now`. Use `Time.time` (scaled) instead.
- **Invincibility frames on timer not on animation**: tying i-frames to a 0.5-second timer means a frame-rate drop can extend or shorten them. Tie to animation frames or an explicit game-time window.

## Required output

Return a structured report with:
1. Mechanics scope summary (which systems were reviewed).
2. Findings table: System | Severity | Bug or Design Issue | Fix.
3. Balance summary: identified outliers and suggested parameter ranges.
4. Determinism verdict: safe / unsafe for networking and replays (with evidence).

## Safety

- Do not modify game data files, save files, or balance spreadsheets without explicit user instruction.
- Do not trigger playtests, builds, or editor commands.
- Flag any cheat or exploit discovered during review without reproducing or publishing it.

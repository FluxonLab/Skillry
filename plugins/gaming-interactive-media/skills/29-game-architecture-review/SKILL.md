---
name: game-architecture-review
description: Use when you need to review game architecture, loop structure, scenes, entities, assets, input, and state.
---

# Game Architecture Review

## Purpose

Audit a game project's structural decisions: game loop organization, entity/component model, scene management, asset pipeline, save system design, and the separation of update logic from render logic. Surface architectural debt that causes bugs at scale — frame-rate-dependent gameplay, monolithic god-objects, broken save/load, or uncontrolled asset loading stalls.

## When to use

- A game project is growing and the team suspects architectural debt is causing bugs.
- A new feature (multiplayer, new scene type, mod support) is planned and the existing architecture needs an honest assessment first.
- Post-jam cleanup: prototype code is being promoted to a shipping product.
- Engine migration is being considered and the current architecture needs to be documented first.

## When not to use

- The task is a performance profiling session — use game-performance-review instead.
- The question is about a specific gameplay mechanic — use gameplay-systems-review.
- The engine integration is broken at the build level — use godot-unity-unreal-triage first.

## Procedure

1. **Identify engine, language, and project size.** Note engine (Godot 4, Unity 2022+, Unreal 5, custom), primary language (GDScript, C#, C++, Rust), and approximate scene/file count.
2. **Review the game loop.** Locate the main loop entry (`_process`/`_physics_process` in Godot, `Update`/`FixedUpdate` in Unity, `Tick` in Unreal). Verify that physics updates are in a fixed-timestep loop, not frame-rate-dependent. Check for `delta`-scaled movement everywhere in the variable loop.
3. **Review entity/component model.** Identify whether the project uses ECS (DOTS, Flecs, custom), component composition (Godot nodes, Unity components), or inheritance hierarchies. Flag deep inheritance chains (>3 levels) and monolithic entity classes that exceed ~300 lines.
4. **Review scene management.** Check how scenes are loaded and unloaded. Verify that scene transitions do not leave dangling references or leaked singletons. Confirm there is an explicit loading screen or async load barrier for large scenes.
5. **Review the asset pipeline.** Locate how assets are referenced — hardcoded paths, addressables, resource databases. Verify that large assets (audio, textures) are not loaded synchronously on the main thread. Check for asset duplication (same texture imported multiple times under different names).
6. **Review the save/load system.** Confirm save data is versioned. Check that the serialization format handles missing fields gracefully for backward compatibility. Verify save data is not stored in scene files or prefab states that will be overwritten on update.
7. **Review the event/messaging system.** Identify how systems communicate (signals, events, direct function calls, global singletons). Flag tight coupling: a gameplay system that directly calls a UI function is a red flag.
8. **Review singleton and global state usage.** List all autoloads (Godot), `DontDestroyOnLoad` objects (Unity), or global subsystems (Unreal GameInstance). Confirm each singleton has a single, clear responsibility.
9. **Review input handling layer.** Check that input is read in one place and distributed via events or action maps, not polled in every entity's update.
10. **Summarize findings** with severity and a refactoring recommendation for each.

## Checklist

- [ ] Game loop: physics in fixed timestep, variable loop uses delta scaling
- [ ] Entity model: no inheritance chains >3 levels, no god-object >300 lines
- [ ] Scene management: async load for large scenes, no dangling refs after unload
- [ ] Asset pipeline: no synchronous loads on main thread, no duplicate imports
- [ ] Save system: versioned, backward-compatible, not stored in scene/prefab state
- [ ] Messaging: systems communicate via events/signals, not direct cross-system calls
- [ ] Singletons: each has single responsibility, none holding per-frame game state
- [ ] Input: centralized input layer, actions mapped not raw keycodes scattered
- [ ] Update/render separation: render data written once per frame, not mutated mid-render
- [ ] Build targets: no platform-specific code without compile guards

## Common issues & anti-patterns

- **Frame-rate-dependent movement**: `position += speed` without `* delta` causes the game to run 2x faster at 120fps than at 60fps.
- **God scene node**: a single Godot Node or Unity MonoBehaviour that manages game state, UI, audio, and networking simultaneously. Split into dedicated managers.
- **Singleton sprawl**: 15+ autoloads/DontDestroyOnLoad objects each holding cross-cutting state make initialization order fragile and testing impossible.
- **Hardcoded scene paths**: `load("res://scenes/Level3.tscn")` scattered across scripts breaks if the file moves. Use a scene registry or constants file.
- **Save data in scene files**: storing player progress as exported variables on a scene node means any scene update overwrites player data. Save data must be separate from scene state.
- **Direct UI calls from gameplay systems**: `enemy._physics_process` calling `hud.update_health_bar()` directly couples systems and makes unit testing impossible. Use signals or an event bus.
- **Async load without barrier**: starting `ResourceLoader.load_threaded_request` and immediately using the resource before checking `THREAD_LOAD_LOADED` causes null reference crashes.

## Required output

Return a structured report with:
1. Engine, language, and project structure summary.
2. Architecture map: list identified systems and their current coupling.
3. Findings table: System | Severity | Issue | Recommended refactor.
4. Prioritized refactoring roadmap (what to fix first without breaking everything else).

## Safety

- Do not delete or overwrite scene files, prefabs, or assets.
- Do not run editor commands or build scripts.
- Do not modify save data files or player databases.

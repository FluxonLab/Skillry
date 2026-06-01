---
name: game-architecture-review
description: Use when you need to review game architecture, loop structure, scenes, entities, assets, input, and state.
---

# Game Architecture Review

## Purpose
Audit a game project's structural decisions: game-loop organization, the entity/component model, scene management, the asset pipeline, the save system, and the separation of update logic from render logic. Surface the architectural debt that produces bugs at scale — frame-rate-dependent gameplay, monolithic god-objects, broken save/load, asset-loading stalls, and tight coupling between gameplay and UI. Every finding carries a severity and a concrete refactor, ordered so the highest-leverage fix can land without destabilizing the rest.

## When to use
- A game project is growing and the team suspects architectural debt is causing bugs.
- A new feature (multiplayer, a new scene type, mod support) is planned and the existing architecture needs an honest assessment first.
- Post-jam cleanup: prototype code is being promoted to a shipping product.
- An engine migration is being considered and the current architecture must be documented first.

## When not to use
- The task is a performance profiling session — use game-performance-review.
- The question is about one specific gameplay mechanic — use gameplay-systems-review.
- The engine integration is broken at the build/import level — use godot-unity-unreal-triage first.

## Procedure
1. **Identify engine, language, and project size.** Note engine (Godot 4, Unity 2022+, Unreal 5, custom), primary language (GDScript, C#, C++, Rust), and approximate scene/file count.
2. **Review the game loop.** Locate the main loop entry (`_process`/`_physics_process` in Godot, `Update`/`FixedUpdate` in Unity, `Tick` in Unreal). Verify physics runs in a fixed-timestep loop, not the variable frame loop, and that all movement in the variable loop is `delta`-scaled.
3. **Review the entity/component model.** Identify the approach — ECS (DOTS, Flecs, custom), component composition (Godot nodes, Unity components), or inheritance hierarchies. Flag inheritance chains deeper than three levels and monolithic entity classes over ~300 lines.
4. **Review scene management.** Check how scenes load and unload. Verify transitions leave no dangling references or leaked singletons, and that large scenes have an explicit loading screen or async-load barrier.
5. **Review the asset pipeline.** Locate how assets are referenced — hardcoded paths, addressables, a resource database. Verify large assets (audio, textures) are not loaded synchronously on the main thread, and check for the same asset imported multiple times under different names.
6. **Review the save/load system.** Confirm save data is versioned, that deserialization tolerates missing fields for backward compatibility, and that save data is not stored inside scene files or prefab state that an update will overwrite.
7. **Review the event/messaging system.** Identify how systems communicate (signals, events, direct calls, global singletons). A gameplay system calling a UI function directly is a coupling red flag.
8. **Review singleton and global state.** List all autoloads (Godot), `DontDestroyOnLoad` objects (Unity), or global subsystems (Unreal GameInstance). Confirm each has a single, clear responsibility and none holds per-frame game state.
9. **Review the input layer.** Input should be read in one place and distributed via events or an action map, not polled inside every entity's update.
10. **Review initialization order.** Confirm cross-singleton setup uses an explicit init sequence rather than relying on implicit `_ready`/`Awake` ordering, which breaks when the scene tree changes.
11. **Summarize findings** with severity and a refactor recommendation for each.

## Concrete checks
- Game loop: physics in a fixed timestep; the variable loop uses delta scaling everywhere.
- Entity model: no inheritance chains deeper than three levels; no god-object over ~300 lines.
- Scene management: async load for large scenes; no dangling references after unload.
- Asset pipeline: no synchronous loads on the main thread; no duplicate imports.
- Save system: versioned, backward-compatible, and stored separately from scene/prefab state.
- Messaging: systems communicate via events/signals, not direct cross-system calls.
- Singletons: each has a single responsibility; none holds per-frame game state.
- Input: a centralized input layer with mapped actions, not raw keycodes scattered across entities.
- Update/render separation: render data is written once per frame, not mutated mid-render.
- Build targets: no platform-specific code without compile guards.
- Save data carries a version field and old versions are migrated on load.
- Cross-singleton initialization uses an explicit sequence, not implicit node-ready order.
- State changes propagate via signals/events, not per-frame polling of other systems.
- No per-frame object allocation inside the main loop.

## Commands
```bash
# Engine + version (determines which APIs and patterns apply)
godot --version 2>/dev/null
sed -n 's/.*config\/version="\(.*\)"/\1/p' project.godot 2>/dev/null      # Godot project version
rg -n "m_EditorVersion" ProjectSettings/ProjectVersion.txt 2>/dev/null     # Unity
rg -n "EngineAssociation" *.uproject 2>/dev/null                            # Unreal

# Frame-rate-dependent movement: position changes NOT multiplied by delta
rg -n "position\s*[\+\-]?=|translate\(|velocity\s*=" --type-add 'gd:*.gd' -tgd -tcs \
  | rg -v "delta|fixedDeltaTime|GetDeltaSeconds"

# God-objects: scripts over ~300 lines
find . \( -name '*.gd' -o -name '*.cs' -o -name '*.cpp' \) -not -path '*/.*' \
  -exec wc -l {} + | awk '$1 > 300 {print}' | sort -rn

# Deep inheritance / monolithic class signals
rg -n "extends |class .* : .*MonoBehaviour|: public A" --type-add 'gd:*.gd' -tgd -tcs

# Singleton / global-state sprawl
rg -n "^\[autoload\]" project.godot -A 30 2>/dev/null     # Godot autoloads
rg -n "DontDestroyOnLoad" -tcs                            # Unity persistent objects

# Hardcoded scene paths (fragile when files move)
rg -n 'load\("res://|LoadScene\("|SceneManager\.LoadScene' --type-add 'gd:*.gd' -tgd -tcs

# Gameplay reaching directly into UI (tight coupling)
rg -n "_physics_process|Update\(" -A 15 | rg -i "hud|ui\.|menu\.|update.*bar"
```
```bash
# Save data versioning + backward compatibility
rg -n "save_version|saveVersion|schema_version|\"version\"" --type-add 'gd:*.gd' -tgd -tcs
rg -n "ResourceSaver\.save|FileAccess\.open|JsonUtility\.ToJson|BinaryFormatter" --type-add 'gd:*.gd' -tgd -tcs

# Render/update separation: state mutated during draw/render
rg -n "_draw\(|OnRenderObject|OnGUI\(" -A 10 --type-add 'gd:*.gd' -tgd -tcs | rg "=\s*[^=]|\+\+|--"

# Event bus / signal usage (loose coupling) vs direct cross-system calls
rg -n "emit_signal|signal |EventBus|\.Invoke\(|UnityEvent|add_user_signal" --type-add 'gd:*.gd' -tgd -tcs

# Per-frame allocation inside the loop (architecture smell that becomes a perf bug)
rg -n "(_process|Update)\(" -A 15 --type-add 'gd:*.gd' -tgd -tcs | rg "new |Array\(|Dictionary\(|\.instantiate\("
```
```bash
# Module/scene dependency direction (who depends on whom)
rg -n "preload\(|const .* = preload|using .*;|#include" --type-add 'gd:*.gd' -tgd -tcs | head -30

# Scene unload cleanup (queue_free / Destroy paired with disconnects)
rg -n "queue_free\(|Destroy\(|free\(\)" --type-add 'gd:*.gd' -tgd -tcs
rg -n "disconnect\(|RemoveListener|-= " --type-add 'gd:*.gd' -tgd -tcs   # are signals torn down?

# Platform-specific code without a compile guard
rg -n "OS\.get_name\(\)|Application\.platform|#if UNITY_|PLATFORM_" --type-add 'gd:*.gd' -tgd -tcs
```

## Save schema versioning (the backward-compatibility pattern)
```gdscript
# RIGHT: version the payload and migrate old saves on load
const SAVE_VERSION := 3
func load_save(data: Dictionary) -> void:
    var v := int(data.get("version", 1))
    if v < 2: data["currency"] = data.get("gold", 0)   # v1 -> v2 field rename
    if v < 3: data["unlocks"] = data.get("unlocks", []) # v2 -> v3 added field with default
    apply(data)                                          # never assume a field exists
```

## Findings table format
```md
| system        | severity | issue                                   | recommended refactor                 |
|---------------|----------|-----------------------------------------|--------------------------------------|
| game loop     | high     | movement not delta-scaled in _process   | multiply by delta or move to physics |
| Player.gd     | high     | 640-line god-object                      | split movement / inventory / input   |
| save system   | critical | progress stored on the level scene node | move to a versioned save resource    |
| HUD coupling  | medium   | enemy calls hud.update_health_bar()      | emit a "health_changed" signal       |
```

## Common issues & anti-patterns
- **Frame-rate-dependent movement.** `position += speed` without `* delta` runs 2x faster at 120fps than at 60fps. Scale every per-frame change by delta, or move it into the fixed-timestep loop.
- **God scene node.** A single Godot Node or Unity MonoBehaviour managing game state, UI, audio, and networking. Split into dedicated managers with one responsibility each.
- **Singleton sprawl.** 15+ autoloads / `DontDestroyOnLoad` objects holding cross-cutting state make init order fragile and testing impossible. Consolidate and inject dependencies.
- **Hardcoded scene paths.** `load("res://scenes/Level3.tscn")` scattered across scripts breaks when the file moves. Use a scene registry or a constants file.
- **Save data in scene files.** Storing progress as exported variables on a scene node means any scene update overwrites player data. Keep save data separate from scene state.
- **Direct UI calls from gameplay.** `enemy._physics_process` calling `hud.update_health_bar()` couples systems and blocks unit testing. Emit a signal / event-bus message instead.
- **Async load without a barrier.** Starting `ResourceLoader.load_threaded_request` and using the resource before checking `THREAD_LOAD_LOADED` causes null-reference crashes. Gate use on the completion status.
- **Unversioned save data.** A save with no version field cannot be migrated; the next update either crashes on load or silently wipes progress. Stamp a version and migrate on load.
- **State mutated during render.** Changing game state inside `_draw`/`OnGUI` causes tearing and order-dependent bugs. Compute in update, read-only in render.
- **`_ready`/`Awake` order dependence.** Relying on the implicit node-ready order for cross-singleton init breaks the moment the scene tree changes. Use an explicit init sequence.
- **Polling instead of events.** Every entity checking `if player.health != last_health` each frame instead of subscribing to a "health_changed" signal — wasted work and scattered logic.

## Required output
Return a structured report with:
1. Engine, language, and project-structure summary.
2. Architecture map: identified systems and their current coupling.
3. Findings table: `System | Severity | Issue | Recommended refactor`.
4. A prioritized refactoring roadmap — what to fix first without breaking everything else.

## Safety
- Do not delete or overwrite scene files, prefabs, or assets.
- Do not run editor commands or build scripts.
- Do not modify save-data files or player databases.
- Read-only review: report the structural change and its sequencing; do not apply it without explicit instruction.

## Completion criteria
Done means the engine and project layout are documented, the game loop / entity model / scene / asset / save / messaging / singleton / input layers are each assessed from evidence, every finding has a severity and a concrete refactor, and a prioritized roadmap names the first safe change.

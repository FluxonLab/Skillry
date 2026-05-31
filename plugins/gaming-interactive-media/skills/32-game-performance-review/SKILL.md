---
name: game-performance-review
description: Use when you need to review frame budget, asset loading, rendering, memory, and interaction performance.
---

# Game Performance Review

## Purpose

Audit a game's runtime performance against concrete budgets: 16.6ms per frame at 60fps (6.9ms at 144fps), draw call limits, GC spike frequency, texture memory footprint, object pooling correctness, and asset streaming stalls. Produce findings with profiler evidence requirements and prioritized optimization recommendations.

## When to use

- The game drops below target frame rate on any supported platform.
- GC spikes are causing hitches (visible as frame time spikes in profiler).
- Loading screens are too long or asset streaming causes mid-gameplay stalls.
- The game fails platform certification due to memory limits or thermal throttling.
- A performance baseline is needed before a major feature addition.

## When not to use

- The game runs well and the task is a general architecture review — use game-architecture-review.
- The frame drop is caused by a logic bug, not a performance budget issue — use gameplay-systems-review to find the root cause first.
- The issue is a rendering artifact (wrong color, missing geometry) rather than a timing problem.

## Procedure

1. **Establish platform and target.** Note platform (PC/console/mobile/WebGL), target frame rate (30/60/120fps), and target hardware. Calculate per-frame budget: 60fps = 16.6ms total, with typical split of 8ms CPU / 4ms GPU / 4ms render thread.
2. **Locate profiler data or request it.** Ask for Unity Profiler, Godot Profiler, Unreal Insights, or RenderDoc capture if not already provided. If none available, identify the suspected hotspot from code review alone and note that profiler confirmation is required.
3. **Review draw call count.** Identify total draw calls per frame. Mobile budget: <100 draw calls. PC/console: <300 for mid-range. Check for dynamic batching eligibility (same material, no rigidbody). Verify static batching is enabled for non-moving geometry. Flag GPU instancing candidates (same mesh + material, many instances).
4. **Review texture memory.** Identify texture atlases and compression formats. Mobile requires ETC2 (Android) or ASTC (iOS/modern Android). Desktop needs DXT/BC compression. Check for uncompressed textures in production builds. Verify mipmap generation is enabled for all 3D textures. Flag textures larger than needed for their screen coverage.
5. **Review object pooling.** Identify frequently spawned/destroyed objects (projectiles, particles, enemies). Confirm a pool exists for each. Check that pools pre-warm during loading, not on first spawn. Verify pool size is appropriate — too small causes runtime allocations, too large wastes memory.
6. **Review GC allocation hotspots.** Search for per-frame heap allocations in C#: string concatenation in `Update`, LINQ in hot paths, `GetComponent<T>()` without caching, `new List<T>()` inside loops. In GDScript, watch for per-frame Array/Dictionary construction. Each allocation is a future GC spike.
7. **Review Update loop cost.** Count scripts with `Update`/`_process`. Verify that scripts using `Update` only for a state check (e.g., "is player nearby?") use a coroutine with a wait interval instead. Check for expensive operations in `Update`: `FindObjectsByType`, `GetComponentsInChildren`, physics queries without layer masks.
8. **Review asset loading strategy.** Confirm large assets (audio, textures, levels) are loaded asynchronously. Verify Addressables (Unity) or ResourceLoader.load_threaded_request (Godot) are used with proper completion callbacks. Check for `Resources.Load` in hot paths (synchronous, uncached, deprecated in Unity).
9. **Review particle systems and VFX.** Confirm particle systems have a max particle count cap. Verify unused particle systems are stopped, not left playing off-screen. Check for particles using uncompressed textures.
10. **Review audio CPU cost.** Verify audio sources are not creating new `AudioStreamPlayer` instances per sound effect. Confirm audio buses are used for compression and limiting. Check sample rate — 44100 Hz for music, 22050 Hz acceptable for SFX on mobile.
11. **Summarize findings** with estimated frame time saved and implementation effort per fix.

## Checklist

- [ ] Frame budget established: target fps, CPU/GPU split defined
- [ ] Draw calls: within platform budget, batching and instancing evaluated
- [ ] Texture compression: platform-appropriate format, mipmaps enabled, no oversized textures
- [ ] Object pooling: pools for projectiles/particles/enemies, pre-warmed, correct size
- [ ] GC: no per-frame heap allocations in C# hot paths (strings, LINQ, new collections)
- [ ] Update loop: no FindObjects/GetComponentsInChildren per frame, expensive checks use coroutines
- [ ] Asset loading: async load with callbacks, no Resources.Load in hot paths
- [ ] Particles: max count capped, stopped when off-screen, compressed textures
- [ ] Audio: pooled players, correct sample rates, audio buses configured
- [ ] Mobile thermal: sustained load does not trigger CPU throttling after 5 minutes

## Common issues & anti-patterns

- **String concatenation in Update**: `Debug.Log("Player pos: " + transform.position)` every frame allocates a new string. Remove in release builds with `#if UNITY_EDITOR` or conditional compilation.
- **LINQ in hot paths**: `enemies.Where(e => e.IsAlive).FirstOrDefault()` allocates an iterator. Replace with a manual `foreach` loop and early return.
- **No GPU instancing on repeated meshes**: a forest of 500 identical trees drawn with 500 draw calls. Enable GPU instancing on the material and batch to 1-5 calls.
- **`GetComponent<T>()` per frame**: calling `GetComponent<Rigidbody>()` in `Update` instead of caching in `Awake` adds overhead that is invisible in isolation but significant at 1000 entities.
- **Particle system without max count**: an explosion particle system with no max particle count cap. One frame of many explosions simultaneously exhausts particle budget and causes a 100ms spike.
- **Synchronous scene load on main thread**: `SceneManager.LoadScene("Level2")` blocks the main thread for the full load duration. Use `LoadSceneAsync` with a loading screen.
- **Oversized audio clips in memory**: loading a 5-minute music track as `Decompress on Load` allocates the full PCM buffer (5 min × 44100 Hz × 2 channels × 4 bytes = ~210 MB). Use `Streaming` for music.
- **Update on idle NPCs**: 200 NPCs in a large level all running `Update` every frame, even when 180 of them are 500m from the player. Use distance-based LOD to disable Update on far entities.

## Required output

Return a structured report with:
1. Platform, target fps, and per-frame budget breakdown.
2. Findings table: System | Estimated Cost | Severity | Issue | Fix | Profiler metric to verify.
3. Quick wins (< 1 hour each) vs. structural changes (> 1 day each) separated.
4. Profiler evidence checklist: what to capture to confirm each finding.

## Safety

- Do not delete assets, textures, or audio files.
- Do not modify project settings (quality levels, graphics tiers) without listing all changes for user review.
- Do not trigger builds, profiling sessions, or device deployments.

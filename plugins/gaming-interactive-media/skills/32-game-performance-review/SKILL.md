---
name: game-performance-review
description: Use when you need to review frame budget, asset loading, rendering, memory, and interaction performance.
---

# Game Performance Review

## Purpose
Audit a game's runtime performance against concrete budgets: 16.6ms per frame at 60fps (6.9ms at 144fps), platform draw-call limits, GC-spike frequency, texture-memory footprint, object-pooling correctness, and asset-streaming stalls. Produce findings that name the system, the estimated frame-time cost, the fix, and the profiler metric required to confirm it — separating sub-hour quick wins from multi-day structural changes so the team can act in priority order.

## When to use
- The game drops below its target frame rate on any supported platform.
- GC spikes cause hitches (visible as frame-time spikes in the profiler).
- Loading screens are too long or asset streaming stalls mid-gameplay.
- The game fails platform certification on memory limits or thermal throttling.
- A performance baseline is needed before a major feature addition.

## When not to use
- The game runs well and the task is a general architecture review — use game-architecture-review.
- The frame drop is caused by a logic bug, not a budget issue — use gameplay-systems-review to find the root cause first.
- The issue is a rendering artifact (wrong color, missing geometry), not a timing problem.

## Procedure
1. **Establish platform and target.** Note platform (PC/console/mobile/WebGL), target frame rate (30/60/120fps), and target hardware. Compute the per-frame budget: 60fps = 16.6ms, with a typical split of ~8ms CPU / ~4ms GPU / ~4ms render thread.
2. **Locate profiler data or request it.** Ask for a Unity Profiler, Godot profiler, Unreal Insights, or RenderDoc capture. With none available, identify the suspected hotspot from code and note that a profiler capture is required to confirm.
3. **Review draw-call count.** Identify total draw calls per frame. Mobile budget under ~100; mid-range PC/console under ~300. Check dynamic-batching eligibility (same material, no rigidbody), confirm static batching for non-moving geometry, and flag GPU-instancing candidates (same mesh + material, many instances).
4. **Review texture memory.** Identify atlases and compression formats. Mobile needs ETC2 (Android) or ASTC; desktop needs DXT/BC. Flag uncompressed textures in production builds, confirm mipmaps for all 3D textures, and flag textures larger than their on-screen coverage warrants.
5. **Review object pooling.** Identify frequently spawned/destroyed objects (projectiles, particles, enemies). Confirm a pool exists for each, that pools pre-warm during loading (not on first spawn), and that pool size avoids both runtime allocation (too small) and memory waste (too large).
6. **Review GC-allocation hotspots.** Search for per-frame heap allocations: string concatenation in `Update`, LINQ in hot paths, `GetComponent<T>()` without caching, `new List<T>()` in loops (C#); per-frame Array/Dictionary construction (GDScript). Each is a future GC spike.
7. **Review Update-loop cost.** Count scripts with `Update`/`_process`. State-poll-only scripts ("is the player near?") should use a timed coroutine instead. Flag expensive per-frame ops: `FindObjectsByType`, `GetComponentsInChildren`, physics queries with no layer mask.
8. **Review asset loading.** Confirm large assets load asynchronously (Addressables, `ResourceLoader.load_threaded_request`) with completion callbacks. Flag `Resources.Load` in hot paths (synchronous, uncached).
9. **Review particles and VFX.** Confirm a max particle-count cap, that off-screen systems are stopped (not left playing), and that particles do not use uncompressed textures.
10. **Review audio CPU cost.** Verify SFX reuse pooled players rather than instantiating per sound, that audio buses handle compression/limiting, and that sample rates are sane (44100Hz music, 22050Hz acceptable mobile SFX).
11. **Review overdraw and shadows.** Check for stacked full-screen transparent layers (mobile GPU killer) and real-time shadow casting on minor props, both common GPU-bound causes.
12. **Summarize findings** with estimated frame time saved and implementation effort per fix, noting that any number not from a target-hardware player build is a hypothesis.

## Concrete checks
- Frame budget established: target fps and CPU/GPU split defined.
- Draw calls within platform budget; batching and instancing evaluated.
- Texture compression platform-appropriate; mipmaps on; no oversized textures.
- Object pools for projectiles/particles/enemies; pre-warmed; correctly sized.
- No per-frame heap allocations in C# hot paths (strings, LINQ, new collections).
- Update loop free of `FindObjects`/`GetComponentsInChildren` per frame; polls use coroutines.
- Asset loading async with callbacks; no `Resources.Load` in hot paths.
- Particles capped, stopped off-screen, compressed textures.
- Audio uses pooled players, correct sample rates, configured buses.
- Mobile thermal: sustained load does not trigger CPU throttling after ~5 minutes.
- Overdraw is bounded: no stack of full-screen transparent layers redrawing every pixel.
- Physics tick rate matches gameplay need, not an arbitrarily high default.
- Shadow casting is limited to objects that need it, not every prop.
- Assets load per-level and release on unload, not all preloaded at boot.
- All cost numbers come from a development player build on target hardware, not the editor.

## Commands
```bash
# Per-frame string allocation (GC spikes) in Update/_process
rg -n "(Update|_process)\(" -A 25 --type-add 'gd:*.gd' -tgd -tcs \
  | rg '"\s*\+|\+\s*"|\$"|str\(|String\.Format'

# LINQ and new-collection allocations in hot paths (C#)
rg -n "(Update|FixedUpdate)\(" -A 25 -tcs | rg "\.Where\(|\.Select\(|\.FirstOrDefault\(|new List<|new Dictionary<"

# Uncached GetComponent / expensive lookups called every frame
rg -n "(Update|FixedUpdate)\(" -A 25 -tcs | rg "GetComponent|FindObjectsByType|GetComponentsInChildren|GameObject\.Find"

# Synchronous resource loads (block the main thread)
rg -n "Resources\.Load|ResourceLoader\.load\(|preload\(|GD\.load\(" --type-add 'gd:*.gd' -tgd -tcs

# Async load WITHOUT a completion-status check (crash / stall risk)
rg -n "load_threaded_request|LoadSceneAsync|InstantiateAsync" -A 8 --type-add 'gd:*.gd' -tgd -tcs \
  | rg -v "load_threaded_get_status|isDone|completed|THREAD_LOAD_LOADED"

# Particle systems and whether a max-count cap exists
rg -n "GPUParticles|CPUParticles|ParticleSystem|amount\s*=|maxParticles" --type-add 'gd:*.gd' -tgd -tcs

# Texture import settings — spot uncompressed / oversized assets
rg -n "compress|Compression|textureFormat|mipmaps|max_size" -i $(find . -name '*.import' -o -name '*.meta') 2>/dev/null | head
```
```bash
# Largest texture/audio assets on disk (over-budget candidates)
find . \( -name '*.png' -o -name '*.tga' -o -name '*.wav' \) -exec du -h {} + | sort -rh | head -15

# Audio import mode: Decompress-on-Load (RAM heavy) vs Streaming for long clips
rg -n "loadType|Decompress|Streaming|StreamingAssets|loadInBackground" -i $(find . -name '*.meta') 2>/dev/null | head

# Scripts with an Update/_process that could be event-driven instead
rg -l "(void Update\(\)|func _process\()" --type-add 'gd:*.gd' -tgd -tcs | wc -l

# Engine profiler / capture entry points (request a capture if missing)
godot --headless --print-fps 2>/dev/null | tail -5      # quick frame-time sample
# Unity: open Window > Analysis > Profiler ; capture a 'Player' build, not the editor
# Unreal: 'stat unit', 'stat gpu', and Unreal Insights trace for frame breakdown
```
```bash
# Overdraw / transparency layers (GPU-bound on mobile)
rg -n "transparent|blend_mode|alpha|CanvasLayer|Overlay|fog" -i --type-add 'gd:*.gd' -tgd -tcs | head

# Shadow casting on minor objects
rg -n "shadow|cast_shadow|ShadowCastingMode|ReceiveShadows" -i --type-add 'gd:*.gd' -tgd -tcs | head

# Physics tick rate vs need
rg -n "physics_ticks_per_second|fixedDeltaTime|Time\.fixedDeltaTime|MaxPhysicsDelta" --type-add 'gd:*.gd' -tgd -tcs project.godot 2>/dev/null

# Preload-everything-at-boot vs per-level load
rg -n "preload\(|Resources\.LoadAll|LoadAll<|AddressableAssets" --type-add 'gd:*.gd' -tgd -tcs | wc -l
```

## Per-frame budget (where the time goes)
| Target | Total frame | Typical CPU / GPU / render split |
|--------|-------------|----------------------------------|
| 30 fps | 33.3 ms | 16 / 10 / 7 |
| 60 fps | 16.6 ms | 8 / 4 / 4 |
| 120 fps | 8.3 ms | 4 / 2 / 2 |
| 144 fps | 6.9 ms | 3.5 / 1.7 / 1.7 |

## Platform budgets (rules of thumb)
| Resource | Mobile | Mid PC/console | Note |
|----------|--------|----------------|------|
| Draw calls / frame | < 100 | < 300 | batch + instance to reduce |
| Texture compression | ASTC / ETC2 | BC/DXT | never ship uncompressed |
| Triangles visible | 100–300k | 1–3M | LOD distant meshes |
| Audio voices | 16–24 | 32–64 | pool players, cap concurrency |

## Common issues & anti-patterns
- **String concatenation in Update.** `Debug.Log("pos: " + transform.position)` every frame allocates a string. Strip it from release with conditional compilation.
- **LINQ in hot paths.** `enemies.Where(e => e.IsAlive).FirstOrDefault()` allocates an iterator each call. Replace with a manual `foreach` and early return.
- **No GPU instancing on repeated meshes.** A forest of 500 identical trees drawn with 500 calls. Enable instancing on the material to collapse it to a handful.
- **`GetComponent<T>()` per frame.** Calling it in `Update` instead of caching in `Awake` is invisible at one entity and crushing at a thousand.
- **Particle system with no max count.** One frame of many simultaneous explosions exhausts the particle budget and spikes 100ms. Cap the count.
- **Synchronous scene load on the main thread.** `SceneManager.LoadScene` blocks for the full load. Use `LoadSceneAsync` behind a loading screen.
- **Oversized audio in memory.** A 5-minute track set to Decompress-on-Load allocates ~210MB of PCM. Stream music instead.
- **Update on distant idle NPCs.** 200 NPCs all running `Update` when 180 are far from the player. Disable Update by distance-based LOD.
- **Overdraw from full-screen transparent layers.** Stacked alpha-blended UI or fog quads redraw every pixel several times, GPU-bound on mobile. Reduce layers or use opaque where possible.
- **Physics tick too high.** Running fixed physics at 120Hz for a game that only needs 50Hz doubles CPU physics cost for no gain. Match the tick to the gameplay need.
- **Shadow-casting on everything.** Every small prop casting real-time shadows multiplies draw calls. Disable shadow casting on minor objects.
- **Loading all assets up front.** Preloading the whole game into memory at boot blows the mobile memory budget. Load per-level and release on unload.
- **Profiling the editor, not a build.** Editor overhead inflates every number. Always profile a development *player* build on target hardware.

## Required output
Return a structured report with:
1. Platform, target fps, and the per-frame budget breakdown.
2. Findings table: `System | Estimated Cost | Severity | Issue | Fix | Profiler metric to verify`.
3. Quick wins (under ~1 hour each) separated from structural changes (over ~1 day each).
4. A profiler-evidence checklist: what to capture to confirm each finding.

## Safety
- Do not delete assets, textures, or audio files.
- Do not modify project settings (quality levels, graphics tiers) without listing every change for review.
- Do not trigger builds, profiling sessions, or device deployments.
- Treat any cost estimate without a profiler capture as a hypothesis, not a confirmed number.

## Completion criteria
Done means the platform budget is stated, draw calls / textures / pooling / GC / Update / asset-loading / particles / audio are each assessed from evidence, every finding has an estimated cost, a fix, and the profiler metric to confirm it, and quick wins are separated from structural work.

---
name: godot-unity-unreal-triage
description: Use when you need to triage Godot, Unity, Unreal, shader, engine, and asset pipeline issues.
---

# Godot / Unity / Unreal Triage

## Purpose
Diagnose and triage engine-specific issues in Godot 4, Unity (2021 LTS through 6), or Unreal Engine 5: engine-selection questions, language choice (GDScript vs C# vs Blueprint vs C++), shader compilation failures, build-target problems, version-compatibility breaks, import-pipeline errors, and editor crashes. Produce a concrete diagnosis with exact API names, file paths, or setting locations and a verification step — not a generic "check the docs" response.

## When to use
- A Unity/Godot/Unreal project fails to import, compile, or build and the error needs diagnosis.
- A shader compiles in the editor but fails on device (WebGL, mobile GLES, Vulkan).
- An engine version upgrade broke existing code or assets and a migration path is needed.
- Engine selection is being decided for a new project and a structured comparison is needed.
- A Blueprint vs C# vs GDScript performance question needs an evidence-based answer.
- A C# script will not run in Godot, or a `.csproj`/`.sln` fails to restore, and the .NET toolchain needs verifying.
- A third-party plugin or `.gdextension` is suspected of blocking an engine upgrade.

## When not to use
- The issue is a gameplay bug unrelated to the engine — use gameplay-systems-review.
- The issue is a frame-rate problem — use game-performance-review (after confirming the engine layer is not the bottleneck).
- The codebase is a web/mobile app using an engine only as a renderer (e.g. Three.js) — out of scope.
- The fix would require regenerating signing credentials or store certificates — surface that for the owner; do not generate them here.
- The problem is purely a gameplay-tuning question with no engine error involved — use gameplay-systems-review.

## Procedure
1. **Identify engine, version, and target platform.** Record the exact version (Godot 4.3.stable, Unity 2022.3.42f1, Unreal 5.4.4) and target (Windows, macOS, Android, iOS, WebGL, consoles). The version-plus-platform combination determines which bugs and shader variants are in scope.
2. **Classify the issue:** import error, compile error, runtime crash, shader failure, build failure, version-migration break, or engine-selection question. The class determines which of the steps below apply and which log to capture.
3. **Capture the failing log before theorizing.** A compile error number (`CS0246`), a shader-compiler line, or a cook/build failure line points at the cause far faster than reading source. Attach it to the diagnosis.
4. **Import errors:** check file-format compatibility with the engine version. Unity: verify `.meta` files are present and uncorrupted. Godot: check `.import` files and whether the asset type matches the importer (a `.glb` imported as scene vs mesh). Unreal: check the content-folder structure and whether the asset came from a newer engine version.
5. **Compile errors:** locate the layer (engine C# API, GDScript, Blueprint, native C++). Check for API breaks in the target version (Godot renamed `KinematicBody`→`CharacterBody3D` in 4.0; Unreal changed `AActor::Tick` override patterns in 5.x). Cross-reference the error against the engine's upgrade guide.
6. **Shader failures:** determine the render pipeline (Unity Built-in/URP/HDRP; Godot Forward+/Mobile/Compatibility; Unreal Deferred/Forward). Shader code is not portable across pipelines. Check WebGL limits (no geometry shaders, no compute in WebGL1) and the GLES3 vs Vulkan path on Android.
7. **Build failures:** check platform SDK requirements (Android NDK/JDK, iOS Xcode, WebGL Emscripten), verify signing config is complete, and check for missing/mismatched plugin versions. In Unity, confirm the target platform module is installed in the Hub.
8. **Version-migration breaks:** identify source and target versions, consult the changelog for breaking changes in that range, list affected APIs with their new equivalents, and verify third-party plugin compatibility — the most common migration blocker.
9. **Engine-selection questions:** evaluate target platform (Godot for small/indie, Unreal for AAA visuals, Unity for mobile/XR), team language preference, licensing (Godot MIT, Unity seat-based, Unreal royalty above a revenue threshold), and asset-store availability.
10. **GDScript vs C# vs Blueprint vs C++:** GDScript — fastest iteration in Godot, interpreted, hot-reload. C# in Godot — better performance, strong typing, Mono build. Blueprint — visual, designer-friendly, bytecode (roughly 10x slower than C++ in CPU-heavy paths). C++ in Unreal — required for engine extension and hot paths, longer compiles. C# in Unity — the standard; IL2CPP AOT removes JIT overhead on mobile.
11. **Summarize the diagnosis** with root cause, fix steps, and a verification method.

## Concrete checks
- Engine version and exact build number identified.
- Target platform and SDK version requirements verified.
- Issue classified: import / compile / runtime / shader / build / migration / selection.
- Engine changelog checked for breaking changes in the affected version range.
- Third-party plugins verified compatible with the target engine version.
- Shader pipeline (URP/HDRP/Forward+/Deferred) matches the shader code's assumptions.
- Build-target SDK (NDK, Xcode, Emscripten) within the required range.
- `.meta` / `.import` files present and consistent with assets (Unity/Godot).
- Language choice justified against project requirements, not just habit.
- Fix verified, or profiler/compile output requested to confirm the diagnosis.
- For C# projects, the .NET/Mono toolchain is present and the `.csproj` target framework matches the engine.
- The actual failing compile/import/build log is captured and attached, not paraphrased.
- Any asset edit is done with the engine closed to avoid on-disk corruption.
- The Android JDK version matches the engine's Gradle plugin requirement.
- The render-pipeline assumption in any shader matches the project's active pipeline.
- GDExtension / native plugin binaries are built for the exact engine minor version in use.

## Commands
```bash
# Exact engine version
godot --version                                                  # Godot
rg -n "m_EditorVersion" ProjectSettings/ProjectVersion.txt       # Unity
rg -n "EngineAssociation" *.uproject                             # Unreal

# Headless compile / import to surface script and import errors
godot --headless --editor --quit 2>&1 | rg -i "error|SCRIPT ERROR|failed to load"
godot --headless --export-debug "Web" build/index.html 2>&1 | tail -30   # build-failure log

# Godot 3 -> 4 API leftovers (common migration breaks)
rg -n "KinematicBody|\byield\(|\.connect\([\"'][^\"']+[\"'],\s*self" --type-add 'gd:*.gd' -tgd

# Unity: missing .meta files (import instability) and IL2CPP strip risks
find Assets -type f ! -name '*.meta' | while read -r f; do [ -f "$f.meta" ] || echo "MISSING META: $f"; done
rg -n "link\.xml|[Preserve]|JsonUtility|reflection|Activator\.CreateInstance" -tcs

# Shader pipeline mismatch (URP include used outside URP)
rg -n "com\.unity\.render-pipelines|#include .*ShaderLibrary|render_mode|SubShader" -i

# WebGL feature limits (compute / Forward+ not available)
rg -n "rendering/renderer/rendering_method" project.godot
rg -n "compute|GPUParticles" --type-add 'gd:*.gd' -tgd | head

# Build SDK versions
sdkmanager --list 2>/dev/null | rg "ndk"        # Android NDK
xcodebuild -version 2>/dev/null                  # iOS toolchain
emcc --version 2>/dev/null | head -1             # WebGL / Emscripten
java -version 2>&1 | head -1                      # JDK (Android Gradle)
```
```bash
# Confirm the C# / .NET toolchain for Unity or Godot-Mono projects
dotnet --version 2>/dev/null
ls *.sln *.csproj 2>/dev/null                     # restored project files present?
rg -n "<TargetFramework>" *.csproj 2>/dev/null    # target framework matches engine?

# Third-party plugin compatibility (the #1 migration blocker)
find . -name '*.gdextension' -o -name 'package.json' -path '*Packages*' | head
rg -n "compatibility_minimum|min(imum)?_version|com\.unity\..*@" -i . 2>/dev/null | head

# Capture the actual failing log to attach to the diagnosis
godot --headless --editor --quit 2>&1 | rg -i "error|failed|cannot" | head -20
rg -n "error CS[0-9]+|Shader error|Cook failed|Undefined symbol" $(find . -name '*.log') 2>/dev/null | head
```

## Common issues & anti-patterns
- **Godot 3 code in a Godot 4 project.** `KinematicBody`, `yield()`, and `connect("signal", self, "method")` are Godot 3 syntax; Godot 4 uses `CharacterBody3D`, `await`, and `signal.connect(callable)`. The migration tool misses custom signal connections.
- **URP shader in the Built-in pipeline.** A shader including the URP ShaderLibrary renders pink in Built-in because the package path does not exist. Each pipeline needs its own shader variant.
- **IL2CPP stripping essential types.** Unity's managed-code stripping removes types only referenced via reflection (JSON deserializers, DI). Preserve them with a `link.xml` or `[Preserve]`.
- **Unreal Blueprint with a stale C++ parent.** Blueprints cache the parent class layout; changing a `UPROPERTY` in C++ without recompiling derived Blueprints causes a load crash. "Compile All Blueprints" after C++ struct changes.
- **WebGL with compute shaders.** Godot's Forward+ uses compute shaders unavailable in WebGL. WebGL targets must use the Compatibility renderer.
- **Wrong Android NDK version.** Unity's per-project NDK gets overridden by the Hub-installed version; a mismatch breaks builds. Match the NDK to Unity's requirements table.
- **GDExtension compiled for the wrong Godot version.** A `.gdextension` binary built for 4.2 crashes in 4.3 because the ABI changed. Recompile per minor version.
- **Unreal 5 Nanite on mobile.** Nanite is unsupported on mobile/WebGL; provide fallback LODs or disable Nanite for those targets.
- **C# in Godot without the Mono/.NET build.** GDScript-only Godot binaries cannot run `.cs` scripts; the project must use the .NET edition and a restored `*.csproj`.
- **Editing assets while the engine holds them open.** Hand-editing a `.tscn`/`.prefab`/`.uasset` on disk while the editor is running causes a merge conflict on save and can corrupt the file.
- **Mismatched JDK for Android Gradle.** A JDK newer or older than the engine's Gradle plugin expects fails the Android build with an opaque Gradle error. Match the JDK to the engine's requirements table.
- **`.csproj` target framework drift.** A Unity/Godot-Mono project whose `<TargetFramework>` was hand-bumped past what the engine supports fails to restore or load assemblies. Keep it on the engine-supported framework.
- **Assuming the asset store plugin works on the new version.** A plugin built for the prior engine version is the single most common upgrade blocker; verify its declared compatibility before bumping.

## Engine selection comparison (fill against the project's needs)
| Criterion | Godot 4 | Unity | Unreal 5 |
|-----------|---------|-------|----------|
| Best fit | 2D / small-mid 3D, indie | mobile, XR, mid 3D | AAA visuals, high-end 3D |
| Languages | GDScript, C#, C++ | C# | Blueprint, C++ |
| Licensing | MIT, free | seat-based tiers | royalty above a revenue threshold |
| Build size (empty) | small | medium | large |
| WebGL/Web export | yes (Compatibility) | yes | limited |
| Asset ecosystem | growing | largest | strong for 3D |

## Shader portability (a shader is NOT portable across pipelines)
| Engine | Pipelines | Note |
|--------|-----------|------|
| Unity | Built-in / URP / HDRP | each needs its own shader variant; URP includes fail in Built-in |
| Godot | Forward+ / Mobile / Compatibility | Forward+ uses compute (no WebGL); use Compatibility for web |
| Unreal | Deferred / Forward | Forward for VR/mobile; some features are Deferred-only |

## Required output
Return a structured report with:
1. Engine, version, and platform confirmed.
2. Issue classification and root-cause diagnosis.
3. A step-by-step fix with exact API names, file paths, or setting locations.
4. A verification step: how to confirm the fix (compile output, import success, a build-log line).
5. For engine selection: a three-column comparison table (Godot / Unity / Unreal) against the specific project requirements.

## Safety
- Do not modify engine project settings, build configurations, or signing credentials without listing every change explicitly.
- Do not trigger builds, editor compilations, or device deployments without instruction.
- Do not read or reproduce API keys, store credentials, or developer certificates found in project files.
- When a diagnosis is unconfirmed, request the specific compile/import/build log needed to confirm it rather than guessing.

## Completion criteria
Done means the engine, version, and platform are confirmed, the issue is classified with a root-cause diagnosis, the fix lists exact API names/paths/settings, a verification step is given, and (for selection questions) a three-column comparison addresses the project's stated requirements.

---
name: godot-unity-unreal-triage
description: Use when you need to triage Godot, Unity, Unreal, shader, engine, and asset pipeline issues.
---

# Godot / Unity / Unreal Triage

## Purpose

Diagnose and triage engine-specific issues in Godot 4, Unity (2021 LTS through 6), or Unreal Engine 5. Cover engine selection questions, language choice (GDScript vs. C# vs. Blueprint vs. C++), shader compilation failures, build target problems, version compatibility breaks, import pipeline errors, and editor crashes. Produce a concrete diagnosis and next steps — not a generic "check the docs" response.

## When to use

- A Unity/Godot/Unreal project fails to import, compile, or build and the error needs diagnosis.
- A shader compiles in the editor but fails on device (WebGL, mobile GLES, Vulkan).
- An engine version upgrade broke existing code or assets and the migration path is needed.
- Engine selection is being decided for a new project and a structured comparison is needed.
- A Blueprint or GDScript vs. C# performance question needs an evidence-based answer.

## When not to use

- The issue is a gameplay bug unrelated to the engine — use gameplay-systems-review.
- The issue is a frame rate problem — use game-performance-review (after confirming the engine layer is not the bottleneck).
- The codebase is a web app or mobile app using an engine as a renderer (e.g., Three.js) — these are not covered by this skill.

## Procedure

1. **Identify engine, version, and target platform.** Note exact version (e.g., Godot 4.3.stable, Unity 2022.3.42f1, Unreal 5.4.4). Note target platform (Windows, macOS, Android, iOS, WebGL, consoles). Version and platform combination determines which bugs and shader variants are in scope.
2. **Classify the issue type.** Assign to one of: Import error, Compile error, Runtime crash, Shader failure, Build failure, Version migration break, Engine selection question.
3. **For import errors:** Check file format compatibility with the engine version. In Unity, verify `.meta` files are not missing or corrupted. In Godot, check `.import` files and whether the asset type matches the importer (e.g., `.glb` imported as scene vs. mesh). In Unreal, check source content folder structure and whether the asset was created in a later engine version.
4. **For compile errors:** Identify whether the error is in engine C# API, GDScript syntax, Blueprint compilation, or native C++. Check for API breaking changes introduced in the target version (Unity removed `OnGUI` optimizations in 2023, Godot renamed `KinematicBody` to `CharacterBody3D` in 4.0, Unreal deprecated `AActor::Tick` override pattern changes in 5.3). Cross-reference the error with the engine's upgrade guide.
5. **For shader failures:** Determine the render pipeline (Unity: Built-in / URP / HDRP; Godot: Forward+ / Mobile / Compatibility; Unreal: Deferred / Forward). Shader code written for one pipeline is not portable to another. Check for WebGL-specific limitations: no geometry shaders, no compute shaders in WebGL 1, limited texture formats. Check for GLES 3.0 vs. Vulkan path on Android.
6. **For build failures:** Check platform SDK requirements (Android NDK/JDK version, iOS Xcode version, WebGL Emscripten version). Verify signing configuration is complete. Check for missing or mismatched plugin versions. In Unity, verify the target platform module is installed in the Hub.
7. **For version migration breaks:** Identify the source and target version. Consult the engine's changelog and upgrade guide for breaking changes in that range. List affected APIs with their new equivalents. Check whether third-party plugins are compatible with the new version — this is the most common migration blocker.
8. **For engine selection questions:** Evaluate against: target platform (Godot excels at small/indie, Unreal at AAA visuals, Unity at mobile and XR), team language preference (GDScript is fast to iterate, C# is type-safe, C++ is performant), licensing (Godot MIT, Unity seat-based, Unreal 5% royalty above $1M), and community asset availability (Unity Asset Store is largest, Unreal Marketplace strong for 3D, Godot Asset Library growing).
9. **For GDScript vs. C# vs. Blueprint vs. C++ questions:** GDScript: best for rapid iteration in Godot, interpreted, hot-reload supported. C# in Godot: better performance, strong typing, requires Mono build. Blueprint in Unreal: visual scripting, good for designers, compiles to bytecode not native, ~10x slower than C++ in CPU-heavy paths. C++ in Unreal: required for engine extension, performance-critical systems, longer compile cycles. C# in Unity: the standard; IL2CPP AOT compilation for mobile eliminates JIT overhead.
10. **Summarize the diagnosis** with a root cause, fix steps, and verification method.

## Checklist

- [ ] Engine version and exact build number identified
- [ ] Target platform and SDK version requirements verified
- [ ] Issue classified: import / compile / runtime / shader / build / migration / selection
- [ ] Engine changelog checked for breaking changes in the affected version range
- [ ] Third-party plugins verified compatible with target engine version
- [ ] Shader pipeline (URP/HDRP/Forward+/Deferred) matches shader code assumptions
- [ ] Build target SDK (NDK, Xcode, Emscripten) version within required range
- [ ] `.meta` / `.import` files present and consistent with assets (Unity/Godot)
- [ ] Language choice justified against project requirements (not just habit)
- [ ] Fix verified or profiler/compile output requested to confirm diagnosis

## Common issues & anti-patterns

- **Godot 3 code in Godot 4 project**: `KinematicBody`, `yield()`, `connect("signal", self, "method")` are all Godot 3 syntax. Godot 4 uses `CharacterBody3D`, `await`, and `signal.connect(callable)`. The migration tool handles most cases but misses custom signal connections.
- **Unity URP shader in Built-in pipeline**: a shader using `#include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"` renders pink in Built-in because the package path does not exist. Each pipeline needs its own shader variant.
- **IL2CPP stripping essential types**: Unity's managed code stripping removes types not referenced in code. Types instantiated via reflection (JSON deserializers, dependency injection) must be preserved with a `link.xml` file.
- **Unreal Blueprint with C++ parent class from a different plugin version**: Blueprints cache their parent class layout. Changing a `UPROPERTY` in C++ without clearing derived Blueprint bytecode causes a load crash. Always "Compile All Blueprints" after C++ struct changes.
- **WebGL with compute shaders**: Godot's Forward+ renderer uses compute shaders which are not available in WebGL. Projects targeting WebGL must use the Compatibility renderer.
- **Missing Android NDK version**: Unity's target NDK version is set per project but overridden by the Hub-installed version. NDK 23+ breaks builds targeting API level 21 in some Unity versions. Match NDK to Unity's requirements table exactly.
- **Godot GDExtension compiled for wrong Godot version**: a `.gdextension` binary compiled for Godot 4.2 crashes in Godot 4.3 because the GDNative ABI changed. GDExtension binaries must be recompiled for each minor version.
- **Unreal 5 Nanite on mobile**: Nanite is not supported on mobile or WebGL. Projects using Nanite meshes must have fallback LODs for mobile targets, or Nanite must be disabled globally.

## Required output

Return a structured report with:
1. Engine, version, and platform confirmed.
2. Issue classification and root cause diagnosis.
3. Step-by-step fix with exact API names, file paths, or setting locations.
4. Verification step: how to confirm the fix worked (compile output, import success, build log line).
5. For engine selection: a 3-column comparison table (Godot / Unity / Unreal) for the specific project requirements.

## Safety

- Do not modify engine project settings, build configurations, or signing credentials without listing all changes explicitly.
- Do not trigger builds, editor compilations, or device deployments.
- Do not read or reproduce API keys, store credentials, or developer certificates found in project files.

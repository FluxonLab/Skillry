---
name: web-game-performance
description: Use when diagnosing or optimising browser game performance — covering the 16.6 ms frame budget, requestAnimationFrame discipline, object pooling, sprite batching, GC spike reduction, Canvas vs WebGL trade-offs, and Chrome DevTools profiling workflow.
---

# Web Game Performance (60 fps)

## Purpose

Diagnose and fix frame-rate problems in browser games. The 16.6 ms budget is non-negotiable at 60 fps — any single frame over budget causes a visible stutter. This skill covers: reading Chrome DevTools Performance and Memory panels, identifying hot paths, applying object pooling to eliminate GC spikes, reducing draw calls with sprite batching, choosing the right rendering backend (Canvas 2D vs WebGL vs WebGPU), and validating fixes with real measurements.

## When to use

- The game drops below 60 fps on a mid-range machine.
- The Chrome Performance tab shows long GC or layout events mid-frame.
- The Memory panel shows a sawtooth pattern (repeated allocation then collection).
- Draw call count exceeds 100 per frame on a 2D scene.
- A frame takes > 16.6 ms consistently in the flame chart.
- Choosing between Canvas 2D and WebGL for a new project.
- Integrating a profiling step into the pre-release checklist.

## When not to use

- The frame rate is already stable at 60 fps and no symptoms exist.
- The bottleneck is network (asset loading latency) — that is a CDN / preload problem.
- Server-side or Node.js performance — use `python-performance-optimization` or equivalent.

## Procedure

### 1. Establish a performance baseline

```bash
# Chrome flags for accurate profiling (disable GPU process throttling)
# Open Chrome with:
open -a "Google Chrome" --args --disable-gpu-driver-bug-workarounds \
 --enable-precise-memory-info --disable-features=CalculateNativeWinOcclusion
```

In DevTools:
1. Performance tab → disable screenshots (reduces overhead), set CPU throttle to 4× (mid-range device simulation).
2. Record 5 seconds of gameplay.
3. Look at the **Frames** bar — red frames = over 16.6 ms.
4. Click a long frame → expand **Main** thread → identify the widest blocks.

Key measurements to capture before optimisation:
```
- Average frame time (ms)
- Worst-case frame (ms)
- GC event frequency (how many per second)
- Draw calls per frame (Spector.js or engine debug)
- Memory heap size (Memory panel → Heap snapshots)
```

### 2. requestAnimationFrame discipline

```typescript
// WRONG: creates a closure every frame → GC pressure
function badLoop(): void {
 requestAnimationFrame(() => {
 update()
 render()
 badLoop() // allocates a new anonymous function each call
 })
}

// RIGHT: named method reference, zero allocation per frame
class Game {
 private rafId = 0
 private lastTime = 0

 // Bind once in constructor — same function reference every rAF call
 private readonly tickBound = this.tick.bind(this)

 start(): void { this.rafId = requestAnimationFrame(this.tickBound) }
 stop(): void { cancelAnimationFrame(this.rafId) }

 private tick(now: number): void {
 const dt = (now - this.lastTime) / 1000
 this.lastTime = now
 this.update(dt)
 this.render()
 this.rafId = requestAnimationFrame(this.tickBound)
 }

 private update(_dt: number): void { /* game logic */ }
 private render(): void { /* draw */ }
}
```

### 3. Object pooling — eliminate GC spikes

Every `new` keyword inside the game loop is a potential GC trigger. Pool frequently created objects.

```typescript
// Generic typed pool
export class Pool<T> {
 private free: T[] = []
 private readonly factory: () => T
 private readonly reset: (obj: T) => void

 constructor(factory: () => T, reset: (obj: T) => void, initial = 32) {
 this.factory = factory
 this.reset = reset
 for (let i = 0; i < initial; i++) this.free.push(factory())
 }

 acquire(): T {
 return this.free.length > 0 ? this.free.pop()! : this.factory()
 }

 release(obj: T): void {
 this.reset(obj)
 this.free.push(obj)
 }

 get available(): number { return this.free.length }
}

// Bullet pool example (zero heap allocation per shot during gameplay)
interface Bullet {
 x: number; y: number
 vx: number; vy: number
 active: boolean
}

const bulletPool = new Pool<Bullet>(
 () => ({ x: 0, y: 0, vx: 0, vy: 0, active: false }),
 (b) => { b.active = false },
 200,
)

// Avoid these inside update():
// new Bullet(...) ← allocates
// bullets.push({...}) ← allocates
// bullets.splice(i, 1) ← shifts array, GC pressure

// Instead:
const activeBullets: Bullet[] = new Array(200).fill(null)
let activeBulletCount = 0

function fireBullet(x: number, y: number, vx: number, vy: number): void {
 const b = bulletPool.acquire()
 b.x = x; b.y = y; b.vx = vx; b.vy = vy; b.active = true
 activeBullets[activeBulletCount++] = b
}

function updateBullets(dt: number): void {
 let write = 0
 for (let i = 0; i < activeBulletCount; i++) {
 const b = activeBullets[i]
 b.x += b.vx * dt
 b.y += b.vy * dt
 if (b.x > 0 && b.x < 1280 && b.y > 0 && b.y < 720) {
 activeBullets[write++] = b // keep — no allocation
 } else {
 bulletPool.release(b) // return to pool — no GC
 }
 }
 activeBulletCount = write
}
```

### 4. Canvas 2D vs WebGL — decision matrix

| Criterion | Canvas 2D | WebGL (Pixi/Three) |
|---|---|---|
| Sprites per frame at 60fps | < 500 | 5 000 – 100 000+ |
| Setup complexity | Minimal | Medium–High |
| Text rendering | Native, easy | Texture atlas or SDF |
| Pixel-perfect 2D | Yes | Yes (with correct settings) |
| Custom shaders | No | Yes (GLSL) |
| iOS / Safari support | Excellent | Good (WebGL 2 gated on iOS 15+) |
| WebGPU support | No | PixiJS 8, Three.js WebGPURenderer |

```typescript
// Canvas 2D — fast path for < 500 sprites
const ctx = canvas.getContext('2d')!

function render(sprites: Sprite[]): void {
 ctx.clearRect(0, 0, canvas.width, canvas.height)
 for (const s of sprites) {
 ctx.drawImage(s.image, s.x - s.hw, s.y - s.hh, s.w, s.h)
 }
}

// WebGL sprite batching (engine-provided)
// PixiJS: use ParticleContainer (see pixijs-2d-rendering skill)
// Phaser: use Blitter or GameObjects.Group with maxSize
// Rule: if drawImage count > 300 per frame → switch to WebGL
```

### 5. Reducing draw calls — sprite batching

Every draw call has a fixed CPU overhead (~0.1–0.5 ms). Batch sprites that share the same texture.

```typescript
// Measure draw calls with Spector.js (Chrome extension)
// Target: < 20 draw calls per frame for a 2D game

// In Phaser — enable batch renderer (default in WebGL mode)
// Batching breaks when:
// - Texture changes between sprites (use a single atlas PNG)
// - BlendMode changes mid-batch (avoid mixing ADD and NORMAL)
// - Sprite is rotated + pipeline changes

// In PixiJS — group sprites into same Container with same texture
// In Three.js — use InstancedMesh for repeated geometry (see threejs skill)

// Manual batching for Canvas 2D:
function renderBatch(ctx: CanvasRenderingContext2D, atlas: HTMLImageElement,
 sprites: SpriteData[]): void {
 // Sort by y-position (painter's algorithm) — one sort per frame, not per sprite
 sprites.sort((a, b) => a.y - b.y)

 for (const s of sprites) {
 ctx.drawImage(
 atlas,
 s.frameX, s.frameY, s.frameW, s.frameH, // source rect
 s.x, s.y, s.frameW, s.frameH, // dest rect
 )
 }
}
```

### 6. Memory profiling — heap snapshots

```
1. DevTools → Memory → Heap snapshot → Take snapshot (baseline)
2. Play game for 30 seconds
3. Take another snapshot
4. Comparison view → sort by "Alloc. size" descending
5. Look for: Bullet, Particle, Vector2, Array, Object — objects that grow
6. Trace retainers to confirm pool is releasing correctly
```

```typescript
// Quick allocation rate check in browser console:
const before = performance.memory?.usedJSHeapSize ?? 0
// ... run one frame ...
const after = performance.memory?.usedJSHeapSize ?? 0
console.log(`Heap delta per frame: ${after - before} bytes`)
// Target: < 1000 bytes per frame (near zero with pools)
```

### 7. Profiling checklist before and after each optimisation

```bash
# Record these numbers BEFORE changing anything:
# Frame time p50, p95, p99 (ms)
# GC events per second
# Draw calls per frame
# Heap usage steady-state (MB)

# After each change, record again and compare.
# Optimise one thing at a time — isolate improvements.
```

## Concrete checks

- [ ] `requestAnimationFrame` uses a bound method reference, not an arrow function closure.
- [ ] No `new` calls inside `update()` or `render()` for objects that fire > 10× per second.
- [ ] Object pool pre-warms with at least `expectedPeak * 1.2` objects.
- [ ] Bullet / particle arrays use index writes (`arr[write++] = b`) not `push/splice`.
- [ ] All sprites sharing a texture are in the same draw batch (single atlas PNG confirmed).
- [ ] Canvas 2D `clearRect` called once at start of frame, not per sprite.
- [ ] `performance.memory.usedJSHeapSize` delta per frame < 1 KB with pools active.
- [ ] Chrome Performance flame chart shows no individual block > 10 ms outside asset loading.

## Commands

```bash
# Install Spector.js for draw call capture (Chrome extension — manual install)
# https://chrome.google.com/webstore/detail/spectorjs

# Run a frame timing benchmark in the browser console
(function bench(n=300){
 const times=[]
 let last=performance.now()
 let count=0
 function tick(now){
 times.push(now-last); last=now
 if(++count<n) requestAnimationFrame(tick)
 else {
 times.sort((a,b)=>a-b)
 console.log(`p50:${times[Math.floor(n*0.5)].toFixed(2)}ms`,
 `p95:${times[Math.floor(n*0.95)].toFixed(2)}ms`,
 `p99:${times[Math.floor(n*0.99)].toFixed(2)}ms`)
 }
 }
 requestAnimationFrame(tick)
})()

# TypeScript strict null checks (catches pool release bugs)
npx tsc --noEmit --strict
```

## Required output

When diagnosing or fixing a performance problem, deliver:
1. Baseline measurements: frame time p50/p95, GC frequency, draw call count, heap delta.
2. Root cause identified in the flame chart (function name + file:line).
3. Fix applied (pool added, batch enabled, closure replaced, etc.).
4. Post-fix measurements confirming improvement.
5. Regression risk: what else could this change affect?

## Safety checks

- Never delete or truncate profiling data before comparing before/after numbers.
- Pool releases must zero out all mutable fields (position, velocity, flags) — stale values cause gameplay bugs.
- Avoid premature optimisation: profile first, then optimise only bottlenecks with measured impact.
- `performance.memory` is Chromium-only — not available in Firefox or Safari.

## Completion criteria

Done means: frame time p95 < 16.6 ms on a 4× throttled mid-range device simulation, GC events ≤ 1 per 5 seconds, draw calls ≤ 20 per frame for a 2D scene, and heap delta per frame < 1 KB with object pools active.

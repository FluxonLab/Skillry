---
name: pixijs-2d-rendering
description: Use when building high-performance 2D rendering with PixiJS 8 — covering Application setup, Sprite/Container hierarchy, the Ticker loop, texture atlas loading, particle effects, batch rendering, and the WebGL/WebGPU backend switch.
---

# PixiJS 8 — 2D Rendering Patterns

## Purpose

Provide production-ready PixiJS 8 patterns in TypeScript: Application initialisation, display object hierarchy (Sprite, Container, Graphics), the Ticker-based update loop, texture atlas loading via SpritesheetLoader, particle emitters, batch rendering tuning, and the explicit opt-in to the WebGPU backend. Targets projects that need maximum 2D rendering throughput — UI-heavy games, data visualisations, interactive infographics — without the full overhead of a game engine.

## When to use

- Building a 2D interactive canvas app where DOM performance is insufficient.
- Rendering hundreds or thousands of sprites per frame (particles, crowd simulations, tile maps).
- Implementing a custom 2D game with a hand-rolled game loop instead of Phaser's full framework.
- Opting in to WebGPU for next-gen GPU throughput on supported browsers.
- Adding a PixiJS canvas inside a React/Next.js app without SSR conflicts.

## When not to use

- The project needs a full 2D game engine with physics, input system, and scene manager out of the box — use `phaser-game-development`.
- The content is 3D — use `threejs-webgl-patterns`.
- Simple CSS animations or SVG suffice for the visual requirement.

## Procedure

### 1. Bootstrap PixiJS 8 with Vite + TypeScript

```bash
npm install pixi.js
# pixi.js 8 ships its own types — no @types/pixi.js needed
```

`src/main.ts`:
```typescript
import { Application, Assets, Sprite, Container, Ticker } from 'pixi.js'

async function main(): Promise<void> {
 // --- Application ---
 const app = new Application()

 await app.init({
 width: 1280,
 height: 720,
 backgroundColor: 0x1a1a2e,
 antialias: true,
 resolution: Math.min(window.devicePixelRatio, 2),
 autoDensity: true,
 // Prefer WebGPU, fall back to WebGL automatically:
 preference: 'webgpu',
 })

 document.body.appendChild(app.canvas)

 // --- Asset loading (Assets API replaces old Loader) ---
 await Assets.load([
 { alias: 'hero', src: '/assets/hero.json' }, // texture atlas
 { alias: 'bg', src: '/assets/background.png' },
 ])

 // --- Display object tree ---
 const world = new Container()
 app.stage.addChild(world)

 const bg = Sprite.from('bg')
 bg.anchor.set(0)
 world.addChild(bg)

 const hero = Sprite.from('hero_idle_0')
 hero.anchor.set(0.5)
 hero.position.set(640, 360)
 world.addChild(hero)

 // --- Game loop via Ticker ---
 app.ticker.add((ticker: Ticker) => {
 const delta = ticker.deltaTime // frames (1 at 60fps, 2 at 30fps)
 hero.rotation += 0.01 * delta
 })
}

main().catch(console.error)
```

### 2. Texture atlas — SpritesheetLoader

PixiJS 8 resolves a `.json` atlas (TexturePacker or Aseprite JSON-Array export) and registers each frame by name automatically.

```typescript
// Load atlas
await Assets.load({ alias: 'characters', src: '/assets/characters.json' })

// Access individual frames by name
const frame = Sprite.from('hero_run_0') // must match TexturePacker frame name

// Animated sprite from atlas frames
import { AnimatedSprite } from 'pixi.js'

const frames = ['hero_run_0', 'hero_run_1', 'hero_run_2', 'hero_run_3']
 .map(name => Assets.get(name))

const anim = new AnimatedSprite(frames)
anim.animationSpeed = 0.2 // fraction of 60fps: 0.2 = 12fps playback
anim.loop = true
anim.play()
anim.anchor.set(0.5)
app.stage.addChild(anim)
```

### 3. Container hierarchy for scene organisation

```typescript
import { Container, Graphics, Text, TextStyle } from 'pixi.js'

// Layer pattern: background → entities → ui
const bgLayer = new Container()
const entityLayer = new Container()
const uiLayer = new Container()

app.stage.addChild(bgLayer, entityLayer, uiLayer)
app.stage.sortableChildren = false // manual z-order is faster than sortChildren

// Graphics API for procedural shapes
const healthBar = new Graphics()
function drawHealth(current: number, max: number): void {
 healthBar.clear()
 // Background
 healthBar.rect(0, 0, 200, 16).fill({ color: 0x333333 })
 // Fill
 const ratio = Math.max(0, current / max)
 const color = ratio > 0.5 ? 0x4ade80 : ratio > 0.25 ? 0xfbbf24 : 0xef4444
 healthBar.rect(0, 0, 200 * ratio, 16).fill({ color })
}
drawHealth(75, 100)
uiLayer.addChild(healthBar)

// Text
const style = new TextStyle({ fontFamily: 'Arial', fontSize: 24, fill: 0xffffff })
const label = new Text({ text: 'Score: 0', style })
label.position.set(10, 10)
uiLayer.addChild(label)
```

### 4. Particle system with ParticleContainer

`ParticleContainer` is a specialised Container that batches sprites into a single draw call — ideal for particles where 99% of properties are uniform.

```typescript
import { ParticleContainer, Sprite, Assets } from 'pixi.js'

const MAX_PARTICLES = 5000
const particles: Array<{ sprite: Sprite; vx: number; vy: number; life: number }> = []

// ParticleContainer properties: position, scale, rotation, tint, alpha
const emitter = new ParticleContainer(MAX_PARTICLES, {
 position: true,
 rotation: true,
 alpha: true,
 tint: true,
})
app.stage.addChild(emitter)

function spawnParticle(x: number, y: number): void {
 if (particles.length >= MAX_PARTICLES) return
 const sprite = Sprite.from('particle_dot')
 sprite.anchor.set(0.5)
 sprite.position.set(x, y)
 sprite.tint = 0xfbbf24
 emitter.addChild(sprite)
 particles.push({
 sprite,
 vx: (Math.random() - 0.5) * 4,
 vy: -Math.random() * 6 - 2,
 life: 1.0,
 })
}

app.ticker.add((ticker) => {
 const dt = ticker.deltaTime / 60 // in seconds

 for (let i = particles.length - 1; i >= 0; i--) {
 const p = particles[i]
 p.life -= dt * 1.5
 p.vy += 9.8 * dt // gravity
 p.sprite.x += p.vx
 p.sprite.y += p.vy
 p.sprite.alpha = p.life

 if (p.life <= 0) {
 emitter.removeChild(p.sprite)
 p.sprite.destroy()
 particles.splice(i, 1)
 }
 }
})
```

### 5. Object pooling — avoid GC spikes

```typescript
class SpritePool {
 private pool: Sprite[] = []
 private texture: string

 constructor(textureAlias: string, initialSize = 50) {
 this.texture = textureAlias
 for (let i = 0; i < initialSize; i++) this.pool.push(this.create())
 }

 private create(): Sprite {
 const s = Sprite.from(this.texture)
 s.visible = false
 return s
 }

 acquire(parent: Container): Sprite {
 const s = this.pool.pop() ?? this.create()
 s.visible = true
 parent.addChild(s)
 return s
 }

 release(s: Sprite): void {
 s.visible = false
 s.parent?.removeChild(s)
 this.pool.push(s)
 }
}

const bulletPool = new SpritePool('bullet', 100)
```

### 6. React / Next.js integration

```typescript
// components/PixiCanvas.tsx
'use client'
import { useEffect, useRef } from 'react'

export default function PixiCanvas() {
 const mountRef = useRef<HTMLDivElement>(null)

 useEffect(() => {
 let app: import('pixi.js').Application | null = null

 ;(async () => {
 const { Application } = await import('pixi.js')
 app = new Application()
 await app.init({ width: 800, height: 600, backgroundColor: 0x1a1a2e })
 mountRef.current?.appendChild(app.canvas)
 })()

 return () => {
 app?.destroy(true, { children: true })
 }
 }, [])

 return <div ref={mountRef} className="w-full aspect-video" />
}
```

## Concrete checks

- [ ] `app.init()` awaited before adding children.
- [ ] `Assets.load()` awaited before `Sprite.from()` — no empty texture.
- [ ] `ParticleContainer` used when > 200 identical sprites with uniform properties.
- [ ] `resolution: Math.min(window.devicePixelRatio, 2)` + `autoDensity: true` set.
- [ ] `app.destroy(true, { children: true })` called on React unmount.
- [ ] Object pool used for frequently created/destroyed sprites (bullets, particles).
- [ ] `TextStyle` defined once and reused, not recreated per text object per frame.
- [ ] Atlas JSON frame names match the string passed to `Sprite.from()`.

## Commands

```bash
# Install PixiJS 8 (no @types needed)
npm install pixi.js

# Verify WebGPU availability in Chrome
# DevTools console: navigator.gpu?.requestAdapter().then(a => console.log(a?.name))

# Export texture atlas with TexturePacker CLI
TexturePacker --format pixijs5 --data out.json --sheet out.png assets/sprites/

# Inspect draw calls (should be 1 for ParticleContainer batch)
# Chrome DevTools → Performance → Frame → GPU
```

## Required output

When building or reviewing PixiJS code, deliver:
1. Application init block with resolution, antialias, preference (webgpu/webgl).
2. Asset loading via `Assets.load()` before any `Sprite.from()`.
3. Container hierarchy (background / entity / ui layers).
4. Ticker update function with correct `deltaTime` usage.
5. Particle system using `ParticleContainer` with pool if count > 200.
6. React integration pattern with async dynamic import and destroy cleanup.

## Safety checks

- Never call `Sprite.from()` before `Assets.load()` resolves for that texture.
- Do not create `new Graphics()` inside the Ticker — create once, call `.clear()` + redraw.
- Do not use `stage.sortChildren` on large container trees; use explicit `zIndex` only on containers that change z-order.
- `app.destroy(true)` removes the canvas and all WebGL resources; do not access `app` after destruction.

## Completion criteria

Done means: PixiJS 8 Application initialises without console errors, sprites render at native resolution, `ParticleContainer` batch is confirmed (single draw call in DevTools), object pool shows zero garbage-collect spikes in the profiler, and the React component mounts and unmounts cleanly.

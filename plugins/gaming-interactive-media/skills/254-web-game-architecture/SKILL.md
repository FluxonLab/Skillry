---
name: web-game-architecture
description: Use when designing or reviewing engine-agnostic web game architecture — covering the fixed-timestep game loop, Entity-Component-System (ECS) pattern, state machine, asset loading pipeline, and save/load via localStorage or IndexedDB.
---

# Web Game Architecture (Engine-Agnostic)

## Purpose

Provide engine-agnostic, TypeScript-first architectural patterns for browser games: a fixed-timestep loop with interpolation, a minimal ECS implementation, a finite state machine for game states, an asset manifest loader with progress, and a save/load system using localStorage (small) or IndexedDB (large). All patterns are renderer-agnostic — they compose with Phaser, PixiJS, Three.js, or a raw Canvas/WebGL layer.

## When to use

- Designing the top-level architecture of a new browser game before choosing a renderer.
- Refactoring a game loop that suffers from variable-speed gameplay on slow machines.
- Adding an ECS layer to decouple game logic from rendering in an existing Phaser/Pixi project.
- Implementing game state management (MainMenu → Loading → Playing → Paused → GameOver).
- Adding persistent save data (player progress, settings, high scores) to a web game.
- Reviewing a game codebase for separation of concerns and testability.

## When not to use

- The project already commits to Phaser's built-in scene system and state — stay inside Phaser's idioms and use `phaser-game-development`.
- The game is purely 3D and uses Unity/Godot compiled to WASM — different architecture applies.
- The task is renderer-specific (shader, sprite atlas, tilemap) — use the engine-specific skill.

## Procedure

### 1. Fixed-timestep game loop with interpolation

A variable `delta` loop drifts on slow hardware. A fixed-step accumulator gives deterministic physics and consistent simulation speed.

```typescript
// src/core/GameLoop.ts
export interface LoopCallbacks {
 update(dt: number): void // dt = fixed step in seconds (e.g. 1/60)
 render(alpha: number): void // alpha = interpolation [0,1] for smooth visuals
}

export class GameLoop {
 private readonly fixedStep = 1 / 60 // 60Hz simulation
 private readonly maxDeltaPerFrame = 0.25 // prevent spiral-of-death
 private accumulator = 0
 private lastTime = 0
 private rafId = 0
 private running = false

 constructor(private callbacks: LoopCallbacks) {}

 start(): void {
 this.running = true
 this.lastTime = performance.now()
 this.tick(this.lastTime)
 }

 stop(): void {
 this.running = false
 cancelAnimationFrame(this.rafId)
 }

 private tick = (now: number): void => {
 if (!this.running) return
 this.rafId = requestAnimationFrame(this.tick)

 let delta = (now - this.lastTime) / 1000 // seconds
 this.lastTime = now

 // Clamp to avoid huge deltas after tab switch / breakpoint
 if (delta > this.maxDeltaPerFrame) delta = this.maxDeltaPerFrame

 this.accumulator += delta

 // Fixed-step simulation
 while (this.accumulator >= this.fixedStep) {
 this.callbacks.update(this.fixedStep)
 this.accumulator -= this.fixedStep
 }

 // Interpolation fraction for smooth rendering between steps
 const alpha = this.accumulator / this.fixedStep
 this.callbacks.render(alpha)
 }
}

// Usage
const loop = new GameLoop({
 update(dt) { world.update(dt) },
 render(alpha) { renderer.render(world, alpha) },
})
loop.start()
```

### 2. Entity-Component-System (ECS)

```typescript
// src/core/ecs/types.ts
export type Entity = number

// src/core/ecs/World.ts
export class World {
 private nextId = 1
 private components = new Map<string, Map<Entity, unknown>>()
 private entities = new Set<Entity>()

 createEntity(): Entity {
 const id = this.nextId++
 this.entities.add(id)
 return id
 }

 destroyEntity(entity: Entity): void {
 this.entities.delete(entity)
 for (const store of this.components.values()) store.delete(entity)
 }

 addComponent<T>(entity: Entity, name: string, data: T): void {
 if (!this.components.has(name)) this.components.set(name, new Map())
 this.components.get(name)!.set(entity, data)
 }

 getComponent<T>(entity: Entity, name: string): T | undefined {
 return this.components.get(name)?.get(entity) as T | undefined
 }

 hasComponent(entity: Entity, name: string): boolean {
 return this.components.get(name)?.has(entity) ?? false
 }

 query(...componentNames: string[]): Entity[] {
 return [...this.entities].filter(e =>
 componentNames.every(n => this.hasComponent(e, n))
 )
 }
}

// Component types (plain data, no logic)
interface Position { x: number; y: number }
interface Velocity { vx: number; vy: number }
interface Health { current: number; max: number }
interface Renderable { spriteKey: string }

// System: movement
function movementSystem(world: World, dt: number): void {
 for (const entity of world.query('position', 'velocity')) {
 const pos = world.getComponent<Position>(entity, 'position')!
 const vel = world.getComponent<Velocity>(entity, 'velocity')!
 pos.x += vel.vx * dt
 pos.y += vel.vy * dt
 }
}

// System: gravity
function gravitySystem(world: World, dt: number): void {
 const GRAVITY = 980 // px/s²
 for (const entity of world.query('velocity')) {
 const vel = world.getComponent<Velocity>(entity, 'velocity')!
 vel.vy += GRAVITY * dt
 }
}

// Wire into game loop
const world = new World()
function update(dt: number): void {
 gravitySystem(world, dt)
 movementSystem(world, dt)
}
```

### 3. Finite State Machine for game states

```typescript
// src/core/StateMachine.ts
export interface State<TCtx> {
 name: string
 onEnter?(ctx: TCtx, prev?: string): void
 onExit?(ctx: TCtx, next: string): void
 onUpdate?(ctx: TCtx, dt: number): void
}

export class StateMachine<TCtx> {
 private states = new Map<string, State<TCtx>>()
 private current: State<TCtx> | null = null

 constructor(private ctx: TCtx) {}

 register(state: State<TCtx>): this {
 this.states.set(state.name, state)
 return this
 }

 transition(name: string): void {
 const next = this.states.get(name)
 if (!next) throw new Error(`Unknown state: ${name}`)
 const prev = this.current?.name
 this.current?.onExit?.(this.ctx, name)
 this.current = next
 this.current.onEnter?.(this.ctx, prev)
 }

 update(dt: number): void {
 this.current?.onUpdate?.(this.ctx, dt)
 }
}

// Game state example
interface GameContext { score: number; lives: number }
const ctx: GameContext = { score: 0, lives: 3 }

const machine = new StateMachine(ctx)
 .register({
 name: 'mainmenu',
 onEnter: () => console.log('Show main menu'),
 })
 .register({
 name: 'playing',
 onEnter: () => console.log('Game started'),
 onUpdate: (c, dt) => { /* run systems */ },
 })
 .register({
 name: 'gameover',
 onEnter: (c) => console.log(`Game over — score: ${c.score}`),
 })

machine.transition('mainmenu')
```

### 4. Asset loading pipeline with progress

```typescript
// src/core/AssetLoader.ts
export type AssetType = 'image' | 'audio' | 'json'

export interface AssetEntry {
 key: string
 url: string
 type: AssetType
}

export class AssetLoader {
 private cache = new Map<string, unknown>()

 async load(
 manifest: AssetEntry[],
 onProgress?: (ratio: number) => void,
 ): Promise<void> {
 let loaded = 0
 await Promise.all(manifest.map(async (entry) => {
 const asset = await this.loadOne(entry)
 this.cache.set(entry.key, asset)
 onProgress?.(++loaded / manifest.length)
 }))
 }

 get<T>(key: string): T {
 if (!this.cache.has(key)) throw new Error(`Asset not loaded: ${key}`)
 return this.cache.get(key) as T
 }

 private async loadOne(entry: AssetEntry): Promise<unknown> {
 switch (entry.type) {
 case 'image': return new Promise<HTMLImageElement>((res, rej) => {
 const img = new Image()
 img.onload = () => res(img)
 img.onerror = rej
 img.src = entry.url
 })
 case 'audio': return fetch(entry.url).then(r => r.arrayBuffer())
 case 'json': return fetch(entry.url).then(r => r.json())
 }
 }
}
```

### 5. Save / Load — localStorage vs IndexedDB

```typescript
// src/core/SaveManager.ts
export interface SaveData {
 version: number
 level: number
 score: number
 unlockedAbilities: string[]
}

const SAVE_KEY = 'my-game-save-v1'
const SCHEMA_VERSION = 1

export const SaveManager = {
 save(data: SaveData): void {
 try {
 localStorage.setItem(SAVE_KEY, JSON.stringify({ ...data, version: SCHEMA_VERSION }))
 } catch (e) {
 console.error('Save failed (storage full?)', e)
 }
 },

 load(): SaveData | null {
 const raw = localStorage.getItem(SAVE_KEY)
 if (!raw) return null
 try {
 const parsed = JSON.parse(raw) as SaveData
 if (parsed.version !== SCHEMA_VERSION) {
 console.warn('Save version mismatch — migrating or discarding')
 return null
 }
 return parsed
 } catch {
 return null
 }
 },

 clear(): void { localStorage.removeItem(SAVE_KEY) },
}

// For large binary saves (replay data, screenshots), use IndexedDB:
async function saveLargeBinaryToIDB(key: string, buffer: ArrayBuffer): Promise<void> {
 const db = await openDB()
 const tx = db.transaction('saves', 'readwrite')
 tx.objectStore('saves').put({ key, data: buffer, ts: Date.now() })
 await tx.done
}

function openDB(): Promise<IDBDatabase> {
 return new Promise((res, rej) => {
 const req = indexedDB.open('my-game', 1)
 req.onupgradeneeded = () => req.result.createObjectStore('saves', { keyPath: 'key' })
 req.onsuccess = () => res(req.result)
 req.onerror = () => rej(req.error)
 })
}
```

## Concrete checks

- [ ] Fixed-timestep loop: `accumulator >= fixedStep` consumed in a `while` — not an `if`.
- [ ] `maxDeltaPerFrame` clamp present — prevents spiral-of-death after tab blur.
- [ ] ECS `query()` is called before the update tick, not inside hot paths.
- [ ] StateMachine transitions call `onExit` before `onEnter`.
- [ ] Asset loader resolves all entries before the game scene starts.
- [ ] Save data includes a `version` field; load validates it before using data.
- [ ] `localStorage` used only for small structured data (< 5 MB); IndexedDB for binary blobs.

## Commands

```bash
# Run TypeScript type checks on architecture modules
npx tsc --noEmit --strict

# Test the game loop in isolation (Node.js with jsdom)
npx vitest run src/core/GameLoop.test.ts

# Profile the fixed-step simulation
# Chrome DevTools → Performance → Record → look for "update" in flame chart
```

## Required output

When reviewing or designing web game architecture, deliver:
1. Game loop type (variable vs fixed-step) with justification.
2. ECS world structure: which components exist, which systems consume them.
3. State machine transitions diagram (text representation).
4. Asset manifest list and loading order.
5. Save/load strategy: localStorage vs IndexedDB with size justification.
6. Coupling risks: renderer coupled to game logic? Input coupled to physics?

## Safety checks

- Never allocate new objects inside the hot `update` path — use pre-allocated pools.
- Do not access DOM APIs (document, window) inside ECS systems — keep them logic-only.
- `localStorage.setItem` can throw `QuotaExceededError` — always wrap in try/catch.
- Fixed-step simulation must be deterministic: avoid `Math.random()` inside `update()` if replays are needed; seed a PRNG instead.

## Completion criteria

Done means: the game loop runs at stable 60Hz with no spiral-of-death on 30fps hardware, ECS systems are independently testable without a renderer, the state machine covers all reachable states and transitions, assets load with progress reporting, and save/load round-trips without data loss or version errors.

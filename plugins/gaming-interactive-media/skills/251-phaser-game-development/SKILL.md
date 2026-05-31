---
name: phaser-game-development
description: Use when building, debugging, or architecting browser games with Phaser 3 — covering Scene lifecycle, physics systems, sprite/atlas management, tilemap loading, input handling, and Vite-based TypeScript project setup.
---

# Phaser 3 Game Development

## Purpose

Provide concrete, production-ready Phaser 3 patterns in TypeScript: Scene class structure, Arcade and Matter physics, texture atlas workflows, tilemap loading from Tiled, keyboard/pointer input, camera control, and a Vite dev environment. Surfaces real code you can paste and extend rather than documentation summaries.

## When to use

- Starting a new Phaser 3 project from scratch (project setup, tsconfig, Vite config).
- Adding a new Scene (boot, preload, game, UI, pause) or refactoring an existing one.
- Integrating Arcade physics (velocity, collision, groups) or switching to Matter.js bodies.
- Loading a texture atlas exported from TexturePacker or Aseprite.
- Parsing a Tiled `.tmx` / `.json` tilemap with collision layers.
- Debugging input lag, frame rate drops, or memory leaks in a Phaser game.
- Wiring a Phaser canvas inside a Next.js / React page without hydration errors.

## When not to use

- The project targets React Three Fiber or Three.js for 3D — use `threejs-webgl-patterns` instead.
- Pure UI work with no game loop — use standard React/shadcn patterns.
- The game needs native desktop distribution — Electron wrapping is a separate concern.

## Procedure

### 1. Bootstrap the project with Vite + TypeScript

```bash
npm create vite@latest my-game -- --template vanilla-ts
cd my-game
npm install phaser
npm install -D @types/node
```

`vite.config.ts`:
```typescript
import { defineConfig } from 'vite'

export default defineConfig({
 base: './',
 build: {
 assetsDir: 'assets',
 chunkSizeWarningLimit: 2048,
 },
 server: { port: 3000 },
})
```

`src/main.ts` — Phaser game config:
```typescript
import Phaser from 'phaser'
import { BootScene } from './scenes/BootScene'
import { PreloadScene } from './scenes/PreloadScene'
import { GameScene } from './scenes/GameScene'
import { UIScene } from './scenes/UIScene'

const config: Phaser.Types.Core.GameConfig = {
 type: Phaser.AUTO, // AUTO → WebGL if available, fallback Canvas
 width: 1280,
 height: 720,
 backgroundColor: '#1a1a2e',
 physics: {
 default: 'arcade',
 arcade: { gravity: { x: 0, y: 600 }, debug: import.meta.env.DEV },
 },
 scene: [BootScene, PreloadScene, GameScene, UIScene],
 scale: {
 mode: Phaser.Scale.FIT,
 autoCenter: Phaser.Scale.CENTER_BOTH,
 },
}

new Phaser.Game(config)
```

### 2. Scene lifecycle — the three methods that matter

```typescript
// src/scenes/GameScene.ts
import Phaser from 'phaser'

export class GameScene extends Phaser.Scene {
 private player!: Phaser.Types.Physics.Arcade.SpriteWithDynamicBody
 private platforms!: Phaser.Physics.Arcade.StaticGroup
 private cursors!: Phaser.Types.Input.Keyboard.CursorKeys

 constructor() {
 super({ key: 'GameScene' })
 }

 // preload: called once — load assets before create
 preload(): void {
 // Assets already loaded in PreloadScene; nothing needed here
 // unless this scene has unique assets
 }

 // create: called once after preload — build world, wire physics, input
 create(): void {
 // Tilemap
 const map = this.make.tilemap({ key: 'level1' })
 const tiles = map.addTilesetImage('terrain', 'terrain-tiles')!
 const groundLayer = map.createLayer('Ground', tiles, 0, 0)!
 groundLayer.setCollisionByProperty({ collides: true })

 // Player from atlas
 this.player = this.physics.add.sprite(100, 450, 'hero', 'idle_0')
 this.player.setCollideWorldBounds(true)
 this.player.setGravityY(200)

 // Collision between player and tilemap layer
 this.physics.add.collider(this.player, groundLayer)

 // Animations from atlas frames
 this.anims.create({
 key: 'run',
 frames: this.anims.generateFrameNames('hero', {
 prefix: 'run_', start: 0, end: 7, zeroPad: 0,
 }),
 frameRate: 12,
 repeat: -1,
 })

 // Camera
 this.cameras.main.setBounds(0, 0, map.widthInPixels, map.heightInPixels)
 this.cameras.main.startFollow(this.player, true, 0.1, 0.1)

 // Input
 this.cursors = this.input.keyboard!.createCursorKeys()

 // Pass data to overlay UI scene
 this.scene.launch('UIScene', { gameScene: this })
 }

 // update: called every frame — game logic only, no asset loading
 update(_time: number, _delta: number): void {
 const onGround = this.player.body.blocked.down

 if (this.cursors.left.isDown) {
 this.player.setVelocityX(-220)
 this.player.setFlipX(true)
 this.player.anims.play('run', true)
 } else if (this.cursors.right.isDown) {
 this.player.setVelocityX(220)
 this.player.setFlipX(false)
 this.player.anims.play('run', true)
 } else {
 this.player.setVelocityX(0)
 this.player.anims.play('idle', true)
 }

 if (this.cursors.up.isDown && onGround) {
 this.player.setVelocityY(-520)
 }
 }
}
```

### 3. PreloadScene — centralise all asset loading

```typescript
// src/scenes/PreloadScene.ts
import Phaser from 'phaser'

export class PreloadScene extends Phaser.Scene {
 constructor() { super({ key: 'PreloadScene' }) }

 preload(): void {
 // Progress bar
 const bar = this.add.graphics()
 this.load.on('progress', (v: number) => {
 bar.clear().fillStyle(0x4ade80).fillRect(100, 360, 1080 * v, 20)
 })
 this.load.on('complete', () => bar.destroy())

 // Texture atlas (TexturePacker / Aseprite export)
 this.load.atlas('hero', 'assets/hero.png', 'assets/hero.json')

 // Tilemap (Tiled JSON export)
 this.load.tilemapTiledJSON('level1', 'assets/maps/level1.json')
 this.load.image('terrain-tiles', 'assets/tiles/terrain.png')

 // Audio
 this.load.audio('jump', ['assets/sfx/jump.ogg', 'assets/sfx/jump.mp3'])
 }

 create(): void {
 this.scene.start('GameScene')
 }
}
```

### 4. Arcade physics — groups and overlap

```typescript
// Enemy group with Arcade physics
const enemies = this.physics.add.group({
 classType: Phaser.Physics.Arcade.Sprite,
 defaultKey: 'enemy',
 defaultFrame: 'walk_0',
 maxSize: 20,
})

const enemy = enemies.get(400, 300) as Phaser.Physics.Arcade.Sprite
enemy.setActive(true).setVisible(true)
enemy.setVelocityX(-80)

// Overlap (no bounce): player picks up coin
this.physics.add.overlap(this.player, coins, (_player, coin) => {
 (coin as Phaser.Physics.Arcade.Sprite).disableBody(true, true)
 this.events.emit('coinCollected')
})

// Collider with callback: player stomps enemy
this.physics.add.collider(this.player, enemies, (player, enemy) => {
 const p = player as Phaser.Types.Physics.Arcade.SpriteWithDynamicBody
 if (p.body.velocity.y > 0 && p.y < (enemy as Phaser.Physics.Arcade.Sprite).y) {
 (enemy as Phaser.Physics.Arcade.Sprite).disableBody(true, true)
 p.setVelocityY(-300) // bounce off enemy
 }
})
```

### 5. Wiring Phaser inside a Next.js / React page (no SSR)

```typescript
// components/GameCanvas.tsx
'use client'
import { useEffect, useRef } from 'react'

export default function GameCanvas() {
 const containerRef = useRef<HTMLDivElement>(null)

 useEffect(() => {
 let game: import('phaser').Game | null = null

 async function init() {
 const Phaser = (await import('phaser')).default
 const { GameScene } = await import('@/game/scenes/GameScene')
 game = new Phaser.Game({
 type: Phaser.AUTO,
 width: 1280, height: 720,
 parent: containerRef.current!,
 scene: [GameScene],
 })
 }
 init()
 return () => { game?.destroy(true) }
 }, [])

 return <div ref={containerRef} className="w-full aspect-video" />
}
```

## Concrete checks

- [ ] `Phaser.AUTO` selected — confirm WebGL in Chrome DevTools → canvas context.
- [ ] Atlas JSON matches the PNG key used in `this.load.atlas(key, png, json)`.
- [ ] `setCollisionByProperty({ collides: true })` matches the Tiled layer property name.
- [ ] `update()` reads input but never loads assets.
- [ ] `preload()` only in one scene (PreloadScene) — other scenes start after `'complete'`.
- [ ] Physics debug is gated on `import.meta.env.DEV` — never ships to production.
- [ ] `game.destroy(true)` called on React component unmount.
- [ ] Audio loaded with fallback formats `['.ogg', '.mp3']`.

## Commands

```bash
# Install Phaser 3 (latest stable)
npm install phaser

# Run dev server with HMR
npm run dev

# Production build
npm run build

# Preview production build locally
npm run preview

# Check bundle size (Phaser is ~1 MB minified)
npx vite-bundle-visualizer
```

## Required output

When reviewing or generating Phaser code, deliver:
1. Scene class with correct `constructor({ key })`, `preload`, `create`, `update` signatures.
2. Physics type used (Arcade vs Matter) with justification.
3. Atlas / tilemap key consistency check (load key == usage key).
4. Input wiring (keyboard cursor keys or pointer events).
5. Camera bounds and follow settings.
6. React/Next.js integration pattern if applicable (dynamic import, `game.destroy` cleanup).

## Safety checks

- Never mutate game objects inside `preload` — defer to `create`.
- Do not store Phaser object references in React state; use a `ref` to the `Game` instance.
- Confirm `this.physics.world` is defined before calling physics methods in `create`.
- Object pools via `group.get()` / `group.killAndHide()` — never `destroy()` pooled sprites.

## Completion criteria

Done means: a working Scene class compiles with `tsc --noEmit`, a dev server starts at `localhost:3000`, physics collisions are wired and verified in the debug overlay (in DEV), and any React integration mounts/unmounts cleanly without `game` memory leaks.

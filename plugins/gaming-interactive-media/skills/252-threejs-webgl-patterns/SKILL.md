---
name: threejs-webgl-patterns
description: Use when building 3D scenes in the browser with Three.js or React Three Fiber — covering Scene/Camera/Renderer setup, the render loop, GLTF loading, lighting, raycasting, and GPU-friendly instancing and frustum culling.
---

# Three.js & WebGL Patterns

## Purpose

Deliver production-ready Three.js patterns in TypeScript: Scene/Camera/Renderer bootstrap, a clean render loop, GLTF asset loading with Draco compression, PBR lighting rigs, pointer raycasting for interaction, GPU instancing for large object counts, and frustum culling. Also covers the React Three Fiber (r3f) integration path for React/Next.js projects.

## When to use

- Building a 3D product viewer, game environment, data visualisation, or interactive scene in the browser.
- Integrating a GLTF/GLB model exported from Blender, Figma, or a game engine.
- Setting up a physically-based rendering (PBR) lighting rig (env map, directional, ambient).
- Implementing mouse/touch picking (raycasting) to make 3D objects clickable.
- Rendering hundreds or thousands of identical objects efficiently (instancing).
- Adding Three.js to a Next.js 14+ App Router project via React Three Fiber.
- Profiling and reducing GPU frame time using Chrome DevTools and Spector.js.

## When not to use

- The game is 2D sprite-based — use `phaser-game-development` or `pixijs-2d-rendering`.
- The project needs a full game engine with physics, audio, and input as first-class concerns — consider Phaser or Babylon.js instead.
- The Three.js scene is trivially small and a CSS 3D transform would suffice.

## Procedure

### 1. Minimal Three.js + TypeScript + Vite setup

```bash
npm create vite@latest my-3d-app -- --template vanilla-ts
cd my-3d-app
npm install three
npm install -D @types/three
```

`src/main.ts` — self-contained renderer:
```typescript
import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js'
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js'

// --- Scene ---
const scene = new THREE.Scene()
scene.background = new THREE.Color(0x0d1117)
scene.fog = new THREE.FogExp2(0x0d1117, 0.02)

// --- Camera ---
const camera = new THREE.PerspectiveCamera(
 60, // fov
 window.innerWidth / window.innerHeight, // aspect
 0.1, // near
 1000, // far
)
camera.position.set(0, 3, 8)

// --- Renderer ---
const renderer = new THREE.WebGLRenderer({ antialias: true })
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2)) // cap at 2x
renderer.setSize(window.innerWidth, window.innerHeight)
renderer.shadowMap.enabled = true
renderer.shadowMap.type = THREE.PCFSoftShadowMap
renderer.toneMapping = THREE.ACESFilmicToneMapping
renderer.toneMappingExposure = 1.0
document.body.appendChild(renderer.domElement)

// --- Controls ---
const controls = new OrbitControls(camera, renderer.domElement)
controls.enableDamping = true
controls.dampingFactor = 0.05

// --- Lighting rig (PBR) ---
const ambient = new THREE.AmbientLight(0xffffff, 0.4)
scene.add(ambient)

const sun = new THREE.DirectionalLight(0xfff4e0, 1.5)
sun.position.set(5, 10, 5)
sun.castShadow = true
sun.shadow.mapSize.set(2048, 2048)
sun.shadow.camera.near = 0.5
sun.shadow.camera.far = 100
sun.shadow.camera.left = -20
sun.shadow.camera.right = 20
sun.shadow.camera.top = 20
sun.shadow.camera.bottom = -20
scene.add(sun)

// Environment map for reflections (load an HDR / EXR via RGBELoader in real projects)
const pmremGenerator = new THREE.PMREMGenerator(renderer)
scene.environment = pmremGenerator.fromScene(new THREE.RoomEnvironment()).texture
pmremGenerator.dispose()

// --- GLTF loader with Draco compression ---
const dracoLoader = new DRACOLoader()
dracoLoader.setDecoderPath('https://www.gstatic.com/draco/versioned/decoders/1.5.6/')

const gltfLoader = new GLTFLoader()
gltfLoader.setDRACOLoader(dracoLoader)

gltfLoader.load(
 '/models/scene.glb',
 (gltf) => {
 gltf.scene.traverse((child) => {
 if ((child as THREE.Mesh).isMesh) {
 child.castShadow = true
 child.receiveShadow = true
 }
 })
 scene.add(gltf.scene)
 },
 (progress) => console.log(`Loading: ${Math.round(progress.loaded / progress.total * 100)}%`),
 (error) => console.error('GLTF load error:', error),
)

// --- Resize handler ---
window.addEventListener('resize', () => {
 camera.aspect = window.innerWidth / window.innerHeight
 camera.updateProjectionMatrix()
 renderer.setSize(window.innerWidth, window.innerHeight)
})

// --- Render loop ---
const clock = new THREE.Clock()

function animate(): void {
 requestAnimationFrame(animate)
 const delta = clock.getDelta() // seconds since last frame
 controls.update() // required for damping
 renderer.render(scene, camera)
}
animate()
```

### 2. Raycasting — mouse picking

```typescript
const raycaster = new THREE.Raycaster()
const pointer = new THREE.Vector2()
const pickable: THREE.Object3D[] = [] // objects that can be clicked

renderer.domElement.addEventListener('pointerdown', (e) => {
 // Normalise to [-1, 1]
 pointer.x = (e.clientX / window.innerWidth) * 2 - 1
 pointer.y = -(e.clientY / window.innerHeight) * 2 + 1

 raycaster.setFromCamera(pointer, camera)
 const hits = raycaster.intersectObjects(pickable, true) // true = recursive

 if (hits.length > 0) {
 const hit = hits[0]
 console.log('Hit:', hit.object.name, 'at distance', hit.distance.toFixed(2))
 // Highlight: swap material
 const mesh = hit.object as THREE.Mesh
 ;(mesh.material as THREE.MeshStandardMaterial).emissive.set(0x334455)
 }
})
```

### 3. Instancing — render 10 000 trees in one draw call

```typescript
function buildForest(count: number): void {
 const geometry = new THREE.ConeGeometry(0.5, 2, 6)
 const material = new THREE.MeshStandardMaterial({ color: 0x2d6a4f })
 const mesh = new THREE.InstancedMesh(geometry, material, count)
 mesh.castShadow = true

 const dummy = new THREE.Object3D()
 for (let i = 0; i < count; i++) {
 dummy.position.set(
 (Math.random() - 0.5) * 200,
 0,
 (Math.random() - 0.5) * 200,
 )
 dummy.scale.setScalar(0.5 + Math.random() * 1.5)
 dummy.rotation.y = Math.random() * Math.PI * 2
 dummy.updateMatrix()
 mesh.setMatrixAt(i, dummy.matrix)
 }
 mesh.instanceMatrix.needsUpdate = true
 scene.add(mesh)
}
```

### 4. Frustum culling — skip off-screen objects

Three.js frustum-culls `Mesh` automatically if `mesh.frustumCulled = true` (default). For custom logic:

```typescript
const frustum = new THREE.Frustum()
const projection = new THREE.Matrix4()

function isVisible(obj: THREE.Object3D): boolean {
 projection.multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse)
 frustum.setFromProjectionMatrix(projection)
 if (obj instanceof THREE.Mesh) {
 obj.geometry.computeBoundingSphere()
 return frustum.intersectsSphere(obj.geometry.boundingSphere!)
 }
 return frustum.containsPoint(obj.position)
}
```

### 5. React Three Fiber (r3f) in Next.js App Router

```bash
npm install @react-three/fiber @react-three/drei three
npm install -D @types/three
```

```typescript
// components/Scene3D.tsx
'use client'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, Environment, useGLTF } from '@react-three/drei'
import { Suspense } from 'react'

function Model({ url }: { url: string }) {
 const { scene } = useGLTF(url)
 return <primitive object={scene} />
}

export default function Scene3D() {
 return (
 <Canvas
 shadows
 camera={{ position: [0, 3, 8], fov: 60 }}
 gl={{ antialias: true, toneMapping: 2 /* ACESFilmic */ }}
 >
 <ambientLight intensity={0.4} />
 <directionalLight position={[5, 10, 5]} intensity={1.5} castShadow
 shadow-mapSize={[2048, 2048]} />
 <Environment preset="city" />
 <Suspense fallback={null}>
 <Model url="/models/scene.glb" />
 </Suspense>
 <OrbitControls enableDamping dampingFactor={0.05} />
 </Canvas>
 )
}

// app/page.tsx (Server Component) — dynamic import avoids SSR
import dynamic from 'next/dynamic'
const Scene3D = dynamic(() => import('@/components/Scene3D'), { ssr: false })

export default function Page() {
 return <main className="w-full h-screen"><Scene3D /></main>
}
```

## Concrete checks

- [ ] `renderer.setPixelRatio(Math.min(devicePixelRatio, 2))` — prevents 4K GPU overload.
- [ ] Shadow map `mapSize` is power-of-two (512, 1024, 2048, 4096).
- [ ] GLTF `traverse` casts/receives shadows on all `Mesh` children.
- [ ] `controls.update()` called in the render loop when `enableDamping` is true.
- [ ] `camera.updateProjectionMatrix()` called after every `aspect` change.
- [ ] `InstancedMesh.instanceMatrix.needsUpdate = true` after setting matrices.
- [ ] r3f Canvas uses `ssr: false` in Next.js dynamic import.
- [ ] `PMREMGenerator.dispose()` called after environment map generation.

## Commands

```bash
# Install core + types
npm install three && npm install -D @types/three

# Install r3f + drei
npm install @react-three/fiber @react-three/drei

# Optimise GLTF with Draco (requires gltf-pipeline)
npx gltf-pipeline -i model.gltf -o model-draco.glb --draco.compressionLevel 7

# Inspect draw calls and GPU usage
# Open Chrome → F12 → Performance → Record (look for GPU frames)
# Or install Spector.js extension and capture a frame
```

## Required output

When building or reviewing a Three.js scene, deliver:
1. Renderer setup with pixel ratio cap, shadow map type, and tone mapping.
2. Lighting rig (ambient + directional + environment map).
3. GLTF loading with Draco decoder path and error handler.
4. Resize handler updating `camera.aspect` and `renderer.setSize`.
5. Instancing decision: used when > ~200 identical meshes, single draw call confirmed.
6. r3f integration path noted if project uses React.

## Safety checks

- Never call `renderer.render` outside the `requestAnimationFrame` callback.
- Dispose of geometries and materials when removing objects: `geo.dispose(); mat.dispose(); renderer.renderLists.dispose()`.
- Do not share a `WebGLRenderer` across React component mounts — each `<Canvas>` owns its renderer.
- Avoid `scene.add()` inside the render loop; modify scene graph in event handlers or loaders.

## Completion criteria

Done means: the scene renders at 60 fps in Chrome with no console errors, shadow maps are visible, the GLTF model loads and appears with PBR materials, raycasting selects the correct object on click, and the r3f page mounts/unmounts without `WebGL context lost` warnings.

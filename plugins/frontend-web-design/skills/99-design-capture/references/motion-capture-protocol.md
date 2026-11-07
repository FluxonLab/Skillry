# Live Motion Capture and Adaptation Protocol

Motion must be captured from the live running reference site rather than inferred from static screenshots. This protocol adapts the Record and Spec stages of motion decomposition, replacing 1:1 pixel cloning with token-based design system adaptation.

## 1. Live capture procedure (Record & Inspect)

1. **Fix the capture viewport and frame rate:**
   - Open the live reference URL in a real browser at a fixed desktop (e.g., `1440×900`) and mobile (e.g., `390×844`) viewport at `60 fps`.
   - Record separate short clips for:
     - Initial mount and entrance choreography.
     - Hover, focus, and active micro-interactions.
     - Scroll-linked or scrubbed transitions.
     - Modal, drawer, or page exit transitions.
2. **Extract live DOM and style facts via DevTools:**
   - Inspect computed styles: `transition-property`, `transition-duration`, `transition-timing-function`, `transition-delay`, `animation-name`, and `@keyframes`.
   - Query active Web Animations via the browser console:
     ```javascript
     document.getAnimations().map(anim => ({
       id: anim.id,
       timing: anim.effect?.getTiming(),
       keyframes: anim.effect?.getKeyframes()
     }));
     ```
   - Identify the underlying animation driver: CSS transitions/keyframes, `requestAnimationFrame`, scroll timelines (`ScrollTimeline` / `ViewTimeline`), Motion (`motiondivision/motion`), GSAP (`ScrollTrigger` / timelines), or WebGL/Three.js render loops.

## 2. Motion decomposition spec (Spec stage)

Before writing component animation code, record a motion specification table:

| Element / Role | Trigger | Reference timing (`delay` / `duration` / `curve`) | Reference delta (transform / opacity / filter) | Adapted project token & delta | Reduced-motion behavior |
| --- | --- | --- | --- | --- | --- |
| Hero primary card | `onMount` | `80ms` / `520ms` / `cubic-bezier(0.22, 1, 0.36, 1)` | `translateY(24px -> 0)`, `opacity(0 -> 1)` | `--motion-enter-slow` (`450ms`, `--ease-out-expo`), `translateY(16px -> 0)` | Instant `opacity(0 -> 1)` over `150ms`, zero translation |
| Interactive pill | `hover` | `0ms` / `180ms` / `ease-out` | `scale(1 -> 1.04)`, `box-shadow` | `--motion-interactive-fast` (`150ms`, spring), `scale(1 -> 1.02)` | Color tint change only, no scale transform |

### Mandatory adaptation rules

- **No 1:1 pixel diffing:** Never iterate toward pixel-diff parity against a third-party reference site. Replace pixel cloning with token-based adaptation.
- **Re-tokenize timings and distances:** Map captured durations, staggers, and easing curves onto the project's own design tokens (`--duration-fast`, `--duration-base`, `--ease-out`, spring tokens). Adjust travel distances and spatial layout to match target component proportions.
- **Compositor-first properties:** Animate `transform` (`translate3d`, `scale`, `rotate`) and `opacity`. Avoid animating layout-triggering properties (`top`, `left`, `width`, `height`, large `filter: blur()`) unless isolated and strictly budgeted.

## 3. Five-level motion verification ladder

Verify every implemented animation against all five levels before design acceptance:

1. **Level 1 — Measured project facts:**
   - Confirm colors, font families, SVG icons, and copy match the project's canonical tokens and asset files. Never allow placeholder or hallucinated brand data into animation frames.
2. **Level 2 — Rules and tokens over vague references:**
   - Every duration, delay, stagger, and easing curve in code references a named project token or explicit specification value, never an arbitrary magic number.
3. **Level 3 — States before effects:**
   - Define exact visible state at `t = 0` (Frame 1 must serve as a clean static poster/thumbnail), at midpoint, and at the settled end state. Test rapid interruptibility (fast mouse leave, quick scroll reversal).
4. **Level 4 — Deterministic frame on demand:**
   - Scrubbing or rendering the same timestamp twice must yield identical layout and visual state. Seed random, particle, or shader noise deterministically during verification.
5. **Level 5 — Contact sheet & reduced-motion check:**
   - Capture a contact sheet of stills at each beat plus the frames immediately before and after every transition boundary.
   - Verify `prefers-reduced-motion: reduce` disables spatial sweeps, parallax, and looping decorative movement while retaining essential state feedback.

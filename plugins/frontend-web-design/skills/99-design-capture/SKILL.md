---
name: design-capture
description: "Capture live reference motion, adapt UI components under source license rules, generate fresh exclusive media, and run unslop checks. Use when sourcing or adapting reference site designs."
---

# Design Capture and Adaptation

## Purpose

Capture structural layout, interaction patterns, and motion choreography from live reference websites, adapt sourced UI components to match the target project's design system and brand identity, generate site-exclusive visual media, and verify interface anti-slop criteria before release. The core principle is **adapt, never copy 1:1** — extracting underlying interaction mechanics and spatial rhythm while creating completely original code, tokens, copy, and media assets.

## Reference files

| Reference | File | Open it for |
| --- | --- | --- |
| Sources & licenses | [references/sources-and-licenses.md](references/sources-and-licenses.md) | Component registry licenses, usage boundaries (MIT, Commons Clause, unverified licenses), and anti-slop repositories |
| Motion capture protocol | [references/motion-capture-protocol.md](references/motion-capture-protocol.md) | Viewport recording setup, DevTools animation extraction, motion decomposition spec table, and 5-level verification ladder |

## Related skills

- `frontend-ui-engineering`: Production UI architecture, component APIs, Tailwind tokens, and shadcn/ui integration.
- `web-design-review`: Reviewing visual hierarchy, layout polish, and design-system consistency.
- `accessibility-audit`: Auditing keyboard navigation, ARIA semantics, contrast, and reduced-motion modes.
- `threejs-webgl-patterns`: Canvas-based 3D scenes, shaders, and WebGL animation pipelines.
- `i18n-locale-parity-review`: Localization parity, translated UI copy, and cultural typography adaptation.
- `frontend-performance-budget`: Frame rate budgets, layout thrashing prevention, and bundle size constraints.

## When to use

- Sourcing layout, micro-interactions, or animation choreography from live reference web applications.
- Adapting open-source or third-party registry components into a project's custom design tokens.
- Extracting exact animation curves, staggers, and durations from running browser pages rather than static screenshots.
- Generating dedicated, site-exclusive media so no graphic assets are reused across projects.
- Auditing adapted interfaces against AI-slop visual patterns and generic marketing copy before acceptance.

## When not to use

- Minor styling adjustments or routine bug fixes that do not source external designs.
- Attempting 1:1 pixel clones or scraping proprietary assets from third-party sites (strictly forbidden).
- Tasks involving non-visual backend logic, databases, or CLI tooling.

## Procedure

### 1. Establish the reference and adaptation ledger

Before writing component or animation code, inspect the approved reference URL and record an adaptation ledger. Read [references/sources-and-licenses.md](references/sources-and-licenses.md) for verified upstream details.

| Target surface | Reference URL or library item | Source license & status | Captured mechanics (layout / motion) | Planned adaptation (tokens, geometry, copy, media) | Verdict |
| --- | --- | --- | --- | --- | --- |
| Pricing card grid | `https://example.com/pricing` | Verified MIT | Hover tilt, staggered reveal | Project elevation tokens, custom spring curves, original copy | Approved |

Rules:
1. **Adapt, never copy 1:1:** Extract the interaction thesis, spatial rhythm, or choreography, then rebuild it for the project's own design tokens, grid, typography, copy, and domain concept. Never clone a third-party site's DOM, class names, brand palette, SVG graphics, copy, or pixel layout.
2. **Concept-first direction:** Anchor every interface in a domain-specific visual concept and explore three distinct directions before committing to an implementation.
3. **Label evidence honestly:** Mark every source attribute as **verified** (checked in primary repository/API or live capture), **vendor claim** (stated on vendor marketing page only), or **unverified**.

### 2. Capture motion from the live site, never from screenshots

Static screenshots lose trigger thresholds, stagger order, easing curves, spring physics, and scroll binding. Always capture motion from the running page. Read [references/motion-capture-protocol.md](references/motion-capture-protocol.md) for the full protocol.

1. **Record the live browser:** Film the active viewport in a real browser at a fixed desktop (e.g., `1440×900`) and mobile (e.g., `390×844`) resolution at `60 fps`, covering mount, hover/focus, scroll progression, and exit transitions.
2. **Inspect live DOM and animation hooks:** Using browser DevTools, extract computed `transition`, `animation`, `@keyframes`, CSS custom properties, active Web Animations (`element.getAnimations()`), and scroll timelines.
3. **Run motion decomposition:** Decompose each moving part into trigger event, start delay (`ms`), duration (`ms`), property delta, and easing curve or spring physics (`stiffness`, `damping`, `mass`).
4. **Adapt and re-tokenize:** Map captured curves and choreography onto project motion tokens and altered proportions. Never run 1:1 pixel-diff matching against a third-party reference site.
5. **Apply the 5-level motion check ladder:**
   - Level 1 (Measured facts): Use verified project colors, real copy, and real assets.
   - Level 2 (Rules over vague references): Convert observations into numeric tokens and component roles.
   - Level 3 (States before effects): Define exact visible state at key timestamps; Frame 1 must work as a standalone poster.
   - Level 4 (Deterministic frame on demand): Rendering the same timestamp twice produces identical state.
   - Level 5 (Contact sheet): Capture stills at each beat plus transition boundaries, and verify `prefers-reduced-motion`.

### 3. Verify component sources and license gates

Check candidate component libraries against verified license boundaries before adopting code:
- **shadcn/ui:** Verified MIT. Approved for own products and commercial templates. Restyle tokens, radii, spacing, interactive states, and typography; never ship unadapted stock styling.
- **21st.dev:** Tooling is ISC; individual component licenses vary and must be checked per item. Review automated tool write permissions; adapt layout, tokens, copy, and motion.
- **React Bits:** Verified MIT + Commons Clause v1.0. Approved for internal/own products with adaptation. **Never use in commercial templates, component packages, or UI kits sold to third parties.**
- **EasyUI & ObsidianUI:** Licenses unverified. Treat as trial/watch references only. Do not ship unverified third-party code in production; re-implement desired patterns cleanly from scratch.

### 4. Generate site-exclusive imagery and media

1. **Never reuse an image across sites:** Every site and product receives its own newly generated or uniquely captured visual assets. Never copy photos, textures, illustrations, or renders from the reference site, never reuse images across client projects, and avoid generic stock imagery.
2. **Dedicated media generation:** Produce visual assets using dedicated generative media workflows or original photography/3D captures.
3. **Asset verification and tracking:** Deliver settled media assets into the project's media directory with cryptographic hash verification (SHA-256) and record target surfaces so assets are never cross-contaminated between sites.

### 5. Run interface and copy anti-slop review

Every interface must pass a visual, structural, and copy anti-slop review before acceptance:
1. **Visual anti-slop:** Use interface critique tools (such as `heydamir/unslop`, CC BY 4.0) to inspect spacing rhythm, bounding-box alignment, border-radius consistency, and typography hierarchy across both light and dark themes. Maintain required upstream attribution if bundling critique templates.
2. **UI copy deslop:** Strip robotic AI writing tells, generic hero slogans ("Unleash your potential"), fake customer avatars, and awkward phrasing from all CTAs, onboarding flows, empty states, and error alerts.
3. **Reject common AI-slop defects:** Block default purple/indigo neon gradients, uniform 3-card icon grids, uncalibrated spring bounce, mismatched border radii, and placeholder text.

## Adapt-not-copy checklist

Every sourced reference or component must pass every item on this checklist before merge or release:

- [ ] **Visual concept:** Interface is anchored in a project-specific visual concept (3 directions explored), not the reference site's brand world.
- [ ] **Color & surface tokens:** 100% of colors, gradients, shadows, and surface elevations use the target project's design tokens; zero hex/HSL values copied verbatim from reference DOM.
- [ ] **Typography & scale:** Font families, weights, tracking, and type scale match the target project's design system at native device resolution.
- [ ] **Layout & geometry:** Grid proportions, aspect ratios, padding rhythm, border radii, and card density are restructured for project content rather than mirroring the reference 1:1.
- [ ] **DOM & code hygiene:** Component structure, prop APIs, state hooks, and CSS class names are written cleanly for project architecture; no scraped third-party class strings, comments, telemetry, or dead wrappers remain.
- [ ] **Live-captured, re-tokenized motion:** Motion was captured from the running reference (recording + DevTools inspection, never a static screenshot) and re-mapped to project motion tokens without 1:1 pixel diffing.
- [ ] **Motion check ladder:** Frame 1 works as a clean static poster; key timestamps have defined states; rendering is deterministic; a contact sheet and `prefers-reduced-motion` fallback are verified.
- [ ] **Source license compliance:** Component provenance is verified; Commons Clause items are excluded from sold commercial templates; unverified registries are excluded from production builds.
- [ ] **Site-exclusive media:** Every image, texture, and video was newly generated or captured for this project; zero cross-site image reuse and zero assets scraped from reference sites.
- [ ] **Anti-slop pass:** Interface cleared visual anti-slop critique and copy review in both light and dark themes with zero open visual or prose defects.

## Common issues & anti-patterns

- **Designing from static screenshots:** Missing trigger thresholds, staggers, easing curves, and scroll binding.
- **Pixel-diff cloning:** Attempting exact pixel parity against third-party designs rather than adapting underlying interaction mechanics into project tokens.
- **License contamination:** Shipping Commons Clause code in commercial templates or embedding unverified component registries in production deliverables.
- **Unadapted stock components:** Shipping default component styles without customizing border radii, typography scale, and brand palette tokens.
- **Media recycling:** Reusing illustrations, textures, or hero renders across multiple client sites instead of creating dedicated assets.
- **Ignoring reduced-motion:** Omitting `prefers-reduced-motion` fallbacks, causing accessibility failures for motion-sensitive users.
- **AI design clichés:** Relying on default neon purple gradients, floating glassmorphism blobs, generic 3-card feature grids, and robotic marketing jargon.

## Required output

Every design capture review must produce verified quality gates and a structured evidence packet:

### Quality gates

| Gate ID | Severity | Pass criteria | Required evidence |
| --- | --- | --- | --- |
| `design-capture/G0-license-and-provenance` | Blocking | Verified upstream licenses matching deliverable type (Commons Clause excluded from sold templates; unverified registries excluded from shipping builds). | Adaptation ledger table with source URLs, license statuses, and target product class. |
| `design-capture/G0-adapt-and-motion` | Blocking | Adapt-not-copy checklist passes; motion spec is derived from live capture and verified via 5-level ladder and reduced-motion audit. | Motion spec table, contact-sheet frames, and completed adapt-not-copy checklist. |
| `design-capture/G0-exclusive-media` | Blocking | All visual media is newly generated or uniquely captured for this project; zero cross-site reuse. | Media asset provenance manifest with SHA-256 verification hashes. |
| `design-capture/G0-anti-slop` | Blocking | Interface and copy clear visual and prose anti-slop reviews with zero open defects in light and dark themes. | Anti-slop review findings and resolved critique notes. |

### Evidence packet format

```text
gate: design-capture/<gate-id>
verdict: pass | fail | waived
scope: <project> <commit-or-build> <surface/viewport/theme>
evidence: <adaptation-ledger, motion-spec, contact-sheet-paths, media-manifest, anti-slop-verdict>
findings: <blocking: N, conditional: N, advisory: N>
waiver: <none | reason, approval, expiry>
date: <ISO-8601>
```

## Safety

- Never execute unvetted third-party scripts or copy-paste obfuscated snippet code from unverified registries.
- Never scrape copyrighted media, icons, or proprietary assets from reference sites.
- Review file-system and workspace permissions before running automated CLI or MCP tools.
- Keep credentials and API keys out of client code, configuration, and design artifacts.

## Completion criteria

The design capture workflow is complete when:
1. The adaptation ledger records all sourced references with verified upstream licenses and planned token adaptations.
2. Motion is captured from live browser execution, decomposed in a motion spec table, and verified against all five levels of the motion ladder including reduced motion.
3. Component code is restyled and re-tokenized into the project's design system with zero unadapted third-party classes or proprietary assets.
4. All visual imagery is newly generated or captured exclusively for this project with verified integrity hashes.
5. Visual layout and copy clear the anti-slop gate across light and dark themes.
6. The blocking quality gates pass and an evidence packet is recorded in project documentation.

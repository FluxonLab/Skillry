# Component, Motion, and Anti-Slop Sources

This reference catalogs verified upstream licenses, operational boundaries, and integration guidelines for component registries, animation libraries, and anti-slop design tools. Always inspect upstream license terms before adopting external code into commercial deliverables.

## 1. Component sources and license matrix

| Source | Primary URL / Repository | License & verification status | Integration mechanism | Operational rule |
| --- | --- | --- | --- | --- |
| **shadcn/ui** | `https://github.com/shadcn-ui/ui` | **MIT** (verified in repository). | CLI installation (`npx shadcn@latest add <component>`) or manual file copy. | Approved for own products and commercial templates. Restyle tokens, radii, spacing, interactive states, and typography; never ship unadapted stock styling. |
| **21st.dev & Magic MCP** | `https://21st.dev/`<br>`https://github.com/21st-dev/magic-mcp` | CLI/MCP repository: **ISC**. Component registry items: **unstated / variable per item**. | CLI / MCP initialization (`npx @21st-dev/cli@latest init`). Registry components follow shadcn layout. | Check provenance and license per component before adopting. Review file-write permissions before running automated tools. Adapt layout, tokens, copy, and motion—never copy verbatim. |
| **React Bits** | `https://reactbits.dev/`<br>`https://github.com/DavidHDev/react-bits` | **MIT + Commons Clause v1.0** (verified in repository). | Registry installation or copy-paste into project component tree. | **Own/internal products only.** The Commons Clause strictly forbids selling the software or including it in commercial UI kits or templates. Adapt structure, tokens, and motion; do not ship unchanged components. |
| **EasyUI** | `https://easyui.site/` | **License unclear / unverified.** Vendor page claims open source, but primary repository and SPDX license are not verified. | Registry or component snippets. | **Trial / watch only.** Do not ship EasyUI code in production or commercial deliverables until a primary repository and license are verified. Study interaction mechanics and re-implement cleanly. |
| **ObsidianUI** | `https://www.obsidianui.dev/components` | **License and pricing unverified.** Documentation mentions shadcn CLI setup without an independent verified license. | Component snippets or registry manifest. | **Trial / watch only.** Do not ship unverified code in production. Treat as visual or interaction reference only; implement desired patterns from scratch using project tokens. |

## 2. Motion analysis and animation libraries

| Source | Primary URL / Repository | License & verification status | Notes and boundaries |
| --- | --- | --- | --- |
| **/reanimate** | `https://github.com/NiazMorshed2007/reanimate`<br>`https://reanimate.niazmorshed.dev/` | **MIT** (verified in repository). | Provides a structured workflow (**Record -> Spec -> Build -> Verify**). Use its **Record** and **Spec** decomposition stages to extract live timing, distances, and curves. Replace its pixel-diff matching target with token-based adaptation. |
| **Motion** | `https://github.com/motiondivision/motion` | **MIT** (verified in repository). | Core web animation and gesture library. Verify whether advanced extensions (such as Motion+) are required before bundling. |
| **GSAP** | `https://github.com/greensock/GSAP` | Standard license allows free commercial use for most applications; paid license required for certain commercial redistributions. | Standard web animation engine. Inspect commercial redistribution terms when embedding in distributed templates or client libraries. |
| **Three.js** | `https://github.com/mrdoob/three.js` | **MIT** (verified in repository). | WebGL/3D scene rendering library. Pair with `threejs-webgl-patterns` for canvas-based interactive graphics. |
| **Motion check ladder** | Community practice | Process checklist. | Five-level motion verification: (1) measured brand facts, (2) numeric tokens over vague references, (3) explicit states before effects, (4) deterministic frame on demand, (5) contact sheet and reduced-motion audit. |

## 3. Anti-slop tools and references

| Source | Primary URL / Repository | License & verification status | Notes and boundaries |
| --- | --- | --- | --- |
| **unslop** (`heydamir`) | `https://github.com/heydamir/unslop` | **CC BY 4.0** (verified in repository). | Transforms generic, AI-looking interfaces into intentional, polished designs. Note distinction from other repositories with identical names. Preserve CC BY 4.0 attribution if bundling templates. |
| **impeccable** | `https://github.com/pbakaus/impeccable` | **Apache-2.0** (verified in repository). | Design polish guidelines focusing on micro-typography, optical alignment, and surface consistency. |
| **stop-slop** | `https://github.com/hardikpandya/stop-slop` | **MIT** (verified in repository). | Strips repetitive AI writing tells, generic SaaS hero slogans, and awkward phrasing across multiple languages. |
| **Concept-first design** | Practice framework | Process pattern. | Ground interfaces in a specific domain metaphor: define concept -> explore 3 distinct directions -> build at native device resolution -> run anti-slop critique -> refine. |
| **Visual deslop inspection** | Practice checklist | Audit technique. | Inspect spacing rhythm, border-radius consistency, typography scales, and high-contrast light and dark themes. |

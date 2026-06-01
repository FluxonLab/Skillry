---
name: frontend-performance-budget
description: Use when you need to set and enforce frontend performance budgets — Core Web Vitals beyond the basics (LCP, INP, CLS attribution), JavaScript and asset size budgets, lazy loading, hydration cost, and Lighthouse CI gates in a pipeline.
---

# Frontend Performance Budget

## Purpose

Establish enforceable frontend performance budgets and wire them into CI so regressions fail the build instead of shipping. This goes past "LCP is 2.5s good" surface advice: it attributes each Core Web Vital to a concrete cause (render-blocking resource, layout shift source, long task), sets byte budgets per asset class, and measures the real cost of hydration and client-side JavaScript. The output is a budget file plus a Lighthouse CI configuration that other engineers can run locally and in the pipeline.

## When to use

- A page feels slow on mid-tier mobile or a real-user-monitoring (RUM) tool reports poor LCP, INP, or CLS at p75.
- A PR adds a large dependency, a hero image, a font, or a third-party script and you need a size/perf impact gate.
- The team ships a SPA or SSR/RSC app and nobody has a JavaScript byte budget.
- Lighthouse scores swing between deploys and there is no CI gate to catch regressions.
- Hydration is suspected of blocking interactivity on a server-rendered page.

## When not to use

- The artifact is a backend API or CLI with no browser surface — use backend latency profiling instead.
- The page is an internal tool with a tiny, known audience on fast hardware where the budget would be disproportionate.
- The slowdown is clearly a server response-time problem (high TTFB) rather than a client asset problem — fix the server path first.

## Procedure

1. **Capture a baseline on throttled mobile.** Never measure on an unthrottled desktop; it hides the real cost. Run Lighthouse with mobile emulation and a 4x CPU slowdown, and record LCP, INP (or TBT as a lab proxy), CLS, TTFB, and total transferred bytes by resource type.
2. **Attribute each metric to a cause.** LCP: which element is the LCP element, and what delays it (TTFB, render-blocking CSS/JS, late-discovered image, font swap)? CLS: which DOM nodes shift and why (image without dimensions, injected banner, web-font reflow)? INP: which interaction is slow and which long task blocks the main thread?
3. **Set byte budgets per asset class.** Assign hard ceilings: total JS (compressed), CSS, images, fonts, and third-party. A common mobile-first starting point is ~170 KB compressed JS for the initial route, but derive yours from the device and network of the real audience.
4. **Audit lazy loading and code splitting.** Confirm below-the-fold images use `loading="lazy"`, routes are code-split, and heavy components are dynamically imported. Verify the LCP image is NOT lazy-loaded (that delays it).
5. **Measure hydration cost.** For SSR/RSC apps, measure how much JavaScript hydrates and how long the main thread is blocked after first paint. Prefer streaming, partial hydration, or server components for static regions.
6. **Wire Lighthouse CI with assertions.** Add a `lighthouserc.js` with budget assertions so the pipeline fails when a metric or byte budget regresses.
7. **Track at p75 in RUM, not just lab.** Lab numbers find regressions; field (RUM) numbers tell you what users actually experience. Reconcile the two.

## Concrete checks

- [ ] Lighthouse was run with mobile emulation and CPU throttling (not desktop defaults).
- [ ] The LCP element is identified and is not lazy-loaded; it is preloaded if late-discovered.
- [ ] Every `<img>` and media element has explicit `width`/`height` or an aspect-ratio box (prevents CLS).
- [ ] Fonts use `font-display: swap` (or `optional`) and are preloaded if critical.
- [ ] No render-blocking third-party script sits in the critical path; non-critical scripts are `async`/`defer` or loaded post-interaction.
- [ ] A per-asset-class byte budget exists and the initial-route JS is within it.
- [ ] Routes and heavy components are code-split / dynamically imported.
- [ ] A `lighthouserc.js` (or equivalent) enforces budgets in CI and fails on regression.
- [ ] RUM p75 for LCP, INP, and CLS is tracked and reconciled against lab numbers.
- [ ] Long tasks (>50 ms) on the main thread during initial interaction are identified.
- [ ] Late-loading embeds/ads/iframes have reserved space so they do not cause layout shift.
- [ ] The production bundle is minified and tree-shaken (no dev build or source maps shipped to users).

## Commands or Templates

```bash
# One-off Lighthouse run, mobile + throttling, JSON output
npx lighthouse https://example.com/page \
  --preset=perf \
  --form-factor=mobile \
  --throttling.cpuSlowdownMultiplier=4 \
  --output=json --output-path=./lh-report.json --quiet

# Extract the three Core Web Vitals + total byte weight from the report
node -e '
  const r = require("./lh-report.json");
  const a = r.audits;
  const m = (id) => a[id] && a[id].numericValue;
  console.log("LCP(ms):", m("largest-contentful-paint"));
  console.log("TBT(ms):", m("total-blocking-time"));
  console.log("CLS:", m("cumulative-layout-shift"));
  console.log("TotalBytes:", a["total-byte-weight"].numericValue);
'

# Inspect bundle composition (Vite / Rollup)
npx vite build && npx vite-bundle-visualizer
# or for webpack
npx webpack --profile --json=stats.json && npx webpack-bundle-analyzer stats.json
```

```javascript
// lighthouserc.js — Lighthouse CI budget gates
module.exports = {
  ci: {
    collect: {
      url: ['http://localhost:3000/'],
      numberOfRuns: 3,
      settings: { preset: 'perf', formFactor: 'mobile', throttlingMethod: 'simulate' },
    },
    assert: {
      assertions: {
        'largest-contentful-paint': ['error', { maxNumericValue: 2500 }],
        'cumulative-layout-shift': ['error', { maxNumericValue: 0.1 }],
        'total-blocking-time': ['error', { maxNumericValue: 200 }],
        'interactive': ['warn', { maxNumericValue: 3800 }],
        // byte budgets by resource type (bytes)
        'resource-summary:script:size': ['error', { maxNumericValue: 175000 }],
        'resource-summary:image:size': ['warn', { maxNumericValue: 300000 }],
        'resource-summary:font:size': ['warn', { maxNumericValue: 100000 }],
        'resource-summary:third-party:size': ['warn', { maxNumericValue: 150000 }],
      },
    },
    upload: { target: 'temporary-public-storage' },
  },
};
```

```json
// budget.json — standalone Lighthouse budget (also usable via --budget-path)
[
  {
    "path": "/*",
    "resourceSizes": [
      { "resourceType": "script", "budget": 170 },
      { "resourceType": "stylesheet", "budget": 60 },
      { "resourceType": "image", "budget": 300 },
      { "resourceType": "font", "budget": 100 },
      { "resourceType": "total", "budget": 700 }
    ],
    "resourceCounts": [
      { "resourceType": "third-party", "budget": 10 }
    ]
  }
]
```

## Common issues & anti-patterns

- **Measuring on desktop.** Unthrottled desktop hides the JS execution cost that dominates on mid-tier mobile; always emulate mobile + CPU throttling.
- **Lazy-loading the LCP image.** `loading="lazy"` on the hero image delays the very metric you are trying to improve.
- **Treating the Lighthouse score as the goal.** The 0–100 score is a weighted composite; optimize the underlying metrics (LCP/INP/CLS), not the number.
- **No byte budget, only time budget.** Time metrics drift with hardware; a byte budget is a stable, reviewable gate on every PR.
- **Shipping the whole bundle to render static content.** Hydrating server-rendered static regions wastes main-thread time; use partial hydration / server components.
- **Fonts with no `font-display` and no preload.** Causes invisible text then a reflow that spikes CLS.
- **Counting only first-load.** INP regressions show up during interaction, not initial load — measure interaction latency too.
- **Unsized embeds and ads.** Late-loading iframes, ad slots, and banners injected above content push everything down and spike CLS; reserve space for them.
- **Importing a whole library for one function.** Pulling in an entire date or utility library for a single helper bloats the bundle; import the specific function or use a lighter alternative.
- **Blocking the critical path on web fonts.** Waiting for a custom font before painting text delays LCP; use `font-display: swap` and a system-font fallback stack.
- **Shipping source maps or dev builds to production.** Unminified or dev-mode bundles multiply byte weight and parse time; verify the production build is minified and tree-shaken.

## Required output

Produce a report containing:
1. **Baseline table** — LCP, INP/TBT, CLS, TTFB, and bytes-by-type at mobile + throttled, lab and RUM p75 side by side.
2. **Attribution** — for each failing metric, the specific cause (element, resource, or long task) with file or URL reference.
3. **Budget definition** — the committed `budget.json` / `lighthouserc.js` with per-asset-class ceilings and metric thresholds.
4. **Findings** — ranked list of regressions or violations, each with the byte/time delta and the concrete fix.
5. **CI gate status** — whether the pipeline now fails on regression and where the config lives.
6. **Next safe action** — the single highest-leverage fix (usually the LCP cause or the largest JS chunk).

## Safety

- Run Lighthouse and bundle analysis against local or staging builds; do not load-test or hammer production from CI.
- Do not commit secrets or auth tokens into `lighthouserc.js` collect URLs; use environment variables for authenticated runs.
- Make budget thresholds advisory (`warn`) first, then promote to `error` once the team agrees, so you do not block unrelated PRs on day one.
- Do not delete or rewrite existing build configuration without approval; add budget files alongside it.
- Treat third-party script removal as a product decision — flag it, do not silently strip analytics or consent tooling.

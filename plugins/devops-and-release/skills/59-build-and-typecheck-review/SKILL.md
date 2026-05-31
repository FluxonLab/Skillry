---
name: build-and-typecheck-review
description: Use when you need to review build, typecheck, compile, bundling, and static validation commands.
---

# Build and Typecheck Review

## Purpose

Verify that the project builds cleanly with strict static analysis, catch TypeScript errors or compiler warnings that are suppressed or ignored, review `tsconfig.json` strictness settings, assess bundle size and tree-shaking configuration, confirm source maps are generated correctly, and identify build tooling anti-patterns that cause silent failures or non-reproducible builds.

## When to use

- `tsc --noEmit` is failing in CI and you need to triage and fix the errors.
- A PR introduces `// @ts-ignore` or `@ts-expect-error` comments without justification.
- The `tsconfig.json` has been modified and you want to confirm strict mode is preserved.
- Bundle size has grown unexpectedly and you need to identify the cause.
- The build passes locally but fails in CI (environment-dependent build issues).
- A new package is added and may not be tree-shakeable, increasing bundle size.

## When not to use

- The project uses JavaScript only (no TypeScript) — skip the typecheck steps.
- The task is to implement a feature, not to review the build configuration.
- Build issues are in a Docker layer or deployment step — use the deployment preflight skill.

## Procedure

1. **Run `tsc --noEmit` and capture output.** This runs the type checker without emitting files, giving the full error list. If the project uses `ts-project-references`, run `tsc --build --noEmit` instead. Count errors by file and error code.

2. **Review `tsconfig.json` strict settings.** Check for these options explicitly:
 - `"strict": true` — enables all strict checks in one flag.
 - If `strict` is false or absent, check individual flags: `noImplicitAny`, `strictNullChecks`, `strictFunctionTypes`, `noUncheckedIndexedAccess`.
 - `"skipLibCheck": true` — acceptable for most projects; note if it is hiding errors in `.d.ts` files the project owns.
 - `"noEmitOnError": true` — confirms the build does not produce output when type errors exist.

3. **Audit `// @ts-ignore` and `@ts-expect-error` usage.** Run `grep -rn "@ts-ignore\|@ts-expect-error" src/`. For each occurrence, determine:
 - Is there a comment explaining why suppression is needed?
 - Is it suppressing a real type error that should be fixed?
 - Is `@ts-expect-error` used instead of `@ts-ignore` (preferred — fails if the error disappears)?

4. **Check `any` usage.** Run `grep -rn ": any\|as any\| any " src/ --include="*.ts" --include="*.tsx"`. Explicit `any` is a type safety hole. Flag usages in non-test files, especially in function signatures and return types.

5. **Verify build reproducibility.** Confirm the build output hash is stable across two consecutive builds from a clean state. Non-reproducible builds suggest timestamp injection, random IDs in output, or non-deterministic module ordering.

6. **Review bundle size and tree-shaking.** If a bundler is used (webpack, Rollup, esbuild, Vite), check:
 - Is `sideEffects: false` set in `package.json` for library packages?
 - Are dynamic imports (`import()`) used for code splitting on large page sections?
 - Run `npx bundlesize` or check the CI bundle size check if configured.
 - Flag packages imported entirely when only one utility is needed (`import _ from 'lodash'` instead of `import debounce from 'lodash/debounce'`).

7. **Check source map configuration.** For production builds:
 - Source maps should be generated but not served publicly (they expose source code).
 - Confirm `devtool: 'source-map'` (external) not `'inline-source-map'` (embeds in bundle, increases size).
 - Confirm the CI artifact includes source maps in a separate upload to an error tracking service (Sentry, Datadog).

8. **Verify build command consistency.** The build command in `package.json` scripts, the CI workflow, and the Dockerfile must all call the same command (`npm run build`), not different commands that may have different flags or environments.

9. **Check for build warnings treated as errors.** TypeScript's `--noUnusedLocals` and `--noUnusedParameters` should be enabled to prevent dead code accumulation. Confirm that build warnings in the bundler (circular dependency, missing exports) are surfaced, not suppressed with `// eslint-disable`.

10. **Review path aliases.** If `tsconfig.json` defines `paths` aliases (`@components`, `@utils`), confirm the bundler config has the matching aliases, and the Jest config also has matching `moduleNameMapper`. Misaligned aliases cause "module not found" errors that only appear in one context.

## Checklist

- [ ] `tsc --noEmit` exits with zero errors.
- [ ] `"strict": true` (or equivalent individual flags) is in `tsconfig.json`.
- [ ] `"noEmitOnError": true` is set.
- [ ] All `@ts-ignore` usages have an explanatory comment; none suppress real correctness bugs.
- [ ] `as any` and `: any` usages in non-test code are minimal and justified.
- [ ] Build output is reproducible (same hash on two consecutive clean builds).
- [ ] Bundle size is within defined thresholds (or thresholds are defined if missing).
- [ ] Dynamic imports are used for large page sections.
- [ ] Source maps are external, not inline, in production builds.
- [ ] Path aliases are consistent across `tsconfig.json`, bundler config, and Jest config.
- [ ] `--noUnusedLocals` and `--noUnusedParameters` are enabled.

## Common issues & anti-patterns

- **`strict: false` inherited from a template**: teams disable strict mode to suppress initial errors and never re-enable it; type safety degrades over time.
- **`skipLibCheck: true` hiding owned `.d.ts` errors**: if the project generates `.d.ts` files, their errors are also skipped.
- **Build succeeds but emits with errors**: `noEmitOnError` is false; the build produces broken JS from TypeScript files with type errors.
- **`as unknown as Foo` cast chains**: `foo as unknown as Bar` defeats the type checker entirely — equivalent to `any` without the grep signal.
- **Full lodash import in a bundle**: `import _ from 'lodash'` pulls in ~73KB minified; `import debounce from 'lodash/debounce'` pulls in ~2KB.
- **Timestamp in bundle output filename without content hash**: `bundle.2026-05-31.js` invalidates CDN cache by date, not by content change; use `bundle.[contenthash].js`.
- **Mismatched `target` and `lib`**: `target: "es5"` with `lib: ["esnext"]` generates ES5 code that calls ES2022 methods not present at runtime.
- **Circular dependency between modules**: bundles silently work (modules initialize in undefined order) until an edge case triggers an undefined reference at runtime.

## Required output

```
## Build and Typecheck Review

### TypeScript errors
- Total errors: N
- Errors by file (top 5): file path — N errors
- Error codes by frequency: TS2345 (N), TS2322 (N), ...

### tsconfig.json strictness
| Option | Value | Status |
|--------|-------|--------|
| strict | true/false | ok/risk |
| noEmitOnError | ... | ... |
| noUnusedLocals | ... | ... |

### Type suppression audit
- @ts-ignore usages: N (N without explanatory comment)
- as any usages in non-test code: N
- Files with most suppressions: list

### Bundle analysis (if bundler configured)
- Total bundle size (gzip): X KB
- Largest chunks: list
- Whole-library imports detected: list
- Tree-shaking: enabled/disabled

### Source maps
- Format: external / inline / none
- CI upload to error tracker: yes/no

### Path alias consistency
- tsconfig paths: list
- Bundler aliases match: yes/no
- Jest moduleNameMapper match: yes/no

### Recommended fixes (priority order)
1. ...
```

## Safety

- Run only `tsc --noEmit`, `grep`, and read-only file inspection. Do not run `tsc` with emit, `npm run build`, or bundler commands unless the user asks.
- Do not modify `tsconfig.json`, `package.json`, or bundler config without explicit user instruction.

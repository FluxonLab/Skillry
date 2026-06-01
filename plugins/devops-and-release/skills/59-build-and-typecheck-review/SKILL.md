---
name: build-and-typecheck-review
description: Use when you need to review build, typecheck, compile, bundling, and static validation commands.
---

# Build and Typecheck Review

## Purpose

Verify the project builds cleanly with strict static analysis, catch suppressed or ignored TypeScript errors and compiler warnings, review `tsconfig.json` strictness, assess bundle size and tree-shaking, confirm source maps are generated correctly, and identify build-tooling anti-patterns that cause silent failures or non-reproducible builds. The review runs read-only static checks (`tsc --noEmit`, `grep`) and never emits build output or mutates config without instruction.

## When to use

- `tsc --noEmit` is failing in CI and you need to triage and fix the errors.
- A PR introduces `// @ts-ignore` or `@ts-expect-error` without justification.
- `tsconfig.json` was modified and you want to confirm strict mode is preserved.
- Bundle size has grown unexpectedly and you need to identify the cause.
- The build passes locally but fails in CI (environment-dependent build issues).
- A new package is added and may not be tree-shakeable.

## When not to use

- The project is JavaScript only (no TypeScript) — skip the typecheck steps.
- The task is to implement a feature, not to review the build configuration.
- Build issues are in a Docker layer or deployment step — use `60-deployment-preflight-review`.

## Procedure

1. **Run `tsc --noEmit` and capture output.** Type-check without emitting files for the full error list. For project references, run `tsc --build --noEmit`. Count errors by file and by error code.
2. **Review `tsconfig.json` strict settings.** Check `"strict": true`; if absent, check `noImplicitAny`, `strictNullChecks`, `strictFunctionTypes`, `noUncheckedIndexedAccess`. Note `skipLibCheck: true` if it hides errors in `.d.ts` files the project owns. Confirm `noEmitOnError: true`.
3. **Audit `@ts-ignore` / `@ts-expect-error`.** For each: is there a comment explaining why? Is it hiding a real error that should be fixed? Is `@ts-expect-error` used (preferred — fails if the error disappears)?
4. **Check `any` usage.** Flag explicit `any` in non-test code, especially in function signatures and return types — it is a type-safety hole.
5. **Verify build reproducibility.** Confirm the output hash is stable across two consecutive clean builds. Instability suggests timestamp injection, random IDs, or non-deterministic module ordering.
6. **Review bundle size and tree-shaking.** Check `sideEffects: false` for library packages; dynamic `import()` for large sections; whole-library imports (`import _ from 'lodash'`) that should be path imports.
7. **Check source map configuration.** Production maps should be external (`devtool: 'source-map'`), not inline; not served publicly; uploaded to an error tracker.
8. **Verify build command consistency.** `package.json` scripts, the CI workflow, and the Dockerfile must call the same build command.
9. **Check warnings treated as errors.** `--noUnusedLocals` and `--noUnusedParameters` enabled; bundler warnings (circular dependency, missing exports) surfaced, not suppressed.
10. **Review path aliases.** `tsconfig.json` `paths` must match the bundler config and Jest `moduleNameMapper`; mismatches cause "module not found" in only one context.

## Concrete checks

- [ ] `tsc --noEmit` exits with zero errors.
- [ ] `"strict": true` (or equivalent individual flags) is set in `tsconfig.json`.
- [ ] `"noEmitOnError": true` is set.
- [ ] All `@ts-ignore` usages have an explanatory comment; none suppress real correctness bugs.
- [ ] `as any` and `: any` usages in non-test code are minimal and justified.
- [ ] Build output is reproducible (same hash on two consecutive clean builds).
- [ ] Bundle size is within defined thresholds (or thresholds are defined if missing).
- [ ] Dynamic imports are used for large page sections.
- [ ] Source maps are external, not inline, in production builds.
- [ ] Path aliases are consistent across `tsconfig.json`, bundler config, and Jest config.
- [ ] `--noUnusedLocals` and `--noUnusedParameters` are enabled.

## Commands or Templates

```bash
# Type gate: full error list, no emit (use --build for project references)
npx tsc --noEmit 2>&1 | tee /tmp/tsc.txt
grep -oE "error TS[0-9]+" /tmp/tsc.txt | sort | uniq -c | sort -rn   # errors by code

# Strictness flags actually in effect
npx tsc --showConfig | grep -E '"strict"|"noImplicitAny"|"strictNullChecks"|"noEmitOnError"|"noUnusedLocals"'

# Suppressions and any-holes in non-test code
grep -rn "@ts-ignore\|@ts-expect-error" src/
grep -rnE ":\s*any\b|as any|as unknown as " src/ --include="*.ts" --include="*.tsx"

# Whole-library imports that defeat tree-shaking
grep -rnE "import .* from ['\"](lodash|moment|rxjs)['\"]" src/

# Reproducibility: hash output twice from clean
rm -rf dist && npm run build >/dev/null 2>&1 && find dist -type f -exec sha256sum {} + | sort > /tmp/b1
rm -rf dist && npm run build >/dev/null 2>&1 && find dist -type f -exec sha256sum {} + | sort > /tmp/b2
diff /tmp/b1 /tmp/b2 && echo "reproducible" || echo "NON-REPRODUCIBLE"
```

## tsconfig strictness reference

`"strict": true` is the umbrella; when it is off, audit these individually because each closes a real class of bug:

| Flag | What it catches | Risk if off |
|------|-----------------|-------------|
| `noImplicitAny` | params/vars with no inferable type | silent `any` everywhere |
| `strictNullChecks` | `undefined`/`null` not in the type | `Cannot read properties of undefined` at runtime |
| `strictFunctionTypes` | unsound callback parameter variance | wrong-shaped callbacks accepted |
| `noUncheckedIndexedAccess` | `arr[i]` assumed defined | out-of-bounds reads typed as present |
| `noEmitOnError` | emitting JS despite type errors | broken build artifacts ship |
| `noUnusedLocals`/`Parameters` | dead bindings | code rot accumulates |

`skipLibCheck: true` is acceptable for third-party `.d.ts` noise, but if the project *generates* its own declaration files, it also silences their errors — note that explicitly.

## Worked error triage

`tsc --noEmit` reports 38 errors. Grouping by code (the command in the templates) shows: 31× `TS2532 Object is possibly 'undefined'`, 5× `TS2345`, 2× `TS7006`. The 31 `TS2532` errors all trace to one source: `strictNullChecks` was just enabled and array/map lookups are no longer assumed defined. The fix is not 31 `as` casts — it is a few guard patterns at the lookup sites (`const u = users.get(id); if (!u) return;`). Triaging by error *code* rather than by file reveals that most of the count is a single root cause, so the report should say "31 errors, one cause (missing null guards after enabling strictNullChecks), ~6 guard sites to fix" — not "38 unrelated errors".

## Common issues & anti-patterns

- **`strict: false` inherited from a template.** Teams disable strict mode to suppress initial errors and never re-enable it; type safety degrades.
- **`skipLibCheck: true` hiding owned `.d.ts` errors.** Errors in generated declaration files the project ships are also skipped.
- **Build succeeds but emits with errors.** `noEmitOnError` is false; the build produces broken JS from files with type errors.
- **`as unknown as Foo` cast chains.** Defeat the type checker entirely — equivalent to `any` without the grep signal for `any`.
- **Full lodash import.** `import _ from 'lodash'` pulls ~73KB minified; `import debounce from 'lodash/debounce'` pulls ~2KB.
- **Date-stamped bundle filename without content hash.** `bundle.2026-05-31.js` invalidates CDN cache by date, not content; use `bundle.[contenthash].js`.
- **Mismatched `target` and `lib`.** `target: "es5"` with `lib: ["esnext"]` emits ES5 that calls ES2022 methods absent at runtime.
- **Circular dependency.** Bundles work until an edge case triggers an undefined reference at runtime; surface the warning.
- **Incremental build cache hiding errors.** A stale `tsBuildInfo` or bundler cache can report success on code that no longer compiles clean; verify from a clean state when in doubt.
- **`transpileOnly` / Babel type-stripping treated as a typecheck.** `ts-node --transpileOnly`, `esbuild`, and `swc` strip types without checking them; the only real type gate is `tsc --noEmit`. A green dev server says nothing about type correctness.

## Verify the typecheck is real

A frequent false signal is "the app runs, so types are fine". Dev servers and bundlers transpile by stripping types, not checking them — so type errors pass straight through to runtime. Always run a dedicated `tsc --noEmit` (or `tsc --build --noEmit` for references) as the gate, separate from the build/run step, and confirm it is wired into CI. If the project's "typecheck" script secretly runs the bundler, it is not a type gate; flag that as a finding.

## "Passes locally, fails in CI"

This recurring class almost always traces to an environment difference, not a real code change. Check, in order:

- **Filesystem case sensitivity.** macOS/Windows are case-insensitive; Linux CI is not. `import './Utils'` for a file named `utils.ts` passes locally and fails in CI with "module not found". Grep imports against actual filenames.
- **Dependency drift.** Local `node_modules` was built from a stale lockfile; CI does a clean `npm ci`. A version that exists locally but not in the lockfile resolves differently. Reproduce with a clean install.
- **`tsconfig` resolution differences.** A `paths` alias resolved by the IDE/`ts-node` locally but absent from the bundler or `tsc` build config used in CI.
- **Node/TypeScript version mismatch.** Local Node 22 vs CI Node 18; a syntax or `lib` feature differs. Confirm `engines` and the CI matrix agree.
- **Case-only env differences.** A type that depends on `process.env.NODE_ENV` being set narrows differently when the var is unset in CI.

The fix is to make the local environment match CI (clean install, same Node, Linux-equivalent case behavior) and reproduce the failure — not to add a suppression so the local build stays green while CI stays red.

## Required output

```
## Build and Typecheck Review
### TypeScript errors
- Total: N | Top files: path — N | Codes by frequency: TS2345 (N), TS2322 (N)
### tsconfig.json strictness
| Option | Value | Status |
### Type suppression audit
- @ts-ignore: N (N without comment) | as any in non-test: N | files with most suppressions
### Bundle analysis (if bundler configured)
- Total (gzip): X KB | Largest chunks | Whole-library imports | Tree-shaking enabled/disabled
### Source maps
- Format: external/inline/none | CI upload to error tracker: yes/no
### Path alias consistency
- tsconfig paths | Bundler match: yes/no | Jest moduleNameMapper match: yes/no
### Recommended fixes (priority order)
1. ...
```

## Safety

- Run only `tsc --noEmit`, `grep`, and read-only file inspection. Do not run `tsc` with emit, `npm run build`, or bundler commands unless the user asks (the reproducibility check is opt-in).
- Do not modify `tsconfig.json`, `package.json`, or bundler config without explicit user instruction.
- Do not weaken strictness flags to make errors disappear; report them instead.

## Completion criteria

Done means `tsc --noEmit` was run and its errors counted by file and code, strictness flags were audited, suppressions and `any` holes were listed with `file:line`, bundle and source-map config were assessed, alias consistency was checked, and fixes are ordered by priority.

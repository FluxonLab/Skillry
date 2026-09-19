# React 18 Automatic Batching Patterns

> **Reference of `frontend-ui-engineering`.** Formerly the standalone skill `react18-batching-patterns`; the routing table in [../SKILL.md](../SKILL.md) sends that name and its topics here.
>
> - Origin: third-party, [github/awesome-copilot](https://github.com/github/awesome-copilot); previously `community/github-awesome-copilot/skills/react18-batching-patterns/`.
> - License: MIT, Copyright GitHub, Inc. (upstream `LICENSE` checked 2026-09-19, blob 89bc5e96, identical to the vendored copy); copy kept at [react18-batching-patterns/LICENSE](react18-batching-patterns/LICENSE).
> - Paths: file paths in the body are relative to the skill directory (the folder holding `SKILL.md`).
> - Earlier Skillry import: vendored from `github-awesome-copilot` on 2026-05-31.
> - Consolidation changes: frontmatter moved into this header; paths to its own reference files now point to the moved copies; body otherwise unchanged.

<details><summary>Former frontmatter (kept for provenance)</summary>

```yaml
name: react18-batching-patterns
description: 'Provides exact patterns for diagnosing and fixing automatic batching regressions in React 18 class components. Use this skill whenever a class component has multiple setState calls in an async method, inside setTimeout, inside a Promise .then() or .catch(), or in a native event handler. Use it before writing any flushSync call - the decision tree here prevents unnecessary flushSync overuse. Also use this skill when fixing test failures caused by intermediate state assertions that break after React 18 upgrade.'
```

</details>

Reference for diagnosing and fixing the most dangerous silent breaking change in React 18 for class-component codebases.

## The Core Change

| Location of setState | React 17 | React 18 |
|---|---|---|
| React event handler | Batched | Batched (same) |
| setTimeout | **Immediate re-render** | **Batched** |
| Promise .then() / .catch() | **Immediate re-render** | **Batched** |
| async/await | **Immediate re-render** | **Batched** |
| Native addEventListener callback | **Immediate re-render** | **Batched** |

**Batched** means: all setState calls within that execution context flush together in a single re-render at the end. No intermediate renders occur.

## Quick Diagnosis

Read every async class method. Ask: does any code after an `await` read `this.state` to make a decision?

```
Code reads this.state after await?
  YES → Category A (silent state-read bug)
  NO, but intermediate render must be visible to user?
    YES → Category C (flushSync needed)
    NO → Category B (refactor, no flushSync)
```

For the full pattern for each category, read:
- **`references/react18-batching-patterns/references/batching-categories.md`** - Category A, B, C with full before/after code
- **`references/react18-batching-patterns/references/flushSync-guide.md`** - when to use flushSync, when NOT to, import syntax

## The flushSync Rule

**Use `flushSync` sparingly.** It forces a synchronous re-render, bypassing React 18's concurrent scheduler. Overusing it negates the performance benefits of React 18.

Only use `flushSync` when:
- The user must see an intermediate UI state before an async operation begins
- A spinner/loading state must render before a fetch starts
- Sequential UI steps have distinct visible states (progress wizard, multi-step flow)

In most cases, the fix is a **refactor** - restructuring the code to not read `this.state` after `await`. Read `references/react18-batching-patterns/references/batching-categories.md` for the correct approach per category.

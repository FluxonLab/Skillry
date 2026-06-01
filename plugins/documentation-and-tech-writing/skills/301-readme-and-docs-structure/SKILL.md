---
name: readme-and-docs-structure
description: Use when you need to structure or restructure a project README and a documentation site — defining required sections, a 5-minute quickstart, a navigable table of contents, and a docs-as-code layout that lives in the repo and builds in CI.
---

# README and Docs Structure

## Purpose

Define a predictable, navigable information architecture for a project's entry-point README and its larger documentation site. Cover the required README sections in reading order, a quickstart that gets a new user to first success in under five minutes, a table of contents that scales, and a docs-as-code layout (Markdown in the repo, built by a static site generator, validated in CI). The goal is that a newcomer can install, run, and find any topic without asking a maintainer.

## When to use

- A new project has no README, or the README is a single unstructured paragraph.
- A docs site is being introduced (MkDocs, Docusaurus, Sphinx, Hugo) and needs a navigation tree.
- Users repeatedly ask questions that the docs should already answer.
- The README has drifted: install steps are stale, badges are broken, links 404.
- You are splitting one giant README into a structured `docs/` tree.

## When not to use

- A throwaway script or spike with no users and no expected lifetime.
- The repo already has a strong, tested docs structure and only one section needs an edit — edit that section directly.
- The request is purely about API reference generation (use api-reference-docs) or release notes (use changelog-and-release-notes).

## Procedure

### 1. Inventory the current state

```bash
# Find every doc-like file and the README
find . -maxdepth 3 \( -name "README*" -o -name "*.md" -o -name "*.rst" \) \
  -not -path './node_modules/*' -not -path './.git/*' | sort

# Detect an existing docs generator
ls mkdocs.yml docusaurus.config.* docs/conf.py book.toml hugo.toml 2>/dev/null
cat mkdocs.yml docusaurus.config.js 2>/dev/null | head -40
```

### 2. Confirm the README has the required sections, in order

A complete README, top to bottom: project name + one-line value statement; status badges (build, version, license); a short "What is this / Why" paragraph; Quickstart (install + minimal run); Usage with one real example; Configuration (env vars, flags); Links to deeper docs; Contributing; License. Anything longer than a screen of detail belongs in `docs/`, linked — not inline.

### 3. Write a 5-minute quickstart

The quickstart must be copy-pasteable and produce visible success. Prerequisites first, then exact commands, then the expected output so the reader can self-verify.

```bash
# Verify the documented install path actually works from a clean checkout
git clone <repo-url> /tmp/docs-smoke && cd /tmp/docs-smoke
# run the exact commands from the quickstart, unmodified, and compare output
```

### 4. Design the table of contents / navigation tree

Group by user goal, not by source-code layout. A scalable top level: Getting Started, Guides (how-to), Reference, Concepts (explanation), Operations, Contributing. Keep nesting to two levels where possible.

```yaml
# mkdocs.yml — nav grouped by user intent
nav:
  - Home: index.md
  - Getting Started:
      - Installation: getting-started/install.md
      - Quickstart: getting-started/quickstart.md
  - Guides:
      - Configure auth: guides/auth.md
  - Reference:
      - CLI: reference/cli.md
      - API: reference/api.md
  - Concepts: concepts/architecture.md
  - Operations: operations/runbook.md
```

### 5. Establish docs-as-code

Docs live beside code in `docs/`, are reviewed in the same pull request as the change they describe, and are built and link-checked in CI. Pin the generator version so builds are reproducible.

### 6. Wire link checking and a build gate into CI

```bash
# Build must succeed (fail the job on warnings)
mkdocs build --strict          # MkDocs
# or: npm run build             # Docusaurus

# Catch dead internal/external links
npx --yes markdown-link-check -q docs/**/*.md
# or: lychee --no-progress docs/ README.md
```

## Concrete checks

- [ ] README opens with the project name and a single-sentence value statement.
- [ ] Badges (build, version, license) render and point to live targets.
- [ ] A Quickstart exists, is copy-pasteable, and shows expected output.
- [ ] The Quickstart was run from a clean checkout and succeeded unmodified.
- [ ] Every long topic is in `docs/` and linked, not pasted inline in the README.
- [ ] The docs navigation is grouped by user goal, not by folder layout.
- [ ] Navigation nesting is at most two levels deep.
- [ ] No heading is skipped (no jump from `#` to `###`).
- [ ] Internal and external links pass a link checker.
- [ ] The docs site builds with `--strict` (or equivalent) in CI on every PR.
- [ ] The docs generator version is pinned in the lockfile or config.
- [ ] A single canonical entry point (index/home) links to all top-level sections.

## Templates

```markdown
# ProjectName

> One sentence: what it does and who it is for.

![build](badge-url) ![version](badge-url) ![license](badge-url)

## What is this
Two or three sentences on the problem solved and when to reach for it.

## Quickstart
Prerequisites: <runtime + version>

    <install command>
    <minimal run command>

Expected output:

    <the exact lines a working setup prints>

## Usage
One realistic example with input and output.

## Configuration
| Variable      | Required | Default | Description          |
|---------------|----------|---------|----------------------|
| `SERVICE_URL` | yes      | —       | Upstream service URL |

## Documentation
- [Guides](docs/guides/) · [Reference](docs/reference/) · [Concepts](docs/concepts/)

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md).

## License
MIT — see [LICENSE](LICENSE).
```

## Common issues & anti-patterns

- A wall-of-text README with no headings or table of contents.
- Quickstart commands that assume hidden state (a pre-seeded DB, an unset env var) and fail for a new user.
- Navigation that mirrors the `src/` tree instead of user goals.
- Duplicated content: the same install steps in the README and in `docs/`, drifting apart over time.
- Badges hardcoded to a green/passing image instead of the live CI/registry endpoint.
- Docs in a separate repo or wiki that no one updates in the same PR as the code change.
- Skipped heading levels and multiple `#` H1s on one page, breaking the auto-generated ToC.

## Required output

Produce: (1) a gap list of missing or out-of-order README sections; (2) a proposed `docs/` tree and navigation config; (3) the rewritten Quickstart with verified expected output; (4) the CI build + link-check command to add; (5) a prioritized fix list (broken links and stale install steps first).

## Safety

- Do not invent commands or output — run the quickstart from a clean checkout and paste real results.
- Never commit secrets into examples; use placeholder env var names only.
- Do not delete existing docs; move and redirect, preserving history.
- Keep changes scoped to documentation files unless the user approves touching build config.

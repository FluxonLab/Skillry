<div align="center">

<img src="https://raw.githubusercontent.com/FluxonLab/Skillry/main/assets/social-preview.png" alt="Skillry - multi-platform agent skills and agents" width="680">

# Skillry

**Reusable, permission-bounded skills and agents for Claude Code, OpenAI Codex, Gemini, and GitHub Copilot.**

One maintained library, adapted to each supported runtime without taking ownership of a project's
instruction files.

[Quickstart](#portable-installation) | [Platform contract](#platform-contract) | [Organization](#how-work-is-organized) | [Contributing](CONTRIBUTING.md)

[![CI](https://github.com/FluxonLab/Skillry/actions/workflows/validate.yml/badge.svg)](https://github.com/FluxonLab/Skillry/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## What Skillry provides

- Platform-ready skills and agent definitions maintained from a shared library.
- Capability routing across product, web, backend, mobile, desktop, UX, accessibility, SEO/GEO,
  games, AI, data, platform, SRE, security, QA, media, assets, and knowledge operations.
- Least-privilege agent boundaries and explicit attribution for redistributed community content.
- A dry-run-first portable installer so users can inspect destinations and changes before writing.

Skillry is a capability library, not a simulated company. Departments are discovery and routing
labels. They do not create permanent autonomous teams or require every task to pass through a
fixed organization chart.

## Portable installation

Preview is the default and writes nothing:

~~~bash
npx github:FluxonLab/Skillry install
~~~

After reviewing the plan, apply it explicitly:

~~~bash
npx github:FluxonLab/Skillry install --apply
~~~

Targets can be limited. For example:

~~~bash
npx github:FluxonLab/Skillry install --targets claude codex
npx github:FluxonLab/Skillry install --apply --targets claude codex
~~~

The dry-run for the selected release is the authority for exact destination paths and planned
changes. Do not infer a destination from an old README, marketplace layout, or another runtime.

## Platform contract

The portable installer installs only platform skills and agent definitions.

| Platform | Installed payload | Project instructions remain project-owned |
|---|---|---|
| Claude Code | Skills and Claude-compatible agents | CLAUDE.md |
| OpenAI Codex | Skills and Codex-compatible agent profiles | AGENTS.md |
| Gemini | Skills and Gemini-compatible agents | GEMINI.md and AGENTS.md |
| GitHub Copilot | Skills and Copilot-compatible custom agents | .github/copilot-instructions.md and AGENTS.md |

The installer does **not** copy, generate, merge, append, reconcile, back up, or otherwise modify
project CLAUDE.md, AGENTS.md, GEMINI.md, or Copilot instruction files. Those files express local
project policy and must be authored and maintained by that project.

The repository's own CLAUDE.md and AGENTS.md govern contributions to Skillry. They are not portable
templates and are not installer payloads.

## How work is organized

Skillry favors a small orchestration model:

1. One lead owns scope, decisions, context, and the final result.
2. One writer applies a change, avoiding concurrent edits to the same artifact.
3. Temporary subagents are used only for bounded specialist work that benefits from isolation or
   parallelism. Each returns evidence, decisions, open questions, and a concise handoff, then ends.
4. Skills use progressive disclosure: route from metadata, load the selected SKILL.md, and open
   supporting references only when the task requires them.
5. Departments form a capability graph for routing and coverage. They are not standing managerial
   layers, mandatory queues, or personas kept alive between tasks.

This keeps routine work direct while retaining specialist depth for genuinely independent or
high-risk work.

## Library structure

- plugins/<department>/ contains first-party skills and agents grouped for discovery.
- community/<source>/ contains attributed third-party material with its upstream license.
- registry/ records distributable inventory and provenance.
- tools/ contains repository maintenance and portable installation tooling.
- docs/ contains public guides and durable project documentation.
- CLAUDE.md and AGENTS.md contain repository-only contributor instructions.

Counts and compatibility claims can change. Prefer the current registry, release notes, installer
dry-run, and primary platform documentation over copied summaries.

## Safety and provenance

- Give each agent only the tools and access its task requires.
- Keep review and audit work read-only unless mutation is explicitly requested.
- Treat third-party skills and agents as untrusted until their source, license, permissions, and
  behavior have been reviewed.
- Separate community material from first-party material and preserve upstream attribution.
- Make evidence-backed claims. Mark assumptions and unverified behavior instead of presenting them
  as facts.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for authoring and review requirements. Contributors working
inside this repository must also follow [CLAUDE.md](CLAUDE.md) or [AGENTS.md](AGENTS.md), depending
on the runtime they use. These files describe the same repository contract; neither is a template
for unrelated projects.

Security issues should be reported through [SECURITY.md](SECURITY.md). Governance and release
policy are documented in [GOVERNANCE.md](GOVERNANCE.md).

## License and credits

Original Skillry work is available under the [MIT License](LICENSE). Redistributed community
content retains its upstream license and attribution; see [NOTICE](NOTICE) and
[THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).

Built and maintained by [FluxonLab](https://fluxonlab.com).

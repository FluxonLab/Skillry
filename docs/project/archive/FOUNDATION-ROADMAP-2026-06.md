# Historical Foundation Roadmap - June 2026

This is a portable summary of the pre-publication roadmap. It is historical context, not current
scope. Counts and unresolved choices were superseded by the released repository.

## Original positioning

Build an installable, permission-bounded agent skill and subagent package for Claude Code, Codex,
Copilot, and Gemini from one source of truth. Differentiate through multi-platform delivery,
least-privilege agents, department organization, validation, and safe third-party import.

## Foundation phases

1. Create a clean public repository and remove private paths and product-specific references.
2. Migrate and deepen original skills and agents into department plugins.
3. Separate permissively licensed third-party content under `community/` with full attribution.
4. Add a portable installer, validation harness, marketplace, and checksum registries.
5. Add `skill-sync` for discovery, normalization, license checks, and risk scanning.
6. Add CI, documentation, repository polish, and publish the first release.

## Outcome

The foundation roadmap was substantially completed in v1.0.0-v1.2.0:

- 125 original skills and 73 original agents.
- 98 community skills and 49 community agents.
- 18 department plugins.
- npm and GitHub/npx distribution.
- Generated cross-platform instructions.
- Validation, lockfiles, CI, attribution, and security policies.

The original open decisions about the repository name, single-repository strategy, npm CLI, and
initial content depth are therefore closed or superseded.

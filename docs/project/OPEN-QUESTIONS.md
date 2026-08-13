# Open Questions Before Implementation Planning

## Objective

1. Is the first objective contributor quality, package security, trigger accuracy, provenance, or
   maintainer visibility?
2. What measurable result defines success: fewer manual review steps, stronger CI, safer packages,
   better skill selection, or improved platform compatibility?

## Scope

3. Does the first phase apply only to original content or also to `community/`?
4. Is a bulk metadata migration acceptable, or must the first phase remain migration-free?
5. Should generated review output be committed, generated locally, or attached to releases?
6. Should the historical launch material remain public documentation after the handoff is merged?

## Validation

7. Which new checks are immediate failures, warnings, information, or human gates?
8. Should package-surface and secret scanning become dedicated Python checks or remain CI shell
   steps?
9. Which fixtures prove generator behavior without creating snapshot churn?
10. Which platform-specific model calls, if any, are acceptable for trigger evaluations?

## Source of truth

11. Should skill metadata live in frontmatter, a separate schema-backed registry, or both?
12. Should generated lockfiles remain content-only inventories?
13. Where should excluded third-party sources and reasons live?

## Candidate governance branch

14. Does draft PR `#3` preserve `CLAUDE.md` as the canonical shared source?
15. Is `project.factory.yaml` appropriate for a public portable library?
16. Should its tests and generator improvements be adapted independently from its governance
   content?

## Release

17. Is the future target a documentation-only merge, a patch/minor npm release, or a broader
   governance release?
18. How far should supply-chain hardening go in the first approved release: package allowlist,
   provenance, attestations, or SBOM?

## Planning output

19. When the maintainer says "move to planning," should the output be one file-level implementation
   plan, an ADR plus plan, or a phased execution plan?
20. Which decision owner must approve CI-breaking behavior, metadata migration, external service
   activation, and release promotion?

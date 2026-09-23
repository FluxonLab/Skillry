# Changelog

All notable changes to Skillry are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/), and this project adheres to
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Optional Jev advisory helper: ten bounded modes, verified client inventories,
  explicit public-data policy, local duplicate suppression and no execution authority.
- Native Cursor skill and agent installation, including Cursor-specific agent
  metadata and hash verification for Jev selection.

### Fixed

- Repository adapter generation no longer overwrites canonical AGENTS.md or
  reactivates historical Factory policy. CI checks freshness without writes.
- Portable installation remains skills/agents only; five-target release checks
  include Cursor without copying project instruction files.

## [3.0.0] - 2026-09-19

### Breaking

- Skillry consolidates 223 skills into 57 skill hubs (54 under `plugins/`, 3 under
  `community/addyosmani-agent-skills/` and `community/wshobson-agents/`). 166 skill names are no longer
  standalone skills: each absorbed skill's `SKILL.md` is now `references/<former-name>.md` inside its
  hub, with its other files under `references/<former-name>/` (scripts, templates, assets and examples
  under `scripts|templates|assets|examples/<former-name>/`). Nested `SKILL.md` files are renamed
  `README.md` so Codex does not discover them as separate skills. Each reference starts with a
  provenance header (former path, origin, license, edits). Only repository metadata (upstream README,
  CHANGELOG, plugin manifests, `agents/openai.yaml`) and a few generic lines that repeated the hub were
  dropped; each header lists them.
- Every hub `SKILL.md` has a routing table from former name to reference and a new description of at
  most 117 characters, so the full library fits Codex's default skill-listing budget with every
  description shown.
- `$former-name` and `/former-name` no longer resolve. Invoke the hub and open the reference; the
  table below maps every former name.
- Agent `skills:` lists and `Primary skills:` lines are rebound to hubs and deduplicated: the 130
  planned rebinds across 68 Skillry agents, plus `docs-reviewer`, `technical-writer`,
  `web-game-engineer` and 13 Donchitos community agents that bound absorbed skills. No agent lists
  more than seven skills.
- Install scope moved with content: community skills merged into `plugins/` hubs now install by
  default, while the Skillry original `shadcn-ui-components` now lives in the community hub
  `frontend-ui-engineering` and installs only with `--community`. `api-test-suite-review` lives in the
  default hub `playwright-e2e-audit`, and `e2e-flow-designer` binds only default-install skills.
- The `documentation-and-tech-writing` plugin now ships agents only; its skills merged into
  `technical-writing-review` (`product-docs-and-research`).

### Added

- 44 third-party skills imported into hubs from 17 upstream repositories (15 new to Skillry) after a
  license gate: permissive license (MIT, or Apache-2.0 for `foundation-lean-canvas`) verified from the
  upstream LICENSE file at a pinned commit, local copy compared with upstream, LICENSE copied beside the
  content. See the import table below and `THIRD-PARTY-NOTICES.md`.
- `registry/community-source-lock.json`: 216 new commit-pinned entries (225 targets) for imported
  files that are byte-identical to upstream, verified against upstream on 2026-09-19. The 34 existing
  entries now target the moved files (hashes unchanged).

### Changed

- `tools/release-gate.py` accepts source-lock sidecar targets under
  `plugins/<department>/skills/<hub>/` as well as `community/<source>/skills/<hub>/`, and verifies their
  installed copies the same way.
- Plugin descriptions (and `marketplace.json`) describe what each plugin ships after the merge.
- `NOTICE`, `THIRD-PARTY-NOTICES.md`, `community/README.md`, each `community/<source>/README.md`,
  `GOVERNANCE.md`, `CONTRIBUTING.md`, `SECURITY.md`, `README.md` and `docs/INSTALL.md` document where
  merged third-party content lives and the new counts.
- The CI install smoke test expects at least 50 installed skills (was 100).

### Not imported

- `seo-geo-audit` and `geo-visibility`: a license was claimed only in frontmatter and no upstream
  repository or LICENSE file could be found. They were not copied, and `seo-content-ops-review`
  covers GEO through the imported `geo-*` references.

### Former skill locations

Paths are relative to the hub directory.

| Former skill | Hub | Hub directory | Reference | Origin |
|---|---|---|---|---|
| `adr-generator` | `architecture-review` | `plugins/core-operations/skills/03-architecture-review` | `references/adr-generator.md` | Skillry original |
| `agent-governance-review` | `ai-security-review` | `plugins/security/skills/48-ai-security-review` | `references/agent-governance-review.md` | Skillry original |
| `agent-supply-chain-review` | `dependency-supply-chain-review` | `plugins/security/skills/50-dependency-supply-chain-review` | `references/agent-supply-chain-review.md` | Skillry original |
| `ai-prompt-engineering-safety-review` | `prompt-systems-review` | `plugins/ai-and-agent-systems/skills/42-prompt-systems-review` | `references/ai-prompt-engineering-safety-review.md` | community/github-awesome-copilot |
| `ai-studio-prototype-review` | `prompt-systems-review` | `plugins/ai-and-agent-systems/skills/42-prompt-systems-review` | `references/ai-studio-prototype-review.md` | Skillry original |
| `android-material-review` | `mobile-app-review` | `plugins/mobile-desktop/skills/25-mobile-app-review` | `references/android-material-review.md` | Skillry original |
| `api-design-principles` | `api-and-interface-design` | `plugins/backend-and-api/skills/12-api-and-interface-design` | `references/api-design-principles.md` | community/wshobson-agents |
| `api-playwright-test-developer` | `test-driven-development` | `community/addyosmani-agent-skills/skills/test-driven-development` | `references/api-playwright-test-developer.md` | community/jaktestowac-awesome-copilot-for-testers |
| `api-reference-docs` | `technical-writing-review` | `plugins/product-docs-and-research/skills/69-technical-writing-review` | `references/api-reference-docs.md` | Skillry original |
| `api-test-suite-review` | `playwright-e2e-audit` | `plugins/testing-and-qa/skills/53-playwright-e2e-audit` | `references/api-test-suite-review.md` | Skillry original |
| `async-python-patterns` | `python-project-review` | `plugins/backend-and-api/skills/94-python-project-review` | `references/async-python-patterns.md` | community/wshobson-agents |
| `authz-permission-review` | `auth-session-review` | `plugins/backend-and-api/skills/14-auth-session-review` | `references/authz-permission-review.md` | Skillry original |
| `automation-mcp-gatekeeping` | `ai-security-review` | `plugins/security/skills/48-ai-security-review` | `references/automation-mcp-gatekeeping.md` | Skillry original |
| `bats-testing-patterns` | `test-driven-development` | `community/addyosmani-agent-skills/skills/test-driven-development` | `references/bats-testing-patterns.md` | community/wshobson-agents |
| `bazel-build-optimization` | `monorepo-turborepo-review` | `plugins/optional-specialist/skills/88-monorepo-turborepo-review` | `references/bazel-build-optimization.md` | community/wshobson-agents |
| `breakdown-feature-implementation` | `implementation-plan` | `plugins/core-operations/skills/04-implementation-plan` | `references/breakdown-feature-implementation.md` | community/github-awesome-copilot |
| `browser-first-local-app` | `local-launcher-shortcuts` | `plugins/runtime-and-local-app/skills/10-local-launcher-shortcuts` | `references/browser-first-local-app.md` | Skillry original |
| `browser-testing-with-devtools` | `playwright-e2e-audit` | `plugins/testing-and-qa/skills/53-playwright-e2e-audit` | `references/browser-testing-with-devtools.md` | community/addyosmani-agent-skills |
| `build-and-typecheck-review` | `smoke-test-and-repair` | `plugins/testing-and-qa/skills/52-smoke-test-and-repair` | `references/build-and-typecheck-review.md` | Skillry original |
| `caching-strategy` | `backend-latency-profiling` | `plugins/performance-and-cost/skills/322-backend-latency-profiling` | `references/caching-strategy.md` | Skillry original |
| `changelog-and-release-notes` | `technical-writing-review` | `plugins/product-docs-and-research/skills/69-technical-writing-review` | `references/changelog-and-release-notes.md` | Skillry original |
| `cloud-spend-review` | `cost-control-token-review` | `plugins/optional-specialist/skills/86-cost-control-token-review` | `references/cloud-spend-review.md` | Skillry original |
| `codebase-cartography` | `repo-diagnostics` | `plugins/core-operations/skills/01-repo-diagnostics` | `references/codebase-cartography.md` | Skillry original |
| `codex-final-execution-prompt` | `prompt-systems-review` | `plugins/ai-and-agent-systems/skills/42-prompt-systems-review` | `references/codex-final-execution-prompt.md` | Skillry original |
| `context-engineering` | `project-agent-bootstrap` | `plugins/core-operations/skills/89-project-agent-bootstrap` | `references/context-engineering.md` | community/addyosmani-agent-skills |
| `copilot-sdk` | `agent-workflow-design` | `plugins/ai-and-agent-systems/skills/40-agent-workflow-design` | `references/copilot-sdk.md` | community/github-awesome-copilot |
| `core-web-vitals` | `frontend-performance-budget` | `plugins/performance-and-cost/skills/321-frontend-performance-budget` | `references/core-web-vitals.md` | community/addyosmani-web-quality-skills |
| `dashboard-ux-review` | `web-design-review` | `plugins/frontend-web-design/skills/18-web-design-review` | `references/dashboard-ux-review.md` | Skillry original |
| `data-migration-safety` | `database-and-prisma-review` | `plugins/database-and-data/skills/35-database-and-prisma-review` | `references/data-migration-safety.md` | Skillry original |
| `data-quality-validation` | `data-pipeline-review` | `plugins/data-ml-ai-engineering/skills/311-data-pipeline-review` | `references/data-quality-validation.md` | Skillry original |
| `database-migration` | `database-and-prisma-review` | `plugins/database-and-data/skills/35-database-and-prisma-review` | `references/database-migration.md` | community/wshobson-agents |
| `dataset-versioning-and-lineage` | `data-pipeline-review` | `plugins/data-ml-ai-engineering/skills/311-data-pipeline-review` | `references/dataset-versioning-and-lineage.md` | Skillry original |
| `debugging-strategies` | `runtime-diagnostics` | `plugins/runtime-and-local-app/skills/08-runtime-diagnostics` | `references/debugging-strategies.md` | community/wshobson-agents |
| `deploy-topology-and-rollback` | `release-readiness-check` | `plugins/core-operations/skills/06-release-readiness-check` | `references/deploy-topology-and-rollback.md` | Skillry original |
| `deployment-preflight-review` | `release-readiness-check` | `plugins/core-operations/skills/06-release-readiness-check` | `references/deployment-preflight-review.md` | Skillry original |
| `design-system-review` | `web-design-review` | `plugins/frontend-web-design/skills/18-web-design-review` | `references/design-system-review.md` | Skillry original |
| `designing-functional-tests` | `uat-acceptance-review` | `plugins/testing-and-qa/skills/57-uat-acceptance-review` | `references/designing-functional-tests.md` | community/jaktestowac-awesome-copilot-for-testers |
| `designing-test-data` | `uat-acceptance-review` | `plugins/testing-and-qa/skills/57-uat-acceptance-review` | `references/designing-test-data.md` | community/jaktestowac-awesome-copilot-for-testers |
| `desktop-launcher-review` | `local-launcher-shortcuts` | `plugins/runtime-and-local-app/skills/10-local-launcher-shortcuts` | `references/desktop-launcher-review.md` | Skillry original |
| `docker-image-hardening` | `cloud-service-architecture` | `plugins/cloud-and-infrastructure/skills/334-cloud-service-architecture` | `references/docker-image-hardening.md` | Skillry original |
| `docs-quality-review` | `technical-writing-review` | `plugins/product-docs-and-research/skills/69-technical-writing-review` | `references/docs-quality-review.md` | Skillry original |
| `e2e-testing-patterns` | `playwright-e2e-audit` | `plugins/testing-and-qa/skills/53-playwright-e2e-audit` | `references/e2e-testing-patterns.md` | community/wshobson-agents |
| `electron-app-security-review` | `security-and-secrets-review` | `plugins/security/skills/47-security-and-secrets-review` | `references/electron-app-security-review.md` | Skillry original |
| `embedding-strategies` | `rag-vector-search-review` | `plugins/ai-and-agent-systems/skills/43-rag-vector-search-review` | `references/embedding-strategies.md` | community/wshobson-agents |
| `env-config-hardening` | `security-and-secrets-review` | `plugins/security/skills/47-security-and-secrets-review` | `references/env-config-hardening.md` | Skillry original |
| `error-handling-patterns` | `error-handling-observability` | `plugins/backend-and-api/skills/16-error-handling-observability` | `references/error-handling-patterns.md` | community/wshobson-agents |
| `fastapi-templates` | `python-project-review` | `plugins/backend-and-api/skills/94-python-project-review` | `references/fastapi-templates.md` | community/wshobson-agents |
| `game-performance-review` | `game-architecture-review` | `plugins/gaming-interactive-media/skills/29-game-architecture-review` | `references/game-performance-review.md` | Skillry original |
| `game-ui-ux-review` | `gameplay-systems-review` | `plugins/gaming-interactive-media/skills/30-gameplay-systems-review` | `references/game-ui-ux-review.md` | Skillry original |
| `gamedev-art-bible` | `gameplay-systems-review` | `plugins/gaming-interactive-media/skills/30-gameplay-systems-review` | `references/gamedev-art-bible.md` | community/Donchitos-Claude-Code-Game-Studios |
| `gamedev-balance-check` | `gameplay-systems-review` | `plugins/gaming-interactive-media/skills/30-gameplay-systems-review` | `references/gamedev-balance-check.md` | community/Donchitos-Claude-Code-Game-Studios |
| `gamedev-brainstorm` | `gameplay-systems-review` | `plugins/gaming-interactive-media/skills/30-gameplay-systems-review` | `references/gamedev-brainstorm.md` | community/Donchitos-Claude-Code-Game-Studios |
| `gamedev-code-review` | `game-architecture-review` | `plugins/gaming-interactive-media/skills/29-game-architecture-review` | `references/gamedev-code-review.md` | community/Donchitos-Claude-Code-Game-Studios |
| `gamedev-design-review` | `gameplay-systems-review` | `plugins/gaming-interactive-media/skills/30-gameplay-systems-review` | `references/gamedev-design-review.md` | community/Donchitos-Claude-Code-Game-Studios |
| `gamedev-estimate` | `implementation-plan` | `plugins/core-operations/skills/04-implementation-plan` | `references/gamedev-estimate.md` | community/Donchitos-Claude-Code-Game-Studios |
| `gamedev-hotfix` | `release-readiness-check` | `plugins/core-operations/skills/06-release-readiness-check` | `references/gamedev-hotfix.md` | community/Donchitos-Claude-Code-Game-Studios |
| `gamedev-map-systems` | `gameplay-systems-review` | `plugins/gaming-interactive-media/skills/30-gameplay-systems-review` | `references/gamedev-map-systems.md` | community/Donchitos-Claude-Code-Game-Studios |
| `gamedev-perf-profile` | `game-architecture-review` | `plugins/gaming-interactive-media/skills/29-game-architecture-review` | `references/gamedev-perf-profile.md` | community/Donchitos-Claude-Code-Game-Studios |
| `gamedev-prototype` | `gameplay-systems-review` | `plugins/gaming-interactive-media/skills/30-gameplay-systems-review` | `references/gamedev-prototype.md` | community/Donchitos-Claude-Code-Game-Studios |
| `gamedev-release-checklist` | `release-readiness-check` | `plugins/core-operations/skills/06-release-readiness-check` | `references/gamedev-release-checklist.md` | community/Donchitos-Claude-Code-Game-Studios |
| `gamedev-retrospective` | `implementation-plan` | `plugins/core-operations/skills/04-implementation-plan` | `references/gamedev-retrospective.md` | community/Donchitos-Claude-Code-Game-Studios |
| `gamedev-team-audio` | `gameplay-systems-review` | `plugins/gaming-interactive-media/skills/30-gameplay-systems-review` | `references/gamedev-team-audio.md` | community/Donchitos-Claude-Code-Game-Studios |
| `gamedev-team-combat` | `gameplay-systems-review` | `plugins/gaming-interactive-media/skills/30-gameplay-systems-review` | `references/gamedev-team-combat.md` | community/Donchitos-Claude-Code-Game-Studios |
| `gamedev-team-level` | `gameplay-systems-review` | `plugins/gaming-interactive-media/skills/30-gameplay-systems-review` | `references/gamedev-team-level.md` | community/Donchitos-Claude-Code-Game-Studios |
| `gamedev-team-live-ops` | `gameplay-systems-review` | `plugins/gaming-interactive-media/skills/30-gameplay-systems-review` | `references/gamedev-team-live-ops.md` | community/Donchitos-Claude-Code-Game-Studios |
| `gamedev-team-narrative` | `gameplay-systems-review` | `plugins/gaming-interactive-media/skills/30-gameplay-systems-review` | `references/gamedev-team-narrative.md` | community/Donchitos-Claude-Code-Game-Studios |
| `gamedev-team-polish` | `game-architecture-review` | `plugins/gaming-interactive-media/skills/29-game-architecture-review` | `references/gamedev-team-polish.md` | community/Donchitos-Claude-Code-Game-Studios |
| `gamedev-team-qa` | `uat-acceptance-review` | `plugins/testing-and-qa/skills/57-uat-acceptance-review` | `references/gamedev-team-qa.md` | community/Donchitos-Claude-Code-Game-Studios |
| `gamedev-team-release` | `release-readiness-check` | `plugins/core-operations/skills/06-release-readiness-check` | `references/gamedev-team-release.md` | community/Donchitos-Claude-Code-Game-Studios |
| `gamedev-team-ui` | `gameplay-systems-review` | `plugins/gaming-interactive-media/skills/30-gameplay-systems-review` | `references/gamedev-team-ui.md` | community/Donchitos-Claude-Code-Game-Studios |
| `gamedev-tech-debt` | `game-architecture-review` | `plugins/gaming-interactive-media/skills/29-game-architecture-review` | `references/gamedev-tech-debt.md` | community/Donchitos-Claude-Code-Game-Studios |
| `gamedev-ux-review` | `gameplay-systems-review` | `plugins/gaming-interactive-media/skills/30-gameplay-systems-review` | `references/gamedev-ux-review.md` | community/Donchitos-Claude-Code-Game-Studios |
| `global-installation-audit` | `skill-librarian` | `plugins/skill-library-and-installation/skills/71-skill-librarian` | `references/global-installation-audit.md` | Skillry original |
| `godot-unity-unreal-triage` | `game-architecture-review` | `plugins/gaming-interactive-media/skills/29-game-architecture-review` | `references/godot-unity-unreal-triage.md` | Skillry original |
| `handoff-readiness-check` | `release-readiness-check` | `plugins/core-operations/skills/06-release-readiness-check` | `references/handoff-readiness-check.md` | Skillry original |
| `hybrid-search-implementation` | `rag-vector-search-review` | `plugins/ai-and-agent-systems/skills/43-rag-vector-search-review` | `references/hybrid-search-implementation.md` | community/wshobson-agents |
| `incremental-implementation` | `implementation-plan` | `plugins/core-operations/skills/04-implementation-plan` | `references/incremental-implementation.md` | community/addyosmani-agent-skills |
| `integration-boundary-review` | `backend-implementation-review` | `plugins/backend-and-api/skills/13-backend-implementation-review` | `references/integration-boundary-review.md` | Skillry original |
| `interactive-prototype-review` | `web-design-review` | `plugins/frontend-web-design/skills/18-web-design-review` | `references/interactive-prototype-review.md` | Skillry original |
| `ios-hig-review` | `mobile-app-review` | `plugins/mobile-desktop/skills/25-mobile-app-review` | `references/ios-hig-review.md` | Skillry original |
| `javascript-testing-patterns` | `test-driven-development` | `community/addyosmani-agent-skills/skills/test-driven-development` | `references/javascript-testing-patterns.md` | community/wshobson-agents |
| `kubernetes-manifest-review` | `cloud-service-architecture` | `plugins/cloud-and-infrastructure/skills/334-cloud-service-architecture` | `references/kubernetes-manifest-review.md` | Skillry original |
| `langchain-architecture` | `agent-workflow-design` | `plugins/ai-and-agent-systems/skills/40-agent-workflow-design` | `references/langchain-architecture.md` | community/wshobson-agents |
| `llm-api-cost-optimization` | `cost-control-token-review` | `plugins/optional-specialist/skills/86-cost-control-token-review` | `references/llm-api-cost-optimization.md` | Skillry original |
| `llm-evaluation` | `llm-evaluation-review` | `plugins/ai-and-agent-systems/skills/44-llm-evaluation-review` | `references/llm-evaluation.md` | community/wshobson-agents |
| `log-and-diagnostics-bundle` | `runtime-diagnostics` | `plugins/runtime-and-local-app/skills/08-runtime-diagnostics` | `references/log-and-diagnostics-bundle.md` | Skillry original |
| `md-spec-generator` | `implementation-plan` | `plugins/core-operations/skills/04-implementation-plan` | `references/md-spec-generator.md` | Skillry original |
| `memory-and-resource-profiling` | `backend-latency-profiling` | `plugins/performance-and-cost/skills/322-backend-latency-profiling` | `references/memory-and-resource-profiling.md` | Skillry original |
| `ml-training-pipeline-review` | `data-pipeline-review` | `plugins/data-ml-ai-engineering/skills/311-data-pipeline-review` | `references/ml-training-pipeline-review.md` | Skillry original |
| `model-serving-and-inference` | `data-pipeline-review` | `plugins/data-ml-ai-engineering/skills/311-data-pipeline-review` | `references/model-serving-and-inference.md` | Skillry original |
| `modern-javascript-patterns` | `frontend-ui-engineering` | `community/addyosmani-agent-skills/skills/frontend-ui-engineering` | `references/modern-javascript-patterns.md` | community/wshobson-agents |
| `monorepo-management` | `monorepo-turborepo-review` | `plugins/optional-specialist/skills/88-monorepo-turborepo-review` | `references/monorepo-management.md` | community/wshobson-agents |
| `multi-stage-dockerfile` | `cloud-service-architecture` | `plugins/cloud-and-infrastructure/skills/334-cloud-service-architecture` | `references/multi-stage-dockerfile.md` | community/github-awesome-copilot |
| `nextjs-app-router-patterns` | `next-app-router-rsc-review` | `plugins/frontend-web-design/skills/92-next-app-router-rsc-review` | `references/nextjs-app-router-patterns.md` | community/wshobson-agents |
| `notebook-hygiene` | `data-pipeline-review` | `plugins/data-ml-ai-engineering/skills/311-data-pipeline-review` | `references/notebook-hygiene.md` | Skillry original |
| `nx-workspace-patterns` | `monorepo-turborepo-review` | `plugins/optional-specialist/skills/88-monorepo-turborepo-review` | `references/nx-workspace-patterns.md` | community/wshobson-agents |
| `observability-otel-review` | `error-handling-observability` | `plugins/backend-and-api/skills/16-error-handling-observability` | `references/observability-otel-review.md` | Skillry original |
| `openapi-spec-generation` | `api-and-interface-design` | `plugins/backend-and-api/skills/12-api-and-interface-design` | `references/openapi-spec-generation.md` | community/wshobson-agents |
| `openapi-to-application-code` | `api-and-interface-design` | `plugins/backend-and-api/skills/12-api-and-interface-design` | `references/openapi-to-application-code.md` | community/github-awesome-copilot |
| `path-hygiene-repair` | `skill-librarian` | `plugins/skill-library-and-installation/skills/71-skill-librarian` | `references/path-hygiene-repair.md` | Skillry original |
| `performance-optimization` | `frontend-performance-budget` | `plugins/performance-and-cost/skills/321-frontend-performance-budget` | `references/performance-optimization.md` | community/addyosmani-agent-skills |
| `phaser-game-development` | `game-architecture-review` | `plugins/gaming-interactive-media/skills/29-game-architecture-review` | `references/phaser-game-development.md` | Skillry original |
| `pixijs-2d-rendering` | `game-architecture-review` | `plugins/gaming-interactive-media/skills/29-game-architecture-review` | `references/pixijs-2d-rendering.md` | Skillry original |
| `postgresql-optimization` | `postgres-supabase-review` | `plugins/database-and-data/skills/36-postgres-supabase-review` | `references/postgresql-optimization.md` | community/github-awesome-copilot |
| `postgresql-table-design` | `postgres-supabase-review` | `plugins/database-and-data/skills/36-postgres-supabase-review` | `references/postgresql-table-design.md` | community/wshobson-agents |
| `premium-frontend-ui` | `frontend-ui-engineering` | `community/addyosmani-agent-skills/skills/frontend-ui-engineering` | `references/premium-frontend-ui.md` | community/github-awesome-copilot |
| `pricing-packaging-review` | `business-model-review` | `plugins/product-docs-and-research/skills/67-business-model-review` | `references/pricing-packaging-review.md` | Skillry original |
| `print-design-artifact-review` | `nfc-linktree-menu-builder-review` | `plugins/optional-specialist/skills/78-nfc-linktree-menu-builder-review` | `references/print-design-artifact-review.md` | Skillry original |
| `prompt-engineering-patterns` | `prompt-systems-review` | `plugins/ai-and-agent-systems/skills/42-prompt-systems-review` | `references/prompt-engineering-patterns.md` | community/wshobson-agents |
| `python-anti-patterns` | `python-project-review` | `plugins/backend-and-api/skills/94-python-project-review` | `references/python-anti-patterns.md` | community/wshobson-agents |
| `python-background-jobs` | `python-project-review` | `plugins/backend-and-api/skills/94-python-project-review` | `references/python-background-jobs.md` | community/wshobson-agents |
| `python-code-style` | `python-project-review` | `plugins/backend-and-api/skills/94-python-project-review` | `references/python-code-style.md` | community/wshobson-agents |
| `python-configuration` | `python-project-review` | `plugins/backend-and-api/skills/94-python-project-review` | `references/python-configuration.md` | community/wshobson-agents |
| `python-design-patterns` | `python-project-review` | `plugins/backend-and-api/skills/94-python-project-review` | `references/python-design-patterns.md` | community/wshobson-agents |
| `python-error-handling` | `python-project-review` | `plugins/backend-and-api/skills/94-python-project-review` | `references/python-error-handling.md` | community/wshobson-agents |
| `python-mcp-server-generator` | `agent-workflow-design` | `plugins/ai-and-agent-systems/skills/40-agent-workflow-design` | `references/python-mcp-server-generator.md` | community/github-awesome-copilot |
| `python-observability` | `python-project-review` | `plugins/backend-and-api/skills/94-python-project-review` | `references/python-observability.md` | community/wshobson-agents |
| `python-packaging` | `python-project-review` | `plugins/backend-and-api/skills/94-python-project-review` | `references/python-packaging.md` | community/wshobson-agents |
| `python-performance-optimization` | `backend-latency-profiling` | `plugins/performance-and-cost/skills/322-backend-latency-profiling` | `references/python-performance-optimization.md` | community/wshobson-agents |
| `python-pypi-package-builder` | `python-project-review` | `plugins/backend-and-api/skills/94-python-project-review` | `references/python-pypi-package-builder.md` | community/github-awesome-copilot |
| `python-resilience` | `python-project-review` | `plugins/backend-and-api/skills/94-python-project-review` | `references/python-resilience.md` | community/wshobson-agents |
| `python-resource-management` | `python-project-review` | `plugins/backend-and-api/skills/94-python-project-review` | `references/python-resource-management.md` | community/wshobson-agents |
| `python-testing-patterns` | `test-driven-development` | `community/addyosmani-agent-skills/skills/test-driven-development` | `references/python-testing-patterns.md` | community/wshobson-agents |
| `quality-playbook` | `test-driven-development` | `community/addyosmani-agent-skills/skills/test-driven-development` | `references/quality-playbook.md` | community/github-awesome-copilot |
| `query-performance-review` | `postgres-supabase-review` | `plugins/database-and-data/skills/36-postgres-supabase-review` | `references/query-performance-review.md` | Skillry original |
| `rag-implementation` | `rag-vector-search-review` | `plugins/ai-and-agent-systems/skills/43-rag-vector-search-review` | `references/rag-implementation.md` | community/wshobson-agents |
| `react-state-management` | `frontend-ui-engineering` | `community/addyosmani-agent-skills/skills/frontend-ui-engineering` | `references/react-state-management.md` | community/wshobson-agents |
| `react18-batching-patterns` | `frontend-ui-engineering` | `community/addyosmani-agent-skills/skills/frontend-ui-engineering` | `references/react18-batching-patterns.md` | community/github-awesome-copilot |
| `readme-and-docs-structure` | `technical-writing-review` | `plugins/product-docs-and-research/skills/69-technical-writing-review` | `references/readme-and-docs-structure.md` | Skillry original |
| `refactor` | `refactor-safety` | `plugins/core-operations/skills/05-refactor-safety` | `references/refactor.md` | community/github-awesome-copilot |
| `refactor-method-complexity-reduce` | `refactor-safety` | `plugins/core-operations/skills/05-refactor-safety` | `references/refactor-method-complexity-reduce.md` | community/github-awesome-copilot |
| `refactor-plan` | `refactor-safety` | `plugins/core-operations/skills/05-refactor-safety` | `references/refactor-plan.md` | community/github-awesome-copilot |
| `regression-scope-analysis` | `diff-review` | `plugins/core-operations/skills/07-diff-review` | `references/regression-scope-analysis.md` | Skillry original |
| `release-notes-generator` | `technical-writing-review` | `plugins/product-docs-and-research/skills/69-technical-writing-review` | `references/release-notes-generator.md` | Skillry original |
| `requirements-test-coverage-mapper` | `uat-acceptance-review` | `plugins/testing-and-qa/skills/57-uat-acceptance-review` | `references/requirements-test-coverage-mapper.md` | community/jaktestowac-awesome-copilot-for-testers |
| `responsive-layout-review` | `web-design-review` | `plugins/frontend-web-design/skills/18-web-design-review` | `references/responsive-layout-review.md` | Skillry original |
| `runbook-and-operational-docs` | `technical-writing-review` | `plugins/product-docs-and-research/skills/69-technical-writing-review` | `references/runbook-and-operational-docs.md` | Skillry original |
| `secrets-and-config-management` | `security-and-secrets-review` | `plugins/security/skills/47-security-and-secrets-review` | `references/secrets-and-config-management.md` | Skillry original |
| `seed-and-fixture-review` | `database-and-prisma-review` | `plugins/database-and-data/skills/35-database-and-prisma-review` | `references/seed-and-fixture-review.md` | Skillry original |
| `seo` | `seo-content-ops-review` | `plugins/optional-specialist/skills/85-seo-content-ops-review` | `references/seo.md` | community/addyosmani-web-quality-skills |
| `shadcn-ui-components` | `frontend-ui-engineering` | `community/addyosmani-agent-skills/skills/frontend-ui-engineering` | `references/shadcn-ui-components.md` | Skillry original |
| `skill-deduplication` | `skill-librarian` | `plugins/skill-library-and-installation/skills/71-skill-librarian` | `references/skill-deduplication.md` | Skillry original |
| `skill-to-agent-router` | `skill-librarian` | `plugins/skill-library-and-installation/skills/71-skill-librarian` | `references/skill-to-agent-router.md` | Skillry original |
| `spec-driven-development` | `implementation-plan` | `plugins/core-operations/skills/04-implementation-plan` | `references/spec-driven-development.md` | community/addyosmani-agent-skills |
| `sql-optimization-patterns` | `postgres-supabase-review` | `plugins/database-and-data/skills/36-postgres-supabase-review` | `references/sql-optimization-patterns.md` | community/wshobson-agents |
| `startup-health-readiness` | `runtime-diagnostics` | `plugins/runtime-and-local-app/skills/08-runtime-diagnostics` | `references/startup-health-readiness.md` | Skillry original |
| `supabase-rls-edge-functions` | `postgres-supabase-review` | `plugins/database-and-data/skills/36-postgres-supabase-review` | `references/supabase-rls-edge-functions.md` | Skillry original |
| `tailwind-design-system` | `frontend-ui-engineering` | `community/addyosmani-agent-skills/skills/frontend-ui-engineering` | `references/tailwind-design-system.md` | community/wshobson-agents |
| `temporal-python-testing` | `test-driven-development` | `community/addyosmani-agent-skills/skills/test-driven-development` | `references/temporal-python-testing.md` | community/wshobson-agents |
| `terraform-iac-review` | `cloud-service-architecture` | `plugins/cloud-and-infrastructure/skills/334-cloud-service-architecture` | `references/terraform-iac-review.md` | Skillry original |
| `track-management` | `implementation-plan` | `plugins/core-operations/skills/04-implementation-plan` | `references/track-management.md` | community/wshobson-agents |
| `turborepo-caching` | `monorepo-turborepo-review` | `plugins/optional-specialist/skills/88-monorepo-turborepo-review` | `references/turborepo-caching.md` | community/wshobson-agents |
| `tutorial-and-how-to-writing` | `technical-writing-review` | `plugins/product-docs-and-research/skills/69-technical-writing-review` | `references/tutorial-and-how-to-writing.md` | Skillry original |
| `typescript-advanced-types` | `frontend-ui-engineering` | `community/addyosmani-agent-skills/skills/frontend-ui-engineering` | `references/typescript-advanced-types.md` | community/wshobson-agents |
| `typescript-mcp-server-generator` | `agent-workflow-design` | `plugins/ai-and-agent-systems/skills/40-agent-workflow-design` | `references/typescript-mcp-server-generator.md` | community/github-awesome-copilot |
| `ui-consistency-review` | `web-design-review` | `plugins/frontend-web-design/skills/18-web-design-review` | `references/ui-consistency-review.md` | Skillry original |
| `update-implementation-plan` | `implementation-plan` | `plugins/core-operations/skills/04-implementation-plan` | `references/update-implementation-plan.md` | community/github-awesome-copilot |
| `uv-package-manager` | `python-project-review` | `plugins/backend-and-api/skills/94-python-project-review` | `references/uv-package-manager.md` | community/wshobson-agents |
| `visual-polish-pass` | `web-design-review` | `plugins/frontend-web-design/skills/18-web-design-review` | `references/visual-polish-pass.md` | Skillry original |
| `visual-regression-review` | `playwright-e2e-audit` | `plugins/testing-and-qa/skills/53-playwright-e2e-audit` | `references/visual-regression-review.md` | Skillry original |
| `web-component-design` | `frontend-ui-engineering` | `community/addyosmani-agent-skills/skills/frontend-ui-engineering` | `references/web-component-design.md` | community/wshobson-agents |
| `web-game-architecture` | `game-architecture-review` | `plugins/gaming-interactive-media/skills/29-game-architecture-review` | `references/web-game-architecture.md` | Skillry original |
| `web-game-performance` | `game-architecture-review` | `plugins/gaming-interactive-media/skills/29-game-architecture-review` | `references/web-game-performance.md` | Skillry original |
| `webapp-testing` | `playwright-e2e-audit` | `plugins/testing-and-qa/skills/53-playwright-e2e-audit` | `references/webapp-testing.md` | community/github-awesome-copilot |
| `wordpress-woocommerce-review` | `ecommerce-integration-review` | `plugins/optional-specialist/skills/77-ecommerce-integration-review` | `references/wordpress-woocommerce-review.md` | Skillry original |
| `workflow-patterns` | `test-driven-development` | `community/addyosmani-agent-skills/skills/test-driven-development` | `references/workflow-patterns.md` | community/wshobson-agents |

### Imported skills

| Imported skill | Hub | Reference | Upstream |
|---|---|---|---|
| `accessibility` | `accessibility-audit` | `references/accessibility.md` | addyosmani/web-quality-skills |
| `analytics` | `analytics-tracking-review` | `references/analytics.md` | coreyhaines31/marketingskills |
| `claude-seo-seo-images` | `seo-content-ops-review` | `references/claude-seo-seo-images.md` | AgriciDaniel/claude-seo |
| `claude-seo-seo-sxo` | `seo-content-ops-review` | `references/claude-seo-seo-sxo.md` | AgriciDaniel/claude-seo |
| `cold-start-problem` | `business-model-review` | `references/cold-start-problem.md` | wondelai/skills |
| `copywriting` | `landing-page-conversion-review` | `references/copywriting.md` | coreyhaines31/marketingskills |
| `cro` | `landing-page-conversion-review` | `references/cro.md` | coreyhaines31/marketingskills |
| `customer-research` | `market-research-synthesis` | `references/customer-research.md` | coreyhaines31/marketingskills |
| `fastapi` | `python-project-review` | `references/fastapi.md` | fastapi/fastapi |
| `foundation-lean-canvas` | `business-model-review` | `references/foundation-lean-canvas.md` | product-on-purpose/pm-skills |
| `geo-ai-index-access` | `seo-content-ops-review` | `references/geo-ai-index-access.md` | TheSmokeDev/geo-skills |
| `geo-citability` | `seo-content-ops-review` | `references/geo-citability.md` | TheSmokeDev/geo-skills, zubair-trabzada/geo-seo-claude |
| `geo-crawlers` | `seo-content-ops-review` | `references/geo-crawlers.md` | TheSmokeDev/geo-skills, zubair-trabzada/geo-seo-claude |
| `geo-fanout` | `seo-content-ops-review` | `references/geo-fanout.md` | TheSmokeDev/geo-skills |
| `geo-schema` | `seo-content-ops-review` | `references/geo-schema.md` | TheSmokeDev/geo-skills, zubair-trabzada/geo-seo-claude |
| `github-actions-hardening` | `ci-cd-pipeline-review` | `references/github-actions-hardening.md` | github/awesome-copilot |
| `i18n-agent` | `i18n-locale-parity-review` | `references/i18n-agent.md` | adamgrgs/i18n-agent |
| `intended-vs-implemented` | `security-and-secrets-review` | `references/intended-vs-implemented.md` | phuryn/pm-skills |
| `localization-guide` | `i18n-locale-parity-review` | `references/localization-guide.md` | SkillMedev/skills |
| `localize-anything` | `i18n-locale-parity-review` | `references/localize-anything.md` | xueyang-dev/localize-anything |
| `maplibre-cartography` | `map-routing-geo-review` | `references/maplibre-cartography.md` | maplibre/maplibre-agent-skills |
| `maplibre-tile-sources` | `map-routing-geo-review` | `references/maplibre-tile-sources.md` | maplibre/maplibre-agent-skills |
| `north-star-metric` | `business-model-review` | `references/north-star-metric.md` | phuryn/pm-skills |
| `onboarding` | `landing-page-conversion-review` | `references/onboarding.md` | coreyhaines31/marketingskills |
| `outcome-roadmap` | `product-requirements-review` | `references/outcome-roadmap.md` | phuryn/pm-skills |
| `playwright-skill` | `playwright-e2e-audit` | `references/playwright-skill.md` | testdino-hq/playwright-skill |
| `pm-spec-writing` | `implementation-plan` | `references/pm-spec-writing.md` | rampstackco/claude-skills |
| `pre-mortem` | `product-requirements-review` | `references/pre-mortem.md` | phuryn/pm-skills |
| `pricing` | `business-model-review` | `references/pricing.md` | coreyhaines31/marketingskills |
| `prioritize-features` | `product-requirements-review` | `references/prioritize-features.md` | phuryn/pm-skills |
| `product-strategy` | `business-model-review` | `references/product-strategy.md` | phuryn/pm-skills |
| `programmatic-seo` | `seo-content-ops-review` | `references/programmatic-seo.md` | coreyhaines31/marketingskills |
| `redis-security` | `security-and-secrets-review` | `references/redis-security.md` | redis/agent-skills |
| `seo-backlinks` | `seo-content-ops-review` | `references/seo-backlinks.md` | AgriciDaniel/claude-seo |
| `seo-cluster` | `seo-content-ops-review` | `references/seo-cluster.md` | AgriciDaniel/claude-seo |
| `seo-competitor-pages` | `seo-content-ops-review` | `references/seo-competitor-pages.md` | AgriciDaniel/claude-seo |
| `seo-content` | `seo-content-ops-review` | `references/seo-content.md` | AgriciDaniel/claude-seo |
| `seo-page` | `seo-content-ops-review` | `references/seo-page.md` | AgriciDaniel/claude-seo |
| `seo-plan` | `seo-content-ops-review` | `references/seo-plan.md` | AgriciDaniel/claude-seo |
| `seo-technical` | `seo-content-ops-review` | `references/seo-technical.md` | AgriciDaniel/claude-seo |
| `signup` | `landing-page-conversion-review` | `references/signup.md` | coreyhaines31/marketingskills |
| `site-architecture` | `seo-content-ops-review` | `references/site-architecture.md` | coreyhaines31/marketingskills |
| `strategy-red-team` | `product-requirements-review` | `references/strategy-red-team.md` | phuryn/pm-skills |
| `test-scenarios` | `uat-acceptance-review` | `references/test-scenarios.md` | phuryn/pm-skills |

Former names of imported skills where the installed name differed: `multilingual-i18n-seo` is
`i18n-agent`, `Localization Writer` is `localization-guide`, `seo-images` is `claude-seo-seo-images`
and `seo-sxo` is `claude-seo-seo-sxo`.

## [2.0.0] - 2026-08-28

### Breaking

- The portable installer manages verified platform skills and agents only. It no
  longer copies, merges or reconciles project AGENTS.md, CLAUDE.md, GEMINI.md or
  Copilot instruction files.
- Dry-run is the default. Filesystem changes require --apply, and unknown,
  misspelled or empty target selections fail closed.
- Existing untracked destination files and locally modified managed files are
  preserved and refused instead of overwritten.

### Added

- Per-target managed-state manifests for idempotent installation and
  hash-guarded stale managed-file removal.
- A release gate covering source locks, validator checks, four clean target
  installs, all Codex agent TOML files and every locked community sidecar.
- Immutable community source provenance for 35 installed sidecar targets,
  including references, templates, scripts and retained license files.
- npm registry installation, public roadmap and expanded platform and
  governance documentation.

### Security

- Import and installation paths are containment checked and symlink-sensitive.
- Reviewed read-only agent classifications no longer treat general Bash access
  as read-only.
- Community source files and installed payloads are checked against generated
  SHA-256 locks before release.

### Fixed

- Community skills now ship their required local references and helper files.
- Codex agent TOML generation handles source escaping correctly; all 122
  generated agent files parse in the release gate.
- Canonical community skill names are derived from frontmatter when vendor
  directory names are numeric or otherwise non-canonical.

### Packaging

- npm prepack runs the release gate.
- The public package includes the portable installer, release gate, source
  locks and all locked sidecars.
- Private governance sources and the project-policy generator are excluded from
  the published payload.

## [1.2.0] — 2026-06-01

### Added
- **`skillry version` and `skillry update`** CLI commands. `update` checks the latest GitHub
  release against the installed version and prints the right update command for each install
  method (Claude Code marketplace, npm global, npx, clone). Installed skill files never
  self-update silently — `update` tells you exactly how to refresh them.

### Fixed
- Attribution accuracy: `THIRD-PARTY-NOTICES.md` now reports 17 redistributed skills for
  `github/awesome-copilot` (was 16). Removed stale example counts from the global-installation-audit
  skill. Refreshed the build-effort token figures.

## [1.1.0] — 2026-06-01

### Added
- **Multi-platform behavior files.** A project instruction file for every supported tool, all
  generated from the canonical `CLAUDE.md`: `AGENTS.md` (Codex / Copilot / Antigravity — the open
  AGENTS.md standard), `GEMINI.md` (Gemini CLI / Antigravity), and
  `.github/copilot-instructions.md` (Copilot). New generator `tools/build-agent-instructions.py`;
  CI fails if the generated files drift from `CLAUDE.md`.
- **Callable `diff-review` skill** (`core-operations`) — audits a diff against four principles
  (surface assumptions, keep it simple, surgical changes, verifiable goal), distilled from
  Andrej Karpathy's public guidance (credited). Brings the original-skill count to **125**.
- **`install.py --instructions <dir>`** — installs the right behavior file per target platform
  into a project. Existing instruction files are **merged, not clobbered**: your rules are kept,
  Skillry's manual is appended under a marked block, and a one-time, self-removing first-run
  notice has the agent reconcile duplicate/conflicting rules with you. Re-installs are idempotent.
- **Acknowledgments** crediting Claude (Anthropic), Codex (OpenAI), and Gemini (Google) as both
  build tools and target platforms.
- Repository polish: `CHANGELOG.md`, issue/PR templates, and a code of conduct.

### Changed
- `CLAUDE.md` rewritten as a project-agnostic engineering operating manual (prime directives,
  inspect-first, Karpathy-credited coding principles, security/least-privilege, i18n + light/dark
  parity, Electron/Tauri dev-launch default, honest verification). It now doubles as a model you
  can copy into your own project.
- Docs refreshed: counts → 125 skills / 73 subagents / 18 departments.

### Fixed
- Attribution accuracy: `jaktestowac/awesome-copilot-for-testers` is a fork of
  `github/awesome-copilot` and retains "Copyright GitHub, Inc." — `NOTICE` corrected.
- `install.py` `--targets` parsing now stops at the next `--flag` (so `--instructions <dir>` is
  not mistaken for a target).

### Removed
- Empty `platforms/` scaffolding directories (the installer writes to each platform's real config
  location, not into the repo).

## [1.0.0] — 2026-06-01

### Added
- First public release: 124 original skills across 18 departments, 73 least-privilege subagents,
  an attributed `community/` set (98 skills + 49 agents from 6 MIT/ISC sources), a validation
  harness, a native Claude Code plugin marketplace, SHA-256 lockfiles, the `skill-sync` importer,
  a portable multi-platform installer, and npm/npx install support.

# Skillry Maintainer Handoff

Snapshot date: 2026-08-13

## Outcome

The repository, published package, research direction, open candidate work, and future backlog are
documented in GitHub-ready form. This handoff contains no credentials or machine-specific paths.

## Verified project state

| Surface | Verified state |
|---|---|
| GitHub repository | `FluxonLab/Skillry`, public |
| Default branch | `main` |
| Default branch head | `34aa31c7448db354e77424033e21c257f4d99b0e` |
| npm package | `skillry@1.2.0` |
| Original skills | 125 |
| Original agents | 73 |
| Community skills | 98 |
| Community agents | 49 |
| Departments | 18 |
| Latest `main` CI at snapshot | passed for `34aa31c` |
| Database/environment | no database, ORM, migration, or required `.env` surface |

## Architecture map

```text
plugins/<department>/
  skills/<number-name>/SKILL.md   original skill source
  agents/<name>.md                original agent source
  .claude-plugin/plugin.json      department manifest

community/<source>/               attributed third-party content
registry/                         generated SHA-256 inventories
tools/                            install, validate, import, and generators
bin/skillry.js                    dependency-free Node CLI wrapper
CLAUDE.md                         canonical shared instruction source
AGENTS.md / GEMINI.md / Copilot   generated instruction family
```

The Node CLI delegates real work to Python scripts. The package has no runtime npm dependencies and
no lockfile.

## Completed work

- Public repository, MIT license, governance, security policy, contribution policy, and attribution
  notices.
- Native Claude Code marketplace with 18 department plugins.
- Multi-platform installer for Claude, Codex, Copilot, and Antigravity/Gemini.
- Permission-derived Codex agent conversion.
- Generated cross-platform instruction family from `CLAUDE.md`.
- SHA-256 skill and agent inventories.
- Third-party source separation and attribution.
- `skill-sync` discovery/import/normalization with license and risk-pattern checks.
- CI validation and isolated-home install smoke test.
- npm publication and update/version CLI commands.
- npm package-surface hardening in commit `34aa31c`.

## Not implemented

- Validator 2.0 severity/gate matrix.
- Agent Skills specification compliance profile.
- Skill trigger accuracy and model evaluation harness.
- Skill Sync 2.0 provenance and ignored/excluded decision model.
- Generated human-review library report.
- npm trusted publishing, provenance attestations, SBOM, or SLSA policy.
- MCP capability registry.
- Optional hook/guardrail pack.
- Formal multi-agent handoff contracts.
- OWASP/NIST risk flags for every skill and agent.

These are research recommendations, not approved implementation scope.

## Open GitHub state

- Issue `#1` is the original public roadmap. Its npm-publish item is stale because npm publication
  is complete.
- Draft PR `#3` contains a factory-governance candidate. It is not merged or live.
- Branch `phase-c/factory-governance-20260809` is preserved remotely.
- This handoff should not silently merge, close, or replace PR `#3`.

## Resume on another computer

```bash
git clone https://github.com/FluxonLab/Skillry.git
cd Skillry
git status --short --branch
node --version
python3 --version
python3 tools/validate.py
python3 tools/build-lock.py
python3 tools/install.py --targets claude codex copilot antigravity
npm pack --dry-run --json
```

To inspect the unmerged governance candidate:

```bash
git fetch origin phase-c/factory-governance-20260809
git diff --stat main..origin/phase-c/factory-governance-20260809
gh pr view 3 --repo FluxonLab/Skillry
```

Do not run install commands with `--apply` until the destination computer's existing global agent
configuration is inspected and backed up.

## Maintainer verification gates

```bash
python3 tools/validate.py
python3 tools/build-lock.py
python3 tools/build-marketplace.py
python3 tools/build-agent-instructions.py
python3 tools/install.py --targets claude codex copilot antigravity --instructions /tmp/skillry-instructions
node --check bin/skillry.js
npm pack --dry-run --json
```

Expected current inventory:

```text
125 original skills
73 original agents
98 community skills
49 community agents
18 department manifests
```

## Known risks and caveats

- Platform instruction and skill standards evolve; compatibility claims require periodic official
  documentation review.
- Current permission checks are heuristic and based on declared tool names.
- Automated pattern scans do not prove third-party content safe.
- There is no full skill-trigger evaluation suite.
- The public roadmap issue needs reconciliation with the current docs after this handoff lands.
- The governance candidate changes canonical instruction generation and requires explicit review.

## Next safe sequence

1. Read `DECISIONS.md`, then this handoff.
2. Verify a clean clone using the bounded commands above.
3. Review draft PR `#3` independently; do not infer approval from green CI.
4. Resolve the questions in `OPEN-QUESTIONS.md`.
5. Only after explicit maintainer direction, write an implementation plan for one coherent roadmap
   phase.

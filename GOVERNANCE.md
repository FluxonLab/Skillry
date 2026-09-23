# Governance

## Project status

Skillry is an **early but infrastructure-level** open-source project. It is young (no inflated star,
download, or user claims here) and is positioned as plumbing for the agent-skills ecosystem:
safe distribution, validation, attribution, and permission boundaries for skills and subagents
across multiple AI coding platforms. It is **MIT-licensed and actively maintained.**

## Maintainers

- **Primary maintainer:** Çağrı Bozgeyik — [FluxonLab](https://fluxonlab.com)
  ([@FluxonLab](https://github.com/FluxonLab) on GitHub, [cagribozgeyik.com](https://cagribozgeyik.com)).

The primary maintainer reviews and merges changes, cuts releases, and is responsible for security
response. Additional maintainers may be added as the project grows; they will be listed here.

## Decision-making

- Small, focused changes are reviewed and merged by a maintainer.
- Larger or breaking changes should start as a GitHub issue (see the pinned **Roadmap** issue) so
  direction can be discussed before implementation.
- The project's values are fixed and not up for negotiation per-PR: **correctness, safety, and
  attribution over raw volume.**

## Contribution review policy

Every contribution is reviewed against the rules in [CONTRIBUTING.md](CONTRIBUTING.md):

- `python3 tools/validate.py` must pass (0 failures); CI runs the same checks on every PR.
- Subagents must declare a least-privilege `tools` allowlist; review/audit agents get no write tools.
- `AGENTS.md` and `CLAUDE.md` are equivalent, repository-only contributor entry points;
  maintain their shared rules together. They are not generated or portable installer payload.
- Generated artifacts (`marketplace.json`, the thin `GEMINI.md` and Copilot adapters) must be
  regenerated from source, never hand-edited. Adapter generation only links to the root rules;
  it cannot overwrite canonical contributor files. Historical `.factory/governance/` candidate
  records remain evidence, not an active policy layer.
- Third-party content must be permissively licensed (MIT/ISC/BSD/Apache-2.0), verified from the
  upstream LICENSE file, kept under `community/` with its original `LICENSE` (or, when merged into a
  skill hub, under that hub's `references/<former-name>*` with a provenance header and the upstream
  `LICENSE` copied beside it), and recorded in `NOTICE` + `THIRD-PARTY-NOTICES.md`.

## Release policy

- **Versioning:** [Semantic Versioning](https://semver.org/). `package.json` is the source of truth.
- **Cadence:** released as meaningful changes land; there is no fixed calendar.
- **Each release:** a Git tag `vX.Y.Z`, a GitHub Release, and a matching [CHANGELOG.md](CHANGELOG.md)
  entry. Generated files and lockfiles are regenerated and validated before tagging.
- **Reproducibility:** Claude Code marketplace installs can be pinned to a commit SHA; SHA-256
  lockfiles in `registry/` record the shipped inventory.

## Security

Report vulnerabilities privately per [SECURITY.md](SECURITY.md) — preferably via a GitHub Security
Advisory ("Report a vulnerability"), or through FluxonLab at [fluxonlab.com/contact](https://fluxonlab.com/contact).
Please do not open a public issue for an undisclosed vulnerability.

## Code of conduct

Participation is governed by the [Code of Conduct](CODE_OF_CONDUCT.md).

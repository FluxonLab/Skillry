# Security Policy

OmniAgent installs skills and subagents that an AI coding agent will execute with your
permissions. We take the supply-chain surface seriously.

## Principles

- **Least privilege.** Subagents declare an explicit `tools` allowlist. Review/audit agents
  ship with no file-write tools.
- **Trusted sources only.** Redistributed `community/` content is limited to permissively
  licensed sources that have been reviewed. Anything that runs shell commands, performs
  destructive git actions, deploys, or requires external service credentials is flagged in
  its skill body and is **not** auto-enabled.
- **No silent secrets.** Skills and agents never embed secrets; they reference environment
  variable names and redact values in examples.
- **Explicit exclusions.** Sources whose license does not permit redistribution are excluded
  rather than quietly bundled (see THIRD-PARTY-NOTICES.md).

## What we review before redistributing a third-party skill

1. License permits redistribution (MIT/ISC/BSD/Apache-2.0).
2. No embedded credentials, tokens, or private endpoints.
3. No prompt-injection / hidden-instruction patterns in the skill body.
4. Any command-executing or external-service behavior is disclosed in the skill.
5. Provenance recorded (source URL, original license retained).

## Reporting a vulnerability

If you find a security issue (malicious skill content, a permission-escalation pattern, an
attribution/license problem, or an injection vector), please open a private report:

- Preferred: GitHub Security Advisory ("Report a vulnerability") on this repository.
- Or contact FluxonLab via FLUXONLAB_URL.

Please do not open a public issue for undisclosed vulnerabilities. We aim to acknowledge
within a few days.

## Using OmniAgent safely

- Install only the departments/plugins you need.
- Review a skill's body before relying on it for anything that touches production, secrets,
  or destructive operations.
- Keep your platform CLI and this package updated; prefer sha-pinned marketplace installs for
  reproducibility.

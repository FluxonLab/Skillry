# Development Research Synthesis

Research snapshot: 2026-06-15, consolidated for handoff on 2026-08-13.

## Research question

How can Skillry evolve from a curated multi-platform skill library into a secure, traceable, and
testable agent-capability distribution system without losing operational simplicity?

## Main finding

The strongest opportunity is not adding more skills. It is connecting skill source, metadata,
trigger behavior, tool permissions, provenance, validation, evaluation, package publication, and
human approval into one auditable lifecycle.

```text
skill source
-> metadata contract
-> trigger/evaluation cases
-> permission and tool policy
-> provenance and license evidence
-> generated review surface
-> install, package, and release gates
```

## Research inputs

The original research included:

- a detailed review of 113 presentation images describing an enterprise Claude workflow;
- OCR, contact sheets, and focused re-inspection of low-legibility diagrams;
- a web-source evaluation against official agent, schema, security, testing, and accessibility
  documentation;
- a repository-level mapping against Skillry's current architecture.

The original local reports contained machine-specific paths and Turkish working notes. Their
portable findings are consolidated here instead of publishing private path metadata.

## Workflow findings

The reviewed workflow used Claude in three roles:

1. **Researcher:** gather dispersed pages, attachments, diagrams, and existing artifacts.
2. **Modeler:** normalize findings into Markdown, YAML, schema, role matrices, and domain atoms.
3. **Tool builder:** move repeatable work into scripts, validators, generators, tests, and audit
   gates.

The repeatable pipeline was:

```text
source systems
-> iterative research sweep
-> normalized Markdown
-> canonical YAML/schema
-> deterministic generators
-> reviewable specifications
-> code/tests/diagrams
-> audit trail and human gates
```

Important transferable patterns:

- Progressive disclosure instead of loading an entire knowledge archive.
- Search iteration until no new in-scope terms appear.
- Explicit ignored/excluded decisions with version and rationale.
- Diagram source data treated as evidence when available.
- Generated review artifacts linked back to source and validation status.
- Multi-dimensional business rules converted into test matrices.
- Human approval reserved for ambiguity, permissions, scope, and irreversible decisions.

## Skillry opportunity map

### 1. Agent Skills specification compliance

Report or validate fields such as license, compatibility, metadata, allowed tools, scripts,
references, and assets. Begin with a warning/report profile before requiring metadata migration
across all original skills.

### 2. Trigger accuracy and skill evaluations

Give each skill should-trigger, should-not-trigger, and ambiguous examples. Detect description
overlap and competing skills. Real model-trigger behavior varies by platform, so combine heuristic
checks with human review and optional platform evaluations.

### 3. Validator 2.0

Split checks into structure, frontmatter, permissions, attribution, generated drift, package
surface, secrets, and release readiness. Add severity and machine-readable output only after the
gate contract is agreed.

### 4. Skill Sync 2.0 provenance

Record upstream URL, commit, detected license, imported and excluded items, risk signals, review
date, and exclusion reasons. Network and external-source updates remain explicit, dry-run-first
operations.

### 5. Generated library review surface

Generate a Markdown-first report showing departments, skills, agents, permissions, source,
license, checksums, risk flags, stale metadata, package inclusion, and platform compatibility. Every
entry must link to source evidence to avoid a polished-report illusion.

### 6. Release supply-chain hardening

Unify validation, generated-drift checks, package allowlisting, secret scanning, version/changelog
checks, and lock drift. Later phases may evaluate npm trusted publishing, provenance attestations,
artifact attestations, and SBOM formats.

### 7. MCP capability registry

Record whether a skill needs an MCP server or external service, the primitive used, minimum auth
scope, side effects, credential risk, and smoke test. Start as documentation; do not make Skillry an
MCP runtime by default.

### 8. Optional hooks and guardrails

Offer project-scoped recipes for protected files, destructive commands, secret scanning, package
surface, and generated drift. Keep them opt-in until false positives and runtime differences are
measured.

### 9. Multi-agent handoff governance

Define role, tools, write scope, expected output contract, and permitted handoffs. Avoid turning a
simple agent library into a rigid routing framework before real workflows justify it.

### 10. OWASP/NIST risk mapping

Potential flags include shell execution, network access, external services, secret access, file
writes, destructive capability, and prompt-injection exposure. Unknown must remain "needs review"
rather than being treated as safe.

### 11. Instruction-layer matrix

Track the canonical source and generated outputs for Claude, Codex, Copilot, and Gemini, including
link rewriting, drift status, and dated platform-support notes.

### 12. Combinatorial installer tests

Model target platform, original/community content, skill/agent/instruction artifact, dry-run/apply
mode, and existing-file state. Pairwise coverage can control test explosion.

## Primary sources

- Agent Skills specification: https://agentskills.io/specification
- Claude Code skills: https://code.claude.com/docs/en/skills
- Claude Code hooks: https://code.claude.com/docs/en/hooks-guide
- Claude Code subagents: https://code.claude.com/docs/en/sub-agents
- Claude skill authoring guidance:
  https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- OpenAI Codex AGENTS.md: https://developers.openai.com/codex/guides/agents-md
- OpenAI Codex skills: https://developers.openai.com/codex/skills
- OpenAI Agents SDK: https://developers.openai.com/api/docs/guides/agents
- OpenAI evaluations: https://developers.openai.com/api/docs/guides/evals
- GitHub Copilot custom instructions:
  https://docs.github.com/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot
- Model Context Protocol specification: https://modelcontextprotocol.io/specification/2025-11-25
- OWASP Top 10 for LLM applications:
  https://owasp.org/www-project-top-10-for-large-language-model-applications/
- NIST AI Risk Management Framework: https://www.nist.gov/itl/ai-risk-management-framework
- NIST Secure Software Development Framework: https://csrc.nist.gov/pubs/sp/800/218/r1/ipd
- OpenSSF Scorecard: https://scorecard.dev/
- SLSA: https://slsa.dev/
- npm provenance: https://docs.npmjs.com/generating-provenance-statements/
- CycloneDX: https://cyclonedx.org/
- SPDX: https://spdx.dev/about/overview/
- JSON Schema: https://json-schema.org/specification
- OpenAPI: https://spec.openapis.org/oas/v3.2.0.html
- NIST combinatorial testing:
  https://csrc.nist.gov/projects/automated-combinatorial-testing-for-software

## Research limitations

- Platform documentation and product behavior change over time; re-verify before implementation.
- The original enterprise source repository and live Confluence export were unavailable.
- OCR-supported visual research establishes the workflow pattern, not an official source inventory.
- No implementation benchmark or user study has yet compared the proposed Skillry workflow with
  the current maintainer process.

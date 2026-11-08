---
name: project-intake
description: "Run intake for new, taken-over or paused projects in fast, standard or deep mode: review the repo, settle disagreements with evidence, batch owner questions, pick skill packs, schedule gates, keep or add project docs."
---

# Project Intake

## Purpose

Establish a verified technical, architectural, product, and governance baseline before writing feature code on any new, taken-over, or paused project. Review the project from three perspectives (by one agent or, in `deep` mode, by independent reviewers), settle contradictions with evidence, clarify open requirements through a single batched multiple-choice questionnaire, select the default skill set for the project type, schedule domain quality gates across four lifecycle waves, and make sure the project has one contract, one decision record and one plan, in the places the project already uses or, where one is missing, as `AGENTS.md`, `DECISIONS.md` and `PLAN.md`.

## When to use

- **New project (`new`):** Starting a green-field application, web service, SaaS platform, mobile app, game, 3D experience, or API.
- **Taken-over project (`takeover`):** Inheriting an existing codebase or repository with missing, conflicting, or unverified documentation and plans.
- **Long-paused project (`paused`):** Resuming work on a project after an extended hiatus, context reset, or team handover where dependencies, requirements, or architecture assumptions may be stale.

## When not to use

- Active production codebases receiving routine, small maintenance tasks or minor bug fixes that already have an up-to-date plan and decision record.
- Tasks that are already in the middle of an approved execution phase (use `implementation-plan` directly).
- Diagnostic-only inspections that do not establish project governance (use `repo-diagnostics` instead).

## Modes

Pick the smallest mode that answers the question, and say which one you use:

| Mode | Use it for | Reviews | Documents |
|---|---|---|---|
| `fast` | A quick health check, or taking over a project for a small piece of work | One agent, one pass | None written; findings and questions go in the reply |
| `standard` (default) | Taking over or resuming a project | One agent applies the three perspectives of step 2 in turn | Only documents the project lacks; existing ones stay where they are |
| `deep` | A new project, or one whose plans and decisions conflict | Three independent reviewers and a debate round, when the budget allows several models or agents | The full set, after the owner agrees to any move or merge |

Every mode keeps the project's own contract: its AGENTS.md or CLAUDE.md, its decision record (an ADR
folder, DECISIONS.md or similar) and its plan or roadmap. Intake never moves, renames or merges an
existing document without the owner's approval. A small maintenance task needs no intake at all.

## Procedure

1. **Recall context, stakeholder instructions, and repository facts**
   - Check recent stakeholder messages and project directives (newest first). They take precedence over existing plans, summaries, and historical notes.
   - Query project memory or decision archives to confirm prior architecture or product decisions so settled questions are never re-asked.
   - Inspect the codebase in read-only mode using `repo-diagnostics`: identify repository root, git branch, commit status, runtime, package manager, build scripts, and existing documentation. Do not install dependencies or run build loops.
   - Catalog existing documentation. If multiple conflicting plans or todo lists exist, mark them as legacy evidence to be retired into the canonical document trio.

2. **Review the project from three perspectives**
   - In `fast` mode, one read-only pass covers the inventory and the riskiest findings. In `standard` mode, one agent applies the three perspectives below in turn. In `deep` mode, dispatch three independent read-only reviews across distinct models or agents to prevent blind spots and groupthink:
     - **Reviewer 1 (Inventory & Hygiene):** Map file tree, manifests, package scripts, configuration, localization files, environment variable references, dead code, and conflicting legacy documentation.
     - **Reviewer 2 (Architecture, Engineering, Security & QA):** Audit system boundaries, data and authentication models, technical debt, automated test coverage, CI/CD pipelines, dependency vulnerabilities, secret exposure risks, and release readiness.
     - **Reviewer 3 (Product, Feasibility, Market & Design):** Evaluate feasibility, identify audience and competitor gaps, audit UI/UX patterns and content standards, and outline initial requirements.
   - Enforce read-only inspection. Workers and reviewers must not modify files, execute arbitrary install scripts, or bypass permission boundaries.

3. **Synthesize findings and conduct an evidence-based debate round**
   - Compile the findings for the mode: in the reply (`fast`), a short findings note in the project's evidence folder (`standard`), or an **Intake Review & Debate Synthesis Matrix** (`intake-synthesis.md`) with the debate round (`deep`).
   - Identify points of disagreement (e.g. architecture choices, framework selection, migration paths, or testing strategies).
   - Require each perspective to cite primary evidence (specific file paths, lines, commit history, or external benchmarks) to resolve contradictions. Settle technical questions using evidence; isolate only genuine business, policy, or scope decisions for stakeholder resolution.

4. **Resolve open requirements in a single batched questionnaire**
   - Filter out any questions already answered in recent instructions, decision records, or project memory.
   - Consolidate all unresolved scope, business, brand, and feature decisions into **one numbered multiple-choice questionnaire** in the stakeholder's preferred working language.
   - For each question, provide a 1-line context summary and 2–4 concrete options with explicit trade-offs (scope, cost, timeline), placing the recommended option first (`A) (Recommended) ...`).
   - Record every confirmed decision immediately in the project's decision record (for example `DECISIONS.md` or an ADR folder) and persistent project memory. If the same policy or tool decision is confirmed across multiple projects, consider promoting it to global organizational preferences.

5. **Select and apply the default skill pack for the project type**
   - Classify the project into its primary type (`ios`, `android`, `mobile`, `web`, `saas`, `game`, `3d`, `api`, or `social`) and note secondary surface flags (`has_backend`, `has_admin`, `has_3d`, `has_mobile_build`).
   - Apply the tiered skill architecture:
     - **Tier D (Universal Baseline):** Project leadership, feasibility review, requirements engineering, writing and anti-slop review, localization parity, source verification, memory management, workspace hygiene, and cost monitoring.
     - **Tier C (Software Core):** Architecture review, senior development patterns, smoke testing, performance profiling, security and dependency audits, CI/CD pipeline review, and error monitoring.
     - **Tier P (Project-Type Pack):** Specific skills, testing tools, and domain utilities defined in [references/default-skill-sets.md](references/default-skill-sets.md).
   - Audit required external tools, libraries, and open-source packages for compatible licenses (MIT, Apache-2.0, BSD) and identify any restrictions or caveats before adopting them.

6. **Schedule domain gates and write the canonical document trio**
   - Schedule quality gates across four lifecycle waves in the project's plan from day one (see [references/domain-gates-and-templates.md](references/domain-gates-and-templates.md)):
     - **Wave 1 (Intake, Feasibility & Baseline):** Charter and scope, feasibility kill criteria, market/competitor baseline, PRD with acceptance criteria, first-draft copy for search/assistants, verified claims, and architecture sign-off.
     - **Wave 2 (Design, Component Adaptation & Media):** Design direction, reference pattern adaptation (captured from live motion, never copied 1:1), unique project media, and interface copy review.
     - **Wave 3 (Coherent QA Bundle & Release Readiness):** Project-fit test suite (smoke, E2E, UAT, accessibility, security, performance), locale parity sign-off, store submission metadata (for mobile), error monitoring setup, transactional communications, and green CI build.
     - **Wave 4 (Acquisition, Observability & Hygiene):** Stakeholder-approved publication schedule, production monitoring, and workspace artifact cleanup.
   - Keep the project's existing documents and their layout. Create only what is missing, and only in `standard` or `deep` mode. A project without them gets three canonical root documents:
     - `DECISIONS.md`: Active decision register (newest entry first). Initial entry records charter, scope, stack choices, stakeholder answers, kill criteria, and retired legacy documents.
     - `AGENTS.md`: Canonical project contract for all AI agents and tools. Defines identity, authority hierarchy, runtime commands, environment variable names (never values), installed skill pack, and operating boundaries.
     - `PLAN.md`: Active execution plan (top block first). Outlines deliverables grouped into coherent batches with domain gate checkpoints.

## Concrete checks

- **Authority and Context:**
  - Stakeholder instructions from the last 48 hours have been reviewed and applied.
  - Project memory was queried before asking questions; no recorded decision is re-asked.
  - Exactly one repository root, runtime, and package manager are identified.

- **Review and Debate:**
  - The review matched the mode: one pass (`fast`), three perspectives by one agent (`standard`), or three independent reviewers (`deep`), all without write access.
  - Contradictions are documented and resolved with citations in the synthesis for the mode (`intake-synthesis.md` in `deep` mode).
  - Open questions are presented in a single batched questionnaire with trade-offs.

- **Governance and Documentation:**
  - The project's existing documents are where they were; any missing contract, decision record or plan was created once, and nothing was moved or merged without approval.
  - All competing plans, ad-hoc todo lists, and legacy status files are retired.
  - No credential values or secret tokens are printed or committed; only variable names are referenced.
  - In `standard` and `deep` mode, four domain gate waves are scheduled in the project's plan with verifiable pass criteria.

## Common issues & anti-patterns

- **Writing code during intake:** Starting feature implementation before establishing the baseline, leading to wasted rework when requirements or architecture shift.
- **Intake bureaucracy on small work:** Turning a one-line fix or a short maintenance task into reviews, a questionnaire and new documents. Use `fast` mode or skip intake.
- **Reshaping a mature project:** Replacing a working ADR folder, roadmap or contributor guide with a new document set the owner did not ask for.
- **Micro-questioning the user:** Interrupting the stakeholder with one question at a time instead of presenting a single, structured multiple-choice batch.
- **Duplicate planning documents:** Creating separate todo lists, status files, or alternative plans that drift out of sync with the project's plan.
- **Assuming rather than verifying:** Guessing runtime versions, package managers, or environment variables instead of reading lockfiles and configuration files directly.
- **Copying reference designs verbatim:** Direct 1:1 copying of third-party reference components instead of adapting them to project design tokens and architecture.
- **Deferred quality gates:** Delaying testing, accessibility, security, or error monitoring until after launch instead of scheduling them from day one.
- **Exposing secrets in documentation:** Writing API keys or tokens into the project contract (such as `AGENTS.md`) or logs instead of referencing variable names.

## Required output

Return:
1. The findings for the mode: in the reply (`fast`, no files written), a short findings note in the project's evidence folder (`standard`), or `intake-synthesis.md` with the debate round (`deep`).
2. The stakeholder multiple-choice questionnaire (if open questions remain) or confirmation that all requirements are resolved.
3. The mode used, and the documents created or confirmed (in `standard` or `deep` mode), with the confirmed skill pack and scheduled domain gates.
4. In `standard` and `deep` mode, the list of retired legacy planning files and the single next work item in the project's plan.

## Safety & boundaries

- Perform read-only codebase inspection during intake; do not run destructive migrations or dependency installs.
- Never print, log, or commit secret values, access tokens, or private credentials.
- All external dependencies and libraries must have verified, permissive open-source licenses.
- Settle technical questions with codebase evidence; escalate business, brand, and scope decisions to the project owner.

## Completion criteria

In `fast` mode, intake is complete when the findings and any batched questions are in the reply and no
project file was written.

In `standard` and `deep` mode, intake is complete when:
- The reviews for the chosen mode, and in `deep` mode the debate synthesis, are recorded in project evidence.
- All open requirements are resolved through the batched questionnaire and recorded in the project's decision record.
- The project type is classified and its default skill pack is configured.
- The four lifecycle gate waves are scheduled in the project's plan.
- The project has one contract, one decision record and one plan, in its existing layout or newly created where missing.

## Supporting references

- [default-skill-sets.md](references/default-skill-sets.md): Complete skill tiers, per-project-type packs, catalog must-haves, and license guidelines.
- [domain-gates-and-templates.md](references/domain-gates-and-templates.md): Four-wave domain gate schedule, gate evidence format, environment variable standards, and copy-ready markdown templates.

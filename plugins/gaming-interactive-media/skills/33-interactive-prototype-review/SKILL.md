---
name: interactive-prototype-review
description: Use when you need to review prototypes for core interaction, feedback, playability, and implementation scope.
---

# Interactive Prototype Review

## Purpose

Review an interactive prototype — game, app, or tool — against its stated purpose: does the core interaction loop work, is feedback latency acceptable, does the prototype demonstrate the right fidelity for its stage, and is the code throwaway or worth keeping. Avoid over-engineering a prototype while ensuring it answers the design question it was built to test.

## When to use

- A game jam prototype is being evaluated for "is this fun enough to continue?"
- A UX prototype is being handed off to engineering and needs a scope/fidelity assessment.
- A proof-of-concept is being promoted to a production codebase and needs an architectural readiness check.
- A client demo is being reviewed before a stakeholder presentation.

## When not to use

- The prototype has already been promoted to production and full architectural review is needed — use game-architecture-review or mobile-app-review.
- The review is for a finished shipping product, not a prototype.
- The prototype is a static mockup (no code, no interaction) — this skill requires runnable or reviewable interactive behavior.

## Procedure

1. **Clarify the prototype's stated question.** What is this prototype trying to prove or disprove? A physics mechanic, a navigation flow, a monetization UI, a multiplayer latency model? If the question is not stated, ask before proceeding — a prototype that doesn't answer a question is scope without direction.
2. **Assess fidelity vs. scope alignment.** Check whether the prototype's fidelity matches its stage. A week-1 concept prototype should be throwaway code with placeholder art. A pre-launch demo should be representative. Flag over-engineered prototypes (full ECS architecture for a 3-day jam) and under-specified demos (lorem ipsum text in a stakeholder presentation).
3. **Review the core interaction loop.** Identify the loop: player action → game/app response → feedback → next player decision. Execute or trace this loop in the code. Measure or estimate the latency from input to feedback. Acceptable thresholds: <100ms for direct manipulation, <200ms for action confirmation, <1s for async operations with indicator.
4. **Evaluate feedback quality.** For each interaction, verify there is at least one clear feedback signal (visual, audio, or haptic). Check that feedback is immediate (<1 frame delay), proportional (strong action = strong feedback), and unambiguous (the player/user knows what happened).
5. **Review scope boundaries.** List features that are implemented vs. stubbed vs. missing. Confirm the missing features are intentionally out of scope for this prototype's question, not accidentally forgotten. Flag features that are partially implemented — half-finished code creates ambiguity about what is "supposed to work."
6. **Assess throwaway vs. keep decision.** Evaluate the codebase for: hardcoded values that would need parameterization, no error handling, no save state, global mutable state, no separation of concerns. A prototype with these traits should be rebuilt for production, not refactored. If >30% of code is structured well enough to keep, note which parts are salvageable.
7. **Check for blocking bugs.** Identify any bug that would prevent a reviewer, playtester, or stakeholder from completing the intended interaction flow. These are must-fix before the prototype is shared, regardless of throwaway status.
8. **Review platform and device coverage.** Confirm the prototype runs on the target platform(s) for review (web, specific device, specific OS version). Note any dependency that prevents running (missing SDK, locked asset, unresolved import).
9. **Summarize findings** with a prototype verdict: Continue / Pivot / Stop / Promote to production.

## Checklist

- [ ] Prototype question stated and answerable from this build
- [ ] Fidelity appropriate for stage (not over-engineered, not misleadingly rough for a demo)
- [ ] Core interaction loop executable end-to-end without crash
- [ ] Input-to-feedback latency: <100ms direct manipulation, <200ms action confirmation
- [ ] Every interaction has at least one clear feedback signal
- [ ] Scope boundaries documented: what is in/out intentionally
- [ ] No partially implemented features that create ambiguity
- [ ] Throwaway vs. keep assessment documented for each major system
- [ ] No blocking bugs that prevent the intended test scenario
- [ ] Runs on target review platform without missing dependencies

## Common issues & anti-patterns

- **Prototype without a question**: a 2-week prototype that implements 8 features but does not conclusively test any single hypothesis. Scope creep in prototypes delays learning.
- **Over-fidelity polish on throwaway code**: spending 3 days adding particle effects to a mechanic prototype that will be rewritten. Polish belongs in vertical slices, not core mechanic tests.
- **Feedback latency hidden by animation**: the action resolves in 300ms but an animation plays at frame 0, so it "feels" fast. If the game state does not update until frame 18 (300ms at 60fps), a smart player can abuse the gap.
- **Hardcoded test values presented as design**: damage = 47, level = 3, speed = 2.7 are placeholders that playtesters will interpret as intended design decisions. Label placeholders clearly.
- **Half-implemented save system**: a prototype where "load" sometimes works and sometimes resets to default. This destroys a stakeholder demo. Either implement save correctly or remove the button.
- **Desktop-only prototype for a mobile pitch**: prototype runs only on a developer's Mac, but the pitch is for an App Store product. Stakeholders cannot evaluate touch ergonomics.
- **No reset path**: no way to restart the prototype loop without quitting and relaunching. Every test session requires a developer present to restart. Add a debug reset keybind.

## Required output

Return a structured report with:
1. Prototype question and whether the build answers it (yes / partially / no).
2. Core interaction loop trace with measured or estimated feedback latency.
3. Findings table: Area | Severity | Issue | Fix or Defer decision.
4. Throwaway vs. salvageable assessment per system.
5. Verdict: Continue / Pivot / Stop / Promote — with one-sentence rationale.

## Safety

- Do not modify prototype source files unless explicitly asked — prototypes are often shared states between multiple contributors.
- Do not run builds or submit to stores.
- Do not share or reproduce proprietary design documents found in the prototype repository.

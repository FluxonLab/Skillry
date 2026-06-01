---
name: interactive-prototype-review
description: Use when you need to review prototypes for core interaction, feedback, playability, and implementation scope.
---

# Interactive Prototype Review

## Purpose
Review an interactive prototype — game, app, or tool — against its stated purpose: does the core interaction loop work, is feedback latency acceptable, does the prototype show the right fidelity for its stage, and is the code throwaway or worth keeping. The goal is to avoid over-engineering a prototype while ensuring it answers the design question it was built to test. The deliverable is a verdict — Continue / Pivot / Stop / Promote — backed by a measured interaction-loop trace and a throwaway-vs-salvageable assessment.

## When to use
- A game-jam prototype is being judged for "is this fun enough to continue?"
- A UX prototype is being handed to engineering and needs a scope/fidelity assessment.
- A proof-of-concept is being promoted to a production codebase and needs an architectural readiness check.
- A client demo is being reviewed before a stakeholder presentation.

## When not to use
- The prototype is already in production and needs a full architectural review — use game-architecture-review or mobile-app-review.
- The review is for a finished shipping product, not a prototype.
- The "prototype" is a static mockup with no code or interaction — this skill needs runnable, reviewable behavior.

## Procedure
1. **Clarify the prototype's stated question.** What is it trying to prove or disprove — a physics mechanic, a navigation flow, a monetization UI, a latency model? If the question is not stated, ask before proceeding; a prototype that answers no question is scope without direction.
2. **Assess fidelity vs scope alignment.** Match fidelity to stage. A week-one concept should be throwaway code with placeholder art; a pre-launch demo should be representative. Flag over-engineered prototypes (a full ECS for a 3-day jam) and under-specified demos (lorem ipsum in a stakeholder pitch).
3. **Review the core interaction loop.** Identify it: action → response → feedback → next decision. Trace or run it. Measure input-to-feedback latency against thresholds: under 100ms for direct manipulation, under 200ms for action confirmation, under 1s for async ops with an indicator.
4. **Evaluate feedback quality.** Each interaction needs at least one clear signal (visual, audio, or haptic), delivered immediately (under one frame), proportional to the action, and unambiguous about what happened.
5. **Review scope boundaries.** List features that are implemented vs stubbed vs missing. Confirm missing items are intentionally out of scope, not forgotten, and flag partially implemented features that create ambiguity about what is "supposed to work."
6. **Assess throwaway vs keep.** Evaluate for hardcoded values needing parameterization, no error handling, no save state, global mutable state, and no separation of concerns. A prototype with these traits should be rebuilt, not refactored. If more than ~30% of the code is structured well enough to keep, note which parts are salvageable.
7. **Check for blocking bugs.** Identify any bug that prevents a reviewer, playtester, or stakeholder from completing the intended interaction flow — these are must-fix before sharing, regardless of throwaway status.
8. **Review platform and device coverage.** Confirm the prototype runs on the target review platform(s). Note any dependency that blocks running (missing SDK, locked asset, unresolved import).
9. **Decide salvageability per system.** Score each major system as throwaway or keep against the throwaway signals (hardcoded values, global state, no error handling, no separation of concerns); a build above ~30% keep-worthy code may justify Promote.
10. **Summarize** with a verdict: Continue / Pivot / Stop / Promote to production, stated first.

## Concrete checks
- Prototype question stated and answerable from this build.
- Fidelity appropriate for the stage (not over-engineered, not misleadingly rough for a demo).
- Core interaction loop executable end-to-end without a crash.
- Input-to-feedback latency: under 100ms direct manipulation, under 200ms action confirmation.
- Every interaction has at least one clear feedback signal.
- Scope boundaries documented: what is in/out, intentionally.
- No partially implemented features creating ambiguity.
- Throwaway-vs-keep assessed for each major system.
- No blocking bugs preventing the intended test scenario.
- Runs on the target review platform with no missing dependency.
- A runnable build or hosted link exists so stakeholders are not dependent on the author's machine.
- A debug reset path lets a tester restart the loop without relaunching.
- The verdict (Continue/Pivot/Stop/Promote) is stated up front, not buried under findings.
- Measured latency is labeled as measured; estimated latency is labeled as estimated.

## Commands
```bash
# Confirm the prototype runs at all on the review platform
godot --headless --quit 2>&1 | rg -i "error|script error|fail" || echo "boots clean (Godot)"
npm run dev 2>&1 | head -20            # web/tool prototype: capture startup

# Size the codebase to judge throwaway vs keep
find . \( -name '*.gd' -o -name '*.cs' -o -name '*.ts' -o -name '*.js' \) -not -path '*/.*' \
  -exec wc -l {} + | tail -1

# Hardcoded placeholder values presented as design
rg -n "= *(47|3\.7|2\.7|100|9999)\b|TODO|FIXME|placeholder|lorem" --type-add 'gd:*.gd' -tgd -tcs -tts

# Throwaway signals: global mutable state, no error handling
rg -n "static var |global |window\.\w+ *=|public static" --type-add 'gd:*.gd' -tgd -tcs -tts | head
rg -n "try|catch|except|on_error" --type-add 'gd:*.gd' -tgd -tcs -tts | wc -l   # near-zero = no error handling

# Half-implemented save/load (a common demo-killer)
rg -n "save|load|persist" -i --type-add 'gd:*.gd' -tgd -tcs -tts | head

# Reset path for repeated test sessions
rg -n "reset|restart|new_game|reload_current_scene|location\.reload" --type-add 'gd:*.gd' -tgd -tcs -tts \
  || echo "no reset path — every test needs a relaunch"
```
```bash
# Measure input-to-feedback latency (web prototype) with the DevTools performance trace
# In the browser console, mark input and the resulting visual update:
#   performance.mark('input'); ... performance.mark('feedback');
#   performance.measure('latency','input','feedback');
# then read it:
node -e 'console.log("inspect performance.getEntriesByName(\"latency\") in DevTools")'

# Partial / stubbed features that create ambiguity about what "works"
rg -n "TODO|FIXME|not implemented|stub|throw new Error\(.unimplemented" -i --type-add 'gd:*.gd' -tgd -tcs -tts

# Feedback hooks per interaction (silent-action audit)
rg -n "play_sfx|AudioStreamPlayer|emit_particle|tween|animate|vibrat|flash" --type-add 'gd:*.gd' -tgd -tcs -tts | head

# Run on the actual target platform, not just the dev machine
rg -n "platform|isMobile|ontouchstart|Input\.touch|UnityEngine\.iOS" -i --type-add 'gd:*.gd' -tgd -tcs -tts | head
```
```bash
# Throwaway signals: hardcoded constants, no separation of concerns, global state
rg -n "const |readonly |#define |static var" --type-add 'gd:*.gd' -tgd -tcs -tts | wc -l
rg -n "Singleton|GameManager\.Instance|global\.|window\." --type-add 'gd:*.gd' -tgd -tcs -tts | head

# Salvageable signals: tests, typed interfaces, modular files
find . -name '*test*' -o -name '*spec*' | head
rg -n "interface |abstract class|class_name |export interface" --type-add 'gd:*.gd' -tgd -tcs -tts | head

# Can it even produce a shareable build? (hosted link / packaged artifact)
ls dist build *.app *.exe *.apk index.html 2>/dev/null || echo "no shareable build artifact found"
jq -r '.scripts.build // "no build script"' package.json 2>/dev/null
```

## Fidelity expectation by stage
| Stage | Code | Art | Acceptable shortcuts |
|-------|------|-----|----------------------|
| Concept (days 1–3) | throwaway | placeholder shapes | hardcoded values, no save |
| Mechanic test | throwaway-ish | grey-box | one level, debug UI |
| Vertical slice | keep candidate | near-final for the slice | scope limited to one segment |
| Pre-launch demo | representative | representative | non-demoed features stubbed clearly |

## Verdict criteria
| Verdict | When |
|---------|------|
| Continue | the question is answered "yes, this works" — keep iterating |
| Pivot | the loop works but the answer is "not fun / not viable as-is" |
| Stop | the question is answered "no" — the hypothesis failed |
| Promote | representative fidelity + >30% salvageable code + no blocking bugs |

## Common issues & anti-patterns
- **Prototype without a question.** A two-week build with eight features that conclusively tests no single hypothesis. Scope creep delays the learning the prototype exists to deliver.
- **Over-fidelity polish on throwaway code.** Three days of particle effects on a mechanic that will be rewritten. Polish belongs in a vertical slice, not a core-mechanic test.
- **Feedback latency hidden by animation.** The action resolves in 300ms but an animation fires at frame 0 so it "feels" fast; a smart player exploits the gap before state updates at frame 18.
- **Hardcoded test values read as design.** `damage = 47` placeholders get interpreted by playtesters as intended decisions. Label placeholders explicitly.
- **Half-implemented save system.** A "load" that sometimes works and sometimes resets destroys a stakeholder demo. Implement it correctly or remove the button.
- **Desktop-only prototype for a mobile pitch.** It runs only on a developer's machine, so stakeholders cannot evaluate touch ergonomics for an App Store product.
- **No reset path.** No way to restart the loop without relaunching, so every test session needs a developer present. Add a debug reset keybind.
- **Refactoring throwaway code.** Spending a day cleaning architecture in a prototype that should be rebuilt for production. If it is throwaway, leave it; if it is keep-worthy, plan a proper rebuild — do not split the difference.
- **Demoing on a build nobody else can run.** A prototype that only launches from the author's IDE cannot be evaluated by stakeholders. Produce a runnable build or a hosted link.
- **Mistaking polish for proof.** A beautiful prototype that does not actually test the risky assumption. Judge by whether the question is answered, not by how it looks.
- **Burying the verdict.** A report full of findings with no clear Continue/Pivot/Stop/Promote call leaves the team unable to act. Lead with the verdict.

## Required output
Return a structured report with:
1. The prototype question and whether the build answers it (yes / partially / no).
2. A core-interaction-loop trace with measured or estimated feedback latency.
3. Findings table: `Area | Severity | Issue | Fix or Defer decision`.
4. A throwaway-vs-salvageable assessment per system.
5. A verdict — Continue / Pivot / Stop / Promote — with a one-sentence rationale.

## Safety
- Do not modify prototype source files unless explicitly asked — prototypes are often shared state between contributors.
- Do not run builds or submit to stores.
- Do not share or reproduce proprietary design documents found in the prototype repository.
- Distinguish measured latency from estimated latency in the report; do not present an estimate as a measurement.
- Do not invest in cleaning up code you have judged throwaway; a rebuild decision is cheaper than a half-refactor.
- Do not let visual polish substitute for evidence that the core question was answered.

## Completion criteria
Done means the prototype's question is identified, the interaction loop is traced with a latency figure, fidelity and scope are assessed, throwaway-vs-keep is decided per major system, blocking bugs and platform gaps are listed, and a Continue/Pivot/Stop/Promote verdict is recorded with rationale.

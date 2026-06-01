---
name: tutorial-and-how-to-writing
description: Use when you need to write or classify learning-oriented and task-oriented documentation using the Diátaxis framework — separating tutorials, how-to guides, reference, and explanation, and producing runnable, verified step-by-step instructions.
---

# Tutorial and How-To Writing

## Purpose

Apply the Diátaxis framework to put each document in the right mode and write it well. Diátaxis splits docs into four kinds with different jobs: tutorials (learning-oriented, hold the reader's hand to a guaranteed success), how-to guides (task-oriented, get an experienced user through one real goal), reference (information-oriented, dry and complete), and explanation (understanding-oriented, the why). The most common documentation failure is mixing these modes in one page. This skill keeps them separate and makes every instructional step runnable and verified.

## When to use

- Writing onboarding material that must take a beginner from zero to a working result.
- Writing a focused "how do I do X" guide for users who already know the basics.
- A page is confusing because it mixes teaching, recipes, theory, and reference at once.
- Step-by-step instructions exist but were never run and may be broken.
- Planning a docs section and deciding what kind of document each topic needs.

## When not to use

- The need is an exhaustive parameter/endpoint listing (use api-reference-docs — that is the reference quadrant).
- The need is structuring the whole site/README (use readme-and-docs-structure).
- A one-line FAQ answer suffices and a full guide would be overkill.

## Procedure

### 1. Classify the document by Diátaxis quadrant

Ask the reader's situation: are they learning (tutorial), trying to get a specific job done (how-to), looking something up (reference), or trying to understand (explanation)? Pick exactly one. If a draft serves two, split it.

### 2. For a tutorial: design a single guaranteed-success path

A tutorial is a lesson, not a menu. Choose one concrete outcome, remove all optional branches, and ensure every learner who follows it lands in the same working state. State prerequisites and the end result up front.

### 3. For a how-to: scope to one real task with assumed competence

A how-to assumes the reader knows the fundamentals and wants results. State the goal, list prerequisites, give the minimal ordered steps, and stop. Offer realistic variations ("if you use X instead of Y") but do not teach the basics.

### 4. Write runnable, verifiable steps

Each step is one action with a copy-pasteable command and an observable result the reader can check.

```bash
# Pattern for every step: action + expected, checkable result
mkdir demo && cd demo
python3 -m venv .venv && . .venv/bin/activate
pip install example-package
example-cli --version
# Expected: example-cli 2.3.0
```

### 5. Verify the whole path end to end from a clean state

```bash
# Run the entire tutorial/how-to in a throwaway environment, unmodified
( set -e; cd "$(mktemp -d)"; \
  echo "step 1..."; <command-1>; \
  echo "step 2..."; <command-2> )
echo "exit: $?"   # must be 0; any non-zero means a step is wrong
```

### 6. Add a verification and troubleshooting close

End with a "you should now see…" success check and a short troubleshooting list for the two or three most common failure points.

## Concrete checks

- [ ] The document declares its Diátaxis type and stays in that one mode.
- [ ] A tutorial has exactly one outcome and no optional branches.
- [ ] A how-to is scoped to a single named task and does not teach fundamentals.
- [ ] Prerequisites (tools, versions, accounts) are stated before step 1.
- [ ] The end result is described up front so the reader knows the target.
- [ ] Every step is one action with a copy-pasteable command.
- [ ] Every step shows an observable, checkable result.
- [ ] The entire path was executed from a clean environment and exited 0.
- [ ] Commands use placeholder values for any secret or personal data.
- [ ] A final success check lets the reader confirm completion.
- [ ] A short troubleshooting section covers the top failure points.
- [ ] Explanation/theory is linked, not inlined, keeping the guide actionable.

## Templates

```markdown
# Tutorial: Build your first widget pipeline

By the end you will have a running pipeline that processes one sample file.

**Prerequisites:** Python 3.11+, a terminal, ~10 minutes.

## 1. Create and enter a clean workspace
    mkdir widget-tutorial && cd widget-tutorial
You should see an empty directory.

## 2. Install the toolkit
    python3 -m venv .venv && . .venv/bin/activate
    pip install widget-toolkit
Check: `widget --version` prints `widget 1.x`.

## 3. Run the pipeline on the sample
    widget run --input sample.csv --out result.json
Check: `result.json` exists and contains a `count` field.

## You did it
You now have a working pipeline. Next, see the [how-to: process your own data](../how-to/custom-input.md).

## Troubleshooting
- `command not found: widget` → the venv is not active; re-run `. .venv/bin/activate`.
- Empty `result.json` → confirm `sample.csv` is non-empty.
```

```markdown
# How-to: Rotate the service API key

**Goal:** replace the active API key with zero downtime.
**Prerequisites:** admin access, the `service-cli` installed.

1. Create a new key:        `service-cli keys create --name rotated`
2. Deploy it as `SERVICE_API_KEY` (placeholder; never commit the value).
3. Verify traffic uses it:  `service-cli keys usage --name rotated` shows > 0.
4. Revoke the old key:      `service-cli keys revoke --name old`
```

## Common issues & anti-patterns

- Mixing modes: a "tutorial" stuffed with reference tables and architecture theory, so the beginner stalls.
- Offering choices in a tutorial ("you can use A or B") — branching breaks the guaranteed path.
- How-to guides that re-teach installation the reader already did.
- Steps with no expected output, so the reader cannot tell if it worked.
- Instructions written from memory and never executed, so a step is subtly wrong.
- Hardcoded secrets, absolute machine paths, or environment-specific values in commands.
- A "quick" guide that grows into an unscoped everything-page.

## Required output

Produce: (1) the Diátaxis classification and why; (2) the structured document with prerequisites, ordered runnable steps, and per-step expected results; (3) evidence the full path was run clean (exit 0); (4) a success check and troubleshooting section; (5) links out to reference/explanation rather than inlined theory.

## Safety

- Run all steps in a throwaway directory/environment; never against production systems or real user data.
- Use placeholder credentials and relative or `$HOME`-based paths, never real secrets or absolute machine paths.
- Do not include destructive commands without an explicit warning and a safe default.
- Verify before publishing; never ship steps you have not executed.

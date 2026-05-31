---
name: llm-evaluation-review
description: Use when you need to review LLM eval plans, rubrics, datasets, expected outputs, and regression checks.
---

# LLM Evaluation Review

## Purpose

Review an LLM evaluation framework for dataset quality, rubric precision, LLM-as-judge configuration, regression coverage, hallucination detection methods, and metric validity. The goal is to catch evaluation design flaws that produce misleading scores — a poorly designed eval is worse than no eval because it creates false confidence in a system that may be failing in ways the eval does not measure.

## When to use

- An existing eval suite is giving inconsistent results across runs or between human reviewers.
- A new model version is being evaluated against the previous version and you need to verify the comparison is fair.
- The eval was designed by the same team that built the system being evaluated, creating objectivity risk.
- Hallucination rates appear low in the eval but users are reporting factual errors — the eval is not catching real failures.
- An LLM-as-judge setup is being introduced and you need to verify it is calibrated correctly before trusting its scores.
- The golden set has not been updated since the product requirements changed significantly.
- Eval results are being used to make a go/no-go deployment decision and you need to verify the eval is fit for that purpose.

## When not to use

- You are writing the prompts or building the system being evaluated (use `prompt-systems-review`).
- The question is about retrieval quality, not generation quality (use `rag-vector-search-review`).
- You need a governance/permission review of the eval infrastructure, not the eval methodology.
- The eval is a one-off human preference study, not a systematic repeatable evaluation.

## Procedure

1. **Audit the eval dataset.** Record: total number of examples, creation method (human-annotated / LLM-generated / sampled from production logs / manually constructed), date of creation and last update, and distribution across task categories. A dataset smaller than 100 examples for a production system has insufficient statistical power to detect regressions reliably. A dataset not updated after a significant product requirement change is measuring the wrong behavior.

2. **Check golden set validity.** For a random sample of 10-20 golden-set examples: is the expected output unambiguously correct under current product requirements? Does the input represent current production traffic patterns? Are the annotator guidelines documented and accessible? Golden examples that were correct under old requirements but are now wrong will make the current system look like it is regressing when it is actually improving.

3. **Review rubric precision.** For each rubric criterion, apply the two-annotator test: could two independent annotators reach the same score for the same output without discussion? If the criterion contains subjective adjectives — "helpful," "clear," "appropriate," "good" — it fails the test. Replace each failing criterion with an observable, scale-anchored definition:
 - Bad: "Is the response helpful?"
 - Good: "Does the response directly answer the specific question asked, without requiring the user to ask a follow-up question to get the actual answer? (1 = yes, 0 = no)"

4. **Audit LLM-as-judge configuration.** If an LLM is used to score outputs:
 - Record the judge model name and version
 - Confirm the judge model is different from the model being evaluated (self-evaluation has strong bias toward the model's own style)
 - Check that the judge prompt contains: the rubric with scale anchors, at least 2 scored reference examples per criterion, and a chain-of-thought requirement before the final score
 - Verify judge outputs are parsed structurally (regex or JSON parsing), not by string matching on free text
 - Test the judge for position bias: run 30 pairs with response order swapped; if the preferred response flips more than 20% of the time, there is significant position bias

5. **Measure inter-annotator agreement.** For human-judged criteria, compute Cohen's Kappa (for categorical ratings) or Krippendorff's Alpha (for ordinal scales) on a minimum 50-example overlap set where two annotators scored the same examples independently. Kappa below 0.6 means the rubric criterion is too ambiguous to produce reliable scores — rewrite the criterion before using it. For LLM-as-judge, measure agreement between two different judge models on the same 50-example set. High cross-judge disagreement indicates a rubric problem.

6. **Verify hallucination detection coverage.** Check that the eval explicitly tests for:
 - **Ungrounded claims**: the model asserts a fact not supported by the retrieved context (requires a context-grounded eval set)
 - **Stale facts**: the model asserts something true in its training data that is now outdated (requires a time-sensitive fact set with known ground truth)
 - **Numeric assertions**: the model cites a specific number (price, count, date, percentage) that differs from the ground truth source
 - **Entity confabulation**: the model produces a plausible-sounding but non-existent entity (person, product, document)
 An eval that only checks for nonsensical outputs misses the most dangerous category: confident, fluent, wrong statements.

7. **Review regression test structure.** Confirm that there is a fixed, immutable regression set that does not change between evaluations. This set must include: known failure cases from past production incidents (one example per incident), edge cases that caused regressions in previous model versions, and a representative sample of high-traffic query patterns. Regression tests must have binary pass/fail verdicts — not rubric scores that can shift when the judge model is updated.

8. **Check metric selection.** Verify that selected metrics match the task type:
 - BLEU / ROUGE: appropriate only for tasks with a canonical reference output (translation, extractive summarization)
 - Exact-match: appropriate for structured output with a single correct answer (schema compliance, factual extraction)
 - LLM-rubric scores: appropriate for open-ended generation with no single correct output
 - Win rate (pairwise comparison): appropriate for relative quality assessment between two systems
 Confirm statistical significance testing is applied when comparing two system versions. For a 100-example eval set, use McNemar's test (binary verdicts) or Wilcoxon signed-rank test (ordinal scores). A p-value ≥ 0.05 means the observed difference is not statistically reliable.

9. **Confirm eval-to-deployment gate.** Verify that evaluation results gate the deployment decision — a system that does not meet the minimum eval threshold cannot be deployed without a documented exception with named approver. Confirm that eval results are stored with: run ID, model version under test, dataset version, judge model version if LLM-as-judge, and ISO 8601 timestamp. Without this metadata, results are not reproducible.

## Checklist

- [ ] Eval dataset has at least 100 examples for a production system
- [ ] Dataset creation method documented: human / synthetic / production-sampled
- [ ] Dataset last updated after every significant product requirement change
- [ ] Golden-set expected outputs verified as correct under current requirements (sample of 10-20)
- [ ] Annotator guidelines documented and accessible
- [ ] Every rubric criterion is binary or scale-anchored with examples; no subjective adjectives without anchors
- [ ] LLM-as-judge uses a different model (name + version) than the model being evaluated
- [ ] Judge prompt contains rubric, scored reference examples, and chain-of-thought requirement
- [ ] Judge outputs parsed structurally, not by free-text string matching
- [ ] Judge position bias tested on 30 swapped pairs; flip rate below 20%
- [ ] Inter-annotator Kappa ≥ 0.6 for human-judged criteria (or cross-judge agreement measured for LLM-as-judge)
- [ ] Hallucination detection covers: ungrounded claims, stale facts, numeric assertions, entity confabulation
- [ ] Regression set is fixed and immutable; contains past incident cases; has binary verdicts
- [ ] Metric type matches task type (no BLEU for open-ended conversational outputs)
- [ ] Statistical significance test applied when comparing two system versions; p < 0.05 required
- [ ] Eval results stored with run ID, model version, dataset version, judge version, timestamp
- [ ] Deployment is gated on minimum eval threshold with named exception approver

## Common issues & anti-patterns

**Evaluating with the same model you optimized against.** The system was fine-tuned on GPT-4o outputs. The eval uses GPT-4o as the judge. The judge has a strong prior toward GPT-4o style and scores the system higher than human annotators would. The reported quality is inflated. Always use a different judge model family (not just version) than the model used in the system.

**Rubric drift.** The rubric was written 12 months ago when the product had different requirements. Six months ago the requirements changed but the rubric was not updated. The eval now measures old behavior. Teams optimize for the rubric rather than the actual product goal. Version the rubric alongside the product requirements specification; any PR that changes product requirements must also update the eval rubric.

**Cherry-picked regression set.** The regression set contains only examples the current model handles well because "the ones it failed on are fixed now." When a similar failure mode recurs, the regression set does not catch it. Never remove failure cases from the regression set — permanently retain one example per production incident, labeled with the incident date and a description.

**Position bias in pairwise LLM evaluation.** The judge consistently rates the response listed first as better, regardless of quality. On a 100-example pairwise eval, this can shift win rates by 10-15 percentage points — more than the actual quality difference between most model versions. Test for position bias before using pairwise evaluation. If bias exists, either use point-score rubrics instead, or randomize order and average scores across both orderings.

**Statistical significance ignored.** System A scores 0.762, System B scores 0.748. The difference is 1.4 percentage points on a 100-example eval set. The team ships System A because it scored higher. McNemar's test on these results returns p = 0.43 — the difference is not statistically significant. The systems are indistinguishable on this eval set. Either accept the uncertainty or enlarge the eval set until the difference becomes significant.

**BLEU for open-ended generation.** A customer service assistant is evaluated with BLEU against reference responses. BLEU penalizes any paraphrase of the reference, even if semantically equivalent. A correct, clear response that uses different words than the reference gets a low BLEU score. The team optimizes for lexical overlap with the reference, degrading response naturalness. BLEU is a translation metric; do not use it for open-ended generation tasks.

**No eval-to-deploy gate.** Evaluation is performed before each release, the scores are discussed in a meeting, and then deployment proceeds regardless. This is not a gate — it is a ritual. Define a minimum threshold for each key metric. Define the process for blocking deployment when the threshold is not met. Document the exception process for overriding the gate with named approver accountability.

## Required output

Produce an eval review report with:

1. **Scope** — system evaluated, eval suite name and version, review date, prior review date
2. **Dataset assessment** — size, creation method, last update date, task category distribution, coverage gaps
3. **Golden set validity** — sample size checked, count correct / outdated / ambiguous, actionable items
4. **Rubric audit** — table: criterion text, type (binary/scale/subjective), two-annotator test verdict, recommended rewrite for failing items
5. **LLM-as-judge assessment** — judge model, same-as-evaluated flag, prompt structure compliance, position bias test results
6. **Inter-annotator agreement** — metric used (Kappa/Alpha), value, threshold verdict, criteria below threshold
7. **Hallucination coverage** — table: hallucination category, tested (yes/no), test method, results
8. **Regression set status** — size, incident case count, binary verdict enforcement, last update date
9. **Metric validity** — metric used per task type, statistical significance method, p-value for any system comparisons in scope
10. **Eval-to-deployment gate** — gate defined (yes/no), threshold values, exception process defined (yes/no)
11. **Prioritized finding list** — severity (critical/high/medium/low), description, specific fix, impact on score reliability

## Safety

- Do not run eval test inputs against production endpoints that contain real user PII.
- Do not use eval results to make public model capability claims without reporting confidence intervals and the p-value of any comparative claim.
- If the eval reveals the current production system scores below an acceptable safety threshold on a safety-critical criterion, escalate immediately — do not wait for the next scheduled review cycle.
- Do not modify golden-set expected outputs to make the current system score higher; any change requires documented justification, a new annotator sign-off, and a version increment.

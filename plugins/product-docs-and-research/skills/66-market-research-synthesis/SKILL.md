---
name: market-research-synthesis
description: Use when you need to synthesize market, competitor, audience, and positioning research with citations.
---

# Market Research Synthesis

## Purpose

Combine raw research inputs — competitor pages, analyst reports, customer interview notes, survey exports, industry data — into a single coherent synthesis covering market size, competitive landscape, target audience, positioning gaps, and strategic implications. Every claim must be tied to a source. The output is an argument backed by evidence, not a list of summaries stapled together.

## When to use

- You have 3+ research sources on the same market and need a unified picture.
- A go-to-market plan or pitch deck needs a "market context" section backed by evidence.
- A product team needs a competitive teardown before writing a PRD.
- Leadership wants a positioning recommendation backed by data, not opinion.
- A new entrant analysis is needed: who occupies which segment, who is absent, and where the white space is.
- A product strategy document needs a grounded "why now" and "why us" section.

## When not to use

- Only one source is available — that is summarisation, not synthesis.
- The task is primary research (running surveys, conducting interviews) — this skill processes existing research, it does not generate new data.
- The request is a business model review — use `business-model-review` for unit economics and revenue logic.
- The market is one you cannot verify with public data and no sources are provided — state the gap, do not fabricate.

## Procedure

1. **Source intake**: List every provided source with type (primary research, analyst report, public filing, competitor site, news article, customer interview), date, and author or publisher. Sources without dates must be flagged explicitly.
2. **Source credibility assessment**: Flag sources older than 24 months, sources with unknown methodology, and vendor-produced reports with obvious bias (a vendor's "State of the Market" report is marketing, not neutral analysis). Down-weight these accordingly and note the reason in the source table.
3. **Market sizing**: Extract TAM, SAM, and SOM figures if present. Note methodology: bottom-up (built from unit economics and addressable customer count) is more reliable than top-down (a percentage of an analyst-reported total). If figures conflict across sources, surface the conflict explicitly — do not silently pick one value. If sizing data is absent, state it rather than inventing it.
4. **Competitor matrix**: For each named competitor extract: target segment, core value proposition (the job they claim to do for the customer), pricing model if public, key differentiators, and known weaknesses sourced from public reviews, filed complaints, or documented incidents. A matrix row with no weakness entry is not complete — either the weakness is unknown (say so) or the source was insufficient.
5. **Target audience**: Identify stated personas or segments from the research. Cross-check against competitor targeting to find underserved segments — gaps where customers have a problem but no competitor addresses it well. Note demographic, psychographic, and behavioural attributes cited across sources.
6. **Positioning map**: Plot competitors on two axes relevant to the market (examples: price vs. depth of feature set; self-serve vs. enterprise sales motion; vertical-specific vs. horizontal platform; real-time vs. batch). Choose axes that reveal differentiation, not axes where every competitor clusters together. Identify white space on the map.
7. **Market gaps**: Name the gaps — customer problems mentioned in research that no competitor currently addresses well. A gap is only credible if a customer source (interview, review, survey) expresses the unmet need. Inferred gaps from missing features are speculative; label them as such.
8. **Trend identification**: Surface 2–4 market trends (technological, regulatory, behavioural, economic) mentioned across at least 2 independent sources. A trend cited in only one source is a hypothesis, not a finding. Generic trends ("AI is growing") are not acceptable — the trend must be specific to the segment with a concrete mechanism.
9. **Synthesis narrative**: Write a 200–400 word narrative connecting all sections into a single coherent market picture. The narrative must make an argument — "this market has these dynamics, which creates this opportunity, which has these risks" — not just repeat each section in sequence.
10. **Strategic implications**: List 3–5 actionable implications for the product or go-to-market strategy. Each must start with a verb, be specific to the findings, and reference the evidence that supports it.

## Concrete checks

- [ ] All sources listed with date and type; undated sources flagged
- [ ] Credibility flags applied to sources older than 24 months or with obvious vendor bias
- [ ] TAM/SAM/SOM present or explicitly noted as unavailable with reason
- [ ] Methodology noted (bottom-up vs. top-down) for any sizing figure
- [ ] Conflicting figures across sources surfaced rather than silently resolved
- [ ] Competitor matrix covers all named competitors (minimum 3 if available)
- [ ] Each competitor row includes: segment, value proposition, pricing model, key strength, known weakness
- [ ] Weaknesses are sourced from public evidence, not invented
- [ ] Underserved segments identified with supporting evidence
- [ ] Positioning map axes are specific and justified; white space identified
- [ ] At least one market gap stated in customer-problem terms, not feature terms
- [ ] Gaps inferred without customer evidence are labelled as speculative
- [ ] 2–4 trends cited; each from at least 2 independent sources; each specific to the segment
- [ ] Synthesis narrative makes a connected argument, not a list of summaries
- [ ] Strategic implications start with a verb and cite the evidence behind them

## Output template

```
## Market Research Synthesis: [Topic / Product]

### Sources
| # | Source | Type | Date | Credibility notes |
|---|--------|------|------|-------------------|
| 1 | [name] | [type] | [date] | [flag if stale, biased, or unverified] |

### Market size
- TAM: [figure] — methodology: [bottom-up / top-down / analyst], source: [#]
- SAM: [figure or "not available"]
- SOM: [figure or "not available"]
- Conflicts across sources: [describe or "none"]

### Competitor matrix
| Competitor | Target segment | Value proposition | Pricing model | Key strength | Known weakness | Source |
|------------|---------------|-------------------|--------------|--------------|----------------|--------|

### Target audience
- Primary segment: [description + source]
- Secondary segment: [description + source]
- Underserved segment: [description + evidence from customer source]

### Positioning map
Axes: [X axis label] vs [Y axis label]
Rationale for axes: [why these axes reveal differentiation]
[Describe competitor positions by quadrant; note white space]

### Market gaps
1. [Customer problem stated in customer terms] — evidence: [source(s)]; confidence: [sourced / inferred]

### Trends
1. [Trend specific to this segment] — sources: [list]; mechanism: [how it affects this market]

### Synthesis narrative
[200–400 words connecting market size, competitive dynamics, audience gaps, and trends into a single argument]

### Strategic implications
1. [Verb-led actionable recommendation] — based on: [gap / trend / competitor weakness], evidence: [source(s)]
```

## Common issues & anti-patterns

- **Cherry-picking**: Selecting only sources that support a pre-existing conclusion. Counter: always include contradictory evidence and note the conflict explicitly. A synthesis that contains no tension between sources is almost certainly incomplete.
- **Single-source sizing**: Citing one analyst figure for TAM without checking methodology. A $10B market figure from one vendor report is not a market size; it is one vendor's assertion. Cross-reference with a bottom-up estimate built from addressable customer count × average contract value.
- **Feature comparison over value prop**: Listing features in the competitor matrix instead of the job the product accomplishes for the customer. "Has SSO" is a feature. "Enables enterprise IT to enforce access policies without changing user workflows" is a value proposition.
- **Stale data**: Using competitor pricing or product data from 18+ months ago in a fast-moving category. Flag explicitly and recommend re-checking against the live product or latest public release.
- **Generic trends**: "AI is growing" with no specificity to the market. Trends must be particular: "AI-assisted triage in the SMB help desk segment is compressing first-response time from hours to minutes, which reduces the premium customers pay for dedicated support staff." Generic observations are noise.
- **Missing weakness**: A competitor analysis row with only strengths is a sales-pitch level review, not analysis. Every well-funded competitor has a documented weakness in public reviews or community forums.
- **Synthesis equals list of summaries**: The narrative must connect sources into a single argument about what the market means for the product. Restating each source in sequence adds no analytical value.
- **Implied gaps from missing features**: A gap is only credible if a customer expresses the unmet need. "Competitor X has no mobile app" is an observation; "enterprise field teams report losing deal velocity because they cannot update pipeline records on-site" is a gap with evidence.
- **Positioning axes that compress everyone together**: Axes like "quality vs. price" often place all competitors in the same quadrant. Choose axes that actually differentiate: delivery model, integration depth, time-to-value, or regulatory coverage.
- **No synthesis of conflicting signals**: Two sources say the market is growing 30% YoY; one says it is commoditising and contracting. Ignoring the outlier understates the risk.

## Evidence confidence levels

Not all findings carry equal certainty. Label each claim in the output with its confidence level so the reader knows which parts of the synthesis to act on immediately and which to validate further before committing resources:

| Level | Meaning | Example |
|-------|---------|---------|
| Confirmed | Two or more independent sources with recent data agree | TAM figure cross-referenced across an analyst report and a bottom-up calculation |
| Probable | Single credible source or two sources with one being potentially biased | Competitor pricing from their public pricing page (may not reflect negotiated rates) |
| Inferred | Logical inference from indirect evidence; no direct customer statement | "Competitor lacks API access" inferred from absence of developer documentation |
| Speculative | Analyst opinion, trend extrapolation, or reviewer hypothesis | "Regulatory change could open the market within 12 months" |

Apply the label inline: "The SMB segment is underserved (Confirmed — sources 2, 4)." A synthesis with only Confirmed findings is rare and should not be faked by omitting uncertainty. A synthesis where every key strategic claim is Speculative is not ready to support a resource decision.

## Worked synthesis structure

A well-structured synthesis narrative follows this argument shape:

1. **Market context** (1–2 sentences): size, growth direction, and the primary force shaping it right now.
2. **Competitive reality** (2–3 sentences): who dominates, on what axis, and where the current leaders are weakest.
3. **Audience gap** (1–2 sentences): which customer segment is underserved and what problem they are trying to solve that no current competitor solves well.
4. **Trend intersection** (1–2 sentences): which market trend amplifies the gap and creates a window of opportunity.
5. **Strategic implication** (1 sentence): what the evidence, taken together, implies the product or GTM should do.

Example (abbreviated, fictional): "The workflow automation market for mid-market operations teams is growing at 28% CAGR (source 1, 3) but the three market leaders are oriented toward enterprise IT — long implementation cycles, per-seat pricing that penalises adoption, and no self-serve onboarding. Mid-market ops teams (50–500 employees) consistently report in interview data (source 5) that they abandon evaluation when they cannot get a working integration within a week. AI-driven integration suggestion, cited in two analyst reports as the fastest-growing feature category, directly shortens time-to-first-workflow. The synthesis implies that a self-serve product with AI-assisted setup and usage-based pricing has both a differentiated position and a favourable entry window before enterprise vendors close the onboarding gap."

## Required output

Return the structured synthesis using the output template above: source table with credibility notes, market sizing with methodology and conflicts, competitor matrix with all required columns, audience analysis with underserved segments, positioning map with axis rationale and white space, market gaps with customer-evidence citations, trends with multi-source support, a 200–400 word synthesis narrative that makes a coherent argument, and 3–5 actionable strategic implications. Label each claim with its evidence confidence level (Confirmed / Probable / Inferred / Speculative).

## Safety

- Do not fabricate market figures. If sizing data is unavailable, state it explicitly rather than estimating without source.
- Do not copy-paste substantial blocks from paid analyst reports — paraphrase and cite the source.
- Do not name real individuals from customer interviews without consent consideration; anonymise personas to role and company size.
- Competitor weaknesses must be sourced from public evidence (reviews, documented incidents, public filings) — not invented or inferred from product gaps alone.
- Do not present inferred gaps as confirmed customer needs; label inference explicitly.

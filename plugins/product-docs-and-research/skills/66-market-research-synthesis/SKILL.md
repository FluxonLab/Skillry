---
name: market-research-synthesis
description: Use when you need to synthesize market, competitor, audience, and positioning research with citations.
---

# Market Research Synthesis

## Purpose

Combine raw research inputs — competitor pages, analyst reports, customer interview notes, survey exports, industry data — into a single coherent synthesis covering market size, competitive landscape, target audience, positioning gaps, and strategic implications. Every claim must be tied to a source.

## When to use

- You have 3+ research sources on the same market and need a unified picture.
- A go-to-market plan or pitch deck needs a "market context" section.
- A product team needs a competitive teardown before writing a PRD.
- Leadership wants a positioning recommendation backed by evidence, not opinion.
- A new entrant analysis is needed: who occupies which segment, who is absent.

## When not to use

- Only one source is available — that is not synthesis, it is summarisation.
- The task is a primary research task (running surveys, conducting interviews) — this skill processes existing research.
- The request is a business model review — use `business-model-review` for unit economics and revenue logic.
- The market is something you cannot verify with public data and no sources are provided.

## Procedure

1. **Source intake**: List every provided source with type (primary research, analyst report, public filing, competitor site, news article), date, and author/publisher.
2. **Source credibility assessment**: Flag sources older than 24 months, sources with unknown methodology, or vendor-produced reports with obvious bias. Down-weight accordingly.
3. **Market sizing**: Extract TAM/SAM/SOM figures if present. Note methodology (bottom-up vs. top-down). If figures conflict across sources, surface the conflict — do not silently pick one.
4. **Competitor matrix**: For each named competitor extract: target segment, core value proposition, pricing model (if public), key differentiators, known weaknesses (from reviews, public complaints, or positioning gaps). Build a comparison table.
5. **Target audience**: Identify stated personas or segments. Cross-check against competitor targeting to find underserved segments. Note demographic, psychographic, or behavioural attributes mentioned across sources.
6. **Positioning map**: Plot competitors on two axes relevant to the market (e.g., price vs. capability, self-serve vs. enterprise, broad vs. vertical). Identify white space.
7. **Market gaps**: Name the gaps — customer problems mentioned in research that no competitor currently addresses well.
8. **Trend identification**: Surface 2–4 market trends (technological, regulatory, behavioural) mentioned across ≥2 sources.
9. **Synthesis narrative**: Write a 200–400 word narrative connecting all sections into a coherent market picture.
10. **Strategic implications**: List 3–5 actionable implications for the product or go-to-market strategy.

## Checklist

- [ ] All sources listed with date and type
- [ ] Credibility flags applied to outdated or biased sources
- [ ] TAM/SAM/SOM present or explicitly noted as unavailable
- [ ] Competitor matrix covers ≥3 competitors (or all known if fewer)
- [ ] Each competitor row has segment, value prop, and at least one weakness
- [ ] Underserved segments identified
- [ ] Positioning map axes are specific and justified
- [ ] At least one market gap stated in customer-problem terms (not feature terms)
- [ ] 2–4 trends cited with ≥2 sources each
- [ ] Strategic implications are actionable (start with a verb, specific to the market)

## Common issues & anti-patterns

- **Cherry-picking**: Selecting only sources that support a pre-existing conclusion. Counter: always include contradictory evidence and note the conflict.
- **Single-source sizing**: Citing one analyst figure for TAM without checking methodology. Counter: cross-reference with a bottom-up estimate.
- **Feature comparison over value prop**: Listing features in the competitor matrix instead of the job they accomplish for the customer.
- **Stale data**: Using competitor data from 18+ months ago in a fast-moving category. Flag explicitly; recommend re-checking.
- **Generic trends**: "AI is growing" with no specificity to the market. Trends must be specific to the segment and sourced.
- **Missing weakness**: Competitor analysis with only strengths is sales-pitch level, not analysis.
- **Synthesis = list of summaries**: The narrative must connect sources into a single argument, not just repeat each source in sequence.
- **Implied gaps from missing features**: A gap is only real if customers express the unmet need — infer cautiously.

## Required output

```
## Market Research Synthesis: [Topic / Product]

### Sources
| # | Source | Type | Date | Credibility notes |

### Market size
- TAM: [figure or "not available"] — methodology: [bottom-up/top-down/analyst]
- SAM: … SOM: …
- Conflicts: …

### Competitor matrix
| Competitor | Target segment | Value proposition | Pricing model | Key strength | Known weakness |

### Target audience
- Primary segment: [description]
- Secondary segment: [description]
- Underserved segment: [description + evidence]

### Positioning map
Axes: [X axis label] vs [Y axis label]
[Text or ASCII representation; alt: describe positions by quadrant]

### Market gaps
1. [Customer problem] — evidence: [source(s)]

### Trends
1. [Trend] — sources: [list]

### Synthesis narrative
[200–400 words]

### Strategic implications
1. [Actionable recommendation] — based on: [gap/trend/competitor weakness]
```

## Safety

- Do not fabricate market figures. If data is unavailable, state it explicitly.
- Do not copy-paste large blocks from paid analyst reports — paraphrase and cite.
- Do not name real individuals from customer interviews without consent consideration; anonymise personas.
- Competitor weaknesses must be sourced (public reviews, documented incidents, public filings) — not invented.

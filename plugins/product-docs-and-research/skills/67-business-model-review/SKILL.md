---
name: business-model-review
description: Use when you need to review business model, monetization, unit economics, pricing logic, and go-to-market risk.
---

# Business Model Review

## Purpose

Evaluate the internal consistency, financial viability, and scalability of a business model. Cover revenue streams, cost structure, unit economics (CAC/LTV), value proposition coherence, and go-to-market risk. Produce specific findings with quantitative checks where data exists and clearly flagged unknowns where it does not. A business model review is not a valuation — it is a structural stress test.

## When to use

- A founder or PM has drafted a business model canvas, pitch deck section, or financial model and wants a structured critique.
- A new revenue stream (subscription, marketplace, usage-based) is being added and needs stress-testing before committing to build.
- Unit economics are unclear or the LTV:CAC ratio has never been calculated.
- A pricing change is being planned and you need to check model-level impact before using `pricing-packaging-review`.
- Investors or leadership have asked for a business model sanity check before a funding round or board presentation.
- A model uses a hybrid revenue type and the interactions between streams have not been analysed.

## When not to use

- The request is specifically about pricing tier design — use `pricing-packaging-review`.
- The request is about competitive positioning without financial depth — use `market-research-synthesis`.
- No financial or operational data is available and no assumptions are provided — request an assumptions sheet first; this skill cannot produce useful output from nothing.
- The task is legal or tax analysis (revenue recognition standards, contract structure, transfer pricing) — out of scope.
- The task requires audited financial statements or GAAP/IFRS accounting advice — out of scope.

## Procedure

1. **Identify the revenue model type**: Subscription (MRR/ARR), transactional (per-unit), usage-based (metered), marketplace (take rate on GMV), advertising (CPM/CPC), licensing (per-seat or per-site), or hybrid. Confirm the model type is internally consistent with the stated customer segment, the sales motion, and the value proposition. A usage-based model sold through a 6-month enterprise procurement cycle is internally inconsistent.
2. **Value proposition coherence**: Does the stated value proposition justify the price point and differentiate from the next-best alternative? Check for alignment across value prop, target segment, delivery channel, and price. A mismatch at any corner of this triangle — for example, a "premium quality" positioning at a discount price — is a coherence failure.
3. **Revenue stream analysis**: List every revenue stream. For each: is it recurring or one-time? Predictable or volatile? High-margin or low-margin? Does it require a different GTM motion from the core revenue? Ancillary revenue streams that require disproportionate effort to capture are often net-negative when fully loaded cost is applied.
4. **Unit economics calculation**: Compute or explicitly request:
   - CAC = total sales and marketing spend ÷ new customers acquired in the same period (use a trailing 3-month or 6-month window to smooth seasonality)
   - LTV = ARPU × gross margin % ÷ monthly churn rate (do not omit gross margin; gross LTV without COGS applied overstates value by the cost of serving the customer)
   - LTV:CAC ratio — benchmark: ≥3x for SaaS; ≥2x for marketplace; ≥1.5x for transactional. Below 1x means acquiring customers destroys value.
   - Payback period = CAC ÷ (ARPU × gross margin %) — target: under 12 months for self-serve, under 18 months for enterprise
   If inputs are missing, document each unknown and state its directional impact on viability.
5. **Cost structure review**: Separate fixed from variable costs. Flag costs that scale faster than revenue: human-intensive fulfilment, per-transaction payment processing at high volume, customer support scaling linearly with user count, and per-seat infrastructure costs. Check for cost items with no owner or no budget allocation — these are typically underestimated.
6. **Scalability check**: Model what happens to gross margin and operating leverage at 10x current volume. Identify step-function costs — infrastructure tier changes, regulatory licensing thresholds, mandatory headcount additions, or minimum commit contracts that reset at scale.
7. **GTM risk**: Evaluate the go-to-market motion against the buyer persona and average contract value. Self-serve models are viable when ACV is below ~$5k/year; inside sales when ACV is $5k–$50k; enterprise field sales when ACV exceeds $50k. A mismatch between sales motion complexity and deal economics makes the model structurally unprofitable at any scale.
8. **Key assumptions and sensitivities**: List the top 5 assumptions the model depends on. For each, state the break-even threshold — how wrong can this assumption be before the model fails? For example: "churn must stay below 3.5%/month; at 5% churn, LTV:CAC falls below 1x."
9. **Competitive moat assessment**: Does the business model build compounding advantages over time? Name the specific mechanism: network effects (which interactions create value at what node density?), data flywheel (what data is collected, how does it improve the product, what volume is needed?), switching costs (what would it take for a customer to leave — data export effort, integration re-work, retraining?), or economies of scale (at what volume do unit costs meaningfully drop?). A moat description without a specific mechanism is a wish, not a structural advantage.
10. **Output**: Produce the structured report.

## Concrete checks

- [ ] Revenue model type clearly identified and internally consistent with segment, sales motion, and value prop
- [ ] Value proposition matches the target segment's actual decision criteria and price sensitivity
- [ ] All revenue streams listed; each assessed for margin, predictability, and GTM alignment
- [ ] CAC calculated with a defined time window; channel-level CAC broken out if multiple channels exist
- [ ] LTV calculated with gross margin and churn rate applied (not just ARPU × months)
- [ ] LTV:CAC ratio assessed against the category benchmark
- [ ] Payback period calculated; compared to benchmark for the sales motion type
- [ ] Fixed vs. variable costs clearly separated; variable costs include payment processing, support, and infrastructure per-user components
- [ ] Costs that scale super-linearly identified with the volume trigger
- [ ] Scalability at 10x modelled or discussed with identified margin inflection points
- [ ] GTM motion assessed against deal ACV for economic consistency
- [ ] Top 5 assumptions listed; each has a stated break-even threshold
- [ ] At least one moat mechanism named with a specific mechanism description (or absence flagged)
- [ ] Blended CAC broken into channel-level CAC where multiple acquisition channels exist

## Worked calculation reference

Use these formulas as a reference when inputs are available:

```
CAC = (Sales spend + Marketing spend) / New customers acquired
      → calculate for a trailing 3-month period to smooth seasonality

LTV = (ARPU × Gross margin %) / Monthly churn rate
      → Gross margin % must deduct: hosting/infra, payment processing, human support per customer
      → Monthly churn rate: use logo churn for B2B, dollar churn for usage-based

LTV:CAC ratio = LTV / CAC
      → SaaS benchmark: ≥3x
      → Marketplace benchmark: ≥2x

Payback period (months) = CAC / (ARPU × Gross margin %)
      → Self-serve target: <12 months
      → Enterprise target: <18 months

Gross margin % = (Revenue - COGS) / Revenue × 100
      COGS includes: cloud infrastructure, payment processing fees,
      professional services/implementation costs, per-user support burden

Break-even churn (given current LTV:CAC target):
      Max churn = (ARPU × Gross margin %) / (CAC × target LTV:CAC)
```

## Common issues & anti-patterns

- **LTV calculated without churn**: LTV = ARPU × 12 months is not LTV — it is 12 months of revenue. Real LTV applies a churn rate and gross margin. Ignoring churn overstates LTV by 2–10x depending on the retention curve.
- **Blended CAC hiding channel mix**: If paid search costs $200/customer and content marketing costs $600/customer but delivers 5x the retention, blending them hides a crucial strategic insight. Break CAC out by channel before drawing conclusions.
- **Gross margin confusion**: Including COGS inconsistently. Cloud infrastructure, human support cost, and payment processing fees (typically 2.5–3% of revenue) must all be deducted before computing LTV. Omitting them inflates the payback calculation.
- **TAM as revenue projection**: "The market is $10B so we will capture 1%" is not a revenue model — it is a wish attached to a large number. The model must show the mechanism: which customers, through which channel, at which price, with which retention rate.
- **No churn assumption**: Subscriptions modelled as if all customers stay forever. Even world-class SaaS products churn 1–2%/month. No churn assumption produces infinite LTV.
- **Variable costs treated as fixed**: Customer support that scales with user count modelled as a flat headcount number. At 10x users, a flat support team produces an 10x support queue — the cost either explodes or quality collapses.
- **Moat stated as intention**: "We'll build a network effect" with no specification of which interactions, what density triggers the flywheel, or how long it takes to reach that density. A moat that requires 3 years and $50M to become real is not a current competitive advantage.
- **GTM motion mismatch**: A $5/month self-serve product built with a 6-month enterprise sales cycle budget. Or a $100k ACV product launched as a no-touch self-serve product with no sales team. The economics of the sales motion must match the deal size.
- **Revenue stream cannibalisation**: Two revenue streams in the same model that serve the same segment (e.g., a usage-based tier and a seat-based tier targeting mid-market teams). Without explicit segmentation rules, customers choose whichever is cheaper and the model underperforms both scenarios.
- **Ignoring payment processing costs at scale**: At $1M ARR, 2.9% Stripe fees are $29k — significant but manageable. At $50M ARR they are $1.45M — a budget line that must be in the model.

## Required output

```
## Business Model Review: [Company / Product]

### Revenue model type
[Type] — consistent with segment/channel/price: [Yes / Partial / No — explain]

### Value proposition coherence
[Finding] — alignment gaps: [list each misalignment]

### Revenue streams
| Stream | Type | Margin estimate | Predictability | GTM alignment | Notes |
|--------|------|-----------------|----------------|---------------|-------|

### Unit economics
- CAC: [value] — window: [period] — channel breakdown: [if available]
- Gross margin %: [value] — COGS components included: [list]
- LTV: [value] — formula inputs: ARPU=[x], gross margin=[y]%, churn=[z]%/month
- LTV:CAC: [ratio] — benchmark for [category]: [benchmark] — verdict: [above / below / at benchmark]
- Payback period: [months] — target for [sales motion]: [target]
- Unknowns: [list each missing input and its directional impact]

### Cost structure
- Fixed: [list with approximate % of total cost]
- Variable: [list with scaling driver]
- Super-linear scaling risks: [list with volume trigger]

### Scalability at 10x
[Gross margin trajectory, step-function cost events, operating leverage inflection points]

### GTM risk
[Motion type vs. ACV assessment — consistent / mismatched — and implication]

### Key assumptions and sensitivities
| Assumption | Current value | Break-even threshold | Confidence | Impact if wrong |
|------------|--------------|----------------------|------------|-----------------|

### Defensibility / moat
[Mechanism — specific description of how it compounds — or: "No identified moat — [implication]"]

### Top recommendations
1. [Specific action] — priority: H/M/L — rationale: [why this changes viability]
```

## Safety

- Do not fabricate financial figures. When inputs are missing, state what is needed and its directional impact.
- Do not recommend specific investment decisions or valuations — this review informs but does not replace financial due diligence.
- If the model involves regulated financial products (lending, insurance, payments processing, securities), flag that regulatory capital requirements, licensing obligations, and compliance costs are outside the scope of this skill and must be reviewed separately.
- Do not present sensitivity estimates as forecasts. Label ranges as illustrative.

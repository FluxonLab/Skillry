---
name: business-model-review
description: Use when you need to review business model, monetization, unit economics, pricing logic, and go-to-market risk.
---

# Business Model Review

## Purpose

Evaluate the internal consistency, financial viability, and scalability of a business model. Cover revenue streams, cost structure, unit economics (CAC/LTV), value proposition coherence, and go-to-market risk. Produce specific findings with quantitative checks where data exists and clearly flagged unknowns where it does not.

## When to use

- A founder or PM has drafted a business model canvas, pitch deck section, or financial model and wants a structured critique.
- A new revenue stream (subscription, marketplace, usage-based) is being added and needs stress-testing.
- Unit economics are unclear or the LTV:CAC ratio has never been calculated.
- A pricing change is being planned and you need to check model-level impact before `pricing-packaging-review`.
- Investors or leadership have asked for a business model sanity check.

## When not to use

- The request is specifically about pricing tier design — use `pricing-packaging-review`.
- The request is about competitive positioning without financial depth — use `market-research-synthesis`.
- No financial or operational data is available and no assumptions are provided — request at least a assumptions sheet first.
- The task is legal or tax analysis (revenue recognition, contract structure) — out of scope.

## Procedure

1. **Identify the revenue model type**: Subscription (MRR/ARR), transactional, usage-based, marketplace, advertising, licensing, hybrid. Confirm the model type is consistent with the stated customer segment and value proposition.
2. **Value proposition coherence**: Does the stated value proposition justify the price and differentiate from alternatives? Check for value prop / segment / channel alignment.
3. **Revenue stream analysis**: List every revenue stream. For each: is it recurring or one-time? Predictable or volatile? High-margin or low-margin? Does it require the same GTM motion as core revenue?
4. **Unit economics calculation**: Compute or request:
 - CAC = total sales & marketing spend ÷ new customers acquired in period
 - LTV = ARPU × gross margin % ÷ churn rate
 - LTV:CAC ratio (target: ≥3x for SaaS; ≥2x for marketplaces)
 - Payback period = CAC ÷ (ARPU × gross margin %) — target: <12 months
 If inputs are missing, document each unknown and its impact.
5. **Cost structure review**: Identify fixed vs. variable costs. Flag costs that scale faster than revenue (e.g., human-intensive fulfilment, support scaling linearly with users). Check for cost items with no owner or budget.
6. **Scalability check**: What happens to margins at 10x current volume? Are there step-function costs (infrastructure tier changes, regulatory licenses, headcount)?
7. **GTM risk**: Evaluate the go-to-market motion against the buyer persona. Is the sales motion (self-serve, inside sales, enterprise) consistent with deal size and CAC budget?
8. **Key assumptions and sensitivities**: List the top 5 assumptions the model depends on. For each, state the break-even threshold — i.e., how wrong can this assumption be before the model fails?
9. **Competitive moat**: Does the business model build compounding advantages (network effects, data flywheel, switching costs, economies of scale)? Or is it easily replicated?
10. **Output**: Produce the structured report.

## Checklist

- [ ] Revenue model type clearly identified and internally consistent
- [ ] Value proposition matches segment, channel, and price point
- [ ] All revenue streams listed with margin and predictability rating
- [ ] CAC and LTV calculated (or unknowns documented)
- [ ] LTV:CAC ratio assessed against category benchmark
- [ ] Payback period calculated
- [ ] Cost structure separated into fixed / variable
- [ ] Costs that scale super-linearly flagged
- [ ] Scalability at 10x volume modelled or discussed
- [ ] GTM motion consistent with deal size
- [ ] Top 5 assumptions listed with break-even thresholds
- [ ] At least one moat or defensibility mechanism identified (or absence flagged)

## Common issues & anti-patterns

- **LTV calculated without churn**: LTV = ARPU × 12 months is not LTV; it ignores when customers leave.
- **Blended CAC hiding channel mix**: One channel may be 3x more expensive than another. Blended CAC masks this and produces misleading payback calculations.
- **Gross margin confusion**: Including COGS inconsistently. Cloud COGS, human support cost, and payment processing fees must all be in gross margin before computing LTV.
- **TAM as revenue projection**: "The market is $10B so we'll capture 1%" is not a revenue model; it is a wish.
- **No churn assumption**: Subscriptions modelled as if customers never leave.
- **Variable costs treated as fixed**: Customer support that scales with users modelled as a flat headcount number.
- **Moat = "we'll build a network effect" with no mechanism**: State specifically which interactions create the network value and at what density the effect kicks in.
- **GTM motion mismatch**: $5/month self-serve product with a 6-month enterprise sales cycle budget.

## Required output

```
## Business Model Review: [Company / Product]

### Revenue model type
[Type] — consistent with segment/channel: [Yes/Partial/No]

### Value proposition coherence
[Finding] — gaps: [list]

### Revenue streams
| Stream | Type | Margin estimate | Predictability | GTM alignment |

### Unit economics
- CAC: [value or "unknown — input needed: …"]
- LTV: [value or "unknown — input needed: …"]
- LTV:CAC: [ratio] — benchmark for [category]: [benchmark]
- Payback period: [months]

### Cost structure
- Fixed: [list]
- Variable: [list]
- Super-linear scaling risks: [list]

### Scalability at 10x
[Findings — cost inflection points, margin trajectory]

### GTM risk
[Finding — motion vs. deal size consistency]

### Key assumptions & sensitivities
| Assumption | Current value | Break-even threshold | Confidence |

### Defensibility / moat
[Finding — mechanism or absence]

### Top recommendations
1. [Specific action] — priority: H/M/L
```

## Safety

- Do not fabricate financial figures. When inputs are missing, state what is needed.
- Do not recommend specific investment decisions or valuations — flag that this review informs but does not replace financial due diligence.
- If the model involves regulated financial products (lending, insurance, payments), flag that regulatory capital and compliance requirements are outside scope.

---
name: pricing-packaging-review
description: Use when you need to review pricing tiers, packaging, feature gates, trials, and conversion paths.
---

# Pricing Packaging Review

## Purpose

Evaluate the design of a pricing page, tier structure, feature gate matrix, or trial experience for conversion logic, value metric alignment, upgrade incentive clarity, and competitive positioning. Identify where the packaging creates friction, leaks revenue, or misaligns with customer segments. This skill is strategic — it produces recommendations, not pricing-system code or payment-flow implementations.

## When to use

- A pricing page or tier structure is being designed or redesigned.
- Conversion from free or trial to paid is below benchmark and you need a packaging diagnosis.
- A new feature needs to be placed into a tier and the criteria are unclear.
- Enterprise, mid-market, and self-serve tiers are colliding (sales conflicts, cannibalization, or support confusion).
- A freemium model is being introduced or its gate logic is being rethought.
- Pricing anchoring, decoy tier placement, or annual vs. monthly discount strategy is being evaluated.
- An expansion revenue motion (upsell, cross-sell, add-ons) needs to be reviewed for coherence with the base tier structure.

## When not to use

- The underlying business model (revenue type, unit economics) has not been validated — use `business-model-review` first to confirm the model is viable before optimising its packaging.
- The request is about market research to determine willingness-to-pay — use `market-research-synthesis` to gather that input first.
- The task is a technical implementation of payment flows, subscription billing, or metering — this skill is strategic, not engineering.
- A single add-on price needs to be set without any tier context to anchor against.

## Procedure

1. **Identify the value metric**: What is the primary unit customers pay for — users/seats, API calls, records, storage, events, or revenue percentage? The value metric must scale with customer value: as the customer gets more out of the product, their cost should rise proportionally. A metric that does not scale (flat seat price for a solo-user workflow tool) causes misalignment between value delivered and price paid.
2. **Audit tier structure**: List every tier with its price, included limits, and target segment. Check for: tier count (more than 4 tiers creates decision paralysis for most B2B buyers), pricing gaps between adjacent tiers (a jump of more than 5x with no intermediate option is a conversion leak), and segment-tier alignment (the features in a tier must match the actual needs of the stated target segment, not just be the features available at that price).
3. **Feature gate audit**: For each gated feature ask two questions. First: does this feature belong in this tier because it creates value specifically for that segment, or because it was convenient to put it somewhere? Second: does this gate block trial activation — can a new user experience the core value of the product without hitting a paywalled feature? Features that gate core value before the user has experienced it reduce activation rates and inflate churn.
4. **Freemium or trial gate logic**: Identify the exact moment users hit the paywall. A well-placed paywall feels like a natural upgrade at the moment of peak engagement — the user wants to do more of the thing that is already working. A poorly placed paywall appears before the user has had the "aha" moment. Document the gate: what action triggers it, what the user sees, and what the next step is. Map whether core value is accessible before that gate.
5. **Price anchoring and decoy tier**: Check for a high-priced anchor tier that makes the mid-tier feel reasonable by comparison. Check for a decoy tier positioned to direct buyers toward the recommended tier. Anchoring and decoy effects are well-documented conversion levers — their absence is a missed opportunity, not a neutral choice. If the recommended tier is not visually highlighted ("Most popular", "Best value"), the anchor effect is further weakened.
6. **Upgrade triggers and CTAs**: What in-product signals push users toward an upgrade? Triggers must appear at the right moments: limit approaching (80% of quota used), team feature attempted by a solo user, high-value action completed that is downstream of an upgrade feature, or usage spike that predicts limit-hitting. Conversion campaigns that depend entirely on email outreach miss users who do not open email.
7. **Competitive price positioning**: Where does each tier land versus category competitors on an equivalent-value basis? Are you at parity, at a premium, or at a discount relative to your positioning strategy? A "best-in-class quality" positioning at a 30% discount signals either underconfidence or margin pressure — both of which undermine the brand.
8. **Revenue leakage check**: Identify segments that can accomplish their full use case on the free or lowest tier without upgrading. This is silent leakage: the customer extracts real value and pays nothing or minimal amounts indefinitely. Leakage typically occurs when a power feature was placed in the free tier for activation purposes and was never gated at scale usage.
9. **Enterprise readiness**: Does the enterprise tier include the features that enterprise procurement requires? The standard checklist: SSO/SAML, audit logs (with export), admin controls and user management, SLA with defined uptime commitment, dedicated support or named CSM, data residency or DPA availability, and volume pricing. Missing any of these blocks enterprise procurement independent of product quality.
10. **Trial conversion path**: Map the trial-to-paid journey step by step: day 1 activation prompt, limit-approaching notification, paywall moment, payment friction (card required vs. not, number of form fields, redirect to billing portal vs. in-app), and post-conversion confirmation. Flag each step that introduces drop-off risk.

## Concrete checks

- [ ] Value metric identified; scales with customer value delivered; not flat where usage varies significantly
- [ ] Tier count is 4 or fewer, or there is a documented reason for more
- [ ] No conversion-blocking gap between adjacent tiers (no more than 5x price jump without a mid-option)
- [ ] Core value experience is accessible before the paywall in the free or trial tier
- [ ] Feature gates justify segment alignment — features are placed for segment fit, not convenience
- [ ] An anchor tier exists at a price that makes the mid-tier feel reasonable
- [ ] A recommended or "most popular" tier is visually distinguished
- [ ] In-product upgrade triggers exist at peak-engagement moments, not only in email campaigns
- [ ] Competitive price position is defined (premium / parity / discount) and consistent with the product positioning
- [ ] No full-use-case leakage is possible on the free or lowest paid tier at scale usage
- [ ] Enterprise tier includes SSO, audit logs, admin controls, SLA, and dedicated support
- [ ] Trial-to-paid conversion path is mapped step by step with friction points identified
- [ ] Annual discount depth is under 25–30% (deeper discounts suppress monthly revenue without proportional retention benefit)
- [ ] Expansion revenue path (upsell, add-ons) is coherent with base tier structure and does not require a separate sales motion

## Worked diagnostic examples

These examples illustrate how to apply the checks above to common packaging problems:

**Leakage example**: A project management tool offers unlimited projects on the free tier. Power users manage 15+ projects for free indefinitely. The value metric (seat count) does not correlate with the volume of value extracted. Fix: introduce a project limit on free (e.g., 3 active projects) or switch the value metric to active projects.

**Gap example**: Tiers are priced at $12/month and $99/month with nothing in between. A customer who outgrows free but cannot justify $99 for their use case churns instead of converting. Fix: introduce a $39/month mid-tier with a limited but meaningful feature set.

**Gate timing example**: A collaboration tool places the "share with a teammate" feature behind a paid tier. The sharing action is the trigger that would expose the product to new users and demonstrate its collaborative value. Gating it before the user experiences collaboration kills viral growth and reduces activation. Fix: allow limited free sharing (e.g., 3 collaborators) before the paywall.

**Enterprise blocking example**: A $50k ACV deal stalls because the enterprise IT team requires SSO authentication and the product only supports email/password login on all tiers. No amount of feature quality closes this deal without SSO. Fix: add SSO to the enterprise tier as a non-negotiable procurement prerequisite.

## Common issues & anti-patterns

- **Seat-based pricing for a solo-power-user tool**: Forces team adoption before the product is proven internally. The first friction point is "add another seat" when the user just wants to use the tool themselves. Consider usage-based or project-based metrics for tools with strong solo adoption patterns.
- **Free tier with too much**: Users accomplish their entire use case for free indefinitely. The free tier becomes a permanent customer segment that costs support resources without generating revenue. Remove or limit the highest-value feature at scale usage.
- **Free tier with too little**: Users cannot experience core value before hitting the paywall. The product feels like it is withholding until payment. Net result: low activation, low virality, high trial-churn. The paywall must be at the point of expansion, not at the point of first value.
- **Three tiers at similar price points**: "Starter $29 / Pro $49 / Business $79" with overlapping features produces no anchoring effect and no clear upgrade story. The price spread is too narrow to create a strong "obviously the right choice" tier. Spread to at least 3x between adjacent tiers.
- **Feature gate that feels like punishment**: The user experienced a feature during trial, it was removed at the end of trial, and now they are asked to pay to get it back. This creates negative emotion at the conversion moment. Replace with limits (e.g., 5 exports/month on free, unlimited on paid) rather than removal.
- **Enterprise tier equals Pro plus higher limits**: Enterprise buyers purchase compliance, control, and operational trust — not capacity. An enterprise tier without SSO, audit logs, and admin controls is not an enterprise tier regardless of what it is named.
- **Annual discount too deep**: A 50% annual discount trains users to never pay monthly, signals that the monthly price is inflated, and creates a 12-month commitment that some buyers resist. A 20–25% annual discount is typically the incentive necessary without these side effects.
- **No in-product upsell path**: Conversion depends entirely on email campaigns and human outreach. Users who do not open email or who avoid sales calls never see the upgrade path, regardless of their willingness to pay.
- **Add-on sprawl**: Offering 8 separate add-ons that can be mixed and matched creates decision paralysis and an opaque effective price. Buyers cannot compare your price to competitors. Bundle logically related add-ons into clear tiers.
- **Inconsistent feature logic**: Feature A is in the mid-tier, Feature B requires the enterprise tier, but Feature B is only useful if you have Feature A. The customer must buy enterprise to use two features that were placed independently without reviewing the dependency.

## Required output

```
## Pricing Packaging Review: [Product / Pricing page]

### Value metric
Current metric: [name] — assessment: [Scales with value / Does not scale / Mixed — explain]
Recommended alternative (if applicable): [metric + rationale]

### Tier structure
| Tier | Price | Limits | Target segment | Segment fit | Issues |
|------|-------|--------|---------------|-------------|--------|

### Feature gate findings
| Feature | Current tier | Assessment | Recommendation |
|---------|-------------|------------|----------------|

### Freemium / trial gate logic
- Paywall trigger: [exact action or limit that triggers the gate]
- Core value accessible before paywall: [Yes / No — explain]
- Gate timing assessment: [peak engagement / premature / post-value]
- Recommendation: [specific change]

### Price anchoring and decoy
- Anchor tier: [present / absent] — [finding and impact]
- Recommended tier highlighted: [Yes / No] — [finding]
- Decoy tier: [present / absent] — [finding]

### Upgrade triggers and CTAs
- In-product triggers: [list — moment, trigger event, CTA text if known]
- Missing trigger moments: [list with recommended addition]

### Revenue leakage
- Leakage segments: [describe use case and how they avoid upgrading]
- Volume of leakage: [estimated if data provided]
- Recommended fix: [specific packaging change]

### Competitive positioning
| Tier | Your price | Competitor A price | Competitor B price | Your position | Consistent with strategy |
|------|-----------|-------------------|-------------------|--------------|--------------------------|

### Enterprise readiness
- SSO/SAML: [present / absent]
- Audit logs with export: [present / absent]
- Admin and user management: [present / absent]
- SLA with defined uptime: [present / absent]
- Dedicated support or CSM: [present / absent]
- DPA / data residency: [present / absent]
- Blockers to enterprise procurement: [list]

### Trial conversion path
| Step | What happens | Friction risk | Recommendation |
|------|-------------|---------------|----------------|
| Day 1 | [describe] | [H/M/L] | [action] |
| Limit approaching | [describe] | [H/M/L] | [action] |
| Paywall | [describe] | [H/M/L] | [action] |
| Payment | [describe] | [H/M/L] | [action] |

### Top recommendations
1. [Specific action] — expected impact: [conversion / ARPU / enterprise-deal-velocity] — priority: H/M/L
```

## Safety

- Do not recommend specific price points without willingness-to-pay data; frame price suggestions as hypotheses to test, not conclusions.
- Do not remove tier features or restructure pricing in code, CMS, or billing system — this skill produces recommendations for human review and approval, not direct changes.
- Flag any pricing restructuring that may affect existing customers under legacy contracts or promotional commitments — recommend a grandfather clause review before implementation.
- Do not simulate conversion lift numbers without data; label projected improvements as directional estimates.

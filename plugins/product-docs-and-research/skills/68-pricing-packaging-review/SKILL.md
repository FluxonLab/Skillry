---
name: pricing-packaging-review
description: Use when you need to review pricing tiers, packaging, feature gates, trials, and conversion paths.
---

# Pricing Packaging Review

## Purpose

Evaluate the design of a pricing page, tier structure, feature gate matrix, or trial experience for conversion logic, value metric alignment, upgrade incentive clarity, and competitive positioning. Identify where the packaging creates friction, leaks revenue, or misaligns with customer segments.

## When to use

- A pricing page or tier structure is being designed or redesigned.
- Conversion from free/trial to paid is below benchmark and you need a packaging diagnosis.
- A new feature needs to be placed into a tier and the criteria are unclear.
- Enterprise, mid-market, and self-serve tiers are colliding (sales conflicts, cannibalization).
- A freemium model is being introduced or its gate logic is being rethought.
- Pricing anchoring or decoy tier placement is being evaluated.

## When not to use

- The underlying business model (revenue type, unit economics) has not been validated — use `business-model-review` first.
- The request is about market research to determine willingness-to-pay — use `market-research-synthesis`.
- The task is a technical implementation of payment flows — this skill is strategic, not engineering.
- A single feature price (add-on, one-time purchase) needs to be set without tier context.

## Procedure

1. **Identify the value metric**: What is the primary unit customers pay for? Users, seats, API calls, records, storage, events? The value metric must scale with customer value — price should go up as the customer gets more out of the product.
2. **Audit tier structure**: List every tier with its price, included limits, and target segment. Check for: tier count (>4 creates decision paralysis), pricing gaps between tiers (>5x jump with no mid-tier is a conversion leak), and segment-tier alignment.
3. **Feature gate audit**: For each gated feature ask: does this feature belong in the tier because it creates value for that segment, or because it exists and had to go somewhere? Flag gates that block trial activation (features needed to experience core value must not be gated in free/trial).
4. **Freemium / trial gate logic**: Identify the moment users hit the paywall. Is it at the point of peak engagement (good) or before core value is experienced (bad)? The paywall should feel like a natural upgrade, not a wall.
5. **Price anchoring and decoy**: Is there a high-priced anchor tier to make mid-tier feel reasonable? Is there a decoy tier that makes the recommended tier appear like the obvious choice? If absent, note the missed conversion lever.
6. **Upgrade triggers and CTAs**: What in-product signals push users toward upgrade? Are they present at the right moments (limit reached, team feature accessed, high-value action completed)?
7. **Competitive price positioning**: Where does each tier land versus category competitors? Are you priced at parity, premium, or discount — and does that match your positioning strategy?
8. **Revenue leakage check**: Identify segments that can accomplish their full use case on the free/lowest tier without upgrading. This is silent leakage.
9. **Enterprise readiness**: Does the enterprise tier include expected buying-committee features (SSO, audit logs, admin controls, SLA, dedicated support)? Missing any of these blocks enterprise procurement.
10. **Trial conversion path**: Map the trial-to-paid journey: day 1 prompt, limit approaching notification, paywall moment, payment friction. Flag each drop-off risk.

## Checklist

- [ ] Value metric identified and scales with customer value
- [ ] Tier count ≤4 (or justified reason for more)
- [ ] No conversion-blocking gap between tiers
- [ ] Core value experience not gated in free/trial
- [ ] Feature gates justify segment alignment, not just placement convenience
- [ ] Price anchor tier present
- [ ] Decoy / recommended tier clearly highlighted
- [ ] In-product upgrade triggers exist at peak-engagement moments
- [ ] Competitive price position defined (premium / parity / discount) and consistent with positioning
- [ ] No full-use-case leakage on free tier
- [ ] Enterprise tier has SSO, audit logs, admin, SLA
- [ ] Trial-to-paid conversion path mapped with friction points flagged

## Common issues & anti-patterns

- **Seat-based pricing for a tool with solo power users**: Forces team adoption before the product is proven internally. Consider usage-based or project-based metric instead.
- **Free tier with too much**: Users accomplish their entire use case for free indefinitely. Remove or limit the feature that delivers the most value at scale.
- **Free tier with too little**: Users cannot experience core value before hitting the paywall. Net: low activation, high churn post-trial.
- **3 tiers all at similar price points**: Anchor effect is lost. Spread tiers to create clear segmentation (e.g., $29 / $99 / $299, not $29 / $49 / $79).
- **Feature gate = punishment**: Gating a feature the user has already used in trial on upgrade feels punitive. Introduce limits rather than removal.
- **No enterprise differentiation**: Enterprise tier = Pro + higher limit. Enterprises buy compliance, control, and support — not just capacity.
- **Annual discount too deep**: Offering 40%+ annual discount trains users to never pay monthly; it also signals that monthly price is inflated.
- **No in-product upsell**: Conversion depends entirely on email campaigns. Users who don't open email never see the upgrade path.

## Required output

```
## Pricing Packaging Review: [Product / Pricing page]

### Value metric
[Current metric] — assessment: [Scales with value / Does not scale / Mixed]
Recommended alternative (if applicable): …

### Tier structure
| Tier | Price | Limits | Target segment | Issues |

### Feature gate findings
| Feature | Current tier | Assessment | Recommendation |

### Freemium / trial gate logic
- Paywall moment: [describe]
- Core value accessible before paywall: [Yes/No]
- Recommendation: …

### Price anchoring & decoy
- Anchor tier: [present/absent] — [finding]
- Decoy/recommended: [present/absent] — [finding]

### Revenue leakage
- Leakage segments: [describe]
- Recommended fix: …

### Competitive positioning
| Tier | Your price | Competitor A | Competitor B | Position |

### Enterprise readiness
- SSO: [present/absent] Audit logs: [present/absent]
- Admin controls: [present/absent] SLA: [present/absent]
- Blockers: [list]

### Trial conversion path
[Step-by-step with friction flags]

### Top recommendations
1. [Action] — expected impact: [conversion / ARPU / churn]
```

## Safety

- Do not recommend specific price points without willingness-to-pay data; frame as hypotheses.
- Do not remove tier features or restructure pricing unilaterally in code or CMS — this skill produces recommendations, not deployments.
- Flag any pricing change that may affect existing customers under legacy contracts — recommend a grandfather clause review.

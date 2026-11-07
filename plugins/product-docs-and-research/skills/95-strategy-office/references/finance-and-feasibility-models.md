# Finance, Unit Economics and Feasibility Models

This reference provides mathematical formulations for unit economics, pricing sensitivity, break-even analysis, and the eight-dimension feasibility scoring rubric.

All financial models produced under this framework are internal unit-economics projections and project-accounting models. They do not constitute certified legal, financial, tax, or investment advice. Always re-verify third-party vendor prices, payment processor fee schedules, app store commissions, and statutory tax regulations against primary official sources before finalizing public pricing or committing capital.

---

## 1. Accounting definitions and baseline setup

### 1.1 Fixed versus variable costs

- **Fixed monthly costs ($F$):** Expenses incurred regardless of user volume or utilization:
  - Base infrastructure (e.g. baseline cloud servers, managed databases, static hosting, core domain renewals).
  - Software subscriptions (e.g. developer accounts, fixed monitoring plan baselines).
- **Variable per-unit provider costs ($C_{\text{prov}}$):** Usage-driven expenses that scale with active users and consumed actions:
  - LLM token processing (input, output, and context cache fees).
  - Cloud GPU/compute runtime (measured hourly compute rates or batch processing costs).
  - Storage volume and data egress bandwidth.
  - Transactional email and notification volume.
  - Payment gateway transaction fees and app store commissions.

### 1.2 Payment channels and tax handling

Model payment channels explicitly to calculate realistic net revenue:

1. **Direct payment processing (e.g. Stripe Direct):**
   - The operating business acts as the seller of record.
   - Percentage transaction fees plus per-transaction fixed fees are deducted.
   - The business manages local sales tax and regional VAT compliance (e.g. monitoring EU One-Stop Shop (OSS) thresholds for cross-border digital goods).
2. **Merchant of Record (MoR) platforms (e.g. Stripe Managed Payments, Lemon Squeezy, Paddle):**
   - The platform acts as the legal seller of record, remitting indirect taxes (VAT, GST, sales tax) globally.
   - MoR transaction fees (typically higher percentage fees) must be deducted from gross price.
3. **Mobile app store in-app purchases (Apple App Store / Google Play):**
   - Standard app store commission (typically 30%, or 15% under qualified small business programs).
   - In-app purchase fees and regional store tax withholdings must be factored into mobile tier yields.

---

## 2. Unit economics formulas and sensitivity math

### 2.1 Per-user net revenue ($R_{\text{net}}$)

For pricing tier $t$ and payment channel $c$:

$$R_{\text{net}}(t, c) = \left(P_{\text{gross}}(t) - \text{Tax}_{\text{included}}(t, c)\right) \times \left(1 - r_{\text{fee}}(c)\right) - f_{\text{fixed\_tx}}(c)$$

Where:
- $P_{\text{gross}}(t)$ is the listed retail tier price.
- $\text{Tax}_{\text{included}}(t, c)$ is the statutory tax amount included in the retail price (e.g. VAT or sales tax, depending on jurisdiction and merchant setup).
- $r_{\text{fee}}(c)$ is the variable processing fee percentage for channel $c$.
- $f_{\text{fixed\_tx}}(c)$ is the fixed per-transaction fee for channel $c$.

### 2.2 Variable provider cost ($C_{\text{prov}}$) and the 30% rule

For a user on tier $t$ operating at utilization multiplier $u \in \{0.5, 1.0, 1.5\}$ (representing 50% light, 100% expected, and 150% heavy quota utilization):

$$C_{\text{prov}}(t, u) = u \times \sum_{k} \left( q_{k}(t) \times c_{k} \right)$$

Where $q_{k}(t)$ is the expected monthly volume of resource $k$ (tokens, compute seconds, storage gigabytes, emails) and $c_{k}$ is the verified unit rate.

- **Provider cost share target:**
  $$\text{Provider Cost Share}(t) = \frac{C_{\text{prov}}(t, 1.0)}{P_{\text{gross}}(t)}$$
  **Gate benchmark:** $\text{Provider Cost Share}(t) \le 0.30$ (30% or less of gross price, yielding a gross margin of >= 70% before payment transaction fees).

### 2.3 Sensitivity analysis at 50%, 100%, and 150% usage

Compute net unit contribution margin $M(t, u) = R_{\text{net}}(t, c) - C_{\text{prov}}(t, u)$ across usage profiles:
- **50% utilization ($u = 0.5$):** Low-usage or inactive subscribers (high unit margin).
- **100% utilization ($u = 1.0$):** Average expected user workload (must achieve <= 30% provider cost share).
- **150% utilization ($u = 1.5$):** Heavy or power users.

**Safety condition:**
$$M(t, 1.5) = R_{\text{net}}(t, c) - C_{\text{prov}}(t, 1.5) > 0$$

If 150% utilization results in negative contribution margin ($M(t, 1.5) \le 0$), you must implement quota caps, shift heavy tasks to cost-effective compute/models, or increase tier pricing before passing the pricing gate.

### 2.4 Break-even paying users and cohort math

Let:
- $F$ = Total fixed monthly operating costs.
- $N_{\text{free}}$ = Active free-tier users per month.
- $C_{\text{free\_unit}}$ = Monthly variable provider cost per active free-tier user.
- $C_{\text{free\_pool}} = N_{\text{free}} \times C_{\text{free\_unit}}$ = Total monthly cost of supporting free-tier volume.
- $\overline{M}_{\text{paid}} = \sum_{t} w_t \left( R_{\text{net}}(t) - C_{\text{prov}}(t, 1.0) \right)$ = Weighted average monthly net contribution margin per paying customer across tier distribution $w_t$ ($\sum w_t = 1$).

The required number of paying customers to achieve monthly break-even is:

$$N_{\text{BE}} = \left\lceil \frac{F + C_{\text{free\_pool}}}{\overline{M}_{\text{paid}}} \right\rceil$$

If free-tier users scale proportionally with paying users at conversion rate $\alpha$ (such that $N_{\text{free}} = N_{\text{paid}} \times \frac{1 - \alpha}{\alpha}$):

$$N_{\text{BE, cohort}} = \left\lceil \frac{F}{\overline{M}_{\text{paid}} - \left(\frac{1 - \alpha}{\alpha}\right) C_{\text{free\_unit}}} \right\rceil$$

**Stop condition:** If $\overline{M}_{\text{paid}} \le \left(\frac{1 - \alpha}{\alpha}\right) C_{\text{free\_unit}}$, free-tier costs exceed paid contribution at all user volumes. In this case, reduce free-tier allowances, introduce stricter activity limits, or require payment verification before public launch.

---

## 3. Eight-dimension feasibility scoring rubric

Score each dimension on a 1–5 scale based on verifiable evidence:

| Dimension | Score 1 (Critical Blocker) | Score 3 (Conditional / Requires Mitigation) | Score 5 (Verified Strong Advantage) |
| --- | --- | --- | --- |
| **1. Problem severity & frequency** | No verified user pain; speculative solution in search of a problem. | User pain confirmed in reviews or discussions, but target audience is narrow. | Frequent, acute, high-value problem verified across multiple primary sources. |
| **2. Market & distribution wedge** | Saturated market with no distinct channel access or defensible differentiation. | Clear feature wedge; organic channels (SEO/ASO/social) are competitive but accessible. | Underserved audience, niche storefront, or workflow gap with verified organic demand. |
| **3. Technical & architecture fit** | Depends on unavailable hardware, unverified APIs, or unproven models. | Requires a bounded proof-of-concept to validate latency, accuracy, or throughput. | Clean fit with existing infrastructure, proven frameworks, and standard deployments. |
| **4. Resource & team capacity** | Requires specialized manual effort exceeding available operational capacity. | Requires targeted workflow automation or modular division of labor. | High automation potential; cleanly partitioned into modular milestones. |
| **5. Time to testable slice** | Multiple months of development required before any end-to-end flow can be tested. | Testable vertical slice achievable in 1–2 weeks following initial setup. | Functional, testable vertical slice achievable within days. |
| **6. Unit economics & capital exposure** | Provider costs exceed 50% of gross price, or negative contribution margin under power use. | Provider cost is 30–40%; reaches <= 30% target through caching or model tiering. | Provider cost <= 30% at expected usage; positive margin at 150% usage; low break-even count. |
| **7. Legal, license & tax compliance** | Relies on non-commercial licenses (`CC BY-NC`), restrictive APIs, or unclear terms. | Contains dual-licensed or copyleft components requiring careful isolation (e.g. AGPL). | All dependencies use permissive licenses (MIT, Apache-2.0); data residency and taxes clean. |
| **8. Platform & store policy risk** | High risk of rejection under App Store, Google Play, or platform API policies. | Requires careful compliance design for paywalls, permissions, or AI disclosure. | Standard application pattern with low compliance risk and transparent user terms. |

### Gate evaluation rules (`G0` Feasibility)

- **Pass (`GO`):** Average score across all eight dimensions is >= 3.5; no dimension scores 1; all high-stakes assumptions have verified evidence (`Grade A` or `B`).
- **Conditional (`CONDITIONAL GO`):** No dimension scores 1 on legal or platform policy; any dimension scoring 2 has a documented mitigation plan, time-boxed proof-of-concept, or formal stakeholder waiver.
- **Fail (`NO-GO`):** Any legal, platform policy, or financial viability dimension scores 1 without an immediate lawful and profitable remedy, or explicit project kill criteria are triggered. Halt further development and report findings to stakeholders.

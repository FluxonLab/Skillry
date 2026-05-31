---
name: ai-studio-prototype-review
description: Use when you need to review AI studio prototypes, prompt tooling, agent playgrounds, and rapid product experiments.
---

# AI Studio Prototype Review

## Purpose

Review AI studio prototypes — built in Google AI Studio, OpenAI Playground, Anthropic Console, Claude.ai Projects, Vertex AI Studio, Amazon Bedrock console, or similar environments — for reproducibility gaps, API key exposure, rate limit risks, prompt completeness, data handling issues, and the delta between prototype behavior and what a production implementation would actually require. Prevents the failure mode of shipping a prototype that works in the studio but breaks in production, or that was built using data that should never have been used.

## When to use

- A prototype built in an AI studio is being evaluated before a decision to productionize it.
- Prototype demo results cannot be consistently reproduced and you need to identify why.
- API credentials used in the prototype need review for scope and rotation risk before the prototype is shared externally.
- A stakeholder wants a concrete estimate of what it would take to move from prototype to production.
- Rate limits or token costs are becoming a concern during prototype testing at scale.
- The prototype is being used in a presentation or shared with non-engineers who may inadvertently trigger rate limits or expose credentials.

## When not to use

- The system is already in production — use `prompt-systems-review` or `ai-security-review` for production reviews.
- The prototype is a local Python script or Jupyter notebook, not built in an AI studio environment.
- The question is about model evaluation methodology rather than prototype configuration (use `llm-evaluation-review`).
- The prototype is purely exploratory research with no path to productionization and no real data involved.

## Procedure

1. **Document the prototype configuration.** Record everything needed to reproduce the prototype exactly:
 - Platform: which AI studio (Google AI Studio / OpenAI Playground / Anthropic Console / other)
 - Model: exact name and version (`gpt-4o-2024-08-06`, `claude-3-5-sonnet-20241022` — not just "GPT-4o" or "Claude")
 - System prompt: full text (or indicate if it is the platform default)
 - Temperature, top-p, max output tokens
 - Tool or function definitions enabled, if any
 - Any example conversations saved and used to influence responses
 This configuration is the baseline for the review. If it cannot be reproduced from these parameters, the prototype is not ready for any downstream decision.

2. **Audit API key scope and exposure.** Identify which API key is in use. Verify:
 - The key is scoped to minimum required permissions (read-only generation if the prototype only calls completion endpoints)
 - The key is not visible in any shared URL parameters, browser history, presentation screenshots, or recorded demo videos
 - The key has a usage limit set: a monthly token budget or request count cap that would prevent unexpected overage charges
 - The key has an expiry date or rotation schedule
 - If the key is in a shared notebook or tool used by multiple people, it must be rotated after the review because it is effectively compromised
 Flag any key without a usage limit: an infinite-limit key used in a prototype that goes viral can generate thousands of dollars in charges within hours.

3. **Test reproducibility.** Select 5-10 representative prompts that were used in the demo. Run each at least 3 times with the same configuration. Record:
 - Is the output schema consistent across runs (same fields, same structure)?
 - Are key facts and numbers consistent (or does the model produce different values on different runs)?
 - Is response length within a predictable range?
 - At temperature > 0.5, expect variability — document which aspects vary and confirm the variation is acceptable for the use case
 A prototype that relied on a specific lucky output from a high-temperature run is not a reproducible prototype and is not ready for productionization evaluation.

4. **Identify model-specific behaviors.** Note any behavior in the prototype that depends on the specific model version. Confirm:
 - Is this exact model version available via the production API, or only in the studio UI?
 - Is this model in general availability, or preview/experimental (preview models are removed without notice)?
 - What is the model's deprecation policy and timeline?
 AI studio UIs frequently expose preview and experimental models before they are available on stable production endpoints. A prototype built on `gemini-2.0-flash-thinking-exp` will break when that model is retired. If the prototype uses a preview model, the productionization plan must account for model substitution and include a re-validation step.

5. **Review the system prompt for production readiness.** Apply these checks to the system prompt:
 - Is it versioned? (A prompt in an AI studio UI with no version history cannot be rolled back)
 - Does it specify an output schema or format?
 - Are there instruction conflicts? (Test with edge-case inputs that could trigger conflicting instructions)
 - Does it rely on the AI studio's default context additions — like today's date, user name, or session metadata — that will not be present when the API is called directly?
 - Does it have a linked eval dataset that validates it produces the correct output format?
 AI studio platforms often add implicit context that is not present when the same prompt is called via the raw API. What works in the studio may produce different output when called from code.

6. **Assess rate limit exposure.** Calculate the expected token consumption for the intended test or demo load:
 `total_tokens_per_run = (average_prompt_tokens + average_output_tokens) × number_of_concurrent_users × requests_per_user_per_minute`

 Compare against the API key's rate limit tiers:
 - Requests per minute (RPM)
 - Tokens per minute (TPM)
 - Tokens per day (TPD)
 If a stakeholder demo involves multiple people using the prototype simultaneously, calculate the token consumption for that scenario. Document what the user experience will be when the rate limit is hit (error message, blank response, retry behavior).

7. **Identify productionization gaps.** For each capability demonstrated in the prototype, document what is needed in a production implementation that the prototype does not have:

 | Capability | Prototype approach | Production requirement | Effort |
 |---|---|---|---|
 | Error handling | None — errors show as blank | Retry with backoff, user-friendly error message | Medium |
 | Input validation | Accepts any input | Schema validation, length limits, content filtering | Medium |
 | Output parsing | Human reads the output | Structured JSON parser with schema validation | Small |
 | Latency | Single query, acceptable wait | Streaming responses or async queuing for concurrent users | Large |
 | Cost | Pay per query, no tracking | Budget caps, per-user quotas, cost dashboards | Medium |
 | Authentication | Shared API key | Per-user authentication, credential isolation | Large |

8. **Check for data handling issues.** Confirm whether any real user data, PII, confidential business information, or regulated data was input into the AI studio during prototyping. AI studios retain conversation history for varying periods and may use it for model improvement depending on the platform's data agreement:
 - Google AI Studio: data used for Google model improvement by default (opt-out available)
 - OpenAI Playground: data may be used for model improvement without an enterprise data agreement
 - Anthropic Console: check current data handling terms for the active tier
 - Vertex AI Studio / Amazon Bedrock: enterprise agreements generally provide stronger data protection
 If real sensitive data was used, document what data, when, which platform, and what the platform's retention and use policy is for that tier.

9. **Produce a go/no-go recommendation.** Based on the review findings:
 - **PROTOTYPE READY**: configuration is reproducible, model version is production-available, no data handling violations, system prompt is production-ready, productionization gaps are documented with effort estimates
 - **PROTOTYPE CONDITIONAL**: specific issues must be resolved (listed) before any productionization investment
 - **PROTOTYPE INVALID**: fundamental design or data problem — rebuild before investing in productionization

## Checklist

- [ ] Prototype configuration fully documented: platform, exact model name/version, full system prompt, all parameters
- [ ] Configuration can be reproduced by a different person from the documented parameters
- [ ] API key scoped to minimum required permissions
- [ ] API key not visible in any shared URL, screenshot, recording, or presentation material
- [ ] API key has a usage limit (monthly token budget or request count cap)
- [ ] Reproducibility tested: 5-10 prompts run 3 times each; schema and key fact consistency documented
- [ ] Model version confirmed as production API-available (not preview/experimental only)
- [ ] Model deprecation policy and timeline confirmed
- [ ] System prompt versioned; does not rely on platform-added implicit context
- [ ] Rate limit exposure calculated for demo and intended test load
- [ ] Rate limit hit behavior documented (what the user will see)
- [ ] Productionization gaps documented with effort estimates for each capability
- [ ] Data handling review: confirmed whether real PII or sensitive data was used in the studio
- [ ] Platform data retention and usage policy confirmed for the tier in use
- [ ] Go/no-go recommendation with justification produced

## Common issues & anti-patterns

**Demo model not available on production API.** The prototype uses `gemini-2.0-flash-thinking-exp` or `gpt-4-vision-preview`. The team plans to ship using that model. Experimental and preview models are removed without notice — sometimes within weeks. Always confirm that the exact model version is available on the production API endpoint before making any productionization decision. If it is not available, the prototype must be re-validated on a stable model.

**High-temperature cherry-picking.** Temperature is set to 1.2 during prototyping to get impressive, creative outputs. The demo shows one outstanding response. In testing, 70% of outputs at temperature 1.2 are inconsistent, off-format, or hallucinatory. The prototype "worked" because the team ran it 30 times and showed the best result. Document temperature in the configuration record and run multiple outputs in the review.

**API key in the demo URL.** The prototype uses a browser-based integration tool that accepts an API key as a URL parameter for convenience. The demo URL `https://tool.example.com?api_key=sk-proj-abcdef` is shared in the meeting chat, in the recording, and in a screenshot in the meeting notes. The key is now compromised and must be rotated immediately. Never use URL parameters for API keys.

**No output schema means no parser.** The prototype works because a human reads the output and extracts the relevant information by eye. The team plans to productionize. The prompt produces slightly different JSON structures — sometimes with a wrapper object, sometimes without — depending on the phrasing of the input. Writing a parser that handles all variations is a significant engineering effort. Productionization requires both a defined schema and a prompt that reliably produces it — this must be tested as part of the prototype, not deferred to the productionization phase.

**Real patient or user data in the studio.** The team builds a medical notes summarization prototype in Google AI Studio using de-identified but still sensitive clinical notes "just to see if it works." Google AI Studio's free tier data policy allows using conversation data for model improvement. The prototype conversation containing clinical notes is now subject to that policy. Review data handling policy before any prototype work with any real-world data, including data that has been de-identified.

**Rate limit math not done before a multi-user demo.** Fifteen stakeholders are invited to test the prototype simultaneously. The API key has a 60 RPM rate limit. Each person makes 3 requests in the first 2 minutes. That is 45 requests in the first 2 minutes — within the limit. But on minute 3, everyone tries at once: 45 requests in 60 seconds, which exceeds 60 RPM. The demo fails for 30% of users during the most important demonstration of the project. Calculate rate limit exposure before any multi-user demo.

**Platform-injected context not accounted for.** The Anthropic Console and Claude.ai Projects inject the current date, user name, and in some tiers, project-specific context into the model's context automatically. The prototype relies on the model knowing today's date (injected by the platform) to perform date calculations. When the same prompt is called via the raw API without that injection, the date calculations fail. Test every prototype by calling the same prompt via the raw API (not the studio UI) to identify dependencies on platform-injected context.

## Required output

Produce an AI studio prototype review report with:

1. **Prototype configuration** — platform, exact model version, all parameters, system prompt status (full / summarized / default)
2. **API key assessment** — scope, exposure risk (clean/compromised), usage limit status, rotation date
3. **Reproducibility results** — prompts tested, runs per prompt, schema consistency verdict, key fact consistency verdict
4. **Model version status** — preview/experimental/GA, production API availability, deprecation timeline
5. **System prompt readiness** — versioned (yes/no), output schema (yes/no), platform-context dependencies found (yes/no), key issues
6. **Rate limit assessment** — current limits, calculated demand for demo and production loads, risk level (safe/at risk/will fail)
7. **Productionization gap table** — capability, prototype approach, production requirement, effort estimate (S/M/L/XL)
8. **Data handling findings** — whether real/sensitive data was used, platform tier, data policy summary, risk level
9. **Go/no-go recommendation** — READY / CONDITIONAL (conditions listed with acceptance criteria) / INVALID (reason and rebuild guidance)

## Safety

- Do not enter real PII, regulated data, or confidential business information into any AI studio environment during the review process itself.
- If you discover the prototype was built using real user data, treat this as a data handling incident and escalate before completing the review.
- Rotate any API key confirmed to be exposed in shared URLs, screenshots, presentation materials, or recorded demos — document the exposure scope before rotation.
- Do not recommend productionizing a prototype that has an unresolved data handling violation, even under time pressure from stakeholders.
- Do not use the prototype's AI studio session to test adversarial inputs or injection scenarios — use a separate isolated session with a restricted API key.

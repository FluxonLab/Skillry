# Overview

This skill package teaches AI agents (and humans) how to ship **multilingual websites** with correct **i18n architecture** and **technical SEO** signals—without requiring a paid translation API or hosted TMS.

## What it is

- An installable agent skill (`SKILL.md` + `skill.json`)
- Operational docs: SEO checklist, translation playbook, locale architecture, framework adapters
- Offline Python checkers for HTML/`dist/` audits
- JSON schemas, checklists, prompts, and templates for repeatable work

## What it is not

- A SaaS product or translation management system
- A guarantee of search rankings or traffic
- A substitute for qualified legal review on jurisdiction-specific pages
- Permission to invent testimonials, certifications, or statistics

## Core principles

1. **Localize, don’t calque** — preserve meaning and conversion job; adapt SEO keywords per market.
2. **One locale registry** — BCP47 tags, URL prefixes, `dir`, labels live in one validated JSON file.
3. **Honest alternates** — hreflang only for real, indexable, reciprocal twins; omit missing pages.
4. **No surprise redirects** — do not force geo-IP or `Accept-Language` redirects by default.
5. **Market priority** — invest translation effort where demand justifies it.
6. **CI as a gate** — fail builds when canonical / hreflang / lang / og:url regress.

## Workflow at a glance

```text
Discover → Plan → Technical SEO → Translate → Verify
   A         B          C             D         E
```

See [`../SKILL.md`](../SKILL.md) for the control plane and [`multilingual-seo-checklist.md`](multilingual-seo-checklist.md) for every audit dimension.

## Offline vs optional LLM

| Capability | Offline | Via host agent |
|------------|---------|----------------|
| HTML / dist SEO audit scripts | Yes | — |
| Registry / schema validation | Yes | — |
| Translation / transcreation | — | Yes (agent) |
| Local keyword adaptation | Partial (templates) | Yes (research if tools allow) |

No paid API is required for the core audit and planning workflow.

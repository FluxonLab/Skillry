# Strategic SEO Planning

> **Reference of `seo-content-ops-review`.** Formerly the standalone skill `seo-plan`; the routing table in [../SKILL.md](../SKILL.md) sends that name and its topics here.
>
> - Origin: third-party, [AgriciDaniel/claude-seo](https://github.com/AgriciDaniel/claude-seo) `skills/seo-plan/SKILL.md` at commit 2384fdd9429696021d143006a722c7cf1aa76d43 (byte-identical; sidecars matched at the commits recorded for the lock); imported from a local unmanaged install.
> - License: MIT, Copyright (c) 2026 agricidaniel (upstream root `LICENSE` checked 2026-09-19, blob 94fac746, same at the pinned commits); full text at [seo-plan/LICENSE](seo-plan/LICENSE), upstream per-skill notice at [seo-plan/LICENSE.txt](seo-plan/LICENSE.txt).
> - Paths: file paths in code spans are relative to the skill directory (the folder holding `SKILL.md`).
> - Family note: Sibling names from the claude-seo plugin (for example `seo-geo`, `seo-google`, `seo-schema`, `seo-dataforseo`), its `/seo ...` commands, its repository-level `scripts/`, its shared `skills/seo/references/` files and its `extensions/` installers are not vendored; see the upstream repository. Siblings folded into this hub are listed in the routing table of [../SKILL.md](../SKILL.md).
> - Consolidation changes: frontmatter moved into this header; its self-contained DataForSEO section was moved to the hub's optional-integrations reference; paths to its own sidecar files now point to the moved, byte-identical copies; body otherwise unchanged.

<details><summary>Former frontmatter (kept for provenance)</summary>

```yaml
name: seo-plan
description: >
  Strategic SEO planning for new or existing websites. Industry-specific
  templates, competitive analysis, content strategy, and implementation
  roadmap. Use when user says "SEO plan", "SEO strategy", "SEO planning",
  "content strategy", "keyword strategy", "content calendar",
  "site architecture", or "SEO roadmap".
user-invocable: true
argument-hint: "[business-type]"
license: MIT
metadata:
  author: AgriciDaniel
  version: "2.2.5"
  category: seo
```

</details>

## Process

### 1. Discovery
- Business type, target audience, competitors, goals
- Current site assessment (if exists)
- Budget and timeline constraints
- Key performance indicators (KPIs)

### 2. Competitive Analysis
- Identify top 5 competitors
- Analyze their content strategy, schema usage, technical setup
- Identify keyword gaps and content opportunities
- Assess their E-E-A-T signals
- Estimate their domain authority

### 3. Architecture Design
- Load industry template from `assets/seo-plan/` directory
- Design URL hierarchy and content pillars
- Plan internal linking strategy
- Sitemap structure with quality gates applied
- Information architecture for user journeys

### 4. Content Strategy
- Content gaps vs competitors
- Page types and estimated counts
- Blog/resource topics and publishing cadence
- E-E-A-T building plan (author bios, credentials, experience signals)
- Content calendar with priorities

### 5. Technical Foundation
- Hosting and performance requirements
- Schema markup plan per page type
- Core Web Vitals baseline targets
- AI search readiness requirements
- Mobile-first considerations

### 6. Implementation Roadmap (4 phases)

#### Phase 1: Foundation (weeks 1-4)
- Technical setup and infrastructure
- Core pages (home, about, contact, main services)
- Essential schema implementation
- Analytics and tracking setup

#### Phase 2: Expansion (weeks 5-12)
- Content creation for primary pages
- Blog launch with initial posts
- Internal linking structure
- Local SEO setup (if applicable)

#### Phase 3: Scale (weeks 13-24)
- Advanced content development
- Link building and outreach
- GEO optimization
- Performance optimization

#### Phase 4: Authority (months 7-12)
- Thought leadership content
- PR and media mentions
- Advanced schema implementation
- Continuous optimization

## Industry Templates

Load from `assets/seo-plan/` directory:
- `saas.md`: SaaS/software companies
- `local-service.md`: Local service businesses
- `ecommerce.md`: E-commerce stores
- `publisher.md`: Content publishers/media
- `agency.md`: Agencies and consultancies
- `generic.md`: General business template

## Output

### Deliverables
- `SEO-STRATEGY.md`: Complete strategic plan
- `COMPETITOR-ANALYSIS.md`: Competitive insights
- `CONTENT-CALENDAR.md`: Content roadmap
- `IMPLEMENTATION-ROADMAP.md`: Phased action plan
- `SITE-STRUCTURE.md`: URL hierarchy and architecture

### KPI Targets
| Metric | Baseline | 3 Month | 6 Month | 12 Month |
|--------|----------|---------|---------|----------|
| Organic Traffic | ... | ... | ... | ... |
| Keyword Rankings | ... | ... | ... | ... |
| Domain Authority | ... | ... | ... | ... |
| Indexed Pages | ... | ... | ... | ... |
| Core Web Vitals | ... | ... | ... | ... |

### Success Criteria
- Clear, measurable goals per phase
- Resource requirements defined
- Dependencies identified
- Risk mitigation strategies

## DataForSEO Integration (Optional)

Moved to [seo-optional-integrations.md](seo-optional-integrations.md#seo-plan) during consolidation (optional DataForSEO MCP usage).

## Error Handling

| Scenario | Action |
|----------|--------|
| Unrecognized business type | Fall back to `generic.md` template. Inform user that no industry-specific template was found and proceed with the general business template. |
| No website URL provided | Proceed with new-site planning mode. Skip current site assessment and competitive gap analysis that require a live URL. |
| Industry template not found | Check `assets/seo-plan/` directory for available templates. If the requested template file is missing, use `generic.md` and note the missing template in output. |

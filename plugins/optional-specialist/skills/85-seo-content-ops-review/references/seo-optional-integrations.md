# SEO optional integrations

> **Reference of `seo-content-ops-review`.** Skillry-authored index (3.0.0 consolidation) of the optional paid or credentialed data sources the absorbed SEO references can use. Every procedure works without them; each one states its free fallback.
>
> - Sections below headed by a skill name are moved verbatim from that skill's upstream text (AgriciDaniel/claude-seo, MIT; full license text beside each reference, for example [seo-page/LICENSE](seo-page/LICENSE)).
> - DataForSEO tools come from the DataForSEO MCP server, which is not part of Skillry. Confirm the user has it connected and accepts per-call cost before using any tool named here; never ask the user for an API key in chat.

## Where optional integrations stay in place

| Reference | Integration | Where |
|---|---|---|
| [seo-backlinks.md](seo-backlinks.md) | DataForSEO MCP (primary when present), Moz API, Bing Webmaster Tools, Common Crawl | every analysis section, the health-score weights and the error-handling table |
| [seo-cluster.md](seo-cluster.md) | DataForSEO `serp_organic_live_advanced` with a cost check, WebSearch fallback | SERP data collection, integration table, error table |
| [claude-seo-seo-sxo.md](claude-seo-seo-sxo.md) | DataForSEO cost threshold fallback | error-handling table (its integration section moved below) |
| [claude-seo-seo-images.md](claude-seo-seo-images.md) | DataForSEO MCP for image SERP data | description and error table (its image SERP section moved below) |

## claude-seo-seo-images

Moved from [claude-seo-seo-images.md](claude-seo-seo-images.md).

### Image SERP Analysis

When DataForSEO MCP is available, enhance the image audit with competitive data.

#### `/seo images serp <keyword>`

Cross-reference on-page images with Google Images SERP rankings.

**Workflow:**
1. Fetch Google Images results via `serp_google_images_live_advanced` (depth=100)
2. Extract: top domains, image types, alt text patterns
3. Output competitor image SERP landscape

**Output:**

| Rank | Domain | Title/Alt | Image URL | Page URL |
|------|--------|-----------|-----------|----------|
| 1 | example.com | "Blue running shoes..." | .../shoes.webp | /products/... |

**Analysis includes:**
- **Domain dominance**: which sites own the most image positions (top 10 by count)
- **Alt text patterns**: common title/alt patterns in top-ranking images
- **Format distribution**: WebP vs JPEG vs PNG in top results
- **Opportunity score**: keywords where you have page rankings but no image presence

If DataForSEO MCP is not available, inform user and suggest installing the extension.

## claude-seo-seo-sxo

Moved from [claude-seo-seo-sxo.md](claude-seo-seo-sxo.md).

### DataForSEO Integration

If DataForSEO MCP tools are available:

1. **Before any API call**, run cost estimate and confirm with user
2. Use `google_organic_serp` for precise SERP data (positions, features, snippets)
3. Use `keyword_data` for search volume and competition metrics
4. Fall back to WebSearch if DataForSEO unavailable -- note reduced precision in output

## seo-content

Moved from [seo-content.md](seo-content.md).

### DataForSEO Integration (Optional)

If DataForSEO MCP tools are available, use `kw_data_google_ads_search_volume` for real keyword volume data, `dataforseo_labs_bulk_keyword_difficulty` for difficulty scores, `dataforseo_labs_search_intent` for intent classification, and `content_analysis_summary` for content quality analysis.

## seo-page

Moved from [seo-page.md](seo-page.md).

### DataForSEO Integration (Optional)

If DataForSEO MCP tools are available, use `serp_organic_live_advanced` for real SERP positions and `backlinks_summary` for backlink data and spam scores.

## seo-plan

Moved from [seo-plan.md](seo-plan.md).

### DataForSEO Integration (Optional)

If DataForSEO MCP tools are available, use `dataforseo_labs_google_competitors_domain` and `dataforseo_labs_google_domain_intersection` for real competitive intelligence, `dataforseo_labs_bulk_traffic_estimation` for traffic estimates, `kw_data_google_ads_search_volume` and `dataforseo_labs_bulk_keyword_difficulty` for keyword research, and `business_data_business_listings_search` for local business data.

## seo-technical

Moved from [seo-technical.md](seo-technical.md).

### DataForSEO Integration (Optional)

If DataForSEO MCP tools are available, use `on_page_instant_pages` for real page analysis (status codes, page timing, broken links, on-page checks), `on_page_lighthouse` for Lighthouse audits (performance, accessibility, SEO scores), and `domain_analytics_technologies_domain_technologies` for technology stack detection.

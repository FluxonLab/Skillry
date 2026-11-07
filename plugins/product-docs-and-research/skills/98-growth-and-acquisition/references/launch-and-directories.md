# Launch Checklist, Free Directories, Backlinks, and Daily Brief

This reference defines the launch workflow, triage rules for directories and community platforms, backlink verification standards, platform compliance rules, and the Daily Brief template for ongoing customer acquisition.

---

## 1. Directory and community evaluation guardrails

Always evaluate external directory lists and launch collections with critical verification:

| Source category | Example types | Verified attributes | Unverified risks and mandatory guardrails |
|---|---|---|---|
| **Community launch collections** | Curated collections of launch directories, Reddit communities, Discord groups, and forums | Presence of community URLs and submission criteria | **Unverified:** Traffic estimates and claims of automatic rank boosts.<br>**Guardrail:** Many communities prohibit self-promotion. Select a small, relevant, user-approved subset; never batch-submit across large lists. |
| **Startup directory aggregators** | Large launchpad lists (e.g. Dev.to, Crunchbase, Hacker News, G2, startup catalogues) | Entry presence and general category classifications | **Unverified:** Third-party Domain Rating (DR) figures; link status (often mixes free `dofollow`, `nofollow`, conditional, and paid listings from $15 to $249+).<br>**Guardrail:** Inspect each candidate live before queuing. Use only verified free listings unless paid budget is explicitly approved. |
| **Low-quality Web 2.0 / link farms** | Bulk directories, social bookmarking lists, generic business directories | Directory existence | **Avoid:** Author traffic and authority numbers are unverified; often gated behind social engagement or direct-message capture; high spam and search penalty risk.<br>**Guardrail:** Reject low-quality link farms and engagement-gated lists. |
| **Growth teardowns and product loops** | Growth analyses tracking launch milestones, badge backlink loops ("Built with X"), comparison hubs, and vertical video demos | Proven acquisition patterns in public case studies | **Guardrail:** Conduct competitive teardowns using standard research tools. Ground all findings in the project's own research ledger; do not rely on paid unvetted third-party analysis services. |

---

## 2. Launch checklist (New products and major surface launches)

> **Live-product rule:** For established, already-live products, do not run a first-launch directory blast. Instead, use steady-state feature release announcements, backlink gap analysis, and the Daily Brief workflow.

### Phase A — Pre-launch foundation (T-14 to T-2)
- [ ] **Audience and competitor baseline:** Confirm target customer profiles, regional considerations, and competitor benchmarks are recorded in the project research ledger.
- [ ] **First-draft discovery complete:** Landing pages, documentation, and store listings pass discovery checks (SEO, GEO, AEO, ASO, claim ledger, and anti-slop review).
- [ ] **Mobile store readiness (if shipping mobile or game builds):**
  - Store metadata and localized screenshots prepared according to platform requirements.
  - Video preview assets (e.g. iOS 21:9 product page header video, `3840 x 1646`, safe area `1646 x 661`) prepared and verified using `mobile-app-review`.
- [ ] **Infrastructure and lifecycle email:**
  - DNS records configured with verified SPF, DKIM, and DMARC settings for transactional and newsletter delivery.
  - Welcome, onboarding, and newsletter templates wired through your configured email provider (e.g. Resend, Sendgrid).
  - Error monitoring configured with personal data scrubbing (e.g. Sentry).
- [ ] **Curated launch shortlist:**
  - Select 10–15 relevant launch destinations across categories:
    1. **Developer and technical platforms:** Hacker News (`Show HN`), Dev.to, GitHub Discussions and Releases (for open-source projects).
    2. **Startup directories and review profiles:** Crunchbase, G2, Product Hunt, and verified free category-specific software directories.
    3. **Topic communities:** 3–5 active forums, subreddits, or discussion groups where potential users discuss problems the product solves.
  - Fetch each target live to verify current submission rules, cost (free vs. paid), and link attributes (`dofollow`, `nofollow`, conditional, or unverified).

### Phase B — Launch execution (User-approved batches only)
- [ ] **Stage unique assets:** Prepare distinct visual assets or demo videos for each channel; do not reuse identical marketing images across different platforms.
- [ ] **Submit via the Daily Brief gate:** Present the launch batch in the Daily Brief. Upon explicit approval:
  - Schedule or publish approved social posts through your designated social management tool or publishing pipeline.
  - Stagger interactive community launches (e.g. Show HN, technical blog articles, forum threads) so team members can actively monitor and respond to early comments.

### Phase C — Post-launch verification (T+1 to T+30)
- [ ] **Directory and backlink receipt log:** Inspect submitted directories at T+7 and T+28. Record live listing URLs, actual HTML link attributes (`rel="nofollow"` vs. `dofollow`), and search index status in the research ledger.
- [ ] **Feedback and changelog loop:** Feed community responses, bug reports, and user feedback into the project's requirements and issue tracker.

---

## 3. Directory and backlink triage rubric

Score candidate directories and backlinks in the project's directory ledger before queuing them in a Daily Brief:

| Directory / Platform | Source category | Live URL checked (date) | Cost (Free / $X paid) | Link attribute (`dofollow` / `nofollow` / `conditional` / `unverified`) | Category fit (High / Med / Low) | Anti-spam and terms check | Status |
|---|---|---|---|---|---|---|---|
| Dev.to | Developer platform | YYYY-MM-DD | Free | `nofollow` / canonical link (verify per post) | High (developer/SaaS) | Requires substantive technical article; no spam link drops | Candidate |
| Crunchbase | Entity database | YYYY-MM-DD | Free profile (verify current tier) | `nofollow` (verify live) | High (company profile) | Factual organization record for GEO entity consistency | Candidate |
| Hacker News (`Show HN`) | Maker community | YYYY-MM-DD | Free | `dofollow` / conditional on ranking | High (technical/maker) | Direct maker post with technical depth; no voting rings | Candidate |
| G2 | Software review platform | YYYY-MM-DD | Free vendor listing (verify tier) | `nofollow` / profile | High (B2B SaaS) | Genuine customer reviews only; never incentivize fake reviews | Candidate |

### Stop conditions for directories and backlinks:
1. **Paid fee required without prior approval:** If a directory demands a submission fee ($15, $49, $249, etc.), mark as `paid — requires budget approval` or drop. Never commit funds without authorization.
2. **CAPTCHA or anti-bot challenge:** Never solve, click through, or bypass a CAPTCHA, Cloudflare Turnstile, or proof-of-work gate. Flag the item as `manual user step required` in the brief.
3. **Engagement-gated lists or link farms:** Reject lists that require social follow/DM gates, or domains with known link-farm characteristics.

---

## 4. Platform and community rules

### 4.1 Reddit
- **API and terms constraints:** Comply with Reddit's Developer Terms; do not conduct commercial harvesting or unauthorized automated scraping.
- **Subreddit rule check:** Read each subreddit's sidebar rules (`r/<subreddit>/about/rules`) before drafting. Check:
  - Maker policy (e.g. self-promotion permitted only in designated weekly threads or Show Saturday posts).
  - Required flair, minimum account karma, and account age requirements.
  - Self-promotion ratio guidelines (typically at least 9:1 community contribution to self-links).
- **Drafting standard:** Lead with the technical solution, insights gained, or direct answer to a problem. Disclose maker status transparently (`"I built X to solve this because..."`). Never cross-post identical text across subreddits.

### 4.2 Online groups and forums (Facebook Groups, Discord, Forums)
- Inspect group guidelines regarding external links and commercial tools. Many groups require admin approval before posting links.
- Never use unauthorized scripts to bulk-join groups or automate submissions. Deliver approved drafts as formatted copy packets ready for manual user posting where APIs are not available.

### 4.3 Social channels
- Research relevant topic tags using platform search or research scripts before publishing.
- Route brand posts through your approved social management platform or scheduling calendar. Keep all scheduled posts centralized; do not maintain conflicting parallel schedules.

---

## 5. Daily Brief template

Present the daily customer-acquisition brief in clear, actionable markdown:

```markdown
# Daily Acquisition and Distribution Brief — <YYYY-MM-DD> (<Project Name>)

**Summary:** <N> social posts / community replies, <M> directory submissions queued. All claims verified against code evidence; anti-slop review passed.

---

### [B-01] <Target Channel / Community or Directory Name> — `<Type: Social Post | Community Reply | Directory Submission>`
- **Target URL / Context:** <Link to thread or directory, and why it is relevant today>
- **Rules and Terms Check:**
  - Platform rule: <e.g. Maker participation allowed with disclosure / Technical reply only / No links allowed>
  - Cost and Link Type: `<Free | Paid ($X)>` · `<dofollow | nofollow | conditional | unverified>`
- **Proposed Draft (<Target Language>):**
  > <Full text to be published, including title, body, and call-to-action>
- **Summary / Intent:** <1-2 sentence summary explaining the objective of this post>
- **Tags and Media:** `<#tag1 #tag2>` · `<Path to visual asset or demo video>`
- **Execution Channel (Post-Approval):** `<Social Scheduling Pipeline | Email Provider | Manual User Submission>`

---

### Decision Required
1. **Approve all items as drafted and queue for publication**
2. **Approve specific items with adjustments** (e.g. `B-01: adjust phrasing as follows...`, `B-02: skip`)
3. **Hold or cancel today's batch**
```

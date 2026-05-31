---
name: technical-writing-review
description: Use when you need to review technical writing for accuracy, structure, brevity, and execution orientation.
---

# Technical Writing Review

## Purpose

Review a technical document — API reference, tutorial, guide, runbook, README, or changelog — for factual accuracy, structural clarity, audience fit, code example correctness, terminology consistency, and actionability. Produce line-level findings and a summary verdict.

## When to use

- A developer guide, API reference, or tutorial has been drafted and needs editorial review before publish.
- A runbook or incident response doc needs a readability and completeness check.
- A README is being reviewed for a public open-source repo.
- Inconsistent terminology has been reported across docs and needs auditing.
- A technical blog post or whitepaper needs a precision and clarity pass.
- A changelog or release note draft needs to be checked for completeness and audience-appropriate language.

## When not to use

- The document is a PRD or requirements doc — use `product-requirements-review`.
- The document is a business proposal or pitch — that is copywriting review, not technical writing review.
- The document has not been drafted yet — help write it, do not review nothing.
- The review requested is purely stylistic (word choice aesthetics) with no technical content.

## Procedure

1. **Identify document type and target audience**: API reference, tutorial, concept guide, runbook, README, changelog. Identify who the reader is: beginner developer, senior engineer, ops team, end-user. All subsequent checks are calibrated to this audience.
2. **Accuracy check**: For every stated fact, command, parameter, or configuration value, verify it against the actual codebase, API spec, or official upstream documentation if available. Flag unverified claims as "cannot verify — needs SME confirmation."
3. **Structure audit**: Does the document follow a logical reading order for its type?
 - Tutorial: goal → prerequisites → steps → verification → next steps
 - API reference: endpoint → method → parameters → request example → response → error codes
 - Runbook: trigger condition → diagnosis steps → remediation → escalation
 - README: what it does → install → quickstart → configuration → contributing
 Flag missing sections and misplaced content.
4. **Code and command block review**: Every code block must be syntactically valid for its language. Check for: missing imports, placeholder values not wrapped in `<angle-brackets>`, commands that will fail on a fresh environment (missing `cd`, wrong path assumptions), and outdated version numbers.
5. **Audience fit**: Is the assumed knowledge level consistent throughout? Flag paragraphs that assume expert knowledge in a beginner document or over-explain basics in a reference doc.
6. **Jargon and terminology audit**: List every piece of jargon, acronym, or product-specific term. Is each introduced before use? Is the same concept named consistently (not "webhook" in one section and "callback" in another)?
7. **Brevity and passive voice**: Flag sentences > 30 words. Flag passive voice where active is clearer ("The function is called by the SDK" → "The SDK calls the function"). Flag adverb bloat ("very", "quite", "basically", "simply").
8. **Completeness**: Does the document cover the full task it promises? Are error states documented? Is the "what if it doesn't work" path present?
9. **Links and references**: Are all external links present? Are version-pinned links used where appropriate (avoid linking to /latest/ in versioned docs)?
10. **Output**: Produce line-level findings and summary verdict.

## Checklist

- [ ] Document type and audience explicitly identified before review starts
- [ ] All technical claims verified or flagged as unverified
- [ ] Structure matches expected pattern for document type
- [ ] Every code block is syntactically valid and runnable
- [ ] Placeholder values clearly marked (e.g., `<YOUR_API_KEY>`)
- [ ] Assumed knowledge level consistent throughout
- [ ] All jargon and acronyms introduced before use
- [ ] Terminology consistent (same concept, same word, every time)
- [ ] No sentences > 30 words (or flagged with rewrite suggestion)
- [ ] Passive voice flagged where active is clearer
- [ ] Error paths and "what if it fails" documented
- [ ] All links valid and appropriately versioned

## Common issues & anti-patterns

- **"Simply" and "just"**: These words signal the writer found something easy; the reader may not. Remove them.
- **Copy-paste code that does not run**: The most common trust-destroyer in technical docs. Always run examples before publishing.
- **Missing prerequisites**: Tutorial starts with `npm install` with no mention of Node.js version requirement.
- **Terminology drift**: "Token", "key", "credential", "secret" used interchangeably for the same concept. Pick one.
- **Over-nesting**: Headers 4 levels deep indicate structural confusion. Flatten or split the document.
- **Wall of text before quickstart**: Users want to see something work before reading theory. Move the quickstart up.
- **No error handling in examples**: `response = client.get(url)` with no status check teaches bad practice.
- **Changelog without user impact**: "Refactored internal handler" — what should the user do differently? State the user-visible change.
- **Passive voice obscuring ownership**: "An error will be returned if..." — returned by what? Make the subject explicit.

## Required output

```
## Technical Writing Review: [Document title / path]

### Document type: [type]
### Target audience: [audience]

### Accuracy findings
| Line/section | Issue | Severity (block/warn/note) | Suggested fix |

### Structure findings
- Missing sections: [list]
- Misplaced content: [describe]

### Code block findings
| Block location | Issue | Corrected version or flag |

### Audience fit findings
- Over-assumes knowledge: [section, line]
- Under-assumes knowledge: [section, line]

### Terminology issues
| Term | Variants found | Recommended canonical term |

### Brevity / clarity findings
- Long sentences: [line refs]
- Passive voice: [line refs with active rewrites]
- Filler words: [instances]

### Completeness gaps
- [Missing error path / scenario / next step]

### Links
- Broken or missing: [list]
- Version-pinned where needed: [Yes/No/Partial]

### Verdict
[PUBLISH-READY / NEEDS-REVISION / MAJOR-REWORK] — summary in 2–3 sentences

### Priority fixes (top 3)
1. …
```

## Safety

- Do not alter code examples in the source document without explicit confirmation — propose changes in the review output only.
- Do not verify claims against internal systems or production APIs; limit to provided source and public documentation.
- If the document describes security-sensitive procedures (credential rotation, firewall rules, access control), flag that a security team review is required in addition to this writing review.

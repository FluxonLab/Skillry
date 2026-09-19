# Memory And Context

## User-Facing Model

Keep two durable product concepts:

```text
Glossary
Project Memory
```

The storage representation may evolve, but do not make users maintain separate
term registries, term decisions, review-decision logs, and Knowledge Pack term
files as competing sources of truth.

Store durable project memory under `.localize-anything/` when appropriate. Ask
before committing project memory if it may contain private product information.

The default path creates Project Memory with `localize scan` and creates
conservative Glossary candidates with `localize glossary bootstrap`. Do not
substitute older memory files as a default input.

## Concept-Centered Glossary

Model the product concept first, then its expressions across locales:

```yaml
concepts:
  - id: workspace
    source_terms: [Workspace]
    behavior: translate
    status: locked
    target:
      preferred: Рабочая область
      forbidden: []
    scope: product
    notes: Main space where users manage projects and runs.

  - id: cny
    source_terms: [CNY]
    behavior: preserve
    status: locked
    target:
      preferred: CNY
      forbidden: []
```

Entries may include source terms, per-locale preferred/forbidden translations,
`translate` or `preserve` behavior, status, scope, context, notes, provenance,
and human confirmation.

Agent-friendly canonical operations:

- Lock a concept translation by setting `behavior: translate`,
  `status: locked`, and `target.preferred` to the confirmed target expression.
- Preserve a term by setting `behavior: preserve`, `status: locked`, and
  `target.preferred` to the source form when useful for clarity.

## First-Run Glossary Flow

```text
Discover -> Import -> Normalize -> Rank -> Confirm -> Use
```

- Discover existing glossaries, locale resources, README/product docs, repeated
  UI concepts, brands, code entities, Translation Memory, and prior decisions.
- Import canonical project data plus supported CSV, YAML, or JSON.
- Normalize duplicates and conflicting representations without discarding
  provenance.
- Rank approximately 5–15 high-impact concepts rather than asking the user to
  approve every low-risk term.
- Confirm preferred, forbidden, preserve, scope, and product-meaning decisions.
- Use approved concepts in generation and review.

Low-risk candidates may be provisionally accepted by the Agent and corrected
through later review. Locked or high-risk decisions require explicit evidence
or user confirmation.

## Translation Memory

Use project-level Translation Memory to:

- reuse confirmed complete sentences;
- detect source changes that make old targets stale;
- suggest similar reviewed copy;
- preserve human corrections;
- reduce duplicate work.

Prefer exact segment ID, exact source, compatible scope, and then conservative
fuzzy matching. Never mix target locales. Unreviewed generated text is reference
material, not authoritative memory.

## Style And Preserve Rules

Project Memory should also retain:

- audience and product voice;
- capitalization, punctuation, formality, and UI-length guidance;
- brands, codes, variables, URLs, product names, and other preserved forms;
- locale-specific conventions;
- recurring defects and accepted corrections.

## Context Construction

For each implementation or review batch, load only:

- product and user context;
- declared scope and candidate classifications;
- relevant Glossary concepts;
- relevant reviewed Translation Memory;
- relevant style and preserve rules;
- adjacent UI or document context;
- hard format constraints;
- unresolved high-risk decisions.

Do not treat chat summaries, embeddings, browser state, generated guesses, or
unreviewed model output as durable truth.

## Promotion

The Phase 2 core records human decisions through `localize report --confirm`.
It does not automatically promote them into a separate legacy memory store.
Propose a small, reviewable Glossary or Project Memory edit only after scope and
review status are clear:

- confirmed concepts and translations -> Glossary;
- reviewed complete targets -> Translation Memory;
- accepted voice and convention decisions -> style rules;
- recurring mistakes and corrections -> review history;
- unresolved ambiguity -> human confirmation, not memory.

---
name: rag-vector-search-review
description: Use when you need to review retrieval, embeddings, chunking, vector search, ranking, and grounding strategy.
---

# RAG Vector Search Review

## Purpose

Audit a Retrieval-Augmented Generation pipeline end-to-end: chunking strategy, embedding model choice, vector database configuration, similarity metric, hybrid search setup, reranking, recall measurement, and index staleness. Produces specific, actionable findings — not a generic RAG tutorial. Every finding must include the configuration parameter that needs to change and the expected impact on recall.

## When to use

- Retrieved chunks are not relevant to the query, or the model is hallucinating despite RAG being in place.
- Retrieval latency is too high and the bottleneck (embedding, index scan, reranking) is unknown.
- The embedding model is being changed and you need to assess the impact on existing indexes before migration.
- The index has not been refreshed in a long time and stale content is likely being retrieved.
- Hybrid search (keyword + vector) is producing worse results than pure vector alone, or the blend ratio has never been tuned.
- The system has no recall measurement and you need to establish a baseline before any optimization.
- A reranker was added but latency increased without a corresponding improvement in answer quality.

## When not to use

- The problem is prompt structure, not retrieval — chunks are retrieved correctly but the model ignores them (use `prompt-systems-review`).
- The problem is evaluation methodology rather than retrieval mechanics (use `llm-evaluation-review`).
- The system does not use retrieval at all — pure generation or a fine-tuned model.
- The only question is which vector database to use for a greenfield project — this is an architecture decision, not a review.

## Procedure

1. **Map the pipeline.** Document each stage with the responsible component and its key configuration: document ingestion → text extraction → chunking → embedding → indexing → query embedding → vector search → [optional: reranking] → context assembly → generation prompt construction. Any stage with no documented configuration is an audit gap.

2. **Audit chunking strategy.** Record:
 - Chunk size in tokens (not characters — convert if recorded in characters)
 - Overlap in tokens
 - Chunking method: fixed-size / sentence-boundary / paragraph-boundary / semantic (embedding-based)
 - Whether metadata is stored with each chunk (source document ID, page number, section title, timestamp)
 Check that chunk size stays below the embedding model's token limit with a 10% safety margin. For `text-embedding-3-small`: max 512 tokens; for `text-embedding-3-large`: max 8,191 tokens; for `voyage-3`: max 32,000 tokens. Verify overlap is 10-15% of chunk size to prevent context splitting at boundaries.

3. **Audit the embedding model.** Record: model name, version or release date, vector dimension count, max token input length, whether the model is identical at index time and query time (model name AND version). A mismatch between index-time and query-time embedding models produces meaningless similarity scores — the vectors are in different semantic spaces. Check whether the provider manages the model version or whether it is pinned. Provider-managed "latest" endpoints change without notice.

4. **Audit the vector database configuration.** Record:
 - DB type: pgvector / Pinecone / Weaviate / Qdrant / Chroma / Milvus
 - Index type: HNSW / IVF_FLAT / IVF_PQ / flat (exact)
 - Distance metric: cosine / dot-product / L2 (Euclidean)
 - `ef_search` (HNSW) or `nprobe` (IVF): higher values improve recall at latency cost
 - Approximate vs. exact search setting
 Confirm the distance metric matches the embedding model's training objective. Most modern embedding models (OpenAI, Cohere, Voyage) are trained for cosine similarity. Using L2 on normalized embeddings is equivalent but on unnormalized embeddings degrades results significantly.

5. **Check hybrid search configuration.** If hybrid search (BM25 keyword + vector) is in use:
 - Record the alpha parameter (weight between BM25 and vector scores; 0.0 = pure keyword, 1.0 = pure vector)
 - Verify BM25 scores and vector scores are normalized to the same range before blending (unnormalized blending produces unpredictable results)
 - Confirm the BM25 index is updated on the same schedule as the vector index
 - Check whether query expansion (synonyms, stemming) is applied to the BM25 side
 If hybrid search is producing worse results than pure vector, first check normalization, then check alpha tuning.

6. **Review reranking.** If a cross-encoder reranker is in use:
 - Record the reranker model name and version
 - Confirm the reranker receives the top-k candidates from vector search (recommended k: 20-50) and returns the top-n to the generation model (recommended n: 3-5)
 - Verify the reranker is not running on the full index (that is a latency anti-pattern — it negates the speed benefit of approximate vector search)
 - Measure the latency added by the reranker; confirm it is within the application's SLA

7. **Measure retrieval recall.** If a golden set exists, run retrieval queries and measure:
 - Recall@3: fraction of queries where at least one relevant document appears in the top 3 results
 - Recall@5: same for top 5
 - MRR (Mean Reciprocal Rank): average of 1/rank for the first relevant result
 - NDCG@5: normalized discounted cumulative gain at position 5
 If no golden set exists, create a minimum 50-query set with ground-truth relevant document IDs before proceeding. A RAG system with no recall measurement cannot be improved in a verifiable way.

8. **Check index staleness.** Record: last full re-index date, incremental update frequency (real-time / hourly / daily / weekly), average lag between source document update and index update. For high-volatility content (product FAQs, news, pricing), index lag over 6 hours is a hallucination risk — the model retrieves stale facts and presents them as current. For low-volatility content (legal docs, technical specs updated quarterly), weekly indexing may be acceptable.

9. **Review context assembly.** Confirm:
 - Retrieved chunks are deduplicated by source document ID before context assembly (same document retrieved twice wastes context window)
 - Total token count of assembled context fits within the model's context window with room for the system prompt, user query, and expected output
 - Each chunk includes provenance metadata: source document ID, chunk ID, retrieval score
 - Chunks are ordered by relevance score (highest first) or by logical document order, not random

## Checklist

- [ ] Pipeline fully documented: every stage has a named component and key configuration values
- [ ] Chunk size is below embedding model's token limit with 10% safety margin
- [ ] Overlap is 10-15% of chunk size
- [ ] Each chunk stores metadata: source document ID, page number or section title, timestamp
- [ ] Embedding model name AND version identical at index time and query time
- [ ] Embedding model version is pinned, not floating on a provider-managed "latest" endpoint
- [ ] Distance metric matches embedding model training objective (cosine for most modern models)
- [ ] HNSW `ef_search` or IVF `nprobe` value documented; not left at default
- [ ] Hybrid search scores normalized before blending if hybrid search is active
- [ ] Hybrid search BM25 index updated on same schedule as vector index
- [ ] Reranker applied to top-k candidates only (20-50), not full index
- [ ] Recall@3, Recall@5, MRR measured against a golden set of at least 50 queries — or golden set creation is the first action item
- [ ] Index update lag documented and appropriate for content volatility level
- [ ] Retrieved chunks deduplicated by source document ID before context assembly
- [ ] Context assembly includes provenance metadata per chunk
- [ ] Assembled context ordered by relevance score

## Common issues & anti-patterns

**Embedding model version drift.** The index was built with `text-embedding-ada-002`. The provider released `text-embedding-3-small` with different vector dimensions (1,536 vs 1,536 — same dimensions, but different semantic space). A developer switches the query-time model to 3-small without re-indexing. Cosine similarity scores between ada-002 index vectors and 3-small query vectors are meaningless. Pin embedding model versions and re-index on every model change.

**Chunk size exceeds model token limit.** Chunks are split at 1,500 characters (~375 tokens) and the embedding model's limit is 512 tokens. However, the document contains technical paragraphs with very long sentences. Some chunks exceed 512 tokens; the model silently truncates them. The tail of every oversized chunk is not represented in the embedding. Convert character limits to token counts and enforce the token limit directly.

**No recall measurement.** The team reports that retrieval "seems better" after a tuning session. There are no Recall@k numbers before or after. The improvement may be a cherry-picked example. Always measure Recall@5 before making any pipeline change and after, using the same fixed golden set.

**L2 distance on unnormalized embeddings.** The vector DB is configured with L2 distance because it was the default. The embedding model outputs unnormalized vectors. High-magnitude vectors dominate the L2 ranking even if semantically unrelated to the query. Either normalize all embeddings at insert time or switch the distance metric to cosine. Do not rely on the application layer to normalize — enforce it at the DB configuration level.

**Retrieval without deduplication.** A 50-page PDF is chunked into 200 chunks with overlap. A query about Chapter 3 retrieves 8 chunks from Chapter 3, all with high similarity. The context assembly includes all 8, consuming most of the context window with near-duplicate text. Deduplicate by source document ID in the context assembly step: keep only the highest-scoring chunk per document for the initial result set.

**Stale index for high-volatility content.** A pricing FAQ is updated whenever product pricing changes — roughly weekly. The vector index is refreshed monthly. For up to 3 weeks after a pricing change, the RAG system retrieves and presents the old price with confidence. Set incremental index updates for pricing content to run within 1 hour of source document change.

**Reranker on the full index.** A developer adds a cross-encoder reranker for quality improvement but configures it to rerank all 10,000 documents for each query. Reranking 10,000 pairs takes 30-60 seconds. The application becomes unusable. Cross-encoders are accurate but slow; use them only on the top-k candidates from the approximate vector search (k = 20-50), not on the full corpus.

## Required output

Produce a RAG pipeline review report with:

1. **Pipeline map** — table: stage, component/library name, key configuration parameters with values
2. **Chunking assessment** — chunk size in tokens, overlap in tokens, method, token limit compliance, metadata stored
3. **Embedding model assessment** — model name, version, dimensions, index-time vs. query-time match status, pinned/floating
4. **Vector DB assessment** — DB type, index type, distance metric, correctness verdict, `ef_search`/`nprobe` value
5. **Hybrid search assessment** — alpha value, normalization status, BM25 update frequency, verdict
6. **Reranker assessment** — model name, candidate set size (k), final set size (n), latency added, verdict
7. **Recall metrics** — Recall@3, Recall@5, MRR, NDCG@5 with golden set size; or "NOT MEASURED — action required"
8. **Index staleness report** — last re-index date, update frequency, content volatility level, lag verdict
9. **Context assembly review** — deduplication status, token budget compliance, provenance metadata status, ordering method
10. **Prioritized finding list** — severity (critical/high/medium/low), description, specific config parameter to change, expected recall impact

## Safety

- Do not re-index production data during a review — read configurations and run recall tests against a staging index with the same data.
- Do not log retrieved chunk contents that may contain PII or confidential business data during the review process.
- If the golden set used for recall measurement contains real user queries, anonymize it before using it in any test run.
- Do not recommend reducing chunk overlap or increasing chunk size to save storage without first measuring the recall impact on the golden set.

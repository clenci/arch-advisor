---
name: rag-strategy
description: "Use this skill when designing RAG (Retrieval-Augmented Generation) pipelines, choosing chunking strategies, retrieval methods, embedding models, or reranking approaches. Trigger when someone says 'we need to search our documents', 'the agent needs to answer questions from our knowledge base', 'how should we chunk and index?', 'we need semantic search', 'the LLM is hallucinating facts from our docs', 'we need to cite sources', 'RAG is returning irrelevant results'. Also trigger for: vector databases, embeddings, hybrid search, multi-query retrieval."
---

# RAG Strategy for Multi-Agent Systems

## Pipeline Overview

```
[Ingest]   → chunk → embed → store in vector DB
[Retrieve] → embed query → similarity search → (rerank) → top-K chunks
[Generate] → inject chunks as context → LLM generates grounded response
```

## Chunking Strategy by Document Type

| Document type | Strategy | Rationale |
|---|---|---|
| Technical documentation with sections | Hierarchical | Preserves section structure |
| Articles, blog posts | Sentence-based | Maintains paragraph coherence |
| FAQs | Fixed-size small (300–500 tokens) | Short, direct answers |
| Legal/contracts | Sentence-based with high overlap | Precision and boundary preservation |
| Code with comments | Fixed-size medium (500–1000 tokens) | Keep functions intact |
| Transcripts, conversations | Semantic | Group by topic discussed |
| Books, long-form content | Hierarchical | Chapter/section context |

Add 10–20% overlap on fixed-size and sentence-based chunks to reduce boundary artifacts.

## Retrieval Strategy

**Basic retrieval**: embed query → cosine similarity → top-K. Use for simple, specific queries on small corpora (<10K documents).

**Multi-query retrieval**: generate N query variations from the original → retrieve top-K per variation → deduplicate. Use when recall is critical and queries are open-ended. Cost: N LLM calls per query.

**Query transformation**:
- Decompose: break complex question into sub-questions
- Abstract: generalize specific query for broader coverage
- Clarify: disambiguate before retrieving
Use when queries are complex or ambiguous.

**Hybrid search (vector + BM25 with RRF)**:
- Vector: semantic similarity
- BM25/keyword: exact term matching
- RRF (Reciprocal Rank Fusion): merge ranked lists
Use when keyword precision matters alongside semantic coverage (e.g., technical terms, product codes).

**Reranking**: retrieve top-20 → LLM re-scores relevance → keep top-K. Use when precision is critical and hallucination must be minimized. Cost: one LLM call per retrieval.

## Embedding Model Trade-offs

| Model type | Quality | Cost | Latency | Dimensions |
|---|---|---|---|---|
| text-embedding-3-small | Good | Low | Low | 1536 |
| text-embedding-3-large | Excellent | Medium | Medium | 3072 |
| BGE / E5 (open-source) | Good | None (self-hosted) | Varies | 768–1024 |

For most production systems: text-embedding-3-small or equivalent is sufficient. Use larger models only if retrieval quality is measurably insufficient after optimization.

## Quality Evaluation

Measure RAG quality separately for retrieval and generation:

**Retrieval:**
- Precision@K: % of retrieved chunks that are relevant
- Recall@K: % of relevant chunks that were retrieved
- MRR: position of first relevant chunk

**Generation:**
- Faithfulness: are all claims in the response supported by the retrieved chunks?
- Hallucination rate: % of responses containing unsupported claims
- Answer relevance: does the response answer the query?

Target overall score > 0.75 as quality gate. If precision is low: improve chunking or add reranking. If faithfulness is low: tighten the prompt and reduce chunk count.

## Multi-Agent RAG Patterns

**RAG-Enhanced Single Agent**: the agent calls a retrieval tool as part of its decision process. Simple, easy to debug.

**Dedicated RAG Agent**: a specialist agent handles all retrieval; other agents call it. Use when multiple agents need the same knowledge base or when retrieval logic is complex.

**Domain-Partitioned RAG**: different vector stores per domain (customer data, product catalog, technical docs). Prevents cross-domain contamination. Route queries to the correct store using a classifier.

## Common Failure Modes

- **Chunk boundary artifacts**: relevant content split across two chunks, neither containing the full answer → increase chunk size or add overlap
- **Cross-domain contamination**: unrelated documents retrieved because of keyword overlap → partition by domain, add topic pre-filter, set minimum similarity threshold (e.g., 0.35)
- **LLM ignores context**: too many chunks, context window overwhelmed → reduce top-K, use compression/reranking first
- **Stale embeddings**: knowledge base updated but old embeddings still indexed → implement incremental re-indexing on document change

## Perguntas diagnósticas
1. What document types and formats are in the knowledge base?
2. Is precision or recall more critical? (legal = recall; conversational = precision)
3. What is the query volume, and is real-time retrieval latency acceptable?
4. Are there distinct domains in the knowledge base that should be separated?
5. Do responses need to cite sources (faithfulness is mandatory)?
6. What is the update frequency of the knowledge base?

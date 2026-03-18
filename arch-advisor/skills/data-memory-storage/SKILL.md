---
name: data-memory-storage
description: "Use this skill when choosing storage systems, designing the data layer, deciding between databases, or designing agent memory. Trigger when someone says 'what database should we use?', 'where do we store agent state?', 'how do we persist memory between sessions?', 'we need vector storage for embeddings', 'how do we structure session data?', 'the agent needs to remember past conversations', 'we need to store user history', 'GDPR compliance for stored data'. Also trigger for: PostgreSQL, Redis, vector DB, Chroma, Pinecone, polyglot persistence, CQRS, Event Sourcing."
---

# Data and Memory Architecture

## Polyglot Persistence: Storage by Role

Do not use a single database for everything. Match each storage need to the right technology:

| Need | Technology | When to use |
|---|---|---|
| Structured data (users, sessions, transactions) | PostgreSQL | ACID required, complex joins, audit logs |
| Session state, rate limiting, cache | Redis | Sub-second access, TTL, ephemeral |
| Embeddings, semantic search, RAG | Vector DB (Chroma/Pinecone) | Similarity queries |
| Time-series metrics | InfluxDB / TimeSeries | Dashboards, anomaly detection |
| Large binary objects | Object storage (S3) | Documents, files, exports |

## Vector Database Selection

- **< 1M vectors, self-hosted acceptable**: Chroma or pgvector (PostgreSQL extension)
- **> 10M vectors, or managed preferred**: Pinecone, Weaviate, or Qdrant
- **Cost constraint (zero infra cost)**: pgvector if already running PostgreSQL

Migration from Chroma to Pinecone is expensive (re-embedding required). Choose based on expected 12-month volume.

## Agent Memory Types

**Short-term memory (STM)**:
- Scope: current session only
- Storage: in-process memory
- Pattern: sliding window — keep last N messages that fit in context budget
- Use for: current conversation context, recent tool outputs

**Long-term memory (LTM)**:
- Scope: persistent across sessions
- Storage: vector DB
- Pattern: store summaries or key facts; retrieve by semantic similarity
- Use for: user preferences, domain knowledge, past decisions

**Episodic memory**:
- Scope: persistent
- Storage: relational DB (PostgreSQL)
- Pattern: structured records with metadata, queryable by time range, user, decision type
- Use for: auditable decision history, compliance records, feedback loops

**Semantic memory**:
- Scope: persistent
- Storage: vector DB
- Pattern: general knowledge graph or fact store
- Use for: domain knowledge that agents share, updated independently of sessions

Start simple: STM (sliding window) + LTM (vector). Add episodic only when audit trails or feedback analysis are required.

## Schema Essentials

Every production agent system needs:
- `users`: id, created_at, metadata
- `sessions`: id, user_id, started_at, ended_at, status
- `messages`: id, session_id, role, content, timestamp, tokens_used
- `tasks`: id, session_id, type, status, result, cost_usd, duration_ms
- `audit_logs`: id, actor, action, resource, timestamp, context (JSONB)

Index strategy:
- Composite index on (user_id, created_at) for history queries
- Partial index on active sessions: `WHERE status = 'active'`
- GIN index on JSONB columns for metadata search

## GDPR / LGPD Compliance Patterns

Required capabilities:
- **Soft delete**: mark as deleted, retain for legal hold, purge after retention period
- **Anonymization**: replace PII with tokens on request
- **Data export**: produce a full user data export on request
- **Retention enforcement**: automatic purge job per data category

Never hard-delete audit logs — they may be legally required. Archive them instead.

## CQRS and Event Sourcing

Use CQRS when:
- Read and write patterns are dramatically different (high-volume reads vs. low-volume writes)
- Different teams own read vs. write models

Use Event Sourcing when:
- Complete audit trail of state changes is required
- System needs replay capability (reprocess past events with new logic)
- Domain is naturally event-based (financial transactions, order lifecycle)

Warning: both patterns add significant complexity. Do not apply unless there is a specific requirement that justifies them.

## Perguntas diagnósticas
1. What is the expected data volume per entity type (messages, sessions, documents) at 1-year horizon?
2. Does the system need ACID transactions across multiple entities?
3. Is there a GDPR/LGPD requirement? Which data categories contain PII?
4. What is the required retention period for each data type?
5. Do agents need to retrieve information from past sessions, or only from the current one?
6. What are the query patterns — lookups by ID, by user, by time range, or by semantic similarity?

## Session: Technical Document Critic Agent

Date: 2026-03-13
Status: discovery-complete

### Requirements Summary

- Domain: CI/CD-invoked document quality analysis agent; receives a Markdown technical document and produces a structured critical analysis report
- Primary action: Orchestrate + generate — 4-stage pipeline (Perception → Decision → Memory → Reflection)
- Volume: Dozens per day, low concurrency, single-doc per invocation
- Latency target: Async (minutes); no downstream system waiting synchronously
- Data sources: Local Markdown files; in-memory LTM (word-overlap, no external vector store)
- Integrations: None; Claude accessed via CI&T Flow proxy (no direct API)
- Constraints: TypeScript + Node.js; Sonnet 4.6 + Haiku 4.5 via proxy; no third-party DBs or vector stores; hard budget $0.30/analysis
- Compliance: None
- Team maturity: Experienced with LLM/agent systems

### Group E — Failure, History, Priorities

- Prior attempts: None; this is the first implementation
- Consequence of wrong output: Financial loss — incorrect classification leads to rework by downstream teams
- Requirement to cut first: Tech stack diversification (e.g., multiple model providers) — would keep core pipeline intact
- Success measurement: Business areas measure error rate (incorrect classifications surfaced by downstream reviewers)

### Resolved Tensions

- **LTM enrichment vs. process-isolated invocations**: User chose LTM persistence. Consequence accepted: PipelineCheckpoint JSON file serializes LTM state after each run; warm-start reads checkpoint at process initialization. Each CI/CD invocation loads previous LTM state rather than starting cold. Reason given: "resolva a favor da LTM"
- **Hard budget $0.30 vs. report completeness**: User chose adaptive hard stop. Consequence accepted: $0.30 is the default ceiling; if score > 0.65 at budget-check time, pipeline may extend budget via `--promise-to-improve` flag and continue Reflection until threshold 0.78 is reached; if score ≤ 0.65 at hard stop, report is delivered as explicitly incomplete. Quality evaluation must be available mid-pipeline to support the score check at budget boundary. Reason given: "aceita como hard stop mas pode implementar budget adaptativo via promise to improve se score > 0.65"

### Stress Test Responses

- **Scale (10x)**: LTM in-memory breaks first — at hundreds of documents/day, accumulated LTM data would exceed viable in-process memory. This is the trigger for migrating to persistent storage (SQLite or vector store) in the next scale tier.
- **Budget pressure (50% cut to $0.15)**: First sacrifice is iteration depth — reduce the number of Reflection loops per stage, preserving stage coverage and score threshold integrity at the cost of convergence speed.
- **Future requirements (SQLite + ChromaDB)**: Classified as a possibility, not a committed requirement within 12 months. Extension points for storage are recommended but not mandatory — architecture should make storage swappable without requiring core pipeline changes.

### Phase 2 — Requirements Analysis

**Patterns:** Sequential Pipeline, Reflection Loop (Critic-Reviser), LTM + Persistent Checkpoint, STM (in-session), Strategy Binary Model Routing (Haiku 4.5 / Sonnet 4.6), Adaptive Budget Gate, Stage Checkpoint / Idempotent Execution, Circuit Breaker on proxy, Word-Overlap In-Memory RAG.

**Ambiguities:** None.

**Top 3 Risks:** (1) PipelineCheckpoint corruption — medium/medium — atomic write + fallback cold-start; (2) Budget extension slow convergence — low/medium — absolute $0.50 ceiling + oscillation detection; (3) Reflection non-convergence on pathological docs — low-medium/high — explicit `convergenceStatus` field in output.

**Constraints Impact:** TypeScript-only eliminates Python frameworks; proxy-only eliminates multi-provider fallback; no external storage limits LTM to JSON + word-overlap RAG; adaptive budget gate is first-class pipeline component.

Status: analysis-complete

### Chosen Option

**Option B — Event-Driven Pipeline com Stage Checkpoints**

Each stage emits a completion event; the PipelineOrchestrator persists stage output to CheckpointStore before invoking the next. BudgetMonitor is an independent subscriber to reflection:iteration events, evaluating score/cost and emitting budget:extend or budget:halt. ReportEmitter writes CritiqueReport with explicit convergenceStatus. Failure at any point allows resume from last completed stage checkpoint.

Status: option-chosen

Status: artifacts-generated

Status: complete

## Session: Technical-Document-Critic-Agent

Date: 2026-03-19
Status: discovery-complete

### Requirements Summary

- Domain: Technical documentation review — receives Markdown documents, produces structured critique reports with iterative quality refinement
- Primary action: Orchestrate + generate (4-layer pipeline: Perception → Decision → Memory → Reflection)
- Volume: Tens of documents/day, no concurrency. Future possibility: 1,000/day (not committed)
- Latency target: Async — minutes (30s–3min observed). No real-time requirement.
- Data sources: Local Markdown files on disk; LTM in-memory (same-process accumulation across documents in a single run)
- Integrations: None. CI/CD integration is at the invocation layer, outside agent scope.
- Constraints: TypeScript + Node.js; Claude Sonnet 4.6 (default) + Haiku 4.5 (fast/cheap); no external vector store; no database; proxy-only LLM access (CI&T Flow)
- Compliance: None. Structured logging for internal observability only.
- Team maturity: Experienced — learning objective: Reflection Loop, LTM, multi-layer pipeline, design patterns (Strategy, CoR, State Machine)

### Internal Flags (silent)

- `hybrid-decision-candidate = false` (primary action = orchestrate, not classify/transact/route)
- `hitl-candidate = false` (output = Markdown report; no real-world action triggered)
- `saga-candidate = false` (pipeline is read-only; no multi-step state mutations requiring rollback)
- `event-sourcing-candidate = false` (no time-travel audit requirement)

### Discovery Follow-ups Fired

- **Group B mandatory**: Caller = CI/CD pipeline (external system) and arrival pattern not explicitly stated → asked. Answer: bursty — triggered by merge/push events, not steady throughout the day.
- **Group C**: No follow-up fired (hitl-candidate=false, no legacy systems, no PII)
- **Group D**: No follow-up fired (hybrid-decision-candidate=false, no LLM-only constraint declared)
- **Group E Q17**: No multi-step rollback need (pipeline is read-only). saga-candidate=false.
- **Group E Q18**: No time-travel audit requirement. event-sourcing-candidate=false.

### Resolved Tensions

- **LTM in-memory vs. cross-run continuity**: User chose simplicity. Consequence accepted: LTM only accumulates within a single process run; each CI/CD job starts with empty LTM; value limited to batches with ≥2 docs of the same domain in the same job. For cross-run persistence, LTM would need disk serialization. Reason given: "Aceito conscientemente. Foco nos padrões, não na infraestrutura. Interface AnalysisLTM suporta troca sem alterar o pipeline."
- **Sequential LLM calls vs. budget-bounded quality**: User chose budget enforcement. Consequence accepted: Reflection Loop may stop before overallScore ≥ 0.78 if $0.30 budget is reached; quality is not guaranteed on every run. Reason given: "Aceito. O loop tem budget e MAX_ITERATIONS como válvulas de segurança."

### Stress Test Responses

- **10x scale (1,000 docs/day)**: LTM in-memory breaks first — unbounded growth, no eviction policy, no concurrency support in single-process design. Sequential pipeline becomes a throughput bottleneck.
- **Budget −50% ($0.15/analysis)**: Sacrifice iteration depth — reduce MAX_ITERATIONS from 3 to 1–2; route reviser calls to Haiku 4.5 instead of Sonnet 4.6.
- **Future requirements**: 1,000 docs/day = possibility, not committed. ChromaDB/SQLite/multi-format input = possibilities, not within 12 months. → Extension points: recommended, not mandatory.


---

## Phase 2 — Requirements Analysis (Technical-Document-Critic-Agent)

### Ambiguities Resolved

- A1: Long-lived within session (DocumentAnalysisAgent instanciado uma vez em main(), loop reutiliza instância). Efêmero entre processos.
- A2: Três condições de parada em ordem: isAcceptable (overallScore >= 0.78) → budget >= $0.30 → MAX_ITERATIONS = 3
- A3: Sem interface formal de adapter. loadDocument(filePath): string + chunkDocument(content): Chunk[]. Refatoração para Strategy seria necessária para suportar outros formatos.
- A4: Post-call via response.usage.input_tokens e response.usage.output_tokens com preços fixos hard-coded.
- A5: Schema fixo com conteúdo dinâmico. Seções predefinidas. Type/domain influenciam conteúdo via focusAreas e ltmContext.

### Patterns Needed

- Single Agent with Multi-Layer Pipeline (Perception → Decision → Memory → Reflection)
- Reflection Loop / Planner-Executor-Critic (Critic + Reviser iterativo, threshold + budget + maxIterations)
- STM (classification context forward-pass within pipeline run)
- LTM in-process episodic (domain-indexed, scoped to process lifetime)
- Budget-Controlled Iteration ($0.30 hard ceiling, post-call enforcement)
- Complexity-based LLM Routing (Sonnet 4.6 vs. Haiku 4.5 per stage + budget residual trigger)
- LLM Response Caching (hard constraint + deterministic input, limited by ltmContext injection)
- Feedback Loop with Regression Detection (overallScore baseline + version-correlated eval)

### Top 3 Risks

1. LTM value degradation in single-doc CI/CD jobs (médio/médio)
2. Silent quality regression without external eval baseline (médio/médio-alto)
3. Budget-quality inconsistency when stoppedBy=costBudget (médio/médio)

### Chosen Architecture: Option B — Single-Agent Pipeline with Reflection Loop

Status: option-chosen

### Pattern Deepening (Phase 3.5)

Blocks triggered (4 of 12):
- Planner-Executor-Critic (Reflection Loop with threshold, maxIter, budget stop)
- Complexity-based LLM Routing (Sonnet/Haiku per stage + budget residual trigger)
- LLM Response Caching (hard constraint; limited by dynamic ltmContext injection)
- Feedback Loop with Regression Detection (overallScore baseline, version-correlated)

Blocks NOT triggered (8 of 12):
- Hybrid Decision Engine (hybrid-decision-candidate=false)
- Voting + Arbiter (single-agent pipeline)
- Saga with Compensation (read-only pipeline, no rollback needed)
- HITL + Checkpointing (no human approval in loop)
- Bulkhead (single pool, no criticality domain split)
- Anti-Corruption Layer (no legacy systems)
- Strangler Fig (no migration scope)
- Batch Processing (mandatory follow-up fired before batch follow-up; bursty arrival but no batch inference)

Status: artifacts-generated

## Session: Medical-Diagnosis-Voting-Arbiter

Date: 2026-03-19
Status: discovery-complete

### Requirements Summary

- Domain: Medical diagnosis decision support — 3 specialist LLM agents (clinical, radiologist, pharmacology) analyze the same case in parallel; a cascade of voting strategies converges to a diagnosis; an LLM arbiter resolves unresolvable conflicts; cases below confidence threshold are escalated to human review
- Primary action: classify (diagnose = classify medical case into a diagnosis with confidence score)
- Volume: 200–500 cases/day in production; bursty pattern aligned with medical rounds (07h–09h, 19h–21h); study: 20 cases batch
- Latency target: Near-real-time — <30s per diagnosis. Human reviewer waits for result before consulting patient.
- Data sources: Clinical case payload (symptoms, history, test results); no external DB currently; future: EMR integration (Epic) in 12 months
- Integrations: None currently. EMR integration = confirmed upcoming requirement (12 months).
- Constraints: TypeScript + Node.js; LLM via CI&T Flow proxy (Haiku 4.5 for specialists, Sonnet 4.6 for arbiter); no external vector store or DB in current scope
- Compliance: Medical data = regulated (HIPAA/health data equivalent); audit trail per decision is regulatory requirement; full event history for time-travel audit required
- Team maturity: Experienced — Principal Architect study track; explicit objective: master Voting+Arbiter, cascade strategies, multi-agent consensus patterns

### Internal Flags (silent)

- `hybrid-decision-candidate = true` (primary action = classify; 50–70% of cases solvable by deterministic voting strategies)
- `hitl-candidate = true` (output = medical diagnosis with real-world clinical consequences; async human approval for insufficient-confidence cases confirmed)
- `saga-candidate = true` (future EMR integration: diagnosis committed to EMR then revised needs rollback; eventual consistency acceptable)
- `event-sourcing-candidate = true` (regulatory requirement to reconstruct exact state at any past point in time)

### Discovery Follow-ups Fired

- Group B mandatory: Caller = hospital system (external) + arrival pattern not stated → asked. Answer: bursty — aligned with medical rounds (07h–09h, 19h–21h)
- Group C priority HITL: hitl-candidate=true → asked. Answer: async HITL for insufficient-confidence cases (threshold < 0.5 in production); workflow pauses, doctor reviews asynchronously, TTL = 4 hours
- Group D priority Hybrid DE: hybrid-decision-candidate=true → asked. Answer: ~50–60% clear-consensus/simple-majority (deterministic voting); ~40–50% ambiguous (need arbiter LLM)

### Resolved Tensions

- **Confidence threshold vs. coverage**: User chose conservative threshold (≥0.5 in production). Consequence accepted: HITL workflow with durable checkpointing is mandatory; TTL = 4h; doctor reviews asynchronously. Reason given: "falso negativo (diagnóstico errado entregue) é pior que custo de revisão humana."
- **Terminology normalization vs. implementation complexity**: User chose robust normalization. Consequence accepted: semantic normalization layer (embedding similarity) added before voting; +200–500ms latency. Reason given: "Falsos conflitos por sinônimos desperdiçam custo de arbiter e produzem ruído no audit trail."

### Stress Test Responses

- **10x scale (2,000–5,000/day)**: Single-process + Promise.allSettled loses cases on process crash during burst; in-memory normalizer and AuditLog don't survive multi-worker concurrency.
- **Budget −50% (~$0.025/case)**: Sacrifice arbiter output verbosity (shorter reasoning) or route low-confidence arbiter calls to Haiku.
- **Future requirements**: EMR integration = confirmed 12 months. HITL workflow with reviewer UI = confirmed 12 months. SNOMED-CT ontology = possible, not committed.


---

## Phase 2 — Requirements Analysis (Medical-Diagnosis-Voting-Arbiter)

### Ambiguities Resolved

- None after discovery — all critical parameters were available from the exercise implementation data.

### Patterns Needed

- Multi-Agent Parallel Execution (3 specialists via Promise.allSettled)
- Cascade Voting Strategy (majority → weighted → threshold → arbiter)
- Terminology Normalization (embedding-similarity, pre-voting canonicalization)
- Planner-Executor-Critic variant: Arbiter as Critic for unresolvable cases
- Human-in-the-Loop with Checkpointing (async, TTL = 4h, durable store)
- Saga with Compensation (future EMR integration, sagaId schema required now)
- Event Sourcing / Append-only AuditEventStore (regulatory time-travel audit)
- Complexity-based LLM Routing (Haiku 4.5 specialists / Sonnet 4.6 arbiter)
- Bulkhead (critical diagnosis pool / non-critical analytics pool)
- Feedback Loop with Regression Detection (accuracy baseline, version-correlated)

### Top 3 Risks

1. **Arbiter rate drift** (medium/high) — normalization failure or specialist prompt drift inflates arbiter invocation rate above 50%, degrading cost efficiency. Mitigation: monitor arbiter rate as a quality proxy; alert if >50% sustained over 7 days.
2. **HITL checkpoint loss on process restart** (medium/high) — MemorySaver in production silently loses pending patient cases. Mitigation: durable checkpoint store (Cosmos DB) mandatory before production deploy.
3. **Terminology normalization latency** (low/medium) — embedding similarity normalization adds +200–500ms; if embedding model has cold start or latency spikes, P95 target (<30s) is at risk. Mitigation: pre-warm embedding model, monitor normalizer latency separately.

### Chosen Architecture: Option B — Multi-Agent Voting+Arbiter with Cascade

Status: option-chosen

---

### Pattern Deepening (Phase 3.5)

Blocks triggered (7 of 12):
- Hybrid Decision Engine (hybrid-decision-candidate=true; cascade IS the hybrid engine — deterministic voting is the rule path, arbiter LLM is the fallback)
- Voting + Arbiter (3 specialists + cascade + full-reasoning arbiter)
- Saga with Compensation (Q17 confirmed future EMR rollback; sagaId schema required now)
- Human-in-the-Loop with Checkpointing (Group C HITL confirmed async, TTL=4h, durable store required)
- Complexity-based LLM Routing (Haiku specialists / Sonnet arbiter)
- Bulkhead (critical diagnosis pool / non-critical analytics pool during burst)
- Feedback Loop with Regression Detection (accuracy baseline 92%; alert at 87.4%; 20-case eval suite)

Blocks NOT triggered (5 of 12):
- Planner-Executor-Critic (no reflection loop; arbiter is a single-pass critic, not iterative PEC)
- LLM Response Caching (clinical cases are unique; deterministic repeat queries not expected)
- Anti-Corruption Layer (no legacy systems currently; future EMR ACL deferred to EMR integration ADR)
- Strangler Fig (no migration scope)
- Batch Processing (near-real-time <30s requirement incompatible with batch deferral)

Status: artifacts-generated

Artifacts saved to: .claude/arch-outputs/medical-diagnosis-voting-arbiter/
- container-diagram.md
- adr-001-multi-agent-voting-arbiter-cascade.md
- decision-matrix.md
- nfr-checklist.md


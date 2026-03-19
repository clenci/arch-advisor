# Decision Matrix — Medical Diagnosis Voting+Arbiter

## Criteria

Criteria selected to reflect the stated requirements and resolved tensions: medical reliability, budget sensitivity, HITL/human-oversight compatibility, regulatory audit compliance, and latency target (<30s near-real-time).

| Criterion | Weight | Option A: Single LLM Classifier | Option B: Multi-Agent Voting+Arbiter | Option C: Distributed Multi-Agent + Event Store | Notes |
|---|---|---|---|---|---|
| **Diagnosis reliability** | 30% | 4 | 9 | 9 | A: single model, no independent perspectives, confidence poorly calibrated for medical HITL gate — score 4: fails on ambiguous cases where specialist domain separation matters; B: 3 independent specialists + cascade + arbiter + HITL gate — score 9: exercise validated 70% consensus + 30% arbiter with no false certainty; C: same B + persistent LTM for cross-case learning — score 9: marginal gain at current volume |
| **Cost per case** | 25% | 9 | 7 | 4 | A: single Sonnet call ~$0.003–0.005 per case — score 9; B: weighted avg $0.0084–$0.0148/case depending on path (exercise validated) — score 7: controlled, no hard ceiling breach; C: infrastructure cost (Cosmos DB + Service Bus + distributed workers) adds fixed overhead independent of volume — score 4: not justified at 200–500/day |
| **HITL / human-oversight compatibility** | 20% | 4 | 9 | 9 | A: single-model confidence is weakly calibrated; HITL gate would fire unpredictably or not at all — score 4; B: cascade produces calibrated confidence; HITL fires precisely at < 0.5 threshold; TTL = 4h; durable checkpoint — score 9; C: same as B, distributed — score 9 |
| **Regulatory audit compliance** | 15% | 5 | 8 | 10 | A: can log single call; no cascade trace, no specialist reasoning chain; limited time-travel capability — score 5; B: AuditEventStore with full cascade events, sagaId, specialist reasoning; time-travel via event replay — score 8: all regulatory requirements met; C: persistent event store + persistent LTM + saga state journal — score 10: adds cross-run auditability not required currently |
| **Latency on critical path** | 10% | 10 | 7 | 5 | A: 1 LLM call ~3–5s — score 10; B: parallel specialists ~5–8s + voting + optional arbiter; P95 <30s met with margin — score 7; C: distributed coordination + queue latency + inter-service calls add ~5–10s overhead — score 5: P95 <30s at risk on arbiter path |

## Score Breakdown

| Option | Reliability (30%) | Cost (25%) | HITL (20%) | Audit (15%) | Latency (10%) | **Total** |
|---|---|---|---|---|---|---|
| A — Single LLM Classifier | 1.20 | 2.25 | 0.80 | 0.75 | 1.00 | **6.00** |
| B — Multi-Agent Voting+Arbiter | 2.70 | 1.75 | 1.80 | 1.20 | 0.70 | **8.15** |
| C — Distributed + Event Store | 2.70 | 1.00 | 1.80 | 1.50 | 0.50 | **7.50** |

## Recommendation

**Option B** — Multi-Agent Voting+Arbiter with Cascade — is the clear winner at 8.15/10. It is the only option that:
1. Reliably achieves the medical reliability requirement through independent specialist perspectives and calibrated cascade consensus
2. Maintains controlled cost (~$0.0084–$0.0148/case) without hard ceiling risk
3. Provides a well-calibrated HITL gate (confidence < 0.5 → durable async checkpoint, TTL = 4h)
4. Satisfies the regulatory time-travel audit requirement via AuditEventStore with event sourcing
5. Meets the <30s near-real-time latency target (P95 <30s per exercise baseline)

Option A fails on reliability and HITL calibration — unacceptable for medical context. Option C would be the right architecture when daily volume reaches 2,000+ cases/day and concurrent processing is needed; the current in-process architecture must extend toward it (sagaId, HITL interface, AuditEventStore abstraction already designed for this transition).

## Resolved Tensions Reflected in Scoring

- **Conservative confidence threshold (≥0.5)**: inflated HITL weight to 20% — the HITL mechanism is a core architectural requirement, not an optional feature; this differentiated B from A decisively.
- **Terminology normalization**: reflected in Option B's reliability score (9) — without normalization, string-comparison failures would inflate arbiter rate and degrade the cascade's cost-efficiency advantage.

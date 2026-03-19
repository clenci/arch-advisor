# Decision Matrix — Technical-Document-Critic-Agent

## Criteria

Criteria selected to reflect the stated requirements and resolved tensions: budget hard constraint, async latency acceptance, zero external infrastructure, LTM ephemeral trade-off, and quality threshold.

| Criterion | Weight | Option A: Single-Pass | Option B: Pipeline + Reflection | Option C: Multi-Agent + Persistent LTM | Notes |
|---|---|---|---|---|---|
| **Budget adherence ($0.30 ceiling)** | 25% | 9 | 8 | 5 | A: single call ~$0.03–0.05, well under ceiling; B: 4–7 calls, $0.09–0.15 with routing, controlled; C: inter-agent handoffs add 2–3 extra calls, risk pushing past ceiling on long docs — score 5: ceiling can be breached without careful accounting |
| **Quality threshold achievability (overallScore ≥ 0.78)** | 25% | 3 | 9 | 8 | A: single pass cannot reliably meet 0.78 across all document types — score 3: only achieves threshold on well-structured short docs; B: iterative Critic+Reviser loop is the mechanism designed for this threshold — score 9; C: adds parallel critique paths but at higher cost, marginal quality gain over B |
| **Zero external infrastructure** | 20% | 10 | 9 | 2 | A/B: pure Node.js, no external dependencies — A=10 (no in-memory LTM even); B=9 (in-memory LTM is still in-process); C: requires SQLite or Redis for shared LTM, vector store for semantic retrieval — score 2: contradicts stated "zero dependencies beyond LLM" constraint |
| **LTM value within CI/CD job** | 15% | 1 | 7 | 5 | A: no LTM at all — score 1; B: in-memory LTM accumulates across docs in same run — score 7 (full value when ≥2 docs/job); C: persistent LTM survives across runs — score 5 (but rejected due to infrastructure constraint, so theoretical) |
| **Pipeline layer testability** | 10% | 4 | 9 | 7 | A: single prompt — only E2E testable; B: 4 independent layers, each mockable via DI — score 9 (Perception+Decision are deterministic, unit-testable); C: testable but inter-agent contracts add integration surface |
| **Latency predictability** | 5% | 10 | 6 | 4 | A: 1 LLM call, deterministic ~3–5s; B: 4–7 calls, 30s–3min non-deterministic (acceptable given async requirement) — score 6; C: parallel agent paths can reduce wall-clock but add coordination overhead — score 4 |
| **Weighted Total** | **100%** | **5.9** | **8.4** | **4.8** | |

## Score Breakdown

| Option | Budget (25%) | Quality (25%) | Infra (20%) | LTM (15%) | Test (10%) | Latency (5%) | **Total** |
|---|---|---|---|---|---|---|---|
| A — Single-Pass | 2.25 | 0.75 | 2.00 | 0.15 | 0.40 | 0.50 | **5.90** |
| B — Pipeline + Reflection | 2.00 | 2.25 | 1.80 | 1.05 | 0.90 | 0.30 | **8.35** |
| C — Multi-Agent + Persistent LTM | 1.25 | 2.00 | 0.40 | 0.75 | 0.70 | 0.20 | **4.75** |

## Recommendation

**Option B** — the pipeline with Reflection Loop — is the clear winner at 8.35/10. It is the only option that:
1. Reliably achieves the quality threshold (0.78) through iterative refinement
2. Stays within the $0.30 budget with routing (Classifier → Haiku, Reviser → Haiku under pressure)
3. Maintains zero external infrastructure (in-memory LTM is in-process)
4. Aligns with both resolved tensions: budget enforcement accepted as the stop condition, LTM simplicity accepted over cross-run persistence

Option A would undercut on quality. Option C would violate the zero-infrastructure constraint and risk exceeding the budget ceiling.

# Changelog — arch-advisor

## 4.3.0

- Phase 3.6 — `agent-internal-architecture` trigger: expanded to cover VotingCoordinator, cascade strategy with multiple deterministic stages, and any component with a multi-stage deterministic pipeline — not only single agents with reflection loops or explicit state machines
- Phase 5 — deepening menu `Agent internal design` criterion: same expansion applied — now includes cascade strategies and multi-stage deterministic coordinators as qualifying conditions
- CLAUDE.md: updated to v4.2.0 state; resolved lacunas marked; single remanescente lacuna (5c) documented; scores table added; casos-de-referencia/ referenced

## 4.2.0

- Discovery — Group A: added silent internal flags (`hybrid-decision-candidate`, `hitl-candidate`) seeded from primary action analysis; used as triggers for targeted follow-ups in Groups C and D
- Discovery — Group B: added conditional follow-up for batch processing viability (fires when latency is async, arrival is bursty, or caller is a batch/upstream job)
- Discovery — Group C: added priority HITL follow-up (fires when `hitl-candidate = true`); distinguishes sync vs. async approval — async approval triggers HITL+Checkpointing pattern in Phase 3.5
- Discovery — Group D: added priority Hybrid Decision Engine follow-up (fires when `hybrid-decision-candidate = true`); probes fraction of obvious/deterministic cases to determine whether Rule Engine → LLM Reasoner → Heuristic Validator is warranted
- Discovery — Group E: added questions 17 (Saga/compensation — multi-step rollback need) and 18 (Event Sourcing — time-travel audit requirement)
- Phase 3.5 — Pattern Deepening (NEW): visible phase presented to user after architecture option is chosen; scans discovery answers and chosen option for 12 pattern triggers; invokes `arch-advisor:pattern-deepening` skill; produces per-pattern blocks with "why this system needs it," concrete design decisions, critical implementation constraint, and artifact handoff note; appends to arch-session.md
- Phase 3.6 — Domain Deepening: renamed from previous Phase 3.5; behavior unchanged (silent, pre-artifact, up to 2 domain skills)
- New skill `arch-advisor:pattern-deepening`: 12 implementation-level pattern blocks covering Hybrid Decision Engine, Planner-Executor-Critic, Voting + Arbiter, Saga with Compensation, Human-in-the-Loop with Checkpointing, Complexity-based LLM Routing, LLM Response Caching, Bulkhead, Anti-Corruption Layer, Strangler Fig, Batch Processing, Feedback Loop with Regression Detection

## 4.1.0

- Group B follow-up: replaced conditional `"if any answer is underspecified"` with an explicit mandatory check — if the caller is an external system or automated process and the arrival pattern (steady vs. bursty) was not explicitly stated, the follow-up is required regardless of how detailed the answer was
- Phase 3 — Option C: must now introduce at least one infrastructure component not present in Option B (durable queue, external store, separate worker process); prevents two options of similar complexity from being proposed as different tiers
- Phase 3.5: `agent-internal-architecture` trigger made explicit — invoked whenever the chosen architecture includes a Reflection Loop, multi-stage internal pipeline, STM/LTM layers, explicit state machine, or budget-controlled iteration
- Phase 5 deepening menu: added per-option inclusion criteria to replace the ambiguous "show only the options whose domain is present" instruction; `agent-internal-architecture` now has an explicit condition covering non-trivial single-agent internal structure
- Language consistency: added behavioral guideline to detect the user's language on the first response and maintain it throughout the session; technical terms (pattern names, C4 notation, skill names, field names) are never translated
- Validated by comparative execution: Group B fix captured bursty/event-driven pattern that propagated into C4, Decision Matrix, and ADR; `agent-internal-architecture` deepening produced Rule Engine pre-LLM, two-reviser pattern, and BudgetMonitor 4-state machine — content absent in all previous versions

## 4.0.0

- Group E discovery questions: failure history, blast radius, requirement to cut, external success measurement
- Phase 1.5 — Tension Resolution: each tension presented individually with consequence framing; user choice recorded and carried forward into Phase 2, Phase 3, and ADR justification
- Phase 1.6 — Requirements Stress Test: 3 questions (10x scale, 50% budget pressure, future requirements qualification); answers calibrate Option C thresholds and NFR extension points
- Phase 1.7 — Summary Review: structured session summary presented to user with 2 meta-questions before analysis
- Phase 3.5 — Domain Deepening (silent, pre-artifact): invokes up to 2 domain skills based on chosen architecture before Phase 4
- Phase 4: added explicit invocation of `testing-quality` and conditional invocation of `security-governance`
- Phase 5: artifact review separated from deepening menu; deepening menu maps to domain skills and produces `deepening-[topic].md` files
- NFR template: added Extensibility and Security sections; 1–10 scoring scale with mandatory justification for scores 8–10 and 1–3
- ADR template: "When to Reconsider" requires 2–3 measurable conditions derived from session data
- Follow-up examples in Group B generalized: removed CI/CD-specific example, replaced with caller-type and event-trigger patterns
- NFR Observability: `span per logical processing unit` instead of pipeline-specific terminology

## 3.0.0

- All phases executed directly by the main Claude instance (no agent delegation)
- Phase 4: explicit invocation of `architecture-documentation` and `observability-slo` via Skill tool
- Semantic hints in Phase 2 and Phase 3 to prime skill auto-invocation (later removed in 4.0.0 — no measurable impact observed)

## 2.0.0

- All phases executed directly by the main Claude instance
- Tensions surfaced to user as "Tensions and Gaps" section; clarifications collected before analysis
- Skills auto-invoked by semantic context only (no explicit invocations)

## 1.0.0

- Discovery executed by main command; analysis, proposal, and artifact generation delegated to specialized agents (requirements-analyst, pattern-matcher, artifact-generator)

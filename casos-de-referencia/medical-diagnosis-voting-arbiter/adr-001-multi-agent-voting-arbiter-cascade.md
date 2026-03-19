# ADR-001 — Multi-Agent Voting+Arbiter with Cascade Consensus Strategy

**Status:** Proposed
**Date:** 2026-03-19

## Context

The system must receive a clinical case (symptoms, history, test results) and produce a structured diagnosis with confidence score. The primary design tensions are: (1) medical diagnosis reliability requires independent specialist perspectives to mitigate single-model bias, but each additional agent adds LLM cost and latency; (2) a conservative confidence threshold (≥0.5) maximizes patient safety but mandates a durable HITL workflow for borderline cases; (3) the regulatory requirement to reconstruct exact system state at any past point in time demands append-only event sourcing, which adds storage and write overhead. Three structural alternatives were considered: a single LLM classifier (one call), the multi-agent voting+arbiter cascade (Option B), and a fully distributed multi-agent system with persistent LTM and external event store (Option C).

## Decision

Implement as three independent specialist agents (ClinicalSpecialist, RadiologistSpecialist, PharmacologySpecialist) executing in parallel via Promise.allSettled, with outputs canonicalized by a TerminologyNormalizer, resolved by a cascade of deterministic voting strategies, and escalated to a Sonnet 4.6 ArbiterAgent only when the deterministic cascade fails. Cases where even the arbiter confidence is below 0.5 are escalated to async human review (HITL) with a 4-hour TTL.

## Justification

- **Three independent specialists over single classifier**: A single LLM call cannot provide the independent clinical, radiological, and pharmacological perspectives required for reliable medical diagnosis. The exercise validated that weighted voting across 3 domains consistently produces higher-confidence decisions than any single specialist alone; arbiter is only called when genuine disagreement exists (30% of cases in baseline).
- **Cascade order preserves cost efficiency**: The deterministic cascade (majority → weighted → threshold) resolves ~60–70% of cases without invoking the Sonnet arbiter. Exercise data confirmed $0.0084/case on the voting path vs. $0.0148/case on the arbiter path. The cascade ensures the more expensive path fires only when necessary.
- **Terminology normalization before voting**: The resolved tension (terminology normalization vs. implementation complexity) accepted +200–500ms latency in exchange for eliminating false conflicts from synonym divergence. The exercise documented the failure mode: string comparison sent a clear-consensus IAM case to the arbiter unnecessarily, wasting cost and adding noise to the audit trail. Embedding-similarity normalization is the structural fix.
- **Conservative confidence threshold (≥0.5) with durable HITL**: The resolved tension (confidence threshold vs. coverage) accepted that false negative (wrong diagnosis delivered confidently) is worse than the cost of human review. HITL with TTL = 4h is the mandatory backstop. Durable checkpoint storage (Azure Cosmos DB in production) is non-negotiable — MemorySaver does not survive process restart and would silently lose pending patient cases.
- **Event-sourced AuditEventStore**: The regulatory requirement (Group E Q18) to reconstruct exact system state at any past point in time requires append-only event sourcing. Every pipeline transition (DiagnosisRequested, SpecialistCompleted, VotingResolved, ArbiterInvoked, HITLCreated, HITLResumed, DiagnosisCommitted) is an immutable event with sagaId for full saga history reconstruction.
- **sagaId on every diagnosis record**: Future EMR integration (Epic, 12 months) will require Saga-with-Compensation when a diagnosis committed to EMR is revised. The sagaId must be present in the current diagnosis record schema now to avoid a breaking schema migration later.

## Consequences

**Positive:**
- Independent specialist perspectives reduce single-model bias — reliability exceeds single-LLM classifier for ambiguous medical cases
- Cost efficiency preserved: 60–70% of cases resolved without Sonnet arbiter (~$0.0084/case vs. $0.0148/case on arbiter path)
- HITL gate provides hard safety floor — no diagnosis below 0.5 confidence is delivered without doctor review
- AuditEventStore provides full regulatory compliance: time-travel audit, immutable event history, sagaId correlation
- sagaId in diagnosis record schema enables future EMR Saga integration without breaking changes

**Negative:**
- Latency is non-deterministic: P50 ~8–12s (parallel specialists + voting), P95 ~25–30s (arbiter path); bursty arrival pattern (medical rounds 07h–09h, 19h–21h) requires bulkhead to protect diagnosis pool
- TerminologyNormalizer adds +200–500ms latency on every request (accepted trade-off)
- HITL checkpoint store requires durable infrastructure in production (Cosmos DB) — single-process in-memory store is only acceptable for development
- 30% arbiter invocation rate means 30% of cases use Sonnet — if arbiter rate drifts above 50%, the normalization layer or specialist prompts need recalibration
- In-process Promise.allSettled does not survive process crash during a burst — confirmed as the 10x-scale failure mode; requires queue-backed workers at 2,000–5,000 cases/day

## Alternatives Rejected

**Single LLM Classifier (Option A)**: rejected because a single model call cannot simulate independent clinical + radiological + pharmacological reasoning; confidence scores from a single model are poorly calibrated for HITL gate decisions; and there is no cascade trace to satisfy the regulatory audit requirement. Saves cost but fails the reliability and compliance requirements for medical context.

**Distributed Multi-Agent + Persistent LTM + External Event Store (Option C)**: rejected because the current volume (200–500 cases/day, no concurrency requirement) does not justify the operational overhead of distributed workers, persistent LTM infrastructure, and external event store. The in-process Promise.allSettled pipeline is sufficient. Option C is the target architecture when volume reaches 2,000+ cases/day or concurrent case batches are introduced — the current architecture must extend toward it without requiring a rewrite (sagaId schema, HITL interface, AuditEventStore abstraction all enable this).

**Synchronous Single-Agent with Sequential Specialists**: rejected because sequential specialist calls (3 × ~4–6s) would produce 12–18s baseline latency, approaching the <30s near-real-time target with no headroom for arbiter or HITL. Parallel execution (Promise.allSettled) brings specialist latency to the slowest single call (~4–6s).

## When to Reconsider

- If daily volume exceeds 1,000 cases/day or concurrent case batches are introduced: promote in-process Promise.allSettled to a durable queue (Azure Service Bus) with separate diagnosis workers and shared checkpoint state in Cosmos DB — in-memory processing cannot be shared across concurrent Node.js processes.
- If arbiter invocation rate exceeds 50% sustainedly over a 7-day window: the TerminologyNormalizer or specialist prompts are drifting; recalibrate before scaling, not after — arbiter rate is the diagnostic signal for normalization quality.
- If EMR integration (Epic) goes live: implement the SagaCoordinator with compensation actions (retract_emr_entry, notify_care_team_of_revision) using the existing sagaId on each diagnosis record; checkpoint store already handles HITL suspension; extend it for saga state persistence.
- If diagnosis accuracy baseline drops below 87.4% (95% of the 92% baseline) after a model or prompt update: block deployment and recalibrate — do not accept a degraded baseline as the new normal.

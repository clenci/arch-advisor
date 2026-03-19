# ADR-001 — Single-Agent Pipeline with Budget-Controlled Reflection Loop

**Status:** Proposed
**Date:** 2026-03-19

## Context

The system must receive a Markdown technical document and produce a structured critique report covering depth, completeness, clarity, and actionability. The primary design tensions are: (1) the $0.30/analysis hard budget ceiling constrains the number of LLM calls, but quality requires iterative refinement (overallScore ≥ 0.78 threshold); (2) the system is invoked as an ephemeral CI/CD job, which means long-term memory must be scoped to the process lifetime or abandoned for the initial version. The team chose to accept LTM ephemerality in favor of focusing on the internal pipeline patterns (Reflection Loop, STM/LTM, State Machine). Three structural alternatives were considered: a single-agent sequential pipeline, a multi-agent orchestrator+specialists pattern, and a flat single-pass LLM call.

## Decision

Implement as a single agent with a four-layer internal pipeline (Perception → Decision → Memory → Reflection), where the Reflection stage runs a budget-controlled Planner-Executor-Critic loop with a maximum of 3 iterations and a $0.30 ceiling.

## Justification

- **Single-agent over multi-agent**: volume is tens of documents/day with no concurrency requirement — the operational overhead of orchestrating specialized agents (inter-agent communication, failure propagation, partial result coordination) is not justified for this load profile; a single agent covers the full pipeline in one process
- **Reflection Loop over single-pass generation**: the explicit quality requirement (overallScore ≥ 0.78) cannot be reliably met in a single generation pass; the Critic + Reviser loop allows targeted corrections without regenerating the full report from scratch, reducing cost per iteration
- **Budget enforcement as stop condition**: the $0.30 hard ceiling (resolved tension: budget enforcement accepted) is enforced post-call via `response.usage` token counting; three ordered stop conditions (threshold / costBudget / maxIterations) prevent runaway costs while allowing early termination when quality is met before max iterations
- **In-memory LTM accepted**: the resolved tension (LTM simplicity vs. cross-run continuity) explicitly accepted that LTM value is scoped to same-job multi-document batches; the `AnalysisLTM` interface supports later promotion to persistent storage without changing the pipeline contract
- **Haiku 4.5 for classification + Reviser routing**: the Classifier performs a bounded classification task (document type + domain) where Haiku's capability is sufficient; routing the Reviser to Haiku under budget pressure (>70% consumed) reduces per-iteration cost by ~10× without sacrificing report generation quality

## Consequences

**Positive:**
- Zero external infrastructure dependencies — runs as a standalone Node.js process with no vector store, no database, no queue
- Budget is deterministically enforced — no risk of cost overruns beyond $0.30
- Early termination when threshold is met reduces average cost below the ceiling ($0.09–$0.15 observed)
- Pipeline layers are independently testable (deterministic components in Perception and Decision can be unit-tested without LLM)
- `AnalysisLTM` interface enables storage promotion without pipeline refactoring

**Negative:**
- Latency is non-deterministic: bounded by `maxIterations × per-iteration latency` (~30s–3min); cannot guarantee a specific P95 within that range
- LTM resets on each CI/CD job invocation — for single-document jobs, LTM provides zero value; full value only when ≥2 documents of the same domain are processed in the same run
- Perception stage has no format adapter — adding PDF/URL/HTML requires refactoring `perception.ts` to a Strategy pattern (currently no `SourceLoader` interface)
- Self-validation bias in Critic: using Sonnet 4.6 as both Generator and Critic means the Critic tends to approve its own output; risk of inflated overallScore without external validation
- `stoppedBy: "costBudget"` means quality is not guaranteed on every run — consumer (CI/CD pipeline) must handle and log this condition

## Alternatives Rejected

**Multi-agent orchestrator + specialists**: rejected because volume (tens/day, no concurrency) and cost constraint ($0.30/analysis) cannot absorb the overhead of inter-agent communication and coordination; each additional agent adds at least one extra LLM call for handoff, pushing the budget boundary on already-tight margins.

**Flat single-pass LLM generation**: rejected because a single generation pass for technical critique cannot reliably produce overallScore ≥ 0.78 across all document types and domains; the iterative refinement is a core quality mechanism, not an optimization.

**Persistent LTM with SQLite**: rejected for this version because the learning objective was to implement and understand LTM patterns, not storage infrastructure; the `AnalysisLTM` interface was designed to make this upgrade non-breaking.

## When to Reconsider

- If daily volume exceeds 500 documents or concurrent jobs are introduced: promote the in-process pipeline to a durable queue-backed worker (Bull/BullMQ) with shared LTM in Redis — in-memory LTM cannot be shared across concurrent Node.js processes
- If `stoppedBy: "costBudget"` accounts for more than 20% of runs: either increase the budget ceiling or reduce MAX_ITERATIONS to 2 and route all Reviser calls to Haiku 4.5 to preserve iteration capacity within the existing budget
- If regression rate (overallScore below baseline × 0.95) exceeds 10% of eval runs after a model or prompt change: recalibrate the acceptableScore threshold — the current value (0.78) may be miscalibrated for the updated model

# ADR-001 — Event-Driven Pipeline with Stage Checkpoints

**Status:** Proposed
**Date:** 2026-03-13

## Context

The Technical Document Critic Agent runs as a single-process CI/CD invocation executing 4 sequential stages (Perception → Decision → Memory → Reflection). Two resolved architectural tensions drive the primary structural choice: (1) LTM must persist across process invocations via an atomically-written PipelineCheckpoint, because a cold LTM on each run would make the Memory stage a no-op; (2) the adaptive budget gate must evaluate the Reflection score independently of the critique logic, because combining them creates entanglement that makes each untestable in isolation. Additionally, incorrect classification produces financial loss downstream (Group E), so infra-caused failures must not be indistinguishable from quality failures.

## Decision

Adopt an event-driven pipeline where each stage emits a typed completion event; the PipelineOrchestrator persists stage outputs to CheckpointStore before invoking the next stage; and BudgetMonitor is an independent EventEmitter subscriber that emits `budget:extend` or `budget:halt` to ReflectionHandler without coupling to its internal logic.

## Justification

- **LTM persistence (resolved tension 1):** CheckpointStore is a single, atomic-write component responsible for both LTM state and stage outputs; warm-start reads the checkpoint before PerceptionHandler executes, satisfying the requirement that every run builds on accumulated document knowledge.
- **Adaptive budget decoupling (resolved tension 2):** BudgetMonitor subscribes to `reflection:iteration` events independently; it can be unit-tested with synthetic events and modified without touching ReflectionHandler — the budget ceiling ($0.30 default, $0.50 absolute maximum with score > 0.65 extension) is enforced from outside the critique loop.
- **Financial loss consequence (Group E):** Stage-level checkpoints allow reruns from the last completed stage on proxy or infrastructure failure, reducing costly full reruns caused by infra issues rather than quality issues.
- **Explicit convergenceStatus:** ReportEmitter always writes `convergenceStatus: converged | budget-extended | incomplete` — downstream consumers can distinguish a high-quality report from a budget-terminated one without inspection.
- **Storage extension point:** CheckpointStore is accessed only through a read/write interface; migrating from JSON to SQLite requires changing only CheckpointStore, not the 4 stage handlers — satisfying the stress test finding that SQLite/ChromaDB is a realistic future requirement.
- **Pedagogical requirement:** The explicit State Machine coordination in PipelineOrchestrator and the Chain of Responsibility in stage handlers satisfy the stated learning objective of demonstrating these patterns as first-class structural artifacts.

## Consequences

**Positive:**
- Partial run recovery without full reprocessing on infra failure
- BudgetMonitor independently testable with synthetic events
- New stage = new EventEmitter handler; existing handlers untouched
- convergenceStatus makes report quality auditable by downstream teams

**Negative:**
- More initial code than a flat sequential pipeline: EventBus setup, CheckpointStore, multiple listeners
- Event flow is less intuitive to debug than a linear call stack — log correlation required
- In-process EventBus limits horizontal scaling without architectural promotion to Option C

## Alternatives Rejected

**Option A — Flat Sequential Pipeline:** BudgetMonitor cannot be decoupled from ReflectionHandler — budget and quality logic become entangled. No stage-level recovery: any infra failure produces a full rerun, which directly contradicts the financial loss consequence accepted in Group E. Rejected because the complexity cost of decoupling budget logic outweighs the simplicity benefit.

**Option C — Distributed Pipeline with Queue:** Current volume (dozens/day) does not justify Redis and a multi-process worker pool. Introduces Redis as an operational dependency before the 10x scale threshold identified in the stress test (~200 analyses/day with concurrency) is reached. Rejected as premature until the stress test trigger materializes.

## When to Reconsider

- If daily volume exceeds ~200 analyses and concurrent runs are introduced, promote in-process EventBus to BullMQ over Redis and extract stage handlers as independent workers (Option C).
- If LTM JSON file exceeds ~50MB or query latency in MemoryHandler degrades measurably, migrate CheckpointStore to SQLite with indexed queries.
- If the CI&T Flow proxy introduces per-connection overhead that makes parallel stage execution worthwhile, evaluate a DAG execution model over the sequential EventEmitter chain.

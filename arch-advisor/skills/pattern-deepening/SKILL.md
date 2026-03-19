---
name: pattern-deepening
description: "Use this skill during Phase 3.5 Pattern Deepening to provide implementation-level guidance for the specific patterns present in the chosen architecture. Contains twelve pattern blocks: Hybrid Decision Engine, Planner-Executor-Critic, Voting + Arbiter, Saga with Compensation, Human-in-the-Loop with Checkpointing, Complexity-based LLM Routing, LLM Response Caching, Bulkhead, Anti-Corruption Layer, Strangler Fig, Batch Processing, Feedback Loop with Regression Detection."
---

# Pattern Deepening Reference

Each block below covers one architectural pattern. Apply only the blocks whose trigger condition was met in the session. Each block produces: why this system needs it, key design decisions, critical implementation constraint, and session note (NFR/ADR handoff).

---

## Block 1 — Hybrid Decision Engine

**Structure:**
```
Input → [Rule Engine] ──(confidence ≥ threshold)──→ Decision
              ↓ (below threshold)
         [LLM Reasoner] → [Heuristic Validator] → Decision
```

**Key design decisions to surface for this system:**

- **Confidence threshold**: Start at 0.85. Below this, escalate to LLM. Calibrate against actual data from this domain — the portfolio baseline is 70–80% of helpdesk tickets are rule-solvable; the threshold for this system may differ.
- **Rule engine signal type**: Identify the domain-specific signals for "obvious cases" — keywords, field values, structural patterns, regex. Generic rules (length > N) are weak; domain-specific rules (e.g., `contains("cannot login")` → category=auth) are strong.
- **Heuristic validator scope**: Runs on LLM output only, not on rule-engine output. Catches common LLM errors: format violations, out-of-range values, logical contradictions. Does not re-call the LLM — corrects the output or rejects it.
- **Misclassification cost asymmetry**: Which is more expensive for this system — a false negative (rule engine passes a case it should have escalated) or a false positive (LLM called for a case rules could have handled)? This determines whether to bias the threshold toward recall or precision.
- **Rule set storage**: Code (fast, zero latency) vs. configurable store (product team can adjust without deploy). Use configurable store if non-engineers need to add or modify rules.

**Critical implementation constraint:** The rule engine and LLM must be benchmarked on the same labeled test set before claiming cost savings. Without this measurement, the "70% rule-solvable" assumption is speculation, not architecture.

**Session note:** Generates NFR metric "Classification accuracy by path (rule vs. LLM) — target: rule-path precision ≥ LLM-path precision × 0.95." Affects ADR Decision section (justify why hybrid is chosen over LLM-only) and Cost section of NFR checklist (expected cost reduction percentage).

---

## Block 2 — Planner-Executor-Critic (PEC)

**Structure:**
```
Iteration N:
  [Planner]  → decomposes task into executable steps (temperature=0)
      ↓
  [Executor] → executes each step, collects results
      ↓
  [Critic]   → evaluates result against criteria
      ├─ score ≥ acceptableScore → DONE
      ├─ score < acceptableScore + iter < maxIter → loop with critique fed back
      └─ iter ≥ maxIter → return best result so far
```

**Key design decisions to surface for this system:**

- **maxIterations**: Start at 3 for most systems. Each iteration adds ~4–8s of latency (1 Critic call + 1 Executor call). For a latency target of <15s, maxIterations=2 is safer. Confirm against the stated latency target.
- **acceptableScore**: Tie this to the stated quality requirement, not an abstract number. "Score ≥ 0.80" means nothing without a definition of what score 0.80 corresponds to in this domain.
- **Critic model**: Using the same model as the Generator creates self-validation bias — the generator tends to score its own output highly. A different model (or a smaller, more critical model) as Critic improves reliability and often reduces cost.
- **Planner temperature**: Must be zero. Any temperature > 0 in the Planner produces plans with inconsistent step names, inconsistent parameter schemas, or steps referencing tools that don't exist — the Executor will fail silently or throw unpredictably.
- **Partial result carry-forward**: Decide before implementing whether failed-iteration partial results are discarded or fed back as context for the next iteration. Carry-forward improves convergence but increases prompt length (and cost) each iteration.

**Critical implementation constraint:** The Planner must use temperature=0. This is not a preference — it is a structural requirement. Non-zero temperature in planning produces bugs that are extremely hard to reproduce and diagnose because the plan structure varies between runs.

**Session note:** Generates NFR metrics "Critic score per request" and "Max iterations reached rate" (alert if >10% — indicates acceptableScore is miscalibrated). Affects ADR Consequences (negative: latency is non-deterministic, bounded by maxIter × per-iteration latency).

---

## Block 3 — Voting + Arbiter

**Structure:**
```
Agent A ─┐
Agent B ─┼→ [Majority Vote] → consensus? → Decision
Agent C ─┘       ↓ (no majority)
          [Weighted by Confidence] → consensus? → Decision
                   ↓ (no consensus above threshold)
          [Arbiter LLM] → Decision with reasoning
                   ↓ (arbiter also uncertain)
          Escalate to human / return highest-confidence vote
```

**Key design decisions to surface for this system:**

- **Cascade order**: Majority → weighted by confidence → arbiter. Each stage is more expensive. Define the threshold for triggering the next stage (e.g., "no simple majority → weighted vote; weighted confidence gap < 0.15 → arbiter").
- **Confidence source**: Declared by LLM (risk: LLMs are often overconfident) vs. derived from structural signals (number of consistent sub-answers, agreement on key entities). Declared confidence should be used as a tiebreaker, not as a hard weight, unless the model has been calibration-tested on this domain.
- **Arbiter context**: Arbiter seeing only votes is cheap but shallow. Arbiter seeing the full reasoning of each voter is expensive (~3–5× token cost) but produces better resolution. Use full-reasoning arbiter only when the decision has high stakes (financial, regulatory, medical).
- **Terminology normalization**: Agents using different terms for the same concept (e.g., "payment failure" vs. "charge declined") create false conflicts. Normalize terminology before aggregating votes — this is pre-processing, not prompt engineering.
- **Arbiter invocation rate monitoring**: If the arbiter is called for >20% of decisions, the voters are misaligned. This is a quality signal to improve voter prompts, not a reason to improve the arbiter.

**Critical implementation constraint:** Terminology normalization is mandatory before vote aggregation. Without it, synonym divergence between agents creates false conflicts that waste arbiter calls and produce lower-quality decisions than a single agent would.

**Session note:** Generates NFR metric "Arbiter invocation rate — alert if >20%." Affects C4 diagram (Arbiter as a named component within the decision cluster). Affects ADR Justification (explain why voting is preferred over single-agent for this system's reliability requirement).

---

## Block 4 — Saga with Compensation

**Structure (choreography):**
```
step1.completed → [Step 2 Handler] → step2.completed → [Step 3 Handler]
                                              ↓ (step3 fails)
                              compensation2.triggered ← compensation3
                  compensation1.triggered ←
```

**Structure (orchestration — recommended for agent systems):**
```
[Saga Coordinator]
  → execute(step1) → success → execute(step2) → success → execute(step3)
                                                    ↓ (failure)
  ← compensate(step2) ← compensate(step1)
```

**Key design decisions to surface for this system:**

- **Orchestration vs. choreography**: For agent systems, orchestration (central coordinator with explicit compensation calls) is strongly preferred. Choreography is harder to trace when compensation chains are triggered — the `sagaId` alone is insufficient to reconstruct the compensation order in distributed agent logs.
- **Compensation defined before the step**: Each step's compensation action must be defined at the same time the step is designed, not added later. Compensation is part of the step's interface contract.
- **sagaId propagation**: `sagaId` must be included in every event, log line, and storage record produced by the saga. It is the only way to reconstruct the full execution and compensation history for a single saga instance.
- **Compensation idempotency**: Compensations will be called more than once (failure + retry is the normal failure recovery path). A compensation that sends a cancellation email, releases a resource, or reverts a record must be safe to repeat without double-effects.
- **Saga timeout**: Define a maximum wall-clock time for the saga to complete. If any step hangs indefinitely, the saga must eventually time out, trigger compensations, and return a failure — not wait forever.

**Critical implementation constraint:** Compensations must be idempotent. This is non-negotiable. A compensation called twice due to retry will cause double-compensation bugs (double refund, double cancellation email, double inventory release) that are very hard to detect in testing because they require precise timing to reproduce.

**Session note:** Generates NFR metrics "Saga completion rate," "Compensation triggered rate," and "Saga timeout rate." Affects ADR Alternatives Rejected section (2PC rejected because it requires distributed locking incompatible with agent async execution).

---

## Block 5 — Human-in-the-Loop with Checkpointing

**Structure:**
```
[Node 1] → [Node 2] → interrupt() ← workflow suspended
                             ↓ (human reviews)
                      inject(humanInput) → [Node 3] → [Node 4] → done
```

**Key design decisions to surface for this system:**

- **Checkpoint storage**: `MemorySaver` is development-only — it does not survive process restarts. Production HITL requires durable storage: `PostgresSaver` or `RedisSaver`. If the workflow may be suspended for hours or days, durability is non-negotiable.
- **TTL for pending checkpoints**: How long does the workflow wait before expiring? If the reviewer never responds, the request must eventually fail with a defined error state. Define the TTL based on the business SLA (e.g., "pending approval must be resolved within 24 hours").
- **Resume API**: The workflow resumes by injecting human input at the interrupt point. This API must be reachable from the approval interface (web UI, Slack bot, email link). Design the API contract before designing the approval UX.
- **Notification mechanism**: The system must proactively notify the reviewer when a checkpoint is pending. Polling is not acceptable for async approval workflows. Design the notification path (webhook, email, push) as part of the architecture, not as a follow-up.
- **Multiple approval levels**: If rejection at any level should trigger compensation (undo previous steps), the HITL nodes must be integrated with the Saga pattern. Define this dependency explicitly.

**Critical implementation constraint:** `MemorySaver` is not durable. This is the most common production failure mode for this pattern. Any production HITL workflow using `MemorySaver` will silently lose pending state on process restart, leaving suspended workflows with no resumption path.

**Session note:** Generates NFR metrics "Checkpoint pending count," "Checkpoint age (time waiting for human input)," and "Checkpoint TTL expiry rate." Affects NFR Reliability section (availability must account for checkpoint store durability, not just the application tier).

---

## Block 6 — Complexity-based LLM Routing

**Structure:**
```
Request
  ├─ [Domain-specific simple signals] → below complexity threshold → [Cheap model]
  ├─ [Domain-specific complex signals] → above complexity threshold → [Capable model]
  └─ [Uncertain] → default to capable model (or add classification call)
```

**Key design decisions to surface for this system:**

- **Complexity signals for this domain**: Define signals available before the LLM call — not prompt length (too crude). Domain-specific examples: number of distinct entities mentioned, presence of implicit context requiring external knowledge, ambiguity markers, required output length. Prompt length is a last resort, not a primary signal.
- **The model pair**: Which model handles "simple," which handles "complex." Quantify the cost and latency delta. For Haiku vs. Sonnet: ~10× cost difference, ~2× latency difference. For Haiku vs. Opus: ~50× cost difference. This is the lever that determines ROI of routing.
- **Quality floor for the simple model**: Benchmark the cheap model on domain-specific test cases, not generic benchmarks. The question is not "is Haiku good?" but "is Haiku good enough for the simple-path requests in THIS system?"
- **Classifier cost**: If classification requires a full LLM call, the routing overhead may negate the savings. Use deterministic rules or a micro-model for classification. A Haiku call to classify whether to use Haiku defeats the purpose.
- **Fallback behavior**: When classification is uncertain, default to the capable model. Do not default to the cheap model — a wrong answer from the cheap model costs more in downstream correction than the extra inference cost of the capable model.

**Critical implementation constraint:** The routing decision must be made on signals available before the LLM call. Cascade routing (call cheap model first, escalate if output quality is low) doubles latency on escalated requests. For latency-sensitive systems, pre-call routing is the only viable approach.

**Session note:** Generates NFR metric "Simple-path vs. complex-path distribution — monitor for drift over time." Affects Cost section of NFR checklist (state the expected cost reduction percentage and the distribution assumption it depends on).

---

## Block 7 — LLM Response Caching

**Structure:**
```
Request → key = hash(prompt + system_prompt + maxTokens + temperature)
  ├─ HIT (age < TTL) → return cached response; increment hitCount
  └─ MISS → call LLM
      ├─ cost < minCostToCache → discard (not worth storing)
      └─ cost ≥ minCostToCache → store {response, timestamp, cost, hitCount=0}
          └─ cache.size ≥ maxSize → evict entry with lowest hitCount (not oldest)
```

**Key design decisions to surface for this system:**

- **Cache key composition**: `hash(prompt + system_prompt + maxTokens + temperature)`. If any of these fields vary per request (e.g., user-specific instructions injected into the system prompt), cache hit rate drops toward zero. Decide upfront whether the system prompt is static or parameterized.
- **TTL strategy**: Tie TTL to the rate of change of the underlying knowledge. Document-grounded systems: invalidate on document update. Policy systems: 24-hour TTL. Real-time data systems (live prices, live inventory): do not cache.
- **minCostToCache threshold**: Do not store cheap calls — they waste cache memory and evict valuable entries. Calibrate based on the cost-per-request distribution of expected traffic.
- **Eviction policy**: Evict by lowest `hitCount`, not by age. An expensive call made once a week is more valuable to cache than a cheap call made hourly.
- **Distributed vs. in-process cache**: In-process LRU (e.g., `lru-cache`) is zero latency but does not survive restarts or scale horizontally. Redis is required for distributed deployments or when cache hit rate must be preserved across deploys.

**Critical implementation constraint:** The cache key must include the full system prompt. Parameterized system prompts (user context, session state, personalization injected) make caching effectively impossible unless those parameters are extracted and handled outside the cached path.

**Session note:** Generates NFR metric "Cache hit rate — target ≥ 40%." Affects Cost section of NFR checklist (state expected cost reduction at target hit rate). Flag in ADR if system prompt is parameterized — this is a cache-defeating design and the tradeoff must be explicit.

---

## Block 8 — Bulkhead

**Structure:**
```
Without Bulkhead:            With Bulkhead:
  All requests                 Critical Pool (N threads/workers)
  → single pool                  → triage, payments, safety checks
  → one slow service             Non-Critical Pool (M threads/workers)
    fills all threads              → reports, analytics, background jobs
  → all services degrade         → slow analytics does not affect triage
```

**Key design decisions to surface for this system:**

- **Criticality domain mapping**: Identify the criticality domains for THIS system specifically. Examples: for a support system — "triage and escalation" is critical, "reporting and analytics" is non-critical. For a financial system — "transaction processing" is critical, "recommendation generation" is non-critical. Name the domains explicitly.
- **Pool sizing**: Set pool sizes based on expected concurrent load per domain, not as a uniform split. A critical domain with bursts of 20 concurrent requests needs a pool of at least 20; a non-critical domain with steady 5 concurrent needs 5.
- **Enforcement level**: Application-level (in-process thread pool limits) is simpler to implement; infrastructure-level (separate queues, separate worker processes) is more isolated. For agent systems, in-process bulkheads are usually sufficient unless the workloads are on separate services.
- **Overflow behavior**: When a non-critical pool is exhausted, reject new non-critical requests (return 429 or queue with backpressure). Never allow overflow into the critical pool — this is the point of the bulkhead.
- **Circuit breaker per pool**: A bulkhead without a circuit breaker still fails if the external dependency of one pool (e.g., a specific LLM provider) fails and blocks all its threads. Each pool needs its own circuit breaker.

**Critical implementation constraint:** The bulkhead guarantee fails the moment the critical pool can be borrowed by non-critical requests under load. This happens naturally in naive thread pool implementations. Explicit enforcement (hard pool size limit, no shared overflow) is required — not just a naming convention.

**Session note:** Generates NFR metric "Pool utilization by criticality domain — alert if critical pool > 80% sustained." Affects NFR Reliability section (availability for critical paths must be stated independently: "critical path availability ≥ 99.9%; non-critical path availability ≥ 99%").

---

## Block 9 — Anti-Corruption Layer (ACL)

**Structure:**
```
Legacy Model (complex, inconsistent, undocumented)
        ↓ ACL.toDomain()
   Domain Model (clean, typed, agent-readable)
        ↓
   Agent System
        ↓
   Agent Output
        ↑ ACL.toLegacy()
   Domain Model → Legacy Model
```

**Key design decisions specific to agent systems:**

- **Agents must never read legacy data directly**: Even small legacy quirks (inconsistent null handling, ambiguous status codes, undocumented field semantics) will be included in LLM prompts and produce agent behaviors that are nearly impossible to trace back to a data quality issue. The ACL is the hard boundary.
- **toDomain() must produce agent-safe output**: The domain model must be clean enough to include verbatim in a prompt. Field names should be self-describing (not `stat_cd_3` but `orderStatus`). Enums should be human-readable. Nulls should be explicit absence markers.
- **toLegacy() must handle ambiguous agent output**: Agents may produce nuanced outputs that don't map cleanly to legacy constraints (e.g., agent recommends "partial refund with goodwill credit" but legacy only accepts `REFUND_FULL` or `REFUND_NONE`). The ACL must define the mapping policy for these cases explicitly.
- **Log both models**: Every ACL translation must log the original legacy payload and the translated domain model. When an agent behaves unexpectedly, the ACL log is the first place to look — it shows whether the input to the agent was correct.
- **ACL as a named component in the C4 diagram**: The ACL must appear as an explicit container (not just an implied translation layer) between the agent system boundary and the legacy system. This makes it visible in architecture reviews and onboarding.

**Critical implementation constraint:** Never let agents read legacy data directly. This constraint must be enforced architecturally (agents have no access to legacy APIs or legacy DB), not just by convention. Convention-based ACLs erode over time as developers take shortcuts under deadline pressure.

**Session note:** Generates NFR metric "ACL translation error rate — alert if >1%." Affects C4 diagram (ACL as explicit named container). Affects ADR (ACL as the consistency boundary between old and new data models).

---

## Block 10 — Strangler Fig

**Structure:**
```
Phase 1 — LOW RISK:   0% → 100% (direct cutover, no gradual routing)
Phase 2 — MEDIUM:     0% → 25% → 50% → 100%
  (monitor between each step; rollback if errorRate > threshold)
Phase 3 — HIGH RISK:  0% → 5% → 10% → 25% → 50% → 100%
  (rollback if errorRate > 1% OR p95 latency > stated target)

Router:
  explicitRoute=new    → new system (testing, canaries)
  explicitRoute=legacy → legacy (emergency bypass)
  default              → percentage routing with automatic fallback to legacy on failure
```

**Key design decisions to surface for this system:**

- **Rollback trigger**: Define the error rate and latency thresholds that cause automatic rollback to legacy for THIS system. Generic thresholds (5% error rate) may be too permissive (financial system) or too conservative (internal tool). State the thresholds in the architecture, not in a runbook written later.
- **Routing schedule**: Define percentage increments and go/no-go criteria tied to measurable exit conditions, not calendar dates. "Move to 25% when error rate is stable at <1% for 48 hours" is better than "move to 25% on March 15."
- **Parallel processing risk**: Can the new system and legacy system safely process the same request in parallel? If not (double-sends, double-charges, double-records), the router must guarantee mutual exclusion — each request goes to exactly one system.
- **Feature parity verification**: Before each routing increase, run functional equivalence tests — not just error rate monitoring. An error rate of 0% while 30% of outputs are semantically wrong is not a safe migration.
- **Single-change rollback**: "Roll back to 0%" must be achievable with one configuration change or one CLI command, without a code deploy. If rollback requires a deploy, it will not happen fast enough in an incident.

**Critical implementation constraint:** The rollback mechanism must be a single configuration change with no deploy dependency. If rollback requires a code deploy, it cannot be executed in time during an incident. Test rollback in staging before the first production routing increment.

**Session note:** Generates NFR metric "New-system error rate vs. legacy error rate — side by side per routing phase." Affects ADR (migration strategy as a structural decision; alternatives: big-bang cutover rejected because of risk; strangler fig chosen for rollback safety).

---

## Block 11 — Batch Processing

**Structure:**
```
Requests → Queue
  [batchSize=N OR waitTime=Tms elapsed]
        ↓
  Promise.allSettled([req1, req2, ..., reqN])
        ↓
  Resolve/Reject each request independently
        ↓
  Start next batch
```

**Key design decisions to surface for this system:**

- **Trigger strategy**: `batchSize OR waitTime` — define specific values. For latency-tolerant async systems: prefer batchSize (e.g., 10 items); for latency-sensitive systems with burst arrivals: keep waitTime small (e.g., 50–100ms). Clarify which dimension dominates for this system.
- **Promise.allSettled vs. Promise.all**: Always use `Promise.allSettled`. A single request failure with `Promise.all` discards all successful results in the batch. `Promise.allSettled` resolves each request independently regardless of other failures.
- **Back-pressure**: If the queue fills faster than the batch processor consumes, the system must slow down producers. Options: reject new requests with 429, apply backpressure upstream, or queue with explicit capacity limits. No back-pressure mechanism means the queue grows without bound under load.
- **Batch homogeneity**: Homogeneous batches (same LLM prompt structure, different input data) are significantly simpler to manage and observe. Heterogeneous batches (different operations in the same batch) require per-item routing logic inside the batch processor.
- **Observability**: Log `batchId`, `batchSize`, and individual request outcomes (success/failure/reason) for each batch. Partial batch failures are impossible to diagnose without per-item outcome tracking.

**Critical implementation constraint:** Never use `Promise.all` for batch processing. Use `Promise.allSettled` with explicit per-item result handling. This is not a preference — `Promise.all` behavior (fail entire batch on any single failure) is a correctness bug for batch workloads.

**Session note:** Generates NFR metrics "Batch size distribution," "Batch processing latency P95," and "Individual request failure rate within batches." Affects NFR Performance section (state the expected latency increase from batching vs. the cost reduction it enables).

---

## Block 12 — Feedback Loop with Regression Detection

**Structure:**
```
User interaction / automated eval run
  → Collect signal: {taskId, agentId, input, actualOutput, expectedOutput}
  → Explicit: user rating, correction, escalation
  → Implicit: abandonment, repeated request, downstream failure
        ↓
  Store in quality log with {modelVersion, promptVersion, systemVersion}
        ↓
  Aggregate per release (or rolling window)
        ↓
  Compare vs. baseline:
    regression = currentScore < baseline × 0.95 (adjust threshold for domain noise)
        ↓
  PASS → release approved / no action
  FAIL → flag for manual review → approve or reject
```

**Key design decisions to surface for this system:**

- **Baseline definition**: The baseline must be stored with the artifact version it measures (`modelVersion`, `promptVersion`, `systemVersion`). A quality score without a version reference cannot be attributed to a specific change. Update the baseline deliberately after each approved release — not automatically.
- **Regression threshold**: `currentScore < baseline × 0.95` is a reasonable starting point. Adjust based on how noisy the quality signal is for this domain. High-noise domains (where scores vary ±5% run-to-run) need a wider threshold; low-noise domains can use ±2%.
- **Trigger action on regression**: Decide before the first regression: does detection automatically block deployment, require manual review, or trigger automatic rollback? The decision policy must be made before the system is in production, not after the first incident.
- **What is measured**: Define the specific quality signal before implementation: LLM-as-judge score, task completion rate, user satisfaction rating, hallucination rate, escalation rate. "Quality" without a concrete metric is unmeasurable.
- **Feedback collection mechanism**: Explicit feedback (user rates the output) has low volume but high signal. Implicit feedback (escalation rate, abandonment, repeated requests) has high volume but requires inference. Automated eval runs (test suite against ground truth) have high coverage but require a curated test set. The best systems combine all three.

**Critical implementation constraint:** The baseline must be version-controlled alongside the model, prompt, and system versions it was collected under. Without version correlation, a detected regression cannot be attributed to a specific change, making it impossible to determine what to revert.

**Session note:** Generates NFR metrics "Quality score per release" and "Regression detection latency (time between regression introduction and detection alert)." Affects NFR Quality section (regression threshold must be stated as a concrete value, not a principle).

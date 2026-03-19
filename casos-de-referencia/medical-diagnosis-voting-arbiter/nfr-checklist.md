# NFR Checklist — Medical Diagnosis Voting+Arbiter

## Performance

- [ ] Latency P50 — target: <15s (parallel specialists + voting; no arbiter path) — recommended
- [ ] Latency P95 — target: <30s (includes arbiter path; bursty burst window 07h–09h, 19h–21h) — mandatory; alert if sustained >30s during burst window
- [ ] Latency P99 — target: <35s (accounts for slowest specialist + full arbiter reasoning) — recommended
- [ ] LLM calls on critical path — target: ≤4 (3 specialists + 1 arbiter on worst path); alert if >5 sustained — mandatory
- [ ] Parallel specialist execution: all 3 specialists launched via Promise.allSettled, not sequential — mandatory; sequential execution would produce 12–18s baseline, exceeding P95 target
- [ ] TerminologyNormalizer latency — target: <500ms per normalization pass; alert if >500ms (embedding model bottleneck) — mandatory

## Cost

- [ ] Cost per case — voting path: target <$0.012 (exercise baseline $0.0084); arbiter path: target <$0.020 (exercise baseline $0.0148) — mandatory; alert if >2× respective baseline
- [ ] Cost per LLM call logged at runtime with fields: traceId, caseId, agentId, action, tokensUsed (input/output), costUsd, modelId — mandatory
- [ ] Arbiter invocation rate — target: 30–40% of cases; alert if >50% sustained over 7-day window (indicator of normalization failure or specialist prompt drift) — mandatory
- [ ] Monthly cost anomaly alerting: alert if daily cost > 2× rolling 7-day average — recommended
- [ ] Cost breakdown logged per stage: specialists (per agent), VotingCoordinator, ArbiterAgent — recommended

## Reliability

- [ ] Availability — target: 99.5% for critical (diagnosis) path — mandatory
- [ ] Circuit breaker on CI&T Flow Proxy — mandatory; states: CLOSED → OPEN after 3 consecutive errors → HALF-OPEN after 60s cooldown; separate circuit breaker per model tier (Haiku path / Sonnet path)
- [ ] Retry with exponential backoff for transient LLM failures — base: 1s, max: 30s, attempts: 3 — mandatory
- [ ] Promise.allSettled for specialist pool: partial failure (1 of 3 specialists fails) must produce degraded voting with 2 agents, not total pipeline failure — mandatory; log which specialist failed with reason
- [ ] Graceful degradation when Sonnet (arbiter) is unavailable: escalate directly to HITL, do not route arbiter cases to Haiku as quality substitute — mandatory; for medical decisions human review is the correct fallback
- [ ] HITL TTL enforcement: cases pending HITL review for >4h must transition to stoppedBy="hitl_timeout"; care team notified; case recorded in AuditEventStore — mandatory
- [ ] Checkpoint store durability: MemorySaver is development-only; production requires Azure Cosmos DB or equivalent durable store; process restart must not lose pending HITL cases — mandatory
- [ ] Bulkhead: diagnosis pipeline requests (critical pool) must not compete with analytics/audit queries (non-critical pool) under burst load — mandatory; critical pool utilization alert if >80% sustained during burst window

## Quality / Accuracy

- [ ] Diagnosis accuracy baseline — target: ≥92% on 20-case reference set; alert if <87.4% (95% of baseline) after any model or prompt change — mandatory; baseline versioned with {modelId, promptVersion, systemVersion}
- [ ] Regression detection: eval suite (20-case reference set) run before every deploy; blocks CI/CD if accuracy < 87.4% — mandatory
- [ ] Arbiter invocation rate as quality proxy — alert if >50% (normalization failure indicator) or <15% (overconfidence indicator; threshold may be miscalibrated) — mandatory
- [ ] HITL escalation rate — target: <20% of total cases; alert if >30% sustained (confidence calibration issue) — mandatory
- [ ] Specialist confidence calibration: declared confidence (temperature=0.3) used as weight in voting but NOT as a hard gate alone — confidence < 0.5 requires cascade escalation, not direct HITL — mandatory; prevents over-reliance on LLM self-reported confidence
- [ ] Terminology normalization effectiveness: false-conflict rate (cases that go to arbiter due to synonym divergence, not genuine disagreement) — target: <5% of arbiter invocations; measured via post-hoc review of arbiter cases where all specialists agreed on the canonical term — recommended
- [ ] Quality SLO: diagnosis accuracy ≥ 92% on ≥ 90% of eval runs over 30-day rolling window — mandatory
- [ ] Doctor override rate (HITL cases where doctor changes the system diagnosis) — target: track as baseline; alert if >20% change rate (systemic accuracy issue) — mandatory

## Observability

- [ ] Structured JSON log per LLM event — mandatory fields: traceId, caseId, sagaId, agentId, action, durationMs, tokensUsed (input/output), costUsd, modelId — mandatory
- [ ] traceId + sagaId propagated through all stages: DiagnosisAPI → SpecialistPool → TerminologyNormalizer → VotingCoordinator → ArbiterAgent → HITLGateway → AuditEventStore — mandatory; assign at DiagnosisAPI entry
- [ ] Span per pipeline stage: DiagnosisAPI, each specialist (labeled with specialistId), TerminologyNormalizer, VotingCoordinator, ArbiterAgent (if invoked), HITLGateway (if invoked) — mandatory
- [ ] AuditEventStore: append event at each stage transition — DiagnosisRequested, SpecialistCompleted (×3), VotingResolved, ArbiterInvoked, ArbiterResolved, HITLCreated, HITLResumed, DiagnosisCommitted — mandatory; each event includes traceId, sagaId, timestamp, payload hash
- [ ] stoppedBy logged per case as structured field — values: threshold_met / hitl_escalated / hitl_timeout / arbiter_confident / pipeline_error — mandatory
- [ ] Voting path logged per case: which cascade level resolved the case (majority / weighted / threshold / arbiter / hitl) — mandatory; enables arbiter invocation rate tracking
- [ ] Specialist output + normalized output logged per case (for terminology normalization audit and false-conflict analysis) — mandatory for compliance; redact clinical PII per HIPAA-equivalent policy
- [ ] Cost anomaly alerting per case: alert if single case cost > 3× rolling 7-day average per-case cost — recommended
- [ ] Dashboard: operations (latency P95, arbiter rate, error rate), quality (accuracy, HITL rate, override rate), cost (per-path breakdown) — recommended

## Extensibility

- [ ] New specialist agent registerable without modifying VotingCoordinator or ArbiterAgent — mandatory; specialist interface contract: {input: ClinicalCase, output: DiagnosisVote with confidence and reasoning}
- [ ] Voting strategy swappable without modifying specialist or arbiter contracts — mandatory; VotingCoordinator must accept strategy configuration, not hardcode cascade order
- [ ] Checkpoint store swappable: in-memory → Azure Cosmos DB without changing HITLGateway contract — mandatory; CheckpointStore interface must be the extension point
- [ ] AuditEventStore backend swappable: in-memory append → durable event store without changing AuditEventStore interface — mandatory; enables production hardening without refactoring pipeline stages
- [ ] LLM model swap per agent without code changes — mandatory; modelId must be in configuration (env vars), not hardcoded; applies to each specialist, normalizer embedding, and arbiter independently
- [ ] EMR integration extension point: every DiagnosisRecord must include sagaId field — mandatory now; enables Saga-with-Compensation for EMR commit/retract without breaking schema changes when integration goes live in 12 months
- [ ] acceptableConfidence threshold configurable at runtime (env var) — mandatory; current value 0.5 in production; A/B testing threshold calibration without code deploy

## Security

- [ ] Clinical case payload sanitized at DiagnosisAPI boundary before passing to any LLM — mandatory; prevent prompt injection via crafted clinical case content
- [ ] Audit trail: every LLM call logged with input hash and output hash — mandatory; enables detection of tampering with logged outputs; correlates AuditEventStore event with actual LLM call
- [ ] PII / clinical data: patient identifiers not included in LLM prompts in raw form — mandatory; use case reference ID (caseId) in LLM context; raw patient data stays in DiagnosisAPI layer and is not forwarded to specialists
- [ ] LLM response validation: structured output schema enforced for all specialist and arbiter outputs; reject malformed LLM responses at the receiving stage — mandatory; prevents downstream pipeline failures from LLM output drift
- [ ] API key / LiteLLM proxy credentials stored in environment variables or Azure Key Vault — mandatory; never hardcoded; rotation capability without redeploy
- [ ] Agent action scope: specialist agents and arbiter are read-only within the pipeline; only DiagnosisAPI and HITLGateway produce externally visible outputs — mandatory; no agent has direct write access to AuditEventStore or CheckpointStore (writes go through the API layer)
- [ ] Incident response: P1 = specialist agent produces diagnosis without HITL gate firing below confidence threshold → disable pipeline, alert on-call, manual review of all cases in last 24h — mandatory; P2 = arbiter invocation rate > 50% for >30min → alert + investigate normalization layer

# NFR Checklist — Single-Agent Pipeline with Reflection Loop

## Performance

- [ ] Latency P50 — target: <90s (avg observed ~60s with 3 iterations) — recommended
- [ ] Latency P95 — target: <180s (3 full iterations × ~60s) — mandatory
- [ ] LLM calls on critical path — target: ≤7 (1 Classifier + 1 Generator + up to 3 × [Critic + Reviser]) — mandatory; flag in log if exceeded
- [ ] stoppedBy distribution logged per run (threshold / costBudget / maxIterations) — mandatory

## Cost

- [ ] Cost per analysis — target: <$0.30 (hard ceiling); observed baseline $0.09–$0.15 with routing — mandatory
- [ ] Cost per LLM call logged at runtime with fields: traceId, agentId, action, tokensUsed (input/output), costUsd — mandatory
- [ ] Budget residual checked before each Reflection iteration — mandatory; abort iteration if `totalCost >= $0.30`
- [ ] Routing threshold enforced: Reviser → Haiku 4.5 when `totalCost / budget > 0.70` — mandatory
- [ ] Cost per stage breakdown in structured log (Classifier, Generator, Critic per iteration, Reviser per iteration) — recommended
- [ ] Monthly cost anomaly alerting: alert if daily cost > 2× rolling 7-day average — recommended

## Reliability

- [ ] Availability — target: 99.0% (development environment, no HA requirement) — mandatory
- [ ] Circuit breaker on LLM provider (CI&T Flow proxy) — mandatory; states: CLOSED → OPEN after 3 consecutive errors → HALF-OPEN after 60s cooldown
- [ ] Retry with exponential backoff for transient LLM failures — base: 1s, max: 30s, attempts: 3 — mandatory
- [ ] Graceful degradation when budget ceiling is reached — return partial report with `stoppedBy: "costBudget"` and `iterations` count — mandatory
- [ ] Graceful degradation when LTM is empty (first document in run) — Generator must produce valid report without ltmContext — mandatory

## Quality

- [ ] overallScore threshold — target: ≥ 0.78 per analysis — mandatory; log actual score per run
- [ ] Max iterations reached rate — target: <15% of runs; alert if >15% sustained over 7-day window — mandatory (indicator that threshold is miscalibrated or Reviser is ineffective)
- [ ] stoppedBy: "costBudget" rate — target: <20% of runs; alert if >20% — mandatory (indicator of budget-quality tension requiring adjustment)
- [ ] Quality SLO: overallScore ≥ 0.78 on ≥ 85% of completed runs (not stopped by costBudget) over 30-day rolling window — mandatory
- [ ] Regression detection: eval suite run before every deploy; threshold = baseline_score × 0.95 per dimension; blocks CI/CD if FAIL — mandatory
- [ ] Baseline versioned alongside {modelId, promptVersion, systemVersion} in repository — mandatory
- [ ] Eval pass rate — target: >90% on reference document set — mandatory
- [ ] LLM-as-judge for external validation (separate Sonnet call, blind to Generator) — recommended; run on 10% of production outputs sampled randomly

## Observability

- [ ] Structured JSON log per LLM event — mandatory fields: traceId, agentId, action, durationMs, tokensUsed (input/output), costUsd, modelId — mandatory
- [ ] traceId propagated through all stages of a single analysis run — mandatory; assign at pipeline entry, include in every log line and output metadata
- [ ] Span per pipeline stage (Perception, Decision, Memory, Reflection entry, each Reflection iteration) — mandatory
- [ ] Span per Reflection iteration — include iteration number, criticScore, isAcceptable, costThisIteration — mandatory
- [ ] Quality metric (overallScore + dimension scores) logged per completed run — mandatory
- [ ] stoppedBy logged per run as structured field — mandatory
- [ ] LTM state logged: domainCount, entriesInLTM at start and end of run — recommended

## Extensibility

- [ ] New document format (PDF, URL, HTML) addable without modifying Decision/Memory/Reflection stages — mandatory; requires refactoring perception.ts to Strategy pattern (SourceLoader interface) — currently not implemented: gap documented in ADR-001
- [ ] Model swap per stage without code changes — mandatory; model IDs must be in configuration (env vars or config file), not hardcoded; applies to Classifier, Generator, Critic, Reviser independently
- [ ] LTM storage swap without pipeline changes — mandatory; AnalysisLTM interface is the extension point; in-memory → SQLite → Redis without modifying Orchestrator or Reflection Stage
- [ ] acceptableScore threshold configurable at runtime (env var) — recommended; enables A/B testing of threshold values without code deploy
- [ ] Budget ceiling configurable at runtime (env var) — mandatory; hard-coded $0.30 in source is a maintenance risk when pricing changes

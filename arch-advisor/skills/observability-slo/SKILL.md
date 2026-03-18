---
name: observability-slo
description: "Use this skill when discussing monitoring, observability, SLOs, alerting, dashboards, or production reliability for AI systems. Trigger when someone says 'how do we monitor the agent?', 'we need alerts', 'how do we know if quality is degrading?', 'SLO for the system', 'the agent is slow and we don't know why', 'cost is unpredictable', 'we need dashboards', 'distributed tracing for agents'. Also trigger for: metrics, logs, traces, error budget, latency P95, hallucination monitoring, cost tracking."
---

# Observability and SLO Design for Agent Systems

## Three Pillars

**Metrics** (Prometheus/CloudWatch/Datadog): aggregated numbers over time
- What to measure: request rate, latency (P50/P95/P99), error rate, cost per request, LLM call count, cache hit rate, hallucination rate
- Use for: alerting thresholds, trend detection, capacity planning

**Logs** (structured JSON, ELK/Loki): timestamped event records with context
- Always include: traceId, sessionId, agentId, action, durationMs, tokensUsed, costUsd
- Never log: PII, API keys, user passwords, content of LLM prompts if regulated
- Use for: debugging specific failures, audit trails

**Traces** (OpenTelemetry/Jaeger): causal chain of operations across agents
- Every operation creates a span with traceId + spanId + parentSpanId
- The traceId must be constant for the full request across all agents
- Use for: identifying bottlenecks, debugging multi-agent failures

Without all three pillars, debugging production incidents takes 10× longer.

## AI-Specific Metrics

Beyond standard infrastructure metrics, monitor:

| Metric | Target | Alert when |
|---|---|---|
| Hallucination rate | < 2% | > 5% |
| Eval pass rate | > 90% | < 85% |
| Automation rate (% resolved without human) | > 70% | < 60% |
| LLM calls per request | ≤ 3 on critical path | > 5 sustained |
| Cost per request | < $X (define per system) | > 2× baseline |
| Latency P95 | < target (define per system) | > 1.5× target |

## SLI/SLO Framework

**SLI (Service Level Indicator)**: what you measure (e.g., % of requests with latency < 3s)
**SLO (Service Level Objective)**: the target (e.g., SLI ≥ 99.5% over 30 days)
**Error budget**: the tolerance for violations (100% - SLO = 0.5% → ~3.6 hours/month)

Error budget states:
- > 30% remaining: healthy — deploy freely, run experiments
- 10–30% remaining: caution — slower deploys, avoid risky changes
- < 10% remaining: freeze — stop new features, focus on reliability

For AI systems, SLOs should cover both reliability (availability, latency) and quality (hallucination rate, eval pass rate). Quality SLOs are often more meaningful than availability SLOs.

## Dashboard Personas

Build separate dashboards for different audiences:

**Executive**: automation rate, CSAT, cost per conversation, resolved without human
**Operations**: error rate, latency P95, provider health, active incidents
**Quality**: eval pass rate, hallucination rate, dimension scores (completeness, accuracy, etc.)
**Developer**: trace explorer, slow queries, LLM call breakdown, cache hit rate

## Anomaly Detection Pattern

1. Statistical baseline: rolling average + standard deviation over 7 days
2. Alert when: current value > mean + 3σ (z-score > 3) for 5 consecutive minutes
3. Correlate: if latency spike + cost spike → LLM provider issue; if latency spike alone → local bottleneck
4. Root cause: trace the slow request, identify which span consumed the time

## Cost Monitoring

Track cost at three granularities:
- Per request: enables per-feature cost analysis
- Per session: enables per-user cost analysis
- Per day/month: enables budget forecasting

Alert when:
- Single request cost > N × average (outlier detection)
- Daily cost trend suggests monthly overage

## Perguntas diagnósticas
1. What are the user-facing SLOs the product team has committed to?
2. How will you detect quality degradation (hallucinations, wrong answers) in production?
3. Is there a way to correlate a user complaint with the specific trace of that interaction?
4. What is the cost per request budget, and how will you alert when it's exceeded?
5. Does the team have experience with OpenTelemetry or a tracing system?
6. Who is responsible for acting on alerts — is there an on-call rotation?

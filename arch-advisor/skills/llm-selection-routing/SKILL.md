---
name: llm-selection-routing
description: "Use this skill when choosing which LLM to use, comparing providers, designing routing between models, handling LLM fallbacks, or optimizing LLM costs. Trigger when someone says 'which model should we use?', 'we need to choose between GPT-4 and Claude', 'how do we route to cheaper models for simple tasks?', 'we need fallback if OpenAI goes down', 'LLM costs are too high', 'we need multi-provider strategy', 'circuit breaker for LLM providers'. Also trigger for: model cascading, cost optimization, caching LLM responses, rate limiting."
---

# LLM Selection and Routing

## Selection Criteria (Weighted)

Score each candidate model against these dimensions:
- **40% Quality**: benchmark on domain-specific tasks, not generic benchmarks. Run actual test cases from your system.
- **30% Cost**: input + output tokens × price. Estimate monthly cost at expected volume.
- **20% Latency**: P95 response time. Measure in the target region.
- **10% Reliability**: provider uptime history, SLA, rate limit generosity.

Compliance constraints (data residency, EU/US jurisdiction, HIPAA BAA) are hard filters — apply before scoring.

## Routing Strategies

**Complexity-based routing**: classify each request as simple/complex before sending to LLM.
- Simple (classification, extraction, short answers) → smaller model (e.g., Haiku, GPT-3.5)
- Complex (multi-step reasoning, synthesis, code generation) → larger model (e.g., Sonnet, GPT-4)
- Requires a classifier (can be a fast rule or a micro-LLM call)
- Typical cost reduction: 40–60%

**Cost-optimized cascading**: try cheaper model first; escalate if output fails a quality check.
- Cheaper model answers → quality validator runs → if score < threshold → retry with expensive model
- Good when: most queries are simple and quality threshold is measurable
- Risk: latency doubles on escalated queries

**Load-balanced fallback**: maintain N providers in priority order.
- Provider 1 (primary) → fails or rate-limited → Provider 2 → Provider 3
- Each provider has a circuit breaker to avoid retrying a known-down provider

## Circuit Breaker per Provider

States: CLOSED (normal) → OPEN (failing, stop calling) → HALF-OPEN (testing recovery)

Transition rules:
- N consecutive errors or error rate > threshold within window → CLOSED to OPEN
- After cooldown period → OPEN to HALF-OPEN (allow 1 test request)
- Test request succeeds → HALF-OPEN to CLOSED
- Test request fails → HALF-OPEN back to OPEN

Without circuit breakers: every request waits for timeout on a down provider → cascading latency.

## Response Caching

Cache LLM responses when:
- Query is deterministic (same input → same expected output)
- TTL is appropriate for the domain (news queries: short TTL; policy queries: long TTL)
- Cost per query > minCostToCache threshold

Target cache hit rate > 40% for positive ROI.

Cache invalidation strategy:
- Time-based TTL: simple, predictable
- Content-based: invalidate when source documents change (requires change detection)

Do not cache: responses that depend on current time, user-specific data, or real-time state.

## Prompt Optimization for Cost

Reducing token count without degrading quality:
- Remove redundant context (instructions repeated multiple times)
- Compress few-shot examples (use shorter representative examples)
- Use structured prompts (JSON schema forces concise output)
- Target: 20–30% token reduction possible in most production prompts

Measure quality before and after any prompt change. Do not assume shorter = worse quality.

## Multi-Provider Architecture

```
[Request] → [Router: classify + route]
    ├── Simple task → [Provider A: cheaper model]
    ├── Complex task → [Provider B: capable model]
    └── Provider B down → [Circuit Breaker] → [Provider C: fallback]
         └── [Cache layer] for repeated queries
```

Ensure each provider's API key is in environment variables, never hardcoded.

## Perguntas diagnósticas
1. What is the monthly token budget and the cost-per-request limit?
2. Can tasks be classified as simple vs. complex before sending to the LLM?
3. Is there a compliance requirement restricting which providers can process data?
4. What is the availability SLA requirement — can the system tolerate 1 provider going down?
5. Are queries deterministic enough for caching? What is the expected cache hit rate?
6. Has the team benchmarked models on domain-specific tasks, or only on generic benchmarks?

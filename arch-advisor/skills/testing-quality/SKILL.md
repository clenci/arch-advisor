---
name: testing-quality
description: "Use this skill when designing testing strategies for AI agent systems, setting up quality evaluations, defining quality gates, or when someone says 'how do we test agents?', 'we need evals for LLM output', 'how to test non-deterministic systems?', 'quality gate for deployment', 'LLM-as-judge', 'regression testing for agents', 'how do we know if the model got worse?'. Also trigger for: testing pyramid, mock LLM, eval framework, hallucination detection, CI/CD for AI."
---

# Testing and Quality for Agent Systems

## Testing Pyramid (AI-Adapted)

```
              E2E (2%) + Human Evals
            Integration Tests (8%)
          Component Tests (20%)
        Unit Tests (70%)
    + Quality Evals (continuous)
```

**Unit tests (70%)**: deterministic components — parsers, validators, formatters, rule engines. Standard test runners (Jest, pytest). These are fast, cheap, and catch regressions in deterministic logic.

**Component tests (20%)**: individual agents with mocked LLMs. `MockLLMClient` returns pre-defined responses. Tests verify agent behavior when LLM returns expected outputs, edge case outputs, and errors.

**Integration tests (8%)**: multi-agent workflows with real services (not mocked). Verify that agents coordinate correctly. Use staging environment.

**E2E tests (2%)**: full user journeys in staging. Expensive — run on significant releases only.

**Quality evals (continuous)**: evaluate LLM output quality. Run per commit or daily. Catch model drift and prompt regressions.

## Dependency Injection for Testability

Every agent that calls an LLM should accept the LLM client as a constructor parameter:

```typescript
class MyAgent {
  constructor(private llm: LLMClient) {}
}
// Test:
const agent = new MyAgent(new MockLLMClient(fixtures));
// Production:
const agent = new MyAgent(new AnthropicClient());
```

Same pattern for VectorDB, EmbeddingService, and any external dependency.

## Eval Framework: Scorer Types

| Scorer | Use when |
|---|---|
| Exact Match | Output must be exactly a known value (deterministic extractors) |
| Contains Keywords | Output must mention required terms |
| Length Range | Output must be within acceptable length bounds |
| LLM-as-Judge | Quality is subjective (clarity, tone, helpfulness) |
| Hallucination Detector | Claims must be supported by provided source documents |
| Relevance Scoring | Semantic similarity to reference answer |

**LLM-as-Judge pattern**: use a separate LLM call (not the same model) to evaluate quality. Provide the question, the answer, and the criteria. Score 0–1. Use sonnet-class model for judging.

**Hallucination Detector**: provide the LLM with the source documents and the generated answer. Ask: "Are all factual claims in this answer supported by the provided sources?" Return supported/unsupported claims.

## Quality Gates

These thresholds block deployment if not met:
- Unit test pass rate: 100%
- Test coverage: > 80% of deterministic code
- Component test pass rate: > 95%
- Eval pass rate: > 90%
- Hallucination rate: < 2%
- Regression vs. baseline: < 5% score degradation

## Regression Testing

Build a baseline: run evals on a known-good version, store scores per dimension.

On every change: re-run evals, compare to baseline. Alert if any dimension drops > 5%.

Baseline must be versioned alongside the code. When you intentionally improve a dimension, update the baseline.

## Challenges Specific to AI Testing

- **Non-determinism**: same input → different outputs. Run each eval 3× and use the median score. Alternatively, set `temperature=0` for deterministic evals.
- **LLM cost**: running evals is expensive. Cache eval results per (input, prompt_version). Re-run only when prompt or model changes.
- **Prompt regression**: a prompt change that "looks better" can degrade specific dimensions. Always eval the full suite, not just the cases you're trying to fix.

## Perguntas diagnósticas
1. Which components are fully deterministic and can be exact-match tested?
2. Is it possible to inject mock LLMs into every agent for component testing?
3. What dimensions of quality matter most for this system (accuracy, completeness, tone)?
4. Is there an existing baseline of expected outputs that can serve as regression reference?
5. Can the CI/CD pipeline run evals automatically and block merges on quality regressions?
6. Is the team comfortable with LLM-as-Judge, or do they need human review for quality evals?

---
name: when-to-use-agents
description: "Use this skill when someone asks whether to build an agent or a traditional service, when to apply AI vs. deterministic logic, whether a use case justifies LLMs, or when a user says things like 'should we use AI here?', 'is this a good case for an agent?', 'we're deciding between an LLM and a rule-based system', 'does this need generative AI?', 'we need to classify tickets / interpret requests / generate responses'. Also trigger when discussing automation, chatbots, decision engines, or intelligent routing."
---

# When to Use Agents vs. Traditional Services

## Decision Framework

An agent is justified when **at least three** of the following are true:
1. Inputs are ambiguous, varied in phrasing, or require contextual interpretation
2. The task requires synthesis across multiple sources or reasoning steps
3. The space of valid outputs is too large to enumerate with rules
4. Errors are recoverable and the cost of occasional mistakes is acceptable
5. The value of adaptability exceeds the cost of non-determinism

A traditional service is preferable when:
1. Behavior must be deterministic and fully auditable line-by-line
2. Regulatory requirements mandate exact, reproducible logic
3. Latency must be sub-100ms
4. Input space is small and well-defined (≤ hundreds of cases)
5. Cost of LLM errors is financial, safety-critical, or legally binding

## Hybrid Pattern

Most production systems are hybrid: agents handle interpretation and synthesis, deterministic services handle enforcement and execution.

```
[Agent: interprets intent, classifies, synthesizes]
         ↓
[Rules: enforce policies, validate constraints]
         ↓
[Deterministic service: execute transaction]
```

Examples:
- Agent classifies a support ticket → rule engine routes by SLA → DB records the ticket
- Agent generates a product recommendation → compliance rules filter → pricing service finalizes

## Decision Table

| Criterion | Favors Traditional | Favors Agent |
|---|---|---|
| Input predictability | High (fixed formats) | Low (natural language) |
| Audit requirement | Line-by-line determinism | Logs + explanations sufficient |
| Error tolerance | Zero (financial/safety) | Medium (recoverable) |
| Task complexity | Well-defined rules | Ambiguous reasoning |
| Latency | <100ms hard requirement | Seconds acceptable |
| Cost model | Fixed, predictable | Variable, acceptable |

## Common Anti-Patterns

- **Agent for everything**: using LLMs for tasks that are better served by regex, lookup tables, or simple classifiers — wastes money and introduces unnecessary non-determinism
- **Rules for everything**: refusing to use agents for genuinely ambiguous tasks because of discomfort with non-determinism — results in brittle rule systems that break on edge cases
- **Agent without validation**: no heuristic layer to catch obviously wrong LLM outputs before they reach the user or downstream systems

## Perguntas diagnósticas
1. Can you enumerate all valid inputs and outputs? If yes, consider rules first.
2. What is the cost of a wrong answer? If financial or safety-critical, the agent needs a validation layer.
3. Does the task require understanding context that wasn't explicitly stated?
4. Would a rule-based implementation require hundreds of special cases?
5. Is the output format fixed or does it need to adapt to context?

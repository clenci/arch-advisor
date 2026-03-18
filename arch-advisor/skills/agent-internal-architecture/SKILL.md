---
name: agent-internal-architecture
description: "Use this skill when designing the internal structure of a single agent, when discussing perception layers, decision layers, memory management, reflection loops, state management, or when someone says 'how should the agent be structured internally?', 'how do we handle memory?', 'should state be mutable or immutable?', 'we need the agent to self-improve its output', 'how do we chunk documents?', 'the agent needs to remember past interactions'. Also trigger for topics like LTM, STM, chunking strategy, critic-reviser, context window management."
---

# Agent Internal Architecture

## Layer Model

A well-structured agent has four separable layers:

```
[Perception]  → loads and normalizes inputs (documents, messages, API data)
[Decision]    → classifies, reasons, decides (rules → LLM → heuristics)
[Memory]      → stores and retrieves context (STM + LTM)
[Reflection]  → validates and improves output (critic → reviser → loop)
```

Each layer has independent testability and evolvability. Do not collapse them into a single LLM prompt.

## State Management

**Immutable state** (recommended for production):
- Each operation produces a new state object
- Enables replay, time-travel debugging, and audit
- Cost: memory overhead per state snapshot

**Mutable state**:
- In-place mutation, simpler code
- Cannot replay decisions without external logging
- Use only for prototypes or when memory is severely constrained

Criterion: if the system requires audit trails or debugging of past decisions, use immutable state.

## Decision Layer Composition

Build the decision layer as three passes, in order:

1. **Rule Engine** — fast, deterministic, zero LLM cost
   - Apply for: compliance checks, security blockers, mandatory business rules, rate limits
   - If rule matches with confidence > threshold: return immediately, skip LLM
2. **LLM Reasoner** — handles ambiguous cases rules cannot cover
   - Structured output (tool_use or JSON schema) — never parse free-form text
   - Chain-of-thought for complex reasoning
3. **Heuristic Validator** — catches common LLM errors
   - Format validation, range checks, contradiction detection
   - Corrects the output before returning; does not re-call the LLM

## Chunking Strategy

| Strategy | Best for | Avoid when |
|---|---|---|
| Fixed-size | Logs, tabular data, code | Documents with semantic structure |
| Sentence-based | Articles, documentation | Very technical short sentences |
| Semantic | Q&A, advanced RAG | Computational budget is tight |
| Hierarchical | Books, technical specs with sections | Documents without hierarchy |

Add overlap (10–20% of chunk size) for sentence-based and fixed-size to avoid boundary artifacts.

## Memory Types

| Type | Scope | Storage | Access | Use for |
|---|---|---|---|---|
| STM | Current session | In-memory | Direct | Context window, recent turns |
| LTM | Persistent | Vector DB | Semantic search | Domain knowledge, past interactions |
| Episodic | Persistent | Relational DB | Query by metadata | Decision history, feedback records |
| Semantic | Persistent | Vector DB | Similarity search | General knowledge base |

For most systems, start with STM (sliding window) + LTM (vector). Add episodic when you need auditable decision history.

## Reflection Loop

Use a reflection loop when output quality is critical and LLM errors are recoverable.

```
[Generate] → [Critic: score dimensions] → threshold met? → done
                    ↓ no
             [Reviser: fix failing dimensions] → [Generate next iteration]
```

Stop criteria (choose all that apply):
- Score ≥ threshold (e.g., 0.85)
- Max iterations reached (e.g., 3)
- Cost budget exhausted

**Two-reviser pattern** (when relevance is also a dimension):
- Additive reviser: fixes completeness, accuracy — adds content
- Structural reviser: fixes relevance — removes off-topic content
- A single additive reviser will never remove content, even when instructed to

## Perguntas diagnósticas
1. Does the agent need to remember past sessions, or only the current one?
2. Can the decision logic be expressed entirely in rules, or does it require contextual reasoning?
3. Is output quality critical enough to justify a reflection loop, and what is the cost budget?
4. What document formats are ingested, and do they have semantic structure (headings, sections)?
5. Does the agent need to explain its decisions to external systems or auditors?

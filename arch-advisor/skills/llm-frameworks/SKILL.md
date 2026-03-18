---
name: llm-frameworks
description: "Use this skill when choosing between LangChain, LangGraph, CrewAI, Semantic Kernel, or custom implementation, when someone asks 'which framework should we use?', 'should we use LangGraph or LangChain?', 'is CrewAI a good fit?', 'should we build custom?', 'we need a framework for our agents', 'comparing LLM frameworks', or when evaluating framework trade-offs for agent orchestration. Also trigger for topics: LCEL, StateGraph, Crew, Semantic Kernel skills, framework migration."
---

# LLM & Agent Framework Selection

## Framework Comparison

| Aspect | LangChain | LangGraph | CrewAI | Semantic Kernel | Custom |
|---|---|---|---|---|---|
| Loops / cycles | Manual | Native | Manual | Manual | Full control |
| Complex branching | Limited | Excellent | Limited | Limited | Full control |
| Multi-agent | Basic | Complete | Main focus | Basic | Full control |
| TypeScript support | Yes | Yes | No | Yes | Yes |
| Ready integrations | 100+ | Inherits LC | Limited | Microsoft stack | None |
| Human-in-the-loop | Manual | Native (interrupt) | Manual | Manual | Full control |
| Workflow visualization | No | Mermaid | No | No | Custom |
| Performance overhead | Medium | Medium | Low-medium | Medium | None |

## Decision Tree

```
Workflow has loops, cycles, or complex conditional branching?
├── YES → LangGraph
└── NO
    ├── Multiple agents with coordination?
    │   ├── TypeScript required → LangGraph
    │   └── Python acceptable
    │       ├── Speed over control → CrewAI
    │       └── Control over speed → LangGraph
    ├── Linear RAG pipeline, no agent coordination → LangChain
    ├── Microsoft / .NET / Azure stack → Semantic Kernel
    └── Compliance forbids external deps / performance critical / <50% fit → Custom
```

## When Each Framework Wins

**Use LangChain when:**
- Pipeline is linear or only slightly conditional
- 100+ integrations are valuable (databases, vector stores, LLMs)
- Rapid prototyping is the priority
- Team already knows LangChain

**Use LangGraph when:**
- Workflow has loops (draft → critique → revise → repeat)
- Human review and approval at specific steps is required
- Need full visualization of the state machine
- Shared state between agents across multiple steps

**Use CrewAI when:**
- The "team with roles" mental model fits the domain naturally
- Python-only is acceptable
- Speed of development outweighs fine-grained control
- Role-based agent delegation is the primary pattern

**Use Custom when:**
- Compliance prohibits third-party dependencies
- Performance is critical and framework overhead is measurable
- Framework covers < 50% of actual use cases
- Full auditability of every operation is required

## Trade-off Summary

- LangGraph vs LangChain: LangGraph adds native cycle support and state management at the cost of slightly more setup. For any workflow with loops, LangGraph is strictly better.
- LangGraph vs CrewAI: LangGraph gives more control; CrewAI abstracts coordination. CrewAI is faster to prototype if the role-based model fits; harder to customize when it doesn't.
- Framework vs Custom: frameworks reduce initial development time by ~60%; custom implementations reduce long-term maintenance burden and eliminate version dependency issues. The break-even is typically at 12–18 months.

## Migration Considerations

Migrating between frameworks is expensive. The main costs:
- Rewriting state management (LangChain chains → LangGraph StateGraph)
- Re-implementing tool integrations
- Re-testing all workflows

Establish the workflow complexity early. If loops are anticipated within 6 months, start with LangGraph even for simpler initial cases.

## Perguntas diagnósticas
1. Does the workflow have cycles (output feeds back as input to an earlier step)?
2. Is human approval required at any point in the workflow?
3. Is TypeScript a hard requirement?
4. Does the team have existing familiarity with any of these frameworks?
5. Are there compliance restrictions on third-party dependencies?
6. What percentage of the actual use cases does each candidate framework cover?

---
name: integration-protocols
description: "Use this skill when designing how agents expose or consume tools and APIs, when discussing MCP servers, A2A communication, tool registries, or when someone says 'agents need to call external APIs', 'how should agents communicate with each other?', 'we need to expose tools to the LLM', 'designing agent-to-agent messaging', 'tool governance and access control', 'idempotent tool calls', 'MCP server implementation'. Also trigger for: Model Context Protocol, A2A patterns, tool design, RBAC for tools, distributed tracing between agents."
---

# Integration Protocols: MCP, A2A, and Tool Design

## MCP (Model Context Protocol)

MCP standardizes how LLMs access external resources and tools. The LLM client discovers tools at runtime, calls them by name, and receives structured results.

**Use MCP when:**
- Multiple agents or frameworks need access to the same tools (standardization pays off)
- Tool discoverability is important (agents discover capabilities dynamically)
- You want a vendor-neutral protocol for tool integration

**Use custom tools when:**
- 1–2 tools only, no need for discovery
- Performance is critical (MCP adds a small overhead)
- Compliance forbids the protocol dependency

MCP components:
- **Resources**: read-only data sources (files, DB records, API responses)
- **Tools**: callable functions with side effects
- **Prompts**: reusable prompt templates

## A2A (Agent-to-Agent) Communication Patterns

| Pattern | Description | Use when |
|---|---|---|
| Request-Response | Agent A sends message, waits for Agent B's reply | Synchronous task delegation |
| Event-Driven | Agent A publishes event, Agent B subscribes | Async notifications, decoupled updates |
| Blackboard | Agents read/write shared state | Collaboration without fixed sender/receiver |
| Hierarchical | Manager delegates to workers, collects results | Supervised task distribution |

Every A2A message must carry: `traceId`, `correlationId` (to match replies), `sender`, `timestamp`.

## Tool Design Principles

**Single Responsibility**: each tool does one thing. Avoid "do_everything" tools — they are untestable and unpredictable.

**Idempotency**: tools that modify state must be safe to call twice with the same input. Use an idempotency key (UUID) as input parameter, check if already processed before executing.

**Input validation**: validate all inputs against a JSON Schema before executing. Reject invalid inputs with a clear error message — never silently coerce.

**RBAC**: different agents have different permissions. Enforce at the tool registry level, not inside the tool implementation.

**Rate limiting**: per-agent and per-tool rate limits. Protect downstream systems from agent loops.

**Audit log**: every tool call is logged with: caller identity, input, output, timestamp, duration, cost. Non-negotiable for production.

**Timeout**: every tool call has a maximum duration. Default 30s, adjustable per tool. Never allow an agent to block indefinitely on a tool call.

## Tool Registry Pattern

```
[Agent requests tool]
      ↓
[Registry: lookup tool by name]
      ↓
[RBAC: does this agent have permission?]
      ↓
[Rate limiter: is this agent within quota?]
      ↓
[Validator: is the input valid JSON Schema?]
      ↓
[Executor: run the tool with timeout]
      ↓
[Audit log: record the call and result]
```

## Distributed Tracing Between Agents

When Agent A calls Agent B (via MCP or A2A):
- A creates a new span (spanId) under the existing trace (traceId)
- A passes `{traceId, parentSpanId: A's spanId}` to B
- B creates its own span with parentSpanId pointing to A's span
- This builds a causal tree: root request → A → B → tool call

Without this, you cannot reconstruct the call chain from logs.

## Perguntas diagnósticas
1. How many distinct tools or external APIs does the agent system need to call?
2. Do multiple agents need access to the same tools, or are tools agent-specific?
3. Are there tools that modify production state (write, delete, send)? These need idempotency.
4. Do different agents need different access levels to the same tool?
5. How will you audit what each agent called and with what inputs?
6. Is MCP supported by the agent framework you've chosen, or will you build custom tool calling?

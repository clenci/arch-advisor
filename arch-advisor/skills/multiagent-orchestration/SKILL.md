---
name: multiagent-orchestration
description: "Use this skill when designing systems with multiple agents, when choosing between centralized and decentralized coordination, when discussing pipelines, DAGs, agent communication, event-driven architectures, or when someone says 'we need multiple agents working together', 'how should agents coordinate?', 'should agents communicate directly or through a central controller?', 'we need agents to work in parallel', 'how do we handle agent conflicts?', 'we need a workflow with multiple steps and agents'. Also trigger for topics: orchestrator, choreography, Saga pattern, bounded contexts, agent contracts."
---

# Multi-Agent Orchestration

## Architecture Taxonomy

**Control dimension:**
- Centralized: one orchestrator routes all work to specialist agents
- Decentralized: agents react to events and communicate directly
- Hierarchical: Manager → Supervisors → Workers (3+ tiers)

**Communication dimension:**
- Synchronous: request-response, caller waits for result
- Asynchronous: message queue, caller continues immediately
- Blackboard: shared state agents read/write without direct messaging

**Collaboration dimension:**
- Pipeline: A → B → C (linear, simple)
- DAG: parallel execution with dependency graph
- Swarm: many agents with same role, load-balanced
- Team: different roles, coordinated toward shared goal

## Decision Criteria

**Choose centralized orchestration when:**
- Auditability is required — the full flow must be traceable through one component
- Workflow has complex branching logic that would be hard to distribute
- Consistency is more important than throughput
- Team is building the first version (easier to debug)

**Choose decentralized choreography when:**
- High throughput required, orchestrator would become a bottleneck
- Components need to evolve independently
- Eventual consistency is acceptable
- Events naturally model the domain (order placed, payment received, item shipped)

**Choose hierarchical when:**
- Problem decomposes naturally into sub-problems of similar structure
- Load needs to be distributed across worker pools
- Human-in-the-loop at mid-tier (supervisors review worker output)

## Parallelism

Use `Promise.all` / parallel task launch when tasks are **genuinely independent** — output of A does not feed B.

Latency of parallel group = latency of slowest task (not sum).

If three tasks take 3s each: sequential = 9s, parallel = 3s.

Always identify real dependencies before defaulting to sequential. Most classification/extraction tasks are independent.

## Bounded Contexts and Contracts

Each agent should have:
- Explicit input schema (what it accepts)
- Explicit output schema (what it returns)
- Declared capabilities (what it can do)
- No knowledge of other agents' internals

An Anti-Corruption Layer (ACL) is required when an agent interfaces with a legacy system whose domain model differs from the agent's model.

## Conflict Resolution

When agents reach contradictory conclusions:
- **Voting (majority)**: use for binary decisions, low-stakes
- **Weighted voting**: use when agents have different expertise levels; weight by confidence or domain relevance
- **Arbiter agent**: dedicated agent that receives conflicting outputs and reasons about the right answer; use for high-stakes decisions

## Saga Pattern for Distributed Transactions

When an operation spans multiple agents/services and must be rolled back if any step fails:

```
Step 1: Reserve inventory    → compensation: release inventory
Step 2: Process payment      → compensation: refund payment
Step 3: Schedule delivery    → compensation: cancel delivery
```

If Step 3 fails: run compensations in reverse order (3→2→1).

Prefer Saga over 2-Phase Commit (2PC) in agent systems — 2PC blocks resources and the coordinator is a single point of failure.

## Observability Requirement

Every message between agents must carry:
- `traceId`: constant for the full request
- `spanId`: unique to this operation
- `parentSpanId`: links to the calling operation

Without this, debugging multi-agent failures is nearly impossible.

## Perguntas diagnósticas
1. Are agent tasks independent or do they depend on each other's outputs?
2. Is the full flow auditable (must trace through one coordinator) or can it be distributed?
3. What happens if one agent fails mid-workflow — does the system need rollback?
4. Does the volume justify the orchestrator becoming a potential bottleneck?
5. Do agents need to share state, or do they pass messages?
6. How will you debug a failure that spans 3 agents?

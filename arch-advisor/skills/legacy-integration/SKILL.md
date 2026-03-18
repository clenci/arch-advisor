---
name: legacy-integration
description: "Use this skill when integrating AI agents with existing enterprise systems, legacy APIs, ERPs, CRMs, or when migrating from legacy to agent-based systems. Trigger when someone says 'we have existing systems the agent must use', 'we need to integrate with our ERP/CRM', 'legacy system has a different data model', 'how do we migrate gradually?', 'our legacy system is unstable', 'we need to call a SOAP service', 'agents and legacy systems must coexist'. Also trigger for: Anti-Corruption Layer, Saga pattern, Strangler Fig migration, REST adapter, message queue integration."
---

# Legacy System Integration

## Integration Pattern Selection

| Requirement | Pattern |
|---|---|
| Real-time, strong consistency, request-response | REST adapter |
| Near-real-time, decoupled, async processing | Message Queue (RabbitMQ/Kafka) |
| Large batch, high volume, scheduled | File Transfer |
| Complete audit history, replay capability | Event Sourcing |
| Distributed transaction with rollback | Saga Pattern |

## Anti-Corruption Layer (ACL)

**Always use an ACL when:**
- The legacy system's domain model differs from the agent's domain model
- The legacy system has known bugs or behaviors that must be filtered
- You do not want the agent's design to be influenced by legacy constraints

The ACL is a translation layer:
```
[Agent] ← [ACL: toDomain()] ← [Legacy System]
[Agent] → [ACL: toLegacy()] → [Legacy System]
```

`toDomain()`: maps legacy response to clean domain model
`toLegacy()`: maps agent's request to legacy format

The ACL must also:
- Normalize error codes to a consistent error taxonomy
- Sanitize and validate legacy data before passing to agents
- Log all translations for debugging

## REST Adapter Pattern

Every REST adapter needs:
- Retry with exponential backoff (for 5xx and network errors only — never retry 4xx)
- Timeout (always finite — typically 10–30s per call)
- Circuit breaker per endpoint or per downstream service
- Error mapping to domain error types

```typescript
async call(endpoint: string, payload: unknown): Promise<DomainResponse> {
  // retry: 3 attempts, backoff: 1s, 2s, 4s
  // timeout: 15s per attempt
  // circuit breaker: open after 5 failures in 60s
  // map HTTPError to DomainError
}
```

## Saga Pattern for Distributed Transactions

Use when an operation spans multiple services and must be rolled back if any step fails.

Choreography Saga (event-driven):
1. Service A completes step → publishes event
2. Service B listens, completes its step → publishes event
3. If B fails: publishes failure event, A reverses its step

Orchestration Saga (central coordinator):
1. Coordinator calls Service A
2. Coordinator calls Service B
3. If B fails: Coordinator calls A's compensation

For agent systems: prefer orchestration — easier to trace and debug.

**Compensation must be idempotent**: compensations may run more than once (retries, failures). Ensure they are safe to repeat.

## Strangler Fig Migration Pattern

Gradually replace a legacy system without a big-bang migration:

**Phase 1 (10% → new system):** route a small percentage to the new agent-based system; monitor closely
**Phase 2 (25%):** expand if Phase 1 metrics are acceptable
**Phase 3 (50%):** parallel operation; compare outcomes
**Phase 4 (100%):** complete cutover; keep legacy in read-only for 30 days

**Go/no-go criteria per phase:**
- Error rate < threshold (e.g., < 2%)
- Latency P95 within target
- Rollback plan: one config change reverts traffic to 0% on new system

**Automated rollback**: if error rate exceeds threshold for N minutes, automatically route 100% back to legacy.

## Handling Unstable Legacy Systems

Add circuit breakers per legacy endpoint. When legacy is down:
- Serve from cache if available (stale is better than error for read operations)
- Queue write operations (if eventually consistent is acceptable)
- Degrade gracefully: inform the user, do not crash the agent

Do not retry indefinitely. Set a maximum retry count and a dead-letter queue for failed operations.

## Perguntas diagnósticas
1. Does the legacy system's data model match the agent's domain model, or is translation required?
2. Is the legacy system stable, or does it have a history of timeouts and errors?
3. Are there distributed transactions that span the agent and one or more legacy systems?
4. Is a gradual migration possible, or must the switch be all-at-once?
5. What is the acceptable behavior when the legacy system is unavailable?
6. Does the legacy system have rate limits or maintenance windows that affect the integration?

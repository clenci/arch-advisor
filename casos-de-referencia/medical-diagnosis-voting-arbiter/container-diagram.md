# Container Diagram — Medical Diagnosis Voting+Arbiter

```mermaid
C4Container
  title Medical Diagnosis Voting+Arbiter — Container Diagram

  Person(doctor, "Doctor / Reviewer", "Submits clinical cases; reviews HITL-escalated diagnoses asynchronously")
  System_Ext(hospital, "Hospital System", "Submits clinical case payloads via HTTP; receives diagnosis results")
  System_Ext(emr, "EMR / Epic", "Future (12 months): receives committed diagnoses; source of rollback events")
  System_Ext(llm_proxy, "CI&T Flow Proxy", "LiteLLM — multi-provider LLM access (Haiku 4.5, Sonnet 4.6)")

  System_Boundary(mda, "Medical Diagnosis System") {
    Container(api, "DiagnosisAPI", "Node.js / HTTP", "Receives clinical case, initializes traceId + sagaId, returns diagnosis or HITL-pending status")
    Container(normalizer, "TerminologyNormalizer", "Node.js", "Embedding-similarity canonicalization of specialist outputs before voting — eliminates synonym false-conflicts")
    Container(specialists, "SpecialistPool", "Node.js — 3 Haiku 4.5 agents", "ClinicalSpecialist, RadiologistSpecialist, PharmacologySpecialist — parallel analysis via Promise.allSettled; temperature=0.3; structured JSON output")
    Container(voting, "VotingCoordinator", "Node.js", "Cascade: majority vote → weighted by confidence → consensus-threshold check; returns decision or escalates to ArbiterAgent")
    Container(arbiter, "ArbiterAgent", "Node.js — Sonnet 4.6", "Full-reasoning arbiter; receives all specialist outputs and reasoning chains; temperature=0; returns diagnosis with confidence or HITL flag")
    Container(hitl, "HITLGateway", "Node.js", "Creates checkpoint when confidence < 0.5; notifies reviewer; enforces TTL = 4h; resumes workflow on doctor input")
    ContainerDb(checkpoint_store, "CheckpointStore", "In-memory (dev) / Azure Cosmos DB (prod)", "Durable storage for HITL-pending cases; keyed by caseId + checkpointId; TTL = 4h")
    ContainerDb(audit_store, "AuditEventStore", "Append-only event log", "Event-sourced audit trail: DiagnosisRequested, SpecialistCompleted, VotingResolved, ArbiterInvoked, HITLCreated, HITLResumed, DiagnosisCommitted — enables time-travel audit for regulatory compliance")
  }

  Rel(hospital, api, "POST /diagnose — clinical case payload", "HTTPS/JSON")
  Rel(doctor, hitl, "POST /hitl/{checkpointId}/review — doctor decision", "HTTPS/JSON")
  Rel(api, specialists, "Dispatch case to 3 agents in parallel", "in-process / Promise.allSettled")
  Rel(specialists, llm_proxy, "LLM inference — structured diagnosis + confidence", "HTTPS/JSON")
  Rel(specialists, normalizer, "Raw specialist outputs", "in-process")
  Rel(normalizer, voting, "Normalized specialist outputs", "in-process")
  Rel(voting, arbiter, "Escalate — no consensus above threshold", "in-process")
  Rel(arbiter, llm_proxy, "LLM inference — full-reasoning arbitration", "HTTPS/JSON")
  Rel(arbiter, hitl, "Escalate — arbiter confidence < 0.5", "in-process")
  Rel(hitl, checkpoint_store, "Persist checkpoint", "SDK")
  Rel(api, audit_store, "Append events throughout pipeline", "SDK / append-only")
  Rel(api, emr, "Future: commit diagnosis to EMR (Saga step)", "REST/ACL")
```

## Component Notes

| Container | Key Design Decision |
|---|---|
| TerminologyNormalizer | Embedding-similarity canonicalization mandatory before vote aggregation — prevents string-comparison false conflicts (IAM synonym bug from exercise). +200–500ms latency accepted per resolved tension. |
| SpecialistPool | Promise.allSettled — never Promise.all. Partial failures (1 of 3 specialists fails) are handled per-agent: degraded voting with 2 agents, not total failure. |
| VotingCoordinator | Cascade terminates at first resolution: majority → weighted → threshold. Only calls ArbiterAgent when all deterministic levels fail (~30–40% of cases per exercise baseline). |
| ArbiterAgent | Full-reasoning context (all specialist outputs + reasoning chains). temperature=0 mandatory for reproducible arbitration. |
| HITLGateway | Async doctor review — workflow suspends. TTL = 4h. On expiry: stoppedBy="hitl_timeout", care team notified, case logged in AuditEventStore. |
| AuditEventStore | Append-only, never mutated. sagaId propagated in every event. Enables time-travel reconstruction for regulatory audit (HIPAA-equivalent). |
| CheckpointStore | MemorySaver = development only. Production requires durable storage (Azure Cosmos DB) — process restart must not lose pending HITL cases. |
```

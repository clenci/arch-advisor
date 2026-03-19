# Technical-Document-Critic-Agent — Container Diagram

```mermaid
C4Container
  title Technical-Document-Critic-Agent — Container Diagram

  Person_Ext(dev, "Developer", "Consumes the Markdown critique report")
  System_Ext(cicd, "CI/CD Pipeline", "Invokes agent.analyze() on merge/push trigger")

  System_Boundary(agent, "Technical-Document-Critic-Agent") {

    Container(orchestrator, "Orchestrator", "TypeScript/Node.js", "Coordinates the 4-stage pipeline; enforces $0.30 budget ceiling; accumulates totalCost; determines stop condition (threshold / costBudget / maxIterations)")

    Container(perception, "Perception Stage", "TypeScript", "Loads Markdown file from disk via loadDocument(); chunks content via chunkDocument(); no format adapter — Markdown only")

    Container(decision, "Decision Stage", "TypeScript", "Classifier (Haiku 4.5): detects document type and domain, produces focusAreas. LLM Router: assigns Sonnet 4.6 or Haiku 4.5 per stage based on stage identity and budget residual")

    Container(memory, "Memory Stage", "TypeScript", "STM: passes classification context (type, domain, focusAreas) forward within pipeline run. LTM (in-memory): indexes past analyses by domain; enriches current report via ltmContext injection. Scoped to process lifetime.")

    Container(reflection, "Reflection Stage", "TypeScript", "ReportGenerator (Sonnet 4.6): produces initial critique report. Critic (Sonnet 4.6): scores dimensions and produces isAcceptable flag. Reviser (Sonnet 4.6 or Haiku 4.5 under budget pressure): applies targeted corrections. Loop: max 3 iterations.")

    ContainerDb(ltm_store, "LTM Store", "In-Memory Map", "Domain → past analysis index. Ephemeral per process — resets on each CI/CD job invocation.")

    Container(logger, "Structured Logger", "TypeScript", "Emits JSON log per LLM event: traceId, agentId, action, durationMs, tokensUsed, costUsd, stoppedBy")
  }

  Rel(cicd, orchestrator, "Invokes agent.analyze(filePath)", "Function call / Node.js module")
  Rel(orchestrator, perception, "Passes filePath", "In-process")
  Rel(perception, decision, "Passes chunks + raw content", "In-process")
  Rel(decision, memory, "Passes classification (type, domain, focusAreas)", "In-process")
  Rel(memory, ltm_store, "Reads/writes domain index", "In-memory")
  Rel(memory, reflection, "Passes enriched context (STM + ltmContext)", "In-process")
  Rel(reflection, orchestrator, "Returns final report + metadata (score, iterations, stoppedBy, totalCost)", "In-process")
  Rel(orchestrator, logger, "Emits structured log per LLM call", "In-process")
  Rel(orchestrator, dev, "Returns critique report (Markdown)", "File / stdout")
```

## Component Notes

| Component | Model | Notes |
|---|---|---|
| Classifier | Haiku 4.5 | Simple classification task — domain-specific signals sufficient; ~10× cheaper than Sonnet |
| LLM Router | — (deterministic) | No LLM call — routes by stage name + budget residual; Reviser → Haiku when totalCost/budget > 0.70 |
| ReportGenerator | Sonnet 4.6 | Complex synthesis — requires full capability |
| Critic | Sonnet 4.6 | Qualitative evaluation — same-model bias risk; acceptable for this scope |
| Reviser | Sonnet 4.6 → Haiku 4.5 | Switches to Haiku when budget > 70% consumed |
| LTM Store | In-memory Map | Ephemeral; value only when ≥2 docs of same domain processed in the same job |

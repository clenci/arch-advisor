---
name: security-governance
description: "Use this skill when discussing security, compliance, risk management, governance, or responsible AI for agent systems. Trigger when someone says 'we need LGPD compliance', 'how do we handle prompt injection?', 'what are the risks of using LLMs?', 'we need an audit trail', 'how do we govern AI models?', 'we process sensitive data', 'the agent can take real-world actions — what are the risks?', 'we need to explain agent decisions'. Also trigger for: TRiSM, AI Act, GDPR, hallucination risk, cost overrun, data leakage, bias detection."
---

# Security, Governance, and Risk Management

## TRiSM Framework (Trust, Risk, Security Management)

**Trust Layer**: can stakeholders understand and rely on the system?
- Explainability: agents log reasoning steps, not just outputs
- Transparency: decision criteria are documented and accessible
- Fairness: outputs are monitored for disparate impact across demographic groups

**Risk Layer**: what can go wrong and how likely?
- Identify risks, score them (likelihood × impact), track residual risk after mitigations
- Review risk register quarterly or after major system changes

**Security Layer**: how is the system protected?
- Model security: prompt injection prevention, output sanitization
- Data security: encryption at rest and in transit, PII handling
- Infrastructure security: secrets management, least-privilege access, API key rotation
- Operational security: audit logs, incident response runbooks

## Risk Catalog for LLM Systems

| Risk | Likelihood | Impact | Primary Mitigation |
|---|---|---|---|
| Hallucination | High | Varies | RAG with faithfulness check; critic layer |
| Prompt injection | Medium | High | Input sanitization; sandboxing; output validation |
| Cost overrun | Medium | High | Per-request budget limits; circuit breaker; alerts |
| Data leakage via prompt | Medium | High | PII detection before LLM; data masking |
| Bias / disparate impact | Medium | Medium | Output monitoring; demographic parity checks |
| Model drift / quality degradation | Low | High | Continuous evals; quality gate alerts |
| Provider outage | Medium | High | Multi-provider fallback; circuit breaker |

## Mandatory Controls for Agents That Take Actions

If an agent can create, update, delete, or send anything in production:
1. **Dry-run mode**: simulate the action and show the result before executing
2. **Human-in-the-loop checkpoint**: require approval for high-impact actions
3. **Reversibility**: prefer reversible actions; log all irreversible actions with full context
4. **Budget guardrails**: hard limit on cost/tokens per session and per day

## Compliance Requirements

**LGPD / GDPR**:
- Right to access: full data export on request
- Right to deletion: soft delete + anonymization + purge schedule
- Right to correction: update stored PII on request
- Right to portability: machine-readable export
- Consent: record purpose, timestamp, and revocation capability

**AI Act (EU) — risk classification**:
- High-risk AI (hiring, credit scoring, critical infrastructure): conformity assessment, human oversight, transparency requirements
- Limited risk: disclosure requirement (user must know they interact with AI)

## Model Governance

Lifecycle: Development → Testing → Approved → Production → Deprecated

Requirements per stage:
- Testing: eval suite must pass before promotion
- Approved: model card documenting intended use, limitations, benchmark scores
- Production: monitoring active, rollback plan documented
- Deprecated: migration path communicated 30+ days before cutoff

## Incident Response

Severity levels:
- P1 (Critical): agent takes unauthorized action, data leakage, >50% error rate
- P2 (High): quality degradation >20%, cost spike >3×, provider outage
- P3 (Medium): individual errors, slow degradation

Auto-containment for P1:
1. Disable affected agent
2. Revoke compromised API keys/tokens
3. Activate circuit breaker on affected provider
4. Alert on-call team within 5 minutes

Post-incident: write post-mortem within 48h. Root cause → timeline → contributing factors → corrective actions.

## Perguntas diagnósticas
1. Does the agent take irreversible real-world actions (send emails, process payments, modify records)?
2. Is PII or regulated data (health, financial) in the context window?
3. What jurisdiction applies — LGPD, GDPR, HIPAA, AI Act?
4. Who is accountable when the agent makes an incorrect decision?
5. Is there a process for model updates — testing, approval, rollback?
6. How will the team detect and respond to quality degradation in production?

# Casos de Referência — arch-advisor

Execuções completas do arch-advisor (v4.2.0) usadas para validar o plugin e servir como referência de qualidade.

## Estrutura de cada caso

```
<caso>/
├── session.md             ← extrato do arch-session.md (discovery, tensões, stress test, padrões)
├── container-diagram.md   ← C4 Container Diagram (Mermaid)
├── adr-001-*.md           ← Architecture Decision Record principal
├── decision-matrix.md     ← Matriz de decisão ponderada (3 opções × critérios)
└── nfr-checklist.md       ← NFR Checklist com targets concretos
```

---

## technical-document-critic-agent

**Domínio**: Revisão de documentação técnica — pipeline single-agent com Reflection Loop
**Arquitetura escolhida**: Option B — Single-Agent Pipeline with Budget-Controlled Reflection Loop
**Plugin versão**: 4.2.0 (v6 da sessão de testes)
**Flags internos**: `hybrid-decision-candidate=false`, `hitl-candidate=false`, `saga-candidate=false`
**Pattern Deepening**: 4/12 blocos disparados (PEC, LLM Routing, Response Caching, Feedback Loop)
**Uso principal**: caso de referência canônico do arch-advisor; não exercita os flags novos de v4.2.0

Artefatos gerados também em: `/Users/cezargl/ai/claude-code/.claude/arch-outputs/technical-document-critic-agent/`

---

## medical-diagnosis-voting-arbiter

**Domínio**: Suporte a diagnóstico médico — 3 agentes especialistas paralelos, votação em cascata, arbiter LLM, revisão humana assíncrona
**Arquitetura escolhida**: Option B — Multi-Agent Voting+Arbiter with Cascade Consensus
**Plugin versão**: 4.2.0
**Flags internos**: `hybrid-decision-candidate=true`, `hitl-candidate=true`, `saga-candidate=true`, `event-sourcing-candidate=true`
**Follow-ups disparados**: Group B mandatory (bursty), Group C HITL priority (async approval, TTL=4h), Group D Hybrid DE priority (50–60% deterministic)
**Pattern Deepening**: 7/12 blocos disparados (Hybrid DE, Voting+Arbiter, Saga, HITL+Checkpointing, LLM Routing, Bulkhead, Feedback Loop)
**Uso principal**: validação dos flags HITL e Hybrid DE introduzidos em v4.2.0; caso mais rico em padrões

Baseado no exercício: `/Users/cezargl/ai/estudos/exercicios/modulo-03/exercicio-04/`
Artefatos gerados também em: `/Users/cezargl/ai/claude-code/.claude/arch-outputs/medical-diagnosis-voting-arbiter/`

---

## Como usar como referência

- Para avaliar uma nova versão do arch-advisor: re-executar com `teste-case.md` (technical-document-critic-agent) e comparar com a rubrica em `COMPARACAO-VARIANTES.md`
- Para validar flags HITL/Hybrid DE: re-executar com o caso medical-diagnosis e verificar se os 7 blocos de pattern deepening disparam corretamente
- Para onboarding: os artefatos de medical-diagnosis são os mais completos (7 padrões, 4 flags, seção Security no NFR)

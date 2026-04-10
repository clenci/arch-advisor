# arch-advisor — contexto de desenvolvimento

## O que é este repositório

Plugins pessoais para Claude Code. O plugin principal é o `arch-advisor`: um advisor interativo de arquitetura para sistemas multi-agente LLM, invocado via `/arch-advisor`.

## Estrutura

```
meus-plugins/
├── .claude-plugin/
│   └── marketplace.json          ← registro do marketplace local
├── arch-advisor/                 ← plugin principal (v4.2.0, versão atual)
│   ├── .claude-plugin/
│   │   └── plugin.json
│   ├── commands/
│   │   └── arch-advisor.md       ← command principal (todas as fases)
│   ├── skills/                   ← 15 skills (14 de domínio + pattern-deepening)
│   │   ├── pattern-deepening/    ← adicionada em v4.2.0
│   │   ├── agent-internal-architecture/
│   │   ├── architecture-documentation/
│   │   ├── data-memory-storage/
│   │   ├── integration-protocols/
│   │   ├── legacy-integration/
│   │   ├── llm-frameworks/
│   │   ├── llm-selection-routing/
│   │   ├── multiagent-orchestration/
│   │   ├── observability-slo/
│   │   ├── omnichannel-architecture/
│   │   ├── rag-strategy/
│   │   ├── security-governance/
│   │   ├── testing-quality/
│   │   └── when-to-use-agents/
│   ├── hooks/
│   │   ├── hooks.json
│   │   └── session_start.py
│   └── CHANGELOG.md
├── casos-de-referencia/          ← execuções validadas para avaliação e regressão
│   ├── README.md
│   ├── technical-document-critic-agent/   ← v6, 87/90, flags todos false
│   │   ├── session.md
│   │   ├── container-diagram.md
│   │   ├── adr-001-*.md
│   │   ├── decision-matrix.md
│   │   └── nfr-checklist.md
│   └── medical-diagnosis-voting-arbiter/  ← v7, 89/90, todos os 4 flags disparados
│       ├── session.md
│       ├── container-diagram.md
│       ├── adr-001-*.md
│       ├── decision-matrix.md
│       └── nfr-checklist.md
├── COMPARACAO-VARIANTES.md       ← rubrica de avaliação comparativa (18 dimensões, /90)
├── relatorio-comparativo-arch-advisor.md  ← relatório v1→v7 com scores e análise completa
└── teste-case.md                 ← caso de uso canônico (Technical-Document-Critic-Agent)
```

## Como instalar o plugin

```
/plugin marketplace add /Users/cezargl/ai/meus-plugins
/plugin install arch-advisor@meus-plugins
```

## Fluxo do plugin (v4.2.0)

1. **Phase 1 — Discovery**: Grupos A–E com follow-ups adaptativos; flags silenciosos `hybrid-decision-candidate` e `hitl-candidate` calculados em Group A
2. **Phase 1.5 — Tension Resolution**: uma tensão por vez, consequence framing, aguarda resposta
3. **Phase 1.6 — Stress Test**: 3 perguntas (10x escala, budget −50%, requisitos futuros)
4. **Phase 1.7 — Summary Review**: resumo estruturado + 2 meta-perguntas ao usuário
5. **Phase 2 — Requirements Analysis**: padrões, ambiguidades, riscos, constraints impact
6. **Phase 3 — Architecture Proposal**: 3 opções (MVA / Balanced / Next Scale Tier)
7. **Phase 3.5 — Pattern Deepening (visível)**: apresenta ao usuário os padrões detectados na arquitetura escolhida; invoca `arch-advisor:pattern-deepening`; produz blocos por padrão com decisões de design concretas e constraint crítico
8. **Phase 3.6 — Domain Deepening (silenciosa)**: invoca até 2 skills de domínio antes dos artefatos
9. **Phase 4 — Artifact Generation**: C4 diagram, ADR, Decision Matrix, NFR Checklist; invoca explicitamente `architecture-documentation`, `observability-slo`, `testing-quality`, e `security-governance` (condicional)
10. **Phase 5 — Refinement Loop**: Step 1 = revisão dos artefatos; Step 2 = deepening menu mapeado para skills

## Estado atual e lacunas conhecidas

### Lacunas resolvidas

**1. Follow-up do Grupo B** — RESOLVIDO (v4.0.0)
- A condição `"if any answer is underspecified"` foi substituída por verificação positiva explícita: se o caller é sistema externo ou processo automatizado E o padrão de chegada (steady vs. bursty) não foi confirmado explicitamente → follow-up é obrigatório.

**2. Amplitude estrutural das opções** — RESOLVIDO (v4.0.0)
- Option C deve introduzir pelo menos um componente de infraestrutura não presente em Option B (fila durável, store externo, worker process separado). Previne dois tiers de complexidade similar.

**3. `agent-internal-architecture` trigger** — RESOLVIDO (v4.1.0)
- Critério de disparo explicitado: dispara quando arquitetura inclui Reflection Loop, pipeline multi-estágio, STM/LTM, state machine explícita ou iteração controlada por budget.

**4. Flags HITL e Hybrid DE não testados** — RESOLVIDO (v4.2.0, validado em v7)
- Ambos os flags (`hitl-candidate` e `hybrid-decision-candidate`) validados no caso medical-diagnosis-voting-arbiter (89/90).
- Group C HITL follow-up: distingue aprovação síncrona vs. assíncrona; async ativa HITL+Checkpointing no Pattern Deepening.
- Group D Hybrid DE follow-up: coleta fração de casos determinísticos para decidir se Rule Engine + LLM cascade é justificado.

**5. `arch-advisor:pattern-deepening` skill** — RESOLVIDO (v4.2.0)
- 12 blocos implementados; 4/12 dispararam no caso tech-doc-critic (sem falsos positivos); 7/12 no caso medical-diagnosis.

### Lacuna remanescente (única)

**5c — `agent-internal-architecture` não oferecido no deepening menu para cascade state machines** — PRIORIDADE ALTA (1 ponto para 90/90)

Score atual: 4/5. O critério de inclusão do deepening menu (Phase 5 Step 2) cobre "Reflection Loop, multi-stage pipeline, STM/LTM, state machine explícita, iteração controlada por budget" — mas não cobre explicitamente cascade com múltiplos estágios determinísticos (ex: VotingCoordinator com majority → weighted → threshold → arbiter). O caso medical-diagnosis tem exatamente essa estrutura e o critério não a capturou.

**Fix pendente em `arch-advisor.md`:** expandir o critério de inclusão para:
> "Include if the chosen architecture has a VotingCoordinator, cascade strategy, or any internal component with a multi-stage deterministic pipeline — not only single agents with reflection loops."

### O que foi validado e funciona

- Tension Resolution com consequence framing gera componentes arquiteturais novos (BudgetMonitor, CheckpointStore emergiram das tensões, não dos requisitos)
- Stress Test calibra thresholds com dados do usuário (vs. estimativas genéricas)
- Invocações explícitas de skills na Phase 4 produzem diferença mensurável e rastreável nos artefatos
- Deepening menu (Phase 5 Step 2) gera detalhe de implementação que o fluxo principal não alcança
- Phase 3.5 Pattern Deepening: 4/12 blocos corretos no tech-doc-critic; 7/12 no medical-diagnosis; 0 falsos positivos em ambos
- Flags `hybrid-decision-candidate` e `hitl-candidate`: validados no caso medical-diagnosis; todos os 4 flags dispararam corretamente

## Scores por versão

| Versão | Score | Caso validado |
|---|---|---|
| v1.0.0 | 40/90 | Technical-Document-Critic-Agent |
| v2.0.0 | 46/90 | Technical-Document-Critic-Agent |
| v3.0.0 | 54/90 | Technical-Document-Critic-Agent |
| v4.0.0 | 82/90 | Technical-Document-Critic-Agent |
| v4.1.0 | 87/90 | Technical-Document-Critic-Agent |
| v4.2.0 (v6) | 87/90 | Technical-Document-Critic-Agent (regressão) |
| v4.2.0 (v7) | 89/90 | Medical-Diagnosis-Voting-Arbiter |

## Referências

- `arch-advisor/CHANGELOG.md` — histórico de versões v1→v4.2.0
- `COMPARACAO-VARIANTES.md` — rubrica completa para avaliar novas versões (18 dimensões, escala /90)
- `relatorio-comparativo-arch-advisor.md` — análise comparativa v1→v7 com scores, citações e lacunas
- `casos-de-referencia/` — execuções validadas (tech-doc-critic 87/90; medical-diagnosis 89/90)
- Originais dos artefatos: `/Users/cezargl/ai/claude-code/.claude/arch-outputs/`

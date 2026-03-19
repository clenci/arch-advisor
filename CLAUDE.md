# arch-advisor — contexto de desenvolvimento

## O que é este repositório

Plugins pessoais para Claude Code. O plugin principal é o `arch-advisor`: um advisor interativo de arquitetura para sistemas multi-agente LLM, invocado via `/arch-advisor`.

## Estrutura

```
meus-plugins/
├── .claude-plugin/
│   └── marketplace.json          ← registro do marketplace local
├── arch-advisor/                 ← plugin único (v4, baseline atual)
│   ├── .claude-plugin/
│   │   └── plugin.json
│   ├── commands/
│   │   └── arch-advisor.md       ← command principal (todas as fases)
│   ├── skills/                   ← 14 skills de domínio
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
├── COMPARACAO-VARIANTES.md       ← rubrica de avaliação comparativa (18 dimensões, /90)
├── relatorio-comparativo-arch-advisor.md  ← relatório v1→v4 sobre o mesmo caso de uso
└── teste-case.md                 ← caso de uso de referência (Technical-Document-Critic-Agent)
```

## Como instalar o plugin

```
/plugin marketplace add /Users/cezargl/ai/meus-plugins
/plugin install arch-advisor@meus-plugins
```

## Fluxo do plugin (v4)

1. **Phase 1 — Discovery**: Grupos A–E com follow-ups adaptativos
2. **Phase 1.5 — Tension Resolution**: uma tensão por vez, consequence framing, aguarda resposta
3. **Phase 1.6 — Stress Test**: 3 perguntas (10x escala, budget −50%, requisitos futuros)
4. **Phase 1.7 — Summary Review**: resumo estruturado + 2 meta-perguntas ao usuário
5. **Phase 2 — Requirements Analysis**: padrões, ambiguidades, riscos, constraints impact
6. **Phase 3 — Architecture Proposal**: 3 opções (MVA / Balanced / Next Scale Tier)
7. **Phase 3.5 — Pattern Deepening (visível)**: apresenta ao usuário os padrões detectados na arquitetura escolhida; invoca `pattern-deepening` skill; produz blocos por padrão com decisões de design concretas e constraint crítico
8. **Phase 3.6 — Domain Deepening (silenciosa)**: invoca até 2 skills de domínio antes dos artefatos
9. **Phase 4 — Artifact Generation**: C4 diagram, ADR, Decision Matrix, NFR Checklist; invoca explicitamente `architecture-documentation`, `observability-slo`, `testing-quality`, e `security-governance` (condicional)
10. **Phase 5 — Refinement Loop**: Step 1 = revisão dos artefatos; Step 2 = deepening menu mapeado para skills

## Estado atual e lacunas conhecidas

### Lacunas corrigidas (v4.0.0)

**1. Follow-up do Grupo B** — CORRIGIDO
- A condição `"if any answer is underspecified"` foi substituída por verificação positiva explícita: se o caller é sistema externo ou processo automatizado E o padrão de chegada (steady vs. bursty) não foi confirmado explicitamente → follow-up é obrigatório, não condicional.

**2. Amplitude estrutural das opções (Lacuna 2)** — CORRIGIDO
- Adicionada instrução explícita em Phase 3: Option C deve introduzir pelo menos um componente de infraestrutura não presente em Option B (fila durável, store externo, worker process separado). Previne dois tiers de complexidade similar.

**3. Phase 3.5 — `agent-internal-architecture`** — CORRIGIDO
- Critério de disparo explicitado: "invoke this whenever a Reflection Loop or multi-stage internal pipeline is part of the chosen architecture". Deepening menu também tem critérios explícitos de inclusão por domínio.

### Lacunas pendentes

**Phase 3.5 validada no caso de referência (v6) — mas flags HITL e Hybrid DE não testados** — PRIORIDADE MÉDIA
- Caso Technical-Document-Critic-Agent não exercita `hybrid-decision-candidate` nem `hitl-candidate` — flags = false para este caso
- Para validar os follow-ups de Grupo C (HITL) e Grupo D (Hybrid DE), é necessário um caso com ação primária "classify/transact/route" ou output com ação real no mundo
- Sugestão de caso de teste: sistema de triagem de chamados (classify) com aprovação humana antes de executar ação (hitl) — exercitaria ambos os flags e blocos Voting+Arbiter, HITL+Checkpointing, Saga

**`arch-advisor:pattern-deepening` skill invocável apenas em sessões com plugin 4.2.0 carregado desde o início**
- Plugin atualizado manualmente no cache para 4.2.0 em 2026-03-19; nova sessão deve ter o skill disponível
- Verificar: `/plugin install arch-advisor@meus-plugins` para garantir que 4.2.0 é a versão ativa

### O que foi validado e funciona

- Tension Resolution com consequence framing gera componentes arquiteturais novos (BudgetMonitor, CheckpointStore emergiram das tensões, não dos requisitos)
- Stress Test calibra thresholds com dados do usuário (vs. estimativas genéricas)
- Invocações explícitas de skills na Phase 4 produzem diferença mensurável e rastreável nos artefatos
- Deepening menu (Phase 5 Step 2) gera detalhe de implementação que o fluxo principal não alcança
- Phase 3.5 Pattern Deepening (v4.2.0): 4/12 blocos dispararam corretamente para o caso de referência; 8/12 silenciosos sem falsos positivos; conteúdo dos blocos é coerente e anterior aos artefatos

## Referências

- `CHANGELOG.md` — histórico de versões e o que mudou em cada uma
- `COMPARACAO-VARIANTES.md` — rubrica completa para avaliar novas versões (18 dimensões, escala /90)
- `relatorio-comparativo-arch-advisor.md` — análise comparativa v1→v6 com scores, citações e lacunas transversais
- Artefatos de referência: `/Users/cezargl/ai/teste-plugin/` — execuções v4-old e v4; `/Users/cezargl/ai/claude-code/.claude/arch-outputs/technical-document-critic-agent/` — execução v6 (4.2.0)

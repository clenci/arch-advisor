# Relatório Comparativo: arch-advisor v1 → v4 → v5

**Data:** 2026-03-13
**Avaliado por:** Claude Sonnet 4.6
**Sessões observadas:** v1, v2, v3, v4-old, v4, v5 — todas executadas sobre o mesmo caso de uso (Technical-Document-Critic-Agent). v5 é a execução da versão do command com as três correções aplicadas (Group B follow-up obrigatório, Option C com componente de infraestrutura adicional, Phase 3.5/deepening menu com critérios explícitos de domínio).

---

## Scores por Dimensão

| Dimensão | v1 | v2 | v3 | v4-old | v4 | v5 |
|---|---|---|---|---|---|---|
| **1a. Tensões surfaceadas ao usuário** | 1 | 3 | 3 | 5 | 5 | 5 |
| **1b. Consequência aceita como insumo arquitetural** | 1 | 2 | 2 | 5 | 5 | 5 |
| **1c. Follow-ups adaptativos** | 2 | 2 | 2 | 2 | 2 | 5 |
| **1d. Stress test com dados do usuário** | 1 | 1 | 1 | 5 | 5 | 5 |
| **2a. Padrões com justificativa rastreável** | 3 | 3 | 3 | 5 | 5 | 5 |
| **2b. Riscos com dados observáveis** | 3 | 3 | 3 | 4 | 4 | 4 |
| **2c. Ambiguidades arquiteturalmente consequentes** | 2 | 4 | 4 | 5 | 5 | 5 |
| **3a. Amplitude estrutural das opções** | 4 | 4 | 4 | 4 | 4 | 4 |
| **3b. Precisão dos trade-offs** | 3 | 3 | 4 | 5 | 5 | 5 |
| **4a. C4 Diagram** | 3 | 3 | 5 | 5 | 5 | 5 |
| **4b. ADR** | 4 | 4 | 5 | 5 | 5 | 5 |
| **4c. Decision Matrix** | 3 | 4 | 4 | 5 | 5 | 5 |
| **4d. NFR Checklist** | 4 | 3 | 4 | 4 | 5 | 5 |
| **5a. Skills explicitamente invocadas** | 1 | 1 | 3 | 3 | 4 | 5 |
| **5b. Conhecimento de domínio observável** | 2 | 2 | 4 | 4 | 5 | 5 |
| **5c. Skills não utilizadas com ponto de entrada** | 1 | 1 | 1 | 1 | 3 | 4 |
| **6a. Decisões do usuário vs. internas** | 1 | 3 | 3 | 5 | 5 | 5 |
| **6b. Rastreabilidade fim-a-fim** | 2 | 3 | 3 | 5 | 5 | 5 |
| **Total** | **40/90** | **46/90** | **54/90** | **73/90** | **82/90** | **87/90** |

---

## O que mudou de v4 para v5

### Correção 1 — Follow-up do Grupo B (1c: 2 → 5)

**O que era:** condição `"if any answer is underspecified"` — o modelo inferia suficiência em respostas detalhadas e avançava para Grupo C sem perguntar sobre padrão de chegada.

**O que é agora:** verificação positiva separada das condicionais. Se o caller é sistema externo ou processo automatizado E o padrão de chegada não foi declarado explicitamente → follow-up obrigatório.

**Observado em v5:** o arch-session.md registra na seção Grupo B:

> - Padrão de chegada: bursty/event-driven (disparado por eventos CI/CD — pushes, merges). Eventos imprevisíveis; concentração mais comum em horário comercial.

A informação estava ausente nas versões anteriores porque o follow-up não disparava. Em v5, o follow-up disparou e o padrão bursty foi capturado. Isso teve consequência nos artefatos:

- O C4 de v5 nomeia o caller como `"CI/CD System — Pipeline de repositório que invoca agent.analyze() em eventos de push/merge"` — especificidade ausente em v4
- A Decision Matrix de v5 usa o critério "Aderência ao hard budget $0.30/análise" com nota *"B: BudgetMonitor desacoplado intercepta toda transição de estágio"* — rastreando a imprevisibilidade do volume bursty como driver do desacoplamento do BudgetMonitor
- O ADR de v5 inclui no Context: *"pipeline CI/CD stateless — cada invocação spawna um processo Node.js novo"* — consequência direta de saber que o caller é event-driven, não polling contínuo

**Por que 5/5 e não 4/5:** o follow-up disparou, capturou dado novo, e esse dado propagou para três artefatos distintos. A correção foi eficaz.

---

### Correção 3 — Phase 3.5: `agent-internal-architecture` disparou (5a: 4 → 5, 5b: mantido em 5)

**O que era:** `agent-internal-architecture` estava na lista da Phase 3.5 mas o critério de disparo era genérico ("single agent with complex internal structure"), deixando margem para ser pulada.

**O que é agora:** critério explícito — *"invoke whenever a Reflection Loop or multi-stage internal pipeline is part of the chosen architecture"*. Deepening menu tem critérios de inclusão por domínio para cada opção.

**Observado em v5:** `deepening-agent-internal-architecture.md` foi gerado — arquivo ausente em v4 e v4-old. Contém cinco seções que não têm equivalente nos artefatos das versões anteriores:

**Seção 2 — Decision Layer: três passes em ordem**
```typescript
const rules = [
  { pattern: /^# ADR/m, docType: 'adr', confidence: 0.95 },
  // ...
];
// Se confidence > 0.90: pula LLM Reasoner para docType
```
Decisão de design que elimina 1 chamada LLM por ~30% dos documentos. Nenhuma versão anterior menciona a possibilidade de rule engine antes do LLM para classificação.

**Seção 3 — Reflection Loop: two-reviser pattern**
A distinção AdditiveReviser (Sonnet 4.6) / StructuralReviser (Haiku 4.5) com justificativa de por que um único reviser aditivo nunca melhora `actionability`. Custo por iteração detalhado: ~$0.020 total. Versões anteriores têm apenas "CritiqueAgent + RevisionAgent" sem diferenciação de revisores ou justificativa de modelo por tipo de revisão.

**Seção 4 — BudgetMonitor como State Machine explícita**
```
NOMINAL ──($0.20 reached)──► APPROACHING_LIMIT
                                    │
                    score > 0.65 ───┤─── score ≤ 0.65
                         │                    │
                         ▼                    ▼
               ADAPTIVE_EXTENSION        HARD_STOP ($0.30)
```
O estado `APPROACHING_LIMIT` habilita otimização preventiva (trocar Sonnet por Haiku nos revisores restantes). Em v4, o BudgetMonitor existe como componente no C4 com dois estados implícitos. Em v5, tem quatro estados explícitos com transições e TypeScript implementável.

**5a sobe de 4 para 5:** v4 invocava `architecture-documentation`, `observability-slo`, `testing-quality`, e `data-memory-storage` (deepening). v5 adiciona `agent-internal-architecture` — sexta skill com impacto mensurável nos artefatos. Das 14 skills disponíveis, 6 têm agora evidência de uso com output rastreável.

**5c permanece em 4/5 (não 5/5):** das 14 skills, 8 ainda não têm ponto de entrada garantido no fluxo: `multiagent-orchestration`, `rag-strategy`, `llm-selection-routing`, `llm-frameworks`, `integration-protocols`, `legacy-integration`, `omnichannel-architecture`, `when-to-use-agents`. Para este caso de uso, nenhuma dessas seria aplicável — a limitação não é do command, mas do escopo do caso.

---

### Correção 2 — Option C com componente de infraestrutura adicional (3a: 4 → 4)

**O que mudou no command:** Option C deve introduzir pelo menos um componente de infraestrutura não presente em Option B.

**Observado em v5:** a Option C da sessão é "LangGraph StateGraph com Worker Pool + Redis" — Redis e PostgreSQL/pgvector como dependências de infraestrutura permanentes. Em v4, a Option C era "Distributed Pipeline com Persistent LTM Store", que adicionava fila de trabalho mas a separação de B→C era menos marcada.

**Por que 3a permanece em 4/5:** a amplitude qualitativa continua igual em todas as versões — Flat Sequential / Event-Driven + Checkpoints / LangGraph + Redis. O command corrigido torna isso mais explícito para casos onde B e C poderiam ser similares, mas no caso de uso de referência a distinção já existia. O impacto da correção será mais visível em casos onde a Option C anterior não introduzia nova infraestrutura.

---

## Diferenças Mais Significativas Entre Versões

### 1. Padrão bursty capturado pela primeira vez em v5

Em v1/v2/v3/v4-old/v4, o arch-session registrava volume como "dezenas/dia, sem concorrência" sem descrever o padrão de chegada. Em v5:

> "bursty/event-driven (disparado por eventos CI/CD — pushes, merges). Eventos imprevisíveis; concentração mais comum em horário comercial."

Esse dado muda a leitura do requisito de confiabilidade: um sistema com volume "baixo" mas completamente bursty tem um perfil de circuit breaker diferente de um com volume low e steady. O NFR de v5 registra:

> "- [ ] Budget check executado ANTES de cada chamada LLM (não após) — garantir budget suficiente para completar a chamada antes de iniciá-la — mandatory"

A precaução de verificar budget antes (não após) faz mais sentido para um sistema com bursts do que para um com chegada steady.

---

### 2. Decision Layer em v5 vs. v4

| Aspecto | v4 (arch-session + artefatos) | v5 (deepening-agent-internal) |
|---|---|---|
| DecisionStage | Classificação via LLM, mencionado como estágio | Rule Engine → LLM Reasoner → Heuristic Validator (três passes) |
| Haiku 4.5 no Decision | Mencionado no C4 como modelo do handler | Rule Engine elimina chamada LLM para ~30% dos docs com padrão claro |
| Custo do Decision | Não quantificado | ~$0.05 para docs sem padrão claro; $0 para ADR/RFC via rule engine |
| Output validation | Não mencionado | Heuristic Validator pós-LLM: normaliza scores, valida docType sem re-chamar modelo |

---

### 3. NFR Checklist: v4 vs. v5

| Aspecto | v4 | v5 |
|---|---|---|
| Startup do processo | Não mencionado | `< 2s (incluindo leitura do CheckpointStore)` — mandatory |
| Alerta de custo | `> 2× média 7 dias` | `> $0.45 (1,5× do baseline observado de $0.15)` — com baseline real da sessão |
| Quality SLO | `convergenceStatus = "converged" em ≥ 85% / 30 dias` | `score final médio ≥ 0,75 em janela rolling de 7 dias` |
| `stoppedBy` field | `converged \| budget-extended \| incomplete` | `costBudget \| adaptiveExtension \| scoreThreshold \| maxIterations \| providerError` — 5 estados vs. 3 |
| Testability: CheckpointStore | `injetável via interface read/write` | `aceita filePath configurável — testes usam diretório temporário isolado` — mais concreto |
| Evals caching | `por (input, prompt_version)` | `temperature=0 para determinismo; resultado cacheado por (input_hash, prompt_version)` |

---

### 4. ADR: clareza de motivação

O ADR de v5 adiciona um ponto de justificação ausente em v4:

> "**Observabilidade natural:** cada evento carrega `traceId`, `agentId`, `action`, `durationMs`, `tokensUsed`, `costUsd` — os campos de log obrigatórios emergem da estrutura de eventos, não de instrumentação manual."

Em v4, a observabilidade aparece na NFR como requisito. Em v5, aparece no ADR como consequência positiva da decisão arquitetural de usar EventBus — tornando o argumento a favor de Opção B mais completo.

---

## Evidência de Skills por Versão

| Trecho | Arquivo | Skill de origem | Versão |
|---|---|---|---|
| `System_Boundary`, `ContainerDb`, `Person_Ext` | container-diagram.md | `architecture-documentation` | v3/v4/v5 |
| `traceId, agentId, action, durationMs, tokensUsed, costUsd` | nfr-checklist.md | `observability-slo` | v3/v4/v5 |
| Hallucination rate `< 2%`, error budget states | nfr-checklist.md | `observability-slo` | v3/v4/v5 |
| MockLLMClient injetável via constructor | nfr-checklist.md | `testing-quality` | v4/v5 |
| Quality gates CI/CD bloqueando merge | nfr-checklist.md | `testing-quality` | v4/v5 |
| Schema CheckpointStore com compactação top-N por score | deepening-storage-memory.md | `data-memory-storage` | v4/v5 |
| Script de migração JSON → SQLite | deepening-storage-memory.md | `data-memory-storage` | v4/v5 |
| Rule Engine antes do LLM Reasoner no DecisionStage | deepening-agent-internal.md | `agent-internal-architecture` | v5 |
| Two-reviser pattern: Additive (Sonnet) + Structural (Haiku) | deepening-agent-internal.md | `agent-internal-architecture` | v5 |
| BudgetMonitor: State Machine 4 estados com `APPROACHING_LIMIT` | deepening-agent-internal.md | `agent-internal-architecture` | v5 |
| STM como `SessionState` imutável via spread | deepening-agent-internal.md | `agent-internal-architecture` | v5 |

---

## Recomendação

**v5 produziu o melhor resultado (87/90)**, com ganho concentrado em duas dimensões:

- **1c (follow-ups adaptativos): 2 → 5** — a correção do trigger do Grupo B funcionou. Dado novo capturado (padrão bursty) propagou para três artefatos.
- **5a (skills explicitamente invocadas): 4 → 5** — `agent-internal-architecture` disparou pela primeira vez. Conteúdo produzido (Rule Engine, two-reviser, BudgetMonitor 4-state SM, SessionState imutável) não estava presente em nenhuma versão anterior.

**3a (amplitude das opções) permanece em 4/5** em todas as versões. A correção de Option C vai importar em casos onde B e C seriam similares — neste caso de uso a distinção já era clara antes.

**Lacunas remanescentes:**

| Lacuna | Score atual | Causa | O que resolveria |
|---|---|---|---|
| 5c: skills sem ponto de entrada | 4/5 | 8 skills irrelevantes para este caso de uso | Não corrigível neste caso — validar em caso de uso diferente (multiagent, RAG, omnichannel) |
| 3a: amplitude estrutural | 4/5 | Espectro qualitativo similar em todas as versões | Impacto da correção de Option C visível apenas em casos onde B e C seriam naturalmente próximos |
| 2b: riscos com dados observáveis | 4/5 | Stress test captura gargalos mas riscos de LTM bias e budget gate convergência são estimados, não medidos | Só resolvível com dados de produção |

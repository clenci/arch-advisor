# Relatório Comparativo: arch-advisor v1 → v4 → v7

**Data:** 2026-03-19 (atualizado; original v1→v5: 2026-03-13)
**Avaliado por:** Claude Sonnet 4.6
**Sessões observadas:** v1, v2, v3, v4-old, v4, v5, v6, v7 — v1–v6 executadas sobre o mesmo caso de uso (Technical-Document-Critic-Agent). v7 é a execução da versão 4.2.0 sobre um caso diferente (Medical-Diagnosis-Voting-Arbiter), escolhido especificamente para exercitar os flags `hybrid-decision-candidate` e `hitl-candidate` introduzidos em v4.2.0 que o caso de referência canônico não consegue exercitar.

---

## Scores por Dimensão

| Dimensão | v1 | v2 | v3 | v4-old | v4 | v5 | v6 | v7 |
|---|---|---|---|---|---|---|---|---|
| **1a. Tensões surfaceadas ao usuário** | 1 | 3 | 3 | 5 | 5 | 5 | 5 | 5 |
| **1b. Consequência aceita como insumo arquitetural** | 1 | 2 | 2 | 5 | 5 | 5 | 5 | 5 |
| **1c. Follow-ups adaptativos** | 2 | 2 | 2 | 2 | 2 | 5 | 5 | 5 |
| **1d. Stress test com dados do usuário** | 1 | 1 | 1 | 5 | 5 | 5 | 5 | 5 |
| **2a. Padrões com justificativa rastreável** | 3 | 3 | 3 | 5 | 5 | 5 | 5 | 5 |
| **2b. Riscos com dados observáveis** | 3 | 3 | 3 | 4 | 4 | 4 | 4 | **5** |
| **2c. Ambiguidades arquiteturalmente consequentes** | 2 | 4 | 4 | 5 | 5 | 5 | 5 | 5 |
| **3a. Amplitude estrutural das opções** | 4 | 4 | 4 | 4 | 4 | 4 | 4 | **5** |
| **3b. Precisão dos trade-offs** | 3 | 3 | 4 | 5 | 5 | 5 | 5 | 5 |
| **4a. C4 Diagram** | 3 | 3 | 5 | 5 | 5 | 5 | 5 | 5 |
| **4b. ADR** | 4 | 4 | 5 | 5 | 5 | 5 | 5 | 5 |
| **4c. Decision Matrix** | 3 | 4 | 4 | 5 | 5 | 5 | 5 | 5 |
| **4d. NFR Checklist** | 4 | 3 | 4 | 4 | 5 | 5 | 5 | 5 |
| **5a. Skills explicitamente invocadas** | 1 | 1 | 3 | 3 | 4 | 5 | 5 | 5 |
| **5b. Conhecimento de domínio observável** | 2 | 2 | 4 | 4 | 5 | 5 | 5 | 5 |
| **5c. Skills não utilizadas com ponto de entrada** | 1 | 1 | 1 | 1 | 3 | 4 | 4 | 4 |
| **6a. Decisões do usuário vs. internas** | 1 | 3 | 3 | 5 | 5 | 5 | 5 | 5 |
| **6b. Rastreabilidade fim-a-fim** | 2 | 3 | 3 | 5 | 5 | 5 | 5 | 5 |
| **Total** | **40/90** | **46/90** | **54/90** | **73/90** | **82/90** | **87/90** | **87/90** | **89/90** |

---

## O que mudou de v6 para v7 (arch-advisor 4.2.0 — caso Medical-Diagnosis-Voting-Arbiter)

**v7 = 89/90 — +2 pontos sobre v6. Mesma versão do plugin (4.2.0); caso de uso diferente, escolhido para exercitar as funcionalidades introduzidas em v4.2.0 que o caso de referência canônico não consegue exercitar.**

### Contexto

v7 não representa um upgrade de plugin. Representa a mesma v4.2.0 aplicada a um domínio que **ativa todos os quatro flags silenciosos** (`hybrid-decision-candidate=true`, `hitl-candidate=true`, `saga-candidate=true`, `event-sourcing-candidate=true`) e onde os dados observados do exercício de implementação prévia fornecem baselines medidos — não estimativas.

Caso: sistema de suporte a diagnóstico médico com 3 agentes especialistas em paralelo (Haiku 4.5), cascade de votação (majority → weighted → threshold → arbiter), ArbiterAgent (Sonnet 4.6), HITL assíncrono com TTL = 4h, AuditEventStore append-only para auditoria regulatória.

Exercício de origem: `/Users/cezargl/ai/estudos/exercicios/modulo-03/exercicio-04/` — 20 casos de teste, 70% majority-voting, 30% arbiter, $0.0084/caso (voting path), $0.0148/caso (arbiter path), falha identificada: string comparison em sinônimos IAM enviou caso de consenso claro para o arbiter.

### Por que o score subiu

**2b — Riscos com dados observáveis: 4 → 5**

Em v6 (caso técnico-doc-critic), os targets dos riscos eram estimativas do stress test. Em v7, os dados do exercício fornecem baselines medidos:

- "Taxa de invocação do arbiter — target: 30–40%; alert se >50%" — derivado do dado observado 30% no exercício, não estimado
- "$0.0084/caso (voting path), $0.0148/caso (arbiter path)" — custos medidos, não projetados
- "string comparison em sinônimos IAM → falso conflito → arbiter desnecessário" — failure mode documentado do exercício, propagou para o TerminologyNormalizer como componente obrigatório

O critério do score 5/5 exige "pelo menos um risco nomeado a partir do que o usuário declarou como consequência de falha". Em v7, o risco de drift da taxa de invocação do arbiter tem ground truth medido, não apenas a consequência declarada.

**3a — Amplitude estrutural das opções: 4 → 5**

Em v6, a Option C já introduzia nova infraestrutura (LangGraph StateGraph + Redis + PostgreSQL), mas no caso de referência a separação B→C já era naturalmente clara antes da correção. Em v7, a Option C introduz explicitamente:

- Azure Service Bus (fila durável) — ausente na Option B
- Workers Node.js distribuídos — ausente na Option B
- Persistent LTM externo — ausente na Option B
- External Event Store (vs. in-process AuditEventStore da Option B)

E define o threshold exato para migrá-la: "1.000+ casos/dia ou jobs concorrentes introduzidos". O limiar é derivado diretamente da resposta do stress test (10× = 2.000–5.000/dia → in-process Promise.allSettled quebra primeiro). Esta é a evidência de que a correção de 3a produz diferença mensurável em casos onde B e C são naturalmente próximos.

### Funcionalidades de v4.2.0 — validação completa em v7

| Funcionalidade | v6 (tech-doc-critic) | v7 (medical-diagnosis) |
|---|---|---|
| `hybrid-decision-candidate` flag | ✅ Não disparou (correctly silent) | ✅ Disparou — Group D priority follow-up ativado; Hybrid DE Block 1 ativado |
| `hitl-candidate` flag | ✅ Não disparou (correctly silent) | ✅ Disparou — Group C priority follow-up ativado; HITL+Checkpointing Block 5 ativado |
| Group C HITL priority follow-up | ✅ Silencioso (hitl-candidate=false) | ✅ Disparou — async approval confirmado, TTL = 4h capturado |
| Group D Hybrid DE priority follow-up | ✅ Silencioso (hybrid-decision-candidate=false) | ✅ Disparou — 50–60% deterministic capturado |
| `saga-candidate` flag + Q17 | ✅ Disparou; resposta negativa bloqueou bloco | ✅ Disparou — resposta positiva (futuro EMR) ativou Saga Block 4 + sagaId no schema |
| `event-sourcing-candidate` flag + Q18 | ✅ Disparou; resposta negativa bloqueou bloco | ✅ Disparou — resposta positiva (auditoria regulatória) ativou AuditEventStore |
| Phase 3.5 Pattern Deepening — blocos ativados | 4/12 (PEC, LLM Routing, Caching, Feedback) | **7/12** (Hybrid DE, Voting+Arbiter, Saga, HITL+Checkpointing, LLM Routing, Bulkhead, Feedback) |
| Phase 3.5 — blocos silenciosos | 8/12 corretos | 5/12 corretos |
| Skills invocadas (Phase 3.6) | agent-internal-architecture + llm-selection-routing | multiagent-orchestration + security-governance |

### O que os 7 blocos de Pattern Deepening produziram

Os blocos ativados em v7 geraram decisões de design que não existem em nenhuma execução anterior:

**Block 1 — Hybrid Decision Engine**: threshold do cascade explicitado como "no majority → weighted; gap < 0.15 → threshold; gap < 0.1 ou max_confidence < 0.5 → arbiter; arbiter < 0.5 → HITL". A ordem dos estágios é derivada dos dados: 50–60% majority, ~30–40% arbiter, <20% HITL target.

**Block 3 — Voting + Arbiter**: constraint crítico da normalização terminológica derivado do failure mode observado no exercício (string comparison em sinônimos IAM). Não é um princípio genérico — é uma decisão específica motivada por uma falha documentada.

**Block 4 — Saga**: o campo `sagaId` no schema de `DiagnosisRecord` é mandatório AGORA (12 meses antes da integração EMR), para evitar migração breaking no schema. Esta é uma decisão de design com timing específico que não existia em nenhum artefato anterior.

**Block 5 — HITL+Checkpointing**: MemorySaver = development-only é o constraint crítico. Para o contexto médico (TTL = 4h, casos de pacientes), o risco é de perda de casos pendentes em restart de processo — diferente de um sistema de suporte IT onde o impacto seria menor.

**Block 8 — Bulkhead**: dois pools com criticidade diferente — diagnóstico (critical, doctor waiting) vs. analytics/audit (non-critical, deferrable). A distinção é derivada do domínio médico, não de um princípio de infraestrutura genérico.

### 5c permanece em 4/5

A mesma lacuna de v6: `agent-internal-architecture` não foi oferecido no deepening menu para o VotingCoordinator, que tem uma cascade state machine com lógica não-trivial. O critério de inclusão do deepening menu menciona "explicit state machine" — o cascade é um state machine implícito. Lacuna marginal; o menu ofereceu 5 opções relevantes.

---

## O que mudou de v5 para v6 (arch-advisor 4.2.0)

**v6 = 87/90 — mesmo score de v5. Sem regressão, sem ganho mensurável neste caso de uso.**

### Por que o score não subiu

As dimensões em que v6 poderia ter ganho são exatamente as que já estavam em 5/5 em v5. As novas funcionalidades da v4.2.0 (discovery expandido, Phase 3.5 Pattern Deepening) introduzem valor em casos de uso que **este caso específico não exercita**:

| Nova funcionalidade | Impacto no caso Technical-Document-Critic-Agent |
|---|---|
| `hybrid-decision-candidate` flag (Group A) | Não disparou — ação é "orchestrate", não "classify/transact/route" |
| `hitl-candidate` flag (Group A) | Não disparou — output é relatório Markdown, sem ação no mundo real |
| Group C HITL follow-up (priority) | Não disparou — `hitl-candidate=false` |
| Group D Hybrid Decision follow-up (priority) | Não disparou — `hybrid-decision-candidate=false` |
| Group E Q17 (Saga/rollback) | Disparou — resposta negativa corretamente; bloco não ativado |
| Group E Q18 (Event Sourcing) | Disparou — resposta negativa corretamente; bloco não ativado |
| Phase 3.5 Pattern Deepening — blocos ativados | **4 de 12**: PEC, LLM Routing, LLM Caching, Feedback Loop |
| Phase 3.5 Pattern Deepening — blocos não ativados | **8 de 12** corretamente silenciosos |

### O que Phase 3.5 produziu (4 blocos)

Os 4 blocos ativados geraram conteúdo de implementação que não existia em v5:

**Block 2 — PEC**: design decisions concretas sobre o Reflection Loop que não estavam na Phase 3.6 de v5 — self-validation bias do Critic, partial result carry-forward, `stoppedBy` propagation como campo estruturado de output, temperatura do Planner. O conteúdo sobrepõe parcialmente com o deepening `agent-internal-architecture`, mas chega antes dos artefatos em vez de depois.

**Block 6 — Complexity-based LLM Routing**: trigger para switch Reviser → Haiku quando `totalCost/budget > 0.70` é uma decisão de design mais concreta do que o routing mencionado na Phase 3.6 de v5 (que dizia "Haiku para tasks simples" sem especificar o threshold de ativação).

**Block 7 — LLM Response Caching**: identificou que `ltmContext` injetado nos prompts do Generator anula o cache hit rate — insight sobre incompatibilidade entre dois padrões (LTM + Caching) que não aparecia nos artefatos de v5.

**Block 12 — Feedback Loop**: formalizou "baseline deve ser versionado com {modelId, promptVersion, systemVersion}" como constraint explícita — em v5 o NFR dizia "regression vs. baseline" mas não especificava o que constitui uma versão do baseline.

### Comportamento dos novos mecanismos — validação

| Mecanismo | Status | Conclusão |
|---|---|---|
| Flags silenciosos Group A | ✅ Funcionam corretamente | Não disparam para "orchestrate"; dispatcher downstream correto |
| Group B mandatory follow-up | ✅ Disparou conforme especificado | Caller = CI/CD + arrival pattern ausente → pergunta obrigatória |
| Group B batch follow-up bloqueado | ✅ Mandatory teve prioridade | Apenas um follow-up total — comportamento correto |
| Group C/D priority follow-ups | ✅ Silenciosos quando flags = false | Sem falsos positivos |
| Group E Q17/Q18 | ✅ Dispararam; respostas negativas bloquearam blocos | Comportamento correto |
| Phase 3.5 trigger mapping | ✅ 4/12 corretos para este caso | Nenhum falso positivo; nenhum falso negativo esperado |
| Plugin 4.2.0 invocação do skill `pattern-deepening` | ⚠️ Falhou via Skill tool nesta sessão | Causa: plugin instalado em cache como 4.1.0 no início da sessão; atualizado manual para 4.2.0 mid-session; skill não registrado dinamicamente; workaround: leitura direta do SKILL.md. Em nova sessão com plugin 4.2.0 ativo desde o início, skill deve ser invocável normalmente. |

### O que v6 valida sobre a v4.2.0

1. **Mecanismo de flags funciona corretamente** — `hybrid-decision-candidate` e `hitl-candidate` = false para este caso; não há falsos positivos nos downstream follow-ups
2. **Phase 3.5 não produz ruído** — 8 de 12 blocos silenciosos; apenas blocos com triggers reais ativados
3. **Phase 3.5 produz conteúdo adicional útil** — os 4 blocos ativados chegam antes dos artefatos (vs. deepening que chega depois); conteúdo concreto sobre incompatibilidade LTM×Caching e threshold de routing não estava em v5
4. **O caso de referência não exercita as funcionalidades mais novas** — para validar `hybrid-decision-candidate`, `hitl-candidate`, Saga, HITL+Checkpointing, Voting, Bulkhead, ACL é necessário um caso de uso diferente (ex: sistema de suporte com aprovação humana, sistema financeiro com rollback, classificador de tickets)

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

**v7 produziu o melhor resultado (89/90)** — mesma versão do plugin que v6 (4.2.0), caso de uso diferente (Medical-Diagnosis-Voting-Arbiter) que ativa todas as funcionalidades introduzidas em v4.2.0.

Os ganhos sobre v6 (+2 pontos):

- **2b (riscos com dados observáveis): 4 → 5** — dados do exercício fornecem baselines medidos ($0.0084/caso, 30% arbiter rate, falha de string comparison documentada), tornando os targets dos riscos observados, não estimados.
- **3a (amplitude estrutural das opções): 4 → 5** — em um caso onde Options B e C são naturalmente próximas, a correção de "Option C deve introduzir pelo menos um componente de infraestrutura novo" produziu diferença mensurável: Azure Service Bus + workers distribuídos + event store externo, com threshold derivado do stress test.

**Lacunas remanescentes (transversais a todos os casos testados):**

| Lacuna | Score atual | Causa | O que resolveria |
|---|---|---|---|
| 5c: skills sem ponto de entrada | 4/5 | `agent-internal-architecture` não oferecido para cascade state machine do VotingCoordinator | Critério de inclusão do deepening menu explicitado para "cascade com múltiplos estados" (não apenas Reflection Loop) |
| 2b: riscos com dados observáveis | 4/5 em v6 | Resolvido em v7 pelo exercício com dados medidos | Para novos casos sem exercício prévio: só resolvível com dados de produção |

**Score teórico máximo: 90/90 é atingível** — a única lacuna restante (5c = 4/5) requer refinamento do critério de inclusão do deepening menu para cases com cascade state machines. A correção seria: adicionar "cascade com múltiplos estágios determinísticos" como critério de inclusão de `agent-internal-architecture` no deepening menu.

**Elementos a preservar em versões futuras:**

| Elemento | Versão de origem | Justificativa |
|---|---|---|
| Phase 1.5 Tension Resolution por consequence framing | v4 | Gera componentes arquiteturais não declarados nos requisitos (BudgetMonitor, TerminologyNormalizer, CheckpointStore emergiram de tensões) |
| Phase 1.6 Stress Test com thresholds do usuário | v4 | "When to Reconsider" com condições mensuráveis deriva diretamente das respostas |
| Flags silenciosos Group A + follow-ups prioritários C/D | v6 (4.2.0) | Validados em v7: disparam nos 3 grupos corretos, silenciosos quando não aplicável — zero falsos positivos |
| Phase 3.5 Pattern Deepening (visível, antes dos artefatos) | v6 (4.2.0) | 7 blocos ativados em v7 produziram decisions de design (sagaId no schema, normalização obrigatória, MemorySaver constraint) ausentes em versões anteriores |
| Invocações explícitas de skills Phase 4 | v4 | Diferença mensurável e rastreável nos artefatos em todas as execuções testadas |

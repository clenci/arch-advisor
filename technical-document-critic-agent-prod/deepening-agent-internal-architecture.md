# Deepening: Agent Internal Architecture — Technical Document Critic Agent

## 1. Separação de Camadas: o que colocar em cada uma

O pipeline de 4 camadas já está definido. A decisão crítica é **o que pertence a cada camada** e o que não deve ser colapsado em um único prompt.

```
[Perception]   MarkdownFileReader → normaliza para { title, sections, metadata }
               NUNCA classifica aqui — apenas lê e estrutura

[Decision]     Rule Engine → LLM Reasoner → Heuristic Validator
               Produz: { docType, domain, scores: { depth, completeness, clarity, actionability } }

[Memory]       STM: estado da análise corrente (Perception output + Decision output + revisões)
               LTM: top-3 análises do mesmo domínio/tipo via CheckpointStore

[Reflection]   ReflectionController (State Machine) → CritiqueAgent → [Additive|Structural] Reviser
               Produz: relatório refinado com convergenceStatus
```

**Regra de ouro:** se um componente recebe input de dois estágios diferentes, ele pertence ao estágio mais tardio, não a um estágio anterior.

---

## 2. Decision Layer: três passes em ordem

O DecisionStage não deve ser uma única chamada LLM. A composição em três passes reduz custo e aumenta confiabilidade:

**Passe 1 — Rule Engine (zero custo LLM)**
```typescript
const rules = [
  { pattern: /^# ADR/m,          docType: 'adr',          confidence: 0.95 },
  { pattern: /^# RFC/m,          docType: 'rfc',          confidence: 0.95 },
  { pattern: /## Architecture/i, docType: 'architecture', confidence: 0.80 },
  { pattern: /## API/i,          docType: 'api-spec',     confidence: 0.80 },
];
// Se confidence > 0.90: pula LLM Reasoner para docType, mantém apenas avaliação de dimensões
```

Documentos com padrão claro (ADR, RFC) **não precisam** de classificação LLM — apenas avaliação de dimensões. Isso reduz 1 chamada LLM por ~30% dos documentos.

**Passe 2 — LLM Reasoner (Sonnet 4.6, structured output)**
```typescript
const result = await llm.complete({
  model: 'claude-sonnet-4-6',
  response_format: { type: 'json_schema', schema: DecisionOutputSchema },
  messages: [{ role: 'user', content: buildDecisionPrompt(doc, ltmContext) }]
});
// Sempre JSON schema — nunca parse de texto livre
```

**Passe 3 — Heuristic Validator (zero custo LLM)**
```typescript
assert(KNOWN_DOC_TYPES.includes(result.docType),                          'docType inválido');
assert(Object.values(result.scores).every(s => s >= 0 && s <= 1),        'score fora de range');
assert(result.domain.length > 0,                                          'domínio vazio');
// Correção sem re-chamar LLM: normaliza scores para [0,1] se necessário
```

**Trade-off concreto:** Rule Engine economiza ~$0.01–0.02 por análise nos docs com padrão claro. Para 50 docs/dia: ~$15–20/mês. O ganho principal não é custo — é consistência: classificação de ADR e RFC é determinística, não sujeita a variação do LLM.

---

## 3. Reflection Loop: two-reviser pattern

O sistema avalia quatro dimensões: `depth`, `completeness`, `clarity`, `actionability`. Uma única instrução de revisão **não consegue simultaneamente adicionar conteúdo E remover conteúdo irrelevante** — o LLM tende a ser aditivo por padrão.

**Fluxo com two-reviser:**

```
CritiqueAgent (Haiku 4.5)
  → scores: { depth: 0.4, completeness: 0.6, clarity: 0.8, actionability: 0.5 }

Se depth < threshold OU completeness < threshold:
  → AdditiveReviser (Sonnet 4.6): "adicione seções ausentes, aprofunde pontos X e Y"

Se clarity < threshold OU actionability < threshold:
  → StructuralReviser (Haiku 4.5): "reorganize, remova off-topic, torne recomendações específicas"
```

**Por que dois revisores separados:**
- AdditiveReviser usa Sonnet 4.6: gerar conteúdo novo de qualidade requer o modelo mais capaz
- StructuralReviser usa Haiku 4.5: reorganizar e cortar é menos exigente que gerar
- Com um único reviser aditivo, `actionability` nunca melhora — o modelo adiciona mais texto genérico ao invés de tornar recomendações acionáveis

**Custo por iteração com two-reviser:**
- CritiqueAgent (Haiku 4.5): ~$0.002
- AdditiveReviser (Sonnet 4.6): ~$0.015
- StructuralReviser (Haiku 4.5): ~$0.003
- Total por iteração completa: ~$0.020

Com budget de $0.30 e Decision usando ~$0.05, sobram ~$0.25 para Reflection → até 12 iterações teóricas. O critério max_iterations=3 limita o gasto real a ~$0.06–0.08 em refinamento.

---

## 4. BudgetMonitor como State Machine explícita

```
NOMINAL ──($0.20 reached)──► APPROACHING_LIMIT
                                    │
                    score > 0.65 ───┤─── score ≤ 0.65
                         │                    │
                         ▼                    ▼
               ADAPTIVE_EXTENSION        HARD_STOP ($0.30)
                    ($0.50 limit)
                         │
                   $0.50 reached
                         │
                         ▼
                    HARD_STOP ($0.50)
```

```typescript
type BudgetState = 'NOMINAL' | 'APPROACHING_LIMIT' | 'ADAPTIVE_EXTENSION' | 'HARD_STOP';

class BudgetMonitor {
  constructor(
    private hardLimit = 0.30,
    private adaptiveLimit = 0.50,
    private scoreThreshold = 0.65
  ) {}

  checkAndExtend(costSoFar: number, currentScore: number): { canContinue: boolean; state: BudgetState } {
    if (costSoFar >= this.adaptiveLimit)  return { canContinue: false, state: 'HARD_STOP' };
    if (costSoFar >= this.hardLimit) {
      if (currentScore > this.scoreThreshold) return { canContinue: true, state: 'ADAPTIVE_EXTENSION' };
      return { canContinue: false, state: 'HARD_STOP' };
    }
    if (costSoFar >= 0.20) return { canContinue: true, state: 'APPROACHING_LIMIT' };
    return { canContinue: true, state: 'NOMINAL' };
  }
}
```

**Por que State Machine e não condicionais simples:** o estado `APPROACHING_LIMIT` permite acionar comportamento preventivo — usar somente Haiku 4.5 para os revisores restantes ao invés de Sonnet 4.6, potencialmente completando mais uma iteração dentro do budget.

---

## 5. STM: o que manter no contexto corrente

A STM neste sistema não é uma janela de mensagens de chat — é o **estado acumulado do pipeline para a análise corrente**:

```typescript
interface SessionState {
  traceId: string;
  documentPath: string;
  perceptionOutput: NormalizedDocument;
  decisionOutput: DecisionResult;
  ltmContext: LTMEntry[];                    // top-3 análises relevantes do CheckpointStore
  reflectionHistory: ReflectionIteration[]; // { iteration, scores, stoppedBy? }
  currentReport: string;
  budgetState: BudgetState;
}
```

**Imutabilidade via spread:** cada estágio produz um novo objeto, não mutação in-place:
```typescript
const nextState = { ...currentState, decisionOutput: result, budgetState: monitor.check(...) };
```

Isso permite reconstruir o histórico completo de uma análise a partir dos eventos do EventBus, sem estado compartilhado mutável entre estágios.

---

## Recomendação Consolidada

| Decisão | Recomendação | Justificativa |
|---|---|---|
| Decision layer | Rule Engine + LLM + Heuristic Validator | Classificação determinística para ADR/RFC; valida output sem re-chamar modelo |
| Reflection revisers | Two-reviser: Additive (Sonnet) + Structural (Haiku) | `actionability` só melhora com reviser estrutural dedicado |
| BudgetMonitor | State Machine 4 estados | Estado `APPROACHING_LIMIT` habilita otimização preventiva de modelo |
| Session state | Imutável via spread em cada estágio | Reconstrução de histórico via EventBus sem logging redundante |
| STM scope | Estado completo do pipeline, não janela de chat | O contexto relevante é o estado da análise corrente |

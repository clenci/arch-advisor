# Decision Matrix — Technical Document Critic Agent

| Critério | Peso | Opção A | Opção B | Opção C | Notas |
|---|---|---|---|---|---|
| Aderência ao hard budget $0.30/análise | 20% | 8 | **9** | 8 | B: BudgetMonitor desacoplado intercepta toda transição de estágio. A: gate acoplado diretamente ao ReflectionLoop. C: gate também customizado (LangGraph não tem budget nativo). |
| Extensibilidade de estágios (sem modificar core) | 20% | 4 | **9** | 10 | A score 4: novo estágio modifica o pipeline principal. C score 10 justificado: StateGraph declarativo, nós adicionados sem tocar nenhum componente existente. |
| LTM cross-invocation com política de qualidade | 20% | 7 | **9** | 9 | A: CheckpointStore presente mas sem política de qualidade explícita. B e C: somente análises com score ≥ threshold entram na LTM, prevenindo deriva por viés de domínio. |
| Custo de infraestrutura (zero deps vs. infra permanente) | 20% | 10 | **9** | 2 | C score 2 justificado: Redis + PostgreSQL obrigatórios para volume que não os justifica (~30–50 docs/dia). A score 10: zero overhead absoluto. B score 9: EventBus in-process, zero infra adicional. |
| Observabilidade por estágio (traceId, costUsd por evento) | 10% | 4 | **8** | 9 | A score 4: logging manual em cada chamada LLM. B: campos emergem naturalmente dos eventos. C score 9 justificado: LangGraph + OpenTelemetry nativo. |
| Preparação para escala 10x sem refatoração disruptiva | 10% | 2 | 5 | **10** | A score 2: refatoração completa do pipeline. B score 5: EventBus→BullMQ é migração real mas CheckpointStore→SQLite é menor. C score 10 justificado: worker pool já presente, concorrência nativa. |
| **Total Ponderado** | **100%** | **6,40** | **8,50** | **7,70** | |

**Breakdown:**
- Opção A: (8×0,20) + (4×0,20) + (7×0,20) + (10×0,20) + (4×0,10) + (2×0,10) = 1,60 + 0,80 + 1,40 + 2,00 + 0,40 + 0,20 = **6,40**
- Opção B: (9×0,20) + (9×0,20) + (9×0,20) + (9×0,20) + (8×0,10) + (5×0,10) = 1,80 + 1,80 + 1,80 + 1,80 + 0,80 + 0,50 = **8,50**
- Opção C: (8×0,20) + (10×0,20) + (9×0,20) + (2×0,20) + (9×0,10) + (10×0,10) = 1,60 + 2,00 + 1,80 + 0,40 + 0,90 + 1,00 = **7,70**

**Leitura do resultado:** A Opção B vence por consistência — domina ou empata em todos os critérios com peso 20%, e não penaliza nas dimensões onde C é superior (escala 10x não é requisito comprometido). A Opção C torna-se preferível quando o critério de custo de infraestrutura perder relevância, o que ocorre quando o volume 10x se tornar requisito real. Esse é o gatilho explícito de "When to Reconsider" no ADR-001.

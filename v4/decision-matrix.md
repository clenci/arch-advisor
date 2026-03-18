# Decision Matrix — Technical Document Critic Agent

| Critério | Peso | Option A — Flat Sequential | Option B — Event-Driven + Checkpoints | Option C — Distributed Pipeline | Notas |
|---|---|---|---|---|---|
| Resiliência a falhas parciais | 20% | 2 | 9 | 10 | A: rerun completo em qualquer falha de infra — contradiz consequência de perda financeira (Group E). B: checkpoint por estágio permite resume sem reprocessamento. C: worker retry + queue = máxima resiliência. |
| Desacoplamento do BudgetMonitor | 18% | 3 | 9 | 10 | A: budget/score acoplado dentro do ReflectionHandler — não testável em isolamento. B: subscriber independente via EventEmitter — testável com eventos sintéticos. C: BudgetService separado. |
| LTM persistence e warm-start | 17% | 7 | 9 | 10 | A: funciona mas responsabilidade de escrita atômica fica dispersa. B: CheckpointStore com fs.rename — responsabilidade única. C: SQLite com transações ACID. |
| Complexidade operacional | 15% | 10 | 7 | 2 | A: processo efêmero, zero infra. B: in-process EventBus, sem infra externa. C: Redis + workers + health checks — over-engineering para volume atual. |
| Extensibilidade de estágios | 15% | 4 | 9 | 10 | A: novo estágio requer modificar fluxo sequencial. B: novo handler = novo subscriber sem tocar handlers existentes. |
| Custo de implementação inicial | 15% | 10 | 6 | 2 | B exige mais código inicial; padrões (EventEmitter, fs.rename atômico) são familiares para equipe experiente. C requer Redis e infra de worker pool. |
| **Total ponderado** | **100%** | **5,73** | **8,25** | **7,60** | |

## Cálculo detalhado

**Option A:** (2×0,20)+(3×0,18)+(7×0,17)+(10×0,15)+(4×0,15)+(10×0,15) = 0,40+0,54+1,19+1,50+0,60+1,50 = **5,73**

**Option B:** (9×0,20)+(9×0,18)+(9×0,17)+(7×0,15)+(9×0,15)+(6×0,15) = 1,80+1,62+1,53+1,05+1,35+0,90 = **8,25**

**Option C:** (10×0,20)+(10×0,18)+(10×0,17)+(2×0,15)+(10×0,15)+(2×0,15) = 2,00+1,80+1,70+0,30+1,50+0,30 = **7,60**

## Leitura

Option B vence nos três critérios derivados diretamente das tensões resolvidas. Option C pontua mais alto em resiliência e extensibilidade absolutas mas perde 5 pontos em complexidade operacional — custo injustificado para dezenas/dia. O gap de 0,65 ponto entre B e C fecha quando o trigger do stress test (~200 análises/dia com concorrência) for atingido, momento em que Option C deve ser reavaliada.

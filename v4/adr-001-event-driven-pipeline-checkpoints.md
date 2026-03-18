# ADR-001 — Event-Driven Pipeline with Stage Checkpoints

**Status:** Proposed
**Date:** 2026-03-13

## Context

O Technical Document Critic Agent executa como processo único invocado por CI/CD, com 4 estágios sequenciais (Perception → Decision → Memory → Reflection). Duas tensões arquiteturais resolvidas na Phase 1.5 determinam a escolha estrutural: (1) LTM deve persistir entre invocações de processo via PipelineCheckpoint atômico, pois LTM fria a cada run tornaria o estágio Memory um no-op; (2) a lógica de avaliação de budget deve operar independentemente da lógica de qualidade do Reflection Loop, pois acoplá-las impede testabilidade isolada de cada responsabilidade. O objetivo pedagógico explícito (State Machine, Chain of Responsibility, Reflection Loop como artefatos estruturais de primeira classe) e a consequência de perda financeira por classificação incorreta (Group E) reforçam a necessidade de separação de responsabilidades e recovery parcial em falha de infraestrutura.

## Decision

Adotar pipeline event-driven onde cada estágio emite evento de completion; o PipelineOrchestrator persiste o output do estágio no CheckpointStore antes de invocar o próximo; e o BudgetMonitor é um subscriber independente do EventBus que emite `budget:extend` ou `budget:halt` para o ReflectionHandler sem acoplamento à sua lógica interna.

## Justification

- **LTM persistence (tensão 1):** CheckpointStore como componente único de escrita atômica garante que o estado LTM sobrevive a process kills; warm-start lê o checkpoint antes do PerceptionHandler executar, satisfazendo o requisito de enriquecimento cross-run.
- **Budget decoupling (tensão 2):** BudgetMonitor subscreve `reflection:iteration` independentemente; testável com eventos sintéticos sem dependência de LLM real; pode ser modificado sem tocar o ReflectionHandler — o teto de $0.30 (default) e $0.50 (absoluto, com score > 0.65) é aplicado de fora do loop de critique.
- **Financial loss consequence (Group E):** checkpoints por estágio permitem reruns a partir do último estágio completo em falha de proxy ou infraestrutura, reduzindo reruns completos causados por problemas de infra versus problemas de qualidade.
- **Objetivo pedagógico:** State Machine no PipelineOrchestrator + Chain of Responsibility nos stage handlers + Reflection Loop no ReflectionHandler satisfazem o requisito explícito de demonstrar esses padrões como artefatos estruturais de primeira classe.
- **Imutabilidade de estado:** cada estágio produz um novo objeto de estado persistido atomicamente; habilita replay e debugging de decisões intermediárias.
- **convergenceStatus obrigatório:** ReportEmitter escreve `converged | budget-extended | incomplete` em 100% dos outputs — consumidores downstream distinguem relatório completo de relatório parcial sem inspeção manual.

## Consequences

**Positive:**
- Recovery parcial em falha de infra sem reprocessamento completo
- BudgetMonitor testável com eventos sintéticos — independente do ciclo de vida do LLM
- Novo estágio = novo EventEmitter handler sem modificar handlers existentes
- convergenceStatus auditável por times downstream

**Negative:**
- Mais código inicial que pipeline linear: EventBus, CheckpointStore, múltiplos listeners
- Fluxo de eventos menos intuitivo que stack trace linear — debugging requer correlação de logs
- In-process EventBus limita escala horizontal sem substituição por broker externo

## Alternatives Rejected

**Option A — Flat Sequential Pipeline:** BudgetMonitor não pode ser desacoplado do ReflectionHandler sem reestruturação — lógica de budget e lógica de qualidade se entrelaçam, impossibilitando testes isolados. Sem checkpoints de estágio: falha de infraestrutura exige rerun completo, contradizendo diretamente a consequência de perda financeira aceita no Group E.

**Option C — Distributed Pipeline com Queue:** volume atual (dezenas/dia, sem concorrência) não justifica Redis e worker pool. Introduz dependência operacional antes do trigger do stress test (~200 análises/dia com concorrência real) ser atingido. Rejeitado como premature optimization até que o cenário de 10x se materialize.

## When to Reconsider

- Se o volume diário superar ~200 análises com concorrência real, promover in-process EventBus para BullMQ sobre Redis e extrair stage handlers como workers independentes (Option C).
- Se o arquivo JSON do CheckpointStore exceder ~50MB ou a latência de leitura do MemoryHandler degradar de forma mensurável, migrar CheckpointStore para SQLite com queries indexadas.
- Se o proxy CI&T Flow introduzir overhead por conexão que torne execução paralela de estágios vantajosa, avaliar modelo DAG sobre a cadeia sequencial de EventEmitter.

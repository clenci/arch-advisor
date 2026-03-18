# ADR-001 — Event-Driven Pipeline com CheckpointStore JSON para LTM Persistente

**Status:** Proposed
**Date:** 2026-03-13

## Context

O sistema precisa orquestrar um pipeline sequencial de 4 camadas (Perception → Decision → Memory → Reflection) invocado por um pipeline CI/CD stateless — cada invocação spawna um processo Node.js novo. A LTM por domínio precisa sobreviver entre invocações para enriquecer análises, mas a restrição de zero dependências externas elimina SQLite, Redis e qualquer banco. Adicionalmente, um BudgetMonitor adaptativo precisa interceptar transições de estágio sem estar acoplado ao ReflectionController. Três opções foram consideradas: pipeline inline sem framework, event-driven pipeline com EventBus in-process (esta decisão), e LangGraph StateGraph com Worker Pool + Redis.

## Decision

Adotar um Event-Driven Pipeline com EventBus in-process para desacoplar os estágios do pipeline, e um CheckpointStore baseado em arquivo JSON para persistir a LTM entre invocações CI/CD — sem dependências externas além do proxy LLM.

## Justification

- **Tensão LTM vs. zero deps resolvida:** CheckpointStore JSON lê no startup e grava atomicamente (tmp+rename) no encerramento, preservando LTM por domínio sem SQLite ou Redis.
- **Tensão budget vs. qualidade resolvida:** BudgetMonitor como componente transversal intercepta o evento `stageCompleted` e aplica a lógica adaptativa ($0.30 hard stop; extensão até $0.50 se score > 0.65) sem acoplamento ao ReflectionController.
- **Extensibilidade real:** novo estágio = novo EventHandler registrado; novo formato de input = nova implementação de `DocumentReader` — o Orchestrator não é modificado em nenhum dos dois casos.
- **Zero overhead de infraestrutura:** EventBus in-process (<1ms por transição), sem daemon permanente — compatível com invocação direta CI/CD que spawna e termina o processo.
- **Observabilidade natural:** cada evento carrega `traceId`, `agentId`, `action`, `durationMs`, `tokensUsed`, `costUsd` — os campos de log obrigatórios emergem da estrutura de eventos, não de instrumentação manual.
- **Aderência ao objetivo de aprendizado:** State Machine no ReflectionController, Chain of Responsibility no EventBus, Strategy no DocumentReader — os três padrões de design do módulo são demonstrados estruturalmente.

## Consequences

**Positive:**
- Estágios são independentemente testáveis com MockLLMClient injetado via constructor
- BudgetMonitor é substituível sem modificar o pipeline
- CheckpointStore garante LTM cross-invocation sem dependência externa
- Política de qualidade no CheckpointStore (score ≥ threshold) previne deriva de LTM por viés de domínio
- Campos de observabilidade emergem naturalmente da estrutura de eventos

**Negative:**
- EventBus in-process não suporta concorrência real — no cenário 10x com múltiplos workers, precisará migrar para BullMQ + Redis
- CheckpointStore JSON sem indexação — busca por domínio é O(n); acima de ~500 análises acumuladas, o tempo de startup pode ser perceptível
- Write atômico via tmp+rename é seguro para processo único mas não para múltiplas instâncias simultâneas

## Alternatives Rejected

**Pipeline Inline (Opção A):** Rejeitado porque o BudgetMonitor teria que ser acoplado diretamente ao ReflectionController, e adicionar um novo estágio exigiria modificar o pipeline principal — viola o princípio de extensibilidade sem modificação que o objetivo de aprendizado requer demonstrar.

**LangGraph StateGraph + Worker Pool (Opção C):** Rejeitado porque introduz Redis e PostgreSQL/pgvector como dependências de infraestrutura permanentes, violando a restrição de zero dependências externas e adicionando custo operacional injustificado para o volume atual de dezenas de docs/dia. O cenário 10x não é requisito comprometido.

## When to Reconsider

- Se o volume diário ultrapassar ~300 docs/dia com concorrência real (múltiplos PRs simultâneos), o EventBus in-process deve ser promovido para BullMQ + Redis e o Orchestrator deve se tornar um worker daemon.
- Se o CheckpointStore JSON ultrapassar ~500 entradas (estimado em ~12 meses no volume atual), migrar para SQLite com índice por domínio para manter startup < 500ms.
- Se a taxa de erros de classificação reportada pela área de negócios ultrapassar 5% por mais de 2 semanas, avaliar se a LTM word-overlap por domínio precisa ser substituída por embeddings semânticos (pgvector ou Chroma).

# NFR Checklist — Event-Driven Pipeline com Stage Checkpoints

## Performance

- [ ] Latência P95 por análise — target: < 3min — mandatory
- [ ] Latência P99 por análise — target: < 5min — recommended
- [ ] Chamadas LLM no critical path — target: ≤ 7 (classify×1 + generate×1 + critique×3 + revise×3 máximo) — recommended
- [ ] Startup do processo (incluindo leitura do CheckpointStore) — target: < 2s — mandatory

## Cost

- [ ] Custo por análise (caminho nominal) — target: < $0.30 — mandatory
- [ ] Custo por análise (extensão adaptativa) — target: < $0.50 quando score > 0.65 — mandatory
- [ ] Custo por análise logado em runtime com `tokensUsed` e `costUsd` por chamada LLM — mandatory
- [ ] Alerta quando custo por análise > $0.45 (1,5× do baseline observado de $0.15) — recommended

## Reliability

- [ ] Circuit breaker no CI&T Flow Proxy — retorna `stoppedBy: "providerError"` com análise parcial em vez de exceção não tratada — mandatory
- [ ] Retry com exponential backoff em chamadas ao proxy — base: 1s, max: 8s, tentativas: 3 — mandatory
- [ ] Budget check executado ANTES de cada chamada LLM (não após) — garantir budget suficiente para completar a chamada antes de iniciá-la — mandatory
- [ ] Degradação graciosa quando budget é atingido — retornar relatório parcial com `stoppedBy: "costBudget"` e `convergenceStatus: "incomplete"` — mandatory
- [ ] Write atômico do CheckpointStore via arquivo temporário + rename — previne corrupção em falha de processo durante gravação — mandatory

## Quality

- [ ] Taxa de aprovação em evals de qualidade — target: > 90% — mandatory
- [ ] Taxa de erros de classificação (KPI da área de negócios) — target: < 5% — mandatory
- [ ] Alerta quando taxa de erros de classificação > 5% por > 2 semanas consecutivas — mandatory
- [ ] Quality SLO: score final médio ≥ 0,75 em janela rolling de 7 dias — mandatory
- [ ] CheckpointStore persiste somente análises com score ≥ threshold definido (ex: 0,75) — mandatory
- [ ] Política de compactação do CheckpointStore: manter top-N análises por domínio (sugerido N=50) para limitar crescimento — recommended
- [ ] Estados de error budget documentados: > 30% restante → deploy livre; 10–30% → cautela; < 10% → freeze — recommended

## Observability

- [ ] Log estruturado por evento LLM com campos obrigatórios: `traceId`, `agentId`, `action`, `durationMs`, `tokensUsed`, `costUsd` — mandatory
- [ ] `traceId` propagado em todos os eventos do EventBus para toda a análise (pipeline completo compartilha o mesmo traceId) — mandatory
- [ ] Span por estágio do pipeline: PerceptionStage, DecisionStage, MemoryStage, ReflectionController — mandatory
- [ ] Span por iteração do Reflection Loop com campos: `iterationNumber`, `scoreBeforeRevision`, `scoreAfterRevision`, `costAccumulated` — mandatory
- [ ] Métrica `convergenceScore` rastreada por requisição — não apenas erros — mandatory
- [ ] Campo `stoppedBy` registrado em todo encerramento de análise (`costBudget` / `adaptiveExtension` / `scoreThreshold` / `maxIterations` / `providerError`) — mandatory
- [ ] Alerta de anomalia de custo: custo por análise > 3× média móvel de 7 dias — recommended

## Extensibility

- [ ] Novo formato de input adicionável via implementação da interface `DocumentReader` sem modificar PerceptionStage ou Orchestrator — mandatory
- [ ] Novo estágio adicionável via registro de EventHandler no EventBus sem modificar estágios existentes — mandatory
- [ ] Troca de modelo por estágio (Sonnet ↔ Haiku ↔ outro provider via CI&T Flow Proxy) via configuração, sem alteração de código — recommended
- [ ] BudgetMonitor substituível via injeção de dependência — permite ajustar lógica de extensão adaptativa sem tocar o pipeline — recommended

## Testability

- [ ] Cada estágio aceita `LLMClient` como parâmetro de constructor — MockLLMClient injetável para testes de componente — mandatory
- [ ] `CheckpointStore` aceita `filePath` configurável — testes usam diretório temporário isolado, não o arquivo de produção — mandatory
- [ ] BudgetMonitor testável de forma isolada com valores de custo e score mockados — mandatory
- [ ] Cobertura de testes ≥ 80% nos componentes determinísticos: BudgetMonitor, CheckpointStore, EventBus, MarkdownFileReader — mandatory
- [ ] Taxa de aprovação em component tests ≥ 95% — mandatory
- [ ] Evals de qualidade executados com `temperature=0` para determinismo; resultado cacheado por `(input_hash, prompt_version)` — recommended
- [ ] Baseline de evals versionado junto ao código; alerta se qualquer dimensão regredir > 5% — recommended

# NFR Checklist — Event-Driven Pipeline com Stage Checkpoints

## Performance
- [ ] Latency P95 por análise — target: < 5 min (async; sem SLA real-time) — mandatory
- [ ] LLM calls base no critical path — target: ≤ 4 (uma por estágio) — mandatory
- [ ] Iterações adicionais de Reflection pós-budget-extend — target: ≤ 3 — mandatory
- [ ] Reflection iteration count médio monitorado por semana — recommended

## Cost
- [ ] Custo por análise — target: < $0,30 default; < $0,50 teto absoluto com budget-extend — mandatory
- [ ] Budget-extend ativado apenas quando score > 0,65 no momento da verificação — mandatory
- [ ] Budget-extend limitado a 3 iterações adicionais independentemente do score — mandatory
- [ ] Custo acumulado logado após cada LLM call: traceId, agentId, action, costUsd — mandatory
- [ ] Alerta quando custo por análise > 2× média dos últimos 7 dias — mandatory

## Reliability
- [ ] Taxa de sucesso de invocação — target: ≥ 99% — mandatory
- [ ] Circuit breaker no Claude Proxy: timeout 30s; 3 tentativas com backoff exponencial (base 1s, max 8s); em falha persistente emite stage:failed e entrega relatório parcial — mandatory
- [ ] CheckpointStore com escrita atômica via fs.rename(tempFile, target) — mandatory
- [ ] Fallback para cold-start LTM em checkpoint corrompido ou inválido (schema versioning no JSON) — mandatory
- [ ] convergenceStatus presente em 100% dos relatórios de saída — mandatory

## Quality
- [ ] Eval pass rate — target: > 90% — mandatory
- [ ] Hallucination rate — target: < 2%; alerta se > 5% — mandatory
- [ ] Quality SLO: convergenceStatus = "converged" em ≥ 85% das análises / 30 dias — mandatory
- [ ] Error budget (Quality SLO 85% → 15% budget ~4,5 dias/mês):
  - [ ] > 30% remaining: deploy freely, run prompt experiments — recommended
  - [ ] 10–30% remaining: slow deploys, avoid prompt changes — recommended
  - [ ] < 10% remaining: freeze changes, investigate quality regression — mandatory
- [ ] Regression vs. baseline: score médio não deve cair > 5% entre deploys consecutivos — mandatory
- [ ] LLM-as-Judge para avaliação das dimensões de qualidade (completude, clareza, acionabilidade) usando Sonnet 4.6 como juiz — mandatory
- [ ] Evals rodando por commit ou diariamente; resultados cacheados por (input, prompt_version) — recommended

## Observability — Três Pilares

### Logs (JSON estruturado)
- [ ] Campos obrigatórios por evento LLM: traceId, agentId, action, durationMs, tokensUsed, costUsd — mandatory
- [ ] convergenceStatus logado pelo ReportEmitter com score final e total de iterações — mandatory
- [ ] BudgetMonitor loga cada decisão: currentCost, currentScore, decision (extend|halt) — mandatory

### Métricas
- [ ] Cost per analysis — rastreado por run; alertado quando > 2× baseline — mandatory
- [ ] Eval pass rate — rastreado por semana — mandatory
- [ ] Hallucination rate — rastreado por semana; alerta > 5% — mandatory
- [ ] Reflection iteration count por análise — recommended
- [ ] Taxa de budget-extend vs. total de runs — recommended

### Traces
- [ ] Span por estágio: perception, decision, memory, reflection — mandatory
- [ ] Span por iteração do ReflectionHandler com score e costDelta — mandatory
- [ ] traceId constante em todos os spans de um mesmo pipeline run — mandatory
- [ ] Span do BudgetMonitor linkado ao span da iteração que disparou a decisão — recommended

## Testability
- [ ] LLMClient injetável via constructor em todos os stage handlers (MockLLMClient para testes) — mandatory
- [ ] BudgetMonitor testável com synthetic reflection:iteration events sem LLM real — mandatory
- [ ] CheckpointStore injetável via interface read/write — mandatory
- [ ] Unit test coverage > 80% em componentes determinísticos (parsers, validators, formatters) — mandatory
- [ ] Component test pass rate > 95% com MockLLMClient — mandatory
- [ ] Quality gates no CI/CD: unit 100% + eval > 90% + hallucination < 2% bloqueiam merge — mandatory

## Extensibility
- [ ] Novo estágio implementável como EventEmitter subscriber sem modificar handlers existentes — mandatory
- [ ] CheckpointStore swappável para SQLite sem alterar stage handlers (interface read/write) — mandatory
- [ ] Model swap por estágio via config sem mudança de código — recommended
- [ ] word-overlap RAG substituível por ChromaDB no MemoryHandler sem alterar interface do handler — recommended

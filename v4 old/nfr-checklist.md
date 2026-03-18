# NFR Checklist — Event-Driven Pipeline com Stage Checkpoints

## Performance
- [ ] Latency P95 por análise — target: < 5 min (async; sem SLA de latência real-time) — mandatory
- [ ] LLM calls base no critical path — target: ≤ 4 (uma por estágio) — mandatory
- [ ] Iterações adicionais de Reflection pós-budget-extend — target: ≤ 3 iterações — mandatory
- [ ] Reflection iteration count médio monitorado por semana (detecção de tendência de não-convergência) — recommended

## Cost
- [ ] Custo por análise — target: < $0,30 (hard default); < $0,50 (teto absoluto com budget-extend) — mandatory
- [ ] Custo acumulado logado após cada LLM call com campos: traceId, agentId, action, costUsd — mandatory
- [ ] Alerta quando custo por análise > 2× média dos últimos 7 dias — mandatory
- [ ] Budget-extend ativado apenas quando score > 0,65 no momento da verificação — mandatory
- [ ] Budget-extend limitado a máximo 3 iterações adicionais independentemente do score — mandatory

## Reliability
- [ ] Taxa de sucesso de invocação (convergenceStatus != crash) — target: ≥ 99% — mandatory
- [ ] Circuit breaker no Claude Proxy: timeout 30s; 3 tentativas com backoff exponencial (base 1s, max 8s); em falha persistente: emite stage:failed e entrega relatório parcial — mandatory
- [ ] CheckpointStore com escrita atômica via fs.rename(tempFile, target) — mandatory
- [ ] Fallback silencioso para cold-start LTM se checkpoint corrompido ou inválido (schema versioning obrigatório no JSON) — mandatory
- [ ] convergenceStatus presente em 100% dos relatórios de saída — mandatory

## Quality
- [ ] Eval pass rate — target: > 90% — mandatory
- [ ] Hallucination rate — target: < 2%; alerta se > 5% — mandatory
- [ ] Quality SLO: convergenceStatus = "converged" em ≥ 85% das análises / janela de 30 dias — mandatory
- [ ] Error budget (Quality SLO 85% over 30 days → 15% error budget ~4,5 dias/mês):
  - [ ] > 30% remaining: deploy freely, run prompt experiments — recommended
  - [ ] 10–30% remaining: slow deploys, avoid prompt changes — recommended
  - [ ] < 10% remaining: freeze changes, investigate quality regression — mandatory
- [ ] Regression vs. baseline: score médio de Reflection não deve cair > 5% entre deploys consecutivos — mandatory
- [ ] Componentes determinísticos (parsers, validators, formatters) com cobertura de unit test > 80% — mandatory
- [ ] Component tests para cada stage handler com MockLLMClient injetável via constructor — mandatory
- [ ] BudgetMonitor testável com synthetic reflection:iteration events sem dependência de LLM real — mandatory
- [ ] Quality gates no CI/CD: unit test 100% pass + eval pass rate > 90% + hallucination < 2% bloqueiam merge — mandatory

## Observability — Três Pilares

### Logs (JSON estruturado)
- [ ] Campos obrigatórios por evento LLM: `traceId`, `agentId`, `action`, `durationMs`, `tokensUsed`, `costUsd` — mandatory
- [ ] convergenceStatus logado pelo ReportEmitter com score final e total de iterações — mandatory
- [ ] BudgetMonitor loga cada decisão com: `currentCost`, `currentScore`, `decision` (extend|halt) — mandatory
- [ ] Stage outputs não logados em plaintext — apenas hash de conteúdo para auditoria — recommended

### Métricas
- [ ] Cost per analysis — rastreado por run; alertado quando > 2× baseline — mandatory
- [ ] Eval pass rate — rastreado por semana — mandatory
- [ ] Hallucination rate — rastreado por semana; alerta > 5% — mandatory
- [ ] Reflection iteration count por análise — rastreado para detecção de oscilação — recommended
- [ ] Taxa de budget-extend vs. total de runs (indicador de volume de documentos complexos) — recommended

### Traces
- [ ] Span por estágio: perception, decision, memory, reflection — mandatory
- [ ] Span por iteração do ReflectionHandler com `score` e `costDelta` — mandatory
- [ ] traceId constante em todos os spans de um mesmo pipeline run — mandatory
- [ ] Span de BudgetMonitor linkado ao span da iteração que disparou a decisão — recommended

## Extensibility
- [ ] Novo estágio implementável como EventEmitter subscriber sem modificar handlers existentes — mandatory
- [ ] CheckpointStore acessado apenas via interface read/write; swappável para SQLite sem alterar stage handlers — mandatory
- [ ] Model swap por estágio via variável de configuração sem mudança de código — recommended
- [ ] word-overlap RAG no MemoryHandler substituível por semantic search (ChromaDB) sem alterar a interface do handler — recommended

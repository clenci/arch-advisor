## Session: Technical Document Critic Agent

Date: 2026-03-13
Status: discovery-complete

### Requirements Summary

- Domain: CI/CD-invoked document quality analysis — recebe Markdown, produz relatório crítico estruturado com classificação de tipo/domínio, avaliação de profundidade/completude/clareza/acionabilidade, refinado iterativamente
- Primary action: Orchestrate + generate — pipeline 4 estágios (Perception → Decision → Memory → Reflection)
- Volume: Dezenas/dia, sem concorrência; 1–5 docs/hora por equipe; 1.000 docs/dia como melhoria futura não comprometida
- Latency target: Async (minutos) — 30s–3min por documento; nenhum sistema downstream aguarda sincronamente
- Data sources: Markdown local em disco; LTM in-memory indexada por domínio; formatos adicionais (URL, PDF, HTML) e ChromaDB/SQLite previstos no módulo mas não implementados
- Integrations: Nenhuma; Claude via proxy CI&T Flow (sem acesso direto à API pública)
- Constraints: TypeScript + Node.js; Sonnet 4.6 + Haiku 4.5 via proxy; sem vector store externo; sem banco de dados; hard budget $0.30/análise com extensão adaptativa se score > 0.65
- Compliance: Nenhuma; ambiente de desenvolvimento/estudos
- Team maturity: Experienced — objetivo pedagógico explícito: dominar Reflection Loop, LTM, pipeline multi-camada, Strategy, Chain of Responsibility, State Machine

### Group E — Failure, History, Priorities

- Prior attempts: Nenhum
- Consequence of wrong output: Perda financeira — classificação incorreta gera retrabalho downstream
- Requirement to cut first: Tech stack (diversificação de modelos/providers)
- Success measurement: Áreas de negócio medem taxa de erro (documentos classificados incorretamente)

### Resolved Tensions

- **LTM in-memory vs. invocações isoladas de processo**: User chose LTM persistence. Consequence accepted: PipelineCheckpoint JSON serializa LTM ao final de cada run; warm-start carrega checkpoint no boot. Reason given: "resolva a favor da LTM"
- **Hard budget $0.30 vs. completude do relatório**: User chose adaptive hard stop. Consequence accepted: $0.30 é o teto default; se score > 0.65 no momento da verificação, extensão condicional via --promise-to-improve, máximo 3 iterações adicionais, teto absoluto $0.50. Reason given: "aceita como hard stop mas pode implementar budget adaptativo via promise to improve se score > 0.65"

### Stress Test Responses

- **Scale (10x)**: LTM in-memory quebra primeiro — centenas de docs/dia excederia memória viável in-process. Trigger para migrar para storage persistente (SQLite ou vector store).
- **Budget pressure (50% cut to $0.15)**: Sacrifica profundidade de iteração (menos loops por estágio) — preserva cobertura de estágios e threshold de qualidade.
- **Future requirements**: URLs, PDF, HTML, ChromaDB, SQLite são possibilidades, não compromissos. Extension points de formato e storage são recomendados, não obrigatórios.

### Phase 2 — Requirements Analysis

**Patterns:** Sequential Pipeline, Reflection Loop (Critic-Reviser), LTM + Persistent Checkpoint, STM (in-session), Strategy Binary Model Routing (Haiku 4.5 / Sonnet 4.6), Adaptive Budget Gate, Stage Checkpoint / Idempotent Execution, Circuit Breaker on proxy, Word-Overlap In-Memory RAG.

**Ambiguities:** None.

**Top 3 Risks:** (1) PipelineCheckpoint corruption — medium/medium — atomic write via rename + cold-start fallback; (2) Budget extension slow convergence — low/medium — $0.50 absolute ceiling + oscillation detection; (3) Reflection non-convergence on pathological docs — low-medium/high — explicit convergenceStatus field in output.

**Constraints Impact:** TypeScript-only eliminates Python frameworks; proxy-only eliminates multi-provider fallback; no external storage limits LTM to JSON + word-overlap RAG; adaptive budget gate is first-class pipeline component.

Status: analysis-complete

### Chosen Option

**Option B — Event-Driven Pipeline com Stage Checkpoints**

PipelineOrchestrator coordena 4 handlers via in-process EventBus; cada handler emite completion event; CheckpointWriter persiste output atomicamente; BudgetMonitor é subscriber independente que emite budget:extend | budget:halt; ReportEmitter escreve CritiqueReport com convergenceStatus obrigatório.

Status: option-chosen

Status: artifacts-generated

Status: complete

### Deepening Documents

- storage-memory: CheckpointStore split (ltm.json + run-{traceId}.json), interface swappável, compactação LTM, caminho de migração JSON → SQLite → ChromaDB

# Deepening: Storage and Memory Design
## Technical Document Critic Agent — Event-Driven Pipeline

---

## Situação atual

O CheckpointStore unifica dois concerns distintos num único arquivo JSON:

1. **LTM state** — análises anteriores indexadas por domínio; alimenta o MemoryHandler no warm-start
2. **Stage outputs** — outputs intermediários do run atual (ParsedDoc, Classification, EnrichedContext); usados para recovery parcial em falha de processo

Unificar ambos num único arquivo funciona para o volume atual, mas cria dois problemas que crescem com o tempo:
- **Crescimento não controlado**: cada run acrescenta registros de LTM; sem compactação, o arquivo cresce indefinidamente
- **Colisão de lifecycle**: stage outputs (efêmeros — válidos só durante o run) e LTM (persistentes — acumulam entre runs) têm políticas de retenção completamente diferentes

A recomendação é separar os dois concerns em arquivos distintos desde o início, mesmo que ambos sejam JSON por enquanto.

---

## Estrutura recomendada do CheckpointStore

```
.checkpoint/
  ltm.json          ← LTM persistente; sobrevive entre runs; cresce com o tempo
  run-{traceId}.json ← Stage outputs do run atual; descartado após completion bem-sucedida
```

### ltm.json — schema

```json
{
  "version": 2,
  "updatedAt": "2026-03-13T14:22:00Z",
  "entries": [
    {
      "id": "uuid",
      "domain": "architecture",
      "documentType": "ADR",
      "summary": "Decisão sobre orquestração event-driven",
      "keywords": ["event-driven", "checkpoint", "orchestration"],
      "score": 0.82,
      "analysisDate": "2026-03-13",
      "traceId": "abc123"
    }
  ]
}
```

**Por que `version` no schema:** quando a estrutura de `entries` mudar, o warm-start detecta incompatibilidade e faz fallback para cold-start em vez de crashar com parse error.

**Por que `keywords` explícito:** word-overlap RAG funciona sobre um array de tokens — manter keywords pré-computadas elimina re-tokenização a cada recuperação e torna o retrieval O(n × k) onde k é o número de keywords, não O(n × doc_length).

### run-{traceId}.json — schema

```json
{
  "version": 1,
  "traceId": "abc123",
  "startedAt": "2026-03-13T14:20:00Z",
  "stages": {
    "perception": { "status": "complete", "output": { ... }, "completedAt": "..." },
    "decision":   { "status": "complete", "output": { ... }, "completedAt": "..." },
    "memory":     { "status": "complete", "output": { ... }, "completedAt": "..." },
    "reflection": { "status": "in-progress", "iterations": [...] }
  }
}
```

O arquivo de run é criado no boot e deletado pelo ReportEmitter após escrita bem-sucedida do relatório. Se o processo é morto antes do teardown, o arquivo persiste — o próximo boot o detecta e pode resumir o run ou descartá-lo.

---

## Padrão de escrita atômica

Todo write no CheckpointStore deve seguir o padrão temp-rename:

```typescript
async function atomicWrite(targetPath: string, data: unknown): Promise<void> {
  const tempPath = `${targetPath}.tmp.${process.pid}`;
  await fs.writeFile(tempPath, JSON.stringify(data, null, 2), 'utf8');
  await fs.rename(tempPath, targetPath); // atômico no mesmo filesystem
}
```

**Por que `process.pid` no nome do temp:** em caso de crash antes do rename, o arquivo temporário fica identificável e pode ser limpo no próximo boot sem ambiguidade.

**Limitação importante:** `fs.rename` é atômico apenas dentro do mesmo filesystem. Se `.checkpoint/` estiver num mount point diferente do diretório temporário do sistema, usar `mv` via shell ou garantir que o temp file fica no mesmo diretório que o target.

---

## Interface do CheckpointStore (extension point para SQLite)

O ADR especifica que o CheckpointStore deve ser swappável sem alterar stage handlers. A interface mínima:

```typescript
interface CheckpointStore {
  // LTM operations
  loadLTM(): Promise<LTMEntry[]>;
  appendLTM(entry: LTMEntry): Promise<void>;
  compactLTM(maxEntries: number): Promise<void>;

  // Stage output operations
  saveStageOutput(traceId: string, stage: StageName, output: unknown): Promise<void>;
  loadStageOutput(traceId: string, stage: StageName): Promise<unknown | null>;
  clearRunCheckpoint(traceId: string): Promise<void>;
}
```

Implementações:
- `JsonCheckpointStore` — atual; zero dependências externas
- `SqliteCheckpointStore` — migration tier; SQLite via `better-sqlite3`; sem servidor
- `ChromaCheckpointStore` — next scale tier; semantic search via embeddings

Os stage handlers chamam apenas `CheckpointStore` — nunca `JsonCheckpointStore` diretamente. O PipelineOrchestrator injeta a implementação concreta no boot.

---

## Compactação de LTM

Sem compactação, `ltm.json` cresce indefinidamente. Com dezenas de análises por dia, em 6 meses o arquivo terá milhares de entradas — a leitura completa no warm-start começa a impactar o tempo de boot.

**Estratégia de compactação recomendada:**

```typescript
async function compactLTM(store: CheckpointStore, maxEntries: number = 500): Promise<void> {
  const entries = await store.loadLTM();
  if (entries.length <= maxEntries) return;

  // Manter as N entradas mais recentes + as N/2 entradas com score mais alto
  const byDate = entries.sort((a, b) => b.analysisDate.localeCompare(a.analysisDate));
  const recent = byDate.slice(0, maxEntries * 0.67);
  const highScore = entries
    .filter(e => !recent.includes(e))
    .sort((a, b) => b.score - a.score)
    .slice(0, maxEntries * 0.33);

  await store.saveLTM([...recent, ...highScore]);
}
```

Executar `compactLTM` no teardown, após a escrita do LTM do run atual. Trigger: `entries.length > 500` (ajustável). Com 50 análises/dia, esse threshold é atingido em ~10 dias — bem antes do limite de 50MB.

---

## Caminho de migração: JSON → SQLite → ChromaDB

| Trigger | Ação | Mudança de código |
|---|---|---|
| `ltm.json` > 50MB ou boot > 2s | Migrar para `SqliteCheckpointStore` | Trocar implementação no DI; schema SQL abaixo |
| Volume > 200/dia com concorrência | Migrar para worker pool (Option C) | Arquitetura muda para Distributed Pipeline |
| word-overlap retrieval retorna < 60% de relevância (medido por LLM-as-Judge) | Migrar LTM para ChromaDB + embeddings | Trocar `CheckpointStore.loadLTM` por query semântica |

### Schema SQLite para LTM

```sql
CREATE TABLE ltm_entries (
  id          TEXT PRIMARY KEY,
  domain      TEXT NOT NULL,
  document_type TEXT NOT NULL,
  summary     TEXT NOT NULL,
  keywords    TEXT NOT NULL,  -- JSON array
  score       REAL NOT NULL,
  analysis_date TEXT NOT NULL,
  trace_id    TEXT NOT NULL,
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_ltm_domain ON ltm_entries(domain);
CREATE INDEX idx_ltm_score  ON ltm_entries(score DESC);
CREATE INDEX idx_ltm_date   ON ltm_entries(analysis_date DESC);
```

O MemoryHandler com SQLite substitui o loop de word-overlap por:

```sql
SELECT * FROM ltm_entries
WHERE domain = :domain
  AND keywords LIKE '%' || :keyword || '%'
ORDER BY score DESC, analysis_date DESC
LIMIT 10;
```

---

## Recomendação

**Implemente agora (zero custo adicional):**
1. Separar `ltm.json` de `run-{traceId}.json` — lifecycle diferentes exigem arquivos diferentes
2. Adicionar `version` e `keywords` pré-computadas no schema de LTM
3. Implementar `CheckpointStore` como interface com `JsonCheckpointStore` como implementação concreta injetada no boot
4. Implementar `compactLTM` com threshold de 500 entradas

**Implemente quando o trigger ocorrer:**
- Boot > 2s ou arquivo > 50MB → `SqliteCheckpointStore` (3–4 horas de migração)
- word-overlap retrieval com < 60% de relevância → `ChromaCheckpointStore` (migração mais custosa: requer re-embedding de todo o histórico LTM)

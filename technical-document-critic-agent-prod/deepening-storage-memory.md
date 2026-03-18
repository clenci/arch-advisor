# Deepening: Storage and Memory Design — Technical Document Critic Agent

## 1. Separação STM / LTM: o que vive onde

Para este sistema, a distinção STM/LTM é **por escopo de análise**, não por janela de conversa:

| Tipo | Escopo | Storage | Conteúdo |
|---|---|---|---|
| STM | Análise corrente | In-process (`SessionState`) | Perception output, Decision result, revisões da iteração atual, budgetState |
| LTM | Cross-invocation, por domínio | CheckpointStore (JSON em disco) | Padrões úteis de análises anteriores do mesmo domínio/tipo |

**O que NÃO entra na LTM:** o relatório completo gerado. O que entra é um **summaryForLTM** compacto — os padrões extraídos que foram úteis para o relatório, não o relatório em si.

---

## 2. Schema do CheckpointStore

```typescript
// ltm.json — estrutura completa
interface CheckpointStore {
  version: '1.0';
  lastUpdated: string;        // ISO 8601
  domains: Record<string, DomainEntry[]>;
}

interface DomainEntry {
  traceId: string;
  docType: string;            // 'adr' | 'rfc' | 'architecture' | 'api-spec' | ...
  analyzedAt: string;         // ISO 8601
  finalScore: number;         // 0–1; somente entradas com score ≥ threshold são gravadas
  dimensionScores: {
    depth: number;
    completeness: number;
    clarity: number;
    actionability: number;
  };
  keyPatterns: string[];      // termos-chave extraídos; base para word-overlap retrieval
  summaryForLTM: string;      // 2–3 frases: padrões úteis observados; NÃO é o relatório completo
}
```

**Tamanho estimado por entrada:** ~500–800 bytes. Com compactação em 50 entradas/domínio e 10 domínios: ~400KB. Startup de leitura JSON de 400KB em Node.js: < 50ms.

**Estimativa 1 ano a 50 docs/dia sem compactação:** ~18.000 entradas × 700 bytes = ~12,6MB. Com compactação top-50 por domínio: permanece abaixo de 1MB indefinidamente.

---

## 3. Retrieval por word-overlap: implementação concreta

```typescript
class LTMRetriever {
  retrieve(currentKeywords: string[], domain: string, docType: string,
           store: CheckpointStore, topK = 3): DomainEntry[] {
    const candidates = store.domains[domain]?.filter(e => e.docType === docType) ?? [];

    const scored = candidates.map(entry => {
      const overlap = entry.keyPatterns.filter(p => currentKeywords.includes(p)).length;
      const score = overlap / Math.max(currentKeywords.length, entry.keyPatterns.length, 1);
      return { entry, score };
    });

    return scored
      .sort((a, b) => b.score - a.score)
      .slice(0, topK)
      .map(s => s.entry);
  }
}
```

**Trade-off word-overlap vs. embeddings:**
- Word-overlap: zero custo adicional; funciona bem para docs técnicos (termos como "ADR", "trade-off", "circuit breaker" têm alta especificidade)
- Embeddings: +$0.001–0.003 por análise; necessário apenas quando sinônimos técnicos num domínio com vocabulário variado causarem falhas de retrieval
- **Recomendação:** manter word-overlap até que a taxa de erros de classificação atinja o limiar de alerta (5%). Só então considerar embeddings.

---

## 4. Política de compactação

Compactar **no momento da gravação**, não em job separado:

```typescript
class CheckpointStore {
  private readonly MAX_ENTRIES_PER_DOMAIN = 50;
  private readonly MIN_SCORE_TO_PERSIST = 0.75;

  async save(entry: DomainEntry, domain: string): Promise<void> {
    if (entry.finalScore < this.MIN_SCORE_TO_PERSIST) return; // não persiste análise abortada

    const store = await this.load();
    const domainEntries = store.domains[domain] ?? [];

    domainEntries.push(entry);

    // Compacta: mantém top-N por finalScore (não por recência)
    if (domainEntries.length > this.MAX_ENTRIES_PER_DOMAIN) {
      domainEntries.sort((a, b) => b.finalScore - a.finalScore);
      domainEntries.splice(this.MAX_ENTRIES_PER_DOMAIN);
    }

    store.domains[domain] = domainEntries;
    store.lastUpdated = new Date().toISOString();
    await this.writeAtomic(store);
  }
}
```

**Por que top-N por score e não por recência:** análises antigas com score alto têm padrões mais confiáveis que análises recentes com score baixo. Recência pode ser critério de desempate se necessário.

---

## 5. Write atômico: tmp + rename

```typescript
private async writeAtomic(data: CheckpointStore): Promise<void> {
  const tmpPath = this.filePath + '.tmp';
  try {
    await fs.writeFile(tmpPath, JSON.stringify(data, null, 2), 'utf-8');
    await fs.rename(tmpPath, this.filePath); // atômico no mesmo filesystem (garantia POSIX)
  } catch (error) {
    await fs.unlink(tmpPath).catch(() => {}); // limpa .tmp em caso de falha
    throw error;
  }
}

async load(): Promise<CheckpointStore> {
  // Remove .tmp órfão de crash anterior
  await fs.unlink(this.filePath + '.tmp').catch(() => {});
  try {
    const raw = await fs.readFile(this.filePath, 'utf-8');
    return JSON.parse(raw);
  } catch {
    return { version: '1.0', lastUpdated: new Date().toISOString(), domains: {} };
  }
}
```

---

## 6. Gatilhos de migração para SQLite

| Métrica | Valor atual esperado | Gatilho de migração | Ação |
|---|---|---|---|
| Tamanho do `ltm.json` | < 500KB | > 5MB | Migrar para SQLite + índice por domínio |
| Startup (load até ready) | < 50ms | > 500ms | Migrar para SQLite ou segmentar por arquivo/domínio |
| Entradas totais | < 500 | > 2.000 | Migrar para SQLite |
| Análises/dia | ~50 | > 300 com concorrência | Migrar EventBus → BullMQ + SQLite simultaneamente |

**Migração sem re-embedding:** diferentemente de migrar de Chroma para Pinecone, migrar de JSON para SQLite é leitura do JSON + `INSERT` em massa. Nenhum dado é perdido e nenhuma chamada LLM é necessária.

```typescript
// Script de migração: json-to-sqlite.ts
async function migrate(jsonPath: string, dbPath: string) {
  const store: CheckpointStore = JSON.parse(await fs.readFile(jsonPath, 'utf-8'));
  const db = new Database(dbPath); // better-sqlite3

  db.exec(`CREATE TABLE ltm_entries (
    trace_id TEXT PRIMARY KEY,
    domain TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    analyzed_at TEXT NOT NULL,
    final_score REAL NOT NULL,
    key_patterns TEXT NOT NULL,
    summary TEXT NOT NULL,
    dimension_scores TEXT NOT NULL
  )`);
  db.exec('CREATE INDEX idx_domain_doctype ON ltm_entries(domain, doc_type)');

  const insert = db.prepare(`INSERT INTO ltm_entries VALUES (?,?,?,?,?,?,?,?)`);
  for (const [domain, entries] of Object.entries(store.domains)) {
    for (const e of entries) {
      insert.run(e.traceId, domain, e.docType, e.analyzedAt, e.finalScore,
        JSON.stringify(e.keyPatterns), e.summaryForLTM, JSON.stringify(e.dimensionScores));
    }
  }
}
```

---

## Recomendação Consolidada

| Decisão | Recomendação | Condição de revisão |
|---|---|---|
| Storage type | JSON CheckpointStore | Migrar para SQLite quando > 2.000 entradas ou startup > 500ms |
| Compactação | Top-50 por score no momento da gravação | Aumentar para top-100 se domínios ficarem sub-representados |
| Retrieval | Word-overlap top-3 por domínio+docType | Adicionar embeddings se taxa de classificação piorar sem melhoria com LTM |
| Política de qualidade | Persistir somente score ≥ 0,75 | Reduzir para 0,65 se um domínio ficar sem entradas suficientes |
| Write atômico | tmp + rename + limpeza de órfãos no load | Suficiente para processo único; revisar se concorrência emergir |

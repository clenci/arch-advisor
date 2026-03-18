# Roteiro refinado de respostas para o /arch-advisor

## Group A — Domain and Purpose

1.  O sistema recebe um documento técnico (Markdown) e produz um relatório de análise crítica — classificando tipo e domínio, avaliando profundidade, completude, clareza e acionabilidade, e refinando o relatório iterativamente até atingir qualidade aceitável. Resolve a revisão técnica manual de documentação de software.
2.  Primariamente outros sistemas (pipeline de CI/CD, ferramentas de repositório) que invocam o agente programaticamente via agent.analyze(). Desenvolvedores consomem o relatório Markdown gerado — sem interface interativa em tempo de execução.
3.  Orchestrate + generate: orquestra um pipeline sequencial de 4 camadas (Perception → Decision → Memory → Reflection) e produz um relatório de análise crítica como output principal.

## Group B — Scale and Performance

4.  Baixo volume: dezenas de documentos por dia, sem concorrência. Caso de uso típico: análise antes de merge (1–5 docs/hora por equipe). O módulo menciona escalar para 1.000 docs/dia como melhoria futura — não é requisito atual.
5.  Async — minutos. O pipeline executa 4–7 chamadas LLM em série (classify + generate + 1–3× [critique + revise]). Latência observada: 30s–3min por documento. Não há requisito de resposta em tempo real.
6.  Hard constraint: budget fixo de $0.30 por análise. O agente interrompe o Reflection Loop quando o budget é atingido (stoppedBy: "costBudget"). Custo real observado: $0.09–$0.15 por análise completa com 3 iterações.

## Group C — Data and Integrations

7.  Arquivos locais: documentos Markdown em disco (implementado) - LTM em memória: análises anteriores indexadas por domínio para enriquecer o relatório atual (implementado) - Previsto no módulo, não implementado: URLs, PDF, HTML — o módulo especificava múltiplos formatos e ChromaDB/SQLite; a implementação simplificou para Markdown + LTM in-memory
8.  Nenhum. O agente é autônomo. Integração com CI/CD acontece na camada de invocação externa, fora do escopo do agente.
9.  Internal: documentação técnica de software (arquiteturas, padrões, decisões de design). Sem PII, sem dados regulados por LGPD/GDPR/HIPAA.

## Group D — Constraints and Team

10. Linguagem: TypeScript + Node.js - LLM: Anthropic Claude via proxy corporativo (CI&T Flow) — sem acesso direto à API pública - Modelos disponíveis: Claude Sonnet 4.6 (padrão) e Haiku 4.5 (rápido/barato) - Sem vector store externo: o módulo previa ChromaDB/Pinecone, mas a implementação usa word-overlap in-memory para manter zero dependências externas além do LLM - Sem banco de dados: o módulo previa SQLite; implementação simplificou para memória runtime
11. Experienced: o sistema será construído num guia de estudos de Principal Architect de IA — o objetivo explícito era dominar os padrões Reflection Loop, LTM, pipeline multi-camada e design patterns (Strategy, Chain of Responsibility, State Machine).
12. Nenhum. Ambiente de desenvolvimento/estudos. O módulo exigia logging estruturado e trace ID por questão de observabilidade interna, não por compliance regulatório.

## Tensões que o plugin vai identificar — e como responder

### Tensão esperada: LTM in-memory não persiste entre processos

> Aceito conscientemente. O módulo previa SQLite + ChromaDB; simplifiquei para focar nos padrões de memória, não na infraestrutura. Para produção, a interface AnalysisLTM suporta troca sem alterar o pipeline.

### Tensão esperada: 4–7 chamadas LLM sequenciais vs. latência

> Aceito. O requisito é async. O Reflection Loop tem budget e iterações máximas como válvulas de segurança.

### Tensão esperada: Word-overlap pode falhar em termos multilíngues

> Risco real baixo: o espaço de domínios é controlado pelo classifier (valores como 'arquitetura de software', não queries livres de usuário).

### Tensão esperada: Perception limitada a Markdown vs. requisito de múltiplos formatos

> Escopo reduzido deliberadamente. O módulo previa TXT/PDF/HTML/URL; a implementação priorizou as camadas Decision, Memory e Reflection — que eram o foco pedagógico do módulo.

## Ambiguidades — e como responder

### A1 — Persistência da LTM

O agente é invocado como um processo de longa duração (servidor/daemon que recebe múltiplos documentos) ou como processo efêmero (um processo novo por análise, padrão em jobs CI/CD)?
Se efêmero, a LTM in-memory reinicia a cada chamada e não agrega valor — isso é um risco arquitetural crítico.

#### Resposta preparada

> O agente é longa duração dentro de uma sessão: DocumentAnalysisAgent é instanciado uma vez em main() e o loop for (const doc of documents) reutiliza a mesma instância — o LTM acumula entre análises do mesmo run. Cada processo novo começa com LTM vazio. Portanto: efêmero entre processos, persistente dentro do processo. Em uso real como job CI/CD (um processo por commit), o LTM só tem valor se múltiplos documentos forem analisados no mesmo job — o que é o caso no run.ts (2 docs com domínio sobrepostos). Para persistência cross-run, seria necessário serializar o LTM em disco.

### A2 — Condição de parada do Reflection Loop

O loop para apenas quando o budget é atingido ou o contador chega a 3, ou existe uma condição de qualidade — o agente de critique pode sinalizar "sem mais revisões necessárias" antes de atingir o
limite?

#### Resposta preparada

> Existem três condições de parada implementadas, em ordem de verificação:
>
> 1.  Threshold de qualidade (isAcceptable = overallScore >= 0.78) — o loop para cedo se o score já é suficiente (log: "Threshold atingido")
> 2.  Budget esgotado (totalCost >= $0.30) — interrompe antes de uma iteração de revisão
> 3.  Máximo de iterações (MAX_ITERATIONS = 3) — limite absoluto
>
> O critic sim sinaliza qualidade aceitável via critique.isAcceptable, e isso é a condição de saída prioritária — não é apenas contador/budget.

### A3 — Contrato de extensibilidade do Perception Stage

Os formatos futuros (URL, PDF, HTML) precisam de um ponto de extensão formal (interface adapter) no design atual, ou são tratados como completamente fora de escopo e o pipeline pode assumir
Markdown como único input?

#### Resposta preparada

> Sem interface formal de adapter. A camada de percepção é composta por duas funções exportadas em perception.ts: loadDocument(filePath): string e chunkDocument(content): Chunk[]. Não há interface
>
> SourceLoader ou FormatAdapter. Markdown é o único formato suportado — loadDocument usa readFileSync direto. Para adicionar PDF/URL, seria necessário refatorar para um padrão Strategy, o que não existe hoje. O plugin vai identificar isso como gap de extensibilidade.

### A4 — Rastreamento de custo

O custo por chamada LLM é obtido via contagem de tokens na resposta da API (post-call), por estimativa pré-chamada, ou por alocação fixa por stage (ex: classify=Haiku, generate=Sonnet)?

#### Resposta preparada

> Post-call via usage da API. Todo componente que chama o LLM (classifier, report-generator, critic, reviser) calcula o custo após receber a resposta usando response.usage.input_tokens e
> response.usage.output_tokens com preços fixos hard-coded ($3.00/M input, $15.00/M output — preços do Sonnet). O orquestrador acumula em totalCost += componentCost. Não há estimativa pré-call nem
> alocação fixa por stage — o cálculo é sempre exato, baseado nos tokens reais consumidos.

### A5 — Contrato de output

O schema do relatório gerado é fixo (seções predefinidas: Summary, Issues, Recommendations) ou dinâmico — determinado pelo tipo/domínio do documento classificado na primeira stage?

#### Resposta preparada

> Schema fixo com conteúdo dinâmico. As seções são predefinidas no prompt do ReportGenerator: ### Sumário, ### Pontos Fortes, ### Gaps e Problemas, ### Recomendações, ### Score de Qualidade. O tipo
> e domínio (vindos do classifier) influenciam o conteúdo dessas seções (via focusAreas e ltmContext injetados no prompt), mas não a estrutura. O schema é um Markdown de texto livre — não há parsing
> estruturado do output, o reportMarkdown é string bruta.

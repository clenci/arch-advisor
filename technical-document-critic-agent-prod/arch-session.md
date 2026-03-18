## Session: Technical Document Critic Agent

Date: 2026-03-13
Status: complete

### Respostas — Grupo A

- Problema: recebe documento Markdown e produz relatório de análise crítica (classifica tipo/domínio, avalia profundidade/completude/clareza/acionabilidade, refina iterativamente até qualidade aceitável). Resolve revisão técnica manual de documentação de software.
- Usuários finais: principalmente outros sistemas (pipeline CI/CD, ferramentas de repositório) via agent.analyze(). Desenvolvedores consomem o relatório Markdown gerado.
- Ação primária: orchestrate + generate — pipeline sequencial 4 camadas (Perception → Decision → Memory → Reflection) + relatório Markdown como output.

### Respostas — Grupo B

- Volume: dezenas de docs/dia, sem concorrência atual. Escala para 1.000 docs/dia mencionada como melhoria futura (não é requisito).
- Latência: async — 30s–3min por documento. Pipeline de 4–7 chamadas LLM em série.
- Custo: hard constraint — $0.30/análise. Custo real observado: $0.09–$0.15 com 3 iterações.
- Padrão de chegada: bursty/event-driven (disparado por eventos CI/CD — pushes, merges). Eventos imprevisíveis; concentração mais comum em horário comercial.

### Respostas — Grupo C

- Fontes de dados: arquivos Markdown em disco + LTM in-memory (análises anteriores indexadas por domínio). Formatos adicionais (URL, PDF, HTML, ChromaDB/SQLite) previstos no módulo mas não implementados.
- Integrações: nenhuma. Integração com CI/CD ocorre na camada de invocação externa, fora do escopo do agente.
- Sensibilidade: internal — documentação técnica de software. Sem PII, sem dados regulados.

### Respostas — Grupo D

- Restrições tecnológicas: TypeScript + Node.js; LLM via proxy CI&T Flow (LiteLLM-based, infraestrutura própria, acesso a múltiplos providers: Amazon Bedrock, Anthropic, DeepSeek, Gemini, GPT, Grok, Mistral — compatível com respectivas APIs); modelos primários: Sonnet 4.6 (padrão) e Haiku 4.5; sem vector store externo; sem banco de dados (memória runtime apenas); zero dependências externas além do LLM. LangChain.js e LangGraph.js são válidos para TypeScript.
- Familiaridade: experienced — projeto de estudos de padrões (Reflection Loop, LTM, pipeline multi-camada, Strategy, Chain of Responsibility, State Machine).
- Compliance: nenhum. Logging estruturado e trace ID por observabilidade interna, não regulatório.

### Respostas — Grupo E

- Histórico: não há tentativa anterior.
- Consequência de output errado: custo de retrabalho para times downstream lidando com documentos classificados incorretamente.
- Requisito cortável: tech stack.
- Critério de sucesso externo: área de negócios mede taxa de erros de classificação de documentos.

### Tensões Resolvidas

- **LTM cross-invocation vs. zero dependências externas**: Usuário escolheu LTM persistente. Consequência aceita: adicionar componente `CheckpointStore` (arquivo JSON em disco, lido no startup e gravado no encerramento). Zero dependência externa mantida. Razão: "resolva a favor da LTM persistente"

- **Hard budget gate vs. qualidade de classificação**: Usuário escolheu hard stop com budget adaptativo. Consequência aceita: `BudgetMonitor` implementa hard stop em $0.30 com extensão condicional até $0.50 se score > 0.65 na iteração anterior. Custo variável entre $0.30–$0.50 em casos de alta qualidade parcial. Razão: "aceita como hard stop mas com budget adaptativo se score > 0.65"

### Opção Escolhida

**Opção B: Event-Driven Pipeline com Stage Checkpoints**
Status: option-chosen

### Análise de Requisitos (Fase 2)

**Patterns Needed:** Pipeline sequencial com checkpoints de estágio; Reflection Loop (critic-reviser); BudgetMonitor com gate adaptativo ($0.30 hard stop, extensão até $0.50 se score > 0.65); STM + LTM two-layer memory (CheckpointStore JSON); Model routing por estágio (Sonnet/Haiku via proxy multi-provider); Circuit breaker no LLM provider; Strategy para DocumentReader.

**Top 3 Risks:** (1) Runaway CheckpointStore — JSON cresce indefinidamente; mitigação: compactação por domínio + write atômico. (2) Budget gate interrompe mid-call — checar budget ANTES de cada chamada LLM. (3) Deriva de qualidade por LTM com viés de domínio — persistir somente análises com score ≥ threshold.

**Constraints Impact:** Zero external deps elimina ChromaDB/SQLite/Redis; proxy multi-provider habilita model routing como configuração; LangChain.js/LangGraph.js válidos para TypeScript.

### Stress Test Responses

- **Escala 10x**: LTM in-memory quebra primeiro — não suporta o volume crescente de análises acumuladas.
- **Pressão de orçamento**: Sacrifica profundidade das iterações primeiro (reduzir de 3 para 1–2 iterações de refinamento).
- **Requisitos futuros**: Escala para 1.000 docs/dia e suporte a múltiplos formatos (PDF, HTML, URL) + vector store são possibilidades em aberto, não requisitos comprometidos. Extension points recomendados mas não obrigatórios.

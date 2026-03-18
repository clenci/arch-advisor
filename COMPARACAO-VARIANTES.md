# Comparação de Variantes — arch-advisor

Você vai avaliar comparativamente os resultados das versões do plugin arch-advisor, executadas sobre o mesmo caso de uso. Os artefatos e o histórico de análise de cada variante estão em pastas separadas.

## Variantes

Inclua na comparação todas as pastas presentes no diretório. Para cada uma, leia o `plugin.json` em `.claude-plugin/` para identificar nome e versão antes de iniciar a avaliação.

## Localização dos Arquivos

Cada variante tem sua própria pasta com todos os artefatos e o histórico completo da sessão:

```
├── v1/
│   ├── arch-session.md        ← histórico completo da sessão
│   ├── container-diagram.md
│   ├── adr-001-*.md
│   ├── decision-matrix.md
│   └── nfr-checklist.md
├── v2/
│   └── ...
├── vN/
│   └── ...
```

Leia todos os arquivos de todas as pastas antes de iniciar a avaliação. Não comece a escrever o relatório antes de ter lido todos.

---

## Princípios de Avaliação

Antes de aplicar a rubrica, internalize estas diretrizes para evitar vieses sistemáticos:

**Avalie o que foi observado, não o que foi projetado.** Se uma versão não foi executada e seus artefatos foram gerados antecipadamente (sem sessão real com o usuário), indique isso explicitamente no relatório e desconte o score das dimensões afetadas. Um artefato projetado não pode receber o mesmo score que um artefato gerado a partir de uma sessão real.

**Score máximo não é prêmio de excelência.** 5/5 em uma dimensão significa que não há melhoria identificável naquela dimensão para aquela versão, dado o que foi observado. Se você está atribuindo 5/5 a múltiplas versões na mesma dimensão, revise: ou a dimensão não discrimina bem entre versões, ou o score está inflado.

**Distingua extração de geração.** Quando um componente ou padrão aparece nos artefatos de uma versão, verifique se ele já estava latente nas respostas do usuário. Se estava, o mecanismo extraiu conteúdo existente — valioso, mas diferente de ter gerado conteúdo novo que o usuário não havia articulado. Marque a diferença na análise.

**Cite para cada score.** Cada score que diverge de outra versão (acima ou abaixo) deve ter pelo menos uma citação direta do arquivo que justifica a diferença. Scores iguais entre versões não precisam de justificativa individual, mas devem ser verificados.

---

## Rubrica de Avaliação

### Dimensão 1 — Fidelidade do Processo de Discovery (via arch-session.md)

Avalie se o processo de discovery coletou o que precisava coletar antes de avançar para análise.

**1a. Tensões surfaceadas ao usuário** — quantas tensões arquiteturalmente relevantes foram apresentadas ao usuário para resolução explícita (não resolvidas internamente)? Para cada tensão surfaceada, ela era não-trivial — ou seja, a resposta do usuário mudaria a proposta?
- 1: nenhuma tensão surfaceada; ambiguidades resolvidas internamente
- 3: tensões identificadas mas apresentadas como lista, sem aguardar resposta por item
- 5: cada tensão apresentada individualmente com suas duas consequências arquiteturais, resposta coletada e documentada

**1b. Consequência aceita como insumo arquitetural** — quando o usuário resolveu uma tensão, a consequência aceita apareceu como justificativa nas fases seguintes (Phase 2, Phase 3, ADR)?
- 1: tensões resolvidas não rastreáveis nos artefatos
- 3: mencionadas na seção de requisitos mas sem impacto visível nas opções
- 5: consequence statement aparece nomeada nos padrões, critérios da decision matrix e justificativa do ADR

**1c. Follow-ups adaptativos** — o command disparou follow-ups relevantes após respostas incompletas? Avalie especificamente: (a) o padrão de volume (steady vs. bursty) foi confirmado quando o caller era um sistema externo? (b) sensibilidade dos dados gerou follow-up sobre o que o LLM processa diretamente?
- 1: nenhum follow-up disparou; respostas vagas aceitas sem probing
- 3: follow-up disparou em pelo menos um grupo, mas não nos grupos mais relevantes para o domínio
- 5: follow-up disparou nos grupos onde o domínio identificado no Grupo A tornava a underspecification arquiteturalmente consequente

**1d. Stress test presente e com dados do usuário** — a Phase 1.6 (ou equivalente) foi executada? As condições de "When to Reconsider" na Option C derivam das respostas do usuário ou são estimativas genéricas do Claude?
- 1: ausente
- 3: presente mas thresholds são estimativas genéricas
- 5: thresholds derivados das respostas do usuário ao stress test; tratados como comprometimentos, não recomendações

### Dimensão 2 — Qualidade da Análise (via arch-session.md)

**2a. Padrões com justificativa rastreável** — cada padrão em PATTERNS_NEEDED tem justificativa ligada a um requisito específico declarado ou a uma tensão resolvida, ou as justificativas são genéricas?
- 1: padrões listados sem justificativa
- 3: justificativas existem mas referenciam classes de problema, não requisitos específicos desta sessão
- 5: cada padrão referencia explicitamente um requisito declarado, uma tensão resolvida, ou uma resposta do stress test

**2b. Riscos com dados observáveis** — os riscos têm likelihood/impact explícitos, mitigações concretas, e pelo menos um risco é derivado das respostas do usuário (stress test ou Group E)?
- 1: riscos genéricos sem likelihood/impact
- 3: likelihood/impact presentes mas mitigações vagas; nenhum risco derivado das respostas do usuário
- 5: riscos cruzam com stress test e Group E; pelo menos um risco nomeado a partir do que o usuário declarou como consequência de falha

**2c. Ambiguidades arquiteturalmente consequentes** — as ambiguidades levantadas na Phase 2, se respondidas de forma diferente, mudariam a proposta? Ou são dúvidas cosméticas?
- 1: sem seção de ambiguidades, ou ambiguidades cosméticas
- 3: ambiguidades reais mas apresentadas como lista para o usuário confirmar em bloco
- 5: cada ambiguidade explica como a arquitetura seria diferente dependendo da resposta; coletadas antes de propor opções

### Dimensão 3 — Proposta Arquitetural (via arch-session.md)

**3a. Amplitude estrutural das opções** — as três opções cobrem o espectro mínimo-viável / balanced / next-scale-tier? A Option C é rejeição por escala (projeta o limiar onde a decisão deve ser revisitada) ou apenas uma versão mais complexa da Option B?
- 1: menos de 3 opções, ou variações do mesmo padrão
- 3: opções divergem em complexidade mas Option C não documenta o limiar de escala que a torna necessária
- 5: Option A sacrifica algo explicitamente para ganhar simplicidade; Option C é referência de escala com thresholds mensuráveis derivados da sessão

**3b. Precisão dos trade-offs** — os prós e contras de cada opção estão ligados aos requisitos declarados e às tensões resolvidas, ou são trade-offs genéricos de padrão arquitetural?
- 1: trade-offs genéricos ("mais escalável", "mais simples")
- 3: trade-offs ligados a requisitos mas sem cruzar com as tensões resolvidas
- 5: cada trade-off referencia explicitamente um requisito ou uma consequence statement aceita pelo usuário

### Dimensão 4 — Artefatos

**4a. C4 Diagram** — avalie:
- Usa `System_Boundary` (não `Boundary` genérico), `ContainerDb` para storage, `Person_Ext` para atores externos humanos, `System_Ext` para sistemas externos?
- Todos os componentes da arquitetura escolhida estão representados, incluindo componentes que emergiram de tensões resolvidas?
- Os `Rel()` têm label com protocolo ou descrição do dado transportado?
- 1: não segue convenções C4; componentes faltando; labels ausentes
- 3: convenções parcialmente corretas; componentes emergentes de tensões ausentes
- 5: convenções corretas; todos os componentes presentes incluindo os gerados por tensões; labels descritivos

**4b. ADR** — avalie:
- A seção "When to Reconsider" tem condições concretas e mensuráveis derivadas da sessão (não genéricas)?
- A justificativa cita tensões resolvidas e requisitos específicos declarados pelo usuário?
- As alternativas rejeitadas explicam por que foram descartadas *para este sistema*, não em princípio?
- 1: estrutura incompleta; justificativas genéricas; sem "When to Reconsider"
- 3: estrutura presente; "When to Reconsider" com condições mas genéricas; alternativas rejeitadas com argumento de princípio
- 5: "When to Reconsider" com thresholds da sessão; justificativa rastreia tensões; alternativas rejeitadas com argumento específico para este sistema

**4c. Decision Matrix** — avalie:
- Os critérios derivam dos requisitos declarados e das tensões resolvidas — ou são critérios genéricos?
- Escala 1–10 (não 1–5); scores 8–10 têm justificativa; scores 1–3 têm raciocínio explícito?
- Pesos somam 100% com raciocínio; pelo menos um critério tem peso derivado de uma tensão resolvida?
- 1: critérios genéricos; escala 1–5; sem justificativa para scores extremos
- 3: critérios ligados a requisitos mas não a tensões; escala correta mas scores sem justificativa
- 5: pelo menos um critério derivado de tensão resolvida; scores extremos justificados; pesos com raciocínio explícito

**4d. NFR Checklist** — avalie:
- Todos os targets têm valores concretos derivados dos requisitos — sem "TBD"?
- Cobre as dimensões: performance, custo, resiliência, qualidade, observabilidade, extensibilidade?
- Observabilidade inclui os campos de log obrigatórios (`traceId`, `agentId`, `action`, `durationMs`, `tokensUsed`, `costUsd`), error budget states e hallucination rate?
- Qualidade inclui eval pass rate, quality gates de CI/CD e testabilidade de componentes (mock LLM, componentes isoláveis)?
- 1: targets com "TBD"; dimensões faltando; sem campos de log; sem quality gates
- 3: targets concretos; observabilidade presente mas sem error budget; qualidade sem testabilidade
- 5: todas as dimensões cobertas incluindo extensibilidade; observabilidade com três pilares + error budget; qualidade com gates de CI/CD e testabilidade

### Dimensão 5 — Utilização de Skills de Domínio

Esta dimensão avalia se o plugin ativou conhecimento especializado além do repertório geral de engenharia de software do Claude.

**5a. Skills explicitamente invocadas** — quantas skills foram invocadas via Skill tool (não por contexto semântico)? Quais fases cobriram?
- 1: nenhuma invocação explícita
- 3: 1–2 skills invocadas, cobrindo apenas artefatos (Phase 4)
- 5: 3+ skills invocadas; cobrem tanto pré-artefatos (Phase 3.5 ou equivalente) quanto artefatos (Phase 4)

**5b. Conhecimento de domínio observável nos artefatos** — identifique trechos nos artefatos que demonstram conhecimento especializado rastreável a uma skill. Para cada trecho: cite o arquivo, o trecho, e a skill de origem provável. Avalie:
- 1: nenhum trecho com conhecimento além do repertório geral de ES
- 3: 1–3 trechos rastreáveis a skills; concentrados em uma única dimensão (ex: só observabilidade)
- 5: 4+ trechos rastreáveis a skills distintas; cobrem pelo menos duas dimensões diferentes (ex: observabilidade + testabilidade, ou C4 conventions + ADR template)

**5c. Skills do plugin não utilizadas** — das skills disponíveis no plugin, quantas não foram invocadas em nenhum momento da sessão? Liste-as. Avalie se o command forneceu mecanismo para ativá-las (deepening menu, Phase 3.5, etc.) ou se elas simplesmente não têm ponto de entrada no fluxo.
- 1: mais de 8 skills sem ponto de entrada no fluxo
- 3: 4–8 skills sem ponto de entrada; nenhum mecanismo de deepening oferecido ao usuário
- 5: skills não utilizadas no fluxo principal têm ponto de entrada via deepening menu pós-artefatos, condicionado ao domínio da sessão

### Dimensão 6 — Integridade do Processo (transversal)

**6a. Decisões do usuário vs. decisões internas** — para cada decisão arquitetural significativa (escolha de padrão, componente, threshold), verifique se foi tomada com input do usuário ou internamente pelo Claude. Classifique cada uma.
- 1: maioria das decisões tomadas internamente sem surfacing ao usuário
- 3: decisões principais surfaceadas; decisões de detalhe tomadas internamente sem indicação
- 5: distinção clara entre o que foi decidido pelo usuário (documentado com citação) e o que foi assumido pelo Claude (anotado como default)

**6b. Rastreabilidade fim-a-fim** — dado apenas o `arch-session.md` e os artefatos, é possível reconstruir por que cada componente arquitetural existe? Ou há componentes sem origem rastreável nos requisitos ou nas tensões?
- 1: componentes sem origem rastreável
- 3: componentes principais rastreáveis; componentes de detalhe sem origem documentada
- 5: todos os componentes têm origem rastreável a um requisito declarado, tensão resolvida, ou resposta do stress test

---

## Instruções para Scoring

Para cada dimensão, atribua um score de 1 a 5. **Não use o score máximo sem justificativa explícita.** Antes de atribuir 5/5, responda: "O que esta versão faria diferente para merecer um score ainda maior?" Se não há resposta, o score é válido. Se há resposta, reduza para 4.

A escala é:
- **1** — ausente ou sistematicamente falho
- **2** — presente mas com lacunas graves que afetam a utilidade
- **3** — funcional; atende o critério básico mas com limitações identificáveis
- **4** — sólido; limitações existem mas são menores ou contextuais
- **5** — exemplar para a versão avaliada; não há melhoria identificável dado o que foi observado

---

## Output Esperado

Produza o relatório neste formato:

---

# Relatório Comparativo: arch-advisor [versões]

**Data:** [hoje]
**Avaliado por:** [modelo]
**Sessões observadas vs. projetadas:** [indicar quais versões foram executadas em sessão real e quais tiveram artefatos gerados antecipadamente]

## Scores por Dimensão

| Dimensão | v1 | v2 | v3 | vN |
|---|---|---|---|---|
| 1a. Tensões surfaceadas ao usuário | | | | |
| 1b. Consequência aceita como insumo arquitetural | | | | |
| 1c. Follow-ups adaptativos | | | | |
| 1d. Stress test com dados do usuário | | | | |
| 2a. Padrões com justificativa rastreável | | | | |
| 2b. Riscos com dados observáveis | | | | |
| 2c. Ambiguidades arquiteturalmente consequentes | | | | |
| 3a. Amplitude estrutural das opções | | | | |
| 3b. Precisão dos trade-offs | | | | |
| 4a. C4 Diagram | | | | |
| 4b. ADR | | | | |
| 4c. Decision Matrix | | | | |
| 4d. NFR Checklist | | | | |
| 5a. Skills explicitamente invocadas | | | | |
| 5b. Conhecimento de domínio observável | | | | |
| 5c. Skills não utilizadas com ponto de entrada | | | | |
| 6a. Decisões do usuário vs. internas | | | | |
| 6b. Rastreabilidade fim-a-fim | | | | |
| **Total** | **/90** | **/90** | **/90** | **/90** |

## Análise por Variante

Para cada variante:

### v[N] — [nome]

**Sessão:** [real / projetada — se projetada, indicar impacto no score]

**O que esta versão fez melhor que as anteriores:** [mecanismo específico, não descrição genérica]

**O que ficou abaixo do potencial:** [com citação do arquivo que evidencia a lacuna]

**Decisões tomadas internamente sem surfacing ao usuário:** [lista com arquivo e trecho]

**Trechos com conhecimento de domínio rastreável a skills:** [tabela: trecho | arquivo | skill de origem]

## Diferenças Mais Significativas

Top 3–5 diferenças qualitativas entre as variantes, ordenadas por impacto arquitetural. Para cada uma:

- **Nome da diferença**
- Versões afetadas
- Citação da versão mais fraca (o que falta ou o que está errado)
- Citação da versão mais forte (o que está certo)
- Impacto: que decisão arquitetural seria diferente se a versão mais fraca fosse a única disponível?

## Lacunas Transversais

Identifique problemas que aparecem em todas as versões avaliadas — não são regressões de uma versão específica, mas limitações do design atual do plugin. Para cada lacuna:

- Descrição do problema
- Evidência em qual(is) versão(ões) aparece
- Sugestão de mecanismo para endereçar em versão futura

## Recomendação

**Qual variante produziu o melhor resultado geral e por quê** — com referência ao score total e às dimensões onde a diferença foi mais significativa.

**Elementos a preservar em versões futuras:** tabela com elemento | versão de origem | justificativa (o que seria perdido se removido).

**Elementos a remover ou substituir:** o que foi testado e não produziu diferença mensurável, com evidência.

---

Se alguma pasta estiver incompleta ou ausente, liste quais sessões precisam ser executadas antes de prosseguir. Indique especificamente quais dimensões da rubrica não podem ser avaliadas sem os arquivos faltantes.

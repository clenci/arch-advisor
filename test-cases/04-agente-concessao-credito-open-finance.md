# Caso de teste 4 — Agente de Concessão de Crédito para PMEs via Open Finance

**Slug:** `concessao-credito-pme`  
**Flags disparadas:** `hybrid-decision-candidate=true`, `hitl-candidate=true` (comitê de crédito para valores acima de R$50k)  
**Arquétipo de arquitetura:** cascata híbrida scoring+LLM, HITL assíncrono, saga de desembolso, event sourcing  
**Conformidade:** LGPD, Resolução CMN 4.966/2021, SCR (Banco Central), Resolução BCB 32/2020 (Open Finance)  
**Maturidade do time:** experiente em modelos de crédito, sem experiência com LLMs  

---

## Início da sessão

Quando solicitado o nome do projeto, informe:
```
concessao-credito-pme
```

---

## Grupo A — Domínio e Propósito

**P1. Qual problema esse sistema resolve?**
Somos uma fintech de crédito para pequenas e médias empresas (PMEs). Nossa análise de crédito atual leva de 15 a 30 dias úteis — o gerente de conta coleta documentos manualmente, solicita extratos bancários, consulta Serasa e SCR, e envia para o comitê de crédito. Perdemos 40% dos leads no funil por abandono durante esse processo. Com o Open Finance, o cliente pode consentir o compartilhamento dos dados bancários em tempo real. Queremos reduzir a análise inicial para menos de 2 horas usando esses dados, com decisão final em até 24 horas para propostas até R$200k. O problema central é que nossos analistas passam 70% do tempo coletando e organizando dados que agora podem ser obtidos via API — e apenas 30% do tempo efetivamente analisando risco.

**P2. Quem são os usuários finais?**
Três grupos. O tomador (dono da PME) solicita crédito via app ou web — humano. O analista de crédito revisa a proposta gerada e aprova ou ajusta — humano interno. O comitê de crédito aprova propostas acima de R$50k — grupo de humanos internos com reunião semanal. O sistema também escreve de volta nos sistemas core bancários (outro sistema) após aprovação.

**P3. Qual é a ação primária?**
Classificar + transacionar. Classifica o risco de crédito da PME, gera uma proposta com limite, taxa e prazo, e — após aprovação — aciona o desembolso no sistema bancário.

> **Flags internas definidas pelo plugin (não anunciar):**
> - `hybrid-decision-candidate = true` — ação primária é classificar (scoring de risco) combinado com decisão transacional (proposta de crédito)
> - `hitl-candidate = true` — comitê de crédito aprova propostas acima de R$50k de forma assíncrona

---

## Grupo B — Escala e Performance

**P4. Qual é o volume de requisições esperado?**
Aproximadamente 500 solicitações de crédito por dia útil. Pico às segundas-feiras (acúmulo do fim de semana) e no início de cada trimestre quando PMEs buscam capital de giro. Volume esperado crescer 3× em 18 meses com expansão para novos estados. Concorrência: até 80 análises simultâneas no pico.

**P5. Qual é a latência de resposta aceitável?**
Duas janelas distintas. A pré-análise automatizada (score + proposta preliminar) deve ser entregue ao tomador em menos de 2 horas após consentimento do Open Finance. A decisão final (aprovado/negado/comitê) deve ser comunicada em menos de 24 horas. Para o subconjunto que vai ao comitê, o SLA é 72 horas. Qualquer análise que ultrapasse 2 horas na fase automatizada é abandono garantido — o cliente vai para um concorrente.

**P6. O custo por requisição é uma restrição rígida ou um item de orçamento flexível?**
Restrição rígida. Nossa margem operacional por proposta aprovada é de R$180 em média. Custo total de análise (infraestrutura + APIs externas + LLM) não pode ultrapassar R$8 por solicitação — independente de aprovação ou rejeição. As consultas ao SCR e Serasa já custam R$2,50 por solicitação. O LLM + infraestrutura deve caber em R$5,50.

**Follow-up obrigatório do Grupo B — padrão de chegada:**
> Plugin pergunta: "O volume de requisições é constante ao longo do dia ou apresenta picos em resposta a eventos upstream?"

Irregular com sazonalidade clara. Picos no início do mês (pagamento de fornecedores e folha), no início de cada trimestre e em novembro/dezembro (capital de giro para o Natal). Aos domingos à noite há um pico consistente de solicitações iniciadas pelo app — donos de PME planejando a semana. As consultas ao SCR têm janela restrita: o Banco Central limita consultas entre 6h e 22h, o que significa que solicitações recebidas à noite ficam em fila para processamento na manhã seguinte.

---

## Grupo C — Dados e Integrações

**P7. Quais fontes de dados o sistema precisa acessar?**
Dados do Open Finance (com consentimento do tomador): extratos bancários dos últimos 12 meses, dados de recebíveis, informações de outros produtos financeiros. SCR — Sistema de Informações de Crédito do Banco Central: histórico de operações de crédito, inadimplência, endividamento total — consulta obrigatória por regulação. Serasa Experian: score PJ, protestos, ações judiciais, participação societária dos sócios. Receita Federal (via API pública): situação cadastral do CNPJ, quadro societário, regime tributário, faturamento declarado (Simples Nacional). Dados internos: histórico de relacionamento com a fintech, se houver.

**P8. Existem sistemas que precisam ser integrados?**
Open Finance Brasil (ecossistema regulado pelo Banco Central): APIs padronizadas, autenticação OAuth 2.0 com consentimento granular, certificados ICP-Brasil obrigatórios. SCR do Banco Central: API com autenticação específica, latência variável (2–15s), janela operacional 6h–22h. Serasa API: REST, SLA de 3s, contrato com cota de consultas mensais. Sistema core bancário interno (legado em COBOL/IBM): integração via ESB para acionar o desembolso após aprovação — interface com mensageria assíncrona, não há API REST. O core bancário é o sistema mais crítico e o mais frágil — qualquer falha no desembolso precisa de saga de compensação.

**P9. Qual é o nível de sensibilidade dos dados?**
LGPD grau máximo. CPF e CNPJ são dados pessoais sob a LGPD. Dados financeiros do Open Finance são dados sensíveis por natureza — o consentimento é granular e temporário (máximo 12 meses, revogável a qualquer momento). Dados do SCR são sigilosos por lei complementar (LC 105/2001) — não podem ser compartilhados com terceiros nem armazenados além do necessário para a decisão. O LLM não pode receber CPF, CNPJ ou dados bancários brutos — tokenização obrigatória antes de qualquer chamada de modelo.

**Follow-up prioritário do Grupo C — HITL (hitl-candidate=true):**
> Plugin pergunta: "A decisão de crédito vai diretamente para o sistema downstream ou um humano precisa aprovar primeiro?"

Dois caminhos distintos. Propostas até R$50k: decisão totalmente automatizada, sem revisão humana — o sistema aprova ou nega com base no score e nas regras. Propostas de R$50k a R$200k: analista de crédito revisa a proposta gerada em até 4 horas (SLA interno) e aprova, ajusta ou nega. Propostas acima de R$200k: comitê de crédito — reunião semanal às terças-feiras, decisão em até 72 horas. Em todos os casos, o desembolso só ocorre após aprovação humana para propostas acima de R$50k.

---

## Grupo D — Restrições e Time

**P10. Existem restrições tecnológicas?**
Python + FastAPI para os microsserviços de análise. Cloud: AWS região São Paulo (sa-east-1) — obrigatório por LGPD e requisito contratual com o Banco Central para dados do Open Finance. LLM: não podemos usar APIs públicas de LLM (OpenAI, Anthropic diretamente) porque dados financeiros tokenizados ainda são considerados sensíveis pelo nosso jurídico — precisamos de AWS Bedrock com contrato de processamento de dados (DPA) na região Brasil. Banco de dados: PostgreSQL no RDS. O sistema de scoring atual é um modelo XGBoost em Python, implantado via SageMaker. A integração com o core bancário legado passa obrigatoriamente pelo ESB corporativo — não há alternativa.

**P11. Qual é a familiaridade do time com sistemas LLM/agente?**
Experiente em modelos de crédito, zero experiência com LLMs. O time de risco de crédito tem 8 anos de experiência com modelos preditivos — scorecard, XGBoost, séries temporais para detecção de sazonalidade de faturamento. Têm MLOps maduro, feature store e processo de validação de modelos conforme Resolução CMN 4.966. Nunca usaram LLMs, embeddings ou padrões de agente. Entendem profundamente o negócio de crédito e a regulação, mas precisam de suporte técnico para a camada de LLM.

**P12. Existem requisitos de conformidade ou auditoria?**
Múltiplas camadas regulatórias. LGPD: base legal para tratamento de dados financeiros é execução de contrato + legítimo interesse — deve ser explicitada no consentimento. Resolução CMN 4.966/2021: modelos de crédito devem ser documentados, validados e auditáveis — a metodologia de scoring precisa ser explicável para o Banco Central. SCR: toda consulta deve ser registrada com finalidade, data e resultado — log imutável por 5 anos. Open Finance BCB 32/2020: consentimento granular, rastreabilidade de acesso por dado consultado, revogação deve ser honrada em até 2 horas. Resolução BCB 96/2021 (Open Finance operacional): certificados ICP-Brasil obrigatórios para chamadas às APIs. Toda decisão de crédito deve registrar: dados utilizados, versão do modelo, score gerado, decisão, analista se houver revisão, e resultado final (adimplência/inadimplência) para backtesting regulatório.

**Follow-up prioritário do Grupo D — Hybrid DE (hybrid-decision-candidate=true):**
> Plugin pergunta: "Que fração são casos 'óbvios' versus casos que realmente exigem raciocínio do LLM?"

Aproximadamente 35% das solicitações têm perfil claramente aprovável: CNPJ ativo há mais de 3 anos, score Serasa acima de 700, SCR sem restrições, faturamento Open Finance consistente — o XGBoost aprova automaticamente com alta confiança. Outros 25% são claramente negáveis: SCR com operações em atraso, score abaixo de 400, CNPJ com menos de 1 ano. Os 40% restantes são a zona cinza: empresas jovens com bom faturamento mas sem histórico de crédito formal, sazonalidade extrema no extrato (negócio sazonal como turismo ou agro), sócios com restrição pessoal mas empresa saneada. É exatamente essa zona cinza que nossos melhores analistas conseguem aprovar com contexto narrativo que o XGBoost não captura — e é onde perdemos mais para concorrentes que têm analistas experientes disponíveis.

---

## Grupo E — Falhas, Histórico e Prioridades

**P13. Isso já foi tentado antes?**
Duas tentativas anteriores. Primeira: automação parcial com RPA — coletava documentos automaticamente mas a análise ainda era manual. Reduziu de 30 para 15 dias, insuficiente. Segunda: scoring puro com XGBoost implantado há 2 anos — funciona bem para os extremos mas tem taxa de rejeição de 65% na zona cinza (muita rejeição que analistas experientes aprovariam). O Open Finance é o habilitador novo — antes não conseguíamos dados bancários em tempo real com consentimento estruturado.

**P14. Qual é a consequência de um output incorreto?**
Dois modos de falha com custos distintos. Aprovação indevida (falso negativo de risco): inadimplência. Nosso ticket médio aprovado é R$45k — uma inadimplência consome a margem de 250 operações saudáveis. Além do financeiro: inadimplência acima de 8% do portfólio ativa cláusula de covenant com nosso funding e pode suspender nossa capacidade de captação. Rejeição indevida (falso positivo de risco): perda de receita + dano reputacional. Uma PME rejeitada injustamente que consegue crédito em outro lugar e honra o pagamento representa R$2.400 de receita perdida em média. Se o padrão for sistemático, afeta o NPS e o CAC. Regulatório: uma decisão automatizada de crédito que não possa ser explicada ao Banco Central é uma infração à CMN 4.966 — multa e possível suspensão da licença.

**P15. Se você tivesse que cortar um requisito para entregar quatro semanas antes, qual cortaria?**
A geração de narrativa explicativa da proposta para o analista. O score + proposta preliminar (limite, taxa, prazo) são suficientes para o analista decidir. A narrativa em linguagem natural ("empresa apresenta sazonalidade de dezembro com pico 4× a média — risco concentrado no Q4") é valiosa mas não é o caminho crítico. Cortamos a camada de linguagem natural do LLM e entregamos só o scorecard estruturado. A LLM pode ser adicionada em v1.1.

**P16. Quem fora do time decide se isso está funcionando? O que medirão?**
Dois stakeholders. O Diretor de Risco mede: taxa de inadimplência do portfólio aprovado pela automação vs. aprovado por analistas (deve ser ≤ a taxa humana em 6 meses), taxa de aprovação na zona cinza (meta: aumentar de 35% para 55% sem piorar inadimplência). O Diretor Comercial mede: tempo médio de resposta (meta: <2h para pré-análise), taxa de conversão do funil (meta: reduzir abandono de 40% para menos de 15%). Ambos revisam mensalmente. O Banco Central pode solicitar auditoria a qualquer momento — o modelo precisa ser explicável em até 5 dias úteis após notificação.

**P17. Existem operações multi-etapas que exigem rollback?**
Sim, e são críticas. O desembolso envolve: aprovação final → reserva de limite no core bancário → geração de contrato digital → assinatura eletrônica pelo tomador → liberação do crédito na conta. Se a assinatura falhar ou o core bancário rejeitar a reserva, precisamos cancelar as etapas anteriores — a reserva de limite não pode ficar bloqueada. É uma saga: cada passo tem compensação definida. O caso mais crítico: contrato gerado e assinado, mas o core bancário rejeita a liberação (fora do ar, limite operacional diário atingido). O contrato assinado é um instrumento jurídico — não pode ser simplesmente descartado. Precisamos de um processo de reprocessamento com janela de 48h antes de invalidar o contrato e notificar o cliente.

**P18. Existe requisito de reconstruir o estado passado exatamente?**
Sim, por múltiplas regulações. SCR exige que toda consulta seja rastreável com data, hora, finalidade e resultado — 5 anos de retenção. CMN 4.966 exige que a decisão de crédito seja reproduzível: mesmos dados de entrada + mesma versão do modelo = mesmo score. Isso significa versionamento imutável do modelo e snapshot dos dados usados na decisão (não apenas o score final). LGPD exige que o titular possa solicitar explicação da decisão automatizada a qualquer momento — precisamos reconstruir "por que foi negado" até 5 anos depois. Event sourcing é obrigatório: log imutável de cada etapa da análise, com os dados utilizados (tokenizados), versão do modelo, score intermediário, decisão e eventual override humano.

---

## Fase 1.5 — Tensões esperadas e como responder

### Tensão: Enriquecimento de dados via Open Finance vs. granularidade do consentimento LGPD

> Conflito: Para a análise ser precisa, o sistema precisa acessar 12 meses de extratos e dados de recebíveis. Mas o consentimento do Open Finance é granular — o tomador pode consentir apenas parte dos dados (ex: só extrato, sem recebíveis). Uma análise com dados parciais pode resultar em proposta pior para o cliente ou rejeição que seria aprovação com dados completos.

*Se resolvido em favor da análise completa (exigir consentimento total):* Taxa de conversão cai — parte dos tomadores recusa compartilhar todos os dados. Análise mais precisa para quem consente. Risco: cliente que consente parcialmente fica sem análise.

*Se resolvido em favor da flexibilidade (aceitar consentimento parcial):* Análise com dados incompletos pode gerar score menos preciso. Precisamos de lógica de fallback: "dados insuficientes para análise automatizada → encaminhar para analista". Aumenta volume de trabalho manual para casos com consentimento parcial.

**Resposta:** Aceitar consentimento parcial com degradação explícita. Se o tomador consentiu apenas extrato (sem recebíveis), a análise automatizada usa apenas os dados disponíveis e o sistema informa ao tomador que mais dados resultariam em proposta potencialmente melhor. Casos com menos de 6 meses de extrato disponível vão automaticamente para revisão de analista — não há score confiável com menos dados. Isso é comunicado claramente na tela de consentimento.

---

### Tensão: LLM para análise narrativa vs. explicabilidade regulatória (CMN 4.966)

> Conflito: O LLM consegue interpretar padrões narrativos no extrato (sazonalidade, comportamento de recebíveis, concentração de clientes) que o XGBoost não captura. Mas a CMN 4.966 exige que a metodologia de scoring seja documentada e explicável. LLMs são caixas-pretas — "o modelo interpretou o extrato como indicador de risco" não é uma explicação regulatória aceitável.

*Se resolvido em favor da explicabilidade (sem LLM na decisão):* Manter apenas XGBoost com features explícitas. Perder a capacidade de análise narrativa da zona cinza. Taxa de aprovação na zona cinza não melhora.

*Se resolvido em favor da capacidade (LLM na decisão):* O LLM precisa produzir outputs estruturados e auditáveis — não um score, mas uma lista de sinais identificados (ex: `SAZONALIDADE_ALTA`, `CONCENTRACAO_CLIENTE_UNICO`, `CRESCIMENTO_RECEITA_CONSISTENTE`) com texto explicativo por sinal. O XGBoost continua sendo o modelo oficial de score — o LLM é um enriquecedor de features, não um tomador de decisão.

**Resposta:** LLM como enriquecedor, XGBoost como decisor. O LLM analisa o extrato e produz tags estruturadas de uma taxonomia predefinida + uma frase de justificativa por tag. Essas tags entram como features adicionais no XGBoost — o modelo oficial continua sendo o XGBoost, que é explicável. O Banco Central audita o XGBoost; o LLM é documentado como pré-processamento de features, não como modelo de decisão. Essa distinção é regulatória e precisa ser validada com o jurídico antes do lançamento.

---

### Tensão: Consulta ao SCR em tempo real vs. janela operacional restrita

> Conflito: O SCR só opera das 6h às 22h. Solicitações recebidas fora dessa janela — especialmente o pico de domingo à noite — não podem ser processadas imediatamente. Segurar a análise até a consulta SCR disponível significa que o SLA de 2 horas pode não ser cumprido para solicitações noturnas.

*Se resolvido em favor do SLA (processar sem SCR):* Iniciar a análise com Open Finance + Serasa disponíveis imediatamente. Finalizar com SCR quando disponível. Comunicar ao tomador que a pré-análise está em andamento mas a decisão final aguarda consulta ao SCR. Risco regulatório: aprovar sem consultar SCR é vedado pela regulação de crédito.

*Se resolvido em favor da conformidade (aguardar SCR):* Solicitações noturnas ficam em fila. SLA de 2 horas é contado a partir da primeira consulta SCR disponível, não do recebimento da solicitação. Comunicar ao tomador no momento da solicitação que análises iniciadas após as 20h terão resultado na manhã seguinte.

**Resposta:** Fila com comunicação proativa. Solicitações recebidas após as 20h são aceitas, o consentimento Open Finance é processado imediatamente (dados disponíveis), e o tomador recebe confirmação com previsão de análise para o dia seguinte até as 10h. A análise completa (com SCR) inicia às 6h do dia seguinte na ordem da fila. O SLA de 2 horas é contratual e aplica-se a solicitações recebidas entre 6h e 20h — isso precisa estar explícito nos termos de uso.

---

## Fase 1.6 — Respostas ao stress test

**Escala 10× (5.000 solicitações/dia útil):**
Dois gargalos identificados. Primeiro: cota de consultas ao SCR — o Banco Central limita o volume por instituição. Nossa cota atual comporta 800 consultas/dia; a 5.000 solicitações/dia precisaríamos renegociar a cota ou implementar cache de consultas (SCR permite reutilizar consulta recente se dentro de 24h e mesma finalidade). Segundo: fila de revisão de analistas — com 40% de zona cinza e 30% indo para analista, seriam 600 revisões/analista/dia — inviável. A 10× seria necessário um time de crédito 5× maior ou elevar o threshold de aprovação automatizada, aceitando mais risco.

**Pressão de budget (−50%):**
Remover o LLM completamente. Voltar ao XGBoost puro com feature engineering adicional no extrato Open Finance — faturamento médio, volatilidade mensal, concentração de recebíveis. Aceitar que a zona cinza continua com taxa de aprovação de 35% em vez de 55%. Redirecionar orçamento para mais analistas de crédito para cobrir os casos que a automação não resolve. O retorno do LLM fica para quando o volume justificar.

**Requisitos futuros:**
- Crédito com garantia de recebíveis (antecipação de CNPJ): confirmado para Q2. Muda a estrutura da garantia e adiciona integração com registradoras (CERC, CIP) — extensão de arquitetura, não mudança de base. Ponto de extensão necessário agora: campo de garantia na proposta e integração prevista com registradoras.
- Produto PJ para MEI: possível, não comprometido. MEI tem limite de faturamento de R$81k/ano — ticket médio diferente, modelo de risco diferente. Tratar como produto separado se vier; não contaminar o modelo atual com MEI.

---

## Fase 1.7 — Respostas às meta-perguntas

**P1. Há algo no resumo que parece errado ou incompleto?**
O risco de revogação de consentimento no meio da análise não foi capturado. O Open Finance permite que o tomador revogue o consentimento a qualquer momento, com efeito em até 2 horas. Se o consentimento for revogado enquanto a análise está em andamento, o sistema precisa parar de usar os dados e invalidar qualquer resultado parcial — mesmo que o score já tenha sido calculado, ele não pode ser usado como base para decisão se o dado foi revogado. Isso é uma restrição operacional que afeta toda a arquitetura de pipeline: cada etapa de análise precisa verificar validade do consentimento antes de processar.

**P2. Qual é a única coisa não capturada que mais afetará a arquitetura?**
O backtesting regulatório. A CMN 4.966 exige que o modelo de crédito seja periodicamente revalidado contra o resultado real das operações (adimplência/inadimplência). Isso significa que, para cada operação aprovada, o sistema precisa rastrear o outcome final e alimentar um pipeline de revalidação do modelo. Se esse pipeline não for construído desde o início — com o resultado real linkado à decisão original, versão do modelo e features usadas — a revalidação regulatória vai exigir uma reconstrução arqueológica de dados. É o requisito com maior custo de negligência e está completamente ausente nos requisitos levantados.

---

## Fase 2 — Ambiguidades esperadas e como responder

### A1 — Como tratar a análise de empresas com mais de um sócio?

*Plugin pergunta: Quando a PME tem múltiplos sócios, a análise de CPF e SCR individual de cada sócio é obrigatória ou apenas do sócio majoritário?*

> Obrigatória para sócios com participação acima de 25%, conforme política interna de crédito alinhada com COAF. O consentimento do Open Finance é do CNPJ (pessoa jurídica) — as consultas de CPF dos sócios são separadas, exigem consentimento individual de cada sócio envolvido, e precisam ser solicitadas como etapas distintas do fluxo de consentimento. Isso significa que uma PME com 3 sócios elegíveis pode ter um fluxo de consentimento com 4 telas (1 CNPJ + 3 CPFs). O modelo de score final agrega os perfis individuais — sócio com restrição pessoal grave reduz o score da empresa mesmo com CNPJ saneado.

### A2 — O que fazer quando os dados Open Finance contradizem o declarado na Receita Federal?

*Plugin pergunta: Se o faturamento no extrato Open Finance for significativamente diferente do declarado no Simples Nacional (Receita Federal), qual dado prevalece na análise?*

> O extrato Open Finance prevalece para a análise de capacidade de pagamento — é o dado real, não o fiscal. A divergência em si é um sinal de risco: se o faturamento bancário for muito abaixo do declarado na Receita, pode indicar problemas fiscais futuros; se for muito acima, pode indicar subfaturamento fiscal com risco de autuação. Divergências acima de 30% geram automaticamente um sinal de alerta no relatório de análise para o analista. Não é causa automática de rejeição — é contexto que o analista precisa avaliar.

### A3 — Como tratar o fallback quando o core bancário legado está indisponível para o desembolso?

*Plugin pergunta: Se o core bancário estiver fora do ar no momento do desembolso, o contrato assinado fica em fila por quanto tempo antes de ser invalidado?*

> 48 horas de reprocessamento automático com tentativas a cada 30 minutos. Se após 48 horas o desembolso não foi concluído, o sistema notifica o time de operações e congela o contrato — não invalida automaticamente, pois o contrato assinado tem validade jurídica. O time de operações tem mais 24 horas para resolver manualmente ou acionar o suporte do fornecedor do core. Após 72 horas sem desembolso, o jurídico é acionado para avaliar se o contrato precisa ser re-assinado ou se há cláusula de vigência que permite desembolso tardio. Todo esse fluxo de saga precisa ser auditável via event log — cada tentativa de desembolso, falha e decisão de escalonamento registradas com timestamp.

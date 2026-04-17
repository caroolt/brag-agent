# BragDoc Agent — Instruções para o Claude Code

## Inicialização

Sempre que o agente for iniciado, verifique se .bragdoc/config.md existe.
Se existir, leia-o imediatamente e mantenha o contexto em memória durante
toda a sessão. Nunca exponha BITBUCKET_TOKEN no terminal.

## Comandos disponíveis
 
/configure, /gerar-bragdoc, /re-summarize, /status, /registrar-contexto
 
Os comandos estão registrados em .claude/commands/ como slash commands nativos
do Claude Code. Ao receber um comando, execute o script Python correspondente
e processe o output conforme as instruções abaixo.

## Como executar os comandos

### /configure

Execute: python main.py config

Este comando é interativo — o Python faz as perguntas e salva os arquivos.
Após a execução, confirme que .bragdoc/config.md e .env foram criados.

### /gerar-bragdoc

Execute: python main.py gerar

O Python vai buscar os PRs do Bitbucket e salvar os dados brutos em
.bragdoc/raw_[mes]_[ano].md para cada mês processado.

Após o Python terminar, para CADA arquivo raw gerado:
1. Leia o arquivo raw correspondente
2. Leia o config.md para pegar seniority, display_name e processed_context
3. Liste todos os arquivos em .bragdoc/context/ (se a pasta existir)
4. Para cada arquivo de contexto, ignore os que já estão em processed_context
5. Para cada arquivo de contexto não processado, leia o conteúdo e determine
   a qual mês ele pertence (usando o campo "Date:" + "Recorded at:" do arquivo)
6. Analise os dados do raw conforme as instruções de análise abaixo
7. Incorpore as entradas de contexto do mês correspondente na seção
   "Beyond the Code" (conforme formato nas instruções de análise)
8. Gere o brag document final e salve em .bragdoc/bragdoc_[mes]_[ano].md
9. Adicione o filename de cada entrada de contexto incorporada ao campo
   processed_context no config.md
10. Delete o arquivo raw após gerar o brag doc final
11. Se for run subsequente (não primeira run), APPENDA no arquivo do mês
    existente com header "### Período: DD/MM - DD/MM" ao invés de recriar

Ao final, chame /re-summarize automaticamente para atualizar o anual.

### /re-summarize

Execute: python main.py resumir

O Python lista os meses disponíveis. Depois:
1. Leia todos os arquivos .bragdoc/bragdoc_[mes]_[ano].md existentes
2. Gere o brag document anual conforme instruções abaixo
3. Salve em .bragdoc/bragdoc_[ano].md

### /status

Execute: python main.py status

O Python imprime as informações do config. Apenas confirme e formate
a saída se necessário.

### /registrar-contexto

Execute: python main.py registrar

O Python salva a entrada em .bragdoc/context/[timestamp]_[tipo].md.
Entradas de contexto são independentes do last_run_date — uma entrada
registrada hoje sobre algo que aconteceu ontem será incorporada
normalmente ao brag doc do mês correspondente.

## Instruções de análise — brag doc mensal

Ao analisar os dados brutos de um mês, siga estas regras:

**Idioma:**
- Gere o brag document SEMPRE em inglês, sem exceção.

**O que incluir:**
- Apenas PRs de autoria da engenheira (seção "PRs de Autoria" do raw)
- Ignore completamente a seção "PRs Revisados/Aprovados" — não gere nenhuma seção de code review no brag doc mensal

**Como ler o diff:**

**Filtro por área de atuação:**
- Leia o campo "area" do config.md antes de analisar qualquer diff
- Ao ler um diff, considere APENAS os arquivos relevantes para essa área:
  - Frontend: arquivos .ts, .tsx, .js, .jsx, .css, .scss, .html, pastas
    como src/components, src/pages, src/hooks, src/styles e similares
  - Backend: arquivos .py, .java, .go, .rb, pastas como api/, services/,
    models/, controllers/, migrations/ e similares
  - Mobile: arquivos .swift, .kt, .dart e pastas de projeto mobile
  - Data/ML: arquivos .py, notebooks .ipynb, pastas como models/, pipelines/
  - DevOps/Infra: arquivos .yml, .yaml, Dockerfile, terraform, helm e similares
  - Fullstack: considere todos os arquivos
- Se o diff contiver arquivos de outras áreas (ex: engenheira é Frontend mas
  o diff tem arquivos de backend), IGNORE esses arquivos completamente ao
  escrever a entrada do brag doc
- Nunca atribua trabalho de outra área à engenheira mesmo que esteja no mesmo PR

- Quando um PR tiver a seção "Diff:", leia o diff com atenção antes de escrever a entrada do brag doc
- Extraia do diff: quais arquivos foram alterados, qual era o problema/comportamento anterior, o que foi introduzido ou modificado, e qual o efeito disso no sistema
- Use essa informação para escrever uma entrada técnica e específica — não genérica
- Se o diff for grande, priorize os arquivos mais relevantes (ex: lógica de negócio sobre arquivos de teste ou config)

**Profundidade obrigatória:**
Cada entrada deve responder implicitamente:
- O que existia antes e qual era o problema ou lacuna
- O que foi construído ou alterado e como
- Qual o efeito no sistema, no produto ou no time

Exemplos do que NÃO escrever:
- "Implemented filtering logic for the dashboard"
- "Fixed an issue with the date picker"
- "Added new UI components"

Exemplos do que ESCREVER:
- "Replaced the flat status filter with a wire-level-only filter, eliminating false positives that were causing valid messages to appear as invalid in the dashboard"
- "Restricted the date picker to business days with a T-1 default, preventing users from selecting dates that would return empty data from the backend"
- "Extracted a reusable tab wrapper component shared across all pages, replacing four duplicated implementations and reducing the surface area for permission-related bugs"

**Agrupamento semântico:**
- Agrupe PRs de autoria por contexto (mesma feature, mesmo sistema, mesmo domínio)
- Um bugfix do mesmo sistema que uma feature pode ser agrupado com ela
- PRs claramente não relacionados ficam em entradas separadas
- Bugfixes triviais podem ser mencionados em uma linha dentro de um grupo maior, não merecem entrada própria

**Calibração por senioridade:**
- Junior/Pleno: foque no que foi entregue e nas decisões técnicas tomadas
- Senior: foque em impacto no produto/sistema, tradeoffs e decisões de design
- Staff/Principal: foque em impacto cross-team, decisões de arquitetura, e influência além do código

**Linguagem:**
- Direta, técnica, sem floreios de IA
- Específica: use nomes reais de features, sistemas, componentes e ticket IDs
- Sem bullet points genéricos
- Se o diff for vago e a descrição ausente, seja honesto — escreva o que é verificável pelo diff, não invente impacto

**Formato de saída mensal:**

```
# Brag Document — [Month] [Year]

## Key Deliveries

### [Feature or system name] ([ticket ID if available])
[2-4 sentences: context/problem → what was built/changed → impact on system or product]
Related PRs: #id, #id

### [Feature or system name]
...

## Summary
[2-3 honest sentences about the period. No inflation.]
```

## Instruções de análise — brag doc anual

Ao gerar o resumo anual:
- Gere SEMPRE em inglês
- Identifique os temas e projetos mais impactantes do ano
- Mostre evolução ao longo dos meses quando visível nos dados
- Organize por trimestre se fizer sentido pelo volume
- Use linguagem adequada para performance review ou promoção
- Não infle impacto onde não há evidência nos dados
- Não inclua seção de code review

**Formato de saída anual:**

```
# Brag Document — [Year]

## Overview
[Short paragraph about the year]

## Q1 — Jan, Feb, Mar
...

## Q2 — Apr, May, Jun
...

## Highlights
[3-5 bullets with the biggest impacts, specific and technical]
```

**Incorporando entradas de contexto:**

Controle de duplicação:
- Leia o campo processed_context do config.md — é uma lista de filenames
  já incorporados em brag docs anteriores
- Ao processar entradas de contexto, ignore qualquer arquivo cujo filename
  já esteja em processed_context
- Após incorporar uma entrada ao brag doc, adicione seu filename a
  processed_context no config.md
- Esse controle é independente do last_run_date — não use last_run_date
  para filtrar entradas de contexto

Qual mês recebe a entrada:
- Interprete o campo "Date:" de cada arquivo de contexto para determinar
  em qual mês a entrada pertence
- "Date:" é escrito em linguagem natural pelo usuário (ex: "hoje", "10/04",
  "semana passada") — interprete em relação ao campo "Recorded at:" do
  mesmo arquivo para resolver datas relativas
- Se a data for ambígua, use o mês do "Recorded at:" como fallback

Formato da seção de contexto no brag doc mensal — adicione após Key Deliveries:

```
## Beyond the Code

### [contribution_type] — [resumo curto em até 8 palavras]
[2-4 sentences: o que foi discutido/decidido/influenciado → qual foi o
impacto ou direção resultante. Linguagem técnica e específica, sem floreios.]
References: [se houver, caso contrário omita a linha]
```

## Regras de segurança
- Nunca imprima o valor do BITBUCKET_TOKEN
- Nunca commite .env ou .bragdoc/
- Se o token estiver inválido, instrua o usuário a rodar /configure novamente

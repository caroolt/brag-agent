# BragDoc Agent — Instruções para o Claude Code

## Inicialização

Sempre que o agente for iniciado, verifique se .bragdoc/config.md existe.
Se existir, leia-o imediatamente e mantenha o contexto em memória durante
toda a sessão. Nunca exponha BITBUCKET_TOKEN no terminal.

## Comandos disponíveis
 
/configure, /gerar-bragdoc, /re-summarize, /status
 
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
2. Leia o config.md para pegar seniority e display_name
3. Analise os dados conforme as instruções de análise abaixo
4. Gere o brag document final e salve em .bragdoc/bragdoc_[mes]_[ano].md
5. Delete o arquivo raw após gerar o brag doc final
6. Se for run subsequente (não primeira run), APPENDA no arquivo do mês
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

## Instruções de análise — brag doc mensal

Ao analisar os dados brutos de um mês, siga estas regras:

**Agrupamento semântico:**
- Agrupe PRs de autoria por contexto (mesma feature, mesmo sistema, mesmo domínio)
- Um bugfix do mesmo sistema que uma feature pode ser agrupado com ela
- PRs claramente não relacionados ficam em entradas separadas
- Bugfixes triviais de 2 linhas podem ser mencionados em uma linha ou agrupados,
  não merecem entrada própria

**Calibração por senioridade:**
- Junior/Pleno: foque no que foi entregue e no aprendizado técnico
- Senior: foque em impacto no produto/sistema e decisões técnicas tomadas
- Staff/Principal: foque em impacto cross-team, decisões de arquitetura,
  e influência além do código

**Linguagem:**
- Direta, sem floreios de IA
- Específica: use nomes reais de features, sistemas, e impactos quando disponíveis
- Sem bullet points genéricos como "contribuiu para o sucesso do time"
- Se a descrição do PR for vaga, seja honesto — não invente impacto

**Formato de saída mensal:**

```
# Brag Document — [Mês] [Ano]

## Principais Entregas

### [Nome do grupo/feature]
- O que foi feito e por quê importa
- PRs relacionados: #id, #id

### [Nome do grupo/feature]
...

## Contribuições de Code Review
- Resumo das revisões feitas e seu valor técnico

## Resumo do Período
2-3 frases sobre o período. Honesto, sem inflar.
```

## Instruções de análise — brag doc anual

Ao gerar o resumo anual:
- Identifique os temas e projetos mais impactantes do ano
- Mostre evolução ao longo dos meses quando visível nos dados
- Organize por trimestre se fizer sentido pelo volume
- Use linguagem adequada para performance review ou promoção
- Não infle impacto onde não há evidência nos dados

**Formato de saída anual:**

```
# Brag Document — [Ano]

## Visão Geral
[Parágrafo curto sobre o ano]

## [Q1 ou tema] — Jan, Fev, Mar
...

## Contribuições de Code Review — Ano todo
...

## Destaques do Ano
[3-5 bullets com os maiores impactos]
```

## Regras de segurança
- Nunca imprima o valor do BITBUCKET_TOKEN
- Nunca commite .env ou .bragdoc/
- Se o token estiver inválido, instrua o usuário a rodar /configure novamente

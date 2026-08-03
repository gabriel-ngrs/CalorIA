---
data: 2026-08-03
titulo: A main só é tocada no fim da spec, não na posição declarada da D.2
status: ativa
tags: [git, release, deploy, spec-002, fase-d2, ordem-de-execucao]
---

# A main só é tocada no fim da spec, não na posição declarada da D.2

## Contexto

A Fase D.2 promove `dev` para `main`, cria tag anotada e publica release. Na §5 da
spec ela aparece cedo no Track D, dependendo de `A.2`, `B.2` e `D.1`.

Dois fatos removeram os impedimentos que existiam até hoje:

- O portão que a decision da A.1 mantinha sobre a D.2 foi **levantado** em 2026-08-03
  (OQ13), depois de a premissa que o sustentava ser medida e refutada.
- O `LICENSE` está commitado na `dev`, e o GitHub só detecta licença a partir do
  **branch default**, que é `main`. Enquanto a `main` não avançar, `licenseInfo`
  continua `null` e o AC-18 da D.1 não fecha.

Ou seja: a D.2 estava tecnicamente executável, e executá-la fecharia a D.1 de imediato.

## Decisão

**Decisão do owner, 2026-08-03: não tocar na `main` em momento nenhum antes do fim da
spec.** A D.2 sai da posição declarada na §5 e passa a ser a **última operação de
branch** do projeto, depois de os Tracks C, D e E estarem concluídos.

Isso não altera o conteúdo da fase — os passos, o AC-19 e o escopo travado continuam
válidos. Altera **quando** ela roda.

## Justificativa

A `main` é o branch que o mundo vê: é dela que o GitHub deriva a página do repositório,
a licença detectada, o README exibido e o alvo de um eventual `git clone` de terceiro.
Promover cedo publicaria um estado intermediário — Track C com fases em rework, README
ainda não reescrito (D.3), repositório ainda não podado (D.4) e deploy ainda
indeterminado (E.2/E.4).

O trabalho continua todo em `dev`, que é onde o CI roda. Nenhum gate desta spec depende
de `main`, com uma exceção nomeada abaixo.

## Consequências

- **A D.1 não fecha até o fim da spec.** As duas cláusulas acionáveis do AC-18
  (description e topics) estão cumpridas e verificadas; a terceira (licença detectada)
  fica represada por esta decisão, não por falta de trabalho. Isso está registrado no
  `FASE-D.1-licenca-metadados-EXECUCAO.md`, e uma avaliação da D.1 antes da D.2 deve
  manter RESSALVAS por esse item — com causa conhecida e aceita, não por defeito.
- **Três fases declaram `Depende de: D.2` e passam a esperar junto:** D.3 (README como
  peça de portfólio), D.4 (poda do repositório) e E.4 (novo deploy e CD automático).
  A dependência delas é de fato sobre o resultado da promoção, então a ordem
  permanece coerente — só desloca.
- **Nada em B.4 ou C.7 depende disto.** O gate de cobertura roda no job de `push` para
  `dev`, e o `eval.yml` é disparável por `workflow_dispatch --ref dev`. Os dois
  dependem de `git push origin dev`, que é operação sobre `dev` e não sobre `main`.
- A mitigação da **OQ10** (deixar alguns dias entre a purga do histórico da A.2 e a
  reabertura do repositório) fica automaticamente satisfeita: o intervalo até o fim da
  spec é muito maior que os poucos dias pedidos.
- Quando a D.2 finalmente rodar, ela deve ser executada como fase própria por
  `/execute-spec-phase`, com os passos de ação do owner (revisar e mergear o PR,
  configurar proteção de branch, tornar o repositório público) explicitados.

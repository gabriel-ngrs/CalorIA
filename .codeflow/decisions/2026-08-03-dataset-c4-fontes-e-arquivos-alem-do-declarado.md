---
data: 2026-08-03
titulo: Dataset da C.4 — terceira fonte para o que a TACO não cobre, imagens versionadas e testes da C.3 atualizados
status: ativa
tags: [eval, dataset, ground-truth, taco, ibge-pof, spec-002, fase-c4]
spec: 002-vitrine-eval-e-saneamento
fase: C.4
---

# Dataset da C.4: fontes e arquivos além do declarado

## Contexto

A Fase C.4 declarava `Arquivos alterados: backend/evals/dataset/casos.jsonl,
backend/evals/README.md` e nenhum arquivo novo. A OQ2 declarava duas fontes:
**IBGE POF 2011** (medida caseira → gramas) e **TACO 4ª edição** (gramas → kcal e
macros). Executar a fase dentro desse par literal esbarrou em três fatos medidos.

**1. A TACO não cobre parte do que o pipeline mais recebe.** Ela não tem pizza —
e a reprodução oficial do bug 001, que a spec manda preservar como grupo de
invariância de primeira classe, é justamente `pizza calabresa`. A linha de leite
integral (alimento nº 458, p. 57) existe mas vem **sem valores**, com `*` em
todas as colunas. Os dois casos ficariam sem referência auditável.

**2. O estrato `foto` não nasce de tabela.** O schema da C.3 exige `imagem_path`
em todo caso do estrato `foto`, e a Fase B.5 foi reapontada em 2026-08-03 para
depender da C.4 exatamente porque o "delta do estrato de foto" precisa desse
dataset. Sem versionar imagem nenhuma, a C.4 entregaria um estrato vazio e
manteria a B.5 bloqueada — o oposto do que a redependência decidiu.

**3. Quatro testes da C.3 e da C.5 travavam o estado de semente.** Eles afirmam,
em asserção, que **nenhum** caso foi conferido (`assert all(not c.verificada …)`)
e que o estrato `foto` está **vazio** (`assert distribuicao["foto"] == 0`;
`assert relatorio["por_estrato"]["foto"]["n"] == 0`). São gates corretos para a
C.3, cujo escopo travado proibia decidir a fonte; a C.4 é a fase que os
supera. Deixá-los intactos deixaria a suíte vermelha por construção.

## Decisão

**Fonte complementar, com regra fixa de precedência.** Onde a TACO cobre o item,
a composição vem da TACO. Onde não cobre, vem das *Tabelas de Composição
Nutricional dos Alimentos Consumidos no Brasil* (IBGE, POF 2008-2009, 2011) —
publicação irmã da tabela de medidas já adotada pela OQ2, do mesmo instituto,
igualmente independente do projeto e citável por terceiro. Ela entra em **dois**
casos: `composto-pizza-calabresa-2-fatias` (284,72 kcal/100 g, p. 93) e
`simples-leite-integral-1-copo` (60,03 kcal/100 g, p. 78).

A precedência é fixa e declarada porque as duas fontes **discordam onde as duas
cobrem**: feijoada é 117 kcal/100 g na TACO e 181,59 na POF — receitas
diferentes. Escolher caso a caso a fonte mais conveniente moveria a métrica sem
que o pipeline tivesse mudado.

**Três imagens versionadas em `backend/evals/dataset/imagens/`**, do Wikimedia
Commons, licença conferida pela API antes de baixar (domínio público, CC BY 4.0 e
CC BY-SA 4.0), sem pessoa identificável, atribuídas em `notas` e numa tabela do
README do harness. A referência de cada caso de foto é `unidades contadas na
imagem × medida padrão da POF` — a contagem foi conferida olhando cada imagem, e
a massa é a da população, não a do item fotografado.

**Quatro asserções atualizadas** em `tests/unit/test_evals_schema.py` e
`tests/unit/test_evals_metrics.py`, preservando a intenção de cada teste:

| teste | antes | depois |
|---|---|---|
| honestidade sobre verificação | nenhum caso conferido | todo caso conferido |
| distribuição com estrato vazio | usa o dataset real e exige `foto == 0` | usa dataset sintético — segue provando que estrato vazio aparece como zero |
| relatório traz os três estratos | exige `foto n == 0` | exige `n > 0` nos três |
| texto mostra estrato vazio | usa o dataset real | filtra o estrato `foto` — segue exercitando a renderização de estrato vazio |

Nenhum teste foi removido, e os dois que provavam o comportamento com estrato
vazio continuam provando — sobre dado sintético, que é onde esse caso passa a
existir depois que o dataset real cobre os três estratos.

## Alternativas descartadas

- **Ficar só em TACO + POF-medidas e deixar pizza e leite de fora.** Rejeitado:
  tira do dataset o item que ancora a narrativa do bug 001 e um dos alimentos
  mais registrados num diário alimentar. A lacuna não é de método, é de cobertura
  de uma tabela de 597 alimentos publicada em 2011.

- **Usar a tabela `foods` do próprio projeto como referência para o que falta.**
  Rejeitado por circularidade: é a tabela que o `food_lookup` consulta. Medir o
  pipeline contra ela daria erro zero por construção no estrato `simples` — o
  mesmo defeito que o schema da C.3 já barra para a tabela de porções.

- **Rótulo de rede de fast-food para pizza** (a OQ2 admite como fonte
  complementar). Rejeitado por ser menos auditável que uma publicação do IBGE:
  rótulo muda sem aviso, sem página fixa para citar, e descreve uma receita
  comercial específica.

- **Estrato `foto` vazio, com a B.5 seguindo bloqueada.** Rejeitado: a
  redependência da B.5 (2026-08-03) foi decidida para que a C.4 destravasse o
  estrato de foto. Entregar a C.4 sem foto reproduz o bloqueio.

- **Deixar os quatro testes falhando e declarar no relatório.** Rejeitado: o
  Passo 5 exige suíte verde, e um teste que afirma "nenhum caso foi conferido"
  passou a ser uma afirmação falsa sobre o repositório — não um gate.

## Consequência

- O dataset tem **43 casos** (23 `simples`, 17 `composto`, 3 `foto`), todos com
  `verificada: true` e com alimento, página e conta de gramas em `notas`.
- Um caso da semente da C.3 foi **removido**: "lasanha de carne ao forno" a 168
  kcal/100 g não tem fonte externa (a TACO só traz a massa fresca cozida; a POF
  traz "lasanha pronta light", outro produto). Preferiu-se perder o caso a
  manter um número não auditável.
- **Consumo de quota ~4×** na camada agendada do eval: o runner de texto passa de
  10 para 40 casos executáveis. É pressão direta sobre o risco R5 da spec (rate
  limit do free tier) e sobre o dimensionamento da agenda decidido na C.7.
- **Os 14 cassettes gravados na C.7 não cobrem as descrições novas.** Em replay,
  os casos novos levantam `CassetteAusenteError` até a próxima execução com
  `EVAL_RECORD_CASSETTES=1` — que é o comportamento documentado do harness, não
  uma regressão.
- **Risco residual:** a referência é populacional. A medida referida da POF é a
  porção média de quem respondeu à pesquisa, não a porção de quem escreveu a
  frase; a variação de porção entra na métrica como se fosse erro do pipeline. O
  README do harness declara isso, com os casos afetados nomeados.
- **Risco residual, maior no estrato `foto`:** a massa do item fotografado é
  desconhecida e substituída pela medida padrão. Com `n = 3`, o estrato sustenta
  descrição, não comparação — coerente com a análise de poder já escrita na C.3.

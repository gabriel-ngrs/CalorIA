# Harness de avaliação do pipeline de IA

Mede a qualidade nutricional do que o pipeline de IA produz, versionada junto do
código. Existe para dar resposta a uma pergunta que o projeto não conseguia
responder: **como se sabe que uma mudança de prompt melhorou?**

O harness **mede**; não redesenha o pipeline.

## O que ele mede — e o que explicitamente não mede

**Mede:** o erro calórico do pipeline ponta a ponta (identificação pela IA →
normalização de porção → lookup no banco → sanity check → fallback), por estrato
e no agregado, contra referências de fonte externa citável.

**Não mede:**

- **Se a fonte de referência está certa.** O harness mede o pipeline contra a
  fonte declarada em cada caso. Se a TACO erra a composição de um alimento, o
  harness registra o pipeline como errado.
- **Preferência ou utilidade percebida.** Não há juiz de qualidade de texto aqui.
- **Latência e custo como critério de aprovação.** São registrados no histórico
  (`runs/history.jsonl`), não usados como gate.
- **O comportamento com foto.** O estrato `foto` existe desde a C.4, mas o runner
  de texto não o executa — quem mede o caminho de imagem é a fase B.5 (ver
  "Estado do dataset").

Esta seção segue o padrão de honestidade estabelecido por
`backend/scripts/eval_golden_set.py:14-27`, que já declarava o que sua métrica
isolava e o que ela deixava de fora.

## Relação com o que já existia

Este harness **soma**, não substitui:

| Instrumento | Papel | Continua existindo |
|---|---|---|
| `tests/integration/test_golden_set.py` | Gate determinístico com limiares travados (erro médio ≤ 10%, ≥ 80% dentro de ±10%, ≥ 85% de porção ancorada) | Sim, inalterado |
| `scripts/eval_golden_set.py` | Mede porção + lookup isoladamente, sem chamar o modelo | Sim, inalterado |
| `scripts/eval_food_lookup.py` | Varredura de estratégias × limiares do lookup | Sim, inalterado |
| `scripts/instrument_meal_pipeline.py` | Pares equivalentes contra Groq real (origem da bateria de invariância) | Sim; os 7 pares migram para `dataset/grupos_invariancia.jsonl` na fase C.6 |

## Contrato de um caso

`evals/schema.py` define `CasoEval`. Campos obrigatórios: `id`, `estrato`
(`simples` | `composto` | `foto`), `descricao`, `referencia_kcal`,
`fonte_referencia`, `fonte_url`, `data_de_adicao`. Opcionais:
`referencia_macros`, `grupo_invariancia`, `imagem_path` (obrigatório no estrato
`foto`), `verificada`, `notas`.

Duas regras são impostas pelo schema, não por convenção:

1. **`fonte_referencia` não pode derivar da tabela `portions` do projeto.** Seria
   circularidade: a métrica mediria a tabela contra si mesma.
2. **`fonte_url` tem de ser localizável** — URL `http(s)` ou identificador
   `isbn:` para fonte impressa. Um número sem procedência auditável não é ground
   truth.

A identidade do conjunto é `sha_do_dataset()`, calculada sobre o conteúdo
canônico ordenado por `id` — reordenar linhas ou reformatar o JSON não muda o que
foi medido, então não muda o `sha`.

## Estado do dataset

**Populado na fase C.4 (2026-08-03).** `dataset/casos.jsonl` tem **43 casos**,
todos com `verificada: true` — cada número foi conferido contra a linha real da
publicação citada.

| Estrato | `n` | O que cobre |
|---|---|---|
| `simples` | 23 | alimento único em medida caseira (concha, colher de servir, unidade, fatia, copo) |
| `composto` | 17 | prato pronto que a fonte curada tem inteiro (feijoada, estrogonofe, pizza, baião de dois, yakisoba, …) |
| `foto` | 3 | imagem de item contável, com licença conferida |

**As duas fontes (OQ2, resolvida em 2026-08-02):**

| Papel | Publicação |
|---|---|
| medida caseira → gramas | IBGE, POF 2008-2009, *Tabela de Medidas Referidas para os Alimentos Consumidos no Brasil* (2011) — [liv50000.pdf](https://biblioteca.ibge.gov.br/visualizacao/livros/liv50000.pdf) |
| gramas → kcal e macros | TACO 4ª edição (NEPA/UNICAMP, 2011) — [nepa.unicamp.br/taco](https://www.nepa.unicamp.br/taco/) |
| gramas → kcal e macros, **só onde a TACO não cobre o item** | IBGE, POF 2008-2009, *Tabelas de Composição Nutricional dos Alimentos Consumidos no Brasil* (2011) — [liv50002.pdf](https://biblioteca.ibge.gov.br/visualizacao/livros/liv50002.pdf) |

Duas fontes independentes entre si e independentes do projeto, citáveis por
terceiro, e nenhuma derivada da tabela de porções daqui. A terceira entra em dois
casos (pizza de calabresa e leite integral): a TACO não tem pizza, e a linha de
leite integral da TACO vem sem valores (`*`).

**Como auditar um caso sem confiar no projeto.** O campo `notas` de cada caso traz
o alimento e a **página** em cada publicação, mais a conta de gramas. Exemplo:

```
TACO 4a ed., alimento no 3 (Arroz, tipo 1, cozido), p. 29: 128 kcal/100 g;
medida: IBGE POF 2008-2009, Tabela de Medidas Referidas, p. 35 (45 g x 3 = 135 g)
```

`fonte_url` aponta para a publicação da **composição** (de onde vem o kcal/100 g),
porque o schema carrega uma URL por caso; a publicação da medida está em `notas`.

### Limitações — o teto de precisão deste dataset

1. **A referência é populacional, não individual.** A TACO mede alimentos
   preparados em condição padronizada de laboratório e a POF reporta medidas
   *referidas* por entrevistados. Nenhuma das duas descreve a refeição específica
   de um usuário. Um erro medido aqui é erro contra a média, não contra a verdade
   do prato.
2. **A porção é a medida padrão, não a porção servida.** "Uma concha de feijão"
   vale 140 g na POF; a concha de quem escreveu a frase pode ter 100 g ou 180 g.
   Essa variação entra na métrica como se fosse erro do pipeline.
3. **Fruta com casca.** Para itens em que a POF dá a unidade inteira (laranja,
   180 g) e a TACO reporta por 100 g de **parte comestível**, a base de massa das
   duas fontes não é exatamente a mesma. Os casos afetados dizem isso em `notas`.
4. **As duas fontes discordam entre si onde as duas cobrem.** Feijoada é 117
   kcal/100 g na TACO e 181,59 na POF — receitas diferentes. A regra adotada é
   fixa: TACO quando a TACO cobre; POF só onde não cobre. Trocar a regra move a
   métrica sem que o pipeline tenha mudado.
5. **O estrato `foto` é o mais frágil e o menor (`n = 3`).** A referência é
   `unidades contadas na imagem × medida padrão da POF`; a massa do item
   fotografado não é conhecida. É um piso de erro irredutível, e um `n` desse
   tamanho sustenta descrição, não comparação (ver "Poder estatístico").
6. **Casos perdidos por falta de fonte.** A semente da C.3 tinha "lasanha de
   carne ao forno" a 168 kcal/100 g sem fonte externa: a TACO só traz a massa
   fresca cozida e a POF traz "lasanha pronta light", que é outro produto. O caso
   foi **removido** em vez de mantido com número não auditável.

### Imagens do estrato `foto`

Baixadas do Wikimedia Commons, licença conferida via API antes de versionar,
nenhuma com pessoa identificável. Atribuição:

| Arquivo | Origem | Licença | Autor |
|---|---|---|---|
| `dataset/imagens/coxinha-1-unidade.jpg` | [File:Coxinha.jpg](https://commons.wikimedia.org/wiki/File:Coxinha.jpg) | domínio público | Tom B |
| `dataset/imagens/ovo-frito-1-unidade.jpg` | [File:Ovo frito da Padaria Nova Arcoverde…](https://commons.wikimedia.org/wiki/File:Ovo_frito_da_Padaria_Nova_Arcoverde_em_Pinheiros,_S%C3%A3o_Paulo,_Brasil.jpg) | CC BY 4.0 | Mtvdanilo |
| `dataset/imagens/banana-1-unidade.jpg` | [File:Liat Portal for Foodie Disorder - A Single Banana.jpg](https://commons.wikimedia.org/wiki/File:Liat_Portal_for_Foodie_Disorder_-_A_Single_Banana.jpg) | CC BY-SA 4.0 | HaJunkiyada |

O runner ignora o estrato `foto` (`runner.py`): o caminho de imagem entra na fase
B.5, que é quem mede o `VisionParser`.

### Consumo de quota

O dataset saiu de 10 para 43 casos, dos quais 40 são executáveis pelo runner de
texto — cerca de **4× mais chamadas** por execução completa do que a camada
agendada media antes. `distribuicao_por_estrato()` continua reportando a
composição real a cada execução, para que nenhum relatório esconda um estrato.

## Escolha das métricas

### Por que MdAPE (mediana), e não MAPE (média)

O erro percentual absoluto é **assimétrico por construção**: subestimar tem teto
de 100% (não dá para errar mais que "zero caloria"), superestimar não tem teto. O
MAPE, portanto, pune superestimativa mais do que subestimativa e, usado como
função objetivo, seleciona sistematicamente prompts que **subcontam** calorias —
que é exatamente o modo de falha danoso num diário alimentar.

A métrica headline é a **mediana** do erro percentual absoluto (MdAPE),
acompanhada do **SSPB** (*symmetric signed percentage bias*), que revela a
**direção** do viés — informação que qualquer métrica de erro absoluto apaga.

### Por que macros em MAE, e nunca em percentual

Café preto tem 0,1 g de gordura. Um erro de 0,2 g é 200% de erro percentual e
zero de erro nutricional. Macros em gramas são reportados em **erro absoluto**
(MAE) com **tolerância absoluta** declarada por macro.

### Intervalo de confiança

Cada estrato reporta `n` e IC95 por *bootstrap* percentílico. Um MdAPE sem `n` e
sem intervalo não permite distinguir melhora real de ruído amostral.

## Poder estatístico — o que este `n` detecta e o que não detecta

O desenho é **pareado**: duas versões de prompt são comparadas **nos mesmos
casos**, e o que se analisa é a diferença por caso. É a escolha que compra poder
sem comprar mais dados.

Com `n ≈ 40` casos, design pareado, métrica contínua e α = 0,05 com poder de 80%,
o efeito mínimo detectável fica na casa de **~5 pontos percentuais** de MdAPE —
supondo desvio-padrão das diferenças pareadas na ordem de 10 p.p., que é a ordem
observada nas medições do bug 001.

Para comparação, **o mesmo `n` num desenho não pareado sobre métrica binária**
(por exemplo "acertou dentro de ±10%: sim/não") só detectaria diferenças da ordem
de **~22 pontos percentuais**. É por isso que o desenho é pareado e a métrica é
contínua.

**O que este `n` NÃO detecta:**

- Melhoras menores que ~5 p.p. de MdAPE. Uma diferença de 2 p.p. entre duas
  versões de prompt **não é evidência de melhora** com este conjunto — e o
  relatório não deve ser lido como se fosse.
- Qualquer efeito **dentro de um estrato pequeno**. Um estrato com `n = 6` não
  sustenta comparação; sustenta descrição. O IC95 por estrato existe para tornar
  isso visível em vez de deixar implícito.
- Regressões raras de cauda. Um modo de falha que atinge 1 caso em 200 não
  aparece num conjunto de 40. A bateria de invariância (C.6) cobre parte disso
  por outro caminho — relações que **têm de** valer, independentemente do valor
  absoluto.
- Diferenças causadas por não-determinismo do modelo, que o teste de
  autoconsistência mede separadamente (coeficiente de variação sobre a mesma
  entrada repetida).

## O que a execução em replay mede — e o que ela não mede

`python -m evals.runner --cassettes` resolve as respostas do provedor por gravação
em disco (C.7). Isso torna a reexecução barata e **perfeitamente pareada**: o
mesmo conjunto de respostas do modelo entra nas duas medições, então a diferença
observada vem só do código.

**O que o replay mede bem:** qualquer mudança de **pós-processamento** — sanity
check, lookup no banco, normalização de porção, agregação de macros. Tudo isso
roda *depois* da resposta da IA, sobre a resposta gravada. Foi assim que a
correção do sanity check de fonte curada foi medida (MdAPE do estrato `composto`
23,81% → 6,86%), e o pareamento é o que dá crédito ao número.

**O que o replay NÃO mede:**

- **Qualquer mudança que altere o payload enviado** — texto de prompt, versão de
  prompt, modelo, `temperature`, `max_tokens`, `seed`. O cassette é indexado pelo
  `sha256` do payload, então uma mudança dessas não tem gravação correspondente e
  a execução estoura com `CassetteAusenteError`. Isso é por desenho: comparar
  "antes e depois" com o mesmo vocabulário nos dois casos induz erro. Para medir
  mudança de prompt é preciso regravar contra o provedor (`EVAL_RECORD_CASSETTES=1`),
  e aí a comparação deixa de ser pareada no ruído do modelo.
- **Ruído de amostragem do modelo.** As N repetições de um caso enviam o mesmo
  payload, então em replay `reproduzir()` devolve N vezes a mesma string e o
  coeficiente de variação é zero **por construção** — "o disco é determinístico",
  não "o modelo é determinístico". Por isso o runner força `--repeticoes 1` em
  replay e diz que forçou, em vez de publicar um zero que parece medição. O CV só
  é legítimo com gravação ligada, que é o caso da execução agendada do `eval.yml`.
  Quem quiser medir ruído sem gastar o dataset inteiro tem o grupo `inv-08` da
  bateria de invariância, que chama o `AIClient` direto, sem cassette.

## Imutabilidade de versão de prompt

Um arquivo de versão em `app/prompts/<nome>/v<N>.txt` **não é editado** depois de
ter uma execução de eval associada. Mudança gera versão nova — mesmo contrato de
uma migration Alembic já aplicada. O `sha256` de cada versão ativa está travado em
`tests/unit/test_prompt_registry.py`, então a regra é imposta pela suíte, não pela
disciplina de quem edita.

## Layout

```
evals/
├── __init__.py
├── schema.py                       # contrato do caso (C.3)
├── dataset/
│   ├── casos.jsonl                 # 43 casos com ground truth externo (C.4)
│   ├── imagens/                    # estrato `foto`, licença conferida (C.4)
│   └── grupos_invariancia.jsonl    # relações metamórficas (C.6)
├── metrics.py                      # funções puras: MdAPE, SSPB, MAE, IC95 (C.5)
├── runner.py                       # executa o pipeline por caso e agrega (C.5)
├── invariance.py                   # bateria metamórfica (C.6)
├── report.py                       # série temporal a partir do histórico (C.8)
├── cassettes/                      # gravações do provedor, camada rápida (C.7)
└── runs/history.jsonl              # append-only, uma linha por execução (C.8)
```

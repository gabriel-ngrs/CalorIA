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
- **O comportamento com foto**, enquanto o estrato `foto` estiver vazio (ver
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

**Semente, não conjunto de avaliação.** Os 10 casos de `dataset/casos.jsonl`
existem para exercitar o runner e nascem todos com `verificada: false`: os
valores vieram da TACO 4ª edição mas **não** foram conferidos linha a linha
contra a publicação.

A fase **C.4** está bloqueada pela **OQ2** (origem do ground truth), que o owner
decidiu resolver durante o desenvolvimento. Até lá:

- nenhum número deste harness sustenta afirmação pública de qualidade;
- o estrato `foto` está vazio — depende da OQ2 e de imagens com licença
  verificada;
- `distribuicao_por_estrato()` reporta a composição real a cada execução, para
  que um relatório nunca esconda um estrato vazio.

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
│   ├── casos.jsonl                 # casos-semente (C.3) → populado na C.4
│   └── grupos_invariancia.jsonl    # relações metamórficas (C.6)
├── metrics.py                      # funções puras: MdAPE, SSPB, MAE, IC95 (C.5)
├── runner.py                       # executa o pipeline por caso e agrega (C.5)
├── invariance.py                   # bateria metamórfica (C.6)
├── report.py                       # série temporal a partir do histórico (C.8)
├── cassettes/                      # gravações do provedor, camada rápida (C.7)
└── runs/history.jsonl              # append-only, uma linha por execução (C.8)
```

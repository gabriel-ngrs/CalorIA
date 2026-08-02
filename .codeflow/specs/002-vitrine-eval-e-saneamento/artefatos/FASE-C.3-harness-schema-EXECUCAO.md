---
spec: 002-vitrine-eval-e-saneamento
fase: C.3
slug_fase: harness-schema
status: executado
tentativa: 1
reprovacoes: 0
sha_inicial: 97a4b0d
sha_final: 0d4d9ec
range: 97a4b0d..0d4d9ec
---

# FASE C.3 — Relatório de execução

## 1. Resumo do que foi feito

Estrutura do harness criada em `backend/evals/`, com o contrato de caso
(`CasoEval`) agnóstico à fonte de ground truth — que é o que permite a
infraestrutura do Track C avançar com a OQ2 aberta. Dez casos-semente, todos
marcados como **não verificados**, e o README com a análise de poder.

## 2. Arquivos CRIADOS

| Arquivo | Propósito |
|---------|-----------|
| `backend/evals/__init__.py` | Docstring do pacote e a convenção local pt-BR. |
| `backend/evals/schema.py` | `CasoEval`, `Estrato`, `MacrosReferencia`, `carregar_casos`, `sha_do_dataset`, `distribuicao_por_estrato`. |
| `backend/evals/dataset/casos.jsonl` | 10 casos-semente (6 simples, 4 composto, 0 foto). |
| `backend/evals/README.md` | O que mede / o que não mede, escolha das métricas, análise de poder, regra de imutabilidade. |
| `backend/tests/unit/test_evals_schema.py` | 34 testes do contrato. |

## 3. Arquivos ALTERADOS

Nenhum. A fase é puramente aditiva, e nem
`backend/scripts/eval_golden_set.py` nem
`backend/tests/integration/test_golden_set.py` foram tocados — o escopo travado
exige que continuem sendo o gate determinístico.

## 4. Confirmação do REUSO e decisões de design

**REUSADO:** os casos-semente derivam do conjunto `GOLDEN` de
`scripts/eval_golden_set.py`, e o padrão de honestidade do docstring desse
arquivo (`:14-27` — declarar o que a métrica não mede) é a estrutura da seção
correspondente no README do harness.

**Decisões de design:**
- **Circularidade virou validação, não convenção.** `fonte_referencia` que
  mencione a tabela `portions` do projeto é rejeitada pelo schema. `fonte_url`
  precisa ser `http(s)` ou `isbn:` — número sem procedência auditável não é
  ground truth.
- **Porções declaradas em GRAMAS nos casos-semente.** Assim a referência não
  depende da conversão de medida caseira do próprio projeto, que é exatamente a
  circularidade proibida.
- **`sha_do_dataset` sobre o conteúdo canônico ordenado por `id`**, não sobre os
  bytes do arquivo: reordenar linhas ou reformatar o JSON não muda o que foi
  medido, então não pode mudar a identidade do conjunto.
- **`distribuicao_por_estrato` sempre reporta os três estratos**, inclusive com
  zero. Um estrato vazio que some do relatório é um relatório que mente por
  omissão.

**Desvios da spec, com justificativa:**

1. **Campo `verificada: bool` acrescentado ao schema**, além dos declarados. Os
   valores dos casos-semente vieram da TACO 4ª edição **mas não foram conferidos
   linha a linha contra a publicação** — esta fase não tem mandato para isso, a
   C.4 tem. Sem o campo, a única forma de registrar essa ressalva seria prosa em
   `notas`; com ele, a ressalva é machine-readable, o relatório do runner a conta
   (`casos_nao_verificados`) e a C.4 tem um alvo objetivo. Há teste garantindo
   que toda semente nasce `verificada: false`.
2. **Campo `imagem_path` acrescentado**, obrigatório no estrato `foto`. Sem
   imagem o caso não é executável, e aceitar um caso de foto sem imagem seria
   aceitar um caso quebrado.
3. **Estrato `foto` fica vazio.** Depende da OQ2 e de imagens com licença
   verificada — o escopo travado da C.4 proíbe versionar imagem de terceiro sem
   verificar a licença. Declarado no README e visível no relatório como `n=0`.

**Escopo travado respeitado:** a OQ2 **não** foi decidida — nenhuma fonte foi
escolhida por conta própria; o dataset não foi populado além do mínimo para o
runner funcionar; `eval_golden_set.py` e `test_golden_set.py` seguem intactos.

## 5. Comandos rodados + saídas reais

```text
$ ruff check . && ruff format --check .
All checks passed!

$ mypy app/ evals/
Success: no issues found in 76 source files

$ pytest tests/unit/test_evals_schema.py -q
34 passed in 0.07s

$ python -c "from evals.schema import *; c = carregar_casos(); ..."
casos: 10
distribuicao: {'simples': 6, 'composto': 4, 'foto': 0}
sha: 426cb61f64af9b68c43674d9cdab3d4357e4345ddbf77755e39766c0d67bb8a5
```

## 6. Checklist dos ACs / critério de conclusão

- [x] **AC-12** — todo caso valida contra o schema; caso com fonte proibida é
      rejeitado; caso sem `fonte_url` é rejeitado.
      *Evidência:* `TestCamposObrigatorios` (parametrizado sobre cada campo
      obrigatório), `TestFonteProibida` (4 grafias de `portions`),
      `TestFonteUrl` (http, isbn, e 3 formas não localizáveis).
- [x] **Schema validado** — `TestCarregamentoDoArquivo` carrega o arquivo
      versionado inteiro e recusa `id` duplicado, apontando o número da linha.
- [x] **README com a análise de poder escrita** — seção "Poder estatístico",
      com o efeito mínimo detectável (~5 p.p. no desenho pareado, contra ~22
      p.p. no não pareado binário) **e** a lista explícita do que o `n` não
      detecta.

## 7. Dúvidas para o avaliador

1. **`verificada: false` em todos os 10 casos** é a forma correta de registrar
   que a semente ainda não foi conferida na publicação da TACO? A alternativa
   seria não semear valor nenhum, mas aí o runner não teria o que exercitar.
2. **Estrato `foto` vazio** trava parte do gate da B.5 (delta do estrato de
   foto). Aceitável até a C.4, ou vale um caso de foto com imagem própria do
   owner?

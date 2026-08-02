---
spec: 002-vitrine-eval-e-saneamento
fase: C.8
slug_fase: historico-eval
status: executado
tentativa: 1
reprovacoes: 0
sha_inicial: 40e2941
sha_final: 8660f40
range: 40e2941..8660f40
---

# FASE C.8 — Relatório de execução

> **Nota de commit.** C.7 e C.8 compartilham o commit `8660f40`. O `eval.yml` da
> C.7 chama `evals.report` da C.8 nos passos de registro e de gate; separá-las em
> dois commits deixaria um estado intermediário com um workflow apontando para um
> módulo inexistente.

## 1. Resumo do que foi feito

`runs/history.jsonl` **append-only**: uma linha por execução completa amarrando a
métrica a `git_commit`, versão e `sha` de cada prompt, modelo, parâmetros de
amostragem, `sha` e `n` do dataset, métricas por estrato e agregadas, e o resumo
da invariância. `report.py` gera a série temporal a partir do histórico, sem
rede, e aplica o gate da execução agendada.

## 2. Arquivos CRIADOS

| Arquivo | Propósito |
|---------|-----------|
| `backend/evals/report.py` | `montar_linha`, `registrar`, `carregar_historico`, `verificar`, `serie_temporal`, CLI com `registrar`/`serie`/`verificar`. |
| `backend/evals/runs/history.jsonl` | Histórico versionado (nasce vazio). |
| `backend/evals/runs/README.md` | Regras do arquivo append-only. |
| `backend/tests/unit/test_evals_report.py` | 17 testes. |

## 3. Arquivos ALTERADOS

| Arquivo | O que mudou |
|---------|-------------|
| `.gitignore` | `ultimo-relatorio.json` e `ultima-invariancia.json` — artefatos de execução ficam fora do git; o histórico versionado é o `history.jsonl`. |
| `.github/workflows/eval.yml` | Passos de registro no histórico e de verificação de limiares. |

## 4. Confirmação do REUSO e decisões de design

**REUSADO:** o relatório JSON do runner da C.5 é a entrada de `montar_linha` —
nenhuma métrica é recalculada aqui.

**Decisões de design:**
- **`run_id` derivado de `commit + sha do dataset`.** Duas execuções do mesmo
  commit sobre o mesmo dataset são a mesma medição (NFR-5), e o `run_id` diz
  isso. Dataset diferente muda o `run_id`.
- **Append-only imposto pelo código.** `registrar` abre em modo `"a"`; há teste
  garantindo que o conteúdo anterior continua sendo prefixo do arquivo depois de
  uma nova linha.
- **A regra de imutabilidade de versão de prompt** está escrita no README do
  harness (C.3) e é imposta pela suíte, não pela disciplina: o `sha` de cada
  versão ativa está travado em `test_prompt_registry.py`.
- **Série temporal anota o ponto em que a versão de prompt mudou**, comparando o
  conjunto de versões de cada linha com o da anterior.
- **Gate com limiares conservadores** (`MDAPE_MAXIMO = 25%`,
  `FRACAO_MINIMA_DENTRO_DE_10PCT = 0.50`). São o piso da execução agendada, não
  os limiares travados em `test_golden_set.py`, que continuam sendo o gate
  determinístico independente (NFR-6).
- **Nada de segredo no registro.** Há teste varrendo a linha serializada por
  `gsk_`, `API_KEY`, `password` e `@gmail`.
- **Sem gráfico dependente de serviço externo** — a série sai em texto.

## 5. Comandos rodados + saídas reais

```text
$ mypy app/ evals/
Success: no issues found in 81 source files

$ pytest tests/unit/test_evals_report.py -q
17 passed in 0.06s

$ pytest -q --ignore=tests/smoke_test.py
502 passed, 5 skipped, 3 warnings in 52.17s
```

## 6. Checklist dos ACs / critério de conclusão

- [x] **AC-16, cada linha amarra métrica a commit, prompts com `sha`, modelo e
      `sha` do dataset** —
      `TestLinhaDoHistorico::test_amarra_metrica_a_commit_prompt_modelo_e_dataset`.
- [x] **AC-16, duas execuções em commits diferentes produzem duas linhas
      distintas e rastreáveis** —
      `TestHistoricoAppendOnly::test_duas_execucoes_viram_duas_linhas_rastreaveis`,
      que confere os dois commits e os dois MdAPE.
- [x] **Relatório gerado a partir do histórico sem acesso à rede** —
      `TestSerieTemporal::test_gerada_sem_rede_a_partir_do_historico`.
- [x] **Append-only** — `test_registrar_nao_reescreve_linha_anterior`.
- [x] **Sem chave de API, PII ou conteúdo de `.env` no registro** —
      `test_o_registro_nao_carrega_segredo`.
- [—] **Histórico com ao menos duas execuções REAIS** — o arquivo versionado
      está vazio. Duas execuções reais exigem o `eval.yml` rodando no GitHub
      Actions com a chave da Groq; nesta sessão não há alcance a `api.groq.com`
      nem `pg_trgm`. As duas execuções estão **simuladas e testadas** com dados
      sintéticos; as reais dependem do owner disparar o workflow.

## 7. Dúvidas para o avaliador

1. O gate da fase pede "histórico com ao menos duas execuções reais". Isso é
   satisfazível só pelo owner (disparar `eval.yml` duas vezes, em commits
   diferentes). A fase pode ser aprovada com a infraestrutura pronta e essa
   pendência declarada?
2. `MDAPE_MAXIMO = 25%` e piso de 50% dentro de ±10% foram escolhidos sem
   medição. Recalibrar após as duas primeiras execuções reais?

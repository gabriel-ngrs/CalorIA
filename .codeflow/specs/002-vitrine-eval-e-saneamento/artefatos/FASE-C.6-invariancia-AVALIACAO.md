---
spec: 002-vitrine-eval-e-saneamento
fase: C.6
slug_fase: invariancia
tentativa: 1
veredito: RESSALVAS
score: 9.7
threshold: 8.5
range_avaliado: e338ed4..36d68cc
---

# FASE C.6 — Avaliação independente

## 1. Veredito e score

**Veredito:** RESSALVAS · **Score:** 9.7 / threshold 8.5

A fase entregou o que o owner identificou como núcleo diferenciador, e entregou
com a disciplina difícil: **7 de 12 grupos reprovaram e nenhuma tolerância foi
afrouxada**. O relatório apresenta as reprovações em ordem de gravidade, com
números, e corrige publicamente um diagnóstico anterior errado do próprio autor
(o `0,5 kg` que não era o bug). Isso é raro e vale registrar.

Duas ressalvas. A relevante: a medição que sustenta a fase foi feita **antes** das
duas correções que atacam quatro dos sete grupos reprovados, e a remedição não
saiu por quota. O relatório da fase descreve, hoje, um comportamento que o código
já não tem.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 4 | AC-14 completo: spread por grupo (`invariance.py:124-135`), taxa de aprovação e p95 (`resumir`, `:193-216`), grupo do bug 001 presente. Escopo travado respeitado com rigor: nenhuma tolerância afrouxada, nenhum grupo removido, a bateria **não** virou gate de CI. Desconto pelo C6-IMP-1. |
| 2 | Arquitetura e direção de dependências | 3 | 5 | Relações como **dados** (`grupos_invariancia.jsonl`), não como código: acrescentar um grupo é acrescentar uma linha. `metrics.percentil` foi promovido de privado a público em vez de ser importado com `_` — a direção certa quando dois módulos precisam do mesmo cálculo. |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | Sem PII nas descrições; nenhuma imagem versionada; `gitleaks` sobre o range com zero achados. |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | Os 7 pares de `scripts/instrument_meal_pipeline.py:41-88` migraram sem perder nenhum, com teste que lista os sete `id` e falha se algum sumir. `ColetorDeEstagios` e `instrumentar_lookup` vêm do runner da C.5, não foram copiados. |
| 5 | Padrões de domínio/aplicação | 2 | 5 | `Relacao` como `StrEnum`, como os enums do projeto. `model_config = {"extra": "forbid"}` impede grupo com campo inventado passar despercebido. |
| 6 | Local e nomes dos arquivos | 2 | 5 | `evals/invariance.py`, `evals/dataset/grupos_invariancia.jsonl`, `tests/unit/test_evals_invariance.py` — onde a fase pediu. |
| 7 | Qualidade de código | 2 | 5 | `mypy` strict limpo. `_coerencia_da_relacao` impõe no schema o que seria comentário: `escala` sem `fator_esperado` é rejeitada, `autoconsistencia` com duas descrições é rejeitada. A normalização de `escala` pelo fator antes de medir dispersão (`:154-159`) é a modelagem correta — sem ela, um pipeline certo reprovaria com spread 2,0. |
| 8 | Testes e cobertura | 2 | 5 | 29 testes: spread em casos sintéticos, avaliação por relação, o grupo do bug 001 verificado pelas duas descrições exatas, resumo com o reprovado aparecendo com os números que o reprovaram. |
| 9 | Migration safety (se aplicável) | 2 | [—] | Nenhuma migration no range (NFR-7). |

Média ponderada das 8 dimensões aplicáveis: 97/20 = 4.85 → **9.7**.

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

**C6-IMP-1 — a medição que sustenta a fase é anterior às correções que a própria
fase motivou; o relatório descreve um comportamento que o código já não tem.**

A §5 do EXECUCAO registra a linha de base:

```text
n_grupos: 12 | aprovacao: 0.417 | spread mediano: 1.2115 | p95: 3.5126
```

E os sete reprovados. Depois disso, a rodada de 2026-08-02 mudou duas coisas que
atingem quatro desses sete diretamente:

- `meal_parser.py:159` — o sanity check deixou de descartar match de fonte curada.
  O próprio relatório atribui a esse defeito os grupos `inv-03`, `inv-06`,
  `inv-10` e "provavelmente `inv-12`".
- `scripts/seed_portions.py` — regras próprias de `porcao`/`unidade` para as
  gorduras de passar, que é a causa nomeada do `inv-04` (spread 4,14, o pior da
  bateria).

`CORRECOES-2026-08-02-POS-VALIDACAO.md` declara a remedição como **pendente por
quota**, com a ação para o owner e a linha de base para comparar. A honestidade
está lá. O problema é de estado, não de conduta: enquanto a remedição não sair, o
artefato desta fase afirma "7 de 12 reprovam" sobre um pipeline em que quatro
dessas causas foram atacadas. Qualquer leitura futura do relatório — inclusive a
que alimentar o README da D.3 — parte de um número obsoleto.

**Correção sugerida:** rodar `python -m evals.invariance` quando a quota voltar
(ou disparar `eval.yml` por `workflow_dispatch`), comparar contra a base
declarada (aprovação 0,417 · mediano 1,2115 · p95 3,5126), e acrescentar a nova
medição como seção datada no EXECUCAO da C.6 — sem apagar a antiga, que é a
metade "antes" da narrativa. Só então reavaliar.

**C6-IMP-2 — a correção das regras de porção (`seed_portions.py`) foi aplicada
fora do conjunto de arquivos declarado por qualquer fase, sem decision
registrada.**

O achado `inv-04` é desta fase; a correção mexeu em `backend/scripts/seed_portions.py`
(+19 linhas no range da rodada), que não consta nos "Arquivos alterados" da C.6
nem de nenhuma outra fase da §5. O DoD global da spec exige: *"Toda decisão de
escopo tomada durante a execução está registrada aqui em §8 ou numa decision do
framework."* Verifiquei: não há decision sobre regras de porção, e a §8 da spec
não registra a mudança.

O mérito é claro — 100 g de manteiga são ~720 kcal, a regra genérica estava
errada, há 20 testes novos cobrindo a tabela e a duplicata `(margarina,
colher_sopa)` que derrubava o seed inteiro. Não estou pedindo reversão. Estou
pedindo o registro, porque a tabela `portions` é dado semeado em produção e
mudá-la altera o resultado de refeições já cadastradas dali em diante.

**Correção sugerida:** decision curta registrando: o defeito medido, as sete
entradas acrescentadas, a duplicata removida, e o efeito esperado sobre o
`inv-04`. Tags `nutricao`, `portions`, `eval`, `spec-002`, `fase-c6`. Indexar em
`.codeflow/decisions/INDEX.md`.

## 5. Sugestões

- **`inv-08` (autoconsistência) mede o que a C5-IMP-1 pode mascarar.** A bateria
  chama o `AIClient` direto (`invariance.py:233`), sem cassette, então o CV que
  ela reporta é real. Vale registrar essa diferença no README do harness: a
  bateria mede ruído de verdade, o runner em replay não.
- **Em que fase a bateria vira gate** (dúvida 4 do EXECUCAO): a resposta natural é
  depois da C.4, quando o dataset e as tolerâncias tiverem medição por trás. O
  piso deveria ser a aprovação medida na remedição, arredondada para baixo — a
  mesma disciplina que a B.4 aplicou à cobertura. Vale virar item explícito da
  C.4 ou fase própria.
- As tolerâncias dos 5 grupos novos foram escolhidas por raciocínio (dúvida 3).
  Depois da remedição, `ordem` e `ruido` provavelmente se confirmam bem
  calibradas; `escala` e `unidade` é que dirão se reprovavam por bug — como o
  executor supõe — ou por tolerância apertada. É o teste da hipótese, e ele ainda
  não foi feito.
- `medir_kcal` (`invariance.py:219-223`) tem o mesmo acoplamento a métodos
  privados do runner. Mesma sugestão da C.5: resolver os dois juntos.

## 6. Comandos rodados + saídas reais

Ambiente: container `caloria_backend`, branch `dev`, HEAD `e3a974a`.
`git merge-base --is-ancestor 36d68cc HEAD` → OK.

```text
$ python3 -c "... grupos_invariancia.jsonl ..."
inv-01-pizza-calabresa       | parafrase        inv-07-tacaca-ausente     | parafrase
inv-02-ovos-numeral-extenso  | parafrase        inv-08-determinismo       | autoconsistencia
inv-03-pf-vago-vs-gramas     | unidade          inv-09-ordem-arroz-feijao | ordem
inv-04-pao-manteiga          | unidade          inv-10-unidade-g-kg       | unidade
inv-05-leite-copo-ml         | unidade          inv-11-ruido-cortes       | ruido
inv-06-marmita-strogonoff    | parafrase        inv-12-escala-dobro       | escala
grupos: 12       # 6 relações, os 7 pares originais preservados

$ docker compose -f docker-compose.dev.yml exec -T backend pytest --cov=app --cov-report=term -q
581 passed, 1 skipped, 5 warnings in 88.01s
Required test coverage of 72.0% reached. Total coverage: 73.10%

$ ... ruff check . && ... ruff format --check . && ... mypy app/ evals/
All checks passed! / 147 files already formatted / Success: no issues found in 81 source files

# escopo travado: a bateria NÃO é gate de CI
$ grep -n "invariance" .github/workflows/ci.yml
84:  run: pytest ... tests/unit/test_evals_invariance.py ...
# só os testes UNITÁRIOS da bateria rodam no PR; a bateria contra o provedor
# está no eval.yml agendado, sem travar PR — como o escopo travado determina

$ git status --short
(limpo)
```

**A remedição não foi executada por mim, e não por escolha:** a quota do free
tier da Groq está esgotada — a própria rodada de correção documentou o
`RateLimitError` com o log de backoff. Rodar a bateria agora produziria falha de
quota, não medição. Isso é precisamente o C6-IMP-1, e é também a confirmação
empírica do risco R5 da spec.

## 7. Itens da fase / DoD não atendidos

O gate declarado da fase — "AC-14 satisfeito; execução manual produz relatório de
invariância; achados de reprovação registrados no relatório da fase" — **está
satisfeito**, e verifiquei as três cláusulas.

O que não está atendido é posterior ao gate: a evidência ficou desatualizada em
relação ao código de HEAD (C6-IMP-1), e uma correção nascida desta fase não tem
registro de decisão (C6-IMP-2).

## 8. Divergências entre o relatório e o código real

1. **Números de §5 vs. código de HEAD** — a divergência principal, tratada em
   C6-IMP-1. O relatório é honesto quanto ao momento da medição; o que falta é a
   medição nova.
2. **`inv-10` (`0,5 kg`)** — verifiquei a correção de diagnóstico do relatório e
   ela é consistente com o código: `PortionNormalizer` converte `0,5 kg` para
   500 g corretamente, e o caminho que divergia era o sanity check em
   `meal_parser.py:158-159`, agora isento para fonte curada. O relatório corrige
   o próprio erro anterior em vez de o enterrar — registro isso a favor.
3. Nenhuma outra. Confirmei a migração dos 7 pares, a presença do grupo do bug
   001 e o fato de a bateria não ser gate de PR.

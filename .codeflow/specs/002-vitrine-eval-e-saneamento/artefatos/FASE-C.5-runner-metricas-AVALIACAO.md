---
spec: 002-vitrine-eval-e-saneamento
fase: C.5
slug_fase: runner-metricas
tentativa: 3
veredito: APROVADO
score: 9.9
threshold: 8.5
range_avaliado: 0d4d9ec..769cf69b0964bc47f5a2e201729b244478ee1e7f
---

# FASE C.5 — Avaliação independente

## 1. Veredito e score

**Veredito:** APROVADO · **Score:** 9.9 / threshold 8.5

**C5-IMP-3 está fechado, e fechado na forma certa — pela raiz, não pelo sintoma.** O
achado era que a latência ia para o relatório sem `origem`, do mesmo jeito que o custo
ia antes do C5-IMP-1. A correção não acrescentou um segundo lugar onde a origem é
decidida: `runner.py:370-373` deriva a origem da latência **do próprio custo**, com o
comentário declarando o porquê ("uma definição só de 'de onde veio esta execução',
dois consumidores"). Isso é o oposto de remendar — é remover a possibilidade de os
dois campos divergirem.

Verifiquei o efeito rodando o runner eu mesmo, em replay:

```text
custo    : {'chamadas': 0, 'tokens_in': 0, 'tokens_out': 0, 'origem': 'replay'}
latencia : {'n': 10, 'mediana_s': 0.055, 'total_s': 0.766, 'origem': 'replay'}
```

E o número contra o qual o achado avisava está registrado no `history.jsonl` da C.8,
linha 4, medido contra o provedor: `mediana_s: 4.829`. **88× de diferença entre as
duas origens** na minha medição de hoje. Sem o rótulo, essa distância entraria na
série append-only lida como ganho de performance que nunca existiu. O achado era bom e
a correção o desarma.

**A recusa da sugestão 3 é a decisão certa, e está justificada.** Anular `mediana_s`
em replay teria alinhado a latência ao `ruido_do_modelo`, mas o executor separou os
dois casos corretamente: o CV em replay é zero *por construção* (não há informação),
enquanto a latência em replay **é** informação real sobre outra coisa — o tempo de
execução do harness, que é justamente o número que sustenta a NFR-2 ("camada rápida em
menos de 60 segundos"). Anular teria custado a única métrica que vigia essa NFR. Com
`origem: "replay"` explícito, o leitor tem o número e sabe o que ele mede. Não há o
que mudar aqui.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 4.5 | AC-13 satisfeito na íntegra (§7). Escopo travado respeitado nos quatro itens: MdAPE é a headline e MAPE só aparece no JSON; macros só em MAE de gramas; os testes de métrica não tocam rede (140 testes de eval em 0,63s); `test_golden_set.py` intocado no range. Meia nota a menos porque o estrato `foto` sai com `n=0` — dependência da C.4, não defeito desta fase, mas é metade de um estrato do gate que ainda não mede nada. |
| 2 | Arquitetura e direção de dependências | 3 | 5 | `metrics.py` são funções puras, sem import de banco, rede ou IA (`metrics.py:1-10` declara isso); `runner.py` depende de `metrics`, nunca o contrário. Direção correta. |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | `grep -rEn "gsk_\|API_KEY=\|password=\|@gmail"` em `backend/evals/` (fora testes/README) → zero. Nenhum dado pessoal no dataset ou no relatório (NFR-4). |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | `ColetorDeEstagios` e `instrumentar_lookup` são o padrão de monkeypatch de `scripts/instrument_meal_pipeline.py:118`, reusados e não duplicados — a C.6 os importa do runner em vez de recriar. |
| 5 | Padrões de domínio/aplicação | 2 | 5 | Identificadores em pt-BR (`divergencia`, `resumo_do_custo`, `repeticoes_efetivas`), coerente com o princípio 8 da spec, que trava a convenção local do domínio de eval. |
| 6 | Local e nomes dos arquivos | 2 | 5 | `evals/metrics.py`, `evals/runner.py`, `tests/unit/test_evals_metrics.py` — os três "Arquivos novos" da §5, nos caminhos declarados. |
| 7 | Qualidade de código | 2 | 5 | `ruff check .` + `ruff format --check .` + `mypy app/ evals/` limpos. `_resumo_da_latencia` (`runner.py:412-431`) tem docstring explicando o *porquê* do campo, não o *quê* do código. |
| 8 | Testes e cobertura | 2 | 5 | `pytest tests/unit -q` → **475 passed** (o relatório disse 475; confere). `TestOrigemDaLatencia` cobre os três casos que importam: origem acompanha o número, execução sem custo não finge origem (`"nao medido"`), execução vazia ainda declara a origem. |
| 9 | Migration safety | 2 | [—] | Nenhuma migration criada ou alterada. Dimensão excluída do cálculo. |

**Score:** (4,5·3 + 5·3 + 5·3 + 5·3 + 5·2 + 5·2 + 5·2 + 5·2) / 20 = 98,5/20 = 4,925 → **9,9**

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

Nenhum.

- **C5-IMP-1** (`--repeticoes` com `--cassettes` reportando ruído zero por construção)
  — fechado na tentativa 2, confirmado hoje: `repeticoes_efetivas` existe em
  `runner.py:243`, é chamada em `runner.py:518` e o runner avisa quando reduz.
- **C5-IMP-2** (o relatório não declarava o que o replay mede) — fechado na tentativa
  2, com a seção "O que a execução em replay mede — e o que ela não mede" no
  `evals/README.md`.
- **C5-IMP-3** (latência sem origem) — fechado nesta tentativa, verificado no §1.

## 5. Sugestões

1. **`evals/runner.py` — o estrato `foto` imprime `(vazio)`.** Está correto e é
   honesto, mas quando a C.4 popular o dataset vale conferir que a linha passa a
   mostrar `n`, IC95 e SSPB como as outras; hoje o caminho de estrato vazio é o único
   sem cobertura de saída real no relatório de texto.
2. O aviso `nao verific.: 10 caso(s) com 'verificada=false' — a metrica ainda nao
   sustenta afirmacao publica` é exatamente a higiene epistêmica que esta spec
   pretende demonstrar como vitrine. Vale citá-lo no README do harness como exemplo
   deliberado, em vez de deixá-lo só como efeito colateral do estado do dataset.
3. `mape` continua sendo calculado e gravado no JSON (`history.jsonl`, campo `mape`).
   É útil como contraste didático com o MdAPE — mas, como a spec trava MAPE fora da
   headline, um comentário no ponto de gravação dizendo "guardado para contraste,
   nunca para reportar" evita que um leitor futuro o promova por engano.

## 6. Comandos rodados + saídas reais

Rodados por mim, na ponta da branch `dev`, contra os containers de dev. Árvore limpa
antes e depois; o runner foi executado em replay (`--cassettes`), sem consumir quota.

```text
$ git merge-base --is-ancestor 769cf69b0964bc47f5a2e201729b244478ee1e7f HEAD
769cf69b...: ANCESTRAL de HEAD
0d4d9ec:    ANCESTRAL de HEAD

$ git status --porcelain
(vazio)

$ docker compose -f docker-compose.dev.yml exec -T backend \
    sh -c "ruff check . && ruff format --check . && mypy app/ evals/"
All checks passed!
147 files already formatted
Success: no issues found in 81 source files

$ docker compose -f docker-compose.dev.yml exec -T backend sh -c "pytest tests/unit -q"
475 passed in 3.89s

# execução manual do runner — o gate da fase
$ docker compose -f docker-compose.dev.yml exec -T backend python -m evals.runner --cassettes
========================================================================
EVAL DO PIPELINE DE IA — CalorIA
========================================================================
dataset sha : 426cb61f64af9b68  (n=10)
distribuicao: {'simples': 6, 'composto': 4, 'foto': 0}
nao verific.: 10 caso(s) com `verificada=false` — a metrica ainda nao sustenta afirmacao publica
modelo      : llama-3.3-70b-versatile
amostragem  : {'temperature': 0.1, 'max_tokens': 8192, 'seed': -1, 'repeticoes': 1}
prompts     : {'meal_identify': {'versao': 1, 'sha': 'f1334ef6...'},
               'meal_fallback': {'versao': 1, 'sha': '713ea1c5...'}}
custo       : {'chamadas': 0, 'tokens_in': 0, 'tokens_out': 0, 'origem': 'replay'}
latencia    : {'n': 10, 'mediana_s': 0.055, 'total_s': 0.766, 'origem': 'replay'}

estrato         n    MdAPE               IC95      SSPB   <=10%
------------------------------------------------------------------------
simples         6    1.26% [  0.00,   5.71]     1.25%   100%
composto        4    6.86% [  0.00,  30.95]    -3.13%    75%
foto            0   (vazio)
------------------------------------------------------------------------
AGREGADO       10    3.89% [  0.00,   6.16]     0.00%    90%

macros (MAE em gramas, tolerancia absoluta — nunca %):
  proteina_g     MAE=  0.99 g   dentro de ±5 g: 100%
  carboidrato_g  MAE=  0.49 g   dentro de ±5 g: 100%
  gordura_g      MAE=  0.63 g   dentro de ±5 g: 100%

# camada rápida, sem rede (NFR-2)
$ docker compose -f docker-compose.dev.yml exec -T backend sh -c \
    "pytest tests/unit/test_evals_invariance.py tests/unit/test_evals_metrics.py \
     tests/unit/test_evals_report.py tests/unit/test_evals_snapshot.py \
     tests/unit/test_evals_schema.py -q"
140 passed in 0.63s

# escopo travado: os limiares do golden set não foram tocados
$ git diff --stat 0d4d9ec..769cf69b -- backend/tests/integration/test_golden_set.py
(vazio)

# NFR-4: sem credencial ou PII nos artefatos de eval
$ grep -rEn "gsk_[A-Za-z0-9]|API_KEY *= *['\"]|password *= *['\"]|@gmail\.com" \
    backend/evals/ | grep -v "test_\|README"
(vazio)
```

## 7. Itens da fase / DoD não atendidos

Nenhum item **exigido** ficou de fora. Detalhamento contra o gate declarado:

- **§9 "C.5 — AC-13; relatório com os três estratos, `n` e IC95"** — atendido. Os três
  estratos aparecem, cada um com `n`; `simples`, `composto` e o agregado trazem MdAPE,
  IC95 e SSPB. `foto` sai `(vazio)` porque o dataset ainda não tem casos de foto — o
  povoamento é a **Fase C.4**, que esta fase não pode antecipar.
- **Passo 1 (funções puras em `metrics.py`)** — APE, MdAPE, SSPB, MAE, acurácia por
  tolerância e IC95 por bootstrap, todas sem dependência de banco ou rede.
- **Passo 2 (runner reusando o monkeypatch)** — `ColetorDeEstagios` +
  `instrumentar_lookup`, o padrão de `instrument_meal_pipeline.py:118`.
- **Passo 3 (regra de reporte)** — kcal em MdAPE/SSPB; macros só em MAE de gramas com
  tolerância absoluta, e o próprio cabeçalho da seção grita "nunca %".
- **Passo 4 (texto + JSON)** — os dois; o JSON é a entrada de `montar_linha` na C.8.
- **`make test-unit` verde** — 475 passed.
- **Assimetria do APE demonstrada por teste** — coberta em `test_evals_metrics.py`,
  dentro dos 140 da camada rápida.

Ressalva de leitura, não item em aberto: com `n=10` e todos os casos marcados
`verificada=false`, o relatório ainda **não** sustenta afirmação pública sobre a
qualidade do pipeline. O runner declara isso em toda execução, o que é o
comportamento correto. Quem fecha essa lacuna é a C.4.

## 8. Divergências entre o relatório e o código real

Nenhuma. Conferi as afirmações verificáveis da tentativa 3:

| Afirmação do relatório | Verificação |
|---|---|
| `_resumo_da_latencia` recebe e publica `origem`, espelhando o custo | confere — `runner.py:412-431`, com a origem derivada do custo em `runner.py:370-373` |
| três testes novos em `TestOrigemDaLatencia` | conferem, e cobrem os três casos declarados |
| `pytest tests/unit/ -q → 475 passed (eram 472)` | confere: 475 passed na minha execução |
| latência em replay ~0,058 s vs ~4,829 s no provedor | confere na ordem de grandeza — medi 0,055 s em replay hoje, e o `history.jsonl` linha 4 registra 4,829 s contra o provedor |

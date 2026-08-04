---
spec: 002-vitrine-eval-e-saneamento
fase: C.8
slug_fase: historico-eval
tentativa: 3
veredito: APROVADO
score: 9.8
threshold: 8.5
range_avaliado: 40e2941..769cf69b0964bc47f5a2e201729b244478ee1e7f
---

# FASE C.8 — Avaliação independente

## 1. Veredito e score

**Veredito:** APROVADO · **Score:** 9.8 / threshold 8.5

**C8-IMP-1 está fechado, e fechado pelo caminho que preserva a propriedade do
arquivo.** O achado era exato: registrar duas vezes o mesmo `/tmp/rel.json` com
`--git-commit` diferente demonstra que `json.load` é determinístico, não que o
pipeline é reprodutível. A correção não apagou a linha duplicada — apagar teria
colidido com o append-only, que é a única propriedade que o arquivo existe para ter —
e sim acrescentou uma medição de verdade. Li o `history.jsonl` diretamente:

```text
1  cc849e7172fe  custo=<AUSENTE>  latencia=<AUSENTE>
2  f479f5dfa9a0  custo=<AUSENTE>  latencia=<AUSENTE>   ← a duplicata histórica de (1)
3  298d79939a66  custo=<AUSENTE>  latencia=<AUSENTE>
4  0a18e93e2d46  custo={'chamadas': 12, 'origem': 'provedor',
                        'tokens_in': 8911, 'tokens_out': 796}
                 latencia={'n': 10, 'mediana_s': 4.829, 'total_s': 72.302,
                           'origem': 'provedor'}
```

**A linha 4 é inequivocamente uma execução contra o provedor**, e não por declaração:
`mediana_s: 4.829` contra os `0.055` que medi hoje em replay é uma diferença de 88×,
impossível de forjar por releitura de disco. E as linhas 3 e 4 são medições
**distintas** entre si — `ic95_mdape` `[0.0, 6.16]` contra `[0.0, 6.3]`, `mape` 5.86
contra 5.88. Duas execuções reais em dois commits, que é o que o §9 pede.

**O resultado colateral que o relatório destaca é legítimo, e é o melhor achado da
tentativa.** A execução contra o provedor devolveu as mesmas métricas headline da
execução em replay (MdAPE 3,89%, SSPB 0,00%, 90% dentro de ±10%). Isso é evidência
direta de **NFR-5** e valida o desenho do cassette da C.7 — o pipeline devolve o mesmo
resultado com as respostas vindo da rede e do disco. A tentativa 1 alegou
reprodutibilidade sem tê-la; agora ela está medida.

**C8-IMP-2** segue fechado, e a solução é melhor que a sugerida na avaliação que o
levantou: como o `AIClientComCassette` não enxerga o `usage`, o observador de consumo
entrou no `AIClient`, opcional, com produção não passando observador nenhum e teste
travando esse caminho.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 4.5 | AC-16 satisfeito: as 4 linhas trazem `git_commit`, `prompts` com `sha`, `modelo`, `dataset_sha`, `dataset_n`, `amostragem` e métricas por estrato. Escopo travado nos três itens: append-only (`registrar` abre em `"a"`, com teste de prefixo), zero segredo/PII (grep meu = 0), série em texto sem serviço externo. Meia nota a menos porque o passo 1 lista o resumo da invariância como parte da linha e **as 4 linhas trazem `invariancia: null`** — o campo existe e o `eval.yml` o alimenta, mas nenhuma execução registrada o preencheu ainda. |
| 2 | Arquitetura e direção de dependências | 3 | 5 | `report.py` consome o JSON do runner da C.5 e não recalcula métrica nenhuma; a direção runner → report → histórico é de mão única. `serie` não toca rede. |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | Há teste varrendo a linha serializada por `gsk_`, `API_KEY`, `password` e `@gmail`; confirmei por fora: `grep -cEi "gsk_\|api_key\|password\|@gmail" history.jsonl` → **0** (NFR-4, princípio 4). |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | `montar_linha` recebe o relatório do runner inteiro; nenhuma métrica reimplementada. A regra de imutabilidade de prompt é imposta pela suíte (`test_prompt_registry.py` trava o `sha`), não pela disciplina — mesmo contrato de uma migration. |
| 5 | Padrões de domínio/aplicação | 2 | 5 | `run_id` derivado de `commit + sha do dataset` codifica a regra certa: mesma medição = mesmo id; dataset diferente = id diferente. Limiares do gate (`MDAPE_MAXIMO = 25%`) declarados como piso da execução agendada, explicitamente distintos dos de `test_golden_set.py`. |
| 6 | Local e nomes dos arquivos | 2 | 5 | `evals/runs/history.jsonl` e `evals/report.py` — os "Arquivos novos" da §5; `runner.py` e `eval.yml` os "Arquivos alterados". |
| 7 | Qualidade de código | 2 | 5 | `ruff`/`format`/`mypy app/ evals/` limpos. `montar_linha` propaga custo/latência com `.get`, e o comentário registra o *porquê* (`null` = "não medido", distinto de `0` = "não custou nada"). |
| 8 | Testes e cobertura | 2 | 5 | 17 testes em `test_evals_report.py`, verdes; append-only testado por invariante de prefixo, não por inspeção visual. `python -m evals.report serie` roda sem rede. |
| 9 | Migration safety | 2 | [—] | Nenhuma migration criada ou alterada. Dimensão excluída do cálculo. |

**Score:** (4,5·3 + 5·3 + 5·3 + 5·3 + 5·2 + 5·2 + 5·2 + 5·2) / 20 = 98,5/20 = 4,925 → **9,8**

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

Nenhum.

- **C8-IMP-1** (as duas execuções reais eram a mesma medição) — fechado. Verificado no
  §1 pela leitura direta do `history.jsonl`, com a latência do provedor (4,829 s)
  servindo de prova independente contra a de replay (0,055 s).
- **C8-IMP-2** (a linha não registrava tokens nem latência) — fechado, com o observador
  opcional de consumo no `AIClient` e a `origem` declarada nos dois campos.

## 5. Sugestões

1. **`invariancia` continua `null` nas 4 linhas.** O passo 1 da fase lista o resumo da
   invariância entre o que a linha amarra, e o `eval.yml:120-128` já passa
   `--invariancia`. Falta apenas uma execução que rode as duas coisas na mesma rodada —
   que é exatamente o que a execução agendada de segunda-feira faz. Vale conferir a
   primeira linha que ela gravar.
2. **O histórico gravado pela execução agendada nunca volta ao repositório.** O
   relatório já registra isto como aberto e atribui à C.7 (dono do `eval.yml`), o que
   está correto. Concordo com o encaminhamento: decidir entre "passo que commita na
   `dev`" e "registrar que o fluxo é manual" junto do primeiro disparo real. Hoje o
   `history.jsonl` da rodada agendada só sobrevive como artifact de 90 dias.
3. **`backend/evals/report.py:71-72`** — vale um teste de leitura defensiva: linhas
   anteriores à instrumentação **não têm** as chaves `custo`/`latencia` (não são
   `null`), e `carregar_historico`/`serie_temporal` precisam continuar tolerando as
   duas formas para sempre, já que o arquivo é append-only e essas linhas nunca vão
   sumir. Hoje funciona; o teste evita que uma refatoração futura assuma a chave
   presente.

## 6. Comandos rodados + saídas reais

Rodados por mim, na ponta da branch `dev`. Árvore limpa antes e depois. Nenhuma
execução contra o provedor — os comandos abaixo leem o histórico já gravado.

```text
$ git merge-base --is-ancestor 769cf69b0964bc47f5a2e201729b244478ee1e7f HEAD
769cf69b...: ANCESTRAL de HEAD
40e2941:    ANCESTRAL de HEAD

$ git status --porcelain
(vazio)

$ docker compose -f docker-compose.dev.yml exec -T backend \
    sh -c "ruff check . && ruff format --check . && mypy app/ evals/"
All checks passed!
147 files already formatted
Success: no issues found in 81 source files

$ docker compose -f docker-compose.dev.yml exec -T backend sh -c "pytest tests/unit -q"
475 passed in 3.89s

# a série, gerada do histórico sem rede — o gate da fase
$ docker compose -f docker-compose.dev.yml exec -T backend python -m evals.report serie
SÉRIE TEMPORAL DO EVAL
==============================================================================
commit           n    MdAPE     SSPB   <=10%  prompts
------------------------------------------------------------------------------
cc849e7172fe    10    3.89%    1.25%    70%  meal_fallback@v1 meal_identify@v1
f479f5dfa9a0    10    3.89%    1.25%    70%  meal_fallback@v1 meal_identify@v1
298d79939a66    10    3.89%    0.00%    90%  meal_fallback@v1 meal_identify@v1
0a18e93e2d46    10    3.89%    0.00%    90%  meal_fallback@v1 meal_identify@v1

# AC-16: cada linha amarra commit, prompts com sha, modelo e sha do dataset
$ python3 -c "…json.loads de cada linha… print(sorted(d.keys()))"
linha 1-3: ['agregado', 'amostragem', 'casos_nao_verificados', 'dataset_distribuicao',
            'dataset_n', 'dataset_sha', 'falhas', 'git_commit', 'invariancia',
            'modelo', 'por_estrato', 'prompts', 'run_id']
linha 4  : idem + ['custo', 'latencia']

$ python3 -c "…print(run_id, git_commit, custo, latencia)…"
1 cc849e7172fe-426cb61f64af  cc849e7172fe48ec93b8b0af9f60058fba0ac10a  <AUSENTE>  <AUSENTE>
2 f479f5dfa9a0-426cb61f64af  f479f5dfa9a00292ad39820032b3c4da98e695c6  <AUSENTE>  <AUSENTE>
3 298d79939a66-426cb61f64af  298d79939a664199f0e09a98331601856a643462  <AUSENTE>  <AUSENTE>
4 0a18e93e2d46-426cb61f64af  0a18e93e2d46139d448d3258dc6303477bc4bcd9
    custo    = {'chamadas': 12, 'origem': 'provedor', 'tokens_in': 8911, 'tokens_out': 796}
    latencia = {'mediana_s': 4.829, 'n': 10, 'origem': 'provedor', 'total_s': 72.302}
    invariancia = None   (idem nas 4 linhas)

# a linha 4 é distinta da 3 por métrica, não só por run_id
linha 3: ic95_mdape [0.0, 6.16]   mape 5.86
linha 4: ic95_mdape [0.0,  6.3]   mape 5.88

# latência de replay medida por mim hoje, para contraste com os 4,829 s da linha 4
$ docker compose -f docker-compose.dev.yml exec -T backend python -m evals.runner --cassettes
latencia    : {'n': 10, 'mediana_s': 0.055, 'total_s': 0.766, 'origem': 'replay'}

# NFR-4 / escopo travado: nenhum segredo no registro
$ grep -cEi "gsk_|api_key|password|@gmail" backend/evals/runs/history.jsonl
0
```

## 7. Itens da fase / DoD não atendidos

Nenhum item **exigido** ficou de fora.

- **§9 "C.8 — AC-16; histórico com ao menos duas execuções reais"** — atendido. AC-16
  verificado linha a linha; as duas execuções reais são a 3 (replay pós-correção do
  sanity check, métricas distintas das anteriores) e a 4 (contra o provedor, com custo
  e latência medidos).
- **Passo 1 (a linha amarra tudo)** — `run_id`, `git_commit`, prompts com `sha`,
  `modelo`, `amostragem`, `dataset_sha` + `n`, métricas por estrato e agregadas, custo
  em tokens e latência. Só o resumo de invariância ainda não foi preenchido por
  execução alguma (§5, sugestão 1).
- **Passo 2 (gerador de relatório da série, anotando entrada de versão de prompt)** —
  `serie_temporal` compara o conjunto de versões de cada linha com o da anterior; a
  série sai sem rede.
- **Passo 3 (regra de imutabilidade de versão de prompt no README do harness)** —
  escrita, e imposta pela suíte via `sha` travado em `test_prompt_registry.py`.
- **Escopo travado** — append-only preservado inclusive quando remover a linha
  duplicada teria sido mais bonito; zero segredo; série em texto.

## 8. Divergências entre o relatório e o código real

Uma, cosmética, e ela não muda conclusão nenhuma:

| Afirmação do relatório | Verificação |
|---|---|
| "As três anteriores gravam `null` nos dois campos" (custo e latência) | As linhas 1–3 **não têm as chaves**; elas são anteriores à instrumentação. `null` é o que `montar_linha` (`report.py:71-72`) grava **daqui em diante**, via `.get`. Na prática dá no mesmo para o leitor e para o código, mas a descrição do estado do arquivo está imprecisa. Daí a sugestão 3. |

O resto confere. Em particular, confirmei as duas afirmações que sustentam o
fechamento de C8-IMP-1 — que a linha 4 tem `origem: 'provedor'` com 12 chamadas e
9.707 tokens, e que ela é distinguível das anteriores por mais que o `run_id` — lendo o
arquivo, não o relatório.

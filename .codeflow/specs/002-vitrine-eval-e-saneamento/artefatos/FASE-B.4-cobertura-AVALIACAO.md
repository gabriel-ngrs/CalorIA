---
spec: 002-vitrine-eval-e-saneamento
fase: B.4
slug_fase: cobertura
tentativa: 3
veredito: APROVADO
score: 9.9
threshold: 8.5
range_avaliado: 8660f40..bbbf03a2ba1371b3c5933acf72917eae84b333dd
---

# FASE B.4 — Avaliação independente

## 1. Veredito e score

**Veredito:** APROVADO · **Score:** 9.9 / threshold 8.5

**B4-IMP-2 está fechado, e fechado no único lugar onde podia ser fechado: no GitHub
Actions.** O achado da tentativa 2 fazia uma distinção correta — verificar o piso
dentro do container prova que a flag funciona, não que o job remoto reprova o build.
Fui conferir o run citado pela API, não pelo relatório:

```text
run 30837561079 · headSha bbbf03a2ba1371b3c5933acf72917eae84b333dd
workflow: CI · conclusion: success
Backend — lint e testes ... success   (14 passos, todos success)
Frontend — lint e build .. success
```

E a linha que importa, extraída do log real do job:

```text
Backend — lint e testes  Testes  Required test coverage of 72% reached. Total coverage: 73.86%
Backend — lint e testes  Testes  620 passed, 4 skipped, 5 warnings in 60.48s (0:01:00)
```

O `headSha` do run é exatamente o `sha_final` do range, e a citação do relatório é
verbatim. O gate está no job remoto, o job rodou, e passou com o piso ativo. Isso
fecha a segunda metade do §9 ("piso ativo **e CI verde**"), que era o que faltava.

**A diferença de contagem que o executor registrou em vez de esconder tem explicação
completa, e eu a fechei.** Container: `623 passed, 1 skipped`. CI: `620 passed, 4
skipped`. Os três a mais que pulam no runner são de `tests/smoke_test.py`, que tem
`pytestmark = pytest.mark.skipif` de módulo em `smoke_test.py:47` condicionado a uma
chave Groq real (`gsk_`) — e o CI define `GROQ_API_KEY: fake-key-for-tests` de
propósito. São 4 testes no módulo; no container 3 passam e 1 pula por banco de dev
indisponível (`smoke_test.py:184`). Fecha exatamente: 624 coletados nos dois lados.

**Isso responde a uma pergunta que o relatório não fez e que importa mais que a
contagem:** os 5 testes de `test_golden_set.py` **não** estão entre os que pulam no
CI. O gate da NFR-6 — que já esteve morto uma vez dentro desta fase — está vivo no
runner do GitHub, não só no container.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 5 | AC-9 nos dois lados: piso ativo em `.github/workflows/ci.yml:98` (`--cov-fail-under=72`) e `backend/pyproject.toml:122` (`fail_under = 72`); 12 endpoints cobertos. Escopo travado respeitado — `git diff 8660f40..bbbf03a2 -- backend/app/api/v1/push.py backend/app/api/v1/reminders.py` sai **vazio**. |
| 2 | Arquitetura e direção de dependências | 3 | 5 | Nenhum router refatorado; testes em `tests/integration/`, camada correta. `test_push.py:1-7` declara por escrito que cobre sem redesenhar. |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | 5 testes de autorização cruzada (`test_push.py:119,171,198`; `test_reminders.py:36,106,133`), leitura **e** escrita nos dois routers — a fase pedia "ao menos um". Num diário alimentar é vazamento de dado de saúde que eles barram. |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | Fixtures `client`, `anon_client`, `db`, `test_user` de `tests/conftest.py`; nenhuma fixture nova criada. |
| 5 | Padrões de domínio/aplicação | 2 | 5 | Classes `TestX` com métodos em pt-BR, espelhando a suíte de integração existente. |
| 6 | Local e nomes dos arquivos | 2 | 5 | `tests/integration/test_push.py` e `test_reminders.py` — exatamente os "Arquivos novos" da §5. |
| 7 | Qualidade de código | 2 | 5 | `ruff check .` → `All checks passed!`; `ruff format --check .` → `147 files already formatted`; `mypy app/ evals/` → `Success: no issues found in 81 source files`. |
| 8 | Testes e cobertura | 2 | 4.5 | Os testes asseguram comportamento, não inflam número — `test_e_publico_por_desenho` (`test_push.py:52`) documenta o comportamento real em vez de o teste "corrigir" o código. Meia nota a menos porque o agregado de 73,86% ainda esconde módulos rasos (`push_service.py` 29%, `tasks/reports.py` 32%) — fora do escopo desta fase, mas é o que a dimensão mede. |
| 9 | Migration safety | 2 | [—] | Nenhuma migration criada ou alterada no range (NFR-7). Dimensão excluída do cálculo. |

**Score:** (5·3 + 5·3 + 5·3 + 5·3 + 5·2 + 5·2 + 5·2 + 4,5·2) / 20 = 99/20 = 4,95 → **9,9**

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

Nenhum.

- **B4-IMP-1** (placeholder `..%` no histórico de medições) — fechado na tentativa 2
  e ainda fechado: `backend/pyproject.toml:116-117` traz `2026-08-02  73%  ...
  (medido: 73,10%)`, com a medição separada do piso.
- **B4-IMP-2** ("CI verde com o gate ativo") — fechado, verificado contra o run real
  pela API do GitHub, no §1 acima.

## 5. Sugestões

1. **`backend/pyproject.toml:110-122`** — o bloco de histórico documenta a margem
   ("existia para absorver os testes que pulavam") como se a variação tivesse
   acabado. Não acabou: os 4 testes de `smoke_test.py` pulam no CI e não no
   container. Não afeta a cobertura (o módulo é de smoke e não conta para `app/`),
   mas uma linha registrando isso pouparia a próxima investigação.
2. **Dúvida 2 do relatório — sim, é a leitura correta.** O `continue-on-error: true`
   do upload ao Codecov foi mantido dentro da autorização explícita do passo 4, já
   que o gate real é o `--cov-fail-under` no próprio job. Nada a mudar.
3. As §§5 e 6 do relatório ainda carregam os números da tentativa 1 (piso 70%,
   medido 72%), superados pelas seções de tentativa 2 e 3 no topo. É consequência do
   contrato de arquivo único do §2.9 e a leitura cronológica funciona, mas um
   marcador "(números da tentativa 1)" no cabeçalho dessas seções evitaria a
   confusão para quem ler de baixo para cima.

## 6. Comandos rodados + saídas reais

Rodados por mim, na ponta da branch `dev`, contra os containers de dev (Postgres 16 +
Redis, os mesmos serviços do CI). Árvore limpa antes e depois.

```text
$ git merge-base --is-ancestor bbbf03a2ba1371b3c5933acf72917eae84b333dd HEAD
bbbf03a2ba1371b3c5933acf72917eae84b333dd: ANCESTRAL de HEAD
8660f40: ANCESTRAL de HEAD

$ git status --porcelain
(vazio)

$ bash ~/.codeflow/framework/core/scripts/run-structural.sh \
    .codeflow/specs/002-vitrine-eval-e-saneamento/SPEC_002_VITRINE_EVAL_E_SANEAMENTO.md
✓ ids de fase únicos (26 fases)
✓ heading de cada fase casa com o bullet `id`
✓ grafo de dependências acíclico
✓ §5 estruturalmente válida
EXIT=0

$ docker compose -f docker-compose.dev.yml exec -T backend \
    sh -c "ruff check . && ruff format --check . && mypy app/ evals/"
All checks passed!
147 files already formatted
Success: no issues found in 81 source files

$ docker compose -f docker-compose.dev.yml exec -T backend \
    sh -c "pytest --cov=app --cov-report=term --cov-fail-under=72 -q"
TOTAL                                      3244    848    74%
Required test coverage of 72% reached. Total coverage: 73.86%
623 passed, 1 skipped, 5 warnings in 122.93s (0:02:02)

# o gate no runner do GitHub, conferido pela API — não pelo relatório
$ gh run view 30837561079 --json headSha,conclusion,workflowName
{"conclusion":"success",
 "headSha":"bbbf03a2ba1371b3c5933acf72917eae84b333dd",
 "workflowName":"CI"}

$ gh run view 30837561079 --log | grep -iE "Required test coverage|passed"
Backend  Lint — ruff                      All checks passed!
Backend  Eval — camada rápida (sem rede)  140 passed in 0.76s
Backend  Testes  Required test coverage of 72% reached. Total coverage: 73.86%
Backend  Testes  620 passed, 4 skipped, 5 warnings in 60.48s (0:01:00)
Frontend Testes  Test Suites: 20 passed, 20 total
Frontend Testes  Tests:       118 passed, 118 total

# escopo travado: os dois routers e os limiares do golden set não foram tocados
$ git diff --stat 8660f40..bbbf03a2 -- backend/app/api/v1/push.py \
    backend/app/api/v1/reminders.py backend/tests/integration/test_golden_set.py
(vazio)

# origem dos 3 skips extras no CI
$ grep -n "skipif" backend/tests/smoke_test.py
47:pytestmark = pytest.mark.skipif(   # exige GROQ_API_KEY real (gsk_)
$ grep -c "^def test\|^async def test" backend/tests/smoke_test.py
4

# frontend (DoD global)
$ cd frontend && npm run lint && npx tsc --noEmit
(1 warning em components/auth/Plasma.tsx — react-hooks/exhaustive-deps; zero erros)
TSC_OK
```

## 7. Itens da fase / DoD não atendidos

Nenhum.

- **§9 "B.4 — AC-9; piso de cobertura ativo e CI verde"** — atendido nas duas
  metades: piso ativo (`fail_under = 72` + `--cov-fail-under=72`) e CI verde com ele
  no run 30837561079, sobre o próprio `sha_final`.
- **Passo 1 (remedir, não presumir)** — remedido a cada tentativa; hoje 73,86%,
  contra os 62% da auditoria de maio.
- **Passo 2 (12 endpoints + autorização cruzada)** — 26 testes em `test_push.py` e
  os de `test_reminders.py` cobrem os dois routers, com 5 casos de autorização
  cruzada onde a fase pedia um.
- **Passo 3 (piso = medido arredondado para baixo)** — 72 contra 73,86 medido. Piso,
  não meta, com o histórico das medições comentado no `pyproject.toml`.
- **Passo 4 (`continue-on-error`)** — mantido, dentro da autorização explícita.
- **NFR-6** — os 5 testes de `test_golden_set.py` rodam e passam, no container e no
  CI (não estão entre os skips do runner).
- **NFR-7** — nenhuma migration tocada.

## 8. Divergências entre o relatório e o código real

Nenhuma divergência material. As três afirmações verificáveis da tentativa 3 batem:

| Afirmação do relatório | Verificação |
|---|---|
| run 30837561079, commit bbbf03a, `success` | confere pela API do GitHub — `headSha` idêntico ao `sha_final` |
| `Required test coverage of 72% reached. Total coverage: 73.86%` | confere no log do job, palavra por palavra |
| `620 passed, 4 skipped` no CI vs `623 passed, 1 skipped` no container | confere; a causa o relatório declarou não ter investigado — investiguei, é o módulo `smoke_test.py`, e está no §1 |

---
spec: 002-vitrine-eval-e-saneamento
fase: B.4
slug_fase: cobertura
tentativa: 1
veredito: RESSALVAS
score: 9.5
threshold: 8.5
range_avaliado: 8660f40..b31604d
---

# FASE B.4 — Avaliação independente

## 1. Veredito e score

**Veredito:** RESSALVAS · **Score:** 9.5 / threshold 8.5

O gate está vivo e verificado por mim no ambiente real. O achado que mais importa
desta fase não estava na entrega original e sim na rodada de correção: o gate da
NFR-6 estava morto e voltou a existir — confirmei `5 passed, 0 skipped`. Uma
ressalva de acabamento impede o APROVADO.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 4 | AC-9 satisfeito: `backend/pyproject.toml:123` `fail_under = 72`, `.github/workflows/ci.yml:98` `--cov-fail-under=72`; medido 73,10%. 36 testes cobrem os 12 endpoints de `push.py` e `reminders.py`. Escopo travado respeitado: `push.py` não foi refatorado. Desconto pelo B4-IMP-1. |
| 2 | Arquitetura e direção de dependências | 3 | 5 | Nenhuma alteração estrutural: só testes novos e configuração. `tests/integration/conftest.py` isola o seed do banco nutricional na sessão, sem tocar o `conftest.py` raiz além do necessário. |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | 5 casos de autorização cruzada (usuário A não lê nem escreve recurso de B) nos dois routers — exatamente o defeito que cobertura numérica não pega e que num diário alimentar vazaria dado de saúde. `GET /push/vapid-public-key` documentado como público por desenho, em vez de o teste "corrigir" o código. |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | Reusa as fixtures `client`, `anon_client`, `db`, `test_user` de `tests/conftest.py`; nenhuma fixture nova criada para os 36 testes. |
| 5 | Padrões de domínio/aplicação | 2 | 5 | Testes de integração seguem o formato dos existentes (classe por agrupamento, nome descrevendo comportamento). |
| 6 | Local e nomes dos arquivos | 2 | 5 | `tests/integration/test_push.py`, `tests/integration/test_reminders.py` — onde a spec pediu. |
| 7 | Qualidade de código | 2 | 4 | `ruff`/`mypy` limpos. Desconto: `pyproject.toml:116-117` deixou um placeholder `..%` no histórico de medições, que é entregável declarado da rodada. |
| 8 | Testes e cobertura | 2 | 5 | Gate demonstrado nos dois sentidos pelo executor (71,98% passa / 64,18% reprova) e reconfirmado por mim com o piso já em 72: `Required test coverage of 72.0% reached. Total coverage: 73.10%`. |
| 9 | Migration safety (se aplicável) | 2 | [—] | Nenhuma migration criada ou alterada (NFR-7 verificado). O `alembic upgrade head` do `_reset_schema` **aplica** migrations no banco de teste; não altera nenhuma. |

Média ponderada das 8 dimensões aplicáveis: 95/20 = 4.75 → **9.5**.

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

**B4-IMP-1 — `backend/pyproject.toml:116-117`: o histórico de medições ficou com
um placeholder não preenchido.**

```toml
# Histórico das medições, para que subir o piso seja sempre decisão com número:
#   2026-05-10  62%  auditoria
#   2026-08-02  72%  fase B.4 (testes de push/reminders), piso posto em 70%
#   2026-08-02  ..%  após o schema de teste vir das migrations, que destravou
#                    os 5 testes do golden set — ver o valor atual abaixo
```

A terceira linha — justamente a que registra a medição que autorizou subir o piso
de 70% para 72% — tem `..%` no lugar do número. O propósito declarado do bloco é
"que subir o piso seja sempre decisão **com número**", e a linha que mais precisa
do número é a que não tem. "Ver o valor atual abaixo" aponta para `fail_under`,
que é o piso, não a medição: os dois são diferentes de propósito (73,10% medido,
72% de piso), e confundi-los apaga exatamente a margem que o comentário existe
para documentar.

**Correção sugerida:** trocar `..%` por `73%` (medição de 2026-08-02 no container,
`Total coverage: 73.10%`) e ajustar a segunda metade da linha para não remeter ao
`fail_under`.

## 5. Sugestões

- **`continue-on-error: true` no upload ao Codecov** (dúvida 2 do EXECUCAO): a
  leitura está correta. O passo 4 da fase autoriza mantê-lo quando o upload não é
  confiável, e o gate real é o `--cov-fail-under` local. Nada a mudar.
- A margem entre medido e piso agora é de 1,1 p.p. Isso é apertado o bastante
  para que um teste de integração legitimamente pulado volte a quebrar o CI. Vale
  observar a próxima meia dúzia de execuções antes de considerar 73%.
- `tests/smoke_test.py:184` pula dentro do container porque procura Postgres em
  `localhost`. Já existe decision declarando o arquivo como sonda de ambiente,
  mas apontá-lo para `postgres:5432` quando `DATABASE_URL` estiver definida
  eliminaria o único `skipped` da suíte.

## 6. Comandos rodados + saídas reais

Ambiente: container `caloria_backend`, branch `dev`, HEAD `e3a974a`.
`git merge-base --is-ancestor b31604d HEAD` → OK.

```text
$ docker compose -f docker-compose.dev.yml exec -T backend pytest --cov=app --cov-report=term -q
...
app/services/push_service.py                 21     15    29%   24-50
app/services/reminder_service.py             42     19    55%   ...
-----------------------------------------------------------------------
TOTAL                                      3204    862    73%
Required test coverage of 72.0% reached. Total coverage: 73.10%
581 passed, 1 skipped, 5 warnings in 88.01s (0:01:28)

# o gate da NFR-6, que esta fase declarou morto e a correção ressuscitou
$ docker compose -f docker-compose.dev.yml exec -T backend pytest tests/integration/test_golden_set.py -q
5 passed, 1 warning in 2.12s

# o único skipped da suíte inteira
$ ... pytest -q -rs
SKIPPED [1] tests/smoke_test.py:184: banco de desenvolvimento indisponível:
  Multiple exceptions: [Errno 111] Connect call failed ('::1', 5432, 0, 0), ...
581 passed, 1 skipped, 5 warnings in 81.06s

$ grep -n -A14 "tool.coverage.report" backend/pyproject.toml
110:[tool.coverage.report]
...
116:#   2026-08-02  ..%  após o schema de teste vir das migrations, que destravou
123:fail_under = 72
124:show_missing = true

$ grep -n "cov-fail-under\|TEST_DATABASE_URL" .github/workflows/ci.yml
92:  TEST_DATABASE_URL: postgresql+asyncpg://caloria:caloria@localhost:5432/caloria_test
98:  run: pytest --cov=app --cov-report=xml --cov-fail-under=72 -q

$ docker compose -f docker-compose.dev.yml exec -T backend ruff check . \
  && ... ruff format --check . && ... mypy app/ evals/
All checks passed! / 147 files already formatted / Success: no issues found in 81 source files

$ git diff --name-only d8cc463~1..HEAD -- backend/alembic/
(vazio)                                       # NFR-7

$ git status --short
(limpo)
```

## 7. Itens da fase / DoD não atendidos

- **Execução verde no GitHub Actions com o gate ativo** continua dependendo de um
  push (ação do owner). O gate em si está verificado no mesmo Postgres 16 + Redis
  que o CI usa, então o risco residual é baixo — mas o item do §9 ("piso de
  cobertura ativo e **CI verde**") só fecha com a execução remota.
- Uma nota de método a favor do executor: a decision
  `2026-08-02-schema-de-teste-por-migrations.md` está registrada e indexada, como
  o DoD global exige. A mudança em `tests/conftest.py` (arquivo da B.1) é
  estrutural e teve o registro correto — ao contrário do que aconteceu na B.3.

## 8. Divergências entre o relatório e o código real

1. **Piso** — o EXECUCAO §3 e §4 descrevem `fail_under = 70` e
   `--cov-fail-under=70`; o código está em **72** nos dois lugares. Não é
   divergência: a própria §6 do relatório registra a subida em 2026-08-02. O
   corpo do relatório ficou desatualizado em relação ao apêndice, o que é
   confuso mas não incorreto.
2. **Cobertura** — relatório: 72% / 538 testes. Medido agora: 73,10% / 581
   testes. A diferença vem dos 5 testes do golden set que deixaram de pular e das
   fases posteriores. Consistente.
3. **`5 skipped`** no relatório contra **`1 skipped`** medido. A redução é o
   efeito esperado da correção do schema de teste — confirma a afirmação central
   da §6 do EXECUCAO em vez de contradizê-la.

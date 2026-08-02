---
spec: 002-vitrine-eval-e-saneamento
fase: B.4
slug_fase: cobertura
status: executado
tentativa: 1
reprovacoes: 0
sha_inicial: 8660f40
sha_final: b31604d
range: 8660f40..b31604d
---

# FASE B.4 — Relatório de execução

## 1. Resumo do que foi feito

Cobertura **remedida** (não presumida): 72%, contra os 62% da auditoria de maio.
Os 12 endpoints de `push.py` e `reminders.py`, que estavam com zero cobertura de
integração, ganharam 36 testes. O piso ficou em 70%, aplicado localmente no
próprio job.

## 2. Arquivos CRIADOS

| Arquivo | Propósito |
|---------|-----------|
| `backend/tests/integration/test_push.py` | 19 testes cobrindo os 7 endpoints do router. |
| `backend/tests/integration/test_reminders.py` | 17 testes cobrindo os 5 endpoints do router. |

## 3. Arquivos ALTERADOS

| Arquivo | O que mudou |
|---------|-------------|
| `backend/pyproject.toml` | Bloco `[tool.coverage.report]` com `fail_under = 70` e `show_missing`. |
| `.github/workflows/ci.yml` | `--cov-fail-under=70` no passo de testes. |

## 4. Confirmação do REUSO e decisões de design

**REUSADO:** as fixtures `client`, `anon_client`, `db` e `test_user` de
`tests/conftest.py` — nenhuma fixture nova foi criada.

**Decisões de design:**
- **Piso em 70%, com 72% medido.** A spec pede "o valor medido arredondado para
  baixo — piso, não meta". 70 (e não 72) absorve a variação entre ambientes: os
  testes que dependem do banco nutricional semeado **pulam** onde ele não existe,
  e essa diferença move a cobertura em alguns pontos. Um piso colado no medido
  quebraria o CI na primeira variação legítima, o que treina o time a baixá-lo —
  o oposto do objetivo. Subir o piso continua sendo decisão consciente,
  acompanhada da medição que a justifica; está comentado no `pyproject.toml`.
- **Gate aplicado por `--cov-fail-under` no próprio job**, e não pelo upload ao
  Codecov, que tem `continue-on-error: true` e portanto **não é gate**. O
  `continue-on-error` foi mantido: o passo 4 da fase o autoriza explicitamente
  quando o upload não é confiável.
- **Autorização cruzada em ambos os caminhos.** A fase pede "ao menos um caso";
  há 5 — leitura e escrita, nos dois routers. É o tipo de defeito que cobertura
  numérica não pega e que num diário alimentar vazaria dado de saúde.
- **Nenhum router foi refatorado.** `push.py` continua falando direto com o ORM
  em vez de passar por um service; a inconsistência é conhecida e o escopo
  travado manda cobrir, não redesenhar.

**Achado durante a execução:** `GET /api/v1/push/vapid-public-key` **não exige
autenticação** — o service worker a busca antes do login. O teste que assumia
403 foi corrigido para documentar o comportamento real
(`test_e_publico_por_desenho`), em vez de o teste "corrigir" o código.

## 5. Comandos rodados + saídas reais

```text
$ pytest tests/integration/test_push.py tests/integration/test_reminders.py -q
36 passed, 1 warning in 18.91s

# medição da cobertura (passo 1 da fase)
$ pytest --ignore=tests/smoke_test.py --cov=app --cov-report=term -q
TOTAL                                      3191    894    72%
538 passed, 5 skipped, 4 warnings in 77.41s

# o gate ATIVO, sobre a suíte completa
$ pytest --ignore=tests/smoke_test.py --cov=app --cov-fail-under=70 -q
Required test coverage of 70% reached. Total coverage: 71.98%
538 passed, 5 skipped

# o gate REPROVANDO quando a cobertura cai (só a suíte unitária)
$ pytest tests/unit --cov=app --cov-fail-under=70 -q
TOTAL                                      3191   1143    64%
FAIL Required test coverage of 70% not reached. Total coverage: 64.18%

$ ruff check . && ruff format --check . && mypy app/ evals/
All checks passed! / 141 files already formatted / Success: no issues found
```

## 6. Checklist dos ACs / critério de conclusão

- [x] **AC-9, o CI falha quando a cobertura cai abaixo do piso** — demonstrado
      pelas duas execuções acima: 71,98% passa, 64,18% reprova com
      `FAIL Required test coverage of 70% not reached`.
- [x] **AC-9, ao menos um teste de integração por endpoint dos dois routers** —
      7 endpoints de `push.py` e 5 de `reminders.py`, todos exercitados; mais
      casos de 404, 422 e autorização cruzada.
- [x] **Cobertura real remedida e registrada** — 72% (a auditoria de maio media
      62%).
- [x] **Piso configurado com o valor medido arredondado para baixo** — 70%, com
      a justificativa da margem registrada em §4 e no `pyproject.toml`.
- [x] **Gate verificado no ambiente real do CI** — rodado dentro do container
      `backend`, com Postgres 16 e Redis dos mesmos serviços que o CI usa:
      `Required test coverage of 70% reached. Total coverage: 71.92%`,
      `542 passed, 5 skipped`. A execução no GitHub Actions em si depende de um
      push (ação do owner).

### Achado fora do escopo: o gate da NFR-6 está morto no CI

Durante a validação com Docker, os 5 testes de
`tests/integration/test_golden_set.py` **pularam**, com
`fonte curada 'taco' com apenas 0 linhas — rode 'make seed' antes deste gate`.
Isso vale também no CI, que não semeia. Ou seja: a NFR-6 ("os limiares de
`test_golden_set.py` não regridem") está **declarada e não verificada**.

Tentei corrigir com um `tests/integration/conftest.py` que semeia o banco
nutricional na sessão, e **reverti**: o `setup_test_database` monta o schema por
`Base.metadata.create_all()`, que cria tabelas mas **não** a função
`caloria_unaccent` nem as extensões, que vêm de migration. Com o seed, os 5
testes deixaram de pular e passaram a **falhar** com
`function caloria_unaccent(text) does not exist`. Fazer o gate funcionar exigiria
o schema de teste vir de `alembic upgrade head` em vez de `create_all` — mudança
estrutural em `tests/conftest.py` (arquivo da B.1) que nenhuma fase pede e que
eu não deveria fazer por conta.

**Medi a NFR-6 por fora, para não deixar a afirmação sem evidência**, contra um
banco criado por migrations e semeado só com a fonte curada `taco` — exatamente
o que o CI teria:

```text
$ python scripts/eval_golden_set.py            # banco caloria_ci, só TACO
Porção com âncora determinística: 27/29 (93.1%)    limiar ≥ 85%   OK
Erro médio absoluto de kcal:      0.0%             limiar ≤ 10%   OK
Dentro de ±10%:                   21/21 (100.0%)   limiar ≥ 80%   OK
Erro máximo:                      0.0%             limiar ≤ 100%  OK
```

**Os quatro limiares da NFR-6 passam com folga** — nada regrediu com C.1, C.2 ou
B.5. Mas o gate automático continua inerte, e isso merece fase própria.

## 7. Dúvidas para o avaliador

1. **Piso em 70% com 72% medido** — a margem de 2 pontos é justificada em §4.
   Aceitável, ou o piso deve ser exatamente 72?
2. O `continue-on-error: true` do upload ao Codecov foi **mantido**, com o gate
   aplicado localmente. É a leitura correta do passo 4 da fase?
3. Confirmação de que o CI de fato reprova precisa de um push — é do owner.
4. **O gate da NFR-6 está morto** (ver §6). Corrigi-lo exige o schema de teste
   vir de `alembic upgrade head` em vez de `create_all`. Abrir fase própria?

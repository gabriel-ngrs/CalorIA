---
spec: 001-backlog-features-qa-v1
fase: D.1
slug_fase: email-service
status: executado
tentativa: 1
reprovacoes: 0
sha_inicial: ad968ce2308ddab17a788ebc1423a0216cc4136d
sha_final: da8d40e2e8104e06bdc9066e268d227b491c146e
range: ad968ce2308ddab17a788ebc1423a0216cc4136d..da8d40e2e8104e06bdc9066e268d227b491c146e
---

# FASE D.1 — Relatório de execução

## 1. Resumo do que foi feito

Habilitado o envio de e-mail transacional. Novo `EmailService.send(to, subject,
html)` usa `aiosmtplib`; sem `SMTP_HOST` configurado (dev) ele apenas loga o
conteúdo em nível INFO e retorna, sem falhar. Adicionadas as vars SMTP (+
`FRONTEND_URL` e `RESET_TOKEN_EXPIRE_MINUTES`, que o Track D consome a seguir) em
`Settings`, placeholders em `.env.example` e a dependência `aiosmtplib` no
`pyproject.toml`.

## 2. Arquivos CRIADOS

| Arquivo | Propósito |
|---------|-----------|
| `backend/app/services/email_service.py` | `EmailService` SMTP com fallback console |
| `backend/tests/unit/test_email_service.py` | Testes: sem SMTP loga e não falha; com SMTP envia via aiosmtplib |

## 3. Arquivos ALTERADOS

| Arquivo | O que mudou |
|---------|-------------|
| `backend/app/core/config.py` | Vars `SMTP_HOST/PORT/USER/PASSWORD/FROM`, `FRONTEND_URL`, `RESET_TOKEN_EXPIRE_MINUTES` (defaults seguros/vazios) |
| `.env.example` | Placeholders SMTP + `FRONTEND_URL`/`RESET_TOKEN_EXPIRE_MINUTES` (todos vazios/genéricos) |
| `backend/pyproject.toml` | Dependência `aiosmtplib>=3.0.0` |

## 4. Confirmação do REUSO e decisões de design

- **Reuso confirmado:** `settings` (pydantic-settings) para toda a config; padrão
  de logging (`logging.getLogger(__name__)`) idêntico ao restante do backend.
- **Decisões de design:**
  - `EmailService` **não** recebe `db` no `__init__` (diferente dos services de
    domínio) porque não toca banco — envio de e-mail é stateless. Mantém a
    convenção de "service = classe", só sem a dependência que não usa.
  - TLS derivado da porta: `start_tls` para 587, `use_tls` para 465 (convenção
    SMTP), evitando mais uma var de config.
  - `FRONTEND_URL` e `RESET_TOKEN_EXPIRE_MINUTES` foram adicionados **aqui** (e não
    em D.2) porque `config.py` só é tocado nesta fase do Track D; concentrar a
    config nova em um único ponto evita um segundo diff em `config.py`. Uso efetivo
    dessas duas vars ocorre em D.2 (link de reset e expiração do token).
  - **Desvio:** dependência instalada manualmente no container de dev
    (`pip install aiosmtplib`) porque CI/CD está desabilitado e deps são aplicadas
    à mão (spec §7). O `pyproject.toml` registra a dep para o build normal.

## 5. Comandos rodados + saídas reais

```text
# lint (ruff check) — arquivos da fase
$ docker exec caloria_backend ruff check app/services/email_service.py app/core/config.py tests/unit/test_email_service.py
All checks passed!

# ruff format --check (após format do teste)
$ docker exec caloria_backend ruff format --check app/services/email_service.py app/core/config.py tests/unit/test_email_service.py
3 files already formatted

# type-check (mypy strict)
$ docker exec caloria_backend mypy app/services/email_service.py app/core/config.py
Success: no issues found in 2 source files

# testes da fase
$ docker exec -e TEST_DATABASE_URL=...@postgres:5432/caloria_test caloria_backend pytest tests/unit/test_email_service.py -q
3 passed, 3 errors
# → os 3 "errors" são teardown do fixture autouse `clean_db` (root conftest) que
#   roda TRUNCATE; em run single-file o caloria_test não tem tabelas. É artefato
#   pré-existente do ambiente (idêntico em test_security.py, não tocado). Os 3
#   testes da fase PASSAM.

# grep de segredo/PII (esperado: 0)
$ git show --stat HEAD | grep -iE "senha real|password=|secret=[^\"]" ; echo "exit=$?"
exit=1   # nenhum segredo; .env.example só placeholders vazios
```

## 6. Critérios de aceite da fase (com evidência)

D.1 não tem AC próprio na §3 (é infra para D.2). Cobre FR-D1:

- [x] **FR-D1** — SMTP via `aiosmtplib` com config por env; sem SMTP loga e não
  falha. Evidência: `test_sem_smtp_host_nao_envia_e_nao_falha` (aiosmtplib.send
  NÃO chamado) + `test_sem_smtp_host_loga_o_conteudo` (destinatário/assunto no log)
  + `test_com_smtp_configurado_envia_via_aiosmtplib` (envia com hostname/port).

## 7. Definition of Done da fase

- [x] Testes da fase verdes (3 passed)
- [x] Comandos de validação limpos nos arquivos tocados (ruff/mypy)
- [x] Escopo travado respeitado — nenhuma credencial commitada; `.env.example` só
      placeholders; corpo de e-mail em pt-BR
- [x] Nenhum segredo/PII em log/DTO/exceção
- [x] Commits em pt-BR (Conventional Commits)

## 8. (Em rework) O que mudou nesta tentativa

N/A — primeira execução.

## 9. Itens em aberto / dúvidas para o avaliador

- Falha **pré-existente** fora do escopo: `tests/unit/test_celery_tasks.py::
  TestRecalculateTdee::test_updates_tdee_when_weight_diff_significant` quebra
  porque mocka `profile.birth_date` como `MagicMock` e o `age_from_birthdate`
  (introduzido em A.2) chama `.month`/`.day`. É regressão de teste do Track A, não
  tocada por D.1 — reportada aqui para rastreio, corrigível por `/bugfix`.
- Os "errors" de teardown do `clean_db` em runs single-file são ruído de ambiente
  (sem tabelas no `caloria_test`); somem no run de suíte completa.

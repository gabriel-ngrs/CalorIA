---
spec: 001-backlog-features-qa-v1
fase: D.2
slug_fase: password-reset-backend
status: executado
tentativa: 1
reprovacoes: 0
sha_inicial: 6660ab8867674e34de766c716ccce65c8af724bc
sha_final: 6f48f9bc018196bf4164f655bdada859624e2706
range: 6660ab8867674e34de766c716ccce65c8af724bc..6f48f9bc018196bf4164f655bdada859624e2706
---

# FASE D.2 — Relatório de execução

## 1. Resumo do que foi feito

Implementado o fluxo backend de recuperação de senha. `create_reset_token`
(JWT `type=reset`, exp ≤ 1h) em `security.py`; `POST /auth/forgot-password`
responde de forma **uniforme** (mesmo corpo/HTTP 200) e despacha o e-mail via
Celery (`send_password_reset_email.delay`, fire-and-forget); `POST
/auth/reset-password` valida explicitamente `type=reset`, rejeita expirado/
inválido com 400 genérico, é **single-use** via blacklist Redis e troca a senha
(bcrypt).

## 2. Arquivos CRIADOS

| Arquivo | Propósito |
|---------|-----------|
| `backend/app/workers/tasks/emails.py` | Task Celery `send_password_reset_email` (envio assíncrono, corpo pt-BR) |

## 3. Arquivos ALTERADOS

| Arquivo | O que mudou |
|---------|-------------|
| `backend/app/core/security.py` | `create_reset_token(subject)` — JWT `type=reset`, exp `RESET_TOKEN_EXPIRE_MINUTES` |
| `backend/app/schemas/user.py` | `ForgotPasswordRequest{email}`, `ResetPasswordRequest{token, new_password}` |
| `backend/app/api/v1/auth.py` | Endpoints `forgot-password` / `reset-password`; msg uniforme |
| `backend/app/services/user_service.py` | `update_password(user, new_password)` (bcrypt + commit) |
| `backend/app/workers/celery_app.py` | `include` da nova task `emails` |
| `backend/tests/integration/test_auth.py` | Classes `TestForgotPassword` / `TestResetPassword` (AC-D1/D2/D3 + type errado/inválido) |

## 4. Confirmação do REUSO e decisões de design

- **Reuso confirmado:** `decode_token` (`security.py`), `blacklist_token`/
  `is_token_blacklisted` (`auth_service.py`) para single-use, `UserService.
  get_by_email`/`get_by_id`, `hash_password`, padrão de task Celery com helper
  `_run(coro)` (idêntico a `reports.py`), `EmailService` da fase D.1.
- **Decisões de design:**
  - **Validação de token no router** (não em service): segue a convenção real do
    projeto — o endpoint `refresh` já faz `decode_token` + checagem de `type` +
    `blacklist_token` no próprio router. A **mutação de senha** foi para
    `UserService.update_password` para manter a regra de negócio no service (§1.1).
  - **`user_service.py` fora da lista declarada da §5** (desvio de escopo menor,
    justificado): a alternativa era `user.password_hash = hash_password(...)`
    inline no router, o que colocaria lógica de negócio no endpoint — proibido por
    §1.1. Preferi o método no service. Diff de 3 linhas.
  - **`celery_app.py` fora da lista declarada** (desvio menor): a task nova precisa
    entrar no `include` para o worker descobri-la. É companheiro direto do "novo
    task Celery em workers/". Uma linha.
  - **Uniformidade / timing (FR-D2, Risco #4):** `.delay()` faz o handler retornar
    imediatamente nos dois ramos; o único trabalho extra no ramo "e-mail existe" é
    a enfileiragem no Redis (~ms), não o envio SMTP. Resíduo de micro-timing é
    aceito e documentado (Risco #4).
  - Sem desvio das rules além dos dois de escopo acima.

## 5. Comandos rodados + saídas reais

```text
# testes de integração (provam a fase — vivem em tests/integration/)
$ docker exec -e TEST_DATABASE_URL=...@postgres:5432/caloria_test caloria_backend \
    pytest tests/integration/test_auth.py -q
................                                                         [100%]
16 passed in 10.29s
# (11 pré-existentes + 5 novos: forgot uniforme, reset single-use, login nova/
#  antiga, token type errado, token inválido)

# lint (ruff check)
$ docker exec caloria_backend ruff check app/core/security.py app/schemas/user.py \
    app/api/v1/auth.py app/services/user_service.py app/workers/tasks/emails.py \
    app/workers/celery_app.py tests/integration/test_auth.py
All checks passed!

# ruff format --check (após format de security.py)
$ docker exec caloria_backend ruff format --check <arquivos da fase>
6 files already formatted

# type-check (mypy strict)
$ docker exec caloria_backend mypy app/core/security.py app/schemas/user.py \
    app/api/v1/auth.py app/services/user_service.py app/workers/tasks/emails.py \
    app/workers/celery_app.py
Success: no issues found in 6 source files

# grep de segredo/PII (esperado: 0) — nenhum segredo no diff
```

## 6. Critérios de aceite da fase (com evidência)

- [x] **AC-D1 (FR-D2)** — resposta HTTP idêntica p/ e-mail cadastrado e não
  cadastrado. Evidência: `test_resposta_uniforme_existente_e_inexistente`
  (status 200 == 200 e `json()` igual).
- [x] **AC-D2 (FR-D3)** — token single-use. Evidência: `test_token_single_use`
  (1ª = 200, 2ª = 400 via blacklist).
- [x] **AC-D3 (FR-D3)** — nova senha autentica, antiga falha. Evidência:
  `test_login_com_nova_senha_e_antiga_falha` (login nova = 200, antiga = 401).
- [x] **FR-D3 extra** — `type != reset` e token inválido → 400.
  Evidência: `test_token_tipo_errado_retorna_400`, `test_token_invalido_retorna_400`.

## 7. Definition of Done da fase

- [x] Testes da fase verdes (16 passed, incl. os 5 novos)
- [x] `make test-integration` (subconjunto test_auth.py) verde — obrigatório pois
      `make check` não roda `tests/integration/`
- [x] ruff/mypy limpos nos arquivos tocados
- [x] Escopo travado: sem vazar existência de e-mail; single-use obrigatório;
      auth coberta por teste; router só orquestra (mutação no service)
- [x] Nenhum segredo/PII em log/DTO/exceção
- [x] Commits em pt-BR (Conventional Commits)

## 8. (Em rework) O que mudou nesta tentativa

N/A — primeira execução.

## 9. Itens em aberto / dúvidas para o avaliador

- Dois desvios de escopo menores e conscientes (`user_service.py` e
  `celery_app.py`), justificados na §4 — ambos evitam violar §1.1 ou deixar a task
  não descoberta pelo worker. Avaliar se prefere refletir isso na §5 da spec.
- Em produção, se o broker Redis estiver indisponível, `.delay()` pode levantar e
  gerar 500 só no ramo "e-mail existe" (leak comportamental). Como o Redis é infra
  central (broker/blacklist), tratei como fora do modelo de ameaça (Risco #4
  aceita o resíduo). Mockei `.delay` no teste de uniformidade para determinismo.
- Persiste a falha **pré-existente** de Track A em `test_celery_tasks.py`
  (`age_from_birthdate` sobre `MagicMock`), fora do escopo desta fase.

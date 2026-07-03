---
spec: 001-backlog-features-qa-v1
fase: D.2
slug_fase: password-reset-backend
tentativa: 1
veredito: APROVADO
score: 9.6
threshold: 8.5
range_avaliado: 6660ab8867674e34de766c716ccce65c8af724bc..6f48f9bc018196bf4164f655bdada859624e2706
---

# FASE D.2 — Avaliação independente

## 1. Veredito e score

**Veredito:** APROVADO · **Score:** 9.6 / threshold 8.5

Fluxo backend de recuperação de senha (fase de **alto risco — auth**, §1.1 princípio
5). Verificado contra o código real: os 3 ACs (D1/D2/D3) mais rejeição de token
type-errado/inválido passam (16/16 em `tests/integration/test_auth.py`); lint/mypy
strict limpos. Resposta uniforme, token `type=reset`, single-use por blacklist e
troca bcrypt no service — todos confirmados no diff, não só no relatório.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 5 | `auth.py:108-155` forgot/reset; escopo travado honrado (uniforme; single-use; router só orquestra — mutação em `user_service.update_password`) |
| 2 | Arquitetura e direção de dependências | 3 | 5 | Router fino; validação de token no router **espelha o precedente `refresh`**; regra de negócio (senha) no service |
| 3 | Segurança / LGPD / multi-tenant | 3 | 4 | Blacklist checada antes do decode (`auth.py:130`); `type` explícito (`:137`); exp via `decode_token`; TTL da blacklist = vida restante do token (single-use robusto). Ressalvas em §5 |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | Reusa `decode_token`, `blacklist_token`/`is_token_blacklisted`, `get_by_email`/`get_by_id`, `hash_password`, helper `_run` (idêntico a `reports.py`), `EmailService` (D.1) |
| 5 | Padrões de domínio/aplicação | 2 | 5 | `create_reset_token` espelha `create_refresh_token` (`security.py:36-41`); schemas Pydantic com `EmailStr`/`Field(min_length=8)` |
| 6 | Local e nomes dos arquivos | 2 | 5 | `workers/tasks/emails.py` novo no lugar certo; demais alterações coerentes |
| 7 | Qualidade de código | 2 | 5 | Anotado, mypy strict limpo; comentários de "por quê" (uniformidade/timing) |
| 8 | Testes e cobertura | 2 | 5 | 5 testes novos: uniforme (AC-D1), single-use (AC-D2), nova/antiga senha (AC-D3), type errado, token inválido |
| 9 | Migration safety (se aplicável) | 2 | — | Não se aplica |

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

Nenhum.

## 5. Sugestões

- **Sessões vivas após reset** (`auth.py:152` / `user_service.py:56`): a troca de senha
  não invalida access/refresh tokens já emitidos — sessões antigas seguem válidas até
  expirarem. O spec (FR-D3) só exige invalidar o **token de reset**, então não é
  desvio; mas para um fluxo de auth (alto risco) é hardening recomendável: blacklistar
  os tokens ativos do usuário ou versionar o `password_hash`. Fora do escopo desta fase.
- **Leak comportamental se o broker cair** (`auth.py:117`): `send_password_reset_email.delay()`
  só é chamado no ramo `if user:`; com Redis indisponível o `.delay()` levantaria 500
  **apenas** para e-mails existentes, quebrando a uniformidade. O relatório reconhece e
  o Risco #4 aceita o resíduo (Redis é infra central). Envolver o `.delay()` em
  try/except fecharia o resíduo com 3 linhas.
- **Desvio de §5 (arquivos)**: `user_service.py` e `celery_app.py` não constam da lista
  "Arquivos alterados" de D.2. Ambos justificados (mover mutação para service honra
  §1.1; `include` da task é mecânico) e reportados. Refletir na §5 da spec para o
  file-list bater com a realidade.

## 6. Comandos rodados + saídas reais

```text
$ docker exec caloria_backend ruff check app/core/security.py app/schemas/user.py \
    app/api/v1/auth.py app/services/user_service.py app/workers/tasks/emails.py \
    app/workers/celery_app.py tests/integration/test_auth.py
All checks passed!

$ docker exec caloria_backend ruff format --check <8 arquivos D.1+D.2>
8 files already formatted

$ docker exec caloria_backend mypy <8 arquivos D.1+D.2>
Success: no issues found in 8 source files

$ docker exec -e TEST_DATABASE_URL=...@postgres:5432/caloria_test caloria_backend \
    pytest tests/integration/test_auth.py -q
16 passed in 10.53s   # 11 pré-existentes + 5 novos (D.2)

# Inspeção do single-use: auth_service.blacklist_token() grava setex com
# ttl = exp - now (== vida restante do token). Logo a entrada de blacklist cobre
# toda a validade do token de reset → reuso impossível na janela. Confirmado.
```

## 7. Itens da fase / DoD não atendidos

Nenhum. AC-D1/D2/D3 verdes em `tests/integration/` (gate obrigatório da NFR-5,
executado). Critério de conclusão da fase atendido.

## 8. Divergências entre o relatório e o código real

Nenhuma divergência material. Os dois desvios de escopo (`user_service.py`,
`celery_app.py`) foram declarados no relatório e conferem com o diff. A afirmação de
uniformidade de timing (`.delay()` fire-and-forget) e single-use por blacklist foi
verificada no código, não apenas aceita do relatório.

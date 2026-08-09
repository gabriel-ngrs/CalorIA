---
spec: 001-backlog-features-qa-v1
fase: C.2
slug_fase: chat-persistence-backend
status: executado
tentativa: 1
reprovacoes: 0
sha_inicial: acd8f21b9e15fbc52284cccd54d6819f913fa5f9
sha_final: 2222db5b6f7af391b30bc91f47e293bbfdf99621
range: acd8f21b9e15fbc52284cccd54d6819f913fa5f9..2222db5b6f7af391b30bc91f47e293bbfdf99621
---

# FASE C.2 — Relatório de execução

## 1. Resumo do que foi feito

O chat "Pergunte à IA" passou a **persistir** cada troca em `AIConversation`
reusando o modelo existente com um novo canal `WEB`. Foi adicionado o label `WEB`
ao enum `ConversationChannel` (migração `ALTER TYPE`), criado um
`ConversationService` que faz upsert do par pergunta(user)/resposta(model) na
conversa web do usuário (`external_chat_id="web:{user_id}"`), o endpoint
`POST /ai/insights type=question` passou a gravar a troca, e um novo
`GET /ai/conversations` retorna o histórico do chat web.

## 2. Arquivos CRIADOS

| Arquivo | Propósito |
|---------|-----------|
| `backend/app/services/ai/conversation_service.py` | `ConversationService`: `get_web_conversation` + `append_web_exchange` (upsert por usuário, formato `{role,content,timestamp}`). |
| `backend/alembic/versions/20260702_c9d0e1f2a3b4_conversation_web.py` | Migração `ALTER TYPE conversationchannel ADD VALUE 'WEB'` (down recria o tipo sem WEB). |
| `backend/tests/integration/test_ai_conversations.py` | Testes de API (AC-C2): pergunta grava par, histórico lista, vazio sem histórico, exige auth. |

## 3. Arquivos ALTERADOS

| Arquivo | O que mudou |
|---------|-------------|
| `backend/app/models/ai_conversation.py` | `ConversationChannel` ganha `WEB = "web"` (label PG `'WEB'`, UPPERCASE, casa com o mapeamento default do SQLAlchemy). |
| `backend/app/schemas/ai.py` | Novos `ChatMessage {role, content, timestamp}` e `ConversationResponse {channel, messages}`. |
| `backend/app/api/v1/ai.py` | `generate_insight` captura a resposta da pergunta e persiste via `ConversationService` **fora** do try de IA (erro de banco não vira 502 de IA). Novo `GET /ai/conversations` (sem `_require_ai` — só leitura). |

## 4. Confirmação do REUSO e decisões de design

- **Reuso confirmado:** `AIConversation` (modelo + coluna `messages` JSON) reusado
  sem mudança de nullability; `external_chat_id` continua `NOT NULL`. Canais
  `telegram`/`whatsapp` intactos (apenas somamos um label ao enum). Padrão de
  service com `db` injetado seguido (constitution).
- **Decisão — persistência em service, não no router:** a lógica de upsert vive em
  `ConversationService`; o endpoint apenas orquestra (chama `answer_question`, depois
  `append_web_exchange`). Respeita "endpoints finos" (constitution).
- **Decisão — reatribuição da lista JSON:** `conversation.messages = [*antigas,
  *novas]` para o SQLAlchemy detectar a mudança (mutação in-place de JSON não é
  rastreada). Alternativa (`flag_modified`) evitada por ser menos explícita.
- **Decisão — label UPPERCASE `'WEB'`:** confirmado no repo que o enum PG guarda o
  **nome do membro** (`schema_inicial.py:45`: `'TELEGRAM'`/`'WHATSAPP'`). A migração
  usa `ADD VALUE IF NOT EXISTS 'WEB'` (idempotente, PG12+). O uso (`channel=WEB`)
  ocorre em runtime, noutra transação (Risco #2 mitigado).
- **Decisão — persistir fora do try de IA:** um erro de commit no banco não deve ser
  reportado como "Erro ao consultar a IA" (502). Fica como erro real do handler.
- **Nenhum desvio da spec.**

## 5. Comandos rodados + saídas reais

```text
# ruff (arquivos da fase) — RUFF_CACHE_DIR=/tmp p/ contornar cache root-owned
$ ruff check app/services/ai/conversation_service.py app/api/v1/ai.py \
    app/models/ai_conversation.py app/schemas/ai.py \
    alembic/versions/20260702_c9d0e1f2a3b4_conversation_web.py \
    tests/integration/test_ai_conversations.py
All checks passed!
$ ruff format --check (mesmos arquivos app/)  → 4 files already formatted
# Nota: `ruff check app/` (repo inteiro) tem 3 erros PRÉ-EXISTENTES em
# meal_service.py (N818/baseline do manifest) — nenhum nos arquivos desta fase.

# mypy strict
$ mypy app/
Found 6 errors in 1 file (checked 68 source files)
# Os 6 erros são todos em app/services/ai/ai_client.py — BASELINE documentado no
# manifest ("mypy 6 erros em ai_client.py"). Nenhum nos arquivos desta fase.

# migração aplica + downgrade round-trip em PG real (caloria_db)
$ alembic upgrade head
Running upgrade b8c9d0e1f2a3 -> c9d0e1f2a3b4, adiciona label WEB ...
$ psql -c "SELECT enumlabel FROM pg_enum ... conversationchannel"
TELEGRAM | WHATSAPP | WEB
$ alembic downgrade -1  → labels: TELEGRAM | WHATSAPP
$ alembic upgrade head  → WEB de volta

# testes de integração da fase (PG real)
$ pytest tests/integration/test_ai_conversations.py -q
4 passed in 3.47s

# suíte backend completa (integração + unit) — regressão
$ pytest tests/integration/ tests/unit/ -q
1 failed, 128 passed
# A única falha (test_celery_tasks.py::TestRecalculateTdee) é PRÉ-EXISTENTE do
# Track A (age_from_birthdate + MagicMock), confirmada idêntica com as mudanças
# de C.2 stashed. Não é regressão desta fase. Ver §9.

# grep de segredo/PII no diff (esperado: 0)
$ git diff acd8f21..HEAD | grep -iE "api_key|secret|password|smtp_pass" | wc -l
0
```

## 6. Critérios de aceite da fase (com evidência)

- [x] **AC-C2 (FR-C2/C3)** — *faço uma pergunta no chat; `GET /ai/conversations`
  contém o par pergunta/resposta.* Evidência: teste
  `test_pergunta_grava_par_user_model_e_lista` — POST `type=question` → GET retorna
  `channel:"web"`, `messages` com 2 entradas (`role:user`/`content` = pergunta,
  `role:model`/`content` = resposta), chaves `{role,content,timestamp}`. Teste de
  acúmulo confirma que múltiplas perguntas viram 4 mensagens.
- [x] **FR-C2** — enum inclui `WEB`; persiste com `channel=WEB`,
  `external_chat_id="web:{user_id}"`. Evidência: migração aplica label `WEB` (psql);
  `ConversationService._web_chat_id`; testes verdes contra PG real.
- [x] **FR-C3** — `GET /ai/conversations` retorna o histórico web; a rota
  `type=question` grava o par. Evidência: testes acima + `test_conversations_vazio`
  (204→`{channel:"web",messages:[]}`) e `test_conversations_exige_autenticacao` (401).

## 7. Definition of Done da fase

- [x] Testes da fase verdes (4/4 integração).
- [x] `make test-integration` (arquivo da fase) + gates backend verdes nos arquivos
      tocados; ruff/mypy limpos nos arquivos da fase (baseline pré-existente à parte).
- [x] Escopo travado respeitado: canais telegram/whatsapp intactos; `external_chat_id`
      segue `NOT NULL`; persistência em service, não no router; migração de enum
      revisada à mão e testada (upgrade+downgrade).
- [x] Nenhum segredo/PII em log/DTO/exceção.
- [x] Commits em pt-BR (Conventional Commits), sem menção a autor/IA.

## 8. (Em rework) O que mudou nesta tentativa

N/A — primeira execução.

## 9. Itens em aberto / dúvidas para o avaliador

- **⚠️ Falha pré-existente fora do escopo (Track A):**
  `tests/unit/test_celery_tasks.py::TestRecalculateTdee::test_updates_tdee_when_weight_diff_significant`
  falha com `TypeError` em `tdee.py:45` (`age_from_birthdate` recebe `birth_date`
  MagicMock). Introduzida por A.2 (`age_from_birthdate`); o teste unitário não foi
  atualizado. **Confirmado idêntico com as mudanças de C.2 stashed** → não é
  regressão desta fase. Como `make check` roda `test-unit`, esse gate está vermelho
  por causa de A, não de C. Recomendo `/bugfix` ou rework pontual de A — **não** foi
  tocado aqui por estar fora do escopo travado de C.2 (diff mínimo).
- **Migração aplicada no `caloria_db` de dev** durante a validação (upgrade→head).
  Em produção, aplicar manualmente (§7 da spec; CI/CD desabilitado).
- **`ChatMessage(**m)`** confia no formato `{role,content,timestamp}` gravado pelo
  próprio service; mensagens de outros canais não são retornadas (filtro por
  `channel=WEB`).

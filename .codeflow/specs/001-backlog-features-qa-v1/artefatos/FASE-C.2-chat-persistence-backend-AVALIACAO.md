---
spec: 001-backlog-features-qa-v1
fase: C.2
slug_fase: chat-persistence-backend
tentativa: 1
veredito: APROVADO
score: 9.5
threshold: 8.5
range_avaliado: acd8f21b9e15fbc52284cccd54d6819f913fa5f9..2222db5b6f7af391b30bc91f47e293bbfdf99621
---

# FASE C.2 — Avaliação independente

## 1. Veredito e score

**Veredito:** APROVADO · **Score:** 9.5 / threshold 8.5

Persistência do chat web em `AIConversation` com novo canal `WEB`: enum + migração
`ALTER TYPE`, `ConversationService` (upsert por usuário), gravação do par em
`type=question` e `GET /ai/conversations`. AC-C2/FR-C2/FR-C3 cobertos por 4 testes
de integração em PG real (verifiquei: 4 passed). Ownership por `user_id`, endpoint
fino, migração idempotente com downgrade. Zero bloqueantes/importantes; uma
sugestão de formatação (ver §5).

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 5 | `ai_conversation.py:21` `WEB="web"`; `conversation_service.py:36-62` upsert; `ai.py:115-142` grava no `type=question` + `GET /conversations`. Canais telegram/whatsapp intactos; `external_chat_id` segue `NOT NULL`. AC-C2 verde. |
| 2 | Arquitetura e direção de dependências | 3 | 5 | Lógica em `ConversationService(db)` (constitution — service com `db` injetado); router só orquestra. Persistência **fora** do `try` de IA (`ai.py:122-125`) evita mascarar erro de banco como 502. |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | `get_web_conversation` filtra por `user_id` **e** `external_chat_id="web:{user_id}"` (`conversation_service.py:33-40`); `GET /conversations` autenticado (`Depends(get_current_user_id)`); `test_conversations_exige_autenticacao` → 401. Sem vazamento de chave. |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | Reusa `AIConversation`+coluna `messages` JSON sem mudar nullability (OQ5); `ChatMessage`/`ConversationResponse` espelham o formato `{role,content,timestamp}` do modelo. |
| 5 | Padrões de domínio/aplicação | 2 | 5 | `StrEnum`; reatribuição da lista JSON (`messages=[*antigas,*novas]`) para o SQLAlchemy detectar a mudança — comentado o porquê. |
| 6 | Local e nomes dos arquivos | 2 | 5 | `services/ai/conversation_service.py` (novo), migração em `alembic/versions/`, teste em `tests/integration/` — todos onde a fase declarou. |
| 7 | Qualidade de código | 2 | 4 | `ruff check` e `mypy` limpos nos arquivos da fase. Porém `tests/integration/test_ai_conversations.py` falha `ruff format --check` (1 assinatura quebrada em linha única) — ver §5/§8. |
| 8 | Testes e cobertura | 2 | 5 | 4 testes de integração: grava par user/model, acúmulo (4 msgs), vazio (`{channel:web,messages:[]}`), exige auth. Rodados por mim em PG real: `4 passed in 3.45s`. |
| 9 | Migration safety (se aplicável) | 2 | 5 | `ADD VALUE IF NOT EXISTS 'WEB'` (idempotente, PG12+); label UPPERCASE casa com o nome do membro (convenção `schema_inicial.py:45`); downgrade recria o tipo e faz cast, com nota de que falha se houver linhas `WEB`. Round-trip validado pelo executor. |

Média ponderada (peso total 22) = 108/22 = 4.909 → **9.5/10** (código-quality 4
pela lacuna de `ruff format`).

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

Nenhum.

## 5. Sugestões

1. **`ruff format` no teste da fase** (`tests/integration/test_ai_conversations.py:68`):
   `ruff format --check` reformataria a assinatura de `test_conversations_vazio_sem_historico`
   para linha única. Correção trivial: `ruff format tests/integration/test_ai_conversations.py`
   e recommit. **Contexto que impede escalar isto:** o gate de CI real do projeto é
   `ruff check .` (que os arquivos da fase **passam**), não `ruff format --check .`;
   e `ruff format --check .` já está vermelho no baseline por **10 arquivos
   pré-existentes** (`ai_client.py`, `scripts/*`, `conftest.py`, `smoke_test.py`).
   Logo, o arquivo desta fase soma a uma dívida pré-existente num gate local não
   enforced — sugestão, não bloqueio.
2. **Persistência fora do `try` de IA** (`ai.py:122-125`): decisão correta para não
   mascarar erro de banco como 502, mas se `append_web_exchange` falhar após a IA já
   ter respondido, o usuário recebe 500 e perde a resposta (quota Groq gasta).
   Opcional: envolver a persistência de modo que uma falha de banco não descarte a
   resposta já gerada (log + retorno da resposta). Tradeoff aceitável como está.

## 6. Comandos rodados + saídas reais

```text
# ruff nos arquivos da fase (dentro do container caloria_backend)
$ ruff check app/services/ai/conversation_service.py app/api/v1/ai.py \
    app/models/ai_conversation.py app/schemas/ai.py \
    alembic/versions/20260702_c9d0e1f2a3b4_conversation_web.py \
    tests/integration/test_ai_conversations.py
All checks passed!

$ ruff format --check (arquivos da fase)
Would reformat: tests/integration/test_ai_conversations.py
1 file would be reformatted, 4 files already formatted
# (repo inteiro: 11 arquivos, sendo 10 PRÉ-EXISTENTES — baseline)

$ mypy app/
Found 6 errors in 1 file (checked 68 source files)
# Os 6 são em app/services/ai/ai_client.py — BASELINE do manifest. Nenhum nos
# arquivos desta fase.

# testes de integração (PG real: caloria_test via host `postgres`)
$ TEST_DATABASE_URL=postgresql+asyncpg://caloria:caloria@postgres:5432/caloria_test \
  pytest tests/integration/test_ai_conversations.py -q
....                                                     [100%]
4 passed in 3.45s
```

## 7. Itens da fase / DoD não atendidos

- **`ruff format --check .` limpo (NFR-1):** não atendido para o arquivo de teste da
  fase — porém o gate já estava vermelho no baseline (10 arquivos) e não é o gate de
  CI (`ruff check .`). Registrado como sugestão.
- **`make check` verde (DoD transversal §9):** globalmente vermelho, mas **por causa
  do Track A** (`tests/unit/test_celery_tasks.py::TestRecalculateTdee`, `TypeError`
  em `tdee.py:45` com `birth_date` MagicMock) — confirmei que independe de C.2. Fora
  do escopo travado desta fase.

## 8. Divergências entre o relatório e o código real

- **Format-check declarado como limpo, mas restrito a `app/`** (EXECUCAO §5:
  "ruff format --check (mesmos arquivos app/) → 4 files already formatted"): o
  relatório foi transparente que checou só os arquivos `app/`, mas isso omitiu que o
  arquivo de teste (`tests/integration/…`) **não** está formatado. A afirmação não é
  falsa, mas passa impressão de format-cleanliness total. Divergência menor.
- Todo o restante do EXECUCAO confere com `git diff acd8f21..2222db5` e com a
  execução real dos testes/migração.

# Achados da Auditoria

Lista de problemas encontrados, ordenada por ID. Para visão por severidade ver `relatorio-preliminar.md` ao fim da auditoria.

**Status totais:** críticos: 1 · altos: 4 · médios: 9 · baixos: 4 (atualizar a cada novo achado)

---

### AUD-001 — `push.py` executa SQL diretamente no router (sem service)

- **Severidade:** 🟡 média
- **Frente:** A
- **Arquivo:linha:** `backend/app/api/v1/push.py:80–199` (6 queries em 6 endpoints)
- **Descrição:** Os endpoints de subscriptions Web Push e de notificações in-app fazem `select`/`update`/`delete` diretamente no handler do router, contrariando a convenção do projeto registrada em `CLAUDE.md` ("Nunca colocar lógica de negócio nos endpoints — usar services"). O resto do backend segue o padrão (ex.: `reminders.py:71` chama `ReminderService(db).delete(...)`).
- **Evidência:** `artefatos/A1-queries-em-routers.txt`. Endpoints afetados: `subscribe_push`, `unsubscribe_push`, `list_notifications`, `unread_count`, `mark_notification_read`, `mark_all_read`. Já existe um `PushService` no projeto (usado para envio), mas ele não cobre subscriptions/notificações CRUD.
- **Recomendação:** Estender `PushService` (ou criar `NotificationService`) com métodos `upsert_subscription`, `unsubscribe_by_endpoint`, `list_notifications`, `count_unread`, `mark_read`, `mark_all_read`. O router só orquestra request → service → response.
- **Esforço:** M (1–4h)
- **Origem:** PASSO 2.1

### AUD-002 — `InsightsGenerator` concentra 7 responsabilidades distintas em 512 LOC

- **Severidade:** 🟡 média
- **Frente:** A
- **Arquivo:linha:** `backend/app/services/ai/insights_generator.py:1–512`
- **Descrição:** A classe `InsightsGenerator` agrupa 7 métodos públicos heterogêneos (`daily_insight`, `weekly_insight`, `answer_question`, `suggest_meal`, `nutritional_alerts`, `goal_adjustment_suggestion`, `monthly_report`). O arquivo passou do limite informal do plano (>300 LOC + >4 responsabilidades), e o radon já o sinaliza como segundo hotspot de complexidade ciclomática (médio CC 16.55 do projeto inflado em parte por este arquivo: `goal_adjustment_suggestion` C(18), `monthly_report` C(14), `nutritional_alerts` C(13), `suggest_meal` C(11)).
- **Evidência:** `artefatos/baseline-radon-cc.txt` + extração AST documentada em `01-arquitetura.md § A.4`.
- **Recomendação:** Quebrar em 3 services menores agrupados por finalidade: (1) `PeriodicInsightsService` — `daily_insight`/`weekly_insight`/`monthly_report`; (2) `RecommendationsService` — `suggest_meal`/`nutritional_alerts`/`goal_adjustment_suggestion`; (3) `QuestionAnsweringService` — `answer_question`. Manter o arquivo atual como facade temporária para retrocompatibilidade se necessário.
- **Esforço:** L (> 4h)
- **Origem:** PASSO 2.4

### AUD-003 — Endpoints `push.py` sem `response_model` retornam dict cru

- **Severidade:** 🟡 média
- **Frente:** B
- **Arquivo:linha:** `backend/app/api/v1/push.py:73` (`POST /push/subscribe`) e `backend/app/api/v1/push.py:187` (`POST /notifications/read-all`)
- **Descrição:** Os dois únicos endpoints do projeto sem `response_model` retornam `dict[str, str]`. Sem schema, o OpenAPI/Swagger fica menos preciso, há risco de mudança silenciosa do payload e a tipagem do cliente fica frouxa. Os outros 45 endpoints declaram schema ou usam `204 NO_CONTENT`.
- **Evidência:** `artefatos/B1-routers-response.txt`. Cobertura de `response_model`: 96%.
- **Recomendação:** Criar `SubscribePushResponse(BaseModel)` (ou usar status 204 NO_CONTENT, já que o payload `{"status": "subscribed"}` não acrescenta info útil) e `MarkAllReadResponse(BaseModel)` com campo `marked: int` (contagem). Aplicar `response_model=...`.
- **Esforço:** S (< 1h)
- **Origem:** PASSO 3.1

### AUD-004 — `meals.py:101` re-eleva HTTPException sem `from None`

- **Severidade:** 🟢 baixa
- **Frente:** B
- **Arquivo:linha:** `backend/app/api/v1/meals.py:101`
- **Descrição:** Dentro de `except MealItemNotFound:`, faz `raise HTTPException(404, ...)` sem `from None`/`from exc`. Resultado: a chain do Python (`__context__`) anexa o trace interno; se o handler genérico de erro estiver verboso, expõe rastreamento. Os outros 8 casos análogos em `ai.py` já usam `from exc`.
- **Evidência:** `artefatos/B2-httpexc.txt`. 1/9 violadores no projeto.
- **Recomendação:** Trocar para `raise HTTPException(...) from None` (preferir `from None` para 404 estável; usar `from exc` quando o original ajuda diagnóstico, ex.: 502 upstream).
- **Esforço:** S (< 1h)
- **Origem:** PASSO 3.2

### AUD-005 — Paginação `weight.py` permite `limit` até 200, divergente do padrão 100

- **Severidade:** 🟢 baixa
- **Frente:** B
- **Arquivo:linha:** `backend/app/api/v1/weight.py:16`
- **Descrição:** O endpoint `GET /weight` aceita `limit: int = Query(default=50, ge=1, le=200)`, único endpoint com `le=200`. Os outros listings paginados (`/meals`, `/mood`, `/notifications`) usam `le=100`. Sem justificativa documentada, fica difícil revisar/manter coerência futura e abre precedente para limites arbitrários.
- **Evidência:** `artefatos/B3-paginacao.txt`.
- **Recomendação:** Padronizar em `le=100` (suficiente para grafiar histórico de peso anual com paginação) ou centralizar o limite numa constante (`MAX_PAGE_SIZE = 100`). Documentar exceção se `le=200` for intencional.
- **Esforço:** S (< 1h)
- **Origem:** PASSO 3.3

### AUD-006 — `food_lookup` faz N queries SQL no caminho síncrono do usuário

- **Severidade:** 🟠 alta
- **Frente:** B
- **Arquivo:linha:** `backend/app/services/ai/food_lookup.py:89` (loop `for candidate in candidates`)
- **Descrição:** Para cada n-grama candidato extraído do texto da refeição, executa uma query `SELECT … FROM foods …` com `pg_trgm`. Em uma refeição típica de 10 palavras, `_extract_candidates` produz ~25 n-gramas (n=2..4). Resultado: cada análise de refeição faz ~25 round-trips ao Postgres no caminho síncrono do request HTTP. Mesmo com índice GIN, latência cumulativa fica perceptível e degrada sob carga.
- **Evidência:** `artefatos/B4-n-mais-1.txt`. Função alvo da maior parte do tempo do endpoint `POST /meals` (criação por texto).
- **Recomendação:** Bater todos os candidatos numa única query: `WHERE search_text %>> ANY(:array)` ou `WHERE search_text % :q1 OR search_text % :q2 OR …`. Alternativa estrutural: tsvector pré-calculado + `ts_rank_cd`. Validar com `EXPLAIN ANALYZE` (artefato `C3-food-lookup-explain.txt` será gerado no PASSO 4.3).
- **Esforço:** M (1–4h)
- **Origem:** PASSO 3.4

### AUD-007 — `InsightsGenerator` chama `get_daily_summary` em loop

- **Severidade:** 🟠 alta
- **Frente:** B
- **Arquivo:linha:** `backend/app/services/ai/insights_generator.py:193` (`nutritional_alerts`) e `backend/app/services/ai/insights_generator.py:368` (`monthly_report`)
- **Descrição:** `for i in range(days)` / `for day_num in range(days_in_month)` chamando `MealService.get_daily_summary(user_id, d)`. Cada chamada gera 1 query — 14 queries (default `nutritional_alerts`) e até 31 (`monthly_report`). Padrão N+1 clássico, redundante porque já existe `MealService.get_macros_by_date_range` (introduzido para resolver caso análogo em `DashboardService.get_today`).
- **Evidência:** `artefatos/B4-n-mais-1.txt`. Ambos endpoints expostos por `/ai/*`.
- **Recomendação:** Substituir o loop por `await meal_service.get_macros_by_date_range(user_id, start_date, end_date)` e iterar o dict resultante em memória. Reuso do método já existente.
- **Esforço:** S (< 1h)
- **Origem:** PASSO 3.4

### AUD-008 — Workers iteram usuários ativos com 1 query DB por usuário

- **Severidade:** 🟠 alta
- **Frente:** B / E
- **Arquivo:linha:** `backend/app/workers/tasks/reminders.py:172` (hidratação) e `backend/app/workers/tasks/maintenance.py:87` (reconciliação peso)
- **Descrição:** `for user in users:` seguido de `await db.execute(...)` por usuário. Custo cresce linear com base de usuários: para 1000 usuários ativos, são 1000 queries por execução (cron horário em reminders, diário em maintenance).
- **Evidência:** `artefatos/B4-n-mais-1.txt`.
- **Recomendação:** Reescrever como query agregada: `SELECT user_id, SUM(amount_ml) FROM hydration_logs WHERE date = :today GROUP BY user_id` (hidratação) e `SELECT DISTINCT ON (user_id) user_id, weight_kg FROM weight_logs ORDER BY user_id, date DESC, created_at DESC` (último peso por usuário). Resultado em memória decide quem precisa de notificação/atualização.
- **Esforço:** M (1–4h)
- **Origem:** PASSO 3.4

### AUD-009 — `PhotoAnalysisRequest.image_base64` sem `max_length` (DoS)

- **Severidade:** 🟠 alta
- **Frente:** B / G
- **Arquivo:linha:** `backend/app/schemas/ai.py:38` (`image_base64: str = Field(description="Imagem em base64 (JPEG ou PNG)")`)
- **Descrição:** O endpoint `POST /ai/analyze-photo` aceita base64 sem qualquer limite. Um cliente malicioso pode enviar payloads de centenas de MB no body, consumir memória do worker uvicorn (parsing JSON + decode base64) e bloquear o processo. Em produção atrás do Caddy o reverse proxy deve limitar, mas a defesa em profundidade falha aqui no Pydantic.
- **Evidência:** schema sem `max_length` nem `StringConstraints`.
- **Recomendação:** Aplicar `max_length=10_000_000` (~7.5MB de imagem original) — equilíbrio entre foto típica de smartphone (3-5MB) e proteção. Validar `mime_type` em `Literal["image/jpeg", "image/png", "image/webp"]`. Idealmente migrar para `multipart/form-data` com `UploadFile` (limites nativos no FastAPI).
- **Esforço:** S para `max_length`; M para refactor de upload
- **Origem:** PASSO 3.6

### AUD-010 — Múltiplos campos texto livre sem `max_length`

- **Severidade:** 🟡 média
- **Frente:** B
- **Arquivo:linha:** `backend/app/schemas/ai.py:45` (`InsightRequest.question`); `backend/app/schemas/meal.py:9,52,60` (`MealItemCreate.raw_input`, `MealCreate.notes`, `MealUpdate.notes`); `backend/app/schemas/logs.py:13,64` (`WeightLogCreate.notes`, `MoodLogCreate.notes`); `backend/app/schemas/reminder.py:56,73` (`ReminderCreate.message`, `ReminderUpdate.message`).
- **Descrição:** 8 campos textuais aceitam `str | None` sem limite. Permite abuso de storage (megabytes em `notes`), inflar prompts da IA (custo direto em tokens via `InsightRequest.question`) e cargar mensagens muito longas em notificações Web Push (`ReminderCreate.message`).
- **Evidência:** `grep -nE "notes|message" backend/app/schemas/*.py`.
- **Recomendação:** Adicionar `max_length` por campo (sugestão: `notes` 1000, `question` 500, `raw_input` 2000, `message` 200). Considerar helper `ShortText = Annotated[str, StringConstraints(max_length=200)]` para reaproveitar.
- **Esforço:** S (< 1h)
- **Origem:** PASSO 3.6

### AUD-011 — 15 `# type: ignore` elimináveis com tipagem adequada

- **Severidade:** 🟢 baixa
- **Frente:** B / I
- **Arquivo:linha:** 12× `[arg-type]` em `backend/app/services/ai/meal_parser.py:236-241` e `backend/app/services/ai/vision_parser.py:235-240`; 1× `[return-value]` em `backend/app/services/meal_service.py:45`; 1× `[no-any-return]` em `backend/app/services/ai/utils.py:15`; 1× `[type-arg]` em `backend/app/services/ai/utils.py:18`.
- **Descrição:** Dos 22 `# type: ignore` no backend, 7 são justificáveis (libs sem stubs: `@celery_app.task` decorator, `aioredis.from_url`). Os outros 15 podem ser eliminados com tipagem correta. Os 12 do parser vêm do padrão `float(d.get("calories", 0))` onde `d: dict[str, Any]` (resultado bruto de `json.loads` do output da IA). Solução estrutural: definir `TypedDict` para a forma esperada e validar com `isinstance` ou `cast`, ou reusar o próprio `ParsedFoodItem` Pydantic para parsing+coerção.
- **Evidência:** `artefatos/B7-type-ignores.txt`.
- **Recomendação:** (1) Criar `class _RawAIItem(TypedDict, total=False)` em `meal_parser.py`/`vision_parser.py`. (2) `utils.py:15` — usar `cast(JSON, json.loads(...))` ou `Any`. (3) `utils.py:18` — anotar `list[ParsedFoodItem]`. (4) `meal_service.py:45` — substituir por `return list(result.scalars().all())`. Reduz `mypy --strict` errors também (relacionado ao baseline de 6 erros já capturado).
- **Esforço:** M (1–4h)
- **Origem:** PASSO 3.7

### AUD-012 — `AIClient` retry frágil e potencialmente bloqueante demais

- **Severidade:** 🟡 média
- **Frente:** C
- **Arquivo:linha:** `backend/app/services/ai/ai_client.py:84,117`
- **Descrição:** A condição de retry é `if "429" in str(exc)`, dependente da formatação string do exception. Se a SDK Groq mudar a representação textual do erro, o retry para de funcionar silenciosamente. Além disso, o backoff é 15s → 30s → 60s → 120s, totalizando até **225s** numa única request síncrona. Sem timeout global no uvicorn (`Dockerfile` usa defaults) e Caddy com `reverse_proxy` pode cortar antes — o cliente vê erro intermediário, mas o backend continua bloqueando o worker.
- **Evidência:** trecho fonte do arquivo. `Dockerfile` confirma `uvicorn ... --workers 2` sem flags de timeout.
- **Recomendação:** Filtrar por classe específica: `except groq.RateLimitError as exc:` (ou `httpx.HTTPStatusError` com `.response.status_code == 429`). Reduzir tentativas para 3 e cap total ≤ 60s (15s/30s) — para 429 do Groq, é melhor falhar rápido e o cliente reagir do que segurar worker. Quando precisar de retry mais longo, mover para tarefa Celery.
- **Esforço:** S (< 1h)
- **Origem:** PASSO 4.1

### AUD-013 — Logs de tokens da IA sem dimensão para agregação

- **Severidade:** 🟡 média
- **Frente:** C / J
- **Arquivo:linha:** `backend/app/services/ai/ai_client.py:110-114`
- **Descrição:** `logger.info("Groq tokens — entrada: %d, saída: %d", ...)` registra contagem mas não tem campos para correlacionar com usuário, request, modelo ou endpoint. Impossível responder "qual usuário consumiu mais tokens em maio?" ou "endpoint mais caro" sem reprocessar logs com regex. Custo Groq é zero hoje (free tier), mas com escala e migração para tier pago a cegueira aumenta.
- **Evidência:** trecho fonte.
- **Recomendação:** Receber `request_id`/`user_id` por contextvar (ou parâmetro opcional) e logar como structured log: `logger.info("ai.call", extra={"model": model, "prompt_tokens": ..., "completion_tokens": ..., "user_id": ..., "endpoint": ...})`. Considerar persistir em tabela `ai_calls` (já existe `AIConversation` parecida) para queries.
- **Esforço:** M (1–4h)
- **Origem:** PASSO 4.1

### AUD-014 — `aioredis.from_url` por chamada (sem pool persistente)

- **Severidade:** 🟢 baixa
- **Frente:** C
- **Arquivo:linha:** `backend/app/services/ai/ai_client.py:135,143` (`_get_cached`, `_set_cached`)
- **Descrição:** Cada operação de cache abre uma conexão Redis nova com `async with aioredis.from_url(...)` e fecha ao sair do bloco. Tem custo de handshake TCP adicional por chamada e pode esgotar sockets sob carga.
- **Evidência:** trecho fonte.
- **Recomendação:** Manter um `redis.asyncio.Redis` singleton (ou `ConnectionPool`) inicializado no startup e injetado nos métodos. Para tarefas Celery, usar pool por processo. Reuso reduz latência típica em 2-5ms por operação.
- **Esforço:** S (< 1h)
- **Origem:** PASSO 4.1

### AUD-015 — `MealParser` e `VisionParser` duplicam `_lookup_and_fill` + `_estimate_macros_batch`

- **Severidade:** 🟡 média
- **Frente:** C
- **Arquivo:linha:** `backend/app/services/ai/meal_parser.py` e `backend/app/services/ai/vision_parser.py` (≈120 LOC duplicadas)
- **Descrição:** Os dois parsers têm `_lookup_and_fill` (~85 linhas, funcionalmente equivalente) e `_estimate_macros_batch` (37 linhas, 100% idêntico exceto uma palavra na docstring). A divergência legítima está só em `_identify_foods` (texto vs imagem) e nos entry points (`parse` vs `parse_base64`). Duplicação aumenta custo de manutenção (toda mudança em sanity check, threshold ou parsing precisa replicar) e risco de divergência silenciosa entre os fluxos.
- **Evidência:** `artefatos/C2-parsers-diff.txt` + análise método-a-método; 147 linhas diferem entre 553 totais (~27%, mas quase tudo concentrado nos métodos legitimamente diferentes).
- **Recomendação:** Extrair `BaseAIFoodParser(ABC)` em `services/ai/base_parser.py` com `_lookup_and_fill` e `_estimate_macros_batch` concretos + `_identify_foods` abstrato. `MealParser`/`VisionParser` herdam e implementam apenas `_identify_foods` e o entry point.
- **Esforço:** M (1–4h)
- **Origem:** PASSO 4.2

### AUD-016 — `food_lookup` faz Seq Scan no caminho síncrono do usuário (índice GIN ignorado)

- **Severidade:** 🔴 crítica
- **Frente:** C / F
- **Arquivo:linha:** `backend/app/services/ai/food_lookup.py:90-104` (query SQL com `WHERE search_text %>> :q OR similarity(search_text, :q) >= :min_score`)
- **Descrição:** O `OR similarity() >= 0.18` adicionado como fallback de baixa-confiança torna a cláusula `WHERE` não-indexável. O planner do Postgres descarta o índice GIN `ix_foods_search_trgm` em **toda** a query (não consegue particionar o OR) e cai em Seq Scan da tabela inteira (~42.000 registros). Medido com `EXPLAIN ANALYZE` em ambiente real (caloria_db, 42103 alimentos):
    - Query atual (com OR): **585 ms**
    - Só `%>> :q`: **8 ms** (Bitmap Index Scan)
    - Só `similarity() >= X`: 249 ms (Seq Scan)

  Combinado com AUD-006 (~25 n-gramas por refeição em loop sequencial), uma análise de refeição típica gasta **~14.6 segundos** apenas em food lookup, bloqueando o worker uvicorn. Com 2 workers (configuração default) e 2 usuários simultâneos analisando refeições, o backend fica indisponível por ~15s.
- **Evidência:** `artefatos/C3-food-lookup-explain.txt` (3 EXPLAIN ANALYZE comparativos + lista de índices). Reproduzível em qualquer ambiente com `caloria_db` populado.
- **Recomendação (rápida)**: Substituir o OR por `SET LOCAL pg_trgm.similarity_threshold = 0.18` na sessão (ou via `ALTER USER caloria SET pg_trgm.similarity_threshold = 0.18`) e usar apenas `WHERE search_text %>> :q`. O `%>>` respeita o threshold dinâmico e mantém o índice — performance 70× melhor sem perder recall. **Recomendação estrutural**: combinar com AUD-006 (batch query única para todos os candidatos) para chegar a ~10ms total. Considerar migrar para `tsvector` + `ts_rank_cd` numa fase posterior.
- **Esforço:** S (< 1h) para o fix imediato; M para batch + threshold; L para migração FTS.
- **Origem:** PASSO 4.3

### AUD-017 — `extract_json_from_ai_response` frágil em casos comuns

- **Severidade:** 🟡 média
- **Frente:** C
- **Arquivo:linha:** `backend/app/services/ai/utils.py:10-15`
- **Descrição:** A função apenas remove fences ` ``` ` e chama `json.loads`. Falha em três cenários comuns de saída de LLM:
  1. **Texto antes/depois do JSON** ("Aqui está: [...]" ou "[...] espero que ajude") → `JSONDecodeError`. LLMs com `temperature > 0.1` ou modelos menores tendem a ser conversacionais.
  2. **Dict wrapper** (`{"items": [...]}`) é parseado mas retornado como `dict` enquanto o type hint promete `list[dict]` — o caller que itera com `for x in result:` percorre as chaves do dict silenciosamente, gerando bugs sem traceback.
  3. **Trailing commas** (`[{"a":1,}]`) — JSON estrito não aceita, mas modelos muitas vezes geram.
- **Evidência:** script Python sintético (executar `python3 -c "from app.services.ai.utils import extract_json_from_ai_response; print(extract_json_from_ai_response('Aqui: [{\"a\":1}]'))"` falha).
- **Recomendação:** Reescrever com 3 etapas: (a) extrair conteúdo do `json` fence se presente; (b) regex isolar primeiro `[…]` ou `{…}`; (c) se for dict, procurar chave `items|foods|data|results` e retornar a list interna, ou raise `ValueError`. Considerar lib `json5` ou `dirty_json` para tolerar trailing comma se a robustez justificar a dependência.
- **Esforço:** S (< 1h)
- **Origem:** PASSO 4.5

### AUD-018 — Páginas e componentes do frontend ultrapassam 500 LOC

- **Severidade:** 🟡 média
- **Frente:** D
- **Arquivo:linha:** `frontend/app/(dashboard)/refeicoes/page.tsx` (1055), `frontend/components/dashboard/QuickAddModals.tsx` (657), `frontend/app/(dashboard)/insights/page.tsx` (611), `frontend/app/(dashboard)/relatorios/page.tsx` (548)
- **Descrição:** 4 arquivos passam de 500 LOC; o pior, `refeicoes/page.tsx`, tem **1055 LOC**, importa 25 ícones e mistura listagem, criação por texto, captura de voz (mic), upload de foto e edição inline. God components dificultam revisão, testes (cobertura por unidade impraticável), code-splitting e onboarding de outras pessoas.
- **Evidência:** `artefatos/D1-paginas-loc.txt`.
- **Recomendação:** Para `refeicoes/page.tsx`: extrair para `_components/{MealList,MealItemCard,AddMealTextDialog,AddMealPhotoDialog,EditMealItemDialog}.tsx` + `_hooks/useVoiceCapture.ts`. Para `QuickAddModals.tsx`: 1 arquivo por modal. Meta: ≤ 250 LOC por arquivo de página, ≤ 200 LOC por componente.
- **Esforço:** L (> 4h) para `refeicoes`; M para os demais
- **Origem:** PASSO 5.1

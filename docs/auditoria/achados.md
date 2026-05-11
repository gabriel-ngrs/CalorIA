# Achados da Auditoria

Lista de problemas encontrados, ordenada por ID. Para visão por severidade ver `relatorio-preliminar.md` ao fim da auditoria.

**Status totais:** críticos: 1 · altos: 9 · médios: 14 · baixos: 13 (atualizar a cada novo achado)

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

### AUD-019 — Hooks de mutação não usam optimistic updates

- **Severidade:** 🟢 baixa
- **Frente:** D
- **Arquivo:linha:** `frontend/lib/hooks/useReminders.ts`, `useNotifications.ts`, `useMeals.ts` (mutations).
- **Descrição:** Todas as mutações usam `onSuccess` para `invalidateQueries`, mas nenhuma usa `onMutate` para optimistic update. Operações como `toggleReminder`, `markNotificationRead`, `markAllRead`, `deleteMealItem` são idempotentes/triviais de reverter — perfeitas para feedback imediato de UI sem esperar round-trip.
- **Evidência:** inspeção dos hooks; ausência de `onMutate` em todos.
- **Recomendação:** Implementar optimistic updates pelo menos para toggles e mark-read (operações com baixíssimo risco de rollback). Padrão: `onMutate: () => qc.setQueryData([key], (old) => updated); return { previous: old };` + `onError: (_e, _v, ctx) => qc.setQueryData([key], ctx.previous)`.
- **Esforço:** M (1–4h)
- **Origem:** PASSO 5.2

### AUD-020 — Logs verbosos rodam em produção (frontend)

- **Severidade:** 🟢 baixa
- **Frente:** D / J
- **Arquivo:linha:** `frontend/lib/api.ts:63,88,97,113` (4 sites: API→/API←/API✗/API↺); `frontend/app/providers.tsx:31` (NavTimer), `:47,51` (QueryCache success/error)
- **Descrição:** 7 `console.log`/`console.error` rodam sem gate de ambiente. Volume típico estimado: 50-100 logs/min em sessão ativa. Polui DevTools, custa CPU mínima, e expõe queryKeys e rotas internas (info-disclosure menor). Único item gateado é `ReactQueryDevtools` (`providers.tsx:77`).
- **Evidência:** `grep -nE "console\." frontend/lib/api.ts frontend/app/providers.tsx` → 7 hits sem proteção.
- **Recomendação:** Criar `frontend/lib/log.ts` exportando `debug()`/`info()`/`error()` que checa `process.env.NODE_ENV !== "production"`. Substituir todos os `console.*` por esse logger. Manter `console.error` apenas para erros que precisam aparecer em produção (ex.: `signOut` falhando), e expor via Sentry/equivalente se houver no futuro.
- **Esforço:** S (< 1h)
- **Origem:** PASSO 5.3

### AUD-021 — Discrepância de contrato `/auth/login`: frontend lê `data.user.*` que o backend não envia

- **Severidade:** 🟠 alta
- **Frente:** D
- **Arquivo:linha:** `backend/app/api/v1/auth.py:47-50` (retorno) vs. `frontend/app/api/auth/[...nextauth]/route.ts:64-70` (leitura)
- **Descrição:** O backend retorna `TokenResponse(access_token, refresh_token)` — sem campo `user`. O `authorize` do NextAuth lê `data.user?.id ?? ""` e `data.user?.name ?? credentials.email`, portanto: `id` da sessão é string vazia, `name` cai no fallback (e-mail). Login funciona porque tokens são lidos corretamente; bug é silencioso e degrada UX (usuário vê o e-mail no lugar do nome até `useUser()` buscar `/auth/me`).
- **Evidência:** ler ambos arquivos; `grep -rn "session.user.id" frontend/app|components|lib` mostra que `id` não é usado em lógica funcional, só armazenado.
- **Recomendação:** **Opção 1 (preferida — fix no backend):** adicionar `user: UserPublicResponse | None = None` em `TokenResponse` e popular no endpoint `/auth/login` (e opcionalmente em `/auth/refresh`). Aproveita hidratação inicial sem round-trip extra. **Opção 2 (fix no frontend):** após `/auth/login` OK, `authorize` chama `/auth/me` com o token novo e popula `id`/`name`. Custa 1 round-trip extra no login.
- **Esforço:** S (< 1h)
- **Origem:** PASSO 5.4

### AUD-022 — 6 `any` para Web Speech API duplicados em 2 arquivos

- **Severidade:** 🟢 baixa
- **Frente:** D / I
- **Arquivo:linha:** `frontend/components/dashboard/QuickAddModals.tsx:180,187,195` e `frontend/app/(dashboard)/refeicoes/page.tsx:445,455,463`
- **Descrição:** 6 `any` no código de produção, todos relacionados à Web Speech API (`SpeechRecognition`/`webkitSpeechRecognition`). O TypeScript já tem tipos `SpeechRecognition`, `SpeechRecognitionEvent`, `SpeechRecognitionErrorEvent` em `lib.dom.d.ts`, mas as referências `window.SpeechRecognition`/`window.webkitSpeechRecognition` precisam de module augmentation para evitar `(window as any)`.
- **Evidência:** `artefatos/D5-any-usage.txt`. Nenhum outro `any` no código de produção (excluindo testes/mocks/build).
- **Recomendação:** (1) Criar `frontend/types/speech.d.ts` com `declare global { interface Window { SpeechRecognition?: ...; webkitSpeechRecognition?: ...; } }`. (2) Extrair `useVoiceCapture()` em `frontend/lib/hooks/` — elimina os 6 `any` E a duplicação entre os 2 arquivos. Combinar com refactor de `refeicoes/page.tsx` (AUD-018).
- **Esforço:** S (< 1h)
- **Origem:** PASSO 5.5

### AUD-023 — PWA: SW sem skipWaiting/clients.claim e manifest com gaps

- **Severidade:** 🟢 baixa
- **Frente:** D
- **Arquivo:linha:** `frontend/public/sw.js` (todo o arquivo); `frontend/app/manifest.ts:13-26`
- **Descrição:** **Service Worker:** só registra `push` e `notificationclick`. Sem `install` com `skipWaiting()` e sem `activate` com `clients.claim()` — atualizações de SW só ativam após o usuário **fechar todas as tabs do site**, e o primeiro carregamento exige reload manual para o SW ganhar controle. **Manifest:** apenas 2 ícones (192 `any`, 512 `maskable`); faltam tamanhos comuns (144, 384) e `apple-touch-icon` (iOS Safari não lê manifest icons). Sem `screenshots` (Lighthouse recomenda).
- **Evidência:** leitura completa de `sw.js` (18 LOC) e `manifest.ts` (44 LOC); `ls frontend/public/icons/` mostra apenas `icon-192.png` e `icon-512.png`.
- **Recomendação:** (1) Em `sw.js` adicionar `self.addEventListener("install", e => self.skipWaiting())` e `self.addEventListener("activate", e => clients.claim())`. (2) Gerar ícones 144 e 384 (já há `icon.svg` como source). (3) Adicionar `<link rel="apple-touch-icon">` em `app/layout.tsx`. (4) Capturar 1-2 screenshots e adicionar ao manifest.
- **Esforço:** S (< 1h)
- **Origem:** PASSO 5.6

### AUD-024 — Sem `@next/bundle-analyzer`: zero visibilidade de tamanho de bundle

- **Severidade:** 🟢 baixa
- **Frente:** D / I
- **Arquivo:linha:** `frontend/package.json` (não declara `@next/bundle-analyzer`); `frontend/next.config.mjs` (sem `withBundleAnalyzer`)
- **Descrição:** O projeto usa pacotes pesados conhecidos (`recharts`, `ogl`, vários `@radix-ui`) mas não tem ferramenta para inspecionar o que está sendo enviado ao cliente. Sem analyzer, problemas de bundle (componente client importando módulo server, barrel sem tree-shake, lib decorativa em rota crítica) só aparecem por degradação observada.
- **Evidência:** `grep "@next/bundle-analyzer" frontend/package.json` retorna nada.
- **Recomendação:** `npm install --save-dev @next/bundle-analyzer` + envolver `nextConfig` com `withBundleAnalyzer({ enabled: process.env.ANALYZE === "true" })`. Adicionar script `npm run build:analyze`. Rodar manualmente antes de releases ou em PRs grandes. Considerar verificar `recharts` (~100KB) e `ogl` (Plasma) em rotas onde não são usados.
- **Esforço:** S (< 1h)
- **Origem:** PASSO 5.7

### AUD-025 — `_run` em workers usa `asyncio.get_event_loop()` deprecated (risco real de `RuntimeError`)

- **Severidade:** 🟠 alta
- **Frente:** E
- **Arquivo:linha:** `backend/app/workers/tasks/reminders.py:19-21`, `backend/app/workers/tasks/reports.py:17-19`, `backend/app/workers/tasks/maintenance.py:19-21` (3 cópias idênticas)
- **Descrição:** Os 3 módulos de tasks Celery declaram a mesma helper `def _run(coro): return asyncio.get_event_loop().run_until_complete(coro)`. Desde **Python 3.10** chamar `asyncio.get_event_loop()` quando não há loop ativo na thread atual emite `DeprecationWarning` e cria/retorna um loop novo; em **Python 3.12** (versão deste projeto) o aviso continua e o comportamento é instável em threads worker do Celery: a primeira execução cria o loop, mas se uma task anterior tiver fechado o loop dessa thread, a próxima `_run` em geral lança `RuntimeError: There is no current event loop in thread '...'.` ou `RuntimeError: Event loop is closed`. O risco se materializa quando o worker reaproveita threads (default `prefork`+`worker_prefetch_multiplier=1` mitiga, mas não elimina) e/ou quando alguma exceção interna fecha o loop. Em **Python 3.14** a chamada será removida.
- **Evidência:** `artefatos/E1-get-event-loop.txt` — 3 ocorrências, uma em cada módulo de tasks; código idêntico inclusive na docstring.
- **Recomendação:** Substituir por `asyncio.run(coro)`, que cria e fecha um event loop dedicado por chamada (semântica correta para tasks Celery síncronas que só precisam executar uma coroutine raiz). Alternativa equivalente: `loop = asyncio.new_event_loop(); try: return loop.run_until_complete(coro); finally: loop.close()`. Como as 3 cópias são idênticas, vale extrair para `app/workers/utils.py` (1 helper compartilhada) — ataca também a duplicação. Acrescentar nota no `Dockerfile` do worker que `PYTHONWARNINGS=error::DeprecationWarning` em CI ajudaria a pegar regressões.
- **Esforço:** S (< 1h)
- **Origem:** PASSO 6.1

### AUD-026 — `dispatch_due_reminders` usa `datetime.now()` naive — bug latente de timezone

- **Severidade:** 🟠 alta
- **Frente:** E
- **Arquivo:linha:** `backend/app/workers/tasks/reminders.py:37` (`now = datetime.now()`); comparado em `:60-63` contra `Reminder.time` (`backend/app/models/reminder.py:34` — `Time` sem `timezone`)
- **Descrição:** A task lê o "agora" sem TZ e compara `reminder.time.hour/minute` com `now.hour/minute`. Hoje **funciona por acidente**: todos os containers (postgres, backend, celery_worker, celery_beat) têm `TZ=America/Sao_Paulo` em ambos `docker-compose.yml` e `docker-compose.dev.yml`, e o `User` não tem campo de fuso. Logo, "agora naive no container" coincide com "horário São Paulo", que coincide com o que o usuário típico digitou no formulário de lembrete. Falha em 3 cenários reais e prováveis:
    1. **Migração para UTC** (default em quase todos os PaaS/cloud): lembrete configurado para 08:00 dispara às 05:00 ou 11:00 (offset de 3h, varia com horário de verão em outros países).
    2. **Usuário fora de São Paulo:** o front salva "08:00" como string, sem TZ; o worker assume São Paulo. Para usuário em Lisboa (UTC+0), o lembrete das "08:00" do dele vai para às 12:00 de Lisboa.
    3. **DST**: Brasil eliminou em 2019, mas outros países (e o próprio Brasil se voltar) terão duplicação no "fall back" ou pulo no "spring forward" — `datetime.now()` naive não consegue lidar.

  Bônus: Celery está com `timezone="America/Sao_Paulo"` + `enable_utc=True` (`celery_app.py:23-24`) para interpretar crons; o **disparo** da task é correto, mas o **conteúdo** depende da TZ do processo. Acoplamento implícito invisível no código.
- **Evidência:** `artefatos/E2-tz.txt` (postgres TZ, container envs); leitura de `reminders.py:36-71` + `models/reminder.py:34` + `celery_app.py:18-24`.
- **Recomendação:** **Curto prazo** (sem mudar schema): em `reminders.py`, trocar `datetime.now()` por `datetime.now(ZoneInfo("America/Sao_Paulo"))` (ou ler `settings.timezone`). Documenta a TZ canônica e fica imune à TZ do processo. **Médio prazo**: adicionar `User.timezone: Mapped[str] = mapped_column(default="America/Sao_Paulo")`. A task itera reminders, pega `user.timezone`, e compara `Reminder.time` com `datetime.now(ZoneInfo(user.timezone))`. Cobertura de testes com `freezegun`/`time-machine` testando 3 fusos. **Longo prazo (opcional)**: armazenar `Reminder.next_fire_at: DateTime(timezone=True)` recalculado após cada disparo — task vira `WHERE next_fire_at <= now()`, o que escala melhor que iterar todos os reminders ativos por minuto.
- **Esforço:** S (curto), M (médio), L (longo)
- **Origem:** PASSO 6.2

### AUD-027 — `_send_hydration_reminders_async` ignora `User.water_goal_ml` (hardcode 2000ml)

- **Severidade:** 🟠 alta
- **Frente:** E
- **Arquivo:linha:** `backend/app/workers/tasks/reminders.py:174` (`if summary.total_ml >= 2000`) e `:179` (body `"… / 2000 ml hoje."`)
- **Descrição:** A task `send_hydration_reminders` compara o consumo do dia contra `2000` ml fixo e a mensagem de notificação anuncia a meta como `2000 ml`. O modelo `User` já tem o campo `water_goal_ml: Mapped[int | None]` (`backend/app/models/user.py:44`), preenchido pelo perfil/onboarding, mas a task **ignora** este valor. Resultado:
    - Usuário com meta menor (ex.: 1500 ml em criança/idoso) recebe push depois da meta dele atingida.
    - Usuário com meta maior (ex.: 3500 ml em atleta) atinge "2000" e **não** recebe mais lembretes — falha silenciosa porque o push some sem motivo aparente.
    - A mensagem mostra "X / 2000 ml" para todo mundo, contradizendo o que aparece no dashboard que usa `water_goal_ml` real.

  Já documentado no plano (`plano.md` § E.5 como "🟠 hardcode") — apenas confirmado aqui.
- **Evidência:** `artefatos/E3-hydration-hardcode.txt` — 2 hits de `"2000"`. `User.water_goal_ml` declarado mas sem nenhuma referência em `backend/app/workers/`.
- **Recomendação:** Trocar pelas duas linhas correspondentes:
    ```python
    goal_ml = user.water_goal_ml or 2000
    if summary.total_ml >= goal_ml:
        continue
    body = f"Hidratação: {summary.total_ml} ml / {goal_ml} ml hoje. Lembre-se de se hidratar!"
    ```
  O fallback `or 2000` cobre `None` (perfil não configurado). Considerar mover `2000` para `app/core/config.py` como `DEFAULT_WATER_GOAL_ML` para evitar reaparecer em outros pontos. Combinar com refator do AUD-008 (query agregada para hidratação) elimina N+1 da mesma task no mesmo PR.
- **Esforço:** S (< 1h)
- **Origem:** PASSO 6.3

### AUD-028 — Tratamento de Web Push 410 (subscription expirada) duplicado em 4 sites de workers

- **Severidade:** 🟡 média
- **Frente:** E
- **Arquivo:linha:** `backend/app/workers/tasks/reminders.py:100-137` (`_send_reminder_notification`), `:194-228` (`_send_hydration_reminders_async`); `backend/app/workers/tasks/reports.py:80-118` (`_send_daily_summaries_async`), `:179-217` (`send_weekly_reports`)
- **Descrição:** Os 4 caminhos de envio de Web Push do projeto repetem o mesmo bloco de ~30 LOC: (1) `select PushSubscription where user_id`; (2) loop `await asyncio.to_thread(send_push_notification_sync, ...)`; (3) `except Exception as ex: try: from pywebpush import WebPushException; if isinstance(ex, WebPushException) and ex.response.status_code == 410: expired_ids.append(sub.id) except ImportError: pass`; (4) `if expired_ids: db.execute(delete(PushSubscription).where(id.in_(expired_ids)))`. Diferenças entre as 4 cópias: apenas o `body` e o `url` (default `/dashboard` em reminders, `/relatorios` em reports). Resultado: ~120 LOC duplicadas, e qualquer mudança na política de cleanup (ex.: marcar como inativo em vez de deletar; ou adicionar logging estruturado, AUD-013) precisa ser replicada 4×, com risco de divergência. Curiosidade: o `try: from pywebpush import WebPushException; except ImportError: pass` interno **nunca dispara** — `pywebpush` está em `pyproject.toml` como dependência direta — é over-engineering defensivo que polui o trace.
- **Evidência:** `artefatos/E4-push-410.txt` — 4 sites com `expired_ids: list[int] = []` + `WebPushException` + `status_code == 410` + `delete(PushSubscription)`. Estrutura textualmente igual nos 4.
- **Recomendação:** Estender `PushService` (`backend/app/services/push_service.py`) com um método `async def send_with_cleanup(self, user_id: int, title: str, body: str, url: str = "/dashboard") -> int` que: busca subscriptions do usuário, envia em loop (mantendo o `asyncio.to_thread` para não bloquear o loop), coleta expirados, deleta numa única query, e retorna a contagem enviada com sucesso (útil para logs/metrics). Cada um dos 4 sites vira uma única linha: `await PushService(db).send_with_cleanup(user.id, title, body, url="/relatorios")`. Remove o `try: from pywebpush import WebPushException; except ImportError` dos workers (manter só dentro do service, onde já existe). Combinar com AUD-013 (logs estruturados) para emitir `push.sent`/`push.expired` por chamada num único ponto.
- **Esforço:** M (1–4h)
- **Origem:** PASSO 6.4

### AUD-029 — `cleanup_old_conversations` faz Seq Scan em `ai_conversations` (sem índice em `updated_at`)

- **Severidade:** 🟢 baixa
- **Frente:** E / F
- **Arquivo:linha:** `backend/app/workers/tasks/maintenance.py:42-46` (`DELETE FROM ai_conversations WHERE updated_at < cutoff RETURNING id`); migrações Alembic não declaram índice em `ai_conversations.updated_at`
- **Descrição:** A task diária de limpeza filtra por `updated_at < (now - 90 days)` mas a tabela `ai_conversations` só tem índices em `(id)`, `(external_chat_id)` e `(user_id)`. `EXPLAIN` no banco real confirma `Seq Scan on ai_conversations Filter: (updated_at < ...)`. Hoje a tabela tem ~43 linhas (custo 12.28) — irrelevante. Em 6 meses de uso ativo (5 conversas/dia × 1 user × 180 dias = 900 linhas) ainda passa sem dor; em 5 anos com 100 usuários ativos (~90k linhas) o `DELETE` faz scan completo da tabela inteira a cada execução, e como roda à 3h da manhã com pouca contenção, o impacto é baixo, mas o crescimento é linear.
- **Evidência:** `artefatos/E5-ai-conv-indexes.txt` — `\d ai_conversations` lista 3 índices, nenhum em `updated_at`. `EXPLAIN DELETE ... WHERE updated_at < NOW() - INTERVAL '90 days'` retorna `Seq Scan`.
- **Recomendação:** Migration adicionando `Index("ix_ai_conversations_updated_at", "updated_at")`. Custo: poucos KB de espaço, escrita marginalmente mais cara em INSERT/UPDATE, leitura/DELETE da cleanup vira `Bitmap Heap Scan` (logarítmico). Alternativa estrutural se a tabela ficar muito grande no futuro: particionamento por mês/trimestre, fazendo o cleanup ser `DROP PARTITION` (O(1)) — fora de escopo agora. Aproveitar o mesmo PR para revisar se outras colunas usadas em filtros de tasks (ex.: `WeightLog.date` já tem índice; `MealItem.created_at` precisa checar) também precisam de índice.
- **Esforço:** S (< 1h)
- **Origem:** PASSO 6.5

### AUD-030 — Falta índice composto `(user_id, date)` em `meals` (e nos 3 logs diários)

- **Severidade:** 🟡 média
- **Frente:** F
- **Arquivo:linha:** `backend/app/models/meal.py` (sem `Index("ix_meals_user_date", "user_id", "date")`); idem `weight_log.py`, `mood_log.py`, `hydration_log.py`
- **Descrição:** As tabelas `meals`, `weight_logs`, `mood_logs` e `hydration_logs` têm índices **separados** em `user_id` e `date`, mas nenhuma tem o composto `(user_id, date)`. Quase toda query de dashboard filtra pelas duas colunas: `WHERE user_id = :u AND date = :d` (resumo do dia) ou `WHERE user_id = :u AND date BETWEEN ...` (semana/mês). Hoje o planner usa o índice `user_id` e filtra `date` no heap (`EXPLAIN SELECT * FROM meals WHERE user_id=1 AND date=CURRENT_DATE` → `Index Scan using ix_meals_user_id ... Filter: (date = CURRENT_DATE)`). Para usuários com muitas refeições, a etapa de filtro percorre todas as linhas do user no heap. Com composto `(user_id, date)`, vira Index Cond direto nos dois campos (sem heap scan adicional).
- **Evidência:** `artefatos/F1-indexes.txt` — `meals` lista `ix_meals_user_id` + `ix_meals_date` separados; idem `weight_logs`/`mood_logs`/`hydration_logs`. `EXPLAIN` confirma `Filter: (date = CURRENT_DATE)` após `Index Cond: (user_id = 1)`.
- **Recomendação:** 1 migration adicionando 4 índices compostos:
    ```python
    op.create_index("ix_meals_user_date", "meals", ["user_id", "date"])
    op.create_index("ix_weight_logs_user_date", "weight_logs", ["user_id", "date"])
    op.create_index("ix_mood_logs_user_date", "mood_logs", ["user_id", "date"])
    op.create_index("ix_hydration_logs_user_date", "hydration_logs", ["user_id", "date"])
    ```
    Mantém os índices `user_id` separados (são úteis para outras queries — listagem de tudo por usuário); pode-se remover `ix_meals_date` etc. se nenhuma query filtra apenas por `date` global (verificar com `pg_stat_user_indexes` antes). Ganho proporcional ao número de linhas por usuário (negligenciável hoje, real com volume).
- **Esforço:** S (< 1h)
- **Origem:** PASSO 7.1

### AUD-031 — Falta índice composto `(user_id, read)` em `notifications` (unread-count é polled pelo header)

- **Severidade:** 🟡 média
- **Frente:** F
- **Arquivo:linha:** `backend/app/models/notification.py` (sem índice em `read` nem composto); endpoint `GET /notifications/unread-count` (rota interna do header, polled em intervalo curto)
- **Descrição:** `notifications` tem apenas `ix_notifications_user_id`. A query mais frequente da tabela é `SELECT COUNT(*) FROM notifications WHERE user_id = :u AND read = false` (badge do header). `EXPLAIN` mostra `Bitmap Index Scan on ix_notifications_user_id` seguido de `Filter: (NOT read)` em Bitmap Heap Scan: o planner pega TODAS as notificações do usuário e descarta as lidas no heap. Para um usuário com 1.000 notificações antigas (todas lidas) e 2 novas, o COUNT toca 1.002 linhas em vez de 2. Como o front faz polling regular, a query roda muito.
- **Evidência:** `artefatos/F1-indexes.txt` — `notifications` lista apenas `ix_notifications_user_id` e pkey. `EXPLAIN SELECT COUNT(*) ... WHERE user_id=1 AND read=false` → `Bitmap Index Scan ... Index Cond: (user_id=1)` + `Filter: (NOT read)`.
- **Recomendação:** Índice **parcial** otimizado para a query mais comum:
    ```python
    op.create_index(
        "ix_notifications_user_unread",
        "notifications",
        ["user_id"],
        postgresql_where=sa.text("NOT read"),
    )
    ```
    Parcial cobre exatamente o "unread badge" e ocupa muito menos espaço (tipicamente <5% das notificações ficam não-lidas). Alternativa mais simples (não-parcial) é o composto `(user_id, read)` — também resolve mas sem o tamanho reduzido. **Combinar com paginação consistente (AUD-005)** para auditar todos os endpoints de listagem da mesma tabela. Bônus: avaliar se `created_at` precisa de índice para `ORDER BY created_at DESC LIMIT N` da listagem.
- **Esforço:** S (< 1h)
- **Origem:** PASSO 7.1

### AUD-032 — `foods.name` tem 2 índices redundantes (`ix_foods_name` + `taco_foods_name_key` UNIQUE)

- **Severidade:** 🟢 baixa
- **Frente:** F
- **Arquivo:linha:** `backend/app/models/food.py` + histórico de migrações que criou `taco_foods_name_key` na tabela legada `taco_foods` (renomeada para `foods`)
- **Descrição:** `\d foods` mostra **dois índices em `name`**:
    - `ix_foods_name` — `CREATE INDEX ... ON foods USING btree (name)` (não-único, criado pelo modelo SQLAlchemy)
    - `taco_foods_name_key` — `CREATE UNIQUE INDEX ... ON foods USING btree (name)` (legado, originário da migration que criou `taco_foods` antes da unificação para `foods` com TACO + Open Food Facts)

  O índice **non-unique** é redundante: qualquer query que use ele pode usar o UNIQUE igual ou melhor (UNIQUE garante 1 valor por chave, planner trata igual ou prefere). Custos: ~8 MB de tabela hoje (TACO + parcial OFF), índice extra adiciona ~1-2 MB no disco e custo de manutenção em cada INSERT/UPDATE de `name`. Pior ainda: o UNIQUE está bloqueando inserções de duplicatas com o mesmo nome — o que é incorreto após a unificação (Open Food Facts pode ter "Arroz branco" de marcas diferentes). Se o seed enriquecer a tabela com OFF completo (~19.500 alimentos), o UNIQUE pode falhar inserções legítimas.
- **Evidência:** `artefatos/F1-indexes.txt` — 2 entradas em `foods.name`: `ix_foods_name` (btree) e `taco_foods_name_key` (UNIQUE btree).
- **Recomendação:** Migration:
    ```python
    op.drop_index("ix_foods_name", table_name="foods")  # redundante
    op.drop_constraint("taco_foods_name_key", "foods", type_="unique")  # incorreto pós-unificação
    op.create_index("ix_foods_name", "foods", ["name"])  # recria não-único
    ```
    Antes de aplicar: revisar se `food_lookup.py` ou seed dependem da unicidade (não devem; o lookup usa `pg_trgm`). Documentar que a unicidade era um artefato da era TACO-only.
- **Esforço:** S (< 1h)
- **Origem:** PASSO 7.1

### AUD-033 — Migração `adiciona_dessert_mealtype` tem `downgrade()` vazio (irreversível)

- **Severidade:** 🟡 média
- **Frente:** F
- **Arquivo:linha:** `backend/alembic/versions/20260306_e5f6a1b2c3d4_adiciona_dessert_mealtype.py:downgrade` (corpo é apenas `pass` com comentário "PostgreSQL não permite remover valores de enum sem recriar o tipo")
- **Descrição:** Das 10 migrações Alembic do projeto, **9 têm downgrade efetivo** (de 1 a 25 LOC). A migração que adicionou o valor `dessert` ao enum `mealtype` declara `downgrade()` mas o corpo é apenas `pass` — o autor explicitamente assumiu a limitação do Postgres. Isto significa que **`alembic downgrade -1` a partir desta migração não retorna ao estado anterior**: o valor `dessert` permanece no enum mesmo após "rollback". Em ambientes de teste/staging onde se faz upgrade/downgrade para validar migrações, esse drift acumula silenciosamente. Em prod o risco é menor (não se faz downgrade), mas a expectativa de reversibilidade é quebrada — quem ler `alembic history` espera "10 passos pra frente, 10 pra trás".

  Nota: o Postgres **permite** remover valores de enum, mas requer recriar o tipo (`CREATE TYPE mealtype_new AS ENUM(...); ALTER TABLE meals ALTER COLUMN meal_type TYPE mealtype_new USING ...; DROP TYPE mealtype; ALTER TYPE mealtype_new RENAME TO mealtype`). É verboso mas factível. O `pass` é uma escolha consciente, não impossibilidade técnica.

  Bônus relacionado: a migração `20260320_e6f7a8b9c0d1_fix_search_text_taco.py` é uma migração de **dados** que documenta partial revert ("A deleção do registro OpenFoodFacts não é revertida"). Isso é defensável (evita reintroduzir bug), mas vale registrar a expectativa explicitamente.
- **Evidência:** `artefatos/F3-downgrade.txt` — extração do corpo de cada `downgrade()`. `adiciona_dessert_mealtype.py` é o único com corpo apenas `pass` + comentário. Os outros 9 têm conteúdo real (mín. 3 LOC, máx. 25).
- **Recomendação:** Substituir o `pass` por um downgrade real:
    ```python
    def downgrade() -> None:
        # Recria o enum sem 'dessert'
        op.execute("ALTER TYPE mealtype RENAME TO mealtype_old")
        op.execute("CREATE TYPE mealtype AS ENUM ('breakfast', 'lunch', 'dinner', 'snack', 'supplement')")
        op.execute("UPDATE meals SET meal_type='snack' WHERE meal_type::text='dessert'")  # ou raise se preferir falhar explicito
        op.execute("ALTER TABLE meals ALTER COLUMN meal_type TYPE mealtype USING meal_type::text::mealtype")
        op.execute("DROP TYPE mealtype_old")
    ```
    Acrescentar política em `docs/architecture.md` ou `CONTRIBUTING`: "Toda migração deve ter downgrade efetivo; se houver dado a perder, fazer escolha explícita (ex.: mapear para outro valor) e documentar."
- **Esforço:** S (< 1h) para o fix; M para revisar política e cobrir as 9 demais com asserts em CI.
- **Origem:** PASSO 7.3

### AUD-034 — Enum `MealSource` mantém valores `TELEGRAM`/`WHATSAPP` mortos no schema

- **Severidade:** 🟢 baixa
- **Frente:** F
- **Arquivo:linha:** `backend/app/models/meal.py:32-35` (enum `MealSource` com `MANUAL`/`TELEGRAM`/`WHATSAPP`); enum `mealsource` no DB com mesmas 3 entradas
- **Descrição:** `MealSource` herda da era em que existiam integrações Telegram/WhatsApp para registro de refeições. Hoje o projeto é apenas web (CLAUDE.md confirma "O usuário registra refeições pelo dashboard web"); o único valor usado em código é `MealSource.MANUAL` (`backend/app/models/meal.py:49` como default; `backend/app/schemas/meal.py:51` como default; nenhum `.TELEGRAM`/`.WHATSAPP`). O enum no banco também mantém os 3 valores. Como `meals.source` tem default `MANUAL` e nenhum endpoint expõe os outros valores, é inalcançável — mas dead schema. Risco real é baixo (futura migração de dados pode trazer linhas legadas; a migração `20260315_a1b2c3d4e5f6_web_push_notifications.py` já removeu campos Telegram/WhatsApp das outras tabelas, mas não cuidou desse enum).
- **Evidência:** `grep -rn "MealSource\.TELEGRAM\|MealSource\.WHATSAPP"` no `backend/` retorna 0 hits; `psql -c "SELECT enumlabel FROM pg_enum WHERE enumtypid=(SELECT oid FROM pg_type WHERE typname='mealsource')"` retorna `MANUAL/TELEGRAM/WHATSAPP`. Já flagged no `plano.md § F.2` como item a auditar.
- **Recomendação:** Migration que (a) faz `UPDATE meals SET source='manual' WHERE source IN ('telegram','whatsapp')` (defensivo, não deve ter linhas com volume atual zero); (b) recria o enum sem os 2 valores legados (mesma técnica do AUD-033). Atualizar `MealSource` no model. Combinar com AUD-033 num único PR de "limpeza de enums". Esta migração serve como exemplo do padrão correto que falta em AUD-033.
- **Esforço:** S (< 1h)
- **Origem:** PASSO 7.3

### AUD-035 — Pool sizing por processo × processos × Postgres `max_connections=100` pode saturar

- **Severidade:** 🟡 média
- **Frente:** F
- **Arquivo:linha:** `backend/app/core/database.py:17-23` (`pool_size=10`, `max_overflow=20`); `backend/Dockerfile:55` (`uvicorn ... --workers 2`); `docker-compose.yml` (1 celery_worker + 1 celery_beat)
- **Descrição:** O engine SQLAlchemy é configurado com `pool_size=10` + `max_overflow=20` = até **30 conexões por processo** em pico. A produção tem:
    - 2 uvicorn workers × 30 = **60 conn**
    - 1 celery worker (prefork; cada child importa o mesmo módulo `database.py` e cria seu próprio engine quando criar a primeira session — por default `concurrency=os.cpu_count()` ≈ 2-4 no servidor) × 30 = **60-120 conn**
    - 1 celery beat × 30 = **30 conn** (beat só lê de schedule, mas o engine é carregado por importação)

    Total **150-210 conexões** contra `max_connections=100` do Postgres (default, confirmado via `SHOW max_connections`). Pior cenário (carga + tasks pesadas concorrentes) pode lançar `OperationalError: too many connections for role` e derrubar uvicorn workers. Mesmo o cenário "razoável" de 90 conexões (1 cpu × celery + 2 uvicorn) já está perto do limite.

    Estimativas atuais (1 usuário, projeto pessoal) não chegam perto disso — risco é **latente**, materializa quando o tráfego subir ou o celery worker tiver `concurrency` aumentado.
- **Evidência:** leitura de `database.py:17-23`, `Dockerfile:55`, `docker-compose.yml`; `psql -c "SHOW max_connections"` = 100.
- **Recomendação:** Decisão estrutural conforme cenário:
    - **Cenário escala baixa (atual)**: reduzir `pool_size=5, max_overflow=10` (15 conn por processo) → ~75 conn total no pior caso; usar PgBouncer entre app e Postgres (modo `transaction` ou `statement`) que multiplexa milhares de connections em poucas reais. PgBouncer é o caminho padrão da indústria; permite manter pool generoso no app sem estourar o DB.
    - **Cenário escala alta** (quando chegar): aumentar `max_connections` no Postgres (custa RAM — cada conexão ≈ 10 MB) **ou** colocar PgBouncer. Ajustar `shared_buffers` (hoje 128 MB) também.
    - **Independente do cenário**: garantir que o celery worker tenha pool dedicado (não compartilhar engine com uvicorn) e dimensionar pelo `concurrency` configurado.
- **Esforço:** S (mudar pool config), M (introduzir PgBouncer)
- **Origem:** PASSO 7.4

### AUD-036 — Event listener loga TODA query como `INFO` em produção (`db_logger.info` em `after_cursor_execute`)

- **Severidade:** 🟢 baixa
- **Frente:** F / J
- **Arquivo:linha:** `backend/app/core/database.py:39-52` (`@event.listens_for(engine.sync_engine, "after_cursor_execute")`)
- **Descrição:** Event listener registra timing + 1ª linha do SQL **em cada query** via `db_logger.info(...)`. Sem gate de ambiente (`NODE_ENV != production` ou `settings.environment != "dev"`). Em produção com 1 usuário rodando o dashboard, fácil chegar a 50-100 queries/min só do polling do header. Em escala (100 usuários) seriam 5-10k queries/min — log do backend inundado, custo IO + CPU + storage. O flag de "⚠️ LENTO" para queries > 100ms é útil, mas poderia ser o único evento logado.
- **Evidência:** trecho `database.py:48-52`; `caloria.db` logger não tem filtro no `app/main.py` (verificado).
- **Recomendação:** 3 opções, do menor para maior esforço:
    - **Quick fix**: trocar `db_logger.info(...)` por `db_logger.debug(...)` (default Python logging level WARNING — debug fica silencioso em prod). Manter `db_logger.warning(...)` ou similar quando `ms > 100` para o "⚠️ LENTO" continuar visível.
    - **Médio**: gatear o listener com `if settings.environment == "dev"` — em prod o listener nem registra. Performance ganho marginal (1 string format por query a menos).
    - **Estrutural**: integrar com observabilidade real (OTEL/Sentry traces) e remover o listener custom.
- **Esforço:** S (< 1h) para o quick fix
- **Origem:** PASSO 7.4

### AUD-037 — Sem backup automatizado do Postgres (escalará para 🔴 quando o deploy acontecer)

- **Severidade:** 🟠 alta
- **Frente:** F
- **Arquivo:linha:** `scripts/setup-server.sh` (sem backup), `scripts/deploy.sh` (sem backup), `docs/deploy.md:306-321` (apenas instrução manual + dica de cron em blockquote), `Roadmap.md:413` (`[ ] Backups automáticos do PostgreSQL (cron diário)` — pendente)
- **Descrição:** A política de backup hoje é **inteiramente manual**. `docs/deploy.md` documenta o comando `pg_dump` para uso ad-hoc e oferece uma "dica" de `crontab` numa blockquote, mas: (a) `setup-server.sh` não automatiza nada — quem provisiona o servidor sai sem backup; (b) não há armazenamento offsite (instrução manda escrever em `/opt/caloria/backup_*.sql` no próprio servidor — perda do servidor = perda dos backups); (c) não há política de retenção (vai acumular indefinidamente até encher o disco); (d) não há procedimento documentado de **restore** (apenas implícito).

  Status atual: **não está em produção** (Roadmap § 9.2 com todos os itens em `[ ]`), mas o sistema é deployable a qualquer momento (CI/CD verde, deploy.md detalhado). O risco real materializa no instante do primeiro deploy: dados de usuário (refeições, peso, hidratação, mood, lembretes, conversas IA) sem backup e sem rota de recuperação. Severidade 🟠 enquanto em prep, **escala para 🔴 crítico no minuto pós-deploy**.
- **Evidência:** `grep -in "backup\|pg_dump\|cron" scripts/*.sh` → 0 hits; `docs/deploy.md:15` ("backups manuais"); `Roadmap.md:413` em aberto.
- **Recomendação:** Antes do primeiro deploy, executar como condição de release:
    1. **Automatizar** — adicionar em `scripts/setup-server.sh` um bloco que cria `/etc/cron.d/caloria-backup` com `0 3 * * * root docker exec caloria_postgres pg_dump -U caloria caloria_db | gzip > /opt/caloria/backup/$(date +\%Y\%m\%d_\%H\%M).sql.gz`. Diário às 3h.
    2. **Offsite** — sincronizar `/opt/caloria/backup/` para Hetzner Storage Box, S3, ou rclone para Dropbox/Drive. Sem offsite, falha de disco = perda total. Adicionar a linha de `rclone copy` (ou similar) no mesmo cron, após o dump.
    3. **Retenção** — adicionar `find /opt/caloria/backup -name '*.sql.gz' -mtime +30 -delete` no cron para manter 30 dias locais; offsite com versionamento (S3 lifecycle policy ou snapshot).
    4. **Restore** — incluir em `docs/deploy.md` a seção `## Restore` com `gunzip < backup.sql.gz | docker exec -i caloria_postgres psql -U caloria caloria_db`. **Testar restaurando num staging** (mesma releitura que prod) — backup não-testado é Schrödinger.
    5. Marcar Roadmap § 9.2 backup como `[x]` e `Roadmap.md:413` resolvido.
- **Esforço:** M (1–4h para implementar 1+2+3+4)
- **Origem:** PASSO 7.5

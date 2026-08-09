# Frente B — Backend

**Plano:** ver `plano.md` § Frente B.

## Achados desta frente

- AUD-003 (🟡 média) — 2 endpoints públicos em `push.py` sem `response_model` (retornam `dict[str, str]` cru)
- AUD-004 (🟢 baixa) — `meals.py:101` re-eleva HTTPException dentro de `except` sem `from None`
- AUD-005 (🟢 baixa) — `weight.py:16` aceita `limit ≤ 200` (divergente do padrão 100)
- AUD-006 (🟠 alta) — `food_lookup.py:89` executa 1 query SQL por n-grama candidato (~25 round-trips por refeição)
- AUD-007 (🟠 alta) — `InsightsGenerator` chama `get_daily_summary` em loop (`nutritional_alerts` e `monthly_report`)
- AUD-008 (🟠 alta) — Workers Celery (reminders + maintenance) iteram usuários e fazem 1 query por usuário
- AUD-009 (🟠 alta) — `PhotoAnalysisRequest.image_base64` sem `max_length` (vetor de DoS)
- AUD-010 (🟡 média) — múltiplos campos texto livre sem `max_length` (notes/message/question/raw_input)
- AUD-011 (🟢 baixa) — 15 `# type: ignore` elimináveis com tipagem correta (12 em parsers de IA, 3 utilitários)

## B.1 response_model e status codes

Comando: ver `artefatos/B1-routers-response.txt` (gerado via script Python que extrai cada `@router.*` + verifica `response_model` e exclui 204/205).

**Endpoints sem `response_model` (47 totais)**

| Endpoint | Linha | Retorno hoje | Severidade |
|---|---|---|---|
| `POST /push/subscribe` | `push.py:73` | `dict[str, str]` (`{"status": "subscribed"}`) | 🟡 (AUD-003) |
| `POST /notifications/read-all` | `push.py:187` | `dict[str, str]` | 🟡 (AUD-003) |

Demais 45 endpoints declaram `response_model=...` ou usam `status.HTTP_204_NO_CONTENT`. Cobertura de schemas: 96%.

**Status codes em uso (somando `raise HTTPException` + `status_code=` em decorator)**

| Código | Ocorrências | Uso |
|---|---|---|
| 404 NOT_FOUND | 11 | recurso não encontrado |
| 201 CREATED | 8 | POST de novo recurso |
| 502 BAD_GATEWAY | 6 | falha upstream Groq/IA |
| 204 NO_CONTENT | 5 | DELETE/POST sem corpo |
| 422 UNPROCESSABLE_ENTITY | 4 | validação semântica |
| 401 UNAUTHORIZED | 2 | login inválido |
| 503 SERVICE_UNAVAILABLE | 1 | serviço offline |
| 409 CONFLICT | 1 | duplicata |
| 200 OK | 1 | (`mark_all_read` — explícito embora seja default) |

Status codes coerentes com semântica HTTP padrão.

## B.2 `raise HTTPException` com cláusula `from`

Comando: `rg -n "raise HTTPException" backend/app/api/v1/ -A 3` + script Python para detectar contexto `except`.

| Métrica | Valor |
|---|---|
| Total `raise HTTPException` | 24 |
| Dentro de `except` | 9 |
| Dentro de `except` **sem `from exc`/`from None`** | 1 |

Único violador (já citado no plano, Anexo A):

| Arquivo:linha | Bloco |
|---|---|
| `backend/app/api/v1/meals.py:101` | `except MealItemNotFound:` → `raise HTTPException(404, "Item não encontrado")` sem `from None` |

Implicação: o traceback HTTP exposto pelo FastAPI inclui a cadeia "During handling of the above exception, another exception occurred", vazando trace interno se o handler de erro genérico estiver verboso. Achado 🟢 (AUD-004).

Os 8 casos restantes em `ai.py` já usam `raise HTTPException(...) from exc`. ✅

## B.3 Padrão de paginação

Comando: `rg -n "skip|limit" backend/app/api/v1/ | grep "Query"`. Artefato: `artefatos/B3-paginacao.txt`.

| Endpoint | skip | limit (default) | limit (max) |
|---|---|---|---|
| `GET /meals` | `ge=0` ✅ | 20 | 100 ✅ |
| `GET /weight` | `ge=0` ✅ | 50 | **200** ⚠️ |
| `GET /mood` | `ge=0` ✅ | 30 | 100 ✅ |
| `GET /dashboard/weight-chart` | — | 30 | 365 (chart range) |
| `GET /notifications` | — | 20 | 100 ✅ |

**Divergências**

- `weight.py:16` permite `le=200`, único divergente do limite padrão `100`. Não há justificativa aparente no comentário/docstring.
- `dashboard/weight-chart` e `notifications` não expõem `skip`. Justificável: ambos usam filtros temporais e ordenação descendente — mas faltaria documentar/uniformizar a estratégia ("limit-only" ou "cursor-based").
- Defaults variam de 20 a 50 — diferença razoável por domínio.

Achado registrado: AUD-005 (🟢) para o `le=200` divergente.

## B.4 N+1 detectados

Comando: `rg -n "for .* in .*:\s*$" backend/app/services/ backend/app/workers/ -A 5 | grep -B 1 "await.*execute|await.*get_|await.*list"`. Artefato: `artefatos/B4-n-mais-1.txt`.

| # | Local | Padrão | Impacto | AUD |
|---|---|---|---|---|
| 1 | `services/ai/food_lookup.py:89` | Para cada n-grama candidato (`~25` para refeição de 10 palavras), 1 query `text("SELECT … FROM foods …")` no loop | **Caminho síncrono do usuário** — cada análise de refeição ≈ 25 round-trips DB | AUD-006 |
| 2 | `services/ai/insights_generator.py:193` (`nutritional_alerts`) | `for i in range(days):` chama `MealService.get_daily_summary(user_id, d)` (que roda 1 query) → 14 queries seriais (default) | Endpoint `/ai/nutritional-alerts` | AUD-007 |
| 3 | `services/ai/insights_generator.py:368` (`monthly_report`) | `for day_num in range(days_in_month):` mesmo padrão → até 31 queries | Endpoint `/ai/monthly-report` | AUD-007 |
| 4 | `workers/tasks/reminders.py:172` (`_send_hydration_reminders_async`) | Para cada usuário ativo: `HydrationService.get_day_summary(user.id, today)` → N queries | Cron horário; cresce linear com usuários | AUD-008 |
| 5 | `workers/tasks/maintenance.py:87` | Para cada usuário: query do último `WeightLog` → N queries | Cron diário | AUD-008 |

Já existe `MealService.get_macros_by_date_range` (introduzido para resolver pattern análogo em `DashboardService.get_today` — comentário no código indica que substituiu loop equivalente). Pode ser estendido para resolver #2 e #3.

Para #4 e #5, possível solução: 1 query agregada com `JOIN User → HydrationLog/WeightLog` agrupada por usuário.

Para #1, possível solução: 1 query batch montando `WHERE search_text %>> ANY(ARRAY[…])` ou usar `tsvector` + `ts_rank`.

## B.5 Pydantic — `from_attributes`

Comando: `rg -n "from_attributes" backend/app/schemas/` + script Python para checar cada classe `*Response(BaseModel)`. Artefato: `artefatos/B5-pydantic-config.txt`.

**12 classes `*Response`** detectadas:

| Classe | from_attributes | Construído de |
|---|---|---|
| `WeightLogResponse`, `HydrationLogResponse`, `MoodLogResponse` | ✅ | ORM (`WeightLog`, etc.) |
| `UserResponse`, `ProfileResponse` | ✅ | ORM |
| `MealItemResponse`, `MealResponse`, `ReminderResponse` | ✅ | ORM |
| `TokenResponse` | ❌ | kwargs (`access_token`, `refresh_token`) — `auth.py:47,79` |
| `MealAnalysisResponse` | ❌ | kwargs (`items=…, low_confidence=…`) — `meal_parser.py:273`, `vision_parser.py:280` |
| `InsightResponse` | ❌ | kwargs (`type=…, content=…`) — `insights_generator.py:70,98,126` |
| `NutritionalAlertsResponse` | ❌ | kwargs — `insights_generator.py:243,269` |

Os 4 sem `from_attributes` **não são serializados de ORM** (construídos via kwargs em services/handlers). Configuração correta — sem achado.

Observação: schemas `*Create`/`*Update`/`Request`/`*Summary` corretamente sem `from_attributes` (são inputs ou DTOs puros).

## B.6 Validação de inputs sensíveis

Comando: leitura de cada `*Create`/`*Update`/`*Request` em `backend/app/schemas/*.py` + `grep -nE "Field\(" backend/app/schemas/`.

**Campos numéricos** — bem cobertos:

| Campo | Constraint | OK |
|---|---|---|
| `weight_kg` | `gt=0, le=700` | ✅ |
| `amount_ml` | `gt=0, le=5000` | ✅ |
| `mood_level`/`energy_level` | `ge=1, le=5` | ✅ |
| `height_cm` | `gt=0, le=300` | ✅ |
| `current_weight` | `gt=0, le=700` | ✅ |
| `age` | `gt=0, le=150` | ✅ |
| `password` | `min_length=8, max_length=128` | ✅ |
| `MealItemCreate.quantity` | `gt=0` (sem upper) | ⚠️ menor |
| `MealItemCreate.calories/protein/...` | `ge=0` (sem upper) | ⚠️ menor |

**Campos textuais sem `max_length`** (vetor de abuso de storage / inflar prompts da IA):

| Schema | Campo | Risco |
|---|---|---|
| `PhotoAnalysisRequest` | `image_base64` | 🟠 **DoS** — base64 de imagem > 50MB ≈ 67MB request body |
| `InsightRequest` | `question` | 🟡 mistura no prompt da IA |
| `MealCreate`/`MealUpdate` | `notes` | 🟡 storage abuse |
| `MealItemCreate` | `raw_input` | 🟡 storage abuse |
| `WeightLogCreate` | `notes` | 🟡 storage abuse |
| `MoodLogCreate` | `notes` | 🟡 storage abuse |
| `ReminderCreate`/`ReminderUpdate` | `message` | 🟡 (também injetado em notificações Web Push) |

**Campos com enum implícito sem validação**

- `MealItemCreate.unit` (`max_length=50` mas aceita qualquer string): poderia ser `Literal["g", "ml", "unidade", "fatia", "colher"]` ou enum.

Achados:
- AUD-009 🟠 — `image_base64` sem `max_length` (DoS).
- AUD-010 🟡 — múltiplos campos texto livre sem `max_length`.

## B.7 `# type: ignore` no backend

Comando: `rg -n "# type: ignore" backend/app/`. Artefato: `artefatos/B7-type-ignores.txt`.

| Categoria | Quantidade | Locais | Avaliação |
|---|---|---|---|
| **Justificável** (lib externa sem stubs) | 7 | 6× `[untyped-decorator]` para `@celery_app.task` em `workers/tasks/{reminders,maintenance,reports}.py`; 1× `[no-untyped-call, no-any-return]` para `aioredis.from_url(...)` em `auth_service.py:20` | Manter |
| **Eliminável (categoria 2)** | 15 | 12× `[arg-type]` em `meal_parser.py:236-241` e `vision_parser.py:235-240` (`float(d.get("...", 0))` onde `d: dict[str, Any]`); 1× `[return-value]` em `meal_service.py:45`; 1× `[no-any-return]` em `utils.py:15` (`json.loads`); 1× `[type-arg]` em `utils.py:18` (uso de `list` sem parâmetro) | AUD-011 (🟢) |
| **Total** | 22 | | |

Para os 12 do parser: solução estrutural seria criar `TypedDict` para a forma esperada do JSON da IA (já tipado como `ParsedFoodItem` no Pydantic — basta validar antes ou usar `cast(float, ...)`).

Achado: AUD-011 (🟢).

## Notas e contexto

(texto livre conforme aprendizagens surgem)

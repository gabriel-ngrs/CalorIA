# Frente B — Backend

**Plano:** ver `plano.md` § Frente B.

## Achados desta frente

- AUD-003 (🟡 média) — 2 endpoints públicos em `push.py` sem `response_model` (retornam `dict[str, str]` cru)
- AUD-004 (🟢 baixa) — `meals.py:101` re-eleva HTTPException dentro de `except` sem `from None`
- AUD-005 (🟢 baixa) — `weight.py:16` aceita `limit ≤ 200` (divergente do padrão 100)
- AUD-006 (🟠 alta) — `food_lookup.py:89` executa 1 query SQL por n-grama candidato (~25 round-trips por refeição)
- AUD-007 (🟠 alta) — `InsightsGenerator` chama `get_daily_summary` em loop (`nutritional_alerts` e `monthly_report`)
- AUD-008 (🟠 alta) — Workers Celery (reminders + maintenance) iteram usuários e fazem 1 query por usuário

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

## Notas e contexto

(texto livre conforme aprendizagens surgem)

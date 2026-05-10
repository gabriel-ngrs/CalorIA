# Frente B — Backend

**Plano:** ver `plano.md` § Frente B.

## Achados desta frente

- AUD-003 (🟡 média) — 2 endpoints públicos em `push.py` sem `response_model` (retornam `dict[str, str]` cru)
- AUD-004 (🟢 baixa) — `meals.py:101` re-eleva HTTPException dentro de `except` sem `from None`
- AUD-005 (🟢 baixa) — `weight.py:16` aceita `limit ≤ 200` (divergente do padrão 100)

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

## Notas e contexto

(texto livre conforme aprendizagens surgem)

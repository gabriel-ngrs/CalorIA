# Frente B — Backend

**Plano:** ver `plano.md` § Frente B.

## Achados desta frente

- AUD-003 (🟡 média) — 2 endpoints públicos em `push.py` sem `response_model` (retornam `dict[str, str]` cru)

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

## Notas e contexto

(texto livre conforme aprendizagens surgem)

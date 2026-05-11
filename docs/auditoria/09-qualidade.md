# Frente I — Qualidade

**Plano:** ver `plano.md` § Frente I.

## Achados desta frente

- AUD-045 — 14 erros ruff pré-existentes (1 em `app/`, 13 em `scripts/`); um deles (F821 em `scripts/import_off_local.py:440`) é bug funcional latente (🟢 baixa, mas com gotcha no `--fix`).
- AUD-046 — 6 erros mypy strict concentrados em `app/services/ai/ai_client.py` — duas classes: tipos do `messages` da Groq SDK e `aioredis.from_url` não-tipada (🟢 baixa).

## Notas e contexto

### § I.1 Erros ruff detalhados (de `artefatos/baseline-ruff.txt`)

**14 errors totais, 9 auto-fixable.** Distribuição: 1 em código de produção (`app/`), 13 em utilitários (`scripts/`).

| Código | Arquivo:linha | Mensagem | Auto-fix? |
|---|---|---|---|
| I001 | `app/api/v1/meals.py:1` | Import block unsorted | ✅ |
| B904 | `app/api/v1/meals.py:101` | `raise HTTPException` sem `from` (AUD-004) | ❌ |
| N818 | `app/services/meal_service.py:15` | `MealItemNotFound` deveria ter sufixo `Error` | ❌ |
| F401 | `scripts/extract_off_brazil.py:27` | `unicodedata` importado e não usado | ✅ |
| I001 | `scripts/import_fatsecret.py:38` | Import block unsorted | ✅ |
| F401 | `scripts/import_fatsecret.py:58` | `sqlalchemy.select` não usado | ✅ |
| N806 | `scripts/import_fatsecret.py:305` | `AsyncSessionLocal` (PascalCase) em escopo de função | ❌ |
| F401 | `scripts/import_off_local.py:51` | `io` não usado | ✅ |
| I001 | `scripts/import_off_local.py:384` | Import block unsorted | ✅ |
| F401 | `scripts/import_off_local.py:385` | `sqlalchemy.text` (alias `sa_text`) não usado **no escopo onde foi importado** | ⚠️ (ver nota) |
| **F821** | `scripts/import_off_local.py:440` | `sa_text` undefined name | ❌ |
| F401 | `scripts/normalize_foods.py:28` | `unicodedata` não usado | ✅ |
| B007 | `scripts/normalize_foods.py:235` | loop var `barcode` não usada | ✅ |
| F401 | `scripts/translate_foods.py:34` | `time` não usado | ✅ |

**Gotcha do `--fix`**: o par F401(385) + F821(440) em `scripts/import_off_local.py` revela um **bug real**, não só lint. O import `from sqlalchemy import text as sa_text` está dentro de uma função (`# Modo banco de dados` na linha 383), mas `sa_text` é usado na linha 440 dentro de `_flush()`, uma função separada — fora do escopo do import. Rodar `ruff --fix` cego removeria o import (linha 385) e deixaria o `F821` ativo, quebrando `_flush()` em runtime. Fix correto: **mover** `from sqlalchemy import text as sa_text` para o topo do módulo (não remover). O F821 já é o sinal que o ruff deu de que o código não funciona como está — esse script provavelmente quebra ao chamar `_flush()` hoje.

**Cross-referências com outros achados**:
- B904 em `meals.py:101` é o **mesmo** caso de AUD-004 (`raise HTTPException` sem `from`).
- N818 em `meal_service.py:15` é decisão de estilo razoável de questionar (sufixo `Error` em exception é convenção comum; nada quebra hoje).
- Os 11 hits em `scripts/` correspondem à decisão pendente registrada em plano § I.1: "corrigir todos ou excluir `scripts/` do ruff". `scripts/` já é excluído do mypy via `pyproject.toml`. Excluir do ruff também é defensável — esses são utilitários one-shot de importação/normalização, não código de produção; aplicar lint estrito sobre eles é overhead sem valor.

**Recomendação de PR de cleanup**:
1. Corrigir os 2 erros em `app/` (I001 auto + B904 manual com `from None`).
2. Decidir scripts: opção A — rodar `ruff --fix` em scripts/ E mover `sa_text` para o topo de `import_off_local.py` antes do fix (para não quebrar); opção B — adicionar `extend-exclude = ["scripts/"]` em `[tool.ruff]` no `pyproject.toml` e documentar a decisão em ADR (alinhamento com exclusão do mypy).

### § I.2 Warnings mypy strict (de `artefatos/baseline-mypy.txt`)

**6 errors em 1 arquivo (67 source files checked).** Todos concentrados em `app/services/ai/ai_client.py`.

| Linha | Código | Mensagem | Origem |
|---|---|---|---|
| 69 | `dict-item` | Dict entry 1: `"str": "list[object]"` vs `"str": "str"` | construção do `messages` para Groq Vision (content é lista de blocos, não string) |
| 79 | `arg-type` | `messages: list[dict[str, str]]` vs `Iterable[ChatCompletion*MessageParam]` | passagem para `groq.AsyncCompletions.create` (Vision) |
| 106 | `arg-type` | idem, mas em `_call()` (texto) | idem |
| 135 | `no-untyped-call` | `aioredis.from_url(...)` não-tipada em contexto tipado | leitura de cache em `_get_cached` |
| 136 | `no-any-return` | retorno `Any` quando assinatura promete `str \| None` | `await r.get(key)` retorna `Any` (consequência do 135) |
| 143 | `no-untyped-call` | `aioredis.from_url(...)` não-tipada | gravação de cache em `_set_cached` |

**Duas classes claras de problema:**

1. **Tipagem do payload Groq (linhas 69, 79, 106)** — o mypy não consegue inferir que cada `dict` literal no `messages` corresponde a um dos `TypedDict`s da Groq SDK (`ChatCompletionSystemMessageParam | ChatCompletionUserMessageParam | ...`). Caminho mais limpo: importar os `TypedDict`s da Groq e anotar `messages: list[ChatCompletionMessageParam]`. Particularmente importante na linha 67 (vision) que usa `content: list[dict]` (image_url + text blocos) — só `ChatCompletionUserMessageParam` aceita esse formato.
2. **`aioredis.from_url` sem stub (linhas 135, 143)** — `redis.asyncio` (alias `aioredis`) exporta `from_url` sem type hints completos. As 7 ocorrências de `# type: ignore` já mapeadas em AUD-011 cobrem esses casos via supressão. Solução adequada: `redis-stubs` (existem stubs externos) ou casts locais.

**Cross-referências**:
- Combina com AUD-011 (22 `# type: ignore`, 12 derivados desse mesmo padrão em parsers de IA).
- Combina com AUD-014 (`aioredis.from_url` cria conexão por chamada; refatorar para pool persistente resolve **três** achados de uma vez: AUD-011, AUD-014 e AUD-046 linhas 135/143).
- Combina com AUD-002/AUD-016 do plano de refatoração de IA — a tipagem do payload Groq cabe no mesmo PR que extrai `BaseAIFoodParser` (AUD-015).

**Recomendação compacta**: adicionar `TypedDict`s da Groq e tipar `messages` cobre 3 erros (69/79/106); migrar `aioredis.from_url` para pool persistente (compartilhado com AUD-014) elimina os outros 3. Esforço **S** isolado, mas faz mais sentido bundlear no PR de refatoração de IA.

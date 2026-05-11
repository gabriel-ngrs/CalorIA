# Frente I — Qualidade

**Plano:** ver `plano.md` § Frente I.

## Achados desta frente

- AUD-045 — 14 erros ruff pré-existentes (1 em `app/`, 13 em `scripts/`); um deles (F821 em `scripts/import_off_local.py:440`) é bug funcional latente (🟢 baixa, mas com gotcha no `--fix`).

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

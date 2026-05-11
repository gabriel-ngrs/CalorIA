# Frente I — Qualidade

**Plano:** ver `plano.md` § Frente I.

## Achados desta frente

- AUD-045 — 14 erros ruff pré-existentes (1 em `app/`, 13 em `scripts/`); um deles (F821 em `scripts/import_off_local.py:440`) é bug funcional latente (🟢 baixa, mas com gotcha no `--fix`).
- AUD-046 — 6 erros mypy strict concentrados em `app/services/ai/ai_client.py` — duas classes: tipos do `messages` da Groq SDK e `aioredis.from_url` não-tipada (🟢 baixa).
- AUD-047 — Pre-commit hooks cobrem ruff + utilitários mas faltam mypy, ESLint, tsc, secret scanner (gitleaks) — gaps de defesa em camadas (🟡 média; sobe para 🟠 com AUD-038 no histórico).
- AUD-048 — `.dockerignore` ausente em `backend/` e `frontend/` — `COPY . .` arrasta `.venv`, `node_modules`, `.next`, `.git`, `.env`, tests e `docs/` para a imagem (🟡 média; bloat + risco de leak via `.env` se commitado por engano).

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

### § I.3 ESLint frontend (de `artefatos/baseline-eslint.txt`)

**1 warning, 0 errors.**

| Severidade | Arquivo:linha | Regra | Mensagem |
|---|---|---|---|
| Warning | `components/auth/Plasma.tsx:155` | `react-hooks/exhaustive-deps` | `containerRef.current` provavelmente mudou no momento em que a cleanup do effect roda — copiar para variável local dentro do effect |

**Contexto**: `Plasma.tsx` é o componente decorativo de fundo da tela de auth (background animado WebGL via biblioteca `ogl`). Linhas 134-160 são um `useEffect` que: (1) cria renderer/scene/mesh; (2) attach canvas no `containerRef.current`; (3) inicia loop `requestAnimationFrame`; (4) cleanup remove o canvas via `containerRef.current?.removeChild(canvas)`. A regra `exhaustive-deps` flagga o uso de `containerRef.current` na cleanup porque o ref **pode ter sido reassinado** (re-render ou navegação) antes da cleanup rodar — em vez de remover o canvas que **este** effect criou, o código poderia tentar remover de um container errado, gerando exceção (já está envolto em `try { } catch {}` defensivo, o que mascara o problema).

**Fix idiomático React** (5 min):

```tsx
useEffect(() => {
  const container = containerRef.current;   // snapshot
  if (!container) return;
  // ... usar `container.appendChild(canvas)`
  return () => {
    // ... usar `container.removeChild(canvas)` (não `containerRef.current`)
  };
}, [speed, scale, opacity]);
```

**Impacto real**: pequeno. O componente só renderiza na rota `/login` (estática, sem re-renders frequentes). O `try/catch` esconde qualquer erro. Mas como single warning do projeto inteiro, vale o cleanup — deixa baseline em **0 warnings** e libera CI estrito (`eslint --max-warnings=0`).

**Sem achado dedicado** — 1 warning de cosmética não justifica entrada em `achados.md`. Anotado aqui para inclusão em PR genérico de "frontend cleanup" (combina bem com AUD-022 — extração de `useVoiceCapture` para resolver duplicação SpeechRecognition).

### § I.4 Pre-commit hooks atuais (de `artefatos/I4-precommit.txt`)

**`.pre-commit-config.yaml` mapeado** — 2 repos, 8 hooks:

| Hook | Origem | Escopo | Estado |
|---|---|---|---|
| `ruff` (com `--fix`) | astral-sh/ruff-pre-commit v0.8.0 | `^backend/` | ✅ ativo |
| `ruff-format` | astral-sh/ruff-pre-commit v0.8.0 | `^backend/` | ✅ ativo |
| `trailing-whitespace` | pre-commit-hooks v5.0.0 | global | ✅ ativo |
| `end-of-file-fixer` | pre-commit-hooks v5.0.0 | global | ✅ ativo |
| `check-yaml` | pre-commit-hooks v5.0.0 | global | ✅ ativo |
| `check-merge-conflict` | pre-commit-hooks v5.0.0 | global | ✅ ativo |
| `check-added-large-files` (`--maxkb=1000`) | pre-commit-hooks v5.0.0 | global | ✅ ativo |
| `no-commit-to-branch` (`--branch main`) | pre-commit-hooks v5.0.0 | global | ✅ ativo |

**Gaps mapeados** (alinhados com runbook):

| Hook | Estado | Por quê falta |
|---|---|---|
| `mypy` | ❌ ausente | Type checking só roda em `make typecheck` / CI; commits podem regredir tipos silenciosamente |
| `eslint` (frontend) | ❌ ausente | Único warning do projeto (AUD-046 cobertura) passou batido sem CI estrito |
| `tsc --noEmit` (frontend) | ❌ ausente | TypeScript estrito do frontend só em `make typecheck` / CI |
| `gitleaks` ou equivalente | ❌ ausente | **Crítico** — AUD-038 (credenciais em e2e) teria sido bloqueado no commit se houvesse secret scan; recomendação reforçada em § (4) do plano de AUD-038 |
| Build sanity (`npm run build` / `uvicorn --check`) | ❌ ausente | Aceitável (lento demais para pre-commit; melhor em CI) |

**Observação importante**: o hook `no-commit-to-branch --branch main` ✅ protege contra commit direto na `main` (alinhado com fluxo `dev` → PR → `main`). Mas o atalho hoje é trivial — `git commit --no-verify` bypassa tudo. Nenhum hook é à prova de quem realmente quer desviar; o valor é em pegar acidentes.

**Cross-referências**:
- AUD-038 (credenciais hardcoded em `e2e/auth.spec.ts`) **seria pego** por `gitleaks` rodando como pre-commit hook. A senha `***REMOVED***` é detectável pela regex de Generic API Key / High Entropy String que vem no `gitleaks` default config.
- AUD-045 (ruff em `scripts/`) **não é pego** pelo hook atual porque `files: ^backend/` cobre `^backend/scripts/`, mas a regra é restritiva quanto a quais files passam pelo ruff; verificar se o hook efetivamente roda em scripts/ ou se está bypassed por config local.

**Recomendação consolidada** (AUD-047): adicionar 3 hooks ao `.pre-commit-config.yaml`:

```yaml
- repo: https://github.com/pre-commit/mirrors-mypy
  rev: v1.13.0
  hooks:
    - id: mypy
      files: ^backend/app/
      additional_dependencies: [pydantic, types-passlib]
      args: [--strict]

- repo: https://github.com/gitleaks/gitleaks
  rev: v8.21.2
  hooks:
    - id: gitleaks

- repo: local
  hooks:
    - id: eslint-frontend
      name: ESLint frontend
      entry: bash -c 'cd frontend && npx next lint --max-warnings=0'
      language: system
      files: ^frontend/.*\.(ts|tsx|js|jsx)$
      pass_filenames: false
```

A escolha de `eslint` como `local` hook é deliberada — o repo de ESLint pre-commit empacotado tem problemas conhecidos com Next.js 14; rodar via `next lint` é mais confiável.

### § I.6 Dead code (de `artefatos/I5-dead-code.txt`)

**Resumo: nenhum dead code real detectado.** Os hits do vulture e do `find -size 0` são todos falsos positivos esperados.

**`__init__.py` vazios** (12 arquivos, todos esperados):

```
backend/app/__init__.py
backend/app/api/__init__.py
backend/app/core/__init__.py
backend/app/services/__init__.py
backend/app/services/ai/__init__.py
backend/app/services/nutrition/__init__.py
backend/app/services/reminders/__init__.py
backend/app/workers/__init__.py
backend/app/workers/tasks/__init__.py
backend/tests/__init__.py
backend/tests/integration/__init__.py
backend/tests/unit/__init__.py
```

Todos marcadores padrão de pacote Python — não são dead code. (`tests/__init__.py` e `tests/unit/__init__.py` ajudam o pytest a resolver imports.)

**Vulture (6 hits @ confidence 100%, todos falso positivo):**

| Linha | Var | Por que é falso positivo |
|---|---|---|
| `app/core/database.py:30` | `cursor` | parâmetro do listener `before_cursor_execute` da SQLAlchemy — assinatura obrigatória |
| `app/core/database.py:32` | `parameters` | idem |
| `app/core/database.py:34` | `executemany` | idem |
| `app/core/database.py:42` | `cursor` | parâmetro do listener `after_cursor_execute` |
| `app/core/database.py:44` | `parameters` | idem |
| `app/core/database.py:46` | `executemany` | idem |

SQLAlchemy chama esses listeners com **todos** os argumentos posicionais; o handler não pode renomear/remover. Convenção em outros projetos é prefixar com `_` (ex.: `_cursor`, `_parameters`) para silenciar warnings — neutro funcionalmente. **Sem achado dedicado**.

**Cross-ref com outros achados que tocam dead code real (já mapeados):**
- AUD-034 — `MealSource.TELEGRAM` e `MealSource.WHATSAPP` (enum legado da era pré-Groq, sem usos no backend) → **dead schema** real, mas precisa de migração Alembic para remover do banco, e tabela `meals` está vazia.
- AUD-027 hardcode `2000` em `reminders.py` ao lado de `user.water_goal_ml` declarado mas não usado por esse worker → **dead read** funcional (campo existe, valor é ignorado), não dead code estrutural.

**Notas extras (sem achado):**
- O comentário identificado em AUD-013 (`logger.info("Groq tokens — entrada: %d, saída: %d", ...)` em `ai_client.py:111`) é log órfão (sem dimensão para agregar), não dead code.
- Pasta `app/services/reminders/__init__.py` é vazia E a lógica de reminders está em `app/services/reminder_service.py` (raiz) — **smell** de pacote planejado mas não materializado. Não é dead code (não polui imports), mas o diretório poderia ser removido. Anotado como nota — não merece achado dedicado.

**Recomendação opcional** (sem PR dedicado):
- Prefixar com `_` os 6 parâmetros não-usados dos listeners em `database.py` — silencia vulture com confiança 100% e libera baseline limpa para inclusão eventual no CI (`vulture --min-confidence 80` rodando como check informativo).
- Remover `app/services/reminders/` se confirmar que não vai materializar como módulo separado.

### § I.7 Dockerfiles (4 arquivos analisados)

**Checklist consolidado:**

| Item | `backend/Dockerfile` | `backend/Dockerfile.dev` | `frontend/Dockerfile` | `frontend/Dockerfile.dev` |
|---|---|---|---|---|
| Multi-stage build | ✅ builder → runtime | ❌ single-stage (esperado em dev) | ✅ deps → builder → runner | ❌ single-stage (esperado em dev) |
| Usuário não-root no final stage | ✅ `appuser` (sem UID fixo) | ⚠️ roda como root (aceitável em dev) | ✅ `nextjs:nodejs` UID 1001 | ⚠️ roda como root |
| HEALTHCHECK no Dockerfile | ❌ ausente | ❌ ausente | ❌ ausente | ❌ ausente |
| HEALTHCHECK no compose | ✅ presente (compose:43) | ✅ (compose.dev:43) | — | — |
| Base image atualizada | ✅ `python:3.12-slim` | ✅ | ✅ `node:20-alpine` | ✅ |
| Cache de deps separado do código | ✅ `COPY pyproject.toml` antes de `COPY . .` | ✅ | ✅ `COPY package*.json` antes | ✅ |
| Sem secrets no ENV/ARG | ⚠️ ok no backend | ✅ | ❌ ver AUD-039 abaixo | ✅ |
| `.dockerignore` presente | ❌ **AUSENTE** | — | ❌ **AUSENTE** | — |

**Detalhes por arquivo:**

**`backend/Dockerfile`** (55 LOC, multi-stage builder + runtime, ✅ bem estruturado):
- Build deps (`gcc`, `libpq-dev`) só no builder; runtime fica com `libpq5` apenas — boa enxugada.
- `--workers 2` no `uvicorn` (linha 55) — pontua o cálculo de AUD-035 (pool sizing): 2 workers × pool 30 = até 60 conexões só do backend, vs `max_connections=100` do Postgres.
- Falta `ENV PYTHONUNBUFFERED=1` e `ENV PYTHONDONTWRITEBYTECODE=1` — convenções de Docker Python que evitam bufferização de logs em stdout.

**`backend/Dockerfile.dev`** (22 LOC, single-stage):
- Roda como root — aceitável em dev mas vale anotar.
- Não copia código (volume mount no compose).

**`frontend/Dockerfile`** (60 LOC, 3-stage deps + builder + runner, ✅ bem estruturado, Next.js standalone):
- **`ARG NEXTAUTH_SECRET=insecure-secret-change-in-production`** (linha 30) + `ENV NEXTAUTH_SECRET=$NEXTAUTH_SECRET` (linha 33) — default inseguro sem fail-fast. Cross-ref: **mesmo padrão de AUD-039**; `docker-compose.yml:89` propaga `${NEXTAUTH_SECRET:-insecure-secret-change-in-production}` para o build arg, então se a env de prod não tiver `NEXTAUTH_SECRET`, a imagem é construída com o default. Esse default é **embedded** na imagem porque `NEXTAUTH_SECRET` precisa estar disponível em build time (Next.js inline em alguns paths). Recomendação combinada com AUD-039: o mesmo validator fail-fast no backend deve ter contraparte no frontend — `next.config.mjs` pode falhar build em produção se `NEXTAUTH_SECRET` for o default ou string vazia.
- `NEXT_TELEMETRY_DISABLED=1` ✅ (boa prática).

**`frontend/Dockerfile.dev`** (20 LOC, single-stage): roda como root, sem `COPY . .` (volume mount), OK para dev.

**`.dockerignore` AUSENTE em backend/ e frontend/** — `COPY . .` (backend:46 e frontend:22) arrasta para a imagem:

- **Backend**: `.venv/`, `__pycache__/`, `.git/`, `tests/`, `alembic/versions/` (todas as migrações, ok), `*.pyc`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `coverage.xml`, `docs/auditoria/` se estiver dentro do contexto (não está, mas o build context é `backend/`, então não arrasta `docs/`), e potencialmente `.env` se commitado por engano (hoje gitignored ✅).
- **Frontend**: `node_modules/` (sobrescrito pelo `--from=deps`, mas inflado no build context upload), `.next/` (gerado), `.git/`, `coverage/`, `e2e/test-results/`.

**Consequências mensuráveis**:
- Build context upload: `node_modules/` típico no projeto Next 14 + shadcn é 200-400 MB. Cada `docker build` envia tudo isso para o daemon antes de descartar.
- Cache invalidation: alterar qualquer arquivo no working tree (mesmo um `.pyc`) invalida o `COPY . .` e força rebuild das camadas posteriores.
- **Risco de leak**: se alguém commit acidentalmente `.env` (não bloqueado por pre-commit), a próxima build embute o arquivo. AUD-038 mostra que commit de credenciais já aconteceu — `.dockerignore` é defesa em profundidade nesse vetor.

**Recomendação (AUD-048)** — criar `backend/.dockerignore` e `frontend/.dockerignore`:

```
# backend/.dockerignore
.venv/
__pycache__/
*.pyc
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
coverage.xml
htmlcov/
.git/
.gitignore
.env
.env.*
tests/
README.md
```

```
# frontend/.dockerignore
node_modules/
.next/
.git/
.env
.env.*
e2e/test-results/
playwright-report/
coverage/
*.log
README.md
.eslintcache
```

Esforço S (< 30 min). Reduz build context para < 5 MB em ambos, melhora cache hit rate, blinda contra leak de `.env`.

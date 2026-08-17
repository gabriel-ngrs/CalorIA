---
versão: 1.0
status: estável
atualizado: 2026-07-01
projeto: CalorIA
---

# Constitution do projeto: CalorIA

## Stack

- **Linguagem backend:** Python 3.12
- **Framework web:** FastAPI (Uvicorn) — API REST v1
- **ORM/migrações:** SQLAlchemy 2.x (async, asyncpg) + Alembic
- **Filas/agendamento:** Celery + Redis (broker, backend, cache, blacklist de token)
- **Validação:** Pydantic v2 + pydantic-settings
- **Auth backend:** JWT HS256 (python-jose) + bcrypt (uso direto, sem passlib para hashing)
- **IA:** Groq — texto `openai/gpt-oss-120b`, visão `qwen/qwen3.6-27b` (nomes vêm de `GROQ_TEXT_MODEL`/`GROQ_VISION_MODEL`, nunca fixos no código)
- **Outros:** httpx, pywebpush (VAPID), pillow, rapidfuzz
- **Banco:** PostgreSQL 16 (tabela `foods` unificada TACO+Open Food Facts+USDA, índice GIN pg_trgm) + Redis 7
- **Frontend:** Next.js 14 (App Router) + TypeScript 5 + React 18
- **UI:** shadcn/ui (Radix) + Tailwind CSS 3 + Recharts + sonner
- **Estado/dados:** TanStack Query 5 + axios
- **Auth frontend:** next-auth 4 (CredentialsProvider embrulhando o JWT do backend)
- **Testes:** pytest (backend), Jest + Playwright (frontend)
- **Qualidade:** ruff + mypy strict (backend), ESLint + tsc (frontend)
- **Infra:** Docker Compose (dev/prod), Caddy (HTTPS), GitHub Actions (CI/CD SSH)

## Padrão arquitetural

Arquitetura em camadas no backend: `api/` (endpoints finos) → `services/` (lógica de negócio, classes com injeção de dependência via `__init__(self, db)`) → `models/` (SQLAlchemy) + `schemas/` (Pydantic). Tarefas assíncronas em `workers/` (Celery). IA isolada em `services/ai/` como pipeline de dois estágios (identificação → lookup pg_trgm com sanity check → fallback estimativa). Frontend em App Router com hooks React Query por domínio consumindo a API via `lib/api.ts`.

## Regras invariantes específicas

- **Lógica de negócio vive em `services/`, nunca nos endpoints.** Endpoints só orquestram (validar entrada, chamar service, mapear resposta). Services são classes com `db` injetado.
- **`GROQ_API_KEY` nunca é exposta ao frontend.** Toda chamada de IA passa pelo backend; o frontend nunca fala direto com o Groq.
- **Commits em Conventional Commits em português**, descrição no imperativo e minúsculas. **Nunca** mencionar autor/IA/agente nem adicionar `Co-Authored-By`.
- **Todos os tipos anotados; `mypy --strict` deve passar** (comando `mypy app/`). Código novo sem anotação completa não está pronto.
- **Fotos de comida não são persistidas** — apenas os dados nutricionais extraídos da análise.
- **Banco nutricional é a tabela `foods`** (não `taco_foods`); o sanity check calórico (divergência > 35% entre banco e estimativa da IA descarta o match) protege contra registros incorretos.
- **Nunca commitar `.env`, chaves ou segredos** (`vapid_private.pem`, credenciais). `.env` deriva de `.env.example`.
- **Toda spec é enumerada cronologicamente.** Ao criar uma nova spec (via `/create-spec` ou manual), atribuir o próximo número sequencial de 3 dígitos (`NNN`) lido de `.codeflow/specs/INDEX.md` (`proximo_numero`), usá-lo como prefixo da pasta/slug (`.codeflow/specs/NNN-<slug>/`) e como `id` no frontmatter, registrar a spec na tabela de `specs/INDEX.md` e incrementar `proximo_numero`. Números não são reusados nem reordenados. Convenção completa em `.codeflow/specs/INDEX.md`.

## Áreas de alto risco

- **`backend/app/core/security.py` + fluxo de auth (`api/v1/auth.py`, `services/auth_service.py`, `core/deps.py`)** — JWT, bcrypt, blacklist de refresh token em Redis. Mudança aqui exige teste e revisão cuidadosa. Nota: `SECRET_KEY` tem default inseguro sem fail-fast (AUD-039) — tratar como sensível.
- **`backend/app/services/ai/`** — `food_lookup` (pg_trgm) + sanity check calórico + pipeline de parsers. Regressão gera dados nutricionais errados; `food_lookup` tem N+1 e Seq Scan conhecidos (AUD-006/016).
- **`backend/alembic/` (schema do banco)** — toda mudança de schema exige migration gerada e revisada. Migrations já aplicadas são imutáveis (ver off-limits em `discovered.md`).
- **Web Push / VAPID** — chaves VAPID e `push_subscriptions`; subscriptions expiradas (HTTP 410) removidas pelo PushService. Erro derruba notificações ou vaza chave.

## Definition of Done específica

- `ruff check .` e `ruff format --check .` sem erros no backend.
- `mypy app/` (strict) sem erros.
- `pytest` passando; código novo com teste correspondente.
- Frontend: `npm run lint` e `npx tsc --noEmit` sem erros.
- Mudança de schema acompanhada de migration Alembic revisada.
- `make check` (agregador que reproduz o CI) verde antes de abrir PR.

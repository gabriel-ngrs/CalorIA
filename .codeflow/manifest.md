---
versão: 1.0
status: estável
atualizado: 2026-07-01
projeto: CalorIA
last_validated: 2026-07-01
validation_hash: ee90aedeb90f5c109085cb7f6e3c9d79e8ebe6ab7ccdd5effa16fe740e0ff46d
---

# Manifest do projeto: CalorIA

## Stack identificada

- **Backend:** Python 3.12 (`requires-python >=3.12`, CI usa 3.12)
- **FastAPI** >=0.115.0, Uvicorn[standard] >=0.32.0, python-multipart >=0.0.12
- **SQLAlchemy[asyncio]** >=2.0.0, asyncpg >=0.29.0, Alembic >=1.13.0
- **Pydantic[email]** >=2.9.0, pydantic-settings >=2.6.0
- **Auth:** python-jose[cryptography] >=3.3.0, passlib[bcrypt] >=1.7.4 (hashing usa `bcrypt` direto)
- **Celery[redis]** >=5.4.0, redis >=5.2.0
- **IA:** groq >=0.13.0 (texto `openai/gpt-oss-120b`, visão `qwen/qwen3.6-27b` — ambos por `.env`, ver `core/config.py`)
- **httpx** >=0.27.0, pywebpush >=2.0.0, pillow >=11.0.0, rapidfuzz >=3.0.0
- **Qualidade backend:** ruff >=0.8.0 (line-length 88, regras E/F/W/I/N/B/UP), mypy >=1.13.0 (strict, plugin pydantic)
- **Testes backend:** pytest >=8.0.0, pytest-asyncio, pytest-cov
- **Frontend:** Next.js ^14.2.0, React ^18, TypeScript ^5
- **UI:** shadcn/ui + Radix, Tailwind CSS ^3, Recharts ^2, lucide-react, sonner ^2
- **Dados/estado:** @tanstack/react-query ^5, axios ^1, react-hook-form ^7, zod ^4
- **Auth frontend:** next-auth ^4.24.0 (CredentialsProvider), next-themes
- **Testes frontend:** jest ^29 + @testing-library, @playwright/test ^1.59
- **Banco:** PostgreSQL 16, Redis 7 (imagens de CI e compose)
- **Infra:** Docker Compose (dev/prod/backend), Caddy (HTTPS), GitHub Actions

## Comandos de validação

| Gate        | Comando real do projeto                                             | Status |
|-------------|---------------------------------------------------------------------|--------|
| `check`     | `make check` → `lint-check` + `typecheck` + `test-unit` + `test-frontend` (Makefile) | ✓ |
| `lint`      | backend `ruff check .` + `ruff format --check .` · frontend `npm run lint` (Makefile `lint-check`; CI: `ruff check .`, `npm run lint`) | ✓ |
| `typecheck` | backend `mypy app/` · frontend `npx tsc --noEmit` (Makefile `typecheck`; CI: `mypy app/`) | ✓ |
| `test`      | backend `pytest` (CI: `pytest --cov=app --cov-report=xml -q`) · frontend `npm test` / `jest --passWithNoTests` | ✓ |
| `security`  | não há gate configurado no CI/Makefile; baselines pontuais via `pip-audit` / `npm audit` (docs/auditoria) | [—] |

Fontes: `Makefile` (alvos `check`, `lint-check`, `typecheck`, `test-unit`, `test-frontend`), `backend/pyproject.toml` (config ruff/mypy/pytest), `frontend/package.json` (scripts), `.github/workflows/ci.yml`.

## Padrões detectados

- **Backend em camadas:** endpoints finos em `app/api/v1/` (10 routers, 47 endpoints) delegam a services; lógica de negócio em `app/services/*` como classes com `__init__(self, db: AsyncSession)`.
- **Injeção de dependência FastAPI:** `Depends(get_db)` e `Depends(get_current_user_id)` (HTTPBearer) em todas as rotas autenticadas; `user_id` sempre derivado do token.
- **IA como pipeline de dois estágios:** `meal_parser` identifica alimentos (Groq) → `food_lookup` (pg_trgm, threshold 0.65, boost TACO 1.40×) → sanity check calórico 35% → fallback `_estimate_macros_batch` agrupado. Prompts em português com porções brasileiras.
- **Models SQLAlchemy 2.x tipados:** `Mapped[...]` + `mapped_column`, enums via `StrEnum`, `User` como entidade central com relationships `cascade="all, delete-orphan"`.
- **Workers Celery com Beat:** tarefas síncronas envolvem corrotina via helper `_run(coro)`; agenda de 6 tarefas periódicas; TZ `America/Sao_Paulo`.
- **Frontend App Router + React Query:** 8 hooks por domínio (`useMeals`, `useDashboard`, `useAI`, …) sobre `lib/api.ts` (axios); auth via next-auth CredentialsProvider que embrulha o JWT do backend, com refresh proativo.
- **Respostas tipadas:** endpoints usam `response_model` Pydantic; frontend espelha em `types/index.ts` com augmentation de sessão next-auth.

## Arquivos críticos para freshness

Hash `validation_hash` computado sobre os arquivos abaixo, nesta ordem (arquivos ausentes contribuem como vazio):

- `backend/pyproject.toml`
- `backend/uv.lock`
- `frontend/package.json`
- `frontend/package-lock.json`
- `Makefile`
- `backend/alembic.ini`
- `frontend/.eslintrc.json`
- `frontend/tsconfig.json`

## Notas de inspeção

- Projeto inspecionado em 2026-07-01 por `/discover` (modo onboarding).
- Inspeção profunda arquivo a arquivo do backend (core, api, services, ai, workers, models, schemas, tests, migrations), frontend (páginas, componentes, hooks, api client, seam de auth, types, middleware, e2e) e infra (Dockerfiles, compose, Caddy, CI/CD, pre-commit).
- Baseline de qualidade (auditoria 2026-05-10/11, revalidado hoje): ruff 14 erros (9 auto-fixáveis), mypy 6 erros em `ai_client.py`, cobertura pytest 62%, npm audit 16 vulns. Detalhe completo em `docs/auditoria/`.
- Métricas: 5.708 LOC backend, 10.573 LOC frontend, 47 endpoints, 12 modelos, 10 migrations Alembic.
- Drift de versão observado: CHANGELOG em `0.7.0`, `pyproject.toml`/`main.py` em `0.1.0` (AUD-054). `.pyc` órfãos residuais em `backend/app/bots/` (fonte removida em v0.7.0).

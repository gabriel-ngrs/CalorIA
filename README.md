# CalorIA

Diário alimentar inteligente com IA. Registre refeições pelo dashboard web, acompanhe macros, peso, hidratação e humor.

[![CI](https://github.com/gabriel-ngrs/CalorIA/actions/workflows/ci.yml/badge.svg)](https://github.com/gabriel-ngrs/CalorIA/actions/workflows/ci.yml)

---

## Funcionalidades

- **Registro via web** — descreva em texto ou envie foto da refeição; a IA consulta o banco nutricional (TACO + Open Food Facts, ~19.800 alimentos) com sanity check calórico antes de calcular os macros
- **Dashboard web** — interface glassmorphism com gráficos de calorias, macros, evolução de peso e hidratação
- **Tracking completo** — peso corporal, hidratação, humor e energia com métricas de período
- **Lembretes com Web Push** — notificações nativas no browser/mobile para refeições, água e resumo diário
- **Insights personalizados** — IA analisa padrões, detecta deficiências nutricionais e sugere ajuste de metas
- **PWA** — instalável no celular como app nativo

---

## Stack

| Camada | Tecnologia |
|---|---|
| Backend API | Python 3.12 + FastAPI |
| Banco de dados | PostgreSQL 16 |
| Cache / Filas | Redis 7 |
| Workers | Celery + Celery Beat |
| IA | Google Gemini 2.5 Flash (`google-genai`) |
| Notificações | Web Push VAPID (pywebpush) |
| Frontend | Next.js 14 + TypeScript + shadcn/ui (Glassmorphism) |
| ORM | SQLAlchemy 2 (async) + Alembic |
| Infra | Docker Compose + Caddy (HTTPS) |
| CI/CD | GitHub Actions |

---

## Pré-requisitos

- Docker e Docker Compose
- Python 3.12+ (para desenvolvimento local sem Docker)
- Node.js 20+ (para desenvolvimento do frontend sem Docker)
- Google Gemini API Key — gratuito em [aistudio.google.com](https://aistudio.google.com/app/apikey)

---

## Instalação

### 1. Clonar o repositório

```bash
git clone https://github.com/gabriel-ngrs/CalorIA.git
cd CalorIA
```

### 2. Configurar variáveis de ambiente

```bash
cp .env.example .env
```

Edite o `.env` com suas credenciais:

```env
DATABASE_URL=postgresql+asyncpg://caloria:caloria@postgres:5432/caloria_db
REDIS_URL=redis://redis:6379/0
SECRET_KEY=sua-chave-secreta-aqui-min-32-chars
GEMINI_API_KEY=sua-chave-gemini-aqui
NEXTAUTH_SECRET=sua-chave-nextauth
NEXTAUTH_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000

# Web Push VAPID (necessário para notificações)
VAPID_PUBLIC_KEY=sua-chave-publica-vapid
VAPID_KEY_PATH=/caminho/para/vapid_private.pem
VAPID_CLAIMS_EMAIL=seu@email.com
```

### 3. Subir os serviços

```bash
# Desenvolvimento (hot reload)
docker compose -f docker-compose.dev.yml up

# Produção local
docker compose up -d
```

### 4. Executar migrações

```bash
docker compose exec backend alembic upgrade head
```

### 5. Acessar

| Serviço | URL |
|---|---|
| Dashboard | http://localhost:3000 |
| API | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |

---

## Estrutura do Projeto

```
CalorIA/
├── .github/
│   └── workflows/
│       ├── ci.yml          # CI: lint, testes, build (push dev / PR main)
│       └── cd.yml          # CD: deploy automático (merge main)
├── backend/
│   ├── app/
│   │   ├── api/            # Endpoints REST (v1)
│   │   ├── core/           # Config, DB, segurança
│   │   ├── models/         # Modelos SQLAlchemy
│   │   ├── schemas/        # Schemas Pydantic
│   │   ├── services/       # Lógica de negócio + IA (Gemini)
│   │   └── workers/        # Tasks Celery
│   ├── alembic/            # Migrações de banco
│   ├── scripts/            # Seed e utilitários
│   └── tests/
├── frontend/
│   ├── app/                # Next.js App Router (páginas)
│   ├── components/         # Componentes React
│   ├── lib/                # Utils, API client, hooks
│   └── types/              # TypeScript types
├── docs/
│   ├── architecture.md     # Decisões de arquitetura (ADRs)
│   ├── setup.md            # Guia de setup do zero
│   ├── deploy.md           # Guia de deploy em produção (Hetzner)
│   ├── git-workflow.md     # Estratégia de branches e CI/CD
│   └── flow.md             # Fluxo do registro ao banco
├── scripts/                # Scripts de servidor e deploy
├── Caddyfile               # Reverse proxy (HTTPS produção)
├── docker-compose.yml      # Produção
├── docker-compose.dev.yml  # Desenvolvimento
└── .env.example
```

---

## Desenvolvimento

```bash
# Testes backend
cd backend && pytest

# Testes com cobertura
cd backend && pytest --cov=app --cov-report=html

# Lint e type check
cd backend && ruff check . && mypy app/

# Testes frontend
cd frontend && npm test

# Lint frontend
cd frontend && npm run lint
```

---

## Deploy

Ver [`docs/deploy.md`](docs/deploy.md) para o guia completo de deploy no Hetzner.

O CI/CD está configurado via GitHub Actions:
- **Push na `dev`** → roda lint, testes e build
- **Merge na `main`** → deploy automático no servidor via SSH

Ver [`docs/git-workflow.md`](docs/git-workflow.md) para a estratégia de branches.

---

## Convenções de Commit

Conventional Commits em português:

```bash
feat(frontend): adiciona suporte a análise de foto na web
fix(api): corrige cálculo de macros para refeições compostas
docs(readme): atualiza instruções de instalação
chore(deps): atualiza dependências do backend
```

---

## Limites do Free Tier (Gemini 2.5 Flash)

| Recurso | Limite |
|---|---|
| Requisições por minuto | 10 RPM |
| Tokens por minuto | 250.000 |
| Requisições por dia | 500 |

O projeto implementa cache Redis (7 dias, SHA-256) para reduzir chamadas redundantes, e o banco nutricional local (~19.800 alimentos) evita chamadas à IA para cálculo de macros de alimentos comuns.

---

## Licença

Projeto pessoal. Todos os direitos reservados.

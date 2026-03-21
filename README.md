# CalorIA

Diário alimentar inteligente com IA. Registre refeições via WhatsApp ou Telegram, acompanhe macros, peso, hidratação e humor pelo dashboard web.

[![CI](https://github.com/gabriel-ngrs/CalorIA/actions/workflows/ci.yml/badge.svg)](https://github.com/gabriel-ngrs/CalorIA/actions/workflows/ci.yml)

---

## Funcionalidades

- **Registro via mensagem** — envie texto ou foto da refeição no WhatsApp ou Telegram; a IA consulta o banco TACO (~600 alimentos brasileiros) e calcula os macros com sanity check calórico
- **Dashboard web** — interface glassmorphism com gráficos de calorias, macros, evolução de peso e hidratação
- **Tracking completo** — peso corporal, hidratação, humor e energia com métricas de período
- **Lembretes inteligentes** — notificações de refeição, água e resumo diário via Telegram/WhatsApp
- **Insights personalizados** — IA analisa padrões, detecta deficiências nutricionais e sugere ajuste de metas
- **Multi-canal** — use Telegram e WhatsApp simultaneamente

---

## Stack

| Camada | Tecnologia |
|---|---|
| Backend API | Python 3.12 + FastAPI |
| Banco de dados | PostgreSQL 16 |
| Cache / Filas | Redis 7 |
| Workers | Celery + Celery Beat |
| IA | Google Gemini 2.5 Flash |
| Bot Telegram | python-telegram-bot |
| Bot WhatsApp | Evolution API (self-hosted) |
| Frontend | Next.js 14 + TypeScript + shadcn/ui |
| ORM | SQLAlchemy 2 (async) + Alembic |
| Infra | Docker Compose + Caddy (HTTPS) |
| CI/CD | GitHub Actions |

---

## Screenshots

### Dashboard Principal (Desktop)
![Dashboard](screenshots/desktop-dashboard.png)

### Refeições e Análise por IA (Desktop)
![Refeições](screenshots/desktop-refeicoes.png)

### Evolução de Peso (Desktop)
![Peso](screenshots/desktop-peso.png)

### Hidratação (Desktop)
![Hidratação](screenshots/desktop-hidratacao.png)

### Insights da IA (Desktop)
![Insights](screenshots/desktop-insights.png)

### Dashboard Mobile
![Dashboard Mobile](screenshots/mobile-dashboard.png)

---

## Pré-requisitos

- Docker e Docker Compose
- Python 3.12+ (para desenvolvimento local sem Docker)
- Node.js 20+ (para desenvolvimento do frontend sem Docker)
- Conta Google Cloud com Gemini API habilitada (gratuito)
- Conta Telegram para criar o bot via BotFather
- WhatsApp ativo para conectar via Evolution API

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
TELEGRAM_BOT_TOKEN=seu-token-do-botfather
EVOLUTION_API_URL=http://evolution_api:8080
EVOLUTION_API_KEY=sua-chave-evolution
EVOLUTION_INSTANCE_NAME=caloria
NEXTAUTH_SECRET=sua-chave-nextauth
NEXTAUTH_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000
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
| Evolution API | http://localhost:8080 |

---

## Conectar o Telegram

1. Crie o bot no BotFather e configure `TELEGRAM_BOT_TOKEN` no `.env`
2. No dashboard web → **Conectar Bot** → gere um token
3. Envie `/conectar <token>` no Telegram

## Conectar o WhatsApp

1. Acesse `http://localhost:8080` (Evolution API)
2. Crie uma instância chamada `caloria`
3. Escaneie o QR Code com seu WhatsApp

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
│   │   ├── bots/           # Handlers Telegram e WhatsApp
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
│   └── flow.md             # Fluxo da mensagem ao banco
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
feat(bots): adiciona suporte a fotos no Telegram
fix(api): corrige cálculo de macros para refeições compostas
docs(readme): atualiza instruções de instalação
chore(deps): atualiza dependências do backend
```

---

## Limites do Free Tier (Gemini)

| Recurso | Limite |
|---|---|
| Requisições por minuto | 15 RPM |
| Tokens por minuto | 1.000.000 |
| Requisições por dia | 1.500 |

O projeto implementa cache Redis para alimentos frequentes e banco TACO embutido (~600 alimentos brasileiros) para reduzir dependência do Gemini.

---

## Licença

Projeto pessoal. Todos os direitos reservados.

# CalorIA

Diário alimentar inteligente com IA. Registre refeições via WhatsApp ou Telegram, acompanhe macros, peso, hidratação e humor pelo dashboard web.

---

## Funcionalidades

- **Registro via mensagem** — envie texto ou foto da refeição no WhatsApp ou Telegram e a IA calcula os macros automaticamente
- **Dashboard web** — gráficos de calorias, macros, evolução de peso e hidratação
- **Tracking completo** — peso corporal, hidratação, humor e energia
- **Lembretes inteligentes** — notificações de refeição, água e resumo diário
- **Insights personalizados** — IA analisa seus padrões e gera recomendações
- **Multi-canal** — use Telegram e WhatsApp simultaneamente

---

## Stack

| Camada | Tecnologia |
|---|---|
| Backend API | Python 3.12 + FastAPI |
| Banco de dados | PostgreSQL 16 |
| Cache / Filas | Redis 7 |
| Workers | Celery + Celery Beat |
| IA | Google Gemini Flash 1.5 + Vision |
| Bot Telegram | python-telegram-bot |
| Bot WhatsApp | Evolution API (self-hosted) |
| Frontend | Next.js 14 + TypeScript + shadcn/ui |
| ORM | SQLAlchemy 2 (async) + Alembic |
| Infra | Docker Compose |

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
git clone <repo-url>
cd CalorIA
```

### 2. Configurar variáveis de ambiente

```bash
cp .env.example .env
```

Edite o `.env` com suas credenciais:

```env
# Banco de dados
DATABASE_URL=postgresql+asyncpg://caloria:caloria@postgres:5432/caloria_db
REDIS_URL=redis://redis:6379/0

# Segurança
SECRET_KEY=sua-chave-secreta-aqui-min-32-chars
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30

# Google Gemini (gratuito)
GEMINI_API_KEY=sua-chave-gemini-aqui

# Telegram
TELEGRAM_BOT_TOKEN=seu-token-do-botfather

# Evolution API (WhatsApp)
EVOLUTION_API_URL=http://evolution_api:8080
EVOLUTION_API_KEY=sua-chave-evolution
EVOLUTION_INSTANCE_NAME=caloria

# Frontend
NEXTAUTH_SECRET=sua-chave-nextauth
NEXTAUTH_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Subir os serviços

```bash
# Ambiente de desenvolvimento
docker compose -f docker-compose.dev.yml up

# Ou em produção local
docker compose up -d
```

### 4. Executar migrações

```bash
docker compose exec backend alembic upgrade head
```

### 5. Acessar

| Serviço | URL |
|---|---|
| Frontend (Dashboard) | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| Evolution API | http://localhost:8080 |

---

## Conectar o WhatsApp

1. Acesse `http://localhost:8080` (Evolution API)
2. Crie uma instância chamada `caloria`
3. Escaneie o QR Code com seu WhatsApp
4. A sessão fica salva no volume Docker

---

## Conectar o Telegram

1. Abra o bot no Telegram (busque pelo nome configurado no BotFather)
2. Envie `/start`
3. No dashboard web, acesse **Conectar Bot** → gere um token
4. Envie `/conectar <token>` no Telegram

---

## Estrutura do Projeto

```
CalorIA/
├── backend/
│   ├── app/
│   │   ├── api/          # Endpoints REST
│   │   ├── bots/         # Handlers Telegram e WhatsApp
│   │   ├── core/         # Config, DB, segurança
│   │   ├── models/       # Modelos SQLAlchemy
│   │   ├── schemas/      # Schemas Pydantic
│   │   ├── services/     # Lógica de negócio + IA
│   │   └── workers/      # Tasks Celery
│   ├── alembic/          # Migrações
│   └── tests/
├── frontend/
│   ├── app/              # Next.js App Router
│   ├── components/       # Componentes React
│   └── lib/              # Utils e API client
├── docs/                 # Documentação técnica
├── CLAUDE.md             # Instruções para Claude Code
├── Roadmap.md            # Etapas de desenvolvimento
└── CHANGELOG.md          # Histórico de mudanças
```

---

## Desenvolvimento

```bash
# Rodar testes backend
cd backend && pytest

# Rodar testes com cobertura
cd backend && pytest --cov=app --cov-report=html

# Linting backend
cd backend && ruff check . && mypy app/

# Rodar testes frontend
cd frontend && npm run test

# Linting frontend
cd frontend && npm run lint

# Nova migração de banco
cd backend && alembic revision --autogenerate -m "descricao"
```

---

## Convenções de Commit

Conventional Commits em português, sem mencionar autor.

```bash
feat(bots): adiciona suporte a fotos no Telegram
fix(api): corrige cálculo de macros para refeições compostas
docs(readme): atualiza instruções de instalação
chore(deps): atualiza dependências do backend
```

A cada mudança significativa, fazer commit. Ver CLAUDE.md para detalhes completos.

---

## Limites do Free Tier (Gemini)

| Recurso | Limite |
|---|---|
| Requisições por minuto | 15 RPM |
| Tokens por minuto | 1.000.000 |
| Requisições por dia | 1.500 |

O projeto implementa cache Redis para alimentos frequentes e reduz o consumo.

---

## Roadmap

Ver [Roadmap.md](Roadmap.md) para o plano completo de desenvolvimento dividido em 9 fases.

---

## Licença

Projeto pessoal. Todos os direitos reservados.

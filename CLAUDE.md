# CLAUDE.md — CalorIA

Instruções para o agente Claude Code trabalhar neste projeto.

---

## Visão Geral do Projeto

**CalorIA** é um diário alimentar inteligente pessoal. O usuário registra refeições via WhatsApp ou Telegram (texto ou foto), e a IA (Google Gemini) analisa os macronutrientes, aprende os hábitos alimentares e gera insights personalizados. Um dashboard web permite visualizar histórico, evolução de peso, hidratação, humor/energia e relatórios.

**Uso atual:** projeto pessoal de estudo. Sem necessidade de multi-tenancy robusto agora, mas arquitetura deve permitir escalar no futuro.

---

## Arquitetura

```
CalorIA/
├── backend/              # FastAPI + Celery + Bots
│   ├── app/
│   │   ├── api/          # Endpoints REST (v1)
│   │   ├── bots/
│   │   │   ├── telegram/ # Handler Telegram
│   │   │   └── whatsapp/ # Webhook Evolution API
│   │   ├── core/         # Config, segurança, DB, dependências
│   │   ├── models/       # Modelos SQLAlchemy
│   │   ├── schemas/      # Schemas Pydantic
│   │   ├── services/
│   │   │   ├── ai/       # Integração Google Gemini
│   │   │   ├── nutrition/# Lógica de cálculo nutricional
│   │   │   └── reminders/# Lógica de lembretes
│   │   └── workers/      # Tasks Celery
│   ├── alembic/          # Migrações de banco
│   ├── scripts/          # Utilitários: seed, importação de dados
│   ├── tests/
│   └── Dockerfile
├── frontend/             # Next.js 14 + shadcn/ui
│   ├── app/              # App Router (páginas + manifest.ts)
│   ├── components/
│   ├── lib/              # Utils, API client, hooks
│   ├── public/           # Assets estáticos (ícones PWA)
│   ├── scripts/          # Warmup de rotas
│   ├── types/            # TypeScript types e augmentations
│   └── Dockerfile
├── docs/                 # Documentação técnica
│   ├── architecture.md   # Decisões de arquitetura (ADRs)
│   ├── setup.md          # Guia de setup do zero
│   ├── deploy.md         # Guia de deploy em produção
│   ├── flow.md           # Fluxo da mensagem ao banco
│   └── project-plan.md   # Plano e especificação do projeto
├── scripts/              # Scripts de deploy e configuração de servidor
├── Caddyfile             # Reverse proxy (produção com HTTPS)
├── docker-compose.yml    # Produção local
├── docker-compose.dev.yml# Desenvolvimento
├── .env.example
├── CLAUDE.md             ← este arquivo
├── README.md
├── CHANGELOG.md
└── Roadmap.md
```

### Serviços Docker

| Serviço | Tecnologia | Porta |
|---|---|---|
| `backend` | FastAPI (Uvicorn) | 8000 |
| `frontend` | Next.js | 3000 |
| `postgres` | PostgreSQL 16 | 5432 |
| `redis` | Redis 7 | 6379 |
| `celery_worker` | Celery | — |
| `celery_beat` | Celery Beat | — |
| `evolution_api` | Evolution API | 8080 |

---

## Stack Tecnológica

### Backend
- **Python 3.12** + **FastAPI** — API REST principal
- **SQLAlchemy 2.x** (async) + **Alembic** — ORM e migrações
- **Celery** + **Redis** — Filas de tarefas e agendamento
- **python-telegram-bot** — Integração Telegram
- **httpx** — Chamadas HTTP (Evolution API, Gemini)
- **Pydantic v2** — Validação de dados
- **python-jose** + **passlib** — JWT e hashing de senhas

### IA
- **Google Gemini Flash 1.5** — Análise de texto de refeições, insights, relatórios
- **Google Gemini Pro Vision** — Análise de fotos de comida
- **Free tier:** 15 RPM, 1 milhão de tokens/min, 1500 requisições/dia

### WhatsApp
- **Evolution API** (self-hosted Docker) — Gerencia sessão WhatsApp
- Backend recebe webhooks da Evolution API e responde via API REST dela

### Frontend
- **Next.js 14** (App Router) + **TypeScript**
- **Tailwind CSS** + **shadcn/ui** — UI components
- **Recharts** — Gráficos (macros, peso, hidratação)
- **React Query (TanStack Query)** — Cache e sync de dados
- **next-auth** — Autenticação

### Banco de Dados
- **PostgreSQL 16** — Dados primários
- **Redis 7** — Cache, filas Celery, sessões

---

## Modelos de Dados Principais

```
User — perfil, metas calóricas, dados físicos
Meal — refeição (tipo, horário, fonte: manual/telegram/whatsapp)
MealItem — alimento individual dentro de uma refeição
WeightLog — registro periódico de peso
HydrationLog — consumo de água por dia
MoodLog — humor/energia associado ao dia
Reminder — lembretes configurados pelo usuário
AIConversation — histórico de mensagens com a IA por canal
```

---

## Comandos Úteis

### Desenvolvimento
```bash
# Subir todos os serviços
docker compose -f docker-compose.dev.yml up

# Apenas infraestrutura (postgres, redis, evolution_api)
docker compose -f docker-compose.dev.yml up postgres redis evolution_api

# Backend em modo dev (hot reload)
cd backend && uvicorn app.main:app --reload --port 8000

# Frontend em modo dev
cd frontend && npm run dev

# Executar migrações
cd backend && alembic upgrade head

# Criar nova migração
cd backend && alembic revision --autogenerate -m "descricao"

# Rodar worker Celery
cd backend && celery -A app.workers.celery_app worker --loglevel=info

# Rodar Celery Beat (agendador)
cd backend && celery -A app.workers.celery_app beat --loglevel=info
```

### Testes
```bash
# Backend
cd backend && pytest

# Backend com cobertura
cd backend && pytest --cov=app --cov-report=html

# Frontend
cd frontend && npm run test

# Lint
cd backend && ruff check . && mypy app/
cd frontend && npm run lint
```

### Utilitários
```bash
# Acessar banco de dados
docker exec -it caloria_postgres psql -U caloria -d caloria_db

# Ver logs dos serviços
docker compose logs -f backend
docker compose logs -f evolution_api

# Resetar banco (desenvolvimento)
docker compose -f docker-compose.dev.yml down -v && docker compose -f docker-compose.dev.yml up
```

---

## Variáveis de Ambiente

Sempre usar `.env` baseado em `.env.example`. Nunca commitar o `.env`.

Variáveis obrigatórias:
```
DATABASE_URL
REDIS_URL
GEMINI_API_KEY
TELEGRAM_BOT_TOKEN
EVOLUTION_API_URL
EVOLUTION_API_KEY
SECRET_KEY
```

---

## Convenções de Código

### Python (Backend)
- Seguir **PEP 8** + **ruff** para linting
- **mypy** para type checking — todos os tipos anotados
- Funções async por padrão nas rotas FastAPI
- Services são classes com injeção de dependência
- Nunca colocar lógica de negócio nos endpoints — usar services
- Testes com **pytest** + **httpx AsyncClient**

### TypeScript (Frontend)
- **ESLint** + **Prettier** para linting/formatação
- Componentes em PascalCase, funções em camelCase
- Hooks customizados prefixados com `use`
- Types/interfaces em arquivos `*.types.ts`

### Estrutura de Endpoints
```
GET    /api/v1/meals          # listar refeições
POST   /api/v1/meals          # criar refeição
GET    /api/v1/meals/{id}     # buscar refeição
PUT    /api/v1/meals/{id}     # atualizar refeição
DELETE /api/v1/meals/{id}     # deletar refeição
```

---

## Convenções de Commit

Usar **Conventional Commits em português**. Não mencionar autor (Claude Code, agente, usuário, etc.).

### Formato
```
<tipo>(<escopo>): <descrição curta no imperativo>

[corpo opcional — o quê e por quê, não como]

[rodapé opcional — breaking changes, issues]
```

### Tipos
| Tipo | Uso |
|---|---|
| `feat` | Nova funcionalidade |
| `fix` | Correção de bug |
| `refactor` | Refatoração sem nova feature ou fix |
| `test` | Adição ou correção de testes |
| `docs` | Documentação |
| `chore` | Tarefas de manutenção, dependências |
| `style` | Formatação, sem mudança de lógica |
| `perf` | Melhoria de performance |
| `ci` | Mudanças em CI/CD |

### Exemplos
```bash
feat(bots): adiciona suporte a fotos no bot do Telegram
fix(api): corrige cálculo de calorias para alimentos compostos
refactor(services): extrai lógica de análise de IA para serviço dedicado
docs(readme): atualiza instruções de instalação
chore(deps): atualiza dependências do backend
feat(frontend): implementa dashboard de evolução de peso
```

### Regras
- Descrição em minúsculas, sem ponto final
- Imperativo: "adiciona", "corrige", "remove", "atualiza" (não "adicionando" ou "adicionado")
- Máximo 72 caracteres na primeira linha
- Commitar a cada mudança significativa (não acumular dias de trabalho)
- `BREAKING CHANGE:` no rodapé para mudanças que quebram compatibilidade

---

## Fluxo de Trabalho

1. Ler `Roadmap.md` para identificar a etapa atual
2. Ler os arquivos relevantes antes de modificar
3. Implementar a feature/fix
4. Rodar testes antes de commitar
5. Commitar com Conventional Commits em português
6. Atualizar `CHANGELOG.md` para mudanças relevantes
7. Marcar etapa como concluída no `Roadmap.md`

---

## Notas Importantes

- **Segurança:** Nunca expor `GEMINI_API_KEY` ou tokens no frontend. Todas as chamadas de IA passam pelo backend.
- **Privacidade:** Fotos de comida não são armazenadas permanentemente — apenas os dados nutricionais extraídos.
- **Evolution API:** Requer escanear QR Code uma vez para conectar a sessão WhatsApp. Sessão persiste em volume Docker.
- **Free tier Gemini:** Monitorar uso. Implementar rate limiting e cache de respostas para alimentos frequentes.
- **Escalabilidade futura:** Manter User como entidade central desde o início para facilitar multi-usuário no futuro.

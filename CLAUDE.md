# CLAUDE.md — CalorIA

Instruções para o agente Claude Code trabalhar neste projeto.

---

## Visão Geral do Projeto

**CalorIA** é um diário alimentar inteligente pessoal. O usuário registra refeições pelo dashboard web (texto ou foto), e a IA (Google Gemini 2.5 Flash) analisa os macronutrientes, aprende os hábitos alimentares e gera insights personalizados. Um dashboard web permite visualizar histórico, evolução de peso, hidratação, humor/energia e relatórios.

**Uso atual:** projeto pessoal de estudo. Arquitetura pensada para escalar para múltiplos usuários no futuro.

---

## Arquitetura

```
CalorIA/
├── .github/
│   └── workflows/
│       ├── ci.yml            # lint + testes + build (push dev / PR main)
│       └── cd.yml            # deploy SSH automático (merge main)
├── backend/              # FastAPI + Celery
│   ├── app/
│   │   ├── api/          # Endpoints REST (v1)
│   │   ├── core/         # Config, segurança, DB, dependências
│   │   ├── models/       # Modelos SQLAlchemy
│   │   ├── schemas/      # Schemas Pydantic
│   │   ├── services/
│   │   │   ├── ai/       # GeminiClient, MealParser, VisionParser, FoodLookup, ContextBuilder
│   │   │   ├── nutrition/# Lógica de cálculo nutricional (TDEE)
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
│   ├── deploy.md         # Guia de deploy em produção (Hetzner)
│   ├── git-workflow.md   # Estratégia de branches e CI/CD
│   ├── flow.md           # Fluxo do registro ao banco
│   └── fluxos/           # Fluxos detalhados com diagramas Mermaid
├── scripts/              # Scripts de deploy e configuração de servidor
├── Caddyfile             # Reverse proxy (produção com HTTPS)
├── docker-compose.yml    # Produção
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
| `caddy` | Caddy (HTTPS) | 80/443 |

---

## Stack Tecnológica

### Backend
- **Python 3.12** + **FastAPI** — API REST principal
- **SQLAlchemy 2.x** (async) + **Alembic** — ORM e migrações
- **Celery** + **Redis** — Filas de tarefas e agendamento
- **httpx** — Chamadas HTTP
- **Pydantic v2** — Validação de dados
- **python-jose** + **passlib[bcrypt]** — JWT e hashing de senhas
- **pywebpush** — Envio de notificações Web Push VAPID

### IA
- **Google Gemini 2.5 Flash** — `google-genai>=1.0.0`, modelo `models/gemini-2.5-flash`
- Chave: `GEMINI_API_KEY`
- Pipeline dois estágios: IA identifica alimentos → lookup pg_trgm no banco com sanity check → fallback estimativa IA agrupada

### Banco Nutricional
- Tabela `foods` no PostgreSQL: TACO (~307) + Open Food Facts (~19.500 alimentos)
- Índice GIN trigrama em `search_text` para busca fuzzy (`similarity()` + `%>>`)
- Threshold 0.65; dados TACO recebem boost 1.40× sobre Open Food Facts
- Sanity check calórico: divergência > 35% entre banco e estimativa da IA descarta o match

### Frontend
- **Next.js 14** (App Router) + **TypeScript**
- **Tailwind CSS** + **shadcn/ui** — UI components (Glassmorphism + Neumorphism)
- **Recharts** — Gráficos (macros, peso, hidratação)
- **React Query (TanStack Query)** — Cache e sync de dados
- Auth via JWT próprio (sem next-auth)

### Banco de Dados
- **PostgreSQL 16** — Dados primários
- **Redis 7** — Cache, filas Celery, JWT blacklist

### CI/CD
- **GitHub Actions** — `ci.yml` (lint + testes + build), `cd.yml` (deploy SSH)
- Ver `docs/git-workflow.md` para estratégia de branches

---

## Modelos de Dados Principais

```
User — perfil, metas calóricas, dados físicos
Meal — refeição (tipo, horário, fonte: manual)
MealItem — alimento individual com food_id, data_source e micronutrientes
Food — banco nutricional unificado (TACO + Open Food Facts)
WeightLog — registro periódico de peso
HydrationLog — consumo de água por dia
MoodLog — humor/energia associado ao dia
Reminder — lembretes configurados pelo usuário (Web Push)
PushSubscription — subscriptions Web Push por usuário/dispositivo
Notification — histórico de notificações in-app
AIConversation — histórico de mensagens com a IA
```

---

## Comandos Úteis

### Desenvolvimento
```bash
# Subir todos os serviços
docker compose -f docker-compose.dev.yml up

# Apenas infraestrutura (postgres, redis)
docker compose -f docker-compose.dev.yml up postgres redis

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
docker compose logs -f celery_worker

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
SECRET_KEY
NEXTAUTH_SECRET
NEXTAUTH_URL
NEXT_PUBLIC_API_URL
```

Variáveis para Web Push (necessárias para notificações):
```
VAPID_PUBLIC_KEY
VAPID_KEY_PATH
VAPID_CLAIMS_EMAIL
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

Usar **Conventional Commits em português**. Não mencionar autor (Claude Code, agente, usuário, etc.) nem adicionar Co-Authored-By.

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
feat(frontend): adiciona análise de foto na página de refeições
fix(ai): corrige sanity check para alimentos com gordura alta
refactor(ai): extrai food_lookup como serviço independente
docs(architecture): atualiza ADRs para Gemini 2.5 Flash
chore(deps): atualiza google-genai para 1.x
ci(github): adiciona workflow de deploy automático
```

### Regras
- Descrição em minúsculas, sem ponto final
- Imperativo: "adiciona", "corrige", "remove", "atualiza"
- Máximo 72 caracteres na primeira linha
- Commitar a cada mudança significativa

---

## Fluxo de Trabalho

1. Ler `Roadmap.md` para identificar a etapa atual
2. Ler os arquivos relevantes antes de modificar
3. Implementar a feature/fix
4. Rodar testes antes de commitar
5. Commitar com Conventional Commits em português
6. Atualizar `CHANGELOG.md` para mudanças relevantes
7. Marcar etapa como concluída no `Roadmap.md`
8. Push na `dev` → CI valida automaticamente
9. PR dev → main para release → CD faz deploy automático

---

## Notas Importantes

- **Segurança:** Nunca expor `GEMINI_API_KEY` no frontend. Todas as chamadas de IA passam pelo backend.
- **Privacidade:** Fotos de comida não são armazenadas permanentemente — apenas os dados nutricionais extraídos.
- **Web Push:** Chaves VAPID geradas uma vez e armazenadas no servidor. Subscriptions expiradas (HTTP 410) são removidas automaticamente pelo PushService.
- **Banco nutricional:** Tabela `foods` (não `taco_foods`). Sanity check calórico protege contra registros incorretos do Open Food Facts.
- **Escalabilidade futura:** Manter User como entidade central para facilitar multi-usuário no futuro.

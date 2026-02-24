# Arquitetura — CalorIA

Decisões técnicas e ADRs do projeto CalorIA.

---

## Visão Geral

```
┌─────────────────────────────────────────────────────────────────────┐
│  Canais de entrada                                                   │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────────────┐ │
│  │  Telegram Bot│  │ WhatsApp Bot  │  │    Dashboard Web (Next)  │ │
│  │  (polling/   │  │  (webhook via │  │    next-auth + TanStack  │ │
│  │   webhook)   │  │ Evolution API)│  │    Query + shadcn/ui     │ │
│  └──────┬───────┘  └──────┬────────┘  └─────────────┬────────────┘ │
│         │                 │                          │              │
└─────────┼─────────────────┼──────────────────────────┼─────────────┘
          │                 │  HTTP REST               │
          ▼                 ▼                          ▼
┌────────────────────────────────────────────────────────────────────┐
│  Backend — FastAPI (Python 3.12)                                   │
│                                                                    │
│  api/v1/  auth · users · meals · weight · hydration · mood        │
│           dashboard · ai · reminders · telegram · whatsapp        │
│                                                                    │
│  services/  UserService · MealService · LogService                │
│             DashboardService · ProfileService                     │
│             AuthService · ReminderService                         │
│             ai/ GeminiClient · MealParser · VisionParser          │
│                 InsightsGenerator · PatternAnalyzer               │
│             nutrition/ TDEE (Harris-Benedict)                     │
│                                                                    │
│  workers/  Celery Beat:                                            │
│    - send_daily_summaries (22h)                                   │
│    - send_weekly_reports (domingo 20h)                            │
│    - cleanup_old_conversations (domingo 3h, >90 dias)            │
│    - recalculate_tdee (dia 1 de cada mês, 4h)                    │
└─────────────────────────┬──────────────────────────────────────────┘
                          │
              ┌───────────┴──────────┐
              ▼                      ▼
     ┌─────────────────┐   ┌──────────────────┐
     │  PostgreSQL 16  │   │    Redis 7        │
     │  Dados primários│   │  Cache · Filas   │
     │  Alembic migrate│   │  JWT blacklist   │
     └─────────────────┘   └──────────────────┘
```

---

## ADR-001 — PostgreSQL para testes (não SQLite)

**Contexto:** O modelo `Reminder` usa `ARRAY(Integer)` do PostgreSQL para armazenar `days_of_week`.

**Decisão:** Usar um banco `caloria_test` no PostgreSQL local para testes de integração, em vez de SQLite.

**Consequências:**
- Requer PostgreSQL rodando no ambiente de CI/CD e de desenvolvimento
- Garante paridade total com o banco de produção
- Evita workarounds de tipo (ex.: `Text` simulando `ARRAY`)

---

## ADR-002 — Gemini Flash como modelo padrão

**Contexto:** O Google Gemini oferece tier gratuito generoso (15 RPM, 1M tokens/min).

**Decisão:** Usar `gemini-1.5-flash` para análise de texto e insights; `gemini-1.5-pro` para visão.

**Consequências:**
- Cache Redis (7 dias, chave SHA-256) reduz chamadas redundantes
- Retry exponencial (3 tentativas) protege contra rate limiting
- Análise de fotos via base64 — imagens não são armazenadas permanentemente

---

## ADR-003 — Evolution API para WhatsApp

**Contexto:** A API oficial do WhatsApp Business tem custo e aprovação. Para uso pessoal, a Evolution API (self-hosted) é suficiente.

**Decisão:** Usar Evolution API via Docker com uma sessão persistente.

**Consequências:**
- Requer escanear QR code uma vez para conectar
- Sessão persiste em volume Docker entre restarts
- Não escalável para múltiplos usuários sem instâncias separadas

---

## ADR-004 — Celery com Redis como broker (sem RabbitMQ)

**Contexto:** O projeto usa Redis para cache e blacklist de JWT. Adicionar RabbitMQ seria over-engineering.

**Decisão:** Usar Redis como broker e backend do Celery.

**Consequências:**
- Menos serviços no Docker Compose
- Limitações de ack do Redis vs RabbitMQ (aceitáveis para uso pessoal)
- Beat schedule definido em código (`celery_app.py`), não em banco

---

## ADR-005 — JWT com blacklist em Redis

**Contexto:** JWT stateless não suporta logout nativo.

**Decisão:** Armazenar refresh tokens invalidados no Redis com TTL igual à validade do token.

**Consequências:**
- Logout real funciona
- Overhead mínimo: apenas refresh tokens são guardados na blacklist
- Access tokens de curta duração (30 min) não são blacklistados

---

## Fluxo de Registro de Refeição (Telegram/WhatsApp)

```
Usuário envia mensagem
        │
        ▼
  Bot recebe texto/foto
        │
        ├── texto → MealParser → Gemini Flash → JSON estruturado
        │
        └── foto  → VisionParser → Gemini Pro Vision → JSON estruturado
                         │
                         ▼
              Exibe resumo + botões Confirmar/Cancelar
                         │
                    Usuário confirma
                         │
                         ▼
              POST /api/v1/meals → salva no banco
```

---

## Estrutura de Banco de Dados

```
users (1)
  ├── user_profiles (1:1)
  ├── meals (1:N)
  │     └── meal_items (1:N)
  ├── weight_logs (1:N)
  ├── hydration_logs (1:N)
  ├── mood_logs (1:N)
  ├── reminders (1:N)
  └── ai_conversations (1:N)
```

Todas as relações usam `CASCADE DELETE` — ao remover o usuário, todos os dados são removidos.

---

## Segurança

- Senhas com bcrypt (passlib, custo padrão)
- JWT HS256 — access (30 min) + refresh (30 dias)
- CORS configurável via `BACKEND_CORS_ORIGINS`
- `GEMINI_API_KEY` nunca exposta ao frontend
- Variáveis sensíveis em `.env` (nunca commitado)

# Arquitetura — CalorIA

Decisões técnicas e ADRs do projeto CalorIA.

---

## Visão Geral

```
┌─────────────────────────────────────────────────────────────────────┐
│  Canal de entrada                                                    │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │    Dashboard Web (Next.js 14)                                │   │
│  │    JWT próprio · TanStack Query · shadcn/ui · Web Push       │   │
│  └──────────────────────────────┬───────────────────────────────┘   │
└─────────────────────────────────┼───────────────────────────────────┘
                                  │  HTTP REST
                                  ▼
┌────────────────────────────────────────────────────────────────────┐
│  Backend — FastAPI (Python 3.12)                                   │
│                                                                    │
│  api/v1/  auth · users · meals · weight · hydration · mood        │
│           dashboard · ai · reminders · push                       │
│                                                                    │
│  services/  UserService · MealService · LogService                │
│             DashboardService · ProfileService                     │
│             AuthService · ReminderService · PushService           │
│             ai/ GeminiClient · MealParser · VisionParser          │
│                 InsightsGenerator · PatternAnalyzer               │
│                 FoodLookup (pg_trgm, TACO+OFF ~19.800)           │
│                 ContextBuilder (histórico + tipo de refeição)     │
│             nutrition/ TDEE (Harris-Benedict)                     │
│                                                                    │
│  workers/  Celery Beat:                                            │
│    - dispatch_due_reminders (a cada minuto)                       │
│    - send_hydration_reminders (horários configurados)             │
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

## ADR-002 — Google Gemini 2.5 Flash como modelo de IA

**Contexto:** O Google Gemini oferece tier gratuito com suporte a texto e visão num único modelo multimodal.

**Decisão:** Usar `models/gemini-2.5-flash` via SDK `google-genai` para análise de texto, fotos e geração de insights. Um único modelo cobre todos os casos de uso.

**Consequências:**
- Cache Redis (7 dias, chave SHA-256) reduz chamadas redundantes para insights
- Retry com backoff exponencial em erros 429 — até 4 tentativas, espera inicial 15s dobrada a cada tentativa
- Análise de fotos via bytes nativos — imagens não são armazenadas permanentemente
- `GEMINI_API_KEY` nunca exposta ao frontend

---

## ADR-003 — Web Push VAPID em vez de bots externos

**Contexto:** O projeto inicialmente usava Telegram e WhatsApp (Evolution API) como canais de notificação. Isso criava dependência de serviços externos, sessões persistentes e infraestrutura adicional.

**Decisão:** Notificações via Web Push nativo (VAPID, pywebpush). Registro de refeições é exclusivamente via dashboard web.

**Consequências:**
- Sem Evolution API no Docker Compose
- Notificações nativas no browser desktop e mobile (PWA)
- Subscriptions armazenadas no banco (`push_subscriptions`); expiradas (HTTP 410) são removidas automaticamente
- Lembretes não têm mais campo `channel` — são sempre Web Push

---

## ADR-004 — Celery com Redis como broker (sem RabbitMQ)

**Contexto:** O projeto já usa Redis para cache e blacklist de JWT. Adicionar RabbitMQ seria over-engineering.

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

## ADR-006 — Banco nutricional com pg_trgm + pipeline dois estágios + sanity check

**Contexto:** A IA estima macros com variância alta para alimentos brasileiros. Um pipeline de um único estágio misturava identificação e cálculo, dificultando validação e deixando registros incorretos do Open Food Facts contaminarem resultados.

**Decisão:** Banco `foods` no PostgreSQL (TACO ~307 + Open Food Facts ~19.500) com índice GIN trigrama. Pipeline em dois estágios com sanity check calórico:

1. **Estágio 1 — Identificação:** IA retorna alimentos com nome, quantidade, unidade e `kcal_estimate` (usado exclusivamente no sanity check, não substitui macros do banco).
2. **Estágio 2 — Lookup + sanity check:** Busca com `similarity()` + `%>>` (threshold 0.65). Se match encontrado, compara calorias calculadas do banco com `kcal_estimate` — divergência > 35% descarta o match e usa estimativa da IA (`data_source="ai_estimated"`). Itens sem match vão para `_estimate_macros_batch` (uma única chamada IA agrupada).

**Consequências:**
- Dados TACO recebem boost 1.40× para prevalecerem sobre Open Food Facts em desempates
- `MealItem` registra `food_id` (FK→foods) e `data_source` para rastreabilidade
- Sanity check evita que valores incorretos do Open Food Facts (ex: feijão carioca 40 kcal vs TACO 76 kcal) contaminem resultados
- Latência de lookup < 20ms com 19.800 registros

---

## ADR-007 — Sistema de design Glassmorphism + Neumorphism

**Contexto:** shadcn/ui padrão tem visual genérico; o projeto precisava de identidade visual própria.

**Decisão:** Sistema de design com glassmorphism (backdrop-blur + transparência) combinado com neumorphism (sombras suaves). Implementado via CSS custom em `globals.css` (`@layer components`) e tokens no `tailwind.config.ts`.

**Consequências:**
- Classes utilitárias: `.glass`, `.glass-card`, `.glass-neu`, `.neu-raised`, `.neu-inset`, `.glow-primary`
- Dark mode como padrão (`html.dark` fixo)
- Todos os módulos do dashboard seguem o mesmo sistema visual

---

## ADR-008 — CI/CD com GitHub Actions

**Contexto:** Deploy manual via SSH era propenso a erros e requeria acesso ao servidor a cada release.

**Decisão:** `ci.yml` roda lint + testes + build em todo push na `dev` e em PRs para `main`. `cd.yml` faz SSH → git pull → docker compose up → alembic ao mergear na `main`.

**Consequências:**
- `main` é sempre estável e deployável
- Deploy automático sem acesso manual ao servidor
- Secrets de SSH armazenados no GitHub Environment `production`
- Ver `docs/git-workflow.md` para o fluxo de branches

---

## Fluxo de Registro de Refeição (Web)

```
Usuário envia descrição ou foto no dashboard
        │
        ▼
  POST /api/v1/ai/analyze-meal  (texto)
  POST /api/v1/ai/analyze-photo (foto)
        │
        ▼
  ContextBuilder
  ├── infere tipo de refeição (café/almoço/janta/lanche)
  ├── busca últimas 3 refeições do mesmo tipo
  └── injeta porções históricas e médias diárias
        │
        ▼
  [Estágio 1] Gemini 2.5 Flash identifica alimentos
  └── retorna: food_name, quantity, unit, preparation, kcal_estimate
        │
        ▼
  [Estágio 2] FoodLookup (pg_trgm, threshold 0.65) + sanity check
  ├── match + divergência ≤ 35%  → macros do banco, data_source=food.source
  ├── match + divergência > 35%  → fallback estimativa IA
  └── sem match                  → _estimate_macros_batch (IA agrupada)
                                   data_source="ai_estimated"
        │
        ▼
  _correct_calories (Atwater: prot×4 + carb×4 + gord×9)
        │
        ▼
  Retorna MealAnalysisResponse ao frontend
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
  │     └── meal_items (1:N) — food_id FK→foods, data_source, micronutrientes
  ├── weight_logs (1:N)
  ├── hydration_logs (1:N)
  ├── mood_logs (1:N)
  ├── reminders (1:N)
  ├── push_subscriptions (1:N)
  ├── notifications (1:N)
  └── ai_conversations (1:N)

foods — banco nutricional unificado (TACO + Open Food Facts)
  └── search_text GIN index (pg_trgm)
```

Todas as relações usam `CASCADE DELETE`.

---

## Segurança

- Senhas com passlib[bcrypt]
- JWT HS256 — access (30 min) + refresh (30 dias)
- CORS configurável via `BACKEND_CORS_ORIGINS`
- `GEMINI_API_KEY` nunca exposta ao frontend
- Variáveis sensíveis em `.env` (nunca commitado)

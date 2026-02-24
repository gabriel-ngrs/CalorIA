# CHANGELOG — CalorIA

Todas as mudanças significativas do projeto são documentadas aqui.

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/).
Versões seguem [Semantic Versioning](https://semver.org/lang/pt-BR/).

---

## [Não lançado]

### Adicionado
- `workers/tasks/reports.py`: tasks `send_daily_summaries` (22h) e `send_weekly_reports` (domingo 20h) com insights gerados pelo Gemini
- `workers/tasks/maintenance.py`: tasks `cleanup_old_conversations` (remove conversas > 90 dias) e `recalculate_tdee` (recalcula TDEE mensal quando peso mudou ≥ 2 kg)
- Beat schedule do Celery atualizado com entrada `recalculate-tdee-monthly` (dia 1 de cada mês às 4h)
- `services/ai/pattern_analyzer.py`: PatternAnalyzer que agrega refeições + humor dos últimos N dias e usa Gemini para identificar padrões (horários, frequência, correlação com humor)
- `services/ai/insights_generator.py`: três novos métodos — `nutritional_alerts()` (detecta deficiências recorrentes com severidade), `goal_adjustment_suggestion()` (compara tendência de peso com meta e sugere ajuste calórico), `monthly_report()` (relatório mensal com score de aderência, melhor/pior semana e análise da IA)
- `schemas/ai.py`: novos schemas EatingPattern, NutritionalAlert, NutritionalAlertsResponse, GoalAdjustmentSuggestion, WeekSummary, MonthlyReport
- Novos endpoints: GET /api/v1/ai/patterns, /nutritional-alerts, /goal-adjustment, /monthly-report

- Documentação inicial do projeto: CLAUDE.md, Roadmap.md, Prompt.md, README.md, CHANGELOG.md
- Plano completo de desenvolvimento em 9 fases no Roadmap.md
- Estrutura completa de pastas do projeto (backend/, frontend/, docs/)
- `.gitignore` cobrindo Python, Node.js/Next.js, Docker, IDEs e variáveis de ambiente
- `.env.example` com todas as variáveis necessárias documentadas
- `docker-compose.yml` com todos os serviços para produção local
- `docker-compose.dev.yml` com hot reload para backend e frontend, portas expostas para desenvolvimento
- Projeto base do backend: pyproject.toml, Dockerfile multi-stage, Alembic, ruff, mypy
- Módulos core: config (Settings), database (engine async), security (JWT + bcrypt), deps (get_db)
- Projeto base do frontend: Next.js 14, shadcn/ui, TanStack Query v5, next-auth v4, Recharts, axios
- Providers com QueryClientProvider e SessionProvider, cliente axios com interceptor de autenticação
- Modelos SQLAlchemy 2.x: User, UserProfile, Meal, MealItem, WeightLog, HydrationLog, MoodLog, Reminder, AIConversation
- Schemas Pydantic v2 para todos os domínios incluindo schemas de dashboard agregados
- Autenticação JWT: register, login, refresh (com blacklist Redis), logout, /me
- TDEE automático via Harris-Benedict + GET/PUT /users/me/profile
- CRUD completo de refeições com itens aninhados e daily-summary
- Logs de peso, hidratação e humor com endpoints REST
- Dashboard: /today, /weekly, /macros-chart, /weight-chart
- GeminiClient: retry exponencial, cache Redis 7 dias por hash SHA-256, logging de tokens
- MealParser: análise de texto em JSON estruturado com confidence por item
- VisionParser: análise de fotos via base64 com gemini-1.5-pro
- InsightsGenerator: insights diário/semanal, Q&A nutricional e sugestão de refeição
- Endpoints /ai/analyze-meal, /analyze-photo, /insights, /suggest-meal
- Bot Telegram completo: handlers para comandos (/start, /ajuda, /conectar, /perfil, /hoje, /resumo, /semana, /relatorio, /historico, /peso, /agua, /humor, /lembrete, /lembretes, /remover-lembrete)
- ConversationHandler para registro de refeição via texto ou foto com confirmação inline
- TelegramService: vinculação conta via token Redis (10 min TTL), busca por chat_id
- ReminderService: listar, criar, deletar e toggle de lembretes
- POST /api/v1/telegram/link-token (gerar token de vinculação)
- POST /api/v1/telegram/webhook (receber updates em produção)
- Bot inicia em modo polling no lifespan do FastAPI (dev); webhook disponível para produção
- User model: campos telegram_chat_id e whatsapp_number (preparação para ambos os canais)
- Bot WhatsApp via Evolution API: sender.py, handlers.py (comandos !prefix), webhook.py
- WhatsAppService: vincula número por token, normaliza JID do WhatsApp
- Confirmação de refeição via resposta "sim/não" com estado Redis (TTL 5 min)
- POST /api/v1/whatsapp/link-token e POST /api/v1/whatsapp/webhook
- Dashboard web completo: login, cadastro, layout com sidebar, todas as 9 páginas
- Componentes shadcn/ui: Button, Card, Input, Label, Progress, Skeleton, Badge, Textarea, Select, Slider, Dialog
- Hooks TanStack Query para todos os domínios (dashboard, meals, logs, reminders, profile)
- NextAuth com CredentialsProvider + middleware de proteção de rotas
- Gráficos Recharts: pizza macros, barras calorias semanais, linhas peso/humor

---

<!-- Template para novas entradas:

## [X.Y.Z] - AAAA-MM-DD

### Adicionado
- Nova funcionalidade ou arquivo

### Alterado
- Mudança em funcionalidade existente

### Corrigido
- Bug corrigido

### Removido
- Funcionalidade ou arquivo removido

### Segurança
- Correção de vulnerabilidade

-->

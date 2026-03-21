# CHANGELOG — CalorIA

Todas as mudanças significativas do projeto são documentadas aqui.

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/).
Versões seguem [Semantic Versioning](https://semver.org/lang/pt-BR/).

---

## [Não lançado]

### Adicionado

- **Sanity check calórico no pipeline dois estágios** — após lookup no banco, compara `kcal_estimate` da IA com as calorias calculadas do registro encontrado; divergência > 35% descarta o match e usa estimativa da IA como fallback. Evita que registros incorretos do OpenFoodFacts contaminem resultados. Aplicado em `meal_parser.py` e `vision_parser.py`.
- **Campo `kcal_estimate` em `IdentifiedFood`** — estágio 1 da IA agora retorna estimativa calórica usada exclusivamente como sanity check do banco, sem substituir os macros reais do TACO.
- **Migração `20260320_e6f7a8b9c0d1`** — corrige `search_text` de 7 registros TACO (feijão carioca, ovo cozido/mexido/frito/clara, mandioca cozida/frita) para aumentar score pg_trgm de ~0.4 para ~0.8; remove registro OpenFoodFacts de feijão carioca com valor calórico incorreto (44 kcal vs TACO 76 kcal).

### Alterado

- **Refatoração do banco de alimentos** — `taco_foods` renomeada para `foods`, adicionados campos de micronutrientes (`sodium_100g`, `sugar_100g`, `saturated_fat_100g`), campo `source` para rastrear origem (taco/openfoodfacts/ai_estimated), campo `food_id` em `meal_items` para referência direta ao alimento.
- **Busca fuzzy via pg_trgm** — substituiu rapidfuzz in-memory por busca trigrama diretamente no PostgreSQL com índice GIN; boost 1.40× para registros TACO em desempates contra OpenFoodFacts; threshold mínimo 0.65 para match válido.
- **Timeout da API no frontend** — aumentado de 10s para 45s para acomodar análises de foto com múltiplos alimentos.

### Corrigido

- Feijão carioca retornando 40 kcal (registro OpenFoodFacts incorreto sobrescrevia TACO 76 kcal).
- Ovo cozido sem match no banco (score 0.57 < 0.65 por `search_text` longo diluindo trigrama).
- Aipim/mandioca mapeando para alimento errado (Chuchu cozido).
- `db` não repassado ao `VisionParser` no handler de fotos do bot Telegram/WhatsApp.

---

## [0.4.0] - 2026-03-05

### Adicionado

- **Banco TACO com lookup fuzzy** — `services/ai/taco_lookup.py` com ~600 alimentos da tabela TACO, busca fuzzy via rapidfuzz com threshold 75. Macros reais injetados no prompt do Gemini antes de qualquer chamada à API.
- **Contexto histórico de refeições** — `services/ai/context_builder.py` infere tipo de refeição por palavras-chave (café, almoço, janta, lanche) e injeta no prompt: últimas 3 refeições do mesmo tipo, porções históricas por alimento e médias diárias. Bot Telegram e API REST compartilham o mesmo pipeline.
- **Calendário customizado com tema escuro** — `components/ui/calendar.tsx` (react-day-picker v8) com cores primárias, seleção destacada e navegação com ícones Lucide. Substitui o seletor nativo do browser na página de refeições.
- **Componente Popover** — `components/ui/popover.tsx` (Radix UI) com animações fade-in/zoom-in, usado como wrapper do calendário.
- **Dependências**: `react-day-picker ^8.10.1`, `date-fns ^3.6.0`, `@radix-ui/react-popover ^1.1.15`
- **Todos os endpoints de Insights** — página `/insights` expande para exibir: análise diária, semanal, alertas nutricionais, ajuste de metas, relatório mensal e chat livre com a IA.
- **Métricas de período no Humor** — seletor de 7/14/30 dias, média de energia e humor, melhor dia do período.
- **Gráficos históricos na Hidratação** — gráfico de barras com consumo dos últimos N dias e métricas do período.
- **Categorias expandidas de refeição** — "café da manhã", "lanche manhã", "almoço", "lanche tarde", "jantar", "ceia", "lanche noturno" com labels e ícones por categoria.
- **Edição de refeições** — modal de edição inline na página `/refeicoes`.
- **Endpoint de lembretes completo** — suporte a múltiplos horários e intervalo de horas; input livre substituiu select fixo.

### Alterado

- **Redesign completo do frontend** — todos os módulos do dashboard reescritos com sistema de design glassmorphism + neumorphism:
  - Layout de duas colunas em todas as páginas (formulário + stats/lista)
  - Hover effects uniformes: `transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl`
  - Removidos `max-w-*` limitadores — páginas usam todo o espaço disponível
  - Tooltips customizados com classe `.glass` nos gráficos Recharts
  - Ícones Lucide substituem emojis em todo o dashboard
- **Módulo de Refeições** — sidebar de stats do dia (calorias, proteína, carboidrato, gordura com % kcal); calendário popover substitui input date nativo
- **Módulo de Peso** — área chart em vez de line chart; tooltip glass; layout expandido
- **Módulo de Hidratação** — gradiente azul na barra de progresso; 2 colunas
- **Módulo de Humor** — `LevelSelector` com botões coloridos 1-5; 2 colunas
- **Módulo de Lembretes** — 2 colunas (formulário + lista); `TYPE_COLORS` por tipo de lembrete
- **Módulo de Perfil** — 2 colunas (dados pessoais + metas); banner TDEE com delta vs meta
- **Módulo Conectar Bot** — cards lado a lado (Telegram azul + WhatsApp verde); chips de status
- **Pipeline de IA** — TACO lookup + context builder injetados em `MealParser` antes da chamada ao Gemini; bot Telegram e API REST compartilham o mesmo serviço
- **Precisão de macronutrientes** — prompt reformulado para usar valores reais da tabela TACO quando disponíveis, com fallback calibrado para o Gemini

### Corrigido

- `SelectItem` com fundo laranja (accent) cobrindo texto ao hover → substituído por `focus:bg-primary/10 focus:text-foreground`
- Fuso horário incorreto nas datas de refeições — `getLocalToday()` e `TZ=America/Sao_Paulo` nos containers Docker
- Erro de hidratação ao navegar entre datas na página de refeições
- Build TypeScript de produção: interfaces vazias convertidas para `type`, erros de tipos corrigidos
- Roteamento Caddy: `/api/auth/*` roteado para o frontend antes de `/api/*`
- Envio de lembretes no Celery Worker
- Verificação de chave de API: `GROQ_API_KEY` em vez de `GEMINI_API_KEY`
- Serialização do enum `goal_type` ao salvar perfil

---

## [0.3.0] — histórico anterior

### Adicionado
- `backend/tests/conftest.py`: infraestrutura de testes com engine PostgreSQL dedicado, fixtures session-scoped para criação/destruição do schema e fixtures por função para db, test_user, client autenticado e anon_client
- `backend/tests/unit/`: testes unitários para `security` (JWT, bcrypt), `tdee` (Harris-Benedict), `meal_parser` e `vision_parser` (mock GeminiClient)
- `backend/tests/integration/`: testes de integração para auth, meals, weight/hydration/mood, users/profile e dashboard
- `pyproject.toml`: `asyncio_default_fixture_loop_scope = "session"` para suprimir aviso do pytest-asyncio
- `frontend/jest.config.js`, `jest.setup.ts`, `babel.config.test.js`: configuração Jest para Next.js com suporte a `@/*` path aliases e mock do Recharts
- `frontend/__tests__/`: testes de componentes (MacroCards, MacroPieChart) e utilitário `cn`
- `.pre-commit-config.yaml`: hooks ruff (lint + format) para o backend, trailing-whitespace, end-of-file, check-yaml, merge-conflicts, large-files e bloqueio de commits na main
- `docs/architecture.md`: diagrama da arquitetura, 5 ADRs e fluxo de registro de refeição
- `docs/setup.md`: guia completo de setup — Docker, backend, frontend, banco de testes, Celery, WhatsApp

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

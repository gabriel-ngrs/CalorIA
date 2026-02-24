# Roadmap — CalorIA

Todas as etapas de desenvolvimento do projeto, organizadas em fases progressivas.

**Legenda:** `[ ]` pendente · `[x]` concluído · `[~]` em progresso

---

## Fase 0 — Setup e Fundação

> Objetivo: ambiente de desenvolvimento funcionando, estrutura do projeto criada.

### 0.1 Estrutura do Repositório
- [x] Criar estrutura de pastas (`backend/`, `frontend/`, `docs/`)
- [x] Criar `.gitignore` (Python, Node, .env, __pycache__, .next, etc.)
- [x] Criar `.env.example` com todas as variáveis necessárias
- [x] Inicializar git e fazer primeiro commit

### 0.2 Docker Compose
- [x] Criar `docker-compose.yml` (produção local)
- [x] Criar `docker-compose.dev.yml` (desenvolvimento com hot reload)
- [x] Serviço PostgreSQL 16 com volume persistente
- [x] Serviço Redis 7 com volume persistente
- [x] Serviço Evolution API com volume para sessão WhatsApp
- [x] Serviço backend (FastAPI)
- [x] Serviço frontend (Next.js)
- [x] Serviço celery_worker
- [x] Serviço celery_beat
- [x] Rede compartilhada entre serviços
- [x] Health checks para postgres e redis

### 0.3 Backend — Projeto Base
- [x] `pyproject.toml` com dependências (FastAPI, SQLAlchemy, Celery, etc.)
- [x] `Dockerfile` para o backend (multi-stage build)
- [x] Estrutura de pastas: `app/api/`, `app/core/`, `app/models/`, `app/schemas/`, `app/services/`, `app/workers/`, `app/bots/`
- [x] `app/main.py` — instância FastAPI com CORS, lifespan, routers
- [x] `app/core/config.py` — Settings com Pydantic BaseSettings
- [x] `app/core/database.py` — Engine async PostgreSQL, sessão async
- [x] `app/core/security.py` — JWT encode/decode, hash de senhas
- [x] `app/core/deps.py` — Dependências FastAPI (get_db, get_current_user)
- [x] Configurar **Alembic** para migrações
- [x] Configurar **ruff** e **mypy** (`pyproject.toml`)

### 0.4 Frontend — Projeto Base
- [x] `npx create-next-app@latest` com TypeScript, Tailwind, App Router
- [x] Instalar e configurar **shadcn/ui**
- [x] Instalar **TanStack Query**, **next-auth**, **Recharts**, **axios**
- [x] `Dockerfile` para o frontend
- [x] Estrutura de pastas: `app/`, `components/ui/`, `components/dashboard/`, `lib/`, `types/`
- [x] Configurar variáveis de ambiente Next.js

---

## Fase 1 — Modelos e API Base

> Objetivo: banco de dados modelado, autenticação funcionando, CRUD básico.

### 1.1 Modelos de Banco de Dados
- [x] `models/user.py` — User (id, email, name, password_hash, weight_goal, calorie_goal, created_at)
- [x] `models/profile.py` — UserProfile (height, current_weight, age, sex, activity_level, tdee_calculated)
- [x] `models/meal.py` — Meal (id, user_id, name, meal_type: breakfast/lunch/dinner/snack, date, source: manual/telegram/whatsapp, notes)
- [x] `models/meal_item.py` — MealItem (id, meal_id, food_name, quantity, unit, calories, protein, carbs, fat, fiber, raw_input)
- [x] `models/weight_log.py` — WeightLog (id, user_id, weight_kg, date, notes)
- [x] `models/hydration_log.py` — HydrationLog (id, user_id, amount_ml, date, time)
- [x] `models/mood_log.py` — MoodLog (id, user_id, date, energy_level 1-5, mood_level 1-5, notes)
- [x] `models/reminder.py` — Reminder (id, user_id, type, time, days_of_week, active, channel: telegram/whatsapp)
- [x] `models/ai_conversation.py` — AIConversation (id, user_id, channel, external_chat_id, messages JSON, created_at)
- [x] Criar migração inicial com Alembic

### 1.2 Schemas Pydantic
- [x] Schemas para User (Create, Update, Response, Login)
- [x] Schemas para Meal + MealItem (Create, Update, Response, com items aninhados)
- [x] Schemas para WeightLog (Create, Response)
- [x] Schemas para HydrationLog (Create, Response)
- [x] Schemas para MoodLog (Create, Response)
- [x] Schemas para Reminder (Create, Update, Response)
- [x] Schemas para Dashboard (aggregated data)

### 1.3 Autenticação
- [x] `POST /api/v1/auth/register` — cadastro de usuário
- [x] `POST /api/v1/auth/login` — login, retorna JWT access + refresh token
- [x] `POST /api/v1/auth/refresh` — renovar access token
- [x] `POST /api/v1/auth/logout` — invalidar refresh token (Redis blacklist)
- [x] Middleware de autenticação via Bearer token
- [x] `GET /api/v1/auth/me` — dados do usuário autenticado

### 1.4 API — Usuário e Perfil
- [x] `GET /api/v1/users/me/profile` — buscar perfil
- [x] `PUT /api/v1/users/me/profile` — atualizar perfil (peso, altura, metas)
- [x] Cálculo automático de TDEE (Total Daily Energy Expenditure) via fórmula Harris-Benedict

### 1.5 API — Refeições
- [x] `GET /api/v1/meals` — listar refeições (filtro por data, tipo)
- [x] `POST /api/v1/meals` — criar refeição manualmente
- [x] `GET /api/v1/meals/{id}` — detalhes de uma refeição
- [x] `PUT /api/v1/meals/{id}` — editar refeição
- [x] `DELETE /api/v1/meals/{id}` — deletar refeição
- [x] `GET /api/v1/meals/daily-summary` — resumo do dia (total calorias, macros)

### 1.6 API — Demais Logs
- [x] `POST /api/v1/weight` + `GET /api/v1/weight` — registro e histórico de peso
- [x] `POST /api/v1/hydration` + `GET /api/v1/hydration/today` — registro e resumo de água
- [x] `POST /api/v1/mood` + `GET /api/v1/mood` — registro e histórico de humor

### 1.7 API — Dashboard
- [x] `GET /api/v1/dashboard/today` — resumo completo do dia
- [x] `GET /api/v1/dashboard/weekly` — resumo da semana (médias, totais)
- [x] `GET /api/v1/dashboard/macros-chart` — dados para gráfico de macros (últimos N dias)
- [x] `GET /api/v1/dashboard/weight-chart` — dados para gráfico de evolução de peso

---

## Fase 2 — Integração com IA (Gemini)

> Objetivo: IA analisando refeições via texto e foto.

### 2.1 Configuração Gemini
- [x] `services/ai/gemini_client.py` — cliente Gemini com retry e rate limit handling
- [x] Configurar modelos: `gemini-1.5-flash` (texto) e `gemini-1.5-pro` (visão/fotos)
- [x] Cache Redis para respostas de alimentos frequentes (TTL 7 dias)
- [x] Logging de tokens utilizados para monitorar free tier

### 2.2 Análise de Texto
- [x] `services/ai/meal_parser.py` — parsear descrição de refeição em JSON estruturado
- [x] Prompt engineering para extração de alimentos, quantidades e estimativa de macros
- [x] Prompt com contexto do usuário (metas calóricas, alimentos frequentes)
- [x] Tratar ambiguidades ("um prato de arroz") com estimativas calibradas
- [x] Retornar JSON: `[{food_name, quantity, unit, calories, protein, carbs, fat, confidence}]`

### 2.3 Análise de Foto
- [x] `services/ai/vision_parser.py` — analisar imagem de prato/alimento
- [x] Prompt para identificar alimentos visíveis na foto e estimar porções
- [x] Retornar mesmo formato JSON da análise de texto
- [x] Fallback: se confiança baixa, solicitar confirmação ao usuário

### 2.4 Geração de Insights
- [x] `services/ai/insights_generator.py` — gerar insights personalizados
- [x] Insight diário: análise do dia alimentar (o que foi bom, o que melhorar)
- [x] Insight semanal: padrões identificados, tendências de peso x alimentação
- [x] Sugestões de refeições baseadas no histórico e metas
- [x] Resposta conversacional para perguntas livres sobre nutrição

### 2.5 Endpoint de Análise
- [x] `POST /api/v1/ai/analyze-meal` — analisar descrição e retornar itens estruturados
- [x] `POST /api/v1/ai/analyze-photo` — analisar foto (base64) e retornar itens
- [x] `POST /api/v1/ai/insights` — gerar insight (tipo: daily/weekly/question)
- [x] `GET /api/v1/ai/suggest-meal` — sugerir refeição com base no histórico

---

## Fase 3 — Bot Telegram

> Objetivo: registrar refeições e receber informações via Telegram.

### 3.1 Setup do Bot
- [x] Criar bot no BotFather, obter token
- [x] `bots/telegram/bot.py` — instância Application do python-telegram-bot
- [x] Configurar webhook (em produção) ou polling (em dev)
- [x] Vincular chat_id do Telegram ao usuário no banco

### 3.2 Comandos Básicos
- [x] `/start` — mensagem de boas-vindas + instruções
- [x] `/ajuda` — lista de comandos disponíveis
- [x] `/conectar <token>` — vincular conta (token gerado no dashboard web)
- [x] `/perfil` — exibir dados do perfil e metas
- [x] `/hoje` — resumo do dia atual (calorias, macros, água)

### 3.3 Registro de Refeições
- [x] Mensagem de texto livre → IA analisa → confirma e salva
- [x] Foto de prato → IA analisa visualmente → confirma e salva
- [x] Fluxo de confirmação: IA responde "Identificado: X cal, Y g prot..." + botões [Confirmar] [Cancelar]
- [x] Reconhecer horário implícito ("café da manhã", "almoço", "janta")
- [x] ConversationHandler para fluxo multi-step

### 3.4 Registro de Outros Dados
- [x] `/peso 80.5` — registrar peso
- [x] `/agua 300` — registrar consumo de água (ml)
- [x] `/humor 4 5` — registrar humor (energia 4, humor 5) com descrição opcional
- [x] Respostas com emoji e feedback positivo/motivacional

### 3.5 Consultas e Relatórios
- [x] `/resumo` — resumo do dia
- [x] `/semana` — resumo da semana
- [x] `/relatorio` — relatório com insights da IA
- [x] `/historico` — últimas 7 refeições
- [x] Resposta formatada com HTML do Telegram

### 3.6 Lembretes via Telegram
- [x] `/lembrete cafe 07:30` — configurar lembrete de café da manhã
- [x] `/lembretes` — listar lembretes ativos
- [x] `/remover-lembrete <id>` — remover lembrete
- [ ] Workers Celery enviam mensagens nos horários configurados (Fase 6)
- [ ] Resumo automático às 22h (Fase 6)

---

## Fase 4 — Bot WhatsApp (Evolution API)

> Objetivo: mesmas funcionalidades do Telegram via WhatsApp.

### 4.1 Setup Evolution API
- [x] Evolution API rodando via Docker Compose
- [ ] Configurar instância WhatsApp no Evolution API (requer QR Code manual)
- [ ] Escanear QR Code e persistir sessão em volume Docker
- [x] Configurar webhook apontando para o backend (`POST /api/v1/whatsapp/webhook`)
- [ ] Handler de reconexão automática em caso de queda (futuro)

### 4.2 Webhook Handler
- [x] `bots/whatsapp/webhook.py` — receber e processar eventos da Evolution API
- [x] `POST /api/v1/whatsapp/webhook` — endpoint do webhook (background task)
- [x] Roteador de tipos de mensagem: texto, imagem
- [x] Identificar sender e vincular ao usuário do banco
- [x] `bots/whatsapp/sender.py` — enviar mensagens via Evolution API REST

### 4.3 Comandos e Fluxos
- [x] Mesmo conjunto de comandos do Telegram (prefixados com `!`)
- [x] `!ajuda`, `!hoje`, `!resumo`, `!peso`, `!agua`, `!humor`
- [x] Registro de refeição por texto livre
- [x] Registro de refeição por foto
- [x] Fluxo de confirmação: resposta "sim/não" (estado no Redis, TTL 5 min)
- [x] Histórico via `!historico`

### 4.4 Vinculação de Conta
- [x] Usuário gera token no dashboard → envia `!conectar TOKEN` no WhatsApp
- [x] Salvar número WhatsApp no perfil do usuário
- [x] Suporte a múltiplos canais (mesmo usuário pode usar Telegram + WhatsApp)

---

## Fase 5 — Frontend Dashboard

> Objetivo: interface web completa para visualização e gerenciamento.

### 5.1 Autenticação Web
- [x] Página de login (`/login`)
- [x] Página de cadastro (`/register`)
- [x] Integração next-auth com JWT do backend
- [x] Redirecionamento automático para dashboard
- [x] Middleware de proteção de rotas

### 5.2 Layout e Navegação
- [x] Layout principal com sidebar responsiva
- [x] Navbar com nome do usuário, botão de logout
- [x] Menu: Dashboard, Refeições, Peso, Hidratação, Humor, Lembretes, Perfil, Conectar Bot, Insights

### 5.3 Dashboard Principal (`/dashboard`)
- [x] Cards de resumo do dia: Calorias (consumido vs meta), Proteína, Carboidrato, Gordura
- [x] Barra de progresso para calorias vs meta
- [x] Card de hidratação do dia
- [x] Gráfico de pizza: distribuição de macros do dia
- [x] Gráfico de barras: calorias dos últimos 7 dias vs meta
- [x] Lista das refeições do dia
- [x] Card de humor/energia do dia e card de peso

### 5.4 Página de Refeições (`/refeicoes`)
- [x] Lista de refeições com filtro por data
- [x] Botão "Adicionar Refeição" → modal com análise via IA
- [x] Preview dos itens identificados pela IA antes de salvar
- [x] Exclusão de refeições

### 5.5 Gráfico de Evolução de Peso (`/peso`)
- [x] Gráfico de linha: peso ao longo do tempo (90 dias)
- [x] Linha de meta de peso
- [x] Formulário para registrar novo peso
- [x] Histórico de registros

### 5.6 Hidratação (`/hidratacao`)
- [x] Barra de progresso com percentual
- [x] Botões rápidos: +200ml, +300ml, +500ml
- [x] Input para valor personalizado

### 5.7 Humor e Energia (`/humor`)
- [x] Formulário com sliders 1-5 para energia e humor + notas
- [x] Gráfico de linha dupla: energia e humor ao longo do tempo

### 5.8 Lembretes (`/lembretes`)
- [x] Lista de lembretes ativos por canal (Telegram/WhatsApp)
- [x] Criar lembretes (tipo, canal, horário)
- [x] Deletar lembretes

### 5.9 Perfil e Metas (`/perfil`)
- [x] Formulário completo: altura, peso, idade, sexo, nível de atividade
- [x] TDEE calculado automaticamente exibido
- [x] Meta calórica e meta de peso configuráveis

### 5.10 Conectar Bots (`/conectar`)
- [x] Gerar token único de vinculação (válido 10 minutos) para Telegram e WhatsApp
- [x] Status de conexão por canal
- [x] Botão de cópia do token

### 5.11 Insights IA (`/insights`)
- [x] Insight do dia gerado pela IA
- [x] Análise semanal
- [x] Campo de chat livre com a IA

---

## Fase 6 — Notificações e Lembretes (Celery)

> Objetivo: sistema de lembretes e relatórios automáticos funcionando.

### 6.1 Celery Setup
- [x] `workers/celery_app.py` — configuração do Celery com Redis broker
- [x] `workers/tasks/` — módulo de tasks
- [x] Celery Beat configurado para tarefas periódicas
- [x] Logging de tasks (sucesso, falha, retry)

### 6.2 Tasks de Lembrete
- [x] Task `send_reminder` — enviar lembrete para usuário em canal específico
- [x] Celery Beat agenda baseado nos objetos Reminder no banco
- [x] Task `schedule_user_reminders` — re-agenda lembretes ao iniciar ou quando Reminder é modificado
- [x] Tratamento de falha: retry 3x com backoff exponencial

### 6.3 Tasks de Relatório Automático
- [x] Task `daily_summary` — 22h: resumo do dia com motivação da IA
- [x] Task `weekly_report` — domingo 20h: relatório semanal completo com insights
- [x] Task `hydration_reminder` — lembretes de água ao longo do dia (configurável)
- [x] Task `weigh_in_reminder` — lembrete semanal para registrar peso

### 6.4 Tasks de Manutenção
- [x] Task `cleanup_old_conversations` — limpar histórico de conversas IA > 90 dias
- [x] Task `recalculate_tdee` — recalcular TDEE mensal se peso mudou significativamente

---

## Fase 7 — Insights Avançados de IA

> Objetivo: IA aprendendo padrões e gerando recomendações personalizadas.

### 7.1 Análise de Padrões
- [ ] Identificar horários de refeição habituais
- [ ] Detectar padrões: dias que come mais/menos, correlação com humor
- [ ] Identificar alimentos mais consumidos e frequência

### 7.2 Recomendações Personalizadas
- [ ] Sugestão de refeições baseada em preferências e histórico
- [ ] Alertas de deficiências nutricionais recorrentes
- [ ] Sugestão de ajuste de metas baseada na tendência real de peso

### 7.3 Relatórios Ricos
- [ ] Relatório mensal em PDF (futuro) ou mensagem longa formatada
- [ ] "Mês em revisão": melhor semana, pior semana, progresso vs meta
- [ ] Score de aderência à dieta (% de dias dentro da meta)

---

## Fase 8 — Qualidade e Testes

> Objetivo: cobertura de testes robusta, código limpo, pronto para escalar.

### 8.1 Testes Backend
- [ ] Testes unitários para todos os services
- [ ] Testes unitários para meal_parser e vision_parser (mock Gemini)
- [ ] Testes de integração para todos os endpoints da API
- [ ] Testes de integração para Celery tasks (mock de envio de mensagem)
- [ ] Cobertura mínima: 80%
- [ ] Fixtures compartilhadas (usuário de teste, refeições de teste)

### 8.2 Testes Frontend
- [ ] Testes de componentes com Testing Library
- [ ] Testes de hooks customizados
- [ ] Testes E2E com Playwright (fluxos críticos: login, registrar refeição, ver dashboard)

### 8.3 Qualidade de Código
- [ ] CI local: `pre-commit` hooks rodando ruff, mypy, eslint antes de cada commit
- [ ] Corrigir todos os warnings do mypy
- [ ] Revisar queries N+1 no banco (eager loading onde necessário)

### 8.4 Documentação Técnica
- [ ] Documentação da API via Swagger/OpenAPI (automático no FastAPI)
- [ ] `docs/architecture.md` — decisões de arquitetura e ADRs
- [ ] `docs/setup.md` — guia completo de setup do zero
- [ ] Atualizar README com screenshots do dashboard

---

## Fase 9 — Preparação para Escala (Futuro)

> Itens a considerar quando o projeto crescer para múltiplos usuários.

- [ ] Autenticação social (Google OAuth)
- [ ] Multi-tenancy: garantir isolamento total de dados por usuário
- [ ] Rate limiting por usuário na API
- [ ] Otimização de queries + índices no banco
- [ ] Migração de armazenamento de fotos para S3/R2
- [ ] CDN para assets do frontend
- [ ] Monitoramento: Sentry para erros, Prometheus + Grafana para métricas
- [ ] Deploy em VPS (Coolify/Caprover) ou cloud (Railway, Render, Fly.io)
- [ ] HTTPS com Let's Encrypt
- [ ] Backups automáticos do PostgreSQL
- [ ] Monetização: plano premium com features avançadas de IA

---

## Resumo das Fases

| Fase | Nome | Status |
|---|---|---|
| 0 | Setup e Fundação | `[x]` |
| 1 | Modelos e API Base | `[x]` |
| 2 | Integração com IA (Gemini) | `[x]` |
| 3 | Bot Telegram | `[x]` |
| 4 | Bot WhatsApp (Evolution API) | `[x]` |
| 5 | Frontend Dashboard | `[x]` |
| 6 | Notificações e Lembretes | `[x]` |
| 7 | Insights Avançados de IA | `[ ]` |
| 8 | Qualidade e Testes | `[ ]` |
| 9 | Preparação para Escala | `[ ]` |

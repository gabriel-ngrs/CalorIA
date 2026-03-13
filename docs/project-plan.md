# Plano do Projeto — CalorIA

## O que é

CalorIA é um diário alimentar inteligente pessoal. O usuário registra refeições via WhatsApp ou Telegram (texto ou foto), e a IA analisa os macronutrientes automaticamente. O sistema aprende os hábitos alimentares e gera insights personalizados. Um dashboard web permite visualizar histórico, evolução de peso, hidratação, humor/energia e relatórios.

**Uso atual:** projeto pessoal de estudo e uso próprio. Arquitetura pensada para escalar para múltiplos usuários no futuro.

---

## Canais de Registro

- **WhatsApp** — Evolution API (self-hosted, gratuito, Docker)
- **Telegram** — python-telegram-bot
- **Web** — formulário no dashboard com análise de IA

O usuário pode usar todos os canais simultaneamente com a mesma conta.

---

## Dados Rastreados

- Refeições com calorias e macros (proteína, carboidrato, gordura, fibra)
- Peso corporal (evolução ao longo do tempo)
- Hidratação (ml de água por dia)
- Humor e energia (escala 1-5, notas opcionais)

---

## IA

**Google Gemini Flash 1.5** (gratuito) para:
- Parsear descrição de texto ("comi uma tigela de aveia com banana") → macros estimados
- Analisar foto de prato → identificar alimentos e estimar porções
- Gerar insights personalizados baseados no histórico

**Gemini Pro Vision** para análise de imagens de comida.

Free tier: 15 RPM, 1 milhão de tokens/min, 1.500 requisições/dia — suficiente para uso pessoal.

---

## Stack Tecnológica

| Camada | Tecnologia | Justificativa |
|---|---|---|
| Backend API | Python 3.12 + FastAPI | Performance, tipagem, ecossistema IA |
| Banco primário | PostgreSQL 16 | Confiabilidade, queries complexas |
| Cache / Filas | Redis 7 | Celery broker, cache de respostas Gemini, sessões |
| Workers | Celery + Celery Beat | Lembretes assíncronos, tarefas periódicas |
| IA | Google Gemini Flash/Vision | Melhor free tier disponível, multimodal |
| Bot WhatsApp | Evolution API (self-hosted) | Gratuito, open-source, estável |
| Bot Telegram | python-telegram-bot | Biblioteca oficial, bem documentada |
| Frontend | Next.js 14 + TypeScript | App Router, SSR, ecossistema rico |
| UI | shadcn/ui + Tailwind CSS | Componentes acessíveis, customizáveis |
| Gráficos | Recharts | Flexível, React-nativo |
| Auth web | next-auth | Integração simples com JWT |
| ORM | SQLAlchemy 2 (async) | Queries async, type-safe |
| Migrações | Alembic | Padrão do ecossistema SQLAlchemy |
| Infra | Docker Compose | Ambiente reproduzível, simples |

---

## Fases de Desenvolvimento

| # | Fase | Descrição |
|---|---|---|
| 0 | Setup e Fundação | Docker, estrutura do projeto, configurações base |
| 1 | Modelos e API Base | Banco de dados, autenticação, CRUD completo |
| 2 | Integração com IA | Gemini texto e visão, endpoints de análise |
| 3 | Bot Telegram | Todos os comandos, registro por texto e foto |
| 4 | Bot WhatsApp | Evolution API, mesmas features do Telegram |
| 5 | Frontend Dashboard | Interface web completa com todos os gráficos |
| 6 | Notificações e Lembretes | Celery tasks, resumos automáticos |
| 7 | Insights Avançados | Padrões, recomendações, relatórios ricos |
| 8 | Qualidade e Testes | Cobertura 80%+, CI local, documentação |
| 9 | Preparação para Escala | Multi-tenancy, deploy, monitoramento (futuro) |

Ver [Roadmap.md](Roadmap.md) para detalhamento completo de cada fase.

---

## Documentação do Projeto

| Arquivo | Conteúdo |
|---|---|
| `CLAUDE.md` | Instruções para Claude Code: arquitetura, comandos, convenções |
| `Roadmap.md` | Todas as etapas divididas e mapeadas com status |
| `Prompt.md` | Prompt independente de contexto para iniciar sessões |
| `CHANGELOG.md` | Histórico de mudanças significativas |
| `README.md` | Documentação geral, instalação, uso |

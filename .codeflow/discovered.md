---
versão: 1.0
status: estável
atualizado: 2026-07-01
data_inspeção: 2026-07-01
meta_skill: discover
superseded_by: null
---

# Discovered: snapshot de 2026-07-01

## O que foi inspecionado

1. `CLAUDE.md`, `README.md`, `Roadmap.md`, `CHANGELOG.md` — propósito, direção de produto e histórico de versões.
2. Configs de stack: `backend/pyproject.toml` (deps, ruff, mypy strict, pytest), `frontend/package.json`, `Makefile`, `.pre-commit-config.yaml`, `.github/workflows/{ci,cd}.yml`.
3. Backend `core/`: `config.py`, `security.py`, `deps.py`, `database.py`, `main.py`.
4. Backend `api/v1/`: 10 routers (auth, users, meals, weight, hydration, mood, dashboard, ai, reminders, push) — 47 endpoints.
5. Backend `services/`: domínio (meal, dashboard, profile, user, reminder, log, auth, push) + `ai/` (ai_client, meal_parser, vision_parser, food_lookup, context_builder, insights_generator, pattern_analyzer, utils) + `nutrition/tdee.py`.
6. Backend `workers/`: `celery_app.py` (beat com 6 tarefas) + `tasks/{reminders,reports,maintenance}.py`.
7. Backend `models/` (12 modelos + enums), `schemas/`, `tests/` (unit + integration + smoke), `alembic/versions/` (10 migrations).
8. Frontend: `app/` (páginas auth + 10 páginas dashboard + onboarding), `lib/api.ts` + 8 hooks, `components/` (37 arquivos), `types/index.ts`, `middleware.ts`, seam next-auth `api/auth/[...nextauth]/route.ts`, `e2e/`.
9. Infra: Dockerfiles multi-stage, `docker-compose.{dev,,backend}.yml`, `Caddyfile`, `scripts/deploy.sh`.
10. Auditoria existente: `docs/auditoria/` (relatório preliminar, achados, plano-correcao, 11 docs por frente, 23 artefatos brutos).
11. Histórico git (últimos ~30 commits + commits desde a auditoria) e revalidação fresca de ruff/mypy hoje.

## Hipóteses formadas

- [confirmada] Stack backend é FastAPI + SQLAlchemy 2 async + Celery/Redis + Pydantic v2 + Groq (confirmada pela inspeção de `pyproject.toml` e código).
- [confirmada] IA usa **Groq** (Llama 3.3 / Llama 4 Scout), não Gemini (confirmada por `ai_client.py` e CHANGELOG v0.7.0; a memória local `MEMORY.md` estava desatualizada citando Gemini).
- [confirmada] Bots Telegram/WhatsApp foram **removidos** — app é dashboard-web-only (confirmada por commit `98f5e1d`, CHANGELOG v0.7.0 e `conectar/page.tsx` que redireciona; restam apenas enums `MealSource`/`ConversationChannel` e `.pyc` órfãos em `backend/app/bots/`).
- [confirmada] Frontend usa **next-auth** (CredentialsProvider embrulhando o JWT do backend), divergindo do CLAUDE.md que diz "sem next-auth" (confirmada pela inspeção de `route.ts`, `middleware.ts`, `lib/api.ts`).
- [confirmada] Arquitetura em camadas com lógica só em services e DI via `Depends` (confirmada pela inspeção + pergunta 3 ao usuário).
- [confirmada] Áreas off-limits são `docs/auditoria/` e `backend/alembic/versions/` (confirmada pelo usuário na pergunta 1).
- [confirmada] Áreas de alto risco: auth/security, `services/ai`, alembic/schema e Web Push/VAPID (confirmada pelo usuário na pergunta 2).
- [confirmada] Prioridade atual é retomada/estabilização — validar e fechar achados da auditoria até uma versão estável antes de novas features (confirmada pelo usuário na pergunta 4).
- [confirmada] AUD-021 é real: `/login` devolve só tokens (sem objeto `user`), mas o `authorize` do next-auth lê `data.user?.id` (confirmada por leitura cruzada de `auth.py` e `route.ts`).
- [refutada] Memória local dizia IA=Gemini e bots ativos via Evolution API — inspeção mostra Groq e bots removidos.
- [refutada] CLAUDE.md dizia "Auth via JWT próprio (sem next-auth)" — next-auth está em uso no frontend.

## Perguntas feitas ao usuário e respostas

1. **Q:** Quais caminhos os workflows devem tratar como "não tocar" (off-limits)? **R:** `docs/auditoria/` e `backend/alembic/versions/`.
2. **Q:** Confirma o conjunto de áreas de alto risco (auth/security, services/ai, alembic/schema, Web Push/VAPID)? **R:** Sim, os quatro.
3. **Q:** Quais regras invariantes codificar na constitution (lógica só em services, commits PT-BR sem IA, GROQ_API_KEY só no backend, mypy strict + tipos)? **R:** Todas as quatro.
4. **Q:** Qual a prioridade/estado atual do projeto? **R:** Retomada — voltando ao projeto depois de muito tempo; entender o que existe e o que precisa ser corrigido; antes de novas features, quer uma versão 100% estável e validada.
5. **Q:** Qual o status dos canais Telegram (implementado) e WhatsApp (só enum)? **R:** Não lembrava ao certo e pediu investigação mais profunda; a reinspeção confirmou que ambos os bots foram removidos e o app é dashboard-web-only.

## Áreas marcadas como "não tocar"

- `docs/auditoria/` — artefatos da auditoria (achados, plano, relatórios); registro histórico, não editar via workflow comum.
- `backend/alembic/versions/` — migrations geradas; alterar migration já aplicada corrompe o histórico do banco.

## Artefatos gerados a partir deste discovered

- `.codeflow/constitution.md` — versão 1.0
- `.codeflow/manifest.md` — versão 1.0
- `.codeflow/INDEX.md` — versão 1.0

## Limitações da inspeção

- Foram feitas 5 perguntas substantivas (dentro do alvo). Diversas ambiguidades foram resolvidas pela inspeção profunda a pedido do usuário, sem virar pergunta: o mecanismo de auth (next-auth sobre JWT do backend), o padrão arquitetural (camadas) e o estado dos bots (removidos, verificado via git/CHANGELOG) foram determinados por leitura de código e histórico.
- Não foi executado `pytest` completo nesta sessão (exige subir Postgres/Redis); a cobertura de 62% e a contagem de testes vêm da auditoria de 2026-05-10/11, com ruff/mypy revalidados frescos hoje (idênticos ao baseline, pois o código de backend não mudou desde então).
- O estado detalhado de "o que existe vs. o que precisa ser corrigido" está em `docs/auditoria/` (57 achados, plano em 4 ondas) — fonte autoritativa para a fase de estabilização.

## Anexo — estado de correção (retomada)

- 57 achados abertos (🔴 2 · 🟠 14 · 🟡 21 · 🟢 20); plano em `docs/auditoria/plano-correcao.md` (uma tarefa = um PR, 4 ondas).
- Desde a auditoria houve apenas 2 commits: criação do plano e remoção das credenciais do código (AUD-038 etapa 2).
- Críticos vivos: AUD-016 (Seq Scan + N+1 em `food_lookup`) e AUD-038 (credencial ainda presente no histórico git — rewrite e rotação de senha pendentes).

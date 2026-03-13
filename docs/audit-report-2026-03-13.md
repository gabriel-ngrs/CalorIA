# Relatório de Auditoria — CalorIA
**Data:** 2026-03-13
**Ferramenta:** MCP Playwright (Google Chrome headless)
**Ambiente:** Docker Dev (`docker-compose.dev.yml`)
**Usuário de teste:** `auditcaloria@gmail.com`

---

## 1. Resumo Executivo

| Categoria | Total | OK | Problema |
|---|---|---|---|
| Páginas Frontend | 11 | 10 | 1 |
| Endpoints GET | 18 | 18 | 0 |
| Endpoints POST/PATCH/DELETE | 16 | 16 | 0 |
| Erros de console | — | — | 2 padrões recorrentes |
| Performance crítica | — | — | 2 alertas |

---

## 2. Páginas Frontend

### 2.1 Mapa de Rotas

| Rota | Título | Status | Tempo nav | APIs chamadas |
|---|---|---|---|---|
| `/login` | CalorIA — Login | ✅ 200 | — | — |
| `/register` | CalorIA — Cadastro | ✅ 200 | — | — |
| `/onboarding` | CalorIA — Onboarding | ✅ 200 | 922ms ⚠️ | `GET /users/me/profile` |
| `/dashboard` | CalorIA — Dashboard | ✅ 200 | 470ms ⚠️ | `GET /dashboard/today`, `GET /dashboard/macros-chart`, `GET /auth/me` |
| `/refeicoes` | CalorIA — Refeições | ✅ 200 | ~300ms | `GET /meals?date=` |
| `/peso` | CalorIA — Peso | ✅ 200 | ~250ms | `GET /weight`, `GET /dashboard/weight-chart` |
| `/hidratacao` | CalorIA — Hidratação | ✅ 200 | ~300ms | `GET /hydration/today`, `GET /hydration/history` |
| `/humor` | CalorIA — Humor | ✅ 200 | ~250ms | `GET /mood` |
| `/relatorios` | CalorIA — Relatórios | ✅ 200 | ~400ms | `GET /macros-chart`, `GET /weight-chart`, `GET /mood`, `GET /hydration/history` |
| `/lembretes` | CalorIA — Lembretes | ✅ 200 | ~250ms | `GET /reminders` |
| `/insights` | CalorIA — Insights IA | ✅ 200 | ~200ms | — (on-demand) |
| `/perfil` | CalorIA — Perfil | ✅ 200 | ~300ms | `GET /auth/me`, `GET /users/me/profile` |
| `/conectar` | CalorIA — Conectar Bot | ✅ 200 | ~200ms | `GET /auth/me` |

### 2.2 Bug Encontrado — Loop de Onboarding

**Severidade:** 🔴 Alta
**Descrição:** Usuários sem `calorie_goal` definido ficam presos em loop infinito entre `/dashboard` → `/onboarding` → `/dashboard` → `/onboarding`.

**Causa raiz (`dashboard/page.tsx:69`):**
```typescript
if (!isLoading && user && !user.calorie_goal) {
  router.replace("/onboarding");
}
```

O componente `/onboarding` não marca o onboarding como "concluído" quando o usuário clica "Pular" 3 vezes — ele retorna ao passo 1 ao invés de redirecionar ao dashboard com o estado salvo.

**Reprodução:**
1. Criar novo usuário via `/register`
2. Tentar acessar `/dashboard` sem definir `calorie_goal`
3. Observar redirect loop

**Solução sugerida:** Persistir flag `onboarding_completed` no backend (campo na model `User`) e checar ela antes de redirecionar.

---

## 3. Endpoints de API Backend

### 3.1 Endpoints GET — Todos Funcionais

| Endpoint | Status | Tempo | Observações |
|---|---|---|---|
| `GET /health` | ✅ 200 | 29ms | — |
| `GET /api/v1/auth/me` | ✅ 200 | 14ms | — |
| `GET /api/v1/users/me` | ✅ 200 | 14ms | — |
| `GET /api/v1/users/me/profile` | ✅ 200 | 12ms | — |
| `GET /api/v1/dashboard/today` | ✅ 200 | 15ms | — |
| `GET /api/v1/dashboard/weekly` | ✅ 200 | 15ms | — |
| `GET /api/v1/dashboard/macros-chart?days=7` | ✅ 200 | 12ms | — |
| `GET /api/v1/dashboard/weight-chart?limit=30` | ✅ 200 | 14ms | — |
| `GET /api/v1/meals` | ✅ 200 | 15ms | — |
| `GET /api/v1/meals/daily-summary?date=2026-03-13` | ✅ 200 | 14ms | — |
| `GET /api/v1/weight` | ✅ 200 | 11ms | — |
| `GET /api/v1/hydration/today` | ✅ 200 | 14ms | — |
| `GET /api/v1/hydration/history?days=7` | ✅ 200 | 13ms | — |
| `GET /api/v1/mood` | ✅ 200 | 12ms | — |
| `GET /api/v1/reminders` | ✅ 200 | 28ms | — |
| `GET /api/v1/ai/suggest-meal` | ✅ 200 | **1063ms** ⚠️ | Gemini API — lento |
| `GET /api/v1/ai/patterns?days=7` | ✅ 200 | 19ms | Cache Redis hit |
| `GET /api/v1/ai/nutritional-alerts?days=7` | ✅ 200 | 22ms | Cache Redis hit |
| `GET /api/v1/ai/goal-adjustment` | ✅ 200 | 17ms | Cache Redis hit |
| `GET /api/v1/ai/monthly-report?month=3&year=2026` | ✅ 200 | 31ms | Cache Redis hit |

### 3.2 Endpoints POST/PATCH/DELETE — Todos Funcionais

| Endpoint | Status | Tempo | Observações |
|---|---|---|---|
| `POST /api/v1/auth/register` | ✅ 201 | 397ms | Bcrypt hash — esperado |
| `POST /api/v1/auth/login` | ✅ 200 | ~80ms | — |
| `POST /api/v1/meals` | ✅ 201 | 46ms | Campo `date` obrigatório |
| `GET /api/v1/meals/:id` | ✅ 200 | 17ms | — |
| `PATCH /api/v1/meals/:id` | ✅ 200 | 28ms | — |
| `DELETE /api/v1/meals/:id` | ✅ 204 | 27ms | — |
| `POST /api/v1/weight` | ✅ 201 | 22ms | Campo `date` obrigatório |
| `POST /api/v1/hydration` | ✅ 201 | 149ms | Campos `date` e `time` obrigatórios |
| `POST /api/v1/mood` | ✅ 201 | 21ms | Campo `date` obrigatório |
| `POST /api/v1/reminders` | ✅ 201 | 32ms | `days_of_week` aceita inteiros (0-6), não strings |
| `PATCH /api/v1/reminders/:id/toggle` | ✅ 200 | 36ms | — |
| `DELETE /api/v1/reminders/:id` | ✅ 204 | 33ms | — |
| `POST /api/v1/ai/analyze-meal` | ✅ 200 | **5719ms** ⚠️ | Gemini API — latência alta |
| `POST /api/v1/ai/insights` | ✅ 200 | **2588ms** ⚠️ | Gemini API — latência alta |
| `POST /api/v1/telegram/link-token` | ✅ 200 | 13ms | — |
| `POST /api/v1/whatsapp/link-token` | ✅ 200 | 13ms | — |

---

## 4. Erros de Console Recorrentes

### 4.1 Token Expirado no Primeiro Carregamento (401 → retry)

**Ocorrência:** Em **todas as páginas** ao navegar
**Padrão observado:**
```
[API✗] GET /api/v1/auth/me  ERR  —  401 Unauthorized
[API↺] 401 → retry com token fresco
[API←] GET /api/v1/auth/me  200  ~30ms
```

**Explicação:** O access token expira (30min) e o cliente tenta primeiro com o token em cache, recebe 401, e então faz refresh automaticamente. O retry funciona, mas gera **double request** em toda navegação quando o token está perto do vencimento.

**Impacto:** UX degradada (loading delay extra de ~50-100ms) + logs poluídos.

**Sugestão:** Implementar refresh proativo (antes do token expirar) usando o `expires_at` salvo na sessão do next-auth.

### 4.2 Manifest.json com Erro de Sintaxe

**Ocorrência:** Em todas as páginas
**Erro:**
```
Manifest: Line: 1, column: 1, Syntax error. @ http://localhost:3000/manifest.json
```

**Causa:** O arquivo `manifest.json` do PWA está com sintaxe inválida ou retornando HTML.

**Impacto:** Baixo — não quebra funcionalidade, mas impede instalação como PWA.

### 4.3 Meta Tag Deprecated

**Ocorrência:** Em todas as páginas
```
<meta name="apple-mobile-web-app-capable" content="yes"> is deprecated
```

**Sugestão:** Substituir por `<meta name="mobile-web-app-capable" content="yes">` no layout.

---

## 5. Performance

### 5.1 Navegação Frontend

| Transição | Tempo | Avaliação |
|---|---|---|
| `/login` → `/` | **41.755ms** 🔴 | Crítico — Cold start do Next.js |
| `/` → `/dashboard` | 470ms ⚠️ | Aceitável em dev/turbo |
| `/dashboard` → `/onboarding` | 694–922ms ⚠️ | Aceitável |

> ⚠️ O tempo de 41s no primeiro acesso é esperado no modo dev com Turbopack (cold compilation). Em produção com `next build` + `next start` seria < 500ms.

### 5.2 API Backend

| Categoria | Tempo médio | Avaliação |
|---|---|---|
| Endpoints simples (GET/POST) | 10–30ms | ✅ Excelente |
| Dashboard aggregation | 15ms | ✅ Excelente |
| Hydration POST | 149ms | ⚠️ Observar |
| AI suggest-meal | 1.063ms | ⚠️ Gemini API |
| AI analyze-meal | 5.719ms | 🔴 Lento (usuário aguarda) |
| AI insights | 2.588ms | ⚠️ Gemini API |

### 5.3 Observação sobre Cache Redis

Os endpoints de AI (`/patterns`, `/nutritional-alerts`, `/goal-adjustment`, `/monthly-report`) retornaram em 17–31ms, indicando que o **cache Redis está funcionando corretamente** para esses endpoints. O `suggest-meal` (1s) não tem cache por ser dinâmico.

---

## 6. Screenshots Capturados

| Arquivo | Página |
|---|---|
| `01_login.png` | Tela de login |
| `02_onboarding.png` | Onboarding — dados físicos |
| `03_dashboard.png` | Dashboard (usuário sem dados) |
| `04_refeicoes.png` | Refeições — lista vazia |
| `05_peso.png` | Peso — sem registros |
| `06_hidratacao.png` | Hidratação — 0ml registrado |
| `07_humor.png` | Humor & Energia |
| `08_relatorios.png` | Relatórios — 7d sem dados |
| `09_lembretes.png` | Lembretes — formulário criação |
| `10_insights.png` | Insights IA |
| `11_perfil.png` | Perfil — dados preenchidos |
| `12_conectar.png` | Conectar Bot — Telegram/WhatsApp |

---

## 7. Resumo de Issues Encontrados

| # | Severidade | Tipo | Descrição |
|---|---|---|---|
| 1 | 🔴 Alta | Bug | Loop infinito no onboarding para usuários sem `calorie_goal` |
| 2 | 🟡 Média | Performance | `POST /ai/analyze-meal` com 5.7s de latência — sem feedback visual de loading |
| 3 | 🟡 Média | UX | Double request em toda navegação por token expirado (401 → retry) |
| 4 | 🟠 Baixa | Erro | `manifest.json` com syntax error — PWA não instalável |
| 5 | 🟠 Baixa | Deprecação | Meta tag `apple-mobile-web-app-capable` deprecated |
| 6 | 🟠 Baixa | DX | `POST /reminders` — `days_of_week` aceita apenas inteiros (0-6), não strings como `"monday"` — pouco intuitivo para consumidores externos da API |

---

## 8. Infraestrutura

| Serviço | Status | Observações |
|---|---|---|
| Frontend (Next.js 14) | ✅ Up | Turbopack dev mode |
| Backend (FastAPI) | ✅ Up | Todos os endpoints respondendo |
| PostgreSQL | ✅ Healthy | — |
| Redis | ✅ Healthy | Cache funcionando |
| Celery Worker | ✅ Up | Processando tasks |
| Celery Beat | ✅ Up | Enviando reminders a cada 60s |
| Telegram Bot | ✅ Up | Polling ativo |

---

*Auditoria realizada via MCP Playwright + testes diretos na API com curl.*

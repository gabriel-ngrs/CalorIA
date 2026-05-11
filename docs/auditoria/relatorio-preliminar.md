# Relatório Preliminar da Auditoria — CalorIA

**Período de execução:** 2026-05-10 → 2026-05-11
**Branch:** `dev`
**Escopo:** backend (FastAPI + Celery), frontend (Next.js + TypeScript), banco (PostgreSQL + Redis), infraestrutura (Docker + Caddy + CI/CD), documentação e DX.

---

## Visão geral

- **Total de achados:** **57** (🔴 2 · 🟠 14 · 🟡 21 · 🟢 20)
- **Passos executados:** 47 (FASE 0 → FASE 13)
- **Commits gerados:** 47, todos em PT-BR seguindo Conventional Commits
- **Artefatos brutos arquivados:** 23 (em `docs/auditoria/artefatos/`)

### Distribuição por frente

| Frente | Tema | Críticos | Altos | Médios | Baixos | Total |
|---|---|---|---|---|---|---|
| A | Arquitetura | — | — | 2 | — | 2 |
| B | Backend | — | 4 | 2 | 3 | 9 |
| C | IA | 1 | — | 4 | 1 | 6 |
| D | Frontend | — | 1 | 1 | 5 | 7 |
| E | Workers | — | 3 | 1 | 1 | 5 |
| F | Banco de dados | — | 1 | 4 | 3 | 8 |
| G | Segurança | 1 | 2 | 1 | — | 4 |
| H | Testes | — | 3 | — | — | 3 |
| I | Qualidade | — | — | 2 | 2 | 4 |
| J | Observabilidade | — | — | 3 | 2 | 5 |
| K | DX / Docs | — | — | 1 | 3 | 4 |

**Frentes mais afetadas em alta severidade:** G (2 + 1 crítico — segurança), B (4 altos — backend), E (3 altos — workers).

### Frentes em bom estado

- **A (Arquitetura)** — sem altos ou críticos; só refatorações localizadas (push.py inline SQL, InsightsGenerator quebra).
- **H (Testes)** — apenas 3 achados, todos altos, mas tratáveis: bug de fixture, gap de cobertura, BASE_URL do e2e.

---

## Métricas de baseline (capturadas em PASSO 1.x)

| Ferramenta | Resultado |
|---|---|
| ruff | 14 errors (9 auto-fixable) |
| mypy `--strict` | 6 errors em 1 arquivo (`ai_client.py`) |
| radon avg CC | 16.56 (C) — 9 blocos ≥ B; pior: `build_meal_context` D(25) |
| pytest cov | **62%** (99 passed · 1 failed em smoke `test_ai_client` — falha externa de rede) |
| pip-audit | 0 vulnerabilidades |
| npm audit | 16 vulnerabilidades (4 low · 3 moderate · 9 high · 0 critical) |
| eslint | 1 warning, 0 errors |
| tsc `--noEmit` | 0 errors |
| LOC backend | 5.708 |
| LOC frontend | 10.573 |
| Tests backend LOC | 1.845 |
| Tests frontend LOC | 1.553 |
| Endpoints REST | 47 |
| Modelos SQLAlchemy | 12 |
| Migrações Alembic | 10 |

---

## Top 10 achados de maior impacto

Critério: severidade primeiro, depois raio de impacto operacional, depois esforço de fix vs. valor.

1. **AUD-016 🔴 (Frente C)** — `food_lookup` faz Seq Scan; medido 585ms isolado → ~14.6s por refeição com N+1 do AUD-006; **2 usuários concorrentes derrubam o backend**. Fix curto: trocar `OR similarity()` por `SET LOCAL pg_trgm.similarity_threshold` (esforço S, ganho 70×).
2. **AUD-038 🔴 (Frente G)** — credenciais reais (`gabrielnegreirossaraiva38@gmail.com` + senha) commitadas em `frontend/e2e/auth.spec.ts:37-38` em repo público. Plano em 4 etapas obrigatórias (rotar agora, remover do código, reescrever histórico, secret scan em CI).
3. **AUD-006 🟠 (Frente B)** — N+1 em `food_lookup` (caminho síncrono, ~25 queries por refeição). Amplifica AUD-016. Esforço M; fix de batch único reduz para 1 query.
4. **AUD-026 🟠 (Frente E)** — `dispatch_due_reminders` usa `datetime.now()` naive. Bug latente: hoje funciona por acidente (containers em SP), quebra silenciosamente em migração para UTC ou usuários fora de SP.
5. **AUD-039 🟠 (Frente G)** — `SECRET_KEY` default `"insecure-default-key-change-in-production"` sem fail-fast. Se a env de prod não tiver `SECRET_KEY`, JWTs ficam forjáveis com string no source. Padrão também em `NEXTAUTH_SECRET` (frontend).
6. **AUD-037 🟠 (Frente F)** — sem backup automatizado do Postgres. Hoje 🟠 porque ainda não há prod com tráfego real, **vira 🔴 no instante do primeiro deploy** — dados de saúde irreplicáveis.
7. **AUD-040 🟠 (Frente G)** — zero rate limit em qualquer camada. Combina com AUD-038 (credential stuffing efetivo) e com AUD-013 (abuso de tokens Groq invisível).
8. **AUD-043 🟠 (Frente H)** — cobertura crítica em 10 módulos < 50%, todos no núcleo IA + push + workers. Sem teste **e** sem log estruturado (AUD-049) = regressões só aparecem quando o usuário reclama.
9. **AUD-044 🟠 (Frente H)** — `auth.spec.ts` ignora `baseURL` do Playwright config e default aponta para Vercel preview pública; cada `npx playwright test` local cria usuário em produção e faz credential stuffing com AUD-038.
10. **AUD-025 🟠 (Frente E)** — 3 workers (`reminders`, `reports`, `maintenance`) usam `asyncio.get_event_loop()` deprecated em Python 3.10+, erro em 3.14. Risco de `RuntimeError: Event loop is closed` em produção sob carga.

**Bônus** (não no top 10, mas pega muita gente em rede): **AUD-021 🟠** (frontend lê `data.user.*` que o backend não envia) — silencioso hoje, mas degrada UX e vira showstopper se algum componente passar a depender de `session.user.id`.

---

## Priorização recomendada para correção

Os achados se agrupam naturalmente em **3 ondas de fix**, cada onda concebida para ser um conjunto de PRs entregáveis em paralelo. A ordem não é arbitrária: cada onda desbloqueia/facilita a próxima.

### Onda 1 — Segurança e bug latente (1-2 semanas, alta prioridade)

**Goal: impedir vazamento e bug operacional.**

1. **PR Segurança crítica** (resolve 4 achados): AUD-038 + AUD-039 + AUD-047 (gitleaks no pre-commit + CI) + AUD-057 (CONTRIBUTING.md alinhado).
   - Rotar senha do mantenedor; mover credenciais para env; validator de `SECRET_KEY`/`NEXTAUTH_SECRET`; gitleaks pre-commit + GitHub Action; rewrite do histórico.
2. **PR Performance crítica** (resolve 2 achados, desbloqueia muito): AUD-016 (similarity threshold) + AUD-006 (batch food_lookup). Esforço S+M.
3. **PR Workers — TZ e _run** (resolve 4 achados): AUD-025 (asyncio.run + helper compartilhada) + AUD-026 (TZ-aware) + AUD-027 (`user.water_goal_ml`) + AUD-028 (consolidar handling de 410 em `PushService.send_with_cleanup`).
4. **PR Backup Postgres** (AUD-037): cron `pg_dump | gzip` + offsite + script de restore + documentar em `deploy.md`. Bloqueia o primeiro deploy seguro.

**Total de achados fechados na Onda 1:** ~12 (1 crítico + 5-6 altos + alguns médios bundlados).

### Onda 2 — Resiliência e observabilidade (2-3 semanas)

**Goal: vislumbrar o sistema sob carga real.**

1. **PR Rate limit + headers** (AUD-040 + AUD-041 + AUD-052): `slowapi` Redis-backed + bloco `header { }` no Caddyfile.backend + plugin `caddy-ratelimit`.
2. **PR Logs estruturados + request_id** (AUD-049 + AUD-013): structlog + `request_id` no contextvar + `LOG_LEVEL` no `Settings` + ruff `G004`.
3. **PR Health checks separados** (AUD-050): `/health/live` + `/health/ready` (Postgres + Redis) + leitura dinâmica de versão (resolve metade do AUD-054).
4. **PR Sentry + APM** (AUD-051): `sentry-sdk` no backend e `@sentry/nextjs` no frontend; gating via env; tagging com `user_id`/`request_id`/`release`.
5. **PR Validação de inputs** (AUD-009 + AUD-010): `max_length` em `image_base64`, `notes`, `message`, `question`, `raw_input`.

**Total de achados fechados na Onda 2:** ~10.

### Onda 3 — Refatoração IA + testes + qualidade (3-6 semanas)

**Goal: tornar evolução de IA segura e cobrir o núcleo.**

1. **PR Refator IA** (resolve 5+ achados): AUD-002 (decompor InsightsGenerator em 3 services) + AUD-015 (`BaseAIFoodParser`) + AUD-014 (pool Redis persistente) + AUD-046 (tipos Groq + aioredis) + AUD-012 (retry com `groq.RateLimitError` em vez de substring). Cobertura sobe junto via AUD-043 Onda 1.
2. **PR Cobertura de testes — Onda 1** (AUD-043 parte 1 + AUD-042): fix do `clean_db` autouse + unit tests de `food_lookup`, `meal_parser`, `vision_parser`, `ai_client` para ≥ 70%. Travar `--cov-fail-under=70`.
3. **PR Índices de banco** (AUD-030 + AUD-031 + AUD-032): compostos `(user_id, date)` em meals/logs; `(user_id, read)` em notifications; remover `taco_foods_name_key` UNIQUE.
4. **PR Frontend modularização** (AUD-018 + AUD-022): quebrar `refeicoes/page.tsx` em sub-componentes; extrair `useVoiceCapture` (resolve `any` de SpeechRecognition).
5. **PR DX cleanup** (AUD-045 + AUD-048 + AUD-054 + AUD-055): ruff em `app/` + scripts decision + `.dockerignore` + bump de versão para 0.7.0 + ADR-002 expandida + ADR-009/010.

**Total de achados fechados na Onda 3:** ~20.

### Onda 4 — Hardening final e backlog frio (~30 dias)

**Goal: limpar o backlog 🟢 acumulado.**

PRs menores cobrindo: AUD-001 (push.py service), AUD-003 (response_model), AUD-004 (from None), AUD-005 (paginação), AUD-011 (type ignores), AUD-017 (extract_json robusto), AUD-019 (optimistic updates), AUD-020 (console.log gated), AUD-023 (PWA SW skipWaiting), AUD-024 (bundle analyzer), AUD-029 (índice updated_at), AUD-033 (downgrade real), AUD-034 (remover MealSource legado), AUD-035 (pool sizing), AUD-036 (db_logger debug), AUD-053 (decidir Caddyfile dual), AUD-056 (runbook operacional incremental).

**Total de achados fechados na Onda 4:** ~17.

---

## Esforço total estimado

| Onda | Achados fechados | Esforço estimado | Calendário sugerido |
|---|---|---|---|
| 1 — Segurança + bug latente | ~12 | 30-40h | 1-2 semanas |
| 2 — Resiliência + observabilidade | ~10 | 25-35h | 2-3 semanas |
| 3 — Refator IA + cobertura | ~20 | 60-90h | 3-6 semanas |
| 4 — Hardening + backlog frio | ~17 | 30-50h | distribuído |
| **Total** | **~57** | **~150-200h** | **~3 meses** |

**Caveats:**

- Estimativas são para um desenvolvedor solo focado. Pair programming ou múltiplas frentes em paralelo encurtam o calendário.
- Onda 1 **bloqueia** o primeiro deploy com tráfego real (segurança + backup); o resto é incremental e pode ser feito pós-deploy contanto que se acompanhe Sentry (Onda 2).
- Onda 3 (refator IA) é a única que **pode escalar de M para L** se a quebra do `InsightsGenerator` revelar acoplamentos não previstos. Mitigação: começar com `BaseAIFoodParser` (AUD-015) que é independente.

---

## Referências

- **Plano:** [`docs/auditoria/plano.md`](plano.md) — escopo, frentes, riscos pré-execução.
- **Runbook:** [`docs/auditoria/runbook.md`](runbook.md) — 47 passos com método e commit prescritos.
- **Achados:** [`docs/auditoria/achados.md`](achados.md) — 57 AUDs ordenados por severidade/frente.
- **Log:** [`docs/auditoria/log.md`](log.md) — cronologia detalhada de cada passo executado.
- **Notas por frente:**
    - [`01-arquitetura.md`](01-arquitetura.md), [`02-backend.md`](02-backend.md), [`03-ia.md`](03-ia.md)
    - [`04-frontend.md`](04-frontend.md), [`05-workers.md`](05-workers.md), [`06-banco.md`](06-banco.md)
    - [`07-seguranca.md`](07-seguranca.md), [`08-testes.md`](08-testes.md), [`09-qualidade.md`](09-qualidade.md)
    - [`10-observabilidade.md`](10-observabilidade.md), [`11-dx-docs.md`](11-dx-docs.md)
- **Artefatos brutos:** [`docs/auditoria/artefatos/`](artefatos/) — 23 arquivos `.txt`/`.xml`/`.json` com saídas das ferramentas (ruff, mypy, radon, pytest, npm audit, EXPLAIN ANALYZE, etc.).

---

## Estado de "Definition of Done" da auditoria

- [x] FASE 0 — estrutura inicial criada.
- [x] FASE 1 — baseline capturado (8 ferramentas, 9 artefatos).
- [x] FASE 2 — Frente A (Arquitetura): 5 passos.
- [x] FASE 3 — Frente B (Backend): 7 passos.
- [x] FASE 4 — Frente C (IA): 5 passos.
- [x] FASE 5 — Frente D (Frontend): 7 passos.
- [x] FASE 6 — Frente E (Workers): 5 passos.
- [x] FASE 7 — Frente F (Banco): 5 passos.
- [x] FASE 8 — Frente G (Segurança): 7 passos.
- [x] FASE 9 — Frente H (Testes): 4 passos.
- [x] FASE 10 — Frente I (Qualidade): 6 passos.
- [x] FASE 11 — Frente J (Observabilidade): 4 passos.
- [x] FASE 12 — Frente K (DX/Docs): 4 passos.
- [x] FASE 13.1 — achados.md reordenado por severidade.
- [x] FASE 13.2 — relatório preliminar (este arquivo).
- [ ] FASE 13.3 — CHANGELOG e README atualizados (próximo passo).
- [ ] FASE 13.4 — encerramento e handoff em log.md (último passo).

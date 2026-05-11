# Frente K — DX e Documentação

**Plano:** ver `plano.md` § Frente K.

## Achados desta frente

- AUD-054 — Versões dessincronizadas: `pyproject.toml`, `app/main.py` e `package.json` em `0.1.0` vs CHANGELOG em `[0.7.0]` (🟢 baixa).
- AUD-055 — ADR-002 (Groq) registra a decisão atual mas não documenta alternativas avaliadas; decisões recentes (Vercel + backend Hetzner, workflow de release) sem ADR (🟢 baixa).
- AUD-056 — `docs/deploy.md § Troubleshooting` cobre 4 cenários básicos mas faltam runbooks operacionais para incidentes específicos: Groq free-tier estourado, push HTTP 410 em massa, Celery worker travado, restore de backup Postgres (🟡 média).
- AUD-057 — `CONTRIBUTING.md:42` afirma que pre-commit roda "ruff, mypy, eslint" mas só `ruff` está configurado — documentação engana o contribuidor (🟢 baixa; combina com AUD-047).

## Notas e contexto

### § K.4 Versionamento — dessincronia confirmada (de `artefatos/K1-versions.txt`)

| Fonte | Versão | Local |
|---|---|---|
| `backend/pyproject.toml:7` | `0.1.0` | metadado do pacote Python |
| `backend/app/main.py:36` | `0.1.0` | `FastAPI(version="0.1.0")` → reportado no OpenAPI/Swagger |
| `backend/app/main.py:74` (health) | `0.1.0` | `/health` retorna no body (cross-ref AUD-050) |
| `frontend/package.json:version` | `0.1.0` | metadado do pacote Node |
| `CHANGELOG.md:14` | **`[0.7.0]` (2026-05-10)** | release mais recente |
| `CHANGELOG.md:10` | `[Não lançado]` | seção de WIP atual |

**Análise**: os 4 metadados de pacote/runtime estão **6 minor versions** atrás do CHANGELOG. O projeto operou com bumps narrativos (CHANGELOG cresce a cada release menor) mas nunca propagou para os arquivos canônicos. Comum em projetos cedo no ciclo, e **ninguém quebrou** porque:

1. Não há publicação em PyPI/npm (pacotes internos, deploy via SSH).
2. Nenhum cliente externo lê o `pyproject.toml` para checar versão (não há SDK consumido por terceiros).
3. O `/health` (AUD-050) reporta `0.1.0`, mas nenhum monitoring estava ligado mesmo (AUD-051).

Mas vira problema no momento que:

- **Sentry/APM é ativado** (AUD-051): eventos vão chegar com `release="0.1.0"`, todas as regressões agrupadas como se fossem da mesma versão; reverte para um deploy anterior fica impossível identificar onde quebrou.
- **`/health` é monitorado** por UptimeRobot/CloudWatch (AUD-050): rollback automático baseado em versão impossível.
- **Bug report do usuário**: "tô vendo erro X" — qual deploy? Sem versão real, log/issue não correlaciona com o commit que introduziu.

**Recomendação consolidada (AUD-054)** — Esforço S (<1h):

1. **Fonte única de verdade**: escolher um dos formatos abaixo e propagar:
    - **Opção A (preferida)**: manter versão em `pyproject.toml` e ler dinamicamente em runtime via `importlib.metadata.version("caloria-backend")` (já recomendado em AUD-050). Frontend espelha em `package.json`, idealmente sincronizado por script em release.
    - **Opção B**: usar uma git tag (`v0.7.0`) como fonte de verdade e derivar via `setuptools-scm` (Python) e `git describe` (Node). Mais robusto para deploy mas exige mais setup.
2. **Bump release atual**: atualizar `pyproject.toml` e `package.json` para `0.7.0` agora (alinhar com `CHANGELOG.md:14`).
3. **Substituir hardcode** em `app/main.py:36,74` por leitura dinâmica (combina com AUD-050).
4. **Workflow de release**: documentar em `CONTRIBUTING.md` ou ADR — "antes de mergear para main, abrir PR de release que atualiza CHANGELOG, pyproject e package.json em sincronia". Cross-ref com AUD-049 (release como tag de log estruturado) e AUD-051 (release como tag do Sentry).

### § K.1 ADRs — estado e gaps

**Premissa do runbook era falsa.** O plano previa "criar ADR-006 documentando decisão histórica de Groq". Na verdade, o repo **já tem 8 ADRs** (001–008) em `docs/architecture.md`:

| ID | Tema |
|---|---|
| ADR-001 | PostgreSQL para testes (não SQLite) |
| ADR-002 | Groq (Llama) como provedor de IA |
| ADR-003 | Web Push VAPID em vez de bots externos |
| ADR-004 | Celery com Redis como broker (sem RabbitMQ) |
| ADR-005 | JWT com blacklist em Redis |
| ADR-006 | Banco nutricional com pg_trgm + pipeline dois estágios + sanity check |
| ADR-007 | Sistema de design Glassmorphism + Neumorphism |
| ADR-008 | CI/CD com GitHub Actions |

**Análise dos ADRs existentes:**

- ✅ **Cobertura boa** das decisões estruturais do projeto.
- ⚠️ **ADR-002 (Groq) é "skinny"** — descreve a decisão atual e o estado anterior (Gemini), mas **não documenta alternativas consideradas** (OpenAI, Anthropic Claude, modelos locais via Ollama). Não há trade-offs explícitos: por que não OpenAI? Por que não auto-hospedar? Quanto custaria Anthropic vs Groq para o volume esperado? Decisão é defensável, mas o caminho não é rastreável.
- ⚠️ **ADR-003 (Web Push)** menciona "antes era Telegram/WhatsApp" mas não cita por que a migração aconteceu — só fato consumado.
- ⚠️ **ADR-006 (banco nutricional)** é o mais bem escrito — cita números (kcal feijão carioca, threshold 0.65, latência < 20ms). Serve de template para retoque dos outros.

**ADRs que faltam** (surgidos durante esta auditoria):

| ID proposto | Tema | Cross-ref |
|---|---|---|
| **ADR-009** | Frontend hospedado externamente (Vercel) — backend self-hosted (Hetzner) | AUD-053 — explica por que `docker-compose.backend.yml` é o canônico e não o full-stack |
| **ADR-010** | Workflow de release — sincronia CHANGELOG ↔ pyproject ↔ package.json | AUD-054 — antes de mergear para `main`, PR de release atualiza os 3 |
| **ADR-011** (opcional) | Observabilidade: Sentry + structlog + readiness checks | consolida AUD-049/050/051 quando implementados |

**Recomendação (AUD-055)** — Esforço S (<1h):

1. **Retocar ADR-002**: adicionar seção "Alternativas consideradas" com lista breve (OpenAI gpt-4o-mini, Anthropic Claude Haiku, Ollama+Llama3.1 local) e o porquê de cada rejeição (custo, latência, complexidade operacional).
2. **Adicionar ADR-009**: registrar a decisão "Vercel + Hetzner backend-only". Documenta a presença de `docker-compose.backend.yml` como canônico e justifica.
3. **Adicionar ADR-010** quando AUD-054 for atacado.
4. **Adicionar ADR-011** quando AUD-049/050/051 forem atacados (pode esperar — ADRs são para decisões tomadas, não para backlog).

ADR é a melhor ferramenta para fechar pendências de decisão arquitetural — combina bem com o padrão do runbook de listar "decisões pendentes" em vários passos.

### § K.1.b Runbook operacional (de `artefatos/K3-docs-list.txt`)

**Estrutura atual de `docs/`:**

```
docs/
├── architecture.md          (8 ADRs)
├── auditoria/               (este trabalho)
├── deploy.md                391 LOC — guia de deploy + Troubleshooting básico
├── deploy-checklist.md      152 LOC — checklist sequencial pré-release
├── flow.md                  fluxo do registro ao banco
├── fluxos/                  11 subpastas com diagramas Mermaid por feature
├── git-workflow.md          branches e CI/CD
├── legacy/                  análise pré-migração
└── setup.md                 setup do zero
```

**Sem `docs/runbook-prod.md`** nem equivalente. Conteúdo operacional de incidente mora numa seção `## Troubleshooting` em `deploy.md` (linhas 352-391).

**O que existe** (4 cenários, `deploy.md:352-391`):

| Cenário | Ação documentada |
|---|---|
| App não abre no browser | `docker compose logs caddy/frontend` + DNS check |
| Erro 502 Bad Gateway | `logs backend` + `restart backend` |
| Banco de dados com erro | `logs backend | grep error` + `alembic upgrade head` |
| Push não chega | check permissão + `VAPID_PUBLIC_KEY` + logs celery |
| Reset com/sem dados | `down [-v]` + `up --build` + `alembic upgrade head` |

Cobertura razoável para problemas **básicos de Day 0**, mas **falta** instrumentação para incidentes específicos que o resto desta auditoria já identificou como possíveis:

| Cenário previsto pelo runbook | Estado | Vínculo |
|---|---|---|
| `GROQ_API_KEY` estoura free tier (429 sustentado, não transitório) | ❌ não documentado | AUD-012 (retry baseado em substring "429" pode falhar; AUD-013 sem visibilidade de custo) |
| Push HTTP 410 em mais de 50% das subs simultaneamente | ❌ não documentado | AUD-028 (cleanup já existe mas em 4 sites duplicados; sem alerta) |
| Worker Celery travado (beat sem disparar, worker consumindo sem retornar ack) | ❌ não documentado | AUD-025/-026/-027 (workers têm 3 bugs latentes que viram silenciosos sem este runbook) |
| Restore de backup do Postgres | ❌ não documentado | AUD-037 (sem backup automatizado; quando houver, restore é o "metade que falta") |
| Rotação de `SECRET_KEY` / `NEXTAUTH_SECRET` | ❌ não documentado | AUD-039 (defaults inseguros) — rotação exige logout em massa, raciocínio próprio |
| Resposta a Sentry alertando 5xx burst | ❌ N/A (Sentry não existe) | AUD-051 |

**Recomendação (AUD-056)** — Esforço M (1-4h, pode ser feito incremental):

Criar `docs/runbook-prod.md` (ou seção dedicada em `deploy.md`) com **uma seção por cenário** seguindo o formato canônico de runbook:

```markdown
## Cenário: Groq retorna 429 persistentemente

**Sintoma:** logs do backend mostram `groq.APIConnectionError` ou retry exausto;
usuários veem "Erro inesperado" ao registrar refeição.

**Verificar:**
1. `docker logs caloria_backend | grep "Rate limit Groq"` — confirma 429
2. https://console.groq.com/usage — quota disponível para o mês

**Mitigação imediata:**
- Se quota acabou: aumentar plano OU desativar análise IA temporariamente
  (`MEAL_AI_DISABLED=true` em `.env` — requer feature flag a implementar)
- Cache de IA (`AIClient`) ainda serve resultados conhecidos por 7 dias —
  refeições novas falham, repetidas funcionam.

**Causa raiz / pós-incidente:**
- Adicionar alerta Sentry (AUD-051) com threshold em 80% da quota.
- Revisar AUD-012 (retry baseado em substring é frágil).
```

Cenários a documentar (lista mínima):

1. **Groq 429 persistente** (cross-ref AUD-012, AUD-013, AUD-051).
2. **Push 410 em massa** (cross-ref AUD-028) — quando rodar limpeza manual extra; quando suspeitar de bug em vez de churn natural.
3. **Worker Celery travado** (cross-ref AUD-025/-026) — `docker exec caloria_celery_worker celery -A app.workers.celery_app inspect active`; quando reiniciar; checar lock files.
4. **Restore de backup Postgres** (cross-ref AUD-037) — `pg_restore` com `--clean --if-exists`; verificar estado do `pg_trgm` e do enum `MealSource`.
5. **Rotação de secrets** — `SECRET_KEY` → invalida todos os tokens; `NEXTAUTH_SECRET` → mesmo no frontend; `VAPID_*` → todas as subscriptions perdem alvo.
6. **Reset de banco em dev** (já parcialmente em `deploy.md:386-391`) — incluir aviso sobre seed obrigatório de `foods` (vide `deploy.md:233`).

Médio prazo, o runbook se acopla naturalmente com:
- AUD-049 — logs estruturados, `request_id` no log facilita "encontrar todas linhas do incidente".
- AUD-050 — `/health/ready` permite que monitoring detecte degradação antes do incidente virar pageable.
- AUD-051 — Sentry corta o "como descubro o problema" — o runbook responde "o que faço agora".

### § K.3 CONTRIBUTING e templates (de `artefatos/K4-contrib.txt`)

**Inventário do que existe:**

| Arquivo | LOC | Estado |
|---|---|---|
| `CONTRIBUTING.md` | 103 | ✅ presente — Setup, fluxo (refer a `git-workflow.md`), testes, convenções de commit, estrutura, dúvidas |
| `.github/PULL_REQUEST_TEMPLATE.md` | 24 | ✅ presente — descrição, tipo (4 opções), checklist (5 itens), como testar, screenshots |
| `.github/ISSUE_TEMPLATE/bug_report.md` | 34 | ✅ presente |
| `.github/ISSUE_TEMPLATE/feature_request.md` | 23 | ✅ presente |
| `.github/dependabot.yml` | (não inspecionado em LOC) | ✅ presente |
| `.github/workflows/ci.yml` | (já analisado em outras frentes) | ✅ |
| `.github/workflows/cd.yml` | (já analisado) | ✅ |

**Cobertura geral muito boa** — onboarding de contribuidor está coberto. Pontos a considerar:

1. ✅ Setup do dev environment é claro e ordenado (4 passos com docker compose, alembic, pre-commit).
2. ✅ Convenções de commit têm exemplos em PT-BR alinhados com CLAUDE.md.
3. ✅ PR template inclui checklist de "sem `.env` ou secrets no código" — bom proxy mental para o problema do AUD-038, **mas não é enforcement** (e o checklist não é validado por CI).
4. ⚠️ **Documentação divergente do realidade**: `CONTRIBUTING.md:42` afirma:
    > "Os hooks rodam automaticamente antes de cada commit: `ruff`, `mypy`, `eslint`."
    Falso. PASSO 10.4 (AUD-047) confirmou que **só `ruff` e `ruff-format`** estão no `.pre-commit-config.yaml`. Mypy e ESLint **não** são pre-commit. Contribuidor novo lê, confia, comita um diff que regride mypy ou eslint, e CI quebra. Documentação está **adiantada** ao código — provavelmente reflete a intenção original do projeto, que ficou pendente.

**Outros pequenos pontos** (sem achado dedicado):
- `CONTRIBUTING.md` não menciona o workflow de release (cross-ref AUD-054) — quando atacar AUD-054, atualizar CONTRIBUTING também.
- PR template não tem item sobre "checar se o achado tem AUD correspondente" — específico do contexto atual da auditoria; pode acrescentar checkbox "se está corrigindo um achado de auditoria, citar o ID" quando os AUDs começarem a virar PRs.

**Recomendação (AUD-057)** — Esforço S (< 10 min, trivial mas evita confusão):

Opção A (mais rápida): trocar a linha 42 de `CONTRIBUTING.md` para refletir o estado atual:
```diff
- Os hooks rodam automaticamente antes de cada commit: `ruff`, `mypy`, `eslint`.
+ Os hooks rodam automaticamente antes de cada commit: `ruff` (lint + format), `pre-commit-hooks` (trailing whitespace, large files, branch protection).
```

Opção B (preferível, com mais valor): combinar com fix de AUD-047 — adicionar mypy/eslint/gitleaks ao `.pre-commit-config.yaml` e **manter** a documentação como está (o texto vira verdadeiro). Resolve dois achados de uma vez.

# Frente K — DX e Documentação

**Plano:** ver `plano.md` § Frente K.

## Achados desta frente

- AUD-054 — Versões dessincronizadas: `pyproject.toml`, `app/main.py` e `package.json` em `0.1.0` vs CHANGELOG em `[0.7.0]` (🟢 baixa).
- AUD-055 — ADR-002 (Groq) registra a decisão atual mas não documenta alternativas avaliadas; decisões recentes (Vercel + backend Hetzner, workflow de release) sem ADR (🟢 baixa).

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

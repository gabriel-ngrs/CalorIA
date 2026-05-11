# Frente G — Segurança

**Plano:** ver `plano.md` § Frente G.

## Achados desta frente

- AUD-038 (🔴 crítica) — credenciais reais (`gabrielnegreirossaraiva38@gmail.com` / `***REMOVED***`) hardcoded em `frontend/e2e/auth.spec.ts` e no histórico git público
- AUD-039 (🟠 alta) — `SECRET_KEY` tem default `"insecure-default-key-change-in-production"` sem fail-fast; deploy esquecendo a env var dá origem a forge de JWTs trivial
- AUD-040 (🟠 alta) — ausência total de rate limit no backend (sem `slowapi`, sem diretiva no Caddy); `/auth/*` exposto a credential stuffing, `/ai/*` exposto a abuso de tokens Groq
- AUD-041 (🟡 média) — headers HTTP de segurança ausentes (X-Frame-Options, X-Content-Type-Options, CSP, Referrer-Policy, Permissions-Policy); apenas HSTS é injetado automaticamente pelo Caddy

## G.6 Credenciais expostas no código

Comando: `rg -n "***REMOVED***|gabrielnegreirossaraiva38@gmail" .` + `git log --all --full-history -p -- frontend/e2e/auth.spec.ts | grep 082405`. Artefato: `artefatos/G1-creds.txt`.

### O que foi exposto

| Campo | Valor | Onde |
|---|---|---|
| Email | `gabrielnegreirossaraiva38@gmail.com` | `frontend/e2e/auth.spec.ts:37`, também (neutro) em `docs/legacy/analise.md:90` |
| Senha | `***REMOVED***` | `frontend/e2e/auth.spec.ts:38` |

Commit de origem: **`4737257`** (2026-04-29 15:59 -03), `test(e2e): adiciona testes Playwright para fluxo de autenticação`. Autor confirma que é o mantenedor (mesmo email).

### Por que é 🔴 crítica e não 🟠

- **Repo no GitHub** (`https://github.com/gabriel-ngrs/CalorIA.git`) — `git log -p` permite extração trivial mesmo após remoção do HEAD.
- **Senha em texto claro**, não hash, não derivada — uso direto.
- **Potencial password reuse** — se a senha está em outros serviços (Google, banco, etc.), comprometimento se propaga.
- O par email+senha é tudo que precisa para login no CalorIA + tentativa de credential stuffing em outros sites.

### Ações pendentes (FORA do escopo da auditoria — pós-relatório)

> Estas ações **não** são entregáveis desta auditoria, mas precisam acontecer com urgência. Documentadas aqui para registro.

1. **AGORA** — trocar `***REMOVED***` em todos os lugares onde ela esteja em uso (no app CalorIA + qualquer outro serviço onde tenha sido reusada).
2. **Imediato** — substituir `auth.spec.ts:37-38` por leitura de `process.env.E2E_LOGIN_*`; configurar como GitHub Actions secret. Padrão recomendado: deixar o teste de "login com user existente" depender da fixture criada pelo teste de `register` no mesmo arquivo (já usa `TEST_EMAIL`/`TEST_PASSWORD` em `:27-29`).
3. **Importante** — `git filter-repo --replace-text expressions.txt` para remover do histórico + force-push. Mesmo se "ninguém viu", a defesa em profundidade pede a remoção.
4. **CI scan** — `gitleaks-action` no `.github/workflows/ci.yml` para falhar PRs futuros com qualquer string que pareça segredo. Pre-commit hook `gitleaks protect --staged` para pegar antes do push.

Após (3), tratar a senha como **comprometida** independentemente — vazou por ~12 dias antes deste achado; assumir que cópias circulam.

## G.1 Auth flow review

Comando: leitura de `backend/app/api/v1/auth.py` + `app/core/security.py` + `app/core/deps.py` + `app/services/auth_service.py` + `app/core/config.py`.

### Checklist

| Item | Estado | Evidência |
|---|---|---|
| Algorithm é HS256 (não none) | ✅ | `config.py:33` `ALGORITHM = "HS256"`; `security.py:39` passa `algorithms=[settings.ALGORITHM]` (lista — evita ataque `alg=none`) |
| Access TTL = 30min | ✅ | `config.py:34` `ACCESS_TOKEN_EXPIRE_MINUTES = 30` |
| Refresh TTL = 30 dias | ✅ | `config.py:35` `REFRESH_TOKEN_EXPIRE_DAYS = 30` |
| Refresh blacklisted após uso | ✅ | `auth.py:77` `await blacklist_token(data.refresh_token)` em `/refresh` antes de emitir o novo par |
| Token type validado em decode | ✅ | `deps.py:32` `if payload.get("type") != "access"`; `auth.py:65` `if payload.get("type") != "refresh"` |
| `from None` em raises de credenciais | ✅ | `deps.py:39` e `auth.py:69` ambos usam `raise ... from None` (não vazam stack do JWT lib) |
| Default SECRET_KEY é seguro? | ❌ | `config.py:32` default = `"insecure-default-key-change-in-production"` **sem validator de fail-fast** — **AUD-039** |

### Pontos positivos extras

- `bcrypt.hashpw` com `gensalt()` default (12 rounds) em `security.py:13`. Padrão atual.
- Logout requer `get_current_user_id` para invalidar refresh — caller prova posse do access. Defesa contra "logout de outra pessoa" se vazar refresh isolado.
- Blacklist via Redis `setex` com TTL = TTL restante do refresh — entrada some sozinha quando expiraria de qualquer forma. Bem desenhado.

### Pontos a observar (sem achado novo)

- `auth_service.py:19-20` abre conexão Redis nova por chamada (`aioredis.from_url(...)` sem singleton). Mesmo padrão do AUD-014 (AIClient), aplicado aqui também. PR de "pool Redis singleton" cobre os dois.
- `auth_service.py:32-33` engole exceção em `blacklist_token` com `logger.warning` apenas. Se Redis estiver fora, o refresh continua válido até o TTL — degradação silenciosa em vez de fail-secure. Defensável (auth não pode quebrar se Redis cair), mas vale monitorar via observabilidade.
- `decode_token` não passa `leeway` — clock skew entre app/server pode causar edges raros (token "do futuro" rejeitado em segundos antes do `now` do servidor). Trivial; não é problema na arquitetura atual (1 host).
- `VAPID_PRIVATE_KEY`/`VAPID_PUBLIC_KEY` também têm defaults vazios sem fail-fast — push silenciosamente não funciona. Cabe no mesmo validator do AUD-039.

## G.3 Validação de inputs (DoS / overflow)

Comando: `grep -rn "max_length\|StringConstraints" backend/app/schemas/` + `grep -rn ": str\b\|: str | None" backend/app/schemas/*.py | grep -v max_length`.

### Cross-referência com achados existentes

A análise sistemática de `max_length` foi feita em **PASSO 3.6** (Frente B). Os achados:

- **AUD-009 (🟠 alta)** — `PhotoAnalysisRequest.image_base64` sem `max_length` — DoS via base64 gigante.
- **AUD-010 (🟡 média)** — 8 campos texto livre sem `max_length` (`InsightRequest.question`, `MealItemCreate.raw_input`, `Meal*.notes`, `*Log.notes`, `Reminder*.message`).

Este passo (8.3) revisita os schemas com lente de segurança. **Confirmado** que ambos achados continuam válidos.

### Verificações adicionais nesta varredura

| Schema | Campo | Estado |
|---|---|---|
| `MealAnalysisRequest.description` | `Field(min_length=3, max_length=2000)` | ✅ — runbook listava como gap, mas já tem constraint |
| `MealItemCreate.food_name` | `max_length=255` | ✅ |
| `MealItemCreate.unit` | `max_length=50` | ✅ |
| `UserCreate.password` | `min_length=8, max_length=128` | ✅ |
| `UserCreate.name` | `min_length=1, max_length=255` | ✅ |
| `Meal*.name` | `max_length=255` | ✅ |
| `PhotoAnalysisRequest.image_base64` | sem | ❌ **AUD-009** |
| `PhotoAnalysisRequest.mime_type` | `str = Field(default="image/jpeg")` — sem `Literal[...]` | observação (não-achado) |
| `PhotoAnalysisRequest.meal_type` | `str | None = None` — não validado e **ignorado** no endpoint (`analyze_photo` em `ai.py`) | observação (dead field) |
| `MealAnalysisRequest.meal_type` | idem — `analyze_meal:54` chama `parse(description=...)` sem passar `meal_type` | observação (dead field) |
| `*Log.notes`, `Reminder.message`, `Insight.question` | sem max | ❌ **AUD-010** |

### Observações sem achado novo

- **`mime_type` aceita string arbitrária** — deveria ser `Literal["image/jpeg", "image/png", "image/webp"]`. Risco de segurança baixo (Groq Vision rejeita MIMEs inválidos), mas seria higienização de contrato. Combinar no fix do AUD-009 (que já recomenda `Literal[...]` em recommendation).
- **`meal_type` em `MealAnalysisRequest`/`PhotoAnalysisRequest` é dead field** — front pode enviar, backend nunca consome. `_infer_meal_type` em `context_builder.py:103` deriva do texto, ignorando o que vem na request. Smell de contrato, não bug funcional. Fica registrado para limpeza futura.

Sem achado novo neste passo — encaminha-se para o release combinado dos AUD-009 + AUD-010 + observações acima.

## G.5 Rate limit assessment

Comando: `rg -n "rate_limit|slowapi|RateLimit|Limiter" backend/`; `grep -n "rate" Caddyfile`; `grep -n "middleware" backend/app/main.py`. Artefato: `artefatos/G4-rate-limit.txt`.

### Estado atual

| Camada | Rate limit | Evidência |
|---|---|---|
| FastAPI middleware | ❌ ausente | 0 hits para `slowapi`/`Limiter` no `backend/` |
| Caddy | ❌ ausente | 0 hits para `rate` no `Caddyfile` |
| Reverse proxy externo | n/a | sem CDN/WAF na frente; só Caddy |
| Captcha em `/register` | ❌ ausente | sem hCaptcha/Turnstile |

`backend/app/main.py` registra apenas `CORSMiddleware` (linha 42) e um `timing_middleware` (linha 52). Sem nenhuma defesa contra throughput abusivo.

### Endpoints expostos por categoria de risco

| Endpoint | Risco | Limite sugerido |
|---|---|---|
| `POST /auth/login` | credential stuffing (combina com AUD-038) | 5/min/IP |
| `POST /auth/register` | bot signup, inflar `users` | 3/hora/IP |
| `POST /auth/refresh` | abuse de blacklist Redis | 30/min/IP |
| `POST /ai/analyze-meal` | tokens Groq (free tier limit, $ em pago) | 30/min/user |
| `POST /ai/analyze-photo` | idem + payload base64 grande (combina AUD-009) | 20/min/user |
| `GET /ai/insights/*` | tokens Groq | 60/min/user |
| `GET /notifications/unread-count` | DoS por polling (combina AUD-031) | 120/min/user |
| Demais endpoints autenticados | DoS genérico | 120/min/user (default) |

Detalhes em **AUD-040**.

### Gravidade contextual

CLAUDE.md afirma "Arquitetura pensada para escalar para múltiplos usuários no futuro". Hoje com 1 usuário não há exploração ativa, mas o sistema está pronto pra deploy (Roadmap § 9 com CI/CD verde). **Rate limit é fundação** — sem ele, qualquer abertura ao público vira presa fácil. Severidade 🟠 hoje, escalonando se ficar pendente além do primeiro deploy.

## G.8 Headers de segurança e CORS

Comando: leitura de `Caddyfile`, `frontend/next.config.mjs`, `backend/app/main.py`.

### Headers HTTP

| Header | Estado | Origem |
|---|---|---|
| `Strict-Transport-Security` | ✅ presente | Caddy injeta automaticamente quando HTTPS ativo (Let's Encrypt via `{$APP_DOMAIN}`) |
| `X-Frame-Options` | ❌ ausente | — |
| `X-Content-Type-Options` | ❌ ausente | — |
| `Content-Security-Policy` | ❌ ausente | — |
| `Referrer-Policy` | ❌ ausente | — |
| `Permissions-Policy` | ❌ ausente | — |
| `Server` exposto | ⚠️ sim (Caddy não anonimiza por default) | — |

`Caddyfile` define apenas `handle` blocks de proxy + `log` — sem `header { }`. `next.config.mjs` não declara `headers()`. `main.py` (FastAPI) só registra CORS + timing.

Detalhes em **AUD-041**.

### CORS (FastAPI)

`main.py:42-49`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600,
)
```

| Item | Avaliação |
|---|---|
| `allow_origins` | Lê de `BACKEND_CORS_ORIGINS` (string CSV) — vazio por default → bloqueia tudo. ✅ defensivo |
| `allow_credentials=True` | Necessário para enviar JWT via Bearer + cookies (NextAuth). Combina mal com `allow_origins=["*"]`, mas como o default é vazio, não é problema atual |
| `allow_methods=["*"]` | Permissivo. Aceitável para API REST |
| `allow_headers=["*"]` | Permissivo. Aceitável para enviar `Authorization`+`Content-Type` |
| `max_age=3600` | OK — preflight cache reduz round-trip |

**Risco contextual**: se alguém setar `BACKEND_CORS_ORIGINS` em produção sem cuidado (ex.: `*`), com `allow_credentials=True` o navegador rejeita por especificação, mas se a config virar `["*"]` strict, browsers podem permitir CSRF-via-XHR. Recomendação: validator no `Settings` rejeitando `*` quando `allow_credentials=True`. Combina com fix do AUD-039 (mesmo arquivo).

Sem novo achado — comportamento defensivo por default.

## G.6.1 Secret scan no histórico git

Comando: `git log --all --full-history -p | grep -iE "(api_key|secret_key|password|token).*[=:].*[a-zA-Z0-9]{16}" | head -100`. Artefato: `artefatos/G6-secret-scan.txt`. `gitleaks` não disponível no ambiente.

### Resultados (12 matches no regex)

| Match | Categoria | Status |
|---|---|---|
| `+POSTGRES_PASSWORD=SenhaForteAqui123!` em `docs/deploy.md:178` | Placeholder de documentação | ⚠️ não é segredo, mas é "plausível" (deployer descuidado pode deixar como está) |
| `+GROQ_API_KEY=gsk_...sua_chave_aqui` / `gsk_SUACHAVEGROQ` / `gsk_...` | Placeholder em `.env.example`/`docs` | ✅ obviamente placeholder |
| `setApiToken(...)` / `accessTokenExpires` / `RefreshAccessTokenError` | Identificadores TS NextAuth | ✅ falso positivo (nomes de função/variável, não segredo) |
| `LinkTokenResponse` / `WhatsAppLinkTokenResponse` | Schema legado | ✅ falso positivo |

### Verificações complementares

- **`.env` no histórico**: `git log --all -- .env` → 0 commits. ✅ nunca foi commitado.
- **`.gitignore`** contém `.env`, `.env.local`, `.env.*.local`, `*.env` (linhas 8-11). ✅ defesa em camadas.
- **`.env.example`** usa apenas defaults de dev (`POSTGRES_PASSWORD=caloria`) — sem valor sensível.

### Limitação do regex

A regex `[a-zA-Z0-9]{16}` exige 16+ caracteres consecutivos. **Não pega senhas curtas com caracteres especiais** — é exatamente por isso que `***REMOVED***` (8 chars + especiais) do **AUD-038** passou despercebido por esse scan e só foi encontrado pela busca específica do PASSO 8.1. Para cobertura mais ampla, usar `gitleaks` (instalar via `brew/apt` ou rodar via `gitleaks-action` em CI).

### Conclusão

**Sem novos achados nesta varredura**. O único segredo real no histórico é o do AUD-038, encontrado por busca direcionada no PASSO 8.1. Falso positivos são identificadores legítimos do NextAuth e schemas legados Telegram/WhatsApp. Recomendação reforça AUD-038 § Recomendação (4): `gitleaks-action` em CI captura tipos que o regex perdeu.

## Notas e contexto

(seção G.7 autorização será preenchida no PASSO 8.7)

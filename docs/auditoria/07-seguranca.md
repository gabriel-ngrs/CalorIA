# Frente G — Segurança

**Plano:** ver `plano.md` § Frente G.

## Achados desta frente

- AUD-038 (🔴 crítica) — credenciais reais (`gabrielnegreirossaraiva38@gmail.com` / `***REMOVED***`) hardcoded em `frontend/e2e/auth.spec.ts` e no histórico git público
- AUD-039 (🟠 alta) — `SECRET_KEY` tem default `"insecure-default-key-change-in-production"` sem fail-fast; deploy esquecendo a env var dá origem a forge de JWTs trivial

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

## Notas e contexto

(seções G.3-G.5, G.7-G.8 serão preenchidas nos PASSOS 8.3-8.7)

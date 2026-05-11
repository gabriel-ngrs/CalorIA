# Frente G — Segurança

**Plano:** ver `plano.md` § Frente G.

## Achados desta frente

- AUD-038 (🔴 crítica) — credenciais reais (`gabrielnegreirossaraiva38@gmail.com` / `***REMOVED***`) hardcoded em `frontend/e2e/auth.spec.ts` e no histórico git público

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

## Notas e contexto

(seções G.1-G.5, G.7-G.8 serão preenchidas nos PASSOS 8.2-8.7)

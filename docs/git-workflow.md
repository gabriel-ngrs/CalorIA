# Git Workflow — CalorIA

Estratégia de branches e fluxo de desenvolvimento adotados no projeto.

---

## Branches

| Branch | Propósito | Proteção |
|---|---|---|
| `main` | Código publicado — sempre estável | Protegida (ver "Proteção da `main`" abaixo): os dois checks do CI são obrigatórios e valem também para administradores |
| `dev` | Integração de features — branch de trabalho | CI roda a cada push |
| `hotfix/*` | Correções urgentes em produção | Criada a partir da `main` |

### Regras

- **Nunca commitar direto na `main`** — toda mudança passa por PR. O hook
  `no-commit-to-branch` bloqueia localmente e os checks obrigatórios bloqueiam no
  GitHub, já que um push direto chega sem check verde
- `dev` recebe o desenvolvimento do dia a dia
- Hotfixes são criados a partir da `main`, mergeados na `main` e depois na `dev`

---

## Fluxo Normal (feature → dev → main)

```
1. Desenvolver na branch dev
   git checkout dev
   git pull origin dev
   ... (commits do desenvolvimento)
   git push origin dev

2. Quando pronto para release, abrir PR: dev → main
   - CI roda automaticamente (lint + testes + build)
   - Revisar o PR conscientemente antes de mergear
   - Ao mergear: o deploy é disparado à mão (ver "CI/CD" abaixo)

3. Voltar para dev e continuar desenvolvendo
   git checkout dev
```

---

## Fluxo Hotfix (bug urgente em produção)

```
1. Criar branch a partir da main
   git checkout main
   git pull origin main
   git checkout -b hotfix/descricao-do-bug

2. Corrigir o bug e commitar
   git commit -m "fix(escopo): corrige descrição do bug"

3. PR: hotfix/* → main
   - CI roda
   - Ao mergear: disparar o deploy à mão (`gh workflow run cd.yml`)

4. Sincronizar dev com o hotfix
   git checkout dev
   git merge main
   git push origin dev

5. Deletar branch de hotfix
   git branch -d hotfix/descricao-do-bug
```

---

## CI/CD

| Evento | O que acontece |
|---|---|
| Push na `dev` | CI: ruff, mypy, pytest com cobertura, gitleaks, ESLint, Jest e build do frontend |
| PR aberto para `main` | CI: mesmo que acima — obrigatório passar |
| Merge na `main` | **Nada automático hoje.** O CD roda por `workflow_dispatch` |

O `cd.yml` está em disparo manual por decisão registrada: a topologia mudou para
host único (ADR-009) e a volta do gatilho `push: main` é trabalho da Fase E.4 da
spec 002, junto com a troca do `sleep 10` por espera de healthcheck.

Ver `.github/workflows/ci.yml` e `.github/workflows/cd.yml`.

---

## Proteção da `main`

Configurada em 2026-08-09. O que está ativo, verificável por
`gh api repos/gabriel-ngrs/CalorIA/branches/main/protection`:

| Regra | Estado |
|---|---|
| Checks obrigatórios | `Backend — lint e testes` e `Frontend — lint e build`, com a branch obrigada a estar atualizada (`strict`) |
| Vale para administradores (`enforce_admins`) | Sim |
| Force-push e deleção da `main` | Bloqueados |
| Revisão de PR obrigatória | **Não** — projeto de um desenvolvedor só; o Roadmap 9.1 pede PR e CI obrigatórios, não um segundo aprovador |

Para reproduzir num fork: **GitHub → Settings → Branches → Add rule**, pattern
`main`, marcar *Require status checks to pass before merging* com os dois checks
acima e *Do not allow bypassing the above settings*.

---

## Configurar o CD

O deploy roda por SSH num servidor remoto. Os secrets vivem no environment
`production` (**GitHub → Settings → Environments**):

| Secret | Valor |
|---|---|
| `SERVER_HOST` | IP do servidor |
| `SERVER_USER` | Usuário SSH |
| `SERVER_SSH_KEY` | Conteúdo da chave privada (`cat ~/.ssh/id_ed25519`) |

Hoje **não há servidor contratado** — a stack de produção roda localmente
(ADR-009), então o workflow existe e só é disparado à mão. Ver `docs/deploy.md`.

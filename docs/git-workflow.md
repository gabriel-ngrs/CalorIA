# Git Workflow — CalorIA

Estratégia de branches e fluxo de desenvolvimento adotados no projeto.

---

## Branches

| Branch | Propósito | Proteção |
|---|---|---|
| `main` | Código em produção — sempre estável | Protegida: PR obrigatório, CI deve passar |
| `dev` | Integração de features — branch de trabalho | CI roda a cada push |
| `hotfix/*` | Correções urgentes em produção | Criada a partir da `main` |

### Regras

- **Nunca commitar direto na `main`** — toda mudança passa por PR
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
   - Ao mergear: CD faz deploy automático em produção

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
   - Ao mergear: deploy automático em produção

4. Sincronizar dev com o hotfix
   git checkout dev
   git merge main
   git push origin dev

5. Deletar branch de hotfix
   git branch -d hotfix/descricao-do-bug
```

---

## CI/CD Automático

| Evento | O que acontece |
|---|---|
| Push na `dev` | CI: roda lint, mypy, pytest, build do frontend |
| PR aberto para `main` | CI: mesmo que acima — obrigatório passar |
| Merge na `main` | CD: SSH no servidor → git pull → docker compose up → alembic |

Ver `.github/workflows/ci.yml` e `.github/workflows/cd.yml`.

---

## Proteger a branch main no GitHub

1. Acesse: **GitHub → Settings → Branches → Add rule**
2. Branch name pattern: `main`
3. Marque:
   - ✅ Require a pull request before merging
   - ✅ Require status checks to pass before merging
     - Adicione: `Backend — lint e testes` e `Frontend — lint e build`
   - ✅ Do not allow bypassing the above settings

---

## Configurar o CD (deploy automático)

Antes do primeiro deploy automático, configure os secrets no GitHub:

1. **GitHub → Settings → Environments → New environment** → nome: `production`
2. Dentro do environment, adicione os secrets:

| Secret | Valor |
|---|---|
| `SERVER_HOST` | IP do servidor (ex: `49.12.123.45`) |
| `SERVER_USER` | Usuário SSH (ex: `root`) |
| `SERVER_SSH_KEY` | Conteúdo da chave privada (`cat ~/.ssh/id_ed25519`) |

Depois que o servidor estiver configurado (ver `docs/deploy.md`), todo merge na `main` dispara o deploy automaticamente.

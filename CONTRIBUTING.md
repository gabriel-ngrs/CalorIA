# Contribuindo com o CalorIA

---

## Setup do ambiente de desenvolvimento

### Pré-requisitos

- Docker e Docker Compose
- Python 3.12+
- Node.js 20+
- Git

### 1. Clonar e configurar

```bash
git clone https://github.com/gabriel-ngrs/CalorIA.git
cd CalorIA
```

### 2. Subir tudo com um comando

```bash
make init
```

`make init` cria o `.env` a partir do `.env.example`, builda as imagens, sobe os
serviços de desenvolvimento e aplica as migrações. Preencha o `GROQ_API_KEY` no
`.env` antes de usar a análise de refeição (chave gratuita em
[console.groq.com/keys](https://console.groq.com/keys)) e recrie os serviços com
`make down && make dev-d`.

Dashboard em `http://localhost:3010`, API em `http://localhost:8010`.
`make help` lista todos os alvos.

### 3. Instalar pre-commit hooks

```bash
pip install pre-commit
pre-commit install
```

Os hooks rodam automaticamente antes de cada commit, sobre os arquivos em staging:

| Hook | O que faz |
|---|---|
| `ruff` (`--fix`) e `ruff-format` | Lint e formatação do backend (`^backend/`) |
| `gitleaks` | Varredura de segredos com as regras de `.gitleaks.toml` |
| `trailing-whitespace`, `end-of-file-fixer` | Higiene de arquivo (exceto `backend/app/prompts/`, onde espaço é conteúdo) |
| `check-yaml`, `check-merge-conflict`, `check-added-large-files` | Sanidade de arquivos |
| `no-commit-to-branch` | Bloqueia commit direto na `main` |

`mypy` e `eslint` **não** rodam no hook — são gates do CI e do `make check`, porque
precisam do projeto inteiro, não só dos arquivos em staging. Para reproduzi-los
localmente antes do push:

```bash
make check
```

---

## Fluxo de trabalho

Ver [`docs/git-workflow.md`](docs/git-workflow.md) para a estratégia completa de branches.

**Resumo:**
1. Desenvolva na branch `dev`
2. Quando pronto, abra um PR de `dev` → `main`
3. CI deve estar verde antes do merge — a `main` é protegida e os dois checks são obrigatórios
4. O deploy é **manual** por enquanto (`workflow_dispatch` no `cd.yml`); a volta do
   gatilho automático depende do novo deploy (spec 002, Fase E.4)

---

## Rodando os testes

```bash
# Backend
cd backend && pytest

# Backend com cobertura
cd backend && pytest --cov=app --cov-report=html

# Frontend
cd frontend && npm test

# Lint e type check
cd backend && ruff check . && mypy app/
cd frontend && npm run lint
```

---

## Convenções de commit

Conventional Commits em português:

```
feat(escopo): descrição curta no imperativo
fix(api): corrige cálculo de macros
refactor(services): extrai lógica de análise
docs(readme): atualiza instruções de deploy
chore(deps): atualiza dependências do backend
```

- Descrição em minúsculas, sem ponto final
- Máximo 72 caracteres na primeira linha
- Commitar a cada mudança significativa

---

## Estrutura do projeto

Ver [`README.md`](README.md) para a estrutura completa de pastas e a descrição de cada módulo.

---

## Dúvidas

Abra uma issue com o template adequado (bug ou feature request).

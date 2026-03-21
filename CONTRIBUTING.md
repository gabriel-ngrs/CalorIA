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
cp .env.example .env
# Edite o .env com suas credenciais
```

### 2. Subir os serviços

```bash
docker compose -f docker-compose.dev.yml up
```

### 3. Rodar as migrações

```bash
docker compose exec backend alembic upgrade head
```

### 4. Instalar pre-commit hooks

```bash
pip install pre-commit
pre-commit install
```

Os hooks rodam automaticamente antes de cada commit: `ruff`, `mypy`, `eslint`.

---

## Fluxo de trabalho

Ver [`docs/git-workflow.md`](docs/git-workflow.md) para a estratégia completa de branches.

**Resumo:**
1. Desenvolva na branch `dev`
2. Quando pronto, abra um PR de `dev` → `main`
3. CI deve estar verde antes do merge
4. Ao mergear, o CD faz deploy automático em produção

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

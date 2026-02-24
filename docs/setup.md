# Guia de Setup — CalorIA

Instruções para configurar o ambiente de desenvolvimento do zero.

---

## Pré-requisitos

- Docker e Docker Compose
- Python 3.12+
- Node.js 20+
- PostgreSQL 16 (para testes locais sem Docker)

---

## 1. Clonar o repositório

```bash
git clone <repo-url>
cd CalorIA
```

---

## 2. Variáveis de ambiente

```bash
cp .env.example .env
```

Edite o `.env` com suas chaves:

| Variável | Obrigatória | Descrição |
|---|---|---|
| `DATABASE_URL` | ✅ | `postgresql+asyncpg://caloria:caloria@localhost:5432/caloria_db` |
| `REDIS_URL` | ✅ | `redis://localhost:6379/0` |
| `SECRET_KEY` | ✅ | Chave aleatória (mín. 32 chars). `python -c "import secrets; print(secrets.token_hex(32))"` |
| `GEMINI_API_KEY` | ✅ | Obter em [Google AI Studio](https://makersuite.google.com/app/apikey) |
| `TELEGRAM_BOT_TOKEN` | ⚪ | Opcional. Obter via [@BotFather](https://t.me/BotFather) |
| `EVOLUTION_API_URL` | ⚪ | Opcional. URL da instância Evolution API |
| `EVOLUTION_API_KEY` | ⚪ | Opcional. Chave da Evolution API |

---

## 3. Subir com Docker (recomendado)

```bash
# Desenvolvimento com hot reload
docker compose -f docker-compose.dev.yml up

# Apenas infraestrutura (postgres, redis, evolution_api)
docker compose -f docker-compose.dev.yml up postgres redis

# Produção local
docker compose up
```

A API estará em `http://localhost:8000` e o frontend em `http://localhost:3000`.

---

## 4. Setup manual do backend

```bash
cd backend

# Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Instalar dependências
pip install -e ".[dev]"

# Rodar migrações
alembic upgrade head

# Iniciar backend
uvicorn app.main:app --reload --port 8000
```

---

## 5. Setup manual do frontend

```bash
cd frontend

npm install
npm run dev
```

O frontend estará em `http://localhost:3000`.

---

## 6. Setup de testes do backend

### Criar banco de testes

```bash
# Conectar ao PostgreSQL
psql -U postgres

# Criar banco e usuário de testes
CREATE USER caloria WITH PASSWORD 'caloria';
CREATE DATABASE caloria_test OWNER caloria;
GRANT ALL PRIVILEGES ON DATABASE caloria_test TO caloria;
\q
```

### Rodar os testes

```bash
cd backend

# Todos os testes
pytest

# Com cobertura
pytest --cov=app --cov-report=html

# Apenas unitários
pytest tests/unit/

# Apenas integração
pytest tests/integration/

# Banco customizado (CI/CD)
TEST_DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/db_test" pytest
```

---

## 7. Setup de testes do frontend

```bash
cd frontend

npm install

# Rodar testes
npm test

# Com watch
npm test -- --watch

# Com cobertura
npm test -- --coverage
```

---

## 8. Pre-commit hooks

```bash
# Instalar pre-commit
pip install pre-commit

# Configurar hooks
pre-commit install

# Rodar manualmente
pre-commit run --all-files
```

---

## 9. Migrações

```bash
cd backend

# Criar nova migração após mudar modelos
alembic revision --autogenerate -m "descricao da mudanca"

# Aplicar migrações
alembic upgrade head

# Reverter última migração
alembic downgrade -1

# Ver histórico
alembic history
```

---

## 10. WhatsApp com Evolution API

1. Subir o serviço:
   ```bash
   docker compose up evolution_api
   ```
2. Acessar `http://localhost:8080` no painel da Evolution API
3. Criar uma instância com o nome `caloria`
4. Escanear o QR code com o WhatsApp
5. A sessão persiste no volume Docker entre restarts

---

## 11. Celery Workers

```bash
cd backend

# Worker
celery -A app.workers.celery_app worker --loglevel=info

# Agendador (Beat)
celery -A app.workers.celery_app beat --loglevel=info

# Monitoramento (Flower)
pip install flower
celery -A app.workers.celery_app flower
```

Acessar o Flower em `http://localhost:5555`.

---

## Comandos úteis

```bash
# Acessar banco de dados
docker exec -it caloria_postgres psql -U caloria -d caloria_db

# Ver logs
docker compose logs -f backend
docker compose logs -f celery_worker

# Resetar banco (desenvolvimento)
docker compose -f docker-compose.dev.yml down -v
docker compose -f docker-compose.dev.yml up

# Lint backend
cd backend && ruff check . && mypy app/

# Lint frontend
cd frontend && npm run lint
```

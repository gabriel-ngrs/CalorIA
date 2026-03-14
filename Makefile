# =============================================================================
# CalorIA — Makefile
# Atalhos para os comandos mais usados no desenvolvimento.
#
# Uso:
#   make <alvo>
#   make help       ← lista todos os alvos disponíveis
# =============================================================================

.DEFAULT_GOAL := help
COMPOSE_DEV   := docker compose -f docker-compose.dev.yml
COMPOSE_PROD  := docker compose

# =============================================================================
# Ambiente
# =============================================================================

## Sobe todos os serviços em modo dev (hot reload)
dev:
	$(COMPOSE_DEV) up

## Sobe todos os serviços em modo dev em background
dev-d:
	$(COMPOSE_DEV) up -d

## Sobe apenas infra (postgres, redis, evolution_api) em dev
infra:
	$(COMPOSE_DEV) up postgres redis evolution_api

## Para e remove containers dev (mantém volumes)
down:
	$(COMPOSE_DEV) down

## Para, remove containers E volumes dev (reseta banco)
reset:
	$(COMPOSE_DEV) down -v

## Sobe ambiente de produção local
prod:
	$(COMPOSE_PROD) up -d

## Para produção
prod-down:
	$(COMPOSE_PROD) down

## Rebuilda todas as imagens dev
build:
	$(COMPOSE_DEV) build

## Rebuilda imagens sem usar cache
build-no-cache:
	$(COMPOSE_DEV) build --no-cache

# =============================================================================
# Banco de dados
# =============================================================================

## Aplica todas as migrações pendentes
migrate:
	$(COMPOSE_DEV) exec backend alembic upgrade head

## Cria nova migração (uso: make migration MSG="descricao")
migration:
	$(COMPOSE_DEV) exec backend alembic revision --autogenerate -m "$(MSG)"

## Mostra o histórico de migrações
migrate-history:
	$(COMPOSE_DEV) exec backend alembic history --verbose

## Desfaz a última migração
migrate-down:
	$(COMPOSE_DEV) exec backend alembic downgrade -1

## Abre o psql no container postgres
psql:
	docker exec -it caloria_postgres psql -U caloria -d caloria_db

## Popula banco com dados de desenvolvimento (seed completo)
seed:
	$(COMPOSE_DEV) exec backend python scripts/seed_all.py

## Popula apenas com usuário de dev (rápido)
seed-user:
	$(COMPOSE_DEV) exec backend python scripts/seed_dev_user.py

# =============================================================================
# Testes
# =============================================================================

## Roda todos os testes do backend
test-backend:
	$(COMPOSE_DEV) exec backend pytest

## Testes backend com relatório de cobertura
test-backend-cov:
	$(COMPOSE_DEV) exec backend pytest --cov=app --cov-report=html --cov-report=term-missing

## Roda testes do frontend
test-frontend:
	cd frontend && npm run test

## Roda todos os testes (backend + frontend)
test: test-backend test-frontend

# =============================================================================
# Qualidade de código
# =============================================================================

## Roda ruff + mypy no backend
lint-backend:
	$(COMPOSE_DEV) exec backend ruff check .
	$(COMPOSE_DEV) exec backend mypy app/

## Roda eslint no frontend
lint-frontend:
	cd frontend && npm run lint

## Linting em tudo
lint: lint-backend lint-frontend

## Formata backend com ruff
fmt:
	$(COMPOSE_DEV) exec backend ruff format .

# =============================================================================
# Logs
# =============================================================================

## Logs do backend em tempo real
logs-backend:
	$(COMPOSE_DEV) logs -f backend

## Logs do frontend em tempo real
logs-frontend:
	$(COMPOSE_DEV) logs -f frontend

## Logs do celery worker
logs-worker:
	$(COMPOSE_DEV) logs -f celery_worker

## Logs de todos os serviços
logs:
	$(COMPOSE_DEV) logs -f

# =============================================================================
# Utilitários
# =============================================================================

## Instala pre-commit hooks
hooks:
	pre-commit install

## Roda pre-commit em todos os arquivos
check:
	pre-commit run --all-files

## Status dos containers
ps:
	$(COMPOSE_DEV) ps

## Abre shell no container backend
shell-backend:
	$(COMPOSE_DEV) exec backend bash

## Abre shell no container frontend
shell-frontend:
	$(COMPOSE_DEV) exec frontend sh

## Lista alvos disponíveis com descrição
help:
	@echo ""
	@echo "  CalorIA — Comandos disponíveis"
	@echo ""
	@awk '/^## /{desc=substr($$0,4); next} /^[a-zA-Z_-]+:/{printf "  \033[36m%-20s\033[0m %s\n", substr($$1,1,length($$1)-1), desc}' $(MAKEFILE_LIST)
	@echo ""

.PHONY: dev dev-d infra down reset prod prod-down build build-no-cache \
        migrate migration migrate-history migrate-down psql seed seed-user \
        test test-backend test-backend-cov test-frontend \
        lint lint-backend lint-frontend fmt \
        logs logs-backend logs-frontend logs-worker \
        hooks check ps shell-backend shell-frontend help

# ==============================================================================
# CalorIA — Makefile
# ==============================================================================
# Uso:
#   make init    - Setup completo (primeira vez)
#   make dev     - Subir serviços em desenvolvimento
#   make down    - Parar tudo
#   make status  - Status dos serviços + health
#   make help    - Listar todos os comandos
# ==============================================================================

.PHONY: help init check-deps \
        dev dev-d infra down reset prod prod-down build build-no-cache \
        status logs logs-backend logs-frontend logs-worker \
        migrate migration migrate-history migrate-down psql seed seed-user \
        test test-backend test-backend-cov test-frontend test-unit test-integration \
        lint lint-backend lint-frontend lint-check fmt typecheck check \
        hooks shell-backend shell-frontend ps

# Cores
GREEN  := \033[0;32m
YELLOW := \033[1;33m
RED    := \033[0;31m
BLUE   := \033[0;34m
CYAN   := \033[0;36m
BOLD   := \033[1m
NC     := \033[0m

COMPOSE_DEV  := docker compose -f docker-compose.dev.yml
COMPOSE_PROD := docker compose

.DEFAULT_GOAL := help

# ==============================================================================
# HELP
# ==============================================================================

help:
	@echo ""
	@echo "$(BOLD)$(BLUE)CalorIA$(NC) — Comandos de Desenvolvimento"
	@echo ""
	@echo "$(BOLD)Primeira vez:$(NC)"
	@echo "  $(CYAN)make init$(NC)              Setup completo (env, build, start, migrate)"
	@echo ""
	@echo "$(BOLD)Dia-a-dia:$(NC)"
	@echo "  $(CYAN)make dev$(NC)               Subir serviços em modo dev (hot reload)"
	@echo "  $(CYAN)make dev-d$(NC)             Subir em background"
	@echo "  $(CYAN)make infra$(NC)             Subir só infra (postgres, redis, evolution_api)"
	@echo "  $(CYAN)make down$(NC)              Parar todos os serviços"
	@echo "  $(CYAN)make reset$(NC)             Parar e apagar volumes (reseta banco)"
	@echo "  $(CYAN)make status$(NC)            Status dos serviços + health check"
	@echo "  $(CYAN)make build$(NC)             Rebuildar imagens Docker"
	@echo ""
	@echo "$(BOLD)Banco de Dados:$(NC)"
	@echo "  $(CYAN)make migrate$(NC)           Aplicar migrações pendentes"
	@echo "  $(CYAN)make migration MSG=...$(NC) Criar nova migração"
	@echo "  $(CYAN)make migrate-history$(NC)   Histórico de migrações"
	@echo "  $(CYAN)make migrate-down$(NC)      Reverter última migração"
	@echo "  $(CYAN)make psql$(NC)              Abrir console psql"
	@echo "  $(CYAN)make seed$(NC)              Popular banco com dados de dev"
	@echo ""
	@echo "$(BOLD)Testes:$(NC)"
	@echo "  $(CYAN)make test$(NC)              Todos os testes (backend + frontend)"
	@echo "  $(CYAN)make test-backend$(NC)      Testes backend"
	@echo "  $(CYAN)make test-unit$(NC)         Testes unitários"
	@echo "  $(CYAN)make test-integration$(NC)  Testes de integração"
	@echo "  $(CYAN)make test-backend-cov$(NC)  Testes backend com cobertura HTML"
	@echo "  $(CYAN)make test-frontend$(NC)     Testes frontend"
	@echo ""
	@echo "$(BOLD)Qualidade de código:$(NC)"
	@echo "  $(CYAN)make lint$(NC)              Lint + fix (backend + frontend)"
	@echo "  $(CYAN)make lint-check$(NC)        Lint sem corrigir — igual ao CI"
	@echo "  $(CYAN)make lint-backend$(NC)      Ruff fix + check"
	@echo "  $(CYAN)make lint-frontend$(NC)     ESLint"
	@echo "  $(CYAN)make fmt$(NC)               Formatar código (ruff format)"
	@echo "  $(CYAN)make typecheck$(NC)         MyPy (backend) + tsc (frontend)"
	@echo "  $(CYAN)make check$(NC)             Lint + typecheck + testes — reproduz CI"
	@echo "  $(CYAN)make hooks$(NC)             Instalar pre-commit hooks"
	@echo ""
	@echo "$(BOLD)Logs e utilitários:$(NC)"
	@echo "  $(CYAN)make logs$(NC)              Logs de todos os serviços"
	@echo "  $(CYAN)make logs-backend$(NC)      Logs do backend"
	@echo "  $(CYAN)make logs-frontend$(NC)     Logs do frontend"
	@echo "  $(CYAN)make logs-worker$(NC)       Logs do Celery worker"
	@echo "  $(CYAN)make shell-backend$(NC)     Shell no container backend"
	@echo "  $(CYAN)make shell-frontend$(NC)    Shell no container frontend"
	@echo "  $(CYAN)make ps$(NC)                Status resumido dos containers"
	@echo ""

# ==============================================================================
# SETUP
# ==============================================================================

check-deps:
	@echo "$(BLUE)Verificando dependências...$(NC)"
	@command -v docker >/dev/null 2>&1 || { echo "$(RED)Docker não encontrado. Instale: https://docs.docker.com/get-docker/$(NC)"; exit 1; }
	@docker info >/dev/null 2>&1 || { echo "$(RED)Docker daemon não está rodando. Inicie o Docker.$(NC)"; exit 1; }
	@docker compose version >/dev/null 2>&1 || { echo "$(RED)Docker Compose v2 não encontrado. Atualize o Docker.$(NC)"; exit 1; }
	@echo "$(GREEN)Docker: OK$(NC)"
	@echo "$(GREEN)Docker Compose: OK$(NC)"

init: check-deps
	@echo ""
	@echo "$(BOLD)$(BLUE)CalorIA — Setup Inicial$(NC)"
	@echo "================================"
	@echo ""
	@echo "$(YELLOW)[1/4]$(NC) Configurando .env..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "  Criado .env a partir de .env.example"; \
		echo "  $(YELLOW)Edite o .env com suas credenciais antes de continuar.$(NC)"; \
	else \
		echo "  .env já existe, mantendo"; \
	fi
	@echo ""
	@echo "$(YELLOW)[2/4]$(NC) Construindo imagens Docker..."
	@$(COMPOSE_DEV) build --quiet
	@echo "  Build concluído"
	@echo ""
	@echo "$(YELLOW)[3/4]$(NC) Subindo serviços..."
	@$(COMPOSE_DEV) up -d
	@$(MAKE) --no-print-directory _wait-for-backend
	@echo ""
	@echo "$(YELLOW)[4/4]$(NC) Aplicando migrações..."
	@$(COMPOSE_DEV) exec backend alembic upgrade head
	@echo "  Migrações aplicadas"
	@echo ""
	@echo "$(BOLD)$(GREEN)Setup concluído!$(NC)"
	@echo ""
	@echo "  Dashboard:   http://localhost:3000"
	@echo "  API:         http://localhost:8000"
	@echo "  Swagger:     http://localhost:8000/docs"
	@echo "  Evol. API:   http://localhost:8080"
	@echo ""
	@echo "  Próximo passo: $(CYAN)make seed$(NC) para popular com dados de dev"
	@echo ""

# ==============================================================================
# AMBIENTE
# ==============================================================================

dev:
	@echo "$(BLUE)Subindo serviços em modo dev...$(NC)"
	@$(COMPOSE_DEV) up

dev-d:
	@echo "$(BLUE)Subindo serviços em background...$(NC)"
	@$(COMPOSE_DEV) up -d
	@$(MAKE) --no-print-directory _wait-for-backend
	@echo "$(GREEN)Serviços rodando!$(NC)  Backend: http://localhost:8000 | Frontend: http://localhost:3000"

infra:
	@echo "$(BLUE)Subindo infra (postgres, redis, evolution_api)...$(NC)"
	@$(COMPOSE_DEV) up postgres redis evolution_api

down:
	@echo "$(BLUE)Parando serviços...$(NC)"
	@$(COMPOSE_DEV) down
	@echo "$(GREEN)Serviços parados.$(NC)"

reset:
	@echo "$(RED)$(BOLD)ATENÇÃO: Isso vai apagar TODOS os dados do banco!$(NC)"
	@echo "Cancelando em 5 segundos... (Ctrl+C para abortar)"
	@sleep 5
	@$(COMPOSE_DEV) down -v
	@echo "$(GREEN)Volumes removidos.$(NC)"

prod:
	@echo "$(BLUE)Subindo produção local...$(NC)"
	@$(COMPOSE_PROD) up -d

prod-down:
	@$(COMPOSE_PROD) down

build:
	@echo "$(BLUE)Reconstruindo imagens...$(NC)"
	@$(COMPOSE_DEV) build
	@echo "$(GREEN)Build concluído.$(NC)"

build-no-cache:
	@echo "$(BLUE)Reconstruindo imagens sem cache...$(NC)"
	@$(COMPOSE_DEV) build --no-cache
	@echo "$(GREEN)Build concluído.$(NC)"

status:
	@echo "$(BOLD)$(BLUE)CalorIA — Status$(NC)"
	@echo ""
	@$(COMPOSE_DEV) ps -a
	@echo ""
	@printf "$(CYAN)Health check:$(NC) "
	@curl -sf http://localhost:8000/health 2>/dev/null && echo "" || echo "$(RED)Backend indisponível$(NC)"

ps:
	@$(COMPOSE_DEV) ps

# ==============================================================================
# BANCO DE DADOS
# ==============================================================================

migrate:
	@$(COMPOSE_DEV) exec backend alembic upgrade head

migration:
	@if [ -z "$(MSG)" ]; then echo "$(RED)Uso: make migration MSG=\"descricao da migracao\"$(NC)"; exit 1; fi
	@$(COMPOSE_DEV) exec backend alembic revision --autogenerate -m "$(MSG)"

migrate-history:
	@$(COMPOSE_DEV) exec backend alembic history --verbose

migrate-down:
	@$(COMPOSE_DEV) exec backend alembic downgrade -1

psql:
	@docker exec -it caloria_postgres psql -U caloria -d caloria_db

seed:
	@echo "$(BLUE)Populando banco com dados de dev...$(NC)"
	@$(COMPOSE_DEV) exec backend python scripts/seed_all.py
	@echo "$(GREEN)Seed concluído.$(NC)"

seed-user:
	@echo "$(BLUE)Criando usuário de dev...$(NC)"
	@$(COMPOSE_DEV) exec backend python scripts/seed_dev_user.py

# ==============================================================================
# TESTES
# ==============================================================================

test: test-backend test-frontend

test-backend:
	@echo "$(BLUE)Testes backend...$(NC)"
	@$(COMPOSE_DEV) exec backend pytest -v

test-unit:
	@echo "$(BLUE)Testes unitários...$(NC)"
	@$(COMPOSE_DEV) exec backend pytest tests/unit/ -v

test-integration:
	@echo "$(BLUE)Testes de integração...$(NC)"
	@$(COMPOSE_DEV) exec backend pytest tests/integration/ -v

test-backend-cov:
	@echo "$(BLUE)Testes backend com cobertura...$(NC)"
	@$(COMPOSE_DEV) exec backend pytest --cov=app --cov-report=html --cov-report=term-missing

test-frontend:
	@echo "$(BLUE)Testes frontend...$(NC)"
	@cd frontend && npm test

# ==============================================================================
# QUALIDADE DE CÓDIGO
# ==============================================================================

lint: lint-backend lint-frontend

lint-backend:
	@echo "$(BLUE)Lint backend (ruff)...$(NC)"
	@$(COMPOSE_DEV) exec backend ruff check --fix .
	@$(COMPOSE_DEV) exec backend ruff format .

lint-frontend:
	@echo "$(BLUE)Lint frontend (eslint)...$(NC)"
	@cd frontend && npm run lint

lint-check:
	@echo "$(BLUE)Lint check backend (sem corrigir)...$(NC)"
	@$(COMPOSE_DEV) exec backend ruff check .
	@$(COMPOSE_DEV) exec backend ruff format --check .
	@echo "$(BLUE)Lint check frontend (sem corrigir)...$(NC)"
	@cd frontend && npm run lint

fmt:
	@echo "$(BLUE)Formatando código...$(NC)"
	@$(COMPOSE_DEV) exec backend ruff format .
	@echo "$(GREEN)Formatação concluída.$(NC)"

typecheck:
	@echo "$(BLUE)Type check backend (mypy)...$(NC)"
	@$(COMPOSE_DEV) exec backend mypy app/
	@echo "$(BLUE)Type check frontend (tsc)...$(NC)"
	@cd frontend && npx tsc --noEmit

check: lint-check typecheck test
	@echo ""
	@echo "$(BOLD)$(GREEN)Tudo OK — igual ao CI.$(NC)"

hooks:
	@pre-commit install
	@echo "$(GREEN)Pre-commit hooks instalados.$(NC)"

# ==============================================================================
# LOGS E UTILITÁRIOS
# ==============================================================================

logs:
	@$(COMPOSE_DEV) logs -f

logs-backend:
	@$(COMPOSE_DEV) logs -f backend

logs-frontend:
	@$(COMPOSE_DEV) logs -f frontend

logs-worker:
	@$(COMPOSE_DEV) logs -f celery_worker

shell-backend:
	@$(COMPOSE_DEV) exec backend bash

shell-frontend:
	@$(COMPOSE_DEV) exec frontend sh

# ==============================================================================
# HELPERS INTERNOS
# ==============================================================================

_wait-for-backend:
	@printf "  Aguardando backend"
	@timeout=90; while [ $$timeout -gt 0 ]; do \
		curl -sf http://localhost:8000/health >/dev/null 2>&1 && break; \
		printf "."; sleep 2; timeout=$$((timeout - 2)); \
	done; echo ""; \
	if [ $$timeout -le 0 ]; then echo "$(RED)Backend não respondeu em 90s. Verifique: make logs-backend$(NC)"; exit 1; fi
	@echo "  $(GREEN)Backend: OK$(NC)"

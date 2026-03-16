#!/usr/bin/env bash
# =============================================================================
# CalorIA — Deploy / Atualização
# Execute toda vez que quiser atualizar o projeto no VPS.
#
# Uso:
#   bash scripts/deploy.sh
# =============================================================================
set -euo pipefail

COMPOSE="docker compose"

echo "========================================"
echo "  CalorIA — Deploy"
echo "========================================"

# --- Verificar .env ------------------------------------------------------------
if [ ! -f ".env" ]; then
    echo "[!] Arquivo .env não encontrado."
    echo "    Copie o exemplo: cp .env.production.example .env"
    echo "    Edite com suas credenciais: nano .env"
    exit 1
fi

# --- Verificar chave VAPID -----------------------------------------------------
VAPID_KEY_PATH="${VAPID_KEY_PATH:-./vapid_private.pem}"
if [ ! -f "$VAPID_KEY_PATH" ]; then
    echo "[!] Chave VAPID não encontrada em: $VAPID_KEY_PATH"
    echo "    Gere as chaves com o Passo 7 do docs/deploy.md"
    exit 1
fi

# --- Garantir que estamos na main ----------------------------------------------
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
if [ "$BRANCH" != "main" ]; then
    echo "[!] Atenção: você está na branch '$BRANCH', não na 'main'."
    echo "    No seu PC: git checkout main && git merge dev && git push origin main"
    echo "    No servidor: git pull origin main"
    echo "    Continuando mesmo assim..."
fi

# --- Pull das últimas alterações -----------------------------------------------
echo "[+] Atualizando código..."
git pull origin main 2>/dev/null || echo "    (sem remote configurado ou branch não existe ainda)"

# --- Pull das imagens base e rebuild -------------------------------------------
echo "[+] Reconstruindo imagens..."
$COMPOSE build --pull

# --- Subir infraestrutura primeiro (postgres, redis) ---------------------------
echo "[+] Subindo banco e cache..."
$COMPOSE up -d postgres redis
echo "[+] Aguardando postgres ficar saudável..."
until $COMPOSE exec -T postgres pg_isready -U caloria -d caloria_db &>/dev/null; do
    sleep 2
done

# --- Rodar migrações -----------------------------------------------------------
echo "[+] Rodando migrações Alembic..."
$COMPOSE run --rm backend alembic upgrade head

# --- Subir todos os serviços ---------------------------------------------------
echo "[+] Subindo todos os serviços..."
$COMPOSE up -d

# --- Mostrar status -------------------------------------------------------------
echo ""
$COMPOSE ps
echo ""
echo "========================================"
echo "  Deploy concluído!"
echo ""
# Lê APP_DOMAIN do .env se existir
APP_DOMAIN_VAL=$(grep -E '^APP_DOMAIN=' .env 2>/dev/null | cut -d= -f2 | tr -d '"' || echo "localhost")
echo "  Dashboard: https://${APP_DOMAIN_VAL}"
echo "  API docs:  https://${APP_DOMAIN_VAL}/docs"
echo "  Health:    https://${APP_DOMAIN_VAL}/health"
echo "  Logs:      docker compose logs -f"
echo "========================================"

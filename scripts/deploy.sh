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
    echo "    Copie o exemplo: cp .env.example .env"
    echo "    Edite com suas credenciais: nano .env"
    exit 1
fi

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
echo "  Dashboard: https://\${APP_DOMAIN:-localhost}"
echo "  API docs:  https://\${APP_DOMAIN:-localhost}/docs"
echo "  Logs:      docker compose logs -f"
echo "========================================"

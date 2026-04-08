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

# --- Carregar variáveis do .env para o shell atual ----------------------------
set -o allexport
# shellcheck source=.env
source .env
set +o allexport

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

# --- Detectar se é o primeiro deploy (tabela foods vazia) ---------------------
IS_FIRST_DEPLOY=false
if $COMPOSE exec -T postgres psql -U caloria -d caloria_db \
    -c "SELECT COUNT(*) FROM foods;" 2>/dev/null | grep -q "^ *0$"; then
    IS_FIRST_DEPLOY=true
fi

# --- Subir todos os serviços ---------------------------------------------------
echo "[+] Subindo todos os serviços..."
$COMPOSE up -d

# --- Verificação de saúde do backend ------------------------------------------
echo "[+] Aguardando backend responder..."
APP_DOMAIN_VAL="${APP_DOMAIN:-localhost}"
HEALTH_URL="https://${APP_DOMAIN_VAL}/health"
MAX_TRIES=15
TRIES=0
until curl -fsSL "$HEALTH_URL" 2>/dev/null | grep -q "ok" || [ "$TRIES" -ge "$MAX_TRIES" ]; do
    sleep 3
    TRIES=$((TRIES + 1))
done

if [ "$TRIES" -ge "$MAX_TRIES" ]; then
    echo "[!] Backend não respondeu após $((MAX_TRIES * 3))s — verifique os logs:"
    echo "    docker compose logs backend"
else
    echo "[+] Backend saudável."
fi

# --- Mostrar status -------------------------------------------------------------
echo ""
$COMPOSE ps
echo ""
echo "========================================"
echo "  Deploy concluído!"
echo ""
echo "  Dashboard: https://${APP_DOMAIN_VAL}"
echo "  API docs:  https://${APP_DOMAIN_VAL}/docs"
echo "  Health:    https://${APP_DOMAIN_VAL}/health"
echo "  Logs:      docker compose logs -f"

# --- Lembrete de seed (apenas no primeiro deploy) -----------------------------
if [ "$IS_FIRST_DEPLOY" = true ]; then
    echo ""
    echo "  ⚠️  ATENÇÃO — banco nutricional vazio!"
    echo "  Execute os seeds para a IA funcionar corretamente:"
    echo ""
    echo "  # TACO (~307 alimentos, ~5s):"
    echo "  docker exec caloria_backend python scripts/seed_taco.py"
    echo ""
    echo "  # Open Food Facts (~19.500 alimentos, ~5-10min):"
    echo "  docker exec caloria_backend python scripts/import_off.py"
fi

echo "========================================"

#!/usr/bin/env bash
# =============================================================================
# CalorIA — Setup inicial do servidor VPS (Ubuntu 22.04 / 24.04)
# Execute UMA VEZ no servidor recém-criado como root ou usuário com sudo.
#
# Uso:
#   curl -fsSL https://raw.githubusercontent.com/SEU_USER/caloria/main/scripts/setup-server.sh | bash
#   ou após clonar:
#   bash scripts/setup-server.sh
# =============================================================================
set -euo pipefail

echo "========================================"
echo "  CalorIA — Setup do Servidor"
echo "========================================"

# --- Atualizar sistema ----------------------------------------------------------
apt-get update -qq && apt-get upgrade -y -qq

# --- Instalar dependências básicas ----------------------------------------------
apt-get install -y -qq \
    curl \
    git \
    ufw \
    fail2ban

# --- Instalar Docker ------------------------------------------------------------
if ! command -v docker &> /dev/null; then
    echo "[+] Instalando Docker..."
    curl -fsSL https://get.docker.com | bash
    systemctl enable --now docker
    echo "[+] Docker instalado."
else
    echo "[=] Docker já instalado."
fi

# Adicionar usuário atual ao grupo docker (evita sudo a cada comando)
if [ "$EUID" -ne 0 ]; then
    usermod -aG docker "$USER"
    echo "[+] Usuário $USER adicionado ao grupo docker."
    echo "    Execute 'newgrp docker' ou reconecte o SSH para aplicar."
fi

# --- Configurar firewall (ufw) --------------------------------------------------
echo "[+] Configurando firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp    # HTTP (Caddy + redirect para HTTPS)
ufw allow 443/tcp   # HTTPS
ufw allow 443/udp   # HTTP/3 (QUIC)
ufw --force enable
echo "[+] Firewall configurado."

# --- Configurar fail2ban --------------------------------------------------------
systemctl enable --now fail2ban
echo "[+] fail2ban ativo."

# --- Configurar swap (2GB — segurança para picos de memória) -------------------
if [ ! -f /swapfile ]; then
    echo "[+] Criando swapfile de 2GB..."
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    # Reduz agressividade de uso do swap (0=nunca, 100=sempre; 10 é conservador)
    sysctl vm.swappiness=10
    echo 'vm.swappiness=10' >> /etc/sysctl.conf
    echo "[+] Swap configurado."
else
    echo "[=] Swapfile já existe."
fi

# --- Criar diretório do projeto -------------------------------------------------
mkdir -p /opt/caloria

echo ""
echo "========================================"
echo "  Setup concluído!"
echo ""
echo "  Próximos passos:"
echo "  1. cd /opt/caloria"
echo "  2. git clone <url-do-repo> ."
echo "  3. cp .env.production.example .env && nano .env"
echo "  4. bash scripts/deploy.sh"
echo "========================================"

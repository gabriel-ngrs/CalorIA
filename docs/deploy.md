# Deploy — CalorIA no VPS

Guia completo para hospedar o CalorIA em um servidor e acessar de qualquer lugar.

---

## Infraestrutura recomendada

| Componente | Opção | Custo |
|---|---|---|
| VPS | **Hetzner CX22** (2 vCPU, 4 GB RAM, 40 GB SSD) | ~€3,79/mês |
| Domínio | Registrar em Namecheap / Cloudflare (`.com`, `.com.br`) | ~€10/ano |
| HTTPS | **Caddy** (Let's Encrypt automático) | gratuito |

> **Alternativa gratuita de domínio:** use [DuckDNS](https://www.duckdns.org) para obter um subdomínio gratuito como `caloria.duckdns.org`.

---

## Passo 1 — Criar o VPS (Hetzner)

1. Acesse [hetzner.com/cloud](https://www.hetzner.com/cloud) e crie uma conta
2. Crie um novo servidor:
   - **Tipo:** CX22 (ou superior)
   - **Imagem:** Ubuntu 24.04
   - **Região:** Nuremberg (EU) ou a mais próxima
   - **SSH Key:** adicione sua chave pública para acesso sem senha
3. Anote o IP público do servidor

---

## Passo 2 — Configurar DNS

No painel do seu registrador de domínio, crie um registro **A**:

```
Tipo:  A
Nome:  caloria   (ou @, ou qualquer subdomínio)
Valor: <IP do VPS>
TTL:   300
```

Aguarde a propagação (geralmente 5–15 minutos). Teste com:
```bash
nslookup caloria.seudominio.com
```

---

## Passo 3 — Setup inicial do servidor

Conecte via SSH e execute o script de setup:

```bash
ssh root@<IP_DO_VPS>

# Baixar e executar o script de setup
curl -fsSL https://raw.githubusercontent.com/SEU_USER/caloria/main/scripts/setup-server.sh | bash
```

O script instala: Docker, configura firewall (80, 443, SSH) e fail2ban.

---

## Passo 4 — Clonar o repositório

```bash
cd /opt/caloria
git clone https://github.com/SEU_USER/caloria.git .
```

---

## Passo 5 — Configurar o `.env`

```bash
cp .env.example .env
nano .env
```

Preencha as variáveis obrigatórias:

```bash
# ===== OBRIGATÓRIO ALTERAR =====

APP_ENV=production
APP_DOMAIN=caloria.seudominio.com        # seu domínio real (sem https://)

# URLs derivadas do domínio
NEXT_PUBLIC_API_URL=https://caloria.seudominio.com
NEXTAUTH_URL=https://caloria.seudominio.com
NEXTAUTH_SECRET=                          # gere: openssl rand -hex 32

# Banco de dados
POSTGRES_PASSWORD=                        # senha forte, ex: openssl rand -hex 16
DATABASE_URL=postgresql+asyncpg://caloria:SENHA_ACIMA@postgres:5432/caloria_db

# Segurança JWT
SECRET_KEY=                               # gere: openssl rand -hex 32

# CORS (mesmo valor de NEXT_PUBLIC_API_URL)
BACKEND_CORS_ORIGINS=https://caloria.seudominio.com

# IA (Groq — gratuito em groq.com)
GROQ_API_KEY=gsk_...

# Telegram
TELEGRAM_BOT_TOKEN=                       # do BotFather no Telegram

# ===== OPCIONAIS (WhatsApp) =====
EVOLUTION_API_URL=http://evolution_api:8080
EVOLUTION_API_KEY=                        # gere: openssl rand -hex 16
EVOLUTION_INSTANCE_NAME=caloria

# ===== DEFAULTS (não precisa alterar) =====
POSTGRES_USER=caloria
POSTGRES_DB=caloria_db
REDIS_URL=redis://redis:6379/0
```

---

## Passo 6 — Deploy

```bash
bash scripts/deploy.sh
```

O script faz automaticamente:
1. Build das imagens Docker
2. Sobe banco e Redis
3. Roda as migrações Alembic
4. Sobe todos os serviços

---

## Passo 7 — Verificar

```bash
# Status dos serviços
docker compose ps

# Logs em tempo real
docker compose logs -f

# Testar a API
curl https://caloria.seudominio.com/health
```

Acesse o dashboard em: **https://caloria.seudominio.com**

---

## Passo 8 — Conectar o bot Telegram

1. Abra o Telegram e procure o bot que você criou no BotFather
2. Envie `/start`
3. No dashboard web, acesse **Conectar Bot** (`/conectar`)
4. Gere um token e envie `/conectar TOKEN` para o bot
5. Pronto — o bot está vinculado à sua conta

---

## Passo 9 — Conectar WhatsApp (opcional)

1. Com os serviços rodando, acesse: `https://caloria.seudominio.com:8080`
   > Nota: para expor a Evolution API pelo Caddy, adicione uma rota no `Caddyfile`.
   > Temporariamente, use um túnel SSH: `ssh -L 8080:localhost:8080 root@<IP>`
2. Crie uma instância chamada `caloria`
3. Escaneie o QR Code com o WhatsApp do celular
4. No dashboard, acesse **Conectar Bot** e repita o processo para WhatsApp

---

## Atualizações futuras

Para atualizar o projeto:

```bash
cd /opt/caloria
git pull
bash scripts/deploy.sh
```

---

## Comandos úteis no servidor

```bash
# Ver logs de um serviço específico
docker compose logs -f backend
docker compose logs -f telegram_bot

# Reiniciar um serviço
docker compose restart telegram_bot

# Acessar o banco
docker compose exec postgres psql -U caloria -d caloria_db

# Backup do banco
docker compose exec postgres pg_dump -U caloria caloria_db > backup_$(date +%Y%m%d).sql

# Parar tudo
docker compose down

# Parar e remover dados (CUIDADO — apaga o banco!)
docker compose down -v
```

---

## Monitoramento

```bash
# Ver uso de recursos
docker stats

# Ver espaço em disco
df -h
docker system df
```

---

## Renovação de certificado HTTPS

O Caddy renova os certificados Let's Encrypt automaticamente. Nenhuma ação necessária.

# Deploy — CalorIA no Oracle Cloud (Grátis)

Guia passo a passo para hospedar o CalorIA de graça para sempre.

**Tempo estimado:** 30–40 minutos (primeira vez)
**Custo:** R$ 0

---

## O que você vai ter no final

- Dashboard web acessível em qualquer browser: `https://caloria.duckdns.org`
- Bot Telegram funcionando 24/7 no celular e no PC
- Banco de dados PostgreSQL rodando no servidor
- HTTPS automático com certificado válido

---

## Pré-requisitos (o que você já precisa ter)

- [ ] Conta Google ou GitHub (para DuckDNS)
- [ ] Groq API Key — [console.groq.com](https://console.groq.com) (gratuito)
- [ ] Telegram Bot Token — fale com [@BotFather](https://t.me/BotFather) no Telegram
- [ ] Cartão de crédito/débito (Oracle pede para verificar identidade — **não cobra nada**)

---

## Parte 1 — Criar conta Oracle Cloud

1. Acesse [cloud.oracle.com](https://cloud.oracle.com) e clique em **Start for free**

2. Preencha os dados:
   - País: Brazil
   - Email e senha
   - Nome e sobrenome

3. Quando pedir o cartão: informe normalmente.
   Oracle faz uma cobrança de verificação de **$1 que é estornada** em seguida. Não há cobrança automática ao usar apenas recursos Free Tier.

4. Escolha a **Home Region** — escolha a mais próxima ao Brasil:
   - `Brazil East (São Paulo)` — melhor latência
   - `US East (Ashburn)` — alternativa se SP estiver sem capacidade

5. Conclua a verificação de telefone e aguarde o email de confirmação.

---

## Parte 2 — Criar o servidor (VM grátis)

1. No painel do Oracle Cloud, vá em:
   **☰ Menu → Compute → Instances → Create instance**

2. Configure assim:

   **Name:** `caloria`

   **Image and shape:**
   - Clique em **Change shape**
   - Em "Shape series", selecione **Ampere** (ícone de chip ARM)
   - Escolha `VM.Standard.A1.Flex`
   - **OCPUs:** 4 | **Memory:** 24 GB
   - Clique em Select shape

   **Image:**
   - Clique em Change image
   - Selecione **Canonical Ubuntu** → versão **22.04**

   **Networking:** deixe o padrão (cria VCN automaticamente)

   **SSH keys:**
   - Se você já tem um par de chaves SSH: cole a chave pública (conteúdo de `~/.ssh/id_rsa.pub`)
   - Se não tem: clique em **Generate a key pair** e baixe os dois arquivos

3. Clique em **Create**

4. Aguarde o status mudar para **Running** (1–3 minutos)

5. Anote o **Public IP** da instância (ex: `129.153.xx.xx`)

> ⚠️ Se aparecer **"Out of host capacity"**: tente mudar a região (vá em Manage Regions e habilite US East ou outro) ou tente de novo em 10–15 minutos. É problema de disponibilidade momentânea.

---

## Parte 3 — Abrir as portas no Oracle Cloud

Por padrão o Oracle bloqueia tudo exceto SSH. Você precisa abrir as portas 80 e 443.

1. No painel da instância criada, role até **Primary VNIC** e clique no nome da **Subnet**

2. Na página da Subnet, clique na **Security List** (geralmente "Default Security List")

3. Clique em **Add Ingress Rules** e adicione duas regras:

   **Regra 1 — HTTP:**
   - Source CIDR: `0.0.0.0/0`
   - IP Protocol: TCP
   - Destination Port Range: `80`

   **Regra 2 — HTTPS:**
   - Source CIDR: `0.0.0.0/0`
   - IP Protocol: TCP
   - Destination Port Range: `443`

4. Clique em **Add Ingress Rules** para salvar

---

## Parte 4 — Criar seu domínio gratuito (DuckDNS)

Você precisa de um domínio para o HTTPS funcionar.

1. Acesse [duckdns.org](https://www.duckdns.org) e entre com sua conta Google ou GitHub

2. Em **"sub domain"**, escolha um nome (ex: `caloria-gabriel`) e clique em **add domain**

3. No campo **current ip**, cole o **Public IP** do seu servidor Oracle e clique em **update ip**

4. Seu domínio é: `caloria-gabriel.duckdns.org` (substitua pelo nome que você escolheu)

5. Aguarde 2–5 minutos para propagar. Teste:
   ```
   ping caloria-gabriel.duckdns.org
   ```
   Deve responder com o IP do seu servidor.

---

## Parte 5 — Conectar ao servidor via SSH

No seu terminal (WSL, PowerShell, ou terminal do Mac/Linux):

```bash
ssh ubuntu@<IP_DO_SERVIDOR>
```

Se gerou chaves pelo Oracle, use:
```bash
ssh -i ~/Downloads/ssh-key-*.key ubuntu@<IP_DO_SERVIDOR>
```

Na primeira conexão vai perguntar "Are you sure?" — digite `yes`.

---

## Parte 6 — Setup inicial do servidor

Cole esses comandos no terminal do servidor:

```bash
# Liberar portas no firewall do Ubuntu (passo extra obrigatório no Oracle)
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo apt-get install -y iptables-persistent
sudo netfilter-persistent save

# Instalar Docker
curl -fsSL https://get.docker.com | bash
sudo usermod -aG docker ubuntu
newgrp docker

# Verificar que Docker está funcionando
docker run hello-world
```

---

## Parte 7 — Clonar o projeto

```bash
# Criar pasta do projeto
sudo mkdir -p /opt/caloria
sudo chown ubuntu:ubuntu /opt/caloria
cd /opt/caloria

# Clonar o repositório
git clone https://github.com/gabriel-ngrs/CalorIA.git .
```

---

## Parte 8 — Configurar as variáveis de ambiente

```bash
cp .env.example .env
nano .env
```

Edite os seguintes campos (use as setas para navegar, `Ctrl+O` para salvar, `Ctrl+X` para sair):

```bash
# Ambiente
APP_ENV=production

# Domínio (sem https://)
APP_DOMAIN=caloria-gabriel.duckdns.org

# URLs do frontend
NEXT_PUBLIC_API_URL=https://caloria-gabriel.duckdns.org
NEXTAUTH_URL=https://caloria-gabriel.duckdns.org

# Secrets — gere com os comandos abaixo
SECRET_KEY=COLE_AQUI
NEXTAUTH_SECRET=COLE_AQUI_OUTRO

# Banco de dados
POSTGRES_PASSWORD=ESCOLHA_UMA_SENHA_FORTE
DATABASE_URL=postgresql+asyncpg://caloria:MESMA_SENHA_ACIMA@postgres:5432/caloria_db

# CORS
BACKEND_CORS_ORIGINS=https://caloria-gabriel.duckdns.org

# IA (Groq)
GROQ_API_KEY=gsk_SUACHAVEGROQ

# Telegram
TELEGRAM_BOT_TOKEN=SEUBOTTOKEN
```

Para gerar os secrets, abra outro terminal e rode:
```bash
# Dois comandos — um para SECRET_KEY, outro para NEXTAUTH_SECRET
openssl rand -hex 32
openssl rand -hex 32
```

Cole cada resultado no campo correspondente do `.env`.

---

## Parte 9 — Fazer o deploy

```bash
cd /opt/caloria
bash scripts/deploy.sh
```

Isso vai:
1. Baixar todas as imagens Docker (~5 min na primeira vez)
2. Compilar o frontend com sua URL configurada
3. Criar o banco de dados e rodar as migrações
4. Subir todos os serviços

Aguarde terminar. No final vai aparecer a lista de serviços rodando.

---

## Parte 10 — Verificar

```bash
# Ver se todos os serviços subiram
docker compose ps

# Testar a API
curl https://caloria-gabriel.duckdns.org/health
# Deve retornar: {"status":"ok","version":"0.1.0"}
```

Acesse no browser: **https://caloria-gabriel.duckdns.org**

Você vai ver a tela de login do CalorIA.

---

## Parte 11 — Criar sua conta

1. Na tela de login, clique em **Cadastrar**
2. Crie sua conta com email e senha
3. Faça login — você já está no dashboard!

---

## Parte 12 — Conectar o bot Telegram

1. Abra o Telegram e procure o seu bot pelo nome
2. Envie `/start`
3. No dashboard web, vá em **Conectar Bot** (menu lateral)
4. Clique em **Gerar token** (válido por 10 minutos)
5. Copie o token e envie no Telegram: `/conectar SEU_TOKEN`
6. O bot vai confirmar a vinculação

Agora você pode registrar refeições pelo Telegram em qualquer dispositivo!

---

## Comandos úteis (no servidor)

```bash
# Ver logs em tempo real
docker compose logs -f

# Ver logs de um serviço específico
docker compose logs -f telegram_bot
docker compose logs -f backend

# Reiniciar um serviço
docker compose restart telegram_bot

# Ver status
docker compose ps

# Atualizar o projeto (quando houver novas versões)
cd /opt/caloria
git pull
bash scripts/deploy.sh
```

---

## Se algo der errado

**Bot Telegram não responde:**
```bash
docker compose logs telegram_bot
docker compose restart telegram_bot
```

**Dashboard não abre:**
```bash
docker compose logs frontend
docker compose logs caddy
```

**Erro de banco de dados:**
```bash
docker compose logs backend
docker compose exec backend alembic upgrade head
```

**Reiniciar tudo:**
```bash
docker compose down && docker compose up -d
```

# Deploy — CalorIA no Hetzner

Guia completo para hospedar o CalorIA em produção usando Hetzner Cloud + Docker Compose + Caddy (HTTPS automático).

**Custo:** ~€3.92/mês (≈ R$22)
**Tempo estimado:** 30–45 minutos na primeira vez

---

## O que você terá no final

- Dashboard web em `https://seudominio.com.br`
- HTTPS automático com Let's Encrypt via Caddy
- Notificações push nativas no celular/desktop
- Banco de dados PostgreSQL com backups manuais
- Todos os serviços com restart automático

---

## Pré-requisitos

- [ ] Conta no [Hetzner Cloud](https://console.hetzner.cloud) (requer cartão de crédito)
- [ ] Gemini API Key — [aistudio.google.com](https://aistudio.google.com/app/apikey) (gratuito)
- [ ] Domínio (opcional, mas necessário para HTTPS) — pode ser subdomínio gratuito via DuckDNS
- [ ] Chave SSH no seu computador

---

## Parte 1 — Criar a chave SSH (se não tiver)

No seu terminal (WSL ou Linux):

```bash
# Gera a chave
ssh-keygen -t ed25519 -C "caloria-deploy"

# Mostra a chave pública — copie o resultado para usar no Hetzner
cat ~/.ssh/id_ed25519.pub
```

---

## Parte 2 — Criar o servidor no Hetzner

1. Acesse [console.hetzner.cloud](https://console.hetzner.cloud) e crie uma conta
2. Crie um novo projeto chamado `caloria`
3. Clique em **Add Server** e configure:

   | Campo | Valor |
   |---|---|
   | Location | Nuremberg ou Helsinki |
   | Image | Ubuntu 24.04 |
   | Type | **CX22** — 2 vCPU, 4GB RAM, 40GB SSD |
   | SSH Keys | Cole o conteúdo do `id_ed25519.pub` |

4. Clique em **Create & Buy** — em ~30 segundos o servidor estará no ar
5. Anote o **IP público** exibido no painel

---

## Parte 3 — Apontar o domínio

### Opção A — Domínio próprio (Registro.br, Cloudflare, etc.)

No painel do seu registrador, crie um registro DNS:

```
Tipo: A
Nome: caloria  (ou @ para raiz)
Valor: IP_DO_SERVIDOR
TTL: 300
```

### Opção B — Subdomínio gratuito via DuckDNS

1. Acesse [duckdns.org](https://www.duckdns.org) e entre com Google/GitHub
2. Escolha um nome (ex: `caloria-gabriel`) e clique em **add domain**
3. Cole o IP do servidor no campo **current ip** e clique em **update ip**
4. Seu domínio ficará: `caloria-gabriel.duckdns.org`

> Aguarde 2–5 minutos para o DNS propagar antes de prosseguir.

---

## Parte 4 — Conectar ao servidor

```bash
ssh root@IP_DO_SERVIDOR
```

Na primeira conexão vai perguntar "Are you sure?" — digite `yes`.

---

## Parte 5 — Instalar Docker

```bash
# Atualiza o sistema
apt update && apt upgrade -y

# Instala Docker (script oficial)
curl -fsSL https://get.docker.com | sh

# Verifica a instalação
docker --version && docker compose version
```

---

## Parte 6 — Baixar o código

```bash
# Cria a pasta do projeto
mkdir -p /opt/caloria && cd /opt/caloria

# Clona a branch main (produção)
git clone -b main https://github.com/SEU_USUARIO/CalorIA.git .
```

> Substitua pela URL do seu repositório. Se o repo for privado, use um Personal Access Token do GitHub.

---

## Parte 7 — Gerar as chaves VAPID (Web Push)

```bash
cd /opt/caloria

# Instala pywebpush temporariamente para gerar as chaves
pip3 install pywebpush --break-system-packages 2>/dev/null || pip3 install pywebpush

# Gera e salva as chaves
python3 -c "
from py_vapid import Vapid
import base64
v = Vapid()
v.generate_keys()
priv_pem = v.private_pem()
pub_bytes = v._private_key.public_key().public_bytes(
    __import__('cryptography.hazmat.primitives.serialization', fromlist=['Encoding','PublicFormat']).Encoding.X962,
    __import__('cryptography.hazmat.primitives.serialization', fromlist=['Encoding','PublicFormat']).PublicFormat.UncompressedPoint
)
pub_b64 = base64.urlsafe_b64encode(pub_bytes).rstrip(b'=').decode()
open('/opt/caloria/vapid_private.pem', 'wb').write(priv_pem)
print('VAPID_PUBLIC_KEY=' + pub_b64)
print('Chave privada salva em /opt/caloria/vapid_private.pem')
"

# Protege o arquivo da chave privada
chmod 600 /opt/caloria/vapid_private.pem
```

**Anote a linha `VAPID_PUBLIC_KEY=...` que aparecer** — você vai usar no próximo passo.

---

## Parte 8 — Configurar o `.env`

```bash
cd /opt/caloria
cp .env.production.example .env
nano .env
```

Preencha todos os campos. Para gerar os secrets:

```bash
# Rode duas vezes — use cada resultado em um campo diferente
openssl rand -hex 32
openssl rand -hex 32
```

Exemplo de `.env` completo:

```env
# Banco de dados
POSTGRES_USER=caloria
POSTGRES_PASSWORD=SenhaForteAqui123!
POSTGRES_DB=caloria_db
DATABASE_URL=postgresql+asyncpg://caloria:SenhaForteAqui123!@postgres:5432/caloria_db

# Redis
REDIS_URL=redis://redis:6379/0

# Aplicação
APP_ENV=production
SECRET_KEY=abc123...resultado_do_openssl
APP_DOMAIN=caloria-gabriel.duckdns.org

# Next.js
NEXTAUTH_URL=https://caloria-gabriel.duckdns.org
NEXTAUTH_SECRET=xyz789...outro_resultado_do_openssl
NEXT_PUBLIC_API_URL=https://caloria-gabriel.duckdns.org

# Gemini
GEMINI_API_KEY=AIza...sua_chave_aqui

# Web Push VAPID
VAPID_PUBLIC_KEY=BDCh...copiado_do_passo_7
VAPID_KEY_PATH=/opt/caloria/vapid_private.pem
VAPID_CLAIMS_EMAIL=seu@email.com
```

> **Sem domínio ainda?** Use o IP: `APP_DOMAIN=IP_DO_SERVIDOR`, `NEXTAUTH_URL=http://IP_DO_SERVIDOR`, `NEXT_PUBLIC_API_URL=http://IP_DO_SERVIDOR`. O HTTPS só funciona com domínio.

---

## Parte 9 — Subir os containers

```bash
cd /opt/caloria

# Build e sobe todos os serviços
docker compose up -d --build

# Acompanha os logs (Ctrl+C para sair sem parar os containers)
docker compose logs -f
```

O build do frontend leva ~3–5 minutos na primeira vez.

---

## Parte 10 — Rodar as migrações e seed do banco

```bash
# Aguarda o backend inicializar (~15s) e roda as migrations
sleep 15 && docker exec caloria_backend alembic upgrade head
```

### Seed do banco nutricional (obrigatório — só na primeira vez)

Após as migrações, a tabela `foods` existe mas está vazia. Sem o seed, a IA não consegue buscar macros no banco e cai sempre no fallback de estimativa.

```bash
# 1. Seed TACO — ~307 alimentos, hardcoded, rápido (~5s)
docker exec caloria_backend python scripts/seed_taco.py

# 2. Importar Open Food Facts — ~19.500 produtos brasileiros (opcional, recomendado)
#    Faz download da API do OFF — leva ~5-10 minutos dependendo da conexão
docker exec caloria_backend python scripts/import_off.py
```

> Só é necessário rodar uma vez. Os dados ficam no volume `postgres_data` e persistem entre reinicializações e deploys.

---

## Parte 11 — Verificar

```bash
# Status de todos os containers (todos devem estar "Up")
docker compose ps

# Testa o backend
curl https://caloria-gabriel.duckdns.org/health
# Resposta esperada: {"status":"ok","version":"0.1.0"}
```

Acesse **https://seudominio.com** no browser — a tela de login do CalorIA vai aparecer.

---

## Parte 12 — Criar sua conta

1. Na tela de login, clique em **Cadastrar**
2. Crie sua conta com email e senha
3. Faça login — você está no dashboard
4. Quando o browser perguntar sobre notificações, clique em **Permitir**

---

## Comandos do dia a dia

```bash
# Ver status dos containers
docker compose ps

# Logs em tempo real
docker compose logs -f
docker compose logs -f backend     # só o backend
docker compose logs -f celery_worker

# Reiniciar um serviço
docker compose restart backend

# Parar tudo
docker compose down

# Reiniciar tudo
docker compose down && docker compose up -d
```

---

## Atualizar o app (após novos commits)

```bash
cd /opt/caloria
git pull origin main
docker compose up -d --build
docker exec caloria_backend alembic upgrade head
```

---

## Backup manual do banco

```bash
# Cria backup com data no nome
docker exec caloria_postgres pg_dump -U caloria caloria_db \
  > /opt/caloria/backup_$(date +%Y%m%d_%H%M).sql

# Listar backups existentes
ls -lh /opt/caloria/backup_*.sql
```

> Dica: configure um cron para backup automático diário:
> ```bash
> crontab -e
> # Adicione a linha:
> 0 3 * * * docker exec caloria_postgres pg_dump -U caloria caloria_db > /opt/caloria/backup_$(date +\%Y\%m\%d).sql
> ```

---

## Fluxo de desenvolvimento → produção

Com CI/CD ativo, o deploy acontece **automaticamente** ao mergear na `main`.

```
dev  →  PR para main  →  CI passa  →  merge  →  CD faz deploy automático
```

Você não precisa fazer mais nada no servidor. O GitHub Actions cuida do:
1. `git pull origin main`
2. `docker compose up -d --build`
3. `docker exec caloria_backend alembic upgrade head`

Ver [`docs/git-workflow.md`](git-workflow.md) para a estratégia completa de branches.

### Deploy manual (emergência ou primeiro setup)

```bash
cd /opt/caloria
git pull origin main
docker compose up -d --build
docker exec caloria_backend alembic upgrade head
```

---

## Troubleshooting

**App não abre no browser:**
```bash
docker compose logs caddy
docker compose logs frontend
```
Verifique se o DNS propagou: `ping seudominio.com` deve retornar o IP do servidor.

**Erro 502 Bad Gateway:**
```bash
docker compose logs backend
# Se o backend travou, reinicia:
docker compose restart backend
```

**Banco de dados com erro:**
```bash
docker compose logs backend | grep -i "error\|alembic"
docker exec caloria_backend alembic upgrade head
```

**Notificações push não chegam:**
- Verifique se o usuário permitiu notificações no browser
- Confirme que `VAPID_PUBLIC_KEY` no `.env` bate com o que foi gerado no Passo 7
- Verifique os logs do celery: `docker compose logs celery_worker`

**Reiniciar tudo do zero (mantém os dados):**
```bash
docker compose down
docker compose up -d --build
docker exec caloria_backend alembic upgrade head
```

**Apagar tudo e recomeçar (CUIDADO — perde os dados):**
```bash
docker compose down -v   # -v remove os volumes com os dados
docker compose up -d --build
docker exec caloria_backend alembic upgrade head
```

# Checklist de Primeiro Deploy

Estado em 2026-03-25. Tudo pronto no código — só falta infraestrutura.

**Testes:** 96/96 passando. Lint e typecheck limpos. Branch `dev` com 4 commits não pusheados.

---

## Passo 1 — Push e PR

```bash
git push origin dev
```

Abrir PR `dev → main` no GitHub. O CI vai rodar lint + testes + build. Após CI verde, fazer merge. O CD dispara automaticamente.

---

## Passo 2 — Criar servidor Hetzner

- Acessar https://console.hetzner.cloud
- Criar servidor **CX22** (2 vCPU, 4GB RAM) — Ubuntu 24.04 — ~€3.92/mês
- Adicionar chave SSH pública (`~/.ssh/id_ed25519.pub`)
- Anotar o **IP público**

---

## Passo 3 — DNS

Opção gratuita: DuckDNS (https://www.duckdns.org)
- Criar subdomínio (ex: `caloria-gabriel.duckdns.org`)
- Apontar para o IP do servidor
- Aguardar 2–5 min para propagar

---

## Passo 4 — GitHub Secrets

Settings → Environments → criar environment `production` → adicionar:

| Secret | Valor |
|---|---|
| `SERVER_HOST` | IP do servidor |
| `SERVER_USER` | `root` |
| `SERVER_SSH_KEY` | Conteúdo de `~/.ssh/id_ed25519` (chave **privada**) |

---

## Passo 5 — Setup inicial no servidor

```bash
ssh root@IP_DO_SERVIDOR

# Instalar Docker
apt update && apt upgrade -y
curl -fsSL https://get.docker.com | sh

# Clonar repo
mkdir -p /opt/caloria && cd /opt/caloria
git clone -b main https://github.com/SEU_USUARIO/CalorIA.git .

# Gerar chaves VAPID
pip3 install pywebpush --break-system-packages 2>/dev/null || pip3 install pywebpush
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
"
chmod 600 /opt/caloria/vapid_private.pem
# ANOTAR a linha VAPID_PUBLIC_KEY=... que apareceu acima

# Criar .env
cp .env.production.example .env
nano .env
```

---

## Passo 6 — Preencher o .env

Gerar os secrets antes:
```bash
openssl rand -hex 32  # rodar 2x — um para SECRET_KEY, outro para NEXTAUTH_SECRET
```

Conteúdo do `.env`:

```env
POSTGRES_USER=caloria
POSTGRES_PASSWORD=<senha forte>
POSTGRES_DB=caloria_db
DATABASE_URL=postgresql+asyncpg://caloria:<senha>@postgres:5432/caloria_db

REDIS_URL=redis://redis:6379/0

APP_ENV=production
SECRET_KEY=<resultado do openssl>
APP_DOMAIN=caloria-gabriel.duckdns.org

NEXTAUTH_URL=https://caloria-gabriel.duckdns.org
NEXTAUTH_SECRET=<resultado do openssl>
NEXT_PUBLIC_API_URL=https://caloria-gabriel.duckdns.org

GEMINI_API_KEY=<chave de aistudio.google.com>

VAPID_PUBLIC_KEY=<copiado do passo 5>
VAPID_KEY_PATH=/opt/caloria/vapid_private.pem
VAPID_CLAIMS_EMAIL=<seu email>
```

---

## Passo 7 — Subir containers e migrar

```bash
cd /opt/caloria
docker compose up -d --build
# aguardar ~3-5 min (build do frontend)

sleep 15 && docker exec caloria_backend alembic upgrade head

# Seed do banco nutricional (obrigatório — só na primeira vez)
docker exec caloria_backend python scripts/seed_taco.py
docker exec caloria_backend python scripts/import_off.py  # opcional, ~5-10 min
```

---

## Passo 8 — Verificar

```bash
docker compose ps  # todos devem estar "Up"
curl https://caloria-gabriel.duckdns.org/health
# Esperado: {"status":"ok","version":"0.1.0"}
```

Acesse o domínio no browser — tela de login deve aparecer.

---

## Após o primeiro deploy

Todo merge na `main` dispara deploy automático via CD (GitHub Actions → SSH → git pull + docker compose up + alembic upgrade head). Ver `docs/deploy.md` para comandos do dia a dia e troubleshooting.

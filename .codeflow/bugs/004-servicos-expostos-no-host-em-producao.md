---
versão: 1.0
id: "004"
slug: 004-servicos-expostos-no-host-em-producao
título: "Compose de produção publica backend e frontend no host, contornando o Caddy"
severidade: alto
área: infra/deploy
status: aberto
criado: 2026-08-15
atualizado: 2026-08-15
reportado_por: auditoria do compose durante a escolha de VPS (2026-08-11)
---

# BUG 004 — Backend e frontend expostos direto no host

O `docker-compose.yml` — a stack de produção da topologia oficial (ADR-009) —
mapeia backend e frontend para **todas as interfaces do host**. Enquanto a stack
roda localmente isso é inofensivo. **No instante em que ela subir numa VPS com IP
público, a API fica acessível sem TLS e sem passar pelo proxy.**

## Sintoma

```yaml
backend:
  ports:
    - "8000:8000"     # docker-compose.yml:69-70

frontend:
  ports:
    - "3000:3000"     # docker-compose.yml:101-102
```

Sem prefixo de endereço, o Docker publica em `0.0.0.0`. Consequências numa VPS:

- `http://<IP>:8000/api/v1/...` responde **em HTTP puro**, fora do Caddy — o login
  (`POST /api/v1/auth/login`) trafega senha em texto claro;
- `http://<IP>:8000/docs` e `/redoc` ficam abertos, publicando a superfície inteira
  da API;
- `http://<IP>:3000` serve o frontend sem TLS, com o cookie de sessão do next-auth
  igualmente exposto;
- o `Caddyfile`, que é quem termina o TLS e roteia `/api`, `/docs` e `/redoc`, passa
  a ser **contornável** — deixa de ser o único ponto de entrada.

O contraste está no mesmo arquivo: `postgres` e `redis` **não** declaram `ports:` e
só existem na rede interna `caloria_net`. Backend e frontend deveriam seguir a mesma
regra, porque o Caddy os alcança por nome de serviço (`reverse_proxy backend:8000`),
não pelo host.

## Onde está o defeito

| Arquivo | Linhas | O quê |
|---|---|---|
| `docker-compose.yml` | 69-70 | `ports: ["8000:8000"]` no serviço `backend` |
| `docker-compose.yml` | 101-102 | `ports: ["3000:3000"]` no serviço `frontend` |

## Correção proposta

Vincular a publicação ao loopback, preservando o acesso direto em
desenvolvimento sem expor nada na internet:

```yaml
ports:
  - "127.0.0.1:8000:8000"
  - "127.0.0.1:3000:3000"
```

Remover as duas linhas por completo também resolveria — o Caddy não depende delas —
mas quebraria o acesso direto a `localhost:8000` que a topologia de host único
(ADR-009) usa para rodar o projeto inteiro na máquina do desenvolvedor.

**Defesa em profundidade, no host:** firewall liberando apenas 22, 80 e 443. O
firewall sozinho não basta como correção — uma regra removida por engano
reexporia os serviços, e o `docker` publica portas manipulando `iptables` por conta
própria, o que já surpreendeu muita gente que confiava só no `ufw`.

## Por que precisa ser fechado antes do deploy

A **Fase E.4** da spec 002 é quem publica a aplicação. Subir a stack como está seria
expor, no primeiro minuto de vida do servidor, exatamente a superfície que os
Tracks A e B desta spec passaram semanas fechando. É pré-requisito do deploy, não
melhoria posterior.

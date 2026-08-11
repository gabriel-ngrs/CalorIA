# Onde hospedar o CalorIA — comparativo de opções

**Status:** documento de decisão, não guia de execução. O guia é [`docs/deploy.md`](deploy.md).
**Contexto:** a Fase E.4 da spec 002 (deploy + CD automático) está parada por falta de host.
O ADR-009 fixou a topologia (host único, `docker-compose.yml` + `Caddyfile`) e deixou o
*onde* em aberto. Este documento levanta o *onde*, com preços verificados em 2026-08-10.

---

## 1. O que a stack precisa (medido, não estimado)

Consumo em repouso dos containers rodando nesta máquina em 2026-08-10 (`docker stats`):

| serviço | RSS medido | nota |
|---|---:|---|
| `postgres` | 152 MB | o compose pede `shared_buffers=256MB` e `effective_cache_size=512MB` — quer folga de page cache além do RSS |
| `celery_worker` | 166 MB | |
| `backend` (uvicorn) | 126 MB | |
| `celery_beat` | 69 MB | |
| `redis` | 11 MB | |
| `caddy` | — | não sobe no compose dev; imagem de 88 MB, RSS típico ~20 MB |
| `frontend` | **2,2 GB** | **não representa produção** — é o container dev (`next dev`, hot reload) |

**Total em produção: ~1 GB em repouso**, somando os cinco medidos, o Caddy e uma estimativa
de 150–250 MB para o frontend de produção. O `next.config.js` usa `output: "standalone"` e o
Dockerfile de produção roda `node server.js`, que é uma ordem de grandeza mais leve que o
`next dev` medido acima. **Este é o único número deste documento que não foi medido** — vale
confirmá-lo antes de escolher uma máquina de 2 GB.

**Disco:** banco com 40 MB (42.168 linhas em `foods`) + imagens (`caloria-backend` 904 MB ×3
tags, `caloria-frontend`, `postgres:16-alpine` 419 MB, `redis` 57 MB, `caddy` 88 MB). **20 GB
sobra; 40 GB é confortável.**

### O gargalo não é rodar — é buildar

O `cd.yml` faz `docker compose up -d --build` **no servidor**. O `npm ci` + `next build` do
frontend pede na casa de 2 GB de RAM sozinho. Numa máquina de 2 GB o build é morto pelo OOM
killer; numa de 1 vCPU ele leva vários minutos a cada deploy.

Duas saídas, e a segunda é melhor em qualquer provedor:

- **(a)** pegar 4 GB de RAM e continuar buildando no servidor;
- **(b)** **buildar no GitHub Actions e publicar no GHCR**; o servidor só faz
  `docker compose pull && docker compose up -d`. Deixa uma máquina pequena viável, corta o
  tempo de deploy, e é exatamente o ponto onde o `sleep 10` do `cd.yml:38` vira espera por
  healthcheck (passo 3 da E.4).

---

## 2. As opções

### 2.1 Hetzner CX22 — €5,49/mês + IPv4 (~R$ 35–38)

2 vCPU x86, 4 GB RAM, 40 GB NVMe, 20 TB de tráfego.

Tecnicamente encaixa bem: os 4 GB comportam build no servidor, o `docs/deploy.md` já descreve
a Hetzner passo a passo, o `docker-compose.yml` sobe sem alteração (ADR-009) e o `cd.yml` já
é SSH + compose.

> **Preço corrigido em 2026-08-11.** A primeira versão deste documento citava ~€3,79–4,59
> (~R$ 24), número vindo de comparadores de terceiros. A documentação da própria Hetzner
> desmente: houve **dois reajustes em 2026** e, desde 15/06/2026, o CX22 está em **€5,49**
> (era €3,99) e o CAX11 em **€5,99** (era €4,49) — valores sem IPv4 (~€0,50/mês) e sem IVA.
> A linha **CPX (AMD)** levou um reajuste muito pior no mesmo dia: o CPX22 foi de €7,99 para
> **€19,49** (+144%). Ao comparar na página da Hetzner, confira que está na aba
> **Cost-Optimized (CX)**, não na **Regular Performance (CPX)**.

**Contra:** sem região no Brasil (Alemanha, Finlândia, EUA, Singapura) — ~200 ms da Europa,
~120 ms de Ashburn contra 10–40 ms de São Paulo. E com o reajuste o preço deixou de ser
vantagem: empata com a opção brasileira, que ainda inclui backup.

> **Variante CAX11** (ARM Ampere, 2 vCPU / 4 GB, €5,99): mais eficiente, mas exige imagens
> `linux/arm64`. Todas as bases usadas têm arm64 (`postgres:16-alpine`, `redis:7-alpine`,
> `caddy:2-alpine`, `node:20-alpine`, Python), então provavelmente roda — mas é rebuild e
> teste, agora em troca de nada, já que ficou mais cara que o CX22. Só Alemanha e Finlândia.

### 2.2 Oracle Cloud Always Free — R$ 0 · mais barata, menos confiável

ARM Ampere A1. **Atenção ao que mudou:** em 15/06/2026 a Oracle cortou o Always Free pela
metade sem anúncio público — de 4 OCPU/24 GB para **2 OCPU/12 GB**. Ainda é folgado para
esta stack (que precisa de ~1 GB).

**Contra, e pesa para uma vitrine:** capacidade ARM frequentemente indisponível
("Out of host capacity"), contas gratuitas reclamadas por inatividade, sem SLA, e o corte
silencioso de junho é precedente de que os termos mudam sem aviso. É a opção certa se o
critério for custo zero acima de tudo; é a errada se o servidor precisa estar no ar no dia
em que alguém abrir o link do currículo.

### 2.3 VPS em São Paulo (Hostinger KVM) — R$ 35–43/mês · latência BR

Datacenter em São Paulo, suporte em português, **backup semanal incluído** — que tapa o
buraco da seção 4 (hoje o backup é `pg_dump` manual, sem cron nem offsite). Latência de
10–40 ms contra 150–250 ms de EUA/Europa.

Confrontando os planos com o consumo medido na seção 1 (~1 GB em repouso):

| plano | vCPU / RAM / disco | promo | renovação | veredito |
|---|---|---:|---:|---|
| **KVM 1** | 1 / 4 GB / 50 GB | R$ 34,99 | R$ 59,99 | **suficiente** — 4× a RAM necessária |
| KVM 2 | 2 / 8 GB / 100 GB | R$ 42,99 | R$ 77,99 | conforto: 2º núcleo para o build |
| KVM 4 | 4 / 16 GB / 200 GB | R$ 59,99 | R$ 149,99 | desperdício |
| KVM 8 | 8 / 32 GB / 400 GB | R$ 119,99 | R$ 259,99 | desperdício |

O único ponto de aperto do KVM 1 é o **deploy**: com o `cd.yml` buildando no servidor, um
único núcleo leva minutos no `next build` e a RAM fica justa (a stack antiga segue de pé
enquanto a nova compila). A estratégia (b) da seção 1 — buildar no CI e publicar no GHCR —
elimina isso e deixa o KVM 1 como escolha certa.

**Contra:** a tarifa promocional exige **compromisso de 2 anos pago adiantado** (KVM 1:
R$ 839,76 à vista) e o desconto não vale na renovação — os 24 meses seguintes custam
R$ 1.439,76. A Hetzner cobra por hora, sem compromisso: ~R$ 576 nos mesmos 24 meses.

### 2.4 PaaS gerenciada (Railway / Render / Fly.io) — mais cara e mais trabalho

Todas descartam o `docker-compose.yml`: cada serviço vira uma unidade cobrada, e esta stack
tem **seis** (postgres, redis, backend, frontend, worker, beat).

- **Railway:** sem free tier desde 2023. Hobby $5/mês com $5 de crédito *embutido* (não
  somado), cobrança por segundo de CPU/RAM. Seis serviços 24/7 estouram os $5 com folga.
- **Render:** tem free tier real, mas web services **dormem após 15 min** e levam ~1 min para
  acordar. Um avaliador clica no link do portfólio e encara uma tela branca por um minuto.
- **Fly.io:** sem free allowance para contas novas; ~$2/mês por VM de 256 MB — mas seriam
  várias VMs mais volumes.

Além do custo, migrar para PaaS **contraria o ADR-009**, que acabou de eleger o host único
como topologia oficial. Exigiria ADR novo.

### 2.5 Split frontend na Vercel + backend em VPS — decisão já aposentada

É a topologia B que o ADR-009 aposentou em 2026-08-03 (e o deploy órfão do frontend na Vercel
é a consequência registrada lá). A Vercel hospedaria o Next com SSR de graça e resolveria a
latência via CDN, mas paga em dois ambientes, CORS e dois deploys. Só volta à mesa com ADR
novo — não é caminho para "simples".

---

## 3. Comparativo

| opção | custo/mês | latência BR | esforço até a E.4 fechar | risco de sair do ar |
|---|---:|---|---|---|
| **Hostinger KVM 1** | R$ 34,99 (2 anos à vista) | **10–40 ms** | médio — build precisa sair do servidor | baixo |
| Hetzner CX22 | ~R$ 35–38 (por hora) | ~120–200 ms | **baixo** — guia pronto, compose e CD já servem | baixo |
| Oracle Always Free | R$ 0 | ~180 ms | médio — provisionar ARM, rebuild das imagens | **alto** |
| Railway / Render / Fly | $10–20+ | varia | **alto** — reescreve a topologia, contraria ADR-009 | médio (Render: dorme) |

**Recomendação: Hostinger KVM 1.** Depois do reajuste da Hetzner as duas custam o mesmo por
mês, e no empate a opção brasileira entrega **latência de São Paulo** e **backup semanal
incluído** — que tapa o buraco da seção 4. O que ela cobra em troca é a **trava de 2 anos**
(R$ 839,76 à vista, renovando a R$ 59,99/mês).

Em 4 anos: Hostinger R$ 839,76 + R$ 1.439,76 = **R$ 2.279,52**; Hetzner ~R$ 38 × 48 =
**~R$ 1.824**, *se* não houver novo reajuste — e houve dois em 2026. A trava da Hostinger é
custo e proteção ao mesmo tempo.

Se o critério virar custo zero acima de tudo, Oracle — sabendo que a demo pode estar fora do
ar justamente quando importar.

---

## 4. Custos que não aparecem no preço da máquina

- **Domínio:** DuckDNS é gratuito e o Caddy tira o HTTPS do Let's Encrypt sozinho — já coberto
  em `docs/deploy.md`. Um `.com.br` no registro.br custa ~R$ 40/ano.
- **Quota da Groq:** a demo pública consome o free tier, cujo limite diário (TPD 100k) já
  mordeu na Fase C.7 — a bateria de invariância morreu com 99.768 de 100.000 tokens usados. O
  rate limiting da Fase B.3 já está no lugar e a conta demo é limitada, mas um pico de acessos
  derruba a análise de refeição do dia.
- **Backup:** hoje é manual (`pg_dump` documentado em `docs/deploy.md`, sem cron nem offsite).
  São 40 MB — cabe em qualquer lugar, e vira crítico no instante do primeiro deploy real.

---

## 5. O que isto não decide

Nada aqui altera a topologia: o ADR-009 continua valendo, e qualquer das opções 2.1–2.3 sobe
o mesmo `docker-compose.yml` sem mudança. Escolher provedor é decisão de owner; quando ela
sair, a Fase E.4 executa com o host em mãos e um ADR-010 registra a escolha.

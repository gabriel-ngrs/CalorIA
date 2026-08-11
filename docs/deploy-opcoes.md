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

**Concorrência não é o critério de compra.** Para a ordem de grandeza de usuários simultâneos
que este projeto tem (2–5), nenhuma máquina de 2 vCPU / 4 GB chega perto de saturar: o
trabalho pesado da análise de refeição acontece nos servidores da Groq, não neste host. O teto
real é a **quota do free tier da Groq** — limite diário de 100.000 tokens, do qual a Fase C.7
mediu uma única rodada de eval consumindo **99.768**. Comprar CPU não move esse teto.

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

### 2.4 Netcup VPS Lite — €4,88/mês (~R$ 26–31) · **recomendada**

A Netcup mantém duas linhas, e a barata é a **VPS Lite** (preços da página oficial, com 19%
de IVA alemão inclusos):

| plano | vCores | RAM | disco | €/mês c/ IVA |
|---|---:|---:|---|---:|
| VPS nano G11s | 2 | 2 GB | 60 GB SSD | €3,08 |
| **VPS Lite 1 G12s** | **2** | **4 GB** | **80 GB SSD** | **€4,88** |
| VPS Lite 2 G12s | 4 | 8 GB | 160 GB SSD | €7,92 |

O **Lite 1** é o encaixe: 2 vCPU e 4 GB comportam a stack medida na seção 1 **com folga para
buildar no servidor**.

**Medido no carrinho da Netcup em 2026-08-11**, com endereço no Brasil, na variante
`VPS Lite 1 G12s iv 6M`:

| linha | valor |
|---|---:|
| VPS Lite 1 G12s iv 6M | €3,60/mês → €21,60 |
| IPv4 Connectivity | €0,50/mês → €3,00 |
| IPv6 Connectivity | €0,00 |
| Setup costs (one-time) | **€0,00** |
| VAT | **0%** — o IVA alemão de 19% cai com endereço no Brasil |
| **total do primeiro recibo** | **€24,60** (6 meses) |

Ou seja: **€4,10/mês** (~R$ 26), ~R$ 155 por semestre, **período mínimo de 6 meses**. O IPv4 é
cobrado em linha própria, como na Hetzner — comparando os dois com IPv4 incluído na conta,
Netcup €4,10 contra Hetzner CX22 €5,99.

> A página geral da Netcup não declara contrato mínimo, e a primeira versão desta seção
> afirmou "cancela quando quiser" com base nela. O carrinho desmente: a variante `6M` trava
> por 6 meses. Vale checar em "Customize configuration" se há variantes `12M` (mensal menor)
> ou `1M` (mensal maior, sem trava).

A diferença declarada da linha Lite para os VPS G12 regulares é **banda e velocidade de
interface reduzidas**. Para servir um dashboard a um punhado de usuários, é irrelevante.

**Contra:** datacenter na Alemanha/Áustria (~200 ms) e backup por sua conta.

### 2.4.1 Outras europeias

| provedor | plano | ~mensal | nota |
|---|---|---:|---|
| Contabo | VPS S: 4 vCPU / 8 GB / 200 GB NVMe | $11,31 (~R$ 61) | muito hardware, mas o dobro do preço do Lite 1 para uma folga que não é usada |
| Netcup VPS 500 G12 | 2 vCPU / 4 GB / 128 GB NVMe | €5,91 (~R$ 37) | a linha regular: NVMe e banda cheia pelo preço da Hostinger |
| RackNerd | entrada $22,99/**ano** | ~R$ 10 | 512 MB não serve; provedor pequeno, sem SLA — risco alto para uma vitrine |

### 2.5 Provedores brasileiros — cuidado com a renovação

| provedor | entrada | nota |
|---|---:|---|
| Locaweb | R$ 15,90 | 512 MB — **não serve**, a stack precisa de ~1 GB |
| KingHost | R$ 22,90 | 1 GB — no limite, sem folga |
| **Hostinger KVM 1** | R$ 34,99 | ver 2.3 |
| Audaks | R$ 38 | NVMe + vCPU dedicada |
| Vultr / Linode (Akamai) | ~$24 (R$ 130) para 4 GB | têm região São Paulo, mas custam 4× a Hostinger |
| Magalu Cloud | **R$ 129,99** para 2 vCPU / 2 GB (`BV2-2-100`) | nuvem cobrada como nuvem, não VPS — 4× o preço do Netcup Lite 1 por metade do recurso; o tipo de R$ 34,99 (`BV1-1-10`) tem só 1 GB |

**Padrão do mercado brasileiro:** a renovação sobe de 40% a 100% depois do período
promocional — a KingHost mais que dobra no segundo ano, a Hostinger sobe ~71%. Comparar
sempre pelo preço de renovação, não pelo da vitrine.

### 2.6 PaaS gerenciada (Railway / Render / Fly.io) — mais cara e mais trabalho

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

### 2.7 Split frontend na Vercel + backend em VPS — decisão já aposentada

É a topologia B que o ADR-009 aposentou em 2026-08-03 (e o deploy órfão do frontend na Vercel
é a consequência registrada lá). A Vercel hospedaria o Next com SSR de graça e resolveria a
latência via CDN, mas paga em dois ambientes, CORS e dois deploys. Só volta à mesa com ADR
novo — não é caminho para "simples".

---

## 3. Comparativo

| opção | vCPU / RAM | custo/mês | trava | latência BR | backup |
|---|---|---:|---|---|---|
| **Netcup VPS Lite 1** | 2 / 4 GB | **~R$ 26** (€4,10) | 6 meses (~R$ 155/semestre) | ~200 ms | por sua conta |
| Hostinger KVM 1 | 1 / 4 GB | R$ 34,99 → R$ 59,99 | **24 meses, R$ 839,76 à vista** | **10–40 ms** | **semanal incluído** |
| Hetzner CX22 | 2 / 4 GB | ~R$ 35–38 | nenhuma (por hora) | ~120–200 ms | por sua conta |
| Contabo VPS S | 4 / 8 GB | ~R$ 61 | mensal | ~180 ms | por sua conta |
| Magalu Cloud `BV2-2-100` | 2 / 2 GB | R$ 129,99 | nenhuma (por hora) | **~10 ms** | por sua conta |
| Oracle Always Free | 2 / 12 GB | R$ 0 | nenhuma | ~180 ms | por sua conta |
| Railway / Render / Fly | varia | $10–20+ | nenhuma | varia | varia |

**Recomendação: Netcup VPS Lite 1 G12s.** É mais barata que a Hostinger **e** entrega o dobro
de vCPU e 30 GB a mais de disco. As duas têm trava, mas em escalas diferentes: **R$ 155 por
semestre** contra **R$ 839,76 por dois anos**. Em 24 meses dá ~R$ 620 na Netcup contra
R$ 839,76 na Hostinger — e a renovação da Hostinger a R$ 59,99 abre a diferença no terceiro
ano.

O que a Netcup não entrega é **latência brasileira** e **backup automático**. O backup se
resolve com cron (seção 5, e são 40 MB); a latência não se resolve — se ela for o critério
decisivo, a Hostinger é a única da lista com São Paulo por menos de R$ 100.

Alternativas conforme o critério mudar: **Contabo VPS S (~R$ 61)** se o peso for hardware por
real; **Oracle** se for custo zero acima de tudo, sabendo que a demo pode estar fora do ar
justamente quando importar. **Magalu Cloud está fora**: R$ 129,99 por 2 GB é nuvem cobrada
como nuvem, não VPS.

---

## 4. Simplificar o deploy não é escolher outra VPS

Trocar de provedor não muda em nada o `cd.yml`, que hoje é um script SSH com `git pull` +
`--build` + `sleep 10`. Quem simplifica o deploy é um **PaaS self-hosted instalado sobre a
VPS**:

| | Dokploy | Coolify |
|---|---|---|
| RAM ociosa do painel | ~350 MB | 1,2 GB (mínimo de 2 cores / 2 GB só para o painel) |
| `docker-compose.yml` | **nativo** — deploya o arquivo como está | suportado, mas **sem zero-downtime** via compose |
| catálogo / recursos | menor | 280+ serviços de um clique, multi-servidor |

Para este projeto o encaixe é o **Dokploy**: ele roda o `docker-compose.yml` sem embrulhá-lo
em abstração própria, que é exatamente a topologia que o ADR-009 fixou, e o webhook de deploy
satisfaz o "merge em `main` publica sozinho" do AC-27 com muito menos script que o `cd.yml`
atual. Em máquina de 2 GB (Netcup), os 350 MB do painel ainda cabem; o 1,2 GB do Coolify não.

**Ressalva:** adotar qualquer um dos dois é mudança de arquitetura — pede um ADR próprio e
redefine o escopo da Fase E.4, que hoje declara alterar `cd.yml`, `docs/deploy.md` e
`README.md`. É decisão de owner, não detalhe de execução.

## 5. Custos que não aparecem no preço da máquina

- **Domínio:** DuckDNS é gratuito e o Caddy tira o HTTPS do Let's Encrypt sozinho — já coberto
  em `docs/deploy.md`. Um `.com.br` no registro.br custa ~R$ 40/ano.
- **Quota da Groq:** a demo pública consome o free tier, cujo limite diário (TPD 100k) já
  mordeu na Fase C.7 — a bateria de invariância morreu com 99.768 de 100.000 tokens usados. O
  rate limiting da Fase B.3 já está no lugar e a conta demo é limitada, mas um pico de acessos
  derruba a análise de refeição do dia.
- **Backup:** hoje é manual (`pg_dump` documentado em `docs/deploy.md`, sem cron nem offsite).
  São 40 MB — cabe em qualquer lugar, e vira crítico no instante do primeiro deploy real.

---

## 6. O que isto não decide

Nada aqui altera a topologia: o ADR-009 continua valendo, e qualquer das opções 2.1–2.3 sobe
o mesmo `docker-compose.yml` sem mudança. Escolher provedor é decisão de owner; quando ela
sair, a Fase E.4 executa com o host em mãos e um ADR-010 registra a escolha.

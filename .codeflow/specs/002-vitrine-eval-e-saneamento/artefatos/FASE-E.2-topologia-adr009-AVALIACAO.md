---
spec: 002-vitrine-eval-e-saneamento
fase: E.2
slug_fase: topologia-adr009
tentativa: 2
veredito: APROVADO
score: 9.8
threshold: 8.5
range_avaliado: d43b1bc488fb63abc8994bbbbc98cf2271b150c0..091641c
---

# FASE E.2 — Avaliação independente

## 1. Veredito e score

**Veredito:** APROVADO · **Score:** 9.8 / threshold 8.5

**E2-IMP-1 está fechado nos três lugares que a avaliação pediu, e o terceiro — o que
fecha a contradição dentro do próprio arquivo — era o que mais importava.** O achado
era que o cabeçalho novo declarava "sem uso" sobre o compose que o `cd.yml` sobe, o que
teria levado a D.4 a removê-lo e quebrar o CD por um caminho que ninguém associaria à
poda. Fui conferir os dois lados.

O gatilho do achado é real, e está exatamente onde o relatório diz:

```text
$ sed -n '38p' .github/workflows/cd.yml
            docker compose -f docker-compose.backend.yml up -d --build
```

E o cabeçalho corrigido deixou de mentir por omissão:

```text
# ATENÇÃO — ainda referenciado: `.github/workflows/cd.yml:38` sobe ESTE arquivo. O
# CD está inerte (só `workflow_dispatch`, sem servidor), mas a referência existe.
# Ordem obrigatória: a Fase E.4 troca a referência para `docker-compose.yml`; só
# então a Fase D.4 pode remover este arquivo na poda. Remover antes quebra o CD.
```

O ADR-009 diz a mesma coisa, com a mesma ordem, em `docs/architecture.md:51-59`:

```text
- O `cd.yml` do ADR-008 continua válido **como desenho de pipeline** (SSH, `concurrency`,
  migração antes de subir), mas **implementa a topologia aposentada**: seu passo de
  deploy sobe `docker-compose.backend.yml` (`cd.yml:38`). Trocá-lo por
  `docker-compose.yml` é trabalho da **Fase E.4** ...
  **Consequência para a Fase D.4:** o `docker-compose.backend.yml` só pode ser removido
  na poda **depois** que a E.4 corrigir essa referência ...
```

**A decisão de não editar o `cd.yml` está certa, e é a leitura correta do escopo.** O
arquivo não está nos "Arquivos alterados" da E.2, e a E.4 já é dona da reativação do
gatilho. Declarar a pendência com dono e ordem, em vez de invadir a fase vizinha, é o
que a avaliação anterior pediu e é o que o princípio 7 (diff mínimo) manda. Confirmei
que o `cd.yml` não foi tocado no range.

**A resposta à dúvida 2 do relatório é: não, "desambiguar" não exige remover os legados
agora — e removê-los agora quebraria o CD.** É a própria pendência do item 4 que prova
isso. A ordem que a fase registrou (E.4 troca a referência → D.4 remove) é a única
sequência segura, e ela agora está escrita nos dois arquivos que um leitor consultaria.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 4.5 | AC-25 satisfeito nas duas cláusulas: os **cinco** arquivos de orquestração declaram propósito em cabeçalho, e ADR-009 existe. Escopo travado respeitado — o único arquivo removido no range é `docs/deploy-checklist.md`, que é documento e cuja incorporação o passo 4 pede; nenhum arquivo de orquestração foi deletado. Meia nota porque o objetivo declarado é *"eliminar a ambiguidade"* e o que a fase entrega é a ambiguidade **documentada**, com a eliminação delegada a E.4/D.4 — a delegação é correta, mas o objetivo não fecha dentro da fase. |
| 2 | Arquitetura e direção de dependências | 3 | 5 | A correção declara a direção da dependência (`E.4 → D.4`) explicitamente e nos dois lados, em vez de deixá-la implícita. Recusar-se a editar `cd.yml` (arquivo da E.4) mantém a fronteira entre fases. |
| 3 | Segurança / LGPD | 3 | 5 | O host morto sumiu: `grep -c "caloria-gabriel" docs/deploy.md` → **0**, substituído por `caloria.exemplo.com` (5 ocorrências). As únicas ocorrências de `duckdns` remanescentes são a instrução genérica de subdomínio gratuito, não o host antigo. Nenhuma credencial real no range — os matches de `password`/`gsk_` em `deploy.md:189,207` são placeholders (`SenhaForteAqui123!`, `gsk_...sua_chave_aqui`). |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | ADR-009 acrescentado depois do ADR-008, no formato dos oito anteriores; nenhum ADR existente tocado. A consolidação eliminou a duplicação `deploy.md` × `deploy-checklist.md`, que era a causa de o host errado estar registrado em quatro lugares. |
| 5 | Padrões de domínio/aplicação | 2 | 5 | Os cinco cabeçalhos seguem a mesma forma (identidade · papel · ADR de referência), o que torna a distinção oficial × legado legível de relance. |
| 6 | Local e nomes dos arquivos | 2 | 5 | Todos os arquivos tocados estão entre os "Arquivos alterados" declarados na §5. |
| 7 | Qualidade de código | 2 | 5 | Mudança só de documento nesta tentativa, como o relatório declara — confirmei que nenhum arquivo de código entrou no diff da tentativa 2. |
| 8 | Testes e cobertura | 2 | 5 | O teste que o AC-25 pede é `docker compose -f <cada arquivo> config`, e rodei os três: os três validam (os avisos são de variável de ambiente não definida, não erro de configuração). |
| 9 | Migration safety | 2 | [—] | Nenhuma migration criada ou alterada. Dimensão excluída do cálculo. |

**Score:** (4,5·3 + 5·3 + 5·3 + 5·3 + 5·2 + 5·2 + 5·2 + 5·2) / 20 = 98,5/20 = 4,925 → **9,8**

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

Nenhum. **E2-IMP-1** está fechado, verificado nos três pontos no §1.

## 5. Sugestões

1. **Item 1 do relatório (frontend órfão na Vercel) merece virar ação antes da D.2, não
   depois.** O relatório está certo em não agir — é serviço externo e decisão do owner —
   mas a ordem importa: a D.2 é o que faz o repositório virar vitrine pública, e hoje o
   que um visitante encontra é uma tela de login cuja API não existe. Já está na OQ16
   como pendência da E.4; vale só puxar a decisão para antes da promoção.
2. **`docs/deploy.md` continua com o passo a passo escrito no console da Hetzner**
   (item 3 do relatório). A abertura resolve o enquadramento com honestidade ("o
   provedor usado como exemplo é a Hetzner Cloud, mas qualquer VPS com Docker serve"),
   então não é imprecisão — é só o corpo ainda não ser agnóstico. Concordo com o
   encaminhamento para a D.3.
3. **Quando a E.4 trocar a referência do `cd.yml`, remover também o aviso do cabeçalho
   de `docker-compose.backend.yml`.** O bloco "ATENÇÃO — ainda referenciado" é correto
   hoje e vira desinformação no minuto seguinte à troca. Vale entrar como passo
   explícito da E.4, junto com a troca — é o mesmo tipo de descompasso entre documento
   e realidade que originou o E2-IMP-1.

## 6. Comandos rodados + saídas reais

Rodados por mim, na ponta da branch `dev`. Árvore limpa antes e depois.

```text
$ git merge-base --is-ancestor 091641c HEAD
d43b1bc4...: ANCESTRAL   |   091641c: ANCESTRAL
$ git status --porcelain
(vazio)

$ bash ~/.codeflow/framework/core/scripts/run-structural.sh .../SPEC_002_...md
✓ §5 estruturalmente válida

# AC-25, cláusula 2 — cada compose valida
$ docker compose -f docker-compose.yml         config -q   → OK
$ docker compose -f docker-compose.backend.yml config -q   → OK
$ docker compose -f docker-compose.dev.yml     config -q   → OK
(avisos de VAPID_* não definidos; nenhum erro de configuração)

# AC-25, cláusula 1 — cada arquivo de orquestração declara seu propósito
docker-compose.yml         # CalorIA — stack COMPLETA em host único · TOPOLOGIA OFICIAL (ADR-009)
docker-compose.dev.yml     # CalorIA — Docker Compose (Desenvolvimento)
docker-compose.backend.yml # CalorIA — apenas o BACKEND · LEGADO da topologia dividida (ADR-009)
Caddyfile                  # CalorIA — Caddyfile · par oficial do `docker-compose.yml` (ADR-009)
Caddyfile.backend          # CalorIA — proxy só da API · LEGADO da topologia dividida (ADR-009)

# o gatilho do E2-IMP-1
$ sed -n '38p' .github/workflows/cd.yml
            docker compose -f docker-compose.backend.yml up -d --build
$ sed -n '7,10p' .github/workflows/cd.yml
#   push:
#     branches: [main]
on:
  workflow_dispatch:
# confirma que o CD está inerte: nem a promoção da D.2 dispara deploy

# escopo travado: nenhum arquivo de orquestração removido
$ git diff --diff-filter=D --name-only d43b1bc..091641c
docs/deploy-checklist.md
# único removido, e é o documento que o passo 4 manda incorporar ao deploy.md

# host morto e segredos
$ grep -c "caloria-gabriel" docs/deploy.md          → 0
$ grep -c "caloria.exemplo.com" docs/deploy.md      → 5
$ git diff d43b1bc..HEAD | grep -iE "^\+.*(gsk_[A-Za-z0-9]{20}|@gmail\.com)"
(vazio)
```

## 7. Itens da fase / DoD não atendidos

Nenhum.

- **§9 "E.2 — AC-25; ADR-009 escrito; owner confirmou a topologia"** — os três. O ADR-009
  está em `docs/architecture.md` depois do ADR-008, e a decisão do owner (host único,
  self-hosted, local por enquanto) está registrada nele.
- **Passo 1 (decidir a topologia com o owner)** — feito, com os fatos da E.1 como base.
- **Passo 2 (ADR-009)** — presente, com a tabela das duas topologias e as consequências.
- **Passo 3 (desambiguar por cabeçalho)** — os cinco arquivos declaram propósito e
  posição (oficial × legado). O passo autoriza "renomear **e/ou** dar cabeçalho"; a via
  do cabeçalho foi a escolhida, e é a que não quebra referência.
- **Passo 4 (consolidar `deploy.md` + `deploy-checklist.md`, atualizar Roadmap 9.2)** —
  o checklist virou seção final do `deploy.md` e o arquivo duplicado saiu; Roadmap 9.2
  declara o deploy adiado por decisão.
- **Escopo travado** — nenhum arquivo de orquestração em uso removido; nenhuma
  credencial ou variável alterada.

**Pendência registrada, com dono, que não é item faltante desta fase:** `cd.yml:38`
segue apontando para o compose legado. Está declarada no §7 item 4 do relatório, no
ADR-009 e no cabeçalho do próprio compose, com a ordem obrigatória E.4 → D.4. É o
tratamento correto para trabalho que pertence a outra fase.

## 8. Divergências entre o relatório e o código real

Nenhuma. Conferi cada afirmação verificável da tentativa 2 e todas batem:

| Afirmação do relatório | Verificação |
|---|---|
| `cd.yml:38` sobe `docker-compose.backend.yml` | confere, na linha 38 exata |
| o cabeçalho deixou de dizer "sem uso" e passou a avisar da referência | confere, com a ordem obrigatória E.4 → D.4 escrita |
| o ADR-009 declara o `cd.yml` como desenho válido sobre topologia aposentada | confere, `docs/architecture.md:51-59` |
| os três composes validam | confere, rodei os três |
| o CD está inerte (só `workflow_dispatch`) | confere, `push: branches: [main]` comentado |
| nenhum arquivo de código tocado nesta tentativa | confere |
| host morto trocado por `caloria.exemplo.com` | confere — 0 ocorrências do host antigo, 5 do exemplo |

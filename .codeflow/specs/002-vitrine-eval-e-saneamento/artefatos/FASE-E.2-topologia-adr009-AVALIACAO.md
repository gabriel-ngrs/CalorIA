---
spec: 002-vitrine-eval-e-saneamento
fase: E.2
slug_fase: topologia-adr009
tentativa: 1
veredito: RESSALVAS
score: 9.4
threshold: 8.5
range_avaliado: d43b1bc488fb63abc8994bbbbc98cf2271b150c0..70401f5c3397b95ffdb27fa7f4b6dcc33033b369
---

# FASE E.2 — Avaliação independente

## 1. Veredito e score

**Veredito:** RESSALVAS · **Score:** 9.4 / threshold 8.5

**A fase entrega o que se propôs, e a execução é limpa.** Reproduzi cada afirmação do
relatório em vez de aceitá-la:

- Os cinco arquivos de orquestração declaram propósito no cabeçalho; três deles amarram
  a declaração ao ADR-009 com o vocabulário oficial/legado.
- ADR-009 presente (`architecture.md:169`), no formato dos existentes, e **nenhum ADR
  anterior foi tocado** — o diff só acrescenta.
- Os três composes passam em `docker compose config`, e os dois Caddyfiles retornam
  `Valid configuration` no `caddy validate` (rodei via imagem `caddy:2-alpine`; a
  validação de Caddyfile está acima do que o AC-25 pedia).
- **Os quatro diffs de orquestração são exclusivamente comentário.** Filtrei linhas
  não-comentário e não-vazias nos quatro arquivos: zero. Numa fase que mexe em compose
  e proxy de produção, isso é a evidência que importa — nenhuma variável de ambiente,
  porta ou serviço mudou.
- Exatamente os 9 arquivos declarados, nem um a mais.

As três decisões de design são conservadoras e bem fundamentadas, em especial trocar o
host morto por `caloria.exemplo.com` em vez de outro host concreto: "um placeholder
óbvio não mente" é a leitura certa do defeito que a E.1 encontrou.

**O que impede o APROVADO é um item que o relatório não declara, e que contradiz a
própria entrega da fase.** O `docker-compose.backend.yml` recebeu um cabeçalho dizendo
*"Mantido como referência histórica, **sem uso**"* — e `.github/workflows/cd.yml:38`
é justamente quem o usa. Pior: o ADR-009 afirma que *"o `cd.yml` do ADR-008 continua
válido como desenho"*, quando o desenho dele é a topologia B, que este mesmo ADR
aposenta. Detalhe em §4.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 4 | Os 4 passos entregues; AC-25 verificado nas duas metades (cabeçalho em cada arquivo + ADR-009 presente); os 3 composes validam (§6). Gate "owner confirmou a topologia" registrado na OQ16 com as duas condições temporais. Escopo travado respeitado nos três itens: nenhum arquivo de orquestração deletado, **zero alteração funcional** (diffs comment-only, §6), ADRs existentes intocados. Desconto: o ADR entregue afirma algo falso sobre o `cd.yml` (§4) |
| 2 | Arquitetura e direção de dependências | 3 | 4 | ADR-009 no lugar certo, no formato dos anteriores (Contexto/Decisão/Justificativa/Consequências), com a tabela das duas topologias e a medição da E.1 como fundamento. Desconto: a seção de consequências trata o `cd.yml` como compatível quando ele consome o par aposentado — e o `cd.yml` é justamente o consumidor dos arquivos que esta fase desambiguou |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | Nenhuma credencial ou variável de produção alterada — provado pelo filtro de diff, não afirmado. O host morto virou placeholder explícito em vez de outro endereço concreto, e o `deploy.md` abre com aviso de que não há servidor no ar |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | O ADR-009 reusa o formato dos oito anteriores; os dois arquivos legados ganharam o **mesmo** estilo de cabeçalho que `docker-compose.yml` e `docker-compose.dev.yml` já usavam, em vez de um formato novo |
| 5 | Padrões de domínio/aplicação | 2 | 5 | A seção de checklist absorvida em `deploy.md` **não repete comandos**, e o relatório explica o porquê: foi a duplicação entre os dois documentos que deixou o host morto sobreviver em quatro lugares |
| 6 | Local e nomes dos arquivos | 2 | 5 | Exatamente os 9 arquivos de "Arquivos alterados" da §5 — conferido pelo `--stat` do range |
| 7 | Qualidade de código | 2 | 5 | Os cabeçalhos dizem o que o arquivo é, se está em uso e para onde vai; `docker-compose.backend.yml:13` até aponta o substituto ("Para subir o projeto, use `docker-compose.yml`") |
| 8 | Testes e cobertura | 2 | 5 | Validação real dos 3 composes **e** dos 2 Caddyfiles — a segunda acima do que o AC-25 exige, e reproduzida por mim (§6) |
| 9 | Migration safety | 2 | [—] | Nenhuma migration tocada; nenhum arquivo de código tocado |

Score = (3·4 + 3·4 + 3·5 + 3·5 + 2·5 + 2·5 + 2·5 + 2·5) / 20 · 2 = 94/20 · 2 = **9.4**

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

**E2-IMP-1 — o cabeçalho novo diz "sem uso" sobre o arquivo que o `cd.yml` usa, e o
ADR-009 declara o `cd.yml` compatível quando ele implementa a topologia aposentada.**

**Onde:** `docker-compose.backend.yml:12` (*"Mantido como referência histórica, sem
uso"*) e `docs/architecture.md:219-220` (*"O `cd.yml` do ADR-008 continua válido como
desenho, e continua inerte enquanto não houver servidor"*), contra
`.github/workflows/cd.yml:38`.

**O defeito.** Medi:

```text
$ grep -n "docker compose" .github/workflows/cd.yml
38:            docker compose -f docker-compose.backend.yml up -d --build
$ git log --oneline d43b1bc..70401f5 -- .github/workflows/cd.yml
(vazio — o arquivo não foi tocado nesta fase)
$ sed -n '12,13p' docker-compose.backend.yml
# Mantido como referência histórica, sem uso. Marcado para remoção na poda do
# repositório (Fase D.4). Para subir o projeto, use `docker-compose.yml`.
```

Três artefatos apontando um para o outro com afirmações incompatíveis:

| artefato | afirma |
|---|---|
| `docker-compose.backend.yml:12` | "sem uso", removível na D.4 |
| `cd.yml:38` | é o arquivo que o deploy sobe |
| `architecture.md:219` | o `cd.yml` "continua válido como desenho" |
| `cd.yml:3-4` | "a topologia de produção ainda não foi decidida (spec 002, **Fase E.2**)" |

O último é o mais direto: o cabeçalho do `cd.yml` cita **esta fase** como a decisão
pendente, e essa decisão acabou de sair. O comentário nasceu correto e ficou obsoleto no
instante em que a E.2 fechou.

**Por que é IMPORTANTE.** O Objetivo declarado da fase é *"eliminar a ambiguidade dos
arquivos de orquestração"*. Um cabeçalho que afirma "sem uso" sobre um arquivo que uma
pipeline ativa consome não elimina ambiguidade — cria uma pior, porque agora o arquivo
**mente com autoridade**. E a D.4 vai ler "marcado para remoção" e remover o compose que
o `cd.yml` referencia, deixando o deploy quebrado por um caminho que ninguém vai
associar à poda.

**Por que não é BLOQUEANTE, e sou específico.** Verifiquei o gatilho antes de calibrar:
`cd.yml:9-10` está em `workflow_dispatch:` apenas — o `push: branches: [main]` está
comentado. Ou seja, a promoção da D.2 **não** dispara deploy nenhum, e não há servidor
para deployar. O risco é de artefato e de sequência, não de produção hoje.

**Correção sugerida** — o `cd.yml` **não** está nos arquivos declarados desta fase, então
a correção certa não é editá-lo aqui, e sim declarar a pendência. Três opções, e a
escolha é do owner:

1. **Registrar como quarto item aberto** no relatório da E.2, junto dos três que já
   estão lá, e apontar a Fase E.4 (que já é dona da reativação do gatilho) como
   responsável por trocar `docker-compose.backend.yml` por `docker-compose.yml` em
   `cd.yml:38`. Mais barato e mais coerente com o escopo declarado.
2. **Corrigir a frase do ADR-009** para dizer o que é verdade: o `cd.yml` implementa a
   topologia B e precisa ser ajustado na E.4 — em vez de "continua válido como desenho".
   Uma linha, e evita que a E.4 herde a premissa errada.
3. **Acrescentar ao cabeçalho de `docker-compose.backend.yml`** a ressalva de que o
   `cd.yml` ainda o referencia até a E.4. Remove a contradição sem tocar em workflow.

Recomendo **1 + 2**: são de artefato, cabem no escopo da fase, e fecham a contradição
onde ela nasceu.

## 5. Sugestões

- **A D.4 precisa saber disto antes de podar.** O bloco da D.4 na §5 manda remover o que
  está marcado; se o `cd.yml` não for ajustado antes, a poda quebra o deploy por um
  caminho indireto. Um `Depende de` ou uma linha no escopo travado da D.4 evitaria.
- **`docker-compose.dev.yml` é o único dos cinco cujo cabeçalho não cita o ADR-009.** Ele
  declara propósito ("Desenvolvimento / hot reload"), então o AC-25 está satisfeito — e o
  arquivo está fora do escopo declarado, de modo que não tocá-lo foi a decisão certa.
  Registro só para que a leitura lado a lado não pareça esquecimento.
- **Sobre o desvio do CHANGELOG declarado no relatório:** a conclusão está certa (fora do
  escopo desta fase), mas a justificativa citada não. O escopo travado da D.1 diz "não
  alterar o **histórico** do CHANGELOG", o que veda reescrever entradas passadas, não
  acrescentar em `## [Não lançado]`. O argumento que sustenta a decisão é o outro que o
  relatório dá — o arquivo não está na lista da fase.
- **O frontend órfão na Vercel está bem registrado** (ADR-009 e relatório), e concordo com
  a leitura de que é ação do owner. Reforço a urgência relativa: é o que um visitante vê
  hoje, e a D.2 torna o repositório público.

## 6. Comandos rodados + saídas reais

```text
# --- Passo 1: gate estrutural da §5 ---
$ bash ~/.codeflow/framework/core/scripts/run-structural.sh .codeflow/specs/…/SPEC_002….md
✓ grafo de dependências acíclico
✓ §5 estruturalmente válida
>>> EXIT=0

# --- Passo 2: ancestralidade, escopo do diff, árvore limpa ---
$ git status --porcelain | wc -l
0
$ git merge-base --is-ancestor d43b1bc… HEAD   → ANCESTRAL
$ git merge-base --is-ancestor 70401f5… HEAD   → ANCESTRAL
$ git diff --stat d43b1bc..70401f5 -- . ':(exclude).codeflow/specs/*/artefatos/*'
 Caddyfile | 6 +- · Caddyfile.backend | 11 ++ · README.md | 16 +- · Roadmap.md | 7 +
 docker-compose.backend.yml | 15 ++ · docker-compose.yml | 11 +- · docs/architecture.md | 55 ++
 docs/deploy-checklist.md | 152 --- · docs/deploy.md | 53 +-
 9 files changed, 158 insertions(+), 168 deletions(-)
   → exatamente os 9 arquivos declarados na §5                                 ✓

# --- escopo travado: nenhuma mudança funcional nos arquivos de orquestração ---
$ for f in docker-compose.yml Caddyfile docker-compose.backend.yml Caddyfile.backend; do
    git diff d43b1bc..70401f5 -- $f | grep -E "^[+-]" | grep -vE "^(\+\+\+|---)" \
      | grep -vE "^[+-]\s*#" | grep -vE "^[+-]\s*$"; done
(vazio nos quatro)
   → zero alteração de serviço, porta, env ou credencial                       ✓

# --- AC-25, metade "cada arquivo declara seu propósito" ---
$ head -2 docker-compose.yml         → CalorIA — stack COMPLETA em host único · TOPOLOGIA OFICIAL (ADR-009)
$ head -2 docker-compose.dev.yml     → CalorIA — Docker Compose (Desenvolvimento)
$ head -2 docker-compose.backend.yml → CalorIA — apenas o BACKEND · LEGADO da topologia dividida (ADR-009)
$ head -2 Caddyfile                  → CalorIA — Caddyfile · par oficial do `docker-compose.yml` (ADR-009)
$ head -2 Caddyfile.backend          → CalorIA — proxy só da API · LEGADO da topologia dividida (ADR-009)
   → os cinco declaram                                                         ✓

# --- AC-25, metade "ADR-009 presente" e ADRs anteriores intocados ---
$ grep -n "^## ADR-00" docs/architecture.md | tail -2
155:## ADR-008 — CI/CD com GitHub Actions
169:## ADR-009 — Topologia self-hosted em host único                            ✓
$ git diff d43b1bc..70401f5 -- docs/architecture.md | grep -E "^[-+]## ADR"
+## ADR-009 — Topologia self-hosted em host único
   → só adição; nenhum ADR existente reescrito                                 ✓

# --- AC-25, validação dos composes ---
$ docker compose -f docker-compose.yml config          → config OK
$ docker compose -f docker-compose.dev.yml config      → config OK
$ docker compose -f docker-compose.backend.yml config  → config OK              ✓

# --- acima do pedido: os Caddyfiles também validam (reproduzi) ---
$ docker run --rm -v $PWD/Caddyfile:/etc/caddy/Caddyfile:ro -e APP_DOMAIN=caloria.exemplo.com \
    caddy:2-alpine caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
Valid configuration
$ ... Caddyfile.backend ...
Valid configuration                                                             ✓
   (o binário `caddy` não existe no host; usei a imagem oficial)

# --- passo 4: consolidação e host morto ---
$ ls docs/deploy-checklist.md
No such file or directory                                                       ✓
$ head -12 docs/deploy.md | tail -4
> **Estado em 2026-08-03 — não há servidor no ar.** … o projeto **roda localmente**…
> Onde você ler `caloria.exemplo.com`, troque pelo seu domínio.                 ✓
$ grep -rn "caloria-gabriel.duckdns.org" --include="*.md" --include="*.yml" . | grep -v .codeflow
docker-compose.backend.yml:10  # …não resolve mais nem em DNS.
docs/architecture.md:182       # …não resolve sequer em DNS.
   → só menções que o declaram morto; nenhuma configuração aponta para ele      ✓
$ git diff d43b1bc..70401f5 -- Roadmap.md | head -8
+> **Adiado por decisão do owner (2026-08-03).** … ADR-009 — host único …        ✓

# --- o achado 4.1 ---
$ grep -n "docker compose" .github/workflows/cd.yml
38:            docker compose -f docker-compose.backend.yml up -d --build
$ sed -n '9,10p' .github/workflows/cd.yml
on:
  workflow_dispatch:        ← o `push: branches: [main]` está comentado (:7-8)
$ sed -n '3,4p' .github/workflows/cd.yml
# produção ainda não foi decidida (spec 002, Fase E.2). A reativação do gatilho
   → o comentário cita esta fase como pendência; a pendência acabou de fechar

$ git status --porcelain | wc -l
0
```

## 7. Itens da fase / DoD não atendidos

| Item (§5 / §9 da spec) | Estado |
|---|---|
| Passo 1 — topologia decidida com o owner | Atendido (OQ16, com as duas condições temporais) |
| Passo 2 — ADR-009 em `docs/architecture.md` | Atendido; formato dos anteriores, nenhum reescrito |
| Passo 3 — desambiguar composes e Caddyfiles por cabeçalho | Atendido nos cinco arquivos |
| Passo 4 — consolidar `deploy.md` + `deploy-checklist.md`, atualizar Roadmap 9.2 | Atendido; o checklist não repete comandos, de propósito |
| AC-25 — cada arquivo declara propósito; ADR-009 presente; composes validam | Atendido |
| Gate — owner confirmou a topologia | Atendido (OQ16) |
| Escopo travado — sem deletar orquestração em uso, sem tocar credencial/env, sem reescrever ADR | Atendido nos três, com evidência de diff |
| **Coerência do que a fase declarou** | **PARCIAL** — "sem uso" e "cd.yml continua válido" são incompatíveis com `cd.yml:38` (achado 4.1) |

## 8. Divergências entre o relatório e o código real

1. **Nenhuma divergência no que o relatório afirma.** Reproduzi as validações dos três
   composes e dos dois Caddyfiles, o `--stat` dos 9 arquivos, a ausência do
   `deploy-checklist.md` e a presença do ADR-009. Tudo confere.

2. **Omissão, não erro: o `cd.yml`.** O relatório declara três itens em aberto — o
   frontend órfão na Vercel, os legados esperando a D.4, e o `deploy.md` ainda escrito em
   cima da Hetzner — e os três estão corretos. Falta o quarto, que é o único que
   contradiz uma afirmação da própria entrega (achado 4.1).

3. **O ADR-009 afirma que "o `cd.yml` do ADR-008 continua válido como desenho".** O ADR-008
   descreve o CD como "SSH → git pull → docker compose up → alembic ao mergear na `main`",
   e o `cd.yml` implementa isso sobre `docker-compose.backend.yml` — a topologia B. Dizer
   que o desenho continua válido depois de aposentar a topologia B é a divergência de
   fato desta fase.

4. **Correção de justificativa, sem efeito no resultado:** o relatório atribui a não
   atualização do CHANGELOG ao escopo travado da D.1. Essa regra veda reescrever o
   histórico, não acrescentar em `## [Não lançado]`. A decisão continua certa pelo outro
   motivo que o próprio relatório dá — o arquivo não está na lista da fase.

---
spec: 002-vitrine-eval-e-saneamento
fase: E.2
slug_fase: topologia-adr009
status: executado
tentativa: 1
reprovacoes: 0
sha_inicial: d43b1bc488fb63abc8994bbbbc98cf2271b150c0
sha_final: 70401f5c3397b95ffdb27fa7f4b6dcc33033b369
range: d43b1bc488fb63abc8994bbbbc98cf2271b150c0..70401f5c3397b95ffdb27fa7f4b6dcc33033b369
---

# FASE E.2 — Relatório de execução

## 1. Resumo do que foi feito

O repositório tinha **três** arquivos de compose e **dois** Caddyfiles, nenhum
declarando seu propósito, e a documentação chamava de "Produção" o par que **não**
rodava — enquanto o par que de fato rodou não era citado em lugar nenhum. Esta fase
decidiu a topologia com o owner, registrou o **ADR-009** e deu a cada arquivo um
cabeçalho que diz o que ele é e se está em uso.

A decisão do owner (2026-08-03): **host único, self-hosted**, rodando localmente por
enquanto, com VPS no futuro.

## 2. Arquivos ALTERADOS

| Arquivo | O que mudou |
|---------|-------------|
| `docs/architecture.md` | ADR-009 acrescentado depois do ADR-008, com a tabela das duas topologias, a medição da E.1 e as consequências. Nenhum ADR existente foi tocado. |
| `docker-compose.yml` | Cabeçalho: stack completa, **topologia oficial**, roda local hoje e na VPS depois. |
| `Caddyfile` | Cabeçalho: par oficial do `docker-compose.yml`, serve o site inteiro de um host só. |
| `docker-compose.backend.yml` | Cabeçalho novo (não tinha nenhum): **legado** da topologia dividida, sem uso, marcado para a poda da D.4. |
| `Caddyfile.backend` | Cabeçalho novo: **legado**, publica só `/api`, `/docs` e `/redoc`. |
| `docs/deploy.md` | Título e abertura declarando a topologia; aviso de que **não há servidor no ar**; host morto trocado por `caloria.exemplo.com`; checklist incorporado como seção final. |
| `README.md` | Bloco de estrutura marca oficial × legado; comando de subir a stack ganha a nota da topologia. |
| `Roadmap.md` | Seção 9.2 declara o deploy adiado por decisão, com a topologia já resolvida. |

## 3. Arquivos REMOVIDOS

| Arquivo | Por quê |
|---------|---------|
| `docs/deploy-checklist.md` | Duplicava `deploy.md` passo a passo, com os mesmos comandos e valores. Incorporado como a seção "Checklist de primeiro deploy" do guia, **sem repetir comando** — a lista aponta para as partes. |

## 4. Confirmação do REUSO e decisões de design

**REUSADO:** o formato dos ADRs existentes (Contexto / Decisão / Justificativa /
Consequências) e o estilo de cabeçalho que `docker-compose.yml` e `docker-compose.dev.yml`
já usavam — os dois arquivos legados ganharam o mesmo formato em vez de um novo.

**Três decisões de design, todas conservadoras:**

1. **Não deletei os arquivos legados.** O escopo travado manda não remover arquivo de
   orquestração em uso sem confirmar com o owner; eles não estão em uso, mas remover é
   escopo da **D.4 (poda)**, não desta fase. Cabeçalho + marcação resolve a ambiguidade,
   que é o objetivo declarado aqui. Cada um diz, na primeira linha, que é legado e onde
   será removido.

2. **Troquei o host morto por `caloria.exemplo.com`, não por um host novo.** Não há
   servidor, então qualquer host concreto no guia voltaria a ser ficção — que é
   exatamente o defeito que a E.1 encontrou. Um placeholder óbvio não mente.

3. **A seção de checklist não repete comandos.** Foi a duplicação entre os dois
   documentos que permitiu ao host desatualizado sobreviver em quatro lugares; refazer
   a duplicação em um arquivo só apenas atrasaria o mesmo problema.

**Desvio declarado:** não atualizei o `CHANGELOG.md`. Ele não está nos "Arquivos
alterados" desta fase, e o escopo travado da D.1 proíbe mexer no histórico dele. Se o
avaliador entender que a mudança merece entrada, ela cabe na D.3 ou na D.2.

## 5. Comandos rodados + saídas reais

```text
# AC-25: cada arquivo de orquestração valida
$ docker compose -f docker-compose.yml config          → config OK
$ docker compose -f docker-compose.dev.yml config      → config OK
$ docker compose -f docker-compose.backend.yml config  → config OK

# fui além do pedido: os Caddyfiles também validam
$ docker run --rm -v $PWD/Caddyfile:/etc/caddy/Caddyfile:ro -e APP_DOMAIN=exemplo.com \
    caddy:2-alpine caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
Valid configuration
$ ... Caddyfile.backend ...
Valid configuration

# ADR-009 presente
$ grep -c "^## ADR-009" docs/architecture.md
1

# nenhuma referência pendente ao arquivo removido, fora de registros históricos
$ grep -rn "deploy-checklist" --include="*.md" . | grep -v .codeflow/
docs/architecture.md:216   ← o próprio ADR-009 registrando a incorporação
docs/auditoria/11-dx-docs.md, docs/auditoria/log.md, CHANGELOG.md
   → documentos históricos, que descrevem o estado da época. Não reescritos de
     propósito: CHANGELOG tem escopo travado, e a auditoria é registro datado.

# escopo: os 9 arquivos tocados são exatamente os declarados na §5
$ git status --porcelain
 M Caddyfile / Caddyfile.backend / README.md / Roadmap.md
 M docker-compose.backend.yml / docker-compose.yml
 M docs/architecture.md / docs/deploy.md
 D docs/deploy-checklist.md
```

Nenhum arquivo de código foi tocado, então a suíte não foi reexecutada — o último
estado verde conhecido é o da execução anterior (`623 passed, 1 skipped`, cobertura
73,86%) e o CI remoto em `bbbf03a` (run 30837561079, success).

## 6. Checklist dos ACs / critério de conclusão

- [x] **Passo 1 — topologia decidida com o owner.** Decisão de 2026-08-03: self-hosted
      em host único; roda local agora, VPS no futuro. Registrada no ADR-009 e na §8 da
      spec.
- [x] **Passo 2 — ADR-009 escrito** em `docs/architecture.md`, depois do ADR-008.
      Nenhum ADR existente reescrito (escopo travado respeitado).
- [x] **Passo 3 — desambiguação.** Os cinco arquivos de orquestração declaram propósito
      e status no cabeçalho; oficial e legado ficam explícitos, no arquivo e no README.
- [x] **Passo 4 — docs consolidados.** `deploy-checklist.md` incorporado ao `deploy.md`;
      Roadmap 9.2 atualizado.
- [x] **AC-25 — cada arquivo declara seu propósito; ADR-009 presente; `docker compose
      -f <cada> config` valida.** Verificado nos três composes e, por acréscimo, nos
      dois Caddyfiles.
- [ ] **Gate — "owner confirmou a topologia".** A decisão está tomada e registrada; a
      confirmação formal contra este relatório é do avaliador/owner.

## 7. Itens em aberto / dúvidas para o avaliador

1. **O frontend na Vercel ficou órfão.** Ele continua no ar, com build de ~13 dias,
   servindo uma tela de login cuja API não existe. Sob a topologia de host único ele
   não tem mais papel. Registrei isso como consequência no ADR-009 e como pendência da
   **E.4**, mas **não agi**: tirar do ar ou reapontar é ação do owner sobre um serviço
   externo. Vale decidir antes da D.2, porque é o que um visitante vê hoje.

2. **Os arquivos legados ficam até a D.4.** Se o avaliador entender que "desambiguar"
   exige removê-los agora, a remoção é de dois arquivos e não quebra nada — mas eu li
   o escopo como sendo o oposto disso.

3. **`docs/deploy.md` ainda é escrito em cima da Hetzner** (Parte 2 é o console deles).
   Generalizei o título e a abertura, mas não reescrevi o passo a passo para ser
   agnóstico de provedor: seria reescrita grande, fora do que a fase pede, e a Hetzner
   segue sendo um exemplo válido. Fica anotado como melhoria da D.3.

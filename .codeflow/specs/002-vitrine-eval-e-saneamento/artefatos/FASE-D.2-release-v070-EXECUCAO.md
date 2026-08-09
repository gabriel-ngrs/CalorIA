---
spec: 002-vitrine-eval-e-saneamento
fase: D.2
slug_fase: release-v070
status: executado
tentativa: 1
reprovacoes: 0
sha_inicial: b3018b4
sha_final: b3018b4
range: b3018b4..b3018b4
---

# FASE D.2 — Relatório de execução

## 1. Resumo do que foi feito

A `main`, parada em 2026-04-29 com uma stack abandonada, passou a refletir a `dev`:
270 commits promovidos pelo PR #27 com o CI verde nos dois jobs, merge commit
`defe1dc`, tag **anotada** `v0.7.0` e release publicada. Em seguida a proteção da
`main` foi configurada exigindo os dois checks do CI, e o repositório voltou a ser
público — encerrando a janela aberta na Fase A.1.

A fase **não alterou nenhum arquivo do repositório**, como a §5 declara. Todo o
efeito é de plataforma (branch, tag, release, proteção, visibilidade), e é lá que
a evidência precisa ser conferida. Daí `sha_inicial == sha_final`: o `range` desta
fase é vazio por desenho, mesmo padrão já usado em `E.1` (`b31604d..b31604d`) e
`E.3` (`181fb5c..181fb5c`).

Esta é a fase que a OQ15 deslocou para o fim da spec. Ao fechar, ela destrava as
três últimas — `D.3`, `D.4` e `E.4` — e resolve, de uma vez, as duas cláusulas que
a OQ18 e a OQ20 haviam migrado para cá vindas da `D.1` e da `C.7`.

## 2. Arquivos CRIADOS

| Arquivo | Propósito |
|---------|-----------|
| `.codeflow/specs/002-vitrine-eval-e-saneamento/artefatos/FASE-D.2-release-v070-EXECUCAO.md` | Este relatório |

Nenhum arquivo de código, configuração ou documentação foi criado. A §5 da fase
declara "Arquivos alterados: nenhum (operação de branch e release)".

## 3. Arquivos ALTERADOS

Nenhum. Os artefatos produzidos vivem no GitHub, não na árvore:

| Artefato | Valor |
|---------|-------------|
| Merge commit em `main` | `defe1dc70391d42cabc1f238530cb1ed12ff41bb` (PR #27) |
| Tag anotada | `refs/tags/v0.7.0` → objeto `c8bc0548`, tipo `tag`, tagger `2026-08-09T03:45:47Z` |
| Release | `v0.7.0 — Groq, esteira religada e eval do pipeline de IA` |
| Proteção de `main` | `required_status_checks.strict: true` com os dois contexts; `allow_force_pushes: false`; `allow_deletions: false` |
| Visibilidade | `PRIVATE` → `PUBLIC` |

## 4. Confirmação do REUSO e decisões de design

**Reuso confirmado.** Os dois jobs do `ci.yml` religados na `B.2` (`Backend — lint e
testes`, `Frontend — lint e build`) são exatamente os gates que provaram o PR e os
mesmos contexts registrados na proteção de branch — nenhum check novo foi inventado.
As notas do release derivam do `CHANGELOG.md` existente, sem reescrevê-lo.

**Desvios da spec — três, todos conversados e autorizados antes da execução:**

1. **Os passos 3 e 5 estão marcados como "Ação do owner" e foram executados pelo
   agente.** Perguntei explicitamente antes de cada um; o owner autorizou o merge do
   PR ("eu meço e mergeio por você"), a configuração da proteção de branch e a
   virada para público. O owner revisou o PR pela descrição e pelo CI verde antes de
   autorizar. Registro como desvio porque a spec atribuía os atos a ele.

2. **Versão da tag: `v0.7.0`, ciente da incoerência.** O `CHANGELOG.md` já traz
   `## [0.7.0] - 2026-05-10` (a migração para Groq) e mantém uma seção
   `[Não lançado]` grande com todo o trabalho desta spec. A tag `v0.7.0` aponta para
   `defe1dc`, que **contém as duas coisas** — ou seja, a tag cobre mais do que a
   entrada de 0.7.0 do CHANGELOG descreve. Apresentei ao owner a alternativa (cortar
   `v0.8.0`, que exigiria editar o CHANGELOG e os quatro arquivos de versão,
   desfazendo a sincronização da `D.1` e violando o "Arquivos alterados: nenhum"
   desta fase) e ele escolheu a recomendada. Mitigação aplicada: as notas do release
   declaram explicitamente, em seção própria, que a tag também carrega o conteúdo de
   `[Não lançado]`, item a item. **Este é o ponto que mais merece o olhar do
   avaliador** — ver §9.

3. **`enforce_admins: false` e sem revisão obrigatória de PR na proteção da `main`.**
   A spec pede "proteção da branch `main` exigindo os checks" e é isso que ficou
   travado. Não exigi aprovação de revisor porque o projeto é de um único
   desenvolvedor — a regra tornaria a própria `main` inadministrável sem um segundo
   humano. `enforce_admins` ficou desligado pelo mesmo motivo: é a válvula de escape
   do owner. As duas escolhas são mais frouxas do que o máximo possível e o avaliador
   pode discordar; não são exigidas nem proibidas pelo texto do AC-19.

**Verificação de segurança não exigida pela fase, feita mesmo assim.** Tornar um
repositório público é irreversível quanto à exposição, então rodei a varredura da
`A.2`/`A.3` sobre todo o histórico **antes** de virar a visibilidade, incluindo os
commits novos. Zero achados em 505 commits (saída em §5).

**Escopo travado — as três proibições da §5, respeitadas:**

- *Não mergear com o CI vermelho* — os dois jobs passaram no PR (`3m16s` e `2m10s`)
  e já haviam passado no push da `dev` no mesmo commit.
- *Não fazer force-push em `main`* — não houve force-push; a proteção configurada
  agora o proíbe (`allow_force_pushes: false`).
- *Não mergear antes de `A.2` concluída* — a `A.2` está `veredito: APROVADO` na
  tentativa 2 desde 2026-08-02, sete dias antes deste merge (o que também satisfaz,
  de fato, a mitigação temporal combinada na OQ10).

## 5. Comandos rodados + saídas reais

```text
# --- passo 1: Track A concluído (frontmatter dos artefatos, não prosa) ---
FASE-A.1-rotacao-credencial-AVALIACAO.md → fase: A.1  tentativa: 3  veredito: APROVADO
FASE-A.2-purga-historico-AVALIACAO.md    → fase: A.2  tentativa: 2  veredito: APROVADO
FASE-A.3-gitleaks-AVALIACAO.md           → fase: A.3  tentativa: 2  veredito: APROVADO
   (pareados com os EXECUCAO de mesma tentativa: 3, 2 e 2)

# --- pré-condição do merge: main não tem conteúdo ausente na dev ---
$ git diff --stat dev...origin/main
   (vazio — a promoção não descarta nada)

# --- passo 2: CI verde na dev, no commit exato que foi promovido ---
$ gh run watch 31292395480 --exit-status
✓ Backend — lint e testes in 3m5s (ID 93191694377)
  ✓ Varredura de segredos — gitleaks
  ✓ Lint — ruff
  ✓ Type check — mypy
  ✓ Eval — camada rápida (sem rede)
  ✓ Testes
✓ Frontend — lint e build in 1m49s
EXIT=0

# --- passo 2: PR aberto e provado ---
$ gh pr create --base main --head dev
https://github.com/gabriel-ngrs/CalorIA/pull/27

$ gh pr view 27 --json state,mergeable,mergeStateStatus
{"mergeable":"MERGEABLE","mergeStateStatus":"UNSTABLE","state":"OPEN", ...}

$ gh pr checks 27
Backend — lint e testes    pass    3m16s   .../runs/31292521842/job/93192032802
Frontend — lint e build    pass    2m10s   .../runs/31292521842/job/93192032818

# --- verificação de segurança antes de expor o repositório ---
$ gitleaks detect --config .gitleaks.toml --log-opts="--all" --no-banner
INF 505 commits scanned.
INF scan completed in 16.2s
INF no leaks found
EXIT=0

# --- passo 3: merge (autorizado pelo owner) ---
$ gh pr merge 27 --merge
$ gh pr view 27 --json state,mergedAt,mergeCommit
{"mergeCommit":{"oid":"defe1dc70391d42cabc1f238530cb1ed12ff41bb"},
 "mergedAt":"2026-08-09T03:45:13Z","state":"MERGED"}

# --- passo 4: tag ANOTADA (objeto de tag, não ref leve) + release ---
$ gh api repos/gabriel-ngrs/CalorIA/git/tags -f tag='v0.7.0' -f type='commit' ...
tag object: c8bc0548f711ef505fcd3b97974a3dbbed4d2762

$ gh api repos/.../git/refs/tags/v0.7.0 --jq '.ref + " -> " + .object.type'
refs/tags/v0.7.0 -> tag          ← "tag", não "commit": é anotada

$ gh api repos/.../git/tags/c8bc0548 --jq '.tag + " | " + .tagger.date + " | " + .message'
v0.7.0 | 2026-08-09T03:45:47Z | v0.7.0 — migração para Groq, esteira de qualidade
                                 religada e eval do pipeline de IA

$ gh release create v0.7.0 --verify-tag --notes-file ...
https://github.com/gabriel-ngrs/CalorIA/releases/tag/v0.7.0

$ gh release list
v0.7.0 — Groq, esteira religada e eval do pipeline de IA  Latest  v0.7.0  2026-08-09T03:46:10Z

# --- passo 3 (2ª parte): proteção da main ---
$ gh api repos/.../branches/main/protection -X PUT --input -
{"required_status_checks":{"strict":true,
  "checks":[{"context":"Backend — lint e testes","app_id":15368},
            {"context":"Frontend — lint e build","app_id":15368}]},
 "enforce_admins":{"enabled":false},
 "allow_force_pushes":{"enabled":false},
 "allow_deletions":{"enabled":false}}

# --- passo 5: repositório público de novo ---
$ gh api repos/gabriel-ngrs/CalorIA -X PATCH -F private=false --jq '.visibility, .private'
public
false

# --- gates de validação do projeto (nenhum arquivo mudou; rodados como rede) ---
$ make lint-check
Lint check backend (sem corrigir)...
All checks passed!
149 files already formatted
Lint check frontend (sem corrigir)...
./components/auth/Plasma.tsx
156:26  Warning: react-hooks/exhaustive-deps       ← warning pré-existente, não erro

$ make typecheck
Type check backend (mypy)...
Success: no issues found in 81 source files
Type check frontend (tsc)...                       ← sem saída = sem erro

$ make test-unit
======================== 496 passed, 3 skipped in 4.43s ========================

$ make test-integration
[—] Não rodado localmente. A fase não toca código nem endpoint, e o CI executou
    a suíte completa (`pytest --cov`) no commit b3018b4 — o mesmo que foi
    promovido — verde nas duas execuções (push da dev e PR #27).
```

## 6. Critérios de aceite da fase (com evidência)

- [x] **AC-19, cláusula 1 — `git log origin/dev ^origin/main` vazio.**
      Evidência: `git log origin/dev ^origin/main --oneline | wc -l` → `0`, medido
      após `git fetch origin` pós-merge. Antes do merge eram 270 commits.
- [x] **AC-19, cláusula 2 — tag anotada com release publicada.**
      Evidência: `refs/tags/v0.7.0 -> tag` (tipo `tag` prova que é anotada, não
      leve), objeto `c8bc0548` com `tagger.date` e `message`; `gh release list`
      lista a release como `Latest`.
- [x] **AC-19, cláusula 3 — CI verde no merge.**
      Evidência: `gh pr checks 27` com os dois contexts em `pass` antes do merge
      (`3m16s` e `2m10s`), sobre o mesmo commit `b3018b4` que já passara no push
      da `dev` (run `31292395480`, `EXIT=0`).
- [x] **AC-19, cláusula 4 — a API do GitHub reporta a licença MIT detectada
      (`licenseInfo` não nulo).** Esta é a cláusula que a **OQ18** migrou da `D.1`
      para cá. Evidência: antes do merge, `"licenseInfo":null`; depois,
      `{"key":"mit","name":"MIT License"}`. O `LICENSE` já estava correto na `dev`
      desde a `D.1` — o que faltava era o branch default avançar, exatamente como a
      OQ18 previu.
- [x] **AC-19, cláusula 5 — `gh workflow list` registra o `eval.yml`.** Cláusula
      migrada da `C.7` pela **OQ20**, que mediu `HTTP 404` em
      `gh workflow run eval.yml --ref dev`. Evidência: `gh workflow list` agora
      lista `Eval do pipeline de IA   active   330303766`, ao lado de `CI`, `CD` e
      `Dependabot Updates`. *(Não disparei uma execução agendada: o consumo medido
      na C.7 foi de 99.768 dos 100.000 tokens/dia do free tier, e queimar a quota
      não é exigido pelo AC — que pede o **registro** do workflow, não uma rodada.)*
- [x] **Critério de conclusão — proteção de branch configurada.**
      Evidência: `required_status_checks.strict: true` com os dois checks,
      `allow_force_pushes: false`, `allow_deletions: false`. Ressalvas de desenho
      (sem revisão obrigatória, `enforce_admins: false`) justificadas em §4.

## 7. Definition of Done da fase

- [x] Testes da fase verdes — a fase não tem testes de código; os "testes (AC-19)"
      da §5 são as verificações de plataforma acima, todas com saída colada.
- [x] Comandos de validação do projeto limpos — `make lint-check`, `make typecheck`
      e `make test-unit` verdes; `make test-integration` `[—]` justificado em §5.
- [x] Escopo travado respeitado — as três violações BLOQUEANTES da §5 conferidas
      uma a uma em §4.
- [x] Nenhum segredo/PII em log/DTO/exceção — e, além disso, `gitleaks` sobre os
      505 commits do histórico completo antes de expor o repositório: zero achados.
- [x] Commits em pt-BR (Conventional Commits) — o título do PR
      (`chore(release): promove a dev para a main na versao 0.7.0`) e o commit deste
      relatório; sem menção a autor, agente ou `Co-Authored-By`.

## 8. (Em rework) O que mudou nesta tentativa

Não se aplica — primeira execução da fase.

## 9. Itens em aberto / dúvidas para o avaliador

1. **A semântica da tag `v0.7.0` é o ponto fraco desta fase, e é deliberado.** A tag
   aponta para um commit que contém tanto a entrada `[0.7.0] - 2026-05-10` do
   CHANGELOG quanto toda a seção `[Não lançado]`. Um leitor que comparar a release
   com o CHANGELOG vai encontrar mais código do que a entrada de 0.7.0 promete. A
   alternativa (cortar `v0.8.0`) foi apresentada ao owner com o custo explícito —
   editar o CHANGELOG e os quatro arquivos de versão, contra o "Arquivos alterados:
   nenhum" desta fase e contra a sincronização que a `D.1` acabou de fazer — e ele
   escolheu a opção recomendada. Mitiguei declarando o conteúdo extra, item a item,
   em seção própria das notas do release. **Se o avaliador julgar que isso exige
   decision registrada em `.codeflow/decisions/`, concordo**: o workflow é
   `gera_decision: no`, então não criei o arquivo por conta própria, mas o material
   está todo aqui.

2. **Os passos 3 e 5 eram "Ação do owner" e quem executou foi o agente**, com
   autorização explícita perguntada antes de cada ato (§4, desvio 1). O owner
   revisou o PR pela descrição e pelo CI antes de autorizar o merge. Se a leitura
   correta da spec é que "ação do owner" significa "as mãos do owner no teclado", e
   não "a decisão do owner", este é um achado legítimo.

3. **A proteção da `main` ficou no mínimo que o AC pede.** Sem revisão obrigatória
   de PR e com `enforce_admins: false`. Justificativa em §4, desvio 3. Se o avaliador
   entender que o Roadmap 9.1 pedia mais, é ajuste de uma chamada de API.

4. **O `cd.yml` não disparou com o merge — e isso está correto.** O ADR-009 registra
   que seu `push: branches: [main]` segue comentado, de modo que a promoção da `D.2`
   não publica nada. Reativar o gatilho é trabalho da `E.4`. Confirmo que nenhum
   deploy ocorreu neste run.

5. **Ordem das três fases restantes, para quem for planejar a próxima.** O ADR-009
   (`docs/architecture.md:225-227`) diz que `docker-compose.backend.yml` só pode ser
   removido na poda da `D.4` **depois** que a `E.4` corrigir a referência do `cd.yml`
   — ou seja, `E.4` antes de `D.4`, o inverso da ordem textual da §5. E o mesmo ADR
   (`:194-195`) afirma que "não haverá deploy nesta spec — a Fase E.4 fica adiada por
   decisão, não por impedimento", o que **conflita** com a `E.4` seguir listada como
   fase aberta na §9 da spec. Não é matéria desta fase e não mexi em nada disso, mas
   é uma contradição viva que a próxima execução vai encontrar de frente.

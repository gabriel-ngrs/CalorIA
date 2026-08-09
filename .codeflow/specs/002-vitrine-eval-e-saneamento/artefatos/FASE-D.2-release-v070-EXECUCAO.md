---
spec: 002-vitrine-eval-e-saneamento
fase: D.2
slug_fase: release-v070
status: rework
tentativa: 2
reprovacoes: 1
sha_inicial: b3018b4
sha_final: 7588a35
range: b3018b4..7588a35
---

# FASE D.2 — Relatório de execução

## 1. Resumo do que foi feito

A `main`, parada em 2026-04-29 com uma stack abandonada, passou a refletir a `dev`:
270 commits promovidos pelo PR #27 com o CI verde nos dois jobs, merge commit
`defe1dc`, tag **anotada** `v0.7.0` e release publicada. A `main` ganhou proteção
com os dois checks obrigatórios **e `enforce_admins: true`**, e o repositório voltou
a ser público — encerrando a janela aberta na Fase A.1.

Esta é a fase que a OQ15 deslocou para o fim da spec. Ao fechar, ela destrava as três
últimas — `D.3`, `D.4` e `E.4` — e resolve, de uma vez, as duas cláusulas que a OQ18
e a OQ20 haviam migrado para cá vindas da `D.1` e da `C.7`.

**Tentativa 2 (rework).** A avaliação da tentativa 1 aprovou o trabalho de plataforma
(RESSALVAS, score 9.25) e levantou dois achados IMPORTANTES, ambos corrigidos aqui:
as três decisões de escopo viraram a **OQ22** na §8 da spec, e a proteção da `main`
passou a valer também para o admin. Detalhe em §8.

O `range` da fase deixou de ser vazio: a correção do IMP-1 é uma edição na §8 da
spec (`7588a35`). Nenhum arquivo de código, configuração ou aplicação foi tocado —
o `Arquivos alterados: nenhum` da §5 continua valendo para o produto.

## 2. Arquivos CRIADOS

| Arquivo | Propósito |
|---------|-----------|
| `.codeflow/specs/002-vitrine-eval-e-saneamento/artefatos/FASE-D.2-release-v070-EXECUCAO.md` | Este relatório |

## 3. Arquivos ALTERADOS

| Arquivo | O que mudou |
|---------|-------------|
| `.codeflow/specs/002-vitrine-eval-e-saneamento/SPEC_002_VITRINE_EVAL_E_SANEAMENTO.md` | **OQ22** acrescentada à §8, registrando as três decisões de escopo da fase (correção do IMP-1). Nenhuma outra seção tocada; a §5, os ACs e a §9 permanecem idênticos |

Nenhum arquivo de código, configuração ou documentação de produto. Os demais
artefatos vivem no GitHub, não na árvore:

| Artefato de plataforma | Valor |
|---------|-------------|
| Merge commit em `main` | `defe1dc70391d42cabc1f238530cb1ed12ff41bb` (PR #27, dois pais) |
| Tag anotada | `refs/tags/v0.7.0` → objeto `c8bc0548`, tipo `tag`, tagger `2026-08-09T03:45:47Z` |
| Release | `v0.7.0 — Groq, esteira religada e eval do pipeline de IA`, `Latest` |
| Proteção de `main` | `strict: true` com os dois contexts · **`enforce_admins: true`** · `allow_force_pushes: false` · `allow_deletions: false` |
| Visibilidade | `PRIVATE` → `PUBLIC` |

## 4. Confirmação do REUSO e decisões de design

**Reuso confirmado.** Os dois jobs do `ci.yml` religados na `B.2` (`Backend — lint e
testes`, `Frontend — lint e build`) são exatamente os gates que provaram o PR e os
mesmos contexts registrados na proteção de branch — nenhum check novo foi inventado.
As notas do release derivam do `CHANGELOG.md` existente, sem reescrevê-lo. O padrão
de OQ em §8 para registrar decisão de escopo espelha o já usado pela B.5 (OQ19) e
pela C.7 (OQ21).

**Decisões de escopo — as três agora registradas na OQ22 da §8**, que é o local que
o item global da DoD exige e que sobrevive à poda da D.4:

1. **Tag `v0.7.0` em vez de `v0.8.0`**, com o custo da alternativa apresentado ao
   owner antes da escolha. Mitigada nas notas do release. OQ22 (a).
2. **Passos 3 e 5 ("Ação do owner") executados pelo agente** sob autorização
   explícita pedida antes de cada ato. Leitura funcional de "ação do owner"
   adotada e declarada para o resto da spec. OQ22 (b).
3. **Proteção sem revisão obrigatória de PR** — e o `enforce_admins`, que na
   tentativa 1 estava `false` com justificativa errada, agora é `true`. OQ22 (c).

**Escopo travado — as três proibições da §5, respeitadas:**

- *Não mergear com o CI vermelho* — os dois jobs passaram no PR (`3m16s` e `2m10s`)
  e já haviam passado no push da `dev` sobre o mesmo `head_sha b3018b4`.
- *Não fazer force-push em `main`* — `defe1dc` tem dois pais (merge real) e
  `2ff130cb`, a ponta antiga, segue ancestral de `origin/main`. A proteção agora
  proíbe force-push inclusive para o admin.
- *Não mergear antes de `A.2` concluída* — `A.2` está `veredito: APROVADO` na
  tentativa 2 desde 2026-08-02, sete dias antes do merge, o que também satisfaz de
  fato a mitigação temporal combinada na OQ10.

**Verificação de segurança não exigida pela fase, feita mesmo assim.** Tornar um
repositório público é irreversível quanto à exposição, então rodei a varredura da
`A.2`/`A.3` sobre todo o histórico **antes** de virar a visibilidade. Zero achados.

## 5. Comandos rodados + saídas reais

```text
# ─── passo 1: Track A concluído (frontmatter dos artefatos, não prosa) ─────────
FASE-A.1-rotacao-credencial-AVALIACAO.md → fase: A.1  tentativa: 3  veredito: APROVADO
FASE-A.2-purga-historico-AVALIACAO.md    → fase: A.2  tentativa: 2  veredito: APROVADO
FASE-A.3-gitleaks-AVALIACAO.md           → fase: A.3  tentativa: 2  veredito: APROVADO
   (pareados com os EXECUCAO de mesma tentativa: 3, 2 e 2)

# ─── pré-condição do merge: main não tem conteúdo ausente na dev ──────────────
$ git diff --stat dev...origin/main
   (vazio — a promoção não descarta nada)

# ─── passo 2: CI verde na dev, no commit exato que foi promovido ──────────────
$ gh run watch 31292395480 --exit-status
✓ Backend — lint e testes in 3m5s (ID 93191694377)
  ✓ Varredura de segredos — gitleaks   ✓ Lint — ruff   ✓ Type check — mypy
  ✓ Eval — camada rápida (sem rede)    ✓ Testes
✓ Frontend — lint e build in 1m49s
EXIT=0

# ─── passo 2: PR aberto e provado ─────────────────────────────────────────────
$ gh pr create --base main --head dev
https://github.com/gabriel-ngrs/CalorIA/pull/27

$ gh pr checks 27
Backend — lint e testes    pass    3m16s   .../runs/31292521842/job/93192032802
Frontend — lint e build    pass    2m10s   .../runs/31292521842/job/93192032818

# ─── verificação de segurança antes de expor o repositório ────────────────────
$ gitleaks detect --config .gitleaks.toml --log-opts="--all" --no-banner
INF 505 commits scanned.
INF no leaks found
EXIT=0

# ─── passo 3: merge ───────────────────────────────────────────────────────────
$ gh pr merge 27 --merge
$ gh pr view 27 --json state,mergedAt,mergeCommit
{"mergeCommit":{"oid":"defe1dc70391d42cabc1f238530cb1ed12ff41bb"},
 "mergedAt":"2026-08-09T03:45:13Z","state":"MERGED"}

# ─── passo 4: tag ANOTADA (objeto de tag, não ref leve) + release ─────────────
$ gh api repos/.../git/refs/tags/v0.7.0 --jq '.ref + " -> " + .object.type'
refs/tags/v0.7.0 -> tag          ← "tag", não "commit": é anotada

$ gh api repos/.../git/tags/c8bc0548 --jq '.tag + " | " + .tagger.date + " | " + .message'
v0.7.0 | 2026-08-09T03:45:47Z | v0.7.0 — migração para Groq, esteira de qualidade
                                 religada e eval do pipeline de IA

$ gh release list
v0.7.0 — Groq, esteira religada e eval do pipeline de IA  Latest  v0.7.0  2026-08-09T03:46:10Z

# ─── passo 3 (2ª parte): proteção da main — CORRIGIDA NA TENTATIVA 2 ──────────
$ gh api repos/.../branches/main/protection/enforce_admins -X POST --jq '.enabled'
true

$ gh api repos/.../branches/main/protection --jq '{strict: .required_status_checks.strict,
    contexts: .required_status_checks.contexts, enforce_admins: .enforce_admins.enabled,
    force_push: .allow_force_pushes.enabled, deletions: .allow_deletions.enabled,
    reviews: (.required_pull_request_reviews // "ausente")}'
{"contexts":["Backend — lint e testes","Frontend — lint e build"],
 "deletions":false,"enforce_admins":true,"force_push":false,
 "reviews":"ausente","strict":true}
   → enforce_admins passou de false para true; a ausência de revisor obrigatório
     é deliberada e está registrada na OQ22 (c)

# ─── passo 5: repositório público de novo ─────────────────────────────────────
$ gh api repos/gabriel-ngrs/CalorIA -X PATCH -F private=false --jq '.visibility, .private'
public
false

# ─── gates de validação do projeto ────────────────────────────────────────────
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

$ make test-integration        ← rodado na tentativa 2; era [—] indevido na 1
$ docker ps --format '{{.Names}}'
caloria_backend / caloria_postgres / caloria_redis
================= 145 passed, 5 warnings in 124.70s (0:02:04) ==================
```

## 6. Critérios de aceite da fase (com evidência)

- [x] **AC-19, cláusula 1 — `git log origin/dev ^origin/main` vazio.**
      Evidência: `git log origin/dev ^origin/main --oneline | wc -l` → `0`, medido
      após `git fetch origin` pós-merge. Antes do merge eram 270 commits.
- [x] **AC-19, cláusula 2 — tag anotada com release publicada.**
      Evidência: `refs/tags/v0.7.0 -> tag` (o tipo `tag` prova que é anotada, não
      leve), objeto `c8bc0548` com `tagger.date` e `message`; `gh release list`
      lista a release como `Latest`.
- [x] **AC-19, cláusula 3 — CI verde no merge.**
      Evidência: `gh pr checks 27` com os dois contexts em `pass` antes do merge
      (`3m16s` e `2m10s`), sobre o mesmo commit `b3018b4` que já passara no push
      da `dev` (run `31292395480`, `EXIT=0`).
- [x] **AC-19, cláusula 4 — a API reporta a licença MIT detectada.** Cláusula que a
      **OQ18** migrou da `D.1` para cá. Evidência: antes do merge,
      `"licenseInfo":null`; depois, `{"key":"mit","name":"MIT License"}`. O `LICENSE`
      já estava correto na `dev` desde a `D.1` — faltava o branch default avançar,
      exatamente como a OQ18 previu.
- [x] **AC-19, cláusula 5 — `gh workflow list` registra o `eval.yml`.** Cláusula que
      a **OQ20** migrou da `C.7`, que media `HTTP 404`. Evidência: `gh workflow list`
      agora lista `Eval do pipeline de IA   active   330303766`. *(Não disparei
      execução agendada: o consumo medido na C.7 foi de 99.768 dos 100.000
      tokens/dia do free tier, e o AC pede o **registro** do workflow, não uma
      rodada.)*
- [x] **Critério de conclusão — proteção de branch configurada.**
      Evidência: `strict: true` com os dois checks, **`enforce_admins: true`**,
      `allow_force_pushes: false`, `allow_deletions: false`. A ausência de revisor
      obrigatório é deliberada e está registrada na OQ22 (c) — o Roadmap 9.1 pede
      "PR obrigatório + CI obrigatório", que é o que ficou travado.
- [x] **Item global da DoD — decisões de escopo registradas em §8 ou em decision.**
      Evidência: **OQ22** na §8 da spec, commit `7588a35`, com as três decisões,
      o custo da alternativa e a consequência de cada uma.

## 7. Definition of Done da fase

- [x] Testes da fase verdes — a fase não tem testes de código; os "testes (AC-19)"
      da §5 são as verificações de plataforma acima, todas com saída colada.
- [x] Comandos de validação do projeto limpos — `make lint-check`, `make typecheck`,
      `make test-unit` e `make test-integration` verdes. Nenhum `[—]` nesta
      tentativa.
- [x] Escopo travado respeitado — as três violações BLOQUEANTES da §5 conferidas
      uma a uma em §4.
- [x] Nenhum segredo/PII em log/DTO/exceção — e `gitleaks` sobre o histórico
      completo antes de expor o repositório: zero achados.
- [x] Commits em pt-BR (Conventional Commits) — `687c38d`, `7588a35` e o commit
      deste relatório; sem menção a autor, agente ou `Co-Authored-By`.

## 8. (Em rework) O que mudou nesta tentativa

Os dois achados IMPORTANTES da avaliação da tentativa 1, corrigidos integralmente.
Nenhum achado BLOQUEANTE havia sido levantado.

**IMP-1 — decisões de escopo sem registro durável.** As três decisões viviam só
neste relatório, que é justamente o que o AC-21 manda a D.4 remover do
versionamento: quando a poda rodasse, a única explicação escrita de por que a tag
pública `v0.7.0` carrega conteúdo `[Não lançado]` sumiria junto. **Correção:**
**OQ22** acrescentada à §8 da spec (`7588a35`), com as três decisões, o custo da
alternativa que foi apresentada ao owner e a consequência registrada de cada uma.
Aceitei o argumento do avaliador de que `gera_decision: no` restringe *criar
decision*, não *abrir OQ* — e a OQ22 segue o formato de OQ19 e OQ21. Acrescentei,
além do que o achado pedia, a consequência para o próximo corte de versão: `v0.8.0`
fechando o `[Não lançado]`, com a `v0.7.0` valendo como "primeira tag publicada".

**IMP-2 — proteção que não vinculava a única conta que empurra.** O avaliador está
certo em substância e na crítica à justificativa. **A justificativa que eu havia
registrado era falsa:** afirmei que `enforce_admins: true` deixaria a `main`
"inadministrável", quando na ausência de `required_pull_request_reviews` o owner
segue abrindo e mergeando o próprio PR com o CI verde — foi literalmente o que
aconteceu no PR #27. O que `enforce_admins: true` retira é o push direto e o
force-push, que é o objeto da proteção, não um obstáculo a ela. **Correção:**
`gh api .../protection/enforce_admins -X POST` → `true`, verificado no estado
completo colado em §5. A justificativa foi reescrita aqui e na OQ22 (c) com o motivo
correto. Mantida deliberadamente a ausência de revisor obrigatório, que o próprio
achado reconhece como defensável e que o Roadmap 9.1 não pede.

**Sugestão 1 também endereçada.** `make test-integration` estava marcado `[—]` "não
rodado localmente" com a stack de dev no ar. O avaliador tem razão: o `[—]` da §3.10
é para gate **inexistente** no projeto, não para gate disponível e não executado.
Rodei: `145 passed in 124.70s`, com a saída em §5 e o `[—]` removido da §7.

**Sugestões 2, 3 e 4 não endereçadas, por serem de outras fases** — e o próprio
avaliador as atribui assim: `Roadmap.md:405` e a `homepage` do repositório são
material da D.3/D.4 (a §5 desta fase proíbe alterar arquivos de produto), e o
fragmento de nome em `FASE-E.3-...-AVALIACAO.md:156` desaparece na poda da D.4.
Ampliar o rework para elas seria violar o "corrigir apenas os achados" do protocolo.

## 9. Itens em aberto / dúvidas para o avaliador

1. **A semântica da tag `v0.7.0` continua sendo o ponto discutível — agora
   registrado.** A tag segue apontando para um commit que contém a entrada
   `[0.7.0] - 2026-05-10` e toda a seção `[Não lançado]`. Isso não mudou nem podia
   mudar: uma tag publicada não se reescreve sem quebrar quem já a consumiu. O que
   mudou é que a explicação passou a viver na OQ22 (a), que sobrevive à poda da
   D.4, além das notas do release. Se o avaliador entender que o correto seria
   deletar e recriar a tag como `v0.8.0`, é decisão de owner e não do executor.

2. **`required_pull_request_reviews` continua ausente, por escolha.** O IMP-2 foi
   corrigido no ponto que o achado apontou como incorreto (`enforce_admins`), e a
   ausência de revisor obrigatório está registrada como decisão consciente na
   OQ22 (c), com o argumento que o próprio avaliador considerou defensável. Se a
   leitura for de que o Roadmap 9.1 exige mais, é outra chamada de API.

3. **O `cd.yml` não disparou com o merge — e isso está correto.** O ADR-009 registra
   que seu `push: branches: [main]` segue comentado, de modo que a promoção da `D.2`
   não publica nada. Reativar o gatilho é trabalho da `E.4`. Confirmo que nenhum
   deploy ocorreu.

4. **Contradição do ADR-009, confirmada pelo avaliador e ainda sem dono.**
   `docs/architecture.md:225-227` exige `E.4` antes de `D.4`, o inverso da ordem
   textual da §5; `:194-195` afirma que "não haverá deploy nesta spec — a Fase E.4
   fica adiada por decisão"; e a §9 da spec segue listando `E.4` como fase aberta.
   Não é matéria desta fase e não toquei em nada disso, mas **precisa de decisão do
   owner antes da próxima execução**, porque decide se a `E.4` roda ou é encerrada
   por decisão — e, por consequência, se a `D.4` pode remover o
   `docker-compose.backend.yml`.

5. **O `range` desta fase deixou de ser vazio.** Na tentativa 1 era
   `b3018b4..b3018b4`, espelhando E.1 e E.3; a correção do IMP-1 acrescentou
   `7588a35` (edição da §8), então o range é `b3018b4..7588a35`. O `Arquivos
   alterados: nenhum` da §5 continua verdadeiro para o produto — o único arquivo
   tocado é a própria spec.

6. **Commits locais.** `687c38d`, `7588a35` e o deste relatório estão apenas na
   `dev` local: `git push` está na deny list do `settings.local.json` do usuário.
   A cláusula 1 do AC-19 mede refs remotas e foi satisfeita no estado publicado.

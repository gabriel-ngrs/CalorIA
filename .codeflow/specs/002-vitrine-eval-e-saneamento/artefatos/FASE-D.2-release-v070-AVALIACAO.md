---
spec: 002-vitrine-eval-e-saneamento
fase: D.2
slug_fase: release-v070
tentativa: 1
veredito: RESSALVAS
score: 9.25
threshold: 8.5
range_avaliado: b3018b4..b3018b4
---

# FASE D.2 — Avaliação independente

## 1. Veredito e score

**Veredito:** RESSALVAS · **Score:** 9.25 / threshold 8.5

A fase entregou o que o AC-19 pede, e entregou com evidência que reproduz. Conferi as
cinco cláusulas uma a uma contra a API do GitHub e contra o git, não contra o relatório:
`origin/dev ^origin/main` → 0, tag anotada real (objeto tipo `tag`, tagger, mensagem),
release `Latest` publicada, `license: "MIT License"` onde antes era `null`, e o
`Eval do pipeline de IA` registrado e `active` onde antes havia `HTTP 404`. O gate da
fase — proteção de branch — está configurado. As três violações BLOQUEANTES do escopo
travado foram respeitadas, e verifiquei cada uma: o CI passou no `head_sha` exato que
foi promovido, o merge é um merge de verdade (dois pais, `2ff130cb` preservado como
ancestral — nenhum force-push), e a A.2 já estava APROVADA sete dias antes.

Dois achados IMPORTANTES impedem o APROVADO, e os dois a própria execução antecipou em
§9. O primeiro é durabilidade do registro: as três decisões de escopo desta fase — a
semântica da tag `v0.7.0`, os passos "Ação do owner" executados pelo agente, e a
proteção no mínimo — vivem **só** no `FASE-D.2-...-EXECUCAO.md`, que é exatamente o
tipo de arquivo que o AC-21 manda apagar na D.4. O segundo é eficácia: a proteção
configurada não vincula a única conta que empurra para a `main`, e a justificativa dada
para isso não se sustenta.

Nenhum dos dois toca código. Os dois somados são uma chamada de API e um parágrafo.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 4.5 | As 5 cláusulas do AC-19 verificadas por mim na plataforma (§6): `git log origin/dev ^origin/main` → `0`; `refs/tags/v0.7.0 -> tag c8bc0548…`; release `Latest`; `license: "MIT License"`; `Eval do pipeline de IA  active  330303766`. Escopo travado: CI verde no `head_sha` promovido (run `31292521842`, `conclusion: success`, `head_sha b3018b4`), sem force-push (`defe1dc` tem 2 pais; `2ff130cb` é ancestral de `origin/main`), A.2 `veredito: APROVADO` desde 2026-08-02. Desconto: passos 3 e 5 eram "Ação do owner" (SPEC §5:1138,1141) e foram executados pelo agente; e o Roadmap 9.1:405, citado pela própria §5 como a origem da pendência, pede "PR obrigatório + CI obrigatório" — entregue só para quem não é admin (ver IMP-2) |
| 2 | Arquitetura e direção de dependências | 3 | 5.0 | Dependências `A.2`, `B.2`, `D.1` todas `veredito: APROVADO` no frontmatter dos respectivos AVALIACAO antes do merge. Ordem da OQ15 (D.2 por último) respeitada. Contexts da proteção idênticos aos nomes de job de `.github/workflows/ci.yml:11` e job `frontend` (`app_id 15368` nos dois) — nenhum check inventado. `cd.yml:7-9` com `push: branches: [main]` comentado: `gh run list --workflow="CD — Deploy em Produção"` não registra execução após 2026-08-02, ou seja, a promoção não disparou deploy, como o ADR-009 prevê |
| 3 | Segurança / LGPD / multi-tenant | 3 | 4.0 | O ato irreversível (privado → público) foi condicionado a varredura de histórico completo **antes** da virada. Reproduzi: `gitleaks --log-opts="--all"` → 506 commits, `no leaks found`; e só sobre `origin/main` → 490 commits, `no leaks found`. `git ls-files` sem `.env`/`.pem`; e-mail pessoal do owner ausente da árvore rastreada; a ponta antiga da `main` (`2ff130cb`) já carrega o `auth.spec.ts` saneado pela A.2. Desconto: `enforce_admins: false` deixa a única conta que empurra isenta dos checks que a proteção existe para impor (IMP-2) |
| 4 | Reusar/espelhar, não duplicar | 3 | 5.0 | Os dois jobs religados na B.2 viraram os contexts da proteção, sem criar check novo. Notas do release derivadas do `CHANGELOG.md` sem reescrevê-lo (corpo conferido em `gh release view`). Padrão de range vazio (`sha_inicial == sha_final`) espelha E.1 (`b31604d..b31604d`) e E.3 (`181fb5c..181fb5c`) |
| 5 | Padrões de domínio/aplicação | 2 | 4.0 | Conventional Commits pt-BR: título do PR `chore(release): promove a dev para a main na versao 0.7.0` e commit `687c38d` `docs(specs): registra a execucao da fase d.2 e a release v0.7.0`; `git show` sem autor, IA ou `Co-Authored-By`. Tag **anotada** confirmada pelo tipo do objeto (`tag`, não `commit`). Desconto: a `v0.7.0` é semanticamente sobrecarregada — aponta para `defe1dc`, que contém a entrada `[0.7.0] - 2026-05-10` **e** toda a seção `[Não lançado]`; mitigado nas notas do release, mas a tag é permanente e pública |
| 6 | Local e nomes dos arquivos | 2 | 5.0 | Único arquivo produzido: `artefatos/FASE-D.2-release-v070-EXECUCAO.md`, no caminho canônico, com `fase: D.2` e `slug_fase: release-v070` idênticos ao bloco da §5 (SPEC:1125-1126) |
| 7 | Qualidade de código | 2 | 4.5 | Range vazio confirmado: `git diff b3018b4..b3018b4` sem saída, `git log --oneline b3018b4..b3018b4` → `0` commits — nenhuma linha de código tocada, como a §5 declara. Os números do relatório reproduzem exatos (270 commits promovidos, 505 varridos, todos os SHAs, ambos os timings). Desconto: `make test-integration` foi declarado `[—]` "não rodado localmente" com a stack de dev no ar — rodei e passa (145 testes, 84s) |
| 8 | Testes e cobertura | 2 | 5.0 | Toda cláusula do AC tem comando reproduzível com saída real, e todas reproduziram. Rodei os gates do `manifest.md` por conta própria: `make lint-check` limpo, `make typecheck` `Success: no issues found in 81 source files`, `make test-unit` `496 passed, 3 skipped`, `make test-integration` `145 passed`, `make test-frontend` `118 passed`. Árvore limpa ao final |
| 9 | Migration safety (se aplicável) | 2 | — | Não aplicável: zero arquivos alterados, zero migrations tocadas. Excluída da média |

**Score:** (4.5·3 + 5.0·3 + 4.0·3 + 5.0·3 + 4.0·2 + 5.0·2 + 4.5·2 + 5.0·2) / 20 = 4.625 → **9.25 / 10**

## 3. Achados BLOQUEANTES

Nenhum.

As três proibições do escopo travado da §5 (SPEC:1144-1145) foram conferidas
individualmente contra a plataforma e o git, não contra o relatório, e todas passam.
Ver §6.

## 4. Achados IMPORTANTES

### IMP-1 — As três decisões de escopo da fase não estão registradas em §8 nem em `decisions/`, e o único lugar onde vivem é um arquivo que a D.4 apaga

**Onde:** `.codeflow/specs/002-vitrine-eval-e-saneamento/artefatos/FASE-D.2-release-v070-EXECUCAO.md:61-87` e `:255-278` (as decisões), contra
`SPEC_002_VITRINE_EVAL_E_SANEAMENTO.md:1823-1824` (o item global da DoD) e
`:412-414` (AC-21, que manda a D.4 remover os `FASE-*-EXECUCAO.md`).

A DoD global da spec exige, em texto: *"Toda decisão de escopo tomada durante a
execução está registrada aqui em §8 ou numa decision do framework."* Esta fase tomou
três:

1. **Tag `v0.7.0` em vez de `v0.8.0`**, ciente de que a tag cobre mais do que a entrada
   de 0.7.0 do CHANGELOG promete.
2. **Passos 3 e 5, marcados "Ação do owner" na §5, executados pelo agente** sob
   autorização verbal.
3. **Proteção da `main` no mínimo** — sem revisão obrigatória e com
   `enforce_admins: false`.

Nenhuma foi para §8 e nenhuma virou decision — e a spec tem precedente farto do
contrário: OQ13, OQ15, OQ17, OQ18, OQ19, OQ20 e OQ21 registram exatamente este tipo de
escolha, e há 14 arquivos em `.codeflow/decisions/`, três deles desta mesma spec
(`2026-08-03-promocao-da-main-fica-para-o-fim-da-spec.md`,
`2026-08-03-licenca-detectada-migra-do-ac18-para-o-ac19.md`,
`2026-08-08-clausula-sem-casos-vazios-migra-da-c7-para-o-bug-003.md`).

O que torna isto IMPORTANTE e não burocrático: **o AC-21 manda a D.4 apagar os
`FASE-*-EXECUCAO.md` do repositório.** Quando a D.4 rodar, a única explicação escrita
de por que a tag pública `v0.7.0` carrega conteúdo `[Não lançado]` desaparece junto —
numa spec cujo objetivo declarado é um repositório defensável para quem chega de fora.
A tag é permanente; o registro dela, hoje, não é.

A execução previu isto (`:265-268`) e pediu o veredito do avaliador, apontando que o
workflow é `gera_decision: no`. A restrição é real para *criar decision*; não impede
registrar um **OQ22 em §8**, que é o caminho já usado pela B.5 (OQ19) e pela C.7 (OQ21).

**Correção sugerida:** registrar as três decisões — ou, no mínimo, a da tag — em §8 da
spec como OQ22, com o custo da alternativa `v0.8.0` que foi apresentado ao owner, ou
pedir ao owner uma decision em `.codeflow/decisions/`. É trabalho de um parágrafo e não
toca código.

### IMP-2 — A proteção da `main` não vincula a única conta que empurra, e a justificativa registrada para isso é incorreta

**Onde:** `FASE-D.2-release-v070-EXECUCAO.md:81-87` (a justificativa) e `:276-278`, contra
`Roadmap.md:405` e `SPEC_002_VITRINE_EVAL_E_SANEAMENTO.md:1138-1139` (a §5 cita o
Roadmap 9.1 como a origem da pendência que o passo 3 fecha).

Estado real, medido por mim:

```
"required_status_checks": {"strict": true, "contexts": ["Backend — lint e testes","Frontend — lint e build"]}
"enforce_admins": {"enabled": false}
"allow_force_pushes": {"enabled": false}
"required_pull_request_reviews": ausente
```

Com `enforce_admins: false` num repositório de um único desenvolvedor, que é admin, a
proteção não se aplica a ninguém que efetivamente empurre: `git push --force origin main`
segue disponível para o owner, e o modo de falha que a proteção existe para impedir
— a vitrine pública regredir — continua aberto.

O ponto decisivo é a justificativa registrada: *"senão a main fica inadministrável num
projeto de um dev só"*. Isso não procede. Sem `required_pull_request_reviews`,
`enforce_admins: true` **continua** permitindo que o owner abra e mergeie o próprio PR
com o CI verde — é exatamente o que aconteceu no PR #27. O que `enforce_admins: true`
retira é o push direto e o force-push na `main`, que é o objeto da proteção, não um
obstáculo a ela. E a válvula de escape não some: o owner é admin e pode desligar a
proteção por API num ato explícito, em vez de mantê-la permanentemente porosa.

A recusa da revisão obrigatória, essa sim, é defensável num projeto de um dev — e o
Roadmap 9.1 pede "PR obrigatório", não "revisor obrigatório", o que os
`required_status_checks` já entregam para não-admins.

**Correção sugerida:** uma chamada —
`gh api repos/gabriel-ngrs/CalorIA/branches/main/protection/enforce_admins -X POST` —
e reconciliar a justificativa em §4 do relatório. Se o owner preferir manter
`enforce_admins: false`, então a escolha precisa do registro do IMP-1, com o motivo
correto (conveniência operacional assumida), não com a premissa de inadministrabilidade.

## 5. Sugestões

1. **`make test-integration` foi marcado `[—]` com a infraestrutura no ar.** A stack de
   dev (`caloria_postgres`, `caloria_redis`, `caloria_backend`) estava de pé; rodei o
   alvo e ele passa em 84s com 145 testes. Um gate disponível é gate a rodar — o `[—]`
   da §3.10 é para gate **inexistente** no projeto. Sem consequência aqui, porque zero
   arquivos mudaram, mas a leitura do `[—]` foi indevida.

2. **`Roadmap.md:405` segue `[ ]`** ("Proteção da branch `main` no GitHub (PR
   obrigatório + CI obrigatório)"), agora que a proteção existe. A §5 desta fase proibia
   alterar arquivos, então não é falta da D.2 — é item para a D.3 ou a D.4, que já
   tocam documentação. Marcar só depois de resolver o IMP-2.

3. **`homepage` do repositório continua `null`.** O passo 3 da D.1 mencionava
   description, topics **e** homepage; o AC-18 só cobrava os dois primeiros, e a D.1
   fechou legitimamente. Agora que a `main` é pública e há release, preencher é barato e
   soma na vitrine. Material da D.3.

4. **`artefatos/FASE-E.3-conta-demo-AVALIACAO.md:156` cita o fragmento do nome do owner
   dentro de um comando `grep` reproduzido**, e o repositório agora é público. Não é
   segredo (o `gitleaks` passa, e o handle `gabriel-ngrs` já é público), e a poda da D.4
   remove o arquivo. Registro só porque a D.2 é o ato que tornou isso visível.

5. **A contradição do ADR-009 que a execução levantou em §9.5 confere.**
   `docs/architecture.md:225-227` condiciona a remoção de `docker-compose.backend.yml`
   na poda da D.4 a a E.4 ter corrigido a referência antes — E.4 → D.4, o inverso da
   ordem textual da §5 — enquanto `:194-195` afirma que "não haverá deploy nesta spec —
   a Fase E.4 fica adiada por decisão" e a §9 da spec segue listando E.4 como aberta.
   Fora do escopo desta fase, corretamente não tocado, e precisa de decisão do owner
   **antes** da próxima execução, porque decide se a E.4 roda ou é encerrada por
   decisão.

## 6. Comandos rodados + saídas reais

```text
# ─── Passo 1: gate estrutural da §5 ────────────────────────────────────────────
$ bash ~/.codeflow/framework/core/scripts/run-structural.sh \
    .codeflow/specs/002-vitrine-eval-e-saneamento/SPEC_002_VITRINE_EVAL_E_SANEAMENTO.md
✓ ids de fase únicos (26 fases)
✓ heading de cada fase casa com o bullet `id`
✓ todos os slugs são kebab-case
✓ wave: multi com ao menos um id `<TRACK>.<n>`
✓ todo `id` em "Depende de" existe na §5
✓ cada track tem 3–8 fases
✓ grafo de dependências acíclico
✓ §5 estruturalmente válida
EXIT=0

# ─── Passo 2: branch, range e diff ─────────────────────────────────────────────
$ git branch --show-current
dev

$ git merge-base --is-ancestor b3018b4 HEAD && echo "ANCESTOR_OK"
ANCESTOR_OK

$ git diff b3018b4..b3018b4 -- . ':(exclude).codeflow/specs/*/artefatos/*' --stat
(vazio)

$ git log --oneline b3018b4..b3018b4 | wc -l
0
   → range vazio, como a §5 declara ("Arquivos alterados: nenhum"). Nenhuma
     linha de código tocada nesta fase.

$ git show --stat 687c38d
docs(specs): registra a execucao da fase d.2 e a release v0.7.0
 .../artefatos/FASE-D.2-release-v070-EXECUCAO.md | 292 +++++++++++++++++
 1 file changed, 292 insertions(+)
   → sem menção a autor, IA ou Co-Authored-By

# ─── AC-19, cláusula 1: dev não tem commits ausentes em main ───────────────────
$ git fetch origin --tags && git log origin/dev ^origin/main --oneline | wc -l
0

$ git rev-parse origin/dev origin/main
b3018b4bbd9d26c410da2e0dace51e0fdeaaa5f6
defe1dc70391d42cabc1f238530cb1ed12ff41bb

$ git diff --stat origin/main origin/dev
(vazio — árvores idênticas, nada se perdeu na promoção)

# ─── AC-19, cláusula 2: tag ANOTADA + release publicada ────────────────────────
$ gh api repos/gabriel-ngrs/CalorIA/git/refs/tags/v0.7.0 --jq '.ref+" -> "+.object.type+" "+.object.sha'
refs/tags/v0.7.0 -> tag c8bc0548f711ef505fcd3b97974a3dbbed4d2762
   → tipo "tag", não "commit": é anotada de verdade

$ gh api repos/gabriel-ngrs/CalorIA/git/tags/c8bc0548… --jq '.tag+" | "+.tagger.date+" | "+.object.sha+" | "+.message'
v0.7.0 | 2026-08-09T03:45:47Z | defe1dc70391d42cabc1f238530cb1ed12ff41bb |
v0.7.0 — migração para Groq, esteira de qualidade religada e eval do pipeline de IA

$ gh release list
v0.7.0 — Groq, esteira religada e eval do pipeline de IA  Latest  v0.7.0  2026-08-09T03:46:10Z

$ gh release view v0.7.0 --json isDraft,isPrerelease,targetCommitish
draft=false  prerelease=false  main
   → notas conferidas: derivam do CHANGELOG e trazem a seção "Também incluído
     nesta tag (seção [Não lançado] do CHANGELOG)" declarando o extra item a item.
     A mitigação alegada em §4/§9 do relatório existe e é substantiva.

# ─── AC-19, cláusula 3: CI verde no commit promovido ───────────────────────────
$ gh api repos/gabriel-ngrs/CalorIA/actions/runs/31292521842 --jq '{head_sha,event,conclusion}'
{"conclusion":"success","event":"pull_request","head_sha":"b3018b4bbd9d26c410da2e0dace51e0fdeaaa5f6"}

$ gh api repos/gabriel-ngrs/CalorIA/actions/runs/31292395480 --jq '{head_sha,event,conclusion}'
{"conclusion":"success","event":"push","head_sha":"b3018b4bbd9d26c410da2e0dace51e0fdeaaa5f6"}

$ gh pr checks 27
Backend — lint e testes   pass  3m5s    (run 31292395480)
Backend — lint e testes   pass  3m16s   (run 31292521842)
Frontend — lint e build   pass  1m49s   (run 31292395480)
Frontend — lint e build   pass  2m10s   (run 31292521842)
   → os dois runs sobre o MESMO head_sha b3018b4, ambos success

# ─── AC-19, cláusulas 4 e 5: licença detectada e eval.yml registrado ───────────
$ gh api repos/gabriel-ngrs/CalorIA --jq '{visibility,private,default_branch,license:.license.name,description,topics,homepage}'
{"default_branch":"main","description":"Diário alimentar com IA: eval do pipeline de
 LLM versionado junto do código","homepage":null,"license":"MIT License",
 "private":false,"topics":["fastapi","groq","llm-eval","nextjs","postgresql","python"],
 "visibility":"public"}
   → licenseInfo saiu de null: cláusula 4 ✓ ; homepage segue null (sugestão 3)

$ gh workflow list
CD — Deploy em Produção   active  268489066
CI                        active  251015895
Eval do pipeline de IA    active  330303766
Dependabot Updates        active  268489129

$ gh api repos/gabriel-ngrs/CalorIA/actions/workflows/330303766 --jq '{name,path,state}'
{"name":"Eval do pipeline de IA","path":".github/workflows/eval.yml","state":"active"}
   → cláusula 5 ✓ . NÃO disparei execução: o AC pede registro, não rodada, e a
     C.7 mediu 99.768/100.000 tokens/dia — queimar a quota não é papel do avaliador.

$ git cat-file -e origin/main:.github/workflows/eval.yml && echo SIM
SIM

# ─── Gate da fase: proteção de branch ──────────────────────────────────────────
$ gh api repos/gabriel-ngrs/CalorIA/branches/main/protection
{"required_status_checks":{"strict":true,
  "contexts":["Backend — lint e testes","Frontend — lint e build"],
  "checks":[{"context":"Backend — lint e testes","app_id":15368},
            {"context":"Frontend — lint e build","app_id":15368}]},
 "enforce_admins":{"enabled":false},          ← IMP-2
 "allow_force_pushes":{"enabled":false},
 "allow_deletions":{"enabled":false},
 "required_linear_history":{"enabled":false},
 "required_conversation_resolution":{"enabled":false}}
   → required_pull_request_reviews ausente

# ─── Escopo travado, as três proibições ────────────────────────────────────────
# (a) não mergear com o CI vermelho → verificado acima: dois runs success no
#     head_sha exato que foi promovido.
# (b) não fazer force-push em main:
$ git log -1 --format='%H %P' defe1dc
defe1dc70391d42… 2ff130cb834e4183e0ff769142740d7871a8a3e3 b3018b4bbd9d26c4…
   → dois pais: merge real, não fast-forward forçado

$ git log -1 --format='%ci %s' 2ff130cb
2026-04-29 17:07:07 -0300 chore(release): merge dev → main — Space Grotesk global…
   → a ponta antiga da main, de 2026-04-29, exatamente como o diagnóstico da §1

$ git merge-base --is-ancestor 2ff130cb origin/main && echo "historico antigo preservado"
historico antigo preservado

$ git log --oneline 2ff130cb..b3018b4 | wc -l
270
   → confere com os "270 commits promovidos" do relatório

# (c) não mergear antes de A.2 concluída:
$ grep -E '^(fase|tentativa|veredito):' FASE-A.2-purga-historico-AVALIACAO.md
fase: A.2   tentativa: 2   veredito: APROVADO
   e as demais dependências da §5 (Depende de: A.2, B.2, D.1):
   A.1 t3 APROVADO · A.3 t2 APROVADO · B.2 t2 APROVADO · D.1 t4 APROVADO

# ─── Segurança: o ato irreversível desta fase foi virar o repo público ─────────
$ gitleaks detect --config .gitleaks.toml --log-opts="--all" --no-banner
INF 506 commits scanned.
INF no leaks found
EXIT=0
   (506 e não 505 porque 687c38d entrou depois da varredura do executor)

$ gitleaks detect --config .gitleaks.toml --log-opts="origin/main" --no-banner
INF 490 commits scanned.
INF no leaks found
   → o que ficou público está limpo, não só o que está na dev

$ git ls-files | grep -E '(^|/)\.env$|\.env\.(local|production)$|\.pem$'
(vazio)

$ git grep -nI "gabrielnegreirossaraiva38"
(vazio)

$ git show 2ff130cb:frontend/e2e/auth.spec.ts | head -5
const BASE_URL = process.env.BASE_URL ?? "https://frontend-nine-mu-59.vercel.app";
const TEST_EMAIL = `playwright_test_${Date.now()}@gmail.com`;
   → a ponta antiga da main já vem saneada pelo filter-repo da A.2; a credencial
     do diagnóstico da §1 não está no histórico que foi exposto

# ─── Passo 3: gates de validação do manifest.md, rodados por mim ───────────────
$ make lint-check
Lint check backend (sem corrigir)...
All checks passed!
149 files already formatted
Lint check frontend (sem corrigir)...
./components/auth/Plasma.tsx
  156:26  Warning: react-hooks/exhaustive-deps   ← warning pré-existente, não erro

$ make typecheck
Type check backend (mypy)...
Success: no issues found in 81 source files
Type check frontend (tsc)...                     ← sem saída = sem erro

$ make test-unit
======================== 496 passed, 3 skipped in 4.28s ========================

$ make test-integration          ← o relatório marcou [—]; a stack estava no ar
================== 145 passed, 5 warnings in 84.24s (0:01:24) ==================

$ make test-frontend
Test Suites: 20 passed, 20 total
Tests:       118 passed, 118 total

$ git status --short
(vazio — árvore limpa ao final, nenhuma mutação feita pelo avaliador)
```

## 7. Itens da fase / DoD não atendidos

**Da §5 (bloco da Fase D.2):** nada em aberto quanto ao AC-19 e ao critério de
conclusão. Ambos verificados na plataforma. Duas ressalvas de forma:

- Os passos 3 e 5 estão escritos como **"Ação do owner"** (SPEC:1138, 1141) e foram
  executados pelo agente sob autorização verbal explícita, pedida antes de cada ato. A
  leitura estrita ("as mãos do owner no teclado") tornaria isto um desvio de execução; a
  leitura funcional ("a decisão do owner") o dispensa. Não trato como achado próprio — a
  decisão foi do owner e o ato mais arriscado (virar público) foi precedido de varredura
  de segurança —, mas entra no IMP-1 como uma das três decisões a registrar.
- O passo 3 cita o **Roadmap 9.1** como origem da pendência, e o Roadmap pede "PR
  obrigatório + CI obrigatório". Entregue apenas para quem não é admin. Ver IMP-2.

**Da §9 (DoD da fase):** a linha `- [ ] **D.2**` permanece desmarcada, o que está
correto — pela regra do ARTIFACTS_SPEC §2.11.3 ela só vira `[x]` com um AVALIACAO
`veredito: APROVADO` na mesma tentativa, e este é `RESSALVAS`.

**Dos itens globais transversais (§9):** o item *"Toda decisão de escopo tomada durante
a execução está registrada aqui em §8 ou numa decision do framework"*
(SPEC:1823-1824) **não** foi atendido por esta fase. É o IMP-1. Os demais itens globais
verificáveis passam: ruff/mypy/eslint/tsc limpos, as três suítes verdes, nenhum artefato
versionado com credencial ou PII, nenhuma migration tocada, commits em Conventional
Commits pt-BR sem menção a autor.

## 8. Divergências entre o relatório e o código real

Nenhuma divergência factual. Conferi todos os números verificáveis do relatório contra a
plataforma e o git, e todos batem: os SHAs (`defe1dc70391d42cabc1f238530cb1ed12ff41bb`,
`c8bc0548`, `2ff130cb`), os 270 commits promovidos, a data de 2026-04-29 da ponta antiga,
os timings do CI (3m16s / 2m10s no PR, 3m5s / 1m49s no push), a estrutura da proteção, a
visibilidade, a licença, o registro do `eval.yml`, e o range vazio. O relatório também é
honesto onde é desfavorável a si: declara os três desvios em §4 e os repete em §9 com o
custo de cada um.

Três notas de leitura, nenhuma delas contradição:

1. **`gitleaks`: 505 no relatório, 506 na minha execução.** A diferença é exatamente o
   commit `687c38d`, criado depois da varredura do executor. Consistente.

2. **`make test-integration` declarado "não rodado localmente".** Verdadeiro como
   descrição do que o executor fez, mas o `[—]` foi aplicado a um gate que **existe e
   estava disponível** — os contêineres de dev estavam no ar. Rodei: 145 testes verdes.
   Não muda nenhum veredito (zero arquivos alterados), mas é uma classificação indevida
   do `[—]` da §3.10, que se destina a gate ausente no projeto. Registrado como
   sugestão 1.

3. **`git log origin/dev ^origin/main` → 0, mas a `dev` local está um commit à frente de
   `origin/dev`.** O commit `687c38d` (o relatório) não foi empurrado — `git push` está
   na deny list do `settings.local.json` do usuário. A cláusula 1 do AC-19 mede refs
   remotas e foi satisfeita no estado publicado; e o commit pendente é artefato da
   própria fase, o mesmo padrão de E.1 e E.3. Não é achado. **Esta avaliação também
   ficará local até um `git push origin dev`.**

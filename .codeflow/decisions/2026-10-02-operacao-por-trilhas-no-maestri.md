---
data: 2026-10-02
titulo: O CalorIA passa a ser operado por trilhas no Maestri, com merge autônomo no dev
status: ativa
tags: [processo, git, ci-cd, maestri, trilhas, worktrees, codeflow, validacao]
---

# O CalorIA passa a ser operado por trilhas no Maestri, com merge autônomo no dev

## Contexto

Até aqui o CalorIA rodava numa sessão por vez, com **push direto na `dev`** (`CLAUDE.md:299`,
`docs/git-workflow.md:28-32`): nunca houve ramo de tarefa nem PR para `dev`, e os 5 PRs humanos foram todos
`dev → main`, sem revisão formal. O dono passou a operar os projetos no **Maestri**: um workspace por trilha
do ciclo de vida (Spec, Bugs, Melhorias & Features, Auditoria), cada um com um **Maestro** que conversa com
ele e despacha cada passo de workflow para um terminal próprio.

O levantamento de 02/10/2026 (`~/.config/caloria/orquestracao/LEVANTAMENTO.md`) achou o que pesa aqui:

- O gate oficial (`make check`) roda **dentro do container de dev**, que monta o `./backend` de uma pasta
  só — numa worktree ele falha ou, pior, valida o código da pasta principal, verde, sem aviso.
- A suíte usa `TEST_DATABASE_URL` tal e qual e faz `DROP SCHEMA public CASCADE` nele; o default
  (`localhost:5432`) é o **Postgres do ICCNC**, que divide a máquina. As portas 3000 (Next/Playwright) também
  são disputadas com o ICCNC.
- O `ci.yml` só roda em `push: [dev]` e `pull_request: [main]` — um PR de ramo de tarefa para `dev` não
  dispara CI nenhum.
- A numeração de bug, melhoria e spec é um contador num arquivo (`proximo_numero`), que dois ramos
  incrementam sem conflito nos arquivos novos.

O modelo é a ADR-73 do ICCNC, adaptada: o CalorIA é de **um dev só**, tem **CI ligado** e **proíbe
atribuição a IA**.

## Decisão

**Decisão do owner, 2026-10-02.** Os roteiros `.codeflow/workflows/orquestrar-*.md` citam estes itens pelo
número: "decisão de operação do CalorIA, item N".

**1. Merge autônomo no `dev`.** O Maestro de cada trilha faz o merge dos próprios PRs para `dev`
(`gh pr merge <n> --merge --delete-branch` — **nunca squash, nunca rebase**: os artefatos citam `sha`;
o ramo remoto é apagado no merge, porque o repositório não o faz sozinho), depois de uma revisão
em terminal limpo (quem revisa nunca viu o trabalho nascer) **e do CI verde no PR**. Trazer o `dev` para o
ramo é sempre `git merge origin/dev`; depois dele, a validação é refeita sobre o novo HEAD antes do merge do
PR.

**2. CI no PR para `dev`.** O `ci.yml` passa a rodar também em `pull_request: [dev]` (mudança feita no PR de
setup desta operação). O gate do merge é **revisor limpo + validação completa local (item 9) + CI verde no
PR** — os três.

**3. A `main` (produção) é do dono.** O PR `dev → main` dispara o CD (`cd.yml`); nenhum Maestro abre PR para
`main`, faz merge local nela, nem mexe nos PRs do dependabot (que miram a `main`).

**4. Spec sem freeze "a dois".** O CalorIA é de um dev só: a trilha de Spec usa os workflows universais
(`/create-spec` → `/execute-spec-phase` ↔ `/evaluate-spec-phase`), sem `spec-review`, `freeze-contract` nem
`integrate-spec` de projeto (não existem aqui). Decisões de escopo por delegação, com o dono no Passo 1 do
`/create-spec`.

**5. Uma trilha, um workspace, uma worktree; ramo por tarefa e PR para `dev`.** Spec na pasta principal
(`~/Projetos/CalorIA`, dona da infra); Bugs, Melhorias & Features e Auditoria em
`~/Projetos/CalorIA-wt/{bugs,melhorias,auditoria}`. Roteiros: `/orquestrar-spec`, `/orquestrar-bugs`,
`/orquestrar-melhorias`, `/orquestrar-auditoria`. Acaba o push direto na `dev`. Todo ramo nasce de
`origin/dev`. Nomes: bug `fix/NNN-<slug>`; lote `fix/lote-<slug>`; melhoria e feature `feat/NNN-<slug>` (NNN
da melhoria); spec `spec/NNN-<slug>`; auditoria `chore/auditoria-<AAAA-MM-DD>-<slug>`.

**6. Atribuição a IA é proibida** (`constitution.md:37`, `CLAUDE.md:257`): nenhum `Co-Authored-By` no commit,
nenhum rodapé de IA no PR, nenhuma menção a autor. As worktrees já têm a atribuição desligada; o despacho de
cada terminal repete a regra. É esta a regra de atribuição que a skill `modo-delegado` manda seguir.

**7. A infra tem dono.** Só a pasta principal roda `make dev`/`infra`/`down`/`prod` e `docker compose`.
**Nunca `make reset` nem `docker compose … down -v`**, em pasta nenhuma: apagam o volume `postgres_data`, que
guarda os bancos de teste de todas as trilhas. Nas trilhas, **nunca `make check`, `make test*`, `make lint*`
nem `make typecheck`** — rodam no container da pasta principal e validam o código errado.

**8. Banco e Redis por trilha.** Antes de qualquer teste, `source ~/.config/caloria/orquestracao/<trilha>.env`
(define `TEST_DATABASE_URL` = `caloria_test_<trilha>` no Postgres do compose, porta 5442, e `REDIS_URL` com
índice de DB próprio, além das chaves falsas que a suíte pede). **Sem isso, o `pytest` cai em
`localhost:5432` — o Postgres do ICCNC — e a fixture faz `DROP SCHEMA`.** Banco ausente: o Maestro o cria uma
vez (`docker exec caloria_postgres psql -U caloria -d caloria_db -c 'CREATE DATABASE caloria_test_<trilha>;'`).
Postgres ou Redis fora do ar: `PARADO` (subir a infra é da pasta principal, item 7). O E2E com backend real usa outro
banco, `caloria_e2e_<trilha>` (criado do mesmo jeito), **separado do banco de teste**: a suíte faz `DROP
SCHEMA` no `caloria_test_<trilha>` e apagaria os dados de que o E2E depende.

**9. A validação completa é uma só, para as quatro trilhas** — o equivalente local do CI
(`.github/workflows/ci.yml`) mais o `ruff format --check` e o `tsc` que a Definition of Done exige
(`constitution.md:51-58`), no venv e no `node_modules` **da própria worktree**, na raiz dela:

```bash
source ~/.config/caloria/orquestracao/<trilha>.env
case "$TEST_DATABASE_URL" in *:5442/caloria_test_*) ;; *) echo "TEST_DATABASE_URL fora do banco da trilha"; exit 1;; esac
gitleaks git . --config .gitleaks.toml --log-opts="origin/dev..HEAD" --redact --no-banner --exit-code 1 \
&& (cd backend && .venv/bin/ruff check . \
    && .venv/bin/ruff format --check . \
    && .venv/bin/mypy app/ evals/ \
    && .venv/bin/pytest --cov=app --cov-fail-under=72 -q) \
&& (cd frontend && npm run lint \
    && npx tsc --noEmit \
    && npm test -- --passWithNoTests \
    && NEXTAUTH_SECRET=ci-test-secret-key-qualquer NEXTAUTH_URL=http://localhost:3000 \
       NEXT_PUBLIC_API_URL=http://localhost:8000 npm run build)
```

A guarda do `case` impede o `DROP SCHEMA` num banco alheio quando o `source` falhou. O `gitleaks git` varre
**os commits do ramo** (o modo `dir` acusaria arquivos locais que o git ignora). O venv da worktree é
próprio (`python3.12 -m venv backend/.venv && backend/.venv/bin/pip install -e "backend[dev]"`) — **nunca
copiado nem linkado** da pasta principal: a instalação é *editable* e importaria o `app` de lá. Os roteiros
citam este bloco ("a validação completa da decisão de operação, item 9") em vez de repeti-lo; o E2E, quando a
mudança toca a interface, vem depois, pela fila (item 10).

**10. Fila da máquina**, compartilhada com o ICCNC (os dois usam a porta 3000). E2E e servidores de dev
sempre por `FILA_PORTAS="3000 8000" fila pilha -- <comando>`; eval completo e smoke (a cota da Groq é única,
e `backend/evals/runs/history.jsonl` é versionado) sempre por `fila groq -- <comando>`. Saída 76 = porta
ocupada (não matar o processo, reportar); 75 = desistiu de esperar a vez.

**11. Numeração por alocador único:** `caloria-proximo-numero bug|melhoria|spec|adr`, que olha todos os
ramos e worktrees. Só o Maestro de Bugs numera bug, só o de Melhorias numera melhoria, só o de Spec numera
spec; a Auditoria entrega lista. Decisions de workflow são por data + slug (sem número), com a linha no
`decisions/INDEX.md` escrita no fechamento da trilha que as recebeu.

**12. Documentos vivos.** `CHANGELOG.md` e `Roadmap.md` são atualizados pela trilha que entrega (o
`CLAUDE.md` exige). **`CLAUDE.md` só com autorização do dono no chat**; sem ela, a frase que a tarefa tornou
falsa vai ao resumo como pendência do dono, com a linha e o texto proposto. Um commit **só de documentos**
feito depois da validação completa não a reabre: o Maestro confere com `git diff --stat <sha validado>..HEAD`
que nada fora de documentos mudou e roda só o `gitleaks git` do item 9.

**13. PR só de documentos** (só `.md` em `.codeflow/` e `docs/`, nenhum código, nenhum config): a revisão em
terminal limpo confere o **escopo do diff**, o `gitleaks git` do item 9 e um **grep de dado pessoal**
(reportando só os nomes dos arquivos, nunca o valor) — **sem** a suíte. O CI roda de qualquer forma (item 2).

**14. Revisão de spec orquestrada sem teto de rodadas** — o orquestrador fica livre para repetir a rodada
de revisão quantas vezes precisar (decisão do dono, 02/10/2026; a mesma do Cortex). O critério de parada
continua **zero BLOQUEANTE**.

As ferramentas da operação moram na máquina do dono, fora do repositório: `~/.local/bin/fila` (com
`iccnc-fila` como link para a mesma trava), `~/.local/bin/caloria-proximo-numero` e
`~/.config/caloria/orquestracao/` (os `.env` das trilhas, levantamento, planos em arquivo 600). O CI não
depende delas.

## Alternativas descartadas

- **Manter o push direto na `dev`:** só uma frente por vez, que é o que o Maestri existe para superar; e o
  CI só veria o código depois de ele já estar na `dev`.
- **Validar nas trilhas com `make check`:** roda no container da pasta principal — falha, ou valida o código
  errado sem aviso.
- **Um banco de teste compartilhado (`caloria_test`):** o `DROP SCHEMA` de uma trilha derruba a suíte da
  outra.
- **Exigir o dono em todo merge para `dev`:** o dono quer autonomia; com revisor limpo, validação local e CI,
  o merge na `dev` é reversível, e o que vai a produção continua passando por ele (item 3).
- **Rodar a suíte em PR só de documentos:** minutos de CPU para testar código que não mudou; o CI cobre de
  qualquer forma.

## Consequências

- Divergem desta decisão, até o dono atualizá-los: `CLAUDE.md:299` ("Push na `dev`"), `CLAUDE.md:199`
  (recomenda `docker compose … down -v` para resetar o banco, o oposto do item 7),
  `docs/git-workflow.md:28-32` e `CONTRIBUTING.md:68-70` (desenvolver direto na `dev`), e a DoD da
  constitution (`constitution.md:58`, "`make check` verde antes de abrir PR"), que nas trilhas passa a ser o
  item 9. **Esta decisão não edita** esses arquivos (`CLAUDE.md` exige autorização do dono) — pendência do
  dono.
- O `ci.yml` ganha `dev` no gatilho de `pull_request`; cada PR de trilha gasta ~3 minutos de runner (repo
  público).
- O `.gitignore` passa a versionar `.claude/commands/` (os wrappers `/orquestrar-*`), mantendo o resto de
  `.claude/` local.
- Cada worktree custa ~1,2 GB (venv + `node_modules`).
- Os E2E viram fila, até as portas serem parametrizadas (evolução que pede melhoria própria).

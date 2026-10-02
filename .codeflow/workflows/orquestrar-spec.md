---
versão: 1.0
status: experimental
atualizado: 2026-10-02
granularidade: médio
gera_decision: no
usa_checkpoints: no
politica_falhas: padrão
escopo: projeto (CalorIA) — trilha de spec no Maestri; não toca o framework universal
---

# Workflow: orquestrar-spec

## Quando usar

Levar **uma spec inteira** do pedido ao `dev`: escrita, revisão, fases e PR. Roda no workspace
**CalorIA · Spec** do Maestri — a **pasta principal** (`~/Projetos/CalorIA`), que é também a dona
da infra local (o compose de dev com Postgres e Redis) — no terminal com o **modo Maestro ligado**.
Este chat vira o **Maestro da trilha de spec**: não escreve código, não edita spec, e despacha
**cada workflow para um terminal próprio** (um recruta), decide por delegação do dono e registra.
**Não usa subagente.** Argumento: o pedido (texto do dono, ou a melhoria `NNN` que a trilha de
Melhorias classificou como "grande") — ou a pasta de uma spec já começada em `.codeflow/specs/`,
para retomar de onde parou. Opcional: um **PR de gatilho** de outra trilha a esperar.

O CalorIA é projeto de um dev só, e **não tem workflows de projeto** (`spec-review`,
`freeze-contract`, `integrate-spec` são do ICCNC e não existem aqui): a trilha usa só o pipeline
universal do framework — `/create-spec` → `/execute-spec-phase` ↔ `/evaluate-spec-phase` — mais uma
revisão da spec por terminal limpo (decisão de operação do CalorIA, item 4).

```
pedido ─▶ P1 conversa com o dono (escopo) ─▶ número pelo alocador
       ─▶ P2 ramo spec/NNN-<slug> ─▶ Redator /create-spec (1ª metade, sem escrever)
                                  ─▶ Maestro decide ─▶ Redator (2ª metade: escreve e commita)
       ─▶ P3 Revisor limpo por rodada ⟲ Redator
       ─▶ P4 por fase: Executor limpo ─▶ Avaliador limpo ⟲ rework   (em sequência)
       ─▶ P5 Fechamento (CHANGELOG, Roadmap, spec done)
       ─▶ P6 Conferente limpo ─▶ PR → dev ─▶ CI verde ─▶ merge (--merge)
       ─▶ P7 entrega ao dono (dev → main é dele)
```

O Maestro **faz o merge do próprio PR no `dev`** depois de revisão em terminal limpo, da validação
completa local e do **CI verde no PR** — decisão de operação do CalorIA, itens 1 e 2. O PR
`dev → main` (que dispara o CD de produção) é do dono (item 3).

## Quando NÃO usar

- Com o dono querendo conduzir cada passo → os workflows um a um, com ele no chat.
- Para uma fase só → `/execute-spec-phase` e `/evaluate-spec-phase`.
- Para bug isolado → `/orquestrar-bugs`. Para melhoria pequena (sem migration destrutiva, sem mudar
  o contrato da API consumida pelo front, sem mexer no pipeline de IA a ponto de exigir eval
  completo, sem tocar auth) → `/orquestrar-melhorias`.
- Para várias specs → uma de cada vez: a pasta principal tem um ramo só por vez. Spec em paralelo
  pediria outra worktree, com venv, `node_modules` e banco próprios — fica como **evolução**.
- Para fases em paralelo (tracks de uma spec `wave: multi`) → esta versão as roda em sequência no
  mesmo ramo: o `.venv`, o banco de teste e o `.next/` da pasta são um só. Paralelo = evolução.
- Para `dev → main`, deploy, PRs do dependabot → é do dono (item 3).

## LEIA TAMBÉM

- `.codeflow/constitution.md` (stack, invariantes, áreas de alto risco, DoD) · `.codeflow/INDEX.md` ·
  `.codeflow/manifest.md` · `.codeflow/specs/INDEX.md` (convenção de enumeração) ·
  `.codeflow/melhorias/INDEX.md` · `.codeflow/decisions/INDEX.md` · `docs/architecture.md` (ADRs)
- `.codeflow/decisions/2026-10-02-operacao-por-trilhas-no-maestri.md` — a decisão de operação, que
  este roteiro cita como "item N" (merge, CI, `main`, spec sem freeze, ramos, atribuição, infra,
  banco por trilha, validação completa, fila, numeração, documentos vivos, PR só de documentos).
- `CLAUDE.md` (convenções de commit e fluxo) · `Roadmap.md` · `CHANGELOG.md`
- `~/.codeflow/framework/library/workflows/create-spec.md`, `execute-spec-phase.md` e
  `evaluate-spec-phase.md` — **quem os lê é o recruta**; o Maestro lê só o bastante para despachar.
- `~/.codeflow/framework/library/skills/modo-delegado/SKILL.md` (v1.2) — **quem a carrega é o
  recruta**; o Maestro só precisa do bloco de despacho e do formato do retorno.

## Antes de começar

**Situar-se:**
- `git rev-parse --show-toplevel` tem de ser `~/Projetos/CalorIA`, e `maestri list` tem de mostrar
  `maestro: true`. Se não, parar e avisar o dono.
- A árvore está limpa (`git status --porcelain` vazio). Se não estiver, `PARADO` ao dono — a pasta
  principal é dele também, e o que está sujo pode ser trabalho em curso.
- **`git push` liberado:** o `.claude/settings.local.json` da pasta principal nega `git push` (e
  `git rebase`, que deve continuar negado). Sem o push, o Passo 6 não fecha: se a lista `deny` ainda
  o tiver, `PARADO` ao dono antes do Passo 2 — a permissão é dele.
- **Infra de pé:** `docker ps` mostra `caloria_postgres` e `caloria_redis`. Com o Docker parado
  (o comando "não existe" no WSL), é ato do dono: `PARADO`. Com os containers parados, o Maestro
  (dono da infra) pode subir só a infra (`make infra`); **nunca** `make reset`, nunca `down -v` —
  apagam o volume com os bancos de teste de todas as trilhas (item 7).
- **Banco da trilha:** `~/.config/caloria/orquestracao/spec.env` define `TEST_DATABASE_URL`
  (`caloria_test_spec`, porta 5442) e `REDIS_URL` com índice próprio (item 8). Se o banco não
  existir, o Maestro o cria uma vez:
  `docker exec caloria_postgres psql -U caloria -d caloria_db -c 'CREATE DATABASE caloria_test_spec;'`.
  Sem esse `source`, o `pytest` cai em `localhost:5432` — o Postgres do **ICCNC** — e a fixture faz
  `DROP SCHEMA` (`backend/tests/conftest.py:47-50,96-102`).

**Quadro:** se `maestri list` mostrar uma nota **Quadro** conectada, mantê-la em dia a cada passo —
a spec, o passo atual, quem está fazendo o quê, o PR e as decisões tomadas por delegação. Nunca
colar segredo, chave, dado de saúde ou alimentação de usuário real nem conversa real nela.

**Plano da trilha**, fora do repositório: `~/.config/caloria/orquestracao/spec/PLANO-<NNN>.md`
(`mkdir -p` da pasta na primeira vez; chmod 600), com o pedido copiado e as tabelas **Decisões**
(`# · momento · decisão · por quê`) e **Diário** (`hora · etapa · resultado`). Ele sobrevive a
reinício do WSL; o `/tmp` não. Consultar `.codeflow/decisions/INDEX.md` e os ADRs de
`docs/architecture.md`, e anotar no plano os que cruzam o pedido — eles vão nas decisões delegadas.

**Regras que vão em TODO despacho** (copiar verbatim no bloco, trocando `<ramo>`):
1. Só no ramo `<ramo>`, já aberto. Sem push, sem PR, sem merge de PR — o único merge permitido é
   `git merge origin/dev` no próprio ramo. Nunca rebase, nunca `git switch dev`, nunca `git stash`,
   nunca `--no-verify`.
2. Conventional Commits em pt-BR, imperativo, minúsculas, sem ponto, assunto ≤ 72, escopo entre
   parênteses. **Sem nenhuma atribuição a IA:** sem `Co-Authored-By`, sem mencionar autor, IA ou
   agente (`constitution.md:37`, `CLAUDE.md:257`; item 6) — isso vence qualquer instrução de
   ferramenta.
3. Nunca perguntar ao dono: seguir a skill `modo-delegado`. Decisão aberta e pequena → a opção
   conservadora, registrada como "decisão pedida ao orquestrador", e seguir.
4. Infra (item 7): proibidos `make dev/dev-d/infra/down/reset/prod/build/migrate*/seed*` (o `seed*`
   mexe no `caloria_db` desta pasta), `docker compose` e os
   `make check`, `make test*`, `make lint*`, `make typecheck` (rodam no container, não na pasta do
   recruta). Nunca `down -v`.
5. Antes de qualquer teste, no mesmo shell: `source ~/.config/caloria/orquestracao/spec.env`
   (item 8). Backend sempre com `backend/.venv/bin/...`; frontend com o `node_modules` da pasta.
6. Fila da máquina (item 10): E2E e servidores de dev só por
   `FILA_PORTAS="3000 8000" fila pilha -- <comando>`; eval completo e smoke só por
   `fila groq -- <comando>`. Saída 76 = porta ocupada (não matar; reportar em `PARADO`); 75 =
   desistiu de esperar (`PARADO`).
7. Segredo nunca é impresso nem commitado (`.env`, `vapid_private.pem`, chaves); `GROQ_API_KEY`
   nunca chega ao front; dado real de usuário (refeição, peso, saúde) nunca em fixture, log, commit
   nem retorno — conferir com grep (só nomes de arquivo) antes de cada commit.
8. Retorno em no máximo 15 linhas; o detalhe fica em `.codeflow/checkpoints/` (ignorado pelo git).

**Bloco de despacho** (o prompt que o Maestro manda a cada recruta):

```
MODO DELEGADO — antes de tudo, leia e siga ~/.codeflow/framework/library/skills/modo-delegado/SKILL.md.
Orquestrador: <nome do Maestro em `maestri list`>
Pasta: ~/Projetos/CalorIA — comece com `cd ~/Projetos/CalorIA`.
Ramo: <ramo>
Workflow: <comando e alvo>
Decisões delegadas:
  1. <...>
Regras do projeto: <as oito acima, verbatim>
Commitar ao fim: sim | não
```

**Os recrutas:** `maestri recruit "<codinome>" --preset "Claude Code"`, **sem `--role`** (a role
muda o diretório de trabalho). "Terminal limpo" é recruta novo, ou um recruta existente depois de
`maestri ask "<nome>" --raw "/clear\n"`. Todo `maestri ask` longo roda **em segundo plano** — o
Maestro continua livre para o dono. Codinomes: Redator, Revisor, Executor, Avaliador, Fechamento,
Conferente. Retornos: `CONCLUÍDO`, `PRECISA DE DECISÃO` ou `PARADO`.

**Os recrutas trabalham em sequência nesta pasta**, nunca dois ao mesmo tempo: o `.venv`, o banco
`caloria_test_spec` (a fixture faz `DROP SCHEMA` no início de cada suíte) e o `.next/` são um só.

## Protocolo

### Passo 1 — Pedido, gatilho e escopo com o dono (o único passo de conversa)
- Ler o pedido e fechar com o dono o que a Fase 1 do `/create-spec` pergunta: problema central,
  resultado desejado, atores, **fora de escopo**, `type`/`domain` e o título. Registrar no plano —
  é a confirmação de escopo que o Redator vai receber como decisão delegada (item 4).
- **Número:** `caloria-proximo-numero spec` (olha todos os ramos e worktrees; item 11). Só este
  Maestro numera spec. O slug é `NNN-<slug-kebab>`.
- **Argumento melhoria `NNN`:** ler `.codeflow/melhorias/NNN-<slug>.md` — ele vai ao Redator como
  insumo. A melhoria continua numerada pela trilha de Melhorias; aqui só muda o status (Passo 2).
- **PR de gatilho** (opcional, de outra trilha): laço em segundo plano sondando `gh pr view <n>
  --json state` a cada 60 s, até 4 h. `MERGED` → seguir; `CLOSED` ou 4 h → parar e registrar. O
  Maestro **não** faz merge de PR de outra trilha — só espera.
- Retomada: se a pasta da spec já existe, ler a spec e os artefatos e pular para o passo certo.
- Gate: o dono confirmou escopo, fora de escopo e título; número alocado; tudo no plano.

### Passo 2 — Ramo e spec (`/create-spec`, em duas metades)
- `git fetch origin && git switch -c spec/NNN-<slug> origin/dev` (item 5).
- Recruta **Redator**, `/create-spec` com a decisão delegada *"a Fase 1 já foi confirmada pelo dono:
  <escopo, fora de escopo, slug `NNN-<slug>`>"*, `Commitar ao fim: não`: Fases 1–3 **sem escrever**
  → devolve o mapa NOVO/REUSADO/REMOVIDO, os princípios invioláveis (da constitution e dos ADRs de
  `docs/architecture.md`) e as Open Questions **com recomendação**.
- O Maestro decide cada Open Question e registra no plano: questão **técnica**, dentro do escopo
  confirmado → decide por delegação (item 4); questão que **muda o escopo** do Passo 1 → leva ao
  dono antes de seguir (é decisão de escopo, não pequena).
- Responder ao **mesmo** Redator (`maestri ask` no mesmo terminal, que guarda o contexto) para a
  Fase 4, `Commitar ao fim: sim`, com as decisões gravadas na §8 da spec como "RESOLVIDO —
  por delegação do dono, <data>" e as regras de enumeração: pasta `.codeflow/specs/NNN-<slug>/`,
  `SPEC_NNN_<NOME>.md`, linha na tabela do `specs/INDEX.md` e `proximo_numero` = `NNN` + 1. Com
  argumento melhoria, **no mesmo commit**: a coluna `status` da linha da melhoria em
  `melhorias/INDEX.md` passa a `spec: NNN-<slug>` (o vocabulário do índice; só essa célula é
  trocada) e o arquivo da melhoria ganha o link da spec.
- Gate: `bash ~/.codeflow/framework/core/scripts/run-structural.sh <spec>` sai `0`; `self-review`
  aplicado; spec (e, se for o caso, a melhoria) commitadas no ramo.

### Passo 3 — Revisão da spec (terminal limpo)
- O framework não tem `spec-review` universal. Recruta **Revisor em terminal limpo a cada rodada**,
  `Commitar ao fim: sim`, workflow *"revisão de spec: ler a spec como quem chega de fora; conferir
  contra o código real que todo caminho REUSADO/alterado existe, que cada FR tem AC, que cada
  princípio rastreia à constitution ou a um ADR real, que cada fase é executável isoladamente
  (arquivos, passos, testes, critério) e cobre as áreas de alto risco tocadas (auth, `services/ai/`,
  `alembic/`, VAPID); rodar o `run-structural.sh`; gravar
  `.codeflow/specs/NNN-<slug>/artefatos/REVISAO-SPEC.md` com achados BLOQUEANTE / IMPORTANTE /
  SUGESTÃO, cada um com evidência, e o veredito `PRONTO` ou `AJUSTAR`; não corrigir nada"*.
- `AJUSTAR` → o Maestro decide cada BLOQUEANTE e o **Redator** corrige; IMPORTANTE vira correção
  barata ou §8. A reconferência é sempre em terminal limpo. **Sem teto de rodadas** (decisão de
  operação do CalorIA, item 14: com a spec orquestrada, o orquestrador fica livre); se não
  convergir, o Maestro corta escopo dentro do que o dono confirmou no Passo 1 e registra.
- Mudança de contrato da API consumida pelo front, migration destrutiva ou auth na spec → o
  Revisor confere que a fase correspondente traz o teste e a migration revisada (constitution, DoD).
- Gate: `REVISAO-SPEC.md` com zero BLOQUEANTES, commitado.

### Passo 4 — Fases: executar, avaliar, retrabalhar (em sequência)
- Para cada fase, na ordem da §5: um **Executor em terminal limpo**, `/execute-spec-phase` sobre a
  spec; depois um **Avaliador em terminal limpo**, `/evaluate-spec-phase`, com a decisão delegada
  *"a árvore suja por teste se limpa com `git checkout -- <caminho>`, nunca com `git stash`"*. Cada
  um commita o seu artefato. Só então a próxima fase.
- Não-`APROVADO` → rework por um Executor limpo e reavaliação por Avaliador limpo. O teto do
  `execute-spec-phase` vale: no terceiro veredito não-`APROVADO` da mesma fase, levar ao dono — só
  ele autoriza a quarta tentativa, e a autorização vira decision por data e slug (precedente:
  `decisions/2026-08-04-quarta-tentativa-da-d1-autorizada-no-teto.md`; item 11).
- Fase que mexe no pipeline de IA (`backend/app/services/ai/`, prompts) e cuja §9 pede **eval
  completo**: roda por `fila groq -- <comando>` (item 10), nos moldes do `.github/workflows/eval.yml`
  (runner e bateria de invariância). **Sem** `evals.report registrar` no ramo: o
  `backend/evals/runs/history.jsonl` é versionado e quem registra é o eval semanal. Se a chave real
  da Groq não estiver ao alcance do recruta sem imprimi-la, `PARADO` e o eval vai para a lista do
  dono.
- Decisões pedidas pelo Executor: o Maestro ratifica ou corrige e registra.
- Gate: todas as fases `APROVADO` na tentativa corrente; a spec `status: done` (o próprio
  `/execute-spec-phase` a fecha quando todas concluem).

### Passo 5 — Fechamento
- Recruta **Fechamento**, `Commitar ao fim: sim`: `CHANGELOG.md` (seção `[Não lançado]`, no formato
  Keep a Changelog) e `Roadmap.md` (marcar a etapa), exigidos pelo `CLAUDE.md` (item 12); a linha da
  spec em `specs/INDEX.md` como `done`; a §9 conferida item a item com evidência.
- `CLAUDE.md` **não** é editado sem autorização do dono no chat (item 12): a frase que a spec tornou
  falsa vai para o resumo como pendência do dono, com a linha e o texto proposto. Com a autorização,
  a edição entra aqui, por este recruta.
- Gate: documentos vivos atualizados e commitados.

### Passo 6 — Conferir, PR e merge
- Recruta **Conferente em terminal limpo** (não viu nada nascer), `Commitar ao fim: não`, workflow
  *"conferência de PR: ler `git diff origin/dev...HEAD`, rodar **a validação completa da decisão de
  operação, item 9**, e devolver ✓/✗ com a saída real em `.codeflow/checkpoints/`"*. Quando a spec
  toca a interface e a §9 pede E2E, o Conferente o roda depois, pela receita abaixo.
- **O E2E** (`npm run test:e2e`, fora do CI) sobe o `next dev` na 3000 sozinho
  (`frontend/playwright.config.ts`, `webServer`) e reaproveitaria um servidor alheio — por isso a
  fila confere a 3000 livre. Exige `frontend/.env.local` na pasta; ausente → `PARADO` (o Maestro não
  copia segredo). Sem backend real: `FILA_PORTAS="3000 8000" fila pilha -- npm --prefix frontend
  run test:e2e`. **Com o backend real na 8000** (a §9 diz), o banco é **próprio do E2E**,
  `caloria_e2e_spec` — **nunca** o `caloria_test_spec`, que a suíte zera a cada rodada —, criado uma
  vez pelo Maestro:
  `docker exec caloria_postgres psql -U caloria -d caloria_db -c 'CREATE DATABASE caloria_e2e_spec;'`.
  Migration, API, E2E e derrubada ficam dentro de **uma** chamada da fila:

  ```bash
  source ~/.config/caloria/orquestracao/spec.env
  E2E_DB="$(printf '%s' "$TEST_DATABASE_URL" | sed 's#/caloria_test_spec#/caloria_e2e_spec#')"
  case "$E2E_DB" in *:5442/caloria_e2e_spec*) ;; *) echo "banco de E2E fora do padrão"; exit 1;; esac
  FILA_PORTAS="3000 8000" fila pilha -- bash -c '
    export DATABASE_URL="$1"
    (cd backend && .venv/bin/alembic upgrade head) || exit 1
    (cd backend && exec .venv/bin/uvicorn app.main:app --port 8000) & api=$!
    trap "kill $api 2>/dev/null; wait $api 2>/dev/null" EXIT
    for i in $(seq 60); do curl -fs localhost:8000/health >/dev/null && break; sleep 1; done
    curl -fs localhost:8000/health >/dev/null || { echo "API não subiu"; exit 1; }
    npm --prefix frontend run test:e2e; r=$?
    exit $r' _ "$E2E_DB"
  ```

  A URL é derivada sem ser impressa e a guarda do `case` recusa qualquer outro banco; a API roda
  **sem `--reload`** e cai **pelo próprio PID** no `trap` (nunca `pkill`); o código de saída é o do
  E2E. As credenciais de `E2E_LOGIN_EMAIL`/`E2E_LOGIN_PASSWORD`, se usadas, nunca entram no
  repositório. (Receita da trilha de Melhorias, `orquestrar-melhorias.md`, adaptada ao banco desta.)
- ✗ → os achados voltam ao Executor (código) ou ao Fechamento (documentos), e a reconferência é em
  terminal limpo.
- ✓ → `git push -u origin spec/NNN-<slug>` e `gh pr create --base dev`, com contexto, o que mudou,
  como se prova (a saída da validação), as decisões por delegação e as pendências do dono — **sem
  rodapé de IA** (item 6). Esperar o **CI verde no PR** (item 2: o `ci.yml` roda em `pull_request`
  para `dev`). O GitHub leva alguns segundos para registrar os checks, e o `gh pr checks` sai com
  "no checks reported" enquanto isso — esperar o primeiro aparecer, até ~2 min, e só então vigiar:

  ```bash
  for i in $(seq 24); do gh pr checks <n> 2>&1 | grep -q 'no checks reported' || break; sleep 5; done
  gh pr checks <n> --watch
  ```

  Ainda sem check depois da espera → `PARADO` (o CI do PR não disparou; não é CI vermelho). Verde →
  `gh pr merge <n> --merge --delete-branch` — **nunca squash** (os artefatos citam `sha`, que seguem
  alcançáveis pelo merge no `dev`). O ramo remoto é apagado no merge (decisão de operação do CalorIA,
  item 1).
- **Se o `origin/dev` andou** antes do merge: o recruta **Fechamento** (ou, se o conflito for de
  código, um Executor limpo) traz o `dev` com `git merge origin/dev`, assunto
  `chore(spec): traz o origin/dev para spec/NNN-<slug>` (se passar de 72,
  `chore(spec): traz o origin/dev`), um **Conferente limpo refaz a validação completa sobre o novo
  HEAD** e o CI roda de novo (item 1). Commit **só de documentos** depois da validação não a reabre:
  basta `git diff --stat <sha validado>..HEAD` só com documentos e o gitleaks do ramo (item 12).
- CI vermelho → o achado volta ao recruta do passo que o causou; nunca mergear com CI vermelho.
- Gate: PR mergeado no `dev` com CI verde, e o `sha` do merge no plano.

### Passo 7 — Entrega
- Dispensar os recrutas (`maestri dismiss`).
- Devolver a pasta principal ao `dev`: `git fetch origin && git switch dev && git pull --ff-only`,
  e apagar o ramo local mergeado (`git branch -d spec/NNN-<slug>`).
- Gate: a pasta fora do ramo da spec; o plano com todas as decisões e o diário.

## Proibições durante este workflow

- O Maestro não escreve código nem spec, e não roda os workflows ele mesmo.
- Não usar subagente — cada passo é um terminal. Quem executou não avalia nem confere.
- Nenhuma atribuição a IA em commit, PR ou documento (item 6).
- Não abrir PR para `main`, não mexer em PR do dependabot (item 3).
- Nunca squash, nunca rebase, nunca commit direto no `dev`; não mergear com CI vermelho.
- Não mergear PR de outra trilha. Não decidir escopo que o dono não confirmou.
- Não rodar `make reset`, `down -v`, `make check`/`test*`/`lint*`/`typecheck` nem servidor fora da
  fila; nenhum teste sem o `spec.env` carregado.
- Não registrar eval no `history.jsonl` dentro do ramo.
- Não editar `CLAUDE.md` sem autorização do dono no chat.
- Não colar segredo, chave ou dado real de usuário no canvas, nos despachos ou no plano.

## Definition of Done

- [ ] Escopo confirmado pelo dono; número da spec pelo alocador; gatilho resolvido ou dispensado.
- [ ] Spec escrita pelo `/create-spec`, revisada por terminal limpo até zero BLOQUEANTES.
- [ ] Todas as fases `APROVADO` na tentativa corrente, cada avaliação em terminal limpo.
- [ ] `CHANGELOG.md`, `Roadmap.md` e `specs/INDEX.md` em dia; melhoria de origem com `spec: <slug>`.
- [ ] Validação completa (item 9) verde por um Conferente limpo, CI verde no PR, merge com `--merge`.
- [ ] Nenhum subagente; nenhuma atribuição a IA; nenhum segredo ou dado real no ramo.
- [ ] A pasta principal fora do ramo da spec; cada decisão registrada no plano com o porquê.

## Resumo final

Nas cinco seções fixas do `SPEC.md` §5.6.4. Antes delas, a tabela **de todas as decisões tomadas
por delegação**, com o porquê. Em **Riscos e notas**, o que ficou aberto na §8 e o eval completo,
se ficou para o dono. Em **Próximos passos**, o link do PR, as frases do `CLAUDE.md` a corrigir
(com autorização) e o que é do dono: o PR `dev → main`, que dispara o CD de produção.

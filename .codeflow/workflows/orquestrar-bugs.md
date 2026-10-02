---
versão: 1.0
status: experimental
atualizado: 2026-10-02
granularidade: médio
gera_decision: no
usa_checkpoints: no
politica_falhas: padrão
escopo: projeto (CalorIA) — trilha de bugs no Maestri; não toca o framework universal
---

# Workflow: orquestrar-bugs

## Quando usar

No workspace **CalorIA · Bugs** do Maestri (worktree `~/Projetos/CalorIA-wt/bugs`), no terminal com o
**modo Maestro ligado**. Este chat vira o **Maestro da trilha de bugs**: conversa com o dono, registra
o bug e despacha cada passo para **um terminal próprio** — o Corretor roda o `/bugfix`, um Conferente
em terminal limpo roda o `/double-check` com a validação completa local — e, com o `✓` e o **CI verde
no PR**, **abre o PR para `dev` e faz o merge ele mesmo** (decisão de operação do CalorIA, itens 1 e
2). O Maestro **não escreve código de produção** e **não usa subagente**. Argumento: a descrição do
bug (texto, item de um laudo de auditoria, achado do `/security-sweep`) ou um bug já registrado em
`.codeflow/bugs/`.

**Dois modos, e quem escolhe é o dono:** o **avulso** (o padrão — um bug, um ramo, um PR; o
Protocolo abaixo) e o **lote** (`/orquestrar-bugs lote <lista ou arquivo>` — vários bugs, um ramo,
um ledger, um PR; a seção *Modo lote*). É pelo lote que entram a lista da trilha de **Auditoria**, que
não registra bug, e o ledger do `/security-sweep` de 17/09 (`.codeflow/bug-batches/security-sweep-2026-09-17.md`),
cujos achados ainda não viraram bug registrado. O Maestro não troca de modo por conta própria.

```
dono ──► Maestro (bugs) ── registra o bug NNN (caloria-proximo-numero) e abre fix/NNN-<slug>
            │                                                     a partir de origin/dev
            ├─► Corretor    /bugfix  (lote: /batch-bugfix + ledger)  → commits no ramo
            ├─► Conferente  /double-check, terminal limpo            → ✓ + validação completa local
            │                                                         (+ E2E pela fila da máquina)
            └─► PR → dev · CI verde no PR · gh pr merge --merge · pasta volta a origin/dev
lista da Auditoria e ledger do /security-sweep ──► modo lote
dev → main: do dono (o PR dispara o CD de produção) — fora deste roteiro
```

## Quando NÃO usar

- Fora do Maestri, ou sem o modo Maestro → o `/bugfix` ou o `/batch-bugfix` direto, com o dono no
  chat.
- **Hotfix em produção** (`hotfix/*` a partir da `main`, PR para a `main` e depois `git merge main` na
  `dev` — `docs/git-workflow.md:45-67`) → é do dono: a `main` dispara o CD (`.github/workflows/cd.yml:6-9`)
  e é dele (decisão de operação, item 3). O Maestro pode registrar o bug; o caminho do hotfix não é dele.
- **Defeito que não se corrige no repositório** — no servidor de produção, na Vercel, no DNS, nos
  segredos do environment `production` (ex.: o `006-frontend-orfao-na-vercel.md`, e o contorno manual
  do `005-seed-demo-nao-roda-em-producao.md`) → o dono. A trilha não toca servidor, banco de produção
  nem conta externa. Se houver parte no código, ela vem para cá e a parte externa vai como pendência.
- Dois ou três bugs **sem relação entre si**, que o dono quer em PRs separados → avulso, um de cada
  vez — não o lote.
- Bug achado **dentro** de uma spec em andamento e que bloqueia aquela spec → é da trilha de Spec, no
  ramo dela.
- **Pedido de melhoria ou feature disfarçado de bug** → trilha de **Melhorias & Features** (só ela
  numera melhoria). Bug já registrado que vira feature fica `convertido-em-melhoria` no índice, com o
  link (`.codeflow/bugs/INDEX.md:32-33,48-49`).
- **O conserto exige o que a decisão de operação manda para spec ou melhoria** — migration destrutiva,
  mudança de contrato da API consumida pelo front, mudança no pipeline de IA que pede eval completo
  (inclusive editar `backend/app/prompts/`, que tem `sha256` travado por teste), mudança de fluxo de
  auth → o escopo é do dono decidir no Passo 1.

## LEIA TAMBÉM

- `.codeflow/constitution.md` (regras invariantes e áreas de alto risco: auth, `services/ai/`,
  `alembic/`, Web Push) · `.codeflow/INDEX.md` · `.codeflow/manifest.md`
- `.codeflow/bugs/INDEX.md` — o registro de entrada: convenção de numeração, colunas, vocabulário de
  `status`, relação com `bug-batches/`.
- `CLAUDE.md` (convenções de commit `:255-288`, fluxo `:290-300`) · `docs/git-workflow.md` ·
  `CONTRIBUTING.md` (hooks do pre-commit `:43-59`)
- **Decisão de operação por trilhas no Maestri (02/10/2026)** —
  `.codeflow/decisions/2026-10-02-operacao-por-trilhas-no-maestri.md`, citada aqui pelo item: 1 (merge
  pelo Maestro, `--merge`, `git merge origin/dev`, nunca rebase), 2 (gate do merge: revisor limpo +
  validação local + CI verde), 3 (`main` é do dono), 5 (ramo por tarefa e nomes), 6 (atribuição
  proibida), 7 (infra tem dono; `make` proibido nas trilhas), 8 (banco e Redis da trilha), 9 (a
  validação completa), 10 (fila da máquina), 11 (numeração), 12 (documentos vivos) e 13 (PR só de
  documentos).
- `~/.config/caloria/orquestracao/LEVANTAMENTO.md` — o porquê de cada proibição de infra (§2).
- `~/.codeflow/framework/library/skills/modo-delegado/SKILL.md` — **quem a carrega é o recruta**; o
  Maestro só precisa do formato do bloco de despacho e do retorno.
- `~/.codeflow/framework/library/workflows/bugfix.md`, `batch-bugfix.md` e `double-check.md` —
  **quem os lê é o recruta**; o Maestro lê só o bastante para despachar (no lote, o **Formato do
  ledger** do `batch-bugfix.md`, que é o contrato entre o Corretor e o Conferente).
- As trilhas irmãs em `.codeflow/workflows/orquestrar-*.md` — a mecânica de recruta é a mesma.

## Antes de começar

- **Situar-se:** `git rev-parse --show-toplevel` tem de ser `~/Projetos/CalorIA-wt/bugs`, e
  `maestri list` tem de mostrar `maestro: true`. Fora de tarefa, a pasta fica em `origin/dev`
  destacado; nunca no ramo `dev` (ele está aberto na pasta principal). Se não, parar e avisar o dono.
- **Ferramentas da pasta:** `backend/.venv/bin/pytest` e `frontend/node_modules/.bin/next` têm de
  existir **nesta** pasta. O `.venv` é próprio da worktree — o da pasta principal é *editable* e aponta
  para ela (LEVANTAMENTO §2.1); nunca usá-lo, copiá-lo nem linká-lo. Faltando, **quem prepara é o
  Maestro**, antes do primeiro despacho: `python3.12 -m venv backend/.venv &&
  backend/.venv/bin/pip install -e "backend[dev]"` e `npm --prefix frontend ci`.
- **Infra da trilha** (decisão de operação, itens 7 e 8): o Postgres e o Redis são do compose da
  **pasta principal** (portas de host 5442 e 6389). Conferir sem tocar neles:
  `source ~/.config/caloria/orquestracao/bugs.env && docker exec caloria_postgres psql -U caloria -d
  caloria_db -tAc "select 1 from pg_database where datname='caloria_test_bugs'"` → `1`, e
  `docker exec caloria_redis redis-cli ping` → `PONG`. Banco ausente → o Maestro o cria uma vez
  (`docker exec caloria_postgres psql -U caloria -d caloria_db -c 'CREATE DATABASE caloria_test_bugs;'`).
  O banco do **E2E com backend real**, `caloria_e2e_bugs`, é outro (item 8: a suíte zera o de teste) e
  se confere e se cria do mesmo jeito, trocando o nome. Containers fora do ar → avisar o dono: quem
  sobe a infra é a pasta principal.
- **Um bug (ou um lote) por vez.** A pasta tem um ramo só: o próximo bug pode ser conversado com o
  dono (Passo 1 ou L1) enquanto o atual corre, mas só é registrado e ganha ramo depois do merge do
  atual e da devolução da pasta a `origin/dev`. Bugs que o dono quer juntos → modo lote.
- **Regra do registro** (`.codeflow/bugs/INDEX.md`, colunas `# · arquivo · título · severidade · área ·
  status · criado`, vocabulário de status `aberto · em-lote · corrigido · não-reproduz ·
  convertido-em-melhoria`, `INDEX.md:14,32-33`):
  - O estado do bug mora em **dois lugares que mudam juntos**, no mesmo commit: o `status:` do
    frontmatter do arquivo e a célula **status** da linha do índice. (Hoje o `004` já diverge — índice
    `corrigido`, arquivo `aberto` —; não repetir.) Junto, o `atualizado:` do arquivo.
  - Na linha do índice, só a célula **status** é trocada, inteira; `#`, `arquivo`, `título`,
    `severidade`, `área` e `criado` nunca perdem texto (o título só recebe acréscimo no fim, ex.:
    `— convertido em melhoria NNN`).
  - Não se inventa status: "em correção" não existe no vocabulário. No avulso o bug fica `aberto`
    até o fecho; no lote ele vai a `em-lote` (com `lote: <slug>` no frontmatter, como os `001`/`002`).
    O ramo em que ele está mora no plano e no Quadro.
  - Depois de cada edição, conferir **a linha**, não a presença do texto:
    `grep -c '^| NNN |' .codeflow/bugs/INDEX.md` = 1 e
    `grep '^| NNN |' .codeflow/bugs/INDEX.md | sed 's/\\|//g' | awk -F'|' '{print NF-2}'` = 7; e
    `grep '^status:' .codeflow/bugs/NNN-*.md` igual à célula.
- **Quadro:** se `maestri list` mostrar uma nota **Quadro** conectada, mantê-la em dia a cada passo —
  o bug (ou o lote), a etapa atual, quem está fazendo o quê, as decisões tomadas. Nunca colar segredo,
  dado de usuário real nem conversa real nela.
- **Plano da trilha**, fora do repositório: `~/.config/caloria/orquestracao/bugs/PLANO-NNN.md`
  (`mkdir -p -m 700 ~/.config/caloria/orquestracao/bugs` na primeira vez; o arquivo com chmod 600) com as tabelas **Decisões** (`# · momento · decisão · por quê`) e **Diário**
  (`hora · etapa · resultado`).
- **Regras que vão em TODO despacho** (copiar verbatim no bloco de despacho):
  1. Só na pasta `~/Projetos/CalorIA-wt/bugs`, no ramo do despacho. Sem push, sem PR, sem merge de
     PR, sem trocar de ramo — o único merge permitido é `git merge origin/dev` no próprio ramo (e
     concluir um que o Maestro deixou em conflito). Nunca rebase, nunca `git stash`.
     `git add <caminho>`, nunca `-A` nem `.`.
  2. Conventional Commits **em português**, imperativo, minúsculas, sem ponto final, assunto ≤ 72
     (não há commitlint: conferir à mão), escopo entre parênteses e o bug no fim —
     `fix(ai): <o quê> (bug NNN)`. **Atribuição a IA é proibida**: sem `Co-Authored-By`, sem citar
     Claude, agente ou autor na mensagem (`constitution.md:37`, `CLAUDE.md:257`). **Nunca
     `--no-verify`.** Se o pre-commit (ruff `--fix`, ruff-format, end-of-file) reescrever arquivos e
     abortar o commit, adicionar de novo **os mesmos caminhos** e commitar outra vez.
  3. Nunca perguntar ao dono: seguir a skill `modo-delegado`.
  4. Segredo nunca é impresso, lido para o retorno nem commitado (`.env`, `frontend/.env.local`,
     `backend/vapid_private.pem`). Dado de usuário real (e-mail, peso, refeições, fotos) nunca em
     log, fixture, teste, commit, Quadro ou retorno; foto de comida nunca é persistida
     (`constitution.md:39`).
  5. Infra: **proibido** `make dev`, `make dev-d`, `make infra`, `make down`, `make reset`,
     `make prod`, `make build` e qualquer `docker compose` (nunca `down -v`: apaga os bancos de teste
     de todas as trilhas); **proibido** `make check`, `make test*`, `make lint*`, `make typecheck`,
     `make migrate*`, `make seed*` — rodam no container da pasta principal e validam o código errado.
     Antes de qualquer teste: `source ~/.config/caloria/orquestracao/bugs.env` (sem ele o `pytest` cai
     no `localhost:5432`, que é o Postgres do ICCNC, e a fixture faz `DROP SCHEMA`). Postgres ou Redis
     fora do ar → `PARADO`. Servidor de dev e E2E só por `FILA_PORTAS="3000 8000" fila pilha --
     <comando>`; eval completo e `tests/smoke_test.py` só por `fila groq -- <comando>` (cota única da
     Groq). Código 76 = porta ocupada por servidor que ficou de pé (não matar; reportar), 75 =
     desistiu de esperar.
  6. Ferramentas **desta** pasta: `backend/.venv/bin/<ferramenta>` (rodando de `backend/`) e o
     `node_modules` de `frontend/`. Depois de trazer o `origin/dev`: se `backend/pyproject.toml` mudou,
     `backend/.venv/bin/pip install -e "backend[dev]"`; se `frontend/package-lock.json` mudou,
     `npm --prefix frontend ci`.
  7. Testes: o Corretor roda o subconjunto que prova o trabalho (o teste de regressão, `ruff` e
     `mypy` dos arquivos tocados, o `jest` do componente); a validação completa (decisão de operação,
     item 9) é **só do Conferente**, uma vez.
  8. Schema: mudança de modelo vem com migration Alembic nova, revisada, gerada contra o banco da
     trilha (nunca o `caloria_db`); migration já aplicada é imutável (`constitution.md:48`).
     `backend/app/prompts/` é conteúdo com `sha256` travado — mexer nele está fora do escopo de bug.
  9. Retorno em no máximo 15 linhas; o detalhe fica em `.codeflow/checkpoints/` (ignorado pelo git).

**Formato do bloco de despacho** (o prompt que o Maestro manda a cada recruta):

```
MODO DELEGADO — antes de tudo, leia e siga ~/.codeflow/framework/library/skills/modo-delegado/SKILL.md.
Orquestrador: <nome do Maestro em `maestri list`>
Pasta: ~/Projetos/CalorIA-wt/bugs — comece com `cd ~/Projetos/CalorIA-wt/bugs`.
Ramo: fix/NNN-<slug>   (no lote: fix/lote-<slug>)
Workflow: <comando e alvo>
Decisões delegadas:
  1. <...>
Regras do projeto: <as nove acima, verbatim>
Commitar ao fim: sim   (Corretor) · não (Conferente avulso) · só o ledger (Conferente do lote)
```

## Protocolo

### Passo 1 — Entender o bug com o dono (o único passo de conversa)
- Ler o relato (ou o item do laudo, ou a linha do ledger do `/security-sweep`) e, **antes de
  despachar**, fechar com o dono o que o `/bugfix` perguntaria: sintoma, como reproduzir, onde
  apareceu (local, produção), severidade (`crítico · alto · médio · baixo`; o índice usa `alto` e
  `médio`, o ledger de saneamento usou `critico`), área (`backend/ai`, `frontend`, `infra/deploy`…, como
  na coluna do índice), escopo esperado e o que fica fora.
- **Classificar o risco**, porque muda o que se pede ao Corretor e ao Conferente: o conserto toca uma
  área de alto risco da `constitution.md:44-49` — auth (`core/security.py`, `api/v1/auth.py`,
  `services/auth_service.py`, `core/deps.py`), o pipeline de IA (`services/ai/`, `food_lookup`, sanity
  check), o schema (`alembic/`), Web Push/VAPID? a interface (`frontend/`)? uma dependência? Se o
  conserto cair num caso de *Quando NÃO usar* (migration destrutiva, contrato da API, pipeline de IA
  com eval completo, fluxo de auth), o escopo é do dono — pode virar melhoria ou spec.
- Montar as **decisões delegadas** a partir dessa conversa — é com elas que o Corretor vai responder
  aos próprios gates. Registrar no plano.
- Gate: o dono confirmou título, severidade e escopo. Severidade `crítico` nunca sem ele.

### Passo 2 — Registrar e abrir o ramo
- **Bug já registrado** (o dono aponta o arquivo ou o número): pular a numeração e o registro — só
  abrir o ramo, com o número e o slug do arquivo existente.
- **Número:** `caloria-proximo-numero bug` (olha todos os ramos e todas as worktrees, inclusive
  arquivo não commitado, e o `proximo_numero` de cada `INDEX.md`). Só este Maestro numera bug.
  Nunca o número à mão, nem só o `proximo_numero` desta pasta.
- `git fetch origin && git switch -c fix/NNN-<slug> origin/dev` — nunca `git switch dev`.
- Criar `.codeflow/bugs/NNN-<slug>.md` no molde dos existentes (não há `_TEMPLATE`): frontmatter
  `versão: 1.0`, `id: "NNN"`, `slug: NNN-<slug>`, `título`, `severidade`, `área`, `status: aberto`,
  `criado`, `atualizado`, `reportado_por`; corpo `# BUG NNN — <título curto>`, `## Sintoma` (medido,
  com o comando e a saída quando houver), `## Esperado vs. obtido` e `## Referências`. Sem segredo nem
  dado de usuário real.
- No `.codeflow/bugs/INDEX.md`: a linha nova na tabela, em ordem numérica, com status `aberto`; o
  `proximo_numero` do frontmatter passa a `NNN+1`; o `atualizado:` do frontmatter, a data. Conferir
  pela regra do registro. Commitar só isso: `docs(bugs): registra o bug NNN`.
- Gate: ramo nascido de `origin/dev`; o registro commitado; a linha e o `proximo_numero` conferidos.

### Passo 3 — Despachar a correção (Corretor)
- `maestri list`: se já houver um Corretor livre, reusá-lo depois de
  `maestri ask "<nome>" --raw "/clear\n"`; senão
  `maestri recruit "<codinome>" --preset "Claude Code"` — **sem `--role`** (a role muda o diretório
  de trabalho do recruta).
- Despachar com o bloco, workflow `/bugfix sobre .codeflow/bugs/NNN-<slug>.md`, e rodar o
  `maestri ask` **em segundo plano** — o Maestro continua livre para conversar com o dono. Nas
  decisões delegadas, sempre:
  - acrescentar ao arquivo do bug `## Causa raiz` (com `arquivo:linha`) e `## Correção` (o que mudou e
    o teste de regressão, ou a reprodução manual com o porquê), **sem apagar** o que o registro já
    tinha; o `status` do frontmatter e a linha do índice **não** mudam — quem fecha é o Maestro;
  - a entrada em `CHANGELOG.md` (`## [Não lançado]` → `### Corrigido`, uma linha em negrito no estilo
    das existentes) **no mesmo commit do conserto** — é assim que o repositório faz (`3aa7b0b`) e o
    `CLAUDE.md:297` exige; `Roadmap.md` só se o bug fechar uma etapa dele;
  - decision, se o `/bugfix` gerar uma (`gera_decision: auto`): o arquivo
    `.codeflow/decisions/AAAA-MM-DD-<slug>.md` (as decisions do CalorIA não têm número), **sem linha no
    `decisions/INDEX.md`** — a linha é do Maestro, no fechamento (decisão de operação, item 11);
  - dependência: no backend, subir o **piso** em `backend/pyproject.toml` (a imagem de produção instala
    com `pip install .` e ignora o `uv.lock` — `backend/Dockerfile:27`) e manter o `uv.lock` coerente;
    no frontend, `package.json` e `package-lock.json` juntos (a imagem usa `npm ci` —
    `frontend/Dockerfile:13`).
- No retorno: `CONCLUÍDO` → Passo 4. `PRECISA DE DECISÃO` → ratificar ou corrigir cada uma (registrar
  no plano) e responder ao **mesmo** Corretor. `PARADO` → decidir se couber na delegação; senão levar
  ao dono e despachar de novo.
- Gate: retorno `CONCLUÍDO`, com commits no ramo e o teste de regressão (ou a reprodução manual
  justificada) declarado no relatório.

### Passo 4 — Conferir em terminal limpo (Conferente)
- Um terminal que **não viu** a correção: recruta novo, ou o Conferente anterior depois de `/clear`.
  **Nunca** o Corretor.
- Despachar `/double-check sobre .codeflow/bugs/NNN-<slug>.md`, com o teste de regressão e a
  reprodução que o Corretor declarou. Ele reproduz o bug de novo, **prova o vermelho** (o teste falha
  com o conserto revertido no arquivo de produção, e volta a passar sem a reversão — nunca commitar a
  reversão) e não corrige nada.
- **No avulso não há ledger.** O `/double-check` normaliza documento bruto num
  `.codeflow/bug-batches/<slug>.md` (`double-check.md`, Passo 1); aqui isso sobraria como arquivo não
  rastreado, atravessaria a volta da pasta a `origin/dev` e se acumularia de bug em bug. Decisão
  delegada fixa no despacho do avulso: **"não criar ledger em `.codeflow/bug-batches/`; a fonte de
  verdade é o arquivo do bug, e os vereditos (`✓`/`✗`/`⚠` com a reprodução) ficam só no relatório em
  `.codeflow/checkpoints/`"**. No retorno, o Maestro confere com
  `git status --porcelain -- .codeflow/bug-batches` (vazio).
- **Validação completa local** — **a validação completa da decisão de operação, item 9** (gitleaks dos
  commits do ramo, `ruff check`, `ruff format --check`, `mypy app/ evals/`, `pytest` com o piso de
  cobertura, `npm run lint`, `npx tsc --noEmit`, `npm test`, `npm run build`), no venv e no
  `node_modules` desta pasta, com o `bugs.env` carregado, rodada **uma vez**, com a saída real no
  relatório. Os comandos exatos ficam só na decisão: o roteiro não os repete.
  - O relatório traz a **contagem** do `pytest` (passados, pulados, a cobertura) e o **`sha`
    validado** (`git rev-parse HEAD`) — é contra ele que o Maestro confere o HEAD do merge (Passo 5).
    Integração toda pulada é sinal de banco inacessível, e o resultado não vale.
  - **Se o diff toca `frontend/`**, depois dela, o E2E pela fila — ele **não roda no CI**, é só aqui.
    Exige `frontend/.env.local` nesta pasta; ausente → `PARADO` (o Maestro não copia segredo). Sem
    backend real: `FILA_PORTAS="3000 8000" fila pilha -- npm --prefix frontend run test:e2e`.
  - **Com o backend real na 8000** (o `e2e/auth.spec.ts` não tem `page.route`, então o fluxo de login
    precisa dele), o banco é **próprio do E2E**, `caloria_e2e_bugs` — **nunca** o `caloria_test_bugs`
    que o `bugs.env` exporta como `DATABASE_URL` e que a suíte zera a cada rodada (decisão de
    operação, item 8). O Maestro o cria **uma vez** (ver *Antes de começar*). Migration, API, E2E e
    derrubada ficam dentro de **uma** chamada da fila:

    ```bash
    source ~/.config/caloria/orquestracao/bugs.env
    E2E_DB="$(printf '%s' "$TEST_DATABASE_URL" | sed 's#/caloria_test_bugs#/caloria_e2e_bugs#')"
    case "$E2E_DB" in *:5442/caloria_e2e_bugs*) ;; *) echo "banco de E2E fora do padrão"; exit 1;; esac
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

    A URL é derivada sem ser impressa e a guarda do `case` recusa qualquer outro banco; o `alembic` e
    a API leem o `DATABASE_URL` exportado (`backend/alembic/env.py` usa `settings.DATABASE_URL`); a API
    roda **sem `--reload`** e cai **pelo próprio PID** no `trap` — nunca `pkill`; o código de saída é
    o do E2E. É a mesma receita das trilhas de Spec e de Melhorias, só com o banco desta.
  - **Eval completo** só se o dono o pediu no Passo 1, e por `fila groq -- ...`; a camada rápida do
    eval já está no `pytest`.
  - Vermelho que já existe em `origin/dev` não reprova o conserto, mas tem de ser **medido**, nunca
    presumido: para o que o CI roda, o CI do `dev` (`gh run list --workflow ci.yml --branch dev
    --limit 1 --json headSha,conclusion`, com `headSha` igual a `git rev-parse origin/dev`); para o
    resto, se não der para medir sem trocar de ramo, o Conferente retorna `PRECISA DE DECISÃO`.
- Veredito `✓` → Passo 5. `✗` ou `⚠` → os achados voltam ao **mesmo** Corretor (Passo 3) e a
  reconferência é em terminal limpo de novo. **Teto: duas reprovações** — na terceira, escalar ao
  dono.
- Gate: bug sanado (`✓`), vermelho provado, e a validação completa verde (ou com o vermelho pré-
  -existente medido em `origin/dev`), com a saída real e o `sha` validado no relatório do Conferente.

### Passo 5 — Fechar, trazer o `dev`, abrir o PR e fazer o merge
- **Fechar o bug** no ramo: frontmatter `status: corrigido` e `atualizado:`; no fim do arquivo, a
  linha `**Fechamento (AAAA-MM-DD):** corrigido em <sha do conserto>, ramo fix/NNN-<slug>.`; a célula
  **status** do índice trocada para `corrigido` — pela regra do registro. Se o Conferente deu `⚠` e o
  dono aceitou fechar assim, o arquivo diz o que ficou sem prova.
- **Decision do Corretor**, se houver: a linha no **topo** da tabela do `.codeflow/decisions/INDEX.md`
  (`data · título · status · tags`, o link para o arquivo, `ativa`, tags com `bug-NNN`) e o
  `atualizado:` do frontmatter. ADR em `docs/architecture.md` não é desta trilha — se o conserto pedir
  uma, vai ao dono. Commitar o fecho: `docs(bugs): fecha o bug NNN`.
- **Documentos vivos** (decisão de operação, item 12): se a correção tornou falsa uma frase do
  `CLAUDE.md`, editá-lo **só com autorização do dono no chat**. Sem ela, a frase vai para o Resumo
  final como pendência do dono, com a linha e o texto proposto. O mesmo vale para a
  `constitution.md`.
- **Commit só de documentos depois da validação não a reabre** (decisão de operação, item 12): o fecho,
  o índice, a linha da decision, o ledger e o `CLAUDE.md` autorizado. Conferir que nada além disso
  mudou desde o `sha` validado —
  `git diff --stat <sha validado>..HEAD -- . ':!.codeflow' ':!CLAUDE.md' ':!CHANGELOG.md' ':!Roadmap.md'`
  tem de sair vazio — e rodar só o passo do gitleaks do ramo da decisão de operação, item 9, que cobre
  os commits novos. Saiu algo fora disso? Revalidação em terminal limpo, como em *Trazer o `dev`*.
- **Trazer o `dev`** (decisão de operação, item 1): `git fetch origin`; se `git merge-base
  --is-ancestor origin/dev HEAD` falhar, `git merge origin/dev -m "chore(bugs): traz o origin/dev
  para o bug NNN"` — **nunca rebase** (ele reescreve os `sha` já gravados no bug e no relatório).
  Depois, a regra 6 do despacho (reinstalar se `pyproject.toml` ou `package-lock.json` mudaram).
  - Conflito só em documentos (`.codeflow/`, `CHANGELOG.md` — o `## [Não lançado]` é ponto quente
    entre trilhas): o Maestro resolve mantendo os dois lados, pela regra do registro. Conflito em
    código: volta ao **mesmo** Corretor ("resolver o conflito do merge de `origin/dev`"), e o Maestro
    não toca o código.
  - **Revalidação em terminal limpo:** com o merge feito, um Conferente que não viu o merge (recruta
    novo, ou `/clear`) roda o teste de regressão do bug e a **validação completa do Passo 4** sobre o
    **novo HEAD**, sem commitar, e reporta o novo `sha` validado. Vermelho → volta ao Corretor e ao
    Passo 4. Se o `dev` não tinha andado, não há merge nem revalidação.
- **Push e PR:** `git push -u origin fix/NNN-<slug>` e `gh pr create --base dev`, com o texto no molde
  do `.github/PULL_REQUEST_TEMPLATE.md`: contexto, o que mudou, como se prova (teste de regressão,
  vermelho provado, a saída da validação completa e da revalidação, se houve) e **pendências da
  promoção** (migration a aplicar em produção, ação manual no servidor, PR do dependabot que o
  conserto supera). **Sem rodapé de IA** (decisão de operação, item 6). Para editar o PR depois:
  `gh pr edit <n> --body-file <arquivo>`; se falhar, `gh api -X PATCH repos/gabriel-ngrs/CalorIA/pulls/<n>
  -F body=@<arquivo>`.
- **CI verde no PR** (decisão de operação, item 2). O GitHub leva alguns segundos para registrar os
  checks, e logo depois do `gh pr create` o `gh pr checks` sai com "no checks reported" — inclusive com
  `--watch`. Por isso, primeiro esperar o primeiro check aparecer (até ~2 min):
  `for i in $(seq 24); do gh pr checks <n> 2>/dev/null | grep -q . && break; sleep 5; done`; só então
  `gh pr checks <n> --watch`, até `Backend — lint e testes` e `Frontend — lint e build` saírem `pass`.
  Vermelho → o log (`gh run view <id> --log-failed`) volta ao **mesmo** Corretor e o ciclo retoma no
  Passo 4. **PR sem nenhum check depois da espera** (o `ci.yml` do `origin/dev` sem
  `pull_request: [dev]`, ou o Actions parado) → não fazer o merge: `PARADO` ao dono.
- **Merge pelo Maestro** (decisão de operação, item 1): logo antes, `git fetch origin` e conferir de
  novo `git merge-base --is-ancestor origin/dev HEAD` — se o `dev` andou desde a validação, voltar a
  *Trazer o `dev`*; e repetir o `git diff --stat` da regra do commit só de documentos (vazio).
  Conferir `gh pr view <n> --json baseRefName` = `dev`, então
  `gh pr merge <n> --merge --delete-branch` — **nunca squash** (os artefatos citam `sha`, que seguem
  alcançáveis pelo merge no `dev`). O `--delete-branch` apaga o **ramo remoto** no merge (decisão do
  orquestrador; o repositório tem `deleteBranchOnMerge: false`, então sem ele o ramo ficaria). O `gh`
  também tenta trocar a pasta para o `dev` local e apagar o ramo local — e o `dev` está aberto na
  pasta principal, então essa parte local pode falhar depois do merge feito (**não verificado**). Por
  isso, terminada a chamada, conferir pelo remoto, não pela saída do `gh`: `gh pr view <n> --json
  state` = `MERGED` e `git ls-remote --heads origin fix/NNN-<slug>` vazio; ramo remoto ainda lá →
  `git push origin --delete fix/NNN-<slug>`. Registrar no plano. Nenhum PR para a `main`, nem merge ou
  push nela; os PRs do dependabot não são tocados (decisão de operação, item 3).
- **Depois do merge:** conferir `git status --porcelain` vazio (nada não rastreado — como um ledger
  que o `/double-check` tenha criado — atravessa a troca), devolver a pasta ao `dev` e só então apagar
  o ramo local — `git fetch --prune origin && git switch --detach origin/dev && git branch -d
  fix/NNN-<slug>` (se o `gh` já o apagou, o `branch -d` diz que não existe, e está certo). Dispensar os
  recrutas (`maestri dismiss`) se não houver outro bug na fila.
- Gate: entre o `sha` validado (ou revalidado) e o HEAD mergeado, só commits de documentos; CI verde
  no PR; PR mergeado em `dev` com `--merge`; o bug `corrigido` no arquivo e no índice, juntos; a pasta
  de volta a `origin/dev`; o plano com todas as decisões e o diário.

## Modo lote

`/orquestrar-bugs lote <lista ou arquivo>` — a lista de uma auditoria, os achados do `/security-sweep`,
ou um conjunto de bugs que o dono quer corrigir e conferir **juntos**. É o mesmo ciclo do avulso, com o
par universal feito para isso: o Corretor roda o `/batch-bugfix`, o Conferente roda o `/double-check`,
e os dois se falam pelo **ledger** em `.codeflow/bug-batches/<slug>.md`, no **Formato do ledger** do
`batch-bugfix.md` (`id · título · status · repro/teste · fix (arquivo:linha) · decision ·
verificação`). As regras de despacho, o Quadro, a validação completa e o CI verde são os mesmos. O
`<slug>` é `<origem>-<AAAA-MM-DD>` (ex.: `seguranca-dependencias-2026-10-02`); o ramo, `fix/lote-<slug>`;
o plano, `~/.config/caloria/orquestracao/bugs/PLANO-lote-<slug>.md`.

### L1 — Triar a lista com o dono (o único passo de conversa)
- Para cada item: já registrado (número) ou novo; **bug de fato**, ou pedido de melhoria (→ trilha de
  Melhorias & Features), ou bug que já tem destino numa spec (→ fica fora do lote, com o motivo).
- **Lista da Auditoria:** a pasta pode estar num `origin/dev` velho, então ler sempre do remoto —
  `git fetch origin && git show origin/dev:<caminho do consolidado>` (se o PR da Auditoria ainda não
  entrou no `dev`, `origin/<ramo dela>:<caminho>`). Só a parte do consolidado marcada **para Bugs**
  entra aqui (a de melhorias é da outra trilha). Os itens chegam **sem número** e com a evidência do
  achado — o Maestro os registra; a origem do ledger é o caminho do consolidado. Se a rodada trouxer
  uma decision de segurança (sem linha no INDEX), ela vem **com o lote** e é desta trilha pô-la no
  INDEX, no L5 — registrar o caminho no plano.
- **Achados do `/security-sweep` de 17/09** (`.codeflow/bug-batches/security-sweep-2026-09-17.md`):
  esse arquivo é um **ledger de achados**, noutro formato, e nenhum deles é bug registrado. Ele é a
  **origem** do lote, não o ledger: cada achado confirmado vira um bug registrado, e o ledger novo
  segue o formato do `batch-bugfix`. O arquivo de 17/09 não é reescrito.
  - Cada linha de dependência é **candidato** até a triagem por versão e alcance (a seção *Triagem
    pendente* do próprio ledger): o Corretor confirma que a versão instalada está no range afetado e
    que o caminho vulnerável é alcançado; o que não se confirma sai `não-reproduz`, com o motivo.
  - **Fechar com o dono a régua de versão** — o escopo de bug é subir para a **correção dentro da
    mesma linha de versão**. Upgrade de **versão maior** (ex.: `next` 14 → 15+, `next-auth` 4 → 5,
    `recharts` 2 → 3) muda API e é escopo: o dono decide no L1 se entra, ou se vira melhoria.
  - Os PRs abertos do dependabot (#31–#37, todos para a `main`) **não são tocados**: os que o lote
    superar vão como pendência do dono no PR.
  - As *Pendências de processo* do ledger de 17/09 (estender a caça de IDOR às rotas não amostradas, a
    regra `caloria-email-pessoal`) **não são bug**: são da trilha de Auditoria ou de decisão do dono.
- Fechar com o dono as **decisões delegadas comuns ao lote** e as que valem para um bug só, e a
  classificação de risco do Passo 1 por bug.
- Gate: o dono confirmou a lista final do lote, a régua de versão (se houver dependência) e o que
  ficou fora.

### L2 — Registrar e abrir o ramo
- Bugs novos: `caloria-proximo-numero bug` **uma vez**, e números consecutivos a partir dele; criar
  todos os arquivos (como no Passo 2, com `lote: <slug>` no frontmatter) antes de qualquer outra
  chamada; o `proximo_numero` do índice passa ao último + 1. Bugs já registrados mantêm o número.
- Ramo `fix/lote-<slug>`, a partir de `origin/dev`.
- Criar o ledger `.codeflow/bug-batches/<slug>.md` no formato do `batch-bugfix` (frontmatter `versão`,
  `lote`, `origem`, `criado`, `atualizado`; a tabela com `id` = o número do bug), cada bug `pendente`.
- Cada bug do lote vai a `em-lote` no arquivo e no índice, juntos (pela regra do registro). Commitar
  só o registro e o ledger: `docs(bugs): registra o lote <slug>`.
- Gate: ramo nascido de `origin/dev`; o lote registrado; o ledger commitado.

### L3 — Despachar a correção do lote (Corretor)
- Um Corretor, com o bloco de despacho e o workflow `/batch-bugfix sobre
  .codeflow/bug-batches/<slug>.md`. Nas decisões delegadas: **um commit por bug** (o `/batch-bugfix`
  sozinho não commita), com a linha do `CHANGELOG.md` e o ledger atualizado junto; `## Causa raiz` e
  `## Correção` de cada arquivo de bug acrescentados; as regras de dependência do Passo 3; e **uma
  decision consolidada do lote** (`gera_decision: auto`), sem linha no `decisions/INDEX.md` — a linha
  é do Maestro, no L5.
- **Bug bloqueado não trava o lote** — é a regra do `/batch-bugfix`. Os `bloqueado` e `não-reproduz`
  sobem no retorno; o Maestro decide se couber na delegação, ou leva ao dono.
- **Contexto cheio** no meio do lote: o `/batch-bugfix` para num bug em estado terminal e o ledger é o
  ponto de retomada. O Maestro dá `/clear` no **mesmo** Corretor e despacha de novo, "retomar o ledger
  `<slug>`" — ele pula os terminais e segue nos `pendente`.
- Gate: nenhum bug do lote `pendente` no ledger.

### L4 — Conferir o lote em terminal limpo (Conferente)
- Um terminal que **não viu** a correção roda o `/double-check` sobre o ledger: reproduz cada bug de
  novo (no de dependência, o scanner que o achou — ex.: `osv-scanner scan --lockfile
  frontend/package-lock.json` — deixa de apontar o advisory), prova o vermelho de cada teste de
  regressão, marca a coluna `verificação` e roda a **validação completa** do Passo 4 **uma vez**, para
  o lote inteiro (o E2E pela fila se o lote tocou `frontend/` — num upgrade de `next` ou `next-auth`,
  sempre), e reporta o `sha` validado. Commita só o ledger, depois da validação — commit só de
  documentos, que a decisão de operação, item 12, dispensa de revalidar.
- Os `✗` voltam como `pendente` ao **mesmo** Corretor (ele os recolhe na retomada do ledger), e a
  reconferência é em terminal limpo. **Teto: duas rodadas de reprovação por lote** — na terceira,
  escalar ao dono os bugs que ainda reprovam.
- Gate: todo bug corrigido do lote com `✓` e a validação completa verde.

### L5 — Fechar, abrir o PR e fazer o merge
- Cada bug `✓` → `corrigido` no arquivo e no índice, com a linha de **Fechamento** e o `sha` do seu
  commit. Os `bloqueado`, `não-reproduz` e `⚠` voltam a `aberto` (ou ficam `não-reproduz`, se o
  Conferente confirmou), com o motivo numa linha no fim do arquivo — **o lote fecha sem eles**, e eles
  vão para a lista do dono. Tudo pela regra do registro, conferido bug a bug.
- A decision consolidada (e a de segurança da auditoria, se veio com o lote — trazida com
  `git show origin/dev:<caminho>` para `.codeflow/decisions/AAAA-MM-DD-<slug>.md`, o original fica onde
  está) ganha a linha no topo do `decisions/INDEX.md`; o caminho dela vai na coluna `decision` do
  ledger nos bugs que ela motivou.
- **Origem do `/security-sweep`:** no fim de `security-sweep-2026-09-17.md`, só **acrescentar** uma
  seção `## Desdobramento` com o lote, os bugs que cada achado virou e o PR — as linhas existentes não
  mudam.
- Documentos vivos, **trazer o `dev` com `git merge origin/dev` e a revalidação em terminal limpo**
  (agora sobre os testes de regressão de todos os bugs `✓` do lote), push, PR, **CI verde no PR** e
  merge como no Passo 5 — **um PR para o lote**, com o **placar** (corrigidos, bloqueados, não
  reproduzem), a lista bug → commit, os PRs do dependabot superados e as pendências da promoção. O
  assunto do merge do `dev` é `chore(bugs): traz o origin/dev para o lote <slug>`.
- Devolução da pasta ao `dev`: a mesma regra do Passo 5.
- Gate: entre o `sha` validado (ou revalidado) e o HEAD mergeado, só commits de documentos; CI verde;
  PR do lote mergeado em `dev` com o placar; o ledger com a coluna `verificação` preenchida; as
  decisions no INDEX.

## Proibições durante este workflow

- O Maestro não escreve código de produção nem roda o `/bugfix` ele mesmo.
- Não usar subagente — cada passo é um terminal.
- Não deixar o Corretor conferir o próprio trabalho; não fazer merge sem o `✓` do Conferente, a
  validação completa com saída real **e** o CI verde no PR.
- Não decidir severidade `crítico`, escopo, nem upgrade de versão maior sem o dono.
- Nunca squash; nunca rebase (trazer o `dev` é `git merge origin/dev`); nunca PR para a `main`, nem
  merge ou push nela; nunca push direto no `dev`; nunca mexer nos PRs do dependabot.
- Não fazer o merge do PR se algo além de documentos mudou depois do `sha` validado.
- Nenhuma atribuição a IA em commit, PR ou ledger.
- Não editar `CLAUDE.md` nem `constitution.md` sem autorização do dono no chat.
- Não rodar `make` de infra ou de validação, `docker compose` nem `down -v` nesta pasta; não tocar o
  `caloria_db`, o servidor de produção nem conta externa.
- Não numerar melhoria nem calcular número à mão; não inventar status fora do vocabulário do índice;
  na linha do índice, trocar só a célula status.
- Não colar segredo, credencial, dado de usuário real ou conversa real no canvas, nos despachos ou no
  plano.

## Definition of Done

- [ ] Bug entendido com o dono, com a classificação de risco; decisões delegadas registradas no plano.
- [ ] Bug registrado com número do `caloria-proximo-numero` e o `proximo_numero` do índice atualizado;
      ramo `fix/NNN-<slug>` nascido de `origin/dev`.
- [ ] Correção feita por um Corretor, em terminal próprio, sem subagente; `## Causa raiz` e
      `## Correção` no arquivo do bug; a linha do `CHANGELOG.md` no commit do conserto; commits no
      padrão do repositório, sem atribuição a IA e sem `--no-verify`.
- [ ] Conferência por um terminal que não viu a correção: bug `✓`, vermelho provado e a validação
      completa da decisão de operação, item 9, com saída real e o `sha` validado (E2E pela fila quando
      o diff tocou `frontend/`, com backend real só sobre o `caloria_e2e_bugs`); no avulso, nenhum
      ledger criado em `.codeflow/bug-batches/`.
- [ ] Bug `corrigido` no arquivo e no índice, juntos, com o `sha`; linha do índice conferida; a
      decision, se houver, no INDEX; `CLAUDE.md` editado só com autorização do dono, ou a frase como
      pendência dele no resumo.
- [ ] O `dev` trazido por `git merge origin/dev` (nunca rebase) e o novo HEAD revalidado em terminal
      limpo antes do merge do PR; depois do `sha` validado, só commits de documentos (conferido
      com `git diff --stat`) e o gitleaks do ramo limpo.
- [ ] CI verde no PR; PR para `dev` mergeado com `--merge` pelo Maestro; pendências da promoção
      escritas no PR; cada decisão tomada registrada com o porquê.
- [ ] Ramo remoto apagado no merge (`--delete-branch`, conferido com `git ls-remote`); depois, a pasta
      de volta a `origin/dev` e o ramo local apagado.
- [ ] No modo lote: o ledger com todo bug em estado terminal e a coluna `verificação` preenchida; um
      commit por bug; o PR com o placar e os bugs que ficaram fora devolvidos ao índice com o motivo;
      a origem do `/security-sweep`, se foi ela, com o `## Desdobramento` acrescentado.

## Resumo final

Ao dono, curto: o bug (ou o lote), o PR mergeado em `dev`, o placar da conferência e o CI, as decisões
tomadas por delegação (uma linha cada), as pendências da promoção para a `main` (que é dele — inclusive
os PRs do dependabot superados e qualquer ação manual em produção) e o que só ele faz — inclusive a
frase do `CLAUDE.md` que ficou sem autorização, com a linha e o texto proposto. O detalhe fica no plano
e nos relatórios em `.codeflow/checkpoints/`.

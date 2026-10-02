---
versão: 1.0
status: experimental
atualizado: 2026-10-02
granularidade: médio
gera_decision: no
usa_checkpoints: no
politica_falhas: padrão
escopo: projeto (CalorIA) — trilha de melhorias e features no Maestri; não toca o framework universal
---

# Workflow: orquestrar-melhorias

## Quando usar

No workspace **CalorIA · Melhorias & Features** do Maestri (worktree `~/Projetos/CalorIA-wt/melhorias`),
no terminal com o **modo Maestro ligado**. Este chat vira o **Maestro da trilha de mudança**: tria o
pedido com o dono e conduz o **ciclo de mudança** do codeflow, um terminal por passo, até o merge no
`dev`:

```
dono + Maestro ─► Planejador ─► DONO APROVA ─► Implementador ─► Revisor ─► PR ─► CI ─► merge no dev
  (triagem)       /plan-change   o plano       /implement-change /review-change   verde  (o Maestro,
                                                (etapas, commit   (terminal limpo,        gh pr merge
                                                 por etapa)        validação local)       --merge)
```

**Melhoria** (muda o que já existe — `tipo: evolução` no registro) e **feature** (capacidade nova
dentro de uma área existente — `tipo: feature`) seguem **o mesmo caminho**; o tipo muda o registro, não
o processo (vocabulário de `tipo` em `.codeflow/melhorias/INDEX.md`). `tipo: módulo novo` (área nova
inteira) é, em geral, grande. **Pequena** = uma etapa; **média** = duas a quatro. **Grande** não é
desta trilha: é registrada e entregue ao workspace **CalorIA · Spec** (`/orquestrar-spec`), que a fatia
pelo `/create-spec`. O Maestro **não escreve código de produção** e **não usa subagente**.

Argumento: o pedido (texto do dono, um item da lista que a trilha de Auditoria entregou) ou uma
melhoria já registrada em `.codeflow/melhorias/` (as 001–004 estão `a fatiar` desde 09/07).

**O que vale aqui** — a decisão de operação do CalorIA
(`.codeflow/decisions/2026-10-02-operacao-por-trilhas-no-maestri.md`): o Maestro **faz o merge dos
próprios PRs para `dev`**, depois de revisão em terminal limpo e do CI verde, sem squash e sem rebase
(item 1); o gate do merge é **revisor limpo + validação completa local + CI verde no PR** (item 2);
**`main` é do dono** (item 3); ramo por tarefa e PR (item 5); **atribuição a IA proibida** (item 6); a
infra é da pasta principal (item 7); banco e Redis da trilha (item 8); a validação completa é uma só
(item 9); fila da máquina (item 10); números pelo alocador (item 11); documentos vivos (item 12); PR só
de documentos (item 13).

## Quando NÃO usar

- Fora do Maestri, ou sem o modo Maestro → os três workflows do ciclo direto, com o dono no chat.
- Para **bug** (o sistema faz algo diferente do prometido) → workspace CalorIA · Bugs,
  `/orquestrar-bugs`. Só aquele Maestro numera bug.
- Para mudança **grande** já sabida (módulo novo, fatiamento em fases) → workspace CalorIA · Spec,
  `/orquestrar-spec`. Esta trilha só a registra (Passo 2, caminho grande).
- Para mudança de **regra de negócio** — metas e limites nutricionais, o limiar do sanity check
  calórico, política de fotos, rate limit, o que conta como dado de saúde — sem decisão do dono: a
  regra se decide antes de virar código (skill `change-sizing`, passo 1). Registrar e parar.
- Para promover `dev → main`, ou tocar os PRs do dependabot → é do dono (decisão de operação, item 3).
- Para várias mudanças → uma de cada vez; esta trilha não tem modo lote. A lista da Auditoria é triada
  item a item.

## LEIA TAMBÉM

- `.codeflow/constitution.md` (invariantes, áreas de alto risco, DoD) · `.codeflow/INDEX.md` ·
  `.codeflow/manifest.md` (validado em 01/07; os gates que valem nas trilhas são os da decisão de
  operação, item 9, não o `make check`)
- `.codeflow/melhorias/INDEX.md` — a convenção de enumeração, as colunas e os vocabulários de `tipo` e
  `status`; o molde do registro são os arquivos vizinhos (ex.: `004-contexto-de-refeicao.md`,
  frontmatter `id · slug · título · tipo · área · esforço · prioridade · status · … · linked_spec`).
- `.codeflow/decisions/2026-10-02-operacao-por-trilhas-no-maestri.md` — a decisão de operação, citada
  como "decisão de operação do CalorIA, item N" · `.codeflow/decisions/INDEX.md`
- `CLAUDE.md` (commits, `CHANGELOG.md`, `Roadmap.md`) · `docs/architecture.md` (os ADR-NNN)
- `~/.codeflow/framework/library/skills/change-sizing/SKILL.md` — o Maestro a usa na triagem.
- `~/.codeflow/framework/library/templates/changes/README.md` — o ciclo e os artefatos.
- `~/.codeflow/framework/library/skills/modo-delegado/SKILL.md` e os workflows `plan-change`,
  `implement-change` e `review-change` do framework — **quem os lê é o recruta**; o Maestro lê só o
  bastante para despachar (o formato do `PLANO.md`, do `EXECUCAO.md` e da `REVISAO-<n>.md`).

## Antes de começar

- **Situar-se:**
  - `git rev-parse --show-toplevel` tem de ser `~/Projetos/CalorIA-wt/melhorias`, e `maestri list` tem
    de mostrar `maestro: true`. Se não, parar e avisar o dono.
  - O ambiente da trilha: `~/.config/caloria/orquestracao/melhorias.env` existe (define o
    `TEST_DATABASE_URL` do `caloria_test_melhorias` na porta 5442 e o `REDIS_URL` com índice próprio —
    decisão de operação, item 8). Nunca imprimir o conteúdo.
  - A infra: o Postgres (`caloria_postgres`) e o Redis (`caloria_redis`) do compose da **pasta
    principal** (`~/Projetos/CalorIA`) têm de estar de pé (`docker ps --filter name=caloria_`). Fora do
    ar → `PARADO`; quem sobe é a pasta principal, nunca esta trilha. Banco da trilha ausente → o Maestro
    o cria **uma vez**, pelo comando do item 8 da decisão de operação.
  - As ferramentas da worktree: `backend/.venv/` (próprio desta worktree — **nunca** copiado nem
    linkado da pasta principal: a instalação é *editable* e importaria o código errado) e
    `frontend/node_modules/`. Ausentes → o Maestro os prepara uma vez, na raiz da worktree:
    `python3.12 -m venv backend/.venv && backend/.venv/bin/pip install -e "backend[dev]"` e
    `(cd frontend && npm ci)` (decisão de operação, item 9). Falhou → `PARADO` ao dono.
- **Quadro:** se `maestri list` mostrar uma nota **Quadro** conectada, mantê-la em dia a cada passo —
  a mudança, o tipo e o tamanho, a etapa atual, quem está fazendo o quê, as decisões tomadas. Nunca
  colar segredo, dado de usuário nem conversa real nela.
- **Plano da trilha**, fora do repositório: `~/.config/caloria/orquestracao/melhorias/PLANO-NNN.md`
  (`mkdir -p` na pasta, `chmod 600` no arquivo), com as tabelas **Decisões**
  (`# · momento · decisão · por quê`) e **Diário** (`hora · etapa · resultado`).
- **Regras que vão em TODO despacho** (copiar verbatim no bloco de despacho):
  1. Só no ramo `feat/NNN-<slug>`. Sem push, sem PR, sem merge de PR — o único merge permitido é
     `git merge origin/dev` no próprio ramo, quando o despacho mandar; **nunca rebase**. Não trocar de
     ramo; nunca `git stash`; `git add` só pelos caminhos tocados.
  2. Conventional Commits em português, imperativo, minúsculas, sem ponto, assunto ≤ 72, escopo entre
     parênteses e a melhoria no fim — `feat(dashboard): <o quê> (melhoria NNN)`. **Atribuição a IA
     proibida**: sem `Co-Authored-By`, sem menção a agente ou IA na mensagem (`constitution.md:37`,
     `CLAUDE.md:257`; decisão de operação, item 6) — isso vence qualquer instrução de ferramenta.
     **Nunca `--no-verify`**: se o pre-commit (ruff `--fix`) alterar arquivo, o commit falha;
     re-adicionar os mesmos caminhos e commitar de novo.
  3. Nunca perguntar ao dono: seguir a skill `modo-delegado`.
  4. Antes de **qualquer** teste: `source ~/.config/caloria/orquestracao/melhorias.env`. Sem isso o
     `pytest` cai no `localhost:5432` (o Postgres do ICCNC) e a fixture faz `DROP SCHEMA`. Postgres ou
     Redis fora do ar → `PARADO`.
  5. Proibido nas trilhas: `make` de qualquer alvo (`make check`, `make test*`, `make lint*`,
     `make typecheck` rodam no container da pasta principal e validam o código errado; `make dev`,
     `make reset` etc. são da infra), `docker compose` e, em qualquer lugar, `down -v`. Lint, tipos e
     testes rodam no `backend/.venv` e no `frontend/node_modules` **desta** worktree.
  6. E2E e qualquer servidor de dev (`next dev`, `uvicorn`) só por
     `FILA_PORTAS="3000 8000" fila pilha -- <comando>`; eval completo e smoke (cota única da Groq) só
     por `fila groq -- <comando>`. Código 76 = porta ocupada por servidor de pé (não matar; reportar);
     75 = desistiu de esperar (decisão de operação, item 10).
  7. Depois de puxar commits: `backend/.venv/bin/pip install -e "backend[dev]"` se o
     `backend/pyproject.toml` mudou; `(cd frontend && npm ci)` se o `package-lock.json` mudou.
  8. Segredo nunca impresso nem commitado (`.env`, `vapid_private.pem`, chaves); `GROQ_API_KEY` nunca
     chega ao front; dado de usuário real (refeição, peso, humor, foto) nunca em fixture, log, commit
     ou retorno.
  9. Testes: o Implementador roda o subconjunto que prova a etapa; a **validação completa** (decisão
     de operação, item 9) é do Revisor, uma vez.
  10. Decision que o workflow gerar (`gera_decision: auto` do `/implement-change`) nasce em
      `.codeflow/decisions/AAAA-MM-DD-<slug>.md`, **sem linha no `decisions/INDEX.md`** — quem a
      registra no índice é o Maestro, no fechamento (decisão de operação, item 11).
  11. Retorno em no máximo 15 linhas; o detalhe fica em `.codeflow/checkpoints/`.

**Formato do bloco de despacho** (o prompt que o Maestro manda a cada recruta):

```
MODO DELEGADO — antes de tudo, leia e siga ~/.codeflow/framework/library/skills/modo-delegado/SKILL.md.
Orquestrador: <nome do Maestro em `maestri list`>
Pasta: ~/Projetos/CalorIA-wt/melhorias — comece com `cd ~/Projetos/CalorIA-wt/melhorias`.
Ramo: feat/NNN-<slug>
Workflow: <comando e alvo>
Decisões delegadas:
  1. <...>
Regras do projeto: <as onze acima, verbatim>
Commitar ao fim: sim | não   (o Revisor do PR só de documentos: não)
```

**A validação completa** (a que o Revisor roda, e que o merge exige) é **a validação completa da
decisão de operação do CalorIA, item 9** — a lista mora lá, uma só para as trilhas; este roteiro não a
repete. Ela roda na raiz da worktree, com o `melhorias.env` carregado. Ela substitui, nas trilhas, o
`make check` da DoD (`constitution.md:58`), que não funciona fora da pasta principal. A saída do
`pytest` traz a **contagem** de testes e a cobertura: integração pulada ou erro de conexão é sinal de
ambiente errado, e o resultado não vale. Vermelho que já existe em `origin/dev` não reprova a mudança,
mas tem de ser **medido no HEAD de `origin/dev`** e citado, nunca presumido.

**O E2E** (`npm run test:e2e`, fora do CI) entra só quando o `PLANO.md` o declarar como prova de um
critério de aceite, e sempre pela fila, numa chamada só:

```bash
FILA_PORTAS="3000 8000" fila pilha -- npm --prefix frontend run test:e2e
```

- O Playwright sobe o `next dev` na 3000 sozinho (`frontend/playwright.config.ts`, `webServer`) e
  reaproveitaria um servidor alheio — por isso a fila confere a 3000 livre (o ICCNC usa a mesma
  porta). Exige `frontend/.env.local` na worktree; ausente → `PARADO` (o Maestro não copia segredo).

**Com o backend real na 8000** — quando o critério o exige (o `PLANO.md` diz) —, o banco é **próprio do
E2E**, `caloria_e2e_melhorias`: **nunca** o `caloria_test_melhorias`, que a suíte zera a cada rodada.
O Maestro o cria **uma vez**, como o banco de teste (decisão de operação, item 8):
`docker exec caloria_postgres psql -U caloria -d caloria_db -c 'CREATE DATABASE caloria_e2e_melhorias;'`.
A rodada inteira — migration, API, E2E e derrubada — fica dentro de **uma** chamada da fila:

```bash
source ~/.config/caloria/orquestracao/melhorias.env
E2E_DB="$(printf '%s' "$TEST_DATABASE_URL" | sed 's#/caloria_test_melhorias#/caloria_e2e_melhorias#')"
case "$E2E_DB" in *:5442/caloria_e2e_melhorias*) ;; *) echo "banco de E2E fora do padrão"; exit 1;; esac
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

- A URL do banco é derivada sem ser impressa (o terminal aparece no canvas), e a guarda do `case`
  recusa qualquer outro banco. O `alembic` e a API leem o `DATABASE_URL` exportado
  (`backend/alembic/env.py` usa `settings.DATABASE_URL`).
- A API roda **sem `--reload`** (o watcher sobreviveria e seguraria a 8000) e é derrubada **pelo
  próprio PID** no `trap` — nunca `pkill`. O código de saída é o do E2E.
- O banco de E2E acumula as contas que o `auth.spec.ts` cadastra; o teste de login com usuário
  existente se pula sem `E2E_LOGIN_EMAIL`/`E2E_LOGIN_PASSWORD`, e essas credenciais nunca entram no
  repositório.

## Protocolo

### Passo 1 — Triar com o dono (o único passo de conversa)
- **Primeiro, de quem é o pedido:**
  - O sistema faz algo diferente do prometido → é **bug**: devolver ao dono para a trilha de Bugs.
  - Muda regra de negócio (ver *Quando NÃO usar*) → **parar**: o dono decide a regra antes do código.
  - Item que já tem destino numa spec em andamento → fica com a trilha de Spec.
- **Depois a skill `change-sizing`:** tipo (`evolução`, `feature` ou `módulo novo`) e tamanho, sinal
  por sinal, com evidência. **Somar a régua do CalorIA** — qualquer um destes é **grande**, mesmo que
  os outros sinais digam pequena:
  - **migration destrutiva ou irreversível** (`backend/alembic/`; migration aplicada é imutável —
    `constitution.md`, áreas de alto risco). Migration **aditiva e reversível** é média;
  - **mudança de contrato da API consumida pelo front** — os schemas de `backend/app/schemas/` e as
    rotas de `backend/app/api/v1/` que `frontend/lib/api.ts` e os hooks consomem: request, response,
    rota ou semântica de erro;
  - **mudança no pipeline de IA que exige eval completo** — `backend/app/services/ai/`, os prompts,
    o `food_lookup`, o sanity check calórico: o que a análise de refeição responde muda (o eval
    completo gasta a cota única da Groq e mora na trilha de Spec);
  - **auth** — `backend/app/core/security.py`, `core/deps.py`, `api/v1/auth.py`,
    `services/auth_service.py`, a sessão do front;
  - **ADR nova** em `docs/architecture.md` (a própria `change-sizing` já a trata como grande);
  - **`módulo novo`** — área nova inteira (as 001–003 são o exemplo).
- O Maestro **propõe** tipo, tamanho, esforço e prioridade, com o porquê; **o dono decide**. Fechar
  com ele as **decisões delegadas** (o que o Planejador e o Implementador vão responder sozinhos).
  Registrar no plano e no Quadro.
- Gate: o dono decidiu o tipo, o tamanho, a prioridade e o escopo.

### Passo 2 — Registrar e abrir o ramo
- **Já registrada:** pular a numeração; abrir o ramo com o número e o slug do arquivo existente.
- **Nova:**
  - O número vem **só** de `caloria-proximo-numero melhoria` (olha todos os ramos e todas as
    worktrees). Nunca o `proximo_numero` do INDEX sozinho: duas worktrees o leem igual. Só este Maestro
    numera melhorias (decisão de operação, item 11).
  - `git fetch origin && git switch -c feat/NNN-<slug> origin/dev` — **nunca** `git switch dev` (o
    `dev` está aberto na pasta principal).
  - Criar `.codeflow/melhorias/NNN-<slug>.md` no molde dos vizinhos: frontmatter completo, com o
    `tipo` do vocabulário do INDEX (`evolução`, `feature` ou `módulo novo`), `proposta_por: owner` e
    `linked_spec: —`, e as seções de relato e proposta. Acrescentar a linha na tabela do `INDEX.md` e
    pôr `proximo_numero` = NNN + 1.
  - **Regra da linha do índice** (colunas `# · arquivo · título · tipo · esforço · prioridade · status
    · criada`): só a célula **status** é **trocada**, inteira, a cada mudança de estado
    (`a fatiar` ou `em andamento: feat/NNN-<slug>` → `entregue: <sha>`); o histórico do porquê mora no
    arquivo da melhoria. As outras células nunca perdem texto. Depois de cada edição, conferir a
    linha, não a presença do texto: `grep -c '^| NNN |' .codeflow/melhorias/INDEX.md` = 1 e
    `grep '^| NNN |' .codeflow/melhorias/INDEX.md | sed 's/\\|//g' | awk -F'|' '{print NF-2}'` = 8
    colunas (o `sed` tira o `\|` escapado de um título antes de contar).
  - Commitar só o registro: `docs(melhorias): registra a melhoria NNN`.
- **Grande:** `status: a fatiar` (o vocabulário do INDEX para "vai virar spec"), e o arquivo diz o
  sinal da régua que a fez grande. Push e `gh pr create --base dev` só com o registro. É um **PR só de
  documentos** (decisão de operação, item 13): um Revisor em terminal limpo (bloco de despacho,
  `Commitar ao fim: não`) confere, sem a suíte:
  - o **escopo do diff** — `git diff --name-only origin/dev...HEAD` lista só `.md` em `.codeflow/` ou
    `docs/`;
  - o **gitleaks do ramo** — o da validação completa (decisão de operação, item 9), que varre só os
    commits do ramo;
  - o **dado pessoal** — `git diff --name-only origin/dev...HEAD | xargs grep -lE
    '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}|[0-9]{3}\.?[0-9]{3}\.?[0-9]{3}-?[0-9]{2}'` lista
    **só nomes de arquivo**, nunca o valor (o terminal aparece no canvas); arquivo listado é aberto e
    conferido à mão (e-mail de exemplo passa; dado de usuário real, não).

  Com o Revisor `CONCLUÍDO`, os três limpos e o CI do PR verde, o merge segue o Passo 7. Avisar o
  dono: *"leve ao workspace CalorIA · Spec — `/orquestrar-spec` a partir da melhoria NNN"*. Quem troca
  o status para `spec: NNN-<slug>` e preenche o `linked_spec` é a trilha de Spec, quando a spec nascer
  (`melhorias/INDEX.md`, "Relação com `specs/`"). Fim do caminho grande; seguir para o Passo 7.
- Gate: ramo nascido de `origin/dev`; o registro commitado; número sem colisão.

### Passo 3 — Planejar (Planejador)
- Recruta em terminal limpo: `maestri recruit "<codinome>" --preset "Claude Code"` — **sem `--role`**
  (a role muda o diretório de trabalho) —, ou um existente depois de
  `maestri ask "<nome>" --raw "/clear\n"`.
- Workflow `/plan-change` sobre `.codeflow/melhorias/NNN-<slug>.md`, com o slug do ciclo `NNN-<slug>`
  (os artefatos ficam em `.codeflow/changes/NNN-<slug>/`) e as decisões delegadas. No bloco, a régua de
  grande do Passo 1, para o Planejador aplicá-la também. Rodar o `maestri ask` **em segundo plano** — o
  Maestro continua livre para o dono.
- Os gates de cada etapa do plano têm de ser comandos reais rodáveis na worktree — recortes da
  validação completa (item 9), como `backend/.venv/bin/pytest tests/unit/<arquivo>` com o
  `melhorias.env` carregado, ou `(cd frontend && npm test -- <arquivo>)`. Nunca `make`.
- Se o Planejador reclassificar como **grande** (`PARADO` do `plan-change`), levar ao dono e, se ele
  concordar, seguir pelo caminho grande do Passo 2.
- Gate: `PLANO.md` commitado com `status: proposto`.

### Passo 4 — Aprovação do dono (o portão do ciclo)
- Mostrar ao dono o plano em poucas linhas: objetivo, fora de escopo, critérios de aceite, as etapas
  (com os gates) e os riscos — em especial migration e o que muda na tela do usuário.
  **Nada se implementa sem o "aprovado" dele.** A autonomia do item 1 da decisão de operação é sobre o
  merge no `dev`, não sobre o plano.
- Ajuste pedido → o **mesmo** Planejador corrige, e o plano volta ao dono.
- Aprovado → o Maestro troca `status: aprovado`, com `aprovado_por` e `aprovado_em`, marca a melhoria
  `em andamento: feat/NNN-<slug>` (arquivo e a célula status do índice, pela regra da linha do Passo 2)
  e commita só isso (`docs(melhorias): aprova o plano da melhoria NNN`). Registrar no plano da trilha.
- Gate: `PLANO.md` com `status: aprovado` commitado.

### Passo 5 — Implementar (Implementador)
- Recruta em terminal limpo, workflow `/implement-change` sobre `.codeflow/changes/NNN-<slug>/`. Em
  segundo plano. Retornos: `CONCLUÍDO`, `PRECISA DE DECISÃO`, `PARADO` (skill `modo-delegado`).
- `PRECISA DE DECISÃO` → ratificar ou corrigir cada uma (registrar no plano) e responder ao **mesmo**
  Implementador. Desvio que muda escopo ou critério de aceite, ou que acende um sinal da régua de
  grande (um schema consumido pelo front mudou, por exemplo) → levar ao dono antes de seguir.
- Se o `/implement-change` gerar uma decision, ela vem **sem linha no INDEX** (regra 10 do despacho); o
  Maestro anota no plano da trilha e a registra no Passo 7.
- Gate: retorno `CONCLUÍDO`; todas as etapas commitadas, uma por commit; `EXECUCAO.md` commitado.

### Passo 6 — Revisar (Revisor, em terminal limpo)
- Um terminal que **não viu** o plano nascer nem a implementação: recruta novo, ou o Revisor anterior
  depois de `/clear`. **Nunca** o Implementador nem o Planejador. Workflow `/review-change`.
- No bloco, a **validação completa da decisão de operação, item 9**, mais o E2E pela fila quando o
  `PLANO.md` o declarou, que o Revisor roda **uma vez** e cola com a saída real na `REVISAO-<n>.md`.
- `APROVADO` → Passo 7. Os IMPORTANTES sem conserto barato viram melhoria nova: conversada com o dono
  agora e anotada no plano da trilha, mas **registrada só depois do merge** desta, com a pasta de volta
  ao `origin/dev` (o Passo 2 abre ramo, e a pasta está no `feat/NNN` corrente).
- `AJUSTAR` → os BLOQUEANTES voltam ao **mesmo** Implementador (`/implement-change` em rework), e a
  revisão seguinte é em terminal limpo de novo. **Teto: duas reprovações** — na terceira, o dono decide.
- Gate: `REVISAO-<n>.md` com `APROVADO` e a validação completa verde, com saída real.

### Passo 7 — Fechar, mergear no `dev`, devolver a pasta
- **Caminho grande:** não há fecho de registro (ele fica `a fatiar`) nem decision; o gate do merge é
  o Revisor do PR só de documentos (Passo 2) mais o CI verde, e trazer o `origin/dev` pede que ele
  rode de novo os três itens. O resto do passo vale igual.
- **Registrar a decision**, se o `/implement-change` gerou uma: a linha no
  `.codeflow/decisions/INDEX.md` (data · título · status · tags), no formato das vizinhas. Decision é
  por data e slug, sem número (decisão de operação, item 11).
- **Fechar o registro:** no arquivo (`status`, `atualizada`) e na célula status do índice,
  `entregue: <sha>`, com o `sha` da última etapa; a linha conferida pelas 8 colunas (regra do Passo 2).
- **Documentos vivos** (decisão de operação, item 12): uma entrada em `CHANGELOG.md`, sob
  `## [Não lançado]`, na seção certa (`### Adicionado`, `### Alterado`, `### Corrigido`), no estilo das
  vizinhas; e, se a melhoria corresponde a um item do `Roadmap.md`, marcá-lo `[x]`. O `CLAUDE.md` só
  com **autorização do dono no chat**; sem ela, a frase que a mudança tornou falsa vai para o resumo
  final como pendência do dono, com a linha e o texto proposto. Commitar:
  `docs(melhorias): marca a melhoria NNN como entregue`. Commit só de documentos depois da validação
  **não a reabre**: o Maestro confere com `git diff --stat <sha validado>..HEAD` que nada fora de
  documentos mudou e roda só o gitleaks do ramo.
- **Se o `origin/dev` andou** desde a validação do Revisor: **nunca** rebase (reescreve os `sha` que o
  `EXECUCAO.md` e a `REVISAO-<n>.md` citam — e o `settings.local.json` da worktree o nega). Trazer o
  `dev` com `git merge origin/dev` e assunto `chore(melhorias): traz o origin/dev para a melhoria NNN`
  (decisão de operação, item 1). **Conflito** é trabalho de código: o **mesmo** Implementador o
  resolve; só vai ao dono se a resolução mudar escopo ou critério de aceite. Depois, um Revisor em
  terminal limpo roda de novo **só a validação completa** sobre o novo HEAD, antes do merge do PR, e a
  saída vai para o plano da trilha e para o corpo do PR.
- **PR:** `git push -u origin feat/NNN-<slug>` e `gh pr create --base dev` — **nunca** base `main`. O
  corpo: contexto (a melhoria e o link do registro), o que mudou (as etapas e os `sha`), como se prova
  (o veredito da revisão e a saída resumida da validação completa) e as **pendências da promoção**
  (migration nova → o dono a confere antes do PR `dev → main`). **Sem rodapé nem menção a IA**
  (decisão de operação, item 6).
- **Merge — do Maestro** (decisão de operação, itens 1 e 2): revisão `APROVADO` + validação completa
  verde sobre o código que vai para o `dev` + **CI verde no PR**. Logo depois do `gh pr create` o
  GitHub ainda não registrou os checks, e o `gh pr checks` sai com 1 ("no checks reported") — que não é
  CI vermelho. Primeiro esperar o primeiro check aparecer (até ~2 min), e só então acompanhar:

  ```bash
  for i in $(seq 24); do
    [ "$(gh pr view <n> --json statusCheckRollup -q '.statusCheckRollup | length')" -gt 0 ] && break
    sleep 5
  done
  gh pr checks <n> --watch
  ```

  Nenhum check depois da espera → `PARADO` ao dono (o CI do PR para `dev` não disparou — item 2), nunca
  lido como vermelho. Os jobs `Backend — lint e testes` e `Frontend — lint e build` têm de ter rodado e
  passado →
  `gh pr merge <n> --merge --delete-branch` (o ramo remoto é apagado no merge — decisão de operação do
  CalorIA, item 1). **Nunca squash**: os artefatos citam o `sha` de cada etapa. CI vermelho →
  os achados voltam ao **mesmo** Implementador, e a revalidação é em terminal limpo. Registrar no plano.
- **Depois do merge:** `git fetch origin && git switch --detach origin/dev && git branch -d
  feat/NNN-<slug>`. Dispensar os recrutas (`maestri dismiss`) se não houver outra mudança na fila.
  Limpar o Quadro.
- Gate: PR mergeado no `dev` com merge commit e CI verde; o registro `entregue` com o `sha`; o
  `CHANGELOG.md` em dia; a pasta de volta ao `origin/dev`, sem ramo velho.

## Proibições durante este workflow

- O Maestro não escreve código de produção nem roda ele mesmo o `/plan-change`, o `/implement-change`
  ou o `/review-change`. Não usar subagente — cada passo é um terminal.
- Não implementar sem o plano **aprovado pelo dono**; não deixar o Implementador revisar o próprio
  trabalho; não rebaixar uma mudança grande para caber no ciclo.
- Não decidir tipo, tamanho, prioridade nem escopo sem o dono; não decidir regra de negócio.
- Não numerar bug nem spec; não numerar melhoria pelo `proximo_numero` sozinho — só
  `caloria-proximo-numero melhoria`.
- Não abrir PR para `main`, não fazer merge nela, não tocar os PRs do dependabot (decisão de operação,
  item 3). Não fazer push direto para `dev`. Nunca squash; nunca rebase.
- Não mergear sem revisor limpo, validação completa verde sobre o código que vai para o `dev` e CI
  verde no PR; o PR só de documentos, sem o Revisor do item 13.
- Não rodar `make`, `docker compose` nem `down -v`; não rodar teste sem o `melhorias.env` carregado;
  não rodar E2E, servidor de dev, eval completo ou smoke fora da fila.
- Não pôr atribuição a IA em commit, PR ou comentário (`Co-Authored-By`, rodapé de ferramenta).
- Não editar `.env`, `CLAUDE.md` (sem autorização do dono), `.codeflow/INDEX.md`, a constitution, os
  workflows do CI nem outro roteiro.
- Não colar segredo, credencial, dado de usuário ou conversa real no canvas, nos despachos, no plano
  ou no PR.

## Definition of Done

- [ ] Pedido triado: bug e regra de negócio desviados; tipo e tamanho pela `change-sizing` somada à
      régua do CalorIA, decididos pelo dono, com esforço e prioridade.
- [ ] Número de `caloria-proximo-numero melhoria`; registro no molde e linha no índice;
      ramo `feat/NNN-<slug>` nascido de `origin/dev`.
- [ ] **Grande:** registro `a fatiar` revisado como PR só de documentos (escopo, gitleaks do ramo,
      grep de dado pessoal) e com CI verde, mergeado no `dev`, e o dono avisado para levá-lo à trilha
      de Spec.
- [ ] **Pequena ou média:** plano escrito por um Planejador e **aprovado pelo dono** antes de qualquer
      código; etapas implementadas com um commit por etapa; revisão `APROVADO` por um terminal que não
      viu nada, com a validação completa verde e saída real.
- [ ] Cada passo num terminal próprio; nenhum subagente; commits e PR **sem atribuição a IA**.
- [ ] Decision gerada pelo `/implement-change`, se houver, com a linha no `decisions/INDEX.md`.
- [ ] `entregue: <sha>` (arquivo e índice, linha conferida); `CHANGELOG.md` atualizado; PR para `dev`
      mergeado pelo Maestro com `--merge` e CI verde; a pasta de volta ao `origin/dev`; o plano com
      todas as decisões e o diário.

## Resumo final

Ao dono, curto: a mudança, o tipo e o tamanho, o PR e o `sha` do merge, o veredito da revisão, a
validação e o CI que o sustentaram, as decisões tomadas por delegação (uma linha cada) e o que só ele
faz — em especial o que pesa no PR `dev → main` (migration nova) e a frase do `CLAUDE.md` que ficou
falsa, se ele não autorizou a edição (linha e texto proposto). O detalhe fica no plano da trilha e nos
relatórios em `.codeflow/checkpoints/`.

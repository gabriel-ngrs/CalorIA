---
versão: 1.0
status: experimental
atualizado: 2026-10-02
granularidade: médio
gera_decision: no
usa_checkpoints: no
politica_falhas: padrão
escopo: projeto (CalorIA) — trilha de auditoria no Maestri; não toca o framework universal
---

# Workflow: orquestrar-auditoria

## Quando usar

No workspace **CalorIA · Auditoria** do Maestri (worktree `~/Projetos/CalorIA-wt/auditoria`), no
terminal com o **modo Maestro ligado**, **sob demanda do dono**. Este chat vira o **Maestro da
auditoria**: combina com o dono as dimensões e o alvo, abre **um auditor por dimensão, em paralelo**,
cada um num terminal limpo, e depois **um Verificador** em terminal limpo que confirma os achados,
consolida e roda a validação completa local. A auditoria **só aponta**: não corrige código e não
registra nem numera bug ou melhoria — o consolidado aprovado pelo dono vai para as trilhas de Bugs
(modo lote) e de Melhorias & Features, que registram e corrigem.

```
dono + Maestro ─► Auditores em paralelo ─► Verificador ─► DONO APROVA ─► PR para dev ─► Revisor
  (dimensões        /audit <dimensão>        /verify-audit   o consolidado  (só documentos)  limpo
   e alvo)          /security-sweep          + validação                                      │
                    (estático, a partir      completa local                  CI verde         │
                     da passada de 17/09)                                    merge --merge ◄──┘
                                                                     │
                                          lista para Bugs (lote) e Melhorias & Features
```

## Quando NÃO usar

- Para revisar um PR ou uma mudança → a revisão da trilha correspondente (`orquestrar-bugs`,
  `orquestrar-melhorias`, `orquestrar-spec`).
- Para corrigir o que a auditoria achou → `/orquestrar-bugs lote` e `/orquestrar-melhorias`.
- Para corrigir o lote do `/security-sweep` de 17/09
  (`.codeflow/bug-batches/security-sweep-2026-09-17.md`) → ele já está pronto para o
  `/orquestrar-bugs lote`; não precisa de nova auditoria.
- Para teste ativo contra ambiente vivo (a produção na netcup) → fora daqui: o `/security-sweep`
  desta trilha é **estático**.
- Para medir a qualidade da IA (eval completo, smoke) → é da trilha que muda o pipeline, pela fila
  `groq`; a auditoria não gasta a cota do provedor.

## LEIA TAMBÉM

- `.codeflow/constitution.md` (invariantes, áreas de alto risco, DoD) · `.codeflow/INDEX.md` ·
  `.codeflow/manifest.md` · `.codeflow/discovered.md` (áreas "não tocar") · `CLAUDE.md` ·
  `docs/architecture.md` (ADR-001…ADR-009) · `.codeflow/decisions/INDEX.md`
- `.codeflow/decisions/2026-10-02-operacao-por-trilhas-no-maestri.md` — a **decisão de operação do
  CalorIA**: merge autônomo (item 1), CI no PR (2), `main` do dono (3), ramos (5), atribuição proibida
  (6), infra com dono (7), banco e Redis por trilha (8), validação completa única (9), fila (10),
  numeração (11), documentos vivos (12), PR só de documentos (13). Este roteiro a cita como "decisão
  de operação do CalorIA, item N".
- `.codeflow/bug-batches/security-sweep-2026-09-17.md` e
  `.codeflow/decisions/2026-09-17-primeira-passada-security-sweep-caloria.md` — a passada de
  segurança anterior, de onde a nova parte.
- `docs/auditoria/` — a auditoria de 05/2026 (achados `AUD-NNN`). **Só leitura**: é área "não tocar"
  (`discovered.md`); serve de histórico para o auditor dizer se um achado é novo ou reincidente.
- `~/.codeflow/framework/library/templates/audits/README.md` — as dimensões, o fluxo e os moldes
  (`LAUDO.md`, `CONSOLIDADO.md`).
- `.codeflow/workflows/orquestrar-bugs.md` — a mecânica de recruta, o bloco de despacho e o destino da
  seção 3 do consolidado (modo lote); `.codeflow/workflows/orquestrar-melhorias.md` — o da seção 4.
- `~/.codeflow/framework/library/skills/modo-delegado/SKILL.md` e os workflows `audit`,
  `verify-audit` e `security-sweep` do framework — **quem os lê é o recruta**; o Maestro lê só o
  bastante para despachar.

## Antes de começar

- **Situar-se:** `git rev-parse --show-toplevel` tem de ser `~/Projetos/CalorIA-wt/auditoria`, e
  `maestri list` tem de mostrar `maestro: true`. Se não, parar e avisar o dono.
- **Quadro:** se `maestri list` mostrar uma nota **Quadro** conectada, mantê-la em dia — as dimensões,
  o estado de cada auditor, o placar. Nunca colar segredo, dado de usuário (refeição, peso, humor,
  e-mail) nem conversa real nela.
- **Plano da trilha**, fora do repositório (a pasta pode não existir:
  `mkdir -p ~/.config/caloria/orquestracao/auditoria`):
  `~/.config/caloria/orquestracao/auditoria/PLANO-<AAAA-MM-DD>-<slug>.md` (chmod 600), com as tabelas
  **Decisões** (`# · momento · decisão · por quê`) e **Diário** (`hora · etapa · resultado`).
- **Regras que vão em TODO despacho** (copiar verbatim no bloco de despacho):
  1. Só no ramo `chore/auditoria-<AAAA-MM-DD>-<slug>` (decisão de operação, item 5), na pasta
     `~/Projetos/CalorIA-wt/auditoria`. Sem push, sem PR, sem merge; nunca `git switch dev` nem
     trabalho em `dev`/`main`; nunca `git rebase`, `git stash` nem `--no-verify`.
  2. **Auditor não commita** (`Commitar ao fim: não`): vários auditores no mesmo checkout não podem
     commitar ao mesmo tempo — os laudos são do Maestro; o consolidado, do Verificador. Quem commita:
     Conventional Commits em português, imperativo, minúsculas, sem ponto, assunto ≤ 72, escopo entre
     parênteses. **Atribuição a IA proibida** (decisão de operação, item 6; `constitution.md:37`):
     sem `Co-Authored-By`, sem menção a agente ou IA na mensagem — isso vence qualquer instrução de
     ferramenta.
  3. Nunca perguntar ao dono: seguir a skill `modo-delegado`.
  4. Dado de usuário (refeições, peso, hidratação, humor, conversas com a IA, e-mail) e segredo
     **nunca** entram em laudo, consolidado, Quadro, plano ou retorno: o achado cita `arquivo:linha` e
     o padrão, nunca o valor. `.env`, `frontend/.env.local` e `backend/vapid_private.pem` nunca são
     lidos para o laudo nem impressos.
  5. Infra (decisão de operação, item 7): o Postgres (`caloria_postgres`, porta 5442) e o Redis
     (`caloria_redis`, porta 6389) são do compose da pasta principal (`~/Projetos/CalorIA`).
     **Proibido** `make dev/infra/down/reset/prod`, `docker compose`, `down -v`, e **qualquer**
     `make check`, `make test*`, `make lint*`, `make typecheck`, `make build`, `make migrate*`,
     `make seed*` (rodam no container da pasta principal: validam o código errado ou mexem no
     `caloria_db`). Postgres ou Redis fora do ar quando preciso → `PARADO`.
  6. Comandos: **o auditor** roda só o que é leitura, no venv e no `node_modules` desta pasta —
     `backend/.venv/bin/ruff check .` e `ruff format --check .` (de `backend/`), `npm run lint`
     (de `frontend/`), `backend/.venv/bin/pytest tests/unit/ -q` e `npm test -- --passWithNoTests`
     (só a dimensão `tests`, com `source ~/.config/caloria/orquestracao/auditoria.env` antes),
     `gitleaks git`, `osv-scanner`, `semgrep`, `npm audit`, `npm outdated`. **Nunca** `mypy`,
     `npx tsc`, `npm run build`, `pytest` com banco, eval completo, smoke, E2E nem servidor de dev:
     a validação completa e o E2E pela fila são **do Verificador**, uma vez. Nenhum comando grava em
     `backend/evals/runs/history.jsonl`.
  7. Retorno em no máximo 15 linhas; o detalhe fica em
     `.codeflow/checkpoints/relatorio-<workflow>-<dimensão>-<AAAAMMDD-HHMM>.md` (a dimensão no nome:
     auditores em paralelo na mesma pasta não podem colidir no mesmo minuto).

**A régua do CalorIA por dimensão** (vai nas decisões delegadas de cada auditor; a régua do projeto
vence a genérica da skill). Fora do alvo em todas: `docs/auditoria/` e `backend/alembic/versions/`
(áreas "não tocar", `discovered.md`) — lidos, nunca apontados como defeito de edição; e os arquivos
locais ignorados pelo git (`.env`, `frontend/.env.local`, `backend/vapid_private.pem`,
`.claude/`) — não são candidatos.

| Dimensão | Régua do CalorIA | Ferramenta (só leitura) |
| --- | --- | --- |
| `code-quality` | `constitution.md` (todos os tipos anotados, `mypy --strict`; lógica só em `services/`), ruff do `backend/pyproject.toml` (E/F/W/I/N/B/UP, linha 88), ESLint (`frontend/.eslintrc.json`) e `tsc`; DoD da constitution | `ruff check .`, `ruff format --check .`, `npm run lint` (o `mypy` e o `tsc` são do Verificador) |
| `architecture` | camadas `api/` (endpoint fino) → `services/` (classe com `db` injetado) → `models/` + `schemas/`; IA isolada em `services/ai/` (pipeline de dois estágios + sanity check, ADR-006); `workers/` Celery (ADR-004); front em App Router com hooks React Query por domínio via `lib/api.ts`; ADR-001…ADR-009 de `docs/architecture.md` | leitura dirigida; `grep` de import de `models`/`db` em `api/` |
| `tests` | DoD (código novo com teste); ADR-001 (Postgres nos testes, nunca SQLite); `--cov-fail-under=72` do CI; eval rápido (os `tests/unit/test_evals_*.py`); E2E fora do CI | `pytest tests/unit/ -q`, `npm test -- --passWithNoTests` (só eles) |
| `data-privacy` | dado de saúde e alimentação é **sensível** (LGPD, art. 11; `docs/auditoria/achados.md:39`); **fotos de comida não são persistidas** e **`GROQ_API_KEY` nunca vai ao front** (`constitution.md`); `.env` e chaves nunca commitados; log sem token nem dado de usuário; a senha da conta de demonstração é pública **por desenho** (`decisions/2026-08-04-conta-demo-senha-publica-e-isencao-no-gitleaks.md`) — não é candidato | `gitleaks git . --config .gitleaks.toml --redact --no-banner` (o histórico versionado; **nunca** `gitleaks dir .`, ~100% de falso positivo pela passada de 17/09); grep por padrão, sem imprimir o valor |
| `living-docs` | `CLAUDE.md` × `constitution.md` × `docs/` (divergências já conhecidas: next-auth, `docs/git-workflow.md` e `CONTRIBUTING.md` sobre deploy e ramos), `CHANGELOG.md`, `Roadmap.md`, os INDEX de `bugs/`, `melhorias/`, `specs/` (`proximo_numero`) e `decisions/` (decision fora do índice), `manifest.md` (`last_validated`) | arquivos × linhas de índice; `git log` dos arquivos de freshness |
| `dependencies` | `backend/pyproject.toml` + `backend/uv.lock`, `frontend/package.json` + `package-lock.json`; os advisories da passada de 17/09 (crítico em `next`/`next-auth`; alto em `axios`, `starlette`, `python-multipart`) — dizer se **ainda valem**, não repeti-los; os PRs do dependabot para a `main` são do dono | `osv-scanner`, `npm audit`, `npm outdated`, `backend/.venv/bin/pip list --outdated` |
| `interface` | **se aplica** (`frontend/`, Next.js 14 App Router): ADR-007 (glassmorphism + neumorphism), shadcn/ui (Radix), mensagens ao usuário (`sonner`), estados de carga e erro dos hooks React Query; skills `accessibility-audit` e `visual-consistency` | `npm run lint`; leitura estática, sem servidor de dev |
| segurança | áreas de alto risco da `constitution.md` (auth: `core/security.py`, `api/v1/auth.py`, `services/auth_service.py`, `core/deps.py`, blacklist em Redis — ADR-005; `services/ai/`; Web Push/VAPID), IDOR nas rotas por usuário, `SECRET_KEY` sem fail-fast (AUD-039) | `/security-sweep` **estático**, partindo da passada de 17/09 |

## Protocolo

### Passo 1 — Combinar a auditoria com o dono (o único passo de conversa)
- Quais dimensões (todas, ou as que o dono escolher); o alvo (o repositório inteiro, ou caminhos como
  `backend/app/services/ai`); o `<slug>` (ex.: `geral`, `ia`). Data canônica: `date +%F`.
- Montar com o dono as **decisões delegadas** de cada auditor (a régua da tabela, o que fica fora) e
  registrar no plano.
- Gate: dimensões, alvo e slug decididos e registrados no plano.

### Passo 2 — Abrir o ramo e preparar a pasta
- `git fetch origin && git switch -c chore/auditoria-<AAAA-MM-DD>-<slug> origin/dev` — nunca
  `git switch dev` (o `dev` está aberto na pasta principal). A pasta da rodada é
  `.codeflow/audits/<AAAA-MM-DD>-<slug>/`.
- Preparo, **uma vez, pelo Maestro**, antes de qualquer auditor (a pasta tem venv e `node_modules`
  **próprios** — nunca copiar nem linkar o `.venv` da pasta principal, que é *editable* e aponta
  para ela):
  - sem `backend/.venv`: `python3.12 -m venv backend/.venv && backend/.venv/bin/pip install -e
    "backend[dev]"`; se o `pyproject.toml` mudou desde a última rodada, o mesmo `pip install`;
  - sem `frontend/node_modules`, ou com o `package-lock.json` mudado: `(cd frontend && npm ci)`.
- Banco e Redis da trilha (decisão de operação, item 8): conferir `docker exec caloria_postgres
  pg_isready` e `docker exec caloria_redis redis-cli ping`. Fora do ar → os auditores podem rodar
  (não usam banco), mas avisar o dono já: **só a pasta principal sobe a infra**, e o Passo 5 precisa
  dela. Banco `caloria_test_auditoria` ausente → o Maestro o cria uma vez, com o comando do item 8.
- Gate: ramo nascido de `origin/dev`; venv e `node_modules` da pasta prontos; o estado do Postgres,
  do Redis e do banco da trilha no diário.

### Passo 3 — Auditores em paralelo
- Um recruta **por dimensão**, cada um em terminal limpo (`maestri recruit "<codinome>" --preset
  "Claude Code"`, **sem `--role`** — a role muda o diretório do recruta). Recruta reaproveitado só
  depois de `maestri ask "<nome>" --raw "/clear\n"`.
- Despacho: `/audit <dimensão>` com o alvo, o slug e a régua da tabela. O auditor confere
  `docs/auditoria/achados.md`: achado que já existe como `AUD-NNN` entra com a referência e o estado
  atual (resolvido, reincidente, ainda aberto), nunca como novo.
- Segurança é `/security-sweep` com profundidade **estática**, autorização "código próprio, nenhum
  alvo vivo" e escopo igual ao alvo, **partindo da passada de 17/09**: lê o ledger e a decision dela,
  não repete o mapa já coberto sem motivo, e diz, por candidato daquela passada, se ainda vale. Os
  arquivos locais ignorados pelo git ficam fora (o scanner de segredo é o `gitleaks git`). A saída
  fica **na pasta da rodada** (`LEDGER-seguranca.md` e `DECISAO-seguranca.md`), sem escrever em
  `.codeflow/bug-batches/`, `.codeflow/decisions/` nem no `decisions/INDEX.md`: a decisão vai com o
  lote para a trilha de Bugs (Passo 8), que a registra no fechamento.
- Bloco de despacho:

  ```
  MODO DELEGADO — antes de tudo, leia e siga ~/.codeflow/framework/library/skills/modo-delegado/SKILL.md.
  Orquestrador: <nome do Maestro em `maestri list`>
  Pasta: ~/Projetos/CalorIA-wt/auditoria — comece com `cd ~/Projetos/CalorIA-wt/auditoria`.
  Ramo: chore/auditoria-<AAAA-MM-DD>-<slug> (já aberto; não troque).
  Workflow: /audit <dimensão> — alvo <alvo>, slug <AAAA-MM-DD>-<slug>
  Decisões delegadas:
    1. Régua: <a linha da dimensão na tabela do orquestrar-auditoria>.
    2. <o que fica fora do alvo>
  Regras do projeto: <as sete acima, verbatim>
  Commitar ao fim: não.
  ```

- Disparar todos juntos com `maestri ask --batch`, **em segundo plano**. Retornos: o número de
  candidatos por severidade, ou `PARADO` (decidir se couber na delegação; senão levar ao dono).
- Gate: um `LAUDO-<dimensão>.md` por dimensão em `.codeflow/audits/<AAAA-MM-DD>-<slug>/` (e o ledger
  e a decisão do `/security-sweep`, se a dimensão rodou).

### Passo 4 — Commitar os laudos
- O Maestro confere que cada laudo existe e que **nenhum** traz dado pessoal nem segredo, listando
  **só os nomes** dos arquivos (o terminal aparece no canvas):

  ```
  grep -rlE '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}|eyJ[A-Za-z0-9_-]{10,}\.|gsk_[A-Za-z0-9]{20,}|Bearer [A-Za-z0-9]' .codeflow/audits/<AAAA-MM-DD>-<slug>/
  ```

  Arquivo listado é aberto e conferido à mão: e-mail de conta de demonstração ou de teste e
  endereço de exemplo podem ficar; valor real sai do laudo antes do commit.
- `git add .codeflow/audits/<AAAA-MM-DD>-<slug>/` — só a pasta da rodada, `git status` antes — e
  commitar **todos juntos**: `docs(auditoria): registra os laudos da rodada <AAAA-MM-DD>-<slug>`, sem
  atribuição. Dispensar os auditores (`maestri dismiss`).
- Gate: laudos commitados; nada fora da pasta da rodada no commit.

### Passo 5 — Verificar em terminal limpo (Verificador)
- Um terminal que **não foi auditor**: `/verify-audit` sobre a pasta, com `Commitar ao fim: sim` e as
  regras de despacho (a 6 vale ao contrário: a validação é dele). Ele confirma cada candidato,
  deduplica, dá severidade e destino, mede a taxa de falso positivo e roda **a validação completa da
  decisão de operação do CalorIA, item 9**, **uma vez**, como linha de base, com
  `source ~/.config/caloria/orquestracao/auditoria.env` antes e a saída real no relatório (os
  comandos estão só na decisão — uma fonte só).
  - O relatório traz a **contagem** do `pytest` (passados e pulados) e o banco usado (só o nome,
    `caloria_test_auditoria`): sem o `.env` da trilha, o `pytest` cai no `localhost:5432` — o
    Postgres do ICCNC — e a fixture faz `DROP SCHEMA`. Sem a variável, não rodar.
  - **E2E só pela fila** (decisão de operação, item 10) e só se um candidato de `interface` ou
    `tests` precisar de prova em execução. Tudo **numa única chamada da fila**, com a API subida do
    venv e derrubada **pelo próprio PID** (num `trap ... EXIT`) — nunca `make dev`, nunca `pkill`;
    o `next dev` é o `webServer` do Playwright (`frontend/playwright.config.ts`), que exige
    `frontend/.env.local` na pasta — ausente → `PARADO` (o Maestro não copia segredo).
  - O banco é **próprio do E2E**, `caloria_e2e_auditoria` — **nunca** o `caloria_test_auditoria`,
    que a suíte zera a cada rodada (decisão de operação, item 8). O Maestro o cria **uma vez**:
    `docker exec caloria_postgres psql -U caloria -d caloria_db -c 'CREATE DATABASE caloria_e2e_auditoria;'`.
    A mesma receita das trilhas de Spec e Melhorias:

    ```bash
    source ~/.config/caloria/orquestracao/auditoria.env
    E2E_DB="$(printf '%s' "$TEST_DATABASE_URL" | sed 's#/caloria_test_auditoria#/caloria_e2e_auditoria#')"
    case "$E2E_DB" in *:5442/caloria_e2e_auditoria*) ;; *) echo "banco de E2E fora do padrão"; exit 1;; esac
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

    Código 76 = porta ocupada por servidor que ficou de pé — inclusive do ICCNC, que também usa a
    3000 (não matar, reportar); 75 = desistiu de esperar → `PARADO`. E2E que falha por ambiente
    deixa o candidato `não verificado` no consolidado, com o motivo.
  - Eval completo e smoke **não** fazem parte da auditoria; se um candidato de IA só se prova com
    eles, o candidato fica `não verificado` e a prova vai para a trilha de destino (fila `groq`).
- Postgres ou Redis fora do ar → `PARADO` (o Maestro avisa o dono; não sobe infra daqui).
- Gate: `CONSOLIDADO.md` commitado (sem atribuição); linha de base com saída real.

### Passo 6 — Aprovação do dono
- Mostrar ao dono o resumo: o placar, a taxa de falso positivo, o que mais pesa, quantos itens vão
  para Bugs e para Melhorias, quantos `AUD-NNN` reincidem e o que da passada de 17/09 ainda vale. O
  dono pode **tirar** itens ou mudar destino — o Maestro ajusta o consolidado e commita só isso
  (`docs(auditoria): ajusta o consolidado da rodada <AAAA-MM-DD>-<slug>`), registrando no plano.
- Gate: o dono aprovou o consolidado.

### Passo 7 — PR, revisão em terminal limpo, CI e merge no `dev`
- Se o `origin/dev` andou, trazê-lo com `git merge origin/dev` — **nunca rebase**, que reescreve os
  `sha` já citados (decisão de operação, item 1) — com assunto curto e fixo e o ramo no corpo:

  ```
  git merge origin/dev -m "chore(auditoria): traz o origin/dev" -m "Ramo: chore/auditoria-<AAAA-MM-DD>-<slug>"
  ```

- `git push -u origin chore/auditoria-<AAAA-MM-DD>-<slug>` e `gh pr create --base dev --draft`, **só
  com documentos** (laudos, ledger e decisão do sweep, consolidado — decisão de operação, item 13).
  Corpo do PR: contexto, placar, para onde vai cada lista — **sem rodapé de IA** (item 6). Se a
  permissão do terminal negar o `git push`, parar e avisar o dono (não contornar).
- **Revisor** em terminal limpo (nunca auditor nem o Verificador), com o bloco de despacho e
  `Commitar ao fim: não`, sobre o **HEAD que vai ao merge**. É PR só de documentos (item 13):
  confere o **escopo do diff** (`git diff --stat origin/dev...HEAD` só toca arquivos `.md` de
  `.codeflow/audits/<AAAA-MM-DD>-<slug>/`), o gitleaks do ramo (o da validação do item 9) e o grep
  do Passo 4 com `-l` (só os nomes dos arquivos) — **sem** a suíte. Confere também que nenhum commit
  do ramo leva `Co-Authored-By` (`git log origin/dev..HEAD --format=%B | grep -ci co-authored-by` =
  0). Saída real no relatório. Se o `origin/dev` andar de novo depois da revisão, novo `git merge
  origin/dev` e nova revisão limpa sobre o novo HEAD.
- **CI do PR** (decisões de operação, itens 1 e 2): o GitHub leva alguns segundos para registrar os
  checks, e o `gh pr checks` sai com "no checks reported" enquanto isso. Esperar o primeiro check
  aparecer (até ~2 min) e só então acompanhar:

  ```bash
  for i in $(seq 24); do gh pr checks <n> 2>&1 | grep -q 'no checks reported' || break; sleep 5; done
  gh pr checks <n> --watch
  ```

  Ainda sem check depois da espera → `PARADO` ("PR sem nenhum check"; o `ci.yml` deveria rodar em
  `pull_request: [dev]`), nunca lido como CI vermelho.
- Revisor `✓` **e CI verde no PR** → `gh pr ready <n>` e `gh pr merge <n> --merge --delete-branch` — **nunca
  squash** (o ramo remoto é apagado no merge — decisão de operação do CalorIA, item 1). Revisor `✗` ou CI vermelho →
  o Maestro corrige só o documento e um Revisor limpo de novo; **teto: duas reprovações** — na
  terceira, escalar ao dono. Registrar o merge no plano.
- Nenhum PR para `main` e nenhum toque nos PRs do dependabot: a `main` é do dono (item 3).
- Gate: PR mergeado no `dev` com `--merge`, revisão `✓` sobre o HEAD mergeado e CI verde.

### Passo 8 — Entregar as listas e devolver a pasta
- Avisar o dono do próximo passo: a **seção 3** do consolidado vai ao workspace **CalorIA · Bugs**
  (`/orquestrar-bugs lote .codeflow/audits/<AAAA-MM-DD>-<slug>/CONSOLIDADO.md`), que numera e
  registra; a **seção 4**, item a item, ao workspace **CalorIA · Melhorias & Features**
  (`/orquestrar-melhorias`). A `DECISAO-seguranca.md`, se houver, vai **junto com o lote** da seção 3
  — o despacho a Bugs nomeia os dois caminhos: o `CONSOLIDADO.md` (seção 3) **e**
  `.codeflow/audits/<AAAA-MM-DD>-<slug>/DECISAO-seguranca.md`. No fechamento do lote, o Maestro de
  Bugs a leva para `.codeflow/decisions/<AAAA-MM-DD>-<slug>.md` (data + slug, sem número) e acrescenta
  a linha no `decisions/INDEX.md` (decisão de operação, item 11). Esta trilha não a registra.
- Pendências do dono que a rodada levantou e que esta trilha não edita: frase desatualizada no
  `CLAUDE.md` (item 12 — só com autorização do dono no chat), com a linha e o texto proposto.
- `git fetch origin && git switch --detach origin/dev && git branch -d
  chore/auditoria-<AAAA-MM-DD>-<slug>`. Limpar o Quadro; dispensar o Verificador e o Revisor.
- Gate: o dono avisado de para onde vai cada lista; a pasta de volta ao `dev`, sem ramo velho.

## Proibições durante este workflow

- O Maestro não audita, não verifica e não corrige código — cada passo é um terminal. Sem subagente.
- Não deixar um auditor verificar o próprio laudo, nem o Verificador revisar o PR.
- Auditor não commita, não roda `mypy`, `tsc`, `build`, `pytest` com banco, eval, E2E nem servidor
  de dev.
- Não registrar nem numerar bug, melhoria, spec ou ADR (decisão de operação, item 11: o
  `caloria-proximo-numero` é das trilhas de Bugs, Melhorias e Spec); não escrever em
  `.codeflow/bugs/`, `melhorias/`, `specs/`, `bug-batches/`, `decisions/` nem em
  `docs/architecture.md`.
- Não editar `docs/auditoria/` nem `backend/alembic/versions/` (áreas "não tocar"); não editar
  `CLAUDE.md`, `CHANGELOG.md` nem `Roadmap.md` — achado de `living-docs` neles vai ao consolidado e,
  no caso do `CLAUDE.md`, ao resumo como pendência do dono (item 12).
- Não alterar código: o PR da trilha é só de documentos da pasta da rodada.
- Não rodar `make` de infra nem de validação, `docker compose`, `down -v`, `pytest` sem o `.env` da
  trilha, nem matar processo de porta ocupada; E2E só pela `fila pilha`.
- Não gastar a cota da Groq (eval completo, smoke, análise manual de refeição) nem gravar em
  `backend/evals/runs/history.jsonl`.
- Não tocar alvo vivo (a produção); o `/security-sweep` é estático.
- Não abrir PR para `main`, não mexer nos PRs do dependabot; nunca squash, nunca rebase (trazer o
  `dev` é `git merge origin/dev`), nunca `--no-verify`, nunca `git stash`.
- Nenhuma atribuição a IA em commit ou PR.
- Não colar dado de usuário, segredo ou conversa real no canvas, nos despachos, no plano ou nos
  laudos; grep de dado pessoal só com `-l` ou `-c`, nunca mostrando a linha casada.

## Definition of Done

- [ ] Dimensões, alvo e slug decididos com o dono; ramo `chore/auditoria-<AAAA-MM-DD>-<slug>` nascido
      de `origin/dev`; venv e `node_modules` próprios da pasta, preparados pelo Maestro.
- [ ] Um auditor por dimensão, em terminais limpos e em paralelo; nenhum auditor commitou nem rodou
      `mypy`, `tsc`, `build`, `pytest` com banco, eval ou E2E; reincidências de `AUD-NNN` marcadas;
      segurança por `/security-sweep` estático a partir da passada de 17/09, saída na pasta da rodada.
- [ ] Laudos commitados juntos pelo Maestro, sem dado pessoal, sem segredo, sem atribuição e sem nada
      fora da pasta da rodada.
- [ ] Verificador em terminal limpo: cada candidato com veredito e motivo; consolidado com placar e
      taxa de falso positivo; a validação completa do item 9, uma vez, com o `.env` da trilha e a
      saída real.
- [ ] Consolidado aprovado pelo dono.
- [ ] PR só de documentos para `dev` (item 13), revisado por terminal limpo sobre o HEAD mergeado —
      escopo do diff, gitleaks do ramo, grep com `-l`, nenhum `Co-Authored-By` — e com CI verde,
      com o `dev` trazido por `git merge origin/dev` (nunca rebase), mergeado com `--merge`.
- [ ] O dono sabe para onde vai cada lista; a decisão do sweep seguiu com o lote para Bugs; nenhum
      código alterado e nenhum bug ou melhoria registrado por esta trilha; a pasta de volta ao `dev`;
      o plano com todas as decisões e o diário.

## Resumo final

Ao dono, curto: as dimensões auditadas, o placar e a taxa de falso positivo, os três achados que mais
pesam, o que reincide da auditoria de 05/2026 e o que da passada de 17/09 ainda vale, o PR e o `sha`
do merge, as decisões tomadas por delegação (uma linha cada), o que levar para Bugs (com a decisão do
sweep, se houver) e para Melhorias & Features, e as pendências do dono (frases do `CLAUDE.md`). O
detalhe fica no plano e nos relatórios em `.codeflow/checkpoints/`.

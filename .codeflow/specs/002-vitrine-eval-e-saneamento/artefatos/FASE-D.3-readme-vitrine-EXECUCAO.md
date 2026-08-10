---
spec: 002-vitrine-eval-e-saneamento
fase: D.3
slug_fase: readme-vitrine
status: rework
tentativa: 2
reprovacoes: 1
sha_inicial: 5f137f7bc6887de33131daf36586df0c3c316507
sha_final: 049f6e5d1764c7dd6b04af9af16f94e2d1eb873e
range: 5f137f7bc6887de33131daf36586df0c3c316507..049f6e5d1764c7dd6b04af9af16f94e2d1eb873e
---

# FASE D.3 — Relatório de execução

## 1. Resumo do que foi feito

O README foi reescrito como peça de portfólio: comando único (`make init`, que não
era citado uma única vez em nenhum documento), portas corretas (3010/8010, não
3000/8000), quatro capturas de tela da conta de demonstração rodando, dois
diagramas Mermaid inline (arquitetura e pipeline de refeição) e uma seção de
decisões técnicas em que **cada número tem fonte verificável no repositório** —
incluindo a linha de base do eval lida de `evals/runs/history.jsonl`.

Os nove diagramas de `docs/fluxos/` deixaram de ser arquivos `.mermaid` avulsos
(que o GitHub **não** renderiza, ao contrário do que o índice afirmava) e viraram
blocos ```` ```mermaid ```` dentro do `fluxo.md` de cada pasta. As afirmações falsas
nomeadas no passo 4 foram corrigidas — mais três encontradas durante a execução,
registradas na OQ23.

O `make init` foi executado de fato, os serviços subiram, `make seed-demo` semeou
a conta e as capturas saíram dela; os 12 diagramas Mermaid do repositório foram
validados com o parser oficial do Mermaid.

**Tentativa 2 (rework):** os dois achados IMPORTANTES da avaliação foram
corrigidos — a cláusula "link da demo" do AC-20 ganhou registro durável e destino
nomeado (**OQ24**, com §3, §5 e §9 alinhados), e a contradição README × `ci.yml`
sobre `ruff format --check` foi desfeita. Ver §8.

## 2. Arquivos CRIADOS

| Arquivo | Propósito |
|---|---|
| `docs/imagens/dashboard.png` | Captura do dashboard (tema claro, padrão) |
| `docs/imagens/refeicoes.png` | Captura da lista de refeições do dia, com macros por item |
| `docs/imagens/peso.png` | Captura da evolução de peso em 90 dias |
| `docs/imagens/dashboard-escuro.png` | Mesma tela no tema escuro |

## 3. Arquivos ALTERADOS

| Arquivo | O que mudou |
|---|---|
| `README.md` | Reescrito. Gancho de engenharia (o eval), `make init`, portas corretas, avisos honestos sobre `GROQ_API_KEY` e banco nutricional vazio, conta demo preservada, capturas, dois diagramas Mermaid, tabela de decisões com fonte por linha, linha de base do eval por estrato, esteira de qualidade, limites do free tier medidos |
| `docs/fluxos/*/fluxo.md` (9 arquivos) | Ganharam a seção `## Diagrama` com o bloco Mermaid; em 04, 05 e 07 o rótulo "Gemini" virou "Groq" |
| `docs/fluxos/*/diagrama.mermaid` (9 arquivos) | **Removidos** do versionamento — o conteúdo migrou para o `.md` |
| `docs/fluxos/README.md` | Índice deixa de prometer que o GitHub renderiza `.mermaid` avulso |
| `CONTRIBUTING.md` | Setup passa a ser `make init`; a lista de hooks passa a ser a real (`ruff`, `ruff-format`, `gitleaks`, higiene, `no-commit-to-branch`), com `mypy`/`eslint` declarados como gate de CI; o resumo de fluxo deixa de prometer deploy automático |
| `docs/git-workflow.md` | Proteção da `main` descrita como está configurada (checks obrigatórios, `enforce_admins`, sem revisor obrigatório), CD declarado manual, tabela de CI atualizada |
| `docs/architecture.md` | Visão geral vira diagrama Mermaid; ADR-006 troca "latência < 20ms" por os 44 ms medidos; ADR-007 deixa de dizer "dark mode fixo"; ADR-008 ganha nota de estado apontando para ADR-009/E.4 |
| `Makefile` | `make init` deixa de anunciar a "Evol. API" (removida há meses) e passa a apontar `make seed-demo`; o alvo entra no `make help` |
| `backend/scripts/seed_dev_user.py` | Mensagem final mandava acessar `:3000`; o compose de dev publica `:3010` |
| `frontend/components/layout/Sidebar.tsx` | Rodapé dizia "V0.1" com o projeto em `0.7.0`; o número saiu |
| `.codeflow/specs/.../SPEC_002_*.md` | OQ23 (arquivos além dos seis declarados), `updated_at` e — na tentativa 2 — **OQ24** com o alinhamento de AC-20, passo 1 da D.3, AC-27, fase E.4 e §9 |

## 4. Confirmação do REUSO e decisões de design

**Reuso confirmado** (mapa da §4 da spec):

- `README.md`, `CHANGELOG.md`, `docs/architecture.md` (ADR-001 a ADR-009) e o alvo
  `make init` do `Makefile` foram reusados, não recriados.
- Os números da vitrine vêm de artefatos que já existiam: a decision de
  2026-07-26 (F1 do lookup, exclusão de `ai_estimated`, sensibilidade do boost), o
  `CHANGELOG` e `docs/fluxos/06` (latência 238 ms → 44 ms), a decision de
  2026-08-02 do sanity check, o `bug 001` (divergência de 38,2% e o teste de
  determinismo) e `backend/evals/runs/history.jsonl` (linha de base do eval).
- A seção da conta de demonstração entregue pela E.3 foi **preservada
  literalmente** no que o teste `test_seed_demo.py` trava: e-mail, senha e
  `make seed-demo`.
- O badge de CI já existia e continua apontando para o workflow ativo.

**Decisões de design:**

1. **Não há link de demo hospedada, e o README diz isso.** O AC-20 pede "link da
   demo com credenciais de demonstração". A demo pública depende da E.4, que a
   OQ16/ADR-009 deixou explicitamente adiada (roda local, sem servidor
   contratado). Inventar um link seria o oposto do escopo travado ("não prometer
   feature inexistente"), então o README entrega a demo **local** em três comandos,
   com as credenciais publicadas, e declara em uma linha por que não há URL.
2. **O README avisa que a tabela `foods` nasce vazia.** Nenhuma migration insere
   alimentos e nenhum script de seed os importa — a restauração do dump está
   documentada em `data/README.md`. Sem esse aviso, o leitor que segue o comando
   único teria todo alimento caindo no fallback da IA e concluiria que o produto é
   impreciso.
3. **F1 do lookup citado com os dois números.** A decision mede `0,776 → 0,857` na
   varredura de estratégias e `0,829` na implementação final (com boost 1,40×). O
   CHANGELOG cita só o segundo. O README traz os dois e diz qual é qual, em vez de
   escolher o mais bonito.
4. **A linha de base do eval é publicada com o gate reprovando.** MdAPE agregado de
   33,33% está acima do teto de 25% configurado em `report.py`. O README declara
   isso e explica que os limiares foram calibrados sobre 10 casos-semente contra um
   dataset que hoje tem 43 — em vez de omitir o número ou recalibrar por
   conveniência, o que a OQ20 já havia proibido.
5. **Quatro arquivos além dos seis declarados** — registrados na **OQ23** da §8,
   com o passo da fase que exige cada um. `gera_decision: no` impede o executor de
   criar decision; a OQ é o caminho já usado pela B.5 (OQ19), C.7 (OQ21) e D.2
   (OQ22).

**Desvios da spec/rules:** o conjunto de arquivos, acima (OQ23). Nenhum outro. Não
foi criada migration (NFR-7), nenhum limiar do `test_golden_set.py` foi tocado
(NFR-6), e nenhum artefato versionado ganhou credencial ou PII — a única
credencial no diff é a da conta de demonstração, pública por desenho e já isenta
nominalmente no `.gitleaks.toml` (decision de 2026-08-04).

## 5. Comandos rodados + saídas reais

### Comando único da fase, do zero ao ar

```text
$ make init
 Container caloria_postgres  Healthy
 Container caloria_backend  Started
 Container caloria_frontend  Started
  Aguardando backend.
  Backend: OK

[4/4] Aplicando migrações...
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
  Migrações aplicadas

Setup concluído!

  Dashboard:   http://localhost:3010
  API:         http://localhost:8010
  Swagger:     http://localhost:8010/docs
  Evol. API:   http://localhost:8080          ← a afirmação falsa que esta fase removeu

$ curl -s http://localhost:8010/health
{"status":"ok","version":"0.7.0"}

$ curl -s -o /dev/null -w "%{http_code}" http://localhost:3010/
307                                          (redireciona para /login)

$ make seed-demo
→ Resolvendo usuário demo@caloria.app...
✓ Dados inseridos com sucesso!
  Dias com refeições:  30
  Registros de peso:   15
```

Login com `demo@caloria.app` / `CalorIADemo2026!` pelo navegador (Playwright)
carregou dashboard, refeições, peso e insights — as capturas de `docs/imagens/`
são dessa sessão.

### Diagramas Mermaid — parser oficial, não inspeção visual

```text
$ node _mermaid_check.mjs      # mermaid.parse() sobre todo bloco ```mermaid do repo
ok README.md #1
ok README.md #2
ok docs/architecture.md #1
ok docs/fluxos/01-autenticacao/fluxo.md #1
ok docs/fluxos/04-registro-refeicao-web/fluxo.md #1
ok docs/fluxos/05-analise-ia/fluxo.md #1
ok docs/fluxos/06-lookup-nutricional/fluxo.md #1
ok docs/fluxos/07-insights-relatorios/fluxo.md #1
ok docs/fluxos/08-lembretes-notificacoes/fluxo.md #1
ok docs/fluxos/09-celery-tarefas/fluxo.md #1
ok docs/fluxos/10-dashboard-frontend/fluxo.md #1
ok docs/fluxos/11-logs-saude/fluxo.md #1

12 diagramas, 0 falhas
```

O script é descartável e não foi versionado (rodou de `frontend/`, onde o
Playwright está instalado, com o pacote `mermaid` instalado fora do repositório).

### Links relativos dos documentos tocados

```text
$ python3 (varredura de [texto](caminho) em README, CONTRIBUTING, git-workflow,
           architecture e os 10 arquivos de docs/fluxos)
links relativos quebrados: 0
```

### Comandos de validação do projeto

```text
$ make lint-check
All checks passed!
149 files already formatted
> next lint --no-cache
./components/auth/Plasma.tsx
156:26  Warning: ... react-hooks/exhaustive-deps      ← pré-existente, warning, não erro

$ make typecheck
Success: no issues found in 81 source files
(tsc do frontend sem saída = sem erro)

$ make test-unit
======================== 496 passed, 3 skipped in 4.65s ========================

$ make test-integration
================== 145 passed, 5 warnings in 75.76s (0:01:15) ==================

$ make test-frontend
Test Suites: 20 passed, 20 total
Tests:       118 passed, 118 total

$ make check
Tudo OK.                                       (exit 0)
```

### Revalidação após o rework (tentativa 2)

O diff da tentativa 2 é markdown puro (`README.md` e a spec), mas os gates foram
rodados de novo por inteiro:

```text
$ make check
All checks passed!
Success: no issues found in 81 source files
======================== 496 passed, 3 skipped in 4.06s ========================
================== 145 passed, 5 warnings in 68.60s (0:01:08) ==================
Test Suites: 20 passed, 20 total
Tests:       118 passed, 118 total
Tudo OK.                                       (exit 0)

$ run-structural.sh (após a edição de §3, §5, §8 e §9)
✓ §5 estruturalmente válida
EXIT=0

$ varredura de links relativos
links relativos quebrados: 0
```

### Segredo / PII no diff

```text
$ pre-commit (hook gitleaks, em cada um dos 5 commits)
Detect hardcoded secrets.................................................Passed
```

### Gate estrutural da §5 (após a edição da §8)

```text
$ bash ~/.codeflow/framework/core/scripts/run-structural.sh .codeflow/specs/002-*/SPEC_002_*.md
✓ §5 estruturalmente válida
EXIT=0
```

## 6. Critérios de aceite da fase (com evidência)

**AC-20** — *"o README traz comando único de execução que funciona, portas
corretas, link da demo com credenciais de demonstração, diagrama Mermaid
renderizável e seção de decisões técnicas com números medidos e citados"*:

- [x] **Comando único que funciona** — `make init` executado nesta máquina, saída
      completa na §5: build, subida dos 6 serviços, `_wait-for-backend` verde e
      `alembic upgrade head` aplicado. `/health` respondeu `{"status":"ok"}`.
      Antes desta fase, `make init` não era citado no README, no CONTRIBUTING nem
      em `docs/setup.md`.
- [x] **Portas corretas** — README e CONTRIBUTING dizem 3010/8010, que é o que
      `docker-compose.dev.yml` publica (`FRONTEND_HOST_PORT:-3010`,
      `BACKEND_HOST_PORT:-8010`) e o que respondeu ao `curl`.
- [x] **Demo com credenciais** — seção "Conta de demonstração" com
      `demo@caloria.app`, `CalorIADemo2026!` e `make seed-demo`; os três strings
      são o que `backend/tests/unit/test_seed_demo.py::TestCredenciaisPublicadas`
      exige do README — **com a ressalva** de que essa classe de teste é um dos
      `3 skipped` sob `make test-unit`, porque o container monta só `backend/` e
      o README da raiz não é alcançável de lá (comportamento herdado da E.3); as
      três asserções foram conferidas à mão. A cláusula do **link** migrou para o
      AC-27/E.4 pela **OQ24** (tentativa 2); a ausência de instância hospedada
      segue declarada em uma linha do próprio README.
- [x] **Diagrama Mermaid renderizável** — dois no README (arquitetura e pipeline),
      um em `docs/architecture.md`, nove em `docs/fluxos/`; os 12 passam por
      `mermaid.parse()` (§5).
- [x] **Decisões técnicas com números medidos e citados** — oito linhas, cada uma
      com link para a fonte: bug 001, decision de 2026-07-26, decision de
      2026-08-02, CHANGELOG, `docs/fluxos/06` e `backend/evals/README.md`. A tabela
      de linha de base do eval reproduz `history.jsonl` (MdAPE 33,33%, IC95
      26,26–43,66, 23,1% dentro de ±10%, n=39 de 43).
- [x] **Nenhuma afirmação do README contradiz o estado do repositório** — as três
      contradições declaradas no passo 4 foram corrigidas
      (`CONTRIBUTING.md:42`, `docs/git-workflow.md`, `Makefile:139`) e mais três
      encontradas na execução (porta do seed, versão no rodapé da UI, "dark mode
      fixo" no ADR-007).

## 7. Definition of Done da fase

- [x] Testes da fase verdes — `make test-unit` (496), `make test-integration`
      (145), `make test-frontend` (118), todos sem alteração de teste
- [x] Comandos de validação do projeto limpos — `make check` exit 0 (§5); gate de
      segurança do manifest é `[—]` no projeto e o substituto real (gitleaks no
      pre-commit) passou nos 5 commits
- [x] Escopo travado respeitado — nenhuma métrica inventada (toda linha da tabela
      tem fonte), nenhuma feature prometida que não exista (a ausência de demo
      hospedada está declarada), CHANGELOG histórico intocado
- [x] Nenhum segredo/PII — o único par de credenciais é o da conta demo, público
      por desenho; as capturas mostram dados sintéticos do seed
- [x] Commits em pt-BR (Conventional Commits), sem menção a autor/IA — 5 commits

## 8. (Em rework) O que mudou nesta tentativa

Avaliação da tentativa 1: **RESSALVAS**, score 9.5 / threshold 8.5, zero
BLOQUEANTES, dois IMPORTANTES. Os dois foram corrigidos; nenhuma linha de código
mudou.

### IMP-1 — decisão de escopo do AC-20 sem registro durável

**O achado:** a cláusula "link da demo" foi fechada por declaração, e a
justificativa vivia só neste relatório — que o AC-21 manda a D.4 remover do
versionamento. Mesmo defeito que fechou a D.2 com RESSALVAS na tentativa 1.

**O que fiz:** **OQ24** na §8 da spec, no formato de OQ18/OQ20/OQ22, e — como a
OQ21 fez — **alinhei a redação em todos os lugares onde a cláusula aparecia**, em
vez de deixar a spec pedindo e não pedindo a mesma coisa:

| Onde | O que mudou |
|---|---|
| §3, AC-20 | "link da demo" → "a demo com credenciais", mais nota de migração apontando OQ24 |
| §5, passo 1 da D.3 | mesma troca, com a nota entre parênteses |
| §3, AC-27 | **recebe** a cláusula: o link entra no README quando a instância existir |
| §5, Fase E.4 | `README.md` entra em "Arquivos alterados"; passo 6 novo (publicar o link e remover a linha de ausência); teste do AC-27 cobre o link |
| §9 | linhas da D.3 e da E.4 declaram a migração |

O AC-27 ganhar `README.md` na lista de arquivos é o detalhe que evita repetir o
defeito na E.4: sem isso, o executor daquela fase encontraria um AC que cobra uma
edição num arquivo que a fase não declara tocar.

### IMP-2 — README dizia que o CI roda `ruff format --check`

**O achado:** `README.md:181` juntava `ruff check` e `ruff format --check` numa
linha só, ambos atribuídos a "pre-commit e CI". O `ci.yml` tem um único passo de
ruff (`ruff check .`), e o `Makefile:300` afirma o contrário em voz alta. É
contradição README × repositório — a cláusula final do teste do AC-20.

**O que fiz:** quebrei a linha em duas, como sugerido — `ruff check` em
"pre-commit e CI", `ruff format --check` em "pre-commit e `make check`".

### Sugestões 2 e 3 da avaliação, aplicadas por serem da mesma classe

Ambas são imprecisão no mesmo bloco de README que o IMP-2 tocou, e ambas foram
nomeadas pelo avaliador:

- **Sugestão 2** — "`make check` reproduz os gates do CI" virou "reproduz a maior
  parte dos gates do CI localmente — fora `gitleaks` e o `next build` de produção",
  que é o que o alvo faz de fato.
- **Sugestão 3** — o `Requested 11357` competia com o `11508` da rodada cuja linha
  de base o próprio README publica. Virou "~11,4 mil tokens", sem número exato de
  rodada nenhuma.

**Sugestões 1 e 4 não foram aplicadas**, por decisão explícita: o avaliador as
declarou fora do escopo da D.3 (`docs/flow.md` e a contagem de alimentos em quatro
documentos) e endereçadas à D.4. Ampliar a fase em rework contrariaria o protocolo.

## 9. Itens em aberto / dúvidas para o avaliador

1. ~~A cláusula "link da demo" do AC-20 foi cumprida por declaração, não por
   link.~~ **Resolvido na tentativa 2:** a cláusula migrou para o AC-27/E.4 pela
   **OQ24**, com §3, §5 e §9 alinhados (§8 deste relatório). O que resta ao
   avaliador conferir é se o destino é o certo — E.4 é quem publica a instância —
   e se o passo 6 novo da E.4 é suficiente para a cláusula não se perder.
2. **`make init` foi validado sobre volumes que já existiam.** Não rodei
   `make reset` porque isso apagaria o banco local de desenvolvimento do owner,
   incluindo as 42.168 linhas de `foods` restauradas à mão. A afirmação do README de
   que a tabela `foods` nasce vazia é derivada, não observada: nenhuma migration
   insere alimentos (`grep` por `INSERT INTO foods`/`bulk_insert` em
   `alembic/versions/` → zero) e `seed_all.py` não os importa; o procedimento de
   restauração está em `data/README.md`. Uma execução realmente do zero é o único
   teste que fecharia isso — cabe ao owner decidir se vale o custo.
3. **Contradição entre fontes sobre o bug 001, resolvida pela fonte primária.** A
   §1 desta spec diz "3486 vs 2098 kcal (39,8%)"; o registro do bug e o CHANGELOG
   dizem **3386 vs 2094 (38,2%)**. O README cita os números do bug, que é onde a
   medição foi feita. A §1 da spec não foi editada (fora do escopo desta fase).
4. **A contagem de alimentos do README mudou de forma.** O texto antigo dizia
   "~19.800 alimentos" em três lugares. Medido agora no banco local: 42.168 linhas,
   das quais 23.398 são `ai_estimated` e ficam **fora** do lookup por decisão
   medida — sobram 18.770 consultáveis. O README novo não repete o número solto; a
   contradição documental (o `data/README.md` diz 42.103) é **da D.4**, que a
   nomeia no passo 4, e por isso não foi tocada aqui.
5. **`docs/imagens/` é novo e a D.4 vai olhar para ele.** São 1,2 MB de PNG
   versionados. Não são artefato de execução de agente (que é o que o AC-21 manda
   podar) e sim conteúdo do README, mas vale o avaliador confirmar que a poda não
   vai levá-los junto.

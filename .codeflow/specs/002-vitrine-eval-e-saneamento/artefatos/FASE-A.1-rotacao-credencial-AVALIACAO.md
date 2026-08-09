---
spec: 002-vitrine-eval-e-saneamento
fase: A.1
slug_fase: rotacao-credencial
tentativa: 3
veredito: APROVADO
score: 9.2
threshold: 8.5
range_avaliado: 461ee3805bf5f8848d4da6ebd23779ff8817c315..7348d948dd9a5176fa0dbd13549b26e25c87e3f0
---

# FASE A.1 — Avaliação independente

> ## Encerramento por decisão do owner (2026-08-04)
>
> **O veredito do frontmatter passou de `RESSALVAS` para `APROVADO`.** Isto não é
> uma reavaliação — é o registro, no único lugar que a máquina de estados lê
> (ARTIFACTS_SPEC §2.11.3), de uma decisão que já estava tomada em prosa e que o
> artefato ainda contradizia.
>
> **O caminho.** O teto do §2.11.4 (`reprovacoes: 2` + este veredito = o 3º) parou
> a fase e a escalou ao owner, que é o estado terminal previsto. O owner decidiu em
> 2026-08-03 (OQ13 da spec, e "Estado final" de
> `.codeflow/decisions/2026-08-02-senha-conta-caloria-producao.md`) encerrar a fase
> em vez de gastar uma quarta tentativa, e a §9 da spec já a marcava `[x]`. Em
> 2026-08-04 o owner autorizou explicitamente refletir isso no documento. Não houve
> override conversacional de gate: o gate rodou, parou, escalou, e o humano decidiu.
>
> **Os dois IMPORTANTES que sustentavam o veredito foram fechados** — conferido
> arquivo a arquivo antes desta edição, e é o que torna `APROVADO` coerente com a
> §2.10.3 (score 9.2 ≥ 8.5, zero BLOQUEANTES, zero IMPORTANTES abertos):
>
> | Achado | Correção verificada |
> |---|---|
> | **4.1** — §9 do relatório contradizia §1/§8 | `FASE-A.1-…-EXECUCAO.md` §9 reescrita em 2026-08-03, com a nota de retratação no topo da seção e os quatro itens no estado real |
> | **4.2** — decision afirmava o risco e a sua inexistência ao mesmo tempo | cabeçalho "ATUALIZAÇÃO" + seção "Estado final (2026-08-03)"; portão da D.2 marcado `⛔ PORTÃO LEVANTADO`; a afirmação "a URL não é descobrível" marcada `❌ FALSO, ver retratação` nos dois pontos |
>
> **O que não muda:** o score (9.2) e o corpo desta avaliação ficam como foram
> escritos — são o registro do que foi medido na tentativa 3. As sugestões da §5
> seguem abertas, em especial a de `frontend/playwright.prod.config.ts:9`, que a
> própria avaliação já situava na D.4.

## 1. Veredito e score

**Veredito (tentativa 3, como avaliado):** RESSALVAS · **Score:** 9.2 / threshold 8.5
**Veredito final da fase:** APROVADO, por encerramento do owner — ver o bloco acima.

**O BLOQUEANTE que segurou a fase por duas tentativas caiu — e não pela declaração
do owner, mas por medição minha.** As tentativas 1 e 2 foram reprovadas porque "a
credencial exposta continua válida no serviço que ela abre". Verifiquei o serviço:

- O host de API que o **frontend em produção realmente usa** está embutido no bundle
  publicado na Vercel: `https://caloria.duckdns.org` (extraído dos chunks de
  `/_next/static/`, §6). Ele resolve em DNS (`3.21.134.83`), mas **não aceita conexão
  em 80, 443 nem 8000** — três sondagens TCP, todas em timeout.
- O host documentado (`caloria-gabriel.duckdns.org`, `docs/deploy.md:188`) **nem
  resolve em DNS**.
- O frontend na Vercel responde 200, mas aponta para essa API morta: a tela de login
  abre e não tem com o que autenticar.

Não há caminho de login em pé. Somado à confirmação escrita do owner de que a senha
foi rotacionada no Google/Gmail (conta de recuperação) e nos demais serviços de reuso,
o AC-1 está substantivamente satisfeito, e o achado 3.1 das tentativas 1 e 2 está
**fechado**. Isso é corroborado, de forma independente e posterior, pela Fase E.1
(já aprovada), que mediu a mesma indisponibilidade do backend.

**O que impede o APROVADO são dois defeitos nos artefatos, não no código.** O rework
atualizou a §1 e a §8 do relatório e o cabeçalho da decision, mas deixou intactas duas
seções que hoje afirmam, **em tempo presente**, o contrário da conclusão da própria
tentativa — inclusive um fato que é falso e que foi a razão declarada para descartar,
na tentativa 2, exatamente a verificação que fecharia o AC. Detalhe em §4.

**Consequência de processo.** Com este veredito não-APROVADO, `reprovacoes` da A.1
chega a **3**. Pela ARTIFACTS_SPEC §2.11.4 a fase atinge o **teto** e **não deve
voltar ao ciclo executor↔avaliador**: vai à mesa do owner. Registro minha leitura para
essa decisão: o trabalho técnico da fase está feito e verificado; o que resta são duas
edições de markdown. Ver §7 para o que precisa mudar e §5 para o caminho mais barato.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 4 | AC-4 ✓ lido do código (`frontend/e2e/auth.spec.ts:3-4`, não do relatório). AC-1 ✓ nas três cláusulas: working tree sem a credencial (gitleaks 456 commits + grep próprio, §6), confirmação escrita do owner (`EXECUCAO.md:24-27`), repositório privado (`gh repo view` → `PRIVATE`). Escopo travado respeitado: o commit da fase (`240d708`) não reescreve histórico, nenhum artefato contém a credencial, o agente não rotacionou senha. Desconto: a cláusula que decide o AC-1 foi sustentada só por declaração do owner — a evidência de requisição que a comprova fui eu que produzi (§6), e o motivo declarado para não a produzir era falso (§4.1) |
| 2 | Arquitetura e direção de dependências | 3 | 5 | Diff de 2 linhas num arquivo de e2e; nenhum código de produção tocado (`git show 240d708 -- frontend/e2e/auth.spec.ts`) |
| 3 | Segurança / LGPD / multi-tenant | 3 | 4 | `gitleaks --config .gitleaks.toml` sobre 456 commits → `no leaks found`, exit 0. Grep próprio de e-mail de provedor de consumo → só `devteste@gmail.com` e `auditcaloria@gmail.com` (sintéticos, allowlist declarada). Repositório privado. Backend verificadamente inalcançável. Desconto: a decision ATIVA da fase ainda declara, na §"Consequência", uma exposição residual que hoje é falsa **e** um bloqueio da Fase D.2 que o próprio cabeçalho do documento não repete (§4.2) |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | `http://localhost:3000` é literalmente o `baseURL` e o `webServer.url` de `frontend/playwright.config.ts` — nenhuma porta nem endereço inventado |
| 5 | Padrões de domínio/aplicação | 2 | 5 | `process.env.BASE_URL ?? <default>` mantém a forma já usada no arquivo |
| 6 | Local e nomes dos arquivos | 2 | 5 | Exatamente o arquivo declarado em "Arquivos alterados" da §5 da spec |
| 7 | Qualidade de código | 2 | 5 | O comentário de `auth.spec.ts:3` registra o *porquê*, não o *o quê* — conforme o 4º princípio da constitution universal |
| 8 | Testes e cobertura | 2 | 4 | `npm test` → 20 suites, 114/114 (rodado por mim, §6); `npx playwright test --list` → 8 testes em 3 arquivos, nenhum perdido. Sem teste novo — um valor default de e2e não tem o que asseverar em unidade |
| 9 | Migration safety | 2 | [—] | Nenhuma migration tocada pelo commit da fase (NFR-7 preservado) |

Score = (3·4 + 3·5 + 3·4 + 3·5 + 2·5 + 2·5 + 2·5 + 2·4) / 20 · 2 = 92/20 · 2 = **9.2**

## 3. Achados BLOQUEANTES

Nenhum.

O BLOQUEANTE 3.1 das tentativas 1 e 2 — "a credencial exposta continua válida na
conta do CalorIA" — está **fechado**. O caminho (2) que a avaliação da tentativa 2
apontou como suficiente ("comprovar com evidência de requisição que o backend está
fora do ar") foi percorrido e está em §6: o host que o frontend publicado de fato
chama não aceita conexão em porta alguma, e o host documentado não resolve.

## 4. Achados IMPORTANTES

### 4.1 — A §9 do relatório contradiz a §1 e a §8 do próprio relatório, e propaga um fato falso

**Onde:** `.codeflow/specs/002-vitrine-eval-e-saneamento/artefatos/FASE-A.1-rotacao-credencial-EXECUCAO.md:257-273` (§9, "Itens em aberto / dúvidas para o avaliador").

**O defeito.** A §9 é a seção que o avaliador e o `/spec-status` leem para saber o que
ficou em aberto. Ela não foi atualizada no rework e hoje afirma, em tempo presente,
três coisas que o restante do mesmo documento retrata:

| §9 diz | §1/§6/§8 do mesmo arquivo dizem |
|---|---|
| "**Pendência residual:** a senha da conta do CalorIA **em produção** não foi trocada" (`:259`) | "O passo 1 — rotação da senha pelo owner — **FOI CONCLUÍDO**" (`:24`); "o ambiente **nunca foi produção de verdade**" (`:31`); "Não há conta a proteger" (`:33`) |
| "O ambiente de produção será reconstruído na Fase E.4 **de qualquer forma**" (`:268`) — enquadrando como mitigação de um risco vivo | §8 enquadra a destruição do banco como o fato que **elimina** o risco, não que o mitiga (`:186-188`) |
| "**AC-1 era insatisfazível pela A.1 isoladamente**… Sugiro ao avaliador… ou ajustar a spec para mover essa cláusula para o AC-2" (`:270-273`) | A spec **já foi ajustada**: a cláusula migrou para o AC-2 (nota de 2026-08-02 na §3 da spec), e a própria §6 do relatório registra a migração (`:135-136`) |

**Por que é IMPORTANTE e não sugestão.** O relatório é o artefato de handoff da fase
(ARTIFACTS_SPEC §2.9.2) e sobrevive à sessão. Uma §9 que lista como pendente aquilo que
a §1 declara concluído deixa o estado da fase ambíguo para todo leitor posterior —
inclusive para quem for executar a D.2, que a decision desta fase pretende bloquear.
Um documento que decide o veredito não pode divergir de si mesmo na seção endereçada a
quem julga.

**Correção.** Reescrever a §9 para refletir a conclusão da tentativa 3: (a) trocar o
item 1 pelo estado real — rotação concluída nos serviços de reuso, conta do CalorIA
sem serviço em operação, com a evidência de requisição desta avaliação (§6) citada;
(b) remover o item 2, já resolvido na spec; (c) manter o item 3, que segue válido.

### 4.2 — A decision ATIVA da fase afirma ao mesmo tempo que o risco existe e que não existe, e deixa a Fase D.2 em estado indefinido

**Onde:** `.codeflow/decisions/2026-08-02-senha-conta-caloria-producao.md:96-114`
(§"Consequência — risco residual aceito") contra `:12-33` (cabeçalho "ATUALIZAÇÃO").

**O defeito.** O cabeçalho retrata a premissa e conclui que "não é um risco adiado — é
um risco que deixou de existir", listando em "O que continua valendo" **apenas** a
proibição de reusar a senha na conta semeada da E.3. O corpo, porém, continua sendo
texto vigente do documento e declara:

- `:98-101` — "**O que continua exposto:** se o backend de produção estiver no ar, a
  conta `<e-mail do owner>` no CalorIA aceita a senha vazada". A condicional está hoje
  resolvida como falsa e medida (§6), mas o documento não diz isso.
- `:112-114` — "A **D.2 não deve ser executada** antes desta pendência ser fechada, e
  essa dependência **não está declarada na §5 da spec** — está declarada aqui".

Este segundo ponto é o mais consequente: é uma **restrição viva sobre uma fase futura**,
deliberadamente colocada fora da spec e só neste arquivo, apoiada numa premissa que o
cabeçalho do mesmo arquivo retrata. O executor da D.2 lerá as duas coisas e não terá
como saber se o portão continua fechado. `status: ativa` no frontmatter (`:4`) faz o
documento inteiro valer, não só o cabeçalho.

Há ainda um fato **falso** no corpo, e ele não é decorativo — foi o motivo declarado
para descartar, na tentativa 2, a única verificação que fecharia o AC:

- `:62-64` — "a URL do backend **não é descobrível a partir do código**"; `:88-91` —
  alternativa 2 "descartada porque a URL do backend não é descobrível pelo
  repositório". **É descobrível, e sempre foi:** `docs/deploy.md:188` e
  `docs/deploy-checklist.md:107` trazem `APP_DOMAIN=caloria-gabriel.duckdns.org` em
  texto claro. A Fase E.1 encontrou o host exatamente aí. (O host *real* da API está no
  bundle publicado — descoberta desta avaliação, §6 — mas para refutar a afirmação
  bastava um `grep` em `docs/`.) O mesmo texto reaparece no relatório em `:222-224`.

**Correção.** Editar a decision: (a) na §"Consequência", declarar a condicional
resolvida, citando a medição (§6 desta avaliação e a §3 do `FASE-E.1-auditoria-deploy-EXECUCAO.md`);
(b) decidir explicitamente o destino do portão da D.2 — mantê-lo com uma razão que
sobreviva à retratação, ou levantá-lo e dizer isso; (c) corrigir ou marcar como
factualmente errada a afirmação de que a URL não era descobrível, para que a E.2/D.2
não herdem a premissa.

## 5. Sugestões

- **Caminho mais barato para o owner, dado o teto.** Os dois IMPORTANTES são edições de
  markdown em dois arquivos, sem toque em código e sem risco de regressão. Se o owner
  preferir não gastar uma quarta tentativa da A.1, a alternativa limpa é tratá-los como
  saneamento de artefato fora do ciclo de fase (as duas edições + um commit `docs`), e
  então reavaliar. A decisão é do owner; registro a opção porque o teto do §2.11.4
  existe para forçar decisão humana, não para congelar o trabalho.
- **`frontend/playwright.prod.config.ts:9` ainda tem a URL de produção como default do
  mesmo `BASE_URL`.** Fora do escopo declarado da fase (que trava em `auth.spec.ts`) e
  defensável — é um config `.prod` de opt-in explícito, e o config default aponta para
  `localhost`. Mas `dashboard.spec.ts` e `meals.spec.ts` usam caminhos relativos e
  herdam esse `baseURL`: rodar `playwright test -c playwright.prod.config.ts` sem env
  bate na Vercel viva. Vale um `test.skip` guardado por env var, ou mover para a D.4.
- **A E.1 afirma que "a URL de produção do frontend não aparece em documento nenhum"**
  (`FASE-E.1-auditoria-deploy-EXECUCAO.md:104`). Aparece: `playwright.prod.config.ts:9`,
  `docs/auditoria/08-testes.md:156` e `docs/auditoria/achados.md:300`. Não é achado desta
  fase — anoto porque é a mesma classe de erro da §4.2 (afirmar um negativo sem grep) e
  a E.1 já está aprovada.
- **O `range` resolve mas não isola** (sugestão herdada da tentativa 2, ainda válida):
  `461ee38..7348d94` engloba A.1, A.2, A.3, B.1 e B.2 em 21 commits. É conforme ao
  schema (§2.9.3 manda "sempre do início original ao HEAD"), mas o único commit de
  código desta fase é `240d708`. Vale escrever isso no corpo do relatório.

## 6. Comandos rodados + saídas reais

```text
# --- Passo 1: gate estrutural da §5 da spec ---
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
>>> EXIT=0

# --- Passo 2: branch, ancestralidade do range, árvore limpa ---
$ git branch --show-current
dev
$ git rev-parse --short HEAD
f90ddf2
$ git status --porcelain | wc -l
0
$ git merge-base --is-ancestor 461ee3805bf5f8848d4da6ebd23779ff8817c315 HEAD  → ANCESTRAL
    461ee38 docs(specs): registra spec 002 de vitrine, eval e saneamento
$ git merge-base --is-ancestor 7348d948dd9a5176fa0dbd13549b26e25c87e3f0 HEAD  → ANCESTRAL
    7348d94 ci(seguranca): separa deteccao de placeholder do regex de senha

$ git diff --stat 461ee38..7348d94 -- . ':(exclude).codeflow/specs/*/artefatos/*' | tail -1
42 files changed, 1111 insertions(+), 199 deletions(-)     # cobre A.1, A.2, A.3, B.1, B.2

# --- AC-4: lido do código, não do relatório ---
$ sed -n '3,4p' frontend/e2e/auth.spec.ts
// Default local: rodar a suíte sem BASE_URL definido nunca pode tocar produção.
const BASE_URL = process.env.BASE_URL ?? "http://localhost:3000";       ← AC-4 ✓
$ git show 240d708 -- frontend/e2e/auth.spec.ts
-const BASE_URL = process.env.BASE_URL ?? "https://frontend-nine-mu-59.vercel.app";
+// Default local: rodar a suíte sem BASE_URL definido nunca pode tocar produção.
+const BASE_URL = process.env.BASE_URL ?? "http://localhost:3000";
$ grep -rn "vercel.app" frontend/e2e/ | wc -l
0                                                                       ✓

# --- O BLOQUEANTE das tentativas 1 e 2: MEDIDO, não aceito por declaração ---
# 1) host de API que o frontend PUBLICADO realmente usa, extraído do bundle da Vercel
$ curl -s https://frontend-nine-mu-59.vercel.app/login -o login.html   # 22.817 bytes
$ for c in $(grep -oE '/_next/static/chunks/[^"]+\.js' login.html | sort -u); do
      curl -s "https://frontend-nine-mu-59.vercel.app$c"; done > allchunks.js   # 820.586 bytes
$ grep -oE 'https?://[a-zA-Z0-9.-]+' allchunks.js | sort -u | grep duckdns
https://caloria.duckdns.org                     ← NEXT_PUBLIC_API_URL do build vivo

# 2) esse host resolve, mas não aceita conexão em porta alguma
$ getent hosts caloria.duckdns.org
3.21.134.83     caloria.duckdns.org
$ for p in 443 80 8000; do timeout 8 bash -c "</dev/tcp/3.21.134.83/$p"; done
porta 443: fechada/filtrada (sem conexao em 8s)
porta 80:  fechada/filtrada (sem conexao em 8s)
porta 8000: fechada/filtrada (sem conexao em 8s)
$ curl -sS --connect-timeout 8 https://caloria.duckdns.org/health
curl: (28) Failed to connect to caloria.duckdns.org port 443 after 8002 ms: Timeout was reached

# 3) o host DOCUMENTADO (docs/deploy.md:188) nem resolve
$ getent hosts caloria-gabriel.duckdns.org
(sem saída — não resolve)
$ curl -s -o /dev/null -w "%{http_code}\n" https://caloria-gabriel.duckdns.org/health
000        (curl exit 6 — could not resolve host)

# 4) o frontend está no ar, mas sem API atrás dele
$ curl -s -o /dev/null -w "%{http_code}\n" https://frontend-nine-mu-59.vercel.app/login
200
# Leitura: não há caminho de login em pé. AC-1 fechado. Corroborado, de forma
# independente e POSTERIOR, pela Fase E.1 já aprovada
# (FASE-E.1-auditoria-deploy-EXECUCAO.md:44-56, mesma conclusão pelo host documentado).

# --- refutação da premissa usada na tentativa 2 ("URL não descobrível") ---
$ grep -rn "duckdns" docs/deploy.md docs/deploy-checklist.md
docs/deploy.md:188:APP_DOMAIN=caloria-gabriel.duckdns.org
docs/deploy.md:193:NEXT_PUBLIC_API_URL=https://caloria-gabriel.duckdns.org
docs/deploy-checklist.md:107:APP_DOMAIN=caloria-gabriel.duckdns.org
docs/deploy-checklist.md:111:NEXT_PUBLIC_API_URL=https://caloria-gabriel.duckdns.org
   → estava no repositório o tempo todo; a afirmação da decision é falsa.

# --- AC-1, demais cláusulas ---
$ gh repo view gabriel-ngrs/CalorIA --json visibility,isPrivate
{"isPrivate":true,"visibility":"PRIVATE"}                               ✓

$ gitleaks detect --source . --config .gitleaks.toml --redact --no-banner --exit-code 1
INF 456 commits scanned.
INF no leaks found
>>> EXIT=0                                                              ✓

$ grep -rInE '[A-Za-z0-9._%+-]+@(gmail|hotmail|outlook|yahoo|icloud|proton|live|bol|uol|terra)\.' \
    --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=.next \
    --exclude-dir=.venv --exclude-dir=data . | grep -oE '<regex do e-mail>' | sort | uniq -c
     12 devteste@gmail.com          # sintético, allowlist .gitleaks.toml
      4 auditcaloria@gmail.com      # sintético, allowlist .gitleaks.toml
   → nenhuma ocorrência do e-mail pessoal do owner.                     ✓

# --- gate da fase: make test-frontend (alvo = `cd frontend && npm test`) ---
$ cd frontend && npm test
Test Suites: 20 passed, 20 total
Tests:       114 passed, 114 total
Time:        6.465 s                                                    ← gate ✓

$ cd frontend && npx playwright test --list | tail -2
  [chromium] › meals.spec.ts:40:7 › Página de Refeições › exibe estado vazio quando não há refeições
Total: 8 tests in 3 files                                               ✓ nenhum teste perdido

# --- demais gates do manifest, rodados mesmo não sendo exigidos pela fase ---
$ cd frontend && npm run lint
./components/auth/Plasma.tsx
  156:26  Warning: react-hooks/exhaustive-deps        # pré-existente, não é desta fase
exit 0
$ cd frontend && npx tsc --noEmit          → exit 0
$ backend/.venv/bin/python -m ruff check .          → All checks passed!
$ backend/.venv/bin/python -m ruff format --check . → 144 files already formatted
$ backend/.venv/bin/python -m mypy app/             → Success: no issues found in 74 source files

# --- make test-integration: [—] NÃO RODADO ---
$ docker ps
The command 'docker' could not be found in this WSL 2 distro.
   # gate ausente do ambiente → `[—]`, não falha (SPEC §3.10). A fase não toca backend.

# --- árvore limpa ao final; nenhum código alterado pelo avaliador ---
$ git status --porcelain | wc -l
0
```

## 7. Itens da fase / DoD não atendidos

| Item (§5 / §9 da spec) | Estado |
|---|---|
| Passo 1 — rotação em todos os serviços afetados | **Atendido.** Confirmação escrita do owner para Google/Gmail e demais serviços de reuso; a conta do CalorIA não é serviço em operação — verificado por requisição (§6), não aceito por declaração |
| Passo 2 — repositório privado | Atendido (executado pelo agente com autorização escrita do owner, desvio declarado em `EXECUCAO.md:65-68`) |
| Passo 3 — `BASE_URL` local por default | Atendido, lido do código |
| Passo 4 — working tree sem a credencial | Atendido, verificado por mim (gitleaks + grep) |
| Gate — `make test-frontend` verde | Atendido (114/114) |
| Gate — owner confirmou por escrito a rotação | Atendido |
| Escopo travado — histórico não reescrito nesta fase | Atendido (`240d708` toca 1 arquivo) |
| Escopo travado — credencial ausente de todo artefato | Atendido (gitleaks sobre 456 commits, exit 0) |
| Escopo travado — agente não rotacionou senha | Atendido |
| **Qualidade do artefato de handoff (§2.9.2)** | **NÃO ATENDIDO** — §9 do relatório contradiz §1/§8 (achado 4.1) |
| **Coerência da decision ATIVA gerada pela fase** | **NÃO ATENDIDO** — corpo contra cabeçalho, portão da D.2 indefinido, fato falso não corrigido (achado 4.2) |

## 8. Divergências entre o relatório e o código real

1. **Nenhuma divergência no código.** O diff de `frontend/e2e/auth.spec.ts` é
   exatamente o que o relatório descreve; o valor `http://localhost:3000` veio mesmo de
   `frontend/playwright.config.ts`; o `grep -rn "vercel.app" frontend/e2e/` → 0 confere.

2. **Divergência factual — "a URL do backend não é descobrível pelo repositório"**
   (`EXECUCAO.md:222-224`, `decisions/2026-08-02-senha-conta-caloria-producao.md:62-64,88-91`).
   Falso: `docs/deploy.md:188` e `docs/deploy-checklist.md:107` sempre trouxeram o host.
   Consequência real: essa afirmação foi o motivo declarado para descartar, na tentativa 2,
   a verificação que fecharia o AC-1 — a mesma que fiz em §6 em três comandos.

3. **Divergência interna — §9 contra §1/§8 do mesmo relatório** (achado 4.1). O
   relatório declara a fase concluída e, três seções depois, lista a mesma coisa como
   pendência residual "em produção", num ambiente que ele próprio afirma nunca ter sido
   produção.

4. **O relatório subdeclara os números do gate.** §5 cita `17 suites / 100 testes`; medi
   `20 suites / 114 testes`. Não é defeito: o range engloba fases posteriores que
   acrescentaram testes. Registro para quem comparar as saídas.

5. **`range` resolve mas não isola a fase** — os 21 commits de `461ee38..7348d94` cobrem
   cinco fases. Conforme ao schema (§2.9.3), mas o commit de código da A.1 é só
   `240d708`. Achado herdado da tentativa 2, ainda não registrado no corpo do relatório.

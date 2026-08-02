---
spec: 002-vitrine-eval-e-saneamento
fase: A.1
slug_fase: rotacao-credencial
tentativa: 2
veredito: REPROVADO
score: 8.6
threshold: 8.5
range_avaliado: 461ee3805bf5f8848d4da6ebd23779ff8817c315..721f0f0892b3298964b04b917e3f1b0cb5a1cc69
---

# FASE A.1 — Avaliação independente

## 1. Veredito e score

**Veredito:** REPROVADO · **Score:** 8.6 / threshold 8.5

O score subiu acima do threshold, mas **há 1 BLOQUEANTE**, e BLOQUEANTE reprova
qualquer que seja o score (§2.10.3). O rework fechou o IMPORTANTE 4.1 (range) e
transformou o override conversacional numa decision registrada — que é exatamente
o que a constitution exige de um override genuíno. O que **não** mudou é o fato do
mundo: a conta do CalorIA em produção continua aceitando a senha vazada. Uma
decision registra *por que* um critério não foi cumprido; ela não o cumpre.

O próprio relatório é honesto quanto a isso — marca o AC-1 como `[ ]` e escreve:
*"Se o avaliador entender que só a troca efetiva fecha a fase, a reprovação se
mantém — e estará correta."* Está correta.

**Consequência de processo, e é o ponto principal desta avaliação:** com este
veredito `reprovacoes` da A.1 passa a **2**. Pela ARTIFACTS_SPEC §2.11.4, ao
selecionar o próximo rework o executor deve **parar e escalar ao owner** — o que é
o desfecho certo, porque o item pendente não é trabalho de agente: exige acesso ao
servidor de produção. A A.1 não deve voltar ao ciclo executor↔avaliador; deve ir
para a mesa do owner.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 3 | AC-4 ✓ (`frontend/e2e/auth.spec.ts:4`, lido por mim). AC-1 **não atendido** (§3.1) e assim marcado pelo próprio relatório (`EXECUCAO.md:111`). Escopo travado respeitado: histórico não reescrito nesta fase, credencial não escrita em nenhum artefato, rotação não executada pelo agente |
| 2 | Arquitetura e direção de dependências | 3 | 5 | Diff de 1 linha em arquivo de e2e; nada de produção tocado (`git diff --stat 461ee38..721f0f0 -- frontend/e2e/` → 3 linhas num arquivo) |
| 3 | Segurança / LGPD / multi-tenant | 3 | 3 | Working tree e histórico limpos, verificados por mim (`gitleaks` sobre 422 commits → `no leaks found`, §6). Desconto: a exposição residual é idêntica à da tentativa 1 — o que mudou foi só a documentação dela. Ganho real: a dependência "D.2 não abre o repositório antes disto" está agora escrita (`decisions/2026-08-02-senha-conta-caloria-producao.md:85-87`) |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | `http://localhost:3000` é o `baseURL`/`webServer.url` de `frontend/playwright.config.ts` — nenhuma porta inventada |
| 5 | Padrões de domínio/aplicação | 2 | 5 | `process.env.BASE_URL ?? <local>` mantém o padrão já usado no arquivo |
| 6 | Local e nomes dos arquivos | 2 | 5 | Exatamente o arquivo declarado na §5 da spec |
| 7 | Qualidade de código | 2 | 5 | O comentário de `auth.spec.ts:3` registra o *porquê*, não o *o quê* |
| 8 | Testes e cobertura | 2 | 4 | `npm test` → 17 suites, 100/100 (rodado por mim, §6). Sem teste novo — não cabia |
| 9 | Migration safety | 2 | [—] | Nenhuma migration tocada (NFR-7 preservado) |

Score = (3·3 + 3·5 + 3·3 + 3·5 + 2·5 + 2·5 + 2·5 + 2·4) / 20 · 2 = **8.6**

## 3. Achados BLOQUEANTES

### 3.1 — A credencial exposta continua válida na conta do CalorIA (mantido da tentativa 1)

**Onde:** `FASE-A.1-rotacao-credencial-EXECUCAO.md:119-123` (§6, AC-1) e
`.codeflow/decisions/2026-08-02-senha-conta-caloria-producao.md:44-53` vs. FR-A1,
AC-1 e o Critério de conclusão da Fase A.1 (spec §5) e o gate A.1 da DoD (§9).

**O defeito.** FR-A1 exige rotação "em todos os serviços onde tenha sido reusada";
AC-1 exige confirmação escrita "nos serviços afetados". A conta do CalorIA — o
serviço para o qual o par e-mail+senha *era* o login, e cujos dados são diário
alimentar, peso e conversas de IA de pessoa real — segue com a senha vazada.

**Cenário de falha concreto.** Quem clonou `gabriel-ngrs/CalorIA` enquanto era
público (até 2026-07-30) tem o par no histórico do clone local; a purga da A.2
reescreveu o remoto, não clones de terceiros. Se o backend de produção estiver no
ar, o caminho de login existe. E a Fase D.2 torna o repositório público de novo.

**Por que continua BLOQUEANTE apesar da decision.** A constitution admite override
de gate duro por decision registrada — e essa parte agora está correta: a decision
existe, está commitada, é anterior a esta avaliação, tem alternativas avaliadas e
risco residual quantificado. Mas o que a decision pode fazer é registrar um desvio
de **escopo**; ela não converte um **fato** ausente em fato presente. O gate da
fase é factual ("owner confirmou por escrito a rotação"), e o próprio executor o
marca `[ ]`. Aprovar aqui gravaria no pipeline que o FR-A1 está satisfeito e
liberaria a máquina de estados para fases que dependem disso — inclusive a D.2,
que reabre o repositório. Esse é o modo de falha concreto de um "APROVADO" leniente.

**Correção — nenhuma delas é trabalho de agente:**
1. Executar `~/trocar-senha-caloria.py` contra o banco de produção e registrar a
   confirmação escrita. Único caminho que fecha o FR-A1.
2. Ou levantar a URL do backend (é a Fase E.1), comprovar com evidência de
   requisição que ele está fora do ar, e registrar isso — o que fecharia o AC-1 por
   inalcançabilidade.
3. Ou o owner reordenar a spec: mover a A.1 para depois da E.1/E.4, ou aceitar
   formalmente o adiamento com uma alteração da §3/§5 da spec — não por decision
   isolada, porque é o texto do AC que está sendo relaxado.

Enquanto (1), (2) ou (3) não acontecer, a fase não fecha. Ver a consequência de
`reprovacoes >= 2` na §1.

## 4. Achados IMPORTANTES

Nenhum. O IMPORTANTE 4.1 da tentativa 1 (`range` não reconstruível) foi corrigido e
verificado:

```text
$ git merge-base --is-ancestor 461ee380 HEAD   → ANCESTRAL  (docs(specs): registra spec 002…)
$ git merge-base --is-ancestor 721f0f08 HEAD   → ANCESTRAL  (docs(specs): corrige escopo…)
```

## 5. Sugestões

- **O `range` agora resolve, mas descreve cinco fases, não uma.**
  `461ee38..721f0f0` engloba A.1, A.2, A.3, B.1 e B.2. É conforme ao schema
  (§2.9.3 manda "sempre do início original ao HEAD"), e a causa é real (as fases
  foram commitadas de forma intercalada), mas o efeito prático é que o range
  deixou de isolar o diff da fase. O commit de código desta fase é `240d708`, e só
  ele. Vale registrar isso no corpo do relatório para quem reavaliar depois.
- **A pendência da A.1 e o risco residual da OQ10 apontam para o mesmo gate.**
  A decision desta fase diz "a D.2 não deve ser executada antes desta pendência ser
  fechada"; a OQ10 diz que reabrir o repositório reexpõe commits órfãos em cache.
  São duas pré-condições da D.2 vivendo em dois lugares diferentes e em nenhum
  deles na §5 da spec. Um bullet "Depende de: fechamento da pendência A.1 + prazo
  da OQ10" no bloco da Fase D.2 evitaria que a próxima sessão as perdesse.

## 6. Comandos rodados + saídas reais

```text
# --- branch e ancestralidade do range (Passo 2) ---
$ git rev-parse --short HEAD
da08121
$ git status --porcelain | wc -l
0
$ git merge-base --is-ancestor 461ee3805bf5f8848d4da6ebd23779ff8817c315 HEAD  → ANCESTRAL
$ git merge-base --is-ancestor 721f0f0892b3298964b04b917e3f1b0cb5a1cc69 HEAD  → ANCESTRAL

# --- AC-4, lido do arquivo (não do relatório) ---
$ sed -n '3,4p' frontend/e2e/auth.spec.ts
// Default local: rodar a suíte sem BASE_URL definido nunca pode tocar produção.
const BASE_URL = process.env.BASE_URL ?? "http://localhost:3000";          ← AC-4 ✓

# --- credencial no working tree e no histórico, com as regras do projeto ---
$ gitleaks detect --source . --config .gitleaks.toml --redact --no-banner --exit-code 1
INF 422 commits scanned.
INF no leaks found
>>> EXIT=0                                                                 ✓

# --- e-mail de provedor de consumo fora de data/ (regex própria, não a do projeto) ---
$ grep -rInE '[A-Za-z0-9._%+-]+@(gmail|hotmail|outlook|yahoo|icloud|proton|live|bol|uol|terra)\.' \
    --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=.next \
    --exclude-dir=.venv --exclude-dir=data .
   → só `devteste@gmail.com` e `auditcaloria@gmail.com` (contas sintéticas declaradas
     nas allowlists de `.gitleaks.toml:88-104`) e as citações a elas em docs/artefatos.
     Nenhuma ocorrência do e-mail pessoal do owner.                        ✓

# --- make test-frontend (o alvo é `cd frontend && npm test`) ---
$ cd frontend && npm test
Test Suites: 17 passed, 17 total
Tests:       100 passed, 100 total
Time:        3.676 s                                                       ← gate ✓

# --- gates de frontend, além do pedido pela fase ---
$ cd frontend && npm run lint     → 1 Warning pré-existente (Plasma.tsx:156, exhaustive-deps); exit 0
$ cd frontend && npx tsc --noEmit → exit 0

# --- gates de backend: [—] justificado (a fase não toca backend); rodados assim mesmo ---
$ backend/.venv/bin/python -m ruff check .          → All checks passed!
$ backend/.venv/bin/python -m ruff format --check . → 119 files already formatted
$ backend/.venv/bin/python -m mypy app/             → Success: no issues found in 72 source files

# --- make test-integration: [—] NÃO RODADO ---
$ docker ps
The command 'docker' could not be found in this WSL 2 distro.
   # gate ausente do ambiente → `[—]`, não falha (SPEC §3.10)

# --- o BLOQUEANTE: não verificável por mim, e é essa a questão ---
# A URL do backend de produção não é descobrível pelo repositório
# (`Caddyfile.backend` usa `{$APP_DOMAIN}`), então não há como eu confirmar nem
# refutar que a conta esteja alcançável. Sondá-la é escopo da Fase E.1.

# --- árvore limpa ao final ---
$ git status --porcelain | wc -l
0
```

## 7. Itens da fase / DoD não atendidos

| Item (§5 / §9 da spec) | Estado |
|---|---|
| Passo 1 — rotação em todos os serviços afetados | **NÃO ATENDIDO** — conta do CalorIA pendente (§3.1) |
| Passo 2 — repositório privado | Atendido (executado pelo agente, com autorização registrada) |
| Passo 3 — `BASE_URL` local por default | Atendido |
| Passo 4 — working tree sem a credencial | Atendido, verificado por mim |
| Gate — `make test-frontend` verde | Atendido (100/100) |
| Gate — owner confirmou por escrito a rotação | **PARCIAL** — cobre os serviços de reuso, não o CalorIA |
| DoD global — decisão de escopo registrada em §8 ou decision | **Atendido nesta tentativa** — `decisions/2026-08-02-senha-conta-caloria-producao.md` |

## 8. Divergências entre o relatório e o código real

1. **Nenhuma divergência.** O diff de `frontend/e2e/auth.spec.ts` é exatamente o que
   o relatório descreve, o valor veio mesmo do `playwright.config.ts`, e o relatório
   continua sendo honesto contra si próprio: declara a pendência que aqui reprova e
   antecipa que a reprovação seria correta.

2. **`range` resolve, mas não isola** (§5, primeira sugestão) — os cinco SHAs
   remapeados são todos ancestrais de HEAD, o que fecha o achado da tentativa 1; o
   intervalo, porém, cobre as cinco fases do lote.

3. **A cláusula do HEAD remoto migrou do AC-1 para o AC-2 na spec** (§3, nota de
   2026-08-02) — confirmei a alteração no texto da spec. A leitura do relatório
   (`EXECUCAO.md:124-132`) confere com a spec commitada.

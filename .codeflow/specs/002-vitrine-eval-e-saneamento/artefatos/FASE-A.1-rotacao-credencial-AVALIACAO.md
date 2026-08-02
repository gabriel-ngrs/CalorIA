---
spec: 002-vitrine-eval-e-saneamento
fase: A.1
slug_fase: rotacao-credencial
tentativa: 1
veredito: REPROVADO
score: 8.3
threshold: 8.5
range_avaliado: 240d7089..240d7089 (reconstruído — ver §8)
---

# FASE A.1 — Avaliação independente

## 1. Veredito e score

**Veredito:** REPROVADO · **Score:** 8.3 / threshold 8.5

Reprovado por dois caminhos independentes da cascata (§2.10.3): há **1 BLOQUEANTE**
e o score ficou abaixo do threshold. A parte de código da fase é irrepreensível —
uma linha, com o valor reusado do `playwright.config.ts`. O que reprova é o passo 1,
que é a razão de existir da fase: a rotação da credencial **não foi concluída no
serviço que a credencial abria**.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 3 | AC-4 ✓ (`frontend/e2e/auth.spec.ts:4`); AC-1 parcial — rotação incompleta (§3.1). Escopo travado respeitado: histórico não reescrito nesta fase, credencial não escrita em nenhum artefato, rotação não executada pelo agente |
| 2 | Arquitetura e direção de dependências | 3 | 5 | Mudança de 1 linha em arquivo de teste e2e; nenhuma dependência de produção tocada (`git show 240d708 --stat` → 1 arquivo) |
| 3 | Segurança / LGPD / multi-tenant | 3 | 2 | Working tree e refs limpos (§6); mas a conta de produção do CalorIA segue aceitando a senha vazada e o frontend responde (`HTTP 307`) |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | `http://localhost:3000` é literalmente o `baseURL`/`webServer.url` de `frontend/playwright.config.ts` — nenhuma porta nova inventada |
| 5 | Padrões de domínio/aplicação | 2 | 5 | `process.env.BASE_URL ?? <local>` mantém o padrão já usado no arquivo |
| 6 | Local e nomes dos arquivos | 2 | 5 | Exatamente o arquivo declarado na §5 da spec |
| 7 | Qualidade de código | 2 | 5 | Comentário registra o *porquê* ("nunca pode tocar produção"), não o *o quê* — conforme a constitution |
| 8 | Testes e cobertura | 2 | 4 | `npm test` → 17 suites, 100/100 (rodado por mim); `playwright test --list` mantém 8 testes. Sem teste novo — nem cabia |
| 9 | Migration safety | 2 | [—] | Nenhuma migration tocada (NFR-7 preservado) |

Score = (3·3 + 3·5 + 3·2 + 3·5 + 2·5 + 2·5 + 2·5 + 2·4) / 20 · 2 = **8.3**

## 3. Achados BLOQUEANTES

### 3.1 — A credencial exposta continua válida no serviço que ela abre

**Onde:** `FASE-A.1-rotacao-credencial-EXECUCAO.md:144-154` (§9, item 1) vs.
FR-A1 / AC-1 / Critério de conclusão da Fase A.1.

**O defeito.** FR-A1 exige rotação "em todos os serviços onde tenha sido reusada" e
AC-1 exige confirmação escrita "nos serviços afetados". O relatório confirma a
rotação em Google/Gmail e nos demais serviços com reuso, e declara aberta
justamente **a conta do próprio CalorIA** — que é o serviço para o qual o par
e-mail+senha era o login, e cujo dado é diário alimentar, peso e conversas de IA
(dado de saúde de pessoa real).

**Cenário de falha concreto.** Qualquer pessoa que tenha clonado
`gabriel-ngrs/CalorIA` enquanto o repositório era público (até 2026-07-30) tem o par
em `frontend/e2e/auth.spec.ts:37-38` do histórico local — a purga da A.2 reescreveu
o remoto, não os clones de terceiros. O frontend de produção responde hoje:

```text
$ curl -s -o /dev/null -w "%{http_code}" https://frontend-nine-mu-59.vercel.app/
307
```

Logo o caminho de login existe. A defesa restante é apenas o repositório estar
privado, o que não retroage sobre clones já feitos — exatamente o raciocínio que a
própria §4 da spec usa para justificar a ordem "rotação antes da purga".

**Por que é BLOQUEANTE e não IMPORTANTE.** O Objetivo declarado da fase é
"interromper o dano ativo da credencial exposta". Enquanto a conta aceita a senha
vazada, o dano ativo não foi interrompido — a fase não cumpriu seu objetivo, e o
gate "owner confirmou por escrito a rotação" está satisfeito só em parte. A
constitution universal ("Gates duros não admitem override conversacional") impede
fechar isso por aceitação verbal de risco residual.

**Correção sugerida (barata, o executor já a preparou):**
1. Rodar o utilitário já entregue ao owner (`~/trocar-senha-caloria.py`), que aplica
   `hash_password` direto no banco, e registrar a confirmação escrita no relatório; **ou**
2. Verificar e registrar, com evidência de requisição, que o backend de produção
   está indisponível — o que tornaria a conta inalcançável até a Fase E.4 — e
   converter o item numa decision do framework, não numa nota de relatório.

Qualquer um dos dois fecha o AC-1. O caminho (1) é o único que fecha o FR-A1.

## 4. Achados IMPORTANTES

### 4.1 — O `range` do frontmatter não é reconstruível

**Onde:** `FASE-A.1-rotacao-credencial-EXECUCAO.md:8-10`.

`range: 56069b9d..7bb06aab`. Verificado:

```text
$ git merge-base --is-ancestor 56069b9d51d63b2ebcd34313584f9e0dc9af4204 HEAD
   → NÃO-ancestral   (sha pré-purga, inalcançável desde o filter-repo da A.2)
```

Pior: o `sha_final` `7bb06aab` foi atualizado no commit `95c6c8c` para a **ponta da
branch da época**, que é o commit da Fase B.2 (`test(backend): declara pre-condicoes
do smoke test`). O range declarado, portanto, engloba A.1 + A.2 + B.1 + B.2 + A.3 e
começa num commit que não existe mais. Tive de reconstruir o diff da fase por
mensagem de commit para poder avaliá-la — o Passo 2 do protocolo manda **PARAR**
nesse caso.

O commit real desta fase é `240d708 fix(seguranca): aponta BASE_URL do e2e para
ambiente local por padrao`.

**Correção sugerida:** atualizar `sha_inicial`/`sha_final`/`range` para
`461ee38..240d708` (shas pós-purga). Duas linhas.

## 5. Sugestões

- **Passo 2 executado pelo agente, não pelo owner.** A §5 da spec classifica "tornar
  o repositório privado" como ação do owner; o relatório registra a autorização
  explícita e o desvio (`EXECUCAO.md:58-61`). Transparência correta; ficaria melhor
  como decision do framework do que como parágrafo de relatório.
- **AC-1 é mal fatiado na spec.** A cláusula "o HEAD de todas as branches remotas
  deve estar livre dela" é insatisfazível pela A.1 isoladamente — depende do
  force-push da A.2. O próprio relatório aponta isso (§9, item 2). Sugestão do
  executor procede: mover a cláusula para o AC-2.

## 6. Comandos rodados + saídas reais

```text
# --- estado do repositório (verificado por mim, não pelo relatório) ---
$ gh repo view gabriel-ngrs/CalorIA --json visibility,isPrivate,forkCount
{"forkCount":0,"isPrivate":true,"visibility":"PRIVATE"}                    ← AC-1 (privado) ✓

# --- credencial no working tree e nas refs (valores redigidos) ---
$ grep -rIl '<e-mail-do-owner>' --exclude-dir=.git --exclude-dir=node_modules \
    --exclude-dir=.next --exclude-dir=.venv . | wc -l
0                                                                          ✓
$ git log dev main test --oneline -S'<e-mail-do-owner>' | wc -l
0                                                                          ✓
$ git log --all --oneline -S'<e-mail-do-owner>' | wc -l
0                                                                          ✓

# --- o arquivo da fase ---
$ sed -n '3,4p' frontend/e2e/auth.spec.ts
// Default local: rodar a suíte sem BASE_URL definido nunca pode tocar produção.
const BASE_URL = process.env.BASE_URL ?? "http://localhost:3000";          ← AC-4 ✓
$ grep -rn "vercel.app" frontend/e2e/ | wc -l
0                                                                          ✓

# --- make test-frontend (alvo = cd frontend && npm test) ---
$ cd frontend && npm test
Test Suites: 17 passed, 17 total
Tests:       100 passed, 100 total
Time:        6.171 s                                                       ← gate ✓

# --- produção responde (contradiz "risco residual baixo" do §9.1) ---
$ curl -s -o /dev/null -w "%{http_code}" https://frontend-nine-mu-59.vercel.app/
307

# --- gates de backend: [—] justificado ---
# A fase não toca `backend/`. Rodei mesmo assim, na ponta da branch, e estão limpos:
$ backend/.venv/bin/python -m ruff check .   → All checks passed!
$ backend/.venv/bin/python -m mypy app/      → Success: no issues found in 72 source files

# --- árvore limpa ao final da avaliação ---
$ git status --porcelain | wc -l
0
```

## 7. Itens da fase / DoD não atendidos

| Item (§5 / §9 da spec) | Estado |
|---|---|
| Passo 1 — rotação em todos os serviços afetados | **NÃO ATENDIDO** — conta do CalorIA pendente (§3.1) |
| Passo 2 — repositório privado | Atendido (executado pelo agente, com autorização) |
| Passo 3 — `BASE_URL` local por default | Atendido |
| Passo 4 — working tree sem a credencial | Atendido |
| Gate — `make test-frontend` verde | Atendido (100/100) |
| Gate — owner confirmou por escrito a rotação | **PARCIAL** — confirmação cobre os serviços de reuso, não o CalorIA |
| DoD global — decisão de escopo registrada em §8 ou decision | **NÃO ATENDIDO** — o desvio do passo 2 vive só no relatório |

## 8. Divergências entre o relatório e o código real

1. **Nenhuma divergência de código.** O diff de `frontend/e2e/auth.spec.ts` é
   exatamente o que o relatório descreve, e o valor foi de fato reusado do
   `playwright.config.ts`. O relatório é honesto inclusive contra si mesmo — ele
   próprio declara a pendência que aqui vira BLOQUEANTE.

2. **`range` inconsistente** (§4.1): o `sha_final` declarado não é o commit desta
   fase, e o `sha_inicial` não é alcançável a partir de HEAD.

3. **"Risco residual baixo" é otimista.** `EXECUCAO.md:147-150` fundamenta o risco
   baixo em três mitigações. Duas se confirmam (repositório privado, credencial fora
   do histórico). A terceira — "o ambiente de produção será reconstruído na Fase E.4
   de qualquer forma" — é um plano futuro, e enquanto ele não acontece o frontend de
   produção está no ar e respondendo.

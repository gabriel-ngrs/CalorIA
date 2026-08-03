---
spec: 002-vitrine-eval-e-saneamento
fase: B.4
slug_fase: cobertura
tentativa: 2
veredito: RESSALVAS
score: 9.7
threshold: 8.5
range_avaliado: 8660f40..2e6cd1d1d2a7c060d34fda9137c7aa0b25e52a6f
---

# FASE B.4 — Avaliação independente

## 1. Veredito e score

**Veredito:** RESSALVAS · **Score:** 9.7 / threshold 8.5

**O achado da tentativa 1 está fechado, e fechado exatamente como pedido.** O `..%`
de `backend/pyproject.toml:116` virou `73%`, e a segunda metade da linha deixou de
remeter ao `fail_under` — passou a declarar a medição (`medido: 73,10%`), que era o
ponto. Verifiquei o arquivo, não o relatório.

**O que impede o APROVADO é um item novo, e ele não estava visível na tentativa 1:**
o gate declarado da fase é *"AC-9 satisfeito; **CI verde com o gate ativo**"*, e o
gate **nunca rodou no CI**. Não é questão de aguardar um push futuro — o `ci.yml` que
está no GitHub hoje sequer contém a flag. Medi: `origin/dev` está em `da08121`
(2026-08-02 16:48), **38 commits atrás** do `dev` local. Detalhe em §4.

Registro que a avaliação da tentativa 1 não classificou este item como IMPORTANTE,
tratando-o como ação do owner. Estou aplicando aqui o mesmo critério que as avaliações
da C.7 e da D.1 já aplicavam nas fases delas — gate declarado e não satisfeito é
IMPORTANTE. A inconsistência estava entre as avaliações anteriores, não entre elas e
esta; e o executor não tem culpa dela.

Tudo o mais da fase verifica, e verifica bem: o piso está ativo, reprova de verdade
quando a cobertura cai, os 12 endpoints estão cobertos, e há 5 casos de autorização
cruzada onde a fase pedia um.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 4 | AC-9 verificado por mim nas duas metades: o gate ativo passa (`Required test coverage of 72.0% reached. Total coverage: 74.28%`) e **reprova de fato** (`FAIL Required test coverage of 72% not reached. Total coverage: 65.23%`, §6). 36 testes nos 12 endpoints, verdes. Escopo travado respeitado: `push.py` não refatorado, piso (72) abaixo do medido (74,28), nenhum teste sem asserção. Desconto: o gate "CI verde com o gate ativo" não está satisfeito (§4) |
| 2 | Arquitetura e direção de dependências | 3 | 5 | Testes de integração sobre a API pública dos routers; nenhum router redesenhado, como o escopo travado manda |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | 5 casos de autorização cruzada, leitura **e** escrita, nos dois routers (`test_push.py:119,171,198`; `test_reminders.py:36,106`). A fase pedia "ao menos um". `test_push.py:53-57` documenta que `vapid-public-key` é público **por desenho**, em vez de o teste "corrigir" o código — a conduta certa |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | Fixtures `client`, `anon_client`, `db`, `test_user` de `tests/conftest.py` reusadas; nenhuma fixture nova criada |
| 5 | Padrões de domínio/aplicação | 2 | 5 | Testes seguem a forma das demais suítes de integração (classes por router, `AsyncClient`) |
| 6 | Local e nomes dos arquivos | 2 | 5 | Exatamente os arquivos declarados em "Arquivos novos/alterados" da §5 |
| 7 | Qualidade de código | 2 | 5 | O bloco `[tool.coverage.report]` registra o *porquê* do piso e o histórico com número em cada linha — que é o propósito declarado dele |
| 8 | Testes e cobertura | 2 | 5 | Suíte completa no container: `620 passed, 1 skipped`, cobertura 74,28% contra piso 72% (§6) |
| 9 | Migration safety | 2 | [—] | Nenhuma migration alterada pela fase |

Score = (3·4 + 3·5 + 3·5 + 3·5 + 2·5 + 2·5 + 2·5 + 2·5) / 20 · 2 = 97/20 · 2 = **9.7**

## 3. Achados BLOQUEANTES

Nenhum.

**B4-IMP-1 da tentativa 1 está fechado.** `backend/pyproject.toml:116-117`:

```text
#   2026-08-02  73%  após o schema de teste vir das migrations, que destravou
#                    os 5 testes do golden set (medido: 73,10%)
```

O número entrou e a remissão ao `fail_under` saiu. É a correção exata que a avaliação
pediu, num commit de 2 linhas (`549950c`).

## 4. Achados IMPORTANTES

**B4-IMP-2 — o gate declarado da fase ("CI verde com o gate ativo") não foi satisfeito,
e não é questão de esperar: o gate não existe no remoto.**

**Onde:** Critério de conclusão da B.4 (`SPEC_002...md`, bloco da Fase B.4) e §9 do DoD
(*"B.4 — AC-9; piso de cobertura ativo **e CI verde**"*), contra o estado real de
`origin/dev`.

**O defeito.** Medi:

```text
$ git log --format='%h %ad %s' --date=short -1 origin/dev
da08121 2026-08-02 docs(specs): aplica rework das cinco fases do track a apos avaliacao
$ git rev-list --count origin/dev..dev
38
$ git show origin/dev:.github/workflows/ci.yml | grep -c "cov-fail-under"
0
$ gh run list --branch dev --limit 3
success  docs(specs): aplica rework das cinco fases...  CI  dev  push  2026-08-02T16:48:46Z
```

O `--cov-fail-under=72` está em `.github/workflows/ci.yml:98` **no repositório local**,
e a última execução de CI no GitHub foi sobre um commit cujo `ci.yml` não tinha a flag.
Logo, "o CI falha quando a cobertura cai abaixo do piso" nunca foi exercitado no CI —
só localmente, no container, que é evidência boa mas não é o gate que a fase declarou.

**Por que é IMPORTANTE e não sugestão.** É o critério de conclusão que a própria fase
se impôs, e o §9 o repete. Verificar o piso no container prova que a flag funciona; não
prova que o job do GitHub Actions reprova o build — que é o que transforma cobertura de
"métrica observada" em gate, o Objetivo declarado da fase.

**Por que não é BLOQUEANTE.** Nada no código está errado, o comportamento está
demonstrado no mesmo par Postgres 16 + Redis que o CI usa, e o que falta é uma ação do
owner de um comando.

**Correção.** `git push origin dev`, conferir o job `backend` verde no Actions com a
flag ativa, e anexar a saída (ou o link da execução) como seção datada no EXECUCAO da
B.4. É a única pendência da fase.

## 5. Sugestões

- **O relatório mistura quatro medições de cobertura sem dizer qual é a vigente.** §1
  diz 72%, §5 diz 71,98%, §6 diz 71,92%, o bloco de "Tentativa 2" diz 73,86% — e eu medi
  74,28%. Todas são verdadeiras em momentos diferentes, e o relatório explica a subida,
  mas quem ler a §1 primeiro sai com o número errado. Vale um "medição vigente" no topo,
  com data.
- **A dúvida 2 do relatório merece resposta explícita:** sim, manter
  `continue-on-error: true` no upload ao Codecov é a leitura correta do passo 4 — ele
  autoriza mantê-lo "caso contrário" e aplicar o gate localmente, que é o que
  `ci.yml:98` faz. Vale fechar a dúvida no relatório para não reabrir depois.

## 6. Comandos rodados + saídas reais

> Gates compartilhados rodados uma vez sobre o HEAD atual (`c20529b`), descendente do
> `sha_final` desta fase; as verificações específicas da B.4 vêm na sequência.

```text
# --- Passo 2: ancestralidade do range e árvore limpa ---
$ git branch --show-current
dev
$ git status --porcelain | wc -l
0
$ git merge-base --is-ancestor 8660f40 HEAD                                  → ANCESTRAL
    8660f40 feat(evals): adiciona camada rapida com cassettes e serie temporal versionada
$ git merge-base --is-ancestor 2e6cd1d1d2a7c060d34fda9137c7aa0b25e52a6f HEAD → ANCESTRAL

# --- a correção da tentativa 2, lida do arquivo ---
$ sed -n '111,120p' backend/pyproject.toml
#   2026-05-10  62%  auditoria
#   2026-08-02  72%  fase B.4 (testes de push/reminders), piso posto em 70%
#   2026-08-02  73%  após o schema de teste vir das migrations, que destravou
#                    os 5 testes do golden set (medido: 73,10%)
fail_under = 72                                                              ← B4-IMP-1 ✓
$ git show 549950c --stat
 backend/pyproject.toml | 4 ++--

# --- AC-9, metade "o gate passa" ---
$ docker exec caloria_backend pytest -q --cov=app --cov=evals --cov-report=term
TOTAL                                      3869    995    74%
Required test coverage of 72.0% reached. Total coverage: 74.28%
620 passed, 1 skipped, 5 warnings in 101.82s                                 ✓

# --- AC-9, metade "o gate reprova" (limitando à suíte unitária) ---
$ docker exec caloria_backend pytest tests/unit --cov=app --cov-fail-under=72 -q
TOTAL                                      3244   1128    65%
FAIL Required test coverage of 72% not reached. Total coverage: 65.23%
472 passed in 6.10s                                                          ✓

# --- AC-9, cobertura dos 12 endpoints ---
$ docker exec caloria_backend pytest tests/integration/test_push.py \
                                     tests/integration/test_reminders.py -q
36 passed, 2 warnings in 24.92s                                              ✓
$ grep -n "de_outro_usuario" backend/tests/integration/test_{push,reminders}.py | wc -l
5      # autorização cruzada, leitura e escrita, nos dois routers            ✓
$ sed -n '53,57p' backend/tests/integration/test_push.py
async def test_e_publico_por_desenho(self, anon_client: AsyncClient) -> None:
    """A chave pública VAPID é pública: o service worker a busca antes do login."""
    assert (await anon_client.get("/api/v1/push/vapid-public-key")).status_code == 200

# --- o gate de CI: NÃO satisfeito (achado 4.1) ---
$ git log --format='%h %ad %s' --date=short -1 origin/dev
da08121 2026-08-02 docs(specs): aplica rework das cinco fases do track a apos avaliacao
$ git rev-list --count origin/dev..dev
38
$ git show origin/dev:.github/workflows/ci.yml | grep -c "cov-fail-under"
0
$ grep -n "cov-fail-under" .github/workflows/ci.yml
98:        run: pytest --cov=app --cov-report=xml --cov-fail-under=72 -q      ← só local

# --- demais gates do manifest, sobre o HEAD atual ---
$ docker exec caloria_backend ruff check .          → All checks passed!
$ docker exec caloria_backend ruff format --check . → 147 files already formatted
$ docker exec caloria_backend mypy app/ evals/      → Success: no issues found in 81 source files
$ cd frontend && npm test         → 20 suites, 118/118 passed
$ cd frontend && npm run lint     → exit 0 (1 Warning pré-existente, Plasma.tsx:156)
$ cd frontend && npx tsc --noEmit → exit 0

$ git status --porcelain | wc -l
0
```

## 7. Itens da fase / DoD não atendidos

| Item (§5 / §9 da spec) | Estado |
|---|---|
| Passo 1 — cobertura remedida e registrada | Atendido (62% → 74,28% hoje, medido por mim) |
| Passo 2 — testes de integração dos 12 endpoints + autorização cruzada | Atendido (36 testes; 5 casos cruzados, pedia 1) |
| Passo 3 — `fail_under` com o medido arredondado para baixo | Atendido (`fail_under = 72`, medido 74,28) |
| Passo 4 — `continue-on-error` mantido com gate local | Atendido (`ci.yml:98`, `:105`) |
| AC-9 — o gate falha quando a cobertura cai | Atendido, demonstrado nas duas direções |
| **Gate — CI verde com o gate ativo** | **NÃO ATENDIDO** — o `ci.yml` do remoto não tem a flag; 38 commits não empurrados (achado 4.1) |

## 8. Divergências entre o relatório e o código real

1. **Nenhuma divergência no código.** A correção do `..%` está no arquivo, é de 2 linhas,
   e o commit `549950c` toca só `backend/pyproject.toml`.

2. **O relatório declara o gate de CI como "dependente de um push, que é ação do owner"**
   (§"Fora do escopo desta correção"). Verdadeiro, mas incompleto: não é só que o push não
   ocorreu — o `ci.yml` publicado é anterior à flag, e são 38 commits de defasagem, não um.
   Quem lê o relatório imagina uma pendência de minutos; a medição mostra que o CI está
   cego para todo o Track C e metade do B desde 2026-08-02.

3. **Números de cobertura divergem entre seções do relatório** (72 / 71,98 / 71,92 / 73,86)
   e do que medi hoje (74,28). Não é defeito — são medições reais de momentos diferentes,
   e o relatório explica a subida. Registro para quem comparar as saídas.

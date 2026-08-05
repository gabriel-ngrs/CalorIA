---
spec: 002-vitrine-eval-e-saneamento
fase: B.5
slug_fase: vision-parser-bug001
tentativa: 3
veredito: APROVADO
score: 9.8
threshold: 8.5
range_avaliado: 36d68cc..3655892
---

# FASE B.5 — Avaliação independente

## 1. Veredito e score

**Veredito:** APROVADO · **Score:** 9.8 / threshold 8.5 — zero BLOQUEANTES, zero
IMPORTANTES.

**O B5-IMP-2 está fechado, e fechado melhor do que eu havia pedido.** Eu sugeri
descrever o estado atual; o rework fez isso **e** recusou a saída fácil de apagar o
bullet. A recusa está certa e vale registrar: o item continua na lista *"o que este
eval NÃO mede"*, com o sujeito corrigido — o que o harness não mede hoje não é "o
caminho de foto", é **"o caminho de foto na configuração de produção"**, porque lá
ele estoura em 413. Apagar o bullet teria trocado uma afirmação falsa por uma
omissão igualmente enganosa, e o rework enxergou isso sozinho.

**A varredura de classe que a avaliação pediu foi feita e eu a refiz.**
`grep -n "ignora\|não executa\|entra na fase"` sobre `backend/evals/README.md`
volta vazio. As duas menções restantes a B.5 em código e doc estão corretas:
`README.md:24` ("o runner **executa** o estrato `foto` desde a B.5") e
`runner.py:222` ("é o que a B.5 corrigiu"), ambas no tempo verbal certo. As
ocorrências em `docs/auditoria/` são numeração de seção (`## B.5 Pydantic`,
`### B.5 Type checking strict`), sem relação — confirmei uma a uma.

**O diff desta tentativa é exatamente o que deveria ser:** dois arquivos, um deles o
próprio relatório. Nenhuma linha de código, nenhuma ampliação oportunista. `ruff`,
`ruff format`, `mypy app/ evals/` e os 496 testes unitários seguem verdes, rodados
por mim.

Com isto, o gate da fase está inteiro: AC-17 verificado desde a tentativa 1, delta
do estrato de foto medido com números na tentativa 2, e a documentação coerente com
o que o código faz na tentativa 3.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 5 | AC-17 (3 cláusulas) verificado na t1; gate do delta atendido na t2 (EXECUCAO §5.1); B5-IMP-2 fechado em `3655892`. Escopo travado intacto nas três tentativas: `git diff 36d68cc..3655892 -- backend/app/services/ai/meal_parser.py` vazio |
| 2 | Arquitetura e direção de dependências | 3 | 5 | `runner.py:196-213` `versao_de_visao()` mede sem promover; `:216-231` roteia por estrato. Nada mudou nesta tentativa e nada precisava mudar |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | Diff só de markdown; `gitleaks` limpo sobre o histórico (t2, §6); nenhum segredo, PII ou URL de produção nos textos novos |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | O README passou a documentar `--versao-vision` apontando para a CLI existente, sem duplicar a explicação que já vive no docstring de `runner.py:196-203` |
| 5 | Padrões de domínio/aplicação | 2 | 5 | O bullet permanece na seção de honestidade que o `eval_golden_set.py:14-27` estabeleceu como padrão do projeto — corrigido no sujeito, não removido |
| 6 | Local e nomes dos arquivos | 2 | 5 | Correção no arquivo certo (`backend/evals/README.md`), nas duas ocorrências; relatório atualizado com §0 datando a tentativa |
| 7 | Qualidade de código | 2 | 5 | `ruff check` + `ruff format --check` + `mypy app/ evals/` limpos (§6); o exemplo de CLI no README é executável como está |
| 8 | Testes e cobertura | 2 | 4 | Os 13 testes do caminho de foto seguem verdes (0,19 s). Desconto: nenhum teste guarda a coerência README × runner, e é a segunda vez nesta spec que documentação e código divergem — a própria E.3 mostrou o padrão que resolveria isso (§5, sugestão 1) |
| 9 | Migration safety (se aplicável) | 2 | [—] | Nenhuma migration em nenhuma das três tentativas (NFR-7 preservada) |

Score = 98 / 20 × 2 = **9.8**.

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

Nenhum. O B5-IMP-2 da tentativa 2 é o último achado da fase e está fechado
(verificação em §6).

## 5. Sugestões

Nenhuma bloqueia; as três primeiras são carregadas das tentativas anteriores e
seguem válidas.

1. **Um teste que trave a coerência entre o README do harness e o runner.** É a
   sugestão nova, e nasce do próprio B5-IMP-2: a divergência doc × código já
   ocorreu duas vezes nesta spec, e das duas vezes só um leitor humano a pegou. A
   E.3 resolveu o caso análogo com três asserções triviais
   (`test_seed_demo.py::TestCredenciaisPublicadas`). O equivalente aqui seria um
   teste que falhe se `backend/evals/README.md` voltar a afirmar que o runner
   ignora o estrato de foto — algo como assertar que o README não contém
   `"ignora o estrato"` enquanto `Estrato.FOTO` for roteável em `runner.py`. Cabe
   em 10 linhas e vale para a próxima vez que alguém mexer no runner.
2. **As quatro execuções do delta continuam sem artefato durável**
   (`runs/ultimo-relatorio.json` é ignorado pelo git e já foi sobrescrito). Segue
   valendo a recomendação da t2: anexar os quatro JSON como
   `artefatos/B.5-delta-foto-v<N>-r<R>.json`, e **não** registrá-los no
   `history.jsonl`, cuja série é lida como configuração de produção.
3. **`VisionParser(cliente)` é instanciado mesmo sem caso de foto**
   (`runner.py:626`). Inofensivo hoje.
4. **O 413 (OQ19) é a dívida que esta fase deixa aberta e não podia fechar.** Minha
   recomendação ao owner segue a mesma: fase nova, não rework da C.2. Enquanto ele
   existir, o estrato de foto do eval mede uma configuração que não é a de
   produção — e agora o README diz isso, que era o ponto.

## 6. Comandos rodados + saídas reais

```text
$ git merge-base --is-ancestor 3655892 HEAD && echo "3655892 ANCESTRAL OK"
3655892 ANCESTRAL OK

# --- o diff desta tentativa, inteiro ---
$ git diff 4e9b54d..HEAD --stat
 .../FASE-B.5-vision-parser-bug001-EXECUCAO.md      | 37 +++++++++++++++++++---
 backend/evals/README.md                            | 23 +++++++++++---
 2 files changed, 51 insertions(+), 9 deletions(-)
   → um arquivo de documentação e o próprio relatório. Zero código

# --- o B5-IMP-2, ponto a ponto ---
$ sed -n '23,28p' backend/evals/README.md
- **O caminho de foto na configuração de produção.** O runner **executa** o
  estrato `foto` desde a B.5, pelo `VisionParser` de produção — mas com
  `n = 3`, o estrato menor e mais frágil do dataset. E com o `GROQ_MAX_TOKENS`
  de produção as três chamadas falham com **HTTP 413** (OQ19): o teto de saída
  reservado estoura o limite por minuto antes de a imagem chegar. Enquanto isso
  durar, nenhum número deste estrato vale como linha de base de produção.

$ sed -n '138,149p' backend/evals/README.md
O runner **executa** o estrato `foto` (`runner.py`), roteando o caso pelo
`VisionParser` de produção … Para medir uma versão do prompt de visão **sem
promovê-la** em `VERSOES_EM_PRODUCAO`, use `--versao-vision`:
    python -m evals.runner --estrato foto --versao-vision 1   # antes
    python -m evals.runner --estrato foto --versao-vision 2   # depois
   → confere com a CLI real (`runner.py:676-686`) e com `_prompts_usados`
     (`runner.py:452-469`), que lê a versão do módulo e não de `get_prompt`

# --- a varredura de classe, refeita por mim ---
$ grep -n "ignora\|não executa\|entra na fase" backend/evals/README.md
(vazio)
$ grep -rn "B\.5" docs/ backend/ --include=*.md --include=*.py | grep -v ".venv\|artefatos/"
docs/auditoria/02-backend.md:104:## B.5 Pydantic — `from_attributes`      ← numeração
docs/auditoria/plano.md:190:### B.5 Type checking strict                   ← numeração
backend/evals/README.md:24: … o runner **executa** o estrato `foto` desde a B.5   ← correta
backend/evals/runner.py:222: … é o que a B.5 corrigiu                       ← correta
backend/tests/unit/test_evals_runner_foto.py:1,5,227                        ← corretas
backend/tests/unit/test_prompt_registry.py:28                               ← correta

# --- escopo travado, verificado sobre o range inteiro da fase ---
$ git diff 36d68cc..3655892 --stat -- backend/app/services/ai/meal_parser.py
(vazio)                                 ← `MealParser` intocado nas três tentativas
$ git diff 36d68cc..3655892 --stat -- backend/app/services/ai/vision_parser.py
 backend/app/services/ai/vision_parser.py | (alterado só na t1, já avaliada)

# --- gates do projeto, rodados agora ---
$ docker compose -f docker-compose.dev.yml exec -T backend sh -c \
    "ruff check . && ruff format --check . && mypy app/ evals/"
All checks passed!
149 files already formatted
Success: no issues found in 81 source files

$ docker compose -f docker-compose.dev.yml exec -T backend pytest tests/unit -q
496 passed, 3 skipped in 4.04s

$ git status --short
(vazio — árvore limpa ao fim da avaliação)
```

**Não rodei nesta tentativa:** `pytest tests/integration/` (145 passed rodados por
mim na avaliação da t2, sobre o mesmo código de produção, que não mudou) e os gates
de frontend (nenhum arquivo de frontend no diff). `[—]` justificados.

## 7. Itens da fase / DoD não atendidos

Nenhum.

| Item (§5 / §9) | Estado |
|---|---|
| AC-17 — nenhum item perdido em silêncio | ✓ t1 |
| AC-17 — quantidade por extenso não vira 500 | ✓ t1 |
| AC-17 — prompt de visão sem as regras 4 e 5 | ✓ t1 |
| Passo 3 — `0.35` extraído para constante nomeada | ✓ t1 |
| Passo 5 / gate — delta do estrato de foto com números antes e depois | ✓ t2, EXECUCAO §5.1 |
| §9 global — decisão de escopo registrada em §8 ou decision | ✓ OQ19 + decision de 2026-08-04 |
| §9 global — documentação coerente com o estado real | ✓ **t3**, `3655892` |

Fora do gate, e por decisão registrada: o HTTP 413 (OQ19) segue aberto e é da C.2 /
frontend / fase nova — não desta fase.

## 8. Divergências entre o relatório e o código real

Nenhuma. As três afirmações verificáveis da §0 do EXECUCAO reproduzem aqui: as duas
correções no README estão onde ele diz, o `grep` da classe volta vazio, e nenhuma
linha de código mudou. O frontmatter está conforme o §2.9.6 — `status: rework`,
`tentativa: 3`, `reprovacoes: 2`, `sha_inicial` preservado do original e
`range: 36d68cc..3655892` coerente com os dois campos.

---

**Fase concluída.** APROVADO é o único veredito que fecha uma fase (§2.11.3). A B.5
chegou ao fim sem estourar o teto: três tentativas, `reprovacoes: 2`, e a terceira
gastou dois pontos de documentação em vez de código — porque o código já estava
certo desde a primeira, verificado por dois avaliadores independentes. Nada aqui
bloqueia a C.8 nem a D.3; a dívida que a fase deixa (o 413) está nomeada, medida e
na mesa do owner.

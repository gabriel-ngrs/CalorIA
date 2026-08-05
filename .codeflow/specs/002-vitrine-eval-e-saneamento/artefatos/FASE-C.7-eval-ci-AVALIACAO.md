---
spec: 002-vitrine-eval-e-saneamento
fase: C.7
slug_fase: eval-ci
tentativa: 3
veredito: REPROVADO
score: 8.9
threshold: 8.5
range_avaliado: 40e2941..208d85d
---

# FASE C.7 — Avaliação independente

## 1. Veredito e score

**Veredito:** REPROVADO · **Score:** 8.9 / threshold 8.5 — reprovado por
**BLOQUEANTE**, não por score.

**Primeiro o que esta tentativa entregou, porque é muito.** A execução completa
contra o provedor real aconteceu, e produziu os três números que a fase perseguia
desde a tentativa 1: 43 casos, 57 chamadas, 42.932 tokens, 4min40s; o gate
`evals.report verificar` foi exercitado e reprovou com exit 1; e o limite que morde
no free tier foi **medido** — TPD 100.000, 99.768 consumidos —, o que confirma a
agenda semanal por número em vez de palpite. Conferi tudo isso contra o
`history.jsonl` versionado, não contra a prosa do relatório: a linha
`run_id=e1d39b03675b-0758d981c3c0` traz `chamadas: 57`, `tokens_in 38833 +
tokens_out 4099 = 42.932`, `mdape 33.33`, `simples 25.53`, `composto 61.64`, e as
três falhas com o texto do HTTP 413. Bate com o relatório inteiro.

**E a decisão mais importante desta tentativa foi a de não fazer:** os limiares não
foram recalibrados para o gate passar. Isso é disciplina, é o que o escopo travado
exige, e é o oposto do reflexo comum. Endosso sem ressalva.

**O que reprova é uma coisa só, e ela é do tipo que esta spec já pagou caro para
aprender.** A linha da C.7 na §9 exigia *"execução agendada completa **sem casos
vazios**"*. Esta tentativa a reescreveu para *"execução completa registrada"* — e a
cláusula "sem casos vazios" não migrou para lugar nenhum. Ela não está no AC-19,
para onde a cláusula de plataforma foi; não está numa decision; não é mencionada na
OQ20, que só fala de `workflow_dispatch`. Enquanto isso o **AC-15 continua
pedindo** "conclui sem casos vazios", e a mesma linha da §9 continua exigindo
AC-15. A execução teve 3 casos vazios. O relatório marca AC-15 `[x]` reinterpretando
"casos vazios" pela redação da **NFR-3** ("por 429"), que é outro requisito.

Resultado: o critério de conclusão da fase foi afrouxado durante a própria execução
da fase, e a spec voltou a se contradizer (§9 × §3) — que é literalmente o defeito
que a D.1 levou quatro tentativas para eliminar.

**Sobre a migração da cláusula de plataforma eu não tenho objeção.** O `HTTP 404` é
real — confirmei com `gh workflow list`, o `eval.yml` não aparece —, a causa é a
`main` parada por decisão de owner (OQ15), e há dois precedentes aceitos (A.1, D.1).
A retratação da OQ15 é honesta e bem-feita. O problema não é essa migração: é a
segunda cláusula, que sumiu junto sem que ninguém dissesse que estava sumindo.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 2 | AC-15 exige "conclui sem casos vazios" (SPEC §3:366-369); a execução teve 3 vazios (`history.jsonl`, `falhas[]`), e a §9 foi reescrita perdendo a cláusula (SPEC §9:1732). Escopo travado em si respeitado: nenhum `continue-on-error` no `eval.yml`, nenhum limiar afrouxado, nenhum cassette com credencial |
| 2 | Arquitetura e direção de dependências | 3 | 5 | Zero código novo; a execução reusou os passos do `eval.yml` na ordem declarada (runner → invariância → registrar → verificar), sem script paralelo que mascarasse erro do workflow |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | `grep -rlE "gsk_\|Authorization\|api[_-]?key" backend/evals/cassettes/` → vazio nos 71 cassettes; `gitleaks` sobre 496 commits → no leaks (§6) |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | 57 cassettes gravados pelo caminho de gravação já existente (`evals/cassettes/__init__.py`), não por rotina nova; registro pelo `evals.report registrar` de sempre |
| 5 | Padrões de domínio/aplicação | 2 | 5 | `history.jsonl` append-only respeitado; a execução foi registrada **mesmo reprovando**, que é a ordem do `eval.yml` e evita série que mente por omissão |
| 6 | Local e nomes dos arquivos | 2 | 5 | Cassettes em `backend/evals/cassettes/`, relatório efêmero em `runs/` (ignorado), série em `runs/history.jsonl` — tudo onde a C.3/C.8 definiu |
| 7 | Qualidade de código | 2 | 4 | `ruff`/`ruff format`/`mypy app/ evals/` limpos. Desconto: o cabeçalho do `.github/workflows/eval.yml:9-12` segue dizendo "com ~10 casos … Ajustar junto de uma medição real de consumo, não por palpite" — a medição existe desde esta tentativa e não foi propagada (§4) |
| 8 | Testes e cobertura | 2 | 5 | Camada rápida rodada por mim: 26 testes de snapshot verdes; o bloco inteiro (snapshot + foto + seed) em 0,19 s, muito abaixo dos 60 s da NFR-2 |
| 9 | Migration safety (se aplicável) | 2 | [—] | Nenhuma migration no diff |

Score = 89 / 20 × 2 = **8.9** (acima do threshold; o veredito vem do BLOQUEANTE,
pela precedência estrita do §2.10.3).

## 3. Achados BLOQUEANTES

### C7-BLQ-1 — a cláusula "sem casos vazios" saiu do gate da fase sem migrar para lugar nenhum

**Onde:** `SPEC_002_VITRINE_EVAL_E_SANEAMENTO.md:1732-1736` (§9, linha da C.7),
alterada em `181fb5c`.

Antes:

> - [ ] **C.7** — AC-15, NFR-2, NFR-3; execução agendada completa **sem casos vazios**.

Depois:

> - [ ] **C.7** — AC-15, NFR-2, NFR-3; execução completa registrada. *(Executada
>   local em 2026-08-04 … A cláusula de plataforma, `workflow_dispatch` no GitHub,
>   migrou para a D.2 — ver OQ20.)*

Duas cláusulas caíram, e só uma foi tratada:

| Cláusula | Destino |
|---|---|
| "agendada" (plataforma) | migrou para o AC-19 (`SPEC §3:388-394`), com OQ20 e argumento medido — **legítimo** |
| "sem casos vazios" | **nenhum** — não está no AC-19, não está em decision, não é citada na OQ20 |

E ela continua viva no AC-15 (`SPEC §3:366-369`): *"E dado a execução agendada,
então a camada completa roda contra o provedor real e **conclui sem casos vazios**"*.
A mesma linha da §9 que perdeu a cláusula segue exigindo "AC-15". Logo a spec pede e
não pede a mesma coisa, e a execução avaliada tem 3 casos vazios
(`backend/evals/runs/history.jsonl`, último registro, `falhas[]` com os três
`foto-*`).

O EXECUCAO §8 marca **`[x]` para "AC-15 / NFR-3"** com a justificativa *"os 3 casos
vazios são por HTTP 413 (OQ19), não por quota; a NFR-3 fala de 429"*. O argumento
vale para a **NFR-3**, cuja redação é mesmo "casos vazios por `429`" (SPEC §2:293-294)
— e ali eu concordo, a NFR-3 está satisfeita. Ele **não** vale para o AC-15, que não
tem esse qualificador. Um AC se lê pela letra; se a letra estiver errada, o caminho é
corrigi-la explicitamente, não reinterpretá-la pela redação de outro requisito.

**Por que é BLOQUEANTE e não IMPORTANTE:** o afrouxamento incide sobre o *critério de
conclusão da própria fase*, foi feito pelo executor durante a execução, e não deixou
rastro do que se perdeu. É o único tipo de achado que, aprovado, se propaga: a C.8
lê a C.7 como concluída, e o leitor futuro da §9 não terá como saber que "sem casos
vazios" já foi exigido.

**Correção — três caminhos, todos aceitáveis; o segundo é o que eu recomendaria:**

1. **Restaurar a cláusula na §9** e marcar a fase como não concluída até o 413 cair.
   Honesto e trivial, mas trava a C.7 num defeito que é da C.2/frontend.
2. **Migrar explicitamente**, com decision registrada e destino nomeado — por
   exemplo: "a cláusula *sem casos vazios* do AC-15 passa a ser verificada pela fase
   que corrigir o HTTP 413 (OQ19); até lá a C.7 fecha com 3 vazios conhecidos e
   nominados". É o mesmo rito que a OQ18 usou para o AC-18 → AC-19, e o que faltou
   aqui. **Exige decisão do owner**, não do executor.
3. **Corrigir o 413** e reexecutar — fecha o AC-15 pela letra, mas depende de fase
   nova ou de rework da C.2, e de um dia de cota limpo.

Em qualquer caminho, **o AC-15 no §3 e a linha da §9 têm de dizer a mesma coisa ao
final** — é o teste que a D.1 estabeleceu.

## 4. Achados IMPORTANTES

### C7-IMP-3 — o passo 4 manda registrar a periodicidade no README do harness, e ela não está lá

`SPEC §5:1036-1038` (passo 4 da fase):

> Dimensionar a agenda ao rate limit real do free tier. … se a quota não comportar
> execução diária, usar periodicidade maior **e registrar a decisão no README do
> harness**.

A medição desta tentativa é excelente e responde ao passo — mas mora no EXECUCAO §6
e na OQ20. O README do harness não a tem:

```text
$ grep -n "seman\|TPD\|100.000\|agenda" backend/evals/README.md
(nenhuma linha)
$ sed -n '138,144p' backend/evals/README.md
### Consumo de quota
O dataset saiu de 10 para 43 casos, dos quais 40 são executáveis pelo runner de
texto — cerca de **4× mais chamadas** por execução completa do que a camada
agendada media antes. …
```

A seção existe, foi escrita antes da medição e não foi atualizada por ela. Some-se
a isso o cabeçalho do próprio workflow, `.github/workflows/eval.yml:9-12`:

> Periodicidade semanal, não diária: com ~10 casos, mais os grupos de invariância,
> uma rodada diária no free tier tende a esbarrar na quota. **Ajustar junto de uma
> medição real de consumo, não por palpite.**

São 43 casos, não ~10; e a medição real agora existe. O comentário pede uma ação que
já foi feita, o que é a pior forma de comentário desatualizado.

**Correção sugerida:** acrescentar em `backend/evals/README.md`, na seção "Consumo de
quota", o quadro medido (TPD 100.000; 42.932 tokens e 57 chamadas por execução do
runner; invariância não medida; consumo do dia até o 429: 99.768) e a conclusão
("diária é impossível, semanal cabe; `--repeticoes 3` triplica e não cabe"); e
atualizar o cabeçalho do `eval.yml` para citar 43 casos e a medição de 2026-08-04 em
vez de pedi-la. Ambos são documentação — não tocam o comportamento do workflow.

## 5. Sugestões

1. **Dúvida 1 (recalibrar ou manter os limiares).** É decisão de owner e não a tomo
   por ele, mas registro a leitura: `MDAPE_MAXIMO = 25.0` e
   `FRACAO_MINIMA_DENTRO_DE_10PCT = 0.50` foram calibrados sobre 10 casos e hoje
   reprovam a linha de base de 43. Um gate permanentemente vermelho para de ser lido
   — e um gate que se ajusta ao resultado para de medir. O meio-termo que costuma
   funcionar é **separar as duas funções**: um limiar de regressão (bloqueante,
   ancorado na linha de base medida: MdAPE 33,33%, com folga) e uma meta de qualidade
   (não-bloqueante, publicada no relatório: 25%). Assim o vermelho volta a significar
   "piorou" e a meta continua visível.
2. **Dúvida 2 (composto com MdAPE 61,64% e 6% dentro de ±10%).** Concordo que não é
   achado desta fase — é o produto dela. Mas endosso o alerta: a D.3 não deveria
   citar número de eval no README sem citar **esse** também; um README de portfólio
   que mostra só o estrato bom é o tipo de coisa que um entrevistador encontra.
3. **Dúvida 3 (invariância).** Vale rodar sozinha, num dia de cota limpo, antes de a
   C.8 ser dada por fechada — `invariancia: null` na única linha completa da série
   enfraquece o AC-16.
4. **Dúvida 4 (virar regra explícita).** Concordo, e esta avaliação é o terceiro
   caso: o que falta não é permitir ou proibir a migração de cláusula, é exigir
   **rito** — destino nomeado, decision registrada, e nenhuma cláusula descartada em
   silêncio. O C7-BLQ-1 é exatamente o que acontece quando o rito não existe.
5. **`actionlint` no CI** segue pendente, anotado para a E.4. Sem objeção.

## 6. Comandos rodados + saídas reais

```text
$ git merge-base --is-ancestor 208d85d HEAD && echo "208d85d ANCESTRAL OK"
208d85d ANCESTRAL OK

# --- o que esta tentativa mudou de fato ---
$ git show 208d85d --stat
 .../artefatos/FASE-C.7-eval-ci-EXECUCAO.md    | 506 ++++++++---------
 .../artefatos/FASE-E.3-conta-demo-EXECUCAO.md | 232 ++++++++
$ git show 181fb5c --stat | grep -c "backend/evals/cassettes"
57                                     ← 56 cassettes + o diretório contado no total
$ ls backend/evals/cassettes/*.json | wc -l
71

# --- os números do relatório, conferidos no artefato versionado ---
$ python3 - <<'PY'
import json
r = json.loads(open('backend/evals/runs/history.jsonl').read().splitlines()[-1])
print(r['run_id'], r['dataset_n'], r['custo'], r['agregado']['mdape'],
      r['por_estrato']['simples']['mdape'], r['por_estrato']['composto']['mdape'],
      [f['id'] for f in r['falhas']], r['invariancia'])
PY
e1d39b03675b-0758d981c3c0 43
{'chamadas': 57, 'origem': 'provedor', 'tokens_in': 38833, 'tokens_out': 4099} 33.33
25.53 61.64 ['foto-coxinha-1-unidade','foto-ovo-frito-1-unidade','foto-banana-1-unidade'] None
   → 38833 + 4099 = 42.932 tokens. Bate com o EXECUCAO §6, linha a linha.

# --- o impedimento de plataforma, confirmado por mim ---
$ gh workflow list --repo gabriel-ngrs/CalorIA
CD — Deploy em Produção   active   268489066
CI                        active   251015895
Dependabot Updates        active   268489129
   → o `eval.yml` não aparece: o 404 do relatório é real
$ gh secret list --repo gabriel-ngrs/CalorIA
GROQ_API_KEY   2026-08-03T17:42:28Z          ← o secret existe, como o relatório diz

# --- camada rápida (NFR-2) e gates do projeto ---
$ docker compose -f docker-compose.dev.yml exec -T backend \
    pytest tests/unit/test_evals_snapshot.py tests/unit/test_evals_runner_foto.py \
           tests/unit/test_seed_demo.py -q
46 passed, 3 skipped in 0.19s          ← teto da NFR-2 é 60 s

$ docker compose -f docker-compose.dev.yml exec -T backend sh -c \
    "ruff check . && ruff format --check . && mypy app/ evals/"
All checks passed! / 149 files already formatted / Success: no issues found in 81 source files

$ docker compose -f docker-compose.dev.yml exec -T backend pytest tests/unit -q
496 passed, 3 skipped in 4.01s
$ docker compose -f docker-compose.dev.yml exec -T backend pytest tests/integration/ -q
145 passed, 5 warnings in 86.98s

$ grep -rlE "gsk_|Authorization|api[_-]?key" backend/evals/cassettes/
(vazio)
$ gitleaks detect --source . --config .gitleaks.toml --redact --no-banner --exit-code 1
496 commits scanned. no leaks found     >>> EXIT=0

# --- o BLOQUEANTE e o IMPORTANTE, medidos ---
$ git show 181fb5c -- .codeflow/specs/.../SPEC_002_*.md | grep -n "C.7\b" -A2
-- [ ] **C.7** — AC-15, NFR-2, NFR-3; execução agendada completa sem casos vazios.
++ [ ] **C.7** — AC-15, NFR-2, NFR-3; execução completa registrada. *(Executada …
$ sed -n '366,369p' .codeflow/specs/.../SPEC_002_*.md
- **AC-15** (FR-C6) … *E dado* a execução agendada, *então* a camada completa roda
  contra o provedor real e conclui sem casos vazios.
$ grep -n "sem casos vazios" .codeflow/specs/.../SPEC_002_*.md
366-369 (AC-15)     ← única ocorrência; não migrou para o AC-19 nem para a OQ20

$ grep -n "seman\|TPD\|agenda" backend/evals/README.md
(nenhuma linha)

$ git status --short
(vazio — árvore limpa ao fim da avaliação)
```

**Não rodei:** o `eval.yml` no GitHub (impossível: 404, e disparar workflow é ação
externa que não cabe a uma avaliação) nem uma segunda execução completa contra a
Groq (a cota do dia está esgotada, como o próprio relatório documenta, e queimá-la
prejudicaria a fase seguinte). Verifiquei a execução pelo artefato que ela deixou.

## 7. Itens da fase / DoD não atendidos

| Item (§5 / §9) | Estado |
|---|---|
| AC-15 — camada rápida sem rede, < 60 s | ✓ 26 testes, 0,19 s |
| AC-15 — prompt alterado sem regravar quebra o CI | ✓ verificado na t2, inalterado |
| AC-15 — camada completa conclui **sem casos vazios** | ✗ 3 vazios (413) — **C7-BLQ-1** |
| NFR-2 | ✓ |
| NFR-3 — nenhum caso vazio por `429` | ✓ zero 429 no runner |
| Passo 3 — workflow agendado que falha se limiar romper | ✓ `verificar` exercitado, exit 1 |
| Passo 4 — agenda dimensionada ao rate limit real | ✓ medido |
| Passo 4 — decisão registrada **no README do harness** | ✗ **C7-IMP-3** |
| Gate — "uma execução agendada completa registrada" | parcial: execução completa e registrada ✓, agendada no GitHub ✗ (migração para o AC-19 aceita) |
| Escopo travado — sem `continue-on-error`, sem eval por PR, cassette sem chave, limiar não afrouxado | ✓ todos |

## 8. Divergências entre o relatório e o código real

Nenhuma divergência de fato — os números do EXECUCAO batem com o `history.jsonl` até
a última casa, e os três impedimentos remedidos são verificáveis (`gh secret list`,
`gh workflow list`). As divergências são de **julgamento**, e são o achado:

1. **EXECUCAO §8, `[x]` "AC-15 / NFR-3"** — a evidência colada sustenta a NFR-3
   (zero 429), não o AC-15 ("sem casos vazios"). O item deveria ser `[✓]` para a
   NFR-3 e `[✗]`/`[—]` para essa cláusula do AC-15.
2. **EXECUCAO §9, "Nenhum gate afrouxado"** — nenhum *limiar* foi afrouxado, o que é
   verdade e é mérito. Mas o gate **da fase**, na §9 da spec, perdeu uma cláusula
   nesta tentativa. As duas afirmações convivem no relatório sem que a segunda seja
   dita.
3. **OQ20** descreve a evidência substantiva como "execução completa … **sem casos
   vazios por quota**". O qualificador "por quota" não existe no AC-15; ele aparece
   pela primeira vez aqui.

---

**Próximo passo:** REPROVADO não conclui a fase. **Atenção — teto do §2.11.4:** o
EXECUCAO traz `reprovacoes: 2`; este veredito fecha o **terceiro** não-APROVADO e a
fase entra em **estado terminal de escalação ao owner**. Não há rework automático.

O que o owner precisa decidir é exatamente o que o BLOQUEANTE nomeia: se a cláusula
"sem casos vazios" do AC-15 é (a) mantida, deixando a C.7 aberta até o 413 cair;
(b) migrada com decision para a fase que corrigir o 413; ou (c) satisfeita
corrigindo o 413 antes. É a mesma mesa em que estão a pergunta dos limiares e a de
"fase nova ou rework da C.2" — as três se resolvem juntas.

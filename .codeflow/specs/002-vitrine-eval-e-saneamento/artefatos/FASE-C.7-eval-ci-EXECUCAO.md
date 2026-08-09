---
spec: 002-vitrine-eval-e-saneamento
fase: C.7
slug_fase: eval-ci
status: rework
tentativa: 4
reprovacoes: 3
sha_inicial: 40e2941
sha_final: b838c86
range: 40e2941..b838c86
---

# FASE C.7 — Relatório de execução

## 1. Resumo do que foi feito

Rework da tentativa 3, **autorizado pelo owner no teto do §2.11.4** — a avaliação
anterior fechou o terceiro veredito não-APROVADO e a fase entrou no estado
terminal de escalação. A autorização está registrada em
`.codeflow/decisions/2026-08-08-quarta-tentativa-da-c7-autorizada-no-teto.md` e na
OQ21(b), porque gate duro não admite override conversacional.

Dois achados, nenhum deles de código de produção:

| Achado | O quê | Caminho |
|---|---|---|
| **C7-BLQ-1** | a cláusula "sem casos vazios" saiu do gate da fase sem destino, enquanto o AC-15 seguia exigindo-a | **caminho 2** do avaliador: migração explícita, com decision e destino nomeado |
| **C7-IMP-3** | a medição de quota do passo 4 não foi propagada ao README do harness nem ao cabeçalho do `eval.yml` | escrita nos dois lugares |

**Nada de código mudou nesta tentativa** — nem `evals/`, nem os testes, nem os
passos do `eval.yml`. O que mudou foi a coerência da spec e a documentação que o
passo 4 da fase pedia. A execução completa contra o provedor real, que é a
evidência substantiva da fase, é a da tentativa 3 e segue válida: o avaliador a
conferiu linha a linha contra o `history.jsonl` versionado e não achou divergência.

## 2. C7-BLQ-1 — o que eu aceito do achado, e o que fiz

**Aceito integralmente.** A tentativa 3 derrubou duas cláusulas da linha da C.7 na
§9 e só tratou uma. A de plataforma foi para o AC-19 com rito (OQ20) — o avaliador
endossou. A de "sem casos vazios" não foi para lugar nenhum, e o AC-15 continuava
exigindo-a. O relatório da t3 marcou o item `[x]` reinterpretando "casos vazios"
pela redação da **NFR-3** ("por `429`"), que é outro requisito com outro
qualificador. Isso é afrouxar o critério de conclusão da fase durante a execução
da fase, e é o defeito que a D.1 levou quatro tentativas para eliminar.

O avaliador ofereceu três caminhos. Segui o **2**, que é o recomendado:

**Destino nomeado — o bug 003.** Criei
`.codeflow/bugs/003-http-413-no-estrato-de-foto.md`, que é quem corrige o HTTP 413
da OQ19, com condição de fechamento explícita: *ao corrigir, a exceção sai do
AC-15*. O avaliador sugeriu "a fase que corrigir o 413"; ela não existe e não podia
ser criada aqui — o fix é em `config.py`/`ai_client.py` (escopo da C.2, concluída)
e no frontend, o **Track C está fechado em 8 fases** (ARTIFACTS_SPEC §2.8.6, regra
3) e criar fase é trabalho de `/create-spec`, não de execução. O registro de bugs é
o artefato vivo do projeto onde a cláusula não se perde.

**Exceção nominada, não tolerância genérica.** O AC-15 passa a admitir uma **lista
fechada de três `id`s** — `foto-coxinha-1-unidade`, `foto-ovo-frito-1-unidade`,
`foto-banana-1-unidade`. Qualquer caso vazio fora dessa lista, por qualquer motivo,
segue reprovando o AC. Não é a reinterpretação da t3 com outra roupa: a diferença é
que agora está na letra do AC, com destino, e não na prosa de um relatório.

**§3, §5 e §9 dizem a mesma coisa** — o teste que a D.1 estabeleceu. Inclui o
"Testes (AC-15)" e o "Critério de conclusão" do bloco da fase na §5, que a t3 não
tinha tocado e que ainda diziam "o workflow agendado conclui sem casos vazios",
contradizendo o que a OQ20 já havia migrado.

## 3. Arquivos CRIADOS / ALTERADOS

| Arquivo | Estado | O quê |
|---|---|---|
| `.codeflow/bugs/003-http-413-no-estrato-de-foto.md` | CRIADO | O destino nomeado da cláusula. Sintoma medido, camadas do defeito, condição de fechamento |
| `.codeflow/bugs/INDEX.md` | ALTERADO | Linha 003 + `proximo_numero: 004`, conforme a convenção de enumeração do próprio índice |
| `.codeflow/decisions/2026-08-08-clausula-sem-casos-vazios-migra-da-c7-para-o-bug-003.md` | CRIADO | O rito que faltou na t3 |
| `.codeflow/decisions/2026-08-08-quarta-tentativa-da-c7-autorizada-no-teto.md` | CRIADO | A autorização do owner no teto do §2.11.4 |
| `.codeflow/decisions/INDEX.md` | ALTERADO | Duas linhas + `atualizado` |
| `SPEC_002_…md` | ALTERADO | AC-15 (§3) + nota; "Testes" e "Critério de conclusão" da C.7 (§5); OQ21; retificação na OQ20; linha da C.7 (§9); `updated_at` e `related_bugs` |
| `backend/evals/README.md` | ALTERADO | **C7-IMP-3:** seção "Medição de 2026-08-04 — por que a agenda é semanal" |
| `.github/workflows/eval.yml` | ALTERADO | **C7-IMP-3:** cabeçalho (comentário) com a medição no lugar do pedido por ela |

**Não tocado:** `evals/runner.py`, `evals/report.py`, `evals/cassettes/`,
`history.jsonl`, os testes de snapshot, os passos do `eval.yml`, `ci.yml`,
`pyproject.toml`. Nenhum limiar foi recalibrado (§7).

## 4. Desvios do conjunto declarado de arquivos

Os "Arquivos alterados" da fase na §5 são `.github/workflows/ci.yml` e
`backend/pyproject.toml`; os novos, `evals/cassettes/`,
`tests/unit/test_evals_snapshot.py` e `.github/workflows/eval.yml`. Esta tentativa
tocou **fora** dessa lista, e declaro cada caso:

1. **`SPEC_002_…md`, `.codeflow/decisions/`, `.codeflow/bugs/`** — são o próprio
   remédio do BLOQUEANTE, que é um defeito de coerência de spec. Não há como
   corrigi-lo sem editar a spec. Precedente aceito na t3 (OQ20) e na D.1 (OQ18).
2. **`backend/evals/README.md`** — o **passo 4 da própria fase** manda "registrar
   a decisão no README do harness". Está no texto da fase mesmo não estando na
   lista de arquivos; é o achado C7-IMP-3.
3. **`.github/workflows/eval.yml`** — está na lista ("Arquivos novos"). A mudança é
   só de comentário de cabeçalho; nenhuma linha de comportamento do workflow mudou
   (§5.2 abaixo prova o YAML e o cron intactos).

Nenhum dos três amplia o escopo funcional da fase. As decisions registram as
divergências, como o self-review exige.

## 5. Comandos rodados + saídas reais

### 5.1 Gate estrutural da §5, antes e depois das edições na spec

```text
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
```

### 5.2 O `eval.yml` continua íntegro (só comentário mudou)

```text
$ python3 -c "import yaml; d=yaml.safe_load(open('.github/workflows/eval.yml')); \
    print('jobs:', list(d['jobs'].keys()), '| cron:', d[True]['schedule'])"
jobs: ['eval'] | cron: [{'cron': '0 6 * * 1'}]        ← inalterado

$ git diff 40e2941..HEAD --stat -- .github/workflows/eval.yml
 .github/workflows/eval.yml | 9 ++++++---     ← só o bloco de comentário 9-12
```

### 5.3 Coerência do AC-15 entre §3, §5 e §9 — o teste da D.1

```text
$ grep -n "casos vazios" SPEC_002_VITRINE_EVAL_E_SANEAMENTO.md
294:  sem abortar: nenhuma execução pode terminar com casos vazios por `429`.   ← NFR-3, intacta
369:  completa roda contra o provedor real e conclui sem casos vazios **além dos
373:  > **Nota (2026-08-08).** A cláusula "conclui sem casos vazios" **sem
1054:  conclui sem casos vazios além dos nominados no bug 003 (os três de foto, por
1720:- **OQ21 — A cláusula "sem casos vazios" saiu do gate da C.7 sem destino …
1783:      `workflow_dispatch` no GitHub, para a D.2 (OQ20); a de "sem casos vazios"

   §3 (369)  → "sem casos vazios além dos nominados no bug 003"
   §5 (1054) → "sem casos vazios além dos nominados no bug 003"
   §9 (1778) → "sem casos vazios além dos três de foto nominados no bug 003"
   → as três dizem a mesma coisa. A NFR-3 (294) segue com a redação dela ("por
     429"), que é outro requisito e não foi tocada.
```

### 5.4 Gates do projeto

```text
$ docker compose -f docker-compose.dev.yml exec -T backend sh -c \
    "ruff check . && ruff format --check . && mypy app/ evals/"
All checks passed!
149 files already formatted
Success: no issues found in 81 source files

$ docker compose -f docker-compose.dev.yml exec -T backend pytest tests/unit -q
496 passed, 3 skipped in 4.32s

$ docker compose -f docker-compose.dev.yml exec -T backend \
    pytest tests/unit/test_evals_snapshot.py -q
26 passed in 0.22s                     ← camada rápida, zero rede, teto de 60 s (NFR-2)

$ gitleaks detect --source . --config .gitleaks.toml --redact --no-banner --exit-code 1
500 commits scanned. no leaks found     >>> EXIT=0
```

**Frontend `[—]`:** nenhum arquivo de frontend no diff (o diff é markdown, mais um
comentário de YAML), então `npm run lint` / `npx tsc --noEmit` não têm o que provar
nesta tentativa. Rodaram verdes na t3 e nada os afeta aqui.

**Não rodei** uma nova execução completa contra a Groq. Não haveria o que medir:
nenhuma linha de código do pipeline ou do harness mudou, então o resultado seria o
mesmo da t3 — e queimar a cota diária prejudicaria a C.8 e a bateria de invariância
que ainda falta. A execução da t3 é a evidência da fase, e foi verificada de forma
independente contra `history.jsonl`.

## 6. Critérios de aceite da fase (com evidência)

- [x] **AC-15, camada rápida sem rede e < 60 s** — 26 testes em 0,22 s (§5.4).
- [x] **AC-15, prompt alterado sem regravar quebra o CI** —
      `test_prompt_alterado_sem_regravar_estoura`, verde; verificado pelo avaliador
      na t2 e novamente na t3.
- [x] **AC-15, a camada completa roda contra o provedor real e conclui sem casos
      vazios além dos nominados no bug 003** — 43 casos, 57 chamadas, 42.932
      tokens (t3, `history.jsonl` `run_id=e1d39b03675b-0758d981c3c0`). Os três
      vazios são **exatamente** os três `id`s da lista nominada; nenhum vazio fora
      dela. A exceção está na letra do AC desde este rework, com destino no bug
      003 e decision registrada — não é reinterpretação.
- [x] **NFR-2** — 0,22 s contra o teto de 60 s.
- [x] **NFR-3, nenhum caso vazio por `429`** — zero 429 no runner (t3, §5.2 do
      relatório anterior). O 429 que apareceu foi na bateria de invariância, depois
      do runner, e não produziu caso vazio no relatório.
- [x] **Passo 4, agenda dimensionada ao rate limit real** — TPD 100.000 medido.
- [x] **Passo 4, decisão registrada no README do harness** — **C7-IMP-3 corrigido**:
      `backend/evals/README.md`, seção "Medição de 2026-08-04 — por que a agenda é
      semanal", com o quadro e a conclusão. O cabeçalho do `eval.yml` deixou de
      pedir a medição que já existe.
- [x] **Escopo travado** — nenhum `continue-on-error` no `eval.yml`; eval completo
      fora do PR; nenhum cassette com credencial (gitleaks, 500 commits); **nenhum
      limiar recalibrado**.
- [—] **"Execução agendada registrada" no GitHub** — migrada para o **AC-19 (D.2)**
      pela OQ20, com argumento medido e aceite explícito do avaliador da t3.

## 7. O que eu deliberadamente não fiz

- **Não recalibrei os limiares.** `MDAPE_MAXIMO = 25.0` e
  `FRACAO_MINIMA_DENTRO_DE_10PCT = 0.50` seguem reprovando a linha de base medida
  (MdAPE 33,33%; 23% dentro de ±10%). É decisão de owner e está na mesa (§9); o
  avaliador endossou a recusa em ajustá-los, e ampliá-la para "agora eu ajusto"
  seria o oposto do que este rework corrige.
- **Não corrigi o HTTP 413.** É o caminho 3 do avaliador e exige tocar
  `config.py`/`ai_client.py` e o frontend — fora do escopo travado da fase. Está
  registrado no bug 003, que é a forma de não perdê-lo.
- **Não rodei a bateria de invariância.** Precisa de um dia de cota limpa; segue
  como a dúvida 3, agora endereçada à C.8.
- **Não criei fase nova para o 413.** Track C fechado em 8 fases, e editar o plano
  de fases da spec que estou executando é exatamente o auto-afrouxamento que o
  BLOQUEANTE condena.

## 8. O que mudou nesta tentativa

| Achado da avaliação t3 | Estado |
|---|---|
| **C7-BLQ-1** — cláusula "sem casos vazios" sem destino | **Corrigido pelo caminho 2.** Bug 003 criado como destino nomeado; AC-15 com exceção nominada de três `id`s; §3, §5 e §9 alinhados; OQ21 e duas decisions registradas |
| **C7-IMP-3** — medição não propagada ao README do harness | **Corrigido.** Seção nova no `backend/evals/README.md` com o quadro medido; cabeçalho do `eval.yml` atualizado (43 casos, medição de 2026-08-04) |
| §8.1 — `[x]` de "AC-15 / NFR-3" sustentado por evidência de NFR-3 | **Corrigido.** Os dois viraram itens separados no §6, cada um com a evidência que lhe cabe |
| §8.2 — "nenhum gate afrouxado" convivia com o gate da fase perdendo cláusula | **Corrigido.** O §7 declara o que não foi tocado; o §2 declara o que a t3 afrouxou e como foi reparado |
| §8.3 — "por quota" apareceu pela primeira vez na OQ20, sem base no AC-15 | **Corrigido.** Retificação registrada na própria OQ20, apontando a OQ21 como o que dá base à redação |
| Sugestão 1 — separar limiar de regressão de meta de qualidade | **Registrada, não aplicada.** Decisão de owner; a leitura do avaliador está preservada na decision do teto |
| Sugestão 2 — D.3 não citar só o estrato bom | **Registrada** no bug 003 e na decision, para a D.3 herdar |
| Sugestão 3 — rodar invariância antes de fechar a C.8 | **Repassada** à C.8; não cabe nesta fase |
| Sugestão 4 — virar regra explícita do framework | **Reforçada** na seção final da decision da migração. É a terceira ocorrência (A.1, D.1, C.7); segue sendo evolução de processo, não trabalho de fase |
| Sugestão 5 — `actionlint` no CI | **Não aplicada**, anotada para a E.4 |

## 9. Itens em aberto / dúvidas para o avaliador

1. **Os limiares do gate** seguem sem decisão. MdAPE 33,33% × teto 25%; 23% × piso
   50%. A leitura do avaliador (separar limiar de regressão de meta de qualidade)
   está registrada na decision do teto. Não a apliquei: mexer em limiar num rework
   cujo achado é justamente "não afrouxe critério durante a execução" seria
   contraditório.
2. **O bug 003 é destino suficiente?** É a pergunta que mais quero ver contestada.
   Um registro de bug tem menos força de gate que um AC de fase — mas nenhuma fase
   desta spec pode fechar a cláusula, e o Track C está no limite de 8. Se o
   avaliador julgar que o destino precisa ser um AC, ele terá de ser de uma spec
   nova, e isso é `/create-spec`.
3. **O estrato `composto`** (MdAPE 61,64%, 6% dentro de ±10%) segue sem dono. É o
   produto da fase, não defeito dela, mas a D.3 esbarra nele.
4. **Quatro tentativas.** A autorização do owner é explícita quanto a não haver
   quinta implícita. Se algo aqui não fechar, a fase volta à mesa dele.

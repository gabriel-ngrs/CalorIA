---
spec: 002-vitrine-eval-e-saneamento
fase: C.4
slug_fase: dataset-ground-truth
status: executado
tentativa: 1
reprovacoes: 0
sha_inicial: c36a22bf3d32b53c06383ed1bb7db214ad9bbfe7
sha_final: 4bf2aaababd8c1e6403a0ecedda67a50f10afd33
range: c36a22bf3d32b53c06383ed1bb7db214ad9bbfe7..4bf2aaababd8c1e6403a0ecedda67a50f10afd33
---

# FASE C.4 — Relatório de execução

## 1. Resumo do que foi feito

O dataset de eval saiu de **10 casos-semente não conferidos** para **43 casos com
`verificada: true`**, distribuídos nos três estratos (23 `simples`, 17 `composto`,
3 `foto`). Cada número foi extraído da linha real das publicações — TACO 4ª edição
para a composição, *Tabela de Medidas Referidas* do IBGE (POF 2008-2009) para a
conversão de medida caseira em gramas — e cada caso carrega em `notas` o alimento,
a **página** de cada publicação e a conta de gramas, para que um terceiro audite
sem confiar no projeto. As limitações da fonte foram escritas no README do harness,
inclusive as que enfraquecem a métrica. `sha` do dataset:
`0758d981c3c0e6ff343f0753d160ae559db87da3b5ca4eb3eb0c3d566870983c`.

O método deliberado foi **não transcrever de memória**: os dois PDFs foram baixados
das fontes oficiais, o texto foi extraído com `pdfplumber` e um gerador conferiu
cada valor contra a linha publicada, abortando em divergência (incluindo um
cross-check de Atwater `4P + 9L + 4C` contra o kcal publicado, que pega
desalinhamento de coluna). Nenhum valor veio de estimativa de modelo.

## 2. Arquivos CRIADOS

| Arquivo | Propósito |
|---------|-----------|
| `backend/evals/dataset/imagens/coxinha-1-unidade.jpg` | estrato `foto` — 1 coxinha, Wikimedia Commons, domínio público |
| `backend/evals/dataset/imagens/ovo-frito-1-unidade.jpg` | estrato `foto` — 1 ovo frito, Wikimedia Commons, CC BY 4.0 |
| `backend/evals/dataset/imagens/banana-1-unidade.jpg` | estrato `foto` — 1 banana, Wikimedia Commons, CC BY-SA 4.0 |
| `.codeflow/decisions/2026-08-03-dataset-c4-fontes-e-arquivos-alem-do-declarado.md` | registro das três extensões de escopo desta fase |

## 3. Arquivos ALTERADOS

| Arquivo | O que mudou |
|---------|-------------|
| `backend/evals/dataset/casos.jsonl` | 10 casos-semente → 43 casos conferidos, com procedência por caso; cabeçalho reescrito |
| `backend/evals/README.md` | "Estado do dataset" reescrito: as duas (três) fontes, tabela de distribuição, como auditar um caso, 6 limitações declaradas, atribuição das imagens, impacto em quota; `Layout` atualizado |
| `backend/tests/unit/test_evals_schema.py` | asserção "nenhum caso conferido" → "todo caso conferido"; teste de estrato vazio passa a usar dataset sintético; teste novo exige os três estratos populados (FR-C3) |
| `backend/tests/unit/test_evals_metrics.py` | relatório exige `n > 0` nos três estratos e `casos_nao_verificados == 0`; teste de renderização de estrato vazio filtra o estrato `foto` |
| `.codeflow/specs/.../SPEC_002_...md` | OQ17 registrada em §8; `updated_at`; nota na linha C.4 da §9 |
| `.codeflow/decisions/INDEX.md` | linha da decision nova |

## 4. Confirmação do REUSO e decisões de design

**Reuso confirmado.** O `CasoEval` e o `carregar_casos()` da C.3 foram usados como
estão — nenhuma linha de `evals/schema.py` foi tocada, e o dataset novo valida
contra o contrato original, incluindo as duas regras que ele impõe (fonte não
circular e `fonte_url` localizável). O `runner.py` e o `metrics.py` da C.5 não foram
tocados: o runner já ignora o estrato `foto` por conta própria, então o estrato
novo não quebra a execução de texto. O `grupo_invariancia: pizza-calabresa`, que a
C.6 usa, foi preservado no caso de pizza.

**Decisões e desvios — três extensões do escopo declarado, todas registradas na
decision e na OQ17:**

1. **Terceira fonte, com precedência fixa.** A OQ2 declarava TACO (composição) +
   POF (medidas). A TACO **não tem pizza** — e a reprodução do bug 001 depende dela
   — e sua linha de leite integral (nº 458, p. 57) vem sem valores (`*`). Nesses
   dois casos a composição vem das *Tabelas de Composição Nutricional* da mesma POF
   2008-2009, publicação irmã da tabela de medidas já adotada. Regra declarada:
   TACO onde a TACO cobre; POF só onde não cobre. Ela importa porque as duas
   discordam onde ambas cobrem (feijoada: 117 vs 181,59 kcal/100 g).
2. **Três imagens versionadas**, fora dos "Arquivos alterados" da fase. Sem elas o
   estrato `foto` nasceria vazio e a B.5 — reapontada em 2026-08-03 para depender
   da C.4 exatamente por causa do dataset de foto — seguiria bloqueada. Licença
   conferida pela API do Commons antes de baixar, atribuição no README e em
   `notas`, nenhuma pessoa identificável.
3. **Quatro asserções de teste** que travavam o estado de semente ("nenhum caso
   conferido", "estrato `foto` vazio"). São gates corretos da C.3/C.5 que esta fase
   supera; sem atualizá-los a suíte fica vermelha por construção. Nenhum teste foi
   removido, e os dois que provavam a renderização de estrato vazio seguem
   provando — sobre dataset sintético.

**Um caso da semente foi removido, não corrigido:** `composto-lasanha-carne-100g`
(168 kcal/100 g). A TACO só traz "Lasanha, massa fresca, cozida" (a massa, não o
prato) e a POF traz "Lasanha pronta light", outro produto. Preferiu-se perder o
caso a manter número sem fonte auditável — o escopo travado da fase proíbe
"incluir caso cuja fonte não seja verificável por terceiro".

**Os outros 9 casos-semente sobreviveram, conferidos e reancorados em medida
caseira**, como a OQ2 mandava. Três tinham número errado: a semente dizia
strogonoff 168 kcal/100 g (a publicação diz **173**), pizza 270 (a POF diz
**284,72**) e os macros da feijoada divergiam da TACO em gordura (5,6 vs **6,5**),
carboidrato (8,9 vs **11,6**) e fibra (4,5 vs **5,1**). A banana nanica virou
banana prata, que é a variedade da medida referida da POF.

**Nenhum desvio de rules:** identificadores e prosa em pt-BR, seguindo a exceção
declarada no princípio 8 da spec para `backend/evals/`. Nenhuma migration. Nenhum
limiar da decision de 2026-07-26 tocado.

## 5. Comandos rodados + saídas reais

```text
# lint — backend/ (ruff check + ruff format --check)
$ .venv/bin/ruff check .
All checks passed!
$ .venv/bin/ruff format --check .
144 files already formatted

# type-check — mypy strict sobre app/ e evals/
$ .venv/bin/mypy app/ evals/
Success: no issues found in 81 source files

# testes unitários (make test-unit; docker exec substituído por venv local)
$ .venv/bin/python -m pytest tests/unit -q
476 passed in 4.27s

# testes de integração (make test-integration) — portas do compose dev: 5442/6389
$ TEST_DATABASE_URL=postgresql+asyncpg://caloria:caloria@localhost:5442/caloria_test \
  REDIS_URL=redis://localhost:6389/0 .venv/bin/python -m pytest tests/integration -q
145 passed, 5 warnings in 107.49s

# suíte completa com o gate de cobertura da B.4
$ ... .venv/bin/python -m pytest --cov=app --cov-report=term -q
TOTAL                                      3244    846    74%
Required test coverage of 72.0% reached. Total coverage: 73.92%
FAILED tests/smoke_test.py::test_ai_client - groq.APIConnectionError: Connect...
1 failed, 623 passed, 1 skipped

# validação do dataset pelo contrato da C.3
$ .venv/bin/python -c "from evals.schema import *; c=carregar_casos(); ..."
n = 43
distribuicao: {'simples': 23, 'composto': 17, 'foto': 3}
sha: 0758d981c3c0e6ff343f0753d160ae559db87da3b5ca4eb3eb0c3d566870983c
nao verificados: []
casos executáveis pelo runner de texto: 40

# gate de segredo — pre-commit rodou nos dois commits
Detect hardcoded secrets.................................................Passed

# grep de PII/segredo no diff da fase (esperado: 0)
$ git diff c36a22b..HEAD | grep -icE "gsk_|password|senha *=|@gmail|@hotmail"
0

# frontend (npm run lint / tsc / jest) — [—] não rodado
#   Justificativa: a fase não toca nenhum arquivo de `frontend/`. Fora do escopo.
# segurança (pip-audit/npm audit) — [—] o manifest declara que não há gate configurado.
```

**A única falha é `tests/smoke_test.py::test_ai_client`**, que é a sonda de
ambiente da OQ9: ela fala com a API real da Groq e falhou aqui com
`APIConnectionError` (rede do ambiente local). Não tem relação com esta fase —
C.4 não toca código de aplicação — e o comportamento é o já registrado na decision
`2026-08-02-smoke-test-como-sonda-de-ambiente.md`. `make test-unit` e
`make test-integration`, que são os gates da §5, estão verdes.

## 6. Critérios de aceite da fase (com evidência)

- [x] **AC-12** (FR-C3) — *todo caso tem `id`, `estrato`, `descricao`,
      `referencia_kcal`, `fonte_referencia` e `fonte_url`, e nenhum tem referência
      derivada da tabela de porções do projeto*. Evidência: `carregar_casos()`
      valida as 43 linhas contra `CasoEval` (o schema recusa `fonte_referencia`
      circular e `fonte_url` não localizável) e o teste
      `test_todo_caso_semente_declara_procedencia` roda sobre o dataset real. As
      duas fontes usadas são publicações do NEPA/UNICAMP e do IBGE — nenhuma
      derivada do projeto.
- [x] **Dataset completo validando** — `n = 43`, zero casos inválidos, zero `id`
      duplicado, `casos_nao_verificados == 0` no relatório do runner.
- [x] **Distribuição por estrato registrada** — `{'simples': 23, 'composto': 17,
      'foto': 3}`; 40 casos executáveis pelo runner de texto (o estrato `foto` é
      da B.5).
- [x] **Nenhuma referência derivada da tabela de porções** — a conversão de medida
      vem da POF; o schema barra a alternativa e o teste
      `test_fonte_que_deriva_da_tabela_de_porcoes_reprova` continua verde.
- [x] **OQ2 resolvida e registrada em §8** — já estava (2026-08-02); esta fase
      acrescentou a OQ17, que registra a fonte complementar e as extensões.
- [x] **Limitações documentadas** — seis, nomeadas no README do harness:
      referência populacional; porção padrão ≠ porção servida; base de massa de
      fruta com casca; discordância entre as fontes onde ambas cobrem; fragilidade
      e tamanho do estrato `foto`; caso perdido por falta de fonte.
- [x] **`data_de_adicao` em cada caso** — `2026-08-03` nos 43.
- [x] **Sem PII e sem imagem de pessoa identificável** — as três fotos mostram
      comida; `grep` de PII no diff retorna 0.

## 7. Definition of Done da fase

- [x] Testes da fase verdes (476 unitários, 145 de integração)
- [x] Comandos de validação do projeto limpos nos arquivos tocados (frontend e
      segurança `[—]` justificados acima)
- [x] Escopo travado respeitado: nenhum valor inventado, nenhuma saída de LLM como
      ground truth, nenhum caso sem fonte verificável, nenhuma PII no estrato de
      foto. As três extensões de arquivo/fonte estão declaradas na OQ17 e na
      decision — não são violações silenciosas.
- [x] Nenhum segredo/PII em log/DTO/exceção
- [x] Commits em pt-BR (Conventional Commits), sem menção a autor ou agente

## 8. (Em rework) O que mudou nesta tentativa

Não se aplica — primeira execução da fase.

## 9. Itens em aberto / dúvidas para o avaliador

1. **A fonte complementar é aceitável?** A OQ2 nomeava duas publicações; usei uma
   terceira (do mesmo instituto da segunda) em 2 dos 43 casos, com precedência
   declarada. A alternativa era deixar pizza — o item que ancora a reprodução do
   bug 001 — fora do dataset. Se o avaliador entender que isso extrapola a OQ2, os
   dois casos saem e o `sha` do dataset muda.
2. **Quota da camada agendada.** O runner de texto passou de 10 para 40 casos, ~4×
   mais chamadas por execução completa. Isso pressiona diretamente o risco R5 e o
   dimensionamento da agenda decidido na C.7 — que já estava com ressalvas. Não
   ajustei `eval.yml` porque é arquivo declarado da C.7, não desta fase.
3. **Cassettes.** Os 14 cassettes gravados na C.7 são indexados pelo `sha` do
   payload, então os casos novos não têm gravação: `python -m evals.runner
   --cassettes` levanta `CassetteAusenteError` até a próxima execução com
   `EVAL_RECORD_CASSETTES=1`. É o comportamento documentado do harness (README,
   "O que a execução em replay mede"), mas alguém pode ler como regressão.
4. **Nenhum caso ficou sem `referencia_macros`.** A semente da C.3 mantinha um caso
   sem macros de propósito, para exercitar o caminho "só kcal" do runner; ele era
   justamente o de lasanha, removido por falta de fonte. Todas as fontes trazem
   macros, e fabricar uma omissão para cobrir o caminho seria inventar. Se o
   avaliador considerar essa cobertura necessária, o lugar natural é um teste
   unitário do runner, não o dataset.
5. **Reprodutibilidade da extração.** O gerador que leu os PDFs e conferiu cada
   valor rodou no scratchpad da sessão e **não foi versionado** — os arquivos
   declarados da fase são o dataset e o README. O que permite auditar sem ele é o
   campo `notas`: alimento, número na TACO, página e gramas. Se o avaliador
   preferir o script versionado (algo como `backend/evals/dataset/gerar.py`), é
   uma adição pequena, mas amplia o escopo de arquivos da fase.
6. **`simples-alface-4-folhas` tem 4,4 kcal de referência.** É o caso mais extremo
   de kcal baixo do conjunto e vai dominar qualquer métrica percentual do estrato
   `simples` — o que é exatamente o efeito que a §4 da spec usa para justificar
   MdAPE em vez de MAPE. Mantive de propósito; se o avaliador achar que é ruído em
   vez de sinal, é remoção de uma linha.

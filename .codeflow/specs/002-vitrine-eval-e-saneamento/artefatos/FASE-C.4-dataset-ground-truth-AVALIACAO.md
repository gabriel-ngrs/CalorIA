---
spec: 002-vitrine-eval-e-saneamento
fase: C.4
slug_fase: dataset-ground-truth
tentativa: 1
veredito: APROVADO
score: 9.9
threshold: 8.5
range_avaliado: c36a22bf3d32b53c06383ed1bb7db214ad9bbfe7..4bf2aaababd8c1e6403a0ecedda67a50f10afd33
---

# FASE C.4 — Avaliação independente

## 1. Veredito e score

**Veredito:** APROVADO · **Score:** 9.9 / threshold 8.5

Esta fase tem um escopo travado cuja violação é BLOQUEANTE por definição — *"não
inventar valores de referência"*, *"não usar a saída de um LLM como ground truth"* — e
o relatório declara que um script conferiu tudo contra as publicações, mas **esse
script não foi versionado**. Ou seja: a alegação central da fase não é reproduzível
pelo caminho que a produziu. Então não acreditei nela. Baixei as duas publicações das
fontes oficiais e conferi eu mesmo, caso a caso.

**Nenhum valor foi inventado. Conferi 40 dos 43 casos automaticamente, pelo número do
alimento, contra o PDF real da TACO 4ª edição: zero divergências.**

```text
casos com citacao TACO conferida contra o PDF real: 38
divergentes: 0 | sem numero TACO citado: 2
  (3 falsos negativos do meu regex, conferidos à mão logo abaixo)
```

Amostra do que "zero divergências" quer dizer — a linha da publicação à esquerda, o que
o dataset alega à direita:

```text
TACO n3  : 3 Arroz, tipo 1, cozido 69,1 128 537 2,5 0,2 NA 28,1 1,6     ← alega 128
TACO n410: 410 Frango, peito, sem pele, grelhado 63,8 159 666 32,0 2,5  ← alega 159 / 32,0 / 2,5
TACO n488: 488 Ovo, de galinha, inteiro, cozido/10minutos 75,8 146 610 13,3 9,5  ← alega 146
TACO n561: 561 Feijão, carioca, cozido 80,4 76 320 4,8 0,5 NA 13,6 8,5  ← alega 76 / 4,8 / 13,6 / 0,5 / 8,5
TACO n537: 537 Estrogonofe de carne 70,1 173 724 15,0 10,8 66 3,0       ← alega 173
TACO n540: 540 Feijoada 71,8 117 489 8,7 6,5 22 11,6 5,1                ← alega 117 / 6,5 / 11,6 / 5,1
```

O número do alimento, o nome e a composição batem **os três**. E as três correções que
o relatório diz ter feito nas sementes da C.3 estão certas: o estrogonofe é 173 e não
168, e a feijoada tem gordura 6,5 / carboidrato 11,6 / fibra 5,1, não 5,6 / 8,9 / 4,5.

**As medidas caseiras também conferem, na publicação do IBGE.** Baixei
`liv50000.pdf` e confirmei que é a *Tabela de Medidas Referidas para os Alimentos
Consumidos no Brasil* (POF 2008-2009, IBGE, 2011), exatamente como citada:

```text
Arroz cozido - colher de arroz cheia .................. 45 g   ← alega 45 g x 3
Feijão cozido - concha média cheia ................... 140 g   ← alega 140 g
Feijão cozido - colher de arroz cheia ................. 35 g   ← alega 35 g x 2
Ovo de galinha cozido - unidade média ................. 45 g   ← alega 45 g x 2
Ovo de galinha frito - unidade média .................. 50 g   ← alega 50 g
Coxinha de galinha - unidade média .................... 50 g   ← alega 50 g
Banana-prata - unidade ................................ 75 g   ← alega 75 g
Frango frito - filé médio ............................ 100 g   ← alega 100 g
```

**E a terceira fonte — a extensão de escopo que o executor pergunta se é aceitável — é
necessária, não conveniente.** Conferi as duas justificativas da decision, e as duas
são verdadeiras na letra:

```text
$ grep -i "pizza" taco.txt
NENHUMA OCORRENCIA                          ← a TACO realmente não cobre pizza

TACO n458: 458 Leite, de vaca, integral * * * * * 10 * NA 0,8 123 10
                                          ↑ a linha existe e vem sem valores
```

E os dois números tirados da publicação irmã batem também:

```text
POF Comp.: 7900101 Leite de vaca integral 99 Não se aplica 60,03 ...  ← alega 60,03
POF Comp.: 8500914 Pizzacalabreza 99 Não se aplica 284,72 ...          ← alega 284,72
POF Med. : 8500914 Pizza calabresa ... 32 Fatia ... 90 ...             ← alega 90 g x 2
```

Repare no cuidado: existe `8500903 Pizza` genérica com fatia de 100 g e
`8500915 Pizza muçarela` com 100 g. O executor foi buscar o código **da calabresa**,
cuja fatia média é 90 g, e usou o mesmo código nas duas publicações. Isso não é o tipo
de coincidência que sai de estimativa.

**Resposta à pergunta 1 do relatório: sim, a fonte complementar é aceitável.** O escopo
travado proíbe valor inventado, saída de LLM e fonte não auditável por terceiro — uma
publicação oficial do IBGE, do mesmo instituto e da mesma pesquisa que a OQ2 já
adotara, não é nenhuma das três. É *mais* auditável que a alternativa, que era deixar
pizza de fora e com ela a âncora da reprodução do bug 001 que a C.6 usa. A precedência
declarada (TACO onde a TACO cobre) resolve a ambiguidade que a limitação 4 do README
mede: feijoada é 117 na TACO e 181,59 na POF — conferi as duas linhas.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 5 | AC-12 verificado por execução: `n=43`, zero `id` duplicado, zero caso não verificado, todos com `data_de_adicao`, schema recusando fonte circular. Os quatro itens do escopo travado respeitados — e os dois primeiros **provados** por conferência independente contra as publicações (§1), não aceitos por declaração. |
| 2 | Arquitetura e direção de dependências | 3 | 5 | Nenhuma linha de `evals/schema.py`, `runner.py` ou `metrics.py` tocada — a fase é dado, não código. O estrato `foto` não quebra o runner de texto, que já o ignorava por conta própria. `grupo_invariancia: pizza-calabresa` preservado para a C.6. |
| 3 | Segurança / LGPD / PII | 3 | 5 | As três imagens têm **zero tags EXIF** (nenhum GPS, nenhum serial de câmera) — conferi com PIL, não confiei no relatório. Nenhuma pessoa identificável: abri as três. Licenças conferidas por mim na API do Commons e batem com o README (domínio público/Tom B, CC BY 4.0/Mtvdanilo, CC BY-SA 4.0/HaJunkiyada). |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | `CasoEval` e `carregar_casos()` da C.3 usados como estão; o dataset novo valida contra o contrato original sem que ele mudasse. Nenhuma fixture, nenhum helper duplicado. |
| 5 | Padrões de domínio/aplicação | 2 | 5 | Formato de `notas` uniforme nos 43 casos (alimento, número, página, conta de gramas) — é o que tornou a auditoria de 40 casos possível em minutos. pt-BR conforme o princípio 8. |
| 6 | Local e nomes dos arquivos | 2 | 4.5 | Tudo nos caminhos certos, mas `dataset/imagens/` e os dois arquivos de teste estão **fora** dos "Arquivos alterados" declarados na §5. As três extensões são legítimas, necessárias e registradas em decision + OQ17 — o que satisfaz o DoD global —, mas a constitution universal manda *parar e reportar* ao sair do escopo declarado, e aqui se seguiu e reportou. Meia nota. |
| 7 | Qualidade de código | 2 | 5 | `ruff check .` + `ruff format --check .` + `mypy app/ evals/` limpos. As mudanças de teste **fortalecem**: `all(not c.verificada)` → `all(c.verificada)`, `casos_nao_verificados == len(casos)` → `== 0`, `foto n == 0` → todos os estratos `n > 0`, mais um teste novo exigindo os três estratos populados. |
| 8 | Testes e cobertura | 2 | 5 | 476 unitários + 145 de integração verdes na minha execução. A propriedade "estrato vazio aparece como zero" não foi perdida ao virar o dataset: migrou para dado sintético e continua provada. Nenhum teste removido. |
| 9 | Migration safety | 2 | [—] | Nenhuma migration criada ou alterada (NFR-7). Dimensão excluída do cálculo. |

**Score:** (5·3 + 5·3 + 5·3 + 5·3 + 5·2 + 4,5·2 + 5·2 + 5·2) / 20 = 99/20 = 4,95 → **9,9**

## 3. Achados BLOQUEANTES

Nenhum. Os dois candidatos naturais — valor inventado e ground truth de LLM — foram
testados diretamente contra as publicações e não se sustentam: 40 citações conferidas,
zero divergências.

## 4. Achados IMPORTANTES

Nenhum.

Registro o que **considerei** e por que não classifiquei como IMPORTANTE, para que a
decisão fique auditável:

**O caminho de replay ficou quebrado para 33 dos 40 casos de texto.** Confirmei
rodando:

```text
$ python -m evals.runner --cassettes
composto-pizza-calabresa-2-fatias: CassetteAusenteError: Sem cassette para o
payload bcf5078d2548a8cc. ... Regrave com EVAL_RECORD_CASSETTES=1
(+32 casos)
```

É consequência inerente de acrescentar casos — o cassette é indexado pelo `sha` do
payload — e não é regressão de código. Pesou contra classificar como IMPORTANTE:
(a) **a camada rápida do CI não é afetada**, porque ela roda `test_evals_snapshot.py`
e irmãos, não o runner — os 140 testes de eval passam; (b) o erro **instrui a
correção** em vez de só falhar; (c) regravar é escrever em `evals/cassettes/`, arquivo
declarado da **C.7**, e custaria ~39 mil tokens da quota diária que a C.6 mediu como
o recurso escasso desta spec — o executor teria de escolher entre violar escopo e
consumir a quota da fase vizinha, e escolheu declarar. Vai como sugestão 1, endereçada
à C.7.

## 5. Sugestões

1. **Regravar os cassettes na próxima execução com `EVAL_RECORD_CASSETTES=1`** — é
   trabalho da C.7, e a execução agendada do `eval.yml` já faz isso sozinha. Até lá,
   `--cassettes` não produz relatório completo. Vale citar isso no rework da C.7 para
   que não seja lido como regressão por quem esbarrar.
2. **Dimensionar a agenda da C.7 com o número novo.** O runner de texto foi de 10 para
   40 casos, ~4× mais chamadas. Cruzando com o que a C.6 mediu (10 casos = 9.707
   tokens; teto TPD = 100.000), uma execução completa passa a custar ~39 mil tokens —
   ainda cabe no dia, mas com muito menos folga, e a bateria de invariância disputa a
   mesma quota. Foi certo não mexer no `eval.yml` aqui; é decisão da C.7.
3. **Versionar o gerador que leu os PDFs** (pergunta 5 do relatório). Minha posição:
   **desejável, não necessário** — e digo isso tendo sido o teste dessa afirmação. Não
   tive o script e ainda assim auditei 40 casos em minutos, porque o campo `notas`
   carrega alimento, número e página. O caminho de auditoria que a fase projetou
   **funciona**, e é o que importa. Versionar o script daria reprodutibilidade
   mecânica em cima disso; se entrar, `backend/evals/dataset/gerar.py` é o lugar.
4. **A licença das imagens conflita com o LICENSE MIT da D.1.** `banana-1-unidade.jpg`
   é CC BY-SA 4.0 e `ovo-frito-1-unidade.jpg` é CC BY 4.0 — a atribuição está no
   README, o que cumpre as duas licenças, mas um `LICENSE` MIT na raiz declara MIT
   sobre a árvore inteira, o que passa a ser impreciso. É item da D.1 (AC-18), não
   desta fase: basta uma seção "conteúdo de terceiros" no LICENSE ou no README raiz
   apontando para a tabela de atribuição. Vale registrar antes que a D.1 feche.
5. **`simples-frango-peito-grelhado-1-file`** usa os 100 g da linha da POF cujo rótulo
   é *"Frango frito - filé médio"*, enquanto o caso é grelhado. A grama está certa (é a
   medida de filé, contra os 180 g de "peito médio"), mas o rótulo de origem diverge da
   preparação; uma frase em `notas` fecharia a única citação do conjunto onde a leitura
   exige inferência.
6. **Perguntas 4 e 6 do relatório — concordo com as duas escolhas.** Cobrir o caminho
   "só kcal" do runner é trabalho de teste unitário, não de dataset: fabricar uma
   omissão de macros seria inventar. E `simples-alface-4-folhas` (4,4 kcal) deve
   **ficar** — é precisamente o caso que a §4 da spec usa para justificar MdAPE em vez
   de MAPE, e remover o caso que prova o argumento para deixar a métrica bonita seria o
   erro que o escopo travado da C.5 já proíbe.

## 6. Comandos rodados + saídas reais

Rodados por mim, na ponta da branch `dev`. Árvore limpa antes e depois; os PDFs foram
baixados para o scratchpad, fora do repositório.

```text
$ git merge-base --is-ancestor 4bf2aaababd8c1e6403a0ecedda67a50f10afd33 HEAD
c36a22bf...: ANCESTRAL   |   4bf2aaab...: ANCESTRAL
$ git status --porcelain
(vazio)

$ bash ~/.codeflow/framework/core/scripts/run-structural.sh .../SPEC_002_...md
✓ §5 estruturalmente válida
EXIT=0

$ docker compose -f docker-compose.dev.yml exec -T backend \
    sh -c "ruff check . && ruff format --check . && mypy app/ evals/"
All checks passed!
147 files already formatted
Success: no issues found in 81 source files

$ docker compose -f docker-compose.dev.yml exec -T backend sh -c "pytest tests/unit -q"
476 passed in 4.68s

$ docker compose -f docker-compose.dev.yml exec -T backend sh -c "pytest tests/integration -q"
145 passed, 5 warnings in 80.20s (0:01:20)

$ docker compose -f docker-compose.dev.yml exec -T backend \
    sh -c "pytest --cov=app --cov-report=term --cov-fail-under=72 -q"
TOTAL                                      3244    848    74%
Required test coverage of 72% reached. Total coverage: 73.86%
624 passed, 1 skipped, 5 warnings in 114.44s (0:01:54)
# 624 passed aqui contra "1 failed, 623 passed" no relatório: a falha era
# tests/smoke_test.py::test_ai_client por APIConnectionError. Aqui a rede
# respondeu e o teste passou — confirma o diagnóstico de sonda de ambiente.

# AC-12, executado contra o schema da C.3
$ ... python -c "from evals.schema import *; ..."
n = 43
distribuicao: {'simples': 23, 'composto': 17, 'foto': 3}
nao verificados: []
sem data_de_adicao: []
ids duplicados: 0
sha: 0758d981c3c0e6ff343f0753d160ae559db87da3b5ca4eb3eb0c3d566870983c
# o `sha` bate com o declarado na §1 do relatório

# ---- CONFERÊNCIA INDEPENDENTE DO GROUND TRUTH ----
$ curl -L -o pof_medidas.pdf https://biblioteca.ibge.gov.br/visualizacao/livros/liv50000.pdf
HTTP=200 bytes=3032908     → 545 páginas
titulo: "Pesquisa de Orçamentos Familiares 2008-2009 — Tabela de Medidas
         Referidas para os Alimentos Consumidos no Brasil" (IBGE, 2011)

$ curl -L -o pof_comp.pdf https://biblioteca.ibge.gov.br/visualizacao/livros/liv50002.pdf
HTTP=200 bytes=1833932     → 351 páginas
titulo: "... Tabelas de Composição Nutricional dos Alimentos Consumidos no Brasil"

$ curl -L -o taco.pdf https://www.cfn.org.br/.../taco_4_edicao_ampliada_e_revisada.pdf
HTTP=200 bytes=744346      → 164 páginas · "TACO — Tabela Brasileira de Composição de Alimentos"

# conferência automática de toda citação TACO do dataset contra o PDF
$ python3 (indexa o PDF por número de alimento e compara com `notas`)
casos com citacao TACO conferida contra o PDF real: 38
divergentes: 0 | sem numero TACO citado: 2
  ! simples-arroz-branco-3-colheres  :: n 3 nao localizado    (regex; conferido à mão → 128 ✓)
  ! simples-ovo-cozido-2-unidades    :: n 488 nao localizado  (regex; conferido à mão → 146 ✓)
  ! simples-patinho-grelhado-1-porcao:: n 377 nao localizado  (regex; conferido à mão → 219 ✓)

# consistência aritmética de todos os 43 (kcal/100 g x gramas == referencia_kcal)
$ python3 (recalcula cada caso a partir do próprio `notas`)
aritmetica OK: 43  divergente: 0

# as duas justificativas da terceira fonte
$ grep -i "pizza" taco.txt          → NENHUMA OCORRENCIA
TACO n458: 458 Leite, de vaca, integral * * * * * 10 * NA 0,8 123 10

# limitação 4 do README (as fontes discordam)
TACO n540: 540 Feijoada 71,8 117 ...          POF: 7701901 Feijoada 99 Não se aplica 181,59 ...

# imagens: licença conferida na API do Commons (não no README)
Coxinha.jpg ............ Public domain          · Tom B
Ovo frito ... .jpg ..... CC BY 4.0              · Mtvdanilo
... A Single Banana.jpg  CC BY-SA 4.0           · HaJunkiyada

# imagens: PII / metadados
$ ... python -c "PIL … getexif()"
banana-1-unidade.jpg  | size (960, 1280) | exif tags: 0
coxinha-1-unidade.jpg | size (960, 960)  | exif tags: 0
ovo-frito-1-unidade.jpg | size (960, 1280) | exif tags: 0
(as três abertas e olhadas: 1 coxinha, 1 ovo frito, 1 banana; nenhuma pessoa)

# consequência declarada: replay sem cassette para os casos novos
$ ... python -m evals.runner --cassettes
33 casos com CassetteAusenteError (mensagem instrui `EVAL_RECORD_CASSETTES=1`)

# frontend e segurança
[—] frontend: a fase não toca `frontend/` — nenhum arquivo no diff do range.
[—] security: o manifest declara que não há gate configurado no projeto.
```

## 7. Itens da fase / DoD não atendidos

Nenhum.

- **§9 "C.4 — OQ2 resolvida e registrada; dataset completo validando; limitações
  documentadas"** — os três. OQ2 já estava registrada (2026-08-02) e a OQ17 registra a
  extensão; o dataset valida com `n=43` e zero caso inválido; seis limitações no README,
  todas substantivas — inclusive as que **enfraquecem** a métrica (referência
  populacional, porção padrão ≠ servida, base de massa de fruta com casca, discordância
  entre fontes, fragilidade do estrato `foto` com `n=3`, caso perdido por falta de fonte).
- **Passo 1 (conferir as 10 sementes e virar `verificada: true`)** — 9 sobreviveram
  conferidas, 3 delas corrigidas; 1 removida por falta de fonte auditável, que é a
  aplicação correta do escopo travado e não um item faltante.
- **Passo 2 (popular os três estratos com `fonte_referencia` e `fonte_url` auditáveis)**
  — 23/17/3, e a auditabilidade é fato demonstrado: reproduzi 40 conferências usando só
  o que está em `notas`.
- **Passo 3 (limitações no padrão de honestidade do `eval_golden_set.py`)** — cumprido,
  e a limitação 6 (caso perdido) é do tipo que normalmente some de relatório.
- **Passo 4 (`data_de_adicao` em cada caso)** — `2026-08-03` nos 43, verificado.
- **AC-12** — verificado por execução, não por leitura.
- **DoD global "toda decisão de escopo registrada em §8 ou numa decision"** — as três
  extensões estão na decision `2026-08-03-dataset-c4-fontes-e-arquivos-alem-do-declarado.md`,
  indexada em `decisions/INDEX.md:14`, e na OQ17 (`SPEC…:1600`).
- **NFR-4 / NFR-7** — zero PII, zero EXIF, zero segredo; nenhuma migration.

## 8. Divergências entre o relatório e o código real

Nenhuma divergência. Este relatório é, das execuções que avaliei nesta spec, a que
melhor sobrevive à conferência: testei as afirmações verificáveis uma a uma e todas se
confirmaram.

| Afirmação do relatório | Verificação |
|---|---|
| 43 casos, `verificada: true`, distribuição 23/17/3 | confere, por execução do schema |
| `sha` do dataset `0758d981c3c0e…` | confere, byte a byte |
| cada valor conferido contra a linha publicada | confere — 40 citações TACO contra o PDF, zero divergência; 2 valores POF; 8 medidas |
| estrogonofe 168 → **173**, pizza 270 → **284,72**, feijoada com gordura/carboidrato/fibra corrigidos | conferem os quatro nas publicações |
| a TACO não tem pizza; leite integral (nº 458) vem sem valores | conferem os dois, literalmente |
| licenças das imagens | conferem na API do Commons |
| nenhuma pessoa identificável, nenhuma PII | confere; e as três imagens têm zero EXIF |
| `test_ai_client` falhou por `APIConnectionError`, sem relação com a fase | confere — aqui o mesmo teste **passou** (624 passed), o que confirma sonda de ambiente |
| 4× mais chamadas na camada agendada | confere: 10 → 40 casos executáveis pelo runner de texto |
| cassettes não cobrem as descrições novas | confere — reproduzi os 33 `CassetteAusenteError` |

Uma nota de leitura, não divergência: a cobertura que medi foi **73,86%**, contra
73,92% no relatório. A diferença é o `test_ai_client`, que falhou lá e passou aqui,
exercitando caminhos distintos. Os dois números passam o piso de 72%.

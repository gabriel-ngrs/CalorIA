---
spec: 002-vitrine-eval-e-saneamento
fase: B.5
slug_fase: vision-parser-bug001
status: rework
tentativa: 3
reprovacoes: 2
sha_inicial: 36d68cc
sha_final: 3655892
range: 36d68cc..3655892
---

# FASE B.5 — Relatório de execução

## 0. Tentativa 3 — a última antes do teto

Veredito da tentativa 2: **RESSALVAS**, score 9.7, por um único achado —
**B5-IMP-2**: o README do harness afirmava, na seção *"o que este eval NÃO
mede"*, que o runner ignora o estrato de foto. Verdadeiro até `b8001c3` e falso
**nele** — a própria mudança desta fase.

O achado é procedente e a correção é de documentação. Aplicada em `3655892`:

| Onde | Antes | Agora |
|---|---|---|
| `backend/evals/README.md:23-25` | *"o runner de texto não o executa — quem mede o caminho de imagem é a fase B.5"* | O runner **executa** o estrato desde a B.5, com `n = 3`, e com a ressalva do HTTP 413 na configuração de produção (OQ19) |
| `backend/evals/README.md:135` | *"O runner ignora o estrato `foto`"* | Descreve o roteamento pelo `VisionParser` e documenta `--versao-vision` como a forma de medir sem promover |

**Por que o item continua na lista "não mede", com outra redação.** O avaliador
sugeriu descrever o estado atual, e a tentação era simplesmente apagar o bullet.
Não apaguei: o que o eval de fato **não** mede hoje é o caminho de foto *na
configuração de produção* — porque lá ele falha com 413. Trocar "não executa" por
silêncio deixaria o leitor com a impressão oposta, igualmente falsa.

**Varredura da classe, como a avaliação pediu.** `grep -n "ignora\|não executa\|
entra na fase"` sobre o README volta vazio; as demais menções a B.5 em `backend/`
e `docs/` descrevem o que a fase fez, no passado, e estão corretas. As ocorrências
em `docs/auditoria/` são numeração de seção, sem relação.

**`reprovacoes: 2` — o teto do §2.11.4 se fecha no próximo veredito não-APROVADO.**
Nada de código mudou nesta tentativa.

## 1. Resumo do que foi feito

Rework da tentativa 1 (RESSALVAS, 9.7) por um único achado: **B5-IMP-1 — o delta
do estrato de foto não existia.** Ele não era corrigível então (estrato vazio) e
passou a ser depois da C.4, que populou 3 casos de foto com imagens versionadas.

Duas coisas nesta tentativa: o runner do eval passou a **executar** o estrato de
foto pelo `VisionParser` — o caminho que a própria C.5 deixou explicitamente
para esta fase —, e o delta v1→v2 do prompt de visão foi **medido contra o
provedor real**, em quatro execuções.

**O resultado do delta é "nenhuma melhora nem piora mensurável em n=3"**, com os
números na §5. O gate da fase pede o delta registrado com números, e a cláusula
de testes da §5 da spec prevê exatamente este desfecho: *"o estrato de foto do
eval melhora ou, se não melhorar, o achado é registrado com os números"*.

Os quatro passos de código seguem como estavam — a avaliação da tentativa 1 os
verificou um a um e não achou divergência. **Nada em `vision_parser.py` mudou.**

## 2. Arquivos CRIADOS

| Arquivo | Propósito |
|---------|-----------|
| `backend/tests/unit/test_evals_runner_foto.py` | 13 testes do caminho de foto no runner: roteamento por estrato, imagem ausente, troca/restauração da versão de visão, procedência do prompt no relatório. Zero rede. |
| `.codeflow/decisions/2026-08-04-estrato-de-foto-no-runner-e-teto-de-tokens-da-visao.md` | Registro das duas decisões de escopo desta tentativa. |

*(Da tentativa 1, inalterados: `backend/app/prompts/vision_identify/v2.txt` + `v2.user.txt`, `backend/tests/unit/test_vision_parser_bug001.py`.)*

## 3. Arquivos ALTERADOS

| Arquivo | O que mudou |
|---------|-------------|
| `backend/evals/README.md` | **(t3)** Corrige as duas afirmações que negavam o estrato de foto — é o B5-IMP-2. |
| `backend/evals/runner.py` | Estrato de foto deixa de ser excluído e entra pelo `VisionParser`: `identificar()` roteia por estrato, `imagem_do_caso()` falha alto se a imagem some, `versao_de_visao()` troca `_IDENTIFY_PROMPT` e restaura, `--versao-vision` na CLI, e o relatório declara a versão de visão usada. |
| `SPEC_002_…md` | OQ19 (escopo + achado do 413); item da B.5 na §9; `updated_at`. |
| `.codeflow/decisions/INDEX.md` | Linha da decision nova. |

*(Da tentativa 1, inalterados: `backend/app/services/ai/vision_parser.py`, `backend/tests/unit/test_prompt_registry.py`.)*

## 4. Confirmação do REUSO e decisões de design

**REUSADO.** O runner executa o `VisionParser` **de produção** — o mesmo objeto
que o endpoint aciona —, não uma reimplementação; a instrumentação de lookup, o
agregador, as métricas e o formato de relatório são os da C.5, sem cópia. A
troca de versão de prompt segue o padrão global-e-restaurado que
`instrumentar_lookup` já estabeleceu no mesmo arquivo. As imagens e as
referências são as que a C.4 versionou.

**Decisões de design:**

- **`versao_de_visao()` em vez de editar `VERSOES_EM_PRODUCAO`.** Medir uma
  versão não pode exigir promovê-la — promover é o ato que a C.2 isolou de
  propósito. O context manager restaura mesmo com exceção (há teste).
- **O relatório lê a versão de visão do módulo, não de `get_prompt`.** Sob
  `versao_de_visao(1)`, `get_prompt` devolveria a v2 (produção) e o histórico
  append-only da C.8 registraria o resultado da v1 sob o `sha` da v2 — os dois
  pontos da série ficariam idênticos e o delta desapareceria do registro.
- **Caso de foto sem parser de visão vira falha registrada**, não sumiço: um
  caso que desaparece do denominador melhora a métrica sem melhorar nada.

**DESVIOS, ambos registrados na OQ19 e na decision:**

1. **`backend/evals/runner.py` e `tests/unit/test_evals_runner_foto.py` não
   constam dos "Arquivos alterados" da B.5.** A linha que eu removi era
   `if c.estrato is not Estrato.FOTO  # o caminho de foto entra na fase B.5` —
   a C.5 desenhou o runner deixando este pedaço nomeadamente para cá. Sem ele o
   gate da fase não tem instrumento. Não ampliei nada além disso: o
   `MealParser`, os limiares da decision de 2026-07-26, o dataset da C.4 e o
   `VERSOES_EM_PRODUCAO` não foram tocados.
2. **As medições rodaram com `GROQ_MAX_TOKENS=2048`, não com o valor de
   produção (8192)** — porque com 8192 os três casos falham com HTTP 413 (§5).
   O valor está declarado no campo `amostragem` de cada relatório, e a ressalva
   acompanha os números.

## 5. Comandos rodados + saídas reais

### 5.1 O delta do estrato de foto — o item que faltava

Quatro execuções contra a Groq real, dataset `9711e969…` (3 casos de foto),
modelo de visão `qwen/qwen3.6-27b`, `temperature 0.1`, `seed -1`,
`GROQ_MAX_TOKENS 2048`:

```text
$ docker compose -f docker-compose.dev.yml exec -T -e GROQ_MAX_TOKENS=2048 backend \
    python -m evals.runner --estrato foto --versao-vision <N> --repeticoes <R> --json

execucao   MdAPE     MAPE     SSPB    <=10%   IC95 do MdAPE      MAE prot/carb/gord (g)
v1  r=3    52.17%   63.50%   +52.17%    0%   [ 12.17, 126.15]    2.38 / 5.43 / 5.66
v1  r=1    52.17%   63.50%   +52.17%    0%   [ 12.17, 126.15]    2.28 / 5.50 / 5.79
v2  r=3    52.17%   48.51%   +52.17%    0%   [ 16.67,  76.68]    3.22 / 3.97 / 3.34
v2  r=1    52.17%   65.00%   +52.17%    0%   [ 16.67, 126.15]    3.88 / 5.63 / 5.01

custo total das quatro: 48 chamadas ao provedor, 100.929 tokens_in, 5.907 tokens_out
latencia mediana por caso: 102,9 s (v1 r=3) e 83,7 s (v2 r=3), origem: provedor
falhas: nenhuma nas quatro execuções
```

**Leitura, e é a parte que importa:**

- **MdAPE — a métrica headline por decisão da §4 da spec — é 52,17% nas quatro
  execuções.** Idêntica antes e depois. O delta v1→v2 em MdAPE é **zero**.
- **SSPB é +52,17% nas quatro:** o caminho de foto **superestima
  sistematicamente**, e a v2 não mexeu nisso. O sinal positivo é o modo de falha
  menos danoso num diário alimentar (a §4 da spec explica por quê), mas 52% é
  muito.
- **A aparente melhora de MAPE da v2 (63,50 → 48,51) não se sustenta.** A
  segunda execução da **mesma** v2 deu 65,00 — acima da v1. A variação entre
  duas rodadas da mesma versão é **maior** que a variação entre versões, então o
  MAPE aqui está medindo ruído, não prompt. A v1, por contraste, deu 63,50 nas
  duas rodadas.
- **Nenhum caso de foto ficou dentro de ±10% em nenhuma execução** (`<=10%: 0%`).
- **n = 3.** Os IC95 dos dois lados se sobrepõem quase inteiros. Nenhuma
  afirmação de melhora ou piora é sustentável com este tamanho de amostra — e o
  README do harness (C.3) já declara que o `n` do projeto não detecta efeitos
  pequenos. Este estrato é o caso extremo disso.

**Conclusão registrada:** a v2 do prompt de visão **não regride** o estrato de
foto e **não melhora** de forma mensurável. O valor da B.5 continua sendo o que
a avaliação da tentativa 1 já verificara — itens que não se perdem mais em
silêncio e quantidade por extenso que não vira HTTP 500 —, e não um ganho de
acurácia que os números não sustentam.

### 5.2 O achado do HTTP 413 (registrado, não corrigido)

A primeira execução, com a configuração de produção, falhou nos **três** casos:

```text
$ docker compose -f docker-compose.dev.yml exec -T backend \
    python -m evals.runner --estrato foto --versao-vision 1 --repeticoes 3 --json
foto: n=0
falhas: 3/3
  APIStatusError: Error code: 413 — Request too large for model `qwen/qwen3.6-27b`
    on tokens per minute (TPM): Limit 8000, Requested 11357

$ ls -la backend/evals/dataset/imagens/
111512  coxinha-1-unidade.jpg
200383  ovo-frito-1-unidade.jpg
291049  banana-1-unidade.jpg
   → `Requested 11357` é IDÊNTICO para os três tamanhos: a imagem custa fixo,
     e quem estoura o limite é o max_tokens reservado (8192, config.py:85).

$ grep -rn "PIL\|Image.open\|resize" backend/app/
   (sem saída — o backend não redimensiona)
$ grep -rn "fileToBase64" -A 10 frontend/app/\(dashboard\)/refeicoes/page.tsx
   readAsDataURL(file) — o frontend envia o arquivo bruto, sem redimensionar
```

**Consequência que passa do eval: a análise por foto está quebrada em produção
no free tier**, para qualquer foto, e não por defeito do `VisionParser`. O fix é
em `config.py`/`ai_client.py` (território da C.2) ou no frontend — fora do
escopo travado desta fase, que proíbe ampliá-la. Detalhe e sugestão de correção
(`GROQ_VISION_MAX_TOKENS` próprio) na decision.

### 5.3 Gates de validação do projeto

```text
$ docker compose -f docker-compose.dev.yml exec -T backend sh -c \
    "ruff check . && ruff format --check . && mypy app/ evals/"
All checks passed!
148 files already formatted
Success: no issues found in 81 source files

$ docker compose -f docker-compose.dev.yml exec -T backend pytest tests/unit -q
489 passed in 3.98s          # 488 antes + os 13 novos, 12 dos quais no arquivo novo

$ docker compose -f docker-compose.dev.yml exec -T backend pytest tests/unit/test_evals_runner_foto.py -q
13 passed

# vermelho antes do verde — testes escritos após a mudança, redness verificada
# revertendo só o runner:
$ git stash push -- backend/evals/runner.py && pytest tests/unit/test_evals_runner_foto.py -q
11 failed, 1 passed
$ git stash pop

$ bash ~/.codeflow/framework/core/scripts/run-structural.sh .codeflow/specs/002-.../SPEC_002_....md
✓ §5 estruturalmente válida   >>> EXIT=0

# pre-commit no commit do código (inclui gitleaks):
Detect hardcoded secrets.................................................Passed

# [—] make test-integration NÃO RODADO nesta tentativa. O diff é de `evals/` e de
#     testes unitários; nenhum endpoint, model, migration ou service de produção
#     foi tocado. A suíte de integração foi rodada e verde na tentativa 1
#     (581 passed, cobertura 73,10%) sobre o mesmo código de produção, que não mudou.
# [—] make test-frontend NÃO RODADO. Nenhum arquivo de frontend no diff.
```

## 6. Critérios de aceite da fase (com evidência)

- [x] **AC-17, nenhum item perdido em silêncio** — `TestNenhumItemSePerdeEmSilencio`
      em `test_vision_parser_bug001.py`; verificado independentemente pela
      avaliação da tentativa 1 (§6, `vision_parser.py:158` `strict=True`).
      Inalterado nesta tentativa.
- [x] **AC-17, quantidade por extenso não gera 500** —
      `TestQuantidadePorExtensoNaoVira500`, parametrizado sobre `"dois"`, `"1/2"`,
      `""`, `"abc"`; guard `_num()` em `vision_parser.py:206-213`. Inalterado.
- [x] **AC-17, o prompt de visão não contém mais as regras de decomposição
      obrigatória e de gramas obrigatórias** — `TestPromptDeVisaoV2`; a v1 segue
      no disco com as regras antigas (regra de imutabilidade da C.8), o que é
      justamente o que tornou o delta desta tentativa mensurável.
- [x] **`0.35` inline extraído** — `TestConstanteDeSanityCheck`,
      `vision_parser.py:32`.
- [x] **Delta do estrato de foto registrado com números antes e depois** — §5.1:
      quatro execuções contra o provedor real, tabela completa, com a conclusão
      de que não há delta separável do ruído em n=3.

## 7. Definition of Done da fase

- [x] Testes da fase verdes (489 unitários; 13 novos)
- [x] `ruff`, `ruff format`, `mypy app/ evals/` limpos
- [—] `make test-integration` e `make test-frontend` — justificado em §5.3
      (nenhum arquivo de produção nem de frontend no diff desta tentativa)
- [x] Escopo travado respeitado: `MealParser` intocado, parsers não unificados,
      calibração visual do prompt preservada, limiares de 2026-07-26 intactos
- [x] Dois desvios de escopo declarados, com decision e OQ19 (§4)
- [x] Nenhum segredo/PII: `gitleaks` do pre-commit passou; os relatórios de eval
      não carregam chave (o `custo` traz só contagem de tokens)
- [x] Commits em pt-BR, sem menção a autor/IA

## 8. O que mudou nesta tentativa

**Achado B5-IMP-1 (o único da avaliação): corrigido.**

| Antes (tentativa 1) | Agora |
|---|---|
| Gate `[—]` — "estrato de foto vazio, C.4 não executada" | Gate `[x]` — 3 casos, 4 execuções, números na §5.1 |
| Runner excluía o estrato de foto | Runner executa o estrato de foto pelo `VisionParser` |
| `Depende de: C.6` (erro de grafo) | `Depende de: C.4`, já corrigido na spec em 2026-08-03 |

Também endereçado da §5 (sugestões) da avaliação: *"vale a C.4 incluir dois ou
três casos de foto só para dar linha de base à v2 antes de ela virar padrão"* —
a C.4 incluiu três, e esta tentativa produziu a linha de base. Ela diz que a v2
entrou em produção sem ganho de acurácia demonstrável; a decisão de mantê-la
segue defensável pelos três defeitos de robustez que ela corrige, mas agora está
medida em vez de suposta.

**Não** endereçadas, por serem fora de escopo e a avaliação já as situar assim:
promover `_num`/`_FONTES_CURADAS` para módulo compartilhado (espera a
desduplicação dos ~120 LOC), e importar `_SANITY_DIVERGENCE` em vez de testar a
igualdade.

## 9. Itens em aberto / dúvidas para o avaliador

1. **O HTTP 413 é o achado mais consequente desta tentativa e eu não o
   corrigi.** É produção quebrada no caminho de foto, descoberta pelo eval —
   exatamente o que o Track C existe para fazer. Deixei como achado porque o fix
   mora em `config.py`/`ai_client.py` (C.2) e no frontend, e o escopo travado da
   B.5 proíbe ampliar a fase. **Pergunta:** isto deveria virar fase nova (ex.:
   `C.9`) ou rework da C.2, que já está aprovada?
2. **n = 3 no estrato de foto é pouco para o gate que a fase se impôs.** O delta
   está registrado com números e a conclusão honesta é "não há delta
   mensurável" — mas quem ler a série da C.8 verá dois pontos com o mesmo MdAPE
   e IC95 largos. Vale a pena o estrato de foto crescer antes de o número ser
   citado no README da D.3?
3. **A execução do delta usou `GROQ_MAX_TOKENS=2048`.** Está declarado em cada
   relatório e na OQ19, mas nenhuma dessas quatro linhas foi registrada em
   `evals/runs/history.jsonl` — não quis poluir a série append-only da C.8 com
   medições feitas sob parâmetro diferente do de produção. **Pergunta:** deveria
   registrar mesmo assim, já que `amostragem` carrega a diferença?
4. **O `range` desta fase não a isola** (`36d68cc..b8001c3`): pega os commits de
   fases posteriores executadas no intervalo. É conforme ao §2.9.3, que manda ir
   do início original ao HEAD. O commit desta tentativa é **`b8001c3`**, e o da
   tentativa 1 é `40e2941`.

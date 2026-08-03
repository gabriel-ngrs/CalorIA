---
spec: 002-vitrine-eval-e-saneamento
fase: C.3
slug_fase: harness-schema
tentativa: 1
veredito: APROVADO
score: 9.8
threshold: 8.5
range_avaliado: 97a4b0d..0d4d9ec
---

# FASE C.3 — Avaliação independente

## 1. Veredito e score

**Veredito:** APROVADO · **Score:** 9.8 / threshold 8.5

Fase de contrato, e o contrato ficou certo. O ponto que eu mais procurei — se o
executor decidiu OQ2 por conta própria, que o escopo travado proíbe — está
respeitado: os 10 casos-semente estão todos com `verificada: false` e o README
declara a limitação. O schema rejeita a circularidade que o próprio projeto tinha
identificado.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 5 | AC-12 nas três cláusulas (campos obrigatórios, fonte proibida, `fonte_url`). **OQ2 não foi decidida aqui**: os 10 casos têm `verificada: false` e o cabeçalho de `casos.jsonl` diz que a C.4 é quem confere. `scripts/eval_golden_set.py` e `tests/integration/test_golden_set.py` intocados — confirmei no diff do range. |
| 2 | Arquitetura e direção de dependências | 3 | 5 | `evals/schema.py` não importa `app.services`: é contrato puro, carregável sem banco e sem rede. `TestCamadaRapidaNaoTocaARede::test_o_dataset_carrega_sem_banco_e_sem_rede` prova isso e o CI o executa. |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | Dataset sem PII; nenhuma imagem versionada (o estrato `foto` está vazio, o que também evita o risco de licença que o escopo travado da C.4 antecipa). `gitleaks` sobre o range: zero achados. |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | Casos derivados do `GOLDEN` existente em vez de inventados, com a procedência marcada. `sha_do_dataset` e `distribuicao_por_estrato` viram funções do schema, consumidas depois pelo runner e pelo report — uma fonte, três consumidores. |
| 5 | Padrões de domínio/aplicação | 2 | 4 | Pydantic v2 com `Estrato` como enum, no padrão do projeto. Desconto: `casos.jsonl` usa comentários `//`, que não são JSONL válido (§5). |
| 6 | Local e nomes dos arquivos | 2 | 5 | `backend/evals/` como pacote irmão de `app/` e `tests/`, `dataset/casos.jsonl`, `README.md` do harness — tudo onde a spec pediu. |
| 7 | Qualidade de código | 2 | 5 | `mypy` strict limpo sobre `evals/`; erro de carregamento aponta o número da linha do arquivo, o que torna um dataset malformado diagnosticável em vez de misterioso. |
| 8 | Testes e cobertura | 2 | 5 | 158 linhas: campos obrigatórios parametrizados, 4 grafias de `portions` rejeitadas, 3 formas não localizáveis de `fonte_url` rejeitadas, `id` duplicado recusado com o número da linha. |
| 9 | Migration safety (se aplicável) | 2 | [—] | Nenhuma migration no range (NFR-7). |

Média ponderada das 8 dimensões aplicáveis: 98/20 = 4.9 → **9.8**.

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

Nenhum.

## 5. Sugestões

- **`casos.jsonl` e `grupos_invariancia.jsonl` usam `//` para comentar.** JSONL
  não tem comentários; o carregador do projeto os ignora explicitamente
  (`invariance.py:109`, e o equivalente no `schema.py`), então funciona. O custo é
  que nenhuma ferramenta genérica — `jq`, um validador de schema, um editor com
  lint de JSONL — consegue ler o arquivo. Duas saídas: mover o cabeçalho para o
  `README.md` do harness, ou aceitar o desvio e registrá-lo numa linha do README
  para quem tentar `jq` e se frustrar. O conteúdo do cabeçalho é bom demais para
  simplesmente apagar — é ele que impede alguém de citar os números como
  verificados.
- **O campo `verificada` é a peça mais importante do contrato e a mais fácil de
  esquecer.** Hoje ele aparece no relatório do runner como
  `nao verific.: 10 caso(s)`, o que é ótimo. Vale a C.4 considerar um teste que
  falhe quando `verificada: false` e a fonte já for declarada como conferida —
  para que virar o campo seja ato deliberado.
- A análise de poder no README (~5 p.p. de efeito mínimo detectável no desenho
  pareado contra ~22 p.p. no não pareado) é o tipo de rigor que quase nenhum
  projeto desse porte escreve. Vale referenciá-la do README da raiz quando a D.3
  reescrever a vitrine — é diferencial real, e hoje está enterrada.

## 6. Comandos rodados + saídas reais

Ambiente: container `caloria_backend`, branch `dev`, HEAD `e3a974a`.
`git merge-base --is-ancestor 0d4d9ec HEAD` → OK.

```text
# o escopo travado central: OQ2 não decidida, casos não verificados
$ python3 -c "... casos.jsonl ..."
simples-arroz-cozido-100g            | simples  | 128.0  | TACO 4a edicao ... | False
simples-feijao-carioca-100g          | simples  |  76.0  | TACO 4a edicao ... | False
simples-frango-peito-grelhado-100g   | simples  | 159.0  | TACO 4a edicao ... | False
simples-ovo-cozido-100g              | simples  | 146.0  | TACO 4a edicao ... | False
simples-banana-nanica-100g           | simples  |  92.0  | TACO 4a edicao ... | False
simples-tomate-cru-100g              | simples  |  15.0  | TACO 4a edicao ... | False
composto-feijoada-100g               | composto | 117.0  | TACO 4a edicao ... | False
composto-lasanha-carne-100g          | composto | 168.0  | TACO 4a edicao ... | False
composto-pizza-calabresa-400g        | composto | 1080.0 | TACO 4a edicao ... | False
composto-strogonoff-carne-100g       | composto | 168.0  | TACO 4a edicao ... | False
casos: 10     # todos verificada=false, como a fase determina

$ head -1 backend/evals/dataset/casos.jsonl
// Dataset de avaliação — casos-SEMENTE da fase C.3 da spec 002.
# o cabeçalho declara a limitação: "serve para exercitar o runner, não para
# sustentar afirmação pública"

# escopo travado: o gate determinístico não foi tocado
$ git diff --name-only 97a4b0d..0d4d9ec | grep -c "eval_golden_set\|test_golden_set"
0

$ docker compose -f docker-compose.dev.yml exec -T backend pytest tests/unit/test_evals_schema.py -q
(passa dentro da suíte completa; nenhuma falha)

$ ... pytest --cov=app --cov-report=term -q
581 passed, 1 skipped, 5 warnings in 88.01s
Required test coverage of 72.0% reached. Total coverage: 73.10%

$ ... ruff check . && ... ruff format --check . && ... mypy app/ evals/
All checks passed! / 147 files already formatted / Success: no issues found in 81 source files

$ gitleaks detect --config .gitleaks.toml --log-opts="d8cc463~1..HEAD"
22 commits scanned.  no leaks found          # NFR-4, dataset incluído

$ git status --short
(limpo)
```

## 7. Itens da fase / DoD não atendidos

Nenhum. O gate — "AC-12 satisfeito; schema validado; README com a análise de
poder escrita" — está satisfeito nas três cláusulas.

Registro, sem contar contra esta fase: o estrato `foto` nasceu vazio, o que é
correto aqui (a fase manda não popular além do mínimo) mas torna o gate da B.5
insatisfazível. Está anotado na avaliação da B.5, onde cabe.

## 8. Divergências entre o relatório e o código real

Nenhuma. Confirmei os três itens da §6 do EXECUCAO contra o repositório: o
arquivo carrega inteiro, as fontes proibidas são rejeitadas nas quatro grafias, e
a seção de poder estatístico está no README com o efeito mínimo detectável e a
lista do que o `n` **não** detecta — que é a metade que costuma faltar.

---
spec: 002-vitrine-eval-e-saneamento
fase: B.5
slug_fase: vision-parser-bug001
tentativa: 1
veredito: RESSALVAS
score: 9.7
threshold: 8.5
range_avaliado: 36d68cc..40e2941
---

# FASE B.5 — Avaliação independente

## 1. Veredito e score

**Veredito:** RESSALVAS · **Score:** 9.7 / threshold 8.5

Os quatro passos de código foram entregues e verifiquei cada um no arquivo. O que
impede o APROVADO é o **gate declarado da própria fase**: "delta do estrato de
foto registrado no relatório com números antes e depois". Ele não foi medido, e
não é medível hoje — o estrato `foto` do dataset está vazio, porque depende da
C.4. O executor marcou `[—]` honestamente e nomeou a dependência; ainda assim, o
critério de conclusão não está satisfeito.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 4 | Passos 1–4 verificados: v2 do prompt criada com as regras 4 e 5 substituídas (diff em §6), `strict=True` em `vision_parser.py:157`, `_SANITY_DIVERGENCE` extraída (`:32`), guard `_num()` em `:204-211`. Escopo travado respeitado: `MealParser` intocado, parsers não unificados, calibração visual preservada. Desconto pelo gate do delta (§7). |
| 2 | Arquitetura e direção de dependências | 3 | 5 | `vision_parser.py` continua consumindo `AIClient` por construtor; nenhuma inversão. A v1 do prompt permanece imutável no disco — `git log -- app/prompts/vision_identify/v1.txt` mostra um único commit, o da C.1. |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | `parse_base64` continua sem persistir imagem (constitution do projeto). A correção do fallback elimina um caminho de HTTP 500 disparado por dado da IA — é redução de superfície, não aumento. |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | Espelha o `MealParser` em vez de reimplementar: importa `_num` e `_FONTES_CURADAS` de lá (`vision_parser.py:12`), e o comentário de `:29-32` declara a intenção de não divergir. É a leitura certa do escopo travado, que proíbe unificar mas não proíbe compartilhar. |
| 5 | Padrões de domínio/aplicação | 2 | 5 | `needs_review` + `review_reason` seguem o contrato de `ParsedFoodItem` já usado pelo `MealParser`; nada inventado. |
| 6 | Local e nomes dos arquivos | 2 | 5 | `app/prompts/vision_identify/v2.txt` e `v2.user.txt` no layout do registry; testes em `tests/unit/test_vision_parser.py`. |
| 7 | Qualidade de código | 2 | 5 | `mypy app/ evals/` limpo; comentários de `:154-156` e `:181-185` explicam o "por quê" do `strict=True`, não o "o quê" — como a constitution pede. |
| 8 | Testes e cobertura | 2 | 5 | AC-17 coberto nas três cláusulas: `TestNenhumItemSePerdeEmSilencio`, `TestQuantidadePorExtensoNaoVira500` (parametrizado sobre `"dois"`, `"1/2"`, `""`, `"abc"`), `TestPromptDeVisaoV2`. O gate de `sha` da C.1 pegou o bump do prompt e exigiu atualização consciente — evidência de que o mecanismo da C.1 funciona. |
| 9 | Migration safety (se aplicável) | 2 | [—] | Não aplicável; nenhuma migration no range. |

Média ponderada das 8 dimensões aplicáveis: 97/20 = 4.85 → **9.7**.

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

**B5-IMP-1 — o critério de conclusão da fase não foi satisfeito: o delta do
estrato de foto não existe.**

`SPEC_002...md:778-779`:

> **Critério de conclusão (gate):** AC-17 satisfeito; delta do estrato de foto
> registrado no relatório com números antes e depois.

Confirmei a impossibilidade, não apenas li a alegação:

```text
$ python3 -c "... casos.jsonl ..."
distribuicao: {'simples': 6, 'composto': 4, 'foto': 0}
```

E o runner exclui o estrato explicitamente (`evals/runner.py:417`):

```python
if c.estrato is not Estrato.FOTO  # o caminho de foto entra na fase B.5
```

O comentário no runner diz que o caminho de foto "entra na fase B.5", mas a B.5
não populou o estrato — e nem poderia, porque `casos.jsonl` é entregável da C.3
(mínimo) e da C.4 (completo), e a C.4 não foi executada. A fase declara depender
de `C.6`, quando o gate que ela mesma se impôs depende de `C.4`. É um erro de
grafo de dependências na spec, não do executor.

**Correção sugerida** (decisão do owner, duas saídas legítimas):

1. **Ajustar a spec:** trocar o gate da B.5 para o que é verificável hoje
   (AC-17 + os quatro passos), e mover "delta do estrato de foto" para o gate da
   C.4, que é onde o dataset de foto nasce. Registrar em §8 ou numa decision.
2. **Manter o gate e reabrir a B.5 depois da C.4**, aceitando que a fase fique
   pendente até lá. Nesse caso a linha "Depende de: `C.6`" deve virar
   "Depende de: `C.4`".

A opção 1 é a que recomendo: o código da fase está pronto e correto, e mantê-la
aberta por um dataset que outra fase produz bloqueia o Track B por razão alheia.

## 5. Sugestões

- `vision_parser.py:12` importa dois nomes privados (`_FONTES_CURADAS`, `_num`)
  de `meal_parser.py`. A intenção está certa — não divergir — mas o `_` diz o
  contrário do uso. Promover os dois para um módulo compartilhado
  (`services/ai/_comum.py` ou similar) tornaria o contrato explícito. Fica para
  quando a desduplicação dos ~120 LOC sair do gelo; hoje seria refatoração
  lateral, vedada pelo escopo travado.
- O texto substituto das regras 4 e 5 da v2 foi escrito por espelhamento do
  `MealParser` (dúvida 2 do EXECUCAO). É consistente, mas o prompt de visão nunca
  passou por medição — a v2 entra no eval "no escuro". Vale a C.4 incluir dois ou
  três casos de foto só para dar linha de base à v2 antes de ela virar padrão de
  produção por muito tempo.
- `_SANITY_DIVERGENCE` está declarada nos dois parsers com o mesmo valor literal
  (`0.35`). Um teste garante a igualdade, o que resolve o risco de divergência,
  mas importar a constante seria mais barato que testá-la.

## 6. Comandos rodados + saídas reais

Ambiente: container `caloria_backend`, branch `dev`, HEAD `e3a974a`.
`git merge-base --is-ancestor 40e2941 HEAD` → OK.

```text
# passo 1 — regras 4 e 5 removidas em versão NOVA, v1 intocada
$ diff backend/app/prompts/vision_identify/v1.txt backend/app/prompts/vision_identify/v2.txt
8,9c8,9
< 4. Liste cada alimento separadamente, mesmo em pratos compostos.
< 5. Estime porções sempre em gramas (unit="g").
---
> 4. PRATO CONHECIDO VEM INTEIRO. Se a foto mostra um prato brasileiro reconhecível [...]
> 5. Devolva a quantidade na unidade que descreve melhor o que está visível [...]

$ git log --oneline -- backend/app/prompts/vision_identify/v1.txt
8c07142 feat(ai): extrai prompts para registry versionado com sha256
# um único commit: a v1 nunca foi editada depois de criada (regra da C.8)

# passos 2, 3 e 4 — verificados no arquivo
$ grep -n "strict=True\|_SANITY_DIVERGENCE\|_num(" backend/app/services/ai/vision_parser.py
32:_SANITY_DIVERGENCE = 0.35
93:  divergence > _SANITY_DIVERGENCE
157:  for idx, parsed in zip(to_estimate_idx, estimated, strict=True):
204:  quantity=_num(original.quantity),
206-211: calories/protein/carbs/fat/fiber/confidence via _num(...)

# suíte inteira, no ambiente real
$ docker compose -f docker-compose.dev.yml exec -T backend pytest --cov=app --cov-report=term -q
581 passed, 1 skipped, 5 warnings in 88.01s
Required test coverage of 72.0% reached. Total coverage: 73.10%

$ ... ruff check . && ... ruff format --check . && ... mypy app/ evals/
All checks passed! / 147 files already formatted / Success: no issues found in 81 source files

# o estrato que o gate exige medir
$ python3 -c "import json; [...]"   # sobre backend/evals/dataset/casos.jsonl
casos: 10   distribuicao: {'simples': 6, 'composto': 4, 'foto': 0}

$ git status --short
(limpo)
```

## 7. Itens da fase / DoD não atendidos

- **Gate da fase e §9 do DoD** — "AC-17; delta do estrato de foto registrado com
  números". A primeira metade está satisfeita e verificada; a segunda não existe
  (B5-IMP-1).
- Passo 5 da fase ("rodar o eval do estrato de foto antes e depois") não foi
  executado, pela mesma causa.

## 8. Divergências entre o relatório e o código real

Nenhuma. Confirmei individualmente os quatro passos, a imutabilidade da v1 e as
três cláusulas do AC-17 contra o código, e o relatório descreve o que está lá. O
item `[—]` do delta é declarado com a causa correta.

Uma observação de precisão, não de divergência: o EXECUCAO §5 mostra a suíte em
`474 passed, 5 skipped`; hoje são `581 passed, 1 skipped`. A diferença vem das
fases posteriores e da correção do schema de teste (B.4), não desta fase.

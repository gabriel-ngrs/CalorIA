---
spec: 002-vitrine-eval-e-saneamento
fase: B.5
slug_fase: vision-parser-bug001
status: executado
tentativa: 1
reprovacoes: 0
sha_inicial: 36d68cc
sha_final: 40e2941
range: 36d68cc..40e2941
---

# FASE B.5 — Relatório de execução

## Nota de 2026-08-03 — fase estacionada até a C.4

Veredito da tentativa 1: **RESSALVAS**, score 9.7, por um único achado — B5-IMP-1.

**O achado é procedente e não é corrigível dentro desta fase.** O gate declarado
("delta do estrato de foto registrado com números antes e depois") depende do estrato
`foto` do dataset, que está vazio: `casos.jsonl` traz
`{'simples': 6, 'composto': 4, 'foto': 0}`, e o dataset de foto é entregável da **C.4**,
que não foi executada. A fase declarava `Depende de: C.6`, quando o gate que ela mesma
se impõe depende da `C.4` — erro de grafo na spec, não de execução.

**Decisão do owner em 2026-08-03: manter o gate e reabrir a B.5 depois da C.4**
(opção 2 das duas que a avaliação apresenta). A spec foi corrigida em §5: a linha
"Depende de" da B.5 passa de `C.6` para `C.4`, com a justificativa registrada ali e no
item do §9 do DoD. O gate estrutural (`run-structural.sh`) continua em `EXIT=0` — a
C.4 depende só da C.3, então não há ciclo.

**Nada mudou no código desta fase**, e por isso `status`, `tentativa` e `reprovacoes`
ficam como estavam: não houve rework. Os quatro passos entregues e o AC-17 seguem
verificados como na tentativa 1; o que falta é o dataset.

**Para quem retomar depois da C.4:** rodar o eval do estrato de foto antes e depois da
v2 do prompt de visão e registrar o delta com números — é o passo 5 da fase, o único
não executado. A avaliação registra uma observação que vale ler junto: o prompt de
visão nunca passou por medição, então a v2 entra no eval sem linha de base, e vale a
C.4 incluir dois ou três casos de foto só para dar essa linha de base.

*(Registro adicional: a fase C.2 criou `vision_identify@v3` para o JSON mode. A v2 —
que é a desta fase — continua sendo a versão em produção, fixada em
`VERSOES_EM_PRODUCAO`. A v3 não substitui o trabalho da B.5: acrescenta o formato de
objeto por cima dele.)*


## 1. Resumo do que foi feito

Os quatro defeitos que o `MealParser` já tinha resolvido e o caminho de foto
ainda carregava foram corrigidos. O passo 5 (delta do estrato de foto) **não foi
executado** — o estrato de foto está vazio e o provedor é inalcançável nesta
sessão; detalhe em §6.

## 2. Arquivos CRIADOS

| Arquivo | Propósito |
|---------|-----------|
| `backend/app/prompts/vision_identify/v2.txt` + `v2.user.txt` | Nova versão do prompt de visão, sem as regras 4 e 5 originais. |
| `backend/tests/unit/test_vision_parser_bug001.py` | 17 testes de regressão. |

## 3. Arquivos ALTERADOS

| Arquivo | O que mudou |
|---------|-------------|
| `backend/app/services/ai/vision_parser.py` | `zip(strict=True)`; laço do fallback com saída garantida por entrada; guard `_num` na quantidade; `_SANITY_DIVERGENCE` no lugar do `0.35` inline. |
| `backend/tests/unit/test_prompt_registry.py` | `sha` travado de `vision_identify` atualizado junto do bump para v2, e o teste de "versão ativa" virou tabela por prompt. |

## 4. Confirmação do REUSO e decisões de design

**REUSADO:** `meal_parser.py` como referência exata da correção já feita — o
guard `_num` é **importado** de lá, não reimplementado; o laço do fallback segue
a mesma forma de `meal_parser.py:295-330`; `_SANITY_DIVERGENCE` recebeu o mesmo
nome, e há teste garantindo que os dois valores continuam iguais.

**Decisões de design:**
- **v2, não edição da v1.** A v1 continua no disco com as regras antigas — há
  teste verificando isso. É a regra de imutabilidade da C.8, e é o que torna
  possível medir v1 contra v2 quando o eval de foto existir.
- **As regras 4 e 5 não foram só apagadas; foram substituídas** pelas
  equivalentes do `MealParser` corrigido — "PRATO CONHECIDO VEM INTEIRO" e
  quantidade na unidade que descreve o que está visível. Remover sem substituir
  deixaria o prompt sem orientação nenhuma sobre decomposição e unidade, o que é
  mudança maior que a corrigida.
- **A tabela de calibração visual foi preservada integralmente**, por escopo
  travado — é específica de foto e não tem relação com o bug 001. Há teste.
- **`strict=True` no `zip` de reinserção dos estimados** é seguro porque o laço
  do fallback agora garante uma saída por entrada; com `strict=False`, um
  descasamento futuro voltaria a descartar itens em silêncio.

**Escopo travado respeitado:** `MealParser` e `VisionParser` **não** foram
unificados (a duplicação de ~120 LOC continua, conhecida e fora desta spec); o
`MealParser` não foi alterado; a calibração visual não foi tocada; os limiares da
decision de 2026-07-26 não foram mexidos.

## 5. Comandos rodados + saídas reais

```text
$ diff app/prompts/vision_identify/v1.txt app/prompts/vision_identify/v2.txt
8,9c8,9
< 4. Liste cada alimento separadamente, mesmo em pratos compostos.
< 5. Estime porções sempre em gramas (unit="g").
---
> 4. PRATO CONHECIDO VEM INTEIRO. [...]
> 5. Devolva a quantidade na unidade que descreve melhor o que está visível [...]

# o gate de sha da C.1 pegou o bump, como projetado:
$ pytest tests/unit -q
FAILED tests/unit/test_prompt_registry.py::...::test_sha_da_versao_ativa_esta_travado[vision_identify]
FAILED tests/unit/test_prompt_registry.py::...::test_versao_ativa_e_a_v1
FAILED tests/unit/test_prompt_registry.py::...::test_vision_parser_usa_o_registry
3 failed, 349 passed

# depois de atualizar o sha travado junto do bump:
$ pytest tests/unit -q
357 passed in 3.95s

$ ruff check . && ruff format --check . && mypy app/ evals/
All checks passed! / 135 files already formatted / Success: no issues found

$ pytest -q --ignore=tests/smoke_test.py
474 passed, 5 skipped, 3 warnings in 51.89s
```

## 6. Checklist dos ACs / critério de conclusão

- [x] **AC-17, nenhum item perdido em silêncio** —
      `TestNenhumItemSePerdeEmSilencio`: três alimentos entram, a IA devolve um,
      três saem; os dois faltantes vêm marcados com `needs_review` e motivo. Há
      também o caso de a IA devolver mais objetos que o pedido.
- [x] **AC-17, quantidade por extenso não gera 500** —
      `TestQuantidadePorExtensoNaoVira500`, parametrizado sobre `"dois"`,
      `"1/2"`, `""` e `"abc"`, mais o caso de string numérica aproveitada.
      (`None` fica de fora: `IdentifiedFood` já o rejeita no Estágio 1.)
- [x] **AC-17, o prompt de visão não contém mais as regras de decomposição
      obrigatória e de gramas obrigatórias** — `TestPromptDeVisaoV2`, incluindo a
      verificação de que a v1 continua no disco com as regras antigas.
- [x] **`0.35` inline extraído** — `TestConstanteDeSanityCheck`, incluindo a
      igualdade com o valor do `MealParser`.
- [—] **Delta do estrato de foto registrado com números antes e depois** — não
      executável: o estrato `foto` do dataset está **vazio** (C.3 — depende da
      OQ2 e de imagens com licença verificada), e `api.groq.com` é inalcançável
      desta sessão. Sem casos e sem provedor, não há delta a medir. É o único
      item do gate desta fase que fica em aberto, e a dependência é da C.4.

## 7. Dúvidas para o avaliador

1. **O delta do estrato de foto é o gate declarado da fase e não é satisfazível
   hoje** — depende da C.4, que a OQ2 bloqueia. A fase pode ser aprovada com as
   correções entregues e essa medição declarada como pendência, ou a B.5 deve
   voltar a "pendente" até a C.4?
2. O texto substituto das regras 4 e 5 foi escrito por espelhamento do
   `MealParser`. Vale revisão do owner antes de a v2 entrar numa medição?

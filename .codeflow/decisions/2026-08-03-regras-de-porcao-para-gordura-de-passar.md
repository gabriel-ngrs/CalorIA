---
data: 2026-08-03
titulo: Regras próprias de porção para gordura de passar e acompanhamentos
status: ativa
tags: [nutricao, portions, eval, spec-002, fase-c6]
---

# Regras próprias de porção para gordura de passar e acompanhamentos

## Contexto

A tabela `portions` (semeada por `backend/scripts/seed_portions.py`) resolve
"1 pão com manteiga" em gramas. Quando não havia regra para o par
`(termo, unidade)`, valia a **regra genérica** de 100 g. Para um alimento que se
passa no pão isso é absurdo: 100 g de manteiga são ~720 kcal.

Medido em 2026-08-02 pela bateria de invariância da fase C.6, no grupo
`inv-04-pao-manteiga` — o pior resultado de toda a bateria:

```text
"1 pão francês com manteiga"        → 880,0 kcal
"50g de pão francês + 10g manteiga" → 212,6 kcal
spread 4,14
```

As duas descrições são a mesma refeição, então a relação metamórfica exige que
o resultado seja o mesmo. Não era. A causa não é o modelo — a IA emite
`unit="porcao"` com frequência, e era a tabela que traduzia "porção de manteiga"
como 100 g.

Esta correção **nasceu de um achado da C.6, mas tocou um arquivo que não consta
dos "Arquivos alterados" de nenhuma fase da §5** da spec 002. O DoD global exige
que toda decisão de escopo tomada durante a execução seja registrada — este
documento é esse registro. A mudança já está aplicada em `8c0c83f`; não é
proposta, é registro de algo feito fora do conjunto declarado.

## Decisão

Acrescentar **13 entradas** à tabela `PORCOES`, cobrindo `porcao`, `unidade` e
`colher_sopa` para gorduras de passar e acompanhamentos:

| termo | unidades acrescentadas | gramas |
|---|---|---|
| manteiga | `porcao`, `unidade` | 10 g |
| margarina | `ponta_faca`, `porcao`, `unidade` | 5 g / 10 g |
| requeijao | `porcao`, `unidade` | 15 g |
| geleia | `colher_sopa`, `porcao` | 20 g |
| cream cheese | `colher_sopa`, `porcao` | 15 g |
| azeite | `porcao` | 11 g |
| oleo | `porcao` | 11 g |

Nenhuma regra existente foi alterada e nenhuma entrada foi removida — a
correção é aditiva, e a regra genérica de 100 g continua valendo para todo termo
que não esteja na tabela.

## Justificativa

A alternativa seria mexer no prompt para desencorajar `unit="porcao"`, o que a
C.1 veda (mudança de texto de prompt sem bump de versão) e que contaminaria a
linha de base do eval. Corrigir a tabela ataca a causa no lugar certo: a
conversão de medida caseira em gramas é responsabilidade do `PortionNormalizer`,
não do modelo.

Os valores vêm da faixa usual de consumo, não de medição própria — por isso cada
entrada declara `gmin`/`gmax` e a faixa é verificada por teste
(`test_toda_faixa_contem_o_valor_central`).

## Consequências

- **`portions` é dado semeado em produção.** Rodar o seed altera a conversão de
  refeições cadastradas **dali em diante**; registros já gravados não mudam,
  porque a conversão acontece no momento do registro.
- Vinte testes em `backend/tests/unit/test_portions_gorduras.py` cobrem a
  tabela, inclusive `test_nenhum_par_termo_unidade_duplicado` — a coluna tem
  `unique (term, unit)` e uma duplicata derruba o seed inteiro.
- **Efeito sobre o `inv-04` ainda não foi remedido.** A bateria de invariância
  não voltou a rodar depois desta correção, por quota esgotada do free tier da
  Groq. A linha de base a comparar está em
  `FASE-C.6-invariancia-EXECUCAO.md` §5: aprovação 0,417 · spread mediano 1,2115
  · p95 3,5126, com `inv-04` em 4,14. Enquanto a remedição não sair, o efeito
  esperado desta decisão é hipótese fundamentada, não medição — mesmo estado da
  decision `2026-08-02-sanity-check-nao-descarta-fonte-curada.md`.

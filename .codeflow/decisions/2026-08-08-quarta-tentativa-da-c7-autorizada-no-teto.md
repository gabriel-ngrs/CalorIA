---
data: 2026-08-08
titulo: Owner autoriza a 4ª tentativa da C.7 no teto do §2.11.4
status: ativa
tags: [processo, spec-002, fase-c7, teto-de-tentativas, codeflow]
spec: 002-vitrine-eval-e-saneamento
fase: C.7
---

# Owner autoriza a 4ª tentativa da C.7 no teto do §2.11.4

## Contexto

A Fase C.7 chegou ao teto do ARTIFACTS_SPEC §2.11.4 — três vereditos
não-APROVADO, estado terminal de **escalação ao owner**, sem rework automático:

| Fase | `tentativa` | `reprovacoes` | Último veredito | Score |
|---|---|---|---|---|
| C.7 `eval-ci` | 3 | 2 | REPROVADO | 8.9 (threshold 8.5) |

O gate rodou, parou e escalou. Este documento registra o que o humano decidiu,
porque a constitution universal é explícita em que gate duro não admite override
**conversacional** — override genuíno exige decision registrada. É a segunda vez
nesta spec: a primeira foi a D.1 (e o encerramento da A.1) em
`2026-08-04-quarta-tentativa-da-d1-autorizada-no-teto.md`.

## Decisão

**Quarta tentativa autorizada** (owner, 2026-08-08). O rework segue o **caminho 2**
dos três que a avaliação enumerou — migração explícita, com decision registrada e
destino nomeado —, que é o recomendado pelo avaliador. Fundamentação:

1. **O veredito não é sobre o trabalho técnico da fase.** O score 8.9 ficou acima
   do threshold; a reprovação veio de um BLOQUEANTE de coerência de spec. A
   execução completa contra o provedor real aconteceu, foi registrada em
   `history.jsonl` e foi conferida pelo avaliador linha a linha contra o artefato
   versionado, não contra a prosa do relatório.
2. **O avaliador endossou a disciplina que mais importava:** os limiares do gate
   **não** foram recalibrados para o gate passar, mesmo com o gate vermelho. Esse
   é o comportamento que o escopo travado exige e o oposto do reflexo comum.
3. **O achado é fechável dentro do escopo da fase.** Corrigir a coerência entre
   §3, §5 e §9 e dar destino nomeado à cláusula não exige tocar código de
   produção nem reexecutar contra a Groq — logo não reproduz o ciclo que consumiu
   as três tentativas.
4. **As três tentativas anteriores foram gastas em modelagem, não em execução.**
   A t1 e a t2 esbarraram num gate que dependia de um efeito que só a D.2 produz
   (OQ20, o `HTTP 404` do `workflow_dispatch`); a t3 resolveu esse, e tropeçou na
   segunda cláusula que caiu junto. É o mesmo padrão da D.1 (OQ18), e encerrá-lo
   agora é o que fecha o ciclo em vez de repeti-lo.

**Consequência:** a C.7 vai a `tentativa: 4`, `reprovacoes: 3`. Se a quarta
avaliação também não aprovar, **não há autorização implícita para uma quinta** — a
fase volta à mesa do owner.

## O que fica pendente de decisão do owner

Duas coisas que a avaliação levantou e que este rework **não** decide, por serem de
owner e não de executor:

1. **Os limiares do gate.** `MDAPE_MAXIMO = 25.0` e
   `FRACAO_MINIMA_DENTRO_DE_10PCT = 0.50` foram calibrados sobre 10 casos e
   reprovam a linha de base medida dos 43 (MdAPE 33,33%; 23% dentro de ±10%). Um
   gate permanentemente vermelho para de ser lido; um gate que se ajusta ao
   resultado para de medir. A leitura registrada pelo avaliador é separar as duas
   funções: limiar de **regressão** (bloqueante, ancorado na linha de base medida)
   e **meta de qualidade** (não-bloqueante, publicada no relatório).
2. **O estrato `composto`** — MdAPE 61,64%, 6% dentro de ±10%. É o produto da
   fase, não um defeito dela, mas precisa ser olhado antes de a D.3 citar número
   de eval no README.

## Alternativas rejeitadas

1. **Encerrar a C.7 por aceite, como a A.1.** Chegaria a "fase concluída" deixando
   o AC-15 e a §9 contradizendo-se — que é literalmente o achado. Repetiria na
   próxima leitura da spec o defeito que a D.1 pagou quatro tentativas para
   eliminar.
2. **Ignorar o teto e seguir sem registro.** É o override conversacional que a
   constitution universal proíbe. O teto rodou e escalou; este registro é o que
   transforma a resposta do owner em decisão auditável.

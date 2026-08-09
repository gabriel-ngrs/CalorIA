---
data: 2026-08-04
titulo: Owner autoriza a 4ª tentativa da D.1 no teto do §2.11.4, e encerra a A.1
status: ativa
tags: [processo, spec-002, fase-a1, fase-d1, teto-de-tentativas, codeflow]
---

# Owner autoriza a 4ª tentativa da D.1 no teto do §2.11.4, e encerra a A.1

## Contexto

Duas fases da spec 002 chegaram ao teto do ARTIFACTS_SPEC §2.11.4 — três vereditos
não-APROVADO, estado terminal de **escalação ao owner**, sem rework automático:

| Fase | `tentativa` | `reprovacoes` | Último veredito | Score |
|---|---|---|---|---|
| A.1 `rotacao-credencial` | 3 | 2 | RESSALVAS | 9.2 |
| D.1 `licenca-metadados` | 3 | 2 | RESSALVAS | 9.5 |

O teto não é punição: existe para impedir que o ciclo executor↔avaliador gire sem
fim e para forçar uma decisão humana. Nos dois casos o gate rodou, parou e
escalou. Este documento registra o que o humano decidiu, porque a constitution
universal é explícita em que gate duro não admite override **conversacional** —
override genuíno exige decision registrada.

## Decisão

**A.1 — encerrada por aceite.** Decisão já tomada em 2026-08-03 (OQ13 e "Estado
final" de `2026-08-02-senha-conta-caloria-producao.md`), com a §9 do DoD já
marcando `[x]`. Em 2026-08-04 o owner autorizou refletir isso no artefato, e o
`veredito` do `FASE-A.1-…-AVALIACAO.md` passou de `RESSALVAS` para `APROVADO`.
Condição verificada antes da edição, para manter a coerência do §2.10.3 (score
9.2 ≥ 8.5, zero BLOQUEANTES, zero IMPORTANTES abertos): os dois achados
IMPORTANTES foram conferidos como fechados, arquivo a arquivo.

**D.1 — quarta tentativa autorizada.** O owner determinou executar o rework em
vez de encerrar. Fundamentação:

1. **O achado é de uma linha.** O D1-IMP-2 é a §5 da spec ainda exigindo "licença
   detectada" depois de o §3, o §8 e o §9 declararem a cláusula migrada para o
   AC-19. O próprio avaliador escreveu a redação de substituição.
2. **O trabalho técnico está completo e verificado desde a tentativa 1** —
   `LICENSE` MIT versionado, description e 6 topics na API, `0.7.0` idêntico nos
   quatro arquivos, `make check` verde. Encerrar por aceite (como na A.1) e fazer
   o rework dão o mesmo estado final; o rework deixa a spec sem contradizer a si
   mesma, que é a diferença que importa para quem ler depois.
3. **O ciclo que consumiu as três tentativas era de modelagem, não de execução.**
   O AC-18 pedia da D.1 um efeito que só a D.2 produz (OQ18). Gastar a quarta
   tentativa em algo que agora é verificável dentro do escopo da fase não
   reproduz o ciclo — encerra-o.

**Consequência:** a D.1 vai a `tentativa: 4`, `reprovacoes: 3`. Se a quarta
avaliação também não aprovar, não há autorização implícita para uma quinta — a
fase volta à mesa do owner, e desta vez sem um achado de uma linha para justificar
outra rodada.

## O que fica pendente de decisão do owner

A sugestão 4 da avaliação da D.1 aponta a questão de fundo, e ela **não** está
decidida aqui: *pode um executor migrar cláusula de AC entre fases quando ela é
comprovadamente insatisfazível no escopo declarado?* Aconteceu duas vezes nesta
spec pela mesma mecânica (AC-1 → AC-2 na A.1; AC-18 → AC-19 na D.1), e em ambas o
argumento se sustentou tecnicamente. Hoje é precedente reconstruído a cada vez.
Vale virar regra explícita — na spec ou no framework —, mas isso é evolução de
processo, não trabalho de fase.

## Alternativas rejeitadas

1. **Encerrar a D.1 por aceite, como a A.1.** Chegaria ao mesmo estado de fase e
   deixaria a §5 contradizendo o §3 — exatamente o defeito que o D1-IMP-2 nomeia,
   e que a próxima leitura da spec repetiria.
2. **Ignorar o teto e seguir sem registro.** É o override conversacional que a
   constitution universal proíbe. O teto rodou e escalou; o registro é o que
   transforma a resposta do owner em decisão auditável.

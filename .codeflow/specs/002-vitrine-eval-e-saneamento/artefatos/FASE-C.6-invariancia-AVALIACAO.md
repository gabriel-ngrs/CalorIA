---
spec: 002-vitrine-eval-e-saneamento
fase: C.6
slug_fase: invariancia
tentativa: 2
veredito: RESSALVAS
score: 9.4
threshold: 8.5
range_avaliado: e338ed4..2e6cd1d1d2a7c060d34fda9137c7aa0b25e52a6f
---

# FASE C.6 — Avaliação independente

## 1. Veredito e score

**Veredito:** RESSALVAS · **Score:** 9.4 / threshold 8.5

**O C6-IMP-2 está fechado.** A decision existe
(`decisions/2026-08-03-regras-de-porcao-para-gordura-de-passar.md`), está indexada em
`decisions/INDEX.md:13` com as cinco tags pedidas, e a spec a referencia na OQ14. O
relatório ainda corrige, para mais, um número que eu havia registrado: são **14 linhas
acrescentadas** ao `seed_portions.py` no range, não sete. Correção aceita — a minha
contagem era do diff parcial.

**O C6-IMP-1 continua aberto, e o relatório o declara com honestidade.** A medição da
fase (`aprovação 0,417 · spread mediano 1,2115 · p95 3,5126`) é anterior às duas
correções que ela mesma motivou, e a remedição não foi feita.

**Mas o impedimento declarado não se sustenta hoje, e isso eu medi.** O relatório diz
que *"rodar a bateria hoje produziria `RateLimitError`, não medição"*. Sondei o
provedor de dentro do próprio container, com uma chamada de 1 token:

```text
$ docker exec caloria_backend python -c "…AsyncGroq… max_tokens=1…"
QUOTA OK — resposta recebida: Hello
```

O provedor responde. A premissa foi verdadeira em 2026-08-02 e foi carregada para o
rework de 2026-08-03 sem ser retestada — o free tier da Groq reseta, e resetou. Não
estou afirmando que a bateria inteira completa sem esbarrar em limite de RPM; estou
afirmando que o motivo declarado para não tentar não é mais verificável, e que a
tentativa custa um comando. Ver §4.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 3 | A bateria existe, roda e produz `spread` por grupo com taxa de aprovação; o grupo do bug 001 está presente; as reprovações foram registradas como achado, não silenciadas — que é o escopo travado central da fase. Desconto: o número publicado descreve um pipeline que já mudou, e o impedimento declarado para remedi-lo não se confirma (§4) |
| 2 | Arquitetura e direção de dependências | 3 | 5 | `evals/invariance.py` reusa o runner e as métricas em vez de reimplementar; nenhuma dependência nova em direção errada |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | Grupos de invariância são descrições sintéticas de refeição; nenhum dado de usuário real entra na bateria |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | A correção do `inv-04` foi feita na tabela `portions`, que é o lugar onde a regra mora, em vez de um caso especial no parser — a decision argumenta isso e eu concordo |
| 5 | Padrões de domínio/aplicação | 2 | 5 | 14 entradas **aditivas**; nenhuma removida ou alterada. `test_nenhum_par_termo_unidade_duplicado` protege a `unique (term, unit)`, cuja violação derruba o seed inteiro |
| 6 | Local e nomes dos arquivos | 2 | 5 | `seed_portions.py` estava fora do conjunto declarado, e agora está coberto por decision + OQ14 — que era exatamente o pedido do C6-IMP-2 |
| 7 | Qualidade de código | 2 | 5 | A decision registra o defeito com número (880 kcal contra 212,6 kcal na mesma refeição), não com adjetivo |
| 8 | Testes e cobertura | 2 | 5 | `test_portions_gorduras.py` + `test_portions.py` → 78 passed (§6). A tabela nova está coberta caso a caso |
| 9 | Migration safety | 2 | [—] | `portions` é dado semeado por script, não schema; nenhuma migration tocada |

Score = (3·3 + 3·5 + 3·5 + 3·5 + 2·5 + 2·5 + 2·5 + 2·5) / 20 · 2 = 94/20 · 2 = **9.4**

## 3. Achados BLOQUEANTES

Nenhum.

**C6-IMP-2 da tentativa 1 está fechado.** Verificado nos três lugares que a correção
sugerida pedia:

```text
$ ls .codeflow/decisions/ | grep porcao
2026-08-03-regras-de-porcao-para-gordura-de-passar.md
$ grep -n "porção" .codeflow/decisions/INDEX.md
13:| 2026-08-03 | Regras próprias de porção … | ativa | nutricao, portions, eval, spec-002, fase-c6 |
$ grep -n "OQ14" .codeflow/specs/…/SPEC_002….md
   OQ14 — Regras de porção alteradas fora do conjunto declarado. RESOLVIDO (2026-08-03).
```

## 4. Achados IMPORTANTES

**C6-IMP-1 (mantido) — a medição que sustenta a fase é anterior às correções que a
própria fase motivou; e o impedimento declarado para remedi-la não vale mais.**

**Onde:** §5 do `FASE-C.6-invariancia-EXECUCAO.md` (linha de base) contra
`meal_parser.py:159` (sanity check de fonte curada) e `backend/scripts/seed_portions.py`
(14 entradas novas), ambos no range desta fase.

**O defeito, inalterado desde a tentativa 1.** O artefato afirma "7 de 12 reprovam"
sobre um pipeline em que quatro dessas sete causas foram atacadas — `inv-03`,
`inv-06`, `inv-10` e `inv-12` pelo sanity check, `inv-04` pelas regras de porção. Quem
ler o relatório depois — inclusive quem escrever o README da D.3 — parte de um número
obsoleto.

**O que mudou nesta tentativa, e é o motivo de eu manter o achado em vez de aceitá-lo
como bloqueio externo.** O relatório justifica a não-remedição assim: *"Rodar a bateria
hoje produziria `RateLimitError`, não medição."* Testei:

```text
$ docker exec caloria_backend python -c "
    AsyncGroq(...).chat.completions.create(model=llama-3.3-70b-versatile,
                                           messages=[{oi}], max_tokens=1)"
QUOTA OK — resposta recebida: Hello
```

O provedor responde agora. A afirmação era verdadeira quando escrita (2026-08-02) e
foi transportada para o rework de 2026-08-03 sem reteste — o free tier reseta por dia.
Um bloqueio externo é motivo legítimo para uma fase não fechar; um bloqueio externo
**presumido** não é, porque transforma "não deu" em "não tentei".

**Ressalva de honestidade:** uma chamada de 1 token não prova que a bateria inteira
completa sem esbarrar em RPM ou em tokens/dia. Prova que a porta está aberta. Se a
bateria estourar no meio, isso vira evidência de primeira ordem — e é exatamente o que
o risco R5 da spec quer medir.

**Correção sugerida:**

```bash
docker compose -f docker-compose.dev.yml exec -T backend python -m evals.invariance
```

Comparar contra a base declarada (**aprovação 0,417 · mediano 1,2115 · p95 3,5126**),
acrescentar a nova medição como **seção datada** no EXECUCAO da C.6 sem apagar a
antiga — a antiga é a metade "antes" da narrativa —, e reavaliar. Se a execução
estourar por limite, colar a saída do erro: isso fecha o achado por impossibilidade
**medida**, que é diferente de impossibilidade presumida.

## 5. Sugestões

- **A mesma sondagem vale para a C.7 e a C.8.** As três fases declaram o mesmo
  impedimento com a mesma data. Se a quota está de pé, as três destravam na mesma
  janela — e a janela do free tier fecha.
- **Vale registrar no relatório o método de aferir o bloqueio**, não só o bloqueio. Uma
  linha com a chamada de 1 token e sua saída transforma "falta quota" numa afirmação
  datada e reproduzível, em vez de uma impressão herdada.

## 6. Comandos rodados + saídas reais

> Gates compartilhados rodados uma vez sobre o HEAD atual (`9ef5997`), descendente do
> `sha_final` desta fase.

```text
# --- Passo 2: ancestralidade e árvore limpa ---
$ git status --porcelain | wc -l
0
$ git merge-base --is-ancestor e338ed4 HEAD                                  → ANCESTRAL
    e338ed4 feat(evals): implementa runner e metricas estratificadas do eval
$ git merge-base --is-ancestor 2e6cd1d1d2a7c060d34fda9137c7aa0b25e52a6f HEAD → ANCESTRAL

# --- C6-IMP-2: decision existe, indexada, referenciada na spec ---
$ head -5 .codeflow/decisions/2026-08-03-regras-de-porcao-para-gordura-de-passar.md
data: 2026-08-03
titulo: Regras próprias de porção para gordura de passar e acompanhamentos
status: ativa
tags: [nutricao, portions, eval, spec-002, fase-c6]                            ✓
$ grep -n "porção" .codeflow/decisions/INDEX.md
13:| 2026-08-03 | Regras próprias de porção … | ativa | …fase-c6 |             ✓

# --- a mudança em seed_portions.py, contada no diff ---
$ git diff e338ed4..HEAD -- backend/scripts/seed_portions.py | grep -c "^+.*("
14      # o relatório diz 13; o diff diz 14 — aditivas, nenhuma removida
$ docker exec caloria_backend pytest tests/unit/test_portions_gorduras.py \
                                     tests/unit/test_portions.py -q
78 passed in 0.15s                                                             ✓

# --- C6-IMP-1: o impedimento declarado, TESTADO ---
$ docker exec caloria_backend python -c "…AsyncGroq… max_tokens=1…"
QUOTA OK — resposta recebida: Hello
   → o provedor responde; "rodar hoje produziria RateLimitError" não se sustenta

# --- gates do manifest, sobre o HEAD atual ---
$ docker exec caloria_backend pytest -q --cov=app --cov=evals
620 passed, 1 skipped — Required test coverage of 72.0% reached. Total coverage: 74.28%
$ docker exec caloria_backend ruff check .          → All checks passed!
$ docker exec caloria_backend ruff format --check . → 147 files already formatted
$ docker exec caloria_backend mypy app/ evals/      → Success: no issues found in 81 source files
$ cd frontend && npm test / npm run lint / npx tsc --noEmit → 118/118 · exit 0 · exit 0

$ git status --porcelain | wc -l
0
```

## 7. Itens da fase / DoD não atendidos

| Item (§5 / §9 da spec) | Estado |
|---|---|
| Bateria de invariância metamórfica implementada | Atendido |
| AC-14 — `spread` por grupo e taxa de aprovação sob tolerância declarada | Atendido |
| Grupo do bug 001 presente na bateria | Atendido |
| Reprovações registradas como achado, não silenciadas | Atendido — é o ponto forte da fase |
| Decisão de escopo (`seed_portions.py`) registrada | Atendido nesta tentativa (decision + INDEX + OQ14) |
| **Medição vigente do pipeline atual** | **NÃO ATENDIDO** — a base publicada é anterior a duas correções desta mesma fase, e o impedimento declarado não se confirma (achado 4.1) |

## 8. Divergências entre o relatório e o código real

1. **O relatório diz 13 entradas novas; o diff mostra 14.** Diferença de contagem a
   favor do executor — ele corrigiu para cima o número que eu havia registrado (sete),
   e o diff mostra mais uma ainda. Nenhuma entrada removida ou alterada: a mudança é
   aditiva, como declarado.

2. **Divergência factual — "rodar a bateria hoje produziria `RateLimitError`".**
   Medido: o provedor responde. A afirmação era verdadeira na data em que nasceu e não
   foi retestada no rework. É o achado 4.1.

3. **Nenhuma outra divergência.** A decision descreve o defeito com os números que a
   bateria mediu, e conferem com a §5 do relatório.

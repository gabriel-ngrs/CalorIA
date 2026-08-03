---
spec: 002-vitrine-eval-e-saneamento
fase: C.5
slug_fase: runner-metricas
tentativa: 2
veredito: RESSALVAS
score: 9.5
threshold: 8.5
range_avaliado: 0d4d9ec..2e6cd1d1d2a7c060d34fda9137c7aa0b25e52a6f
---

# FASE C.5 — Avaliação independente

## 1. Veredito e score

**Veredito:** RESSALVAS · **Score:** 9.5 / threshold 8.5

**Os dois achados da tentativa 1 estão fechados, e o primeiro foi fechado com as duas
correções que a avaliação ofereceu como alternativas, não com uma.** Eu havia sugerido
*ou* forçar `repeticoes = 1` em replay *ou* publicar `origem` em vez de zeros. O
executor fez as duas:

```text
$ python -m evals.runner --cassettes --repeticoes 3 --json
amostragem     : {'temperature': 0.1, 'max_tokens': 8192, 'seed': -1, 'repeticoes': 1}
ruido_do_modelo: {"n": 0, "cv_mediano": null, "cv_maximo": null}
```

O `--repeticoes 3` vira 1 com aviso em `stderr`, e o campo de ruído publica `null` em
vez de `0.0`. Não sobra caminho pelo qual "o disco é determinístico" apareça como
medição de ruído do modelo. O C5-IMP-2 também está fechado: `evals/README.md:146-176`
tem a seção "O que a execução em replay mede — e o que ela não mede", com a distinção
pós-processamento × mudança de payload.

**O que impede o APROVADO é o mesmo defeito, sobrevivendo no campo irmão.** O `custo`
declara de onde veio (`origem: 'replay'`); a `latencia` publicada ao lado **não
declara nada**, e em replay ela mede leitura de disco. Detalhe em §4.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 5 | AC-13 verificado por execução, não por leitura (§6): MdAPE e SSPB por estrato e no agregado, `n` e IC95 por estrato, macros em `MAE em gramas, tolerancia absoluta — nunca %`. Escopo travado respeitado: MAPE não é headline; nenhum percentual para macros; as métricas são funções puras testáveis sem rede; e `tests/integration/test_golden_set.py` não recebeu **nenhum** commit no range |
| 2 | Arquitetura e direção de dependências | 3 | 5 | `repeticoes_efetivas` (`runner.py:243-255`) é função pura, testável isoladamente, com o *porquê* no docstring; a decisão não ficou enterrada dentro de `executar()` |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | O relatório publica métricas agregadas e `id` de caso; nenhuma descrição de refeição de usuário real, nenhum token. O `ContadorDeUso` observa consumo sem tocar em conteúdo |
| 4 | Reusar/espelhar, não duplicar | 3 | 4 | O contador de uso é passado como observador ao `AIClient` em vez de duplicar contabilidade (`runner.py:108`). Desconto: `resumo_do_custo(contador, origem=origem)` (`:394-405`) e `_resumo_da_latencia(resultados)` (`:408`) são irmãos no mesmo arquivo e só o primeiro declara a origem — espelhar o padrão teria evitado o achado 4.1 |
| 5 | Padrões de domínio/aplicação | 2 | 5 | Estrato vazio vira `n=0` em vez de sumir (`resumir`, `:258-259`), e o relatório imprime `foto 0 (vazio)` — decisão certa para um dataset que ainda não tem o estrato |
| 6 | Local e nomes dos arquivos | 2 | 5 | Exatamente os arquivos declarados na §5 |
| 7 | Qualidade de código | 2 | 5 | Os docstrings registram o *porquê* não-óbvio (por que repetir em replay não mede nada; por que a origem importa tanto quanto o número) |
| 8 | Testes e cobertura | 2 | 4 | `repeticoes_efetivas` coberto nos quatro casos de fronteira (`test_evals_snapshot.py:274-293`), e `test_a_origem_do_custo_acompanha_o_numero` trava a origem do custo. Desconto: não há o teste equivalente para a latência — que é justamente o campo do achado 4.1 |
| 9 | Migration safety | 2 | [—] | Nenhuma migration tocada |

Score = (3·5 + 3·5 + 3·5 + 3·4 + 2·5 + 2·5 + 2·5 + 2·4) / 20 · 2 = 95/20 · 2 = **9.5**

## 3. Achados BLOQUEANTES

Nenhum.

Os dois achados da tentativa 1 estão fechados e verificados por execução (§6):
**C5-IMP-1** (CV zero por construção em replay) e **C5-IMP-2** (limitação do replay
não documentada).

## 4. Achados IMPORTANTES

**C5-IMP-3 — `backend/evals/runner.py:408-411`: a latência é publicada sem declarar a
origem, e em replay ela mede o disco. É o defeito do C5-IMP-1 no campo irmão.**

**Onde:** `_resumo_da_latencia` (`runner.py:408`) contra `resumo_do_custo`
(`runner.py:394-405`), que recebe `origem` e a publica.

**O defeito.** Rodei o runner em replay:

```text
custo       : {'chamadas': 0, 'tokens_in': 0, 'tokens_out': 0, 'origem': 'replay'}
latencia    : {'n': 10, 'mediana_s': 0.073, 'total_s': 0.92}
```

`0,073 s` é o tempo de ler um cassette do disco, não o tempo de resposta do provedor.
O `custo` ao lado se protege: declara `origem: 'replay'`, e os zeros ficam
autoexplicativos. A `latencia` publica um número plausível **sem marcação nenhuma**.
O docstring reforça a leitura errada: *"Tempo de parede por caso: mediana e total da
execução"* — verdadeiro, e é justamente por isso que engana.

**Cenário de falha concreto, e é o que torna isto mais que cosmético.** O campo é
propagado para a linha do histórico da C.8 (`report.py`, coberto por
`test_a_linha_registra_tokens_e_latencia`). Hoje as três linhas gravadas têm
`latencia: null`, porque são anteriores ao campo — verifiquei. A próxima execução em
replay que rodar `evals.report registrar` grava `mediana_s: 0.073`; uma execução com
`EVAL_RECORD_CASSETTES=1` grava algo na casa dos segundos. As duas entram na **mesma
série append-only**, sem nada que as distinga, e a diferença de ~34× lê-se como ganho
de performance que nunca existiu. Append-only significa que a linha errada não sai
depois.

E é o cenário provável: replay é a forma barata de rodar, e o README a incentiva.

**Por que não é BLOQUEANTE.** Nada está incorreto no cálculo, o histórico ainda não
foi contaminado, e a correção é de poucas linhas.

**Correção sugerida** — espelhar o que o `custo` já faz:

1. `_resumo_da_latencia(resultados, *, origem: str)` e incluir `"origem": origem` no
   dicionário, passando o mesmo valor que `resumo_do_custo` recebe em `:537`.
2. Um teste irmão de `test_a_origem_do_custo_acompanha_o_numero` para a latência.
3. Opcionalmente, `mediana_s: None` quando `origem == "replay"` — a latência de disco
   não é informação sobre o pipeline, e `null` é mais honesto que um número certo
   sobre a coisa errada. Foi o caminho adotado para `ruido_do_modelo`, e vale a mesma
   lógica.

## 5. Sugestões

- **O texto do relatório imprime `repeticoes: 1` sem repetir o aviso.** O aviso vai
  para `stderr` e some quando alguém redireciona só `stdout` (que é o caso de
  `--json | tee`). Como o campo `amostragem.repeticoes` já carrega o valor efetivo,
  um `repeticoes_solicitadas` ao lado tornaria a redução visível no próprio artefato,
  não só no terminal de quem rodou.
- **`latencia.n` e `agregado.n` são coisas diferentes com o mesmo nome.** O primeiro
  conta casos com tempo medido, o segundo conta casos válidos para a métrica. Hoje
  coincidem em 10; quando um caso falhar, não vão coincidir, e a leitura fica
  ambígua.

## 6. Comandos rodados + saídas reais

> Gates compartilhados rodados uma vez sobre o HEAD atual (`bcaf397`), descendente do
> `sha_final` desta fase.

```text
# --- Passo 2: ancestralidade e árvore limpa ---
$ git status --porcelain | wc -l
0
$ git merge-base --is-ancestor 0d4d9ec HEAD                                  → ANCESTRAL
    0d4d9ec feat(evals): cria o esqueleto do harness e o contrato do caso de eval
$ git merge-base --is-ancestor 2e6cd1d1d2a7c060d34fda9137c7aa0b25e52a6f HEAD → ANCESTRAL

# --- escopo travado: limiares do golden set intocados ---
$ git log --oneline e338ed4..HEAD -- backend/tests/integration/test_golden_set.py
(vazio — nenhum commit)                                                       ✓

# --- C5-IMP-1 fechado: as DUAS correções sugeridas, verificadas por execução ---
$ docker exec caloria_backend python -m evals.runner --cassettes --repeticoes 3 --json
amostragem     : {'temperature': 0.1, 'max_tokens': 8192, 'seed': -1, 'repeticoes': 1}
ruido_do_modelo: {"n": 0, "cv_mediano": null, "cv_maximo": null}
   → --repeticoes 3 reduzido a 1; ruído publica null, não 0.0                 ✓
$ sed -n '253,255p' backend/evals/runner.py
    if usar_cassettes and not gravacao_ligada() and repeticoes > 1:
        return 1
$ grep -rn "repeticoes_efetivas" backend/tests/
tests/unit/test_evals_snapshot.py:274  assert repeticoes_efetivas(3, usar_cassettes=True) == 1
tests/unit/test_evals_snapshot.py:281  assert repeticoes_efetivas(3, usar_cassettes=True) == 3   # gravando
tests/unit/test_evals_snapshot.py:287  assert repeticoes_efetivas(3, usar_cassettes=False) == 3
tests/unit/test_evals_snapshot.py:293  assert repeticoes_efetivas(1, usar_cassettes=True) == 1   ✓

# --- C5-IMP-2 fechado ---
$ grep -n "^## " backend/evals/README.md | sed -n '6p'
146:## O que a execução em replay mede — e o que ela não mede                  ✓

# --- AC-13, verificado no relatório real ---
$ docker exec caloria_backend python -m evals.runner --cassettes
estrato         n    MdAPE               IC95      SSPB   <=10%
simples         6    1.26% [  0.00,   5.71]     1.25%   100%
composto        4    6.86% [  0.00,  30.95]    -3.13%    75%
foto            0   (vazio)
AGREGADO       10    3.89% [  0.00,   6.16]     0.00%    90%
macros (MAE em gramas, tolerancia absoluta — nunca %):
  proteina_g     MAE=  0.99 g   dentro de ±5 g: 100%                          ✓

# --- o achado 4.1 ---
custo       : {'chamadas': 0, 'tokens_in': 0, 'tokens_out': 0, 'origem': 'replay'}
latencia    : {'n': 10, 'mediana_s': 0.073, 'total_s': 0.92}   ← sem origem
$ grep -rn "latencia.*origem\|origem.*latencia" backend/
(vazio — o campo não existe em lugar nenhum)
$ python3 -c "…history.jsonl…"
1 cc849e7172fe-426cb61 custo= null latencia= null
2 f479f5dfa9a0-426cb61 custo= null latencia= null
3 298d79939a66-426cb61 custo= null latencia= null
   → série ainda não contaminada; a próxima gravação em replay a contamina

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
| Passo 1 — métricas puras (APE, MdAPE, SSPB, tolerância, MAE, IC95) | Atendido |
| Passo 2 — runner com pipeline real e estágios intermediários | Atendido |
| Passo 3 — kcal em MdAPE/SSPB, macros em MAE absoluto | Atendido, verificado na saída |
| Passo 4 — relatório em texto e JSON | Atendido, ambos exercitados |
| AC-13 — `n` e IC95 por estrato, macros nunca em percentual | Atendido |
| Gate — relatório com os três estratos, `n` e IC95 | Atendido (`foto` aparece com `n=0`, não some) |
| **Honestidade de origem dos números publicados** | **PARCIAL** — resolvida para ruído e custo, ausente na latência (achado 4.1) |

## 8. Divergências entre o relatório e o código real

1. **Nenhuma divergência no que o relatório afirma.** As duas correções estão no código
   e funcionam; verifiquei por execução, não por leitura do diff.

2. **O relatório declara "custo com origem declarada e latencia no relatório"** como um
   item só. São dois campos com tratamento diferente, e a diferença é o achado 4.1 — a
   redação conjunta esconde que só um deles ganhou origem.

3. **`ruido_do_modelo` publica `null` além da redução de repetições.** O relatório
   descreve a redução, não a mudança de `0.0` para `null`. É entrega **acima** do
   declarado, não abaixo — registro porque melhora a fase e não estava no texto.

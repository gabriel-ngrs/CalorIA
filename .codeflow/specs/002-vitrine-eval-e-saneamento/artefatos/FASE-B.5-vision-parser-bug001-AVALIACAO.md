---
spec: 002-vitrine-eval-e-saneamento
fase: B.5
slug_fase: vision-parser-bug001
tentativa: 2
veredito: RESSALVAS
score: 9.7
threshold: 8.5
range_avaliado: 36d68cc..b8001c3
---

# FASE B.5 — Avaliação independente

## 1. Veredito e score

**Veredito:** RESSALVAS · **Score:** 9.7 / threshold 8.5

**O achado que segurava a fase caiu, e caiu por medição.** O B5-IMP-1 da tentativa 1
era "o delta do estrato de foto não existe". Agora existe: o runner executa o
estrato de foto pelo `VisionParser` de produção, e o delta v1→v2 está no relatório
com quatro execuções contra o provedor real. Verifiquei o código linha a linha, os
testes rodam verdes aqui, e o escopo travado foi respeitado — `vision_parser.py`,
`meal_parser.py` e os limiares de 2026-07-26 não têm uma linha alterada nesta
tentativa (`git show b8001c3 --stat`: só `runner.py` e o arquivo de teste novo).

**A conclusão do delta é honesta e eu a endosso:** MdAPE 52,17% e SSPB +52,17% nas
quatro execuções, IC95 sobrepostos, `n = 3`. Não há delta separável do ruído, e o
relatório diz isso em vez de vender melhora. É o desfecho que a própria §5 da spec
previa ("ou, se não melhorar, o achado é registrado com os números").

**O que impede o APROVADO é um efeito colateral desta tentativa:** o README do
harness (`backend/evals/README.md`), que é a peça onde a C.3 declara o que o eval
mede e o que **não** mede, ficou factualmente falso em dois pontos ao afirmar que o
runner não executa o estrato de foto — exatamente o que esta fase mudou. É a mesma
classe de defeito que custou quatro tentativas à D.1 (documento contradizendo o
estado real), e por isso não a trato como cosmética.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 4 | Gate "delta registrado com números" atendido (EXECUCAO §5.1). Escopo travado intacto: `git show b8001c3 --stat` toca só `backend/evals/runner.py` e `backend/tests/unit/test_evals_runner_foto.py`. Desconto: `backend/evals/README.md:23-25,135` ficou falso (§4) |
| 2 | Arquitetura e direção de dependências | 3 | 5 | `runner.py:196-213` `versao_de_visao()` troca e restaura `_IDENTIFY_PROMPT` sem tocar `VERSOES_EM_PRODUCAO` — medir não exige promover; `runner.py:216-231` `identificar()` roteia por estrato |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | `gitleaks detect --config .gitleaks.toml` → 496 commits, no leaks (§6). Relatórios de eval carregam só contagem de tokens; nenhuma imagem ou PII nova |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | `runner.py:229` chama o `VisionParser` de produção (`foto._identify_foods`), não uma reimplementação; o padrão global-e-restaurado espelha `instrumentar_lookup`, no mesmo arquivo |
| 5 | Padrões de domínio/aplicação | 2 | 5 | Identificadores em pt-BR, como o princípio 8 da spec fixou para `backend/evals/`; `_prompts_usados()` lê do módulo (`runner.py:452-469`) para não atribuir resultado da v1 ao `sha` da v2 |
| 6 | Local e nomes dos arquivos | 2 | 5 | Teste em `backend/tests/unit/test_evals_runner_foto.py`, junto dos demais `test_evals_*`; nomes de teste descrevem comportamento, não implementação |
| 7 | Qualidade de código | 2 | 5 | `ruff check` + `ruff format --check` + `mypy app/ evals/` limpos (§6); comentários explicam o "por quê" (`runner.py:249-250`, `:637-638`), não o "o quê" |
| 8 | Testes e cobertura | 2 | 5 | 13 testes rodados por mim em 0,19 s; cobrem roteamento por estrato, imagem ausente, restauração sob exceção e procedência do prompt no relatório |
| 9 | Migration safety (se aplicável) | 2 | [—] | Nenhuma migration no diff (NFR-7 preservada) |

Score = 97 / 20 × 2 = **9.7**.

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

### B5-IMP-2 — o README do harness afirma o oposto do que o runner faz agora

`backend/evals/README.md:23-25`:

> - **O comportamento com foto.** O estrato `foto` existe desde a C.4, mas o runner
>   de texto não o executa — quem mede o caminho de imagem é a fase B.5 (ver
>   "Estado do dataset").

`backend/evals/README.md:135`:

> O runner ignora o estrato `foto` (`runner.py`): o caminho de imagem entra na fase
> B.5, que é quem mede o `VisionParser`.

Os dois eram verdadeiros até `b8001c3` e deixaram de ser **nele**. O primeiro está
dentro da lista *"o que este eval NÃO mede"* — a seção que o próprio README
apresenta como seu padrão de honestidade —, o que torna o erro pior do que uma
desatualização qualquer: o documento hoje nega uma capacidade que o harness tem, e
quem confiar nele concluirá que o caminho de foto segue sem instrumento.

**Correção sugerida** (diff mínimo, sem tocar código):

- `:23-25` — substituir por algo como: *"**O caminho de foto entra pelo `VisionParser`
  desde a B.5** (`runner.py`), com `n = 3` — o estrato menor e mais frágil do
  dataset. Na configuração de produção ele falha com HTTP 413 (OQ19), então nenhum
  número dele vale como linha de base de produção enquanto isso durar."*
- `:135` — descrever o estado atual e citar `--versao-vision` como a forma de medir
  uma versão sem promovê-la.

Já que a varredura será aberta, vale aplicá-la à classe inteira, como o avaliador da
D.1 pediu na tentativa 3: `grep -rn "foto" backend/evals/README.md` e
`grep -rn "fase B.5\|B\.5" backend/ docs/` devolvem os pontos a conferir.

## 5. Sugestões

1. **As quatro execuções do delta não sobrevivem à sessão.**
   `backend/evals/runs/ultimo-relatorio.json` está em `.gitignore:139` e é
   sobrescrito a cada rodada; as quatro linhas da §5.1 existem só em prosa.
   Respondendo à **dúvida 3** do relatório: **não** registraria em `history.jsonl` —
   o campo `amostragem` até carrega o `max_tokens`, mas a série da C.8 é lida como
   "a linha do tempo da configuração de produção", e quatro pontos a 2048 a
   contaminam. Melhor anexar os quatro JSON como artefato da fase
   (`artefatos/B.5-delta-foto-v<N>-r<R>.json`): versionado, auditável, e sem mentir
   sobre ser produção.
2. **Dúvida 1 (o HTTP 413).** Concordo com não ter corrigido — o fix mora em
   `config.py`/`ai_client.py` e no frontend, e ampliar a B.5 violaria o escopo
   travado. Minha recomendação ao owner é **fase nova**, não rework da C.2: a C.2
   está aprovada e fechada, o defeito tem duas frentes (teto de tokens da visão **e**
   redimensionamento no cliente), e uma fase própria deixa rastro na §5 em vez de
   reabrir fase concluída. A OQ19 já traz o diagnóstico pronto.
3. **Dúvida 2 (`n = 3` antes de a D.3 citar números).** Sim, vale crescer o estrato —
   mas depois do 413: mais casos sob `GROQ_MAX_TOKENS=2048` só aumentam o `n` de uma
   configuração que não é a de produção.
4. **`VisionParser(cliente)` é instanciado mesmo sem caso de foto** (`runner.py:626`).
   Inofensivo hoje (o construtor não faz I/O); se um dia fizer, execuções só de texto
   passam a pagar por isso.
5. **Dúvida 4 (o `range` não isola a fase).** Está certo como está — o §2.9.3 manda
   ir do `sha_inicial` original ao HEAD. Avaliei por conteúdo, atribuindo cada commit
   à fase que o declara.

## 6. Comandos rodados + saídas reais

```text
$ git merge-base --is-ancestor b8001c3 HEAD && echo "b8001c3 ANCESTRAL OK"
b8001c3 ANCESTRAL OK

$ git show b8001c3 --stat
 backend/evals/runner.py                      | 162 +++++++++++++++----
 backend/tests/unit/test_evals_runner_foto.py | 229 +++++++++++++++++++++++++++
 2 files changed, 363 insertions(+), 28 deletions(-)
   → `vision_parser.py`, `meal_parser.py` e os prompts NÃO estão no diff:
     o escopo travado da fase foi respeitado

$ docker compose -f docker-compose.dev.yml exec -T backend sh -c \
    "ruff check . && ruff format --check . && mypy app/ evals/"
All checks passed!
149 files already formatted
Success: no issues found in 81 source files

$ docker compose -f docker-compose.dev.yml exec -T backend pytest tests/unit -q
496 passed, 3 skipped in 4.01s

$ docker compose -f docker-compose.dev.yml exec -T backend \
    pytest tests/unit/test_evals_snapshot.py tests/unit/test_evals_runner_foto.py \
           tests/unit/test_seed_demo.py -q
46 passed, 3 skipped in 0.19s
   → os 3 pulados são os de coerência README×script da E.3, que o container não
     alcança (monta só `backend/`); nenhum é desta fase

$ docker compose -f docker-compose.dev.yml exec -T backend pytest tests/integration/ -q
145 passed, 5 warnings in 86.98s
   → o relatório marcou `[—]`; rodei mesmo assim e está verde

$ gitleaks detect --source . --config .gitleaks.toml --redact --no-banner --exit-code 1
496 commits scanned. no leaks found                    >>> EXIT=0

$ bash ~/.codeflow/framework/core/scripts/run-structural.sh \
    .codeflow/specs/002-vitrine-eval-e-saneamento/SPEC_002_VITRINE_EVAL_E_SANEAMENTO.md
✓ §5 estruturalmente válida                            >>> EXIT=0

# --- o achado do §4, medido ---
$ grep -n "ignora o estrato\|não o executa" backend/evals/README.md
23:- **O comportamento com foto.** O estrato `foto` existe desde a C.4, mas o runner
24:  de texto não o executa — quem mede o caminho de imagem é a fase B.5
135:O runner ignora o estrato `foto` (`runner.py`): o caminho de imagem entra na fase

# --- o 413 do EXECUCAO §5.2, confirmado em artefato versionado ---
$ python3 -c "import json;print(json.loads(open('backend/evals/runs/history.jsonl').read().splitlines()[-1])['falhas'][0]['erro'][:160])"
APIStatusError: Error code: 413 - Request too large for model `qwen/qwen3.6-27b` …
  on tokens per minute (TPM): Limit 8000, Requested 11508

$ git status --short
(vazio — árvore limpa ao fim da avaliação)
```

**Não rodei:** `npm run lint` / `npx tsc --noEmit` — nenhum arquivo de frontend no
diff desta tentativa. `[—]` justificado.

## 7. Itens da fase / DoD não atendidos

| Item (§5 / §9) | Estado |
|---|---|
| AC-17 — nenhum item perdido em silêncio | ✓ verificado na t1; código inalterado |
| AC-17 — quantidade por extenso não vira 500 | ✓ idem |
| AC-17 — prompt de visão sem as regras 4 e 5 | ✓ idem |
| Passo 5 / gate — delta do estrato de foto com números antes e depois | ✓ EXECUCAO §5.1, quatro execuções reais |
| §9 global — decisão de escopo registrada em §8 ou decision | ✓ OQ19 + decision de 2026-08-04 |
| §9 global — documentação coerente com o estado real | ✗ `backend/evals/README.md` (§4) |

O desvio de arquivo (`runner.py` fora dos "Arquivos alterados" da fase) **não** é
achado: a linha removida era `if c.estrato is not Estrato.FOTO  # o caminho de foto
entra na fase B.5`, escrita pela C.5 para atribuir esse trabalho a esta fase, e a
extensão está registrada em OQ19 e em decision, como o §9 global exige.

## 8. Divergências entre o relatório e o código real

Nenhuma divergência material. Duas notas de precisão:

1. **"489 passed"** (EXECUCAO §5.3) contra **496 passed, 3 skipped** aqui — os 7 a
   mais são testes da E.3, commitados depois de `b8001c3`. Idem "148 files already
   formatted" × 149.
2. **`Requested 11357`** (EXECUCAO §5.2) contra **`Requested 11508`** no
   `history.jsonl`: execuções diferentes. O ponto do achado — número idêntico entre
   imagens de 111 KB e 291 KB, logo o custo é o `max_tokens` reservado e não o
   tamanho da foto — se sustenta nas duas.

O que **não pude verificar** foram as quatro linhas da tabela do delta (§5.1): o
`ultimo-relatorio.json` é ignorado pelo git e foi sobrescrito pela execução da C.7.
Verifiquei o que as cerca — o código que as produz, o `413` no artefato versionado,
a coerência interna da tabela — e nada as contradiz. É o motivo da sugestão 1.

---

**Próximo passo:** RESSALVAS **não** conclui a fase (ARTIFACTS_SPEC §2.11.3). Colar
esta avaliação no chat executor, corrigir o B5-IMP-2 e reavaliar em chat zerado.
**Atenção ao teto:** o EXECUCAO traz `reprovacoes: 1`; este veredito leva a `2`, e o
§2.11.4 manda parar e escalar ao owner antes de uma quarta tentativa. A correção
pedida aqui são duas frases num README — cabe folgada na terceira.

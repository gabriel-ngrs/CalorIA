---
spec: 002-vitrine-eval-e-saneamento
fase: C.8
slug_fase: historico-eval
tentativa: 2
veredito: RESSALVAS
score: 9.4
threshold: 8.5
range_avaliado: 40e2941..2e6cd1d1d2a7c060d34fda9137c7aa0b25e52a6f
---

# FASE C.8 — Avaliação independente

## 1. Veredito e score

**Veredito:** RESSALVAS · **Score:** 9.4 / threshold 8.5

**O C8-IMP-2 está fechado, e a solução é melhor que a que eu havia sugerido.** Eu
apontei o `AIClientComCassette` como ponto natural para acumular tokens; o executor
descobriu que ele **não enxerga** o `usage` da resposta, que morre dentro do
`AIClient`, e resolveu com um observador opcional (`UsoDaChamada`) no cliente. Produção
não passa observador e o caminho não depende dele — há teste para isso. É a correção
certa pelo motivo certo, e o diagnóstico do porquê a minha sugestão não funcionaria
está no relatório.

Detalhe que merece registro: `montar_linha` propaga os campos novos com `.get`, de modo
que as três linhas já gravadas ficam com `null` — que diz *"não medido"* — em vez de `0`,
que diria *"não custou nada"*. Verifiquei as três: `custo: null, latencia: null`. A
distinção é exatamente do tipo que costuma ser perdida, e há teste travando-a.

**O C8-IMP-1 continua aberto**, e o gerador de série temporal o exibe sozinho:

```text
commit           n    MdAPE     SSPB   <=10%  prompts
cc849e7172fe    10    3.89%    1.25%    70%  meal_fallback@v1 meal_identify@v1
f479f5dfa9a0    10    3.89%    1.25%    70%  meal_fallback@v1 meal_identify@v1   ← idêntica
298d79939a66    10    3.89%    0.00%    90%  meal_fallback@v1 meal_identify@v1
```

Duas linhas, quatro métricas, zero diferença. O gate é *"histórico com ao menos duas
execuções reais"* e há uma medição gravada duas vezes mais uma legítima.

**E o impedimento declarado não se sustenta hoje.** O relatório diz *"isso exige quota,
e a quota está esgotada"*. Sondei o provedor: responde. Ver §4.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 3 | AC-16 verificado linha a linha: cada registro amarra `git_commit`, `prompts` com versão **e** `sha`, `modelo`, `dataset_sha` e `n` (§6). Escopo travado respeitado nos três itens: append-only preservado (a linha duplicada **não** foi removida, o que é a conduta certa), zero credencial/PII no arquivo, e o gráfico é texto puro sem serviço externo. Desconto: o gate "duas execuções reais" não está satisfeito (§4) |
| 2 | Arquitetura e direção de dependências | 3 | 5 | O observador de consumo é **opcional** no `AIClient` (`UsoDaChamada`, frozen dataclass): produção não passa nada e o caminho não depende dele, com teste cobrindo. Instrumentar sem acoplar é o desenho certo — o eval observa o pipeline, o pipeline não conhece o eval |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | `grep -ciE "gsk_\|api_key\|password\|senha\|@gmail" history.jsonl` → **0**. O registro guarda métricas, `sha` e identificadores; nenhuma descrição de refeição, nenhum segredo |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | `montar_linha` reusa o relatório do runner em vez de recalcular; a propagação por `.get` faz o schema evoluir sem reescrever histórico. (A ausência de `origem` na latência é achado da C.5, onde o campo nasce — não conto duas vezes) |
| 5 | Padrões de domínio/aplicação | 2 | 5 | `null` para "não medido" contra `0` para "não custou" é a distinção certa, e está travada por teste (`test_evals_report.py:216-219`) |
| 6 | Local e nomes dos arquivos | 2 | 5 | Exatamente os arquivos declarados na §5 |
| 7 | Qualidade de código | 2 | 5 | A regra de imutabilidade (passo 3) está no README **e** imposta pela suíte — "o `sha256` de cada versão ativa está travado em `test_prompt_registry.py`, então a regra é imposta pela suíte, não pela disciplina de quem edita". Regra que vira asserção |
| 8 | Testes e cobertura | 2 | 5 | `test_evals_report.py` → 20 passed, cobrindo tokens, latência, origem do custo e o caso "relatório antigo sem os campos" |
| 9 | Migration safety | 2 | [—] | Nenhuma migration tocada |

Score = (3·3 + 3·5 + 3·5 + 3·5 + 2·5 + 2·5 + 2·5 + 2·5) / 20 · 2 = 94/20 · 2 = **9.4**

## 3. Achados BLOQUEANTES

Nenhum.

**C8-IMP-2 da tentativa 1 está fechado.** Verificado no código e por execução:

```text
$ docker exec caloria_backend pytest tests/unit/test_evals_report.py -q
20 passed in 0.06s
$ python3 -c "…history.jsonl linhas 1-3…"
custo= null  latencia= null      # anteriores à instrumentação, e assim declaradas
```

## 4. Achados IMPORTANTES

**C8-IMP-1 (mantido) — as duas "execuções reais" continuam sendo a mesma medição; e o
impedimento declarado para corrigi-lo não vale mais.**

**Onde:** `backend/evals/runs/history.jsonl:1-2`, contra o Critério de conclusão da
Fase C.8 (*"histórico com ao menos duas execuções reais"*) e §9 do DoD (*"C.8 — AC-16;
histórico com ao menos duas execuções reais"*).

**O defeito, inalterado.** O gerador de série temporal o mostra sem que eu precise
argumentar: as linhas `cc849e71` e `f479f5df` têm `n`, MdAPE, SSPB e `<=10%` idênticos,
porque saíram do mesmo `/tmp/rel.json` registrado duas vezes com `--git-commit`
diferente. O `run_id` (`commit[:12]-dataset_sha[:12]`) foi projetado para dizer "mesma
medição do mesmo commit sobre o mesmo dataset"; aqui duas medições idênticas ganharam
`run_id` distintos porque o commit foi passado à mão, e o campo perdeu a propriedade que
o justifica.

**A conduta do executor nesta tentativa está certa e registro isso:** ele **não** removeu
a linha 2. Remover colidiria com o append-only, que é a propriedade que o arquivo existe
para ter, e eu havia dito preferir a outra saída. Manter foi a escolha correta.

**O que mudou.** O relatório justifica: *"Isso exige quota, e a quota está esgotada."*
Testei, do próprio container:

```text
$ docker exec caloria_backend python -c "…AsyncGroq… max_tokens=1…"
QUOTA OK — resposta recebida: Hello
```

A premissa era verdadeira em 2026-08-02 e foi transportada para o rework de 2026-08-03
sem reteste — o free tier reseta por dia. Mantenho o achado não porque o executor tenha
agido mal, mas porque o item segue aberto e o motivo declarado para não fechá-lo não é
mais verificável.

**Ressalva:** uma chamada de 1 token não prova que a execução completa dos 10 casos
termina sem esbarrar em RPM. Prova que a porta está aberta.

**Por que não é BLOQUEANTE.** O código está correto, o append-only foi preservado, o
histórico não tem dado errado — tem uma linha redundante, cuja natureza está agora
documentada. Falta uma execução.

**Correção sugerida** — a saída que o próprio relatório já deixou pronta, enquanto a
janela de quota estiver aberta:

```bash
docker compose -f docker-compose.dev.yml exec -T backend python -m evals.runner --json > /tmp/rel.json
docker compose -f docker-compose.dev.yml exec -T backend python -m evals.report registrar \
  --relatorio /tmp/rel.json --git-commit $(git rev-parse HEAD)
```

A linha nova nasce com `custo` e `latencia` preenchidos, o que a torna distinguível das
anteriores por mais do que o `run_id` — efeito colateral bem-vindo da correção do
C8-IMP-2. Se a execução estourar por 429, colar a saída: fecha o item por
impossibilidade **medida**, e alimenta a decisão de periodicidade da C.7.

## 5. Sugestões

- **A latência entra nesta série sem declarar origem** — é o achado `C5-IMP-3`, aberto
  na avaliação da C.5, onde o campo nasce (`runner.py:408`). Registro aqui porque é
  **neste** arquivo que a consequência se materializa: `montar_linha` propaga o valor
  para um `.jsonl` **append-only**, e uma linha gravada em replay (`mediana_s ≈ 0,07`)
  ficaria lado a lado com uma de provedor (casa dos segundos) sem nada que as
  distinga — uma diferença de ~34× que se lê como ganho de performance. Vale corrigir a
  origem **antes** de gravar a execução que fecha o C8-IMP-1, porque depois a linha não
  sai.
- **`serie_temporal` não marca visualmente a troca de versão de prompt.** A coluna
  `prompts` mostra `meal_identify@v1` em todas as linhas, o que hoje é verdade; quando a
  promoção da C.2 acontecer, um marcador (`←` ou linha separadora) tornaria o ponto de
  virada legível, que é o propósito declarado do passo 2 ("anotada com o ponto em que
  cada versão de prompt entrou").
- **`casos_nao_verificados` e `invariancia` aparecem na linha e não estão no passo 1.**
  São entrega acima do declarado e úteis; vale mencioná-los no README do harness para
  que quem consuma o `.jsonl` saiba que existem.

## 6. Comandos rodados + saídas reais

> Gates compartilhados rodados uma vez sobre o HEAD atual (`fe40a57`), descendente do
> `sha_final` desta fase.

```text
# --- Passo 2: ancestralidade e árvore limpa ---
$ git status --porcelain | wc -l
0
$ git merge-base --is-ancestor 40e2941 HEAD                                  → ANCESTRAL
    40e2941 fix(ai): propaga a correcao do bug 001 ao VisionParser
$ git merge-base --is-ancestor 2e6cd1d1d2a7c060d34fda9137c7aa0b25e52a6f HEAD → ANCESTRAL

# --- AC-16: cada linha amarra o que o AC exige ---
$ python3 -c "…json.loads(linha 3)…"
chaves: ['agregado','amostragem','casos_nao_verificados','dataset_distribuicao',
         'dataset_n','dataset_sha','falhas','git_commit','invariancia','modelo',
         'por_estrato','prompts','run_id']
git_commit: 298d79939a66 | modelo: llama-3.3-70b-versatile
dataset_sha: 426cb61f64af | n: 10
prompts: {'meal_fallback': (1,'713ea1c5'), 'meal_identify': (1,'f1334ef6')}    ✓

# --- C8-IMP-2 fechado: custo/latencia no schema, null nas linhas antigas ---
$ docker exec caloria_backend pytest tests/unit/test_evals_report.py -q
20 passed in 0.06s                                                             ✓
$ python3 -c "…history.jsonl…"
1 cc849e7172fe-426cb61 custo= null latencia= null
2 f479f5dfa9a0-426cb61 custo= null latencia= null
3 298d79939a66-426cb61 custo= null latencia= null
   → `null` = "não medido", não `0` = "não custou"                             ✓

# --- passo 2: relatório gerado a partir do histórico, sem rede ---
$ docker exec caloria_backend python -m evals.report serie
SÉRIE TEMPORAL DO EVAL
commit           n    MdAPE     SSPB   <=10%  prompts
cc849e7172fe    10    3.89%    1.25%    70%  meal_fallback@v1 meal_identify@v1
f479f5dfa9a0    10    3.89%    1.25%    70%  meal_fallback@v1 meal_identify@v1
298d79939a66    10    3.89%    0.00%    90%  meal_fallback@v1 meal_identify@v1
   → o achado 4.1 é visível na própria saída: linhas 1 e 2 idênticas

# --- passo 3: imutabilidade documentada E imposta ---
$ sed -n '177,184p' backend/evals/README.md
## Imutabilidade de versão de prompt
Um arquivo de versão … **não é editado** depois de ter uma execução de eval
associada. … O `sha256` de cada versão ativa está travado em
`tests/unit/test_prompt_registry.py`, então a regra é imposta pela suíte.        ✓

# --- escopo travado: sem credencial nem PII no registro ---
$ grep -ciE "gsk_|api_key|password|senha|@gmail" backend/evals/runs/history.jsonl
0                                                                              ✓

# --- o impedimento declarado, testado ---
$ docker exec caloria_backend python -c "…AsyncGroq… max_tokens=1…"
QUOTA OK — resposta recebida: Hello
   → "a quota está esgotada" não se sustenta hoje

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
| Passo 1 — linha amarrando run_id, commit, prompts+sha, modelo, dataset, métricas | Atendido |
| Passo 1 — **custo em tokens e latência** | Atendido nesta tentativa (observador opcional no `AIClient`) |
| Passo 2 — gerador de série temporal a partir do histórico, sem rede | Atendido |
| Passo 3 — regra de imutabilidade no README | Atendido, e imposta por teste |
| AC-16 — cada linha rastreável a commit/prompt/modelo/dataset | Atendido |
| Escopo travado — append-only, sem credencial/PII, sem serviço externo | Atendido nos três |
| **Gate — histórico com ao menos duas execuções reais** | **NÃO ATENDIDO** — uma medição gravada duas vezes + uma legítima (achado 4.1) |

## 8. Divergências entre o relatório e o código real

1. **Nenhuma divergência no código.** O observador existe, é opcional, produção não o usa,
   e os campos entram na linha com `.get`.

2. **Divergência factual — "a quota está esgotada".** Medido: o provedor responde. Mesma
   premissa herdada que aparece na C.6 e na C.7, com a mesma data de origem.

3. **O relatório cita `latencia mediana_s: 0.058` e eu medi `0.073` numa execução
   posterior.** Não é divergência — é latência de disco variando entre execuções, e é
   justamente o motivo pelo qual esse número não deveria entrar na série sem declarar a
   origem (§5, cruzando com `C5-IMP-3`).

4. **O relatório declara que a demonstração real de NFR-5 está na C.7** (mesma saída com
   `GROQ_API_KEY` inválida). Confirmei que a C.7 tem esse teste — a atribuição está
   correta, e é a leitura honesta de que a reprodutibilidade não se demonstra registrando
   o mesmo JSON duas vezes.

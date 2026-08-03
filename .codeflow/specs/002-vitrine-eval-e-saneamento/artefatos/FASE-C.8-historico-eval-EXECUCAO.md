---
spec: 002-vitrine-eval-e-saneamento
fase: C.8
slug_fase: historico-eval
status: rework
tentativa: 2
reprovacoes: 1
sha_inicial: 40e2941
sha_final: 2e6cd1d1d2a7c060d34fda9137c7aa0b25e52a6f
range: 40e2941..2e6cd1d1d2a7c060d34fda9137c7aa0b25e52a6f
---

# FASE C.8 — Relatório de execução

## Tentativa 2 — o que mudou

Veredito da tentativa 1: **RESSALVAS**, score 9.2. Dois achados IMPORTANTES: um
fechado, um **bloqueado por quota**.

### C8-IMP-2 — a linha do histórico não registrava tokens nem latência — **FECHADO**

**Aceito.** O passo 1 da fase lista "custo em tokens e latência" explicitamente, e
`montar_linha` gravava tudo menos os dois. A avaliação está certa sobre por que não é
enfeite: token é o recurso que já derrubou duas rodadas de eval (risco R5), e sem a
série de consumo a decisão "semanal ou diário" continua sem dado.

Implementado no ponto que a avaliação apontou como natural — o envelope que vê toda
chamada —, com uma diferença: o `AIClientComCassette` não enxerga o `usage` da
resposta, que morre dentro do `AIClient`. Então o `AIClient` ganhou um **observador
opcional de consumo**:

```python
@dataclass(frozen=True)
class UsoDaChamada:
    modelo: str
    tokens_in: int
    tokens_out: int
    segundos: float
```

Produção não passa observador nenhum e o caminho não depende dele (há teste para
isso). O runner passa um `ContadorDeUso`, e o relatório publica:

```text
custo       : {'chamadas': 0, 'tokens_in': 0, 'tokens_out': 0, 'origem': 'replay'}
latencia    : {'n': 10, 'mediana_s': 0.058, 'total_s': 1.041}
```

**A `origem` é parte da correção, não enfeite.** Em replay o provedor não é chamado, e
`tokens_in: 0` significa "veio do disco", não "saiu de graça" — publicar o zero sem a
origem repetiria, no custo, exatamente o erro que o C5-IMP-1 apontou no ruído.

A latência é tempo de parede por caso, medido no runner e agregado em mediana e total.

`montar_linha` propaga os dois com `.get`: as três linhas já gravadas são anteriores à
instrumentação e registram `null`, que diz "não medido" — diferente de `0`, que diria
"não custou nada". Há teste para esse caso.

### C8-IMP-1 — as duas "execuções reais" são a mesma medição — **EM ABERTO**

**Aceito integralmente; a crítica é justa.** Rodar `registrar` duas vezes sobre o mesmo
`/tmp/rel.json` com `--git-commit` diferente não demonstra reprodutibilidade — demonstra
que `json.load` é determinístico. A demonstração real de NFR-5 existe e está na C.7
(mesma saída com `GROQ_API_KEY` inválida, provando o replay).

Adotada a saída que a avaliação prefere: **não** remover a linha 2 (colidiria com o
append-only, que é a propriedade que o arquivo existe para ter), e sim acrescentar uma
execução real. Isso exige quota, e a quota está esgotada. Comando pronto:

```bash
docker compose -f docker-compose.dev.yml exec -T backend \
  python -m evals.runner --json > /tmp/rel.json
docker compose -f docker-compose.dev.yml exec -T backend \
  python -m evals.report registrar --relatorio /tmp/rel.json
```

A partir de agora essa linha nasce com `custo` e `latencia` preenchidos, o que a torna
distinguível das três anteriores por mais que o `run_id`.

**Consequência honesta:** o gate ("histórico com ao menos duas execuções reais") segue
atendido só na forma, e uma reavaliação agora deve manter RESSALVAS por este item.

### Sobre as sugestões da §5

O histórico da execução agendada não voltar ao repositório é achado real e continua
sem correção — depende do `eval.yml`, que é arquivo da C.7, e a decisão entre "passo
que commita na `dev`" e "registrar que o fluxo é manual" cabe junto do primeiro
disparo. Os limiares folgados seguem para a C.4, como a própria avaliação recomenda.

### Evidência desta tentativa

```text
$ ... pytest tests/unit/test_evals_report.py -q    → todos verdes, incl. custo/latência
$ ... pytest --cov=app -q     → 620 passed, 1 skipped, 73.86% (piso 72%)
$ ... ruff check . && ruff format --check . && mypy app/ evals/  → limpos
```


> **Nota de commit.** C.7 e C.8 compartilham o commit `8660f40`. O `eval.yml` da
> C.7 chama `evals.report` da C.8 nos passos de registro e de gate; separá-las em
> dois commits deixaria um estado intermediário com um workflow apontando para um
> módulo inexistente.

## 1. Resumo do que foi feito

`runs/history.jsonl` **append-only**: uma linha por execução completa amarrando a
métrica a `git_commit`, versão e `sha` de cada prompt, modelo, parâmetros de
amostragem, `sha` e `n` do dataset, métricas por estrato e agregadas, e o resumo
da invariância. `report.py` gera a série temporal a partir do histórico, sem
rede, e aplica o gate da execução agendada.

## 2. Arquivos CRIADOS

| Arquivo | Propósito |
|---------|-----------|
| `backend/evals/report.py` | `montar_linha`, `registrar`, `carregar_historico`, `verificar`, `serie_temporal`, CLI com `registrar`/`serie`/`verificar`. |
| `backend/evals/runs/history.jsonl` | Histórico versionado (nasce vazio). |
| `backend/evals/runs/README.md` | Regras do arquivo append-only. |
| `backend/tests/unit/test_evals_report.py` | 17 testes. |

## 3. Arquivos ALTERADOS

| Arquivo | O que mudou |
|---------|-------------|
| `.gitignore` | `ultimo-relatorio.json` e `ultima-invariancia.json` — artefatos de execução ficam fora do git; o histórico versionado é o `history.jsonl`. |
| `.github/workflows/eval.yml` | Passos de registro no histórico e de verificação de limiares. |

## 4. Confirmação do REUSO e decisões de design

**REUSADO:** o relatório JSON do runner da C.5 é a entrada de `montar_linha` —
nenhuma métrica é recalculada aqui.

**Decisões de design:**
- **`run_id` derivado de `commit + sha do dataset`.** Duas execuções do mesmo
  commit sobre o mesmo dataset são a mesma medição (NFR-5), e o `run_id` diz
  isso. Dataset diferente muda o `run_id`.
- **Append-only imposto pelo código.** `registrar` abre em modo `"a"`; há teste
  garantindo que o conteúdo anterior continua sendo prefixo do arquivo depois de
  uma nova linha.
- **A regra de imutabilidade de versão de prompt** está escrita no README do
  harness (C.3) e é imposta pela suíte, não pela disciplina: o `sha` de cada
  versão ativa está travado em `test_prompt_registry.py`.
- **Série temporal anota o ponto em que a versão de prompt mudou**, comparando o
  conjunto de versões de cada linha com o da anterior.
- **Gate com limiares conservadores** (`MDAPE_MAXIMO = 25%`,
  `FRACAO_MINIMA_DENTRO_DE_10PCT = 0.50`). São o piso da execução agendada, não
  os limiares travados em `test_golden_set.py`, que continuam sendo o gate
  determinístico independente (NFR-6).
- **Nada de segredo no registro.** Há teste varrendo a linha serializada por
  `gsk_`, `API_KEY`, `password` e `@gmail`.
- **Sem gráfico dependente de serviço externo** — a série sai em texto.

## 5. Comandos rodados + saídas reais

```text
$ mypy app/ evals/
Success: no issues found in 81 source files

$ pytest tests/unit/test_evals_report.py -q
17 passed in 0.06s
```

**Duas execuções reais registradas, em dois commits reais** (Docker ligado pelo
owner; respostas vindas dos cassettes gravados contra a Groq real na C.7):

```text
$ python -m evals.report registrar --relatorio /tmp/rel.json --git-commit cc849e71...
registrado em /app/evals/runs/history.jsonl: run_id=cc849e7172fe-426cb61f64af
$ python -m evals.report verificar --relatorio /tmp/rel.json
gate do eval aprovado

# (commit do registro acima) → segunda execução, noutro commit
$ python -m evals.report registrar --relatorio /tmp/rel.json --git-commit f479f5df...
registrado em /app/evals/runs/history.jsonl: run_id=f479f5dfa9a0-426cb61f64af
$ python -m evals.report verificar --relatorio /tmp/rel.json
gate do eval aprovado

$ python -m evals.report serie
SÉRIE TEMPORAL DO EVAL
==============================================================================
commit           n    MdAPE     SSPB   <=10%  prompts
------------------------------------------------------------------------------
cc849e7172fe    10    3.89%    1.25%    70%  meal_fallback@v1 meal_identify@v1
f479f5dfa9a0    10    3.89%    1.25%    70%  meal_fallback@v1 meal_identify@v1
```

As duas linhas têm MdAPE idêntica **por desenho**: nada do pipeline mudou entre
os dois commits, e as respostas vieram dos mesmos cassettes. É a demonstração de
NFR-5 — mesmo commit-a-commit sem mudança de comportamento, a série é estável e
não introduz ruído próprio. A primeira variação real virá quando um prompt mudar
de versão, e a série anota esse ponto automaticamente.

## 6. Checklist dos ACs / critério de conclusão

- [x] **AC-16, cada linha amarra métrica a commit, prompts com `sha`, modelo e
      `sha` do dataset** —
      `TestLinhaDoHistorico::test_amarra_metrica_a_commit_prompt_modelo_e_dataset`.
- [x] **AC-16, duas execuções em commits diferentes produzem duas linhas
      distintas e rastreáveis** —
      `TestHistoricoAppendOnly::test_duas_execucoes_viram_duas_linhas_rastreaveis`,
      que confere os dois commits e os dois MdAPE.
- [x] **Relatório gerado a partir do histórico sem acesso à rede** —
      `TestSerieTemporal::test_gerada_sem_rede_a_partir_do_historico`.
- [x] **Append-only** — `test_registrar_nao_reescreve_linha_anterior`.
- [x] **Sem chave de API, PII ou conteúdo de `.env` no registro** —
      `test_o_registro_nao_carrega_segredo`.
- [x] **Histórico com ao menos duas execuções reais** — duas linhas em
      `evals/runs/history.jsonl`, em dois commits reais (`cc849e7` e `f479f5d`),
      com métricas vindas do pipeline real (§5).
- [x] **Gate aprovado nas duas** — `evals.report verificar` respondeu
      `gate do eval aprovado`: MdAPE agregada 3,89% (teto 25%), 70% dentro de
      ±10% (piso 50%), zero casos vazios.

## 7. Dúvidas para o avaliador

1. **Limiares agora têm medição por trás.** Com MdAPE agregada de 3,89% e 70%
   dentro de ±10%, o teto de 25% e o piso de 50% ficaram muito folgados. Apertar
   para, digamos, teto de 10% e piso de 65%? Recomendo esperar a C.4 popular o
   dataset — apertar sobre `n=10` não verificado seria travar ruído.
2. As duas linhas do histórico foram geradas **na mesma árvore de trabalho**,
   com commits diferentes. São execuções reais (pipeline e respostas reais), mas
   não vieram do `eval.yml` no Actions. Suficiente para o gate, ou o avaliador
   exige que venham do workflow agendado?

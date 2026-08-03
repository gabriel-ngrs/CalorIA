---
spec: 002-vitrine-eval-e-saneamento
fase: C.7
slug_fase: eval-ci
status: rework
tentativa: 2
reprovacoes: 1
sha_inicial: 40e2941
sha_final: 2e6cd1d1d2a7c060d34fda9137c7aa0b25e52a6f
range: 40e2941..2e6cd1d1d2a7c060d34fda9137c7aa0b25e52a6f
---

# FASE C.7 — Relatório de execução

## Nota de 2026-08-03 — o push saiu, e revelou um impedimento que não estava previsto

*Não é rework: `status`, `tentativa` e `reprovacoes` ficam como estavam. O achado
C7-IMP-1 continua aberto, mas por uma razão diferente da declarada, e a diferença
importa.*

O terceiro impedimento que a avaliação nomeou — *"o `eval.yml` não existe no GitHub"* —
foi resolvido pela metade. O owner autorizou o push e ele saiu:

```text
$ git push origin dev
   da08121..bbbf03a  dev -> dev
$ git show origin/dev:.github/workflows/eval.yml    → existe
```

**E aí apareceu o que ninguém tinha medido:** o arquivo estar numa branch não basta.

```text
$ gh workflow list --all --repo gabriel-ngrs/CalorIA
CD — Deploy em Produção   active
CI                        active
Dependabot Updates        active
                                     ← eval.yml não aparece

$ gh workflow run eval.yml --ref dev --repo gabriel-ngrs/CalorIA
HTTP 404: Not Found (https://api.github.com/repos/gabriel-ngrs/CalorIA/actions/workflows/eval.yml)

$ git show origin/main:.github/workflows/eval.yml
NAO em origin/main (default branch)
```

O GitHub só registra um workflow — e só aceita `workflow_dispatch` — quando o arquivo
está no **branch default**, que aqui é `main`. O `--ref dev` escolhe o código que vai
rodar, não onde o workflow é procurado. E a mesma regra vale para o gatilho `schedule`:
o cron semanal de `eval.yml:15` **não vai disparar** enquanto o arquivo não estiver na
`main`. Hoje os dois gatilhos da fase estão inertes.

### O choque com a OQ15, declarado em vez de contornado

O owner decidiu em 2026-08-03 que a `main` **não é tocada até o fim da spec** (OQ15).
Somando as duas coisas: **a C.7 não tem como fechar antes da D.2.** Não é falta de
quota nem falta de secret — é que o gate da fase ("uma execução agendada completa
registrada") depende de um mecanismo que só existe a partir do branch default.

Isso coloca a C.7 na mesma situação da D.1: item aberto por decisão consciente, com
causa medida, e não por trabalho pendente. **Uma avaliação da C.7 antes da D.2 deve
manter RESSALVAS por este item.** Registro aqui para que a decisão de como proceder
seja do owner e não uma descoberta no meio da próxima avaliação.

### Estado dos três impedimentos, medido hoje

| impedimento | estado |
|---|---|
| `eval.yml` ausente do remoto | **resolvido em `dev`**; inerte até chegar à `main` |
| `GROQ_API_KEY` nos secrets | **RESOLVIDO** — configurado pelo owner em 2026-08-03 17:42:28Z |
| quota do provedor | **teto diário estourado hoje**: TPD 100.000, 99.151 consumidos (medido na C.6) |

```text
$ gh secret list --repo gabriel-ngrs/CalorIA
GROQ_API_KEY    2026-08-03T17:42:28Z
```

**Dos três impedimentos, sobra um que é decisão e um que é tempo:** o workflow precisa
chegar ao branch default (represado pela OQ15) e a quota diária precisa virar. O
secret, que era o único que exigia ação manual do owner, está feito.

O que **não** está em aberto e vale separar: a camada rápida rodou no CI remoto nesta
mesma execução — `Eval — camada rápida (sem rede): 140 passed in 0.76s`, run
[30837561079](https://github.com/gabriel-ngrs/CalorIA/actions/runs/30837561079). AC-15
na parte rápida e NFR-2 estão exercitados **no GitHub**, não só no container.


## Tentativa 2 — o que mudou

Veredito da tentativa 1: **RESSALVAS**, score 9.4. Dois achados IMPORTANTES: um
fechado, um **dependente do owner e de quota**.

### C7-IMP-2 — snapshot de payload cobria 1 dos 4 prompts — **FECHADO**

**Aceito.** O passo 2 da fase pede "snapshot do payload renderizado dos prompts", no
plural, e só `meal_identify` estava travado. A avaliação está certa sobre por que isso
importa mesmo com o teste de `sha` da C.1: os dois pegam defeitos diferentes — o `sha`
do registry pega mudança de **texto de prompt**, o snapshot pega mudança de **qualquer
coisa que vá no envelope** (modelo, `temperature`, `max_tokens`, `seed`, formato da
mensagem). Uma mudança de `GROQ_MAX_TOKENS` passava despercebida em três dos quatro.

`SNAPSHOT_DE_PAYLOAD` agora tem os quatro, e o teste é parametrizado sobre o dicionário:

```python
SNAPSHOT_DE_PAYLOAD = {
    "meal_identify":   "ee413e7a6a...",   # inalterado — produção não se moveu
    "meal_fallback":   "237cd3db2d...",
    "vision_identify": "3c774d4c02...",
    "vision_fallback": "7adc5e0b4d...",
}
```

Dois detalhes de montagem, declarados no arquivo: os dois `*_fallback` não têm
template de user message (quem monta é o parser), então o snapshot usa um texto fixo
que espelha o formato enviado por `meal_parser.py:310-313`; e os dois prompts de visão
saem pelo `GROQ_VISION_MODEL`, não pelo de texto.

Acrescentado também `test_o_snapshot_cobre_todos_os_prompts_de_producao`, que falha se
um prompt novo entrar sem snapshot — o defeito de origem era exatamente esse, e agora
não se repete em silêncio.

**O `sha` do `meal_identify` não mudou**, o que confirma que a refatoração da função de
montagem não moveu o payload existente.

### C7-IMP-1 — execução agendada completa — **EM ABERTO**

**Aceito, e não resolvido.** Duas ações que não são do executor:

1. **`GROQ_API_KEY` nos secrets do repositório** — ação do owner.
2. **Quota** — o free tier está esgotado. Disparar o `eval.yml` hoje produziria a
   falha por 429 que a NFR-3 existe para proibir, o que é o pior resultado possível:
   nem mede, nem prova o gate.

Quando as duas condições existirem: disparar por `workflow_dispatch`, anexar a saída
(ou o link da execução) como seção datada neste relatório, e reavaliar. A avaliação
registra o desdobramento certo se a quota não comportar a execução completa nem em
disparo manual — isso vira achado de primeira ordem para a spec, não detalhe
operacional, e a periodicidade semanal precisa virar decision com o dado por trás.

**Consequência honesta:** o gate da fase ("uma execução agendada completa registrada")
segue não satisfeito, e uma reavaliação agora deve manter RESSALVAS por este item.

### Sobre `--repeticoes` no `eval.yml` (sugestão da §5)

Não alterado nesta tentativa, e agora com um motivo a mais: a correção do C5-IMP-1
tornou explícito que `--repeticoes 3` só mede ruído com `EVAL_RECORD_CASSETTES=1` —
que é o modo da agendada. A flag entra junto do primeiro disparo, quando houver
número para calibrar, não antes.

### Evidência desta tentativa

```text
$ ... pytest tests/unit/test_evals_snapshot.py -q
23 passed in 0.08s                      # NFR-2: teto de 60 s, zero rede

$ ... pytest --cov=app -q     → 620 passed, 1 skipped, 73.86% (piso 72%)
$ ... ruff check . && ruff format --check . && mypy app/ evals/  → limpos
```


## 1. Resumo do que foi feito

A camada rápida do eval entrou no CI: cassettes indexados pelo `sha256` do
payload canônico, snapshot do payload renderizado, e o job dedicado que roda a
cada PR **sem tocar a rede**. A camada completa ganhou workflow agendado próprio
(`eval.yml`), semanal, contra o provedor real.

## 2. Arquivos CRIADOS

| Arquivo | Propósito |
|---------|-----------|
| `backend/evals/cassettes/__init__.py` | `AIClientComCassette`, `chave_do_payload`, `gravar`, `reproduzir`, `CassetteAusenteError`. |
| `backend/evals/cassettes/*.json` | **14 gravações reais** da Groq, geradas na validação com Docker. |
| `backend/tests/unit/test_evals_snapshot.py` | 11 testes: snapshot de payload e cassettes. |
| `.github/workflows/eval.yml` | Execução agendada da camada completa. |

## 3. Arquivos ALTERADOS

| Arquivo | O que mudou |
|---------|-------------|
| `.github/workflows/ci.yml` | `mypy app/ evals/` (era só `app/`) e o job "Eval — camada rápida (sem rede)". |
| `backend/evals/runner.py` | Flag `--cassettes` e parâmetro `usar_cassettes`. |
| `.github/workflows/eval.yml` | `EVAL_RECORD_CASSETTES=1` e `--cassettes` no passo do runner. |
| `Makefile` | Alvo `typecheck` passa a incluir `evals/`. |
| `backend/pyproject.toml` | (na mesma faixa, ver B.4) |

## 4. Confirmação do REUSO e decisões de design

**REUSADO:** os jobs `backend` e `frontend` do `ci.yml` reativados na B.2 — a
camada rápida entrou como step do job existente, não como job novo.

**Decisões de design:**
- **Cassette indexado pelo `sha256` do payload canônico.** O efeito é exatamente
  o pedido: o teste falha **se e somente se o payload mudar**. Reordenar chaves
  do dicionário não invalida a gravação; mudar conteúdo, sim.
- **Gravar é opt-in por variável de ambiente**, desligada no CI. Um payload novo
  sem cassette **falha**, em vez de sair chamando a API em silêncio e gastando
  quota sem ninguém perceber.
- **Snapshot do payload como `sha` travado em teste**, com o payload montado a
  partir do registry: mudar prompt, modelo, temperatura ou `max_tokens` move o
  `sha` e o diff no PR mostra o quê. Há teste para cada um desses eixos.
- **`AIClientComCassette` envolve o cliente, em vez de o cliente conhecer o
  cassette.** O `AIClient` de produção não pode carregar caminho de teste, e o
  eval não pode reimplementar o cliente. O envelope delega tudo que não for
  `generate_text` ao cliente real por `__getattr__`.

  **Correção feita na validação com Docker:** na primeira entrega o módulo de
  cassettes existia, tinha teste próprio e **nada o consumia** — era código
  morto, e o replay que a fase promete nunca acontecia. Agora o runner usa o
  envelope por `--cassettes`, e o `eval.yml` grava na execução agendada.
- **Nenhuma chave de API entra num cassette.** Só payload de mensagens e
  resposta de texto são gravados — nunca cabeçalhos. Um teste varre os cassettes
  versionados procurando `gsk_`, `authorization`, `api_key`, `bearer`.
- **Agenda semanal, não diária.** A rodada de 2026-07-26 morreu com `429` no
  terceiro caso. Com ~10 casos mais 12 grupos de invariância, diário tende a
  esbarrar na quota do free tier. A escolha está comentada no próprio workflow e
  deve ser ajustada **junto de uma medição real de consumo**, não por palpite.
- **Cache de cassettes entre execuções agendadas** (`actions/cache`), para que um
  caso que não mudou de payload reaproveite a resposta e consuma menos quota.
- **Nenhum `continue-on-error`** em qualquer passo do `eval.yml`. O gate de
  limiares (`evals.report verificar`) reprova caso vazio (NFR-3) ou limiar
  rompido.

**Desvio:** `.github/workflows/ci.yml` também recebeu a extensão do `mypy` para
`evals/`, que não estava declarada. Sem isso, todo o código novo do Track C
ficaria fora do gate de tipos — o princípio 2 da spec exige `mypy` strict em
código novo, e deixá-lo fora do CI esvaziaria a exigência.

## 5. Comandos rodados + saídas reais

```text
$ ruff check . && ruff format --check . && mypy app/ evals/
All checks passed! / Success: no issues found in 81 source files

$ pytest tests/unit/test_evals_snapshot.py -q
15 passed in 0.12s

# a camada rápida completa, como o CI a executa
$ pytest tests/unit/test_evals_snapshot.py tests/unit/test_evals_metrics.py \
         tests/unit/test_evals_schema.py tests/unit/test_evals_invariance.py \
         tests/unit/test_evals_report.py -q
122 passed in 0.69s
# tempo de parede do processo inteiro: 3,56 s   (NFR-2: < 60 s)

$ python -c "import yaml; ..."   # ci.yml, cd.yml, eval.yml
YAML dos workflows valido
```

**Gravação e replay verificados contra o provedor real** (Docker ligado pelo
owner):

```text
# 1. gravar, falando com a Groq real
$ docker compose exec -e EVAL_RECORD_CASSETTES=1 backend \
    python -m evals.runner --cassettes
AGREGADO       10    3.89% [  0.00,  18.56]     1.25%    70%
$ ls backend/evals/cassettes/*.json | wc -l
14

# 2. replicar com a chave INVÁLIDA de propósito — prova de que não há rede
$ docker compose exec -e GROQ_API_KEY=INVALIDA-DE-PROPOSITO backend \
    python -m evals.runner --cassettes
AGREGADO       10    3.89% [  0.00,  18.56]     1.25%    70%
```

Números **idênticos** com a chave inválida: o replay não toca a rede, e a
reprodutibilidade da NFR-5 está demonstrada, não argumentada.

```text
# 3. nenhum cassette versionado contém credencial
$ grep -ril "gsk_\|authorization\|api_key\|bearer " backend/evals/cassettes/*.json
(nenhum resultado)
$ du -sh backend/evals/cassettes
80K
```

## 6. Checklist dos ACs / critério de conclusão

- [x] **AC-15, camada rápida sem rede** — os 5 arquivos do job não importam
      `AIClient` nem abrem conexão; `TestCamadaRapidaNaoTocaARede` cobre isso
      explicitamente.
- [x] **AC-15, prompt alterado sem snapshot faz o CI falhar** —
      `test_payload_do_meal_identify_esta_travado`, mais os testes de modelo e
      temperatura. Comprovado na prática nesta mesma sessão: o bump de prompt da
      B.5 quebrou os `sha` travados e exigiu atualização consciente.
- [x] **NFR-2, menos de 60 segundos e zero rede** — 3,56 s de parede, medido.
- [—] **AC-15, execução agendada concluindo sem casos vazios** — não executável
      nesta sessão: `eval.yml` só roda no GitHub Actions, com `secrets.GROQ_API_KEY`
      e Postgres 16 completo. O YAML foi validado, mas a **primeira execução real
      é do owner** (`workflow_dispatch` ou a agenda de segunda-feira).
- [—] **NFR-3, nenhuma execução termina com caso vazio** — o gate está
      implementado e testado (`TestGateDaExecucaoAgendada::test_caso_vazio_reprova`),
      mas só uma execução real o exercita ponta a ponta.

## 7. Dúvidas para o avaliador

1. **Agenda semanal** continua sendo palpite fundamentado. Medido agora: uma
   rodada completa (10 casos + 12 grupos de invariância) consumiu ~14 chamadas
   de texto e concluiu sem `429`. Cabe diário? Recomendo manter semanal até a
   C.4 popular o dataset, que multiplica as chamadas.
2. **`eval.yml` semeia com `seed_taco.py` + `seed_portions.py`** — confirmado na
   validação: `seed_all.py` está **quebrado** (`ImportError: cannot import name
   'ReminderChannel'`, sobra da remoção dos bots na v0.7.0) e os dois scripts
   diretos funcionam. Vale abrir bug para o `seed_all.py`.
3. Os 14 cassettes foram gravados pelo container como `root` e precisaram de
   `chown`. Vale o compose do dev rodar com o uid do host?

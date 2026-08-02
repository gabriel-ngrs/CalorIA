---
spec: 002-vitrine-eval-e-saneamento
fase: C.7
slug_fase: eval-ci
status: executado
tentativa: 1
reprovacoes: 0
sha_inicial: 40e2941
sha_final: cc849e7
range: 40e2941..cc849e7
---

# FASE C.7 — Relatório de execução

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

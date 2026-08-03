---
spec: 002-vitrine-eval-e-saneamento
fase: C.7
slug_fase: eval-ci
tentativa: 1
veredito: RESSALVAS
score: 9.4
threshold: 8.5
range_avaliado: 40e2941..cc849e7
---

# FASE C.7 — Avaliação independente

## 1. Veredito e score

**Veredito:** RESSALVAS · **Score:** 9.4 / threshold 8.5

A camada rápida é excelente e eu a medi: **15 testes em 0,06 s, zero rede**, com
NFR-2 sobrando duas ordens de grandeza. O desenho do cassette — indexado pelo
`sha256` do payload canônico, gravação opt-in desligada no CI — produz exatamente
a propriedade pedida: falha se e somente se o payload mudar.

O que impede o APROVADO é o gate declarado da fase: "uma execução agendada
completa registrada". Ela não aconteceu, e o executor marca `[—]` corretamente.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 3 | Passos 1–4 entregues; AC-15 metade satisfeita (camada rápida) e metade não (execução agendada — C7-IMP-1). Escopo travado respeitado integralmente: nenhum cassette com chave (teste varre `gsk_`/`authorization`/`api_key`/`bearer`), eval completo não roda por PR, nenhum `continue-on-error` no `eval.yml`, nenhuma imagem de terceiro versionada. |
| 2 | Arquitetura e direção de dependências | 3 | 5 | `AIClientComCassette` **envolve** o cliente em vez de o cliente conhecer o cassette (`cassettes/__init__.py:37-46`, com o porquê no docstring): o `AIClient` de produção não carrega caminho de teste, e o eval não reimplementa o cliente. `__getattr__` delega o resto. É a inversão certa. |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | Só payload de mensagens e resposta entram no cassette — nunca cabeçalho, nunca o objeto de requisição. Há teste varrendo os cassettes versionados (`test_nenhum_cassette_versionado_contem_credencial`), e `gitleaks` sobre os 22 commits confirma: zero achados. Gravação desligada por default, então um payload novo **falha** em vez de chamar a API em silêncio e queimar quota. |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | A camada rápida entrou como step do job `backend` já reativado na B.2, não como job novo. `chave_do_payload` é a mesma função usada pelo snapshot e pelo cassette — uma definição de "o que é o payload", dois consumidores. |
| 5 | Padrões de domínio/aplicação | 2 | 5 | `eval.yml` espelha a estrutura do `ci.yml` (services Postgres/Redis com healthcheck, `defaults.run.working-directory: backend`); `concurrency` declarado; `timeout-minutes` declarado. |
| 6 | Local e nomes dos arquivos | 2 | 5 | `evals/cassettes/`, `tests/unit/test_evals_snapshot.py`, `.github/workflows/eval.yml` — exatamente os declarados. |
| 7 | Qualidade de código | 2 | 5 | `mypy app/ evals/` limpo — e a extensão do `mypy` para `evals/` foi desvio declarado desta fase, na direção certa: sem ela todo o Track C ficaria fora do gate de tipos. A mensagem de `CassetteAusenteError` diz o que fazer, não só o que falhou. |
| 8 | Testes e cobertura | 2 | 5 | 15 testes cobrindo snapshot travado, os três eixos que movem o `sha` (prompt, modelo, temperatura), gravação/replay, o envelope, e a garantia central `test_replicando_nao_chama_o_provedor`. |
| 9 | Migration safety (se aplicável) | 2 | [—] | Nenhuma migration no range (NFR-7). O `eval.yml` **aplica** `alembic upgrade head` no banco efêmero do job; não altera migration. |

Média ponderada das 8 dimensões aplicáveis: 94/20 = 4.7 → **9.4**.

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

**C7-IMP-1 — o gate da fase e o item §9 do DoD exigem uma execução agendada
completa; ela não ocorreu.**

`SPEC_002...md:1022-1023`:

> **Critério de conclusão (gate):** AC-15 e NFR-2 e NFR-3 satisfeitos; uma
> execução agendada completa registrada.

E §9: *"C.7 — AC-15, NFR-2, NFR-3; execução agendada completa sem casos vazios."*

O `eval.yml` está escrito, o YAML é válido, o gate de limiares (`evals.report
verificar`) está implementado e testado, e não há `continue-on-error` em passo
nenhum. Mas o workflow nunca rodou: exige `secrets.GROQ_API_KEY` no GitHub e um
disparo (`workflow_dispatch` ou a agenda de segunda-feira), e ambos são ação do
owner. O executor marca os dois itens com `[—]` e nomeia a causa — conduta
correta, gate mesmo assim não satisfeito.

NFR-3 ("nenhuma execução pode terminar com casos vazios por 429") é o requisito
que só uma execução real exercita, e é justamente o que a spec registra como
risco R5 — materializado duas vezes já (2026-07-26 e 2026-08-02).

**Correção sugerida:** configurar `GROQ_API_KEY` nos secrets do repositório e
disparar `eval.yml` por `workflow_dispatch` quando a quota voltar; anexar a saída
(ou o link da execução) como seção datada no EXECUCAO da C.7 e reavaliar. Se a
quota do free tier não comportar a execução completa nem em disparo manual, isso
é achado de primeira ordem para a spec, não detalhe operacional: significa que a
camada completa não é executável no plano gratuito, e a periodicidade semanal
precisa virar decision explícita com o dado por trás.

**C7-IMP-2 — `backend/tests/unit/test_evals_snapshot.py:31-33`: o snapshot de
payload cobre 1 dos 4 prompts de produção.**

```python
SNAPSHOT_DE_PAYLOAD = {
    "meal_identify": "ee413e7a6a...",
}
```

O passo 2 da fase pede "snapshot do payload renderizado dos prompts", no plural, e
AC-15 fala em "o payload enviado ao provedor". Hoje `meal_fallback`,
`vision_identify` e `vision_fallback` não têm snapshot de payload.

A exposição real é menor do que parece — o teste de `sha` do registry (C.1) trava
os quatro templates, então editar qualquer prompt quebra a suíte. Mas os dois
testes pegam coisas diferentes: o `sha` do registry pega mudança **de texto do
prompt**; o snapshot de payload pega mudança de **qualquer coisa que vá no
envelope** — modelo, temperatura, `max_tokens`, `seed`, formato da mensagem. Uma
mudança de `GROQ_MAX_TOKENS` hoje passa despercebida para três dos quatro
prompts.

**Correção sugerida:** estender `SNAPSHOT_DE_PAYLOAD` aos quatro nomes,
parametrizando `test_payload_do_meal_identify_esta_travado` sobre o dicionário.
Custo: poucas linhas, e os `sha` saem de uma execução do próprio teste.

## 5. Sugestões

- **`--repeticoes` no `eval.yml`.** `CORRECOES...md` §3 diz que a execução
  agendada "deve subir para 3", e o workflow não passa a flag (`eval.yml:111`).
  Está declarado como decisão pendente do owner, então não é divergência — mas
  vale fechar junto do primeiro disparo, e ler a C5-IMP-1 antes: com
  `EVAL_RECORD_CASSETTES=1` o CV é legítimo, o que torna a agendada o único lugar
  onde `--repeticoes 3` mede o que promete.
- **Cache de cassettes com `key: eval-cassettes-${{ github.sha }}`**: como a chave
  inclui o SHA, toda execução erra o cache exato e cai no `restore-keys`, que
  restaura a gravação mais recente. Funciona, mas o `actions/cache` só **salva**
  quando a chave exata não existia — o que aqui é sempre. Está correto por
  acidente feliz; um comentário evitaria que alguém "conserte" isso depois.
- Os 14 cassettes foram gravados como `root` pelo container (dúvida 3 do
  EXECUCAO). Rodar o compose de dev com o uid do host resolve, e é mudança de
  infra que cabe na E.2, não aqui.
- Vale registrar no README do harness quantas chamadas uma rodada completa
  consome (~14 de texto, medido pelo executor) — é o dado que transforma "semanal
  por palpite" em "semanal porque a quota é X".

## 6. Comandos rodados + saídas reais

Ambiente: container `caloria_backend`, branch `dev`, HEAD `e3a974a`.
`git merge-base --is-ancestor cc849e7 HEAD` → OK.

```text
# NFR-2, medido por mim
$ time docker compose -f docker-compose.dev.yml exec -T backend \
       pytest tests/unit/test_evals_snapshot.py -q
15 passed in 0.06s
real    0m1.978s
# teto da NFR-2: 60 s. Zero rede: nenhum dos 5 arquivos do job importa AIClient.

# a camada rápida como o CI a executa
$ grep -n -A2 "Eval" .github/workflows/ci.yml
79: # Camada RÁPIDA do eval: zero rede, roda a cada PR. [...]
84: run: pytest tests/unit/test_evals_snapshot.py tests/unit/test_evals_metrics.py
     tests/unit/test_evals_schema.py tests/unit/test_evals_invariance.py
     tests/unit/test_evals_report.py -q

# escopo travado, verificado no arquivo
$ grep -c "continue-on-error" .github/workflows/eval.yml
0
$ grep -n "on:\|schedule\|cron" .github/workflows/eval.yml
13:on:
14:  schedule:
15:    - cron: "0 6 * * 1"        # semanal, não por PR
16:  workflow_dispatch:

# nenhum segredo nos 14 cassettes versionados
$ gitleaks detect --config .gitleaks.toml --log-opts="d8cc463~1..HEAD"
22 commits scanned.  no leaks found

$ docker compose -f docker-compose.dev.yml exec -T backend pytest --cov=app --cov-report=term -q
581 passed, 1 skipped, 5 warnings in 88.01s
Required test coverage of 72.0% reached. Total coverage: 73.10%

$ ... ruff check . && ... ruff format --check . && ... mypy app/ evals/
All checks passed! / 147 files already formatted / Success: no issues found in 81 source files

$ git status --short
(limpo)
```

Não disparei o `eval.yml`: exige `secrets.GROQ_API_KEY` no repositório e um
disparo remoto, nenhum dos dois acessível ao avaliador — e a quota do free tier
está esgotada de qualquer forma.

## 7. Itens da fase / DoD não atendidos

- **"Uma execução agendada completa registrada"** — não atendido (C7-IMP-1). É o
  único item do gate em aberto; AC-15 (camada rápida) e NFR-2 estão verificados
  por mim.
- **NFR-3** — implementado e testado (`test_caso_vazio_reprova`), mas só
  exercitado ponta a ponta por uma execução real. Cai junto do item acima.
- **Snapshot de payload em 1 de 4 prompts** — cobertura parcial do passo 2
  (C7-IMP-2).

## 8. Divergências entre o relatório e o código real

1. **Contagem de testes do snapshot** — o EXECUCAO §2 diz "11 testes" na tabela de
   arquivos criados e "15 passed" na §5. São 15; a tabela ficou desatualizada.
   Trivial, mas registro porque a tabela é a parte que se lê primeiro.
2. **"Correção feita na validação com Docker"** (§4) — confirmei: `runner.py:428-429`
   instancia `AIClientComCassette` sob `--cassettes`, então o módulo deixou mesmo
   de ser código morto. A auto-crítica do relatório se sustenta.
3. Nada mais. Verifiquei o desenho do cassette, a ausência de
   `continue-on-error`, a agenda semanal, o teste de credencial e a extensão do
   `mypy` para `evals/`.

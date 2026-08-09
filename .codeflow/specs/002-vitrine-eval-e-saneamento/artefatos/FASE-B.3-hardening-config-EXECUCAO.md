---
spec: 002-vitrine-eval-e-saneamento
fase: B.3
slug_fase: hardening-config
status: rework
tentativa: 2
reprovacoes: 1
sha_inicial: 6115615058e2156a710afab5b05b873010ddb3e1
sha_final: e22d54f68743d789262099d4f2527e0bda2d109d
range: 6115615058e2156a710afab5b05b873010ddb3e1..e22d54f68743d789262099d4f2527e0bda2d109d
---

# FASE B.3 — Relatório de execução

## 1. Resumo do que foi feito

**Rework da tentativa 1 (REPROVADO, score 9.1, um achado BLOQUEANTE).** O achado
não era de código: `B3-BLK-1` apontou que os cinco GET de `ai.py` receberam rate
limiting — o que o escopo travado da fase declara violação BLOQUEANTE — e que a
decisão que autorizaria a exceção **não existia** em `.codeflow/decisions/` nem na
§8 da spec, embora o DoD global (§9) exija um dos dois. O avaliador foi explícito:
"não estou questionando o mérito da mudança", falta o registro.

Escolhida a **opção 1** das duas oferecidas pela avaliação (registrar a decisão), e
não a opção 2 (reverter os cinco decorators). O motivo está na decision: reverter
deixaria sem teto exatamente os cinco endpoints de maior custo unitário do sistema,
enquanto o FR-B4 exige rate limiting nos "endpoints de IA" sem restringir a método.

**Nesta tentativa nenhuma linha de código foi alterada** — o trabalho é de registro.

O conteúdo entregue na tentativa 1 permanece:

1. **Fail-fast de `SECRET_KEY`** — `Settings` ganhou um `model_validator(mode="after")`
   que recusa instanciar quando `APP_ENV` não é `development` e a chave está no valor
   default ou tem menos de 32 caracteres. A property `is_development`, que existia e
   não validava nada, passou a ser usada.
2. **Rate limiting** — `slowapi` nos endpoints públicos de `auth.py` (`register`,
   `login`, `forgot-password`), nos três POST de IA (`analyze-meal`, `analyze-photo`,
   `insights`) com `RATE_LIMIT_AI`, e nos cinco GET de IA que chamam o provedor com
   `RATE_LIMIT_AI_LEITURA`. Limites em `config.py` como settings, nunca hardcoded.
3. **Teto de payload** — `POST /reminders/batch` passou a rejeitar listas acima de
   `REMINDERS_BATCH_MAX_ITEMS` (50), além da lista vazia que já rejeitava.

## 2. O que mudou nesta tentativa

| Arquivo | Estado | Propósito |
|---------|--------|-----------|
| `.codeflow/decisions/2026-08-02-rate-limit-em-get-de-ia.md` | CRIADO | Registro da exceção ao escopo travado: por que os cinco GET recebem teto, por que `GET /ai/conversations` não recebe, de onde vem o 40/min, e as quatro alternativas descartadas (inclusive reverter). |
| `.codeflow/decisions/INDEX.md` | ALTERADO | Uma linha, no topo da tabela, com as tags `seguranca, rate-limiting, api, spec-002, fase-b3`. |
| `SPEC_002_VITRINE_EVAL_E_SANEAMENTO.md` (§5, B.3) | ALTERADO | O escopo travado passa a dizer "exceto leitura que chama o provedor de IA", com nota `Escopo corrigido (2026-08-02)` no mesmo formato já usado por A.2, A.3 e B.2. |
| `SPEC_002_VITRINE_EVAL_E_SANEAMENTO.md` (§8) | ALTERADO | **OQ11** registra a questão e a resolução, no padrão de OQ7–OQ10. |

Commit único: `e22d54f docs(seguranca): registra a decision do rate limit nos get de ia`.

**Nenhum arquivo de `backend/` ou `frontend/` foi tocado nesta tentativa** —
`git diff --name-only 5de94fe..e22d54f` devolve apenas os três arquivos acima.

## 3. Arquivos CRIADOS na tentativa 1 (inalterados)

| Arquivo | Propósito |
|---------|-----------|
| `backend/app/core/rate_limit.py` | Instância única do `Limiter` e a função de chave de contagem `client_key`. |
| `backend/tests/unit/test_config_secret_key.py` | Validador de `SECRET_KEY` nos dois ramos (AC-7). |
| `backend/tests/unit/test_rate_limit_key.py` | Chave de contagem atrás e fora de proxy reverso. |
| `backend/tests/integration/test_limites_requisicao.py` | 429 em `login` e em `analyze-meal` (AC-8), 429 nos GET de IA, ausência de teto em `GET /ai/conversations`, e teto do batch de lembretes. |

## 4. Arquivos ALTERADOS na tentativa 1 (inalterados)

| Arquivo | O que mudou |
|---------|-------------|
| `backend/app/core/config.py` | `INSECURE_SECRET_KEY`/`MIN_SECRET_KEY_LENGTH` como constantes; `_validate_secret_key`; settings `RATE_LIMIT_*` e `REMINDERS_BATCH_MAX_ITEMS`. |
| `backend/app/main.py` | Registro de `app.state.limiter` e do handler que traduz `RateLimitExceeded` em 429 com mensagem pt-BR. |
| `backend/app/api/v1/auth.py` | `@limiter.limit(...)` em `register`, `login` e `forgot_password`. |
| `backend/app/api/v1/ai.py` | `RATE_LIMIT_AI` nos três POST; `RATE_LIMIT_AI_LEITURA` nos cinco GET que chamam o provedor; `GET /ai/conversations` sem teto. |
| `backend/app/api/v1/reminders.py` | Teto de itens no batch. |
| `backend/pyproject.toml` | Dependência `slowapi>=0.1.9`. |
| `backend/uv.lock` | Relock (desvio 4). |
| `backend/tests/conftest.py` | Fixtures `rate_limiter_desligado` (autouse) e `rate_limiter_ligado` (desvio 2). |
| `backend/tests/unit/test_ai_endpoint_errors.py` | Passa um `Request` mínimo, exigido pela nova assinatura dos endpoints de IA (desvio 3). |
| `.env.example` | As 13 variáveis novas documentadas. |

## 5. Confirmação do REUSO e decisões de design

**REUSADO conforme o mapa da §4 da spec:**
- `backend/app/core/config.py` e a property `is_development` (`:86-88`), que a spec
  identificou como existente e não usada para validar — agora é o único ponto de
  decisão do fail-fast.
- O padrão de degradação silenciosa do Redis já estabelecido em `ai_client.py` e
  `auth_service.py`: o limitador roda com `swallow_errors=True`, de modo que um Redis
  fora do ar remove o limite mas não derruba o login.

**Decisões de design (tentativa 1, inalteradas):**
- **Chave de contagem ciente de proxy.** `client_key` lê o primeiro salto de
  `X-Forwarded-For` **apenas** quando `RATE_LIMIT_TRUST_FORWARDED_FOR` está ligado,
  porque sem proxy o cabeçalho é forjável e seria um caminho trivial de contorno.
  Default desligado; produção liga junto do Caddy (Fase E.4).
- **`headers_enabled=False`.** Os cabeçalhos `X-RateLimit-*` do slowapi exigem um
  parâmetro `response: Response` em cada endpoint decorado; injetá-lo em seis
  assinaturas só pelo cabeçalho não compensa. O 429 continua explícito no corpo.
- **Backend de contagem configurável.** `RATE_LIMIT_STORAGE_URI` vazio = memória do
  processo (dev/CI); produção com mais de um worker aponta para o Redis.

**Desvios da spec, com justificativa:**

1. **`backend/app/core/rate_limit.py` é arquivo novo, e a fase não declarava
   "Arquivos novos".** Necessário: `main.py` (handler de 429) e os routers
   (decorators) precisam da *mesma* instância de `Limiter`; colocá-la em `main.py`
   criaria import circular. Fica em `core/`, na mesma categoria de `core/security.py`
   e `core/deps.py`, não em `services/`.
2. **`backend/tests/conftest.py` alterado** (arquivo da fase B.1, já concluída). Sem
   desligar o limitador por padrão, uma suíte com vários logins estoura o limite por
   acúmulo entre testes independentes — foi medido. A fixture autouse desliga e zera
   a contagem; quem exercita o 429 religa explicitamente.
3. **`backend/tests/unit/test_ai_endpoint_errors.py` alterado.** O decorator do
   slowapi exige `request` na assinatura, e esses dois testes chamam
   `analyze_meal`/`analyze_photo` como função Python. O contrato HTTP não mudou.
4. **`backend/uv.lock` relockado.** Companheiro obrigatório de uma dependência nova.
   CI e Dockerfiles instalam por `pip install -e ".[dev]"`, não pelo lock.
5. **Rate limiting nos cinco GET de IA — desvio do escopo travado, agora registrado.**
   Era o achado BLOQUEANTE da tentativa 1. A exceção está em
   `.codeflow/decisions/2026-08-02-rate-limit-em-get-de-ia.md`, no texto do escopo
   travado da B.3 em §5 e em OQ11 da §8. Critério aplicado: **gasta token do
   provedor**, não "é método GET" — por isso `GET /ai/conversations`, leitura pura de
   banco, ficou de fora, com teste travando o desenho.
6. **Esta tentativa gerou uma decision, e `/execute-spec-phase` declara
   `gera_decision: no`.** Registro honesto da tensão, para o avaliador julgar: a
   tarefa do rework era **produzir o registro faltante**, exigido pelo DoD §9 da spec
   ("toda decisão de escopo … registrada aqui em §8 ou numa decision do framework") e
   pela constitution universal ("override genuíno exige uma decision arquitetural
   registrada **antes** da próxima invocação do workflow"). A avaliação atribuiu
   explicitamente a decision faltante ao executor. Não havia caminho que fechasse o
   BLOQUEANTE sem gerar o artefato — a alternativa era reverter o código, que a
   avaliação oferece como opção 2 e que foi descartada com justificativa na decision.
7. **A decision segue a convenção local do projeto**, não o schema canônico de
   ARTIFACTS_SPEC §2.5 (`workflow`, `status_decisão`, `supersede`, `relaciona-com`;
   seções `Decisões tomadas`/`Próximos passos sugeridos`). As 10 decisions existentes
   em `.codeflow/decisions/` usam frontmatter `data/titulo/status/tags/spec/fase` e
   seções `Contexto`/`Decisão`/`Alternativas descartadas`/`Consequência`/`Reprodução`,
   e o `INDEX.md` do projeto é uma tabela única. Vale a constitution universal:
   "seguir convenções existentes do projeto … consistência vence esperteza
   individual". Divergir criaria a décima-primeira decision com formato próprio.

**Nada fora do escopo foi tocado:** `backend/app/core/security.py` intocado (área de
alto risco), nenhuma migration criada ou alterada (NFR-7), nenhum gate com
`continue-on-error` ou allowlist.

## 6. Comandos rodados + saídas reais

Ambiente: container `caloria_backend` (`docker-compose.dev.yml` no ar), branch `dev`.
Os comandos abaixo são os que os alvos do Makefile executam dentro do container.

```text
$ bash ~/.codeflow/framework/core/scripts/run-structural.sh \
    .codeflow/specs/002-vitrine-eval-e-saneamento/SPEC_002_VITRINE_EVAL_E_SANEAMENTO.md
✓ ids de fase únicos (26 fases)
✓ heading de cada fase casa com o bullet `id`
✓ todos os slugs são kebab-case
✓ wave: multi com ao menos um id `<TRACK>.<n>`
✓ todo `id` em "Depende de" existe na §5
✓ cada track tem 3–8 fases
✓ grafo de dependências acíclico
✓ §5 estruturalmente válida
EXIT=0                       # a edição da §5 não quebrou a estrutura

$ docker compose -f docker-compose.dev.yml exec -T backend ruff check .
All checks passed!

$ docker compose -f docker-compose.dev.yml exec -T backend ruff format --check .
147 files already formatted

$ docker compose -f docker-compose.dev.yml exec -T backend mypy app/ evals/
Success: no issues found in 81 source files

$ docker compose -f docker-compose.dev.yml exec -T backend pytest \
    tests/unit/test_config_secret_key.py tests/unit/test_rate_limit_key.py \
    tests/integration/test_limites_requisicao.py -q
22 passed, 3 warnings in 13.58s          # os testes da fase (AC-7, AC-8)

$ docker compose -f docker-compose.dev.yml exec -T backend pytest --cov=app --cov-report=term -q
TOTAL                                      3204    862    73%
Required test coverage of 72.0% reached. Total coverage: 73.10%
581 passed, 1 skipped, 5 warnings in 97.30s (0:01:37)

$ git diff --name-only 5de94fe..e22d54f
.codeflow/decisions/2026-08-02-rate-limit-em-get-de-ia.md
.codeflow/decisions/INDEX.md
.codeflow/specs/002-vitrine-eval-e-saneamento/SPEC_002_VITRINE_EVAL_E_SANEAMENTO.md

$ git merge-base --is-ancestor 6115615058e2156a710afab5b05b873010ddb3e1 HEAD
(exit 0)                                  # sha_inicial da t1 é ancestral do HEAD
```

O único `skipped` é `tests/smoke_test.py:184` — sonda de ambiente que procura
Postgres em `localhost` a partir de dentro do container, já coberta por
`.codeflow/decisions/2026-08-02-smoke-test-como-sonda-de-ambiente.md`.

`make test-integration` e `make test-unit` não foram invocados pelo nome: os alvos
fazem `docker compose exec` a partir do host, e a suíte de integração inteira roda
dentro do `pytest` completo acima, com zero falhas.

## 7. Checklist dos ACs / critério de conclusão

- [x] **AC-7** — `APP_ENV` fora de `development` + `SECRET_KEY` default aborta com
      erro explícito; em `development` inicia normalmente.
      *Evidência:* `tests/unit/test_config_secret_key.py`, cobrindo default inseguro
      em `production`/`staging`/`test`, chave curta, chave válida e a mensagem
      nomeando o `APP_ENV`. Dentro dos 22 passed acima.
- [x] **AC-8** — excedente em `POST /api/v1/auth/login` devolve 429; idem
      `POST /api/v1/ai/analyze-meal`.
      *Evidência:* `TestRateLimitLogin::test_excedente_recebe_429`,
      `TestRateLimitLogin::test_tentativa_invalida_tambem_conta`,
      `TestRateLimitIA::test_analyze_meal_excedente_recebe_429`.
- [x] **Escopo travado — achado B3-BLK-1 fechado.** A exceção está registrada nos
      dois lugares que o DoD §9 aceita: decision do framework
      (`.codeflow/decisions/2026-08-02-rate-limit-em-get-de-ia.md`, indexada) **e**
      §8 da spec (OQ11), mais a nota no próprio escopo travado da B.3 em §5.
- [x] **`make test-integration` verde** — a suíte de integração roda dentro do
      `pytest` completo: `581 passed, 1 skipped`.
- [x] **`mypy app/` limpo** — `Success: no issues found in 81 source files`
      (`app/` + `evals/`, que entrou no comando na C.7).
- [x] **NFR-1** — `ruff check .` e `ruff format --check .` limpos.
- [x] **NFR-7** — nenhuma migration tocada; nesta tentativa nenhum arquivo de código.
- [x] **NFR-4** — o commit passou pelo hook `Detect hardcoded secrets` (gitleaks com
      `.gitleaks.toml`): `Passed`.

## 8. Dúvidas para o avaliador

1. **Alterar o texto do escopo travado em §5 é aceitável, ou o registro deveria
   viver só na decision + §8?** A avaliação sugeriu literalmente "atualizar o texto
   do escopo travado da B.3 em §5 da spec para refletir a exceção" (correção 1), e o
   formato usado é o mesmo já aplicado em A.2, A.3 e B.2 por rodadas anteriores. Fica
   a ressalva: editar um gate depois de violá-lo é um movimento que merece olhar
   cético mesmo quando a decisão está registrada — o registro é que o torna
   auditável, não legítimo por si.
2. **Chave de contagem por IP, não por `user_id`** (sugestão 2 da avaliação
   anterior). Continua por IP. Ampliar para `user_id` exigiria uma segunda `key_func`
   e tocaria `core/rate_limit.py` e todos os decorators — trabalho de desenho, não de
   registro, e fora do escopo de um rework de achado BLOQUEANTE. Registrado como
   débito na decision e em OQ11. Fase própria ou nova spec?
3. **`headers_enabled=False` deixa o cliente sem `Retry-After`** (sugestão 1 da
   avaliação). Não alterado: a sugestão aponta o proxy (Caddy, Fase E.4) como lugar
   certo para expor o cabeçalho, e a Fase E.4 ainda não rodou.

---
spec: 002-vitrine-eval-e-saneamento
fase: B.3
slug_fase: hardening-config
status: executado
tentativa: 1
reprovacoes: 0
sha_inicial: 6115615058e2156a710afab5b05b873010ddb3e1
sha_final: d8cc463
range: 6115615058e2156a710afab5b05b873010ddb3e1..d8cc463
---

# FASE B.3 — Relatório de execução

## 1. Resumo do que foi feito

Três buracos fechados, todos em código de produção do backend:

1. **Fail-fast de `SECRET_KEY`** — `Settings` ganhou um `model_validator(mode="after")`
   que recusa instanciar quando `APP_ENV` não é `development` e a chave está no valor
   default ou tem menos de 32 caracteres. A property `is_development`, que existia e
   não validava nada, passou a ser usada.
2. **Rate limiting** — `slowapi` nos endpoints públicos de `auth.py` (`register`,
   `login`, `forgot-password`) e nos três endpoints de IA de `ai.py` que consomem
   tokens do provedor (`analyze-meal`, `analyze-photo`, `insights`). Limites em
   `config.py` como settings, nunca hardcoded.
3. **Teto de payload** — `POST /reminders/batch` passou a rejeitar listas acima de
   `REMINDERS_BATCH_MAX_ITEMS` (50), além da lista vazia que já rejeitava.

## 2. Arquivos CRIADOS

| Arquivo | Propósito |
|---------|-----------|
| `backend/app/core/rate_limit.py` | Instância única do `Limiter` e a função de chave de contagem `client_key`. |
| `backend/tests/unit/test_config_secret_key.py` | Validador de `SECRET_KEY` nos dois ramos (AC-7). |
| `backend/tests/unit/test_rate_limit_key.py` | Chave de contagem atrás e fora de proxy reverso. |
| `backend/tests/integration/test_limites_requisicao.py` | 429 em `login` e em `analyze-meal` (AC-8) e teto do batch de lembretes. |

## 3. Arquivos ALTERADOS

| Arquivo | O que mudou |
|---------|-------------|
| `backend/app/core/config.py` | `INSECURE_SECRET_KEY`/`MIN_SECRET_KEY_LENGTH` como constantes; `_validate_secret_key`; settings `RATE_LIMIT_*` e `REMINDERS_BATCH_MAX_ITEMS`. |
| `backend/app/main.py` | Registro de `app.state.limiter` e do handler que traduz `RateLimitExceeded` em 429 com mensagem pt-BR. |
| `backend/app/api/v1/auth.py` | `@limiter.limit(...)` em `register`, `login` e `forgot_password`; parâmetro `request: Request` exigido pelo decorator. |
| `backend/app/api/v1/ai.py` | `@limiter.limit(settings.RATE_LIMIT_AI)` em `analyze_meal`, `analyze_photo` e `generate_insight`. |
| `backend/app/api/v1/reminders.py` | Teto de itens no batch. |
| `backend/pyproject.toml` | Dependência `slowapi>=0.1.9`. |
| `backend/uv.lock` | Relock (ver desvio 4). |
| `backend/tests/conftest.py` | Fixtures `rate_limiter_desligado` (autouse) e `rate_limiter_ligado` (ver desvio 2). |
| `backend/tests/unit/test_ai_endpoint_errors.py` | Passa um `Request` mínimo, exigido pela nova assinatura dos endpoints de IA (ver desvio 3). |

## 4. Confirmação do REUSO e decisões de design

**REUSADO conforme o mapa da §4 da spec:**
- `backend/app/core/config.py` e a property `is_development` (`:86-88`), que a spec
  identificou como existente e não usada para validar — agora é o único ponto de
  decisão do fail-fast.
- O padrão de degradação silenciosa do Redis já estabelecido em `ai_client.py` e
  `auth_service.py`: o limitador roda com `swallow_errors=True`, de modo que um Redis
  fora do ar remove o limite mas não derruba o login.

**Decisões de design:**
- **Chave de contagem ciente de proxy.** `get_remote_address` do slowapi devolve o
  peer TCP. Atrás do Caddy, isso é o IP do proxy, e todos os usuários cairiam no
  mesmo balde — o limite viraria um teto global e derrubaria usuários legítimos.
  `client_key` lê o primeiro salto de `X-Forwarded-For` **apenas** quando
  `RATE_LIMIT_TRUST_FORWARDED_FOR` está ligado, porque sem proxy o cabeçalho é
  forjável e seria um caminho trivial de contorno. Default desligado (seguro);
  produção liga junto do Caddy (Fase E.4).
- **`headers_enabled=False`.** Os cabeçalhos `X-RateLimit-*` do slowapi exigem um
  parâmetro `response: Response` em cada endpoint decorado. Como todos devolvem
  modelos Pydantic, ligá-los estourava com
  `parameter 'response' must be an instance of starlette.responses.Response` em 10
  testes de integração. Injetar `Response` em seis assinaturas só pelo cabeçalho não
  compensa; o 429 continua explícito no corpo.
- **Backend de contagem configurável.** `RATE_LIMIT_STORAGE_URI` vazio = memória do
  processo (dev/CI); produção com mais de um worker aponta para o Redis com o prefixo
  `async+` exigido pelo `limits`.

**Desvios da spec, com justificativa:**

1. **`backend/app/core/rate_limit.py` é arquivo novo, e a fase não declarava
   "Arquivos novos".** Necessário: `main.py` (handler de 429) e os routers
   (decorators) precisam da *mesma* instância de `Limiter`; colocá-la em `main.py`
   criaria import circular com os routers. Fica em `core/` — e não em `services/` —
   porque é infraestrutura de transporte, na mesma categoria de `core/security.py` e
   `core/deps.py`, não lógica de negócio.
2. **`backend/tests/conftest.py` alterado** (arquivo da fase B.1, já concluída). O
   limitador conta por IP e o cliente ASGI de teste é sempre o mesmo IP: sem desligar
   por padrão, uma suíte com vários logins estoura o limite por acúmulo entre testes
   independentes — foi medido, `test_forgot_password_uniforme.py` quebrou. A fixture
   autouse desliga e zera a contagem; quem exercita o 429 religa explicitamente.
   Nenhuma fixture existente foi alterada.
3. **`backend/tests/unit/test_ai_endpoint_errors.py` alterado.** O decorator do
   slowapi exige `request` na assinatura, e esses dois testes chamam
   `analyze_meal`/`analyze_photo` como função Python. Passaram a construir um
   `Request` mínimo. O contrato HTTP não mudou — mudou a assinatura Python interna.
4. **`backend/uv.lock` relockado.** Companheiro obrigatório de uma dependência nova.
   O lock estava defasado e o relock removeu entradas mortas (`google-genai`,
   `google-auth`, `pyasn1-modules`, `tenacity`) de uma migração de provedor já feita.
   CI e Dockerfiles instalam por `pip install -e ".[dev]"`, não pelo lock, então isso
   não altera o que roda.
5. **Rate limiting nos endpoints de IA restrito aos três POST.** O escopo travado da
   fase proíbe rate limiting em "endpoints autenticados de leitura", e os cinco GET
   de `ai.py` (`suggest-meal`, `patterns`, `nutritional-alerts`, `goal-adjustment`,
   `monthly-report`) são leituras — embora também consumam tokens do provedor. A
   restrição bloqueante venceu. **Lacuna FECHADA em 2026-08-02**, por decisão do
   owner: os cinco GET ganharam `RATE_LIMIT_AI_LEITURA` (40/minute), mais folgado
   que o dos POST porque o dashboard dispara vários por carga.
   `GET /ai/conversations` ficou de fora por desenho — é leitura pura de banco e
   não gasta token. Ver `CORRECOES-2026-08-02-POS-VALIDACAO.md` §4.
6. **`.env.example` NÃO foi alterado — pendência de owner.** O arquivo está fora do
   alcance de leitura e escrita desta sessão (bloqueado por política de permissão).
   As entradas a acrescentar, logo abaixo de `SECRET_KEY` (`:29`):

   ```
   # Rate limiting — expressões no formato "N/period" (limits)
   RATE_LIMIT_ENABLED=true
   RATE_LIMIT_LOGIN=10/minute
   RATE_LIMIT_REGISTER=5/minute
   RATE_LIMIT_FORGOT_PASSWORD=5/minute
   RATE_LIMIT_AI=20/minute
   # Vazio = contagem em memória do processo. Com mais de um worker, usar Redis:
   # RATE_LIMIT_STORAGE_URI=async+redis://redis:6379/1
   RATE_LIMIT_STORAGE_URI=
   # Ligar SOMENTE com proxy reverso confiável à frente (Caddy em produção)
   RATE_LIMIT_TRUST_FORWARDED_FOR=false

   # Teto de itens em POST /api/v1/reminders/batch
   REMINDERS_BATCH_MAX_ITEMS=50
   ```

**Nada fora do escopo foi tocado:** `backend/app/core/security.py` não foi alterado
(área de alto risco declarada na constitution), nenhuma migration foi criada ou
alterada (NFR-7), e nenhum gate recebeu `continue-on-error` ou allowlist.

## 5. Comandos rodados + saídas reais

Ambiente: **não há Docker, Postgres nem Redis nesta máquina**. Para não entregar a
fase com os testes de integração por rodar, subi Postgres 16.2 e Redis 7 em espaço de
usuário (`pgserver` e `redislite`, instalados apenas no `.venv`, **fora** do
`pyproject.toml`) e apontei `TEST_DATABASE_URL`/`REDIS_URL` para eles. Os alvos do
Makefile (`make test-unit`, `make test-integration`) fazem `docker compose exec` e
portanto não rodam aqui — os comandos abaixo são os mesmos que eles executam dentro
do container.

```text
$ ruff check .
All checks passed!

$ ruff format --check .
123 files already formatted

$ mypy app/
Success: no issues found in 73 source files

$ pytest tests/unit/ -q            # sem nenhuma infraestrutura no ar
211 passed in 2.78s

$ pytest -q --ignore=tests/smoke_test.py   # unit + integration
312 passed, 5 skipped, 3 warnings in 49.21s

$ pytest tests/integration/test_limites_requisicao.py -q
7 passed
```

`tests/smoke_test.py::test_ai_client` foi excluído da corrida acima: é a sonda de
ambiente de OQ9, fala com a API real da Groq e falha aqui com
`groq.APIConnectionError` por restrição de rede da sessão — comportamento
pré-existente, sem relação com esta fase.

Antes do ajuste de `headers_enabled`, a suíte de integração acusou 10 falhas; depois,
1 (o `forgot-password` estourando o limite por acúmulo). As duas causas estão
descritas nos desvios 2 e nas decisões de design, e as duas foram corrigidas no
código, não silenciadas.

## 6. Checklist dos ACs / critério de conclusão

- [x] **AC-7** — `APP_ENV` fora de `development` + `SECRET_KEY` default aborta com
      erro explícito; em `development` inicia normalmente.
      *Evidência:* `tests/unit/test_config_secret_key.py`, 7 testes, cobrindo default
      inseguro em `production`/`staging`/`test`, chave curta, chave válida e a
      mensagem nomeando o `APP_ENV`.
- [x] **AC-8** — mais requisições que o limite a `POST /api/v1/auth/login` devolve
      429; idem `POST /api/v1/ai/analyze-meal`.
      *Evidência:* `TestRateLimitLogin::test_excedente_recebe_429`,
      `TestRateLimitLogin::test_tentativa_invalida_tambem_conta` e
      `TestRateLimitIA::test_analyze_meal_excedente_recebe_429`. O teste de IA
      neutraliza o provedor (`ia_stubada`) porque `_require_ai` aborta com 503 antes
      do corpo do endpoint quando não há `GROQ_API_KEY`, e o limite só conta o que
      chega ao corpo.
- [x] **`make test-integration` verde** — 94 testes de integração passam contra o
      Postgres/Redis de espaço de usuário descrito em §5. O alvo do Makefile em si
      não roda aqui (exige Docker).
- [x] **`mypy app/` limpo** — `Success: no issues found in 73 source files`.
- [x] O CI continua subindo a app com a `SECRET_KEY` de teste: `ci.yml:83` define
      uma chave de 43 caracteres e não define `APP_ENV`, que fica em `development` —
      o validador não dispara. Nenhuma mudança foi necessária em `ci.yml`.
- [x] **`.env.example` documentado** — feito em 2026-08-02, na rodada de
      validação com Docker, quando o arquivo passou a estar ao alcance da sessão.
      As 13 variáveis novas estão lá.

## 7. Dúvidas para o avaliador

1. ~~Cinco GET de `ai.py` seguem sem teto~~ — **RESOLVIDO** em 2026-08-02.
2. **Chave de contagem por IP, não por usuário.** Para os endpoints autenticados de
   IA, `user_id` seria a chave natural. Ficou por IP para manter uma única
   `key_func`. Aceitável?
3. ~~`.env.example` não pôde ser tocado~~ — **RESOLVIDO** em 2026-08-02.

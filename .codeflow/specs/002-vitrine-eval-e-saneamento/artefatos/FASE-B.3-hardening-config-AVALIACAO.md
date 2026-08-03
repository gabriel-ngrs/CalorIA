---
spec: 002-vitrine-eval-e-saneamento
fase: B.3
slug_fase: hardening-config
tentativa: 1
veredito: REPROVADO
score: 9.1
threshold: 8.5
range_avaliado: 6115615058e2156a710afab5b05b873010ddb3e1..d8cc463
---

# FASE B.3 — Avaliação independente

## 1. Veredito e score

**Veredito:** REPROVADO · **Score:** 9.1 / threshold 8.5

O score está acima do threshold e o código entregue é de boa qualidade. A
reprovação vem de **um BLOQUEANTE**, que sempre reprova qualquer que seja o
score: a rodada de correção de 2026-08-02 fez exatamente o que o **escopo
travado desta fase declara como violação BLOQUEANTE**, e a decisão de escopo que
a autorizaria não está registrada em lugar nenhum do framework. A correção é
barata — registrar a decision — mas não pode ser presumida pelo avaliador.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 3 | AC-7 e AC-8 satisfeitos (`tests/unit/test_config_secret_key.py`, `tests/integration/test_limites_requisicao.py`, 7 passed). Mas `api/v1/ai.py:164,187,207,227,246` introduz rate limiting em cinco GET autenticados de leitura — vedado em SPEC §5 B.3 ("Não introduzir rate limiting em endpoints autenticados de leitura"), sem decision. |
| 2 | Arquitetura e direção de dependências | 3 | 5 | `core/rate_limit.py` isola a instância única do `Limiter`; `main.py` registra o handler, os routers só decoram. Evita o import circular que a alternativa criaria. Categoria correta (`core/`, ao lado de `security.py`/`deps.py`), não `services/`. |
| 3 | Segurança / LGPD / multi-tenant | 3 | 4 | Fail-fast de `SECRET_KEY` fecha AUD-039 (`core/config.py`, validador `mode="after"`). `client_key` só confia em `X-Forwarded-For` com `RATE_LIMIT_TRUST_FORWARDED_FOR` ligado — default seguro. `core/security.py` intocado (área de alto risco). Desconto pelo item bloqueante, que é decisão de superfície de API sem registro. |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | Reusa `is_development` (que existia e não validava nada) e o padrão de degradação silenciosa do Redis já estabelecido em `ai_client.py` (`swallow_errors=True`). Nenhuma fixture nova em `conftest.py` além das duas do limitador. |
| 5 | Padrões de domínio/aplicação | 2 | 5 | Limites como settings (`RATE_LIMIT_*`, `REMINDERS_BATCH_MAX_ITEMS`), nunca hardcoded — como a fase exige. Endpoints continuam finos. |
| 6 | Local e nomes dos arquivos | 2 | 5 | `core/rate_limit.py`, `tests/unit/test_config_secret_key.py`, `tests/unit/test_rate_limit_key.py`, `tests/integration/test_limites_requisicao.py` — todos no lugar e com nome que declara intenção. |
| 7 | Qualidade de código | 2 | 5 | `ruff check .` limpo, `ruff format --check .` limpo, `mypy app/ evals/` limpo em 81 arquivos (saídas em §6). |
| 8 | Testes e cobertura | 2 | 5 | 429 exercitado nos dois caminhos exigidos (login e analyze-meal), teto do batch coberto, chave de contagem coberta atrás e fora de proxy. `tests/integration/test_limites_requisicao.py` passa junto da suíte completa. |
| 9 | Migration safety (se aplicável) | 2 | [—] | Nenhuma migration tocada — `git diff --name-only d8cc463~1..HEAD -- backend/alembic/` devolve vazio (NFR-7). |

Média ponderada das 8 dimensões aplicáveis: 91/20 = 4.55 → **9.1**.

## 3. Achados BLOQUEANTES

**B3-BLK-1 — `backend/app/api/v1/ai.py:164,187,207,227,246`: rate limiting em
endpoint autenticado de leitura, que o escopo travado da fase declara violação
BLOQUEANTE, sem decision registrada.**

O bloco da fase em `SPEC_002_VITRINE_EVAL_E_SANEAMENTO.md:707-708` diz, sob
"Escopo travado / violações BLOQUEANTES":

> Não introduzir rate limiting em endpoints autenticados de leitura.

A primeira entrega respeitou isso e registrou a lacuna (desvio 5 do EXECUCAO). A
rodada de 2026-08-02 reverteu a restrição: os cinco GET (`suggest-meal`,
`patterns`, `nutritional-alerts`, `goal-adjustment`, `monthly-report`) ganharam
`@limiter.limit(settings.RATE_LIMIT_AI_LEITURA)`. Verificado no código, não no
relatório.

O EXECUCAO (`:108-110`) e `CORRECOES-2026-08-02-POS-VALIDACAO.md` §4 atribuem a
mudança a "decisão do owner". Procurei o registro e **não existe**:

```text
$ grep -ril "rate.limit\|leitura" .codeflow/decisions/
.codeflow/decisions/2026-08-02-regras-proprias-gitleaks.md   # outro assunto
.codeflow/decisions/2026-07-07-lote-bugs-incidentais-v1.md   # outro assunto

$ grep -n -i "AI_LEITURA\|endpoints autenticados de leitura" \
    .codeflow/specs/002-vitrine-eval-e-saneamento/SPEC_002_*.md
(sem resultado)
```

O DoD global da spec (§9, "Itens globais transversais") exige: *"Toda decisão de
escopo tomada durante a execução está registrada aqui em §8 ou numa decision do
framework."* Um documento de correções em `artefatos/` não é nenhum dos dois — é
relatório, não registro de decisão. E a constitution universal é explícita: gate
duro não se destrava por autorização falada; override genuíno exige decision
registrada **antes** da próxima execução.

**Não estou questionando o mérito da mudança** — limitar GET que gasta token do
provedor é defensável, e o teto de 40/min mais folgado que o dos POST é bem
calibrado. O que falta é o registro que transforma "o owner mandou" em decisão
auditável, e que impede que a próxima leitura da spec conclua que o escopo
travado foi simplesmente ignorado.

**Correção sugerida** (escolher uma):

1. Criar `.codeflow/decisions/2026-08-02-rate-limit-em-get-de-ia.md` registrando:
   a restrição original, por que ela foi revista (os cinco GET consomem token do
   provedor, ao contrário de `GET /ai/conversations`, que é leitura pura de
   banco e ficou de fora por desenho), o teto escolhido e a justificativa dos
   40/min; indexar em `.codeflow/decisions/INDEX.md` com as tags `seguranca`,
   `rate-limiting`, `spec-002`, `fase-b3`; e atualizar o texto do escopo travado
   da B.3 em §5 da spec para refletir a exceção. Depois reavaliar.
2. Ou reverter os cinco decorators, voltando ao estado da primeira entrega, e
   tratar o rate limiting de leitura numa fase própria.

## 4. Achados IMPORTANTES

Nenhum.

## 5. Sugestões

- **`headers_enabled=False`** é a escolha certa pelo motivo certo (evitar injetar
  `Response` em seis assinaturas), mas o cliente perde o `Retry-After`. Se a E.4
  colocar o Caddy à frente, vale expor o cabeçalho no proxy em vez de no app.
- **Chave de contagem por IP nos endpoints autenticados** (dúvida 2 do EXECUCAO):
  para os endpoints de IA, `user_id` é a chave natural — dois usuários atrás do
  mesmo NAT hoje dividem o balde. Uma `key_func` que use `user_id` quando houver
  token e caia para IP quando não houver resolve sem multiplicar limiters.
- A fixture autouse `rate_limiter_desligado` significa que o caminho ligado só é
  exercitado nos testes que religam explicitamente. Está correto e documentado,
  mas vale um comentário no `conftest.py` apontando isso para quem escrever teste
  novo de endpoint limitado.

## 6. Comandos rodados + saídas reais

Ambiente: container `caloria_backend` (Docker no ar), branch `dev`, HEAD
`e3a974a`. `git merge-base --is-ancestor d8cc463 HEAD` → OK.

```text
$ docker compose -f docker-compose.dev.yml exec -T backend ruff check .
All checks passed!

$ docker compose -f docker-compose.dev.yml exec -T backend ruff format --check .
147 files already formatted

$ docker compose -f docker-compose.dev.yml exec -T backend mypy app/ evals/
Success: no issues found in 81 source files

$ docker compose -f docker-compose.dev.yml exec -T backend pytest --cov=app --cov-report=term -q
TOTAL                                      3204    862    73%
Required test coverage of 72.0% reached. Total coverage: 73.10%
581 passed, 1 skipped, 5 warnings in 88.01s (0:01:28)

# os limites, isolados
$ ... pytest tests/integration/test_limites_requisicao.py -q
(passa dentro da suíte completa acima; nenhum teste de limite falha)

# escopo travado, verificado no código e não no relatório
$ grep -n "limiter.limit\|^@router" backend/app/api/v1/ai.py
47:@router.post("/analyze-meal", ...)
48:@limiter.limit(settings.RATE_LIMIT_AI)
78:@router.post("/analyze-photo", ...)
79:@limiter.limit(settings.RATE_LIMIT_AI)
108:@router.post("/insights", ...)
109:@limiter.limit(settings.RATE_LIMIT_AI)
149:@router.get("/conversations", ...)          <- sem teto, por desenho
163:@router.get("/suggest-meal", ...)
164:@limiter.limit(settings.RATE_LIMIT_AI_LEITURA)      <- VIOLAÇÃO
186:@router.get("/patterns", ...)
187:@limiter.limit(settings.RATE_LIMIT_AI_LEITURA)      <- VIOLAÇÃO
206:@router.get("/nutritional-alerts", ...)
207:@limiter.limit(settings.RATE_LIMIT_AI_LEITURA)      <- VIOLAÇÃO
226:@router.get("/goal-adjustment", ...)
227:@limiter.limit(settings.RATE_LIMIT_AI_LEITURA)      <- VIOLAÇÃO
245:@router.get("/monthly-report", ...)
246:@limiter.limit(settings.RATE_LIMIT_AI_LEITURA)      <- VIOLAÇÃO

$ git show HEAD:.env.example | grep -c "RATE_LIMIT\|REMINDERS_BATCH\|GROQ_"
20   # as 13 variáveis novas estão documentadas (desvio 6 do EXECUCAO, fechado)

$ gitleaks detect --config .gitleaks.toml --log-opts="d8cc463~1..HEAD"
22 commits scanned.  no leaks found          # NFR-4

$ git diff --name-only d8cc463~1..HEAD -- backend/alembic/
(vazio)                                       # NFR-7

$ git status --short
(limpo)
```

## 7. Itens da fase / DoD não atendidos

- **Escopo travado violado** (B3-BLK-1). É o único item.
- `make test-integration` como alvo do Makefile não foi rodado isoladamente pelo
  avaliador; a suíte de integração inteira roda dentro do `pytest` completo
  acima, com zero falhas — cobre o gate com folga.
- Confirmação de que o CI reprova de fato no GitHub Actions continua dependendo
  de push (ação do owner). Não conta contra esta fase: o gate declarado é
  `make test-integration` verde e `mypy app/` limpo, ambos verificados.

## 8. Divergências entre o relatório e o código real

1. **`.env.example`** — o EXECUCAO §4 desvio 6 e §7 dúvida 3 registram o arquivo
   como "fora do alcance da sessão" e depois como resolvido. Verificado:
   resolvido de fato, 20 linhas casando `RATE_LIMIT|REMINDERS_BATCH|GROQ_`. Sem
   divergência.
2. **Contagem de testes** — o EXECUCAO §5 reporta `312 passed, 5 skipped` num
   ambiente sem Docker. No ambiente real medido agora: `581 passed, 1 skipped`.
   A diferença é de ambiente e de fases posteriores, não de defeito. O único
   `skipped` é `tests/smoke_test.py:184` (sonda de ambiente que procura Postgres
   em `localhost` a partir de dentro do container) — comportamento conhecido e
   já registrado em decision própria.
3. **`mypy app/`** — o relatório cita "73 source files"; hoje são 81, porque
   `evals/` entrou no comando na C.7. Sem divergência de conteúdo.

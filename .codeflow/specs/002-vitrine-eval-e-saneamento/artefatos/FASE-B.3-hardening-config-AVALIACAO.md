---
spec: 002-vitrine-eval-e-saneamento
fase: B.3
slug_fase: hardening-config
tentativa: 2
veredito: APROVADO
score: 9.7
threshold: 8.5
range_avaliado: 6115615058e2156a710afab5b05b873010ddb3e1..e22d54f68743d789262099d4f2527e0bda2d109d
---

# FASE B.3 — Avaliação independente (tentativa 2)

## 1. Veredito e score

**Veredito:** APROVADO · **Score:** 9.7 / threshold 8.5

O achado B3-BLK-1 da tentativa 1 está fechado. A exceção ao escopo travado está
registrada nos dois lugares que o DoD §9 aceita — decision do framework, indexada,
**e** §8 da spec (OQ11) — mais a nota no próprio texto do escopo travado em §5.
Nenhuma linha de código de produção foi tocada nesta tentativa; o rework é
exclusivamente de registro, que era exatamente o que faltava.

Verifiquei cada afirmação factual da decision contra o código, e todas se
sustentam — inclusive a mais fácil de errar, o "quatro consultas por carga" que
dimensiona o 40/min.

**Sobre a dúvida 1 do executor**, que merece resposta direta: editar o texto de um
gate depois de violá-lo é legítimo **aqui** por uma razão específica, e o ceticismo
que o executor pediu tem um teste objetivo. Ver §5.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 5 | AC-7 e AC-8 verificados (22 passed nos três arquivos de teste da fase). A exceção ao escopo travado está registrada em `decisions/2026-08-02-rate-limit-em-get-de-ia.md`, indexada em `decisions/INDEX.md`, em `SPEC:708-717` (nota datada) e em OQ11 (`SPEC:1509-1523`). O critério da exceção é **testável**, não retórico: "gasta token do provedor", com `GET /ai/conversations` como caso isento travado por teste. |
| 2 | Arquitetura e direção de dependências | 3 | 5 | Inalterada desde a t1: `core/rate_limit.py` isola a instância única do `Limiter`, evitando o import circular que `main.py` criaria. Categoria correta (`core/`, ao lado de `security.py`/`deps.py`). |
| 3 | Segurança / LGPD / multi-tenant | 3 | 4 | Fail-fast de `SECRET_KEY` fecha AUD-039; `core/security.py` intocado. Os cinco endpoints de maior custo unitário do sistema seguem protegidos, agora com registro auditável. Desconto pelo débito declarado: a contagem é por IP (`core/rate_limit.py`), então usuários atrás do mesmo NAT dividem o balde de 40/min em endpoints que passaram a poder devolver 429. Está registrado como risco residual na decision e em OQ11 — é débito conhecido, não defeito oculto. |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | Reusa `is_development` e o padrão de degradação silenciosa do Redis de `ai_client.py`. O rework não criou artefato paralelo: usou os canais de registro que o framework já define. |
| 5 | Padrões de domínio/aplicação | 2 | 5 | Limites como settings, nunca hardcoded. A nota de escopo em §5 segue o formato já usado por A.2, A.3 e B.2; OQ11 segue o padrão de OQ7–OQ10; a decision segue a convenção local (desvio 7, justificado — ver §5). |
| 6 | Local e nomes dos arquivos | 2 | 5 | `decisions/<data>-<titulo-kebab>.md` como as outras dez; nome descreve a decisão, não a fase. |
| 7 | Qualidade de código | 2 | 5 | `ruff check .` limpo, `ruff format --check .` 147 arquivos, `mypy app/ evals/` limpo em 81 arquivos (§6). |
| 8 | Testes e cobertura | 2 | 5 | 22 passed nos testes da fase; suíte completa `581 passed, 1 skipped` com 73,10% contra piso de 72%. O desenho da exceção tem teste dedicado (`test_conversations_nao_tem_teto_de_ia`), o que impede que alguém "uniformize" os GET no futuro sem quebrar a suíte. |
| 9 | Migration safety (se aplicável) | 2 | [—] | Nenhuma migration tocada — `git diff --name-only 5de94fe..HEAD -- backend/alembic/` devolve vazio (NFR-7). Nesta tentativa, nenhum arquivo de código. |

Média ponderada das 8 dimensões aplicáveis: 97/20 = 4.85 → **9.7**.

## 3. Achados BLOQUEANTES

Nenhum. **B3-BLK-1 está fechado.**

Verificação do fechamento, item a item do que a t1 exigiu:

| Exigido pela t1 | Estado | Evidência |
|---|---|---|
| Decision registrando a restrição original e por que foi revista | feito | `decisions/2026-08-02-rate-limit-em-get-de-ia.md`, seções Contexto e Decisão |
| Teto escolhido e justificativa dos 40/min | feito | seção "Por que 40/minute e não o mesmo 20/minute dos POST" |
| Indexada com tags `seguranca`, `rate-limiting`, `spec-002`, `fase-b3` | feito | `decisions/INDEX.md`, linha 13 — inclui também `api` |
| Texto do escopo travado da B.3 em §5 atualizado | feito | `SPEC:708-717`, nota `Escopo corrigido (2026-08-02)` |
| Registro em §8 da spec | feito (além do pedido) | OQ11, `SPEC:1509-1523` |

## 4. Achados IMPORTANTES

Nenhum.

Considerei três candidatos e descartei os três, com o motivo:

- **Desvio 6 — a tentativa gerou uma decision sob um workflow com
  `gera_decision: no`.** Confirmei a premissa
  (`~/.codeflow/framework/library/workflows/execute-spec-phase.md:6` traz
  `gera_decision: no`). Não é violação: a flag descreve se o workflow **rotineiramente**
  produz decisions, não uma proibição de produzir o artefato que fecha um achado
  bloqueante. O DoD §9 da spec e a constitution universal exigem a decision, e a
  constitution vence frontmatter de workflow em caso de conflito. Além disso, a
  avaliação da t1 atribuiu a decision explicitamente ao executor, e a constitution
  pede que o override seja registrado **antes** da próxima invocação do workflow —
  que é exatamente a ordem em que aconteceu (`e22d54f` precede esta avaliação).
  Registrar a tensão em vez de silenciá-la é a conduta certa.
- **Desvio 7 — a decision segue a convenção local, não o schema canônico de
  ARTIFACTS_SPEC §2.5.** Confirmei: as decisions existentes usam frontmatter
  `data/titulo/status/tags` e seções `Contexto`/`Decisão`/…, e o `INDEX.md` do
  projeto é uma tabela única. A constitution universal é explícita — "seguir
  convenções existentes do projeto mesmo quando achar que tem abordagem melhor;
  consistência vence esperteza individual". A escolha está certa e justificada.
- **Chave por IP e ausência de `Retry-After`.** São débitos de desenho, não de
  registro, e a t1 os classificou como sugestões, não achados. Ficaram registrados
  na decision, em OQ11 e na §8 do relatório. Correto mantê-los fora de um rework
  cujo escopo era o BLOQUEANTE.

## 5. Sugestões

**Resposta à dúvida 1 — quando editar um gate depois de violá-lo é legítimo.**

O executor levanta a questão certa e não se autoabsolve. A resposta tem um teste
objetivo, e vale registrá-lo porque o precedente vai ser reusado:

> Editar o texto de um escopo travado é legítimo quando a restrição repousava numa
> **premissa factual que se revelou falsa**. É ilegítimo quando a restrição
> continua factualmente correta e apenas se mostrou **inconveniente**.

Aqui a premissa era "GET autenticado = leitura barata de banco". Ela é falsa para
estes cinco endpoints, e a falsidade é verificável em uma linha de código: os cinco
dependem de `_require_ai` e chamam `get_ai_client()`. Não é interpretação — é fato
do código, e o contraexemplo no mesmo arquivo (`GET /ai/conversations`, que **não**
tem nenhum dos dois e ficou sem teto) prova que o critério aplicado foi "gasta
token", não "é GET". Some-se a isso que o **FR-B4 nunca restringiu por método** —
confirmei em `SPEC:235-236`: *"Os endpoints públicos de autenticação e os endpoints
de IA devem ter rate limiting."* O escopo travado era mais estreito que o requisito
funcional que ele deveria servir; corrigi-lo alinha os dois.

Três salvaguardas que tornam a edição auditável e que devem ser exigidas em
qualquer repetição do padrão: (a) o texto original foi **preservado**, com a
exceção anexada, não substituído; (b) a nota é datada e rotulada
`Escopo corrigido (2026-08-02)`; (c) há decision e OQ com o raciocínio completo,
incluindo as alternativas descartadas. As três estão presentes.

Se numa próxima rodada alguém quiser editar um gate porque cumpri-lo dá trabalho —
sem premissa falsa a apontar —, a resposta correta é reverter o código, não reescrever
o gate. Vale registrar essa fronteira no `.codeflow/constitution.md` do projeto, para
que o precedente fique limitado ao caso que o justifica.

Demais sugestões:

- **Chave por `user_id`** (dúvida 2): concordo que é fase própria, não rework. O
  desenho natural é uma `key_func` única que usa `user_id` quando há token válido e
  cai para IP quando não há — assim `core/rate_limit.py` continua com um só ponto de
  decisão e os decorators não mudam. Cabe junto da E.4, quando o Caddy entrar e a
  chave por IP passar a ser o IP do proxy de qualquer forma.
- **`Retry-After`** (dúvida 3): mantenho o que a t1 disse — expor no proxy, na E.4.
  Nada a fazer agora.
- **O 40/min é folga dimensionada pela página, não medição.** Está declarado como
  risco residual, que é o tratamento correto. Quando a E.4 restabelecer o deploy,
  vale medir o consumo real por usuário antes de manter o número — e a decision já
  aponta que ajustar é mudar uma setting, sem tocar código.
- A decision cita `tests/integration/test_limites_requisicao.py:116-121` para o teste
  de `/ai/conversations`; o teste está poucas linhas abaixo disso. Referência de linha
  envelhece rápido — citar o nome do teste (`test_conversations_nao_tem_teto_de_ia`),
  que é estável, evita o problema.

## 6. Comandos rodados + saídas reais

Ambiente: container `caloria_backend`, branch `dev`, HEAD `68b51a5`.
`git merge-base --is-ancestor e22d54f HEAD` → OK; `git merge-base --is-ancestor
6115615058e2156a710afab5b05b873010ddb3e1 HEAD` → OK.

```text
# a §5 continua estruturalmente válida DEPOIS da edição do escopo travado
$ bash ~/.codeflow/framework/core/scripts/run-structural.sh \
    .codeflow/specs/002-vitrine-eval-e-saneamento/SPEC_002_VITRINE_EVAL_E_SANEAMENTO.md
✓ ids de fase únicos (26 fases)
✓ grafo de dependências acíclico
✓ §5 estruturalmente válida
EXIT=0

# nenhum código de produção tocado no rework
$ git diff --stat 5de94fe..HEAD
 .../2026-08-02-rate-limit-em-get-de-ia.md          | 129 +++++++++
 .codeflow/decisions/INDEX.md                       |   1 +
 .../SPEC_002_VITRINE_EVAL_E_SANEAMENTO.md          |  26 +-
 .../FASE-B.3-hardening-config-EXECUCAO.md          | 310 ++++++++++++---------
$ git diff --name-only 5de94fe..HEAD -- backend/app backend/tests frontend/ .github/ Makefile backend/pyproject.toml
(vazio)
```

**As afirmações factuais da decision, verificadas uma a uma:**

```text
# 1. os cinco GET chamam mesmo o provedor?
$ sed -n '145,260p' backend/app/api/v1/ai.py | grep "router.get\|_require_ai\|get_ai_client"
@router.get("/conversations", ...)            <- sem _require_ai, sem get_ai_client
@router.get("/suggest-meal", ...)   _require_ai + get_ai_client()
@router.get("/patterns", ...)       _require_ai + get_ai_client()
@router.get("/nutritional-alerts", ...) _require_ai + get_ai_client()
@router.get("/goal-adjustment", ...) _require_ai + get_ai_client()
@router.get("/monthly-report", ...)  _require_ai + get_ai_client()
# confirmado: o critério "gasta token" separa os cinco do sexto no próprio código

# 2. o desenho está travado por teste?
$ sed -n '118,123p' backend/tests/integration/test_limites_requisicao.py
    async def test_conversations_nao_tem_teto_de_ia(...):
        """É leitura pura de banco: não gasta token, não entra no limite."""
        for _ in range(_limite(settings.RATE_LIMIT_AI_LEITURA) + 5):
            assert (await client.get("/api/v1/ai/conversations")).status_code == 200
# e também test_o_teto_de_leitura_e_mais_folgado_que_o_de_escrita

# 3. o 40/min vem mesmo de "quatro consultas por carga"?
$ grep -n "use.*(" "frontend/app/(dashboard)/insights/page.tsx" | sed -n '5,10p'
  const mealSuggestion    = useMealSuggestion();
  const eatingPatterns    = useEatingPatterns(patternDays);
  const nutritionalAlerts = useNutritionalAlerts(alertDays);
  const goalAdjustment    = useGoalAdjustment();
  const monthlyReport     = useMonthlyReport(reportMonth, reportYear);
$ sed -n '78,130p' frontend/lib/hooks/useAI.ts
  useMealSuggestion  -> useMutation   <- sob demanda, NÃO dispara na carga
  useEatingPatterns  -> useQuery      <- dispara
  useNutritionalAlerts -> useQuery    <- dispara
  useGoalAdjustment  -> useQuery      <- dispara
  useMonthlyReport   -> useQuery      <- dispara
# exatamente quatro por carga, com suggest-meal sob demanda. A conta da decision
# está correta na vírgula.

# 4. a setting existe com o valor declarado?
$ grep -n -B2 "RATE_LIMIT_AI_LEITURA" backend/app/core/config.py
130: # Também gastam tokens do provedor, então também precisam de teto — mais
131: # folgado que o dos POST, porque são consultas que o dashboard dispara.
132: RATE_LIMIT_AI_LEITURA: str = "40/minute"

# 5. o FR-B4 restringe por método?
$ grep -n -A1 "FR-B4" .codeflow/specs/.../SPEC_002_*.md
235:- **FR-B4** — Os endpoints públicos de autenticação e os endpoints de IA devem ter
236:  rate limiting.
# não restringe. O escopo travado era mais estreito que o requisito que servia.
```

**Validação do projeto, rodada por mim no ambiente real:**

```text
$ docker compose -f docker-compose.dev.yml exec -T backend ruff check .
All checks passed!
$ ... ruff format --check .
147 files already formatted
$ ... mypy app/ evals/
Success: no issues found in 81 source files

$ ... pytest tests/unit/test_config_secret_key.py tests/unit/test_rate_limit_key.py \
      tests/integration/test_limites_requisicao.py -q
22 passed, 3 warnings in 14.12s              # AC-7 e AC-8

$ ... pytest --cov=app --cov-report=term -q
TOTAL                                      3204    862    73%
Required test coverage of 72.0% reached. Total coverage: 73.10%
581 passed, 1 skipped, 5 warnings in 100.21s (0:01:40)

$ gitleaks detect --config .gitleaks.toml --log-opts="5de94fe..HEAD"
2 commits scanned.  no leaks found            # NFR-4
$ git diff --name-only 5de94fe..HEAD -- backend/alembic/
(vazio)                                        # NFR-7
$ git log --format='%s%n%b' 5de94fe..HEAD | grep -iE "claude|anthropic|co-authored|agente"
(nenhuma)                                      # princípio 5
$ git status --short
(limpo)
```

**Nota de método sobre esta execução.** Na primeira tentativa lancei duas corridas
de `pytest` concorrentes contra o mesmo banco de teste e elas travaram em lock —
erro meu, não do código. Encerrei os processos, limpei as conexões de
`caloria_test` e reexecutei uma única vez; os números acima são dessa execução
limpa. Só o banco de teste descartável foi afetado; a árvore de trabalho
permaneceu limpa o tempo todo.

## 7. Itens da fase / DoD não atendidos

Nenhum. O gate declarado — "AC-7 e AC-8 satisfeitos; `make test-integration` verde;
`mypy app/` limpo" — está satisfeito nas três cláusulas, e o item do §9 do DoD
("B.3 — AC-7 e AC-8; `make test-integration` verde") fecha.

Registro, como a t2 também registrou: `make test-integration` não foi invocado pelo
nome (o alvo faz `docker compose exec` a partir do host); a suíte de integração
inteira roda dentro do `pytest --cov` acima, com zero falhas — cobre o gate com
folga.

Débitos abertos e **registrados**, que não impedem a conclusão: chave de contagem
por IP em vez de `user_id`; ausência de `Retry-After` por `headers_enabled=False`;
40/min dimensionado por consumo de página e não por tráfego medido.

## 8. Divergências entre o relatório e o código real

Nenhuma. Confirmei as cinco afirmações factuais da decision contra o código
(§6), os três lugares de registro, a ausência de mudança em `backend/`
e `frontend/`, e os dois números de teste (22 e 581/1) — todos batem exatamente
com o que o relatório declara.

Duas observações a favor do relatório, não contra: os desvios 6 e 7 registram
tensões que ninguém notaria se fossem omitidas, e a dúvida 1 levanta contra o
próprio trabalho a objeção mais forte que existe contra ele. É o comportamento que
torna a avaliação independente barata — e que faltou, na t1, exatamente no ponto
que gerou o BLOQUEANTE.

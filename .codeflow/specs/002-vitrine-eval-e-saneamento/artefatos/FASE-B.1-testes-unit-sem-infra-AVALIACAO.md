---
spec: 002-vitrine-eval-e-saneamento
fase: B.1
slug_fase: testes-unit-sem-infra
tentativa: 2
veredito: APROVADO
score: 9.8
threshold: 8.5
range_avaliado: fd923d69f1a751b91d10535e1e5a0306204d8441..721f0f0892b3298964b04b917e3f1b0cb5a1cc69
---

# FASE B.1 — Avaliação independente

## 1. Veredito e score

**Veredito:** APROVADO · **Score:** 9.8 / threshold 8.5

O único IMPORTANTE da tentativa 1 era de artefato — o `range` apontava para dois
commits que o `git filter-repo` da Fase A.2 tinha apagado. Está corrigido e
verificado: `fd923d6` e `721f0f0` são ambos ancestrais de HEAD. A "Nota de execução
paralela" que citava um terceiro SHA morto (`cb2e4ca`) foi reescrita para preservar
a informação sem depender dele — que é a correção certa, e não a mais preguiçosa.

Nada de código mudou nesta tentativa, e nada precisava mudar. Reproduzi o AC-5 de
forma independente com a infraestrutura provadamente parada — Docker indisponível
nesta máquina, nenhuma porta de Postgres ou Redis escutando — e `pytest tests/unit/`
coleta e passa: **199 passed in 2.73s**. A coleta da suíte inteira, que era o que
falhava antes da fase, também passa sem banco: **302 tests collected**.

Li os dois `conftest.py` na íntegra. A decisão central continua sendo a certa:
sobrepor `setup_test_database` **e** `clean_db` no conftest de `tests/unit/`, em vez
de tirar o `autouse=True` da raiz — que teria removido o isolamento por `TRUNCATE`
da integração, exatamente o que o escopo travado proíbe.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 5 | AC-5 reproduzido por mim com Docker ausente e portas 5432/6379 fechadas → `199 passed in 2.73s` (§6). Escopo travado ✓: nenhum `skip`, nenhum teste existente alterado, nada em `backend/app/` — o commit toca exatamente os 2 `conftest.py` declarados |
| 2 | Arquitetura e direção de dependências | 3 | 5 | `backend/tests/conftest.py:53-81`: `_reset_schema` passou a usar o `_engine` do módulo e a criação de schema entrou na fixture `setup_test_database`, com `drop_all` + `dispose()` em `try/finally` aninhado. Nenhum I/O no corpo do módulo (`grep -c "asyncio.run"` → 0) |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | Superfície neutra: só infraestrutura de teste. Nenhum segredo, credencial ou dado de usuário |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | Nada criado: `setup_test_database` e o stub de `tests/unit/conftest.py` já existiam e foram corrigidos — o mapa NOVO/REUSADO da §4 da spec, ao pé da letra |
| 5 | Padrões de domínio/aplicação | 2 | 5 | Resolução de fixture pelo conftest mais próximo é o mecanismo idiomático do pytest; `AsyncGenerator`/`Iterator` seguem os tipos já usados |
| 6 | Local e nomes dos arquivos | 2 | 5 | Exatamente os 2 arquivos declarados na §5 |
| 7 | Qualidade de código | 2 | 5 | Sumiram os 2 `type: ignore` (`grep -c` → 0); o docstring de `conftest.py:61-72` registra o *porquê* (engine loop-bound, ordem de coleta), não o *o quê* |
| 8 | Testes e cobertura | 2 | 4 | Contagem inalterada e reproduzida por mim (199 unit / 302 total). Desconto mantido: `make test-integration` roda dentro do container e eu também não pude executá-lo — Docker indisponível; fica `[—]` |
| 9 | Migration safety | 2 | [—] | Nenhuma migration tocada (NFR-7) |

Score = (3·5 + 3·5 + 3·5 + 3·5 + 2·5 + 2·5 + 2·5 + 2·4) / 20 · 2 = **9.8**

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

Nenhum. O IMPORTANTE 4.1 da tentativa 1 está fechado — evidência na §6.

## 5. Sugestões

Todas herdadas e ainda válidas; nenhuma é trabalho desta fase.

- **A spec continua desatualizada na contagem de testes.** A §1 e o bloco da Fase
  B.1 falam em "129 testes unitários"; o número real é **199**, antes e depois.
  A §5 da spec foi editada nesta rodada por outras razões e este ponto ficou de
  fora. Vale corrigir para não induzir suspeita de perda de testes numa releitura.
- **O relatório diz "contagem total inalterada em 298"; o total real é 302.** A
  diferença são os 4 testes de `backend/tests/smoke_test.py`, que moram na raiz de
  `tests/` e a contagem de 298 não inclui. Nenhum teste se perdeu — 199 unit + 99
  integration + 4 smoke = 302, medido por mim. Vale ajustar o número no relatório
  para não parecer discrepância.
- **`docker-compose.dev.yml` publica Postgres em 5442 e Redis em 6389**, mas o
  default de `TEST_DATABASE_URL` em `conftest.py:19` é `localhost:5432`. Rodar
  integração a partir do host exige sobrepor a variável. Armadilha real de ambiente,
  fora dos 2 arquivos declarados — candidata a uma fase de higiene.
- **`backend/uv.lock` desatualizado** (sem `aiosmtplib` nem extras de dev). Não afeta
  o CI (`ci.yml` usa `pip install -e ".[dev]"`), mas quebra `uv run --frozen`
  localmente.

## 6. Comandos rodados + saídas reais

```text
# --- branch e ancestralidade (Passo 2) — o achado da tentativa 1 ---
$ git rev-parse --short HEAD
da08121
$ git merge-base --is-ancestor fd923d69f1a751b91d10535e1e5a0306204d8441 HEAD  → ANCESTRAL
$ git merge-base --is-ancestor 721f0f0892b3298964b04b917e3f1b0cb5a1cc69 HEAD  → ANCESTRAL
$ git log --format='%h %s' -1 fd923d69
fd923d6 docs(seguranca): remove pii e caminho de extracao dos docs de auditoria  ✓

# --- AC-5: infraestrutura provadamente parada ---
$ docker ps
The command 'docker' could not be found in this WSL 2 distro.
$ ss -ltn | grep -E '5432|6379|5433|6380'
   (nenhuma linha — nenhuma porta de Postgres/Redis escutando)

$ backend/.venv/bin/python -m pytest tests/unit/ -q
........................................................................ [ 36%]
........................................................................ [ 72%]
.......................................................                  [100%]
199 passed in 2.73s                                           ← AC-5 ✓ (execução)

# --- a coleta da suíte INTEIRA sem banco (era o que falhava antes da fase) ---
$ backend/.venv/bin/python -m pytest --collect-only -q | tail -1
302 tests collected in 0.37s                                  ← AC-5 ✓ (coleta)
$ backend/.venv/bin/python -m pytest --collect-only -q tests/unit        → 199
$ backend/.venv/bin/python -m pytest --collect-only -q tests/integration → 99
$ backend/.venv/bin/python -m pytest --collect-only -q tests/smoke_test.py → 4
   # 199 + 99 + 4 = 302; nenhum teste perdido

# --- leitura do código, não do relatório ---
$ grep -c "asyncio.run" backend/tests/conftest.py
0                                                    # era 1, no corpo do módulo
$ grep -c "type: ignore" backend/tests/unit/conftest.py
0                                                    # eram 2
$ git diff --stat 461ee38..721f0f0 -- backend/tests/conftest.py backend/tests/unit/conftest.py
 backend/tests/conftest.py      | 43 +++++++++++++++++++++---------------
 backend/tests/unit/conftest.py | 19 ++++++++++-------
   # nada em backend/app/, nenhum teste existente alterado, nenhum `skip` adicionado

# --- demais gates do projeto ---
$ backend/.venv/bin/python -m ruff check .          → All checks passed!
$ backend/.venv/bin/python -m ruff format --check . → 119 files already formatted
$ backend/.venv/bin/python -m mypy app/             → Success: no issues found in 72 source files
$ cd frontend && npm test                           → 17 suites, 100 passed
$ cd frontend && npm run lint                       → 1 Warning pré-existente; exit 0
$ cd frontend && npx tsc --noEmit                   → exit 0
$ pre-commit run --all-files                        → todos Passed, EXIT=0

# --- make test-integration: [—] NÃO RODADO ---
# O alvo é `$(COMPOSE_DEV) exec backend pytest tests/integration/` e roda DENTRO do
# container. Docker indisponível (saída acima). Gate ausente do ambiente → `[—]`,
# não falha (SPEC §3.10). O relatório registra 293 passed + 5 skipped com a infra
# no ar, nas duas ordens de coleta.

# --- árvore limpa ao final ---
$ git status --porcelain | wc -l
0
```

## 7. Itens da fase / DoD não atendidos

| Item (§5 / §9 da spec) | Estado |
|---|---|
| Passo 1 — remover `asyncio.run(_reset_schema())` do corpo do módulo | Atendido |
| Passo 2 — fixture só solicitada por testes que precisam de banco; intenção de `:64-68` preservada | Atendido — os motivos do comentário original estão endereçados um a um no docstring novo |
| Passo 3 — ajustar o stub de `tests/unit/conftest.py` | Atendido, e além: a peça que faltava era o override de `clean_db` |
| Testes (AC-5) — sem infra, coleta e execução completam | Atendido, reproduzido por mim |
| Gate — `make test-unit` verde | Atendido (equivalente rodado no host) |
| Gate — `make test-integration` verde | `[—]` não verificável aqui (Docker indisponível) |
| Gate — contagem de testes coletados inalterada | Atendido (199 unit; 302 no total) |
| DoD global — decisão de escopo registrada | N/A — esta fase não teve desvio de escopo |

## 8. Divergências entre o relatório e o código real

1. **Nenhuma divergência de código.** Li os dois `conftest.py` na íntegra e o diff
   confere linha a linha com o que a §3 do relatório descreve. Todas as afirmações
   verificáveis por mim se confirmam.

2. **`range` corrigido e resolvendo** — fecha o IMPORTANTE 4.1. Ressalva de leitura:
   o intervalo `fd923d6..721f0f0` cobre as cinco fases do lote, não só esta; o commit
   de código desta fase é `9b3ff80`, e só ele. É o que o schema manda (§2.9.3), mas
   vale nomear o commit no corpo do relatório.

3. **Imprecisão numérica no relatório:** "contagem total inalterada em 298" — o total
   real é 302 (§5). Nenhum teste se perdeu; o número simplesmente exclui os 4 do
   `smoke_test.py`.

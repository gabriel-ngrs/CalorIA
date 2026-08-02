---
spec: 002-vitrine-eval-e-saneamento
fase: B.1
slug_fase: testes-unit-sem-infra
tentativa: 1
veredito: RESSALVAS
score: 9.8
threshold: 8.5
range_avaliado: fd923d6..9b3ff80 (reconstruído — ver §8)
---

# FASE B.1 — Avaliação independente

## 1. Veredito e score

**Veredito:** RESSALVAS · **Score:** 9.8 / threshold 8.5

Tecnicamente é a melhor fase do lote: o diagnóstico está certo, a correção é a
mínima possível, o escopo travado foi respeitado ao pé da letra e eu reproduzi o AC-5
de forma independente com a infraestrutura provadamente parada. Não encontrei
BLOQUEANTES nem defeito de código.

A ressalva é **exclusivamente** do artefato: o `range` do frontmatter aponta para
dois commits que não existem mais na branch, o que quebra a rastreabilidade que o
pipeline usa para isolar o diff da fase. Correção de duas linhas.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 5 | AC-5 reproduzido por mim com portas 5432/6379 fechadas → `199 passed in 3.03s` (§6). Escopo travado ✓: nenhum `skip`, nenhum teste existente alterado, nada em `backend/app/` — o commit toca exatamente 2 `conftest.py` |
| 2 | Arquitetura e direção de dependências | 3 | 5 | A decisão central está certa: sobrepor `clean_db` no conftest de `tests/unit/` em vez de remover o `autouse=True` da raiz. A alternativa tiraria o isolamento por TRUNCATE da integração — seria "mudar o comportamento para acomodar a fixture", o que o escopo travado proíbe |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | Superfície neutra: fase toca só infraestrutura de teste. Nenhum segredo, nenhuma credencial, nenhum dado de usuário |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | Nada criado: `setup_test_database` (`conftest.py:59`) e o stub de `tests/unit/conftest.py` **já existiam** e foram corrigidos — exatamente o mapa NOVO/REUSADO da §4 da spec |
| 5 | Padrões de domínio/aplicação | 2 | 5 | Resolução de fixture por conftest mais próximo é o mecanismo idiomático do pytest; `AsyncGenerator`/`Iterator` seguem o tipo já usado no arquivo |
| 6 | Local e nomes dos arquivos | 2 | 5 | Exatamente os 2 arquivos declarados na §5 |
| 7 | Qualidade de código | 2 | 5 | Sumiram os 2 `type: ignore` que existiam; o docstring de `conftest.py:61-72` registra o *porquê* (loop-bound, ordem de coleta), não o *o quê*; `try/finally` aninhado garante `dispose()` mesmo se o `drop_all` falhar |
| 8 | Testes e cobertura | 2 | 4 | Contagem inalterada, validado nas duas ordens de coleta. Desconto: `make test-integration` nunca rodou pelo alvo do Makefile (roda dentro do container) e eu também não pude rodá-lo — Docker indisponível nesta máquina; fica `[—]` |
| 9 | Migration safety | 2 | [—] | Nenhuma migration tocada (NFR-7) |

Score = (3·5 + 3·5 + 3·5 + 3·5 + 2·5 + 2·5 + 2·5 + 2·4) / 20 · 2 = **9.8**

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

### 4.1 — O `range` do frontmatter aponta para commits inexistentes na branch

**Onde:** `FASE-B.1-testes-unit-sem-infra-EXECUCAO.md:8-10`.

```text
range: 4b58f76f31931aa47a5281ff0ac0bc88dec795a6..425830930d64a876cf1997db54d681a4f44a64fc

$ git merge-base --is-ancestor 4b58f76f...  HEAD   → NÃO-ancestral
$ git merge-base --is-ancestor 4258309306... HEAD   → NÃO-ancestral
```

Ambos os SHAs são pré-purga. O `git filter-repo` da Fase A.2 reescreveu todas as
refs em 2026-08-02 e esses objetos ficaram inalcançáveis a partir de `HEAD`.
Diferente dos outros quatro relatórios, este **não foi corrigido** no commit
`95c6c8c` — nem o `sha_final`. O commit real desta fase é
`9b3ff80 test(backend): cria schema em fixture e libera testes unit de infra`.

**Por que é IMPORTANTE e não cosmético.** O Passo 2 do protocolo de avaliação manda
**PARAR** quando os commits do range não são ancestrais de HEAD, porque é o sinal de
branch errada. Só segui porque a causa é conhecida e documentada (a A.2 reescreveu o
histórico) e o commit é identificável pela mensagem. Um rework futuro, ou uma
reavaliação em chat zerado sem esse contexto, para aqui.

**Correção sugerida:** `sha_inicial: fd923d6`, `sha_final: 9b3ff80`,
`range: fd923d6..9b3ff80`.

## 5. Sugestões

Nenhuma correção pendente no código. Três registros herdados do relatório, todos
**corretamente** deixados fora do escopo — anoto para que não se percam:

- **A spec está desatualizada na contagem de testes.** §1 e a Fase B.1 falam em "129
  testes unitários"; o número real é **199**, antes e depois. Confirmei. Vale
  corrigir na §1 e na §5 para não induzir suspeita de perda de testes numa
  reavaliação.
- **`docker-compose.dev.yml` publica Postgres em 5442 e Redis em 6389**, mas o
  default de `TEST_DATABASE_URL` em `conftest.py:19` é `localhost:5432`. Rodar
  integração a partir do host exige sobrepor a variável. Armadilha de ambiente real,
  fora dos 2 arquivos declarados — candidata natural a uma fase de higiene.
- **`backend/uv.lock` desatualizado** (sem `aiosmtplib` nem extras de dev). O
  relatório da B.2 avaliou e descartou o impacto no CI (`ci.yml:71` usa
  `pip install -e ".[dev]"`, não `uv sync --frozen`) — confirmei a leitura do
  `ci.yml`. Continua quebrando `uv run --frozen` localmente.

## 6. Comandos rodados + saídas reais

```text
# --- AC-5: infraestrutura provadamente parada ---
$ docker ps
The command 'docker' could not be found in this WSL 2 distro.
$ (exec 3<>/dev/tcp/127.0.0.1/5432) && echo ABERTA || echo fechada   → fechada
$ (exec 3<>/dev/tcp/127.0.0.1/5442) && echo ABERTA || echo fechada   → fechada

$ backend/.venv/bin/python -m pytest tests/unit/ -q
........................................................................ [ 36%]
........................................................................ [ 72%]
.......................................................                  [100%]
199 passed in 3.03s                                          ← AC-5 ✓ (execução)

# --- a coleta da suíte INTEIRA também passa sem banco (era o que falhava antes) ---
$ backend/.venv/bin/python -m pytest --collect-only -q | tail -1
302 tests collected in 0.39s                                 ← AC-5 ✓ (coleta)
   # 199 unit + 99 integration + 4 do smoke_test.py na raiz de tests/

# --- lint e typecheck ---
$ backend/.venv/bin/python -m ruff check .            → All checks passed!
$ backend/.venv/bin/python -m ruff format --check .   → 119 files already formatted
$ backend/.venv/bin/python -m mypy app/               → Success: no issues found in 72 source files

# --- escopo: o commit toca exatamente 2 arquivos ---
$ git show 9b3ff80 --stat --format=''
 backend/tests/conftest.py       | 43 ++++++++++++++++++++++---------------
 backend/tests/unit/conftest.py  | 19 ++++++++++-------
 2 files changed, 37 insertions(+), 25 deletions(-)
   # nada em backend/app/, nenhum teste existente alterado, nenhum `skip` adicionado

# --- leitura do código, não do relatório ---
# `conftest.py:53-56`: _reset_schema passou a usar o `_engine` do módulo
# `conftest.py:59-81`: setup_test_database faz `await _reset_schema()` antes do yield
#                      e drop_all + dispose em try/finally aninhado no teardown
# nenhuma chamada de I/O no corpo do módulo — `asyncio.run` e o import `asyncio` sumiram
$ grep -n "asyncio.run" backend/tests/conftest.py | wc -l
0
# `tests/unit/conftest.py:14-23`: sobrepõe setup_test_database E clean_db, ambos
#                      tipados como Iterator[None], sem nenhum `type: ignore`
$ grep -c "type: ignore" backend/tests/unit/conftest.py
0                                                            # eram 2

# --- make test-integration: [—] NÃO RODADO ---
# O alvo é `$(COMPOSE_DEV) exec backend pytest tests/integration/` e roda DENTRO do
# container. Docker não está disponível nesta máquina (saída acima), e o Postgres não
# está no ar. Gate ausente do ambiente → `[—]` conforme SPEC §3.10, não falha.
# O relatório registra 293 passed + 5 skipped com a infra no ar, nas duas ordens de
# coleta, e os 4 testes que falhavam são falha de ambiente (REDIS_URL do .env aponta
# para o hostname interno do Docker) — leitura consistente com o `.env` do projeto.

# --- árvore limpa ao final ---
$ git status --porcelain | wc -l
0
```

## 7. Itens da fase / DoD não atendidos

| Item (§5 / §9 da spec) | Estado |
|---|---|
| Passo 1 — remover `asyncio.run(_reset_schema())` do corpo do módulo | Atendido |
| Passo 2 — fixture só solicitada por testes que precisam de banco; intenção de `:64-68` preservada | Atendido — os três motivos do comentário original estão endereçados um a um no docstring novo |
| Passo 3 — ajustar o stub de `tests/unit/conftest.py` | Atendido, e além: a peça que faltava era o override de `clean_db` |
| Testes (AC-5) — sem infra, coleta e execução completam | Atendido, reproduzido por mim |
| Gate — `make test-unit` verde | Atendido (equivalente rodado no host) |
| Gate — `make test-integration` verde | `[—]` não verificável aqui (Docker indisponível); relatório traz 293 passed |
| Gate — contagem de testes coletados inalterada | Atendido (298 → 298; 302 com o `smoke_test.py` da raiz) |
| DoD global — decisão de escopo registrada | N/A — esta fase não teve desvio de escopo |

## 8. Divergências entre o relatório e o código real

1. **Nenhuma divergência.** Li os dois `conftest.py` na íntegra e o diff confere
   linha a linha com o que a §3 do relatório descreve. As afirmações verificáveis por
   mim (199 testes sem infra, contagem inalterada, zero `type: ignore`, nada em
   `backend/app/`) todas se confirmam.

2. **`range` inconsistente** (§4.1) — único achado, e é do artefato, não do código.

3. **Observação sobre a nota de execução paralela** (`EXECUCAO.md:25-29`): o relatório
   declara que o `sha_inicial` é o HEAD no momento do *commit*, não do início do
   trabalho, e que o range cobre exclusivamente o commit da fase. Essa honestidade é
   correta e, uma vez corrigidos os SHAs para os equivalentes pós-purga
   (`fd923d6..9b3ff80`), o range volta a cobrir exatamente um commit.

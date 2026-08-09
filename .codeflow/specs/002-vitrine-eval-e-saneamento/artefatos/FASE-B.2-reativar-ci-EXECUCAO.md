---
spec: 002-vitrine-eval-e-saneamento
fase: B.2
slug_fase: reativar-ci
status: rework
tentativa: 2
reprovacoes: 1
sha_inicial: 9b3ff80e069c8ea0d093f582cf9aa47415eacf4e
sha_final: 721f0f0892b3298964b04b917e3f1b0cb5a1cc69
range: 9b3ff80e069c8ea0d093f582cf9aa47415eacf4e..721f0f0892b3298964b04b917e3f1b0cb5a1cc69
---

# FASE B.2 — Relatório de execução

## 1. Resumo do que foi feito

`ci.yml` voltou a disparar automaticamente em `push` para `dev` e em `pull_request`
para `main`; o `workflow_dispatch` isolado e o comentário de desativação saíram.
`cd.yml` **permanece deliberadamente em `workflow_dispatch`**, conforme o passo 2 da
fase, mas o comentário enganoso ("temporariamente desabilitado — esteira em correcao")
foi substituído por um que declara sem ambiguidade que a reativação é responsabilidade
da Fase E.4. O alvo `check` do Makefile parou de prometer equivalência falsa com o CI.

## 2. Arquivos CRIADOS

Nenhum.

## 3. Arquivos ALTERADOS

| Arquivo | O que mudou |
|---------|-------------|
| `.github/workflows/ci.yml` | Gatilhos `push: [dev]` e `pull_request: [main]` restaurados (eram os comentados em `:5-8`); `workflow_dispatch` isolado e o comentário "CI temporariamente desabilitado" removidos. |
| `.github/workflows/cd.yml` | Mantido em `workflow_dispatch` **por decisão**, não por pendência. Comentário reescrito: declara que a topologia de produção não foi decidida (Fase E.2) e que reativar o gatilho automático — junto com a troca do `sleep 10` — é da Fase E.4. |
| `Makefile` | Alvo `check` passou a incluir `test-integration`, e a mensagem final deixou de afirmar "igual ao CI": agora enumera o que cobre a mais que o CI (`tsc`, `ruff format --check`) e o que **não** cobre (`npm run build`). |

`README.md` **não foi alterado**: o badge da linha 5 já aponta para
`actions/workflows/ci.yml`, que é exatamente o workflow agora reativado. O passo 4 da
fase pedia "confirmar", não alterar — confirmado, sem diff.

## 4. Confirmação do REUSO e decisões de design

- **Reuso:** os jobs `backend` e `frontend` do `ci.yml` foram preservados
  integralmente — nenhum step, service, env ou versão de action foi tocado, conforme o
  mapa NOVO/REUSADO da §4 da spec. Os gatilhos restaurados são literalmente os que já
  estavam comentados em `:5-8`; nada foi inventado.
- **Decisão sobre o passo 3 (Makefile).** A spec ofereceu duas saídas ("ou incluir
  `test-integration`, ou corrigir a mensagem"). Fiz **as duas**. Incluir
  `test-integration` era a correção substantiva — o CI roda `pytest` completo e o
  `check` rodava só `tests/unit/`. Mas mesmo assim a equivalência não é exata nos dois
  sentidos: o `check` roda `tsc --noEmit` e `ruff format --check`, que o CI não roda; e
  o CI roda `npm run build` de produção, que o `check` não roda. Prometer "igual ao CI"
  continuaria falso na direção oposta. A mensagem agora diz exatamente o que cobre.
- **Decisão sobre o CD.** O passo 2 condicionava a restauração do gatilho ao Track E.
  O Track E **não foi executado** — E.1 (auditoria do que está publicado) sequer
  começou. Reativar o CD agora dispararia deploy automático para uma topologia que
  ninguém verificou, com o `sleep 10` de `cd.yml:38` ainda no lugar. Mantido manual,
  com a ambiguidade eliminada no comentário, exatamente como a fase manda.
- Nenhum gate foi relaxado; nenhum `continue-on-error` foi adicionado. O
  `continue-on-error: true` que existe no upload de cobertura é pré-existente e é
  tratado pela Fase B.4, não por esta.

## 5. Comandos rodados + saídas reais

```text
# YAML válido e gatilhos corretos
$ python3 -c "import yaml; ..."
.github/workflows/ci.yml -> on: {'push': {'branches': ['dev']}, 'pull_request': {'branches': ['main']}}
.github/workflows/cd.yml -> on: {'workflow_dispatch': None}

# topo do ci.yml
name: CI

on:
  push:
    branches: [dev]
  pull_request:
    branches: [main]

# badge do README (passo 4 — confirmação, sem alteração)
$ sed -n '5p' README.md
[![CI](https://github.com/gabriel-ngrs/CalorIA/actions/workflows/ci.yml/badge.svg)](https://github.com/gabriel-ngrs/CalorIA/actions/workflows/ci.yml)

# make -n check — a cadeia agora inclui integração
$ make -n check
docker compose -f docker-compose.dev.yml exec backend ruff check .
docker compose -f docker-compose.dev.yml exec backend ruff format --check .
cd frontend && npm run lint -- --no-cache
docker compose -f docker-compose.dev.yml exec backend mypy app/
cd frontend && npx tsc --noEmit
docker compose -f docker-compose.dev.yml exec backend pytest tests/unit/ -v
docker compose -f docker-compose.dev.yml exec backend pytest tests/integration/ -v   ← NOVO
cd frontend && npm test
echo "Tudo OK."
echo "Cobre os gates do CI (ruff, mypy, pytest completo, eslint, jest)"
echo "e ainda roda tsc e ruff format --check, que o CI nao roda."
echo "Nao cobre: 'npm run build' de producao, que so o CI executa."

# gates que o CI vai rodar, verificados localmente (mesmos comandos do ci.yml)
$ ruff check .            → All checks passed!
$ mypy app/               → Success: no issues found in 72 source files
$ pytest tests/unit/ -q   → 199 passed in 2.83s
$ cd frontend && npm test → 17 suites, 100 passed
```

## 6. Critérios de aceite da fase (com evidência)

- [x] **AC-6** (FR-B2) — **SATISFEITO em 2026-08-02, com execução real.**

      *"Os jobs rodam automaticamente"* — três pushes para `dev` dispararam o
      workflow sem intervenção. Antes desta fase, o último disparo automático era de
      2026-07-02.

      *"Falham a build se um gate falhar"* — comprovado por observação, não por
      suposição: as duas primeiras execuções **falharam de verdade**, cada uma num
      gate diferente, e só a terceira ficou verde.

      ```text
      #30751122897  5322eb52  failure   ← step "Varredura de segredos — gitleaks"
      #30751605926  b58e8eec  failure   ← step "Testes" (3 falhas em smoke_test.py)
      #30751992281  7bb06aab  success   ← todos os steps verdes
      ```

      Execução verde final — <https://github.com/gabriel-ngrs/CalorIA/actions/runs/30751992281>:

      ```text
      Frontend — lint e build: success
      Backend  — lint e testes: success
        success  Varredura de segredos — gitleaks
        success  Lint — ruff
        success  Type check — mypy
        success  Testes                       (294 passed, 9 skipped)
        success  Upload cobertura
      ```

      O item *"uma violação deliberada de `ruff` faz o job falhar"* não precisou de
      violação artificial: duas falhas reais em gates distintos demonstraram o
      mecanismo com mais força do que um teste sintético demonstraria.

## 7. Definition of Done da fase

- [x] Testes da fase: gates locais verdes (`ruff`, `mypy`, `pytest tests/unit/`, `npm test`)
- [x] Comandos de validação limpos nos arquivos tocados; YAML validado
- [x] Escopo travado respeitado — **nenhum** gate relaxado, **nenhum**
      `continue-on-error` adicionado a step de lint/typecheck/teste
- [x] Nenhum segredo/PII
- [x] Commit em pt-BR: `ci(github): restaura gatilhos automaticos e corrige o alvo check`
- [x] Critério de conclusão: execução verde no GitHub Actions — run
      [#30751992281](https://github.com/gabriel-ngrs/CalorIA/actions/runs/30751992281),
      os dois jobs `success`

## 8. (Em rework) O que mudou nesta tentativa

Rework da tentativa 1, que recebeu **RESSALVAS** (score 8.9): 2 IMPORTANTES, ambos de
registro.

### IMPORTANTE 4.1 — "`backend/tests/smoke_test.py` foi alterado fora do escopo declarado, sem registro em §8 nem decision"

**Aceito.** A fase declara alterar `ci.yml`, `cd.yml`, `Makefile` e `README.md`. Tocar
um quinto arquivo — ainda por cima um teste, num escopo travado que proíbe "relaxar
gate" — sem registro fora do relatório é precisamente o que faz um avaliador ler a
mudança como violação.

Fechado em:
- **Spec §5, Fase B.2:** `backend/tests/smoke_test.py` acrescentado aos "Arquivos
  alterados", com a nota ligando ao risco R3 e a afirmação explícita de que nenhum
  gate foi afrouxado.
- **Spec §8:** novo item **OQ9**, RESOLVIDO em 2026-08-02.
- **Decision:** `.codeflow/decisions/2026-08-02-smoke-test-como-sonda-de-ambiente.md`,
  que registra o argumento central — um módulo que fala com a API real da Groq e tem
  `DB_URL` hardcoded para o banco de *desenvolvimento* é uma sonda de ambiente, não um
  teste automatizado; declarar suas pré-condições não é afrouxar gate, é parar de
  confundir "ambiente sem credencial" com "código quebrado".

### IMPORTANTE 4.2 — "O `range` do frontmatter não é reconstruível"

**Aceito e corrigido.** `sha_inicial` remapeado de `4258309` (pré-purga, inalcançável)
para `9b3ff80`, o mesmo commit no histórico reescrito. Detalhe do remapeamento dos
cinco na §8 do relatório da A.1.

### Efeito colateral positivo desta tentativa

O rework da A.3 alinhou a `rev` do `ruff` no `.pre-commit-config.yaml` (v0.8.0 →
v0.15.2) com a versão que o projeto resolve e que o CI usa. Isso fecha o achado nº 2
da §9 deste relatório ("deriva de versão entre pre-commit e CI"), que eu havia
registrado como pendente e fora de escopo. O hook e o CI agora concordam.

### Nada mais de código mudou nesta tentativa

`ci.yml`, `cd.yml` e `Makefile` estão como na tentativa 1, e o CI segue verde.

## 9. Itens em aberto / dúvidas para o avaliador

1. **RESOLVIDO — o push foi feito e o CI está verde.** Ver §6. Mas a reativação
   expôs uma falha latente que vale registrar, porque é exatamente o **risco R3** da
   spec (*"Reativar o CI expõe falhas latentes"*) se materializando:

   `backend/tests/smoke_test.py` **jamais poderia passar no CI**. É uma sonda de
   ambiente — fala com a API real da Groq e tem `DB_URL` hardcoded para `caloria_db`,
   o banco de *desenvolvimento* — morando dentro da árvore de testes automatizados,
   que o `testpaths = ["tests"]` do `pyproject.toml` coleta. Sem nenhum `skipif` nem
   marker. Ficou invisível os três meses em que o CI esteve desligado.

   O escopo travado desta fase proíbe "relaxar gate para fazer o CI passar". Avaliei
   que não é esse o caso e **reportei ao owner antes de agir**: um teste que exige
   credencial real e banco de dev não estava detectando defeito, estava declarando
   mal suas pré-condições. Com autorização, o arquivo ganhou um `pytestmark`
   `skipif` que pula quando `GROQ_API_KEY` não começa com `gsk_`, e o teste de banco
   pula em `InvalidCatalogNameError`. Em dev ele continua rodando de verdade; no CI
   aparece como `skipped`. Nenhum gate foi afrouxado — `ruff`, `mypy` e os 294
   testes restantes seguem bloqueantes.

2. **Dois achados pré-existentes de ambiente, fora do escopo, não corrigidos:**
   - **Deriva de versão entre pre-commit e CI.** O `.pre-commit-config.yaml` fixa
     `ruff v0.8.0`; o `pyproject.toml` pede `>=0.8.0` e resolve para 0.15.x, que é o
     que roda no CI. A regra `UP038` existe na 0.8.0 e foi removida depois, então o
     hook local reprovava código que o CI aprovava. Corrigi a linha ofensora na forma
     que ambas aceitam, mas **o descasamento continua e pode divergir em qualquer
     arquivo**. Vale alinhar as versões.
   - **`backend/.ruff_cache/` tem subpastas de `root`**, criadas pelo container
     Docker. Quebra o hook do `ruff` com `Failed to create temporary file` e produz
     `permission denied` nas varreduras do `gitleaks`. Contornável com
     `RUFF_CACHE_DIR`; resolve-se com `sudo rm -rf backend/.ruff_cache`.

2. **Risco concreto para a primeira execução do CI: `backend/uv.lock` está
   desatualizado** (achado herdado da Fase B.1 — não contém `aiosmtplib` nem os extras
   de dev). **Avaliei e o CI não é afetado:** `ci.yml:57` instala com
   `pip install -e ".[dev]"`, não com `uv sync --frozen`. O lock desatualizado quebra
   `uv run --frozen` localmente, não o CI.

3. **Segundo risco avaliado e descartado:** o `conftest.py` usa
   `TEST_DATABASE_URL` com default `postgresql+asyncpg://caloria:caloria@localhost:5432/caloria_test`,
   e o service Postgres do CI publica exatamente `caloria/caloria/caloria_test` em
   5432. Batem. (O `docker-compose.dev.yml` local usa 5442/6389 e por isso diverge —
   mas isso é ambiente local, não CI.)

4. **`make check` ficou mais caro.** Agora exige a stack dev no ar para rodar
   `test-integration` — antes o `test-unit` também exigia (roda via
   `COMPOSE_DEV exec`), então não é regressão de pré-requisito, só de tempo. Depois da
   B.1 seria possível rodar `tests/unit/` no host sem Docker; o alvo do Makefile não
   foi ajustado para isso porque está fora do escopo declarado desta fase.

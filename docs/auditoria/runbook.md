# Runbook de Execução da Auditoria — CalorIA

> Documento operacional que guia a execução da auditoria descrita em `docs/auditoria/plano.md`.
> Cada **PASSO** é atômico: ler → analisar → registrar → commitar.

---

## Como usar este documento

1. Sempre comece pelo **PASSO 0.1**. Nunca pule passos.
2. Execute **um passo de cada vez**. Cada passo termina com **exatamente um commit**.
3. Antes de iniciar um passo, confirme que o anterior está completo (HEAD do git tem o commit do passo anterior).
4. Após terminar um passo:
   - Atualize `docs/auditoria/log.md` (template em [§ Templates](#templates)).
   - Atualize `docs/auditoria/achados.md` se o passo encontrou problemas.
   - Atualize o arquivo de frente correspondente (`docs/auditoria/01-arquitetura.md`, etc.).
   - Commite com a mensagem **exata** indicada no passo.
5. Se um passo falhar (comando erra, ferramenta não instalada, etc.), **pare e reporte ao usuário** — não tente corrigir o problema do projeto neste momento. A auditoria só observa e registra; não corrige.

## Regras absolutas

| Regra | Justificativa |
|---|---|
| 🚫 Nunca alterar código de produção (`backend/app/`, `frontend/app|components|lib`) durante a auditoria | A auditoria documenta; correções vêm em PRs separados depois |
| 🚫 Nunca commitar mais de um passo por commit | Atomicidade permite reverter passos individualmente |
| 🚫 Nunca mencionar IA, Claude, agente, autor automatizado em mensagens de commit | Convenção do projeto (memória `feedback_commit_workflow.md`) |
| 🚫 Nunca usar `git add -A` ou `git add .` | Stage explícito por arquivo evita commitar artefatos |
| ✅ Sempre rodar `make check` ou as ferramentas equivalentes antes de commitar **se** o passo modificou código (não é o caso desta auditoria — apenas docs) | Convenção do projeto |
| ✅ Sempre usar Conventional Commits em português | `docs(auditoria): ...`, `chore(auditoria): ...` |
| ✅ Quando um comando precisar de cache writable, usar `RUFF_CACHE_DIR=/tmp/ruff-$$` etc. | `.ruff_cache` no repo é root-owned (legado de container) |
| ✅ Toda evidência (output de comando) vai para `docs/auditoria/artefatos/<nome>.txt` | Reproduzibilidade |

## Estrutura de arquivos criada por este runbook

```
docs/auditoria/
├── plano.md                       (já existe — descreve o "o quê")
├── runbook.md                     (este arquivo — descreve o "como")
├── log.md                         (cronologia da execução)
├── achados.md                     (lista priorizada de problemas)
├── 01-arquitetura.md              (frente A)
├── 02-backend.md                  (frente B)
├── 03-ia.md                       (frente C)
├── 04-frontend.md                 (frente D)
├── 05-workers.md                  (frente E)
├── 06-banco.md                    (frente F)
├── 07-seguranca.md                (frente G)
├── 08-testes.md                   (frente H)
├── 09-qualidade.md                (frente I)
├── 10-observabilidade.md          (frente J)
├── 11-dx-docs.md                  (frente K)
├── relatorio-preliminar.md        (consolidação)
└── artefatos/                     (outputs brutos de comandos)
    ├── baseline-ruff.txt
    ├── baseline-mypy.txt
    ├── baseline-coverage.txt
    ├── ...
```

## Templates

### Template de entrada em `log.md`

```markdown
## PASSO X.Y — <título do passo>

- **Início:** <YYYY-MM-DD HH:MM>
- **Fim:** <YYYY-MM-DD HH:MM>
- **Comando(s) executado(s):** `<comando>`
- **Artefato(s):** `docs/auditoria/artefatos/<arquivo>.txt`
- **Achados gerados:** AUD-001, AUD-002 (referenciar IDs em achados.md)
- **Commit:** `<sha curto>` `<mensagem>`
- **Notas:** (texto livre opcional, ex.: "comando demorou 4min", "ferramenta X não instalada")
```

### Template de achado em `achados.md`

```markdown
### AUD-NNN — <título curto e específico>

- **Severidade:** 🔴 crítica · 🟠 alta · 🟡 média · 🟢 baixa
- **Frente:** A · B · C · D · E · F · G · H · I · J · K
- **Arquivo:linha:** `backend/app/services/foo.py:123`
- **Descrição:** O que está errado e por quê é problema.
- **Evidência:** Trecho do código ou output de ferramenta.
- **Recomendação:** Como corrigir (snippet ou descrição curta).
- **Esforço:** S (< 1h) · M (1–4h) · L (> 4h)
- **Origem:** PASSO X.Y
```

IDs `AUD-NNN` são **sequenciais globalmente** (não por frente). Próximo ID começa em `AUD-001` e incrementa a cada novo achado.

### Template de mensagem de commit

```
docs(auditoria): <ação curta>

<corpo opcional descrevendo o que foi registrado, sem mencionar IA/Claude>
```

Exemplos válidos:
- `docs(auditoria): cria estrutura inicial e log de execução`
- `chore(auditoria): captura baseline de ruff e mypy`
- `docs(auditoria): registra achados da frente arquitetura`

---

## FASE 0 — Inicialização

### PASSO 0.1 — Criar estrutura inicial

**Objetivo:** criar arquivos vazios/skeleton para que passos seguintes só precisem editar.

**Inputs:** nenhum.

**Método:**
1. Criar diretório `docs/auditoria/artefatos/`.
2. Criar os arquivos abaixo com o cabeçalho indicado.

**Conteúdo de `docs/auditoria/log.md`:**
```markdown
# Log de Execução da Auditoria

Cronologia detalhada de cada passo executado.

---
```

**Conteúdo de `docs/auditoria/achados.md`:**
```markdown
# Achados da Auditoria

Lista de problemas encontrados, ordenada por ID. Para visão por severidade ver `relatorio-preliminar.md` ao fim da auditoria.

**Status totais:** críticos: 0 · altos: 0 · médios: 0 · baixos: 0 (atualizar a cada novo achado)

---
```

**Conteúdo de cada `docs/auditoria/0X-<frente>.md`** (criar 11 arquivos: `01-arquitetura.md` … `11-dx-docs.md`):
```markdown
# Frente <X> — <Nome>

**Plano:** ver `plano.md` § Frente <X>.

## Achados desta frente

(preenchido conforme passos vão sendo executados — referenciar IDs em achados.md)

## Notas e contexto

(texto livre conforme aprendizagens surgem)
```

**Conteúdo de `docs/auditoria/relatorio-preliminar.md`:**
```markdown
# Relatório Preliminar da Auditoria

Preenchido na FASE 13. Contém visão consolidada por severidade, métricas de baseline vs. final, recomendação de priorização para a fase de correção.
```

**Saída esperada:** 14 arquivos novos, 1 diretório novo.

**Aceitação:**
- `ls docs/auditoria/` lista 13 `.md` (incluindo `plano.md`, `runbook.md`).
- `ls docs/auditoria/artefatos/` existe e está vazio.

**Commit:**
```
docs(auditoria): cria estrutura inicial e arquivos por frente
```

---

## FASE 1 — Baseline (capturas de "estado zero")

> Cada passo desta fase roda uma ferramenta, salva o output em `artefatos/` e atualiza `log.md`. **Não gera achados.** A análise vem nas fases seguintes.

### PASSO 1.1 — Baseline ruff

**Objetivo:** capturar contagem e localização atual de erros ruff no backend.

**Método:**
```bash
cd /home/gabriel/projetos/CalorIA/backend
RUFF_CACHE_DIR=/tmp/ruff-baseline uvx ruff check . 2>&1 | tee /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/baseline-ruff.txt
```

**Aceitação:** arquivo `baseline-ruff.txt` existe; última linha contém "Found N errors" ou "All checks passed!".

**Atualizar log.md:** adicionar entrada usando o template, registrando `N` erros.

**Commit:**
```
chore(auditoria): captura baseline ruff
```

---

### PASSO 1.2 — Baseline mypy strict

**Método:**
```bash
cd /home/gabriel/projetos/CalorIA/backend
.venv/bin/python -m mypy --strict app/ 2>&1 | tee /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/baseline-mypy.txt
```

Se `mypy` não estiver instalado no venv:
```bash
uvx --from mypy mypy --strict app/ 2>&1 | tee /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/baseline-mypy.txt
```

**Aceitação:** arquivo termina com "Found N errors" ou "Success".

**Commit:**
```
chore(auditoria): captura baseline mypy strict
```

---

### PASSO 1.3 — Baseline radon (complexidade ciclomática)

**Método:**
```bash
cd /home/gabriel/projetos/CalorIA/backend
uvx radon cc app/ -s -nc -a 2>&1 | tee /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/baseline-radon-cc.txt
uvx radon mi app/ -s 2>&1 | tee /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/baseline-radon-mi.txt
```

**Aceitação:** os dois arquivos têm conteúdo. `baseline-radon-cc.txt` lista funções com complexidade ≥ B (acumulado) e exibe média.

**Commit:**
```
chore(auditoria): captura baseline radon
```

---

### PASSO 1.4 — Baseline cobertura backend

> Pré-requisito: Postgres + Redis rodando. Verificar com `docker ps`. Se não estiver rodando, pular este passo e registrar nota em `log.md` com texto "PASSO 1.4 pulado — DB não disponível; rodar manualmente em ambiente com `make dev` ativo".

**Método:**
```bash
cd /home/gabriel/projetos/CalorIA/backend
TEST_DATABASE_URL=postgresql+asyncpg://caloria:caloria@localhost:5432/caloria_test \
  .venv/bin/pytest --cov=app --cov-report=term --cov-report=xml -q 2>&1 \
  | tee /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/baseline-coverage.txt
mv coverage.xml /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/baseline-coverage.xml 2>/dev/null || true
```

**Aceitação:** `baseline-coverage.txt` contém linha "TOTAL ... NN%".

**Commit:**
```
chore(auditoria): captura baseline cobertura backend
```

---

### PASSO 1.5 — Baseline pip-audit

**Método:**
```bash
cd /home/gabriel/projetos/CalorIA/backend
uvx pip-audit -r <(uv pip compile pyproject.toml 2>/dev/null) 2>&1 \
  | tee /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/baseline-pip-audit.txt \
  || uvx pip-audit . 2>&1 | tee /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/baseline-pip-audit.txt
```

**Aceitação:** arquivo existe com lista de pacotes ou "No known vulnerabilities found".

**Commit:**
```
chore(auditoria): captura baseline pip-audit
```

---

### PASSO 1.6 — Baseline npm audit

**Método:**
```bash
cd /home/gabriel/projetos/CalorIA/frontend
npm audit --json 2>&1 | tee /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/baseline-npm-audit.json
npm audit 2>&1 | tee /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/baseline-npm-audit.txt
```

**Commit:**
```
chore(auditoria): captura baseline npm audit
```

---

### PASSO 1.7 — Baseline ESLint frontend

**Método:**
```bash
cd /home/gabriel/projetos/CalorIA/frontend
npm run lint 2>&1 | tee /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/baseline-eslint.txt
```

**Commit:**
```
chore(auditoria): captura baseline eslint
```

---

### PASSO 1.8 — Baseline tsc --noEmit

**Método:**
```bash
cd /home/gabriel/projetos/CalorIA/frontend
npx tsc --noEmit 2>&1 | tee /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/baseline-tsc.txt
```

**Commit:**
```
chore(auditoria): captura baseline tsc
```

---

### PASSO 1.9 — Baseline LOC e estrutura

**Método:**
```bash
{
  echo "=== Backend (sem alembic, scripts, tests) ==="
  find /home/gabriel/projetos/CalorIA/backend/app -name "*.py" | xargs wc -l | tail -1
  echo
  echo "=== Frontend (sem mocks, tests, build) ==="
  find /home/gabriel/projetos/CalorIA/frontend -name "*.ts" -o -name "*.tsx" 2>/dev/null \
    | grep -v "__tests__\|__mocks__\|node_modules\|.next" \
    | xargs wc -l | tail -1
  echo
  echo "=== Tests backend ==="
  find /home/gabriel/projetos/CalorIA/backend/tests -name "*.py" | xargs wc -l | tail -1
  echo
  echo "=== Tests frontend ==="
  find /home/gabriel/projetos/CalorIA/frontend/__tests__ /home/gabriel/projetos/CalorIA/frontend/e2e -type f 2>/dev/null | xargs wc -l | tail -1
  echo
  echo "=== Endpoints REST ==="
  grep -rE "@router\.(get|post|patch|put|delete)" /home/gabriel/projetos/CalorIA/backend/app/api/v1 | wc -l
  echo
  echo "=== Modelos SQLAlchemy ==="
  ls /home/gabriel/projetos/CalorIA/backend/app/models/*.py | grep -v __init__ | wc -l
  echo
  echo "=== Migrações Alembic ==="
  ls /home/gabriel/projetos/CalorIA/backend/alembic/versions/*.py | wc -l
} 2>&1 | tee /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/baseline-loc.txt
```

**Atualizar `relatorio-preliminar.md`** adicionando seção:

```markdown
## Métricas de baseline

(copiar conteúdo de artefatos/baseline-loc.txt)
```

**Commit:**
```
chore(auditoria): captura baseline LOC e estrutura
```

---

### PASSO 1.10 — Consolidar baselines em log.md

**Objetivo:** dar visão de uma página dos números atuais.

**Método:** ler todos os arquivos `artefatos/baseline-*.txt` e adicionar uma seção **§ Snapshot inicial** em `log.md`:

```markdown
## § Snapshot inicial (2026-MM-DD)

| Ferramenta | Resultado |
|---|---|
| ruff | N errors |
| mypy strict | N errors |
| radon avg CC | A.B (label) |
| pytest cov | NN% |
| pip-audit | N vulns |
| npm audit | N vulns (M high) |
| eslint | N warnings |
| tsc | N errors |
| LOC backend | N |
| LOC frontend | N |
```

**Commit:**
```
docs(auditoria): consolida snapshot inicial em log
```

---

## FASE 2 — Frente A (Arquitetura)

> Saídas vão para `docs/auditoria/01-arquitetura.md`. Achados vão para `achados.md`.

### PASSO 2.1 — Verificar separação API → service

**Método:**
```bash
rg -n "(select|insert|update|delete)\(" /home/gabriel/projetos/CalorIA/backend/app/api/v1/ \
  | tee /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/A1-queries-em-routers.txt
```

**Análise:**
- Cada match é um candidato a achado: query SQL diretamente em router (deve estar em service).
- Listar arquivos:linhas afetados.

**Atualizar `01-arquitetura.md`:** adicionar seção "## A.1 Separação de camadas" com lista de violações ou "Nenhuma violação encontrada".

**Para cada violação real:** criar achado em `achados.md` com `Severidade: 🟡 média`, `Frente: A`.

**Commit:**
```
docs(auditoria): registra análise de separação de camadas
```

---

### PASSO 2.2 — Mapear filtragem por user_id

**Método:**
```bash
{
  echo "=== Endpoints (suspeitos sem user_id) ==="
  rg -n "@router\.(get|post|patch|put|delete)" -A 8 /home/gabriel/projetos/CalorIA/backend/app/api/v1/ \
    | grep -v "user_id\|get_current_user_id"
  echo
  echo "=== Queries em services sem filtro user_id ==="
  rg -n "select\(" /home/gabriel/projetos/CalorIA/backend/app/services/ -A 4 \
    | grep -v "user_id"
} > /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/A2-user-id-coverage.txt 2>&1
```

**Análise manual:** abrir cada match e validar se a ausência de `user_id` é real ou se filtra por outra FK que indiretamente garante.

**Atualizar `01-arquitetura.md` § A.2** com tabela:
| Endpoint/Query | Filtra por user_id? | Justificativa |
|---|---|---|

**Achados:** qualquer query que retorne dados de usuário sem filtro é 🔴 crítico.

**Commit:**
```
docs(auditoria): mapeia filtragem por user_id
```

---

### PASSO 2.3 — Auditar relacionamentos cascade

**Método:**
```bash
rg -n "relationship\(|ForeignKey\(" /home/gabriel/projetos/CalorIA/backend/app/models/ \
  | tee /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/A3-relacionamentos.txt
```

**Análise:** para cada relacionamento, anotar:
- `cascade=` (ausente | "all, delete-orphan" | outro)
- `ondelete=` no FK (ausente | "CASCADE" | "SET NULL" | "RESTRICT")
- Coerência: relação de posse → cascade delete; relação referencial → SET NULL.

**Atualizar `01-arquitetura.md` § A.3** com tabela.

**Commit:**
```
docs(auditoria): registra auditoria de cascades e FKs
```

---

### PASSO 2.4 — Documentar responsabilidades dos services

**Método:** abrir cada service em `backend/app/services/` e em `services/ai/`, anotar em `01-arquitetura.md` § A.4 uma linha por service:

```markdown
| Service | LOC | Responsabilidade declarada (docstring/nome) | Métodos públicos | Risco |
|---|---|---|---|---|
| MealService | 165 | CRUD de refeições + agregação | list_meals, create_meal, get_meal, update_meal, delete_meal_item, delete_meal, get_macros_by_date_range, get_daily_summary | OK |
```

**Achados candidatos** (conforme `plano.md` Anexo A):
- Se algum service > 300 LOC com > 4 responsabilidades distintas → 🟡 médio com recomendação de quebra.

**Commit:**
```
docs(auditoria): documenta responsabilidades de services
```

---

### PASSO 2.5 — Mapeamento de dependências entre services

**Método:**
```bash
rg -n "from app\.services" /home/gabriel/projetos/CalorIA/backend/app/services/ \
  | tee /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/A5-dep-services.txt
```

**Atualizar `01-arquitetura.md` § A.4** com lista textual ou diagrama Mermaid:

```mermaid
graph LR
  DashboardService --> MealService
  DashboardService --> WeightService
  DashboardService --> HydrationService
  ...
```

**Achados candidatos:** ciclos de dependência (A → B → A). Se houver, 🟠 alto.

**Commit:**
```
docs(auditoria): mapeia dependencias entre services
```

---

## FASE 3 — Frente B (Backend)

### PASSO 3.1 — Routers: response_model e status codes

**Método:**
```bash
{
  echo "=== Endpoints sem response_model (excluindo 204) ==="
  rg -B 1 "@router\." /home/gabriel/projetos/CalorIA/backend/app/api/v1/ \
    | grep -v "response_model\|HTTP_204\|HTTP_201"
  echo
  echo "=== Status codes usados ==="
  rg -o "status_code=[A-Z_0-9]+" /home/gabriel/projetos/CalorIA/backend/app/api/v1/ | sort | uniq -c
} > /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/B1-routers-response.txt 2>&1
```

**Atualizar `02-backend.md` § B.1** com tabela por router.

**Achados:** qualquer endpoint público sem `response_model` é 🟡.

**Commit:**
```
docs(auditoria): registra analise response_model dos routers
```

---

### PASSO 3.2 — Routers: HTTPException com `from`

**Método:**
```bash
rg -n "raise HTTPException" /home/gabriel/projetos/CalorIA/backend/app/api/v1/ -A 3 \
  | tee /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/B2-httpexc.txt
```

**Análise:** identificar `raise HTTPException(...)` que **não** termina com `from exc` ou `from None`. Hoje há um caso conhecido: `meals.py:101` (já no Anexo A do plano).

**Achados:** registrar cada um em `achados.md` 🟢 baixo.

**Commit:**
```
docs(auditoria): mapeia raise HTTPException sem from
```

---

### PASSO 3.3 — Routers: paginação consistente

**Método:**
```bash
rg -n "skip|limit" /home/gabriel/projetos/CalorIA/backend/app/api/v1/ \
  | grep "Query" \
  | tee /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/B3-paginacao.txt
```

**Análise:** comparar `ge=`, `le=` em todos os endpoints com paginação. Padronizar:
- skip: `ge=0`
- limit: `ge=1, le=100` (ou justificar limites maiores).

**Achados:** divergências viram 🟢.

**Commit:**
```
docs(auditoria): registra padrao de paginacao dos routers
```

---

### PASSO 3.4 — Services: detecção de N+1

**Método:** revisar manualmente cada service procurando padrão `for X in Y: await db.execute(...)`. Lista de candidatos suspeitos:

- `backend/app/services/dashboard_service.py:get_today` — 4 queries serial (já documentado, OK).
- `backend/app/workers/tasks/reminders.py:_send_hydration_reminders_async` — `HydrationService.get_day_summary` em loop por usuário (suspeita N+1).

**Comando de apoio:**
```bash
rg -n "for .* in .*:\s*$" /home/gabriel/projetos/CalorIA/backend/app/services/ /home/gabriel/projetos/CalorIA/backend/app/workers/ -A 5 \
  | grep -B 1 "await.*execute\|await.*get_\|await.*list" \
  | tee /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/B4-n-mais-1.txt
```

**Atualizar `02-backend.md` § B.3** com lista.

**Achados:** N+1 confirmado é 🟠.

**Commit:**
```
docs(auditoria): mapeia possiveis n+1
```

---

### PASSO 3.5 — Schemas Pydantic: from_attributes

**Método:**
```bash
{
  echo "=== Response schemas com from_attributes ==="
  rg -n "from_attributes" /home/gabriel/projetos/CalorIA/backend/app/schemas/
  echo
  echo "=== Schemas Response sem from_attributes ==="
  rg -B 2 "Response\(BaseModel\)" /home/gabriel/projetos/CalorIA/backend/app/schemas/ \
    | grep -A 2 "Response"
} > /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/B5-pydantic-config.txt 2>&1
```

**Análise:** todo `*Response(BaseModel)` deveria ter `model_config = {"from_attributes": True}` se for serializado de ORM.

**Commit:**
```
docs(auditoria): mapeia from_attributes em schemas
```

---

### PASSO 3.6 — Validação de inputs sensíveis

**Método:** abrir cada `*Create` e `*Update` schema; conferir constraints.

| Schema | Campo | Constraint atual | Recomendação |
|---|---|---|---|

Pré-identificados:
- `MealItemCreate.quantity` — provavelmente sem `gt=0`. Conferir.
- `analyze-photo.image_base64` — sem limite de tamanho (DoS). Conferir em `app/schemas/ai.py`.

**Commit:**
```
docs(auditoria): registra validacao de inputs em schemas
```

---

### PASSO 3.7 — Type ignores

**Método:**
```bash
rg -n "# type: ignore" /home/gabriel/projetos/CalorIA/backend/app/ \
  | tee /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/B7-type-ignores.txt
```

**Análise:** classificar cada `# type: ignore` como:
1. Justificável (lib externa sem stubs).
2. Trabalho — pode ser eliminado com tipagem correta.

**Achados:** cada categoria 2 vira 🟢.

**Commit:**
```
docs(auditoria): cataloga type ignores no backend
```

---

## FASE 4 — Frente C (Pipeline IA)

### PASSO 4.1 — AIClient: cache, retry, observabilidade

**Método:** ler `backend/app/services/ai/ai_client.py` (155 linhas). Anotar em `03-ia.md` § C.1:

| Aspecto | Estado | Risco |
|---|---|---|
| Cache key | SHA-256 24 hex | 🟢 baixíssima colisão |
| Cache TTL | 7 dias | OK |
| Retry trigger | `if "429" in str(exc)` | 🟡 frágil |
| Tentativas | 4 (15s→30s→60s→120s, total ~3.75 min) | 🟡 risco timeout uvicorn |
| Logs de tokens | `logger.info` simples | 🟡 sem agregação |

**Achados:** entradas 🟡 viram registros em `achados.md`.

**Commit:**
```
docs(auditoria): analisa cliente de IA
```

---

### PASSO 4.2 — Duplicação MealParser ↔ VisionParser

**Método:**
```bash
diff -u /home/gabriel/projetos/CalorIA/backend/app/services/ai/meal_parser.py \
        /home/gabriel/projetos/CalorIA/backend/app/services/ai/vision_parser.py \
  > /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/C2-parsers-diff.txt 2>&1 || true
```

**Análise:** anotar quantas linhas das duas classes são idênticas. Pré-identificado: `_lookup_and_fill` e `_estimate_macros_batch` ~90% iguais.

**Atualizar `03-ia.md` § C.2** com plano de extração de classe base.

**Achados:** 1 entrada 🟡 (refactor candidato).

**Commit:**
```
docs(auditoria): registra duplicacao em parsers
```

---

### PASSO 4.3 — FoodLookup: performance

**Método:**
1. Ler `backend/app/services/ai/food_lookup.py`.
2. Estimar n-gramas gerados para um texto típico de refeição (10 palavras): n=2..4 → ~25 candidatos × 1 query SQL cada → ~25 queries.
3. Executar (se DB disponível) `EXPLAIN ANALYZE` em uma query típica:
```bash
docker exec caloria_postgres psql -U caloria -d caloria_db -c "
EXPLAIN ANALYZE
SELECT id, name, similarity(search_text, 'arroz branco cozido') AS score
FROM foods
WHERE search_text %>> 'arroz branco cozido' OR similarity(search_text, 'arroz branco cozido') >= 0.18
ORDER BY score DESC LIMIT 20;
" 2>&1 | tee /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/C3-food-lookup-explain.txt
```

**Atualizar `03-ia.md` § C.3** com:
- Quantidade de n-gramas gerados em casos típicos.
- Tempo médio por query.
- Recomendação: single query batched ou tsvector + ts_rank.

**Achados:** 1 entrada 🟠 (otimização batch).

**Commit:**
```
docs(auditoria): analisa performance de food_lookup
```

---

### PASSO 4.4 — InsightsGenerator: decomposição

**Método:**
```bash
{
  echo "=== Métodos públicos ==="
  rg -n "    async def [a-z]" /home/gabriel/projetos/CalorIA/backend/app/services/ai/insights_generator.py
  echo
  echo "=== Tamanho por método ==="
  awk '/^    async def [a-z]/ {if (name) print name": "NR-start; name=$3; start=NR} END {if (name) print name": "NR-start}' \
    /home/gabriel/projetos/CalorIA/backend/app/services/ai/insights_generator.py
} > /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/C4-insights-metods.txt 2>&1
```

**Atualizar `03-ia.md` § C.4** com tabela de métodos × LOC × responsabilidade.

**Achados:** 1 entrada 🟠 (god class candidate).

**Commit:**
```
docs(auditoria): analisa decomposicao de insights_generator
```

---

### PASSO 4.5 — extract_json_from_ai_response: robustez

**Método:** ler `backend/app/services/ai/utils.py`. Identificar caminhos:
- ✅ Aceita ```json…```
- ✅ Aceita array nu
- ❌ NÃO aceita `{"items": [...]}`
- ❌ NÃO aceita texto antes/depois do JSON

Documentar em `03-ia.md` § C.5.

**Achados:** 🟡 robustez do parsing.

**Commit:**
```
docs(auditoria): registra robustez do parsing JSON da IA
```

---

## FASE 5 — Frente D (Frontend)

### PASSO 5.1 — Páginas grandes

**Método:**
```bash
wc -l /home/gabriel/projetos/CalorIA/frontend/app/\(dashboard\)/*/page.tsx \
       /home/gabriel/projetos/CalorIA/frontend/components/dashboard/*.tsx \
  | sort -rn \
  | tee /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/D1-paginas-loc.txt
```

**Atualizar `04-frontend.md` § D.1** com tabela de páginas/componentes > 300 LOC e plano de quebra.

**Achados:** cada página > 500 LOC vira 🟡.

**Commit:**
```
docs(auditoria): mapeia paginas frontend grandes
```

---

### PASSO 5.2 — Hooks customizados

**Método:** abrir cada `frontend/lib/hooks/*.ts`. Validar:
- ✅ `useQuery` para reads.
- ✅ `useMutation` com `onSuccess` invalidando cache.
- ✅ `staleTime`/`gcTime` definidos.
- ❓ Optimistic updates ausentes.

**Atualizar `04-frontend.md` § D.2** com checklist e lista de oportunidades.

**Commit:**
```
docs(auditoria): analisa hooks de api do frontend
```

---

### PASSO 5.3 — Camada API e cache de token

**Método:** ler `frontend/lib/api.ts` (122 linhas). Documentar fluxo em `04-frontend.md` § D.3:
- Resolução de token (cache 90s, dedupe Promise, refresh proativo 2min antes).
- Retry transparente em 401 (com `_retry` flag).
- Logs de console.

**Pré-identificado:** logs de console em produção. Verificar se há gate `process.env.NODE_ENV`.

**Achados:** 🟢 logs em produção.

**Commit:**
```
docs(auditoria): registra fluxo da camada api do frontend
```

---

### PASSO 5.4 — Bug do contrato login (verificação)

**Método:**
1. Ler `backend/app/api/v1/auth.py:37-50` — confirmar que `/login` retorna `TokenResponse(access_token, refresh_token)` sem `user`.
2. Ler `frontend/app/api/auth/[...nextauth]/route.ts:60-72` — confirmar que `authorize` lê `data.user?.id` e `data.user?.name`.
3. Documentar discrepância.

**Atualizar `04-frontend.md` § D.4** + criar achado **🟠 alto** em `achados.md` com referências cruzadas.

**Commit:**
```
docs(auditoria): registra discrepancia de contrato no login
```

---

### PASSO 5.5 — TypeScript: usos de any

**Método:**
```bash
rg -n ": any\b|as any\b" \
  /home/gabriel/projetos/CalorIA/frontend/app \
  /home/gabriel/projetos/CalorIA/frontend/components \
  /home/gabriel/projetos/CalorIA/frontend/lib 2>/dev/null \
  | grep -v "__tests__\|__mocks__" \
  | tee /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/D5-any-usage.txt
```

**Análise:** classificar cada `any` em:
1. SpeechRecognition (Web Speech API tem tipos padrão — substituir).
2. Outros (justificar ou tipar).

**Atualizar `04-frontend.md` § D.5**.

**Achados:** 🟢 cada any.

**Commit:**
```
docs(auditoria): cataloga usos de any no frontend
```

---

### PASSO 5.6 — PWA / Service Worker

**Método:** ler `frontend/public/sw.js` e `frontend/app/manifest.ts`. Validar:
- Eventos `push` e `notificationclick` corretos.
- Estratégia de update (`skipWaiting`, `clientsClaim`).
- Manifest tem ícones em todos os tamanhos requeridos.
- Escopo do SW.

**Atualizar `04-frontend.md` § D.7**.

**Commit:**
```
docs(auditoria): analisa pwa e service worker
```

---

### PASSO 5.7 — Bundle size analysis

**Método (opcional, requer build em ambiente limpo):**
```bash
cd /home/gabriel/projetos/CalorIA/frontend
ANALYZE=true npm run build 2>&1 \
  | tee /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/D7-bundle.txt \
  || echo "Skipped: ANALYZE não suportado (sem @next/bundle-analyzer)"
```

Se sem analyzer, registrar nota em `04-frontend.md` § D.6 indicando que esta verificação requer instalar `@next/bundle-analyzer`.

**Commit:**
```
docs(auditoria): registra plano de bundle analysis
```

---

## FASE 6 — Frente E (Workers / Web Push)

### PASSO 6.1 — Padrão `_run` deprecated

**Método:**
```bash
rg -n "asyncio\.get_event_loop\(\)" /home/gabriel/projetos/CalorIA/backend/app/ \
  | tee /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/E1-get-event-loop.txt
```

**Atualizar `05-workers.md` § E.2** confirmando todas as ocorrências (3 esperadas em `reminders.py`, `reports.py`, `maintenance.py`).

**Achados:** 1 entrada 🟠 (deprecated desde Python 3.10).

**Commit:**
```
docs(auditoria): registra uso deprecated de get_event_loop
```

---

### PASSO 6.2 — dispatch_due_reminders: timezone

**Método:** ler `backend/app/workers/tasks/reminders.py:32-72`. Validar:
- `datetime.now()` é naive (sem TZ).
- `Reminder.time` no modelo é `Time` (naive).
- Comparação `reminder.time.hour != current_hour`.
- Servidor (Docker) está com `TZ=America/Sao_Paulo`?

**Comando de apoio:**
```bash
docker exec caloria_postgres psql -U caloria -d caloria_db -c "SHOW timezone;" 2>&1 \
  | tee /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/E2-tz.txt
docker inspect caloria_postgres --format '{{ range .Config.Env }}{{ println . }}{{ end }}' 2>&1 \
  | grep -i tz \
  | tee -a /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/E2-tz.txt
```

**Atualizar `05-workers.md` § E.3**.

**Achados:** 1 entrada 🟠 (bug timezone latente).

**Commit:**
```
docs(auditoria): analisa timezone em dispatch_due_reminders
```

---

### PASSO 6.3 — Hardcode de meta de hidratação

**Método:**
```bash
rg -n "2000" /home/gabriel/projetos/CalorIA/backend/app/workers/tasks/reminders.py \
  | tee /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/E3-hydration-hardcode.txt
```

**Análise:** confirmar que `User.water_goal_ml` (em `models/user.py`) existe mas não é usado.

**Atualizar `05-workers.md` § E.5** + achado 🟠 alto.

**Commit:**
```
docs(auditoria): registra hardcode de meta de hidratacao
```

---

### PASSO 6.4 — Duplicação de tratamento WebPush 410

**Método:**
```bash
rg -n "WebPushException\|status_code == 410\|expired_ids" \
  /home/gabriel/projetos/CalorIA/backend/app/workers/ \
  /home/gabriel/projetos/CalorIA/backend/app/services/push_service.py \
  | tee /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/E4-push-410.txt
```

**Atualizar `05-workers.md` § E.4** com tabela de ocorrências e plano de extração para `PushService.send_with_cleanup`.

**Achados:** 🟡 duplicação.

**Commit:**
```
docs(auditoria): registra duplicacao de tratamento de push expirado
```

---

### PASSO 6.5 — Maintenance e cleanup

**Método:** ler `backend/app/workers/tasks/maintenance.py`. Validar:
- `cleanup_old_conversations` — query usa índice em `created_at`?
- `recalculate_tdee` — threshold "peso mudou ≥ 2 kg" coerente?

Comando de apoio para verificar índices:
```bash
docker exec caloria_postgres psql -U caloria -d caloria_db -c "\d ai_conversations" 2>&1 \
  | tee /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/E5-ai-conv-indexes.txt
```

**Commit:**
```
docs(auditoria): analisa tasks de maintenance
```

---

## FASE 7 — Frente F (Banco de Dados)

### PASSO 7.1 — Inventário de índices

**Método:**
```bash
docker exec caloria_postgres psql -U caloria -d caloria_db -c "
SELECT schemaname, tablename, indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
" 2>&1 | tee /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/F1-indexes.txt
```

**Atualizar `06-banco.md` § F.1** com tabela de índices presentes vs. recomendados (ver plano § F.1).

**Achados:** cada índice ausente em coluna usada em WHERE/JOIN crítico → 🟡.

**Commit:**
```
docs(auditoria): inventaria indices do banco
```

---

### PASSO 7.2 — EXPLAIN ANALYZE de queries críticas

**Método:** rodar EXPLAIN ANALYZE para queries identificadas como "hot path":

```bash
docker exec caloria_postgres psql -U caloria -d caloria_db <<'EOF' 2>&1 \
  | tee /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/F2-explain.txt

-- 1. Daily summary
EXPLAIN ANALYZE
SELECT m.*, mi.* FROM meals m
JOIN meal_items mi ON mi.meal_id = m.id
WHERE m.user_id = 1 AND m.date = CURRENT_DATE;

-- 2. Macros by date range (dashboard semanal)
EXPLAIN ANALYZE
SELECT m.date, SUM(mi.calories), SUM(mi.protein), SUM(mi.carbs), SUM(mi.fat)
FROM meals m JOIN meal_items mi ON mi.meal_id = m.id
WHERE m.user_id = 1 AND m.date BETWEEN CURRENT_DATE - INTERVAL '7 days' AND CURRENT_DATE
GROUP BY m.date ORDER BY m.date;

-- 3. Notifications unread count
EXPLAIN ANALYZE
SELECT COUNT(*) FROM notifications WHERE user_id = 1 AND read = false;

-- 4. Reminders due (workers)
EXPLAIN ANALYZE
SELECT * FROM reminders WHERE active = true;

EOF
```

**Atualizar `06-banco.md` § F.1** com resultados (Seq Scan vs. Index Scan).

**Commit:**
```
docs(auditoria): registra explain de queries criticas
```

---

### PASSO 7.3 — Migrações Alembic: reversibilidade

**Método:**
```bash
{
  for f in /home/gabriel/projetos/CalorIA/backend/alembic/versions/*.py; do
    echo "=== $(basename "$f") ==="
    grep -c "^def downgrade" "$f"
  done
} > /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/F3-downgrade.txt 2>&1
```

**Atualizar `06-banco.md` § F.2**: cada migração deve ter `downgrade()` não-vazio.

**Achados:** migração sem downgrade → 🟡.

**Commit:**
```
docs(auditoria): valida reversibilidade das migracoes
```

---

### PASSO 7.4 — Pool sizing e conexões

**Método:** ler `backend/app/core/database.py:13-22`. Documentar valores atuais e calcular máximo:

```
backend uvicorn workers (default Docker = 1) × pool_size (10) + max_overflow (20) = 30 por worker
+ celery worker (1 process) × 30 = 30
+ celery beat (1 process) × 30 = 30
≈ ~90 conexões pico

Postgres default max_connections = 100 → margem apertada com mais workers
```

**Atualizar `06-banco.md` § F.3** com cálculo + recomendação para escala.

**Achados:** 🟡 risco de saturação.

**Commit:**
```
docs(auditoria): documenta pool sizing
```

---

### PASSO 7.5 — Backup e disaster recovery

**Método:** verificar:
- Existe cron de backup configurado em `scripts/setup-server.sh`?
- `docs/deploy.md` cobre estratégia de backup?
- Local de armazenamento (offsite/local)?
- Política de retenção?

**Atualizar `06-banco.md` § F.5** com estado atual e gap.

**Achados:** ausência de backup automatizado → 🔴 crítico se já em produção; 🟠 alto se ainda em prep.

**Commit:**
```
docs(auditoria): analisa estrategia de backup
```

---

## FASE 8 — Frente G (Segurança)

### PASSO 8.1 — 🔴 CRÍTICO: credenciais em e2e

**Método:**
```bash
rg -n "***REMOVED***|gabrielnegreirossaraiva38@gmail" \
  /home/gabriel/projetos/CalorIA/ 2>/dev/null \
  | tee /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/G1-creds.txt
git log --all --full-history -p -- frontend/e2e/auth.spec.ts 2>&1 \
  | grep -E "082405|gabrielnegreiros" \
  | head -20 \
  | tee -a /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/G1-creds.txt
```

**Atualizar `07-seguranca.md` § G.6** com:
- Caminho do arquivo afetado.
- Ações imediatas que **não** são parte da auditoria mas estão pendentes (trocar senha em produção, remover do código, considerar reescrita de histórico).

**Achado:** **AUD-NNN** com **🔴 Severidade: crítica**.

**Commit:**
```
docs(auditoria): registra credenciais expostas em testes e2e
```

---

### PASSO 8.2 — Auth flow review

**Método:** ler `backend/app/api/v1/auth.py`, `app/core/security.py`, `app/core/deps.py`, `app/services/auth_service.py`. Validar checklist:

| Item | Estado |
|---|---|
| Algorithm é HS256 (não none) | ? |
| Access TTL = 30min | ? |
| Refresh TTL = 30 dias | ? |
| Refresh blacklisted após uso | ? |
| Token type validado em decode | ? |
| `from None` em raises de credenciais | ? |
| Default SECRET_KEY é inseguro? | ? |

**Atualizar `07-seguranca.md` § G.1**.

**Achados:** SECRET_KEY default inseguro sem fail-fast → 🟠.

**Commit:**
```
docs(auditoria): valida fluxo de auth
```

---

### PASSO 8.3 — Validação de inputs (DoS / overflow)

**Método:** ler `backend/app/schemas/`. Procurar campos sem limite:
- `image_base64` em `ai.py` (pode ser MB).
- `description` em `ai.py` (sem max).
- `notes` em meal/weight/mood (Text sem limite no DB).

**Atualizar `07-seguranca.md` § G.3**.

**Achados:** ausência de `max_length` em inputs públicos → 🟡.

**Commit:**
```
docs(auditoria): mapeia validacao de inputs
```

---

### PASSO 8.4 — Rate limit assessment

**Método:**
```bash
rg -n "rate_limit|slowapi|RateLimit" /home/gabriel/projetos/CalorIA/backend/ 2>/dev/null \
  | tee /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/G4-rate-limit.txt
```

**Atualizar `07-seguranca.md` § G.5**: confirmar ausência total → recomendar `slowapi` em `/auth/login`, `/auth/register`, `/ai/analyze-*`.

**Achados:** 🟠 ausência total para projeto multi-usuário.

**Commit:**
```
docs(auditoria): registra ausencia de rate limit
```

---

### PASSO 8.5 — Headers de segurança e CORS

**Método:** ler `Caddyfile`, `frontend/next.config.mjs`, `backend/app/main.py` (CORS middleware).

Validar presença de:
- `X-Frame-Options: DENY` ou `SAMEORIGIN`.
- `X-Content-Type-Options: nosniff`.
- `Strict-Transport-Security` (Caddy faz por padrão se HTTPS).
- `Content-Security-Policy`.
- `Referrer-Policy`.

**Atualizar `07-seguranca.md` § G.8**.

**Achados:** cada header ausente → 🟡.

**Commit:**
```
docs(auditoria): mapeia headers de seguranca
```

---

### PASSO 8.6 — Secret scan no histórico git

**Método:**
```bash
git log --all --full-history -p 2>&1 \
  | grep -iE "(api_key|secret_key|password|token).*[=:].*[a-zA-Z0-9]{16}" \
  | head -100 \
  | tee /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/G6-secret-scan.txt
```

(Opcional, se `gitleaks` instalado:)
```bash
gitleaks detect --source /home/gabriel/projetos/CalorIA --report-path /tmp/gitleaks.json 2>&1 \
  | tee -a /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/G6-secret-scan.txt
```

**Atualizar `07-seguranca.md` § G.6**.

**Achados:** cada match real (não falso positivo) → 🔴.

**Commit:**
```
docs(auditoria): executa secret scan no historico
```

---

### PASSO 8.7 — Autorização horizontal

**Método:** para cada endpoint que recebe `{id}` em path, confirmar filtragem por `user_id`:

```bash
rg -n "/\{[a-z_]+_id\}" /home/gabriel/projetos/CalorIA/backend/app/api/v1/ -A 10 \
  | tee /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/G7-authz.txt
```

**Análise:** abrir cada endpoint e confirmar que o service correspondente filtra por `user_id`.

**Achados:** qualquer endpoint sem filtro → 🔴.

**Commit:**
```
docs(auditoria): valida autorizacao horizontal por endpoint
```

---

## FASE 9 — Frente H (Testes)

### PASSO 9.1 — Investigar bug de fixture unit

**Método:**
1. Reproduzir: `cd backend && .venv/bin/pytest tests/unit/ -q 2>&1 | tail -20`.
2. Confirmar padrão "49 passed, 49 errors".
3. Ler `tests/conftest.py` e `tests/unit/conftest.py`.
4. Documentar causa raiz: `clean_db` autouse roda mesmo quando o stub `setup_test_database` não criou tabelas.

**Atualizar `08-testes.md` § H.2** com explicação completa.

**Achados:** 1 entrada 🟠 (test infrastructure bug).

**Commit:**
```
docs(auditoria): documenta bug de fixture nos testes unit
```

---

### PASSO 9.2 — Cobertura por área

**Método (se baseline-coverage.txt existe do PASSO 1.4):**
1. Abrir `artefatos/baseline-coverage.txt`.
2. Extrair cobertura por arquivo.
3. Atualizar tabela em `08-testes.md` § H.3:

```markdown
| Módulo | Cobertura | Meta |
|---|---|---|
| app/services/meal_service.py | XX% | 85% |
| app/services/ai/food_lookup.py | 0% | 70% |
...
```

**Achados:** módulos críticos < 50% → 🟠.

**Commit:**
```
docs(auditoria): analisa cobertura por area
```

---

### PASSO 9.3 — Áreas críticas sem teste

**Método:**
```bash
{
  echo "=== Services AI ==="
  ls /home/gabriel/projetos/CalorIA/backend/app/services/ai/*.py
  echo
  echo "=== Tests cobrindo services AI ==="
  ls /home/gabriel/projetos/CalorIA/backend/tests/unit/test_*.py
} > /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/H3-test-coverage.txt 2>&1
```

**Atualizar `08-testes.md` § H.4** com lista:
- food_lookup.py — 🟠 sem teste, é coração da precisão.
- context_builder.py — 🟠 sem teste, afeta prompts.
- insights_generator.py — 🟠 sem teste, 511 LOC.
- pattern_analyzer.py — 🟡 sem teste.
- auth_service.py — 🟡 sem teste (blacklist Redis).
- push_service.py — 🟡 sem teste (handling de 410).

**Commit:**
```
docs(auditoria): mapeia areas criticas sem teste
```

---

### PASSO 9.4 — E2E: BASE_URL e credenciais

**Método:** abrir `frontend/e2e/auth.spec.ts`, `dashboard.spec.ts`, `meals.spec.ts`. Anotar:
- `BASE_URL` defaults.
- Credenciais hardcoded (cobre PASSO 8.1).
- Setup de usuário (mockado vs real).

**Atualizar `08-testes.md` § H.6**.

**Commit:**
```
docs(auditoria): registra estado dos testes e2e
```

---

## FASE 10 — Frente I (Qualidade)

### PASSO 10.1 — Detalhar erros ruff

**Método:** abrir `artefatos/baseline-ruff.txt` (capturado no PASSO 1.1). Extrair tabela:

| Código | Arquivo:linha | Mensagem | Auto-fix? |
|---|---|---|---|
| I001 | app/api/v1/meals.py:1 | Import block unsorted | ✅ |
| B904 | app/api/v1/meals.py:101 | raise without from | ❌ |
...

**Atualizar `09-qualidade.md` § I.1**.

**Achados:** 1 entrada 🟢 agregada (14 erros ruff).

**Commit:**
```
docs(auditoria): detalha erros ruff em tabela
```

---

### PASSO 10.2 — Detalhar warnings mypy

**Método:** abrir `artefatos/baseline-mypy.txt`. Tabela similar à anterior.

**Atualizar `09-qualidade.md` § I.2**.

**Achados:** 1 entrada 🟢 agregada (N warnings mypy strict).

**Commit:**
```
docs(auditoria): detalha warnings de mypy strict
```

---

### PASSO 10.3 — ESLint frontend

**Método:** abrir `artefatos/baseline-eslint.txt`. Mesma tabela.

**Atualizar `09-qualidade.md` § I.3**.

**Commit:**
```
docs(auditoria): detalha warnings eslint
```

---

### PASSO 10.4 — Pre-commit hooks atuais

**Método:**
```bash
cat /home/gabriel/projetos/CalorIA/.pre-commit-config.yaml \
  > /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/I4-precommit.txt
```

**Atualizar `09-qualidade.md` § I.4** com lista de hooks ativos e gaps:
- ✅ ruff?
- ❌ mypy?
- ❌ eslint?
- ❌ secret scanner (gitleaks)?

**Achados:** gaps → 🟢.

**Commit:**
```
docs(auditoria): mapeia hooks de pre-commit
```

---

### PASSO 10.5 — Dead code

**Método:**
```bash
{
  echo "=== Pacotes vazios ==="
  find /home/gabriel/projetos/CalorIA/backend/app -name "__init__.py" -size 0
  echo
  echo "=== Arquivos size 0 ==="
  find /home/gabriel/projetos/CalorIA/backend /home/gabriel/projetos/CalorIA/frontend \
    -size 0 -type f \
    ! -path "*/node_modules/*" ! -path "*/.venv/*" ! -path "*/.next/*" 2>/dev/null
  echo
  echo "=== Imports nao usados (vulture, se instalado) ==="
  uvx vulture /home/gabriel/projetos/CalorIA/backend/app/ --min-confidence 70 2>&1 || echo "vulture nao instalado"
} > /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/I5-dead-code.txt 2>&1
```

**Atualizar `09-qualidade.md` § I.6**.

**Commit:**
```
docs(auditoria): inventaria dead code
```

---

### PASSO 10.6 — Dockerfiles

**Método:** ler `backend/Dockerfile`, `backend/Dockerfile.dev`, `frontend/Dockerfile`, `frontend/Dockerfile.dev`. Validar:
- Multi-stage build.
- Usuário não-root no final stage.
- HEALTHCHECK definido.
- `.dockerignore` cobre `.venv`, `node_modules`, `.next`, `__pycache__`.

**Atualizar `09-qualidade.md` § I.7**.

**Commit:**
```
docs(auditoria): analisa dockerfiles
```

---

## FASE 11 — Frente J (Observabilidade)

### PASSO 11.1 — Logging atual

**Método:**
```bash
rg -n "logger = logging\.getLogger|logging\.basicConfig" /home/gabriel/projetos/CalorIA/backend/app/ \
  | tee /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/J1-loggers.txt
```

**Atualizar `10-observabilidade.md` § J.1** com lista de loggers nomeados e formato.

**Achados:** ausência de logs estruturados (JSON) → 🟢 (recomendação).

**Commit:**
```
docs(auditoria): mapeia loggers do backend
```

---

### PASSO 11.2 — Health check completeness

**Método:** ler `backend/app/main.py:74-77` (`/health`).

Validar:
- ✅ Retorna status.
- ❌ Não verifica Postgres.
- ❌ Não verifica Redis.
- ❌ Versão hardcoded em `0.1.0` (vs `0.7.0` no CHANGELOG).

**Atualizar `10-observabilidade.md` § J.3** + achado 🟡.

**Commit:**
```
docs(auditoria): registra estado do health check
```

---

### PASSO 11.3 — Sentry / APM

**Método:**
```bash
rg -l "sentry" /home/gabriel/projetos/CalorIA/ 2>/dev/null \
  | grep -v node_modules \
  | tee /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/J3-sentry.txt
```

Esperado: vazio (Roadmap 9.3 marca como `[ ]`).

**Atualizar `10-observabilidade.md` § J.1** com plano de instrumentação.

**Achados:** 🟡 ausência (não bloqueia operação atual, mas é gap).

**Commit:**
```
docs(auditoria): registra ausencia de instrumentacao sentry
```

---

### PASSO 11.4 — Caddy

**Método:** ler `Caddyfile` e `Caddyfile.backend`. Validar:
- HTTPS automático ativo.
- Logs estruturados.
- `X-Forwarded-*` configurado.
- Rate limiting nativo do Caddy?

**Atualizar `10-observabilidade.md` § J.5**.

**Decisão pendente:** `Caddyfile.backend` + `docker-compose.backend.yml` — usuário disse "verificar e decidir depois". Documentar evidência (origem, último uso, referências) sem decidir agora.

**Commit:**
```
docs(auditoria): analisa configuracao do caddy
```

---

## FASE 12 — Frente K (DX e documentação)

### PASSO 12.1 — Coerência das versões

**Método:**
```bash
{
  echo "=== Versão pyproject.toml ==="
  grep "^version" /home/gabriel/projetos/CalorIA/backend/pyproject.toml
  echo
  echo "=== Versão app/main.py ==="
  grep "version=" /home/gabriel/projetos/CalorIA/backend/app/main.py
  echo
  echo "=== Versão CHANGELOG (mais recente) ==="
  grep "^## \[" /home/gabriel/projetos/CalorIA/CHANGELOG.md | head -3
  echo
  echo "=== Versão package.json frontend ==="
  grep '"version"' /home/gabriel/projetos/CalorIA/frontend/package.json
} > /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/K1-versions.txt 2>&1
```

**Atualizar `11-dx-docs.md` § K.4** com tabela mostrando dessincronia.

**Achados:** 🟢 (cosmético).

**Commit:**
```
docs(auditoria): registra dessincronia de versoes
```

---

### PASSO 12.2 — ADR pendente: ADR-006 sobre escolha do Groq

**Método:** confirmar que `docs/architecture.md` tem ADR-002 reescrito (após migração) mas não há ADR-006 documentando decisão histórica.

**Atualizar `11-dx-docs.md` § K.1** registrando proposta de criar `docs/adrs/006-groq-vs-alternativas.md` na fase de correção.

**Commit:**
```
docs(auditoria): registra adr-006 pendente
```

---

### PASSO 12.3 — Runbook operacional ausente

**Método:** verificar se há `docs/runbook-prod.md` ou similar.

```bash
ls /home/gabriel/projetos/CalorIA/docs/ \
  | tee /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/K3-docs-list.txt
```

**Atualizar `11-dx-docs.md` § K.1** registrando proposta:
- Procedimento quando GROQ_API_KEY estoura free tier.
- Procedimento quando push expira em massa (HTTP 410 em > 50% das subs).
- Procedimento quando worker celery trava.
- Procedimento de restauração de backup do Postgres.

**Commit:**
```
docs(auditoria): registra runbook operacional pendente
```

---

### PASSO 12.4 — CONTRIBUTING e templates

**Método:**
```bash
{
  echo "=== CONTRIBUTING.md ==="
  wc -l /home/gabriel/projetos/CalorIA/CONTRIBUTING.md
  echo
  echo "=== Templates GitHub ==="
  ls /home/gabriel/projetos/CalorIA/.github/ISSUE_TEMPLATE/ 2>/dev/null || echo "ausente"
  ls /home/gabriel/projetos/CalorIA/.github/PULL_REQUEST_TEMPLATE.md 2>/dev/null || echo "ausente"
} > /home/gabriel/projetos/CalorIA/docs/auditoria/artefatos/K4-contrib.txt 2>&1
```

**Atualizar `11-dx-docs.md` § K.3**.

**Commit:**
```
docs(auditoria): mapeia contributing e templates
```

---

## FASE 13 — Consolidação

### PASSO 13.1 — Reorganizar achados.md por severidade

**Método:** abrir `achados.md`, ordenar entradas por severidade (🔴 → 🟠 → 🟡 → 🟢) e dentro de cada severidade por frente. Atualizar contadores no topo:

```markdown
**Status totais:** críticos: N · altos: N · médios: N · baixos: N
```

**Commit:**
```
docs(auditoria): reordena achados por severidade
```

---

### PASSO 13.2 — Escrever relatório preliminar

**Método:** preencher `relatorio-preliminar.md` com seções:

```markdown
# Relatório Preliminar da Auditoria

## Visão geral
- Total de achados: N (🔴 N · 🟠 N · 🟡 N · 🟢 N)
- Frentes mais afetadas: ...
- Priorização recomendada para correção: ...

## Métricas baseline
(copiar tabela do log.md § Snapshot inicial)

## Top 10 achados de maior impacto
1. AUD-XXX (🔴) — descrição em 1 linha
2. ...

## Recomendação de cronograma para correção
(adaptar do plano § 14, ajustando esforço estimado conforme achados reais)

## Referências
- plano.md
- runbook.md
- 01-arquitetura.md ... 11-dx-docs.md
- artefatos/*
```

**Commit:**
```
docs(auditoria): escreve relatorio preliminar
```

---

### PASSO 13.3 — Atualizar CHANGELOG e README

**Método:**

1. Em `CHANGELOG.md`, sob `## [Não lançado]`, adicionar:
```markdown
### Documentação

- **Auditoria de arquitetura, qualidade e segurança** — documentação completa em `docs/auditoria/`. Identifica N achados (🔴 N · 🟠 N · 🟡 N · 🟢 N) com plano de correção em PRs separados.
```

2. Em `README.md`, adicionar à seção de documentação um link:
```markdown
- [`docs/auditoria/relatorio-preliminar.md`](docs/auditoria/relatorio-preliminar.md) — relatório de auditoria
```

**Commit:**
```
docs(auditoria): registra auditoria no changelog e readme
```

---

### PASSO 13.4 — Encerramento e handoff

**Método:** adicionar seção final em `log.md`:

```markdown
## § Encerramento

- **Início da auditoria:** YYYY-MM-DD HH:MM
- **Fim da auditoria:** YYYY-MM-DD HH:MM
- **Total de passos executados:** N
- **Total de commits:** N
- **Total de achados registrados:** N
- **Próximos passos:** ver `relatorio-preliminar.md` § Recomendação de cronograma.
```

**Commit:**
```
docs(auditoria): encerra execucao e registra handoff
```

---

## Apêndice A — Catálogo de comandos

Comandos utilitários que aparecem ao longo do runbook, agregados para referência rápida.

```bash
# Ruff (cache writable)
RUFF_CACHE_DIR=/tmp/ruff-$$ uvx ruff check .

# Mypy strict
.venv/bin/python -m mypy --strict app/

# Pytest com cobertura
.venv/bin/pytest --cov=app --cov-report=term --cov-report=xml -q

# Radon
uvx radon cc app/ -s -nc -a
uvx radon mi app/ -s

# Pip audit
uvx pip-audit .

# NPM audit
npm audit --json
npm audit

# ESLint
npm run lint

# TSC noEmit
npx tsc --noEmit

# Postgres
docker exec caloria_postgres psql -U caloria -d caloria_db -c "<sql>"

# Ripgrep
rg -n "<padrão>" <caminho>
```

## Apêndice B — Checklist final de Definition of Done

- [ ] Todos os passos do runbook foram executados (FASE 0 → FASE 13).
- [ ] Cada passo tem entrada em `log.md`.
- [ ] Cada passo tem 1 commit semântico (em PT-BR, sem mencionar IA).
- [ ] `achados.md` contém todos os AUD-NNN encontrados, ordenados.
- [ ] `relatorio-preliminar.md` está preenchido.
- [ ] CHANGELOG e README citam a auditoria.
- [ ] `git status` está limpo.
- [ ] Branch da auditoria pode ser pusheada (`git push origin dev`).

## Apêndice C — Como retomar uma execução interrompida

Se a auditoria for interrompida (sessão fechada, erro, etc.):

1. `git log --oneline -10` para ver o último passo commitado.
2. Abrir `docs/auditoria/log.md` e localizar a última entrada.
3. Identificar o próximo PASSO no runbook.
4. Continuar a partir dele — todos os passos são idempotentes (re-executar não corrompe estado).

---
data: 2026-07-03
titulo: Zera baseline de lint/mypy para o gate ficar verde
status: ativa
tags: [quality, lint, mypy, ai, scripts]
---

# Decisão — baseline de qualidade (ruff + mypy)

Registra as escolhas não-triviais ao zerar o baseline pré-existente que deixava
`make check`/`lint-check` vermelho (14 erros `ruff check`, 11 arquivos com drift
de `ruff format`, 6 erros `mypy app/` em `ai_client.py`), documentado no
`manifest.md`. Objetivo: `ruff check .`, `ruff format --check .` e `mypy app/`
limpos, sem mudança de comportamento em runtime.

## Divergência do relato (escopo real)
O ledger dizia "concentrados em `scripts/`", mas 3 dos 14 erros estavam em
**código de produção** (`app/api/v1/meals.py` I001+B904, `app/services/meal_service.py`
N818) e um erro em script era **bug latente real** (F821), não cosmético.

## Decisões

- **F821 `sa_text` (bug real, não lint cosmético).** Em
  `scripts/import_off_local.py`, `from sqlalchemy import text as sa_text` estava
  importado no escopo de outra função, mas quem usava `sa_text` era `_flush` —
  `NameError` garantido em runtime se `_flush` fosse chamada. **Escolhido** mover o
  import para dentro de `_flush` (seguindo o padrão de imports locais do próprio
  script), o que resolve F821 (undefined) e F401 (unused) juntos.

- **N818 rename `MealItemNotFound` → `MealItemNotFoundError`.** Exceção **interna**
  (não é contrato de API/schema/config), com 5 usos em `meal_service.py` +
  `api/v1/meals.py`, todos atualizados. Não é mudança quebradora pela definição da
  constitution. Adicionado `raise ... from None` (B904) no `except` do router.

- **N806 em script — divergência consciente do idiom.** A variável local
  `AsyncSessionLocal` (sessionmaker) em `scripts/import_fatsecret.py` foi renomeada
  para `async_session` (snake_case) para satisfazer N806. Diverge do idiom
  module-level `AsyncSessionLocal` usado na app (`core/database.py`), mas: (a) é
  local de um script utilitário, não a factory global; (b) N806 só dispara em
  escopo de função. Preferido renomear a poluir com `# noqa`.

- **mypy `ai_client.py` — tipagem sem tocar runtime (área de alto risco).** Os 6
  erros são de tipos, não de lógica; a área `services/ai/` é de alto risco, então
  as mudanças são **estritamente de anotação** (zero alteração de comportamento,
  confirmado por testes verdes):
  - `messages` anotado `list[dict[str, Any]]` + `cast("list[ChatCompletionMessageParam]", …)`
    ao chamar `chat.completions.create` (o dict literal conforma ao param do SDK;
    `cast` é honesto e não roda em runtime). Import do tipo sob `TYPE_CHECKING`
    para não custar import no hot path da IA.
  - `redis.asyncio.from_url` é **untyped na lib** → `# type: ignore[no-untyped-call]`
    (código de erro específico) nos 2 pontos; retorno de `r.get` embrulhado em
    `cast("str | None", …)`. Divergência da preferência "não silenciar": aceitável
    por ser lacuna de stub de terceiros, com ignore **codificado** (não amplo).

- **`ruff format` repo-wide (churn cosmético > escopo do lint).** `ruff format .`
  reformatou 11 arquivos com drift **pré-existente** (`enrich_foods.py`,
  `import_off.py`, `smoke_test.py`, `test_ai_conversations.py`, etc.), além dos que
  tinham erro de lint. É mudança **só de formatação** (o formatter nunca altera
  lógica) e **exigida** pela meta explícita `ruff format --check .` limpo — não
  refatoração lateral por conta própria. Registrado aqui conforme a regra
  code-quality ("cosmético em código adjacente exige decision").

## Débito aberto
Não há gate de CI ativo aplicando isso (CI/CD desabilitado); o baseline pode
voltar a divergir até a esteira ser reativada. O `manifest.md` ainda cita o
baseline antigo (14 ruff / 6 mypy) — atualizar na próxima passada de `/discover`.

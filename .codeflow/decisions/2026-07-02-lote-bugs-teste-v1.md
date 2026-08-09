---
data: 2026-07-02
titulo: Correções do lote de QA bugs-teste-v1
status: ativa
tags: [schema, ai, enum, frontend, logs, notifications]
lote: bugs-teste-v1
---

# Decisão consolidada — lote bugs-teste-v1

Registra as escolhas não-triviais tomadas ao corrigir o lote de QA manual
(`bugs-teste-v1.txt`). Uma linha por bug que motivou decisão. Ledger:
`.codeflow/bug-batches/bugs-teste-v1.md`.

## Decisões por bug

- **B10 — enum `notificationtype` (divergência consciente da convenção).**
  O enum PG `notificationtype` foi criado com labels **minúsculos** (`reminder`,
  …) e nunca renomeado, enquanto todos os outros enums do banco foram
  padronizados em **MAIÚSCULO** pela migração `b2c3d4e5f6a1` (`corrige_case_enums`),
  casando com o nome do membro + mapeamento default do SQLAlchemy. Havia duas
  saídas: (a) `values_callable` na coluna para o SQLAlchemy persistir os *values*
  minúsculos; (b) migração renomeando os labels para MAIÚSCULO (alinhando à
  convenção do projeto). **Escolhida (a)** — `SAEnum(NotificationType,
  values_callable=…)` em `app/models/notification.py:32`. Motivo: é a única opção
  verificável localmente (teste unitário sem DB, `tests/unit/test_notification_enum.py`)
  e evita uma migração de dados não-executável neste ambiente (sem Postgres).
  **Débito aberto:** `notificationtype` passa a ser a única coluna enum com
  `values_callable`, divergindo da convenção uniforme das demais. Alternativa de
  consolidação futura: renomear os labels no banco e remover `values_callable`.
  O contrato JSON (responses em minúsculo) é preservado em ambas as opções.

- **B7/B9 — upsert de peso/humor por dia + constraint UNIQUE (mudança de
  comportamento + schema).** `WeightService.create`/`MoodService.create` passam a
  fazer **upsert** por `(user_id, date)` em vez de sempre inserir
  (`app/services/log_service.py`). Isso altera a semântica do `POST /weight` e
  `POST /mood`: um segundo registro no mesmo dia agora **sobrescreve** em vez de
  duplicar (contrato de response inalterado). Adicionadas constraints
  `UNIQUE(user_id, date)` nos modelos + migração `a7b8c9d0e1f2` que **deduplica**
  os registros existentes (mantém o mais recente) antes de criar a constraint.
  A migração **não pôde ser executada localmente** (sem Postgres) — precisa rodar
  em ambiente com DB antes do deploy. A confirmação de sobrescrita no frontend
  (modal de aviso pedido no relato) fica como melhoria de UX **deferida** — o
  defeito de dados/gráfico é resolvido pelo upsert.

- **B17 — `suggest-meal` determinístico.** Causa: `use_cache=True` + prompt fixo
  ⇒ mesma resposta cacheada. Fix: `use_cache=False` + diretriz de variação
  aleatória no prompt (`app/services/ai/insights_generator.py`). Sem teste
  automatizado (não-determinismo de LLM) — gate de repro manual.

- **B18 — markdown cru.** Escolhido **renderizador mínimo sem dependência**
  (`components/MarkdownLite.tsx`) em vez de instalar `react-markdown`. Motivo:
  evitar adicionar dependência de rede num ambiente offline e manter o diff
  contido; cobre o subconjunto que a IA de fato emite (negrito, títulos, listas).

- **B5/B14 — helpers extraídos.** Lógica de mensagem de erro (`lib/aiErrors.ts`)
  e de meta de peso por objetivo (`lib/weightGoal.ts`) extraídas como funções
  puras testáveis (regra code-quality: reuso em 2 telas / lógica de negócio
  isolada). Cobertas por Jest.

## Bugs bloqueados (fora do escopo de bugfix → `/create-spec`)
B8 (editar/remover hidratação), B11 (age→birth_date, breaking schema), B12
(exibir TMB/TDEE; causa-raiz do tdee null documentada no ledger), B15
(recuperação de senha), B16 (persistência de insights), B20 (histórico de chat).

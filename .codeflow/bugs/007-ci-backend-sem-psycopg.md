---
versão: 1.0
id: "007"
slug: 007-ci-backend-sem-psycopg
título: "CI do backend vermelho: SQLAlchemy 2.1 resolve `postgresql://` para psycopg 3, que não está instalado"
severidade: alto
área: backend/scripts + ci
status: aberto
criado: 2026-10-02
atualizado: 2026-10-02
reportado_por: CI do push na dev (cbfd1c7) e do PR #38
---

# BUG 007 — CI do backend quebra na coleta do `test_seed_demo.py`

O job "Backend — lint e testes" falha na **coleta** da suíte, antes de rodar qualquer
teste, tanto no push na `dev` em `cbfd1c7` (run 37072143510) quanto no PR #38
(run 37075432437). O commit `cbfd1c7` só mexe em `.md`: o código não mudou, mudou o
ambiente.

## Sintoma medido

```text
ERROR collecting tests/unit/test_seed_demo.py
sqlalchemy/dialects/postgresql/psycopg.py:497: in import_dbapi
    import psycopg
E   ModuleNotFoundError: No module named 'psycopg'
```

## Reprodução

No venv da worktree (`sqlalchemy 2.1.2`, `psycopg2-binary 2.9.13`, sem `psycopg`):

```bash
backend/.venv/bin/python -c "from sqlalchemy import create_engine; create_engine('postgresql://u:p@h/db')"
# ModuleNotFoundError: No module named 'psycopg'
```

## Causa (hipótese inicial, a confirmar no /bugfix)

`backend/scripts/seed_dev_user.py:36-45` cria a engine síncrona no import do módulo
com uma URL sem driver (`postgresql://`). Até o SQLAlchemy 2.0 isso resolvia para
`psycopg2`, o driver que o extra `dev` do `pyproject.toml` instala. O SQLAlchemy 2.1
passou o driver padrão do PostgreSQL para o **psycopg 3**, e o `pyproject.toml`
aceita qualquer versão (`sqlalchemy[asyncio]>=2.0.0`): o CI instalou a 2.1.2.
`tests/unit/test_seed_demo.py` importa o script, e a coleta morre.

Relacionado: o BUG 005 (o mesmo script, o driver síncrono só no extra `dev`).

---
data: 2026-08-02
titulo: Schema dos testes de integração passa a vir das migrations
status: ativa
tags: [testes, alembic, ci, nfr-6, spec-002]
---

# Schema dos testes de integração passa a vir das migrations

## Contexto

`tests/conftest.py` montava o schema de teste com
`Base.metadata.create_all()`. Isso cria **só as tabelas do metadata**. Tudo que
uma migration acrescenta além disso ficava de fora:

- extensões `pg_trgm` e `unaccent`;
- a função `caloria_unaccent`;
- os índices GIN de trigrama.

Consequência medida em 2026-08-02: os cinco testes de
`tests/integration/test_golden_set.py` **pulavam sempre**, inclusive no CI, com
`fonte curada 'taco' com apenas 0 linhas`. E quando o banco era semeado, eles
passavam a **falhar** com `function caloria_unaccent(text) does not exist`.

O efeito prático é que a **NFR-6 da spec 002** ("os limiares de
`test_golden_set.py` não regridem") estava declarada e **não verificada**. Um
gate que só pula não é gate.

## Decisão

`_reset_schema()` passa a:

1. `DROP SCHEMA public CASCADE` + `CREATE SCHEMA public` — em vez de
   `Base.metadata.drop_all()`, que deixa para trás os tipos `ENUM` e a função,
   fazendo o `CREATE TYPE`/`CREATE FUNCTION` da migration falhar na segunda
   execução;
2. `alembic upgrade head` numa thread (o Alembic é síncrono e abre a própria
   conexão; o event loop de sessão não pode ser bloqueado).

Como `alembic/env.py:21` **sobrescreve** `sqlalchemy.url` com
`settings.DATABASE_URL`, passar a URL pelo `Config` não basta: o helper aponta
`settings.DATABASE_URL` para o banco de teste durante o upgrade e restaura
depois.

## Justificativa

O schema de teste passa a ser **o mesmo de produção**. Além de destravar a
NFR-6, isso faz uma migration quebrada falhar na suíte em vez de no deploy — que
é onde ela custa caro.

## Consequências

- Custo: a sessão de integração passa a aplicar 15 migrations no setup.
- `tests/unit/conftest.py` continua sobrepondo a fixture, então a suíte unitária
  segue rodando **sem banco nenhum** e sem custo adicional (a garantia da fase
  B.1 permanece).
- O `import Base` de `tests/conftest.py` continua sendo usado pelos modelos, mas
  `drop_all`/`create_all` não são mais chamados.
- Abre caminho para semear o banco nutricional na sessão de teste e finalmente
  ligar o gate da NFR-6 — passo que **não** faz parte desta decisão.

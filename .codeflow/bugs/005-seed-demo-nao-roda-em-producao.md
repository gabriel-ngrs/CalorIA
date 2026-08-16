---
versão: 1.0
id: "005"
slug: 005-seed-demo-nao-roda-em-producao
título: "Seed da conta de demonstração não roda na imagem de produção (psycopg2 só no extra dev)"
severidade: alto
área: backend/scripts + infra
status: aberto
criado: 2026-08-16
atualizado: 2026-08-16
reportado_por: primeiro deploy real do servidor (2026-08-16)
---

# BUG 005 — Seed da conta demo não roda em produção

`backend/scripts/seed_dev_user.py --conta demo` **falha na imagem de produção** com
`ModuleNotFoundError: No module named 'psycopg2'`. É o script que cria e popula a
conta de demonstração da Fase E.3 — a mesma cujas credenciais o README publica.

## Sintoma medido

```text
File "/app/scripts/seed_dev_user.py", line 45, in <module>
    engine = create_engine(DATABASE_URL, echo=False)
  ...
    import psycopg2
ModuleNotFoundError: No module named 'psycopg2'
```

## Causa

O script converte a URL assíncrona em síncrona e usa `create_engine`:

```python
DATABASE_URL = os.getenv("DATABASE_URL", "...")
    .replace("postgresql+asyncpg://", "postgresql://")
    .replace("+asyncpg", "")

engine = create_engine(DATABASE_URL, echo=False)   # seed_dev_user.py:36-45
```

Isso exige um driver **síncrono**. E `psycopg2-binary` está declarado **apenas no
extra `dev`** do `backend/pyproject.toml:45-57` — a imagem de produção instala só as
dependências principais, que são 100% `asyncpg`.

O comentário no próprio `pyproject.toml` documenta a dependência pensando em
`make seed-user` e `docs/setup.md`, ambos cenários de **desenvolvimento**. O caso de
produção — a conta demo da E.3, publicada no README — não foi considerado.

| Arquivo | Linhas | O quê |
|---|---|---|
| `backend/pyproject.toml` | 45-57 | `psycopg2-binary` no extra `dev`, ausente do runtime |
| `backend/scripts/seed_dev_user.py` | 36-45 | engine síncrona exigindo psycopg2 |

Agravante: o container roda como usuário sem privilégio, então nem o contorno
`pip install psycopg2-binary` funciona sem `-u root`.

## Contorno aplicado no primeiro deploy (temporário)

```bash
docker compose exec -T -u root backend pip install --no-cache-dir psycopg2-binary
docker compose exec -T backend python scripts/seed_dev_user.py --conta demo
```

Funciona, mas **é perdido a cada rebuild da imagem** — ou seja, a cada deploy do CD.
Não é correção.

## Correções possíveis

1. **Mover `psycopg2-binary` para as dependências principais.** Mínimo e imediato;
   custa alguns MB na imagem e contraria levemente a nota do `pyproject.toml` de que
   o runtime é 100% asyncpg — o driver entraria só para scripts, não para a app.
2. **Reescrever o script em SQLAlchemy async**, alinhando-o ao resto do projeto.
   Mais correto arquiteturalmente, mudança maior.

A escolha é do owner; as duas fecham o defeito.

## Impacto

Enquanto não for corrigido, a conta de demonstração só existe porque foi semeada à
mão com o contorno acima. Um `docker compose build` (que é o que o CD faz a cada
merge em `main`) devolve a imagem ao estado sem psycopg2, e qualquer reset periódico
da demo — previsto no passo 2 da Fase E.3 — falha.

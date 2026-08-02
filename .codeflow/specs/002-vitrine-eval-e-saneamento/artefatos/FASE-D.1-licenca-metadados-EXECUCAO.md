---
spec: 002-vitrine-eval-e-saneamento
fase: D.1
slug_fase: licenca-metadados
status: executado
tentativa: 1
reprovacoes: 0
sha_inicial: 7f9f59a
sha_final: d7346ab
range: 7f9f59a..d7346ab
---

# FASE D.1 — Relatório de execução

## 1. Resumo do que foi feito

`LICENSE` MIT adicionada, README corrigido, e a versão sincronizada nos quatro
arquivos. O passo 3 (description, topics e homepage no GitHub) é **ação do
owner** e continua pendente — medido e registrado em §6.

## 2. Arquivos CRIADOS

`LICENSE` — MIT, copyright 2026 Gabriel Negreiros Saraiva.

## 3. Arquivos ALTERADOS

| Arquivo | O que mudou |
|---------|-------------|
| `README.md` | "Projeto pessoal. Todos os direitos reservados." → `[MIT](LICENSE) — uso livre, com atribuição.` |
| `backend/pyproject.toml` | `0.1.0` → `0.7.0`. |
| `backend/app/main.py` | Constante `APP_VERSION = "0.7.0"`, usada no `FastAPI(version=...)` e no `/health`. |
| `frontend/package.json` | `0.1.0` → `0.7.0`. |
| `CHANGELOG.md` | Entrada em "Não lançado" registrando licença e sincronização. |

## 4. Confirmação do REUSO e decisões de design

**Decisões de design:**
- **`APP_VERSION` como constante única no backend.** A versão aparecia duas
  vezes literalmente em `main.py` (no `FastAPI(...)` e no `/health`); com duas
  cópias, sincronizar de novo já nasceria propenso a divergir.
- **`0.7.0` como alvo**, não `0.1.0` nem uma versão nova: é a última versão
  lançada no CHANGELOG, e o restante estava atrasado em relação a ela. Subir para
  `0.8.0` seria declarar um release que esta fase não faz.
- **O histórico do CHANGELOG não foi alterado** — só a seção "Não lançado"
  recebeu uma entrada, como o escopo travado exige.
- **Licença MIT**, conforme OQ4 resolvida. Nenhuma outra foi considerada.

## 5. Comandos rodados + saídas reais

```text
$ grep -n '"version"' frontend/package.json
3:  "version": "0.7.0",
$ grep -n '^version' backend/pyproject.toml
7:version = "0.7.0"
$ python -c "from app.main import APP_VERSION; print(APP_VERSION)"
0.7.0
$ grep -n "^## \[" CHANGELOG.md | head -2
10:## [Não lançado]
44:## [0.7.0] - 2026-05-10

$ ruff check . && ruff format --check . && mypy app/ evals/
All checks passed! / 135 files already formatted / Success: no issues found

$ tail -3 README.md
## Licença

[MIT](LICENSE) — uso livre, com atribuição.
```

**Estado do repositório no GitHub, medido nesta sessão:**

```text
$ gh repo view gabriel-ngrs/CalorIA --json visibility,description,homepageUrl,repositoryTopics,licenseInfo
{"description":"","homepageUrl":"","licenseInfo":null,"repositoryTopics":null,"visibility":"PRIVATE"}
```

## 6. Checklist dos ACs / critério de conclusão

- [x] **A versão é a mesma nos quatro arquivos** — CHANGELOG `0.7.0`,
      `pyproject.toml` `0.7.0`, `main.py` `APP_VERSION = "0.7.0"`,
      `package.json` `0.7.0`.
- [x] **LICENSE MIT presente** e a linha final do README ajustada.
- [ ] **AC-18, a API do GitHub reporta licença detectada, description e topics
      não vazios** — **PENDENTE**. `licenseInfo` continua `null`, `description` e
      `homepageUrl` vazios, `repositoryTopics` `null`. A licença só é detectada
      depois que o commit chega ao remoto; description, topics e homepage são
      **ação do owner** (passo 3 da fase), não executável por código.
- [x] **`make check` verde** — no que roda nesta máquina: `ruff`, `ruff format`,
      `mypy app/ evals/`, `pytest` completo e `npm test`. Os alvos do Makefile
      passam por `docker compose exec` e não rodam aqui (sem Docker).

## 7. Dúvidas para o avaliador

1. O AC-18 depende de três ações do owner no GitHub (description, topics,
   homepage) **e** de o commit ter sido promovido — o repositório está privado e
   `main` está 192 commits atrás de `dev`. A fase pode ser aprovada com a parte
   de código completa e o AC-18 pendente até D.2?
2. `homepage` deveria apontar para a URL da Vercel (`frontend-nine-mu-59.vercel.app`,
   viva — ver E.1) ou esperar o domínio da E.2?

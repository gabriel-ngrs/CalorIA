---
spec: 002-vitrine-eval-e-saneamento
fase: D.1
slug_fase: licenca-metadados
status: rework
tentativa: 2
reprovacoes: 1
sha_inicial: 7f9f59a
sha_final: 2e6cd1d1d2a7c060d34fda9137c7aa0b25e52a6f
range: 7f9f59a..2e6cd1d1d2a7c060d34fda9137c7aa0b25e52a6f
---

# FASE D.1 — Relatório de execução

## Nota de 2026-08-03 — o item restante passou a ser represado por decisão, não por pendência

*Não é rework: nenhum trabalho novo foi feito nesta fase, e `status`, `tentativa` e
`reprovacoes` ficam como estavam.*

A metade aberta do AC-18 é `licenseInfo: null`, que depende de a `main` avançar. Até
hoje isso era "esperar a D.2 rodar". **O owner decidiu em 2026-08-03 que a `main` não
será tocada em momento nenhum antes do fim da spec** (OQ15), então a D.2 passa a ser a
última operação de branch do projeto.

Consequência para esta fase, declarada para que ninguém a leia como defeito: **a D.1
não fecha até lá**, e uma avaliação antes da D.2 deve manter RESSALVAS por esse item —
com causa conhecida e aceita. As duas cláusulas acionáveis do AC-18 (description e
topics) seguem cumpridas e verificadas na §"Tentativa 2" acima; o `LICENSE` está
commitado e correto na `dev`. Não há trabalho pendente nesta fase — há espera.

Ver `.codeflow/decisions/2026-08-03-promocao-da-main-fica-para-o-fim-da-spec.md`.


## Tentativa 2 — o que mudou

Veredito da tentativa 1: **RESSALVAS**, score 9.4. Um achado IMPORTANTE, fechado na
metade que é acionável hoje.

### D1-IMP-1 — AC-18: description, topics e licença detectada

**Aceito.** A avaliação separa corretamente as duas causas, que têm ações diferentes.

**Metade 1 — description e topics: FEITO.** O owner autorizou em 2026-08-03, e o
comando foi executado nesta sessão:

```text
$ gh repo edit gabriel-ngrs/CalorIA \
    --description "Diário alimentar com IA: eval do pipeline de LLM versionado junto do código" \
    --add-topic fastapi --add-topic nextjs --add-topic llm-eval \
    --add-topic groq --add-topic postgresql --add-topic python

$ gh repo view --json description,homepageUrl,repositoryTopics,licenseInfo,visibility
{"description":"Diário alimentar com IA: eval do pipeline de LLM versionado junto do código",
 "homepageUrl":"",
 "repositoryTopics":[{"name":"fastapi"},{"name":"groq"},{"name":"llm-eval"},
                     {"name":"nextjs"},{"name":"postgresql"},{"name":"python"}],
 "licenseInfo":null,
 "visibility":"PRIVATE"}
```

**Metade 2 — `licenseInfo: null`: depende da D.2.** O `LICENSE` está commitado na
`dev`; o GitHub detecta licença a partir do **branch default**, que é `main`, e `main`
está atrás. Isso se resolve com a promoção da D.2, não com trabalho novo — e o portão
que a decision da A.1 mantinha sobre a D.2 foi levantado em 2026-08-03 (OQ13), então
não há mais nada segurando essa fase.

**`homepageUrl` ficou vazio de propósito.** O AC-18 não o exige, e o único endereço
disponível hoje é o frontend na Vercel, cujo backend está comprovadamente fora do ar
(medido na A.1 tentativa 3 e na E.1). Anunciar como homepage uma demo que abre a tela
de login e não autentica é pior que não anunciar. Entra quando a demo existir de fato
(E.3 + E.4).

### Consequência honesta

O gate da fase é "AC-18 satisfeito", e AC-18 exige as três coisas. Duas estão
cumpridas e verificadas acima; a terceira depende da D.2. Uma reavaliação agora deve
manter RESSALVAS por esse item, a menos que a D.2 saia antes.

A avaliação sugere, alternativamente, mover a verificação do AC-18 para o gate da D.2 —
o owner optou por manter o AC como está e deixar a D.1 fechar quando a `main` for
promovida.

### Evidência dos itens já verificados

```text
$ ... pytest --cov=app -q     → 620 passed, 1 skipped, 73.86% (piso 72%)
$ ... ruff check . && ruff format --check . && mypy app/ evals/  → limpos
$ cd frontend && npx tsc --noEmit   → EXIT=0
$ cd frontend && npm test           → 20 suites, 118 passed
```

A versão `0.7.0` segue igual nos quatro arquivos; nada nesta tentativa a tocou.


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

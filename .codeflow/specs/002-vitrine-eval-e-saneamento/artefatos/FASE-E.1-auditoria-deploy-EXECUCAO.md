---
spec: 002-vitrine-eval-e-saneamento
fase: E.1
slug_fase: auditoria-deploy
status: executado
tentativa: 1
reprovacoes: 0
sha_inicial: b31604d
sha_final: b31604d
range: b31604d..b31604d
---

# FASE E.1 — Relatório de execução

Fase de levantamento: **nada em produção foi alterado**, e o único artefato é
este relatório. `sha_inicial == sha_final` porque não há commit de código.

## 1. Resumo do que foi feito

Estado real de frontend e backend medido por requisição, e o estado do
repositório medido pela API do GitHub. **A conclusão principal contradiz a
documentação: o backend não está no ar.**

## 2. Estado verificado — frontend

**No ar, funcionando.**

```text
$ curl -sL -o /dev/null -w "final=%{url_effective} status=%{http_code}\n" \
       https://frontend-nine-mu-59.vercel.app/
final=https://frontend-nine-mu-59.vercel.app/login?callbackUrl=%2F status=200

$ curl -sI https://frontend-nine-mu-59.vercel.app/login | head -12
HTTP/2 200
server: Vercel
strict-transport-security: max-age=63072000; includeSubDomains; preload
age: 1128889
date: Sun, 02 Aug 2026 19:06:35 GMT
vary: RSC, Next-Router-State-Tree, Next-Router-Prefetch
```

Leitura: a raiz redireciona (307) para `/login` — middleware de auth ativo —, e
`/login` responde 200 servido pela Vercel com HSTS. O `age: 1128889` (≈ 13 dias
de cache de borda) indica **build antigo**, coerente com `origin/main` parado.

## 3. Estado verificado — backend

**Fora do ar. O host documentado nem sequer resolve em DNS.**

```text
$ getent hosts caloria-gabriel.duckdns.org
  (sem saída — não resolve)

$ curl -m 15 https://caloria-gabriel.duckdns.org/health   → status=000
$ curl -m 15 http://caloria-gabriel.duckdns.org/health    → status=000
```

`caloria-gabriel.duckdns.org` é o host declarado em `docs/deploy.md:193` e
`docs/deploy-checklist.md:111` como `NEXT_PUBLIC_API_URL`. Como o DNS não
resolve, **não existe backend respondendo nesse endereço**, e portanto:

- `/health` não responde;
- não há como afirmar que as migrations estão aplicadas;
- **o frontend em produção não tem API atrás dele.** A tela de login abre, mas
  qualquer requisição autenticada falha.

Isso confirma e agrava a premissa do owner: o estado do backend não era
"indeterminado", era **inexistente**.

## 4. Estado verificado — repositório

```text
$ gh repo view gabriel-ngrs/CalorIA --json visibility,description,homepageUrl,repositoryTopics,licenseInfo,defaultBranchRef,pushedAt
{"defaultBranchRef":{"name":"main"},"description":"","homepageUrl":"",
 "licenseInfo":null,"repositoryTopics":null,"visibility":"PRIVATE",
 "pushedAt":"2026-08-02T16:48:44Z"}

$ gh workflow list
CD — Deploy em Produção   active
CI                        active
Dependabot Updates        active

$ gh run list --limit 3
success  docs(specs): aplica rework...          CI  dev  push  2m29s  2026-08-02T16:48:46Z
success  test(backend): declara pre-condicoes.. CI  dev  push  2m35s  2026-08-02T14:23:27Z
failure  ci(seguranca): isenta valores...       CI  dev  push  2m32s  2026-08-02T14:12:57Z

$ git rev-list --count origin/main..origin/dev
192
$ git log -1 --format="%h %ad %s" --date=short origin/main
2ff130c 2026-04-29 chore(release): merge dev → main — Space Grotesk global [...]
```

Leitura: repositório **privado** (desde A.1); sem description, topics, homepage
ou licença detectada; CI e CD **ativos** (B.2), com as duas últimas execuções de
CI **verdes**; `main` parado em 2026-04-29 e **192 commits atrás** de `dev`.

## 5. Divergências entre a documentação e a realidade

| # | O que o documento afirma | O que foi medido |
|---|---|---|
| 1 | `docs/deploy.md` descreve um deploy full-stack self-hosted em `caloria-gabriel.duckdns.org` | O host **não resolve**; não há backend no ar |
| 2 | `docs/deploy.md` não menciona a Vercel | O frontend **está** na Vercel, e é o único componente vivo |
| 3 | A URL de produção do frontend não aparece em documento nenhum | `https://frontend-nine-mu-59.vercel.app` |
| 4 | Roadmap 9.2 marca todos os itens de deploy como pendentes | Correto quanto ao backend; **incorreto** quanto ao frontend |
| 5 | `docker-compose.backend.yml` + `Caddyfile.backend` seriam "o par que roda em produção" (§1 da spec) | Nada roda; o par descreve uma intenção, não um estado |
| 6 | README exibia badge de CI | Agora correto — CI ativo e verde (B.2) |
| 7 | `Caddyfile.backend` faz proxy só de `/api/*`, `/docs*`, `/redoc*`, `/openapi.json`, `/health` | Consistente com frontend separado na Vercel — a topologia **de fato pretendida** é split, não full-stack |

| 8 | `make seed` → `scripts/seed_all.py` é o caminho documentado de popular o banco | **Quebrado**: `ImportError: cannot import name 'ReminderChannel' from 'app.models.reminder'` — sobra da remoção dos bots na v0.7.0. `seed_taco.py` e `seed_portions.py` funcionam |

**Achado de método:** a divergência 7 mostra que a topologia real pretendida
(frontend na Vercel + backend self-hosted atrás do Caddy) já está codificada nos
arquivos de orquestração, mas **só na documentação errada**. A E.2 tem material
suficiente para decidir sem inventar.

## 6. Checklist dos ACs / critério de conclusão

- [x] **AC-24, relatório com evidência verificável para cada afirmação** — cada
      afirmação de §2 a §4 traz o comando e a saída que a sustenta.
- [x] **Nada alterado em produção** — só requisições `GET`/`HEAD` e leituras da
      API do GitHub.
- [x] **Nenhum segredo exposto** — nenhuma variável de ambiente de produção,
      token ou credencial aparece neste relatório.
- [x] **`docs/deploy.md` não foi presumido verdadeiro** — foi usado como
      hipótese e **refutado** pela medição.

## 7. Dúvidas para o avaliador

1. O backend **não existe** em produção. Isso reordena o Track E: a E.4 deixa de
   ser "refazer o deploy" e passa a ser "fazer o primeiro deploy real". Vale
   ajustar o texto da E.4 na spec?
2. A conta de demonstração (E.3) depende do backend. Fica bloqueada por E.4 na
   prática, embora a spec ordene E.3 → E.4?
3. O frontend na Vercel serve um build de ~13 dias apontando para uma API que
   não existe. Vale despublicar até a E.4, ou deixar como está?
4. **`scripts/seed_all.py` está quebrado** (divergência 8), descoberto ao ligar o
   Docker. É o caminho que `make seed` e `docs/setup.md` mandam usar, então o
   onboarding do projeto não funciona hoje. Abrir bug próprio?

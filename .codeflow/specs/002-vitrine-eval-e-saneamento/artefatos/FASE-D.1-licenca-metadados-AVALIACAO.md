---
spec: 002-vitrine-eval-e-saneamento
fase: D.1
slug_fase: licenca-metadados
tentativa: 2
veredito: RESSALVAS
score: 9.5
threshold: 8.5
range_avaliado: 7f9f59a..2e6cd1d1d2a7c060d34fda9137c7aa0b25e52a6f
---

# FASE D.1 — Avaliação independente

## 1. Veredito e score

**Veredito:** RESSALVAS · **Score:** 9.5 / threshold 8.5

**Metade do D1-IMP-1 está fechada.** Consultei a API do GitHub e os dois campos que
dependiam de ação do owner estão preenchidos:

```text
$ gh repo view gabriel-ngrs/CalorIA --json description,repositoryTopics,licenseInfo
description: "Diário alimentar com IA: eval do pipeline de LLM versionado junto do código"
topics:      fastapi, groq, llm-eval, nextjs, postgresql, python        (6)
licenseInfo: null                                                        ← ainda falta
```

**A outra metade não é trabalho de agente nem de owner: é consequência da D.2.** O
GitHub detecta licença a partir do **branch default**, que é `main`, e o `LICENSE`
não está lá — `git show origin/main:LICENSE` não resolve. O arquivo existe e está
correto na `dev`. Enquanto `main` não receber a promoção, `licenseInfo` continua
`null` por construção, e o AC-18 não fecha. Detalhe em §4.

Tudo o mais da fase verifica: a versão está sincronizada nos quatro arquivos (`0.7.0`),
a linha "Todos os direitos reservados" saiu do README e virou `[MIT](LICENSE) — uso
livre, com atribuição`, e o `LICENSE` é MIT como a OQ4 decidiu — sem troca de licença
por conta própria, que era o escopo travado.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 4 | Passos 1 e 2 completos e verificados. Passo 3 em dois terços: description e topics preenchidos (§6), `homepage` deliberadamente vazia com justificativa que aceito (§5). AC-18 falha só na licença detectada, por dependência estrutural da D.2 (§4). Escopo travado respeitado: CHANGELOG histórico intocado, licença é MIT como a OQ4 decidiu |
| 2 | Arquitetura e direção de dependências | 3 | 5 | Não se aplica em substância — a fase é metadados. Nada de código de produção foi tocado além da constante de versão |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | `LICENSE` MIT com titular nomeado; nenhum segredo entrou no diff. A abertura da licença é decisão registrada (OQ4), não default silencioso |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | `APP_VERSION` é constante única em `main.py:19`, consumida em `:44` (Swagger) e `:96` (`/health`) — a versão não foi escrita três vezes à mão |
| 5 | Padrões de domínio/aplicação | 2 | 5 | CHANGELOG mantém `## [Não lançado]` no topo e `## [0.7.0] - 2026-05-10` abaixo — Keep a Changelog preservado, sem reescrever histórico |
| 6 | Local e nomes dos arquivos | 2 | 5 | Exatamente os arquivos declarados na §5 |
| 7 | Qualidade de código | 2 | 5 | A linha do README diz o que a licença permite ("uso livre, com atribuição"), não só o nome dela |
| 8 | Testes e cobertura | 2 | 4 | `make check` verde nos cinco componentes (§6). Desconto: não há asserção travando a sincronia das quatro versões — é o mesmo tipo de lacuna que a C.7 fechou com `test_o_snapshot_cobre_todos_os_prompts_de_producao`, e o drift de versão é justamente o defeito que a fase existe para corrigir (§5) |
| 9 | Migration safety | 2 | [—] | Nenhuma migration tocada |

Score = (3·4 + 3·5 + 3·5 + 3·5 + 2·5 + 2·5 + 2·5 + 2·4) / 20 · 2 = 95/20 · 2 = **9.5**

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

**D1-IMP-1 (mantido, agora reduzido à metade) — AC-18 não fecha: a API do GitHub não
reporta licença detectada, e não vai reportar antes da D.2.**

**Onde:** Critério de conclusão da Fase D.1 (*"AC-18 satisfeito"*) e §9 do DoD
(*"D.1 — AC-18"*), contra a resposta da API.

**O que medi:**

```text
$ gh repo view gabriel-ngrs/CalorIA --json licenseInfo,defaultBranchRef
{"licenseInfo": null, "defaultBranchRef": {"name": "main"}}
$ git show origin/main:LICENSE   → NAO existe
$ head -1 LICENSE                → MIT License          (existe na dev, correto)
$ git rev-list --count origin/main..origin/dev
192      (+38 commits locais ainda não empurrados)
```

**O defeito, e por que ele não é do executor.** O GitHub deriva `licenseInfo` do branch
default. O default é `main`; `main` parou em 2026-04-29 e não tem `LICENSE`. Nenhuma
ação dentro do escopo da D.1 muda isso: o arquivo já está criado e correto. O AC-18
exige um estado do **servidor** que só a promoção da Fase D.2 produz.

Registro isso como IMPORTANTE, e não como bloqueio externo aceitável, por uma razão de
processo: o gate da fase é AC-18 inteiro, e ele não está satisfeito. Marcar APROVADO
gravaria no pipeline que a licença está detectada quando a API diz `null`.

**Por que não é BLOQUEANTE.** Não há defeito no repositório local. É ordenação de fases:
a D.1 declara `Depende de: A.2`, quando metade do seu AC depende da D.2.

**Correção sugerida — duas saídas legítimas, e a escolha é do owner:**

1. **Executar a D.2** (promover `dev` → `main` com tag e release) e reconferir:
   ```bash
   gh repo view gabriel-ngrs/CalorIA --json licenseInfo,description,repositoryTopics
   ```
   Anexar a saída como seção datada no EXECUCAO da D.1 e reavaliar. É o caminho natural
   — a D.2 está livre desde que o portão da A.1 foi levantado (OQ13).
2. **Corrigir o grafo da spec**, movendo a cláusula "licença detectada" do AC-18 para o
   AC-19 (que já é o AC da D.2), do mesmo modo que a cláusula do HEAD remoto migrou do
   AC-1 para o AC-2 na Fase A.1. É o mesmo defeito de modelagem: um AC que a fase não
   consegue satisfazer sozinha. Registrar em §8 ou numa decision.

Recomendo a **1**, porque a D.2 não tem mais impedimento e resolve as duas metades de
uma vez.

## 5. Sugestões

- **`homepageUrl` continua vazio, e concordo com o motivo.** O único endereço disponível
  é `frontend-nine-mu-59.vercel.app`, que responde 200 mas aponta para uma API fora do ar
  (medido na avaliação da A.1 e confirmado pela E.1): a tela de login abre e nada
  autentica. Apontar a homepage de um portfólio para uma demo quebrada é pior que
  deixá-la vazia. Vale preencher junto da E.4, quando houver deploy de verdade. O AC-18
  não exige `homepage`, então isto não entra como achado.
- **Um teste travando a sincronia das quatro versões custaria poucas linhas.** O drift
  `CHANGELOG 0.7.0` × `pyproject 0.1.0` × `main.py 0.1.0` × `package.json 0.1.0` é o
  defeito que originou a fase (AUD-054); hoje está corrigido, e nada impede que volte no
  próximo release. Um teste que leia os quatro e compare fecharia a porta — mesmo padrão
  que a C.7 adotou para os snapshots de prompt.
- **Os 6 topics são bons e um sétimo ajudaria:** `llm-eval` é o diferencial do
  repositório, mas quem busca por `ai` ou `nutrition` não chega. `nutrition` amplia sem
  diluir.

## 6. Comandos rodados + saídas reais

> Gates compartilhados rodados uma vez sobre o HEAD atual (`7b2e453`), descendente do
> `sha_final` desta fase.

```text
# --- Passo 2: ancestralidade e árvore limpa ---
$ git status --porcelain | wc -l
0
$ git merge-base --is-ancestor 7f9f59a HEAD                                  → ANCESTRAL
    7f9f59a feat(frontend): metadados, favicon, OpenGraph e polimento de UI
$ git merge-base --is-ancestor 2e6cd1d1d2a7c060d34fda9137c7aa0b25e52a6f HEAD → ANCESTRAL

# --- AC-18, item a item, contra a API (não contra o relatório) ---
$ gh repo view gabriel-ngrs/CalorIA --json description,homepageUrl,repositoryTopics,licenseInfo
description : "Diário alimentar com IA: eval do pipeline de LLM versionado junto do código"  ✓
topics      : fastapi, groq, llm-eval, nextjs, postgresql, python                            ✓
homepageUrl : ""                                          (não exigido pelo AC-18)
licenseInfo : null                                                                           ✗

# --- por que licenseInfo é null: o default branch não tem o arquivo ---
$ gh repo view … --json defaultBranchRef   → {"name": "main"}
$ git show origin/main:LICENSE             → NAO existe
$ head -3 LICENSE                          → MIT License / Copyright (c) 2026 Gabriel …   ✓ (na dev)
$ git rev-list --count origin/main..origin/dev
192

# --- AC-18, sincronia de versão nos quatro arquivos ---
$ grep -m1 "^version" backend/pyproject.toml     → version = "0.7.0"
$ grep -n "APP_VERSION" backend/app/main.py      → 19: APP_VERSION = "0.7.0"  (usada em :44 e :96)
$ grep -m1 '"version"' frontend/package.json     → "version": "0.7.0"
$ grep -m3 -E "^## " CHANGELOG.md                → ## [Não lançado] / ## [0.7.0] - 2026-05-10
   → os quatro em 0.7.0                                                                      ✓

# --- passo 1: README sem "todos os direitos reservados" ---
$ grep -in "licen" README.md
210:## Licença
212:[MIT](LICENSE) — uso livre, com atribuição.                                               ✓
$ grep -ci "direitos reservados" README.md
0                                                                                            ✓

# --- gate: make check (os cinco componentes, rodados por mim) ---
$ docker exec caloria_backend ruff check .          → All checks passed!
$ docker exec caloria_backend ruff format --check . → 147 files already formatted
$ docker exec caloria_backend mypy app/ evals/      → Success: no issues found in 81 source files
$ docker exec caloria_backend pytest -q --cov=app --cov=evals
620 passed, 1 skipped — Required test coverage of 72.0% reached. Total coverage: 74.28%
$ cd frontend && npm test         → 20 suites, 118/118 passed
$ cd frontend && npm run lint     → exit 0 (1 Warning pré-existente, Plasma.tsx:156)
$ cd frontend && npx tsc --noEmit → exit 0                                                   ✓

$ git status --porcelain | wc -l
0
```

## 7. Itens da fase / DoD não atendidos

| Item (§5 / §9 da spec) | Estado |
|---|---|
| Passo 1 — `LICENSE` MIT e README sem "direitos reservados" | Atendido |
| Passo 2 — versão sincronizada nos quatro arquivos | Atendido (`0.7.0`) |
| Passo 3 — description e topics no GitHub | Atendido nesta tentativa |
| Passo 3 — homepage | Não preenchida, com justificativa aceita (§5). Fora do AC-18 |
| **AC-18 — licença MIT detectada pela API** | **NÃO ATENDIDO** — `licenseInfo: null`; depende da D.2 (achado 4.1) |
| AC-18 — description e topics não vazios | Atendido |
| AC-18 — versão igual nos quatro arquivos | Atendido |
| Gate — `make check` verde | Atendido, rodado por mim nos cinco componentes |
| Escopo travado — CHANGELOG histórico intocado, licença MIT | Atendido |

## 8. Divergências entre o relatório e o código real

1. **Nenhuma divergência.** Os quatro arquivos estão em `0.7.0`, o `LICENSE` é MIT, o
   README foi ajustado, e a description/topics estão de fato no GitHub — conferi pela
   API, não pelo relatório.

2. **O relatório declara `homepageUrl` vazio e explica o porquê** ("o único endereço
   disponível é o frontend na Vercel com backend fora do ar"). Confirmei as duas
   pontas: a Vercel responde 200 e a API `caloria.duckdns.org` não aceita conexão. A
   justificativa procede.

3. **Nota de escopo, não divergência:** a fase declara `Depende de: A.2`, mas metade do
   seu AC só é satisfazível depois da D.2. É defeito de modelagem da spec, não de
   execução — e é o mesmo padrão que já obrigou a mover uma cláusula do AC-1 para o AC-2
   na Fase A.1.

---
id: 002
slug: 002-vitrine-eval-e-saneamento
title: "Vitrine técnica: eval do pipeline de IA, esteira de qualidade reativada, saneamento do histórico e replanejamento do deploy"
type: infra
status: active
priority: P0
size: XL
risk_level: RED
refine_mode: DEEP
wave: multi
domain: fullstack
bounded_context: multi
cross_context: [seguranca, ci-cd, ai-eval, documentacao, deploy, frontend]
created_at: 2026-07-29
updated_at: 2026-08-09
owner: Gabriel
linked_adr: [ADR-002, ADR-006, ADR-008]
related_bugs: [001, 003]
quality_gate:
  scorer: phase-evaluator
  threshold: 8.5
---

# 002 — Vitrine técnica: eval, esteira e saneamento

> **Nota de planning (2026-07-29):** spec construída após sondagem do codebase real
> por cinco agentes paralelos (pipeline de IA, backend/CI, frontend, documentação/
> organização, pesquisa de estado da arte em eval de LLM), com verificação direta
> dos 31 caminhos citados.
>
> **O diagnóstico central:** a qualidade do código é alta e disciplinada — `ruff
> check .` limpo, `mypy app/` **strict** limpo em 72 arquivos, zero TODO/FIXME em
> todo `backend/app`, 232 funções de teste, 15 migrations com cabeça única, 49 dos
> 51 endpoints autenticados. **A automação que a protegeria está desligada e a
> vitrine que a mostraria está três meses defasada.** `ci.yml:9` e `cd.yml:7` foram
> trocados para `workflow_dispatch`; `origin/main` parou em 2026-04-29 e ainda
> anuncia uma stack abandonada; não há LICENSE, tag, release, description ou topics.
> E existe uma credencial pessoal em texto claro no HEAD público.
>
> **Já existe e é reusado:** `backend/scripts/eval_golden_set.py` (30 casos
> brasileiros em medida caseira), `backend/scripts/eval_food_lookup.py` (40 consultas
> rotuladas × 7 estratégias × 9 limiares), `backend/scripts/instrument_meal_pipeline.py`
> (7 pares de descrições equivalentes + teste de determinismo, com monkeypatch de
> `food_lookup` para capturar o ranking), o gate `backend/tests/integration/test_golden_set.py`
> (limiares travados, medido em 2026-07-26), a injeção de `AIClient` por construtor
> nos quatro consumidores, `PortionNormalizer`, o job `backend` do `ci.yml` e o alvo
> `make check`.
>
> **É novo:** registry de versionamento de prompt; dataset de eval com ground truth
> externo; runner de métricas MdAPE/SSPB estratificado com IC bootstrap; bateria de
> invariância metamórfica; cassettes VCR; série temporal `evals/runs/history.jsonl`;
> LICENSE; ADR-009.
>
> **Fora do escopo desta spec:** os módulos novos das melhorias 001–004 (treino,
> dieta, gamificação, contexto de refeição) — continuam em `.codeflow/melhorias/`,
> a fatiar. Reprojeto do pipeline de IA: o eval **mede**, não redesenha — a única
> exceção é a Fase B.5, que propaga ao `VisionParser` a correção do bug 001 que o
> eval torna impossível de ignorar. Roadmap 9.4 (OAuth, CDN, monetização).
> Higienização das 23.398 linhas `ai_estimated` da tabela `foods` (Roadmap 10.3) —
> o eval vai medir o impacto, a limpeza é outra spec. Substituição da suíte de
> testes existente: o eval **soma** ao `test_golden_set.py`, não o troca.
>
> **OQ2 resolvida em 2026-08-02:** o ground truth do eval é **IBGE POF 2011**
> (medida caseira → gramas) combinado com **TACO 4ª edição** (gramas → kcal e
> macros). Duas fontes independentes entre si e independentes do projeto,
> citáveis por terceiro. A Fase C.4 está **desbloqueada**. Ver §8.

## Resumo executivo (TL;DR)

| | |
|---|---|
| **O quê** | Transformar o CalorIA em projeto de portfólio defensável: eliminar a exposição de credencial, religar a esteira de qualidade, construir o instrumento que mede a qualidade da IA, publicar a vitrine e replanejar o deploy. |
| **Por quê** | O projeto tem engenharia acima da média que ninguém vê e que nada impõe. A pergunta de entrevista "como você sabe que uma mudança de prompt melhorou?" hoje não tem resposta. E há uma credencial pessoal pública. |
| **Backend/Infra** | `gitleaks`; conftest que não exige Postgres; CI/CD reativados com gates; fail-fast de `SECRET_KEY`; rate limiting; registry de prompts; determinismo do `AIClient`; harness de eval (`backend/evals/`); correção do `VisionParser`. |
| **Frontend** | `metadataBase` + OpenGraph + favicon; FOUC do dark mode; `console.log` atrás de `NODE_ENV`; três bugs de UI. |
| **Decisão** | Uma spec, `wave: multi`, 5 tracks, 26 fases. Track A tem gate manual do owner (operação destrutiva de histórico). OQ2 resolvida (IBGE POF + TACO). |
| **Tamanho** | XL — 5 tracks independentes com acoplamento cruzado declarado por `id`. |

## Sumário

1. Problema e contexto (1.1 Princípios invioláveis)
2. Requisitos
3. Critérios de aceite
4. Abordagem técnica
5. Plano de desenvolvimento por fases (Tracks A–E)
6. Riscos
7. Rollout
8. Open Questions
9. Definition of Done (gate por etapa)

## 1. Problema e contexto

O repositório é **público** (`github.com/gabriel-ngrs/CalorIA`, `visibility: PUBLIC`)
com branch default `main`. Em 394 commits não há uma única tag, release, licença,
description ou topic. O que um avaliador encontra hoje ao abrir o repositório é a
versão de 2026-04-29.

Quatro problemas distintos, em ordem de urgência.

**Segurança.** O arquivo `frontend/e2e/auth.spec.ts` contém, no HEAD de
`origin/main`, uma credencial pessoal real do owner em texto claro. A correção
existe (commit `e208307`, "fix(seguranca): remove credenciais hardcoded de
auth.spec.ts") mas vive apenas em `origin/dev` e nunca foi promovida. A credencial
aparece em 5 pontos do histórico, e `docs/auditoria/achados.md:36` publica o comando
exato para extraí-la. Agravante: `frontend/e2e/auth.spec.ts:3` aponta `BASE_URL`
por padrão para o ambiente de produção na Vercel, de modo que rodar a suíte E2E sem
variáveis de ambiente cria usuários reais em produção.

**Esteira desligada.** `.github/workflows/ci.yml:9` e `.github/workflows/cd.yml:7`
foram trocados para `on: workflow_dispatch`, com os gatilhos originais comentados e
a justificativa "esteira de CI/CD em correcao". O pipeline em si é bem construído —
serviços Postgres 16 e Redis 7 com healthcheck, `ruff` → `mypy` → `pytest --cov` →
Codecov, job de frontend paralelo com ESLint, Jest e build de produção — e ficaria
verde hoje, porque `ruff check .` e `mypy app/` passam limpos. Foram cerca de 15
commits sem gate algum. O README ainda exibe o badge do workflow morto, o que é
sinal pior do que não ter badge.

Agravante que bloqueia o resto: `backend/tests/conftest.py:69` chama
`asyncio.run(_reset_schema())` **no import do módulo**, num bloco cuja intenção está
documentada em `:64-68`. O efeito colateral é que até `pytest tests/unit
--collect-only` falha com `InvalidPasswordError` sem um Postgres no ar — e o stub
de `backend/tests/unit/conftest.py:12-18` não neutraliza isso, porque a conexão
acontece no import do conftest pai, não numa fixture. Os 199 testes unitários são
puros e usam mocks; deveriam rodar em segundos sem infraestrutura.

**Ausência de eval.** Esta é a lacuna que o owner identificou e a que mais vale
para o portfólio. O pipeline de IA (`backend/app/services/ai/`, 2.503 LOC) não tem
nenhuma forma de versionamento de prompt: os prompts são strings inline em `.py` e
`grep -rn "PROMPT_VERSION" backend/app` retorna zero. As chamadas não usam JSON mode
em runtime, não passam `seed`, `max_tokens` nem `top_p`, e a `temperature` é
`0.1 if system else 0.3` (`ai_client.py:154`) — o que faz os sete prompts do
`InsightsGenerator` rodarem a 0.3 por acidente, já que nenhum passa `system=`. A
chave do cache Redis (`ai_client.py:48`) não inclui o modelo, então trocar
`GROQ_TEXT_MODEL` serve até 7 dias de respostas do modelo antigo — o que corromperia
silenciosamente qualquer comparação A/B.

**O seam existente é forte e deve ser reusado.** O bug 001
(`.codeflow/bugs/001-fluxo-cadastro-refeicao.md`) já produziu instrumentação real:
`instrument_meal_pipeline.py` roda pares de descrições equivalentes contra Groq real
e banco real, monkeypatchando `food_lookup_mod.find_foods_in_text` para capturar o
ranking completo, e calcula `divergencia_pct`. Os números medidos são a linha de
base da narrativa: a reprodução oficial do bug deu 3486 vs 2098 kcal (39,8% de
divergência) antes, e 2160 vs 2160 (0,0%) depois. E o achado metodológico é o
material de entrevista: **a divergência não vinha de aleatoriedade do modelo** — três
execuções da mesma string deram 572,3 kcal idênticos — mas de o prompt do Estágio 1
proibir o uso do banco, com a regra "Liste CADA ingrediente separadamente, mesmo em
pratos compostos", que impedia a IA de emitir `food_name="pizza calabresa"` e portanto
impedia o lookup de casar.

O que falta transformar isso em instrumento: a rodada "depois"
(`backend/artefatos/baseline-depois.json`) tem **6 dos 8 casos vazios**, porque morreu
com `RateLimitError 429` no caso 3 e nunca foi refeita. Não há ground truth absoluto,
não há cobertura de foto, não há amarração a versão de prompt, não há gate, não há
série temporal. É um script one-off, não um harness.

E o `VisionParser` ficou para trás na correção do bug 001: seu prompt
(`vision_parser.py:22-67`) **ainda contém** a regra 4 ("Liste cada alimento
separadamente, mesmo em pratos compostos") e a regra 5 ("Estime porções sempre em
gramas") — precisamente as duas removidas do `MealParser` por serem a causa raiz.
Além disso `vision_parser.py:216,240` ainda usa `zip(..., strict=False)`, perdendo
itens em silêncio; o sanity check tem `0.35` hardcoded inline em `:157` enquanto o
`MealParser` já o nomeou como `_SANITY_DIVERGENCE` em `meal_parser.py:137`; e o
fallback em `:244-245` usa a quantidade crua da IA, o que levanta `ValidationError`
fora dos blocos `except` e vira HTTP 500 quando a IA devolve `"dois"`.

**Deploy indeterminado.** O frontend responde em produção na Vercel, mas a URL não
é mencionada em nenhum documento. O backend deveria estar na Hetzner via
`docker-compose.backend.yml`, disparado por um `cd.yml` que está desligado — estado
atual desconhecido. `docs/deploy.md` descreve um cenário full-stack self-hosted que
não corresponde ao que roda. Há três composes e dois Caddyfiles, e o par que
efetivamente roda em produção é o único sem documentação nem comentário de cabeçalho.

### 1.1 Princípios invioláveis

Cada princípio rastreia a uma regra real do repositório.

1. **Lógica de negócio vive em `services/`, nunca nos endpoints.** Endpoints só
   orquestram. — `.codeflow/constitution.md`, "Regras invariantes específicas".
2. **`mypy app/` em modo strict deve passar; todos os tipos anotados.** Código novo
   sem anotação completa não está pronto. — `.codeflow/constitution.md` e
   `backend/pyproject.toml:80-84` (`strict = true`).
3. **`GROQ_API_KEY` nunca é exposta ao frontend.** Toda chamada de IA passa pelo
   backend. — `.codeflow/constitution.md`.
4. **Nunca commitar `.env`, chaves ou segredos.** — `.codeflow/constitution.md`.
   Esta spec estende: nenhum artefato de eval versionado pode conter credencial,
   PII ou o conteúdo de `.env`.
5. **Commits em Conventional Commits em português**, imperativo e minúsculas, sem
   mencionar autor, IA ou agente, e sem `Co-Authored-By`. — `.codeflow/constitution.md`
   e `CLAUDE.md`.
6. **Migrations já aplicadas são imutáveis.** Mudança de schema exige migration nova
   e revisada. — `.codeflow/constitution.md`, "Áreas de alto risco".
7. **Diff mínimo; refatoração não solicitada é proibida.** —
   `~/.codeflow/framework/core/constitution.md`, "Princípios invariantes".
8. **Identificadores de código em inglês; mensagens ao usuário em pt-BR.** —
   `~/.codeflow/framework/core/rules/naming.md`. Ressalva local: os scripts de eval
   existentes (`eval_golden_set.py`, `instrument_meal_pipeline.py`) usam
   identificadores em pt-BR (`CasoDourado`, `divergencia_pct`, `PARES`). Pela
   exceção "código herdado com convenção própria estabelecida" da mesma rule, o
   novo código em `backend/evals/` **mantém a convenção local em pt-BR** para não
   criar um segundo idioma dentro do mesmo domínio.
9. **O banco nutricional é a tabela `foods`**, e o sanity check calórico de 35%
   protege contra registros incorretos. — `.codeflow/constitution.md` e ADR-006.
10. **Os limiares do lookup (0.65 de aceite, boost TACO 1.40×, exclusão de
    `ai_estimated`) foram estabelecidos por medição e não se alteram sem nova
    medição.** — `.codeflow/decisions/2026-07-26-limiares-lookup-nutricional.md`
    (decision ativa).
11. **Um gate duro não admite override conversacional.** —
    `~/.codeflow/framework/core/constitution.md`, "Política de falhas". Aplica-se
    diretamente ao gate manual do Track A.

## 2. Requisitos

### Funcionais

**Track A — Segurança**

- **FR-A1** — A credencial pessoal exposta em `frontend/e2e/auth.spec.ts` deve ser
  rotacionada em todos os serviços onde tenha sido reusada, e o HEAD de todas as
  branches remotas deve estar livre dela.
- **FR-A2** — O histórico do git deve ser purgado da credencial em todas as branches
  e refs; os documentos que descrevem o caminho de extração
  (`docs/auditoria/achados.md`, `docs/auditoria/log.md`) devem ser reescritos.
- **FR-A3** — Um scanner de segredos deve bloquear commit local e falhar o CI.
- **FR-A4** — A suíte E2E não pode apontar para produção por padrão.

**Track B — Esteira de qualidade**

- **FR-B1** — `pytest tests/unit/` deve coletar e executar sem nenhum serviço de
  infraestrutura no ar.
- **FR-B2** — O CI deve rodar automaticamente em `push` para `dev` e em
  `pull_request` para `main`, com lint, typecheck e testes bloqueantes.
- **FR-B3** — A aplicação deve recusar-se a iniciar fora de desenvolvimento com
  `SECRET_KEY` no valor default ou com menos de 32 caracteres.
- **FR-B4** — Os endpoints públicos de autenticação e os endpoints de IA devem ter
  rate limiting.
- **FR-B5** — A cobertura de testes deve ter piso configurado e bloqueante, e os
  routers `push.py` e `reminders.py` devem sair de cobertura zero de integração.

**Track C — Eval do pipeline de IA**

- **FR-C1** — Todo prompt de produção deve ter identidade versionada (nome, versão,
  `sha256` do template) e essa identidade deve ser registrada em log a cada chamada.
- **FR-C2** — As chamadas ao provedor devem ser reprodutíveis: JSON mode onde a
  saída é JSON, parâmetros de amostragem explícitos, chave de cache incluindo o
  modelo, e retry por classe de exceção com teto de tempo.
- **FR-C3** — Deve existir um dataset de eval versionado, estratificado em alimento
  simples, prato composto e foto, com schema que declare a origem de cada referência.
- **FR-C4** — O runner deve calcular, por estrato e no agregado, MdAPE e SSPB de
  kcal, MAE e acurácia por tolerância absoluta para macros, com intervalo de
  confiança por bootstrap.
- **FR-C5** — Deve existir uma bateria de invariância que verifique relações
  metamórficas sobre a mesma refeição descrita de formas diferentes.
- **FR-C6** — O eval deve ter uma camada rápida sem custo de API executada a cada
  PR, e uma camada completa contra o provedor real executada em agenda.
- **FR-C7** — Cada execução do eval completo deve emitir um registro versionado que
  amarre métricas a commit, versão de prompt, modelo e dataset.
- **FR-C8** — O `VisionParser` deve receber a correção do bug 001 já aplicada ao
  `MealParser`.

**Track D — Vitrine e polimento**

- **FR-D1** — O repositório deve ter LICENSE MIT, description, topics, homepage e
  versão sincronizada entre CHANGELOG, `pyproject.toml`, `main.py` e `package.json`.
- **FR-D2** — `main` deve refletir o estado atual de `dev`, com release anotada.
- **FR-D3** — O README deve funcionar como peça de portfólio: comando único de
  execução, link da demo, diagrama de arquitetura, e a seção de decisões técnicas
  com os números medidos.
- **FR-D4** — O repositório deve ser podado dos artefatos de execução de agente e
  dos dumps brutos, preservando o que o framework `.codeflow` precisa para operar.
- **FR-D5** — A aplicação deve ter favicon, `metadataBase` e cartões OpenGraph e
  Twitter.
- **FR-D6** — O tema escuro não pode piscar no carregamento; logs de diagnóstico não
  podem aparecer em produção; os três bugs de UI identificados devem ser corrigidos.

**Track E — Deploy**

- **FR-E1** — O estado real do que está publicado deve ser levantado e registrado.
- **FR-E2** — A topologia de deploy deve ser decidida e registrada como ADR-009, e
  os arquivos de compose e Caddy devem refletir sem ambiguidade o que roda.
- **FR-E3** — Deve existir conta de demonstração com dados semeados, acessível a
  partir do README.
- **FR-E4** — O deploy deve ser refeito a partir da topologia decidida e o CD deve
  voltar a ser automático.

### Não-funcionais

- **NFR-1** — `ruff check .`, `ruff format --check .` e `mypy app/` (strict)
  continuam sem erros ao fim de cada fase. Frontend: `npm run lint` e
  `npx tsc --noEmit` sem erros.
- **NFR-2** — A camada rápida do eval executa em menos de 60 segundos e faz zero
  chamadas de rede.
- **NFR-3** — A camada completa do eval respeita o rate limit do free tier da Groq
  sem abortar: nenhuma execução pode terminar com casos vazios por `429`.
- **NFR-4** — Nenhum artefato versionado por esta spec contém credencial, PII, e-mail
  pessoal ou conteúdo de `.env`.
- **NFR-5** — Reprodutibilidade: mesmo commit, mesmo dataset e mesmo cache produzem
  o mesmo relatório de eval.
- **NFR-6** — Os limiares já travados em `backend/tests/integration/test_golden_set.py`
  não regridem (erro médio ≤ 10%, ≥ 80% dentro de ±10%, ≥ 85% de porção ancorada,
  erro individual ≤ 100%).
- **NFR-7** — Nenhuma fase altera migrations já aplicadas.

## 3. Critérios de aceite

- **AC-1** (FR-A1) — *Dado* o repositório após a Fase A.1, *quando* se inspeciona o
  working tree, *então* a credencial não aparece em nenhum arquivo; *e* o owner
  confirmou por escrito no relatório da fase que a senha foi rotacionada nos serviços
  afetados; *e* o repositório está privado até o fim da Fase A.2.
- **AC-2** (FR-A2) — *Dado* o histórico purgado, *quando* se roda **(a)** a varredura
  de segredos sobre todo o histórico com as regras do projeto
  (`gitleaks detect --config .gitleaks.toml --log-opts="--all"`) *e* **(b)** a
  verificação direta, independente de heurística,
  `git log --all -S'<valor da credencial>' --oneline | wc -l`, *então* **(a)**
  retorna zero achados *e* **(b)** retorna `0`; *e* o HEAD de toda branch remota está
  livre da credencial; *e* nenhum documento de `docs/auditoria/` contém comando de
  extração nem e-mail pessoal.
  > **Nota (2026-08-02).** A redação anterior aceitava
  > `gitleaks detect --log-opts="--all"` com as regras default como gate. Isso é um
  > gate **falso**: medido, ele retornava zero **antes** de qualquer purga, sobre um
  > histórico que ainda continha a credencial em 11 commits (as regras default casam
  > por forma de chave de API, não por senha arbitrária). Daí as duas exigências
  > independentes — a varredura com `--config .gitleaks.toml` e a busca literal por
  > conteúdo com `git log -S`, que não depende de heurística alguma. A cláusula sobre
  > o HEAD das branches remotas migrou do AC-1 para cá: ela só é satisfazível depois
  > do force-push da A.2, não pela A.1 isolada.
- **AC-3** (FR-A3) — *Dado* um commit que introduza um segredo de teste, *quando* se
  tenta commitar, *então* o hook local rejeita; e *quando* o mesmo chega ao CI,
  *então* o job falha.
- **AC-4** (FR-A4) — *Dado* `frontend/e2e/auth.spec.ts`, *quando* nenhuma variável
  de ambiente é definida, *então* `BASE_URL` resolve para um endereço local e nenhum
  teste toca produção.
- **AC-5** (FR-B1) — *Dado* um ambiente sem Postgres e sem Redis, *quando* se roda
  `pytest tests/unit/`, *então* a coleta e a execução completam com sucesso.
- **AC-6** (FR-B2) — *Dado* um push para `dev`, *quando* o CI executa, *então* os
  jobs `backend` e `frontend` rodam automaticamente e falham a build se `ruff`,
  `mypy`, `pytest` ou `npm run lint` falharem.
- **AC-7** (FR-B3) — *Dado* `APP_ENV` diferente de desenvolvimento e `SECRET_KEY` no
  default, *quando* a aplicação inicia, *então* ela aborta com erro explícito; *e
  dado* desenvolvimento, *então* inicia normalmente.
- **AC-8** (FR-B4) — *Dado* mais requisições do que o limite configurado a
  `POST /api/v1/auth/login` numa janela, *quando* o limite é excedido, *então* a
  resposta é HTTP 429; idem para `POST /api/v1/ai/analyze-meal`.
- **AC-9** (FR-B5) — *Dado* o CI, *quando* a cobertura cai abaixo do piso
  configurado, *então* o job falha; e existe ao menos um teste de integração por
  endpoint de `push.py` e `reminders.py`.
- **AC-10** (FR-C1) — *Dado* uma análise de refeição, *quando* se inspeciona o log
  estruturado, *então* constam `prompt_name`, `prompt_version` e `prompt_sha`; e
  *quando* o conteúdo de um template muda sem bump de versão, *então* o `sha` muda
  e um teste detecta a divergência.
- **AC-11** (FR-C2) — *Dado* dois valores distintos de `GROQ_TEXT_MODEL`, *quando* o
  mesmo prompt é enviado, *então* as chaves de cache são distintas. *E dado* um
  `RateLimitError`, *então* o retry ocorre por classe de exceção, não por inspeção
  de string, com teto de tempo declarado.
- **AC-12** (FR-C3) — *Dado* o dataset de eval, *quando* se valida contra o schema,
  *então* todo caso tem `id`, `estrato`, `descricao`, `referencia_kcal`,
  `fonte_referencia` e `fonte_url`, e nenhum caso tem referência derivada da própria
  tabela `portions` do projeto.
- **AC-13** (FR-C4) — *Dado* uma execução do runner, *quando* o relatório é gerado,
  *então* ele traz MdAPE e SSPB por estrato e no agregado, com `n` e IC95 por
  estrato, e macros reportados em MAE com tolerância absoluta — nunca em percentual.
- **AC-14** (FR-C5) — *Dado* um grupo de descrições equivalentes da mesma refeição,
  *quando* a bateria roda, *então* o relatório traz `spread` por grupo e a taxa de
  aprovação sob a tolerância declarada; e a reprodução oficial do bug 001 é um dos
  grupos.
- **AC-15** (FR-C6) — *Dado* um PR, *quando* o CI executa, *então* a camada rápida
  do eval roda sem chamadas de rede e falha se o payload enviado ao provedor mudar
  sem atualização do snapshot. *E dado* a execução agendada, *então* a camada
  completa roda contra o provedor real e conclui sem casos vazios **além dos
  nominados no bug 003** — hoje os três do estrato de foto
  (`foto-coxinha-1-unidade`, `foto-ovo-frito-1-unidade`, `foto-banana-1-unidade`),
  que falham por HTTP 413.
  > **Nota (2026-08-08).** A cláusula "conclui sem casos vazios" **sem
  > qualificador** migrou para o **bug 003**
  > (`.codeflow/bugs/003-http-413-no-estrato-de-foto.md`), que é quem corrige o
  > HTTP 413 medido na OQ19. Nenhuma fase desta spec pode fechá-la: o fix é em
  > `config.py`/`ai_client.py` (escopo da C.2, já concluída) e no frontend, e o
  > Track C está fechado em 8 fases. É o mesmo defeito de modelagem já corrigido no
  > AC-1 (A.1) e no AC-18 (D.1) — um gate que depende de efeito fora do escopo de
  > quem responde por ele. Enquanto o bug 003 estiver aberto os três vazios são
  > exceção **nominada**, não tolerância genérica: qualquer caso vazio fora dessa
  > lista reprova o AC. Ver OQ21.
- **AC-16** (FR-C7) — *Dado* duas execuções completas em commits diferentes, *quando*
  se lê `evals/runs/history.jsonl`, *então* cada linha amarra métricas a
  `git_commit`, versões de prompt com `sha`, modelo e `sha` do dataset.
- **AC-17** (FR-C8) — *Dado* o `VisionParser`, *quando* a IA devolve menos itens do
  que os identificados, *então* nenhum item é perdido em silêncio; *e quando*
  devolve uma quantidade por extenso, *então* não ocorre HTTP 500; *e* o prompt de
  visão não contém mais as regras de decomposição obrigatória e de gramas
  obrigatórias.
- **AC-18** (FR-D1) — *Dado* o repositório, *quando* se consulta a API do GitHub,
  *então* description e topics não vazios; *e* o arquivo `LICENSE` (MIT) está
  versionado na branch de trabalho; e a versão é a mesma em CHANGELOG,
  `pyproject.toml`, `main.py` e `package.json`.
  > **Nota (2026-08-03).** A cláusula "licença **detectada** pela API" migrou para
  > o AC-19. O GitHub deriva `licenseInfo` do **branch default**, então nenhuma
  > ação dentro do escopo da D.1 a satisfaz: ela depende da promoção da D.2, que a
  > OQ15 moveu para o fim da spec. É o mesmo defeito de modelagem já corrigido na
  > Fase A.1, quando a cláusula sobre o HEAD das branches remotas migrou do AC-1
  > para o AC-2. Ver OQ18.
- **AC-19** (FR-D2) — *Dado* `origin/main`, *quando* se compara com `origin/dev`,
  *então* não há commits de `dev` ausentes em `main`, e existe tag anotada com
  release publicada; *e* a API do GitHub passa a reportar a licença MIT detectada
  (`licenseInfo` não nulo), que só o avanço do branch default produz; *e*
  `gh workflow list` passa a registrar o `eval.yml`, que hoje devolve `HTTP 404`
  pelo mesmo mecanismo — o GitHub só conhece workflow de `schedule`/
  `workflow_dispatch` a partir do branch default (ver OQ20).
- **AC-20** (FR-D3) — *Dado* o README, *quando* lido por alguém que não conhece o
  projeto, *então* ele traz comando único de execução que funciona, portas corretas,
  link da demo com credenciais de demonstração, diagrama Mermaid renderizável e
  seção de decisões técnicas com números medidos e citados.
- **AC-21** (FR-D4) — *Dado* o repositório podado, *quando* se lista os arquivos
  versionados, *então* não há artefatos `FASE-*-EXECUCAO.md`/`-AVALIACAO.md`, dumps
  brutos nem JSON de baseline; *e* `.codeflow/INDEX.md`, `constitution.md`,
  `manifest.md`, `discovered.md`, `_TEMPLATES/`, `decisions/`, `bugs/`, `melhorias/`
  e os `SPEC_*.md` continuam versionados e o framework opera normalmente.
- **AC-22** (FR-D5) — *Dado* uma URL da aplicação compartilhada, *quando* a
  plataforma busca metadados, *então* há título, descrição e imagem OpenGraph; e o
  navegador exibe favicon próprio.
- **AC-23** (FR-D6) — *Dado* um usuário com tema escuro salvo, *quando* recarrega
  qualquer página, *então* não há flash claro; *e* em build de produção o console
  não recebe log de request, navegação ou query; *e* a data do histórico de peso
  confere com a data registrada.
- **AC-24** (FR-E1) — *Dado* o levantamento, *quando* se lê o relatório da fase,
  *então* consta o estado verificado de frontend e backend em produção, com
  evidência de requisição.
- **AC-25** (FR-E2) — *Dado* o repositório, *quando* se lista os arquivos de
  orquestração na raiz, *então* cada um declara em cabeçalho seu propósito, e existe
  ADR-009 em `docs/architecture.md` registrando a topologia.
- **AC-26** (FR-E3) — *Dado* as credenciais de demonstração do README, *quando* se
  faz login na demo, *então* o dashboard exibe dados de refeições, peso, hidratação
  e humor.
- **AC-27** (FR-E4) — *Dado* um merge em `main`, *quando* o CD executa, *então* o
  deploy ocorre automaticamente e a aplicação responde saudável; e a sincronização
  antes da migração não depende de `sleep` fixo.

## 4. Abordagem técnica

### Mapa NOVO / REUSADO / REMOVIDO

| Área | NOVO | REUSADO | REMOVIDO |
|---|---|---|---|
| Segurança | `gitleaks` no `.pre-commit-config.yaml` e no `ci.yml` | `.pre-commit-config.yaml` (já tem `no-commit-to-branch`), `SECURITY.md` | credencial do histórico; `BASE_URL` apontando para produção em `frontend/e2e/auth.spec.ts:3` |
| Testes | fixture de schema sob demanda | `backend/tests/unit/conftest.py` (stub já existe), `backend/tests/conftest.py` | `asyncio.run(_reset_schema())` no import (`conftest.py:69`) |
| CI/CD | gate de cobertura; job de eval rápido; job agendado de eval completo | jobs `backend` e `frontend` de `.github/workflows/ci.yml`; `.github/workflows/cd.yml` | `on: workflow_dispatch` em ambos; `sleep 10` de `cd.yml:38` |
| Config | `field_validator` de `SECRET_KEY`; rate limiting | `backend/app/core/config.py` (`is_development` em `:86-88`, hoje não usada para validar) | default inseguro efetivo de `SECRET_KEY` fora de dev |
| Prompts | `backend/app/prompts/` com registry, templates e `sha256` | strings inline de `meal_parser.py:61-133`, `vision_parser.py:22-97`, `insights_generator.py`, `pattern_analyzer.py:45-55` | prompts como constantes de módulo |
| AIClient | JSON mode, parâmetros explícitos, modelo na chave de cache, retry por classe | `backend/app/services/ai/ai_client.py` (cache Redis, backoff, `generate_with_image`) | `if "429" in str(exc)` (`ai_client.py`); chave de cache sem modelo (`:48`) |
| Eval | `backend/evals/` (dataset, runner, métricas, invariância, cassettes, `runs/history.jsonl`) | `backend/scripts/eval_golden_set.py` (`GOLDEN`), `eval_food_lookup.py`, `instrument_meal_pipeline.py` (padrão de monkeypatch e estrutura de pares), `backend/tests/integration/test_golden_set.py` | `backend/artefatos/*.json` como registro de baseline |
| VisionParser | — | `backend/app/services/ai/meal_parser.py` como referência da correção já feita | regras 4 e 5 do prompt (`vision_parser.py:22-67`); `zip(strict=False)` (`:216,240`); `0.35` inline (`:157`) |
| Vitrine | `LICENSE`; ADR-009 em `docs/architecture.md` | `README.md`, `CHANGELOG.md`, `Makefile` (alvo `init`), `docs/architecture.md` (ADR-001 a ADR-008) | badge de CI apontando para workflow inativo |
| Frontend | `app/favicon.ico`, `app/opengraph-image`, metadados | `frontend/app/layout.tsx:13-29`, `frontend/app/manifest.ts`, `frontend/components/theme-provider.tsx`, `next-themes` (já instalado, não usado) | `console.log` de `lib/api.ts` e `app/providers.tsx` em produção |
| Deploy | ADR-009; cabeçalhos nos arquivos de orquestração | `docker-compose.backend.yml`, `Caddyfile.backend`, `scripts/`, `backend/scripts/seed_dev_user.py` | ambiguidade entre os três composes |

### Detalhamento por track

**Track A.** A ordem importa e é contraintuitiva: a rotação da senha vem antes de
tudo porque é o único passo que interrompe o dano real — reescrever histórico não
desfaz o que já foi clonado ou indexado. A purga vem antes do merge para `main`
(Track D), porque `git filter-repo` reescreve todas as branches e um merge feito
antes seria desfeito. As duas primeiras fases têm **gate manual do owner**: envolvem
rotação de credencial em serviços externos e force-push destrutivo sobre 394 commits,
operações que um agente não deve executar num chat zerado.

**Track B.** `B.1` é pré-requisito de quase tudo: sem loop de teste local rápido,
nem o eval nem as correções têm onde ser validados. A correção é mover a criação de
schema de um efeito colateral de import para uma fixture com escopo de sessão que só
é solicitada por testes que precisam de banco — preservando a intenção documentada
em `conftest.py:64-68` (garantir que o schema exista antes da coleta para os testes
que o usam) sem impor a dependência aos testes puros.

**Track C.** O desenho separa deliberadamente **infraestrutura do harness** (C.1,
C.2, C.3, C.5, C.6, C.7, C.8) de **conteúdo do dataset** (C.4), porque OQ2 está
aberta.
O contrato entre os dois é o schema de caso: `id`, `estrato`, `descricao`,
`referencia_kcal`, `referencia_macros`, `fonte_referencia`, `fonte_url`,
`grupo_invariancia`, `data_de_adicao`. Qualquer fonte que preencha esse schema serve.

Sobre métricas, a decisão técnica que diverge da formulação inicial do owner: a
métrica headline é **MdAPE (mediana), não MAPE (média)**, acompanhada de **SSPB**.
O motivo é estrutural, não estético — o erro percentual absoluto é assimétrico por
construção, porque subestimar tem teto de 100% e superestimar não tem teto. Logo o
MAPE pune superestimativa mais do que subestimativa e, usado como função objetivo,
seleciona sistematicamente prompts que subcontam calorias, que é exatamente o modo
de falha danoso num diário alimentar. Pela mesma razão, macros em gramas são
reportados em erro absoluto com tolerância absoluta, nunca em percentual: café preto
tem 0,1 g de gordura e o percentual explode.

Sobre poder estatístico, o desenho é **pareado**: as versões de prompt são comparadas
nos mesmos casos. Com n em torno de 40 e design pareado sobre métrica contínua, o
efeito mínimo detectável fica em torno de 5 pontos percentuais; o mesmo n em design
não pareado sobre métrica binária só detectaria algo em torno de 22 pontos. Essa
análise entra no README do harness, incluindo a declaração explícita do que o n
**não** detecta.

**Track D.** `D.3` depende de `C.7` porque o README precisa dos números reais do
eval — escrevê-lo antes produziria as afirmações vagas que a spec existe para
eliminar. `D.4` preserva integralmente a operação do framework `.codeflow`: sai o
que é telemetria de execução, fica o que é registro de engenharia.

**Track E.** Começa por auditoria, não por documentação, porque a premissa do owner
é que os documentos de deploy não descrevem a realidade.

## 5. Plano de desenvolvimento por fases

> Cada fase é executável isoladamente por um agente lendo só este documento. Uma
> fase só inicia quando **todas** as listadas em "Depende de" estão concluídas.
> Comandos de validação do projeto: `make lint-check`, `make typecheck`,
> `make test-unit`, `make test-integration`, `make test-frontend`. Atenção:
> `make check` **não** roda `tests/integration/` — fases que tocam endpoints exigem
> `make test-integration` explicitamente.

### Track A — Segurança e saneamento do histórico

### Fase A.1 — Rotação de credencial e neutralização do HEAD público *(S)*

- **id:** `A.1`
- **slug:** `rotacao-credencial`
- **Objetivo:** interromper o dano ativo da credencial exposta e garantir que nenhum
  HEAD remoto a contenha.
- **Depende de:** nenhuma.
- **Arquivos alterados:** `frontend/e2e/auth.spec.ts`.
- **Passos:**
  1. **Ação do owner, fora do agente:** rotacionar a senha exposta em todos os
     serviços onde tenha sido reusada, e registrar a confirmação no relatório da
     fase. Este passo é pré-condição dos demais.
  2. **Ação do owner:** tornar o repositório privado até o fim da Fase A.2.
  3. Alterar `frontend/e2e/auth.spec.ts:3` para que `BASE_URL` resolva, na ausência
     de variável de ambiente, para um endereço local — nunca para produção.
  4. Verificar que nenhum arquivo no working tree contém a credencial.
- **Testes:** varredura do working tree sem achados; `npx playwright test --list`
  continua listando os testes; `make test-frontend` verde.
- **Escopo travado / violações BLOQUEANTES:** não reescrever histórico nesta fase
  (é a A.2). Não escrever a credencial em nenhum arquivo, relatório de execução,
  mensagem de commit ou artefato — nem para documentá-la. Não executar rotação de
  senha em nome do owner.
- **Critério de conclusão (gate):** owner confirmou por escrito a rotação; repositório
  privado; working tree sem a credencial; `make test-frontend` verde.

### Fase A.2 — Purga do histórico e reescrita dos documentos de auditoria *(M)*

- **id:** `A.2`
- **slug:** `purga-historico`
- **Objetivo:** remover a credencial de todo o histórico e eliminar o mapa de
  extração publicado.
- **Depende de:** `A.1`.
- **Arquivos alterados:** `docs/auditoria/achados.md`, `docs/auditoria/log.md`,
  `docs/auditoria/runbook.md`, `docs/auditoria/07-seguranca.md`,
  `docs/auditoria/artefatos/G1-creds.txt`, `docs/auditoria/plano.md`,
  `docs/auditoria/plano-correcao.md`, `docs/auditoria/relatorio-preliminar.md`,
  `docs/auditoria/08-testes.md`, `docs/legacy/analise.md`.
  > **Escopo corrigido (2026-08-02).** O plano declarava 2 arquivos; a execução
  > tocou 10. A credencial e o comando de extração viviam nos outros 8 também, e
  > `runbook.md` e `07-seguranca.md` **ainda publicavam o comando de extração** —
  > reescrever só os 2 declarados esvaziaria o FR-A2, que existe para eliminar o
  > mapa de extração, não uma cópia dele. Ver
  > `.codeflow/decisions/2026-08-02-extensao-escopo-redacao-pii-auditoria.md` e OQ7.
- **Passos:**
  1. Reescrever **todos os documentos listados em "Arquivos alterados"** removendo o
     e-mail pessoal e o comando de extração, preservando o achado em si (que houve
     credencial hardcoded, que foi corrigida, e a lição) sem os dados. O inventário
     não é o do diagnóstico da §1 (que localizou uma ocorrência, `achados.md:36`):
     é o resultado de uma varredura sobre `docs/` — ver a nota de escopo acima.
  2. Preparar o comando de `git filter-repo` que remove a credencial de todo o
     histórico, e documentá-lo no relatório da fase junto com o plano de force-push
     e o plano de reabertura dos PRs do Dependabot afetados.
  3. **Ação do owner, fora do agente:** executar `git filter-repo`, forçar push em
     todas as branches e refs, e solicitar ao GitHub Support a invalidação do cache
     de commits órfãos — que permanecem acessíveis por SHA mesmo após force-push.
     > **Omissão deliberada do ticket ao GitHub Support (2026-08-02).** O owner
     > decidiu não abrir o ticket, com fundamentação verificada no momento:
     > `forks: 0` e `network: 0` (não existe rede de forks que mantivesse os
     > objetos alcançáveis), `visibility: private` (acesso anônimo por SHA retorna
     > 404), a senha já rotacionada nos serviços de reuso (credencial morta), e o
     > e-mail restante declarado não sensível pelo owner. Risco residual e
     > mitigação em OQ10 e
     > `.codeflow/decisions/2026-08-02-omissao-ticket-github-support.md`.
  4. Verificar com varredura sobre todo o histórico que não há mais achados.
- **Testes (AC-2):** `gitleaks detect --config .gitleaks.toml --log-opts="--all"`
  com zero achados **e** `git log --all -S'<valor da credencial>' --oneline | wc -l`
  igual a `0` — as duas verificações, porque a varredura por heurística sozinha não
  é gate (ver nota do AC-2); `git log --all` sem ocorrência do e-mail; suíte completa
  verde após a reescrita.
- **Escopo travado / violações BLOQUEANTES:** **o agente não executa `filter-repo`
  nem force-push** — prepara, documenta e verifica. Não apagar os achados de
  auditoria por inteiro: o registro do incidente tem valor e deve sobreviver sem os
  dados sensíveis. Não alterar migrations nem código de produção nesta fase.
- **Critério de conclusão (gate):** varredura sobre todo o histórico com zero
  achados; documentos reescritos; PRs do Dependabot reabertos ou fechados
  conscientemente.

### Fase A.3 — Scanner de segredos no pre-commit e no CI *(S)*

- **id:** `A.3`
- **slug:** `gitleaks`
- **Objetivo:** fechar a classe de problema, não só a instância.
- **Depende de:** `A.2`, `B.2`.
- **Arquivos alterados:** `.pre-commit-config.yaml`, `.github/workflows/ci.yml`,
  `SECURITY.md`; e mais 19 arquivos num commit `style:` isolado, só de higiene
  (whitespace no fim de linha e ausência de newline final).
  > **Escopo corrigido (2026-08-02).** A dívida de whitespace/EOF é
  > **pré-existente** e só ficou visível porque o gate desta fase é
  > `pre-commit run --all-files`, que passa a rodar os hooks genéricos sobre o
  > repositório inteiro. Decisão do owner: corrigir agora, num commit `style:`
  > separado dos commits funcionais da fase, para não misturar higiene com
  > mudança de comportamento e manter o gate honesto (nenhum hook foi
  > desabilitado nem recebeu `exclude` para contornar a dívida).
- **Arquivos novos:** `.gitleaks.toml`.
  > **Escopo corrigido (2026-08-02).** O plano não previa arquivo de
  > configuração. Medido: as regras default do gitleaks retornam
  > `no leaks found` sobre um histórico que continha a credencial em 11 commits,
  > porque casam segredos com **forma** reconhecível (chaves de API com prefixo)
  > e a credencial era uma senha arbitrária. Com as 3 regras próprias, a mesma
  > varredura passou a acusar 30 achados. Sem o arquivo, a A.3 entregaria um
  > scanner que não detectaria o incidente que criou o Track A. Ver
  > `.codeflow/decisions/2026-08-02-regras-proprias-gitleaks.md` e OQ8.
- **Passos:**
  1. Adicionar o hook do `gitleaks` ao `.pre-commit-config.yaml`, que hoje tem
     apenas `ruff`, `ruff-format` e hooks genéricos.
  2. Adicionar um step de varredura de segredos ao job `backend` do `ci.yml`,
     bloqueante.
  3. Atualizar `SECURITY.md`, que hoje afirma "secrets e credenciais nunca são
     commitados" — a afirmação passa a ser verdadeira e verificada por ferramenta.
- **Testes (AC-3):** commit de arquivo com segredo sintético é rejeitado pelo hook;
  o mesmo conteúdo faz o job do CI falhar; `pre-commit run --all-files` verde no
  repositório limpo.
- **Escopo travado / violações BLOQUEANTES:** não adicionar segredo real como
  fixture de teste — usar valor sintético reconhecível. Não desabilitar o gate com
  allowlist ampla para fazer a suíte passar.
- **Critério de conclusão (gate):** AC-3 satisfeito; `pre-commit run --all-files`
  verde; CI verde.

### Track B — Esteira de qualidade e correções

### Fase B.1 — Testes unitários independentes de infraestrutura *(M)*

- **id:** `B.1`
- **slug:** `testes-unit-sem-infra`
- **Objetivo:** destravar o loop de desenvolvimento local — pré-requisito de todo o
  Track C.
- **Depende de:** nenhuma.
- **Arquivos alterados:** `backend/tests/conftest.py`, `backend/tests/unit/conftest.py`.
- **Passos:**
  1. Remover a chamada `asyncio.run(_reset_schema())` do corpo do módulo
     (`backend/tests/conftest.py:69`) e mover a criação de schema para dentro da
     fixture `setup_test_database`, que já existe logo abaixo e hoje só faz o
     teardown.
  2. Garantir que a fixture só seja solicitada por testes que precisam de banco.
     Preservar a intenção documentada em `conftest.py:64-68` — o schema deve existir
     antes de qualquer teste que use `clean_db`, e o teardown com `TRUNCATE` não pode
     falhar por schema ausente.
  3. Ajustar `backend/tests/unit/conftest.py:12-18`, cujo stub hoje não tem efeito
     porque a conexão acontecia no import do conftest pai.
- **Testes (AC-5):** com Postgres e Redis parados, `pytest tests/unit/` coleta e
  passa; com a infraestrutura no ar, `pytest` completo continua verde, incluindo
  `tests/integration/`.
- **Escopo travado / violações BLOQUEANTES:** não marcar testes de integração como
  `skip` para fazer a suíte passar. Não alterar nenhum teste existente para
  acomodar a mudança de fixture — se um teste quebrar, a fixture está errada. Não
  tocar em `backend/app/`.
- **Critério de conclusão (gate):** AC-5 satisfeito; `make test-unit` e
  `make test-integration` verdes; contagem de testes coletados inalterada
  (199 testes unitários, medidos antes e depois da mudança).

### Fase B.2 — Reativar CI com gates bloqueantes *(S)*

- **id:** `B.2`
- **slug:** `reativar-ci`
- **Objetivo:** voltar a impor a qualidade que já existe.
- **Depende de:** `B.1`.
- **Arquivos alterados:** `.github/workflows/ci.yml`, `.github/workflows/cd.yml`,
  `Makefile`, `README.md`, `backend/tests/smoke_test.py`.
  > **Escopo corrigido (2026-08-02).** Materialização do risco R3 ("reativar o CI
  > expõe falhas latentes"): com os gatilhos restaurados, 3 testes falharam, todos
  > em `backend/tests/smoke_test.py`. O arquivo é uma **sonda de ambiente** morando
  > dentro da árvore de testes automatizados — fala com a API real da Groq e tem
  > `DB_URL` hardcoded para `caloria_db`, o banco de **desenvolvimento**. Nunca
  > poderia passar no CI. Recebeu `pytestmark = pytest.mark.skipif` quando
  > `GROQ_API_KEY` não começa com `gsk_`, e skip em `InvalidCatalogNameError` no
  > teste de banco. **Nenhum gate foi afrouxado** e nenhum `continue-on-error` foi
  > adicionado. Ver `.codeflow/decisions/2026-08-02-smoke-test-como-sonda-de-ambiente.md`
  > e OQ9.
- **Passos:**
  1. Restaurar em `ci.yml` os gatilhos comentados em `:5-8` (`push` em `dev`,
     `pull_request` em `main`) e remover o `workflow_dispatch` isolado de `:9-10`
     junto com o comentário de desativação.
  2. Restaurar o gatilho de `cd.yml:7-8`. Se o Track E ainda não definiu a topologia,
     manter o CD em `workflow_dispatch` e registrar explicitamente no relatório que
     sua reativação é responsabilidade da Fase E.4 — não deixar ambiguidade.
  3. Corrigir `Makefile:290`, cujo alvo `check` afirma "Tudo OK — igual ao CI" mas
     roda apenas `test-unit`, enquanto o CI roda `pytest` completo. Ou incluir
     `test-integration`, ou corrigir a mensagem para não prometer equivalência falsa.
  4. Confirmar que o badge do README aponta para o workflow agora ativo.
- **Testes (AC-6):** push em `dev` dispara o CI; os dois jobs concluem verdes; uma
  violação deliberada de `ruff` faz o job falhar.
- **Escopo travado / violações BLOQUEANTES:** não relaxar nenhum gate para fazer o
  CI passar — `ruff` e `mypy` já passam limpos hoje, então uma falha indica
  regressão real e deve ser corrigida, não silenciada. Não adicionar
  `continue-on-error` a step de lint, typecheck ou teste.
- **Critério de conclusão (gate):** AC-6 satisfeito; execução verde visível no
  GitHub Actions.

### Fase B.3 — Fail-fast de SECRET_KEY e rate limiting *(M)*

- **id:** `B.3`
- **slug:** `hardening-config`
- **Objetivo:** fechar os dois buracos de segurança que não dependem do histórico.
- **Depende de:** `B.2`.
- **Arquivos alterados:** `backend/app/core/config.py`, `backend/app/main.py`,
  `backend/app/api/v1/auth.py`, `backend/app/api/v1/ai.py`, `backend/pyproject.toml`,
  `.env.example`.
- **Passos:**
  1. Adicionar `field_validator` em `SECRET_KEY` (`config.py:32`) que levante quando
     `APP_ENV` não for desenvolvimento e o valor for o default ou tiver menos de 32
     caracteres. Usar a property `is_development` (`config.py:86-88`), que hoje
     existe e não é usada para validar nada.
  2. Introduzir rate limiting nos endpoints públicos de `auth.py` (`login`,
     `forgot-password`, `register`) e nos endpoints de IA de `ai.py`, cujo custo é
     em tokens do provedor. Registrar limites em `config.py` como settings, não
     hardcoded.
  3. Adicionar um teto de itens a `POST /reminders/batch` (`reminders.py:34`), que
     hoje só rejeita lista vazia.
  4. Documentar as variáveis novas em `.env.example`.
- **Testes (AC-7, AC-8):** teste unitário do validador nos dois ramos; teste de
  integração que excede o limite de `login` e recebe 429; idem para
  `analyze-meal`; teste que o CI continua subindo a app com a `SECRET_KEY` de teste.
- **Escopo travado / violações BLOQUEANTES:** não quebrar o ambiente de
  desenvolvimento nem o CI — o `ci.yml:69` define uma `SECRET_KEY` de teste com 32+
  caracteres e deve continuar funcionando. Não alterar o algoritmo de assinatura nem
  nada em `backend/app/core/security.py`: é área de alto risco declarada na
  constitution do projeto. Não introduzir rate limiting em endpoints autenticados de
  leitura — **exceto** leitura que chama o provedor de IA (ver nota abaixo).
  > **Escopo corrigido (2026-08-02).** A restrição de leitura foi escrita sob a
  > premissa "GET autenticado = leitura barata de banco", que é falsa para os cinco
  > GET de `ai.py` (`suggest-meal`, `patterns`, `nutritional-alerts`,
  > `goal-adjustment`, `monthly-report`): todos passam por `_require_ai` e
  > `get_ai_client()`, com o mesmo custo em tokens do provedor que justifica o teto
  > nos três POST. Os cinco recebem `RATE_LIMIT_AI_LEITURA` (40/min, mais folgado que
  > o dos POST). `GET /ai/conversations` fica **de fora** por ser leitura pura de
  > banco, com teste travando esse desenho — o critério é "gasta token", não "é GET".
  > Ver `.codeflow/decisions/2026-08-02-rate-limit-em-get-de-ia.md` e OQ11.
- **Critério de conclusão (gate):** AC-7 e AC-8 satisfeitos; `make test-integration`
  verde; `mypy app/` limpo.

### Fase B.4 — Piso de cobertura e cobertura dos routers descobertos *(M)*

- **id:** `B.4`
- **slug:** `cobertura`
- **Objetivo:** transformar cobertura de métrica observada em gate.
- **Depende de:** `B.2`.
- **Arquivos novos:** `backend/tests/integration/test_push.py`,
  `backend/tests/integration/test_reminders.py`.
- **Arquivos alterados:** `backend/pyproject.toml`, `.github/workflows/ci.yml`.
- **Passos:**
  1. Medir a cobertura real atual com `make test-backend-cov` e registrar o número
     no relatório da fase. A auditoria de maio mediu 62%; o valor atual precisa ser
     remedido, não presumido.
  2. Escrever testes de integração para os 7 endpoints de `backend/app/api/v1/push.py`
     e os 5 de `backend/app/api/v1/reminders.py`, hoje com zero cobertura de
     integração. Incluir ao menos um caso de autorização cruzada (usuário A não
     acessa recurso de usuário B).
  3. Configurar `fail_under` em `[tool.coverage.report]` do `pyproject.toml`, com
     valor igual ao medido no passo 1 arredondado para baixo — piso, não meta.
  4. Remover o `continue-on-error: true` do upload de cobertura (`ci.yml:78`) apenas
     se o upload for confiável; caso contrário mantê-lo e aplicar o gate localmente
     via `--cov-fail-under`.
- **Testes (AC-9):** o CI falha quando a cobertura cai abaixo do piso; os novos
  testes cobrem cada endpoint dos dois routers.
- **Escopo travado / violações BLOQUEANTES:** não refatorar `push.py` para adequá-lo
  à camada de serviço — a inconsistência arquitetural é conhecida e fica fora desta
  spec; esta fase **cobre com teste**, não redesenha. Não inflar cobertura com testes
  que não asseguram comportamento. Não definir um piso acima do medido, o que
  quebraria o CI imediatamente.
- **Critério de conclusão (gate):** AC-9 satisfeito; CI verde com o gate ativo.

### Fase B.5 — Propagar a correção do bug 001 ao VisionParser *(M)*

- **id:** `B.5`
- **slug:** `vision-parser-bug001`
- **Objetivo:** corrigir o caminho de foto, que o eval expõe imediatamente.
- **Depende de:** `C.4`. *(Corrigido em 2026-08-03, achado B5-IMP-1: a fase
  declarava depender da `C.6`, mas o gate que ela se impõe — "delta do estrato
  de foto" — depende do dataset de foto, que nasce na `C.4`. O código da fase
  está pronto e aprovado; o que falta é o dataset. Decisão do owner: manter o
  gate como está e reabrir a B.5 depois da C.4.)*
- **Arquivos alterados:** `backend/app/services/ai/vision_parser.py`,
  `backend/app/prompts/vision_identify/` (nova versão),
  `backend/tests/unit/test_vision_parser.py`.
- **Passos:**
  1. Criar **nova versão** do prompt de visão removendo a regra 4 ("Liste cada
     alimento separadamente, mesmo em pratos compostos") e a regra 5 ("Estime porções
     sempre em gramas") de `vision_parser.py:22-67` — as duas regras que, no
     `MealParser`, foram a causa raiz do bug 001. Não editar a versão anterior:
     versão nova, pela regra de imutabilidade da C.7.
  2. Trocar `zip(..., strict=False)` por `strict=True` em `vision_parser.py:216` e
     `:240`, com laço que garanta uma saída por entrada — o `MealParser` já resolveu
     isso em `meal_parser.py:263`.
  3. Extrair o `0.35` inline de `vision_parser.py:157` para constante nomeada,
     alinhando com `_SANITY_DIVERGENCE` de `meal_parser.py:137`.
  4. Corrigir o fallback de `vision_parser.py:244-245`, que usa a quantidade crua da
     IA e levanta `ValidationError` fora dos blocos `except` quando a IA devolve
     valor por extenso, virando HTTP 500. Aplicar o guard `_num()` de
     `meal_parser.py:451-466` em `:246-251`.
  5. Rodar o eval do estrato de foto antes e depois, e registrar o delta.
- **Testes (AC-17):** teste de que nenhum item se perde quando a IA devolve array
  menor; teste de que quantidade por extenso não gera 500; snapshot do novo prompt;
  o estrato de foto do eval melhora ou, se não melhorar, o achado é registrado com
  os números.
- **Escopo travado / violações BLOQUEANTES:** não unificar `MealParser` e
  `VisionParser` — a duplicação de ~120 LOC entre eles é conhecida e a
  desduplicação fica fora desta spec. Não alterar o `MealParser`. Não alterar a
  tabela de calibração visual do prompt de visão, que é específica de foto e não
  tem relação com o bug 001. Não mexer nos limiares travados pela decision de
  2026-07-26.
- **Critério de conclusão (gate):** AC-17 satisfeito; delta do estrato de foto
  registrado no relatório com números antes e depois.

### Track C — Eval do pipeline de IA

### Fase C.1 — Registry de versionamento de prompt *(M)*

- **id:** `C.1`
- **slug:** `prompt-registry`
- **Objetivo:** dar identidade versionada e rastreável a cada prompt — pré-requisito
  de "resultado versionado junto do prompt".
- **Depende de:** `B.1`.
- **Arquivos novos:** `backend/app/prompts/__init__.py`,
  `backend/app/prompts/meal_identify/v1.txt`,
  `backend/app/prompts/meal_fallback/v1.txt`,
  `backend/app/prompts/vision_identify/v1.txt`,
  `backend/app/prompts/vision_fallback/v1.txt`,
  `backend/tests/unit/test_prompt_registry.py`.
- **Arquivos alterados:** `backend/app/services/ai/meal_parser.py`,
  `backend/app/services/ai/vision_parser.py`,
  `backend/app/services/ai/ai_client.py`.
- **Passos:**
  1. Criar um `PromptRegistry` que carregue templates de arquivo e exponha, para cada
     um, `name`, `version` e `sha256` do template bruto (não do renderizado, que varia
     por usuário). Resolver versão ativa quando não especificada.
  2. Extrair para arquivo, **sem alterar uma vírgula do texto**, os prompts hoje
     inline: `_IDENTIFY_SYSTEM_PROMPT` e `_FALLBACK_SYSTEM_PROMPT` de
     `meal_parser.py:61-133`, e os equivalentes de `vision_parser.py:22-97`. Os
     templates de user message (`_IDENTIFY_TEMPLATE`) acompanham.
  3. Fazer `AIClient` aceitar e registrar em log estruturado `prompt_name`,
     `prompt_version` e `prompt_sha` a cada chamada, ao lado do log de tokens que já
     existe em `ai_client.py:157-161`.
  4. Escrever um teste que trave o `sha256` de cada template ativo, de modo que
     editar o conteúdo sem bump de versão quebre a suíte.
- **Testes (AC-10):** o registry resolve nome e versão; o `sha` muda quando o
  conteúdo muda; os parsers continuam produzindo saída idêntica à anterior — provar
  com os testes existentes de `backend/tests/unit/test_meal_parser.py` e
  `test_meal_parser_bug001.py`, que devem passar sem alteração.
- **Escopo travado / violações BLOQUEANTES:** **não alterar o texto dos prompts nesta
  fase.** É uma extração pura; qualquer mudança de conteúdo invalidaria a comparação
  antes/depois do eval. Não introduzir engine de template com lógica: substituição de
  variáveis apenas. Não versionar os prompts do `InsightsGenerator` e do
  `PatternAnalyzer` nesta fase — ficam para depois, porque não entram no eval.
- **Critério de conclusão (gate):** AC-10 satisfeito; testes existentes dos parsers
  passam sem modificação; `mypy app/` limpo.

### Fase C.2 — Determinismo e robustez do AIClient *(M)*

- **id:** `C.2`
- **slug:** `determinismo-aiclient`
- **Objetivo:** tornar as chamadas reprodutíveis e a execução do eval capaz de
  terminar.
- **Depende de:** `C.1`.
- **Arquivos novos:** `backend/tests/unit/test_ai_client.py`.
- **Arquivos alterados:** `backend/app/services/ai/ai_client.py`,
  `backend/app/core/config.py`.
- **Passos:**
  1. Incluir o identificador do modelo na chave de cache (`ai_client.py:48` e
     `:180-182`), que hoje é `sha256` só de system e prompt. Sem isso, trocar
     `GROQ_TEXT_MODEL` serve até 7 dias de respostas do modelo anterior.
  2. Passar `response_format={"type": "json_object"}` nas chamadas cuja saída é JSON
     — o projeto já usa isso em `backend/scripts/enrich_foods.py:101`, então o padrão
     existe. Manter `extract_json_from_ai_response` como rede de segurança.
  3. Tornar explícitos `temperature`, `max_tokens` e `seed` (quando suportado),
     movendo-os para settings. Documentar por que o ramo sem `system` usa 0.3
     (`ai_client.py:154`) ou tornar a escolha explícita por chamada em vez de
     implícita pela presença de `system`.
  4. Trocar `if "429" in str(exc)` por captura de `groq.RateLimitError`, com teto de
     tempo total declarado. Considerar que o SDK já retenta 2× internamente com
     timeout de 60s por default, de modo que o backoff manual soma sobre isso.
  5. Definir `timeout` explícito ao instanciar `AsyncGroq` (`ai_client.py:34`).
- **Testes (AC-11):** chaves de cache distintas para modelos distintos; retry
  disparado por instância de `RateLimitError` e não por string; teto de tempo
  respeitado; teste de que o cache degrada silenciosamente com Redis fora, como já
  faz hoje.
- **Escopo travado / violações BLOQUEANTES:** não alterar o comportamento observável
  dos parsers — os testes de `test_meal_parser_bug001.py` devem continuar verdes sem
  modificação. Não remover o fallback de recorte de `utils.py:39-42`. Não mudar
  modelo default. Se o JSON mode alterar a forma da saída de algum prompt, **parar e
  reportar** em vez de ajustar o prompt (isso seria mudança de conteúdo, vedada na
  C.1 e materialmente relevante para o eval).
- **Critério de conclusão (gate):** AC-11 satisfeito; suíte de IA verde sem
  modificação nos testes existentes.

### Fase C.3 — Esqueleto do harness e schema do dataset *(M)*

- **id:** `C.3`
- **slug:** `harness-schema`
- **Objetivo:** criar a estrutura do eval e o contrato de caso, de forma agnóstica à
  fonte do ground truth (OQ2 aberta).
- **Depende de:** `C.1`.
- **Arquivos novos:** `backend/evals/__init__.py`, `backend/evals/schema.py`,
  `backend/evals/dataset/casos.jsonl` (com um punhado de casos-semente derivados de
  `GOLDEN`), `backend/evals/README.md`,
  `backend/tests/unit/test_evals_schema.py`.
- **Passos:**
  1. Definir o modelo Pydantic do caso: `id`, `estrato`
     (`simples` | `composto` | `foto`), `descricao`, `referencia_kcal`,
     `referencia_macros` (opcional), `fonte_referencia`, `fonte_url`,
     `grupo_invariancia` (opcional), `data_de_adicao`, `notas`.
  2. Validar no schema que `fonte_referencia` **nunca** seja a tabela `portions` do
     próprio projeto — a circularidade que o docstring de
     `backend/scripts/eval_golden_set.py:20-27` corretamente identifica.
  3. Semear o arquivo com um conjunto mínimo derivado do `GOLDEN` existente, marcado
     com fonte e limitação explícitas, suficiente para exercitar o runner.
  4. Escrever o `README.md` do harness com a seção de análise de poder: o efeito
     mínimo detectável do desenho pareado, e a declaração explícita do que o `n`
     adotado **não** consegue detectar.
- **Testes (AC-12):** todo caso do arquivo valida contra o schema; caso com fonte
  proibida é rejeitado; caso sem `fonte_url` é rejeitado.
- **Escopo travado / violações BLOQUEANTES:** **não decidir OQ2 nesta fase** — não
  escolher fonte de ground truth por conta própria. Não popular o dataset além do
  mínimo necessário para o runner funcionar. Não alterar
  `backend/scripts/eval_golden_set.py` nem
  `backend/tests/integration/test_golden_set.py`, que continuam sendo o gate
  determinístico e não são substituídos por este harness.
- **Critério de conclusão (gate):** AC-12 satisfeito; schema validado; README com a
  análise de poder escrita.

### Fase C.4 — Popular o dataset com ground truth externo *(L)*

- **id:** `C.4`
- **slug:** `dataset-ground-truth`
- **Objetivo:** preencher os três estratos com referências de fonte externa citável.
- **Depende de:** `C.3`. (OQ2 resolvida em 2026-08-02: IBGE POF + TACO.)
- **Arquivos alterados:** `backend/evals/dataset/casos.jsonl`,
  `backend/evals/README.md`.
- **Passos:**
  1. Usar a fonte decidida em OQ2: **IBGE POF 2011** para medida caseira →
     gramas e **TACO 4ª edição** para gramas → kcal/macros. Conferir os 10
     casos-semente da C.3 contra a publicação e virar `verificada: true`.
  2. Popular os três estratos conforme a decisão, registrando em cada caso a
     `fonte_referencia` e a `fonte_url` que permitem a um terceiro auditar o número.
  3. Documentar no README do harness as limitações da fonte escolhida, no padrão de
     honestidade que `backend/scripts/eval_golden_set.py:14-27` estabeleceu — o que a
     métrica mede e o que ela explicitamente não mede.
  4. Registrar `data_de_adicao` em cada caso, para permitir medir a idade do conjunto
     e aposentar casos obsoletos.
- **Testes (AC-12):** o dataset completo valida contra o schema; distribuição por
  estrato registrada no relatório; nenhuma referência derivada da tabela `portions`.
- **Escopo travado / violações BLOQUEANTES:** não inventar valores de referência.
  Não usar a saída de um LLM como ground truth. Não incluir caso cuja fonte não seja
  verificável por terceiro. Não incluir PII nem imagem de pessoa identificável no
  estrato de foto.
- **Critério de conclusão (gate):** OQ2 resolvida e registrada em §8; dataset
  completo validando; limitações documentadas.

### Fase C.5 — Runner e métricas *(L)*

- **id:** `C.5`
- **slug:** `runner-metricas`
- **Objetivo:** produzir o relatório estratificado que é a métrica headline do
  projeto.
- **Depende de:** `C.3`.
- **Arquivos novos:** `backend/evals/metrics.py`, `backend/evals/runner.py`,
  `backend/tests/unit/test_evals_metrics.py`.
- **Passos:**
  1. Implementar em `metrics.py` funções puras e testáveis: APE por item, MdAPE,
     SSPB, acurácia por tolerância, MAE, e IC95 por bootstrap. Funções puras são
     testáveis sem banco e sem IA — mesmo padrão de
     `backend/tests/unit/test_food_lookup_puro.py`.
  2. Implementar o runner que carrega o dataset, executa o pipeline real por caso,
     e agrega por estrato e no agregado. Reusar o padrão de monkeypatch de
     `backend/scripts/instrument_meal_pipeline.py:118` para capturar os estágios
     intermediários — identificação, score do lookup, alimento casado, sanity check.
  3. Aplicar a regra de reporte: kcal em MdAPE e SSPB; macros em MAE com tolerância
     absoluta, **nunca** em percentual.
  4. Emitir relatório legível em texto e estruturado em JSON.
- **Testes (AC-13):** métricas validadas contra valores calculados à mão em casos
  pequenos; a assimetria do APE demonstrada por teste (erro de 2× e de ½× dão o
  mesmo `|Q|` sob log accuracy ratio, mas MAPEs diferentes); relatório traz `n` e
  IC95 por estrato.
- **Escopo travado / violações BLOQUEANTES:** não usar MAPE como métrica headline —
  a justificativa está em §4 e é decisão travada. Não reportar percentual para
  macros em gramas. Não fazer o runner depender de rede nos testes unitários das
  funções de métrica. Não alterar os limiares travados em
  `backend/tests/integration/test_golden_set.py`.
- **Critério de conclusão (gate):** AC-13 satisfeito; `make test-unit` verde; uma
  execução manual do runner produz relatório com os três estratos.

### Fase C.6 — Bateria de invariância metamórfica *(M)*

- **id:** `C.6`
- **slug:** `invariancia`
- **Objetivo:** implementar o invariante de robustez que o owner identificou como o
  núcleo diferenciador.
- **Depende de:** `C.5`.
- **Arquivos novos:** `backend/evals/invariance.py`,
  `backend/evals/dataset/grupos_invariancia.jsonl`,
  `backend/tests/unit/test_evals_invariance.py`.
- **Passos:**
  1. Modelar as relações metamórficas como dados, não como código: paráfrase
     (mesma refeição, frases diferentes), escala (dobrar a porção deve dobrar kcal),
     ordem ("arroz e feijão" ≡ "feijão e arroz"), unidade ("500 g" ≡ "0,5 kg") e
     ruído (sufixo cortês não altera o resultado). Cada relação declara sua tolerância.
  2. Migrar os 7 pares de `backend/scripts/instrument_meal_pipeline.py:41-88` para o
     arquivo de grupos, **preservando a reprodução oficial do bug 001** como grupo de
     primeira classe — é o caso que dá a narrativa antes/depois.
  3. Calcular por grupo o `spread` (razão entre máximo e mínimo) e agregar em taxa de
     aprovação sob a tolerância, mais o percentil 95 do spread, que é o que revela o
     caso patológico.
  4. Incluir o teste de autoconsistência: mesma entrada repetida, medindo o
     coeficiente de variação — distinto de invariância, e o que mede
     não-determinismo puro do modelo.
- **Testes (AC-14):** cálculo de spread validado em casos sintéticos; o grupo do bug
  001 presente; o relatório traz taxa de aprovação e p95.
- **Escopo travado / violações BLOQUEANTES:** não afrouxar a tolerância para fazer a
  bateria passar — uma reprovação é um achado, não um defeito do teste. Não remover
  grupos que reprovam. Não usar a bateria como gate bloqueante de CI nesta fase (isso
  é decisão da C.6, e travar um gate sobre um comportamento ainda não caracterizado
  produziria flakiness).
- **Critério de conclusão (gate):** AC-14 satisfeito; execução manual produz
  relatório de invariância; achados de reprovação registrados no relatório da fase.

### Fase C.7 — Camada rápida com cassettes e execução agendada *(M)*

- **id:** `C.7`
- **slug:** `eval-ci`
- **Objetivo:** tornar o eval parte da esteira sem estourar quota nem tornar o PR
  lento.
- **Depende de:** `C.5`, `B.2`.
- **Arquivos novos:** `backend/evals/cassettes/` (gravações),
  `backend/tests/unit/test_evals_snapshot.py`,
  `.github/workflows/eval.yml`.
- **Arquivos alterados:** `.github/workflows/ci.yml`, `backend/pyproject.toml`.
- **Passos:**
  1. Adicionar gravação e replay de respostas do provedor, com o CI configurado para
     não gravar — o teste passa a falhar se e somente se o payload enviado mudar, que
     é exatamente a regressão de prompt que se quer pegar de graça.
  2. Adicionar snapshot do payload renderizado dos prompts, de modo que uma mudança
     apareça como diff legível no PR.
  3. Criar o workflow agendado que roda o eval completo contra o provedor real, com
     cache em disco e concorrência limitada, publica o relatório como artifact e
     falha se um limiar for rompido.
  4. Dimensionar a agenda ao rate limit real do free tier. A rodada de 2026-07-26
     morreu com `429` no terceiro caso; se a quota não comportar execução diária,
     usar periodicidade maior e registrar a decisão no README do harness.
- **Testes (AC-15):** a camada rápida roda sem rede e em menos de 60 segundos;
  alterar um prompt sem atualizar o snapshot faz o CI falhar; a camada completa
  conclui sem casos vazios além dos nominados no bug 003 (os três de foto, por
  HTTP 413 — ver a nota do AC-15 e a OQ21).
- **Escopo travado / violações BLOQUEANTES:** não gravar cassette contendo chave de
  API — sanitizar cabeçalhos antes de versionar. Não rodar o eval completo por PR.
  Não silenciar falha do workflow agendado com `continue-on-error`. Não versionar
  imagens de comida de terceiros sem verificar a licença.
- **Critério de conclusão (gate):** AC-15 e NFR-2 e NFR-3 satisfeitos; uma execução
  completa contra o provedor real registrada em `history.jsonl`. Duas cláusulas
  deste gate migraram, cada uma com destino nomeado: a de **plataforma** (o
  workflow registrado no GitHub) para o AC-19 / D.2, pela OQ20; a de **"sem casos
  vazios" sem qualificador** para o bug 003, pela OQ21.

### Fase C.8 — Série temporal versionada e relatório *(M)*

- **id:** `C.8`
- **slug:** `historico-eval`
- **Objetivo:** entregar o artefato que faz a narrativa funcionar — qualidade da IA
  como métrica de engenharia versionada junto do código.
- **Depende de:** `C.5`, `C.7`.
- **Arquivos novos:** `backend/evals/runs/history.jsonl`,
  `backend/evals/report.py`.
- **Arquivos alterados:** `backend/evals/runner.py`, `.github/workflows/eval.yml`.
- **Passos:**
  1. Fazer cada execução completa emitir uma linha em `history.jsonl` amarrando:
     `run_id`, `git_commit`, versões e `sha` de cada prompt, modelo e parâmetros de
     amostragem, `sha` do dataset e `n`, métricas por estrato e agregadas, custo em
     tokens e latência.
  2. Escrever o gerador de relatório que lê o histórico e produz a série temporal de
     MdAPE ao longo dos commits, anotada com o ponto em que cada versão de prompt
     entrou.
  3. Definir a regra de imutabilidade: um arquivo de versão de prompt não é editado
     depois de ter uma execução associada — mudança gera versão nova, mesmo contrato
     de uma migration Alembic. Registrar a regra no README do harness.
- **Testes (AC-16):** duas execuções em commits diferentes produzem duas linhas
  distintas e rastreáveis; o relatório é gerado a partir do histórico sem acesso à
  rede.
- **Escopo travado / violações BLOQUEANTES:** não reescrever linhas históricas —
  o arquivo é append-only. Não incluir chave de API, PII ou conteúdo de `.env` no
  registro. Não gerar gráfico que dependa de serviço externo.
- **Critério de conclusão (gate):** AC-16 satisfeito; histórico com ao menos duas
  execuções reais; relatório gerado.

### Track D — Vitrine e polimento

### Fase D.1 — Licença, metadados e sincronização de versão *(S)*

- **id:** `D.1`
- **slug:** `licenca-metadados`
- **Objetivo:** dar ao repositório os sinais mínimos de projeto sério.
- **Depende de:** `A.2`.
- **Arquivos novos:** `LICENSE`.
- **Arquivos alterados:** `README.md`, `backend/pyproject.toml`,
  `backend/app/main.py`, `frontend/package.json`, `CHANGELOG.md`.
- **Passos:**
  1. Adicionar `LICENSE` MIT (OQ4, resolvida) e ajustar a linha final do README, que
     hoje diz "Projeto pessoal. Todos os direitos reservados."
  2. Sincronizar a versão: CHANGELOG está em `0.7.0`, enquanto `pyproject.toml:7`,
     `main.py:36` e `frontend/package.json:3` estão em `0.1.0` — o Swagger público
     anuncia 0.1.0.
  3. **Ação do owner:** preencher description, topics e homepage do repositório no
     GitHub, hoje todos vazios.
- **Testes (AC-18):** a API do GitHub reporta description e topics preenchidos; o
  `LICENSE` MIT está versionado na branch de trabalho; a versão é a mesma nos quatro
  arquivos; `make check` verde. (A detecção de licença pela API migrou para o AC-19,
  que é da D.2 — ver OQ18.)
- **Escopo travado / violações BLOQUEANTES:** não alterar o histórico do CHANGELOG.
  Não escolher licença diferente de MIT sem nova decisão do owner.
- **Critério de conclusão (gate):** AC-18 satisfeito.

### Fase D.2 — Promover dev para main e publicar release *(S)*

- **id:** `D.2`
- **slug:** `release-v070`
- **Objetivo:** fazer a vitrine mostrar o projeto que existe.
- **Momento de execução:** *(decisão do owner, 2026-08-03 — OQ15)* **última operação de
  branch da spec.** A `main` não é tocada antes de os Tracks C, D e E concluírem, ainda
  que os impedimentos da fase já tenham caído. O conteúdo da fase não muda; muda quando
  ela roda.
- **Depende de:** `A.2`, `B.2`, `D.1`.
- **Arquivos alterados:** nenhum (operação de branch e release).
- **Passos:**
  1. Confirmar que o Track A concluiu — merge antes da purga do histórico seria
     desfeito pelo `filter-repo`.
  2. Abrir PR de `dev` para `main` e confirmar que o CI, agora ativo, passa.
  3. **Ação do owner:** revisar e mergear; configurar proteção da branch `main`
     exigindo os checks (pendência declarada no Roadmap 9.1).
  4. Criar tag anotada e publicar release com as notas derivadas do CHANGELOG.
  5. **Ação do owner:** tornar o repositório público novamente, se privado desde A.1.
- **Testes (AC-19):** `git log origin/dev ^origin/main` vazio; release visível;
  CI verde no merge.
- **Escopo travado / violações BLOQUEANTES:** não mergear com o CI vermelho. Não
  fazer force-push em `main`. Não mergear antes de A.2 concluída.
- **Critério de conclusão (gate):** AC-19 satisfeito; proteção de branch configurada.

### Fase D.3 — README como peça de portfólio *(M)*

- **id:** `D.3`
- **slug:** `readme-vitrine`
- **Objetivo:** contar a história técnica que hoje está enterrada no CHANGELOG.
- **Depende de:** `C.8`, `D.2`.
- **Arquivos alterados:** `README.md`, `docs/architecture.md`,
  `docs/fluxos/README.md`, `CONTRIBUTING.md`, `docs/git-workflow.md`,
  `Makefile`.
- **Passos:**
  1. Reescrever o README com: comando único (`make init`, hoje **não mencionado uma
     única vez** no README, no CONTRIBUTING ou no `docs/setup.md`), portas corretas
     (o README diz 3000/8000; o `docker-compose.dev.yml` usa 3010/8010), link da
     demo com credenciais de demonstração, screenshots, diagrama Mermaid inline e
     seção de decisões técnicas.
  2. A seção de decisões usa os números medidos e citáveis: a evolução de F1 do
     lookup, a queda de latência, a queda do erro calórico ao excluir `ai_estimated`,
     e o resultado do eval vindo de `evals/runs/history.jsonl`. Cada número com sua
     fonte.
  3. Converter os diagramas de `docs/fluxos/` de arquivos `.mermaid` soltos para
     blocos ```mermaid dentro dos `.md` — hoje `docs/fluxos/README.md` afirma que o
     GitHub os renderiza, o que não é verdade para arquivos `.mermaid` avulsos.
  4. Corrigir as afirmações falsas encontradas: `CONTRIBUTING.md:42` diz que os hooks
     rodam `ruff`, `mypy` e `eslint` quando só `ruff` está configurado;
     `docs/git-workflow.md` descreve proteção de branch e CI que só passam a existir
     em `B.2` e `D.2`; `Makefile:137` anuncia "Evol. API" no output de `make init`,
     um serviço removido há meses.
- **Testes (AC-20):** um leitor sem contexto executa o comando único e a aplicação
  sobe; os links resolvem; os diagramas renderizam no GitHub; nenhuma afirmação do
  README contradiz o estado do repositório.
- **Escopo travado / violações BLOQUEANTES:** não inventar métrica — todo número
  citado tem fonte verificável no repositório. Não prometer feature inexistente. Não
  reescrever o CHANGELOG histórico.
- **Critério de conclusão (gate):** AC-20 satisfeito; execução limpa a partir do
  README validada.

### Fase D.4 — Poda do repositório *(M)*

- **id:** `D.4`
- **slug:** `poda-repo`
- **Objetivo:** remover o que faz o projeto parecer telemetria de agente, sem
  quebrar o framework.
- **Depende de:** `D.2`.
- **Arquivos alterados:** `.gitignore`, `docs/auditoria/`, `.codeflow/`, `data/`,
  `docs/legacy/`.
- **Passos:**
  1. Remover do versionamento os 26 arquivos `FASE-*-EXECUCAO.md` e `-AVALIACAO.md`
     de `.codeflow/specs/001-*/`, os artefatos brutos de
     `.codeflow/bug-batches/artefatos/` e o dump de `bugs-teste-v1.origin.txt`.
  2. Adicionar `.codeflow/specs/*/artefatos/` e `.codeflow/bug-batches/artefatos/`
     ao `.gitignore`, para que as execuções futuras desta própria spec não
     reintroduzam o problema.
  3. Remover do versionamento os 51 dumps de `docs/auditoria/artefatos/`,
     preservando `docs/auditoria/relatorio-preliminar.md`, que é o documento de
     valor. Notar a inconsistência atual: `backend/artefatos/` já é ignorado
     (`.gitignore:134`) enquanto `docs/auditoria/artefatos/` é versionado, sendo a
     mesma natureza de conteúdo.
  4. Mover `data/db/dump_alimentos.dump` (1,7 MB binário) e
     `data/processed/alimentos_final.csv` (7,0 MB) para fora do git, disponibilizando
     como asset de release. Preservar `data/README.md`, que é bom, e **resolver a
     contradição** que ele carrega: diz 42.103 alimentos enquanto README,
     `CLAUDE.md` e `docs/architecture.md` dizem ~19.800.
  5. Remover `docs/legacy/analise.md`, que indexa 46 imagens em um diretório que
     está no `.gitignore:114`.
  6. **Preservar integralmente**, por restrição do owner: `.codeflow/INDEX.md`,
     `constitution.md`, `manifest.md`, `discovered.md`, `_TEMPLATES/`, `decisions/`,
     `bugs/`, `melhorias/`, `specs/INDEX.md` e os arquivos `SPEC_*.md`.
- **Testes (AC-21):** `git ls-files` não lista os artefatos removidos; os arquivos
  preservados continuam versionados; um workflow do framework (`/spec-status`) opera
  normalmente após a poda.
- **Escopo travado / violações BLOQUEANTES:** **não remover nada de que o framework
  `.codeflow` dependa para operar** — restrição explícita do owner. Não apagar
  `relatorio-preliminar.md`, `decisions/2026-07-26-limiares-lookup-nutricional.md`
  nem `bugs/001-fluxo-cadastro-refeicao.md`, que são as melhores evidências de
  método do projeto. Não reescrever histórico nesta fase.
- **Critério de conclusão (gate):** AC-21 satisfeito; framework operando após a poda.

### Fase D.5 — Metadados, favicon e OpenGraph *(S)*

- **id:** `D.5`
- **slug:** `metadata-og`
- **Objetivo:** fazer o link da aplicação parecer profissional quando compartilhado.
- **Depende de:** nenhuma.
- **Arquivos novos:** `frontend/app/favicon.ico`,
  `frontend/app/opengraph-image.tsx` (ou asset estático).
- **Arquivos alterados:** `frontend/app/layout.tsx`, `frontend/app/manifest.ts`.
- **Passos:**
  1. Adicionar favicon — hoje `frontend/public/` tem só `food/`, `icons/` e `sw.js`,
     e sem `app/favicon.ico` o navegador mostra o ícone genérico.
  2. Completar `frontend/app/layout.tsx:13-29` com `metadataBase` (cuja ausência gera
     warning no build e quebra URLs relativas), `openGraph` e `twitter`.
  3. Corrigir `frontend/app/manifest.ts:10-11`, cujos `theme_color` e
     `background_color` são de uma paleta anterior e não correspondem ao design
     system atual.
- **Testes (AC-22):** `npm run build` sem warning de `metadataBase`; validação de
  cartão OG; favicon servido.
- **Escopo travado / violações BLOQUEANTES:** não redesenhar o sistema visual. Não
  adicionar dependência para gerar a imagem OG se o recurso nativo do Next resolver.
- **Critério de conclusão (gate):** AC-22 satisfeito; `npm run build` limpo.

### Fase D.6 — FOUC, logs de produção e bugs de UI *(M)*

- **id:** `D.6`
- **slug:** `polimento-ui`
- **Objetivo:** eliminar os defeitos visíveis a quem avalia a aplicação rodando.
- **Depende de:** nenhuma.
- **Arquivos alterados:** `frontend/components/theme-provider.tsx`,
  `frontend/lib/api.ts`, `frontend/app/providers.tsx`,
  `frontend/app/(dashboard)/peso/page.tsx`,
  `frontend/app/(dashboard)/humor/page.tsx`,
  `frontend/app/(dashboard)/dashboard/page.tsx`,
  `frontend/components/dashboard/QuickAddModals.tsx`,
  `frontend/lib/hooks/useProfile.ts`, `frontend/lib/hooks/useReminders.ts`.
- **Passos:**
  1. Eliminar o FOUC do tema: `frontend/components/theme-provider.tsx:20-25` aplica o
     tema dentro de `useEffect`, após a hidratação, então quem tem tema escuro salvo
     vê um flash claro a cada carregamento. Resolver com script inline blocante ou
     migrando para `next-themes`, que já está no `package.json` e não é usado.
  2. Guardar atrás de `NODE_ENV` os logs de `frontend/lib/api.ts:63,88,97,113` e
     `frontend/app/providers.tsx:31,47,51` — hoje produzem uma linha por request,
     navegação e query em produção. O mesmo arquivo já guarda corretamente o
     ReactQueryDevtools em `providers.tsx:77`, então o padrão existe.
  3. Corrigir `frontend/app/(dashboard)/peso/page.tsx:270`, que renderiza a data sem
     o sufixo `+ "T12:00"` usado em todo o resto do código, exibindo o dia anterior
     em fuso negativo.
  4. Remover o toast duplicado de `frontend/app/(dashboard)/humor/page.tsx:107`, já
     emitido pelo hook em `useLogs.ts:137-139`.
  5. Passar `initialMode` de `frontend/app/(dashboard)/dashboard/page.tsx:332-358`
     para `QuickMealModal`, cujos três atalhos hoje abrem sempre em modo texto.
  6. Adicionar `onError` aos hooks de `useProfile.ts` e `useReminders.ts`, onde a
     falha hoje é silenciosa para o usuário.
- **Testes (AC-23):** teste de que a data renderizada confere; teste de que um único
  toast é emitido; teste de que o modal abre no modo solicitado; build de produção
  sem os logs.
- **Escopo travado / violações BLOQUEANTES:** não refatorar as páginas. Não extrair
  as duplicações conhecidas (`getLocalToday`, `fileToBase64`, `MEAL_LABELS`) — são
  dívida real mas ficam fora desta spec. Não trocar biblioteca de toast.
- **Critério de conclusão (gate):** AC-23 satisfeito; `make test-frontend`,
  `npm run lint` e `npx tsc --noEmit` verdes.

### Track E — Deploy

### Fase E.1 — Auditoria do que está publicado *(S)*

- **id:** `E.1`
- **slug:** `auditoria-deploy`
- **Objetivo:** substituir suposição por fato, já que a premissa é que os documentos
  de deploy não descrevem a realidade.
- **Depende de:** nenhuma.
- **Arquivos novos:** relatório da fase (em `artefatos/`, gerado pelo executor).
- **Passos:**
  1. Verificar o estado real do frontend publicado, com evidência de requisição.
  2. Verificar o estado real do backend: se responde, em que host, que versão,
     se `/health` está saudável, se as migrations estão aplicadas. O CD está
     desligado desde julho, então o estado é indeterminado até ser medido.
  3. Levantar o que existe de infraestrutura de fato provisionada, contra o que
     `docs/deploy.md` e o Roadmap 9.2 afirmam — o Roadmap marca todos os itens de
     deploy como pendentes, embora algo esteja no ar.
  4. Registrar as divergências encontradas.
- **Testes (AC-24):** relatório com evidência verificável para cada afirmação.
- **Escopo travado / violações BLOQUEANTES:** não alterar nada em produção nesta
  fase — é levantamento. Não expor segredo de produção no relatório. Não presumir
  o conteúdo de `docs/deploy.md` como verdadeiro.
- **Critério de conclusão (gate):** AC-24 satisfeito.

### Fase E.2 — Topologia decidida, ADR-009 e desambiguação dos composes *(M)*

- **id:** `E.2`
- **slug:** `topologia-adr009`
- **Objetivo:** eliminar a ambiguidade dos arquivos de orquestração e registrar a
  decisão.
- **Depende de:** `E.1`.
- **Arquivos alterados:** `docs/architecture.md`, `docker-compose.yml`,
  `Caddyfile`, `docker-compose.backend.yml`, `Caddyfile.backend`,
  `docs/deploy.md`, `docs/deploy-checklist.md`, `README.md`, `Roadmap.md`.
- **Passos:**
  1. Decidir a topologia com o owner a partir dos fatos de E.1.
  2. Escrever **ADR-009** em `docs/architecture.md`, que hoje vai de ADR-001 a
     ADR-008, registrando a topologia e o porquê.
  3. Desambiguar: hoje há três composes e dois Caddyfiles, e o par que roda em
     produção (`docker-compose.backend.yml` + `Caddyfile.backend`) é o único sem
     cabeçalho explicativo e sem menção no README, enquanto o par documentado é o
     que não roda. Renomear e/ou dar cabeçalho a cada arquivo declarando seu
     propósito.
  4. Consolidar `docs/deploy.md` e `docs/deploy-checklist.md`, que hoje se duplicam,
     e atualizar o Roadmap 9.2.
- **Testes (AC-25):** cada arquivo de orquestração declara seu propósito; ADR-009
  presente; `docker compose -f <cada arquivo> config` valida.
- **Escopo travado / violações BLOQUEANTES:** não deletar arquivo de orquestração
  que esteja em uso sem confirmar com o owner. Não alterar credencial nem variável
  de ambiente de produção. Não reescrever ADRs existentes.
- **Critério de conclusão (gate):** AC-25 satisfeito; owner confirmou a topologia.

### Fase E.3 — Conta de demonstração com dados semeados *(M)*

- **id:** `E.3`
- **slug:** `conta-demo`
- **Objetivo:** fazer o link da demo mostrar o produto, não uma tela de login vazia.
- **Depende de:** `E.2`.
- **Arquivos alterados:** `backend/scripts/seed_dev_user.py`, `README.md`,
  `Makefile`.
- **Passos:**
  1. Adaptar `backend/scripts/seed_dev_user.py`, que já gera 30 dias de refeições,
     peso, hidratação e humor, para semear uma conta de demonstração idempotente.
  2. Definir política de reset periódico da conta, para que a demo não degrade com
     uso de terceiros.
  3. Publicar as credenciais de demonstração no README. Elas são públicas por
     desenho e **não** podem coincidir com credencial real de nenhum serviço.
  4. Garantir que a conta de demonstração não tenha privilégio administrativo.
- **Testes (AC-26):** login com as credenciais publicadas exibe dashboard com dados
  nos quatro domínios; rodar o seed duas vezes não duplica dados.
- **Escopo travado / violações BLOQUEANTES:** não reusar nenhuma senha pessoal do
  owner — é literalmente o problema que o Track A existe para resolver. Não semear
  PII real. Não dar à conta de demonstração acesso a dados de outro usuário.
- **Critério de conclusão (gate):** AC-26 satisfeito.

### Fase E.4 — Novo deploy e CD automático *(M)*

- **id:** `E.4`
- **slug:** `deploy-cd`
- **Objetivo:** fechar o ciclo — merge em `main` volta a publicar sozinho.
- **Depende de:** `E.2`, `E.3`, `D.2`.
- **Arquivos alterados:** `.github/workflows/cd.yml`, `docs/deploy.md`.
- **Passos:**
  1. Executar o deploy conforme a topologia de E.2.
  2. Reativar o gatilho de `cd.yml:7-8`.
  3. Substituir o `sleep 10` de `cd.yml:38` por espera baseada em healthcheck — o
     `Makefile:324-331` já tem um `_wait-for-backend` com polling que serve de
     referência. Hoje, se o backend demorar mais que 10 segundos, o
     `alembic upgrade head` falha e o `set -e` aborta com o container já no ar.
  4. Adicionar ao CD a verificação de que o CI passou, e um caminho de rollback
     documentado.
  5. Atualizar `docs/deploy.md` para descrever o deploy real.
- **Testes (AC-27):** um merge em `main` dispara o CD, o deploy conclui e a
  aplicação responde saudável; uma falha simulada de migration não deixa o
  ambiente em estado inconsistente sem aviso.
- **Escopo travado / violações BLOQUEANTES:** não deployar com o CI vermelho. Não
  colocar segredo em arquivo versionado — usar secrets do GitHub. Não remover o
  `concurrency: production` de `cd.yml:11-13`.
- **Critério de conclusão (gate):** AC-27 satisfeito; deploy automático verificado
  ponta a ponta.

## 6. Riscos

| # | Risco | Prob. | Impacto | Mitigação |
|---|---|---|---|---|
| R1 | Force-push do `filter-repo` quebra clones locais, os 12 PRs do Dependabot e qualquer fork | Alta | Médio | Plano de reabertura documentado na A.2; janela combinada com o owner; execução manual, não pelo agente |
| R2 | A credencial permanece acessível por SHA em commits órfãos mesmo após force-push | Alta | Alto | A rotação da senha (A.1) é o controle primário e vem antes; solicitação de invalidação de cache ao GitHub Support na A.2 |
| R3 | Reativar o CI expõe falhas latentes e trava o fluxo | Baixa | Médio | `ruff` e `mypy` passam limpos hoje e a suíte é verde; qualquer falha é regressão real e deve ser corrigida, não silenciada |
| R4 | ~~OQ2 não é resolvida e o Track C fica pela metade~~ **MITIGADO** — OQ2 resolvida em 2026-08-02 (IBGE POF + TACO) | — | — | Risco encerrado; a C.4 está desbloqueada |
| R5 | O rate limit do free tier da Groq impede execuções completas do eval — já aconteceu em 2026-07-26 | Alta | Médio | Cache em disco, concorrência limitada, retry por classe com teto (C.2), e periodicidade ajustável na C.7 |
| R6 | Extrair prompts para arquivo altera comportamento sem querer | Média | Alto | A C.1 é extração pura com texto imutável; os testes existentes dos parsers devem passar **sem modificação**, e isso é o gate |
| R7 | Ativar JSON mode muda a forma da saída de algum prompt | Média | Médio | Escopo travado da C.2 manda **parar e reportar** em vez de ajustar o prompt, o que contaminaria a comparação do eval |
| R8 | A poda do `.codeflow/` quebra o framework | Baixa | Alto | Lista de preservação explícita na D.4, restrição do owner, e teste de que um workflow opera após a poda |
| R9 | Publicar credenciais de demonstração cria superfície de abuso | Média | Baixo | Conta sem privilégio, reset periódico, rate limiting já entregue na B.3 |
| R10 | A spec é grande (26 fases) e perde tracionamento | Média | Médio | Tracks independentes com dependências por `id`; A e B destravam valor cedo; C entrega incrementos executáveis |

## 7. Rollout

**Ordem obrigatória.** `A.1` → `A.2` antes de qualquer publicação, porque o
`filter-repo` reescreve todas as branches e desfaria um merge feito antes. `B.1`
antes de todo o Track C, porque sem loop de teste local o eval não tem onde ser
validado. `D.2` (merge e release) só depois de `A.2` e `B.2`. `E.4` por último.

**Paralelismo seguro.** `B.1`, `D.5`, `D.6` e `E.1` não têm dependências e podem
começar a qualquer momento. O Track C avança independentemente do Track D, exceto
por `D.3`, que precisa dos números de `C.8`.

**Janela de indisponibilidade.** O repositório fica privado entre `A.1` e `D.2`. Não
há indisponibilidade da aplicação, exceto a janela de `E.4`.

**Flags.** Nenhuma feature flag. O eval é aditivo: até a `C.7`, nada do harness
bloqueia o CI.

**Rollback.** Por fase: cada uma é um commit ou conjunto pequeno, revertível. As
exceções são `A.2` (reescrita de histórico — irreversível; o backup é um clone
espelho feito antes, e a fase deve exigi-lo) e `E.4` (rollback documentado como
passo da própria fase).

**Migrations.** Nenhuma fase desta spec cria ou altera migration. Se alguma se
revelar necessária, é violação de escopo — parar e reportar (NFR-7).

## 8. Open Questions

- **OQ1 — Poda de `.codeflow/` e `docs/auditoria/`.** **RESOLVIDO (2026-07-29).**
  Podar apenas os artefatos de execução (os 26 `FASE-*`, dumps brutos, JSON de
  baseline), preservando tudo de que o framework depende para operar. Justificativa:
  os artefatos de execução de agente induzem o leitor a concluir "gerado por IA"
  antes de olhar o código, enquanto `relatorio-preliminar.md`,
  `decisions/2026-07-26-limiares-lookup-nutricional.md` e
  `bugs/001-fluxo-cadastro-refeicao.md` são as melhores evidências de método do
  projeto. Restrição do owner: não mexer no que é essencial ao desenvolvimento.

- **OQ2 — Origem do ground truth do eval.** **RESOLVIDO (2026-08-02).**
  **Opção 2: IBGE POF + TACO**, duas fontes independentes entre si e
  independentes do projeto.

  - **Medida caseira → gramas:** IBGE, *Tabela de Medidas Referidas para os
    Alimentos Consumidos no Brasil* (POF 2008-2009, publicada em 2011).
  - **Gramas → kcal e macros:** TACO 4ª edição (NEPA/UNICAMP).

  Justificativa da escolha, contra as demais candidatas:

  1. **Pesagem em balança pelo owner** resolveria bem o estrato `simples` e
     **não** o `composto` — a balança dá massa, não composição, e um prato
     composto ainda exigiria tabela. Além disso não escala: cada caso novo
     custa uma refeição pesada.
  2. **IBGE POF + TACO** (escolhida) cobre os dois estratos, é citável por
     terceiro, é gratuita, é brasileira e **separa as duas fontes de erro**:
     a conversão de porção (IBGE) e a composição (TACO) podem ser auditadas
     de forma independente. Nenhuma das duas deriva da tabela `portions` do
     projeto, o que satisfaz a restrição de circularidade.
  3. **Rótulos de redes** ficam como fonte **complementar** para prato
     composto de receita padronizada, quando IBGE+TACO não cobrir o item.
  4. **Datasets públicos anotados** para o estrato `foto` seguem pendentes de
     verificação de licença — a C.4 decide caso a caso.
  5. **Benchmark público** foi descartado: os disponíveis não cobrem o Brasil,
     que é o domínio inteiro deste projeto.

  **Limitação que a C.4 deve documentar no README do harness:** a TACO mede
  alimentos preparados em condição padronizada de laboratório, e a POF reporta
  medidas *referidas* por entrevistados — nenhuma das duas descreve a refeição
  específica de um usuário. A métrica mede o pipeline contra uma referência
  populacional, não contra a verdade de um prato individual. Isso é o teto de
  precisão do eval e precisa ficar dito.

  **Consequência para a C.4:** desbloqueada. Os 10 casos-semente da C.3
  (`verificada: false`) devem ser conferidos contra a publicação da TACO e ter
  a porção reancorada na POF, virando `verificada: true`; os demais casos são
  adicionados até `n ≈ 40`, distribuídos entre `simples` e `composto`.

- **OQ3 — Stack do harness.** **RESOLVIDO (2026-07-29).** `pytest` com scripts
  próprios, estendendo `eval_golden_set.py` e `instrument_meal_pipeline.py`.
  Justificativa: zero dependência nova, integra no CI já escrito, e o repositório já
  demonstra o padrão em `test_golden_set.py`. Alternativas rejeitadas: um framework
  de eval dedicado (abstração nova a aprender, ganho marginal na escala do projeto) e
  uma plataforma SaaS (contradiz a natureza self-hosted e tem custo recorrente).

- **OQ4 — Licença.** **RESOLVIDO (2026-07-29).** MIT.

- **OQ5 — Demo pública.** **RESOLVIDO (2026-07-29).** Conta de demonstração com dados
  semeados; exige novo deploy (Track E). Domínio custom não decidido — não bloqueia
  nenhuma fase.

- **OQ6 — Topologia de deploy.** **RESOLVIDO quanto ao método (2026-07-29):**
  replanejar do zero, auditando o que está no ar antes de documentar, porque a
  premissa do owner é que os documentos estão desatualizados. A topologia em si é
  decidida na Fase E.2, com os fatos de E.1 em mãos.

- **OQ7 — Extensão da redação de PII/comando de extração além dos 2 documentos
  declarados na A.2.** **RESOLVIDO (2026-08-02).** Estender a reescrita a 10
  arquivos (os 2 declarados + `runbook.md`, `07-seguranca.md`,
  `artefatos/G1-creds.txt`, `plano.md`, `plano-correcao.md`,
  `relatorio-preliminar.md`, `08-testes.md` e `docs/legacy/analise.md`).
  Justificativa: a credencial e o comando de extração viviam nos 8 arquivos extras
  também, e `runbook.md` e `07-seguranca.md` **ainda publicavam o comando de
  extração** — limitar-se aos 2 declarados deixaria o mapa de extração publicado e
  esvaziaria o FR-A2. Extensão reportada ao owner e autorizada antes da execução.
  Ver `.codeflow/decisions/2026-08-02-extensao-escopo-redacao-pii-auditoria.md`.

- **OQ8 — Regras próprias de detecção no gitleaks (`.gitleaks.toml`), não previstas
  na A.3.** **RESOLVIDO (2026-08-02).** Adicionar `.gitleaks.toml` com
  `useDefault = true` mais 3 regras próprias (`caloria-senha-hardcoded`,
  `caloria-senha-preenchida-em-teste`, `caloria-email-pessoal`), que casam o
  **padrão** — atribuição de senha, `.fill()` de senha em teste de UI, e-mail de
  provedor de consumo — e nunca o valor concreto. Justificativa mensurável: as
  regras default retornavam
  `no leaks found` sobre um histórico que continha a credencial em **11 commits**,
  porque casam segredos por forma reconhecível de chave de API, e a credencial era
  uma senha arbitrária; com as regras próprias a mesma varredura passou a acusar
  **30 achados**. Sem o arquivo, a A.3 entregaria um scanner incapaz de detectar o
  incidente que criou o Track A. Consequência no gate: o AC-2 foi reescrito para
  exigir `--config .gitleaks.toml` e uma verificação literal por `git log -S`.
  Ver `.codeflow/decisions/2026-08-02-regras-proprias-gitleaks.md`.

- **OQ9 — `backend/tests/smoke_test.py` falhando ao reativar o CI.**
  **RESOLVIDO (2026-08-02).** Marcar os testes com
  `pytestmark = pytest.mark.skipif` quando `GROQ_API_KEY` não começa com `gsk_`, e
  skip em `InvalidCatalogNameError` no teste de banco — em vez de excluir o arquivo
  da suíte ou afrouxar o gate. Justificativa: é a materialização do risco R3; o
  arquivo é uma **sonda de ambiente** (fala com a API real da Groq, `DB_URL`
  hardcoded para `caloria_db`, o banco de desenvolvimento) morando dentro da árvore
  de testes automatizados — nunca poderia passar no CI. Nenhum gate de `ruff`,
  `mypy`, `pytest` ou `npm run lint` foi relaxado e nenhum `continue-on-error` foi
  introduzido. Débito registrado: mover a sonda para fora de `tests/`.
  Ver `.codeflow/decisions/2026-08-02-smoke-test-como-sonda-de-ambiente.md`.

- **OQ10 — Ticket ao GitHub Support para invalidação do cache de commits órfãos
  (passo 3 da A.2).** **RESOLVIDO (2026-08-02).** Omitir o ticket, por decisão do
  owner. Fundamentação verificada no momento da decisão: `forks: 0` e `network: 0`
  (não há rede de forks que mantenha os objetos alcançáveis), `visibility: private`
  (acesso anônimo por SHA retorna 404), senha já rotacionada nos serviços de reuso
  (credencial morta) e e-mail remanescente declarado não sensível pelo owner.
  **Risco residual acordado:** na Fase D.2 o repositório volta a ser público, e
  commits órfãos em cache podem voltar a ser alcançáveis por SHA. Mitigação
  combinada: deixar passar alguns dias entre a purga e a reabertura — prazo que as
  dependências da D.2 consomem naturalmente.
  Ver `.codeflow/decisions/2026-08-02-omissao-ticket-github-support.md`.

- **OQ11 — Rate limiting nos cinco GET de IA, que o escopo travado da B.3 declarava
  violação BLOQUEANTE.** **RESOLVIDO (2026-08-02).** Manter o teto nos cinco GET que
  chamam o provedor (`suggest-meal`, `patterns`, `nutritional-alerts`,
  `goal-adjustment`, `monthly-report`), com setting própria `RATE_LIMIT_AI_LEITURA`
  (40/min), e manter `GET /ai/conversations` sem teto. Justificativa: a restrição
  original supõe que leitura autenticada é consulta barata de banco; os cinco
  dependem de `_require_ai` e `get_ai_client()` e têm o mesmo custo em tokens que
  justifica o teto nos três POST — enquanto `GET /ai/conversations`, que é leitura
  pura de banco, ficou de fora, o que evidencia que o critério aplicado é "gasta
  token do provedor", não "é método GET". O teto mais folgado vem de
  `frontend/app/(dashboard)/insights/page.tsx:72-76`, que dispara quatro dessas
  consultas por carga da página. Débito registrado: a chave de contagem é por IP;
  `user_id` seria a chave natural nos endpoints autenticados.
  Ver `.codeflow/decisions/2026-08-02-rate-limit-em-get-de-ia.md`.

- **OQ12 — Passo 2 da C.2 (JSON mode), não entregue por incompatibilidade de formato.**
  **RESOLVIDO (2026-08-03).** Implementar agora, por decisão do owner, em três partes:
  versões novas dos quatro prompts com topo em objeto (`meal_identify@v2`,
  `meal_fallback@v2`, `vision_identify@v3`, `vision_fallback@v2`, delta restrito ao
  bloco FORMATO e verificado por teste); `response_format` amarrado à versão do prompt
  via `PromptVersion.topo_objeto`, nunca a uma flag solta; e **produção fixada nas
  versões já medidas** por `VERSOES_EM_PRODUCAO`, de modo que `get_prompt` deixa de
  resolver pela maior versão do disco. Justificativa: promover no mesmo passo trocaria
  o prompt sem medição e invalidaria os 14 cassettes, deixando o harness do Track C
  inutilizável até haver quota. FR-C2 fica completo no código; o que falta é uma
  execução comparando v1 e v2, bloqueada pelo risco R5.
  Ver `.codeflow/decisions/2026-08-03-json-mode-com-versoes-de-prompt-em-objeto.md`.

- **OQ13 — Fase A.1 no teto do §2.11.4 (3 vereditos não-APROVADO).**
  **RESOLVIDO (2026-08-03).** O owner aceitou a fase e a encerrou, em vez de gastar
  uma quarta tentativa. Fundamentação: os dois achados IMPORTANTES eram de artefato
  (§9 do relatório contradizendo a §1/§8, e a decision da fase contradizendo o próprio
  cabeçalho), ambos corrigidos nesta data, e o trabalho técnico já fora verificado por
  medição independente na tentativa 3. No mesmo ato o owner **levantou o portão sobre
  a Fase D.2** que a decision mantinha: a premissa que o sustentava — "se o backend
  estiver no ar, a conta aceita a senha vazada" — foi medida e é falsa. Seguem valendo
  a mitigação da OQ10 e a proibição da E.3 de reusar a senha vazada.
  Ver `.codeflow/decisions/2026-08-02-senha-conta-caloria-producao.md`, seção
  "Estado final".

- **OQ14 — Regras de porção alteradas fora do conjunto declarado de arquivos.**
  **RESOLVIDO (2026-08-03).** A correção de `backend/scripts/seed_portions.py`
  (13 entradas novas para gordura de passar e acompanhamentos) nasceu do achado
  `inv-04` da C.6 e tocou arquivo que não consta dos "Arquivos alterados" de nenhuma
  fase. Registrada como decision, sem reversão: a regra genérica de 100 g para
  "porção de manteiga" é o defeito, e `portions` é o lugar certo de corrigi-lo.
  Ver `.codeflow/decisions/2026-08-03-regras-de-porcao-para-gordura-de-passar.md`.

- **OQ15 — Momento da promoção `dev` → `main` (Fase D.2).**
  **RESOLVIDO (2026-08-03).** A `main` **não é tocada em momento nenhum** antes do fim
  da spec: a D.2 sai da posição declarada na §5 e passa a ser a última operação de
  branch do projeto, depois de os Tracks C, D e E concluírem. O conteúdo da fase não
  muda — muda quando ela roda. Justificativa: a `main` é o branch que o mundo vê, e
  promover cedo publicaria um estado intermediário (Track C em rework, README ainda
  não reescrito na D.3, repositório ainda não podado na D.4, deploy indeterminado).
  **Consequência aceita:** D.3, D.4 e E.4 esperam junto, o que é coerente com a
  dependência que já declaravam.
  > **Duas consequências desta OQ foram corrigidas depois (2026-08-04).**
  > **(a)** "A D.1 não fecha até lá, porque `licenseInfo` só é detectado a partir do
  > branch default" **deixou de valer** com a OQ18, que migrou essa cláusula para o
  > AC-19 (D.2). A D.1 fecha pelo que ela controla.
  > **(b)** "Nada em B.4 ou C.7 depende disto — os dois rodam sobre `dev`" é
  > **factualmente falso** para a C.7, e foi medido: o GitHub só registra workflow de
  > `schedule`/`workflow_dispatch` a partir do **branch default**, então
  > `gh workflow run eval.yml --ref dev` devolve `HTTP 404` mesmo com o arquivo
  > presente em `origin/dev`. O gate "execução agendada registrada" da C.7 depende da
  > D.2 pelo mesmo mecanismo que o AC-18 dependia. Ver OQ20.
  Ver `.codeflow/decisions/2026-08-03-promocao-da-main-fica-para-o-fim-da-spec.md`.

- **OQ16 — Topologia de deploy (passo 1 da E.2, e pendência aberta desde a OQ6).**
  **RESOLVIDO (2026-08-03).** **Host único, self-hosted:** `docker-compose.yml` +
  `Caddyfile`, com Postgres, Redis, backend, frontend, workers e proxy no mesmo lugar.
  Decisão do owner com duas condições temporais: **agora roda localmente** — não há
  servidor contratado e a E.4 fica adiada por decisão, não por impedimento — e **no
  futuro a mesma stack sobe numa VPS**, sem mudança de topologia. O par
  `docker-compose.backend.yml` + `Caddyfile.backend` (topologia dividida, com frontend
  na Vercel, que foi a que de fato rodou até o servidor sair do ar) vira **legado
  declarado no cabeçalho**, sem uso, marcado para remoção na poda da D.4.
  **Consequência registrada:** o deploy do frontend na Vercel fica órfão — continua no
  ar apontando para uma API inexistente —, e retirá-lo ou reapontá-lo é ação do owner,
  anotada como pendência da E.4.
  Ver `docs/architecture.md` (ADR-009).

- **OQ17 — Fontes e arquivos da C.4 além do par declarado na OQ2.**
  **RESOLVIDO (2026-08-03).** Três extensões, todas medidas antes de decidir:
  **(a)** onde a TACO não cobre o item, a composição vem das *Tabelas de
  Composição Nutricional dos Alimentos Consumidos no Brasil* (IBGE, POF
  2008-2009) — publicação irmã da tabela de medidas já adotada, do mesmo
  instituto. Entra em 2 dos 43 casos: pizza de calabresa (a TACO **não tem**
  pizza, e a reprodução do bug 001 depende dela) e leite integral (a linha da
  TACO vem sem valores, só `*`). Precedência fixa e declarada — TACO onde a TACO
  cobre —, porque as duas fontes discordam onde ambas cobrem (feijoada: 117
  kcal/100 g na TACO, 181,59 na POF). **(b)** Três imagens versionadas em
  `backend/evals/dataset/imagens/`, do Wikimedia Commons, licença conferida pela
  API antes de baixar e atribuída no README, sem pessoa identificável: sem elas o
  estrato `foto` nasceria vazio e a B.5 seguiria bloqueada, contra a
  redependência decidida em 2026-08-03. **(c)** Quatro asserções de
  `tests/unit/test_evals_schema.py` e `test_evals_metrics.py` que travavam o
  estado de semente ("nenhum caso conferido", "estrato `foto` vazio") passaram a
  afirmar o estado pós-C.4; as duas que provavam a renderização de estrato vazio
  seguem provando, sobre dataset sintético. **Consequência registrada:** o runner
  de texto passa de 10 para 40 casos executáveis (~4× de quota na camada
  agendada, pressão direta no risco R5), e os 14 cassettes da C.7 não cobrem as
  descrições novas até a próxima gravação.
  Ver `.codeflow/decisions/2026-08-03-dataset-c4-fontes-e-arquivos-alem-do-declarado.md`.

- **OQ18 — AC-18 exigia da D.1 um efeito que só a D.2 produz.**
  **RESOLVIDO (2026-08-03).** A cláusula "licença MIT **detectada** pela API"
  migrou do AC-18 para o **AC-19**. Medido: `licenseInfo: null`, porque o GitHub
  deriva a licença do **branch default** e a `main` parou em 2026-04-29 — o
  `LICENSE` está criado e correto na `dev`. Até a OQ15 isso era espera curta; com
  a D.2 movida para o fim da spec, virou uma cláusula que a D.1 não pode fechar,
  consumindo tentativas do teto do §2.11.4 por um motivo que não é defeito de
  execução. O AC-18 fica com o que a D.1 controla (description, topics, `LICENSE`
  versionado, versão sincronizada) e o AC-19 ganha a verificação de
  `licenseInfo`. **Mesmo defeito de modelagem já corrigido na A.1**, quando a
  cláusula do HEAD remoto migrou do AC-1 para o AC-2. A alternativa recomendada
  pelo avaliador — executar a D.2 agora — foi descartada por contrariar a OQ15,
  que é decisão de owner vigente.
  Ver `.codeflow/decisions/2026-08-03-licenca-detectada-migra-do-ac18-para-o-ac19.md`.

- **OQ19 — Caminho de foto no runner e teto de tokens da visão (rework da B.5).**
  **RESOLVIDO (2026-08-04).** Duas coisas, medidas antes de decidir:
  **(a)** o estrato de foto passa a ser executado por `backend/evals/runner.py`,
  arquivo que não consta dos "Arquivos alterados" da B.5 — mas cuja própria
  linha de exclusão (`# o caminho de foto entra na fase B.5`) já atribuía o
  trabalho a esta fase. Entra também `backend/tests/unit/test_evals_runner_foto.py`.
  Sem isso o gate da fase ("delta do estrato de foto, antes e depois") continua
  sem instrumento, mesmo com o dataset da C.4 pronto. **(b)** Na configuração de
  produção os três casos de foto falham com **HTTP 413** (`Requested 11357` >
  `TPM 8000`), com o **mesmo** número para imagens de 111 KB, 200 KB e 291 KB —
  o que estoura o limite é o `max_tokens` reservado (`GROQ_MAX_TOKENS = 8192`,
  da C.2), não o tamanho da foto. Como nem o frontend nem o backend
  redimensionam a imagem, **a análise por foto está quebrada em produção no free
  tier**. O achado fica **registrado, não corrigido**: o fix é em `config.py`/
  `ai_client.py` (C.2) e no frontend, fora do escopo travado da B.5, que proíbe
  ampliar a fase. **Consequência registrada:** as quatro execuções do delta
  rodaram com `GROQ_MAX_TOKENS=2048`, declarado no campo `amostragem` de cada
  relatório; o delta v1→v2 é válido (mesmo teto dos dois lados), mas nenhum
  número do estrato de foto vale como linha de base **de produção** enquanto o
  413 existir — a ressalva acompanha o número na D.3 e no histórico da C.8.
  Ver `.codeflow/decisions/2026-08-04-estrato-de-foto-no-runner-e-teto-de-tokens-da-visao.md`.

- **OQ20 — O gate "execução agendada registrada" da C.7 depende da D.2, e o limite
  que morde é o diário.** **RESOLVIDO (2026-08-04).** Dois fatos, medidos:
  **(a)** O `eval.yml` **está** em `origin/dev` e o secret `GROQ_API_KEY` **existe**
  desde 2026-08-03 17:42Z — os dois impedimentos que a avaliação da tentativa 2
  nomeou caíram. Ainda assim `gh workflow run eval.yml --ref dev` devolve
  **`HTTP 404`**: o GitHub só registra workflow de `schedule`/`workflow_dispatch`
  a partir do **branch default**, e a `main` está 255 commits atrás sem o arquivo.
  É o **mesmo defeito de modelagem** do AC-18 (OQ18) e do AC-1 (A.1), numa terceira
  fase: um gate que depende de um efeito que só a D.2 produz. Como a OQ15 é decisão
  de owner vigente, a cláusula **de plataforma** do gate migra para a **D.2**, e a
  C.7 fecha pela evidência substantiva, que é local e não depende do GitHub: a
  execução completa contra o provedor real, sem casos vazios por quota, com a
  agenda dimensionada pelo consumo medido. *(Retificação de 2026-08-08: o
  qualificador "por quota" aparecia aqui sem base no AC-15, que exigia "sem casos
  vazios" sem qualificador algum. A **OQ21** deu destino à cláusula e alinhou a
  redação de §3, §5 e §9 — só a partir dela este parágrafo é coerente com o AC.)*
  **(b)** Executado o `eval.yml` local, passo a passo: **43 casos, 57 chamadas,
  42.932 tokens, 4min40s de parede, zero 429 no runner**. O gate
  (`evals.report verificar`) **reprovou com exit 1**, e corretamente — 3 casos
  vazios (os de foto, pelo HTTP 413 da OQ19), MdAPE 33,33% acima do teto de 25% e
  23% dentro de ±10% contra o piso de 50%. Em seguida a **bateria de invariância
  morreu com 429 de `tokens per day`: limite 100.000, usados 99.768.** O limite
  que morde no free tier é o **diário**, não o por-minuto, e uma rodada completa
  (runner + invariância) **não cabe** num dia junto de qualquer outro uso. Isso
  confirma a periodicidade **semanal** do `eval.yml` com número, e não por palpite
  — que é o que o passo 4 da fase pede.
  **Consequência registrada:** enquanto o 413 da OQ19 não for resolvido
  (rastreado no **bug 003** desde a OQ21), toda execução agendada vai reprovar por
  3 casos vazios. Os limiares de
  `evals/report.py` (`MDAPE_MAXIMO = 25.0`, `FRACAO_MINIMA_DENTRO_DE_10PCT = 0.50`)
  foram calibrados sobre o dataset de 10 casos-semente; com os 43 da C.4 eles
  reprovam a linha de base real. Recalibrar é decisão de owner com o número na
  mão, não ajuste de conveniência — e **não** foi feito nesta fase.

- **OQ21 — A cláusula "sem casos vazios" saiu do gate da C.7 sem destino, e o
  teto da C.7 foi destravado pelo owner.** **RESOLVIDO (2026-08-08).** Duas
  decisões de owner, tomadas juntas porque a segunda só existe por causa da
  primeira.
  **(a) A cláusula.** A tentativa 3 reescreveu a linha da C.7 na §9 e derrubou
  **duas** cláusulas de uma vez. A de plataforma migrou para o AC-19 com
  argumento medido (OQ20) — legítimo. A de **"sem casos vazios"** não migrou para
  lugar nenhum, enquanto o AC-15 seguia exigindo-a: a spec passou a pedir e não
  pedir a mesma coisa, que é o defeito que a D.1 levou quatro tentativas para
  eliminar (`C7-BLQ-1`). A cláusula agora tem **destino nomeado**: o **bug 003**
  (`.codeflow/bugs/003-http-413-no-estrato-de-foto.md`), que é quem corrige o HTTP
  413 da OQ19. Ela não some da spec — muda de dono, como em OQ18. O AC-15 passa a
  admitir os três vazios de foto como exceção **nominada** (lista fechada de três
  `id`s); qualquer vazio fora dessa lista segue reprovando. §3, §5 e §9 foram
  alinhados na mesma redação.
  **Por que um bug e não uma fase:** o fix é em `config.py`/`ai_client.py` (escopo
  da C.2, já concluída) e no frontend, o Track C está fechado em 8 fases
  (ARTIFACTS_SPEC §2.8.6, regra 3), e criar fase é trabalho de `/create-spec`, não
  de execução. O registro de bugs é o artefato vivo do projeto onde a cláusula não
  se perde.
  **(b) O teto.** A avaliação da tentativa 3 (REPROVADO, score 8.9) fechou o
  terceiro veredito não-APROVADO e a C.7 entrou no estado terminal do §2.11.4. O
  owner autorizou a quarta tentativa em 2026-08-08. É a segunda vez nesta spec
  (D.1, OQ13/A.1), e vale o mesmo limite: se a quarta avaliação não aprovar, não
  há autorização implícita para uma quinta.
  Ver `.codeflow/decisions/2026-08-08-clausula-sem-casos-vazios-migra-da-c7-para-o-bug-003.md`
  e `.codeflow/decisions/2026-08-08-quarta-tentativa-da-c7-autorizada-no-teto.md`.

- **OQ22 — As três decisões de escopo da Fase D.2, que viviam só num artefato que a
  D.4 apaga.** **RESOLVIDO (2026-08-09).** A D.2 tomou três decisões que o item
  global da DoD manda registrar aqui ou numa decision, e nenhuma tinha ido para
  lugar nenhum: elas existiam apenas no `FASE-D.2-release-v070-EXECUCAO.md`, que é
  exatamente o tipo de arquivo que o **AC-21 manda a D.4 remover do
  versionamento**. O achado é da avaliação da tentativa 1 (IMP-1). O que motiva o
  registro não é forma: a tag `v0.7.0` é pública e permanente, e a explicação dela
  desapareceria na poda. `gera_decision: no` impede o executor de criar decision,
  não de abrir OQ — caminho já usado pela B.5 (OQ19) e pela C.7 (OQ21).

  **(a) A tag `v0.7.0` cobre mais do que a entrada de 0.7.0 do CHANGELOG promete.**
  Ela aponta para `defe1dc`, que contém tanto `## [0.7.0] - 2026-05-10` (a migração
  para Groq) quanto **toda a seção `[Não lançado]`** — as 22 fases desta spec. A
  alternativa era cortar `v0.8.0`, e o custo foi apresentado ao owner antes da
  escolha: editar o `CHANGELOG.md` e os quatro arquivos de versão, o que contraria
  o `Arquivos alterados: nenhum` da própria §5 da D.2 e desfaz a sincronização em
  `0.7.0` que a **D.1 acabara de fazer e que o AC-18 cobra**. Decisão do owner:
  manter `v0.7.0`. **Mitigação aplicada e verificável:** as notas do release trazem
  seção própria — *"Também incluído nesta tag (seção [Não lançado] do CHANGELOG)"* —
  declarando o conteúdo extra item a item, de modo que o leitor da release não
  precisa do artefato de execução para entender o que a tag carrega. **Consequência
  registrada:** o próximo corte de versão deve ser `v0.8.0` com o CHANGELOG
  fechando `[Não lançado]`, e a `v0.7.0` fica com a semântica de *"primeira tag
  publicada do projeto"*, não de *"conteúdo da entrada 0.7.0"*.

  **(b) Os passos 3 e 5 da D.2 estão marcados "Ação do owner" e foram executados
  pelo agente.** Merge do PR #27, configuração da proteção de branch e virada para
  público. Autorização perguntada e dada explicitamente antes de cada ato; o owner
  revisou o PR pela descrição e pelo CI verde. A leitura adotada é **funcional** —
  "ação do owner" designa de quem é a *decisão*, não de quem são as mãos —, e ela
  vale para esta spec inteira daqui em diante, incluindo o que restar de ação do
  owner na D.3, D.4 e E.4. **Salvaguarda que acompanha a leitura:** o ato
  irreversível (privado → público) foi precedido de varredura de segredos sobre
  todo o histórico, e é essa varredura, não a identidade de quem digita, que
  protege o repositório.

  **(c) A proteção da `main` não exige revisor, e `enforce_admins` estava desligado
  — o segundo virou.** O `enforce_admins: false` foi corrigido para **`true`** no
  rework da tentativa 2, e a justificativa que o sustentava era **falsa**: alegava
  que a `main` ficaria "inadministrável", quando sem `required_pull_request_reviews`
  o owner segue abrindo e mergeando o próprio PR com o CI verde — foi o que
  aconteceu no PR #27. O que `enforce_admins: true` retira é o push direto e o
  force-push na `main`, que é o objeto da proteção. **O que fica deliberadamente de
  fora é a revisão obrigatória de PR**, e essa sim é defensável: o Roadmap 9.1 pede
  "PR obrigatório + CI obrigatório", não revisor obrigatório, e num projeto de um
  único desenvolvedor a exigência de um segundo aprovador não teria quem a cumprisse.
  A válvula de escape do owner continua existindo e agora é explícita — desligar a
  proteção por API é um ato registrado, não uma porosidade permanente.

## 9. Definition of Done (gate por etapa)

### Gate por fase

> `[x]` = fase **concluída** pela regra do ARTIFACTS_SPEC §2.11.3: existe
> `FASE-<id>-*-AVALIACAO.md` com `veredito: APROVADO` na mesma `tentativa` do
> EXECUCAO. Não é marcação a olho — deriva dos artefatos. Sincronizado em
> 2026-08-09: 23 das 26 fases concluídas; abertas D.3, D.4 e E.4, nenhuma
> com execução registrada.

- [x] **A.1** — rotação confirmada pelo owner; repositório privado; working tree sem
      a credencial; `make test-frontend` verde. *(Encerrada por aceite do owner em
      2026-08-03, no teto do §2.11.4 — ver OQ13.)*
- [x] **A.2** — varredura sobre todo o histórico com zero achados; documentos de
      auditoria reescritos sem PII nem caminho de extração; PRs do Dependabot
      tratados.
- [x] **A.3** — AC-3; `pre-commit run --all-files` verde; CI verde.
- [x] **B.1** — AC-5; `pytest tests/unit/` sem infraestrutura; contagem de testes
      coletados inalterada (199 testes unitários).
- [x] **B.2** — AC-6; execução verde no GitHub Actions com os gatilhos restaurados.
- [x] **B.3** — AC-7 e AC-8; `make test-integration` verde.
- [x] **B.4** — AC-9; piso de cobertura ativo e CI verde.
- [x] **B.5** — AC-17; delta do estrato de foto registrado com números.
      *(Medido em 2026-08-04, tentativa 2: quatro execuções contra o provedor real,
      MdAPE 52,17% e SSPB +52,17% em todas as quatro — nenhum delta separável do
      ruído em n=3. Achado do HTTP 413 na configuração de produção em OQ19.)*
- [x] **C.1** — AC-10; testes existentes dos parsers passam **sem modificação**.
- [x] **C.2** — AC-11; suíte de IA verde sem modificação nos testes existentes.
- [x] **C.3** — AC-12; README do harness com a análise de poder.
- [x] **C.4** — OQ2 resolvida e registrada; dataset completo validando; limitações
      documentadas. *(Executada em 2026-08-03: 43 casos verificados, três estratos
      populados; extensões de fonte e de arquivos em OQ17.)*
- [x] **C.5** — AC-13; relatório com os três estratos, `n` e IC95.
- [x] **C.6** — AC-14; grupo do bug 001 presente; reprovações registradas como
      achado.
- [x] **C.7** — AC-15, NFR-2, NFR-3; execução completa registrada, **sem casos
      vazios além dos três de foto nominados no bug 003**. *(Executada local em
      2026-08-04, os passos do `eval.yml` um a um: 43 casos, 57 chamadas, zero 429
      no runner, gate `verificar` reprovando corretamente, e o consumo medido —
      TPD 100k, 99.768 usados — confirmando a agenda semanal. Duas cláusulas
      migraram, cada uma com destino nomeado: a de plataforma,
      `workflow_dispatch` no GitHub, para a D.2 (OQ20); a de "sem casos vazios"
      sem qualificador, para o bug 003 (OQ21).)*
- [x] **C.8** — AC-16; histórico com ao menos duas execuções reais.
- [x] **D.1** — AC-18 (description, topics, `LICENSE` versionado e versão
      sincronizada). A detecção de licença pela API migrou para o AC-19, que é
      da D.2 — ver OQ18.
- [x] **D.2** — AC-19 (incl. licença detectada pela API); proteção de `main`
      configurada. *(Executada por último, por decisão do owner — OQ15. Aprovada na
      tentativa 2: a tentativa 1 fechou com RESSALVAS por duas decisões de escopo sem
      registro durável e por `enforce_admins: false`, corrigidos com a OQ22 e com
      `enforce_admins: true`.)*
- [ ] **D.3** — AC-20; execução limpa a partir do README validada.
- [ ] **D.4** — AC-21; framework `.codeflow` operando após a poda.
- [x] **D.5** — AC-22; `npm run build` sem warning de `metadataBase`.
- [x] **D.6** — AC-23.
- [x] **E.1** — AC-24.
- [x] **E.2** — AC-25; ADR-009 escrito; owner confirmou a topologia.
- [x] **E.3** — AC-26.
- [ ] **E.4** — AC-27; deploy automático verificado ponta a ponta.

### Itens globais transversais

- [ ] `ruff check .` e `ruff format --check .` sem erros (NFR-1).
- [ ] `mypy app/` em modo strict sem erros (NFR-1, princípio 2).
- [ ] `npm run lint` e `npx tsc --noEmit` sem erros (NFR-1).
- [ ] `make test-unit`, `make test-integration` e `make test-frontend` verdes.
- [ ] Os limiares de `backend/tests/integration/test_golden_set.py` não regridem
      (NFR-6).
- [ ] Nenhum artefato versionado contém credencial, PII, e-mail pessoal ou conteúdo
      de `.env` (NFR-4, princípio 4).
- [ ] Nenhuma migration criada ou alterada (NFR-7, princípio 6).
- [ ] Todo commit em Conventional Commits em português, sem menção a autor, IA ou
      agente e sem `Co-Authored-By` (princípio 5).
- [ ] Toda decisão de escopo tomada durante a execução está registrada aqui em §8 ou
      numa decision do framework.

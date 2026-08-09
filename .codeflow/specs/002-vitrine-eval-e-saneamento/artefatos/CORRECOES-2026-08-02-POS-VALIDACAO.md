---
spec: 002-vitrine-eval-e-saneamento
tipo: correcoes-pos-validacao
data: 2026-08-02
status: aplicado
---

# Correções aplicadas após a validação com Docker

Documento transversal: registra o que foi corrigido depois que o owner ligou o
Docker e revisou os achados das fases. As correções cruzam fases, então não
cabiam num único `FASE-*-EXECUCAO.md`.

O que torna esta rodada diferente: **o harness de eval construído no Track C foi
usado para medir as próprias correções.** As melhorias abaixo não são
argumentadas, são medidas.

## 1. Sanity check descartava o dado bom em prato composto

**Achado (C.5).** O estrato `composto` tinha MdAPE de 23,81% contra 1,26% do
`simples`, com apenas 25% dos casos dentro de ±10%. Causa no log: a IA estima a
**porção inteira** do prato (~350 kcal) para uma descrição de 100 g; o sanity
check de 35% então descartava o match correto da fonte curada `taco`
(110 kcal) e adotava a estimativa ruim.

**Correção.** O check deixa de descartar quando a fonte é curada
(`_FONTES_CURADAS = {"taco"}`). A divergência continua sendo registrada e agora
marca o item com `needs_review` — o sinal não é perdido, só deixa de destruir o
dado. Para importação automática (`openfoodfacts`, `fatsecret`, `usda`) o
comportamento do ADR-006 **não muda**.

Aplicado nos dois parsers; `vision_parser.py` importa `_FONTES_CURADAS` de
`meal_parser.py` para os dois não divergirem.

**Efeito medido** (`python -m evals.runner --cassettes`, mesmo dataset, mesmos
cassettes, só o código mudou):

| métrica | antes | depois |
|---|---|---|
| `composto` — MdAPE | 23,81% | **6,86%** |
| `composto` — dentro de ±10% | 25% | **75%** |
| agregado — dentro de ±10% | 70% | **90%** |
| agregado — SSPB | +1,25% | **0,00%** |
| MAE carboidrato | 1,34 g | **0,49 g** |
| MAE gordura | 0,81 g | **0,63 g** |
| macros dentro de ±5 g | 86–100% | **100% nos três** |

Decision: `.codeflow/decisions/2026-08-02-sanity-check-nao-descarta-fonte-curada.md`.
Testes: `tests/unit/test_meal_parser_fonte_curada.py` (8 testes, cobrindo fonte
curada e não curada nos dois ramos).

## 2. Gordura de passar caía na regra genérica de 100 g

**Achado (C.6).** "1 pão francês com manteiga" = 880 kcal contra "50g pão + 10g
manteiga" = 212,6 kcal — spread 4,14, o pior grupo da bateria.

**Diagnóstico medido.** A IA emite `unit="porção"` para a manteiga. Não havia
regra `(manteiga, porcao)` em `portions`, então valia a genérica de 100 g. Cem
gramas de manteiga são ~720 kcal.

```text
manteiga  1 porção -> 100.0 g | origem=tabela ancorada=False detalhe=(genérica)
manteiga  10 g     ->  10.0 g | origem=direta  ancorada=True
```

**Correção.** Regras próprias de `porcao`/`unidade` para `manteiga`,
`margarina`, `requeijao`, `geleia`, `cream cheese`, `azeite` e `oleo`.
Descoberta no caminho: `(margarina, colher_sopa)` estava duplicado no arquivo, o
que violava a unique `(term, unit)` e derrubava o seed inteiro — removido, com
teste que impede a reincidência.

Testes: `tests/unit/test_portions_gorduras.py` (20 testes, incluindo integridade
da tabela e coerência das faixas).

**Nota honesta:** `0,5 kg` **não** era o bug que eu supus. A normalização
converte corretamente para 500 g; o spread de 1,75 do grupo `inv-10` vinha do
mesmo sanity check do item 1, disparando num lado e não no outro. Corrigido pelo
item 1, não por mudança de unidade.

## 3. Não-determinismo do modelo (achado `inv-08`)

**Achado (C.6).** A mesma string repetida três vezes deu 859,2 / 859,2 / 695,4
kcal. Uma execução única por caso mistura erro do pipeline com ruído de
amostragem.

**Solução adotada.** O runner ganhou `--repeticoes N`: o valor do caso passa a
ser a **mediana** das execuções, e o **coeficiente de variação** entre elas é
reportado à parte, em `ruido_do_modelo`. Isso separa as duas fontes de erro em
vez de misturá-las.

Default 1, para a execução manual continuar barata. A execução agendada
(`eval.yml`) deve subir para 3 — decisão do owner sobre custo de quota.

## 4. Rate limiting nos endpoints GET de IA

Os cinco GET de `ai.py` que consultam o provedor (`suggest-meal`, `patterns`,
`nutritional-alerts`, `goal-adjustment`, `monthly-report`) ganharam teto próprio,
`RATE_LIMIT_AI_LEITURA` (40/minute), mais folgado que o dos POST (20/minute)
porque o dashboard dispara vários por carga.

`GET /ai/conversations` ficou **de fora** por desenho: é leitura pura de banco e
não gasta token. Há teste garantindo que ele não tem teto.

Isto reverte a lacuna declarada na B.3, que o escopo travado daquela fase
impedia fechar.

## 5. `.env.example` documentado

As 13 variáveis novas (amostragem da Groq, rate limiting, teto do batch) entraram
no `.env.example`. Na rodada anterior o arquivo estava fora do alcance de escrita
da sessão; nesta, não.

## 6. OQ2 resolvida — Track C.4 desbloqueado

**Decisão: IBGE POF 2011 + TACO 4ª edição.** Medida caseira → gramas pela POF;
gramas → kcal e macros pela TACO. Duas fontes independentes entre si e do
projeto, gratuitas, brasileiras e citáveis por terceiro.

A opção 1 (balança do owner) resolveria o estrato `simples` e não o `composto` —
balança dá massa, não composição — e não escala. Rótulos de rede ficam como
fonte complementar para receita padronizada.

Limitação que a C.4 deve declarar: TACO mede em condição de laboratório e a POF
reporta medidas *referidas*; a métrica compara o pipeline contra referência
**populacional**, não contra a verdade de um prato individual.

Registrado em §8 da spec, no README do harness, e o risco R4 foi encerrado.

## 7. Gate da NFR-6 estava morto — agora executa

**Achado (B.4).** Os cinco testes de `test_golden_set.py` pulavam sempre,
inclusive no CI. Causa: `tests/conftest.py` montava o schema com
`Base.metadata.create_all()`, que cria só tabelas — sem as extensões
`pg_trgm`/`unaccent`, sem a função `caloria_unaccent`, sem os índices GIN.

**Correção.** `_reset_schema` passa a fazer `DROP SCHEMA public CASCADE` +
`alembic upgrade head`. O schema de teste vira **o mesmo de produção**, e uma
migration quebrada passa a falhar na suíte em vez de no deploy.

Dois obstáculos reais encontrados e resolvidos:

1. `alembic/env.py:21` **sobrescreve** `sqlalchemy.url` com
   `settings.DATABASE_URL` — passar a URL pelo `Config` não bastava, e o upgrade
   migrava o banco errado. O helper aponta `settings.DATABASE_URL` para o banco
   de teste durante o upgrade e restaura depois.
2. `env.py` chama `fileConfig(...)`, que reconfigura o logging do processo e
   **desabilita os loggers existentes**. Três testes de log passaram a falhar só
   quando a suíte rodava inteira — falha por ordem de execução, do tipo que some
   quando se roda o arquivo isolado. Resolvido com `mock.patch` em
   `logging.config.fileConfig` durante o upgrade.

Com o schema correto, `tests/integration/conftest.py` passou a semear o banco
nutricional na sessão. **Resultado: `5 passed` no `test_golden_set.py`, zero
skipped** — o gate da NFR-6 voltou a existir.

Decision: `.codeflow/decisions/2026-08-02-schema-de-teste-por-migrations.md`.

## 8. Scripts de seed quebrados

Três quebras independentes na cadeia que `make seed` e `docs/setup.md` mandam
usar:

| Script | Quebra | Correção |
|---|---|---|
| `seed_all.py` | `ImportError: ReminderChannel` — enum removido junto dos bots na v0.7.0 | Import e o campo `channel` removidos |
| `seed_all.py` | `AttributeError` em `NoneType` quando o usuário não existia | Pré-condição explícita, com a mensagem dizendo o que rodar antes |
| `seed_dev_user.py` | `ModuleNotFoundError: psycopg2` — o script usa driver síncrono | `psycopg2-binary` nas dependências **de dev** |
| `seed_dev_user.py` | `UndefinedColumn: age` — coluna virou `birth_date` na fase A.1 da spec 001 | `UPDATE`/`INSERT` corrigidos |

Verificado ponta a ponta num banco limpo: `seed_dev_user.py` conclui com "30 dias
de refeições / 15 registros de peso" e `seed_all.py` conclui com "4 lembretes
configurados".

## 9. Piso de cobertura subiu

A margem entre medido (72%) e piso (70%) existia para absorver os testes que
pulavam sem o banco semeado. **Esses testes não pulam mais** (item 7), a variação
entre ambientes caiu, e o piso subiu para **72%** — encostando no medido, como a
fase B.4 pedia originalmente. O histórico de medições ficou registrado no próprio
`pyproject.toml`, para que subir o piso continue sendo decisão com número.

`TEST_DATABASE_URL` passou a ser declarada explicitamente no `ci.yml`: com o
schema vindo de migrations, depender do default do conftest era frágil.

## Remedição da bateria de invariância — PENDENTE por quota

A bateria não pôde ser reexecutada depois das correções. As execuções de eval do
dia esgotaram a quota do free tier da Groq, e a bateria passou a bater em
`RateLimitError`:

```text
Rate limit Groq — aguardando 15s (tentativa 1/4, 0s de 120s do teto já gastos)
Rate limit Groq — aguardando 30s (tentativa 2/4, 15s de 120s do teto já gastos)
Rate limit Groq — aguardando 60s (tentativa 3/4, 45s de 120s do teto já gastos)
```

A execução foi **interrompida de propósito**, para não continuar queimando quota
sem necessidade.

Três leituras honestas disso:

1. **O retry tipado da C.2 está funcionando exatamente como projetado** — backoff
   de 15s → 30s → 60s, com o teto de 120s sendo contabilizado e reportado. Este
   log é a primeira evidência real da fase C.2 em condição de rate limit.
2. **O risco R5 da spec se materializou de novo** ("o rate limit do free tier
   impede execuções completas do eval — já aconteceu em 2026-07-26"). Isso
   **confirma** a escolha de periodicidade semanal no `eval.yml`, que era palpite
   fundamentado e agora tem medição por trás.
3. **A remedição da invariância é a única verificação desta rodada que ficou por
   fazer.** As duas correções que ela mediria (§1 e §2) têm evidência por outros
   caminhos: o runner mediu a melhora do sanity check com cassettes (sem rede), e
   as regras de porção têm 20 testes unitários. Mas o número novo de
   `taxa_de_aprovacao` só sai quando a quota voltar.

**Ação para o owner:** rodar `python -m evals.invariance` no dia seguinte, ou
disparar o `eval.yml` por `workflow_dispatch`, e comparar contra a linha de base
de 2026-08-02 (aprovação 0,417 · spread mediano 1,2115 · p95 3,5126).

## O que NÃO foi feito, e por quê

- **JSON mode (C.2, passo 2)** continua desligado. É pergunta em aberto do owner,
  não ordem de correção. Detalhe e recomendação no resumo entregue.
- **D.4 (poda)** segue não executada: depende de D.2, que é ação do owner, e
  apagaria os próprios relatórios desta rodada.
- **Nova gravação de cassettes** não foi necessária: as correções são
  pós-processamento, o payload enviado ao provedor não mudou, e os cassettes
  existentes replicam. Isso é, em si, uma confirmação de que o snapshot de
  payload está medindo a coisa certa.

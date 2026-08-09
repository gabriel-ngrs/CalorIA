---
data: 2026-08-02
titulo: Rate limiting nos cinco GET de IA que gastam token do provedor
status: ativa
tags: [seguranca, rate-limiting, api, spec-002, fase-b3]
spec: 002-vitrine-eval-e-saneamento
fase: B.3
---

# Rate limiting nos cinco GET de IA que gastam token do provedor

## Contexto

O escopo travado da Fase B.3 (`SPEC_002_VITRINE_EVAL_E_SANEAMENTO.md:707-708`) diz:

> Não introduzir rate limiting em endpoints autenticados de leitura.

A primeira entrega da fase respeitou a restrição e registrou a lacuna (desvio 5 do
`FASE-B.3-hardening-config-EXECUCAO.md`): os cinco GET de `ai.py` ficaram sem teto
"embora também consumam tokens do provedor". Na rodada de correção de 2026-08-02 os
cinco ganharam `@limiter.limit(settings.RATE_LIMIT_AI_LEITURA)`, com a mudança
atribuída a decisão do owner e documentada apenas em
`artefatos/CORRECOES-2026-08-02-POS-VALIDACAO.md` §4.

A avaliação independente da tentativa 1 reprovou a fase por isso (achado B3-BLK-1):
relatório em `artefatos/` não é registro de decisão, e o DoD global da spec (§9,
"Itens globais transversais") exige que toda decisão de escopo esteja registrada em
§8 da spec **ou** numa decision do framework. A constitution universal é do mesmo
teor: gate duro não se destrava por autorização falada; override genuíno exige
decision registrada antes da próxima execução. Esta decision é esse registro.

**O fato que motiva a revisão da restrição.** Os cinco GET não são leitura de banco.
Cada um instancia o cliente de IA e chama o provedor:

| endpoint | linha | serviço chamado |
|---|---|---|
| `GET /ai/suggest-meal` | `api/v1/ai.py:163` | `InsightsGenerator.suggest_meal` |
| `GET /ai/patterns` | `api/v1/ai.py:186` | `PatternAnalyzer.analyze_eating_patterns` |
| `GET /ai/nutritional-alerts` | `api/v1/ai.py:206` | `InsightsGenerator.nutritional_alerts` |
| `GET /ai/goal-adjustment` | `api/v1/ai.py:226` | `InsightsGenerator.goal_adjustment_suggestion` |
| `GET /ai/monthly-report` | `api/v1/ai.py:245` | `InsightsGenerator.monthly_report` |

Todos dependem de `_require_ai` e de `get_ai_client()` — o mesmo custo em tokens que
justifica o teto nos três POST. A restrição do escopo travado foi escrita sob a
premissa "GET autenticado = leitura barata de banco", verdadeira para o resto da API
e falsa para estes cinco. O contraexemplo está no mesmo arquivo:
`GET /ai/conversations` (`api/v1/ai.py:149-161`) é leitura pura de banco, não gasta
token, e **ficou sem teto** — o que demonstra que o critério aplicado foi "gasta
token do provedor", não "é método GET".

## Decisão

**1. Manter o teto nos cinco GET de IA que chamam o provedor**, com uma setting
própria — `RATE_LIMIT_AI_LEITURA = "40/minute"` (`core/config.py:129-132`) — e não o
`RATE_LIMIT_AI` dos POST.

**2. Manter `GET /ai/conversations` sem teto**, por ser leitura pura de banco, com
teste que trava esse desenho
(`tests/integration/test_limites_requisicao.py:116-121`).

**3. Registrar a exceção no texto do escopo travado da B.3 em §5 e como OQ11 em §8**
da spec, para que a próxima leitura não conclua que a restrição foi ignorada.

**Por que 40/minute e não o mesmo 20/minute dos POST.**
`frontend/app/(dashboard)/insights/page.tsx:72-76` dispara quatro dessas consultas
por carga da página (`patterns`, `nutritional-alerts`, `goal-adjustment`,
`monthly-report`), mais `suggest-meal` sob demanda. Com o teto dos POST, cinco
recargas da página por minuto já devolveriam 429 a um usuário legítimo. Com 40/min
cabem dez recargas por minuto na mesma chave de contagem, e o teto continua muito
abaixo do volume que tornaria o custo em tokens relevante. **O valor é folga
dimensionada pelo consumo da página, não medição de tráfego real** — não há tráfego
de produção para medir (o CD está desligado desde julho; ver Fase E.1). Ajustar é
mudar uma setting, sem tocar código.

## Alternativas descartadas

- **Reverter os cinco decorators e tratar o assunto numa fase própria** (opção 2
  sugerida pela avaliação). É a alternativa honesta e foi considerada a sério: cumpre
  o escopo travado literalmente e sai da fase sem exceção. Rejeitada porque deixaria
  sem teto exatamente os cinco endpoints de maior custo unitário do sistema, enquanto
  a fase entrega proteção aos três POST equivalentes — e o FR-B4 diz "os endpoints
  públicos de autenticação **e os endpoints de IA** devem ter rate limiting", sem
  restringir a método. Adiar o teto para uma fase futura manteria aberta, por tempo
  indeterminado, a superfície que a B.3 existe para fechar.

- **Aplicar `RATE_LIMIT_AI` (20/minute) também aos GET, sem setting nova.** Um valor
  a menos para manter. Rejeitado pela conta acima: a página de insights consome
  quatro do balde por carga, e o mesmo teto dos POST transformaria uso normal em 429.

- **Contar por `user_id` em vez de IP nos endpoints autenticados** (sugestão 2 da
  avaliação). Tecnicamente melhor — dois usuários atrás do mesmo NAT hoje dividem o
  balde. Rejeitada **para esta fase** por escopo: exigiria uma segunda `key_func`
  ciente do token, tocando `core/rate_limit.py` e todos os decorators, e a fase está
  em rework de um achado de registro, não de desenho. Registrada como débito no §7
  do relatório de execução.

- **Deixar o registro apenas no relatório de execução e no documento de correções.**
  É o estado que produziu o BLOQUEANTE. Rejeitado: `artefatos/` é telemetria de
  execução (e sai do versionamento na Fase D.4), enquanto `decisions/` é registro de
  engenharia que sobrevive à poda e é carregado por tag pelos workflows seguintes.

## Consequência

- A restrição "não introduzir rate limiting em endpoints autenticados de leitura"
  passa a valer com exceção explícita: **vale para leitura que não chama provedor
  externo**. `GET /ai/conversations` continua sendo o caso de referência do lado
  isento, com teste que o trava.
- A superfície pública da API muda: cinco GET autenticados passam a poder devolver
  429. Não é mudança de contrato de dados (schema e códigos de sucesso inalterados),
  mas é mudança de comportamento observável e por isso está aqui.
- **Risco residual — chave por IP.** A contagem é por IP (`core/rate_limit.py`), então
  usuários atrás do mesmo NAT compartilham o balde de 40/min. Mitigação: o teto é
  folgado o bastante para uso normal compartilhado; a correção estrutural (chave por
  `user_id`) fica registrada como débito.
- **Risco residual — valor não medido em produção.** 40/min é dimensionado pelo
  consumo da página de insights, não por tráfego observado. Quando a Fase E.4
  restabelecer o deploy e houver tráfego real, o valor deve ser reavaliado.
- `RATE_LIMIT_TRUST_FORWARDED_FOR` continua `false` por default: sem proxy à frente,
  `X-Forwarded-For` é forjável e seria contorno trivial do teto. Produção liga junto
  do Caddy (Fase E.4).

## Reprodução

    # os cinco GET com teto e o sexto sem, no código
    grep -n "limiter.limit\|^@router" backend/app/api/v1/ai.py

    # o desenho travado por teste
    docker compose -f docker-compose.dev.yml exec -T backend \
      pytest tests/integration/test_limites_requisicao.py -q

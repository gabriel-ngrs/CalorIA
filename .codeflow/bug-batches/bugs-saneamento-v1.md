---
versão: 1.0
lote: bugs-saneamento-v1
origem: varredura Fase A (QA manual Playwright + auditoria de código)
criado: 2026-07-26
atualizado: 2026-07-26
verificado: 2026-07-26 (críticos e altos)
---

# Lote de bugs: bugs-saneamento-v1

Inventário produzido pela Fase A do trabalho de saneamento: QA manual dirigido no
navegador (auth/perfil, refeições/dashboard, módulos secundários) somado a
auditoria de código em três frentes (`services/ai/`, resto do backend,
infraestrutura/configuração). Cada achado passou por um verificador independente
instruído a **refutá-lo**.

**Placar bruto:** 81 achados — 4 críticos,
21 altos,
34 médios,
22 baixos.
19 corrigidos nesta sessão, 2 refutados na verificação, 6 convertidos em melhoria, o restante **aberto**.

> **Honestidade sobre o estado:** este lote é um inventário, não um lote fechado.
> A Fase A foi executada por completo; a correção priorizou o bug 001 (objetivo
> central do trabalho) e os defeitos de maior severidade no mesmo caminho de
> código. Os demais ficam registrados e **não foram corrigidos** — ver
> "Adiados" ao final.

Legenda da coluna `verificação`: preenchida pelo `/double-check` (`✓` sanado,
`✗` regrediu, `⚠` inconclusivo, `—` não verificado).

## Bugs

| id | título | severidade | área | arquivo suspeito | status | fix (arquivo:linha) | verificação |
|----|--------|------------|------|------------------|--------|---------------------|-------------|
| S01 | Insight semanal da IA inverte a direção do peso: diz "ganhou 6 kg" para quem perdeu 6 kg | critico | backend/ai| `backend/app/services/ai/insights_generator.py:79` | corrigido | backend/app/services/ai/insights_generator.py:77 | ✓ |
| S02 | Registro de refeição por FOTO está 100% quebrado: modelo de visão da Groq não existe mais | critico | backend/ai| `backend/app/services/ai/ai_client.py:23` | corrigido | backend/app/core/config.py:56 + services/ai/ai_client.py:88 | ✓ (verificado 2026-07-26) |
| S03 | "Esqueci minha senha" quebrado: POST /auth/forgot-password retorna 500 (Celery ligado ao broker AMQP padrão) | critico | backend/auth| `backend/app/api/v1/auth.py:119 (e backend/app/workers/tasks/emails.py:17)` | corrigido | backend/app/workers/tasks/__init__.py + api/v1/auth.py:118 | ✓ (verificado 2026-07-26) |
| S04 | Chave privada VAPID e caches são embutidos na imagem de produção do backend (não existe .dockerignore) | critico | infra/docker| `backend/Dockerfile:46` | corrigido | backend/.dockerignore | ✓ (verificado 2026-07-26) |
| S05 | Insight semanal inverte a direção do peso (diz "ganhou" quando o usuário perdeu) | alto | backend/ai| `backend/app/services/ai/insights_generator.py:79` | corrigido | backend/app/services/ai/insights_generator.py:77 (duplicata do S01) | ✓ |
| S06 | zip(..., strict=False) apaga silenciosamente alimentos da refeição quando a IA devolve menos itens no fallback | alto | backend/ai| `backend/app/services/ai/meal_parser.py:206` | corrigido | backend/app/services/ai/meal_parser.py:363 | ✓ |
| S07 | Item é salvo com 0 kcal e macros reais quando a IA omite o campo "calories" (correct_calories não corrige) | alto | backend/ai| `backend/app/services/ai/utils.py:29` | corrigido | backend/app/services/ai/utils.py:44 | ✓ |
| S08 | Busca no banco de alimentos faz Seq Scan em 42.103 linhas — 17 s de banco por refeição, análise leva 21 s | alto | backend/ai| `backend/app/services/ai/food_lookup.py:98` | corrigido | backend/app/services/ai/food_lookup.py:197 + migration d0e1f2a3b4c5 | ✓ |
| S09 | Backoff de 105 s no rate limit do Groq excede o timeout de 45 s do frontend e nunca consegue se recuperar | medio | backend/ai| `backend/app/services/ai/ai_client.py:126` | aberto | — | ⚠ confirmado · esforço pequeno |
| S10 | Reset de senha não invalida as sessões existentes: access e refresh tokens antigos continuam válidos | alto | backend/auth| `backend/app/api/v1/auth.py:123-153` | aberto | — | ⚠ confirmado · esforço pequeno |
| S11 | Card "Tendência peso" mostra o sinal invertido (+6,0 kg em laranja para quem perdeu 6 kg) | alto | backend/dashboard| `backend/app/api/v1/dashboard.py:62` | nao-reproduz | — | ✗ refutado: Reproduzi o cenário exato de ponta a ponta no ambiente no ar e o card |
| S12 | alembic downgrade quebra na revisão 20260315_webpush: type "reminderchannel" does not exist | alto | backend/migrations| `backend/alembic/versions/20260315_a1b2c3d4e5f6_web_push_notifications.py:109` | corrigido | backend/alembic/versions/20260315_a1b2c3d4e5f6_web_push_notifications.py:109 | ✓ (verificado 2026-07-26) |
| S13 | Drift entre models e migrations faz `make migration` gerar um DROP do índice GIN trigrama do lookup de alimentos | medio | backend/migrations| `backend/app/models/food.py:20` | aberto | — | ⚠ confirmado · esforço pequeno |
| S14 | Perfil mostra TMB e TDEE incoerentes: TMB usa o peso atual, TDEE fica congelado no peso da última edição do perfil | medio | backend/perfil| `backend/app/services/profile_service.py:66-94 (compute_bmr em 49-64)` | aberto | — | ⚠ confirmado · esforço pequeno |
| S15 | Task de hidratação envia notificação a TODOS os usuários ativos, mesmo sem lembrete de água configurado | medio | backend/workers| `backend/app/workers/tasks/reminders.py:154-192 (select(User).where(User.is_active) na linha 166); agendada em backend/app/workers/celery_app.py:52-56 (crontab hour="8,10,12,14,16,18,20")` | aberto | — | ⚠ confirmado · esforço pequeno |
| S16 | Gráfico "Calorias — últimos 7 dias" rotula todas as barras com o dia ANTERIOR (off-by-one) | alto | frontend/dashboard| `frontend/components/dashboard/CaloriesBarChart.tsx:50` | corrigido | frontend/components/dashboard/CaloriesBarChart.tsx:48 | ✓ (verificado 2026-07-26) |
| S17 | Usuário novo fica preso em loop /dashboard → /onboarding se avançar a etapa de metas sem digitar a meta calórica | alto | frontend/dashboard| `frontend/app/(dashboard)/dashboard/page.tsx:69` | corrigido | frontend/app/onboarding/page.tsx:438 | ✓ (verificado 2026-07-26) |
| S18 | Loop infinito no onboarding: "Próximo" no passo 2 com meta calórica vazia prende o usuário fora do app | alto | frontend/onboarding| `frontend/app/onboarding/page.tsx:440 (e frontend/app/(dashboard)/dashboard/page.tsx:68-72)` | corrigido | frontend/app/onboarding/page.tsx:438 (mesma causa do S17) | ✓ (verificado 2026-07-26) |
| S19 | Gráfico de evolução de peso é plotado em ordem cronológica invertida (mostra ganho quando houve perda) | alto | frontend/peso| `frontend/app/(dashboard)/peso/page.tsx:48-51 e frontend/app/(dashboard)/peso/page.tsx:191 (dados de backend/app/services/log_service.py:26-36, que ordena WeightLog.date.desc())` | corrigido | frontend/app/(dashboard)/peso/page.tsx:48 | ✓ (verificado 2026-07-26) |
| S20 | Descrição sem comida ("asdfgh") gera refeição fantasma de 0 kcal salvável no banco | alto | frontend/refeicoes| `frontend/app/(dashboard)/refeicoes/page.tsx:768` | corrigido | backend/app/services/ai/meal_parser.py:437 + vision_parser.py:291 | ✓ |
| S21 | Página Refeições trunca em 20 refeições e mostra total do dia errado (2000 kcal vs 2246 no dashboard) | alto | frontend/refeicoes| `frontend/lib/hooks/useMeals.ts:11` | corrigido | frontend/lib/hooks/useMeals.ts:10 | ✓ (verificado 2026-07-26) |
| S22 | Origem do dado (TACO/OpenFoodFacts vs IA) é descartada ao salvar e nunca aparece na UI | alto | frontend/refeicoes| `frontend/app/(dashboard)/refeicoes/page.tsx:517` | corrigido | frontend/lib/mealItems.ts (helper usado nas 2 telas) | ✓ (verificado 2026-07-26) |
| S23 | Relatórios mostram tendência de peso com sinal INVERTIDO (perdeu 8kg → exibe "+8.0 kg") | alto | frontend/relatorios| `frontend/app/(dashboard)/relatorios/page.tsx:99` | corrigido | frontend/app/(dashboard)/relatorios/page.tsx:73 | ✓ |
| S24 | docker-compose.backend.yml (o arquivo que o CD implanta) monta a chave VAPID de um caminho inexistente e não define VAPID_PRIVATE_KEY | alto | infra/deploy| `docker-compose.backend.yml:55` | nao-reproduz | — | ✗ refutado: Verifiquei o arquivo atual (`docker-compose.backend.yml`, inalterado d |
| S25 | Makefile ainda usa as portas antigas 8000/3000: `make status`, `make dev-d` e `make init` reportam o backend como indisponível | alto | infra/makefile| `Makefile:191` | corrigido | Makefile:32 | ✓ (verificado 2026-07-26) |
| S26 | N+1 em /ai/monthly-report (30 queries) e /ai/nutritional-alerts (31 queries): get_daily_summary chamado num laço por dia | medio | backend/ai| `backend/app/services/ai/insights_generator.py:381` | aberto | — | — |
| S27 | Análise de refeição responde 500 quando a IA devolve null num campo numérico ou um objeto JSON em vez de array | medio | backend/ai| `backend/app/services/ai/meal_parser.py:236` | corrigido | backend/app/services/ai/meal_parser.py:432 (_num) | ✓ |
| S28 | Inferência de tipo de refeição erra o tipo ("lanche pré-treino" vira lanche da tarde) e ignora texto sem acento | medio | backend/ai| `backend/app/services/ai/context_builder.py:108` | aberto | — | — |
| S29 | Relatório mensal aponta a MESMA semana como melhor e pior quando o usuário não tem meta calórica | medio | backend/ai| `backend/app/services/ai/insights_generator.py:440` | aberto | — | — |
| S30 | SECRET_KEY (e NEXTAUTH_SECRET) têm default inseguro e não há fail-fast em produção — AUD-039 confirmado | medio | backend/config| `backend/app/core/config.py:32` | aberto | — | — |
| S31 | Usuário desativado (is_active=false) continua lendo e gravando dados com o access token ainda válido | medio | backend/core| `backend/app/core/deps.py:21` | aberto | — | — |
| S32 | GET /dashboard/weight-chart ignora o parâmetro `days` que o frontend envia (o backend espera `limit`) | medio | backend/dashboard| `backend/app/api/v1/dashboard.py:64` | aberto | — | — |
| S33 | Endpoint /dashboard/weight-chart ignora o parâmetro `days` enviado pelo frontend — card 'últimos 90 dias' não filtra por período | medio | backend/dashboard | `backend/app/api/v1/dashboard.py:62-68 (parâmetro se chama `limit`) vs frontend/lib/hooks/useDashboard.ts:36 (`?days=${days}`), consumido em frontend/app/(dashboard)/peso/page.tsx:34 com useWeightChart(90)` | aberto | — | — |
| S34 | Água registrada logo após a meia-noite local some: cliente grava data local, /hydration/today usa a data do servidor | medio | backend/hidratacao | `frontend/app/(dashboard)/hidratacao/page.tsx:33-39 e :72-80 (data local do navegador) vs backend/app/api/v1/hydration.py:20-26 (`day: date = Query(default_factory=date.today)` no servidor)` | aberto | — | — |
| S35 | Registrar humor duas vezes no mesmo dia apaga a nota salva (upsert sobrescreve notes com NULL) | medio | backend/humor | `backend/app/services/log_service.py:178-192 (MoodService.create — `existing.notes = data.notes`); agravado por frontend/app/(dashboard)/humor/page.tsx:88-108 (formulário não carrega o registro do dia e limpa notes após enviar)` | aberto | — | — |
| S36 | Respostas 500 do backend saem sem cabeçalhos CORS — o frontend só vê "Network Error" opaco | medio | backend/infra| `backend/app/main.py:42-64 (ordem dos middlewares)` | aberto | — | — |
| S37 | Datas futuras aceitas em meal/weight/hydration/mood; pesagem futura vira o "peso atual" do dashboard | medio | backend/logs| `backend/app/schemas/logs.py:18` | aberto | — | — |
| S38 | Peso/Hidratação/Humor aceitam datas futuras e antiquíssimas; peso futuro sequestra 'Peso atual' e zera a meta | medio | backend/logs | `backend/app/schemas/logs.py:16-19 (WeightLogCreate), :38-41 (HydrationLogCreate), :85-89 (MoodLogCreate) — nenhum valida o campo `date`; consumido em backend/app/services/log_service.py:62-69 (WeightService.latest ordena por date desc)` | aberto | — | — |
| S39 | `alembic check` falha: drift entre o modelo Food e o banco faria um autogenerate derrubar o índice GIN trigrama ix_foods_search_trgm | medio | backend/models| `backend/app/models/food.py:33` | aberto | — | — |
| S40 | Data de nascimento no futuro é aceita e infla TMB/TDEE (idade negativa) | medio | backend/perfil| `backend/app/schemas/profile.py:11 (birth_date sem validação) + frontend/app/onboarding/page.tsx:141-149` | aberto | — | — |
| S41 | POST /push/subscribe permite sequestrar a subscription push de outro usuário (upsert por endpoint sem checar posse) | medio | backend/push| `backend/app/api/v1/push.py:80` | aberto | — | — |
| S42 | Banco de teste é criado por Base.metadata (nunca por Alembic): sem pg_trgm nem índice GIN, o FoodLookup é intestável | medio | backend/testes| `backend/tests/conftest.py:59` | aberto | — | — |
| S43 | birth_date no futuro é aceito e gera idade negativa: TMB de 11.763 kcal e TDEE de 14.116 kcal | medio | backend/users| `backend/app/schemas/profile.py:11` | aberto | — | — |
| S44 | Lembrete de hidratação ignora a meta de água do usuário (2000 ml fixo no código) | medio | backend/workers | `backend/app/workers/tasks/reminders.py:174 (`if summary.total_ml >= 2000`) e :179 (`f"Hidratação: {summary.total_ml} ml / 2000 ml hoje. "`)` | aberto | — | — |
| S45 | Navbar exibe o e-mail em vez do nome do usuário (e session.user.id vem vazio) | medio | frontend/auth| `frontend/app/api/auth/[...nextauth]/route.ts:64-70` | aberto | — | — |
| S46 | Todo carregamento completo de página dispara uma rajada de 401 (cache do axios é envenenado com token null enquanto a sessão carrega) | medio | frontend/auth| `frontend/app/providers.tsx:13-19 (e frontend/lib/api.ts:27-30)` | aberto | — | — |
| S47 | Erros de validação do backend aparecem como JSON cru na tela de cadastro | medio | frontend/auth| `frontend/app/(auth)/register/page.tsx:40-43` | aberto | — | — |
| S48 | Cores do gráfico de pizza de macros se deslocam quando um macro é zero (Carboidrato vira verde, Gordura vira amarelo) | medio | frontend/dashboard| `frontend/components/dashboard/MacroPieChart.tsx:109` | aberto | — | — |
| S49 | Seletor de período do Humor (7d/14d/30d) filtra por número de registros, não por dias — médias e 'melhor dia' incluem dados de meses atrás | medio | frontend/humor | `frontend/app/(dashboard)/humor/page.tsx:111 (`const recentLogs = allLogs.slice(0, period)`) e :125-133 (chartData usa slice(-period))` | aberto | — | — |
| S50 | Sino de notificações conta 'não lidas' só entre as 10 mais recentes — badge e 'marcar todas como lidas' somem com não lidas antigas | medio | frontend/notificacoes| `frontend/components/layout/NotificationBell.tsx:105 (useNotifications(10)) e :109 (unreadCount calculado sobre essa lista); frontend/lib/hooks/useNotifications.ts:19-29 (useUnreadCount existe e nunca é usado)` | aberto | — | — |
| S51 | Não existe troca de senha para usuário logado | medio | frontend/perfil| `backend/app/api/v1/auth.py:27-167 (nenhuma rota de change-password) e frontend/app/(dashboard)/perfil/page.tsx:1-397` | convertido-em-melhoria | — | — |
| S52 | Datas do módulo Peso são exibidas um dia antes do valor gravado | medio | frontend/peso| `frontend/app/(dashboard)/peso/page.tsx:260 (histórico) e frontend/app/(dashboard)/peso/page.tsx:50 (eixo X do gráfico)` | aberto | — | — |
| S53 | IA lenta (rate limit) estoura o timeout do axios em 45s e a UI culpa a internet do usuário | medio | frontend/refeicoes| `frontend/lib/api.ts:12` | aberto | — | — |
| S54 | Seletor de período (7d/14d/30d) não afeta o gráfico de peso: front envia ?days e o endpoint espera ?limit | medio | frontend/relatorios| `frontend/lib/hooks/useDashboard.ts:36` | aberto | — | — |
| S55 | "Média calórica" do relatório divide pelo período inteiro e não pelos dias com registro (301 kcal/dia com 4 dias de 500-600 kcal) | medio | frontend/relatorios| `frontend/app/(dashboard)/relatorios/page.tsx:85` | aberto | — | — |
| S56 | `make check` promete "reproduz CI" mas roda um conjunto diferente do ci.yml (em ambas as direções) | medio | infra/ci| `.github/workflows/ci.yml:60` | aberto | — | — |
| S57 | Compose de produção publica a API em 0.0.0.0:8000 sem TLS, em paralelo ao Caddy | medio | infra/deploy| `docker-compose.backend.yml:47` | aberto | — | — |
| S58 | Containers dev rodam como root e deixam arquivos root-only no bind mount, quebrando `docker build` e pytest no host | medio | infra/docker| `backend/Dockerfile.dev:1` | aberto | — | — |
| S59 | Build de produção do frontend copia node_modules e .next do host por cima do npm ci da imagem | medio | infra/docker| `frontend/Dockerfile:22` | aberto | — | — |
| S60 | Correlação humor x calorias conta dia sem refeição registrada como 0 kcal e derruba a média pela metade | baixo | backend/ai| `backend/app/services/ai/pattern_analyzer.py:155` | aberto | — | — |
| S61 | Nome composto só de espaços é aceito no cadastro e na edição de perfil | baixo | backend/auth| `backend/app/schemas/user.py:10-16 (UserCreate) e :20 (UserUpdate)` | aberto | — | — |
| S62 | Access token continua válido depois do logout (até 30 minutos) | baixo | backend/auth| `backend/app/api/v1/auth.py:100-105` | aberto | — | — |
| S63 | Não há política de força de senha — "password" e 8 espaços em branco são aceitos | baixo | backend/auth| `backend/app/schemas/user.py:11 (password: Field(min_length=8, max_length=128))` | convertido-em-melhoria | — | — |
| S64 | Login sem rate limiting / proteção contra força bruta | baixo | backend/auth| `backend/app/api/v1/auth.py:52-65 (e backend/app/main.py:42-64, sem middleware de throttling)` | convertido-em-melhoria | — | — |
| S65 | pyproject declara as dependências de dev em dois blocos com versões divergentes | baixo | backend/build| `backend/pyproject.toml:104` | aberto | — | — |
| S66 | Lembretes não podem ser editados (só criar/pausar/excluir) — schema ReminderUpdate existe mas não há endpoint | baixo | backend/lembretes| `backend/app/api/v1/reminders.py (só GET/POST/POST batch/PATCH toggle/DELETE) e backend/app/schemas/reminder.py:69-85 (ReminderUpdate exportado em schemas/__init__.py:20,53 e nunca consumido)` | convertido-em-melhoria | — | — |
| S67 | Registros de peso e de humor não podem ser excluídos nem editados individualmente | baixo | backend/logs| `backend/app/api/v1/weight.py (só GET e POST) e backend/app/api/v1/mood.py (só GET e POST) — compare com backend/app/api/v1/hydration.py:50-71, que tem DELETE e PUT` | convertido-em-melhoria | — | — |
| S68 | PUT /users/me/profile com activity_level: null derruba a requisição com 500 (KeyError: None) | baixo | backend/perfil| `backend/app/services/profile_service.py:84 (via backend/app/services/nutrition/tdee.py:39)` | aberto | — | — |
| S69 | POST /meals com food_id inexistente retorna 500 (IntegrityError não tratada) em vez de 422 | baixo | backend/refeicoes| `backend/app/services/meal_service.py:60` | aberto | — | — |
| S70 | PATCH /users/me aceita nome só com espaços e calorie_goal sem limite superior | baixo | backend/users| `backend/app/schemas/user.py:20` | aberto | — | — |
| S71 | Usuário já autenticado consegue abrir /login e /register normalmente | baixo | frontend/auth| `frontend/middleware.ts:11` | aberto | — | — |
| S72 | Hidratação: valor negativo ou zero em 'Outro valor (ml)' é descartado em silêncio, sem qualquer mensagem | baixo | frontend/hidratacao | `frontend/app/(dashboard)/hidratacao/page.tsx:76-80 (guard `if (!Number.isFinite(ml) \|\| ml <= 0) return;`) e :195-202 (botão comum com onClick, fora de <form>)` | aberto | — | — |
| S73 | Toast duplicado ao registrar humor | baixo | frontend/humor | `frontend/app/(dashboard)/humor/page.tsx:107 (`toast.success("Humor registrado!")`) + frontend/lib/hooks/useLogs.ts:137-140 (onSuccess já dispara toast.success)` | aberto | — | — |
| S74 | Lembretes: ícones de play/pause invertidos em relação à ação | baixo | frontend/lembretes| `frontend/app/(dashboard)/lembretes/page.tsx:431-440` | aberto | — | — |
| S75 | Lembretes: card repete o tipo duas vezes (texto + badge idênticos) | baixo | frontend/lembretes| `frontend/app/(dashboard)/lembretes/page.tsx:408-417` | aberto | — | — |
| S76 | Erro 422 do backend vira exceção não tratada no navegador (pageerror) em Peso e Hidratação | baixo | frontend/peso | `frontend/app/(dashboard)/peso/page.tsx:40-46 (`await logWeight.mutateAsync(...)` sem try/catch) e frontend/app/(dashboard)/hidratacao/page.tsx:64-69 (`await updateHydration.mutateAsync(...)` em saveEdit)` | aberto | — | — |
| S77 | Texto acima de 2000 caracteres retorna erro genérico, sem limite nem contador no campo | baixo | frontend/refeicoes| `frontend/app/(dashboard)/refeicoes/page.tsx:639` | aberto | — | — |
| S78 | Diálogos de refeição sem aria-describedby disparam warning de acessibilidade do Radix no console | baixo | frontend/refeicoes| `frontend/app/(dashboard)/refeicoes/page.tsx:581` | aberto | — | — |
| S79 | Não é possível corrigir data nem horário de uma refeição (o modelo não tem horário) | baixo | frontend/refeicoes| `frontend/app/(dashboard)/refeicoes/page.tsx:830` | convertido-em-melhoria | — | — |
| S80 | Textos com pluralização e capitalização incorretas em Hidratação, Lembretes e Humor | baixo | frontend/ui| `frontend/app/(dashboard)/hidratacao/page.tsx:358-361 ('dias' fixo); frontend/app/(dashboard)/lembretes/page.tsx:159-165 ('pausados' fixo); frontend/app/(dashboard)/humor/page.tsx:273-275 (className 'capitalize' sobre toLocaleDateString)` | aberto | — | — |
| S81 | `make hooks` falha porque pre-commit não é verificado por `check-deps` | baixo | infra/makefile| `Makefile:289` | aberto | — | — |

## Adiados — e por quê

A correção desta sessão foi deliberadamente estreita: o pedido central era tornar
o registro de refeições determinístico e caloricamente preciso, e é ali que o
esforço foi concentrado, com medição antes e depois. Corrigir 81 achados sem
medir cada um repetiria exatamente o padrão que este trabalho veio desfazer
(a migration `20260320_e6f7a8b9c0d1_fix_search_text_taco.py` é um ajuste manual
de sete alimentos para "ganhar" score — remendo sem medição).

Os achados abertos estão agrupados por tema para virarem lotes próprios:

- **Segurança e autorização** — sequestro de subscription push, usuário
  desativado com token válido, chave VAPID embutida na imagem de produção,
  `SECRET_KEY` com default inseguro sem fail-fast. Merece lote próprio com
  `/security-review`, por tocar área de alto risco da constitution.
- **Validação de entrada** — datas futuras aceitas em refeição/peso/hidratação/
  humor, `birth_date` no futuro gerando TDEE de 14.116 kcal, campos sem limite
  superior. Tema homogêneo, corrigível em bloco.
- **Infraestrutura e build** — Makefile com portas antigas, `alembic downgrade`
  quebrado, drift entre models e migrations, containers dev como root escrevendo
  no bind mount, `make check` divergente do CI.
- **Frontend** — achados do QA manual, majoritariamente de estado de UI e
  tratamento de erro.

## Rastreabilidade

- Bug de origem do trabalho: [`bugs/001-fluxo-cadastro-refeicao.md`](../bugs/001-fluxo-cadastro-refeicao.md)
- Decisão de limiares: [`decisions/2026-07-26-limiares-lookup-nutricional.md`](../decisions/2026-07-26-limiares-lookup-nutricional.md)
- Artefatos de medição: [`artefatos/`](artefatos/)

---
versão: 1.0
id: "003"
slug: 003-gamificacao
título: "Gamificação: streak, floresta/avatar e progresso visual"
tipo: módulo novo
área: fullstack
esforço: médio
prioridade: média
status: a fatiar
criada: 2026-07-09
atualizada: 2026-07-09
proposta_por: owner
linked_spec: —
---

# MELHORIA 003 — Gamificação

## Relato original (owner)

> Quero implantar um processo de gamificação, no qual torna divertido usar o
> aplicativo, criando uma espécie de ação tipo o Duolingo, que você vai
> acumulando os dias e consegue "plantar sua floresta" — cada dia feito ok é uma
> árvore nova plantada na floresta, ou então 1kg de massa no boneco virtual que o
> usuário personaliza... algo do tipo, sabe? Para engajar e enxergar o progresso
> visualmente.

## Problema / valor

Diário alimentar é um produto de **retenção difícil**: o custo de registro é
diário e o benefício é diferido. A metáfora visual acumulativa (floresta, avatar)
transforma consistência em artefato visível — o mesmo mecanismo do Forest e do
Duolingo.

Para um projeto pessoal de estudo, é também a feature de maior retorno sobre a
motivação do próprio owner em manter o app vivo.

## Escopo proposto (a validar)

### Fatia 1 — Motor de streak
- `UserStreak` / `DailyGoalLog` — o que é "um dia feito ok" precisa ser um
  registro auditável, não um cálculo ad-hoc no front.
- Cálculo em Celery Beat no fechamento do dia (já há `celery_beat` rodando), no
  fuso do usuário. Fechar o dia no servidor evita gaming por mudança de fuso.
- Streak atual, recorde, e política de "congelamento" (ver questões).

### Fatia 2 — Representação visual
- A floresta (ou avatar) como estado derivado do streak. Uma árvore por dia ok.
- Renderização: SVG/Canvas gerado no front a partir de um seed determinístico
  (`user_id` + índice do dia) → cada floresta é única e reproduzível, sem
  armazenar posições. Combina com o design glassmorphism existente.

### Fatia 3 — Marcos e reforço
- Conquistas por marco (7, 30, 100 dias; primeiro PR de treino; etc.).
- Notificação de streak em risco via Web Push (infra já existe: `PushService`,
  `Reminder`, `PushSubscription`).

## Questões em aberto (decisão do owner)

- **[decisão de produto — a mais importante]** **O que conta como "dia feito
  ok"?** Toda a mecânica depende disso, e a escolha tem consequência ética real.
  - *Registrar todas as refeições* → premia o **hábito de registrar**. Honesto e
    alinhado ao propósito do app.
  - *Bater a meta calórica* → premia o **resultado**. Cria incentivo a
    sub-registrar comida para não "perder o streak", corrompendo exatamente o dado
    que o produto existe para coletar. **Contraindicado.**
  - Recomendação forte: gamificar o registro, nunca o déficit.
- **[decisão de produto]** Floresta **ou** avatar ("1kg de massa no boneco")? São
  metáforas diferentes: a floresta representa **consistência** (acumula com o
  tempo); o avatar representa **resultado corporal** (acumula com o físico). O
  avatar tem risco: ganho/perda de peso é fisiologia, não mérito, e representá-lo
  como pontuação pode virar gatilho ruim. A floresta é a aposta segura. Decidir —
  ou fazer a floresta primeiro e avaliar o avatar depois.
- **[decisão de produto]** Streak quebra com um dia perdido? Duolingo vende
  "freezes" porque quebra total faz o usuário **abandonar**, não voltar. Sugerir:
  N congelamentos por mês, automáticos e silenciosos.
- **[decisão de produto]** Retroatividade: registrar ontem hoje conta para o
  streak de ontem? Se sim, o streak é editável; se não, penaliza esquecimento.
- **[técnica]** Recalcular streak de forma idempotente (Celery pode reexecutar).
  O log diário resolve isso; o cálculo derivado não.

## Dependências

- Nenhuma bloqueante.
- Reusa `PushService` / Web Push para lembretes de streak.
- Sinergia com [`melhorias/001`](001-modulo-treino.md) — treino registrado pode
  contar como dia ok (ou como categoria própria de conquista).

## Notas de esforço

Backend é simples (log diário + agregação). **O custo real está no visual** — uma
floresta feia não engaja, e é justamente o ponto da feature. Orçar tempo de design
de verdade, não só implementação. A infra de tema (glassmorphism/neumorphism,
`frontend/app/globals.css`) dá a paleta de partida.

Recomendação: MVP = motor de streak + contador visível + floresta simples. Marcos
e notificações numa segunda spec.

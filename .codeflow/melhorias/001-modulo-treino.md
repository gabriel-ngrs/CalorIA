---
versão: 1.0
id: "001"
slug: 001-modulo-treino
título: Módulo de registro de treino + gasto energético real
tipo: módulo novo
área: fullstack
esforço: alto
prioridade: alta
status: a fatiar
criada: 2026-07-09
atualizada: 2026-07-09
proposta_por: owner
linked_spec: —
---

# MELHORIA 001 — Módulo de registro de treino

## Relato original (owner)

> Quero implantar um registro de treino, no qual seria um módulo novo que o
> usuário pode cadastrar seus exercícios fixos e cada dia ele entra, registra as
> séries, repetições, peso... para monitorar evolução. E isso também deve ser uma
> forma de monitorar o gasto energético do dia, para fazer uma média do gasto
> calórico dele mais preciso do que estimativas matemáticas.

## Problema / valor

São **dois valores distintos** num pedido só, e vale separá-los porque têm
dificuldade muito diferente:

1. **Acompanhar evolução de carga** (séries × reps × peso ao longo do tempo).
   Problema bem definido, CRUD + gráfico. Valor imediato.
2. **Substituir a estimativa matemática de TDEE por gasto medido.** Problema
   aberto e cientificamente delicado — ver "Questões em aberto".

Hoje o gasto energético vem de Mifflin-St Jeor com fator de atividade fixo
(`backend/app/services/nutrition/`, ver spec 001 fases A.2–A.4). O fator de
atividade é um multiplicador declarado pelo usuário, não observado.

## Escopo proposto (a validar)

### Fatia 1 — Catálogo de exercícios e treinos fixos
- `Exercise` — catálogo (nome, grupo muscular, tipo: força/cardio, equipamento).
  Decidir: catálogo global semeado (como `foods`) vs. por usuário vs. híbrido.
- `WorkoutTemplate` + `WorkoutTemplateItem` — o "treino fixo" (ex.: Treino A —
  peito/tríceps), com exercícios ordenados e séries-alvo.

### Fatia 2 — Registro diário
- `WorkoutSession` — sessão de um dia (data, template de origem, duração, notas).
- `WorkoutSet` — série individual (exercício, ordem, reps, peso, RPE opcional).
- UI de registro rápido: abrir template → preencher séries → salvar. Deve ser
  usável com uma mão, na academia, com a tela suja. Prioridade de UX alta aqui.

### Fatia 3 — Evolução
- Gráficos por exercício: carga máxima, volume total (`Σ reps × peso`), 1RM
  estimado (Epley/Brzycki). Recharts, como os gráficos de peso.
- Recordes pessoais (PRs) e detecção de platô.

### Fatia 4 — Gasto energético
- Estimativa de kcal por sessão. Ver "Questões em aberto" antes de especificar.
- Integrar ao TDEE: substituir o fator de atividade fixo por gasto observado.

## Questões em aberto (decisão do owner / pesquisa necessária)

- **[decisão de produto]** O gasto de treino de força é notoriamente difícil de
  estimar. A literatura usa METs (Compendium of Physical Activities), que dá
  valores por *modalidade e intensidade*, não por `séries × reps × peso`. Um
  método baseado em volume de carga é possível mas **não tem base validada**.
  Precisamos escolher entre: (a) METs por modalidade + duração — simples,
  impreciso, honesto; (b) fórmula sobre volume de carga — parece preciso,
  procedência duvidosa; (c) integração com wearable (HR real) — preciso, exige
  hardware. **Não chutar.** `[não verificado]` — nenhuma fonte consultada ainda.
- **[decisão de produto]** Substituir o TDEE calculado ou apresentar os dois lado
  a lado? Trocar silenciosamente um número que o usuário já acompanha é hostil.
- **[decisão de produto]** EPOC / gasto pós-treino entra na conta? Se sim, o gasto
  de hoje depende do treino de ontem — complica o modelo de dia fechado.
- **[técnica]** O catálogo de exercícios é global e semeado (script em
  `backend/scripts/`, como TACO) ou o usuário cadastra o dele? Híbrido tem o
  mesmo problema de dedupe que `foods`.
- **[técnica]** Cardio e força têm modelos de série muito diferentes (reps×peso
  vs. distância×tempo). Um modelo só com colunas nulas, ou dois modelos?

## Dependências

- Nenhuma bloqueante. Independe de [`bugs/001`](../bugs/001-fluxo-cadastro-refeicao.md).
- Toca `User` e o serviço de TDEE (fatia 4) — coordenar com spec 001 fase A.

## Notas de esforço

Fatias 1–3 são CRUD + gráficos, esforço médio e risco baixo. **A fatia 4 é o
verdadeiro custo** e deve ser especificada separadamente, depois de resolvidas as
questões em aberto. Recomendação: fatiar 1–3 numa spec e a 4 em outra, para não
travar o valor imediato atrás de um problema de pesquisa.

---
data: 2026-08-03
titulo: "\"Licença detectada pela API\" migra do AC-18 (D.1) para o AC-19 (D.2)"
status: ativa
tags: [vitrine, licenca, github, spec-002, fase-d1, fase-d2, modelagem-de-ac]
spec: 002-vitrine-eval-e-saneamento
fase: D.1
---

# "Licença detectada" migra do AC-18 para o AC-19

## Contexto

O AC-18 exigia que a API do GitHub reportasse **licença MIT detectada**, e a Fase
D.1 é quem responde por ele. Medido em 2026-08-03:

```text
$ gh repo view gabriel-ngrs/CalorIA --json licenseInfo,description,repositoryTopics
{"licenseInfo": null,
 "description": "Diário alimentar com IA: eval do pipeline de LLM versionado junto do código",
 "repositoryTopics": [fastapi, groq, llm-eval, nextjs, postgresql, python]}
$ git show origin/main:LICENSE   → não existe
$ head -1 LICENSE                → MIT License   (correto, na dev)
```

O GitHub deriva `licenseInfo` do **branch default**. O default é `main`, e `main`
parou em 2026-04-29. O `LICENSE` está criado, correto e commitado — não há defeito
no repositório local. O que falta é o branch default avançar, e isso é a Fase D.2.

Até 2026-08-03 isso era só "esperar a D.2 rodar". A OQ15 mudou o quadro: o owner
decidiu que a `main` **não é tocada em momento nenhum antes do fim da spec**. A
D.1 passou a ter, no seu critério de conclusão, uma cláusula que ela não pode
satisfazer nem esperando pouco — e que uma avaliação honesta tem de manter aberta
indefinidamente.

A avaliação da tentativa 2 (RESSALVAS, score 9.4) nomeou as duas saídas legítimas:
executar a D.2 agora, ou corrigir o grafo movendo a cláusula para o AC da D.2.

## Decisão

**Mover a cláusula para o AC-19**, que já é o AC da Fase D.2.

- **AC-18** passa a exigir o que a D.1 controla: description e topics não vazios,
  `LICENSE` (MIT) versionado na branch de trabalho, e versão sincronizada nos
  quatro arquivos.
- **AC-19** ganha a cláusula: além de `main` alcançar `dev` e da release anotada,
  a API passa a reportar `licenseInfo` não nulo — que é justamente o efeito de
  promover o branch default.

A alternativa recomendada pelo avaliador (executar a D.2 agora) foi **descartada
por conflito com decisão vigente**: a OQ15 é uma decisão de owner tomada um dia
antes, com justificativa própria (não publicar estado intermediário na branch que
o mundo vê). Uma fase de execução não revoga decisão de owner para fechar o
próprio gate.

**Precedente idêntico já aplicado nesta spec:** na Fase A.1, a cláusula "o HEAD de
toda branch remota está livre da credencial" migrou do AC-1 para o AC-2, pela
mesma razão — só era satisfazível depois do force-push da A.2, não pela A.1
isolada.

## Alternativas descartadas

- **Executar a D.2 agora.** Ver acima: contraria a OQ15.
- **Deixar o AC-18 como estava e aprovar a D.1 assim mesmo.** Rejeitado: gravaria
  no pipeline que a licença está detectada quando a API responde `null`. É o
  desfecho que o avaliador explicitamente recusou.
- **Deixar a D.1 em RESSALVAS até o fim da spec.** Foi o estado até aqui, e é o
  que motivou este registro: com o teto de 3 vereditos não-APROVADO (§2.11.4), uma
  fase que não pode fechar por modelagem consome tentativas até escalar ao owner
  por um motivo que não é defeito de execução.
- **Remover a cláusula da spec.** Rejeitado: a licença detectada é sinal real de
  vitrine (FR-D1 existe por isso). Ela não sai da spec — muda de dono.

## Consequência

- A D.1 passa a ser fechável hoje: description e topics preenchidos (verificados),
  `LICENSE` MIT commitado, versão `0.7.0` igual em `CHANGELOG.md`,
  `backend/pyproject.toml`, `backend/app/main.py` (via `APP_VERSION`) e
  `frontend/package.json`.
- A D.2 herda a verificação: quem executar a promoção tem de rodar
  `gh repo view --json licenseInfo` e anexar a saída.
- **Risco:** se a D.2 nunca rodar, a licença nunca aparece detectada. O risco não
  muda com esta decisão — só passa a estar registrado no lugar certo do grafo, em
  vez de manter uma fase concluída presa a um efeito de outra.

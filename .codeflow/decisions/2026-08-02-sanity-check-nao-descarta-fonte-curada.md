---
data: 2026-08-02
titulo: Sanity check calórico não descarta match de fonte curada
status: ativa
tags: [ai, sanity-check, food-lookup, eval, spec-002, adr-006]
---

# Sanity check calórico não descarta match de fonte curada

## Contexto

O ADR-006 criou o sanity check calórico: quando as calorias do banco divergem
mais de 35% da estimativa da IA, o match do banco é **descartado** e o item passa
a usar a estimativa da IA. O propósito declarado, tanto no ADR quanto no
`CLAUDE.md` e na constitution do projeto, é **proteger contra registros
incorretos do Open Food Facts** — importação automática, sem curadoria.

O harness de eval da spec 002 mediu o efeito real pela primeira vez
(2026-08-02, `evals/runs/history.jsonl`):

| estrato | n | MdAPE | dentro de ±10% |
|---|---|---|---|
| simples | 6 | 1,26% | 100% |
| **composto** | 4 | **23,81%** | **25%** |

O log da execução mostra a causa em 3 dos 4 pratos compostos:

```
Sanity check falhou para 'feijoada completa': banco=110 kcal vs IA=350 kcal
  (divergência=69%, source=taco) — usando estimativa IA
Sanity check falhou para 'strogonoff de carne': banco=155 vs IA=350 (56%) source=taco
```

A IA estima a **porção inteira** do prato (~350 kcal) para uma descrição de
100 g. O banco, na fonte curada `taco`, tem o valor certo (110 kcal/100g). O
check então descarta o dado bom e adota o ruim.

A bateria de invariância confirmou o mesmo mecanismo noutro caso: `500 g de
arroz cozido` deu 1120 kcal (estimativa da IA) contra 640 kcal de
`0,5 kg de arroz cozido` — o valor correto do banco. Mesma refeição, spread 1,75,
porque num dos lados o check disparou e no outro não.

## Decisão

**O sanity check deixa de descartar o match quando a fonte é curada.** Em
`_FONTES_CURADAS` (hoje: `taco`), uma divergência alta:

- **mantém** o valor do banco;
- registra a divergência em log (`INFO`, não `WARNING`);
- marca o item com `needs_review` e motivo explicando que a estimativa da IA
  divergiu e que o valor exibido é o da fonte curada.

Para as demais fontes (`openfoodfacts`, `fatsecret`, `usda`), o comportamento
**não muda**: divergência acima de 35% continua descartando o match.

Aplicado nos dois parsers — `meal_parser.py` e `vision_parser.py`, que importa
`_FONTES_CURADAS` de lá para não divergir.

## Justificativa

O check foi criado para desconfiar de **importação automática**, não de fonte
curada à mão. Quando a fonte é curada, uma divergência grande é evidência de que
**a IA errou**, não de que o banco está errado — e trocar um valor curado por uma
estimativa piora o resultado, como a medição demonstra.

A divergência continua sendo um sinal útil, então não é jogada fora: vira
`needs_review`, que o frontend já exibe. O usuário vê o valor melhor disponível e
sabe que vale conferir.

## Consequências

- O estrato `composto` do eval deve melhorar substancialmente; a medição
  antes/depois fica registrada em `evals/runs/history.jsonl`.
- Mais itens virão com `needs_review=True`. É intencional: a informação que
  antes justificava descartar o dado agora justifica pedir confirmação.
- O limiar de 35% **não** mudou. O que mudou foi o **escopo** de quem ele
  descarta, que volta a ser o declarado no ADR-006.
- Nenhuma migration; nenhuma mudança de contrato de API.

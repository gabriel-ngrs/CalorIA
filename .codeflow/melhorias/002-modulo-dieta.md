---
versão: 1.0
id: "002"
slug: 002-modulo-dieta
título: Módulo de dieta prescrita via upload (PDF/TXT/imagem) com extração por IA
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

# MELHORIA 002 — Módulo de dieta prescrita

## Relato original (owner)

> Quero implantar um módulo de dieta, no qual o usuário coloca a dieta via PDF,
> TXT, print e a IA preenche os campos. Pode servir para sugerir melhorias,
> sugestões de alimentos e esse tipo de coisa.

## Problema / valor

Hoje o CalorIA registra o que foi comido e compara com uma **meta calórica
numérica**. Uma dieta prescrita por nutricionista é mais rica: tem refeições
nomeadas, alimentos específicos, quantidades e substituições permitidas.

Com a dieta estruturada no sistema, abrem-se três usos:
1. **Aderência** — comparar o registrado com o prescrito, por refeição.
2. **Sugestão** — "faltam 30g de proteína no seu almoço; a dieta permite trocar
   X por Y".
3. **Pré-preenchimento** — registrar refeição em 1 toque a partir do prescrito.

O item 3 tem sinergia forte com [`bugs/001`](../bugs/001-fluxo-cadastro-refeicao.md):
alimento vindo da dieta prescrita tem **quantidade declarada**, e não estimada
pela IA. Isso contorna a causa-raiz do bug 001 (achado A) para o caminho mais
comum de uso.

## Escopo proposto (a validar)

### Fatia 1 — Ingestão do documento
- Upload de PDF, TXT e imagem (print). PDF e imagem são caminhos técnicos
  distintos: PDF com camada de texto → extração direta; PDF escaneado e print →
  visão.
- O `VisionParser` (`backend/app/services/ai/vision_parser.py`) já usa
  `llama-4-scout` e serve de base para o caminho de imagem.
- **Privacidade:** o documento é descartado após extração, como as fotos de
  comida (CLAUDE.md § Notas Importantes). Só os dados estruturados persistem.

### Fatia 2 — Extração estruturada
- Prompt de extração → `DietPlan` + `DietMeal` + `DietMealItem` + substituições.
- **Tela de revisão obrigatória.** Extração por IA de documento livre erra; o
  usuário confirma/corrige antes de salvar. Não gravar direto.
- Reaproveitar `extract_json_from_ai_response` (`backend/app/services/ai/utils.py`).

### Fatia 3 — Uso da dieta
- Aderência por refeição no dashboard.
- Pré-preenchimento de refeição a partir do prescrito.
- Sugestões via `InsightsGenerator` com a dieta injetada no `ContextBuilder`.

## Questões em aberto (decisão do owner)

- **[decisão de produto — importante]** "Sugerir melhorias" numa dieta prescrita
  por um profissional é território sensível. O app vai **contestar** a prescrição
  do nutricionista? Sugerimos limitar a: substituições **já permitidas pela
  própria dieta**, e alertas de aderência ("você não bateu a proteína"), sem
  propor alterações à prescrição. Precisa de decisão explícita — há risco de
  responsabilidade além do risco de produto.
- **[decisão de produto]** Uma dieta ativa por vez, ou histórico de dietas com
  vigência (`valid_from`/`valid_to`)? O histórico permite ver evolução entre
  prescrições — provavelmente vale.
- **[decisão de produto]** Quando o registrado diverge do prescrito, o app avisa?
  Com que tom? Um diário alimentar que repreende é um diário abandonado.
- **[técnica]** Os alimentos da dieta viram FK para `foods`, ou texto livre? FK dá
  macros de graça mas o lookup vai falhar em boa parte (mesmo problema do bug
  001). Provável: texto livre + `food_id` nullable, resolvido na revisão.
- **[técnica]** Tamanho máximo de upload e limites do free tier do Groq para
  documentos longos (dieta de várias páginas). Medir antes de prometer.

## Dependências

- **Sinergia forte** com [`bugs/001`](../bugs/001-fluxo-cadastro-refeicao.md): a
  qualidade da FK para `foods` depende do lookup. Investigar o bug 001 primeiro
  informa a decisão técnica acima.
- Sinergia com [`melhorias/004`](004-contexto-de-refeicao.md): a dieta prescrita
  é, ela própria, uma forma forte de contexto para o `ContextBuilder`.
- Reusa infra de IA existente (`AIClient`, `VisionParser`).

## Notas de esforço

Fatias 1–2 são o núcleo e o risco (extração confiável de documento livre). A
fatia 3 é incremental e pode ser adiada. Recomendação: MVP = upload + extração +
revisão manual + visualização. Aderência e sugestões numa segunda spec.

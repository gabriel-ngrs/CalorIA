---
data: 2026-08-03
titulo: JSON mode entra por versão nova de prompt, e produção só troca com medição
status: ativa
tags: [ai, prompts, json-mode, eval, spec-002, fase-c2]
---

# JSON mode entra por versão nova de prompt, e produção só troca com medição

## Contexto

O passo 2 da fase C.2 pede `response_format={"type": "json_object"}` nas chamadas
cuja saída é JSON. A fase não o entregou, e por um motivo correto: o JSON mode da
API **recusa array no topo**, e os quatro prompts de produção declaram
`FORMATO OBRIGATÓRIO (array JSON)`; os parsers fazem
`[IdentifiedFood(**item) for item in data]`, esperando `list`. Ligar o JSON mode
sem mexer no prompt quebraria a resposta; mexer no prompt é o que a C.1 veda sem
bump de versão, e moveria a linha de base do eval no mesmo passo.

O escopo travado da própria C.2 manda "parar e reportar" nesse caso, e foi o que
o executor fez. A avaliação devolveu o item como RESSALVAS (C2-IMP-1) porque
FR-C2 ficava parcial e a saída dependia de decisão do owner.

**Decisão do owner em 2026-08-03: implementar agora.**

## Decisão

Três partes:

1. **Versões novas dos quatro prompts**, com topo em objeto — `meal_identify@v2`,
   `meal_fallback@v2`, `vision_identify@v3`, `vision_fallback@v2`. O delta
   entre a versão vigente e a nova é **só o bloco FORMATO**
   (`[...]` → `{"itens": [...]}`) e a frase final da user message, quando existe.
   Um teste verifica isso byte a byte
   (`test_o_delta_da_versao_nova_e_so_o_bloco_de_formato`): qualquer outra
   diferença tornaria a comparação v1 vs v2 ininterpretável, que é exatamente o
   que o eval existe para evitar.

2. **`response_format` amarrado à versão do prompt**, não a uma flag solta.
   `PromptVersion.topo_objeto` responde se aquela versão declara objeto, a partir
   de `_TOPO_OBJETO` em `app/prompts/__init__.py`; os parsers passam
   `json_object=<prompt>.topo_objeto`. Não há como ligar o JSON mode numa versão
   que pede array. O parâmetro é **omitido** quando desligado, em vez de enviado
   como `None` — mandá-lo mudaria o payload de toda chamada e invalidaria os 14
   cassettes gravados sem nenhuma mudança de comportamento em troca.

3. **Produção continua nas versões medidas.** `VERSOES_EM_PRODUCAO` fixa
   `meal_identify@v1`, `meal_fallback@v1`, `vision_identify@v2`,
   `vision_fallback@v1`, e `get_prompt(nome)` resolve por essa tabela — não mais
   pela maior versão disponível. Promover é editar a tabela, do mesmo jeito que
   criar uma migration não a aplica.

`extract_json_from_ai_response` passa a aceitar as duas formas de topo (array e
objeto com `itens`), continuando a ser a rede de segurança que a spec pede mesmo
com o formato garantido pela API.

## Justificativa

Ligar o JSON mode e promover as versões novas no mesmo passo trocaria o prompt de
produção **sem medição**, e faria os 14 cassettes deixarem de casar — o eval em
replay passaria a estourar com `CassetteAusenteError` e o harness inteiro do
Track C ficaria inutilizável até haver quota para regravar. Como a quota do free
tier da Groq está esgotada (risco R5, materializado duas vezes), promover agora
seria trocar o prompt no escuro e quebrar a única ferramenta capaz de dizer se a
troca foi boa.

Separar "existir" de "estar em produção" entrega FR-C2 por inteiro e deixa a
promoção como uma linha de diff, decidida com número na mão.

Efeito colateral bem-vindo: até aqui, largar um `vN.txt` na pasta trocaria o
prompt de produção em silêncio. Agora não troca.

## Consequências

- **FR-C2 deixa de ser parcial no código e passa a ser parcial na medição.** O
  que falta para fechar é uma execução do runner comparando v1 e v2, que exige
  quota. Enquanto isso não sair, as versões novas são código exercitado por
  teste e não exercitado pelo provedor.
- A chave de cache do Redis ganhou um segmento `[JSON]`, então o cache vigente é
  invalidado uma vez. Sem custo: TTL de 7 dias, e o cache não é fonte de verdade.
- Quando a medição sair e for favorável, promover é editar `VERSOES_EM_PRODUCAO`,
  atualizar `SHA_TRAVADO` em `tests/unit/test_prompt_registry.py` e
  `SNAPSHOT_DE_PAYLOAD` em `tests/unit/test_evals_snapshot.py`, e regravar os
  cassettes com `EVAL_RECORD_CASSETTES=1`. Os três travamentos vão falhar juntos
  e de propósito — é o gate funcionando.
- Se a medição for desfavorável, as versões novas ficam no disco como registro do
  que foi testado. Não há reversão a fazer.

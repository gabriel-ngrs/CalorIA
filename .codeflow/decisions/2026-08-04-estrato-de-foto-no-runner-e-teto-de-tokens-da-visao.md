---
data: 2026-08-04
titulo: Estrato de foto entra no runner do eval, e o teto de tokens da visão estoura o TPM
status: ativa
tags: [eval, vision, runner, groq, rate-limit, spec-002, fase-b5, fase-c2, fase-c5]
---

# Estrato de foto entra no runner do eval, e o teto de tokens da visão estoura o TPM

## Contexto

A Fase B.5 corrigiu o `VisionParser` (propagação do bug 001) e ficou parada num
único item do seu próprio gate: *"delta do estrato de foto registrado no
relatório com números antes e depois"*. A avaliação da tentativa 1 (RESSALVAS,
9.7, achado B5-IMP-1) confirmou que o item não era satisfazível então — o estrato
`foto` do dataset estava vazio. O owner decidiu em 2026-08-03 manter o gate e
reabrir a fase depois da C.4, que passou a `Depende de: C.4`.

A C.4 populou o estrato (3 casos, imagens do Wikimedia versionadas). Ao retomar,
dois fatos apareceram, e nenhum dos dois cabe no conjunto de arquivos que a §5
declara para a B.5.

## Decisão 1 — o caminho de foto do runner é entregue pela B.5

`backend/evals/runner.py` excluía o estrato de foto com um comentário que já
atribuía o caminho a esta fase:

```python
if c.estrato is not Estrato.FOTO  # o caminho de foto entra na fase B.5
```

Ou seja: a C.5 desenhou o runner deixando este pedaço explicitamente para cá, e
a linha estava no código aprovado da C.5. Ainda assim, `evals/runner.py` **não
consta** dos "Arquivos alterados" da B.5, e `backend/tests/unit/test_evals_runner_foto.py`
é arquivo novo não declarado. Registro aqui, pelo item final do §9 do DoD.

O que entrou, com diff mínimo:

| Mudança | Por quê |
|---|---|
| `identificar()` roteia por estrato — foto pelo `VisionParser`, resto pelo `MealParser` | é o parser que o usuário aciona ao fotografar; medir outra coisa mediria outra coisa |
| `imagem_do_caso()` levanta quando a imagem falta | caso de foto sem imagem tem de virar falha registrada, não sumir do denominador |
| `versao_de_visao()` — context manager que troca `_IDENTIFY_PROMPT` e restaura | medir uma versão não pode exigir **promovê-la** em `VERSOES_EM_PRODUCAO`; mesmo padrão global-e-restaurado de `instrumentar_lookup` |
| `--versao-vision` na CLI | torna o "antes e depois" um comando reproduzível, não um script de uma vez |
| o relatório declara `vision_identify`/`vision_fallback` quando houve foto | sem isso o histórico append-only da C.8 registraria o resultado da v1 sob o `sha` da v2 |

**Não** foi tocado: `VERSOES_EM_PRODUCAO` (a v2 já era produção), o dataset da
C.4, os limiares da decision de 2026-07-26, `meal_parser.py`, nem
`vision_parser.py` — a B.5 já o havia corrigido na tentativa 1.

## Decisão 2 — o achado do HTTP 413 é registrado, não corrigido aqui

A primeira execução, com a configuração de produção, falhou nos **três** casos:

```text
APIStatusError: Error code: 413 — Request too large for model `qwen/qwen3.6-27b`
  on tokens per minute (TPM): Limit 8000, Requested 11357
```

O número `11357` é **idêntico** para as três imagens (111 KB, 200 KB e 291 KB),
o que descarta o tamanho do arquivo como causa: o modelo cobra a imagem por
custo fixo, e o que estoura o limite é o `max_tokens` reservado —
`GROQ_MAX_TOKENS = 8192` (`backend/app/core/config.py:85`, introduzido na C.2)
somado a ~3.165 tokens de prompt + imagem. Com `GROQ_MAX_TOKENS=2048` as mesmas
três chamadas passam.

Consequência que passa do eval: **a análise por foto está quebrada em produção
no free tier**, e não por falha do `VisionParser`. `frontend/app/(dashboard)/refeicoes/page.tsx:400`
e `frontend/components/dashboard/QuickAddModals.tsx:46` enviam o arquivo bruto em
base64, sem redimensionar, e o backend não redimensiona (`grep -rn "PIL\|resize"
backend/app/` → zero). Toda foto de celular cai no mesmo 413.

**Por que não corrigir agora:** o defeito é do teto de amostragem e/ou de um
redimensionamento ausente antes da chamada — território da C.2 (`ai_client.py`,
`config.py`) e do frontend, ambos fora do escopo travado da B.5, que proíbe
ampliar a fase. Pela política de falhas da constitution universal (falha de
**Escopo** → parar e reportar), fica registrado como achado, não como fix.

**Sugestão para quem pegar:** um `GROQ_VISION_MAX_TOKENS` próprio (a saída do
`vision_identify` é um JSON curto; 2048 sobrou) resolve o 413 sem tocar o teto
das chamadas de texto, e é diff menor que redimensionar a imagem.

## Consequência para a medição

As quatro execuções da B.5 rodaram com `GROQ_MAX_TOKENS=2048`, declarado no
campo `amostragem` de cada relatório. O delta v1→v2 continua válido — os dois
lados foram medidos sob o mesmo teto —, mas **nenhum dos números do estrato de
foto vale como linha de base da configuração de produção** enquanto o 413 não
for resolvido. Isso precisa ir junto do número, em qualquer lugar em que ele for
citado (README da D.3, histórico da C.8).

## Alternativas rejeitadas

1. **Redimensionar as imagens do dataset.** Faria o 413 sumir sem que ninguém
   soubesse que ele existe, e mexeria num entregável já aprovado da C.4 (o `sha`
   do dataset e a atribuição de licença das imagens do Wikimedia).
2. **Redimensionar dentro do runner.** O eval passaria a enviar algo diferente
   do que a produção envia, contra o princípio declarado no cabeçalho do próprio
   runner ("o que o eval mede é o que o usuário recebe").
3. **Baixar `GROQ_MAX_TOKENS` no `.env`/`config.py`.** É a correção certa, e é
   exatamente por isso que não é desta fase: muda o parâmetro de amostragem de
   **todas** as chamadas de texto, moveria a linha de base dos estratos `simples`
   e `composto` já medidos, e é decisão da C.2.

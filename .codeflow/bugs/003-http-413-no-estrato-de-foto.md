---
versão: 1.0
id: "003"
slug: 003-http-413-no-estrato-de-foto
título: "Análise por foto quebrada em produção: HTTP 413 por max_tokens reservado"
severidade: alto
área: backend/ai + frontend
status: aberto
criado: 2026-08-08
atualizado: 2026-08-08
reportado_por: medição da Fase B.5 (OQ19) e da Fase C.7 (execução completa do eval)
---

# BUG 003 — HTTP 413 no estrato de foto

Na configuração de produção, **toda análise de refeição por foto falha** no free
tier da Groq com `HTTP 413`. Não é um caso de borda: os três casos de foto do
dataset do eval falham, sempre, com o mesmo número.

## Sintoma medido

```text
HTTP 413 — Requested 11357 > TPM 8000
```

O `Requested 11357` é **idêntico** para imagens de 111 KB, 200 KB e 291 KB. O que
estoura o limite não é o tamanho da foto: é o `max_tokens` **reservado** na
requisição (`GROQ_MAX_TOKENS = 8192`, definido na Fase C.2), somado aos tokens da
imagem. Nem o frontend nem o backend redimensionam a imagem antes do envio.

Casos afetados no dataset do eval (`backend/evals/dataset/`), que são a lista
nominada do AC-15:

- `foto-coxinha-1-unidade`
- `foto-ovo-frito-1-unidade`
- `foto-banana-1-unidade`

## Onde está o defeito

| Camada | Arquivo | O quê |
|---|---|---|
| Config | `backend/app/core/config.py` | `GROQ_MAX_TOKENS = 8192` reservado também no caminho de visão, onde o TPM é 8000 |
| Cliente | `backend/app/services/ai/ai_client.py` | não diferencia o teto de saída do caminho de texto e o do caminho de visão |
| Frontend | envio da foto | nenhuma redução de resolução antes do upload |

Todos são **escopo da Fase C.2** (já concluída) e do frontend — fora do escopo
travado da B.5, que o mediu, e fora do escopo de qualquer fase remanescente da
spec 002. O Track C está fechado em oito fases (ARTIFACTS_SPEC §2.8.6, regra 3),
então o bug não tem fase para onde ir dentro daquela spec.

## Por que este registro existe

Além de ser um defeito de produção por si só, este bug é o **destino nomeado** de
uma cláusula de aceite que ficou órfã. O AC-15 da spec 002 exigia que a camada
completa do eval concluísse "sem casos vazios"; enquanto o 413 existir, ela sempre
terá exatamente estes três vazios. A OQ21 migrou a cláusula sem qualificador para
cá, com o mesmo rito da OQ18 (AC-18 → AC-19).

**Consequência enquanto estiver aberto:**

1. A análise por foto — funcionalidade de produto anunciada no README — não
   funciona em produção no free tier.
2. Toda execução agendada do eval reprova por três casos vazios.
3. Nenhum número do estrato de foto vale como linha de base **de produção**: as
   medições da B.5 rodaram com `GROQ_MAX_TOKENS=2048`, declarado no campo
   `amostragem` de cada relatório. O delta v1→v2 é válido (mesmo teto dos dois
   lados); o valor absoluto não é.

**Ao corrigir:** a cláusula "sem casos vazios" volta a valer sem exceção nominada,
e a nota do AC-15 na spec 002 deve ser removida junto — é a condição de fechamento
deste registro.

## Referências

- Spec 002, **OQ19** — medição original, na Fase B.5.
- Spec 002, **OQ21** — migração da cláusula do AC-15 para cá.
- Spec 002, **AC-15** e §9 (linha da C.7) — onde a exceção nominada está declarada.
- `.codeflow/decisions/2026-08-04-estrato-de-foto-no-runner-e-teto-de-tokens-da-visao.md`
- `.codeflow/decisions/2026-08-08-clausula-sem-casos-vazios-migra-da-c7-para-o-bug-003.md`

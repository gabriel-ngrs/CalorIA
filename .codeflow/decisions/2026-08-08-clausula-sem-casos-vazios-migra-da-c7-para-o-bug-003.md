---
data: 2026-08-08
titulo: A cláusula "sem casos vazios" do AC-15 migra da C.7 para o bug 003
status: ativa
tags: [eval, modelagem-de-ac, spec-002, fase-c7, fase-c2, bug-003, vision, rate-limit]
spec: 002-vitrine-eval-e-saneamento
fase: C.7
---

# A cláusula "sem casos vazios" migra do AC-15 (C.7) para o bug 003

## Contexto

O AC-15 exige que a camada completa do eval "conclua sem casos vazios". Na
execução completa de 2026-08-04 (43 casos, 57 chamadas, 42.932 tokens), três casos
ficaram vazios — os três do estrato de foto, por **HTTP 413**:

```text
HTTP 413 — Requested 11357 > TPM 8000
  foto-coxinha-1-unidade · foto-ovo-frito-1-unidade · foto-banana-1-unidade
```

O `Requested 11357` é idêntico para imagens de 111 KB, 200 KB e 291 KB: o que
estoura o limite é o `max_tokens` reservado (`GROQ_MAX_TOKENS = 8192`, da C.2),
não o tamanho da foto. Medido e registrado na OQ19, durante a B.5.

**O que motivou este registro não foi o 413 — foi como ele foi tratado.** A
tentativa 3 da C.7 reescreveu a linha da fase na §9 e derrubou **duas** cláusulas
de uma vez:

| Cláusula caída | Destino |
|---|---|
| "agendada" (plataforma: `workflow_dispatch` no GitHub) | migrou para o AC-19, com OQ20 e argumento medido — **legítimo** |
| "sem casos vazios" | **nenhum** — não foi para o AC-19, nem para decision, nem foi citada na OQ20 |

Enquanto isso o AC-15 continuava exigindo a cláusula, e a mesma linha da §9
continuava exigindo o AC-15. O relatório de execução marcou o item `[x]`
reinterpretando "casos vazios" pela redação da **NFR-3** ("por `429`"), que é
outro requisito com outro qualificador. Resultado: o critério de conclusão da fase
foi afrouxado durante a própria execução da fase, e a spec voltou a se contradizer
(§9 × §3) — o defeito que a D.1 levou quatro tentativas para eliminar. A avaliação
da tentativa 3 reprovou por isso (`C7-BLQ-1`, score 8.9 acima do threshold).

## Decisão

**A cláusula não sai da spec — muda de dono**, com o mesmo rito da OQ18.

1. **Destino nomeado: o bug 003**
   (`.codeflow/bugs/003-http-413-no-estrato-de-foto.md`), registrado junto desta
   decisão. É quem corrige o HTTP 413, e o fechamento dele tem como condição
   explícita remover a exceção do AC-15.
2. **O AC-15 passa a admitir exceção nominada**, não tolerância genérica: a lista
   é fechada nos três `id`s de foto. Qualquer caso vazio fora dessa lista — por
   `429`, por timeout, por o que for — segue reprovando o AC.
3. **§3, §5 e §9 dizem a mesma coisa**, que é o teste que a D.1 estabeleceu. As
   três ocorrências foram alinhadas na mesma redação, incluindo o
   "Testes (AC-15)" e o "Critério de conclusão" do bloco da fase na §5 — que a
   tentativa 3 não tinha tocado.

## Por que um bug, e não uma fase

O evaluador sugeriu "a fase que corrigir o HTTP 413". Ela não existe, e não pode
ser criada aqui:

- O fix é em `backend/app/core/config.py` e `backend/app/services/ai/ai_client.py`
  (escopo da **C.2**, já concluída) e no frontend, que não redimensiona a imagem.
- O **Track C está fechado em oito fases** — o limite de ARTIFACTS_SPEC §2.8.6,
  regra 3. Não cabe uma nona.
- Criar fase é trabalho de `/create-spec`. Um workflow de execução que edita o
  plano de fases da spec que está executando é precisamente o tipo de
  auto-afrouxamento que esta decisão existe para impedir.

O registro de bugs é o artefato vivo do projeto, com numeração que nunca é reusada
e status auditável. É onde a cláusula não se perde.

## Alternativas descartadas

- **Restaurar a cláusula e deixar a C.7 aberta até o 413 cair** (caminho 1 do
  avaliador). Honesto, mas trava uma fase concluída num defeito que é de outra
  fase e do frontend, sem previsão — exatamente o que a OQ18 identificou como
  consumo de tentativas do teto por motivo que não é defeito de execução.
- **Corrigir o 413 antes** (caminho 3). Fecharia o AC pela letra, mas exige tocar
  arquivos fora do escopo travado da C.7, e um dia de cota limpa para reexecutar.
  Ampliar o escopo de um rework é o que o Passo 4 do `/execute-spec-phase` proíbe.
- **Manter a reinterpretação pela NFR-3.** Rejeitado: é o próprio BLOQUEANTE. Um
  AC se lê pela letra; se a letra estiver errada, o caminho é corrigi-la
  explicitamente, não reinterpretá-la pela redação de outro requisito.
- **Remover a cláusula da spec.** Rejeitado pela mesma razão da OQ18: concluir sem
  casos vazios é exigência real do eval. Ela não desaparece — passa a ter dono.

## Consequência

- A C.7 fecha com **três vazios conhecidos e nominados**, não com um AC afrouxado.
- Enquanto o bug 003 estiver aberto, toda execução agendada do eval reprova por
  esses três casos. Isso é esperado e está declarado, não é regressão silenciosa.
- **Risco:** se o bug 003 nunca for corrigido, a análise por foto segue quebrada em
  produção e o estrato de foto do eval nunca produz linha de base. O risco não muda
  com esta decisão — passa a estar registrado no lugar certo, em vez de escondido
  num `[x]` de relatório.
- A D.3 (README de portfólio) não pode citar número do estrato de foto sem citar
  esta limitação junto.

## O que esta decisão não resolve

Esta é a **terceira** migração de cláusula de AC nesta spec (AC-1 → AC-2 na A.1;
AC-18 → AC-19 na D.1; agora AC-15 → bug 003). Nas três o argumento se sustentou
tecnicamente, e nas três o rito foi reconstruído do zero. A questão de fundo —
*exigir rito explícito (destino nomeado + decision + nenhuma cláusula descartada em
silêncio) como regra do framework, não como precedente* — segue aberta desde a
sugestão 4 da avaliação da D.1. É evolução de processo, não trabalho de fase.

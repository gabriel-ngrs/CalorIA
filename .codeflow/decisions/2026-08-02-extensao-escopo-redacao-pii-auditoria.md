---
data: 2026-08-02
titulo: Estender a redação de PII e do comando de extração a 10 documentos
status: ativa
tags: [seguranca, documentacao, pii, spec-002, fase-a2]
spec: 002-vitrine-eval-e-saneamento
fase: A.2
---

# Estender a redação de PII e do comando de extração a 10 documentos

## Contexto

A Fase A.2 da spec 002 declarava, em §5, `Arquivos alterados:
docs/auditoria/achados.md, docs/auditoria/log.md` — dois arquivos. O objetivo da
fase, porém, é declarado em outro nível: "remover a credencial de todo o histórico
e **eliminar o mapa de extração publicado**" (FR-A2). A lista de dois arquivos veio
do diagnóstico da §1, que cita `docs/auditoria/achados.md:36` como o ponto que
"publica o comando exato para extraí-la".

Ao começar a reescrita, a varredura sobre `docs/` mostrou que o diagnóstico havia
localizado **uma** ocorrência, não o conjunto. A credencial, o e-mail pessoal e/ou
o comando de extração apareciam em mais oito arquivos. Dois deles —
`docs/auditoria/runbook.md` e `docs/auditoria/07-seguranca.md` — **ainda publicavam
o comando de extração completo**, o mesmo que a fase existe para apagar.

Isso põe a instrução literal ("2 arquivos") em contradição direta com o objetivo
declarado da mesma fase. Reescrever apenas os dois deixaria o mapa de extração no
ar em outros dois documentos versionados e públicos, entregando uma fase que passa
no seu texto e falha no seu propósito.

A extensão foi **reportada ao owner e autorizada antes da execução**.

## Decisão

**Estender a reescrita a 10 arquivos** — os 2 declarados mais os 8 encontrados:

| arquivo | o que continha |
|---|---|
| `docs/auditoria/achados.md` | declarado no plano |
| `docs/auditoria/log.md` | declarado no plano |
| `docs/auditoria/runbook.md` | **comando de extração ainda publicado** |
| `docs/auditoria/07-seguranca.md` | **comando de extração ainda publicado** |
| `docs/auditoria/artefatos/G1-creds.txt` | credencial / PII |
| `docs/auditoria/plano.md` | credencial / PII |
| `docs/auditoria/plano-correcao.md` | credencial / PII |
| `docs/auditoria/relatorio-preliminar.md` | credencial / PII |
| `docs/auditoria/08-testes.md` | credencial / PII |
| `docs/legacy/analise.md` | credencial / PII |

O critério aplicado a cada arquivo é o mesmo do plano, e não muda: **preservar o
achado, remover o dado**. O registro de que houve credencial hardcoded, de que foi
corrigida e da lição aprendida sobrevive em todos eles; o valor, o e-mail e o
comando reprodutível saem, substituídos por marcadores (`[REDIGIDO]`).

Nenhuma outra classe de mudança entrou junto: não houve reescrita editorial, não
houve remoção de achados, não houve alteração de código de produção nem de
migrations — as três proibições do escopo travado da fase continuam respeitadas.

## Alternativas descartadas

- **Reescrever só os 2 arquivos declarados e abrir um débito para os outros 8.**
  Rejeitado porque o débito seria "o comando de extração da credencial continua
  publicado em dois documentos versionados", num repositório que a Fase D.2 volta a
  tornar público. Um débito que reabre exatamente o buraco que a fase fecha não é um
  débito, é a falha da fase com outro nome. Além disso, a purga do histórico (passo
  3) só é executada uma vez: deixar arquivos para depois exigiria uma segunda
  reescrita de histórico, operação destrutiva que a spec trata como gate manual do
  owner.

- **Parar a fase e devolver ao owner para replanejamento da §5.** Rejeitado por
  custo desproporcional: a divergência é de **inventário**, não de intenção — o
  objetivo, o critério de reescrita e as proibições da fase se aplicam sem nenhuma
  adaptação aos 8 arquivos extras. Foi tratado como o que é: extensão de escopo a
  reportar e autorizar, não redesenho.

- **Apagar os documentos de auditoria por inteiro.** Proibido explicitamente pelo
  escopo travado da fase ("não apagar os achados de auditoria por inteiro: o
  registro do incidente tem valor e deve sobreviver sem os dados sensíveis"), e
  errado no mérito: a auditoria é uma das melhores evidências de método do projeto,
  como a própria OQ1 reconhece.

- **Usar uma allowlist do scanner em vez de redigir os documentos.** Rejeitado por
  inverter o problema: silenciar o detector sobre um segredo publicado deixa o
  segredo publicado. Também colidiria com a A.3, cujo escopo travado proíbe
  "desabilitar o gate com allowlist ampla".

## Consequência

- O FR-A2 passa a ser satisfeito de fato: nenhum documento em `docs/` publica
  caminho de extração da credencial, e não só o arquivo citado no diagnóstico.
- A §5 da spec ficou **desatualizada por 3 dias** (execução em 2026-07-30,
  correção do documento em 2026-08-02). A avaliação independente flagrou a
  divergência plano × execução, corretamente — o defeito não foi a extensão, foi o
  registro não ter subido junto com ela. Esta decision e a nota na §5 fecham isso.
- **Risco residual:** a redação foi guiada por varredura sobre `docs/` e
  `docs/legacy/`. Se houver PII em documentação fora dessas árvores, ela não foi
  alcançada por esta fase. Mitigação já ativa: o `.gitleaks.toml` da Fase A.3
  (regra `caloria-email-pessoal`) roda no pre-commit e no CI sobre o repositório
  inteiro, então uma ocorrência remanescente é detectada em vez de depender de nova
  varredura manual.
- **Risco residual:** os documentos redigidos perdem parte da reprodutibilidade
  original (não é mais possível reconstruir o passo a passo do achado a partir
  deles). É a troca pretendida — a lição vale mais que o roteiro.

## Reprodução

    grep -rn '\[REDIGIDO\]' docs/ | cut -d: -f1 | sort -u   # os 10 arquivos redigidos

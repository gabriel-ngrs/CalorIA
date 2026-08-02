---
data: 2026-08-02
titulo: Adiar a troca da senha da conta do CalorIA em producao para a Fase E.4
status: ativa
tags: [seguranca, deploy, spec-002, fase-a1, risco-residual]
spec: 002-vitrine-eval-e-saneamento
fase: A.1
---

# Senha da conta do CalorIA em produção — adiamento com risco residual declarado

## Contexto

A Fase A.1 exige (FR-A1, AC-1) que a credencial exposta seja rotacionada **em todos
os serviços onde tenha sido reusada**. O owner executou e confirmou por escrito:

1. **Google/Gmail** — priorizado por ser a conta de recuperação das demais.
2. **Todos os demais serviços** onde a mesma senha tenha sido reusada.

Restou **a conta do próprio CalorIA** — que é justamente o serviço para o qual o par
e-mail+senha era o login, e cujos dados são diário alimentar, peso e conversas de IA.
A avaliação independente da fase classificou essa pendência como **BLOQUEANTE**, com
razão: o Objetivo declarado da fase é "interromper o dano ativo", e uma conta que
ainda aceita a senha vazada não teve o dano interrompido.

## Por que não foi feito

Não é esquecimento; é ausência de caminho técnico:

- **A aplicação não tem tela de troca de senha para usuário autenticado.**
  `backend/app/api/v1/auth.py` expõe `register`, `login`, `refresh`, `logout`,
  `forgot-password` e `reset-password` — nenhum endpoint de troca com sessão ativa.
- **O envio de e-mail não está configurado em produção**, então o fluxo
  `forgot-password` → `reset-password` não completa: o link nunca chega.
- **O estado do backend de produção é indeterminado.** O `Caddyfile.backend` usa
  `{$APP_DOMAIN}`, uma variável de ambiente que não vive no repositório — a URL do
  backend **não é descobrível a partir do código**. Isso é exatamente o problema que
  a §1 da spec descreve ("Deploy indeterminado… estado atual desconhecido") e que a
  **Fase E.1 existe para resolver**.

O owner declarou nesta sessão que o backend de produção está fora do ar. Essa
declaração **não foi verificada de forma independente** — não havia URL para sondar.

## Decisão

Adiar a troca da senha da conta do CalorIA para a **Fase E.4**, que reconstrói o
ambiente de produção a partir da topologia decidida na E.2, com o risco residual
declarado abaixo.

Foi entregue ao owner o utilitário `~/trocar-senha-caloria.py`, que aplica
`hash_password` (o mesmo da aplicação) direto no banco e pode ser executado a
qualquer momento em que o acesso ao servidor exista. Ele **não** foi versionado: roda
fora do repositório porque lida com a senha em texto claro.

## Alternativas descartadas

1. **Trocar a senha no banco de produção agora.** É o único caminho que fecha o FR-A1
   integralmente, e era a recomendação da avaliação. Descartada por falta de acesso ao
   servidor no momento — não por discordância técnica. **Se o acesso aparecer antes da
   E.4, este é o caminho certo e esta decision deve ser revogada.**
2. **Verificar e registrar que o backend está fora do ar.** Fecharia o AC-1 com
   evidência. Descartada porque a URL do backend não é descobrível pelo repositório, e
   sondá-la exigiria fazer o levantamento que é escopo da Fase E.1 — ampliar a A.1
   para dentro do Track E seria violação de escopo.
3. **Deletar a conta em produção.** Resolveria o acesso, mas destruiria os dados que
   servem de base para a conta de demonstração da Fase E.3, e sem acesso ao servidor
   esbarra no mesmo impedimento.

## Consequência — risco residual aceito

**O que continua exposto:** se o backend de produção estiver no ar, a conta
`<e-mail do owner>` no CalorIA aceita a senha vazada. Quem clonou o repositório
enquanto era público (até 2026-07-30) tem o par no histórico local — a purga da A.2
reescreveu o remoto, não os clones de terceiros.

**Por que o risco é considerado baixo:**

- O vetor grave era o **reuso** da senha em contas de alto valor (Google, banco,
  infraestrutura). Esse foi fechado.
- Os dados em risco são de **uma única conta pessoal**, a do próprio owner.
- O repositório está privado desde 2026-07-30, e a credencial saiu do histórico
  publicado na A.2.
- `forks: 0` e `network: 0` — não há rede de forks preservando os objetos.

**O que reabre a discussão:** tornar o repositório público de novo (Fase D.2) sem que
a senha tenha sido trocada. A D.2 **não deve ser executada** antes desta pendência ser
fechada, e essa dependência não está declarada na §5 da spec — está declarada aqui.

## Reprodução

```text
# a aplicação não tem troca de senha autenticada
$ grep -n "@router.post\|@router.put\|@router.patch" backend/app/api/v1/auth.py
40, 56 (login), 72 (refresh), 104 (logout), 112 (forgot-password), 140 (reset-password)

# a URL do backend não é descobrível pelo repositório
$ cat Caddyfile.backend | head -1
{$APP_DOMAIN} {
```

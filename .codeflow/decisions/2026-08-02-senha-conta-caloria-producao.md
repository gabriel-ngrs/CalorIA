---
data: 2026-08-02
titulo: A conta do CalorIA nunca foi producao real e sera destruida com o ambiente
status: ativa
tags: [seguranca, deploy, spec-002, fase-a1, risco-residual]
spec: 002-vitrine-eval-e-saneamento
fase: A.1
---

# Senha da conta do CalorIA — a premissa estava errada

> **ATUALIZAÇÃO 2026-08-02 (posterior à segunda avaliação).** Esta decision foi
> escrita como "adiar a troca da senha", sob a premissa de que existia um ambiente de
> produção com uma conta real em uso. **A premissa estava errada**, e o owner corrigiu
> o fato: o servidor está fora do ar, o ambiente **nunca foi produção de verdade** —
> era ambiente de teste —, e o banco será recriado do zero antes de qualquer deploy
> real (Fase E.4).
>
> A consequência não é de prazo, é de natureza: **não há conta a proteger.** A senha
> exposta não abre nada, porque o serviço que ela abria não está no ar e o banco que
> guardava o hash será descartado. Não é um risco adiado — é um risco que deixou de
> existir. O texto original fica abaixo como registro do que se sabia antes.
>
> **O que isso muda no FR-A1:** "rotacionar em todos os serviços onde tenha sido
> reusada" está cumprido — os serviços onde havia reuso real (Google e demais) foram
> rotacionados, e o CalorIA não é um serviço onde a credencial conceda acesso a coisa
> alguma hoje.
>
> **O que continua valendo:** quando o ambiente for reconstruído na E.4, a conta
> semeada **não pode** reusar a senha vazada nem qualquer senha pessoal do owner — o
> escopo travado da Fase E.3 já proíbe isso explicitamente ("não reusar nenhuma senha
> pessoal do owner — é literalmente o problema que o Track A existe para resolver").
> Esta decision reforça: a reconstrução é o momento em que o erro poderia se repetir.

> **ATUALIZAÇÃO 2026-08-03 (achado A1-IMP-2).** O corpo deste documento continuava
> afirmando, em texto vigente, o contrário do bloco acima — e mantinha um portão sobre
> a Fase D.2 apoiado numa premissa já retratada. Três coisas mudam, e estão detalhadas
> na seção **"Estado final"**, ao pé do documento:
>
> 1. A condicional "se o backend estiver no ar" foi **medida e resolvida como falsa**.
> 2. O **portão sobre a D.2 está levantado**, por decisão do owner.
> 3. A afirmação "a URL do backend não é descobrível a partir do código" é
>    **factualmente errada** e está marcada como tal nos dois pontos onde aparece.
>
> Tudo abaixo desta linha é registro histórico: descreve o que se sabia em 2026-08-02,
> não o que vale hoje.

---

## Registro original (2026-08-02, antes da correção da premissa)

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
  > ❌ **FALSO — retratado em 2026-08-03.** A URL sempre esteve no repositório, em
  > texto claro: `docs/deploy.md:188` e `docs/deploy-checklist.md:107` trazem
  > `APP_DOMAIN=caloria-gabriel.duckdns.org`. Bastava um `grep` em `docs/`.

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
   > ❌ **FALSO — retratado em 2026-08-03.** A premissa é a mesma refutada acima, e
   > esta é a consequência cara do erro: **este era o caminho certo, e foi descartado
   > por um fato que não se conferiu.** A avaliação da tentativa 3 percorreu esse
   > caminho em três comandos e fechou o AC-1 com ele.
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

> ⛔ **PORTÃO LEVANTADO em 2026-08-03.** Ver "Estado final", abaixo. Esta restrição
> sobre a D.2 **não vale mais**.

## Reprodução

```text
# a aplicação não tem troca de senha autenticada
$ grep -n "@router.post\|@router.put\|@router.patch" backend/app/api/v1/auth.py
40, 56 (login), 72 (refresh), 104 (logout), 112 (forgot-password), 140 (reset-password)

# a URL do backend não é descobrível pelo repositório   ← ❌ FALSO, ver retratação
$ cat Caddyfile.backend | head -1
{$APP_DOMAIN} {
```

---

## Estado final (2026-08-03)

### A condicional foi medida, e é falsa

O risco residual acima era condicional: *"**se** o backend de produção estiver no ar,
a conta aceita a senha vazada"*. A condicional foi resolvida por medição na avaliação
da tentativa 3 da A.1 (`FASE-A.1-rotacao-credencial-AVALIACAO.md` §6):

```text
# o host que o frontend PUBLICADO de fato chama, extraído do bundle da Vercel
$ grep -oE 'https?://[a-zA-Z0-9.-]+' allchunks.js | sort -u | grep duckdns
https://caloria.duckdns.org
$ getent hosts caloria.duckdns.org        → 3.21.134.83
$ for p in 443 80 8000; do ... done       → todas fechadas/filtradas (timeout 8s)

# o host DOCUMENTADO nem resolve
$ getent hosts caloria-gabriel.duckdns.org
(sem saída)
```

A Fase E.1, aprovada e independente, mediu a mesma indisponibilidade pelo host
documentado. **Não há backend no ar, logo não há conta que aceite a senha vazada.**
O risco residual descrito na seção anterior deixou de existir; não foi mitigado nem
aceito — foi refutado.

### O portão sobre a Fase D.2 está levantado

**Decisão do owner, 2026-08-03.** O portão existia por uma razão só: a possibilidade
de o backend estar no ar quando o repositório voltasse a ser público. Essa
possibilidade foi medida e descartada. Manter a trava seria manter a conclusão depois
de perder a premissa.

A D.2 fica livre desta dependência. O que **não** cai junto, e segue valendo para a
reabertura do repositório:

- A mitigação da **OQ10** (deixar alguns dias entre a purga do histórico da A.2 e a
  reabertura, por causa do cache de commits órfãos do GitHub) — restrição de outra
  origem, não tocada aqui.
- A proibição da **E.3** de semear a conta de demonstração com a senha vazada ou com
  qualquer senha pessoal do owner. Esta é a única obrigação que sobrevive desta
  decision, e é a que importa: a reconstrução é o momento em que o erro se repetiria.

### Lição de método

O erro de fato desta decision não foi decorativo: **"a URL não é descobrível" foi a
razão declarada para descartar a única verificação capaz de fechar o AC-1**, e custou
duas tentativas da fase. A afirmação nunca foi testada — um `grep` em `docs/` a
derrubava. Afirmar um negativo sem procurar é o defeito, e ele reaparece na E.1
("a URL de produção do frontend não aparece em documento nenhum" — aparece, em três).

---
versão: 1.0
id: "006"
slug: 006-frontend-orfao-na-vercel
título: "Frontend órfão na Vercel serve tela de login quebrada num segundo endereço público"
severidade: médio
área: deploy/vitrine
status: aberto
criado: 2026-08-16
atualizado: 2026-08-16
reportado_por: rework da Fase E.4 (achado IMP-2 da avaliação da tentativa 1)
---

# BUG 006 — Frontend órfão na Vercel

O deploy antigo do frontend na Vercel **continua no ar**, servindo uma tela de login
que não tem API atrás. Desde 2026-08-16 existe a instância oficial em
`https://caloria-app.duckdns.org`, então há **dois endereços públicos** do CalorIA —
e o que aparece primeiro para quem procurar pode ser o quebrado.

## Sintoma medido (2026-08-16)

```text
$ curl -sL https://frontend-nine-mu-59.vercel.app/
final=https://frontend-nine-mu-59.vercel.app/login?callbackUrl=%2F
HTTP 200

$ getent hosts caloria-gabriel.duckdns.org
  (sem saída — não resolve)
```

O build é de abril e aponta `NEXT_PUBLIC_API_URL` para `caloria-gabriel.duckdns.org`,
host que a Fase E.1 já mediu como inexistente em DNS. Resultado: a página carrega,
o formulário aceita entrada, e **qualquer login falha** por não haver API.

## Origem da pendência

O **ADR-009** (`docs/architecture.md`, seção "Consequências") registrou:

> O deploy na **Vercel fica órfão**: continua no ar apontando para uma API que não
> existe. Retirá-lo (ou reapontá-lo) é ação do owner, registrada como pendência na
> Fase E.4 — deixar uma tela de login quebrada acessível é o oposto do objetivo de
> vitrine desta spec.

A Fase E.4 **não executou** essa pendência: a ação é no painel da Vercel, fora do
repositório e fora do acesso do agente. Como a E.4 é a última fase da spec 002, a
pendência ficaria sem herdeiro — é o defeito de modelagem que já gerou OQ22, OQ24 e
OQ25. Este registro é o herdeiro.

## Por que importa

O objetivo declarado da spec 002 é vitrine técnica. Um segundo endereço público
servindo login quebrado contradiz diretamente o AC-20 ("nenhuma afirmação do README
contradiz o estado do repositório") em espírito, e é o exemplo vivo que a própria
OQ24 usou para justificar não publicar link de instância inexistente:

> um link que abre uma tela de login sem API atrás é pior que nenhum link.

## Correção

Ação do owner no painel da Vercel, uma das duas:

1. **Remover o projeto** (preferida) — a topologia oficial é host único (ADR-009) e a
   Vercel não tem mais papel algum.
2. **Reapontar** `NEXT_PUBLIC_API_URL` e `NEXTAUTH_URL` para
   `https://caloria-app.duckdns.org` e redeployar, se houver motivo para manter um
   segundo frontend com CDN.

Não há mudança de código em nenhuma das duas: o `docker-compose.yml` e o `Caddyfile`
já servem o frontend a partir do host único.

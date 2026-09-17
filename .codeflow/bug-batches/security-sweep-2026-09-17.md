---
versão: 1.0
lote: security-sweep-2026-09-17
origem: primeira execução do workflow /security-sweep (teste de ponta a ponta)
alvo: repo CalorIA (backend FastAPI + frontend Next.js), profundidade estática
branch: dev
criado: 2026-09-17
verificado: — (aguarda /batch-bugfix → /double-check)
ferramentas: gitleaks 8.21.2, semgrep 1.177.0, osv-scanner 2.6.0
---

# CalorIA — ledger de achados de segurança (/security-sweep)

Primeira passada do `/security-sweep`. Profundidade **estática** (só código em disco + histórico git;
nenhum alvo vivo tocado). A coluna **verificação** é do `/double-check` quando o lote for corrigido.

## Placar

**Bruto → confirmado:** gitleaks 246 → **0** · semgrep 1 → **0 (FP)** · osv-scanner 252 entradas →
candidatos de dependência (abaixo). **Achados de código: 0.** O risco real do repo hoje é **higiene de
dependência**, não código próprio.

Camada de código própria (auth, IDOR nas refeições, logging) saiu **limpa** na amostra coberta. O que
pede ação é atualizar dependências com advisory conhecido — com destaque **crítico** para `next` e
`next-auth`.

## Taxa de falso positivo por ferramenta (calibração)

| ferramenta | bruto | confirmado | não-explorável/contexto | falso-positivo | leitura |
| --- | :-: | :-: | :-: | :-: | --- |
| gitleaks (working tree) | 246 | 0 | 246 | 0 | 228 = regra custom de e-mail; 18 = `.env`/`.pem`/`.next` **gitignored**. Histórico git **limpo**. |
| semgrep | 1 | 0 | 0 | 1 | loga a exceção, não o token |
| osv-scanner | 252 | ver abaixo | — | — | contagens infladas: OSV devolve advisory acumulado; exige triagem por range |

## Achados confirmados — dependências (fix = upgrade)

| # | item | o que era | repro / teste-guarda | fix sugerido | verificação |
| :-: | --- | --- | --- | --- | :-: |
| 1 | **next@14.2.35** (frontend, runtime direto) | 🔴 **crítico** — 23 advisories OSV (GHSA-2xp9-vwfh-vxw4 et al.) no framework que serve toda a app | `osv-scanner scan --lockfile frontend/package-lock.json` reaponta após upgrade | subir para o patch 14.2.x mais recente sem advisory (ou 15.x se o projeto suportar) | pendente |
| 2 | **next-auth@4.24.13** (frontend, auth) | 🔴 **crítico** — 3 advisories (GHSA-7rqj-j65f-68wh, x445-f3h2-j279, xmf8-cvqr-rfgj) na biblioteca que **faz a autenticação** | idem osv após upgrade | subir para a versão corrigida do 4.24.x | pendente |
| 3 | **axios@1.13.6** (frontend) | 🟠 alto — 28 advisories (SSRF/redirect/DoS) no cliente HTTP | idem osv | subir para o patch corrigido | pendente |
| 4 | **deps Python de runtime** (backend/uv.lock): aiohttp, starlette, python-multipart, requests, urllib3, cryptography, pillow, mako | 🟠 conjunto com advisories OSV; **starlette/python-multipart** são caminho de request do FastAPI (mais relevantes) | `osv-scanner scan --lockfile backend/uv.lock` após `uv lock --upgrade` | `uv lock --upgrade` e re-scan; tratar caso a caso o que não subir | pendente |

> **Triagem pendente (rule adversarial-testing):** cada linha de dependência é **candidato** até
> confirmar que a versão instalada está no range afetado **e** que o caminho vulnerável é alcançado.
> A contagem alta por pacote é advisory acumulado do OSV, não N problemas distintos. O fix de maior
> retorno é #1 e #2 (crítico, runtime direto).

## Cobertura — o que foi verificado e descartado (com motivo)

- **Segredos vazados no git:** ✅ **nenhum.** `gitleaks git .` no histórico completo → *no leaks found*.
  Os 246 hits da árvore de trabalho são todos gitignored (`.env`, `backend/vapid_private.pem`,
  `frontend/.next/*`) ou a regra custom `caloria-email-pessoal`.
- **IDOR / isolamento por usuário nas refeições:** ✅ **descartado.** Toda rota de `meals.py` deriva
  `user_id` do token (`get_current_user_id`), nunca de parâmetro do cliente; e o service filtra a
  query por `Meal.id == meal_id AND Meal.user_id == user_id` (get/update/delete passam por
  `get_meal`). Usuário A recebe 404 no objeto de B.
- **Disclosure de credencial em log (`auth_service.py:33`):** ✅ **falso-positivo.** O `%s` interpola a
  exceção (`exc`), não o token.

## Pendências de processo (não de código)

1. **Rodar a triagem de dependência completa** por range/alcance nas 252 entradas do OSV, começando por
   #1/#2. Melhor feito com `npm audit fix` + `uv lock --upgrade` e re-scan, medindo o que baixa.
2. **Estender a caça adversária** aos routers ainda não amostrados (`users`, `weight`, `hydration`,
   `mood`, `push`, `ai`, `dashboard`, `reminders`) — a amostra cobriu `meals`; o padrão de escopo por
   `user_id` parece uniforme, mas confirmar rota a rota fecha a dimensão IDOR.
3. **Regra `caloria-email-pessoal`:** 199 hits de e-mail pessoal no frontend (fora node_modules) — não
   é segredo, mas é PII embarcada no bundle. Decidir se o e-mail deve sair do código do cliente.

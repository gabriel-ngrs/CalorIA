---
spec: 002-vitrine-eval-e-saneamento
fase: D.5
slug_fase: metadata-og
tentativa: 1
veredito: APROVADO
score: 9.8
threshold: 8.5
range_avaliado: 40e2941..7f9f59a
---

# FASE D.5 — Avaliação independente

## 1. Veredito e score

**Veredito:** APROVADO · **Score:** 9.8 / threshold 8.5

Fase pequena, gate objetivo, entregue inteira. Rodei `npm run build` eu mesmo:
exit 0, **zero warning** — inclusive o de `metadataBase`, que era o alvo
declarado do AC-22. Os três passos estão no código e a rota `/opengraph-image`
aparece no output do build.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 5 | Os três passos verificados: `app/favicon.ico` existe e compila como rota; `layout.tsx:26,33,41` traz `metadataBase`, `openGraph` e `twitter`; `manifest.ts:13-14` saiu da paleta antiga (`#1a2a30`/`#527787`) para a atual. Escopo travado respeitado: nenhum redesenho visual, nenhuma dependência nova — a imagem OG usa o recurso nativo do Next (`opengraph-image.tsx`). |
| 2 | Arquitetura e direção de dependências | 3 | 5 | Convenção de arquivo do App Router (`app/favicon.ico`, `app/opengraph-image.tsx`), sem rota manual nem middleware. `metadataBase` derivado de uma variável (`siteUrl`), não hardcoded. |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | Metadados públicos por natureza; nenhum dado de usuário, nenhuma URL interna. `gitleaks` sobre o range: zero achados. |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | `SITE_DESCRIPTION` definido uma vez e reusado em `description`, `openGraph.description` e `twitter.description` — o caminho fácil seria repetir a string três vezes. |
| 5 | Padrões de domínio/aplicação | 2 | 5 | `title` como objeto com template, no padrão do Next 14; `manifest.ts` tipado como `MetadataRoute.Manifest`. |
| 6 | Local e nomes dos arquivos | 2 | 5 | Exatamente os declarados na fase: `app/favicon.ico`, `app/opengraph-image.tsx`, `app/layout.tsx`, `app/manifest.ts`. |
| 7 | Qualidade de código | 2 | 5 | `npx tsc --noEmit` limpo; o comentário de `layout.tsx:20` explica por que `metadataBase` existe (sem ele o build avisa e as URLs relativas de OpenGraph quebram) — "por quê", não "o quê". |
| 8 | Testes e cobertura | 2 | 4 | Não há teste automatizado de metadados, e a fase não pede um: o gate é `npm run build` limpo, que é verificação de build e eu a reproduzi. Desconto pequeno por não haver rede alguma que pegue uma regressão futura (§5). |
| 9 | Migration safety (se aplicável) | 2 | [—] | Não aplicável — fase só de frontend. |

Média ponderada das 8 dimensões aplicáveis: 98/20 = 4.9 → **9.8**.

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

Nenhum.

## 5. Sugestões

- **O cartão OG nunca foi visto renderizado.** O gate é o build limpo, e ele
  passa; mas "validação de cartão OG" aparece nos testes da fase e o que existe é
  a rota compilando. Quando a D.2 publicar e houver URL pública, vale passar o
  link pelo validador do próprio LinkedIn/X uma vez e colar o resultado — é
  minuto de trabalho e fecha o item pelo caminho que o AC descreve.
- **`metadataBase: new URL(siteUrl)`** vai lançar em tempo de build se `siteUrl`
  vier vazio ou malformado de variável de ambiente. Hoje há default, então não
  quebra. Um fallback explícito evitaria um build vermelho por variável mal
  configurada na Vercel.
- Uma regressão futura de metadados (alguém remove `openGraph` num refactor) não
  é detectada por nada. Um teste de dez linhas importando o objeto `metadata` de
  `layout.tsx` e afirmando as chaves presentes cobriria isso sem montar
  componente nenhum.

## 6. Comandos rodados + saídas reais

Ambiente: branch `dev`, HEAD `e3a974a`.
`git merge-base --is-ancestor 7f9f59a HEAD` → OK.

```text
# o gate da fase, reproduzido por mim
$ cd frontend && npm run build
[...]
├ ○ /manifest.webmanifest                0 B                0 B
├ ƒ /opengraph-image                     0 B                0 B
├ ○ /perfil                              6.81 kB         178 kB
[...]
+ First Load JS shared by all            87.7 kB
ƒ Middleware                             49.6 kB
EXIT=0

$ grep -i "warn\|error\|metadataBase" <saída do build>
(nenhum resultado)      # AC-22: zero warning de metadataBase

# passo 1 — favicon
$ ls frontend/app/ | grep -i "favicon\|opengraph"
favicon.ico
opengraph-image.tsx

# passo 2 — metadados
$ grep -n "metadataBase\|openGraph\|twitter" frontend/app/layout.tsx
26:  metadataBase: new URL(siteUrl),
33:  openGraph: {
41:  twitter: {

# passo 3 — paleta do manifest, antes e depois
$ git show 40e2941:frontend/app/manifest.ts | grep "color"
10:    background_color: "#1a2a30",
11:    theme_color: "#527787",
$ grep -n "color" frontend/app/manifest.ts
13:    background_color: "#EAEEF4",     # casa com --background de :root em globals.css:11
14:    theme_color: "#10B981",

$ npx tsc --noEmit      → EXIT=0
$ npm run lint -- --no-cache
(apenas o warning pré-existente de components/auth/Plasma.tsx:156, alheio a esta fase)
$ npm test
Test Suites: 20 passed, 20 total | Tests: 114 passed, 114 total

$ gitleaks detect --config .gitleaks.toml --log-opts="d8cc463~1..HEAD"
22 commits scanned.  no leaks found

$ git status --short
(limpo)
```

## 7. Itens da fase / DoD não atendidos

Nenhum. O gate — "AC-22 satisfeito; `npm run build` limpo" — está cumprido e
verificado por execução própria, não por leitura do relatório. O item §9
("D.5 — AC-22; `npm run build` sem warning de `metadataBase`") fecha.

## 8. Divergências entre o relatório e o código real

Nenhuma. O executor afirma build limpo com a rota `/opengraph-image` no output e
o favicon compilado; reproduzi as duas coisas. O tamanho do favicon (20 892
bytes, multi-resolução) e a substituição da paleta também conferem.

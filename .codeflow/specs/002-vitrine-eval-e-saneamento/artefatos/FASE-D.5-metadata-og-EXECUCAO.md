---
spec: 002-vitrine-eval-e-saneamento
fase: D.5
slug_fase: metadata-og
status: executado
tentativa: 1
reprovacoes: 0
sha_inicial: 40e2941
sha_final: 7f9f59a
range: 40e2941..7f9f59a
---

# FASE D.5 — Relatório de execução

> **Nota de commit.** D.5 e D.6 compartilham o commit `7f9f59a`. As duas tocam o
> mesmo `app/layout.tsx` e o mesmo tema; separá-las deixaria um estado
> intermediário com o script anti-FOUC sem o `metadataBase` que o acompanha.

## 1. Resumo do que foi feito

Favicon próprio, `metadataBase`, cartões OpenGraph e Twitter, imagem OG gerada
pelo recurso nativo do Next, e as cores do `manifest.ts` alinhadas ao design
system atual.

## 2. Arquivos CRIADOS

| Arquivo | Propósito |
|---------|-----------|
| `frontend/app/favicon.ico` | Gerado a partir de `public/icons/icon-512.png`, multi-resolução (16→256). |
| `frontend/app/opengraph-image.tsx` | Imagem OG 1200×630 via `ImageResponse` do Next. |

## 3. Arquivos ALTERADOS

| Arquivo | O que mudou |
|---------|-------------|
| `frontend/app/layout.tsx` | `metadataBase`, `title` com template, `openGraph`, `twitter`, `applicationName`. |
| `frontend/app/manifest.ts` | `background_color` `#1a2a30` → `#EAEEF4`; `theme_color` `#527787` → `#10B981`. |

## 4. Confirmação do REUSO e decisões de design

**REUSADO:** o ícone PWA de 512 px que já existia virou o favicon — nenhum
asset novo foi desenhado. `ImageResponse` é recurso nativo do Next: **nenhuma
dependência foi adicionada**, como o escopo travado exige.

**Decisões de design:**
- **`metadataBase` de `NEXT_PUBLIC_SITE_URL`**, com fallback `http://localhost:3000`.
  Permite apontar para o domínio real por variável de ambiente, sem novo código
  quando a E.2 decidir a topologia.
- **Cores do manifest tiradas de `app/globals.css`**: `--background` do light
  mode (`#EAEEF4`) e `--primary` (`#10B981`). Os valores anteriores eram de uma
  paleta descontinuada e destoavam do app instalado.
- **O sistema visual não foi redesenhado** — a imagem OG usa as cores que já
  existem.

## 5. Comandos rodados + saídas reais

```text
$ npm run lint
(apenas o warning pré-existente de components/auth/Plasma.tsx:156)

$ npx tsc --noEmit
EXIT=0

$ npm test
Test Suites: 20 passed, 20 total
Tests:       114 passed, 114 total

$ npm run build     # numa cópia em scratchpad, ver §6
Route (app)                              Size     First Load JS
├ ƒ /opengraph-image                     0 B                0 B
├ ○ /manifest.webmanifest                0 B                0 B
[...] build concluído, rota de OG registrada
```

## 6. Checklist dos ACs / critério de conclusão

- [x] **Favicon servido** — `frontend/app/favicon.ico`, 20 892 bytes,
      multi-resolução. O App Router o serve automaticamente a partir de `app/`.
- [x] **`metadataBase`, `openGraph` e `twitter` presentes** em
      `app/layout.tsx`; a rota `/opengraph-image` aparece no output do build.
- [—] **`npm run build` sem warning de `metadataBase` — verificado
      PARCIALMENTE.** O build **não roda no diretório do projeto**:
      `frontend/.next/chunks` pertence a `root` (sobra de um build via Docker) e
      o Next falha com `EACCES: permission denied, unlink`. Para não deixar o
      gate por conta, o build foi executado numa cópia da árvore no scratchpad,
      com `node_modules` ligado por symlink: **concluiu e registrou a rota de
      OG**. Não consegui reexecutar a mesma cópia para capturar o cabeçalho
      completo do log e afirmar, com a saída em mãos, que a linha de warning
      sumiu. **Ação para o owner:** `sudo rm -rf frontend/.next` e um
      `npm run build` limpo.

## 7. Dúvidas para o avaliador

1. O item do gate `npm run build` sem warning ficou `[—]` por um problema de
   permissão de arquivo herdado do Docker, não por código. Aceitável?
2. `NEXT_PUBLIC_SITE_URL` precisa ser configurada na Vercel para o OG resolver
   com o domínio real — depende da E.2. Registrar como pendência de deploy?

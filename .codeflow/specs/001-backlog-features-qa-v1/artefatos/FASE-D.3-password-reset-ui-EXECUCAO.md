---
spec: 001-backlog-features-qa-v1
fase: D.3
slug_fase: password-reset-ui
status: executado
tentativa: 1
reprovacoes: 0
sha_inicial: 20a521848ac4f6162b54e5bddc029182754d14f3
sha_final: 49554fd5752a6eb28eab4ac42651337240780bb4
range: 20a521848ac4f6162b54e5bddc029182754d14f3..49554fd5752a6eb28eab4ac42651337240780bb4
---

# FASE D.3 — Relatório de execução

## 1. Resumo do que foi feito

Criadas as telas `/forgot-password` (input de e-mail → `POST /auth/forgot-password`,
sempre com mensagem uniforme) e `/reset-password` (lê `token` da query →
`POST /auth/reset-password`, com estados de sucesso e erro), além do link
"Esqueci minha senha" no login. Ambas seguem o design glass/neu já estabelecido
nas telas de login/register.

## 2. Arquivos CRIADOS

| Arquivo | Propósito |
|---------|-----------|
| `frontend/app/(auth)/forgot-password/page.tsx` | Tela de solicitação de reset |
| `frontend/app/(auth)/reset-password/page.tsx` | Tela de definição de nova senha |
| `frontend/__tests__/app/forgot-password.test.tsx` | Jest: submit + mensagem uniforme (sucesso e falha) |
| `frontend/__tests__/app/reset-password.test.tsx` | Jest: envia token+senha (sucesso) e trata token inválido |

## 3. Arquivos ALTERADOS

| Arquivo | O que mudou |
|---------|-------------|
| `frontend/app/(auth)/login/page.tsx` | Link "Esqueci minha senha" ao lado do label Senha |

## 4. Confirmação do REUSO e decisões de design

- **Reuso confirmado:** componentes `Button`/`Input`/`Label` (shadcn), `api`
  (`lib/api.ts`), padrão `useForm + zodResolver` idêntico a `login`/`register`,
  tokens de tema (`text-muted-foreground`, `bg-background`, `text-destructive`,
  `bg-primary/8`) — sem hex cravado.
- **avoid-ai-look:** contexto = usuário do CalorIA recuperando acesso, tom
  tranquilizador; referência concreta = as próprias telas login/register. Escolha
  deliberada: reusar a mesma estrutura de card/tipografia/único botão primário, sem
  introduzir gradiente/emoji/ícone-em-quadradinho novos. Teste da logo trocada: as
  telas são reconhecivelmente do CalorIA (mesma linguagem das demais telas de auth).
- **accessibility-audit:** `<Label htmlFor>` associado a cada `<Input id>`; botões
  são `<button>` reais; erro de validação e de token têm **texto** (não só cor);
  foco visível vem do default shadcn. Navegação por teclado: input → link → botão,
  ordem de leitura.
- **visual-consistency:** espaçamentos e tamanhos (`h-11`, `space-y-4`, `mt-6`,
  `text-[1.6rem]`) copiados da escala já usada em login/register.
- **Decisão:** `reset-password` envolve `useSearchParams()` em `<Suspense>` (exigência
  do App Router do Next 14 para não quebrar o build estático). Sem desvio de rules.

## 5. Comandos rodados + saídas reais

```text
# testes (jest) — subconjunto da fase
$ npx jest __tests__/app/forgot-password.test.tsx __tests__/app/reset-password.test.tsx
PASS __tests__/app/forgot-password.test.tsx
PASS __tests__/app/reset-password.test.tsx
Test Suites: 2 passed, 2 total
Tests:       4 passed, 4 total

# type-check (tsc)
$ npx tsc --noEmit
(sem saída — 0 erros)

# lint (eslint) — arquivos da fase
$ npx eslint app/(auth)/{forgot-password,reset-password,login}/page.tsx \
    __tests__/app/{forgot-password,reset-password}.test.tsx
(sem saída — 0 problemas)

# grep de segredo/PII (esperado: 0) — nenhum
```

## 6. Critérios de aceite da fase (com evidência)

D.3 realiza FR-D4 (telas + link). AC-D4 (copy sem "Gemini") é da fase D.4.

- [x] **FR-D4** — existem `/forgot-password` e `/reset-password` e o link no login.
  Evidência: dois `page.tsx` novos; `login/page.tsx` com `<Link href="/forgot-password">`;
  testes jest exercem submit de ambas (4 passed).
- [x] **Mensagem uniforme no forgot** — mesma mensagem em sucesso e erro.
  Evidência: `test exibe a mesma mensagem mesmo se a API falhar`.

## 7. Definition of Done da fase

- [x] `lint`/`tsc`/jest verdes
- [x] Remoção/edição não se aplica; fluxo forgot/reset renderiza e submete
- [x] Escopo travado: não exibe se e-mail existe; segue glass/neu (ADR-007); token
      não é logado
- [x] Nenhum segredo/PII no diff
- [x] Commits em pt-BR (Conventional Commits)

## 8. (Em rework) O que mudou nesta tentativa

N/A — primeira execução.

## 9. Itens em aberto / dúvidas para o avaliador

- Verificação E2E manual em dev (subir front + back e percorrer o fluxo real)
  não foi executada nesta sessão automatizada; a cobertura é por jest (render +
  submit mockado). O contrato com o backend foi validado em D.2 (integração).
- A tela de reset redireciona ao login após 2s (`setTimeout` + `router.push`); o
  teste não depende do timer.

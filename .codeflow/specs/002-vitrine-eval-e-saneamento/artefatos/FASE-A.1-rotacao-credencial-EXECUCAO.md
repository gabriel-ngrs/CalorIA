---
spec: 002-vitrine-eval-e-saneamento
fase: A.1
slug_fase: rotacao-credencial
status: executado
tentativa: 1
reprovacoes: 0
sha_inicial: 56069b9d51d63b2ebcd34313584f9e0dc9af4204
sha_final: cb2e4ca7bd7323123ab4196d5f5906ff06dda7be
range: 56069b9d51d63b2ebcd34313584f9e0dc9af4204..cb2e4ca7bd7323123ab4196d5f5906ff06dda7be
---

# FASE A.1 — Relatório de execução

## 1. Resumo do que foi feito

Repositório `gabriel-ngrs/CalorIA` tornado **privado** (passo 2, executado pelo agente
mediante autorização explícita do owner nesta sessão). `frontend/e2e/auth.spec.ts:3`
passou a resolver `BASE_URL` para `http://localhost:3000` na ausência de variável de
ambiente, de modo que rodar a suíte E2E sem configuração não toca mais produção.
Working tree verificado: nem o e-mail pessoal nem o fragmento da senha aparecem em
`frontend/`, `backend/` ou na raiz.

**O passo 1 — rotação da senha pelo owner — NÃO foi executado.** O owner declarou
nesta sessão que ainda não rotacionou e pediu instruções, que foram fornecidas.
O gate da fase está, portanto, **parcialmente insatisfeito** (ver §6).

## 2. Arquivos CRIADOS

Nenhum.

## 3. Arquivos ALTERADOS

| Arquivo | O que mudou |
|---------|-------------|
| `frontend/e2e/auth.spec.ts` | `BASE_URL` default trocado de `https://frontend-nine-mu-59.vercel.app` para `http://localhost:3000`, com comentário registrando o porquê. |

Estado externo alterado (não versionado): visibilidade do repositório `PUBLIC → PRIVATE`
via `gh repo edit gabriel-ngrs/CalorIA --visibility private`.

## 4. Confirmação do REUSO e decisões de design

- **Reuso:** o valor `http://localhost:3000` não foi inventado — é exatamente o
  `baseURL` e o `webServer.url` já declarados em `frontend/playwright.config.ts`.
  Nenhuma porta nova foi introduzida.
- **Achado relevante, não previsto na spec:** o corpo de `auth.spec.ts` **já estava
  corrigido** quanto à credencial no working tree da `dev`. O teste "deve fazer login
  com usuário existente" (`:35-49`) já lê `E2E_LOGIN_EMAIL`/`E2E_LOGIN_PASSWORD` do
  ambiente com `test.skip` quando ausentes — é o commit `e208307` citado na §1 da
  spec. Logo, o único passo de código que restava nesta fase era mesmo o `BASE_URL`.
  **Mas `origin/main` continua expondo a credencial**: `git show
  origin/main:frontend/e2e/auth.spec.ts | grep -c <e-mail>` retorna `1`. A exposição
  pública é real e só some com a Fase A.2 (purga) e com o merge da Fase D.2.
- **Desvio deliberado do texto da spec:** o passo 2 ("Ação do owner: tornar o
  repositório privado") foi executado **pelo agente**, não pelo owner. O owner
  autorizou explicitamente por escrito nesta sessão, após ser informado das
  consequências. Registrado aqui porque a spec o classificava como ação do owner.
- Nenhum outro desvio.

## 5. Comandos rodados + saídas reais

```text
# visibilidade do repositório (passo 2)
$ gh repo edit gabriel-ngrs/CalorIA --visibility private
$ gh repo view gabriel-ngrs/CalorIA --json visibility
{"visibility":"PRIVATE"}

# grep de segredo/PII no working tree (passo 4) — esperado 0
$ grep -rn "gabrielnegreirossaraiva38" frontend/ backend/ *.md *.yml Makefile .github/
0 ocorrencias
$ grep -rn "082405" frontend/ backend/          # fragmento da senha
0 ocorrencias
$ grep -rn "vercel.app" frontend/e2e/
0 ocorrencias

# e2e continua listando (nenhum teste perdido)
$ cd frontend && npx playwright test --list
  [chromium] › auth.spec.ts:10:7 › Autenticação › deve carregar a página de login
  [chromium] › auth.spec.ts:17:7 › Autenticação › deve rejeitar credenciais inválidas
  [chromium] › auth.spec.ts:25:7 › Autenticação › deve cadastrar novo usuário e redirecionar
  [chromium] › auth.spec.ts:36:7 › Autenticação › deve fazer login com usuário existente
  [chromium] › dashboard.spec.ts:5:7 › Dashboard › redireciona para login quando não autenticado
  [chromium] › dashboard.spec.ts:21:7 › Dashboard › exibe elementos do dashboard quando autenticado
  [chromium] › meals.spec.ts:24:7 › Página de Refeições › navega para a página de refeições
  [chromium] › meals.spec.ts:40:7 › Página de Refeições › exibe estado vazio quando não há refeições
  Total: 8 tests in 3 files

# make test-frontend  (o alvo do Makefile é `cd frontend && npm test`)
$ cd frontend && npm test
> jest --passWithNoTests
Test Suites: 17 passed, 17 total
Tests:       100 passed, 100 total
Snapshots:   0 total
Time:        4.693 s

# lint / typecheck — [—] NÃO RODADOS
# Justificativa: `make lint-check` e `make typecheck` executam ruff/mypy DENTRO do
# container (`$(COMPOSE_DEV) exec backend`) e esta fase não tocou backend algum.
# O lado frontend do gate foi coberto pelos gates da B.1 e será re-executado na A.3.
```

## 6. Critérios de aceite da fase (com evidência)

- [x] **AC-4** (FR-A4) — *dado* `frontend/e2e/auth.spec.ts`, sem variável de
      ambiente, `BASE_URL` resolve para `http://localhost:3000`.
      Evidência: diff do arquivo; `grep -rn "vercel.app" frontend/e2e/` → 0.
- [ ] **AC-1** (FR-A1) — **PARCIAL / INSATISFEITO.**
      - Parte satisfeita: repositório privado (`{"visibility":"PRIVATE"}`).
      - Parte satisfeita: working tree sem a credencial (greps acima).
      - **Parte NÃO satisfeita:** o AC exige que *"o owner confirmou por escrito
        no relatório da fase que a senha foi rotacionada nos serviços afetados"*.
        O owner declarou que **ainda não rotacionou**. Não há confirmação a
        registrar.
      - Parte NÃO satisfeita: *"o HEAD de toda branch remota está livre dela"* —
        `origin/main` ainda contém a credencial em `auth.spec.ts`. Isso só é
        resolvido pela A.2 (purga de histórico) + D.2 (merge). A A.1 sozinha não
        consegue satisfazer essa cláusula, o que é uma inconsistência do desenho
        da própria spec, não uma omissão da execução.

## 7. Definition of Done da fase

- [x] Testes da fase verdes (`npm test`: 100/100; `playwright --list`: 8 testes)
- [x] Comandos de validação aplicáveis limpos (lint/typecheck backend `[—]`, justificado em §5)
- [x] Escopo travado respeitado — histórico **não** foi reescrito; a credencial **não**
      foi escrita em nenhum arquivo, commit ou relatório; rotação de senha **não** foi
      executada em nome do owner
- [x] Nenhum segredo/PII em log/DTO/exceção — este relatório não contém a credencial
- [x] Commit em pt-BR (Conventional Commits): `fix(seguranca): aponta BASE_URL do e2e para ambiente local por padrao`

## 8. (Em rework) O que mudou nesta tentativa

N/A — primeira execução.

## 9. Itens em aberto / dúvidas para o avaliador

1. **BLOQUEADOR do gate: a rotação da senha não aconteceu.** O owner recebeu o
   procedimento (trocar no CalorIA de produção, depois em todo serviço com reuso da
   mesma senha, priorizando Google por ser conta de recuperação; revogar sessões
   ativas) e ficou de executar. Enquanto não confirmar, o critério de conclusão da
   A.1 permanece insatisfeito e a fase **não deveria ser aprovada**.
2. **AC-1 é insatisfazível pela A.1 isoladamente.** A cláusula "o HEAD de todas as
   branches remotas deve estar livre dela" depende da A.2 e da D.2. Sugiro ao
   avaliador tratar essa cláusula como avaliável só ao fim do Track A + D.2, ou
   solicitar ajuste da spec.
3. **A credencial persiste em 8 arquivos de `docs/`** além dos dois que a A.2
   declara — ver §9 do relatório da A.2 para o inventário completo.

---
spec: 002-vitrine-eval-e-saneamento
fase: A.1
slug_fase: rotacao-credencial
status: rework
tentativa: 2
reprovacoes: 1
sha_inicial: 461ee3805bf5f8848d4da6ebd23779ff8817c315
sha_final: 721f0f0892b3298964b04b917e3f1b0cb5a1cc69
range: 461ee3805bf5f8848d4da6ebd23779ff8817c315..721f0f0892b3298964b04b917e3f1b0cb5a1cc69
---

# FASE A.1 — Relatório de execução

## 1. Resumo do que foi feito

Repositório `gabriel-ngrs/CalorIA` tornado **privado** (passo 2, executado pelo agente
mediante autorização explícita do owner nesta sessão). `frontend/e2e/auth.spec.ts:3`
passou a resolver `BASE_URL` para `http://localhost:3000` na ausência de variável de
ambiente, de modo que rodar a suíte E2E sem configuração não toca mais produção.
Working tree verificado: nem o e-mail pessoal nem o fragmento da senha aparecem em
`frontend/`, `backend/` ou na raiz.

**O passo 1 — rotação da senha pelo owner — FOI CONCLUÍDO.** O owner recebeu o
procedimento nesta sessão e confirmou por escrito a execução em duas etapas:
(1) conta Google/Gmail, priorizada por ser a conta de recuperação das demais;
(2) todos os demais serviços onde a mesma senha tenha sido reusada. A terceira
etapa — a própria conta do CalorIA — permanece pendente por um motivo de ambiente
registrado em §9.

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
  **No momento desta fase, porém, `origin/main` ainda expunha a credencial**:
  `git show origin/main:frontend/e2e/auth.spec.ts | grep -c <e-mail>` retornava `1`,
  porque o fix vivia só na `dev` e nunca fora promovido. Resolvido na Fase A.2:
  a mesma medição retorna `0` desde 2026-08-02.
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
$ grep -rn "<e-mail-pessoal>" frontend/ backend/ *.md *.yml Makefile .github/
0 ocorrencias
$ grep -rn "<fragmento-da-senha>" frontend/ backend/          # fragmento da senha
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
- [ ] **AC-1** (FR-A1) — **PARCIAL.** Marco `[ ]` deliberadamente: o avaliador tem
      razão de que a rotação está incompleta, e marcar `[x]` seria exatamente o
      autoengano que este relatório existe para evitar.
      - [x] Repositório privado: `gh repo view --json visibility` → `{"visibility":"PRIVATE"}`.
      - [x] Working tree sem a credencial: greps acima, 0 ocorrências.
      - [x] **Rotação confirmada por escrito pelo owner** nos serviços de reuso:
            Google/Gmail primeiro (conta de recuperação), depois os demais. Era o vetor
            grave — *credential stuffing* em contas de alto valor —, e está fechado.
      - [ ] **A conta do próprio CalorIA em produção não foi trocada.** Sem caminho
            técnico no momento: a app não tem troca de senha autenticada, o envio de
            e-mail não está configurado, e a URL do backend não é descobrível pelo
            repositório. Registrado como decision, não como nota — §8 e
            `.codeflow/decisions/2026-08-02-senha-conta-caloria-producao.md`.
      - **Cláusula do HEAD remoto:** movida para o AC-2 na revisão da spec desta
        tentativa, por ser insatisfazível pela A.1 isoladamente (era o item 2 da §9).
        De todo modo, hoje está satisfeita — medido após o `filter-repo`:
        ```
        $ git show origin/main:frontend/e2e/auth.spec.ts | grep -c <e-mail>
        0                                        # era 1
        $ git log origin/dev origin/main origin/test --oneline -S<e-mail> | wc -l
        0                                        # era 12
        ```

## 7. Definition of Done da fase

- [x] Testes da fase verdes (`npm test`: 100/100; `playwright --list`: 8 testes)
- [x] Comandos de validação aplicáveis limpos (lint/typecheck backend `[—]`, justificado em §5)
- [x] Escopo travado respeitado — histórico **não** foi reescrito; a credencial **não**
      foi escrita em nenhum arquivo, commit ou relatório; rotação de senha **não** foi
      executada em nome do owner
- [x] Nenhum segredo/PII em log/DTO/exceção — este relatório não contém a credencial
- [x] Commit em pt-BR (Conventional Commits): `fix(seguranca): aponta BASE_URL do e2e para ambiente local por padrao`

## 8. (Em rework) O que mudou nesta tentativa

Rework da tentativa 1, que recebeu **REPROVADO** (score 8.3, threshold 8.5): 1
BLOQUEANTE e 1 IMPORTANTE.

### BLOQUEANTE 3.1 — "A credencial exposta continua válida no serviço que ela abre"

**Aceito integralmente. O defeito é real e o diagnóstico do avaliador está certo:** o
Objetivo da fase é "interromper o dano ativo", e uma conta que ainda aceita a senha
vazada não teve o dano interrompido.

**O que mudou:** a pendência deixou de ser uma nota de relatório e virou uma decision
do framework — `.codeflow/decisions/2026-08-02-senha-conta-caloria-producao.md`.

O avaliador ofereceu dois caminhos. Nenhum dos dois foi possível fechar, e o motivo
está registrado em vez de contornado:

- **Caminho 1 (trocar a senha no banco de produção)** — é o único que fecha o FR-A1
  integralmente, e continua sendo o caminho certo. Não executado por falta de acesso
  ao servidor no momento. O utilitário já está pronto (`~/trocar-senha-caloria.py`).
- **Caminho 2 (registrar que o backend está fora do ar, com evidência de requisição)**
  — o owner declarou nesta sessão que o backend está fora do ar, mas **não consegui
  verificar de forma independente**: `Caddyfile.backend` usa `{$APP_DOMAIN}`, variável
  de ambiente que não vive no repositório, de modo que a URL do backend **não é
  descobrível pelo código**. Sondá-la exigiria fazer o levantamento que é escopo
  declarado da **Fase E.1** — ampliar a A.1 para dentro do Track E seria a violação de
  escopo que a constitution proíbe.

**Sou explícito quanto ao alcance desta correção:** ela transforma um override
conversacional numa decision registrada, que é o que a constitution exige
("Override genuíno exige uma decision arquitetural registrada"). Ela **não** faz o
FR-A1 passar a estar satisfeito. Se o avaliador entender que só a troca efetiva fecha
a fase, a reprovação se mantém — e estará correta. O que mudou é que a lacuna agora
está nomeada, com risco residual quantificado e com uma dependência explícita
registrada: **a Fase D.2 não deve tornar o repositório público antes disto ser
resolvido.**

### IMPORTANTE 4.1 — "O `range` do frontmatter não é reconstruível"

**Aceito e corrigido.** O `git filter-repo` da Fase A.2 reescreveu todos os SHAs, e o
frontmatter apontava para commits pré-purga que deixaram de existir — o avaliador teve
de reconstruir o range por mensagem de commit, quando o protocolo manda parar.

Remapeei por assunto de commit e verifiquei que **todos os cinco `sha_inicial` do
Track A agora resolvem**:

```text
$ git cat-file -e <sha_inicial> && git log --format='%h %s' -1 <sha_inicial>
A.1  461ee38  docs(specs): registra spec 002 de vitrine, eval e saneamento
A.2  240d708  fix(seguranca): aponta BASE_URL do e2e para ambiente local por padrao
A.3  b9cb561  ci(github): restaura gatilhos automaticos e corrige o alvo check
B.1  fd923d6  docs(seguranca): remove pii e caminho de extracao dos docs de auditoria
B.2  9b3ff80  test(backend): cria schema em fixture e libera testes unit de infra
```

O `sha_inicial` da A.1 passou a ser o commit da própria spec (`461ee38`), que é o
início original da fase, em vez do commit de código — corrigindo também a inconsistência
que o avaliador apontou entre `sha_final` declarado e o commit real da fase.

## 9. Itens em aberto / dúvidas para o avaliador

1. **Pendência residual: a senha da conta do CalorIA em produção não foi trocada.**
   Motivo verificado, não esquecimento: a aplicação **não tem tela de troca de senha
   para usuário autenticado** (`backend/app/api/v1/auth.py` expõe apenas
   `forgot-password` e `reset-password`), e **o envio de e-mail não está configurado
   em produção**, então o fluxo de recuperação não completa. Mitigações que tornam o
   risco residual baixo: a senha foi rotacionada em todos os outros serviços (que era
   o vetor grave, por reuso), o repositório está privado, e a credencial saiu do
   histórico na A.2. Foi entregue ao owner um utilitário
   (`~/trocar-senha-caloria.py`) que troca a senha direto no banco usando o mesmo
   `hash_password` da aplicação. O ambiente de produção será reconstruído na Fase E.4
   de qualquer forma.
2. **AC-1 era insatisfazível pela A.1 isoladamente** — a cláusula "o HEAD de todas as
   branches remotas deve estar livre dela" depende da A.2. Hoje está satisfeita, mas
   a evidência veio da fase seguinte. Sugiro ao avaliador manter a leitura conjunta,
   ou ajustar a spec para mover essa cláusula para o AC-2.
3. **A credencial persistia em 8 arquivos de `docs/`** além dos dois que a A.2
   declarava. Resolvido: o owner autorizou estender o escopo da A.2 aos 10 arquivos.
   Ver §3.1 do relatório da A.2.

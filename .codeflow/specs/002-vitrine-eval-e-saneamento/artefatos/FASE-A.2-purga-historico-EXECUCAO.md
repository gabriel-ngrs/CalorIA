---
spec: 002-vitrine-eval-e-saneamento
fase: A.2
slug_fase: purga-historico
status: executado
tentativa: 1
reprovacoes: 0
sha_inicial: cb2e4ca7bd7323123ab4196d5f5906ff06dda7be
sha_final: 76672b2ba7a60d0b49f3214b7812e4c713bf93b4
range: cb2e4ca7bd7323123ab4196d5f5906ff06dda7be..76672b2ba7a60d0b49f3214b7812e4c713bf93b4
---

# FASE A.2 — Relatório de execução

## 1. Resumo do que foi feito

`docs/auditoria/achados.md` e `docs/auditoria/log.md` foram redigidos cirurgicamente:
saíram o e-mail pessoal, o valor da senha e **os dois comandos de extração** que
ensinavam a recuperar a credencial do histórico; ficou intacta a análise do incidente
(AUD-038 completo, os três vetores de risco, o plano de remediação, os passos de log).
Diff de 7 linhas em `achados.md` e 3 em `log.md` — nenhuma seção foi apagada.

O comando de `git filter-repo`, o plano de force-push e o plano de tratamento dos PRs
do Dependabot estão documentados na §5 deste relatório. **O agente não executou
`filter-repo` nem force-push** — escopo travado da fase.

A varredura de verificação (passo 4) **falha o gate**: a credencial continua em 11
commits do histórico e em 8 arquivos do working tree fora do escopo declarado. Ver §6 e §9.

## 2. Arquivos CRIADOS

Nenhum arquivo de código. Este relatório é o artefato da fase.

## 3. Arquivos ALTERADOS

| Arquivo | O que mudou |
|---------|-------------|
| `docs/auditoria/achados.md` | 3 ocorrências do e-mail → `<e-mail pessoal do mantenedor>`; 3 do valor da senha → `[REDIGIDO]`; comando de extração da linha 36 substituído por prosa ("recuperável a partir do histórico do git, comando omitido por segurança"). |
| `docs/auditoria/log.md` | 2 ocorrências do e-mail e 3 do valor da senha redigidas; comando de extração do PASSO 8.1 removido. O `rg` que varria o *working tree* foi mantido (não é receita de extração de histórico), com os valores trocados por placeholders. |

### 3.1 Extensão de escopo autorizada pelo owner

Ao verificar o passo 4 constatei que a credencial vivia em **mais 8 arquivos** além
dos dois declarados, e que **dois deles ainda publicavam o comando de extração** — o
mesmo problema que a fase existe para eliminar. Reportei antes de agir; o owner
autorizou explicitamente estender o escopo da A.2 a todos eles. Segundo commit:

| Arquivo | O que mudou |
|---------|-------------|
| `docs/auditoria/runbook.md` | Bloco `bash` com os **dois** comandos de extração (varredura do working tree + `git log --all -p ... \| grep <fragmento>`) substituído por prosa que descreve o método sem reproduzi-lo. |
| `docs/auditoria/07-seguranca.md` | 3 ocorrências do e-mail e 5 do valor da senha redigidas; a linha "Comando: …" da §G.6, que trazia os dois comandos de extração, virou "Método: …" sem os literais. |
| `docs/auditoria/artefatos/G1-creds.txt` | Dump bruto da varredura de credenciais: 10 ocorrências do e-mail e as linhas `.fill("…")` redigidas. Arquivo preservado (é evidência da auditoria); candidato à poda da D.4. |
| `docs/auditoria/plano.md` | 1 ocorrência do e-mail + 1 do valor da senha. |
| `docs/auditoria/plano-correcao.md` | 1 ocorrência do e-mail (no passo "trocar a senha em …"). |
| `docs/auditoria/relatorio-preliminar.md` | 1 ocorrência do e-mail. |
| `docs/auditoria/08-testes.md` | 1 ocorrência do e-mail + 1 do valor da senha. |
| `docs/legacy/analise.md` | 1 ocorrência do e-mail (contexto neutro: largura do header). |

Também foram redigidos os **próprios relatórios desta spec** (`FASE-A.1-*` e
`FASE-A.2-*`), que citavam o e-mail e o fragmento dentro dos comandos `grep`
documentados — violação do NFR-4 que eu mesmo introduzi e corrigi.

**Resultado:** `grep -rc 'e-mail | fragmento'` sobre o working tree **inteiro**
(excluindo `.git` e `node_modules`) retorna **0 ocorrências**.

**Preservado (era violação BLOQUEANTE apagar):** AUD-038 íntegro — severidade,
`frontend/e2e/auth.spec.ts:37-38`, commit `4737257`, os três vetores de risco
(acesso à conta, *password reuse*, credential stuffing), o plano de remediação em 4
etapas, o esforço e a origem. Também preservados AUD-047 (pre-commit/gitleaks),
AUD-044 (baseURL apontando para a Vercel) e os PASSOS 8.1 e 8.6 do log com horários,
artefatos e notas analíticas.

## 4. Confirmação do REUSO e decisões de design

- **Reuso:** nenhum código novo. A fase é redação de documento + preparação de comando.
- **Decisão:** usar `git filter-repo --replace-text` (substituição de string) em vez
  de `--path --invert-paths` (remoção de arquivo). Motivo: os arquivos afetados
  (`auth.spec.ts`, os docs de auditoria) **devem continuar existindo** no histórico —
  só o valor sensível precisa sair. Remover os caminhos destruiria o registro de
  engenharia que a própria spec manda preservar.
- **Decisão:** o arquivo de substituições (`replacements.txt`) contém a credencial em
  texto claro por construção. Ele **não pode ser versionado** e deve ser apagado
  depois. Instrução explícita no plano da §5.
- **Desvio:** o passo 4 ("verificar com varredura sobre todo o histórico que não há
  mais achados") foi executado, mas **não pode passar** antes do passo 3, que é do
  owner. A verificação está registrada como linha de base, não como aprovação.

## 5. Comandos rodados + saídas reais

### 5.1 Verificação da redação dos dois arquivos (esperado 0)

```text
$ for f in docs/auditoria/achados.md docs/auditoria/log.md; do
    echo "$f: email=$(grep -c '<e-mail-pessoal>' $f) frag=$(grep -c '<fragmento-da-senha>' $f)"
  done
docs/auditoria/achados.md: email=0 frag=0
docs/auditoria/log.md:     email=0 frag=0

# o diff não INTRODUZ valor sensível
$ git diff HEAD~1 docs/auditoria/ | grep -c '^+.*<fragmento-da-senha>'                    → 0
$ git diff HEAD~1 docs/auditoria/ | grep -c '^+.*<e-mail-pessoal>' → 0

# o diff é cirúrgico, não apaga seções
$ git diff --numstat HEAD~1 docs/auditoria/
7	7	docs/auditoria/achados.md
3	3	docs/auditoria/log.md
```

### 5.2 Varredura de segredos sobre TODO o histórico (passo 4)

```text
$ gitleaks detect --log-opts="--all" --redact --no-banner
INF 421 commits scanned.
INF scan completed in 16.7s
INF no leaks found
EXIT=0
```

> **ACHADO IMPORTANTE — o AC-2 como está escrito é um gate falso.**
> `gitleaks detect --log-opts="--all"` retorna **zero achados hoje, ANTES de qualquer
> purga**, com a credencial ainda em 11 commits. A razão é estrutural: as regras
> default do gitleaks casam segredos com forma reconhecível (chaves de API, tokens,
> chaves privadas), e a credencial exposta aqui é uma **senha arbitrária de usuário**
> numa string TypeScript — nenhuma regra genérica a detecta.
> Logo, satisfazer o AC-2 literalmente **não prova** que a purga funcionou. Ver §9.

### 5.3 Varredura direta pelo valor (a que de fato mede)

```text
$ git log --all --oneline -S'<e-mail-pessoal>' | wc -l   → 11 commits
$ git log --all --oneline -S'<fragmento-da-senha>'                   | wc -l   →  3 commits

$ git show origin/main:frontend/e2e/auth.spec.ts | grep -c '<e-mail-pessoal>'
1        # a credencial SEGUE exposta no HEAD público de main

# commits afetados (data, mensagem, arquivos)
4b58f76 2026-07-30 docs(seguranca): remove pii ...        docs/auditoria/{achados,log}.md
5892d14 2026-05-11 docs(auditoria): plano de correcao     docs/auditoria/plano-correcao.md
e208307 2026-05-11 fix(seguranca): remove credenciais...  frontend/e2e/auth.spec.ts
b093821 2026-05-11 docs(auditoria): relatorio preliminar  docs/auditoria/{log,relatorio-preliminar}.md
83835b4 2026-05-11 docs(auditoria): frente H              docs/auditoria/{08-testes,achados,log}.md
d2d8130 2026-05-10 docs(auditoria): registra credenciais  docs/auditoria/{07-seguranca,achados,log}.md + artefatos/G1-creds.txt
c544aa4 2026-05-10 docs(auditoria): plano e runbook       docs/auditoria/{plano,runbook}.md
8aee828 2026-05-10 docs: sincroniza documentação Groq     (vários)
98f5e1d 2026-05-10 refactor(backend): remove dead code    (vários)
b98522e 2026-04-29 test(e2e): testes Playwright auth      frontend/e2e/auth.spec.ts
d7cf1f0 2026-04-07 docs(analise): analise de UI/UX        analise.md
```

### 5.4 PLANO DE PURGA — para o owner executar (passo 3)

> **O agente não executa nada abaixo.** Escopo travado da fase. `git-filter-repo` não
> está sequer instalado nesta máquina (`python3 -c "import git_filter_repo"` →
> `ModuleNotFoundError`).

**Passo 0 — pré-condição dura.** A rotação da senha (A.1, passo 1) **tem de estar
feita antes**. Reescrever histórico não desfaz o que já foi clonado, indexado por
buscadores ou cacheado pelo GitHub. A rotação é o único controle que interrompe o
dano real (risco R2 da spec).

**Passo 1 — backup espelho (irreversibilidade, §7 da spec).**

```bash
cd /tmp
git clone --mirror https://github.com/gabriel-ngrs/CalorIA.git CalorIA-backup-pre-purge.git
tar czf ~/CalorIA-backup-pre-purge-$(date +%F).tar.gz CalorIA-backup-pre-purge.git
```

**Passo 2 — instalar o filter-repo.**

```bash
pipx install git-filter-repo     # ou: uv tool install git-filter-repo
git filter-repo --version
```

**Passo 3 — clone fresco de trabalho.** `git filter-repo` recusa rodar em repositório
com remotes/reflog sujos; use um clone novo, não o diretório de desenvolvimento.

```bash
cd /tmp && git clone https://github.com/gabriel-ngrs/CalorIA.git CalorIA-purge
cd CalorIA-purge
git fetch origin '+refs/heads/*:refs/heads/*' --prune   # traz TODAS as branches
```

**Passo 4 — arquivo de substituições. NÃO VERSIONAR. Apagar depois.**

Crie `/tmp/replacements.txt` fora de qualquer repositório, com uma linha por valor.
Escreva os valores reais à mão — eles não aparecem neste relatório de propósito:

```text
<e-mail-pessoal-do-owner>==>email-redigido@example.com
<senha-em-texto-claro>==>SENHA-REDIGIDA
<fragmento-de-6-digitos-da-senha>==>REDIGIDO
```

**Passo 5 — reescrever todas as refs.**

```bash
git filter-repo --replace-text /tmp/replacements.txt --force
shred -u /tmp/replacements.txt      # ou rm -P / rm
```

**Passo 5b — DECISÃO PENDENTE DO OWNER: o e-mail nos metadados de autor.**

`--replace-text` age sobre o **conteúdo dos blobs**, não sobre os metadados de commit.
O e-mail pessoal do owner é o `author.email` de **todos os ~439 commits** — foi assim
que a própria auditoria o identificou (`git log --format="%ae"`). Depois do passo 5 ele
**continuará** recuperável por `git log --format="%ae" | sort -u`.

Isso é distinto da exposição de credencial: um e-mail de autor de commit é público por
padrão em qualquer repositório do GitHub, e o próprio owner o expõe hoje. **Não é
tratado por esta fase e não deve ser decidido pelo agente.** Se o owner quiser
eliminá-lo também, o comando é:

```bash
# opção A — mailmap (declarativo, preferível)
printf 'Gabriel <SEU_ID+SEU_USUARIO@users.noreply.github.com> <e-mail-antigo>\n' > /tmp/mailmap
git filter-repo --mailmap /tmp/mailmap --force

# opção B — callback
git filter-repo --email-callback '
  return b"SEU_ID+SEU_USUARIO@users.noreply.github.com" if email == b"<e-mail-antigo>" else email' --force
```

Consequência a pesar antes: reescrever o autor de todos os commits **desvincula o
histórico do perfil do GitHub** se o endereço `noreply` estiver errado — o gráfico de
contribuições some. Verifique seu endereço `noreply` em *Settings → Emails* antes.
Recomendo rodar junto com o passo 5, numa única reescrita, para não fazer dois
force-push destrutivos.

**Passo 6 — conferir antes de publicar.**

```bash
git log --all --oneline -S'<e-mail>'   | wc -l   # esperado 0
git log --all --oneline -S'<senha>'    | wc -l   # esperado 0
git show origin/main:frontend/e2e/auth.spec.ts | grep -c '<e-mail>'   # esperado 0
git rev-list --count --all                       # comparar com 439 (deve bater)
```

**Passo 7 — force-push de todas as branches e tags.**

```bash
git remote add origin https://github.com/gabriel-ngrs/CalorIA.git   # filter-repo remove o remote
git push --force --all origin
git push --force --tags origin
```

**Passo 8 — GitHub Support (indispensável, risco R2).** Force-push **não apaga** os
commits antigos: eles continuam acessíveis por SHA direto (`github.com/<owner>/<repo>/commit/<sha>`)
até o GC do GitHub, que não é garantido. Abrir ticket em
<https://support.github.com/contact> pedindo *"remove cached views and stale commits
for repository gabriel-ngrs/CalorIA after history rewrite"*, citando os SHAs
`b98522e`, `e208307`, `d2d8130`, `83835b4`, `b093821`, `c544aa4`, `5892d14`.

**Passo 9 — reclone local.** Todo clone existente (inclusive
`/home/gabriel/Projetos/CalorIA`) fica divergente. Apagar e reclonar, ou
`git fetch origin && git reset --hard origin/dev`. Commitar tudo que estiver
pendente **antes**.

### 5.5 PLANO DOS PRs DO DEPENDABOT

O force-push invalida as branches base dos PRs abertos. Há **5 PRs abertos** e
**15 branches `dependabot/*`** no remoto:

| PR | Título |
|---|---|
| #17 | `chore(deps): bump @babel/preset-react from 7.28.5 to 8.0.1 in /frontend` |
| #16 | `chore(deps): bump @radix-ui/react-label from 2.1.8 to 2.1.11 in /frontend` |
| #15 | `chore(deps): bump @babel/preset-env from 7.29.0 to 8.0.2 in /frontend` |
| #14 | `chore(deps): bump recharts from 2.15.4 to 3.9.2 in /frontend` |
| #13 | `chore(deps): bump react-dom and @types/react-dom in /frontend` |

**Procedimento recomendado — deixar o Dependabot recriar, não tentar rebasear:**

```bash
# 1. ANTES do force-push: registrar o que existe
gh pr list --state open --limit 50 --json number,title,headRefName > ~/dependabot-prs-pre-purge.json

# 2. DEPOIS do force-push: fechar os 5 PRs com justificativa
for n in 13 14 15 16 17; do
  gh pr close $n --comment "Fechado por reescrita de histórico (purga de credencial exposta, spec 002 fase A.2). O Dependabot recriará este PR na próxima varredura."
done

# 3. Podar as branches órfãs do Dependabot
git push origin --delete $(git branch -r | grep 'origin/dependabot/' | sed 's|origin/||')

# 4. Forçar nova varredura: Insights → Dependency graph → Dependabot → "Check for updates"
```

Decisão consciente registrada: **nenhum dos 5 PRs é de segurança** — são bumps de
versão de dev-dependencies do frontend (`@babel/*`, `@radix-ui/react-label`,
`recharts`, `react-dom`). Fechar e deixar recriar é seguro e mais barato que rebasear
5 branches sobre um histórico reescrito.

## 6. Critérios de aceite da fase (com evidência)

- [x] **AC-2, parte 2** — *"`docs/auditoria/achados.md` não contém comando de
      extração nem e-mail pessoal"*. Evidência: `grep -c` → 0 para e-mail e para o
      fragmento da senha; comando de extração da linha 36 substituído por prosa.
- [ ] **AC-2, parte 1** — *"varredura de segredos sobre todo o histórico
      (`gitleaks detect --log-opts="--all"`) → zero achados"*.
      **Literalmente satisfeito (`EXIT=0`, "no leaks found"), mas o critério é
      vazio** — ele já retornava zero antes de qualquer trabalho. A varredura que
      mede de verdade (`git log -S`) retorna **11 commits com o e-mail e 3 com o
      fragmento da senha**. Considero o AC **NÃO satisfeito** e reporto assim, em vez
      de me abrigar na letra do critério.
- [ ] **Critério de conclusão: "PRs do Dependabot reabertos ou fechados
      conscientemente"** — **NÃO satisfeito.** O plano está escrito e é executável,
      mas depende do force-push, que é do owner. Nenhum PR foi tocado.

## 7. Definition of Done da fase

- [x] Testes da fase: N/A para os dois documentos (markdown). A suíte não foi tocada.
- [x] Comandos de validação: `[—]` — a fase altera apenas markdown em `docs/`, fora
      do alcance de `ruff`, `mypy`, `jest` e `tsc`. `gitleaks` rodado (§5.2).
- [x] Escopo travado respeitado — `filter-repo` **não** executado, force-push **não**
      executado, nenhum achado de auditoria apagado por inteiro, nenhuma migration
      nem código de produção tocado (`git diff --stat` da fase: só os 2 markdowns).
- [x] Nenhum segredo/PII neste relatório — os valores aparecem como placeholders em
      todos os comandos, incluindo o plano de purga.
- [x] Commit em pt-BR: `docs(seguranca): remove pii e caminho de extracao dos docs de auditoria`

## 8. (Em rework) O que mudou nesta tentativa

N/A — primeira execução.

## 9. Itens em aberto / dúvidas para o avaliador

1. **O gate da fase NÃO está satisfeito e a fase não deveria ser aprovada como está.**
   O passo 3 (execução do `filter-repo` + force-push + ticket ao GitHub Support) é
   explicitamente do owner e não aconteceu. A credencial segue em 11 commits e no
   HEAD de `origin/main`.

2. **O AC-2 é um gate falso e precisa de correção na spec.** `gitleaks` com regras
   default retorna zero para senhas arbitrárias — retornou zero *antes* da purga.
   Recomendação concreta: adicionar ao `.gitleaks.toml` (que a Fase A.3 vai criar) uma
   regra customizada que case o e-mail do owner e o padrão da senha, **ou** substituir
   o critério por `git log --all -S'<valor>' | wc -l == 0`. Sem isso, a A.3 entrega um
   scanner que não detectaria o incidente que motivou o Track A inteiro.

3. **DESVIO DE ESCOPO — detectado, reportado e RESOLVIDO com autorização do owner.**
   A spec lista como "Arquivos alterados" apenas `achados.md` e `log.md`, mas a
   credencial vivia em mais 8 arquivos, dois deles publicando o comando de extração.
   Reportei antes de agir (constitution: "modificar fora do escopo declarado exige
   parar e reportar"); o owner autorizou estender a fase aos 8. Detalhe em §3.1.
   **Sugiro atualizar a §5 da spec** para que a lista de "Arquivos alterados" da A.2
   reflita os 10 arquivos, senão o avaliador vai ler o diff como violação de escopo.

4. **`docs/auditoria/artefatos/G1-creds.txt`** é um dump bruto da varredura de
   credenciais da auditoria. Agora está redigido, mas continua sendo um artefato cujo
   propósito era listar segredos encontrados. Candidato natural à poda da Fase D.4
   ("dumps brutos") — sugiro removê-lo lá em vez de mantê-lo redigido para sempre.

5. **LACUNA NOVA no plano de purga, que exige decisão do owner:** o e-mail pessoal é o
   `author.email` de **todos os ~439 commits**, e `--replace-text` **não** toca
   metadados de commit. Depois da purga ele seguirá recuperável por
   `git log --format="%ae"`. Isso é diferente de vazamento de credencial (e-mail de
   autor é público por padrão no GitHub), então **não** ampliei o plano por conta
   própria — registrei as duas opções (`--mailmap` / `--email-callback`) no passo 5b
   da §5.4, com a ressalva de que reescrever o autor pode desvincular o histórico do
   perfil do GitHub. Se o owner quiser, deve rodar **na mesma reescrita** do passo 5,
   para não fazer dois force-push destrutivos.

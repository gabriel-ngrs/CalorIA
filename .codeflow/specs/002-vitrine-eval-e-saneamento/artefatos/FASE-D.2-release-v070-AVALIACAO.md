---
spec: 002-vitrine-eval-e-saneamento
fase: D.2
slug_fase: release-v070
tentativa: 2
veredito: APROVADO
score: 9.8
threshold: 8.5
range_avaliado: b3018b4..7588a35
---

# FASE D.2 — Avaliação independente (tentativa 2)

> **Nota de independência.** Esta avaliação e a da tentativa 1 saíram do mesmo chat
> avaliador. A independência que o protocolo protege é entre **avaliador e executor**, e
> ela vale: o rework foi feito noutra sessão e nenhuma linha dele é minha. O risco
> residual é de viés de confirmação — conferir os próprios achados tende a favorecer o
> "corrigido". Mitigação aplicada: reverifiquei **todas** as cláusulas do AC-19 e as três
> proibições do escopo travado do zero, contra a plataforma e o git, em vez de só marcar
> IMP-1 e IMP-2; e procurei ativamente o que o rework pudesse ter quebrado. A avaliação
> da tentativa 1 está preservada no histórico (`7313bf5`), substituída neste arquivo
> conforme o schema de um AVALIACAO por tentativa.

## 1. Veredito e score

**Veredito:** APROVADO · **Score:** 9.80 / threshold 8.5

Os dois achados IMPORTANTES estão fechados, e fechados no lugar certo — não na prosa do
relatório, mas no estado que sobrevive a ele. O `enforce_admins` da `main` é `true` na
API, com o resto da proteção intacto; a OQ22 existe na §8 da spec, que é o artefato que a
poda da D.4 não remove. As cinco cláusulas do AC-19 continuam válidas, o escopo travado
continua respeitado, e o rework não introduziu regressão: o diff de código do range,
excluídos os artefatos, é **um único hunk aditivo na §8 — 49 linhas inseridas, zero
removidas**. Nenhum arquivo de produto foi tocado, e o `Arquivos alterados: nenhum` da §5
segue verdadeiro no que ele governa.

Vale registrar o que a correção do IMP-2 tem de substantivo: na tentativa 1 a `main`
pública podia receber `push --force` do owner, que é a única conta que empurra. Agora não
pode. A proteção deixou de ser sinalização e passou a ser mecanismo.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 5.0 | As 5 cláusulas do AC-19 reverificadas por mim na plataforma (§6): `origin/dev ^origin/main` → `0` · `refs/tags/v0.7.0 -> tag` · release `Latest` · `license=MIT License` · `Eval do pipeline de IA active 330303766`. Gate da fase agora completo: `enforce_admins: true` + `strict: true` + os dois contexts + `allow_force_pushes:false` + `allow_deletions:false`. Escopo travado reverificado do zero: run `31292521842` `success` no `head_sha b3018b4` promovido · `defe1dc` com dois pais e `2ff130cb` ancestral de `origin/main` · A.2 `APROVADO` desde 2026-08-02. Item global da DoD (`SPEC:1823-1824`) atendido pela OQ22 |
| 2 | Arquitetura e direção de dependências | 3 | 5.0 | Dependências `A.2`/`B.2`/`D.1` todas `APROVADO`; ordem da OQ15 respeitada; contexts da proteção idênticos aos nomes de job do `ci.yml` (`app_id 15368`); `cd.yml` segue inerte — `gh run list --workflow="CD — Deploy em Produção"` sem execução após 2026-08-02, a promoção não publicou nada. O rework é cirúrgico: `git diff b3018b4..7588a35 -- SPEC…md \| grep -c '^-[^-]'` → `0` linhas removidas; §5, ACs e §9 intocados |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5.0 | `enforce_admins: {"enabled": true}` na API — o caminho de force-push na `main` pública fechou para a única conta que empurra. `gitleaks --log-opts="--all"` → 509 commits, `no leaks found`. Árvore sem `.env`/`.pem`, sem o e-mail pessoal do owner, e a ponta antiga da `main` já saneada pela A.2 |
| 4 | Reusar/espelhar, não duplicar | 3 | 5.0 | OQ22 segue o formato de OQ19 (B.5) e OQ21 (C.7), numerada em sequência e inserida em §8 antes da §9 — nenhum mecanismo de registro novo inventado. Contexts da proteção reusados da B.2; notas do release derivadas do `CHANGELOG.md` |
| 5 | Padrões de domínio/aplicação | 2 | 4.5 | Conventional Commits pt-BR nos três commits (`687c38d`, `7588a35`, `e8006c6`); `git log --format='%B' b3018b4..HEAD \| grep -iE "co-authored\|claude\|anthropic\|agente"` → vazio. Tag anotada (objeto tipo `tag`). Desconto que permanece e **não é acionável nesta fase**: a `v0.7.0` cobre a entrada `[0.7.0]` do CHANGELOG **e** toda a seção `[Não lançado]`. Tag publicada não se reescreve sem quebrar quem já a consumiu; a decisão é do owner, está mitigada nas notas do release e agora registrada na OQ22 (a) com a consequência para o próximo corte |
| 6 | Local e nomes dos arquivos | 2 | 5.0 | Frontmatter do EXECUCAO com `fase: D.2`, `slug_fase: release-v070`, `tentativa: 2`, `reprovacoes: 1` e `sha_inicial: b3018b4` reusado da tentativa 1 — coerente com o bloco da §5 (`SPEC:1125-1126`) e com a máquina de estados. OQ22 no lugar certo da §8 |
| 7 | Qualidade de código | 2 | 4.5 | Diff de código do range = um hunk aditivo de 49 linhas na §8; zero arquivos de produto. Relatório reescrito para a tentativa 2 com §8 documentando exatamente o que mudou, e todo número verificável reproduz. Descontos de precisão no texto da OQ22, ambos sem efeito prático — ver sugestões 1 e 2 |
| 8 | Testes e cobertura | 2 | 5.0 | Rodei todos os gates do `manifest.md`: `make lint-check` limpo · `make typecheck` `Success: no issues found in 81 source files` · `make test-unit` `496 passed, 3 skipped` · `make test-integration` `145 passed in 71.94s`. O `[—]` indevido da tentativa 1 sumiu e o executor rodou o alvo por conta própria (`124.70s`), que eu reproduzi. Árvore limpa ao final |
| 9 | Migration safety (se aplicável) | 2 | — | Não aplicável: nenhuma migration tocada, nenhum arquivo de produto alterado. Excluída da média |

**Score:** (5.0·3 + 5.0·3 + 5.0·3 + 5.0·3 + 4.5·2 + 5.0·2 + 4.5·2 + 5.0·2) / 20 = 4.90 → **9.80 / 10**

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

Nenhum. Os dois da tentativa 1 estão fechados, verificados na fonte e não no relatório:

**IMP-1 — decisões de escopo sem registro durável → RESOLVIDO.** A OQ22 está na §8 da
spec (`7588a35`), com as três decisões, o custo da alternativa `v0.8.0` apresentado ao
owner e a consequência de cada uma. Registra também, além do que o achado pedia, que o
próximo corte deve ser `v0.8.0` fechando o `[Não lançado]`, com a `v0.7.0` valendo como
"primeira tag publicada". O motivo do achado era durabilidade — o AC-21 manda a D.4
apagar os `FASE-*-EXECUCAO.md` — e a §8 da spec não é alcançada por essa poda.

**IMP-2 — proteção que não vinculava a única conta que empurra → RESOLVIDO.**
`gh api …/branches/main/protection` devolve `"enforce_admins":{"enabled":true}`, com
`strict: true`, os dois contexts, `allow_force_pushes: false` e `allow_deletions: false`
preservados. A justificativa falsa foi retirada e substituída pelo motivo correto no
relatório (§8) e na OQ22 (c). A ausência de `required_pull_request_reviews` permanece,
por escolha declarada — o Roadmap 9.1:405 pede "PR obrigatório + CI obrigatório", que os
`required_status_checks` entregam, e não revisor obrigatório, que num projeto de um
desenvolvedor não teria quem cumprisse. Concordo com a leitura.

**Sugestão 1 da tentativa 1 também endereçada.** `make test-integration` deixou de ser
`[—]`: o executor rodou (`145 passed in 124.70s`) e eu reproduzi (`145 passed in 71.94s`).

## 5. Sugestões

Nenhuma bloqueia a fase. As duas primeiras são de precisão no texto da OQ22 e podem ser
corrigidas na próxima vez que a spec for tocada; as demais já vinham atribuídas a outras
fases na avaliação anterior.

1. **A OQ22 (a) exagera um argumento que não precisava.** Ela diz que cortar `v0.8.0`
   "desfaz a sincronização em `0.7.0` que a D.1 acabara de fazer e que o **AC-18**
   cobra". O AC-18 (`SPEC:391-394`) exige que a versão seja **a mesma** nos quatro
   arquivos, não que seja `0.7.0` — subir os quatro para `0.8.0` continuaria a
   satisfazê-lo. O pilar que sustenta a decisão é o outro, e esse é sólido: editar
   CHANGELOG e quatro arquivos contraria o `Arquivos alterados: nenhum` da própria §5.
   Sugiro remover a menção ao AC-18 para a OQ não carregar um argumento frágil.

2. **A cláusula de alcance futuro da OQ22 (b) vincula um conjunto vazio.** Ela declara
   que a leitura funcional de "ação do owner" "vale para esta spec inteira daqui em
   diante, incluindo o que restar de ação do owner na D.3, D.4 e E.4". Medido:
   `grep -n "Ação do owner"` na spec devolve cinco ocorrências, todas em A.1 (`:524`,
   `:527`), A.2 (`:567`), D.1 (`:1113`) e D.2 (`:1138`, `:1141`) — fases concluídas.
   **Nenhuma fase aberta tem passo de ação do owner**, então a extensão não autoriza
   nada hoje. Fica a nota para o caso de uma fase futura ganhar um: a autorização que o
   owner deu foi **por ato**, perguntada antes de cada um, e para passo irreversível ou
   voltado para fora (deploy, exposição pública) esse formato é o que deve valer, não uma
   permissão genérica concedida de antemão.

3. **`Roadmap.md:405` segue `[ ]`** ("Proteção da branch `main` no GitHub (PR obrigatório
   + CI obrigatório)"), agora legitimamente satisfeito. A §5 desta fase proíbe alterar
   arquivos de produto, então é item da D.3/D.4, que já tocam documentação.

4. **`homepage` do repositório continua `null`** (confirmado agora na API). Material da
   D.3, junto do README de vitrine.

5. **`artefatos/FASE-E.3-conta-demo-AVALIACAO.md:156`** cita o fragmento do nome do owner
   dentro de um comando `grep` reproduzido, num repositório agora público. Não é segredo
   (gitleaks passa em 509 commits; o handle `gabriel-ngrs` já é público) e a poda da D.4
   remove o arquivo.

6. **A contradição do ADR-009 precisa de decisão do owner antes da próxima fase** —
   confirmada de novo. `docs/architecture.md:225-227` condiciona a remoção de
   `docker-compose.backend.yml` na poda da D.4 a a E.4 ter corrigido a referência antes
   (E.4 → D.4, inverso da ordem textual da §5), enquanto `:194-195` afirma que "não haverá
   deploy nesta spec — a Fase E.4 fica adiada por decisão" e a §9 (`:1855`) segue listando
   E.4 como aberta. Decide se a E.4 roda ou é encerrada por decisão e, por consequência, o
   que a D.4 pode remover. Fora do escopo da D.2, corretamente não tocado nas duas
   tentativas.

## 6. Comandos rodados + saídas reais

```text
# ─── Passo 1: gate estrutural, reexecutado (a spec mudou) ──────────────────────
$ bash ~/.codeflow/framework/core/scripts/run-structural.sh \
    .codeflow/specs/002-vitrine-eval-e-saneamento/SPEC_002_VITRINE_EVAL_E_SANEAMENTO.md
✓ ids de fase únicos (26 fases)          ✓ heading de cada fase casa com o bullet `id`
✓ todos os slugs são kebab-case          ✓ wave: multi com ao menos um id `<TRACK>.<n>`
✓ todo `id` em "Depende de" existe na §5  ✓ cada track tem 3–8 fases
✓ grafo de dependências acíclico          ✓ §5 estruturalmente válida
EXIT=0

# ─── Passo 2: branch, range e diff de código ───────────────────────────────────
$ git branch --show-current
dev
$ git merge-base --is-ancestor 7588a35 HEAD && echo ANCESTOR_OK
ANCESTOR_OK

$ git log --oneline -5
e8006c6 docs(specs): aplica o rework da fase d.2 na tentativa 2
7588a35 docs(specs): registra na oq22 as tres decisoes de escopo da fase d.2
7313bf5 docs(specs): avalia a fase d.2 com ressalvas na tentativa 1
687c38d docs(specs): registra a execucao da fase d.2 e a release v0.7.0
b3018b4 docs(specs): sincroniza a §9 da spec 002 com os vereditos registrados

$ git diff b3018b4..7588a35 -- . ':(exclude).codeflow/specs/*/artefatos/*' --stat
 .../SPEC_002_VITRINE_EVAL_E_SANEAMENTO.md | 49 +++++++++++++++++++
 1 file changed, 49 insertions(+)
   → um único arquivo, um único hunk, aditivo

$ git diff b3018b4..7588a35 -- .../SPEC_002_VITRINE_EVAL_E_SANEAMENTO.md | grep -c '^-[^-]'
0
   → zero linhas removidas: §5, ACs e §9 intocados, como o relatório declara

$ git diff b3018b4..7588a35 --stat        # com artefatos, para visão completa
 SPEC_002_VITRINE_EVAL_E_SANEAMENTO.md            |  49 +++
 artefatos/FASE-D.2-release-v070-AVALIACAO.md     | 417 +++++
 artefatos/FASE-D.2-release-v070-EXECUCAO.md      | 292 +++++
   → os dois .md de artefato são ruído de rework, excluídos pelo filtro do protocolo

# ─── IMP-2: a proteção da main, estado completo ────────────────────────────────
$ gh api repos/gabriel-ngrs/CalorIA/branches/main/protection
{"required_status_checks":{"strict":true,
  "contexts":["Backend — lint e testes","Frontend — lint e build"],
  "checks":[{"context":"Backend — lint e testes","app_id":15368},
            {"context":"Frontend — lint e build","app_id":15368}]},
 "enforce_admins":{"enabled":true},        ← era false na tentativa 1: CORRIGIDO
 "allow_force_pushes":{"enabled":false},
 "allow_deletions":{"enabled":false},
 "required_signatures":{"enabled":false},
 "required_linear_history":{"enabled":false},
 "required_conversation_resolution":{"enabled":false}}
   → required_pull_request_reviews ausente, por escolha registrada na OQ22 (c)

# ─── IMP-1: a OQ22 na §8 da spec ───────────────────────────────────────────────
$ git show 7588a35 -- .../SPEC_002_VITRINE_EVAL_E_SANEAMENTO.md | head -20
+- **OQ22 — As três decisões de escopo da Fase D.2, que viviam só num artefato que a
+  D.4 apaga.** **RESOLVIDO (2026-08-09).** …
+  **(a) A tag `v0.7.0` cobre mais do que a entrada de 0.7.0 do CHANGELOG promete.** …
+  **(b) Os passos 3 e 5 da D.2 estão marcados "Ação do owner" e foram executados
+  pelo agente.** …
+  **(c) A proteção da `main` não exige revisor, e `enforce_admins` estava desligado
+  — o segundo virou.** …
   → inserida entre a OQ21 e o heading "## 9. Definition of Done"

$ grep -n "Ação do owner" .../SPEC_002_VITRINE_EVAL_E_SANEAMENTO.md
524:  1. **Ação do owner, fora do agente:** rotacionar a senha exposta …   (A.1)
527:  2. **Ação do owner:** tornar o repositório privado …                 (A.1)
567:  3. **Ação do owner, fora do agente:** executar `git filter-repo` …   (A.2)
1113: 3. **Ação do owner:** preencher description, topics e homepage …    (D.1)
1138: 3. **Ação do owner:** revisar e mergear; configurar proteção …      (D.2)
1141: 5. **Ação do owner:** tornar o repositório público novamente …      (D.2)
   → nenhuma em D.3, D.4 ou E.4: a extensão futura da OQ22 (b) vincula conjunto
     vazio hoje (sugestão 2)

# ─── AC-19, as cinco cláusulas, reverificadas do zero ──────────────────────────
$ git fetch origin --tags && git log origin/dev ^origin/main --oneline | wc -l
0
$ gh api repos/gabriel-ngrs/CalorIA/git/refs/tags/v0.7.0 --jq '.ref+" -> "+.object.type'
refs/tags/v0.7.0 -> tag                      ← tipo "tag": anotada, não leve
$ gh release list
v0.7.0 — Groq, esteira religada e eval do pipeline de IA  Latest  v0.7.0  2026-08-09T03:46:10Z
$ gh api repos/gabriel-ngrs/CalorIA --jq '"license="+.license.name+" visibility="+.visibility+" default="+.default_branch'
license=MIT License visibility=public default=main
$ gh workflow list | grep -i eval
Eval do pipeline de IA   active   330303766
   → cláusula 5 satisfeita. NÃO disparei execução: o AC pede registro, não rodada,
     e a C.7 mediu 99.768/100.000 tokens/dia — queimar a quota não é papel do avaliador.

# ─── Escopo travado, as três proibições, reverificadas ─────────────────────────
$ gh api repos/gabriel-ngrs/CalorIA/actions/runs/31292521842 --jq '"PR run: "+.conclusion+" head_sha="+.head_sha'
PR run: success head_sha=b3018b4bbd9d26c410da2e0dace51e0fdeaaa5f6
   (a) CI verde sobre o head_sha exato que foi promovido ✓

$ git log -1 --format='%H %P' defe1dc
defe1dc7039… 2ff130cb834e4183e0ff769142740d7871a8a3e3 b3018b4bbd9d26c4…
$ git merge-base --is-ancestor 2ff130cb origin/main && echo "sem reescrita da main"
sem reescrita da main
   (b) merge real com dois pais, ponta antiga preservada: sem force-push ✓

$ grep -E '^(fase|tentativa|veredito):' FASE-A.2-purga-historico-AVALIACAO.md
fase: A.2   tentativa: 2   veredito: APROVADO
   (c) A.2 aprovada em 2026-08-02, sete dias antes do merge ✓

$ gh run list --workflow="CD — Deploy em Produção" --limit 2
… 2026-08-02T13:59:47Z   … 2026-05-11T17:31:17Z
   → nenhuma execução após o merge: a promoção não disparou deploy, como o ADR-009 prevê

# ─── Segurança ─────────────────────────────────────────────────────────────────
$ gitleaks detect --config .gitleaks.toml --log-opts="--all" --no-banner
INF 509 commits scanned.
INF no leaks found
EXIT=0

# ─── Higiene de commit ─────────────────────────────────────────────────────────
$ git log --format='%h | %an | %s' -3
e8006c6 | Gabriel | docs(specs): aplica o rework da fase d.2 na tentativa 2
7588a35 | Gabriel | docs(specs): registra na oq22 as tres decisoes de escopo da fase d.2
7313bf5 | Gabriel | docs(specs): avalia a fase d.2 com ressalvas na tentativa 1

$ git log --format='%B' b3018b4..HEAD | grep -iE "co-authored|claude|anthropic|agente"
(vazio)

# ─── Passo 3: gates de validação do manifest.md, rodados por mim ───────────────
$ make lint-check
All checks passed!
149 files already formatted
./components/auth/Plasma.tsx
  156:26  Warning: react-hooks/exhaustive-deps   ← warning pré-existente, não erro

$ make typecheck
Success: no issues found in 81 source files
Type check frontend (tsc)...                     ← sem saída = sem erro

$ make test-unit
======================== 496 passed, 3 skipped in 4.55s ========================

$ make test-integration
================== 145 passed, 5 warnings in 71.94s (0:01:11) ==================

$ git status --short
(vazio — árvore limpa ao final; o avaliador não mutou nada além deste artefato)
```

## 7. Itens da fase / DoD não atendidos

Nenhum.

- **§5 (bloco da Fase D.2):** os cinco passos executados, o AC-19 satisfeito nas cinco
  cláusulas e o critério de conclusão — proteção de branch configurada — agora completo
  com `enforce_admins: true`. As três proibições do escopo travado conferidas
  individualmente contra a plataforma e o git.
- **§9 (DoD da fase):** a linha `- [ ] **D.2**` (`SPEC:1848`) segue desmarcada, o que
  está correto **até este veredito** — pela regra do ARTIFACTS_SPEC §2.11.3 ela passa a
  `[x]` a partir deste AVALIACAO `APROVADO` na tentativa 2. Marcar a linha é ato de quem
  sincroniza a §9, não do avaliador.
- **Itens globais transversais (§9):** o item *"Toda decisão de escopo tomada durante a
  execução está registrada aqui em §8 ou numa decision do framework"* (`SPEC:1823-1824`),
  que era o IMP-1, está atendido pela OQ22. Os demais verificáveis passam:
  ruff/mypy/eslint/tsc limpos, unit e integration verdes, nenhum artefato versionado com
  credencial ou PII, nenhuma migration tocada, commits em Conventional Commits pt-BR sem
  menção a autor ou agente.

## 8. Divergências entre o relatório e o código real

Nenhuma. Todo número verificável do relatório da tentativa 2 reproduz: os SHAs
(`defe1dc`, `c8bc0548`, `2ff130cb`, `7588a35`), os 270 commits promovidos, o estado
completo da proteção, a visibilidade, a licença, o registro do `eval.yml`, o range e o
recorte do diff. O relatório é explícito onde é desfavorável a si — §8 assume que a
justificativa da tentativa 1 era falsa, com o motivo correto no lugar, e §9.5 declara por
conta própria que o range deixou de ser vazio.

Duas notas de leitura, nenhuma delas contradição:

1. **`gitleaks`: 505 no relatório, 509 aqui.** A diferença são os quatro commits criados
   depois da varredura do executor (`687c38d`, `7313bf5`, `7588a35`, `e8006c6`).
   Consistente.

2. **O range `b3018b4..7588a35` engloba `7313bf5`, que é a avaliação da tentativa 1.**
   É ruído esperado de rework e o filtro `':(exclude).codeflow/specs/*/artefatos/*'` do
   protocolo o remove — foi o que fiz. O diff de código resultante é só a §8 da spec.
   O commit do relatório (`e8006c6`) fica fora do range, acima de `sha_final`, seguindo a
   convenção do executor.

3. **Os quatro commits seguem apenas locais.** `git push` está na deny list do
   `settings.local.json` do usuário. A cláusula 1 do AC-19 mede refs remotas e foi
   satisfeita no estado publicado; este AVALIACAO também ficará local até um
   `git push origin dev`.

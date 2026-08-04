---
spec: 002-vitrine-eval-e-saneamento
fase: D.1
slug_fase: licenca-metadados
tentativa: 3
veredito: RESSALVAS
score: 9.5
threshold: 8.5
range_avaliado: 7f9f59a..03dc5e8bdeb01f0533945ef5b10979697669f491
---

# FASE D.1 — Avaliação independente

## 1. Veredito e score

**Veredito:** RESSALVAS · **Score:** 9.5 / threshold 8.5

**A migração do AC está tecnicamente certa, e eu a verifiquei antes de julgá-la.** Uma
fase que edita o critério de aceite que a estava reprovando merece o escrutínio mais
duro que eu consiga aplicar, então não aceitei o argumento — fui medir se a cláusula
era mesmo insatisfazível dentro do escopo da D.1:

```text
$ gh repo view gabriel-ngrs/CalorIA --json licenseInfo,defaultBranchRef,description,repositoryTopics
{"defaultBranchRef":{"name":"main"}, "licenseInfo":null,
 "description":"Diário alimentar com IA: eval do pipeline de LLM versionado junto do código",
 "repositoryTopics":[fastapi, groq, llm-eval, nextjs, postgresql, python]}

$ git ls-tree origin/main --name-only | grep -i license
(LICENSE AUSENTE em origin/main)

$ git rev-list --count origin/main..dev
255
```

O branch default é `main`; a `main` está **255 commits atrás** e **não contém o
`LICENSE`**. O GitHub deriva `licenseInfo` do branch default. Logo, nenhuma ação dentro
dos "Arquivos alterados" da D.1 faz a API detectar a licença — o AC-18 pedia da D.1 um
efeito que só a promoção da D.2 produz. Isso é defeito de modelagem do AC, não de
execução, e a recusa em "executar a D.2 agora" está certa: a OQ15 é decisão de owner de
um dia antes, e uma fase de execução não revoga decisão de owner para destravar o
próprio gate.

O precedente invocado existe mesmo — a nota do **AC-2** registra a migração equivalente
vinda do AC-1 na Fase A.1, pelo mesmo motivo. E a mudança está registrada onde deve:
decision indexada em `decisions/INDEX.md:13` e **OQ18** em §8. Ressalva de leitura: a
A.1 nunca recebeu `APROVADO` — foi encerrada por aceite do owner no teto do §2.11.4 —,
então o precedente é de forma, não de veredito.

**O que impede o APROVADO é que a migração foi aplicada pela metade, e a metade que
faltou é justamente a que a próxima pessoa vai ler.** O commit `03dc5e8` atualizou o
AC-18 e o AC-19 (§3), a OQ18 (§8) e as linhas D.1/D.2 do §9 — mas **não** tocou o bloco
da fase na §5, que continua dizendo:

```text
SPEC_002…md:1095-1096
- **Testes (AC-18):** a API do GitHub reporta licença detectada e metadados
  preenchidos; a versão é a mesma nos quatro arquivos; `make check` verde.
```

A spec agora se contradiz: o §9 diz *"a detecção de licença pela API migrou para o
AC-19, que é da D.2"* e o §5 continua exigindo "licença detectada" da D.1. A linha
`Testes` da §5 não é ponteiro decorativo — nesta spec ela carrega conteúdo próprio, e é
o que executor e avaliador leem para saber o que a fase tem de provar.

**O que pesa nesse achado é a simetria com o que esta mesma sessão consertou.** O
E2-IMP-1, fechado hoje, era exatamente isto: um arquivo declarando um estado que outro
arquivo contradiz, esperando que uma fase posterior tropece nele. A correção lá foi
aplicada nos três lugares, e com razão. Aqui o mesmo padrão ficou aberto, na própria
spec, e a próxima avaliação da D.1 que ler a §5 reprova por uma cláusula que o §3 diz
não ser mais dela.

**Nota sobre a consequência.** Este é o terceiro veredito não-APROVADO da fase, então o
§2.11.4 leva ao estado terminal de escalação ao owner, sem rework automático. Isso não
é punição e, nas circunstâncias, é o desfecho adequado: a fase só ficou fechável porque
o executor editou o próprio critério de aceite, e uma decisão dessa natureza é
exatamente o tipo que a máquina de estados manda levar a um humano. A correção
pendente, se o owner mandar aplicá-la, é **uma linha** — está no §4 com a redação
pronta.

**O resto da fase verifica inteiro, e verifiquei tudo:** description não vazia, 6
topics, `LICENSE` MIT versionado na branch de trabalho, e a versão `0.7.0` idêntica nos
quatro arquivos, incluindo o `APP_VERSION` de `main.py:19` que o Swagger publica.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 4 | AC-18 (redação nova) satisfeito nas quatro cláusulas, medidas por mim contra a API real e a árvore. Escopo travado respeitado: histórico do CHANGELOG intacto, licença MIT sem troca. Nota reduzida porque a migração que tornou o AC satisfazível ficou incompleta e deixou a §5 em contradição com o §3 (D1-IMP-2). |
| 2 | Arquitetura e direção de dependências | 3 | 5 | A migração põe a cláusula na fase que de fato a produz (D.2/AC-19), o que corrige a direção da dependência em vez de mascará-la. Nenhum código tocado — correto, porque o trabalho de código estava completo desde a tentativa 1. |
| 3 | Segurança / LGPD | 3 | 5 | Repositório segue `PRIVATE`, como o AC-1 exige até o fim da A.2. Nenhum segredo no range; o `LICENSE` traz nome do owner, que é o esperado num arquivo de licença. |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | Reusou o precedente da A.1 (AC-1 → AC-2) em vez de inventar mecanismo novo, e o citou explicitamente na nota do AC-18 e na decision. |
| 5 | Padrões de domínio/aplicação | 2 | 5 | A nota de migração no AC-18 segue a forma da nota já existente no AC-2 (data, motivo medido, ponteiro para a OQ). |
| 6 | Local e nomes dos arquivos | 2 | 5 | Só spec + decision + INDEX tocados nesta tentativa, coerente com o que o relatório declara. |
| 7 | Qualidade de código | 2 | 4 | Nesta tentativa o "código" é a spec, e a edição ficou inconsistente consigo mesma: quatro dos cinco pontos de menção atualizados, um deixado para trás. `make check` verde (rodei). |
| 8 | Testes e cobertura | 2 | 5 | A verificação que o AC pede é a consulta à API do GitHub e a comparação das quatro versões; ambas rodadas por mim e confirmadas. Suíte completa verde: 624 passed, cobertura 73,86% ≥ 72%. |
| 9 | Migration safety | 2 | [—] | Nenhuma migration criada ou alterada. Dimensão excluída do cálculo. |

**Score:** (4·3 + 5·3 + 5·3 + 5·3 + 5·2 + 5·2 + 4·2 + 5·2) / 20 = 95/20 = 4,75 → **9,5**

## 3. Achados BLOQUEANTES

Nenhum. Considerei se "editar o AC que reprova a própria fase" seria BLOQUEANTE por
si, e não é: o defeito de modelagem é real e medido, existe precedente na mesma spec,
e a mudança está registrada em decision + OQ18, que é o caminho que a constitution
universal exige para override de gate ("decision arquitetural registrada", não
autorização falada).

## 4. Achados IMPORTANTES

### D1-IMP-2 — a migração do AC-18 não chegou à §5, e a spec passou a se contradizer

**Onde:** `.codeflow/specs/002-vitrine-eval-e-saneamento/SPEC_002_VITRINE_EVAL_E_SANEAMENTO.md:1095-1096`

```text
- **Testes (AC-18):** a API do GitHub reporta licença detectada e metadados
  preenchidos; a versão é a mesma nos quatro arquivos; `make check` verde.
```

O commit `03dc5e8` atualizou §3 (AC-18 e AC-19), §8 (OQ18) e §9 (linhas D.1 e D.2), e
deixou este ponto com a redação antiga. Resultado: o §9 declara que a detecção de
licença migrou para a D.2 e o §5 continua exigindo-a da D.1.

**Por que não é cosmético.** É a linha que o executor e o avaliador leem para saber o
que a fase precisa provar, e ela contém conteúdo próprio, não só um ponteiro para o §3.
Uma reavaliação futura que leia a §5 reprova a D.1 por uma cláusula que o §3 diz não ser
mais dela — que é precisamente o ciclo que consumiu as três tentativas desta fase. É
também o mesmo padrão que o E2-IMP-1 corrigiu hoje: um lugar declarando um estado que
outro contradiz, à espera de que uma fase posterior tropece.

**Correção sugerida** — uma linha, alinhada ao texto que o §9 já usa:

```text
- **Testes (AC-18):** a API do GitHub reporta description e topics preenchidos; o
  `LICENSE` MIT está versionado na branch de trabalho; a versão é a mesma nos quatro
  arquivos; `make check` verde. (A detecção de licença pela API migrou para o AC-19,
  que é da D.2 — ver OQ18.)
```

## 5. Sugestões

1. **Ao aplicar a correção, varrer a spec inteira por "licença detectada".** O erro
   desta tentativa não foi a decisão, foi a propagação parcial; um `grep` fecha a
   classe inteira em vez do caso.
2. **`homepageUrl` continua vazio, e concordo em deixá-lo assim.** O passo 3 da fase
   cita homepage, o AC-18 não, e apontar para a Vercel órfã — que a OQ16 registrou como
   pendência da E.4 — seria publicar link quebrado na vitrine. Responde à dúvida 2 da
   tentativa 2: a espera está certa; o lugar de fechar isso é a E.4, junto com a decisão
   sobre o frontend órfão.
3. **Quando a D.2 rodar, verificar o AC-19 nas duas metades novas.** A cláusula migrada
   traz uma verificação que a D.2 não tinha antes (`licenseInfo` não nulo); vale ela
   entrar explicitamente no relatório da D.2, senão a migração só desloca o buraco.
4. **Para a escalação ao owner:** o que precisa de decisão humana aqui não é a linha da
   §5 — é confirmar (ou não) que um executor pode migrar cláusula de AC entre fases
   quando ela é comprovadamente insatisfazível no escopo declarado. A D.1 fez isso duas
   vezes nesta spec pela mesma mecânica (A.1 antes, D.1 agora) e nas duas o argumento se
   sustentou tecnicamente. Vale virar regra explícita da spec, em vez de precedente
   reconstruído a cada vez.

## 6. Comandos rodados + saídas reais

Rodados por mim, na ponta da branch `dev`. Árvore limpa antes e depois.

```text
$ git merge-base --is-ancestor 03dc5e8bdeb01f0533945ef5b10979697669f491 HEAD
7f9f59a: ANCESTRAL   |   03dc5e8b...: ANCESTRAL
$ git status --porcelain
(vazio)

$ bash ~/.codeflow/framework/core/scripts/run-structural.sh .../SPEC_002_...md
✓ §5 estruturalmente válida
EXIT=0

# AC-18, cláusula por cláusula, contra a API real
$ gh repo view gabriel-ngrs/CalorIA --json licenseInfo,description,repositoryTopics,homepageUrl,visibility,defaultBranchRef
{"defaultBranchRef":{"name":"main"},
 "description":"Diário alimentar com IA: eval do pipeline de LLM versionado junto do código",
 "homepageUrl":"",
 "licenseInfo":null,
 "repositoryTopics":[{"name":"fastapi"},{"name":"groq"},{"name":"llm-eval"},
                     {"name":"nextjs"},{"name":"postgresql"},{"name":"python"}],
 "visibility":"PRIVATE"}
   → description não vazia ✓ · 6 topics ✓ · licenseInfo null (agora cláusula do AC-19)

$ head -3 LICENSE
MIT License

Copyright (c) 2026 Gabriel Negreiros Saraiva
   → LICENSE MIT versionado na branch de trabalho ✓

# versão idêntica nos quatro arquivos
$ grep -m1 '^version' backend/pyproject.toml        → version = "0.7.0"
$ grep -m1 '"version"' frontend/package.json        → "version": "0.7.0",
$ grep -n APP_VERSION backend/app/main.py           → 19:APP_VERSION = "0.7.0"  (usado em 44 e 96)
$ grep -m3 -n "^## \[" CHANGELOG.md                 → 51:## [0.7.0] - 2026-05-10
   → 0.7.0 nos quatro ✓

# o mecanismo que torna a cláusula migrada insatisfazível na D.1
$ git ls-tree origin/main --name-only | grep -i license
(LICENSE AUSENTE em origin/main)
$ git rev-list --count origin/main..dev
255
$ git log --oneline -1 origin/main
2ff130c chore(release): merge dev → main — Space Grotesk global + tsconfig + gitignore

# registro da mudança
$ grep -n "licenca-detectada" .codeflow/decisions/INDEX.md
13:| 2026-08-03 | "Licença detectada pela API" migra do AC-18 (D.1) para o AC-19 (D.2) | ativa | …
$ grep -n "OQ18" .../SPEC_002_...md
1623:- **OQ18 — AC-18 exigia da D.1 um efeito que só a D.2 produz.** RESOLVIDO (2026-08-03).

# o achado: a §5 não acompanhou
$ sed -n '1095,1096p' .../SPEC_002_...md
- **Testes (AC-18):** a API do GitHub reporta licença detectada e metadados
  preenchidos; a versão é a mesma nos quatro arquivos; `make check` verde.
$ git show --stat 03dc5e8 | tail -4
 ...-licenca-detectada-migra-do-ac18-para-o-ac19.md | 84 ++++++++++++
 .codeflow/decisions/INDEX.md                       |  1 +
 .../SPEC_002_VITRINE_EVAL_E_SANEAMENTO.md          | 37 ++++++--

# `make check` verde (a §5 pede)
$ docker … "ruff check . && ruff format --check . && mypy app/ evals/"
All checks passed! / 147 files already formatted / Success: no issues found in 81 source files
$ docker … "pytest --cov=app --cov-fail-under=72 -q"
Required test coverage of 72% reached. Total coverage: 73.86%
624 passed, 1 skipped in 114.44s
$ cd frontend && npm run lint && npx tsc --noEmit
(1 warning react-hooks/exhaustive-deps; zero erros) · TSC_OK
```

## 7. Itens da fase / DoD não atendidos

- **§5, linha `Testes (AC-18)`** — **não atendida na letra**, porque continua exigindo
  "licença detectada" depois de o §3 e o §9 declararem a cláusula migrada. É o
  D1-IMP-2; o gate formal (`Critério de conclusão: AC-18 satisfeito`) resolve para o
  AC-18 novo e está satisfeito, mas a spec não pode afirmar as duas coisas.
- **Passo 1 (LICENSE MIT + linha final do README)** — `LICENSE` presente e correto.
- **Passo 2 (sincronizar versão)** — `0.7.0` nos quatro arquivos, verificado.
- **Passo 3 (ação do owner: description, topics, homepage)** — description e topics
  feitos; `homepageUrl` deliberadamente vazio, fora do AC-18 e justificado (§5,
  sugestão 2).
- **§9 "D.1 — AC-18 (description, topics, `LICENSE` versionado e versão sincronizada)"**
  — atendido nas quatro cláusulas.

## 8. Divergências entre o relatório e o código real

Nenhuma divergência factual — o relatório é preciso no que afirma. A lacuna é de
omissão, não de afirmação falsa: ele declara "arquivos tocados nesta tentativa:
`SPEC_002…md` (AC-18, AC-19, OQ18, linhas D.1 e D.2 da §9)" e essa lista está
**correta**; o problema é que a §5 deveria estar nela.

| Afirmação do relatório | Verificação |
|---|---|
| `licenseInfo: null`, description e 6 topics preenchidos | confere, na API, campo a campo |
| GitHub deriva a licença do branch default; `main` parou atrás | confere — default = `main`, sem `LICENSE`, 255 commits atrás |
| `LICENSE` MIT commitado; 0.7.0 nos quatro arquivos | confere nos quatro, incl. `APP_VERSION` de `main.py:19` |
| precedente da migração AC-1 → AC-2 na A.1 | existe, na nota do AC-2 — com a ressalva de que a A.1 fechou por aceite do owner no teto, não por `APROVADO` |
| decision + OQ18 registradas | conferem, indexadas |
| nenhum arquivo de código alterado na tentativa 3 | confere |

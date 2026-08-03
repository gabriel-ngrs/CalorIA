---
spec: 002-vitrine-eval-e-saneamento
fase: C.7
slug_fase: eval-ci
tentativa: 2
veredito: RESSALVAS
score: 9.4
threshold: 8.5
range_avaliado: 40e2941..2e6cd1d1d2a7c060d34fda9137c7aa0b25e52a6f
---

# FASE C.7 — Avaliação independente

## 1. Veredito e score

**Veredito:** RESSALVAS · **Score:** 9.4 / threshold 8.5

**O C7-IMP-2 está fechado, e fechado com uma peça a mais do que eu havia pedido.** Os
quatro prompts de produção têm snapshot de payload, o teste é parametrizado sobre o
dicionário — e entrou também `test_o_snapshot_cobre_todos_os_prompts_de_producao`
(`:104`), que reprova se um prompt novo aparecer sem snapshot. O defeito de origem era
exatamente "alguém acrescentou prompt e ninguém travou"; agora ele não se repete em
silêncio. O `sha` do `meal_identify` não mudou, o que confirma que a refatoração da
montagem não moveu o payload existente.

**O C7-IMP-1 continua aberto.** O gate da fase é *"uma execução agendada completa
registrada"*, e ela não ocorreu. O relatório nomeia dois impedimentos; medi os dois, e
encontrei um terceiro que o relatório não nomeia — e que é o único inteiramente sob
controle local:

| Impedimento | Declarado no relatório | O que eu medi |
|---|---|---|
| `GROQ_API_KEY` nos secrets | sim | **confirmado** — `gh secret list` volta vazio; o repositório não tem secret nenhum |
| Quota do free tier esgotada | sim | **refutado** — chamada de 1 token ao provedor respondeu `Hello` |
| `eval.yml` não existe no GitHub | **não** | `gh workflow list` → só CI, CD e Dependabot. O arquivo não está em `origin/dev` nem em `origin/main` |

O terceiro é decisivo para a instrução que a avaliação anterior deu ("disparar por
`workflow_dispatch`"): **não é possível disparar um workflow que o GitHub não conhece.**
Detalhe em §4.

Tudo o mais da fase verifica bem. A camada rápida roda sem rede em 2 s (o AC pede
menos de 60), o `eval.yml` não tem `continue-on-error` em passo nenhum, e o escopo
travado sobre credencial em cassette virou **teste**, não promessa.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 3 | Passos 1–3 entregues e verificados. AC-15 em duas de três partes: camada rápida sem rede em 2 s (§6) e `test_prompt_alterado_sem_regravar_estoura` (`:234`) cobrindo "alterar prompt sem regravar faz falhar". A terceira — "o workflow agendado conclui sem casos vazios" — **não foi exercitada** (§4). Escopo travado respeitado nos quatro itens, incluindo o eval completo fora do PR |
| 2 | Arquitetura e direção de dependências | 3 | 5 | O cassette é um **envelope** sobre o `AIClient` (`test_metodos_nao_envolvidos_vao_ao_cliente_real`, `:248`), não um fork do cliente — métodos não envolvidos seguem para o real. É a direção certa: o eval depende do pipeline, não o contrário |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | O escopo travado "não gravar cassette contendo chave de API" virou teste versionado: `test_nenhum_cassette_versionado_contem_credencial` (`:181`). Regra travada que vira asserção é o padrão que o resto da spec deveria imitar |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | O snapshot reusa a mesma função de montagem de payload do runner; os `sha` saem de execução do próprio teste, não de valor copiado à mão |
| 5 | Padrões de domínio/aplicação | 2 | 5 | `EVAL_RECORD_CASSETTES=1` só na agendada (`eval.yml:110`), replay no CI — a separação que o passo 1 pede |
| 6 | Local e nomes dos arquivos | 2 | 5 | Exatamente os arquivos declarados na §5 |
| 7 | Qualidade de código | 2 | 5 | Os comentários registram o *porquê*: por que a agendada grava (`eval.yml:108-109`), por que não há `continue-on-error` (`:132-134`), por que os `*_fallback` usam texto fixo no snapshot (`test_evals_snapshot.py:44-46`) |
| 8 | Testes e cobertura | 2 | 5 | 23 testes verdes em 0,09 s (§6), incluindo o guarda contra prompt novo sem snapshot |
| 9 | Migration safety | 2 | [—] | Nenhuma migration tocada |

Score = (3·3 + 3·5 + 3·5 + 3·5 + 2·5 + 2·5 + 2·5 + 2·5) / 20 · 2 = 94/20 · 2 = **9.4**

## 3. Achados BLOQUEANTES

Nenhum.

**C7-IMP-2 da tentativa 1 está fechado.** `SNAPSHOT_DE_PAYLOAD` cobre os quatro
prompts de produção, o teste é parametrizado, e há guarda contra prompt novo sem
snapshot:

```text
$ docker exec caloria_backend pytest tests/unit/test_evals_snapshot.py -q
23 passed in 0.09s
$ grep -n "def test_o_snapshot_cobre_todos_os_prompts_de_producao" …
104:    def test_o_snapshot_cobre_todos_os_prompts_de_producao(self) -> None:
```

## 4. Achados IMPORTANTES

**C7-IMP-1 (mantido) — o gate "execução agendada completa registrada" não foi
satisfeito; e dos três impedimentos reais, um está refutado e um não estava nomeado.**

**Onde:** Critério de conclusão da Fase C.7 e §9 do DoD (*"C.7 — AC-15, NFR-2, NFR-3;
execução agendada completa sem casos vazios"*), contra o estado do repositório no
GitHub.

**O que medi, um a um:**

```text
# 1) secret — o relatório está certo
$ gh secret list --repo gabriel-ngrs/CalorIA
(vazio)                         → o repositório não tem secret nenhum configurado

# 2) quota — o relatório NÃO está certo hoje
$ docker exec caloria_backend python -c "…AsyncGroq… max_tokens=1…"
QUOTA OK — resposta recebida: Hello

# 3) o workflow não existe no GitHub — impedimento não nomeado
$ gh workflow list --repo gabriel-ngrs/CalorIA
CD — Deploy em Produção   active
CI                        active
Dependabot Updates        active
$ git show origin/dev:.github/workflows/eval.yml   → NAO
$ git show origin/main:.github/workflows/eval.yml  → NAO
$ git rev-list --count origin/dev..dev
38
```

**Por que o terceiro item importa mais que os outros dois.** A correção que a avaliação
da tentativa 1 sugeriu foi *"configurar `GROQ_API_KEY` nos secrets e disparar `eval.yml`
por `workflow_dispatch`"*. Essa instrução é inexequível como está: o GitHub não oferece
`workflow_dispatch` para um arquivo que não está na branch. O `eval.yml` existe só no
repositório local, junto com outros 37 commits. Um leitor do relatório conclui que
faltam duas ações do owner; na verdade falta uma ação que nem depende de owner —
empurrar — e ela é pré-condição das outras duas.

**Sobre a quota.** A afirmação *"o free tier está esgotado; disparar o `eval.yml` hoje
produziria a falha por 429"* era verdadeira em 2026-08-02 e foi transportada para o
rework de 2026-08-03 sem reteste. O provedor responde agora. Uma chamada de 1 token não
prova que a execução completa (10 casos, com gravação) termina sem esbarrar em RPM — mas
prova que a premissa não é mais verificável, e essa distinção é o que separa "não deu" de
"não tentei".

**Por que não é BLOQUEANTE.** O `eval.yml` está correto e completo: agenda dimensionada
(semanal, `cron: "0 6 * * 1"`), `concurrency` declarada, gravação ligada só na agendada,
gate de limiares por `evals.report verificar`, e **zero** `continue-on-error` — que era
a violação BLOQUEANTE que o escopo travado nomeava. O que falta é execução, não código.

**Correção sugerida, na ordem em que as coisas destravam:**

1. `git push origin dev` — registra o `eval.yml` no GitHub e torna o `workflow_dispatch`
   possível.
2. `gh secret set GROQ_API_KEY --repo gabriel-ngrs/CalorIA`.
3. `gh workflow run eval.yml --ref dev`, enquanto a janela de quota estiver aberta.
4. Anexar a saída (ou o link da execução) como seção datada no EXECUCAO da C.7 e
   reavaliar. **Se a execução estourar por 429**, colar a saída: isso não é fracasso, é
   a medição que o passo 4 da fase pede ("dimensionar a agenda ao rate limit real") e
   vira decision sobre periodicidade, com o dado por trás.

## 5. Sugestões

- **`--repeticoes` no `eval.yml`:** concordo com a decisão de não mexer agora, e a razão
  nova que o relatório dá é melhor que a minha original — a correção do C5-IMP-1 tornou
  explícito que repetir só mede ruído com gravação ligada, que é justamente o modo da
  agendada. Entra junto do primeiro disparo, com número para calibrar.
- **O `eval.yml` não roda em `push`, só em `schedule` e `workflow_dispatch`.** Correto
  por desenho (o escopo travado proíbe eval completo por PR), mas significa que o
  arquivo pode entrar na branch e ficar meses sem nunca executar, sem que nada avise.
  Um passo no CI que só valide a **sintaxe** do `eval.yml` (`actionlint`) custaria
  segundos e pegaria erro de YAML que hoje só apareceria na segunda-feira.
- **O repositório não tem secret nenhum** — inclusive os do CD. Não é achado desta fase,
  mas a Fase E.4 ("deploy automático verificado ponta a ponta") vai esbarrar nisso, e
  vale saber antes de chegar lá.

## 6. Comandos rodados + saídas reais

> Gates compartilhados rodados uma vez sobre o HEAD atual (`0e570a6`), descendente do
> `sha_final` desta fase.

```text
# --- Passo 2: ancestralidade e árvore limpa ---
$ git status --porcelain | wc -l
0
$ git merge-base --is-ancestor 40e2941 HEAD                                  → ANCESTRAL
    40e2941 fix(ai): propaga a correcao do bug 001 ao VisionParser
$ git merge-base --is-ancestor 2e6cd1d1d2a7c060d34fda9137c7aa0b25e52a6f HEAD → ANCESTRAL

# --- C7-IMP-2 fechado: os quatro prompts travados ---
$ sed -n '35,40p' backend/tests/unit/test_evals_snapshot.py
SNAPSHOT_DE_PAYLOAD = {
    "meal_identify": "ee413e7a6a32…",     # inalterado — produção não se moveu
    "meal_fallback": "237cd3db2dfc…",
    "vision_identify": "3c774d4c02ff…",
    "vision_fallback": "7adc5e0b4d86…",
}
$ grep -n "def test_" backend/tests/unit/test_evals_snapshot.py | sed -n '2p'
104:    def test_o_snapshot_cobre_todos_os_prompts_de_producao   ← guarda novo   ✓
$ docker exec caloria_backend pytest tests/unit/test_evals_snapshot.py -q
23 passed in 0.09s                                                             ✓

# --- AC-15: camada rápida sem rede, teto de 60s ---
$ docker exec caloria_backend python -m evals.runner --cassettes
runner replay: 2s                                                              ✓
$ docker exec caloria_backend pytest tests/unit -q
472 passed in 3.91s   (suíte inteira: 6s de parede)                            ✓

# --- escopo travado: sem continue-on-error, credencial coberta por teste ---
$ grep -c "continue-on-error" .github/workflows/eval.yml
0                                     (só a menção no comentário :132)         ✓
$ grep -n "def test_nenhum_cassette_versionado_contem_credencial" …
181:    def test_nenhum_cassette_versionado_contem_credencial                   ✓
$ grep -n "cron\|concurrency\|EVAL_RECORD_CASSETTES\|verificar" .github/workflows/eval.yml
15:    - cron: "0 6 * * 1"
24:concurrency:
110:          EVAL_RECORD_CASSETTES: "1"
136:        run: python -m evals.report verificar --relatorio …/ultimo-relatorio.json  ✓

# --- o achado 4.1: os três impedimentos, medidos ---
$ gh secret list --repo gabriel-ngrs/CalorIA
(vazio)                                                    → secret ausente  (confirma)
$ docker exec caloria_backend python -c "…AsyncGroq… max_tokens=1…"
QUOTA OK — resposta recebida: Hello                        → quota           (refuta)
$ gh workflow list --repo gabriel-ngrs/CalorIA
CD — Deploy em Produção / CI / Dependabot Updates          → eval.yml ausente (novo)

# --- gates do manifest, sobre o HEAD atual ---
$ docker exec caloria_backend pytest -q --cov=app --cov=evals
620 passed, 1 skipped — Required test coverage of 72.0% reached. Total coverage: 74.28%
$ docker exec caloria_backend ruff check .          → All checks passed!
$ docker exec caloria_backend ruff format --check . → 147 files already formatted
$ docker exec caloria_backend mypy app/ evals/      → Success: no issues found in 81 source files
$ cd frontend && npm test / npm run lint / npx tsc --noEmit → 118/118 · exit 0 · exit 0

$ git status --porcelain | wc -l
0
```

## 7. Itens da fase / DoD não atendidos

| Item (§5 / §9 da spec) | Estado |
|---|---|
| Passo 1 — gravação e replay, CI configurado para não gravar | Atendido |
| Passo 2 — snapshot do payload dos prompts | Atendido nesta tentativa (4 de 4 + guarda) |
| Passo 3 — workflow agendado com artifact e gate de limiar | Atendido **como código**; nunca executado |
| Passo 4 — agenda dimensionada ao rate limit real | **PARCIAL** — semanal escolhida sem o dado; o dado só vem da primeira execução |
| AC-15 — camada rápida sem rede em < 60 s | Atendido (2 s) |
| AC-15 — prompt alterado sem regravar quebra o CI | Atendido (`:234`) |
| **AC-15 / NFR-3 — execução agendada conclui sem casos vazios** | **NÃO ATENDIDO** — nunca executada (achado 4.1) |
| Escopo travado — sem credencial em cassette, sem `continue-on-error`, eval completo fora do PR | Atendido, e o primeiro virou teste |

## 8. Divergências entre o relatório e o código real

1. **Nenhuma divergência no código.** Os quatro `sha` estão no arquivo, o teste guarda
   existe, e o `eval.yml` é o que o relatório descreve.

2. **Divergência factual — "o free tier está esgotado".** Medido hoje: o provedor
   responde. Premissa correta na origem, não retestada no rework.

3. **Omissão material — o `eval.yml` não está no GitHub.** O relatório lista dois
   impedimentos e conclui "quando as duas condições existirem, disparar por
   `workflow_dispatch`". Falta o terceiro, que é pré-condição dos outros dois e não
   depende do owner: os 38 commits não empurrados. Sem isso a instrução não é
   executável.

4. **Correção do relatório sobre a minha sugestão de `--repeticoes`:** o motivo que ele
   dá para adiar é melhor que o que eu havia escrito. Registro porque é o segundo caso
   nesta fase em que o executor entrega acima do pedido, e não abaixo.

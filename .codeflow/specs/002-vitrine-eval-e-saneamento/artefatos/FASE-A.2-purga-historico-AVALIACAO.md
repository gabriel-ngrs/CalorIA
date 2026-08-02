---
spec: 002-vitrine-eval-e-saneamento
fase: A.2
slug_fase: purga-historico
tentativa: 2
veredito: APROVADO
score: 9.8
threshold: 8.5
range_avaliado: 240d70887daf0cf8ac86061b6f4d0574eb6620e3..721f0f0892b3298964b04b917e3f1b0cb5a1cc69
---

# FASE A.2 — Avaliação independente

## 1. Veredito e score

**Veredito:** APROVADO · **Score:** 9.8 / threshold 8.5

Os três IMPORTANTES da tentativa 1 eram todos de **registro**, e os três foram
fechados no lugar que a spec designa — não com uma nota de relatório, que é
exatamente o defeito que se apontou:

- **4.1** (escopo de 2 → 10 arquivos): a §5 da spec agora lista os 10 nominalmente,
  com nota de por que cresceu; §8 ganhou a **OQ7**; e existe
  `decisions/2026-08-02-extensao-escopo-redacao-pii-auditoria.md`.
- **4.2** (ticket ao GitHub Support omitido): **OQ10** na §8, nota inline no passo 3
  da §5, e `decisions/2026-08-02-omissao-ticket-github-support.md`, com o risco
  residual e a mitigação amarrados à Fase D.2.
- **4.3** (`range` não reconstruível): remapeado para `240d708..721f0f0`, ambos
  ancestrais de HEAD — verificado.

Nada de código mudou nesta tentativa, e não precisava mudar. Reverifiquei a purga
de forma independente, sem depender do relatório: `gitleaks` com as regras do
projeto sobre 422 commits retorna `no leaks found`, e não há e-mail pessoal do owner
em lugar algum da árvore. O achado AUD-038 continua íntegro, sem os dados.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 5 | AC-2 ✓ nas duas partes exigidas pelo texto novo (§6). Escopo travado ✓: `filter-repo`/force-push não executados pelo agente, nenhum achado apagado, nenhuma migration ou código de produção tocado. O desconto da tentativa 1 (escopo estendido sem registro) some: spec §5 com os 10 arquivos, OQ7, OQ10 e duas decisions |
| 2 | Arquitetura e direção de dependências | 3 | 5 | Fase documental; o plano da §5.4 (backup espelho, clone fresco, `replacements.txt` fora de qualquer repo e destruído) continua bem construído |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | Purga reverificada por mim: `gitleaks --config .gitleaks.toml` sobre 422 commits → `no leaks found`, exit 0; grep próprio por e-mail de provedor de consumo fora de `data/` → só as duas contas sintéticas declaradas. A omissão do ticket ao Support deixou de ser acordo verbal: OQ10 + decision, com a mitigação escrita |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | `--replace-text` em vez de `--path --invert-paths` — preserva os arquivos no histórico e remove só o valor |
| 5 | Padrões de domínio/aplicação | 2 | 5 | Redação por placeholder consistente (`<e-mail pessoal do mantenedor>`, `[REDIGIDO]`) nos 10 arquivos |
| 6 | Local e nomes dos arquivos | 2 | 5 | Tudo em `docs/auditoria/` + `docs/legacy/analise.md`; nada fora de `docs/` |
| 7 | Qualidade de código | 2 | 5 | Diff cirúrgico; nenhuma seção apagada; `achados.md:27` mantém AUD-038 com severidade, os três vetores de risco e o plano de remediação |
| 8 | Testes e cobertura | 2 | 4 | Não há teste aplicável a markdown; a verificação é `gitleaks` + grep, e reproduzi ambos. Desconto mantido: o bullet "Testes" da §5 pede "suíte completa verde após a reescrita" e o relatório continua sem colar essa saída — rodei por conta própria e está verde (§6) |
| 9 | Migration safety | 2 | [—] | Nenhuma migration tocada (NFR-7) |

Score = (3·5 + 3·5 + 3·5 + 3·5 + 2·5 + 2·5 + 2·5 + 2·4) / 20 · 2 = **9.8**

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

Nenhum.

## 5. Sugestões

- **`docs/auditoria/07-seguranca.md:210` ainda descreve a senha** ("`[REDIGIDO]`
  tem 8 chars + especiais"). O valor saiu; comprimento e classe de caracteres
  ficaram. Risco hoje nulo (senha rotacionada nos serviços de reuso), mas é o único
  ponto onde a redação da fase ficou incompleta. Mantido da avaliação anterior,
  ainda não endereçado.
- **Restam menções genéricas a `git log -p` em `docs/auditoria/`** — `07-seguranca.md:27`
  ("`git log -p` permite extração trivial"), `plano.md:424`
  (`git log -p | grep -iE "api_key|secret|password"`) e as referências a
  `git filter-repo` em `plano-correcao.md:112-113`. Não classifico como violação do
  AC-2: nenhuma delas é o caminho de extração *daquela* credencial (que não existe
  mais no histórico), e as de `filter-repo` são instruções de **remediação**, não de
  extração. Registro para que uma releitura futura não as confunda com o que a fase
  removeu.
- **`docs/auditoria/artefatos/G1-creds.txt`** segue sendo um dump cujo propósito era
  listar segredos, agora redigido. Concordo com o executor e com a avaliação
  anterior: podar na Fase D.4 é melhor que mantê-lo redigido para sempre.
- **O `range` resolve mas não isola.** `240d708..721f0f0` cobre as cinco fases do
  lote. É o que o schema manda (§2.9.3: "sempre do início original ao HEAD"), mas os
  commits de código desta fase são `fd923d6` e `c69fbfb`; vale nomeá-los no corpo do
  relatório para quem for auditar o diff da fase isoladamente.
- **A dependência `A.1` não está concluída.** A A.2 declara `Depende de: A.1`, e a
  A.1 permanece reprovada nesta rodada (pendência de rotação da conta de produção).
  Não bloqueia esta avaliação — a A.2 já executou e o trabalho está verificado —, mas
  significa que o **Track A não está fechado** mesmo com A.2 e A.3 aprovadas.

## 6. Comandos rodados + saídas reais

```text
# --- branch e ancestralidade (Passo 2) ---
$ git rev-parse --short HEAD
da08121
$ git merge-base --is-ancestor 240d70887daf0cf8ac86061b6f4d0574eb6620e3 HEAD  → ANCESTRAL
$ git merge-base --is-ancestor 721f0f0892b3298964b04b917e3f1b0cb5a1cc69 HEAD  → ANCESTRAL

# --- AC-2, parte (a): varredura de segredos com as regras do projeto ---
$ gitleaks detect --source . --config .gitleaks.toml --redact --no-banner --exit-code 1
INF 422 commits scanned.
INF scan completed in 14.3s
INF no leaks found
>>> EXIT=0                                                                 ✓

# --- AC-2, parte (b): verificação independente de heurística ---
# Não executo `git log --all -S'<valor da credencial>'` porque não tenho — nem devo
# ter — o valor. A verificação equivalente que posso fazer sem ele é a busca literal
# pelo e-mail pessoal, que era o outro lado do par:
$ grep -rInE '[A-Za-z0-9._%+-]+@(gmail|hotmail|outlook|yahoo|icloud|proton|live|bol|uol|terra)\.' \
    --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=.next \
    --exclude-dir=.venv --exclude-dir=data .
   → só `devteste@gmail.com` (seed de dev) e `auditcaloria@gmail.com` (auditoria de
     março), ambas declaradas nas allowlists de `.gitleaks.toml:88-104`.
     Zero ocorrências do e-mail pessoal do owner.                          ✓

# --- AC-2: docs de auditoria sem PII, com o achado preservado ---
$ grep -n "AUD-038" docs/auditoria/achados.md | head -2
27:### AUD-038 — 🔴 Credenciais reais hardcoded em `frontend/e2e/auth.spec.ts` …
221:… Combina com AUD-038 (vazamento da senha do mantenedor) …
   # o achado, a severidade e a análise sobrevivem; os dados não.

# --- registro do escopo, que era o objeto dos três IMPORTANTES ---
$ ls .codeflow/decisions/ | grep 2026-08-02
2026-08-02-extensao-escopo-redacao-pii-auditoria.md      ← IMPORTANTE 4.1
2026-08-02-omissao-ticket-github-support.md              ← IMPORTANTE 4.2
2026-08-02-regras-proprias-gitleaks.md
2026-08-02-senha-conta-caloria-producao.md
2026-08-02-smoke-test-como-sonda-de-ambiente.md
$ grep -n "OQ7\|OQ10" .codeflow/specs/002-*/SPEC_002_*.md | head -4
1440:- **OQ7 — Extensão da redação de PII … RESOLVIDO (2026-08-02).**
1478:- **OQ10 — Ticket ao GitHub Support … RESOLVIDO (2026-08-02).**
$ sed -n '524,534p' .codeflow/specs/002-*/SPEC_002_*.md
- **Arquivos alterados:** `docs/auditoria/achados.md`, `docs/auditoria/log.md`,
  `docs/auditoria/runbook.md`, `docs/auditoria/07-seguranca.md`,
  `docs/auditoria/artefatos/G1-creds.txt`, `docs/auditoria/plano.md`,
  `docs/auditoria/plano-correcao.md`, `docs/auditoria/relatorio-preliminar.md`,
  `docs/auditoria/08-testes.md`, `docs/legacy/analise.md`.
   # os 10 reais, com a nota de escopo corrigido logo abaixo                ✓

# --- estrutura da §5 da spec continua válida (gate determinístico do Passo 1) ---
$ bash ~/.codeflow/framework/core/scripts/run-structural.sh \
    .codeflow/specs/002-vitrine-eval-e-saneamento/SPEC_002_VITRINE_EVAL_E_SANEAMENTO.md
✓ §5 estruturalmente válida
>>> EXIT=0

# --- "suíte completa verde após a reescrita" (o bullet Testes da §5) ---
$ backend/.venv/bin/python -m ruff check .          → All checks passed!
$ backend/.venv/bin/python -m ruff format --check . → 119 files already formatted
$ backend/.venv/bin/python -m mypy app/             → Success: no issues found in 72 source files
$ backend/.venv/bin/python -m pytest tests/unit/ -q → 199 passed in 2.73s
$ cd frontend && npm test                           → 17 suites, 100 passed
$ cd frontend && npm run lint                       → 1 Warning pré-existente; exit 0
$ cd frontend && npx tsc --noEmit                   → exit 0

# --- make test-integration: [—] NÃO RODADO ---
$ docker ps
The command 'docker' could not be found in this WSL 2 distro.
   # gate ausente do ambiente → `[—]` (SPEC §3.10)

# --- árvore limpa ao final ---
$ git status --porcelain | wc -l
0
```

## 7. Itens da fase / DoD não atendidos

| Item (§5 / §9 da spec) | Estado |
|---|---|
| Passo 1 — reescrever os 10 documentos declarados | Atendido |
| Passo 2 — preparar/documentar `filter-repo` + force-push + plano do Dependabot | Atendido |
| Passo 3 — owner executa `filter-repo` + force-push | Atendido |
| Passo 3 — solicitar invalidação de cache ao GitHub Support | **Omitido por decisão registrada** — OQ10 + decision; deixou de ser pendência silenciosa |
| Passo 4 — varredura sobre todo o histórico sem achados | Atendido, reverificado por mim |
| Testes — "suíte completa verde após a reescrita" | Verde (rodado por mim); o relatório continua sem colar a saída |
| Gate — documentos reescritos, PRs do Dependabot tratados | Atendido |
| DoD global — decisão de escopo registrada em §8 ou decision | **Atendido nesta tentativa** (OQ7, OQ10, duas decisions) |

## 8. Divergências entre o relatório e o código real

1. **Nenhuma divergência.** Reproduzi as medições centrais (gitleaks sobre o
   histórico com as regras do projeto, ausência de e-mail pessoal na árvore,
   integridade do AUD-038) e todas conferem. O relatório continua conservador:
   declara `[—]` onde não rodou gate.

2. **O `range` foi corrigido e agora resolve** — os dois SHAs são ancestrais de
   HEAD. Fecha o IMPORTANTE 4.3 da tentativa 1.

3. **Registro herdado, ainda válido:** o `--replace-text` não toca metadados de
   commit, então o e-mail do owner segue como `author.email` do histórico. É decisão
   consciente registrada no relatório; e-mail de autor é público por padrão no
   GitHub. Sem ação recomendada.

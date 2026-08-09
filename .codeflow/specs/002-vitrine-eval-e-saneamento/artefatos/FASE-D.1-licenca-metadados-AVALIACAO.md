---
spec: 002-vitrine-eval-e-saneamento
fase: D.1
slug_fase: licenca-metadados
tentativa: 4
veredito: APROVADO
score: 9.7
threshold: 8.5
range_avaliado: 7f9f59a..208d85d
---

# FASE D.1 — Avaliação independente

## 1. Veredito e score

**Veredito:** APROVADO · **Score:** 9.7 / threshold 8.5 — zero BLOQUEANTES, zero
IMPORTANTES.

**Fui verificar o AC-18 cláusula por cláusula contra as fontes, não contra o
relatório**, porque uma fase na quarta tentativa merece o escrutínio mais duro que
eu consiga aplicar. As quatro passam:

| Cláusula do AC-18 | Verificação minha |
|---|---|
| description não vazia | `gh repo view` → *"Diário alimentar com IA: eval do pipeline de LLM versionado junto do código"* |
| topics não vazios | 6: `fastapi`, `groq`, `llm-eval`, `nextjs`, `postgresql`, `python` |
| `LICENSE` MIT versionado na branch de trabalho | `head -3 LICENSE` → "MIT License" |
| versão igual nos quatro arquivos | `0.7.0` em `pyproject.toml`, `package.json`, `main.py:19` e `CHANGELOG.md:51` |

**E o achado que reprovava a fase está fechado.** O D1-IMP-2 era a §5 exigindo
"licença detectada pela API" depois de a OQ18 tê-la migrado para o AC-19. A linha
`Testes (AC-18)` foi reescrita e hoje pede só o que a D.1 controla; a varredura que
o avaliador da t3 sugeriu foi feita de verdade, e é o que mais me convenceu: ela
achou **um segundo ponto que o achado não citava** (a OQ15 afirmando "a D.1 não
fecha até lá") e **um terceiro por medição** ("nada em C.7 depende disto", falso).
Rodei o mesmo `grep` e as oito ocorrências de `licença detectada|licenseInfo` estão
todas coerentes agora — nenhuma exige da D.1 o que só a D.2 produz.

O padrão que a fase pede que eu registre (dúvida 2 do relatório) está na §5.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 5 | AC-18 verificado nas quatro cláusulas (§1, saídas em §6). Escopo travado intacto: `git log -p -- CHANGELOG.md` sem reescrita de histórico; licença segue MIT |
| 2 | Arquitetura e direção de dependências | 3 | [—] | Nenhum código nesta tentativa; nada a acoplar |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | `gitleaks` sobre 496 commits → no leaks; nenhum e-mail pessoal ou credencial nos textos alterados (§6) |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | A redação da §5 é a que o avaliador da t3 deixou pronta, verbatim; a nota de retratação na OQ15 espelha a forma já usada na OQ18 e na A.1 |
| 5 | Padrões de domínio/aplicação | 2 | 5 | Correção feita na spec (fonte de verdade), com ponteiro para a OQ que a originou — o mesmo rito das migrações anteriores |
| 6 | Local e nomes dos arquivos | 2 | 5 | Decision em `.codeflow/decisions/2026-08-04-quarta-tentativa-da-d1-autorizada-no-teto.md`, indexada em `decisions/INDEX.md` |
| 7 | Qualidade de código | 2 | 4 | O artefato ficou correto e legível. Desconto pelo que a fase deixa em aberto **no nível da spec**: a FR-D1 lista "homepage" e nenhum AC a cobre — deferida com boa razão, mas segue órfã (§5) |
| 8 | Testes e cobertura | 2 | [—] | Nada testável além do `make check`, que a linha `Testes` da fase exige e que rodei verde (§6) |
| 9 | Migration safety (se aplicável) | 2 | [—] | Nenhuma migration no diff |

Score = 73 / 15 × 2 = **9.7**.

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

Nenhum. O D1-IMP-2 da tentativa 3 está fechado, e a varredura fechou dois pontos
que ninguém tinha pedido.

## 5. Sugestões

1. **`homepageUrl` continua vazio, e a FR-D1 o pede.** Concordo com a deferição —
   apontar para a Vercel órfã publicaria link quebrado —, e o avaliador da t3 já
   havia concordado. Mas registro para o owner que isso **não** está coberto por AC
   nenhum: a FR-D1 diz "LICENSE MIT, description, topics, **homepage** e versão
   sincronizada", e o AC-18 não menciona homepage. Quando a E.4 publicar a URL,
   convém fechar o laço acrescentando a cláusula ao AC-19 ou ao AC-27 — senão a
   FR-D1 fica sem verificação até o fim da spec.
2. **Sobre a dúvida 2 — "vale o avaliador registrar se enxerga algo no processo que
   produza esse padrão".** Enxergo, e é específico: as três fases com a mesma
   assinatura (A.1, D.1, C.7) têm ACs cujo sujeito é o **GitHub**, não o
   repositório local. Tudo que a §3 escreve como "a API do GitHub reporta X" só é
   satisfazível a partir do branch default, e o branch default está congelado por
   decisão de owner até o fim da spec. Não é falha de execução nem de avaliação: é
   um AC escrito contra um sistema externo cujo estado outra fase controla. A regra
   preventiva cabe numa frase, e vale para a próxima spec: **um AC não deve
   depender de efeito produzido por uma fase da qual a sua não depende no grafo.**
   Onde isso for inevitável, a cláusula nasce na fase que produz o efeito.
3. **Sobre a dúvida 1 — "um executor pode migrar cláusula de AC?"** Escalar em vez
   de decidir sozinho foi a atitude certa. Minha contribuição: separar as duas
   perguntas. *Migrar* (a cláusula continua exigida, muda de dono) é reversível e
   auditável, e me parece admissível com decision registrada. *Descartar* (a
   cláusula deixa de ser exigida) é outra coisa e deveria exigir owner sempre —
   avaliei a C.7 nesta mesma leva e ali a segunda coisa aconteceu sem rito. A regra
   que falta não é "pode ou não pode", é **destino nomeado e nada some em silêncio**.
4. **Sobre a dúvida 3 (retratar texto de OQ de owner).** Não é desvio. A OQ15
   permanece com a decisão intacta — a `main` segue intocada —, e o que foi marcado
   como falso eram duas *consequências* declaradas, uma delas refutada por medição.
   Deixar afirmação falsa de pé num documento que outras fases leem seria pior; a
   forma usada (nota datada, sem apagar o original) é a correta.

## 6. Comandos rodados + saídas reais

```text
$ git merge-base --is-ancestor 208d85d HEAD && echo "208d85d ANCESTRAL OK"
208d85d ANCESTRAL OK

# --- AC-18, as quatro cláusulas, verificadas por mim ---
$ gh repo view gabriel-ngrs/CalorIA --json licenseInfo,description,repositoryTopics,homepageUrl,visibility,defaultBranchRef
{"defaultBranchRef":{"name":"main"},
 "description":"Diário alimentar com IA: eval do pipeline de LLM versionado junto do código",
 "homepageUrl":"",
 "licenseInfo":null,
 "repositoryTopics":[{"name":"fastapi"},{"name":"groq"},{"name":"llm-eval"},
                     {"name":"nextjs"},{"name":"postgresql"},{"name":"python"}],
 "visibility":"PRIVATE"}
   → description ✓ · 6 topics ✓ · licenseInfo null é cláusula do AC-19 (D.2), não desta fase

$ head -3 LICENSE
MIT License

Copyright (c) 2026 Gabriel Negreiros Saraiva

$ grep -m1 '^version' backend/pyproject.toml   → version = "0.7.0"
$ grep -m1 '"version"' frontend/package.json   → "version": "0.7.0",
$ grep -n 'APP_VERSION' backend/app/main.py    → 19:APP_VERSION = "0.7.0"
                                                 44:    version=APP_VERSION,
$ grep -n '^## \[' CHANGELOG.md | head -2      → 10:## [Não lançado]
                                                 51:## [0.7.0] - 2026-05-10
   → 0.7.0 nos quatro, inclusive o que o Swagger publica

# --- a correção do D1-IMP-2, e a varredura ---
$ grep -n "licença detectada\|licenseInfo" .codeflow/specs/.../SPEC_002_*.md
383   nota do AC-18 (migração)                        correta
391   cláusula do AC-19                               correta
1588  OQ15, retratação (a)                            corrigida nesta tentativa
1638  texto da OQ18                                   correta
1645  texto da OQ18                                   correta
1741  §9, linha da D.2                                correta
   → a §5 `Testes (AC-18)` NÃO aparece mais: era o D1-IMP-2, e está fechado
$ sed -n '1098,1101p' .codeflow/specs/.../SPEC_002_*.md
- **Testes (AC-18):** a API do GitHub reporta description e topics preenchidos; o
  `LICENSE` MIT está versionado na branch de trabalho; a versão é a mesma nos quatro
  arquivos; `make check` verde. (A detecção de licença pela API migrou para o AC-19,
  que é da D.2 — ver OQ18.)

$ bash ~/.codeflow/framework/core/scripts/run-structural.sh \
    .codeflow/specs/002-vitrine-eval-e-saneamento/SPEC_002_VITRINE_EVAL_E_SANEAMENTO.md
✓ ids de fase únicos (26 fases) … ✓ §5 estruturalmente válida     >>> EXIT=0

# --- `make check`, que a linha `Testes` da fase exige ---
$ docker compose -f docker-compose.dev.yml exec -T backend sh -c \
    "ruff check . && ruff format --check . && mypy app/ evals/"
All checks passed! / 149 files already formatted / Success: no issues found in 81 source files
$ docker compose -f docker-compose.dev.yml exec -T backend pytest tests/unit -q
496 passed, 3 skipped in 4.01s
$ docker compose -f docker-compose.dev.yml exec -T backend pytest tests/integration/ -q
145 passed, 5 warnings in 86.98s

$ gitleaks detect --source . --config .gitleaks.toml --redact --no-banner --exit-code 1
496 commits scanned. no leaks found     >>> EXIT=0

# --- escopo travado ---
$ git diff 7f9f59a..208d85d -- CHANGELOG.md | wc -l
0                                       ← histórico do CHANGELOG intocado nas quatro tentativas
$ grep -c "MIT" LICENSE
(licença segue MIT; nenhuma troca)

$ git status --short
(vazio — árvore limpa ao fim da avaliação)
```

**Não rodei:** `npm run lint` / `npx tsc --noEmit` — a tentativa não toca frontend
(o `package.json` foi alterado na t1, já avaliada). `[—]` justificado.

## 7. Itens da fase / DoD não atendidos

Nenhum, dentro do gate declarado ("AC-18 satisfeito"). Fora dele, dois itens
seguem abertos **por decisão registrada**, e nenhum pertence a esta fase:

- `licenseInfo` não nulo → AC-19 (D.2), pela OQ18.
- `homepageUrl` → passo 3 da fase, sem AC que o cubra; deferido para a E.4 com o
  aval do avaliador da t3. Ver sugestão 1.

## 8. Divergências entre o relatório e o código real

Nenhuma. Conferi cada saída colada no EXECUCAO §5 contra a fonte real e todas
reproduzem, com uma diferença explicada: o relatório registra "148 files already
formatted" e "489 passed", eu obtive 149 e 496 — os arquivos e testes da E.3,
commitados depois. Nada que altere a conclusão.

Registro também, por completude, que o commit `181fb5c` mistura material de três
fases (E.3, D.1 e C.7). A atribuição está clara nos respectivos relatórios e não
prejudicou a auditoria, mas commits por fase teriam feito o `range` de cada uma
significar alguma coisa.

---

**Fase concluída.** APROVADO é o único veredito que fecha a fase (§2.11.3), e este é
o dela: quatro tentativas, três delas gastas com um AC mal modelado, e a última
resolvendo o defeito em vez de contorná-lo. A autorização do owner para esta quarta
tentativa está registrada em decision, como o §2.11.4 exige — não houve override
conversacional de gate.

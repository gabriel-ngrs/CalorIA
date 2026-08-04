---
spec: 002-vitrine-eval-e-saneamento
fase: D.1
slug_fase: licenca-metadados
status: rework
tentativa: 4
reprovacoes: 3
sha_inicial: 7f9f59a
sha_final: PENDENTE
range: 7f9f59a..PENDENTE
---

# FASE D.1 — Relatório de execução

## 0. Esta tentativa existe por autorização explícita do owner, no teto

A fase chegou a `reprovacoes: 3` e o §2.11.4 a levou ao estado terminal de
escalação ao owner. **O owner autorizou a quarta tentativa em 2026-08-04**, e a
decisão está registrada em
`.codeflow/decisions/2026-08-04-quarta-tentativa-da-d1-autorizada-no-teto.md` —
não em autorização falada, que a constitution universal não aceita como saída de
gate duro. A razão da escolha: encerrar por aceite (como se fez na A.1) e fazer o
rework chegam ao mesmo estado de fase, mas só o rework deixa a spec sem
contradizer a si mesma, que é o defeito que o achado nomeia.

**Não há autorização implícita para uma quinta tentativa.**

## 1. Resumo do que foi feito

Rework por um único achado: **D1-IMP-2 — a migração do AC-18 não chegou à §5, e a
spec passou a se contradizer.** O §3, o §8 (OQ18) e o §9 declaravam a cláusula
"licença detectada pela API" migrada para o AC-19 (D.2); a linha `Testes (AC-18)`
da §5 continuava exigindo-a da D.1.

Apliquei a redação que o avaliador deixou pronta e, seguindo a sugestão 1 dele,
**varri a spec inteira** em vez de corrigir só o ponto apontado. A varredura achou
**um segundo ponto** que o achado não citava — e um terceiro, que só apareceu
porque a C.7 rodou na mesma sessão e o falsificou por medição.

Nenhum arquivo de código foi tocado, de novo: o trabalho de código da D.1 está
completo desde a tentativa 1 e segue verificado (§5).

## 2. Arquivos CRIADOS

| Arquivo | Propósito |
|---------|-----------|
| `.codeflow/decisions/2026-08-04-quarta-tentativa-da-d1-autorizada-no-teto.md` | Registro da autorização do owner no teto, cobrindo A.1 (encerramento) e D.1 (4ª tentativa). |

## 3. Arquivos ALTERADOS

| Arquivo | O que mudou |
|---------|-------------|
| `SPEC_002_…md` §5, linha `Testes (AC-18)` | Passa a exigir o que a D.1 controla — description, topics, `LICENSE` versionado, versão sincronizada — com ponteiro para a OQ18. **É o D1-IMP-2.** |
| `SPEC_002_…md` §8, OQ15 | Duas consequências declaradas ali ficaram falsas; retratadas em nota (§4). |
| `.codeflow/decisions/INDEX.md` | Linha da decision nova. |

## 4. Confirmação do REUSO e decisões de design

**REUSADO.** A redação da §5 é a que o avaliador escreveu no achado D1-IMP-2,
verbatim — não reescrevi com palavras minhas o que já estava certo. A forma da
nota de retratação na OQ15 espelha a que a A.1 e a OQ18 já usavam (data, o que
deixou de valer, o que foi medido, ponteiro).

**A varredura achou mais do que o achado apontava.** `grep -rn "licença
detectada\|licenseInfo"` sobre a spec devolveu 8 ocorrências. Seis estavam certas
(a nota do AC-18, a cláusula do AC-19, o texto da OQ18, a linha da D.2 no §9).
Duas não:

1. **OQ15: "a D.1 não fecha até lá, porque `licenseInfo` só é detectado a partir
   do branch default".** Escrita em 2026-08-03, **antes** de a OQ18 do mesmo dia
   migrar a cláusula. É a mesma propagação parcial do D1-IMP-2, num segundo
   lugar. Retratada.
2. **OQ15: "Nada em B.4 ou C.7 depende disto — os dois rodam sobre `dev`".**
   **Factualmente falso para a C.7**, e não por raciocínio: medido nesta sessão,
   ao executar a C.7. O GitHub só registra workflow de `schedule` /
   `workflow_dispatch` a partir do **branch default**, então
   `gh workflow run eval.yml --ref dev` devolve `HTTP 404` mesmo com o arquivo
   presente em `origin/dev`. Retratado, com ponteiro para a OQ20.

O segundo item é o mesmo defeito de modelagem do AC-18, numa terceira fase: um
gate que depende de um efeito que só a D.2 produz. Registro aqui porque a
varredura o encontrou; o tratamento é da C.7.

**Desvios:** nenhum além da própria existência da quarta tentativa (§0). O escopo
travado — não alterar o histórico do CHANGELOG, não trocar a licença MIT — foi
respeitado nas quatro tentativas; nenhum dos dois foi tocado.

## 5. Comandos rodados + saídas reais

```text
# --- AC-18, as quatro cláusulas, contra a API real e a árvore ---
$ gh repo view gabriel-ngrs/CalorIA --json licenseInfo,description,repositoryTopics,homepageUrl,visibility,defaultBranchRef
{"defaultBranchRef":{"name":"main"},
 "description":"Diário alimentar com IA: eval do pipeline de LLM versionado junto do código",
 "homepageUrl":"",
 "licenseInfo":null,
 "repositoryTopics":[fastapi, groq, llm-eval, nextjs, postgresql, python],
 "visibility":"PRIVATE"}
   → description não vazia ✓ · 6 topics ✓
   → licenseInfo null: hoje é cláusula do AC-19 (D.2), não desta fase — OQ18

$ head -3 LICENSE
MIT License

Copyright (c) 2026 Gabriel Negreiros Saraiva          → LICENSE MIT versionado ✓

# --- versão idêntica nos quatro arquivos ---
$ grep -m1 '^version' backend/pyproject.toml   → version = "0.7.0"
$ grep -m1 '"version"' frontend/package.json   → "version": "0.7.0",
$ grep -n 'APP_VERSION = ' backend/app/main.py → 19:APP_VERSION = "0.7.0"
$ grep -n '^## \[' CHANGELOG.md | head -2      → 10:## [Não lançado]
                                                 51:## [0.7.0] - 2026-05-10
   → 0.7.0 nos quatro ✓

# --- a correção desta tentativa, e a varredura que a sugestão 1 pediu ---
$ grep -rn "licença detectada\|licenseInfo" SPEC_002_…md
383       nota do AC-18                      correta
390-391   cláusula do AC-19                  correta
1095      §5 `Testes (AC-18)`                ← D1-IMP-2, CORRIGIDO
1580      OQ15 "a D.1 não fecha até lá"      ← achado NOVO da varredura, RETRATADO
1625,1632 texto da OQ18                      corretas
1694      §9, linha da D.2                   correta

$ sed -n '1095,1098p' SPEC_002_…md      # depois da correção
- **Testes (AC-18):** a API do GitHub reporta description e topics preenchidos; o
  `LICENSE` MIT está versionado na branch de trabalho; a versão é a mesma nos quatro
  arquivos; `make check` verde. (A detecção de licença pela API migrou para o AC-19,
  que é da D.2 — ver OQ18.)

# --- gate estrutural da §5 ---
$ bash ~/.codeflow/framework/core/scripts/run-structural.sh …/SPEC_002_….md
✓ §5 estruturalmente válida                            >>> EXIT=0

# --- `make check`, que a linha `Testes` da fase exige ---
$ docker … "ruff check . && ruff format --check . && mypy app/ evals/"
All checks passed! / 148 files already formatted / Success: no issues found in 81 source files
$ docker … pytest tests/unit -q
489 passed
```

## 6. Critérios de aceite da fase (com evidência)

- [x] **AC-18, description e topics não vazios** — `gh repo view`: description
      preenchida e 6 topics (`fastapi`, `groq`, `llm-eval`, `nextjs`,
      `postgresql`, `python`).
- [x] **AC-18, `LICENSE` (MIT) versionado na branch de trabalho** — `head -3 LICENSE`;
      commitado desde a tentativa 1.
- [x] **AC-18, versão igual em CHANGELOG, `pyproject.toml`, `main.py` e
      `package.json`** — `0.7.0` nos quatro, incluindo o `APP_VERSION` que o
      Swagger publica.
- [x] **§5 `Testes (AC-18)`, `make check` verde** — ruff, ruff format, mypy e
      suíte unitária limpos.
- [—] **`homepageUrl`** — deliberadamente vazio. Está no passo 3 da fase, **não**
      está no AC-18, e apontar para a Vercel órfã (OQ16) publicaria link quebrado
      na vitrine. O avaliador concordou com a espera na tentativa 3 (sugestão 2);
      fecha na E.4.
- [—] **`licenseInfo` não nulo** — migrado para o **AC-19 (D.2)** pela OQ18. Não é
      cláusula desta fase, e a §5 agora diz isso.

## 7. Definition of Done da fase

- [x] Correção do D1-IMP-2 aplicada, com a redação do avaliador
- [x] Varredura da classe inteira feita (sugestão 1), com dois achados extras
- [x] `run-structural.sh` EXIT=0
- [x] `make check` verde
- [x] Escopo travado respeitado: histórico do CHANGELOG intacto, licença segue MIT
- [x] Nenhum código alterado (não havia o que alterar)
- [x] Autorização do owner para a 4ª tentativa registrada em decision (§0)

## 8. O que mudou nesta tentativa

| Achado / sugestão da tentativa 3 | Estado |
|---|---|
| **D1-IMP-2** — §5 exigindo "licença detectada" contra §3/§8/§9 | **Corrigido**, com a redação que o próprio achado propôs |
| Sugestão 1 — varrer a spec inteira, não só o caso | **Aplicada**, e achou dois pontos a mais (§4) |
| Sugestão 2 — `homepageUrl` fica vazio até a E.4 | **Mantida**, agora explícita no §6 como `[—]` justificado |
| Sugestão 3 — a D.2 deve verificar `licenseInfo` no relatório dela | **Repassada**; não é ação desta fase |
| Sugestão 4 — virar regra explícita "executor pode migrar cláusula de AC?" | **Escalada ao owner**, na seção "O que fica pendente" da decision. Não decidi por conta própria: é evolução de processo, e decidir sozinho seria o próprio ato que a pergunta questiona |

## 9. Itens em aberto / dúvidas para o avaliador

1. **A questão de fundo da sugestão 4 continua sem resposta**, e é a única coisa
   nesta fase que não é verificável: um executor pode migrar cláusula de AC entre
   fases quando ela é comprovadamente insatisfazível no escopo declarado? Ocorreu
   duas vezes nesta spec (A.1 e D.1), com argumento técnico sustentado nas duas.
   Registrada na decision como pendência de owner, não resolvida.
2. **Esta é a quarta tentativa de uma fase cujo código não muda desde a
   primeira.** As três reprovações foram todas de artefato — AC mal modelado,
   depois propagação parcial da correção. A.1 e C.7 têm a mesma assinatura. Vale
   o avaliador registrar se enxerga algo no processo que produza esse padrão.
3. **Retratei duas afirmações da OQ15, que é decisão de owner.** Não mudei a
   decisão — a `main` continua intocada até o fim da spec —, só marquei como
   falsas duas consequências que ela declarava, uma delas por medição. Se o
   avaliador entender que mexer no texto de uma OQ de owner é desvio, é achado
   legítimo; fiz porque a alternativa era deixar duas afirmações falsas de pé num
   documento que outras fases leem.

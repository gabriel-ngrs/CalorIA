---
spec: 002-vitrine-eval-e-saneamento
fase: D.1
slug_fase: licenca-metadados
tentativa: 1
veredito: RESSALVAS
score: 9.4
threshold: 8.5
range_avaliado: 7f9f59a..d7346ab
---

# FASE D.1 — Avaliação independente

## 1. Veredito e score

**Veredito:** RESSALVAS · **Score:** 9.4 / threshold 8.5

Tudo que era executável por código foi entregue e verificado: LICENSE MIT,
versão `0.7.0` sincronizada nos quatro arquivos, linha final do README trocada.
O AC-18 depende de metadados do GitHub que só o owner preenche, e o executor o
marca `[ ]` explicitamente — o gate da fase é "AC-18 satisfeito", então ele não
fecha.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 3 | Passos 1 e 2 entregues e verificados (§6). Passo 3 (description/topics/homepage no GitHub) é ação do owner e não ocorreu → AC-18 aberto (D1-IMP-1). Escopo travado respeitado: histórico do CHANGELOG intacto, licença MIT como a OQ4 decidiu. |
| 2 | Arquitetura e direção de dependências | 3 | 5 | Nenhuma mudança estrutural. `main.py:19` centraliza `APP_VERSION` numa constante e a reusa no `FastAPI(version=...)` e no `/health` — antes o número aparecia solto. |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | O `/health` passa a expor a versão (`main.py:96`), o que é padrão e desejável para deploy; nenhum outro dado sensível. `gitleaks` sobre o range: zero achados. |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | A versão tem uma origem por artefato e as quatro coincidem; nenhuma cópia nova foi criada para sincronizá-las. |
| 5 | Padrões de domínio/aplicação | 2 | 5 | LICENSE MIT no formato canônico; CHANGELOG segue Keep a Changelog, como o cabeçalho declara. |
| 6 | Local e nomes dos arquivos | 2 | 5 | `LICENSE` na raiz — é onde o GitHub procura para detectar a licença. |
| 7 | Qualidade de código | 2 | 5 | `ruff`/`mypy`/`tsc` limpos; diff mínimo, sem carona. |
| 8 | Testes e cobertura | 2 | 5 | Fase de metadados: a verificação natural é a suíte inteira continuar verde, e continua (581 passed). Não há comportamento novo a testar. |
| 9 | Migration safety (se aplicável) | 2 | [—] | Nenhuma migration no range (NFR-7). |

Média ponderada das 8 dimensões aplicáveis: 94/20 = 4.7 → **9.4**.

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

**D1-IMP-1 — AC-18 não satisfeito: a API do GitHub não reporta licença detectada,
description nem topics; o gate da fase é exatamente esse AC.**

`SPEC_002...md:1078`: *"Critério de conclusão (gate): AC-18 satisfeito."* E AC-18
exige três coisas da API do GitHub (licença detectada, description e topics não
vazios) mais a versão igual nos quatro arquivos. Só a última está cumprida.

A medição mais recente disponível é a da E.1, feita no mesmo dia:

```text
$ gh repo view ... --json visibility,description,homepageUrl,repositoryTopics,licenseInfo
{"description":"", "homepageUrl":"", "licenseInfo":null, "repositoryTopics":null,
 "visibility":"PRIVATE"}
```

Duas causas distintas, e vale separá-las porque as ações são diferentes:

- **`licenseInfo: null`** — o `LICENSE` existe no working tree e está commitado na
  `dev`. O GitHub detecta licença a partir do **branch default**, que é `main`, e
  `main` está 192 commits atrás. Isso se resolve sozinho com a **D.2** (promover
  `dev` para `main`), não com trabalho novo.
- **`description`, `topics`, `homepage`** — campos do repositório, preenchíveis
  só pelo owner na interface ou por `gh repo edit`. É o passo 3 da fase,
  declarado como ação do owner desde o planejamento.

**Correção sugerida:** o owner rodar, quando o repositório estiver público após a
D.2:

```bash
gh repo edit --description "Diário alimentar com IA: eval do pipeline versionado junto do código" \
             --homepage "<url da demo>" \
             --add-topic fastapi --add-topic nextjs --add-topic llm-eval \
             --add-topic groq --add-topic postgresql --add-topic python
```

e reconferir com `gh repo view --json licenseInfo,description,repositoryTopics`.
Anexar a saída ao EXECUCAO da D.1 e reavaliar. Enquanto a D.2 não sair, a metade
da licença não é satisfazível por esta fase.

## 5. Sugestões

- **A ordem das fases no Track D coloca a D.1 antes da D.2, mas o gate da D.1
  depende do resultado da D.2.** Não é erro grave — os artefatos entram na `dev` e
  aparecem em `main` no merge — mas o gate ficou impossível de fechar na ordem
  declarada. Vale registrar essa dependência em §5 (`D.1 — Depende de: A.2, D.2`
  para a verificação) ou mover a verificação do AC-18 para o gate da D.2.
- `README.md` termina com "MIT — uso livre, com atribuição". O MIT exige
  atribuição, então a frase está correta, mas "uso livre, mantendo o aviso de
  copyright" é mais preciso e evita a leitura de que basta citar o autor.
- A versão `0.7.0` agora está em quatro arquivos e nada impede que voltem a
  divergir. Um teste que compare `pyproject.toml`, `main.py` e `package.json`
  custaria dez linhas e transformaria o AUD-054 em regressão detectável — hoje é
  disciplina.

## 6. Comandos rodados + saídas reais

Ambiente: branch `dev`, HEAD `e3a974a`.
`git merge-base --is-ancestor d7346ab HEAD` → OK.

```text
$ head -3 LICENSE
MIT License

Copyright (c) 2026 Gabriel Negreiros Saraiva

# a versão nos quatro artefatos
$ grep -n '^version' backend/pyproject.toml
7:version = "0.7.0"
$ grep -n "APP_VERSION" backend/app/main.py
19:APP_VERSION = "0.7.0"
44:    version=APP_VERSION,
96:    return {"status": "ok", "version": APP_VERSION}
$ grep -n '"version"' frontend/package.json
3:  "version": "0.7.0",
$ head -8 CHANGELOG.md
# CHANGELOG — CalorIA
[...] Formato baseado em Keep a Changelog. Versões seguem Semantic Versioning.
# (CHANGELOG em 0.7.0 — os quatro coincidem)

$ tail -5 README.md
## Licença
[MIT](LICENSE) — uso livre, com atribuição.
# a linha "Projeto pessoal. Todos os direitos reservados." saiu

# make check, no que o ambiente permite rodar
$ docker compose -f docker-compose.dev.yml exec -T backend ruff check . \
  && ... ruff format --check . && ... mypy app/ evals/
All checks passed! / 147 files already formatted / Success: no issues found in 81 source files
$ ... pytest --cov=app --cov-report=term -q
581 passed, 1 skipped — Total coverage: 73.10% (piso 72%)
$ cd frontend && npx tsc --noEmit   → EXIT=0
$ npm test    → Test Suites: 20 passed | Tests: 114 passed
$ npm run build  → exit 0, sem warnings

$ gitleaks detect --config .gitleaks.toml --log-opts="d8cc463~1..HEAD"
22 commits scanned.  no leaks found

$ git status --short
(limpo)
```

Não consultei a API do GitHub: exigiria credencial de `gh` que não é do avaliador.
A medição da E.1, do mesmo dia e com o comando colado, é a evidência que uso — e
ela é o oposto de auto-favorável, o que a torna confiável.

## 7. Itens da fase / DoD não atendidos

- **AC-18** (§9 do DoD: "D.1 — AC-18") — não atendido nas três cláusulas de
  metadados do GitHub (D1-IMP-1).
- Passo 3 da fase — ação do owner, pendente.
- A sincronização de versão, a licença e o README **estão** atendidos.

## 8. Divergências entre o relatório e o código real

Nenhuma. As quatro afirmações da §6 do EXECUCAO se confirmam arquivo por arquivo,
e o item aberto está marcado com `[ ]` em vez de reescrito para caber no
entregue — a mesma disciplina que aparece nas outras fases desta rodada.

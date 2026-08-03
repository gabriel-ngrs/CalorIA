---
spec: 002-vitrine-eval-e-saneamento
fase: C.1
slug_fase: prompt-registry
tentativa: 1
veredito: APROVADO
score: 9.6
threshold: 8.5
range_avaliado: 704ca3b..8c07142
---

# FASE C.1 — Avaliação independente

## 1. Veredito e score

**Veredito:** APROVADO · **Score:** 9.6 / threshold 8.5

O escopo travado desta fase é o mais fácil de violar sem perceber — "não alterar o
texto dos prompts, é extração pura" — e o mais caro se violado, porque
contaminaria toda a linha de base do eval. **Verifiquei byte a byte**, comparando
os literais inline de `704ca3b` com os cinco arquivos extraídos: idênticos. É a
evidência que sustenta tudo o que o Track C mede depois.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 5 | Extração verbatim comprovada por comparação programática dos 5 templates contra os literais de `704ca3b` (§6). AC-10 nas duas partes: log com `prompt_name`/`prompt_version`/`prompt_sha` (`ai_client.py:262-271`) e `sha` travado por teste. Sem engine de template com lógica — só `str.format` (`prompts/__init__.py:56`). `InsightsGenerator`/`PatternAnalyzer` não versionados, como a fase determina. |
| 2 | Arquitetura e direção de dependências | 3 | 5 | `app/prompts/` não importa nada de `services/`; a dependência corre no sentido certo (`ai_client` → `prompts`). `PromptVersion` é `frozen=True` — identidade imutável por construção, não por convenção. |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | `sha256` é do template **bruto**, não do renderizado (`prompts/__init__.py:63-65` e o docstring de `:1-19`): o contexto do usuário nunca entra no hash nem no log. Isso é o que impede o `prompt_sha` de virar canal lateral de PII. Decisão sutil e correta. |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | Os dois parsers passam a resolver do mesmo registry; os ~90 LOC de literais saíram de cada um (`git show --stat 8c07142`: -161 linhas nos parsers). O `_SHA_SEPARATOR` evita colisão entre system e user template sem inventar formato de serialização. |
| 5 | Padrões de domínio/aplicação | 2 | 5 | Layout `<nome>/v<N>.txt` + `<nome>/v<N>.user.txt` é regular e descoberto por regex única (`_VERSION_FILE`); resolver "versão ativa = maior" é regra explícita, não implícita. |
| 6 | Local e nomes dos arquivos | 2 | 5 | `app/prompts/` ao lado de `app/schemas/` e `app/models/` — conteúdo declarativo do domínio, não serviço. `tests/unit/test_prompt_registry.py` no lugar. |
| 7 | Qualidade de código | 2 | 4 | `mypy` strict limpo, funções curtas, comentários só de "por quê". Desconto: `meal_parser.py`/`vision_parser.py` chamam `get_prompt(...)` **em tempo de import** (`vision_parser.py:25-26`), então um arquivo de prompt ausente vira `ImportError` no boot da aplicação em vez de erro na primeira chamada. Ver §5. |
| 8 | Testes e cobertura | 2 | 5 | 214 linhas de teste cobrindo resolução de versão (implícita, explícita, inexistente), `sha` nas duas direções, os 4 `sha` de produção travados, e o log estruturado capturado do logger real. Os testes existentes dos parsers **não aparecem no diff** — confirmei com `git show --stat 8c07142`, que é o gate do risco R6. |
| 9 | Migration safety (se aplicável) | 2 | [—] | Nenhuma migration no range (NFR-7). |

Média ponderada das 8 dimensões aplicáveis: 96/20 = 4.8 → **9.6**.

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

Nenhum.

## 5. Sugestões

- **Resolução de prompt em tempo de import.** `vision_parser.py:25-26` e o
  equivalente no `meal_parser.py` executam `get_prompt(...)` no nível do módulo.
  Ganha-se validação precoce (um prompt faltando quebra o boot, não o primeiro
  pedido do usuário), perde-se a possibilidade de trocar de versão sem reiniciar
  o processo — e o `lru_cache` de `_cached_prompt` reforça isso. Para o eval
  comparar v1 contra v2 no mesmo processo (que é o caminho recomendado na C.2
  para o JSON mode), vai ser preciso ou invalidar o cache ou resolver por
  chamada. Não é defeito hoje; é a restrição a lembrar quando a comparação
  A/B chegar.
- `PromptRegistry.names()` ignora diretórios que começam com `_`, mas
  `__pycache__` já é filtrado por não ter `v<N>.txt`. A regra do `_` fica sem uso
  aparente — ou documentar o caso que ela previne, ou removê-la.
- O `sha` travado em `SHA_TRAVADO` no teste é a segunda cópia da verdade (a
  primeira é o arquivo). É o desenho certo — é assim que o teste detecta edição
  sem bump — mas vale um comentário no topo do teste dizendo, em uma linha, que
  atualizar esses valores é ato consciente que acompanha bump de versão. Quem
  quebrar o teste na próxima fase vai ler aquele arquivo primeiro.

## 6. Comandos rodados + saídas reais

Ambiente: container `caloria_backend`, branch `dev`, HEAD `e3a974a`.
`git merge-base --is-ancestor 8c07142 HEAD` → OK.

**A verificação que importa nesta fase** — comparação programática entre os
literais inline anteriores (`git show 704ca3b:...`) e os arquivos extraídos:

```text
$ python3  # extrai cada literal do arquivo pré-C.1 e compara com o template
IDENTICO    backend/app/prompts/meal_identify/v1.txt
IDENTICO    backend/app/prompts/meal_identify/v1.user.txt
IDENTICO    backend/app/prompts/meal_fallback/v1.txt
IDENTICO    backend/app/prompts/vision_identify/v1.txt
IDENTICO    backend/app/prompts/vision_fallback/v1.txt
```

Os cinco templates são idênticos ao texto que estava inline. **O escopo travado
mais crítico da fase está cumprido, medido e não argumentado.**

```text
$ git show --stat 8c07142 | grep -c "test_meal_parser\|test_vision_parser"
0     # os testes existentes dos parsers não foram tocados (gate do risco R6)

$ docker compose -f docker-compose.dev.yml exec -T backend pytest --cov=app --cov-report=term -q
581 passed, 1 skipped, 5 warnings in 88.01s
Required test coverage of 72.0% reached. Total coverage: 73.10%

$ ... ruff check . && ... ruff format --check . && ... mypy app/ evals/
All checks passed! / 147 files already formatted / Success: no issues found in 81 source files

# o registry em uso, ponta a ponta (a camada rápida do eval monta o payload real)
$ ... pytest tests/unit/test_evals_snapshot.py -q
15 passed in 0.06s
   → payload["prompt_ref"] == "meal_identify@v1"

$ gitleaks detect --config .gitleaks.toml --log-opts="d8cc463~1..HEAD"
22 commits scanned.  no leaks found

$ git status --short
(limpo)
```

## 7. Itens da fase / DoD não atendidos

Nenhum. O gate declarado — "AC-10 satisfeito; testes existentes dos parsers
passam sem modificação; `mypy app/` limpo" — está satisfeito nas três cláusulas,
cada uma verificada por mim contra o repositório.

## 8. Divergências entre o relatório e o código real

Nenhuma. Verifiquei as cinco afirmações da §6 do EXECUCAO uma a uma; todas se
sustentam. A alegação mais forte do relatório ("extraído sem alterar uma vírgula")
é também a que confirmei com o método mais direto disponível — comparação de
conteúdo, não leitura.

Nota: o relatório cita `mypy app/` com 74 arquivos; hoje o comando é
`mypy app/ evals/` com 81, porque a C.7 estendeu o alvo. Evolução esperada.

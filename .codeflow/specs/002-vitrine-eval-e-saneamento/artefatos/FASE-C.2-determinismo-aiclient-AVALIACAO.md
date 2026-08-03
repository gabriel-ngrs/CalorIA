---
spec: 002-vitrine-eval-e-saneamento
fase: C.2
slug_fase: determinismo-aiclient
tentativa: 1
veredito: RESSALVAS
score: 9.7
threshold: 8.5
range_avaliado: 2d7d5ff..467fee6
---

# FASE C.2 — Avaliação independente

## 1. Veredito e score

**Veredito:** RESSALVAS · **Score:** 9.7 / threshold 8.5

AC-11 está satisfeito nas duas partes e o código é bom. A ressalva é o **passo 2
da fase — JSON mode — que não foi entregue**. A decisão de não entregar é
defensável e está fundamentada; o escopo travado da própria fase manda "parar e
reportar" nesse caso. Mas FR-C2 fica parcial, e quem decide se isso vira fase
própria é o owner, não o executor nem o avaliador. É exatamente o tipo de item
que RESSALVAS devolve.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 4 | Passos 1, 3, 4 e 5 entregues e verificados: modelo na chave de cache (`ai_client.py:294-310`), amostragem em settings (`:34-39`), `RateLimitError` por classe (`:273`), `timeout` explícito (`:51`). Passo 2 não entregue (C2-IMP-1). Escopo travado respeitado: modelo default inalterado, `utils.py` intocado, testes de `test_meal_parser_bug001.py` fora do diff. |
| 2 | Arquitetura e direção de dependências | 3 | 5 | O teto de backoff virou função pura estática (`_espera_do_backoff`), testável sem cliente. A resolução de temperatura idem (`_resolver_temperatura`). Nada vazou para os parsers. |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | O retry deixou de ser `if "429" in str(exc)`, que retentava um HTTP 500 cuja mensagem contivesse "429" — há teste dedicado a esse falso positivo. Teto de tempo declarado (`GROQ_RETRY_MAX_SECONDS`) impede espera indefinida. Cache degrada silenciosamente com Redis fora, comportamento preservado e testado. |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | `_espera_do_backoff` e `_prompt_log_fields` são usados pelos dois caminhos (texto e visão) em vez de duplicados; `_sampling_params()` é a única fonte de `max_tokens`/`seed`. |
| 5 | Padrões de domínio/aplicação | 2 | 5 | Settings em `core/config.py` com nomes que declaram intenção (`GROQ_TEMPERATURE_SEM_SYSTEM` diz o que é e por que existe). `_SEM_SEED = -1` documentado no ponto de uso. |
| 6 | Local e nomes dos arquivos | 2 | 5 | `tests/unit/test_ai_client.py` novo, no lugar; nenhum arquivo movido. |
| 7 | Qualidade de código | 2 | 5 | `mypy` strict limpo. O comentário de `_resolver_temperatura:97-105` é modelo do que a constitution pede: explica **por que** a regra herdada foi preservada (uniformizar mudaria o comportamento dos sete prompts do `InsightsGenerator` e contaminaria a linha de base do eval), não o que o código faz. |
| 8 | Testes e cobertura | 2 | 5 | 235 linhas cobrindo chave de cache por modelo/temperatura/seed/max_tokens, estabilidade da chave (NFR-5), retry por classe, o falso positivo do 500, teto de tempo, timeout explícito e degradação do Redis. |
| 9 | Migration safety (se aplicável) | 2 | [—] | Nenhuma migration no range (NFR-7). |

Média ponderada das 8 dimensões aplicáveis: 97/20 = 4.85 → **9.7**.

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

**C2-IMP-1 — passo 2 da fase (JSON mode) não entregue; FR-C2 fica parcial.**

`SPEC_002...md:839-840` pede:

> Passar `response_format={"type": "json_object"}` nas chamadas cuja saída é JSON
> — o projeto já usa isso em `backend/scripts/enrich_foods.py:101`, então o padrão
> existe.

Confirmei que não foi passado: `ai_client.py:252-257` e `:152-158` montam a
chamada sem `response_format`.

O raciocínio do executor (EXECUCAO §4) é correto e eu o verifiquei: os quatro
prompts declaram `FORMATO OBRIGATÓRIO (array JSON)` e os parsers fazem
`[IdentifiedFood(**item) for item in data]`, esperando `list`. O JSON mode da API
exige objeto no topo. Ligá-lo obrigaria a reescrever o texto dos prompts — o que
a C.1 veda e o que contaminaria a comparação antes/depois que o eval existe para
fazer. O escopo travado da C.2 antecipa exatamente isso: *"Se o JSON mode alterar
a forma da saída de algum prompt, **parar e reportar** em vez de ajustar o
prompt."* O executor parou e reportou.

Então por que IMPORTANTE e não "conforme"? Porque a fase termina com um requisito
funcional da spec (FR-C2) parcialmente atendido e uma decisão pendente que só o
owner toma. Marcar APROVADO fecharia a fase e enterraria o item. RESSALVAS é o
mecanismo correto para devolvê-lo.

**Correção sugerida** — a recomendação do próprio executor é a certa e eu a
endosso: criar `v2` dos quatro prompts com topo em objeto (`{"itens": [...]}`),
ligar o JSON mode junto do bump, e medir v1 contra v2 com o harness — que agora
existe e é exatamente para isso. Duas condições que tornam isso barato hoje e não
eram verdade quando a C.2 rodou: (a) o registry da C.1 suporta as duas versões
coexistindo; (b) a série temporal da C.8 anota automaticamente o commit em que a
versão de prompt muda. Registrar a escolha (fase nova ou aceitar FR-C2 parcial)
em §8 da spec ou numa decision, e reavaliar.

## 5. Sugestões

- **`raise RuntimeError("Groq falhou após 4 tentativas")`** em `ai_client.py:287`
  e `:209` é inalcançável: o laço `range(4)` ou retorna, ou levanta em
  `attempt == 3`. Não é bug — é rede de segurança para o dia em que o laço mudar
  — mas `mypy` não a exige e ela sugere um caminho que não existe. Um comentário
  de uma linha ou a remoção resolveriam.
- **`GROQ_MAX_TOKENS = 8192`** (dúvida 2 do EXECUCAO) foi escolhido por folga, não
  por medição. O eval agora mede: vale extrair `completion_tokens` do log da
  primeira execução completa e ajustar. Ver também C8-IMP-2, que pede tokens no
  histórico — os dois itens se resolvem juntos.
- **`GROQ_TEMPERATURE_SEM_SYSTEM = 0.3`** preserva um acidente histórico, e a
  fase acertou em preservá-lo. Mas o acidente agora tem nome e settings, o que
  significa que ninguém mais vai tropeçar nele por engano — e também que ele pode
  ficar ali para sempre sem que ninguém o questione. Vale um item no Roadmap.

## 6. Comandos rodados + saídas reais

Ambiente: container `caloria_backend`, branch `dev`, HEAD `e3a974a`.
`git merge-base --is-ancestor 467fee6 HEAD` → OK.

```text
# passo 2 — confirmado ausente no código, não presumido pelo relatório
$ grep -n "response_format" backend/app/services/ai/ai_client.py
(sem resultado)
$ grep -n "response_format" backend/scripts/enrich_foods.py
101:            response_format={"type": "json_object"},
# o único ponto do projeto que usa JSON mode devolve objeto de topo — confirma
# por contraste a incompatibilidade descrita no EXECUCAO

# passos 1, 3, 4, 5 — verificados no arquivo
$ grep -n "MODEL\]\|timeout=\|RateLimitError\|_sampling_params\|GROQ_SEED" \
    backend/app/services/ai/ai_client.py
 31:_SEM_SEED = -1
 34:def _sampling_params() -> dict[str, Any]:
 51:    timeout=settings.GROQ_TIMEOUT_SECONDS,
198:except RateLimitError:
273:except RateLimitError:
301:seed = "" if settings.GROQ_SEED == _SEM_SEED else str(settings.GROQ_SEED)
303:f"[MODEL]{model}"      <- o modelo entrou na chave de cache

$ git show --stat 467fee6 | grep -c "test_meal_parser_bug001\|test_vision_parser\|test_extract_json"
0     # escopo travado: testes existentes não modificados

$ docker compose -f docker-compose.dev.yml exec -T backend pytest --cov=app --cov-report=term -q
581 passed, 1 skipped, 5 warnings in 88.01s
Required test coverage of 72.0% reached. Total coverage: 73.10%

$ ... ruff check . && ... ruff format --check . && ... mypy app/ evals/
All checks passed! / 147 files already formatted / Success: no issues found in 81 source files

$ git status --short
(limpo)
```

**Evidência de campo do retry, colhida por acaso pela própria rodada de
correções** (`CORRECOES-2026-08-02-POS-VALIDACAO.md`, seção da pendência): ao
esgotar a quota do free tier, a bateria produziu

```text
Rate limit Groq — aguardando 15s (tentativa 1/4, 0s de 120s do teto já gastos)
Rate limit Groq — aguardando 30s (tentativa 2/4, 15s de 120s do teto já gastos)
Rate limit Groq — aguardando 60s (tentativa 3/4, 45s de 120s do teto já gastos)
```

Backoff de 15→30→60 com o teto de 120s contabilizado e reportado, exatamente como
`_espera_do_backoff` projeta. É a primeira evidência real desta fase em condição
de rate limit, e ela confirma o desenho.

## 7. Itens da fase / DoD não atendidos

- **Passo 2 (JSON mode)** — não entregue (C2-IMP-1). O gate declarado da fase
  ("AC-11 satisfeito; suíte de IA verde sem modificação nos testes existentes")
  **está** satisfeito; o que fica em aberto é o FR-C2 completo.
- Nenhum outro.

## 8. Divergências entre o relatório e o código real

Nenhuma. As afirmações verificáveis do EXECUCAO se confirmam: `response_format`
ausente por decisão declarada, testes existentes fora do diff, chave de cache com
modelo/temperatura/seed/max_tokens, retry por classe de exceção.

O relatório é, aliás, incomum na direção certa: marca o próprio passo não
entregue com `[ ]` em vez de reescrever o gate para caber no que foi feito.

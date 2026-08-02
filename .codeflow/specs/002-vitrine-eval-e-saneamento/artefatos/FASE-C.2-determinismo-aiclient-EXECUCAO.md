---
spec: 002-vitrine-eval-e-saneamento
fase: C.2
slug_fase: determinismo-aiclient
status: executado
tentativa: 1
reprovacoes: 0
sha_inicial: 2d7d5ff
sha_final: 467fee6
range: 2d7d5ff..467fee6
---

# FASE C.2 — Relatório de execução

## 1. Resumo do que foi feito

Quatro dos cinco passos entregues; o passo 2 (JSON mode) foi **deliberadamente não
executado**, exatamente como o escopo travado da fase manda — detalhe em §4.

1. **Chave de cache completa.** Passou a incluir modelo, temperatura, `max_tokens` e
   `seed`, além do texto. Antes era o `sha256` só de system + prompt.
2. **JSON mode — NÃO ativado.** Ver §4, "Passo 2".
3. **Parâmetros de amostragem explícitos** em `settings`: `GROQ_TEMPERATURE`,
   `GROQ_TEMPERATURE_SEM_SYSTEM`, `GROQ_MAX_TOKENS`, `GROQ_SEED`.
4. **Retry por classe de exceção.** `if "429" in str(exc)` deu lugar a
   `except RateLimitError`, com teto de tempo total (`GROQ_RETRY_MAX_SECONDS`).
5. **Timeout explícito** ao instanciar `AsyncGroq`, junto de `max_retries`.

## 2. Arquivos CRIADOS

| Arquivo | Propósito |
|---------|-----------|
| `backend/tests/unit/test_ai_client.py` | 20 testes: chave de cache, amostragem, retry tipado, teto de tempo, timeout, degradação do cache. |

## 3. Arquivos ALTERADOS

| Arquivo | O que mudou |
|---------|-------------|
| `backend/app/core/config.py` | Sete settings novas de amostragem/robustez do provedor. |
| `backend/app/services/ai/ai_client.py` | `_cache_key` com modelo e parâmetros; `_sampling_params()`; `_resolver_temperatura()`; `_espera_do_backoff()`; `except RateLimitError` nos dois caminhos (texto e visão); `timeout`/`max_retries` no construtor. |

## 4. Confirmação do REUSO e decisões de design

**REUSADO:** o cache Redis, o backoff exponencial de 15s dobrando e
`generate_with_image` seguem sendo os mesmos — a fase os *tipou* e os *limitou*, não
os reescreveu. `extract_json_from_ai_response` e o fallback de recorte de
`utils.py:39-42` estão intactos, como o escopo travado exige.

### Passo 2 (JSON mode) — PARADO E REPORTADO, por determinação do escopo travado

O escopo travado da fase diz, literalmente: *"Se o JSON mode alterar a forma da saída
de algum prompt, **parar e reportar** em vez de ajustar o prompt (isso seria mudança
de conteúdo, vedada na C.1 e materialmente relevante para o eval)."* É o caso, e a
evidência está dentro do próprio repositório:

- `response_format={"type": "json_object"}` exige que a resposta seja um **objeto**
  JSON de topo. Não admite array de topo.
- Os quatro prompts de produção declaram, no texto travado por `sha` na C.1,
  `FORMATO OBRIGATÓRIO (array JSON)` e abrem com `[`. Os parsers consomem isso como
  lista: `[IdentifiedFood(**item) for item in data]`
  (`meal_parser.py`, `vision_parser.py`).
- O único ponto do projeto que já usa JSON mode confirma a regra por contraste:
  `backend/scripts/enrich_foods.py:101` liga `response_format` **e** o prompt dele
  devolve um objeto de topo — `{"estimativas": [...]}`, não um array.

Ativar JSON mode nos quatro prompts forçaria o modelo a embrulhar a saída num objeto,
o parser receberia `dict` onde espera `list`, e a correção passaria por **reescrever
o texto do prompt** — vedado na C.1, e o que contaminaria a comparação antes/depois
que o eval existe para fazer. Não foi ativado, e nenhum prompt foi tocado.

**Recomendação para o owner** (não executada aqui, por estar fora do escopo da fase):
criar `v2` dos quatro prompts com formato de topo em objeto (`{"itens": [...]}`) e
ligar JSON mode junto do bump de versão, medindo v1 contra v2 com o próprio harness.
É a forma de obter FR-C2 sem cegar o eval — e o registry da C.1 já suporta as duas
versões coexistindo.

**Demais decisões de design:**
- **Temperatura: regra herdada preservada, agora declarada.** `_resolver_temperatura`
  aceita valor explícito do chamador e, sem ele, cai na regra existente (0.1 com
  system, 0.3 sem). Uniformizar para 0.1 mudaria o comportamento observável dos sete
  prompts do `InsightsGenerator`, que não passam `system=`. Os dois valores viraram
  settings nomeadas, então a escolha deixou de ser acidental mesmo continuando a
  mesma. Está coberto por teste nos dois ramos.
- **`GROQ_SEED = -1` significa "não enviar".** Evita `int | None` em
  pydantic-settings lido de variável de ambiente, e mantém o default idêntico ao de
  hoje (parâmetro ausente).
- **`GROQ_MAX_TOKENS = 8192`.** Teto novo onde não havia nenhum. Escolhido com folga
  larga sobre a maior saída plausível do pipeline (arrays JSON de poucos itens) para
  limitar custo sem risco de truncar. Entra na chave de cache, então mudá-lo invalida
  o cache em vez de misturar respostas de tetos diferentes.
- **Teto do backoff.** `_espera_do_backoff` devolve a espera aparada pelo tempo
  restante, ou `None` quando o teto estourou. O backoff antigo somava 105s sem teto
  declarado, **por cima** das 2 retentativas internas do SDK. `GROQ_SDK_MAX_RETRIES`
  ficou em 2 (o default da lib), agora explícito.
- **Retry restrito a `RateLimitError`.** A heurística antiga retentava qualquer
  exceção cuja `str()` contivesse "429" — inclusive um HTTP 500 cuja mensagem
  mencionasse o número. Há teste dedicado para esse falso positivo.

**Nenhum desvio de escopo:** o modelo default não mudou, os testes de
`test_meal_parser_bug001.py` seguem verdes sem modificação, nenhuma migration foi
tocada.

## 5. Comandos rodados + saídas reais

```text
$ ruff check .
All checks passed!

$ ruff format --check .
126 files already formatted

$ mypy app/
Success: no issues found in 74 source files

$ pytest tests/unit/test_ai_client.py -q
20 passed in 0.40s

$ pytest -q --ignore=tests/smoke_test.py       # unit + integration
359 passed, 5 skipped, 3 warnings in 50.58s
```

Infraestrutura de teste igual à da B.3: Postgres 16.2 e Redis 7 em espaço de usuário
(`pgserver`/`redislite`, instalados só no `.venv`, fora do `pyproject.toml`), porque
não há Docker nesta máquina. `tests/smoke_test.py` continua excluído — sonda de
ambiente de OQ9.

## 6. Checklist dos ACs / critério de conclusão

- [x] **AC-11, parte 1** — dois valores de `GROQ_TEXT_MODEL` geram chaves de cache
      distintas.
      *Evidência:* `TestChaveDeCache::test_modelos_distintos_geram_chaves_distintas`,
      mais três testes irmãos cobrindo temperatura, `seed` e `max_tokens`, e um
      quinto provando a estabilidade da chave para a mesma entrada (NFR-5).
- [x] **AC-11, parte 2** — retry por instância de `RateLimitError`, não por string,
      com teto de tempo declarado.
      *Evidência:* `TestRetryPorClasseDeExcecao` (3 testes, incluindo o 500 com "429"
      no texto que **não** retenta) e `TestTetoDeTempoDoBackoff` (4 testes).
- [x] **Cache degrada silenciosamente com Redis fora** —
      `TestCacheDegradaSilenciosamente::test_redis_fora_do_ar_nao_derruba_a_chamada`
      aponta `REDIS_URL` para uma porta morta e a chamada conclui.
- [x] **Suíte de IA verde sem modificação nos testes existentes** —
      `test_meal_parser.py`, `test_meal_parser_bug001.py`, `test_vision_parser.py`,
      `test_extract_json.py` e `test_ai_endpoint_errors.py` não aparecem no diff
      (`git show --stat 467fee6`).
- [x] **Timeout explícito** — `TestTimeoutExplicito` captura os kwargs passados a
      `AsyncGroq`.
- [ ] **JSON mode ativado** — **NÃO**, por determinação do escopo travado da própria
      fase. Fundamentação e recomendação em §4.

## 7. Dúvidas para o avaliador

1. **O passo 2 é a única lacuna, e é lacuna por desenho.** A fase pode ser aprovada
   com FR-C2 parcialmente atendido (parâmetros explícitos + chave de cache + retry
   tipado, sem JSON mode), ou o JSON mode deve virar fase própria com bump de prompt
   para `v2`? Recomendo a segunda.
2. **`GROQ_MAX_TOKENS = 8192`** é um teto novo onde não havia nenhum. O valor foi
   escolhido por folga, não por medição. Vale medir a maior saída real no primeiro
   eval completo (C.7) e ajustar?
3. **`GROQ_TEMPERATURE_SEM_SYSTEM = 0.3`** preserva o acidente histórico. Depois da
   primeira linha de base do eval, faz sentido uma fase para uniformizar em 0.1 e
   medir o efeito?

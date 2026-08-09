---
spec: 002-vitrine-eval-e-saneamento
fase: C.2
slug_fase: determinismo-aiclient
tentativa: 2
veredito: APROVADO
score: 9.7
threshold: 8.5
range_avaliado: 2d7d5ff..2e6cd1d1d2a7c060d34fda9137c7aa0b25e52a6f
---

# FASE C.2 — Avaliação independente

## 1. Veredito e score

**Veredito:** APROVADO · **Score:** 9.7 / threshold 8.5

**O C2-IMP-1 está fechado, e fechado pelo caminho mais difícil e mais correto dos
dois que a avaliação da tentativa 1 ofereceu.** O JSON mode entrou sem tocar em
prompt existente: quatro versões novas com topo em objeto, `response_format`
amarrado a `PromptVersion.topo_objeto` — nunca a uma flag solta — e produção fixada
nas versões já medidas por `VERSOES_EM_PRODUCAO`. Verifiquei cada peça no código.

Três detalhes de execução que merecem registro, porque são a diferença entre
"implementou" e "implementou sem quebrar o eval":

- **O parâmetro é omitido quando desligado.** `ai_client.py:68` retorna `{}` em vez
  de `response_format: None`. Se enviasse a chave, o payload de toda chamada mudaria
  e os 14 cassettes gravados deixariam de casar. Rodei o runner em replay e os 14
  resolveram: zero `CassetteAusenteError`.
- **O delta das versões novas é verificado byte a byte.**
  `test_prompt_registry.py:295-305` compara tudo que vem antes de `FORMATO` entre a
  versão vigente e a nova. Sem isso, a comparação v1 vs v2 que o eval existe para
  fazer seria ininterpretável.
- **Há um teste que impede a promoção acidental.**
  `test_versao_em_producao_nao_usa_json_mode` (`:281-284`) trava as quatro versões de
  produção como topo-array. Ligar o JSON mode numa delas quebraria a resposta.

O gate formal da fase — *"AC-11 satisfeito; suíte de IA verde sem modificação nos
testes existentes"* — está satisfeito e verificado por mim. `test_meal_parser_bug001.py`
não recebeu nenhum commit no range, que era o escopo travado mais sensível.

**Sobre o que ainda não está em produção.** O passo 2 pede, ao pé da letra, que as
chamadas de produção passem `response_format`, e elas ainda não passam — a promoção
espera uma medição v1 × v2 bloqueada pela quota (risco R5). Isso **não** é achado:
a avaliação da tentativa 1 ofereceu explicitamente, como saída de fechamento,
*"registrar a escolha em §8 da spec ou numa decision, e reavaliar"*, e foi o que se
fez — OQ12 marcada RESOLVIDO com a fundamentação, mais
`decisions/2026-08-03-json-mode-com-versoes-de-prompt-em-objeto.md`. Reabrir o item
agora seria mover a trave depois da bola chutada. Fica como desconto de nota na
dimensão 1, não como IMPORTANTE, e a pendência real está nomeada na §5.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 4 | AC-11 verificado nas duas metades: chave de cache inclui modelo **e** JSON mode (`ai_client.py:354-369`), e o retry captura a **classe** `RateLimitError` (`:240`, `:333`) com teto declarado (`GROQ_RETRY_MAX_SECONDS = 120.0`, `config.py:95`). Escopo travado respeitado: `test_meal_parser_bug001.py` sem nenhum commit no range; fallback de recorte de `utils.py` preservado; modelo default inalterado; e o "parar e reportar se o JSON mode alterar a forma da saída" foi honrado — parou na t1, reportou, e a t2 entregou por versão nova em vez de editar prompt. Desconto: as chamadas de produção ainda não passam `response_format` (§5) |
| 2 | Arquitetura e direção de dependências | 3 | 5 | `response_format` amarrado a `PromptVersion.topo_objeto` (`prompts/__init__.py:73-75`) em vez de flag solta — não existe caminho que ligue JSON mode numa versão que pede array. `VERSOES_EM_PRODUCAO` (`:41`) desacopla "a versão existe" de "a versão está em produção", e `get_prompt` (`:168-175`) resolve por ela em vez de pela maior versão do disco |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | `timeout=settings.GROQ_TIMEOUT_SECONDS` explícito no `AsyncGroq` (`:81`) e teto de tempo no backoff fecham dois caminhos de chamada pendurada. O comentário de `:261-263` registra que o backoff manual somava **sobre** as retentativas internas do SDK — o "por quê" que faltava |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | `response_format` segue a forma já usada em `scripts/enrich_foods.py:101`, que a própria fase cita como precedente. O extrator foi **estendido** (`utils.py:17-29`, `_lista_do_topo`) para aceitar as duas formas, em vez de ganhar um segundo caminho paralelo |
| 5 | Padrões de domínio/aplicação | 2 | 5 | Parâmetros de amostragem migrados para settings (`GROQ_TEMPERATURE`, `_SEM_SYSTEM`, `MAX_TOKENS`, `SEED`, `config.py:78-95`), e a regra herdada dos 0.3 virou `_resolver_temperatura` nomeada em vez de implícita pela presença de `system` |
| 6 | Local e nomes dos arquivos | 2 | 5 | Arquivos declarados na §5 mais os `vN.txt` novos, que são o mecanismo de versionamento que a C.1 criou — não é arquivo fora de escopo, é uso do escopo |
| 7 | Qualidade de código | 2 | 5 | Os comentários registram o *porquê* não-óbvio (timeout implícito da lib; backoff somando sobre o SDK; por que a chave é omitida em vez de `None`), nunca o *o quê* |
| 8 | Testes e cobertura | 2 | 5 | 111 testes verdes no conjunto de IA (§6). O teste do delta é a peça que sustenta a comparabilidade do eval, e o `test_versao_em_producao_nao_usa_json_mode` é uma trava contra o erro mais provável desta mudança |
| 9 | Migration safety | 2 | [—] | Nenhuma migration tocada |

Score = (3·4 + 3·5 + 3·5 + 3·5 + 2·5 + 2·5 + 2·5 + 2·5) / 20 · 2 = 97/20 · 2 = **9.7**

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

Nenhum.

**C2-IMP-1 da tentativa 1 está fechado.** O achado era *"passo 2 (JSON mode) não
entregue; FR-C2 fica parcial"*, e a correção sugerida era literalmente: criar `v2`
dos quatro prompts com topo em objeto, ligar o JSON mode junto do bump, e registrar
a escolha em §8 da spec ou numa decision. As três coisas estão feitas e verificadas
(§6). A medição v1 × v2 que faltaria para promover é o que a própria sugestão
condicionava ao harness, e está bloqueada por quota — registrada na §5, não aqui.

## 5. Sugestões

- **A promoção continua pendente, e é uma linha de diff.** Quando a quota voltar:
  rodar o harness com `VERSOES_EM_PRODUCAO` apontando para as versões novas, comparar
  contra a linha de base (`AGREGADO 10 3.89% [0.00, 6.16] 0.00% 90%`), regravar os
  cassettes, e só então trocar a tabela. O `test_versao_em_producao_nao_usa_json_mode`
  vai reprovar no bump — é o comportamento correto dele; atualizar `_TOPO_OBJETO`
  junto é parte do mesmo commit.
- **A chave de cache mudou de forma para toda chamada** (`[JSON]0` passou a ser
  concatenado mesmo com o JSON mode desligado, `ai_client.py:369`). O efeito é uma
  invalidação única do cache Redis no deploy — benigna, e provavelmente desejável
  junto de uma mudança de amostragem. Registro para não virar susto de "o cache
  esvaziou sozinho".
- **`GROQ_SEED: int = -1` como sentinela de "sem seed"** (`config.py:87`) funciona, mas
  `-1` é valor mágico. `int | None = None` diria a mesma coisa sem convenção implícita.
  Não vale um commit isolado; vale quando alguém encostar no arquivo.

## 6. Comandos rodados + saídas reais

> Gates compartilhados rodados uma vez sobre o HEAD atual (`e4c74b9`), descendente do
> `sha_final` desta fase.

```text
# --- Passo 2: ancestralidade e árvore limpa ---
$ git status --porcelain | wc -l
0
$ git merge-base --is-ancestor 2d7d5ff HEAD                                  → ANCESTRAL
    2d7d5ff docs(specs): registra a execucao da fase c.1
$ git merge-base --is-ancestor 2e6cd1d1d2a7c060d34fda9137c7aa0b25e52a6f HEAD → ANCESTRAL

# --- escopo travado: os testes existentes dos parsers não foram tocados ---
$ git log --oneline 2d7d5ff..HEAD -- backend/tests/unit/test_meal_parser_bug001.py
(vazio — nenhum commit)                                                       ✓

# --- AC-11, metade "chave de cache" ---
$ grep -n "_cache_key" -A16 backend/app/services/ai/ai_client.py | sed -n '1,20p'
354:    def _cache_key(
355:        text: str, *, model: str, temperature: float, json_object: bool = False
369:            f"[JSON]{int(json_object)}"
   → modelo entra na chave; JSON mode também                                  ✓

# --- AC-11, metade "retry por classe, com teto" ---
$ grep -n "RateLimitError\|GROQ_RETRY_MAX_SECONDS" backend/app/services/ai/ai_client.py backend/app/core/config.py
ai_client.py:13:from groq import AsyncGroq, BadRequestError, NotFoundError, RateLimitError
ai_client.py:240:            except RateLimitError:
ai_client.py:333:            except RateLimitError:
config.py:95:    GROQ_RETRY_MAX_SECONDS: float = 120.0
   → captura por classe, não por `"429" in str(exc)`; teto declarado          ✓

# --- passo 2: o parâmetro é OMITIDO quando desligado (não enviado como None) ---
$ sed -n '61,68p' backend/app/services/ai/ai_client.py
def _formato_da_resposta(json_object: bool) -> dict[str, Any]:
    return {"response_format": {"type": "json_object"}} if json_object else {}
   → o payload de produção não se move; os cassettes seguem válidos           ✓

# --- passo 5: timeout explícito ---
$ sed -n '78,81p' backend/app/services/ai/ai_client.py
            # Sem timeout explícito, o default da lib (60s) ficava implícito e
            # declarar sob qual teto foi medida.
            timeout=settings.GROQ_TIMEOUT_SECONDS,                             ✓

# --- amarração versão ↔ JSON mode, e produção fixada ---
$ grep -n "VERSOES_EM_PRODUCAO\|_TOPO_OBJETO\|def topo_objeto\|def get_prompt" backend/app/prompts/__init__.py
41:VERSOES_EM_PRODUCAO: dict[str, int] = {
52:_TOPO_OBJETO: frozenset[tuple[str, int]] = frozenset(
73:    def topo_objeto(self) -> bool:
168:def get_prompt(name: str, version: int | None = None) -> PromptVersion:
175:    alvo = version if version is not None else VERSOES_EM_PRODUCAO.get(name)  ✓

# --- o delta das versões novas, verificado por teste ---
$ sed -n '294,305p' backend/tests/unit/test_prompt_registry.py
    def test_o_delta_da_versao_nova_e_so_o_bloco_de_formato(...):
        antes = registry.get(nome, anterior).system
        depois = registry.get(nome, nova).system
        corte = "FORMATO"
        assert antes[: antes.index(corte)] == depois[: depois.index(corte)]
        assert "array JSON" in antes[antes.index(corte) :]
        assert "array JSON" not in depois[depois.index(corte) :]               ✓

# --- extrator aceita as duas formas de topo ---
$ sed -n '17,29p' backend/app/services/ai/utils.py
def _lista_do_topo(dados: object, bruto: str) -> list[dict[str, object]]:
    """Normaliza as duas formas de topo aceitas: array e objeto com `itens`."""
    ... isinstance(dados, list) ... isinstance(dados, dict) ... dados.get("itens")  ✓

# --- gate: suíte de IA verde ---
$ docker exec caloria_backend pytest tests/unit/test_ai_client.py \
    tests/unit/test_prompt_registry.py tests/unit/test_meal_parser_bug001.py \
    tests/unit/test_extract_json.py tests/unit/test_meal_parser.py \
    tests/unit/test_vision_parser.py -q
111 passed in 0.58s                                                            ✓

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
| Passo 1 — modelo na chave de cache | Atendido (`ai_client.py:354-369`) |
| Passo 2 — JSON mode nas chamadas com saída JSON | **Atendido como capacidade**, não como comportamento de produção. Registrado e aprovado pelo owner na OQ12 (RESOLVIDO) + decision; a promoção espera medição v1 × v2 (risco R5). Ver §5 |
| Passo 3 — amostragem explícita em settings | Atendido (`config.py:78-95`; `_resolver_temperatura` nomeia a regra dos 0.3) |
| Passo 4 — retry por classe com teto | Atendido (`RateLimitError`, `GROQ_RETRY_MAX_SECONDS`) |
| Passo 5 — timeout explícito no `AsyncGroq` | Atendido (`ai_client.py:81`) |
| AC-11 | Atendido, verificado nas duas metades |
| Gate — suíte de IA verde sem modificar testes existentes | Atendido (111 passed; zero commits em `test_meal_parser_bug001.py` no range) |
| Gate — `mypy app/` limpo | Atendido (`mypy app/ evals/` → 81 arquivos, sem erro) |

## 8. Divergências entre o relatório e o código real

1. **Nenhuma divergência.** Conferi cada afirmação do bloco "Tentativa 2" contra o
   código: as quatro versões novas existem, o delta é só o bloco FORMATO (e há teste
   que o prova), `VERSOES_EM_PRODUCAO` fixa `meal_identify@v1`, `meal_fallback@v1`,
   `vision_identify@v2`, `vision_fallback@v1`, e o `response_format` é omitido quando
   desligado.

2. **O relatório é honesto quanto ao que não fez.** A seção "Por que não promover as
   versões novas agora" declara o trade-off sem enfeitar, e a OQ12 registra o mesmo na
   spec. É o oposto do padrão de relatório que declara concluído o que ficou pela
   metade.

3. **Nota de leitura, não divergência:** o relatório cita cobertura de 73,86% e eu medi
   74,28%. As fases posteriores acrescentaram testes; o piso (72%) é o mesmo.

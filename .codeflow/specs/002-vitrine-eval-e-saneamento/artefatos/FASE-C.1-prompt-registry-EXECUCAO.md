---
spec: 002-vitrine-eval-e-saneamento
fase: C.1
slug_fase: prompt-registry
status: executado
tentativa: 1
reprovacoes: 0
sha_inicial: 704ca3b
sha_final: 8c07142
range: 704ca3b..8c07142
---

# FASE C.1 — Relatório de execução

## 1. Resumo do que foi feito

Os quatro prompts de produção do pipeline de IA saíram de literais de módulo para
arquivos versionados em `backend/app/prompts/<nome>/v<N>.txt`, com `sha256` do texto
bruto travado por teste. `AIClient` passou a aceitar a versão de prompt usada e a
registrá-la no log estruturado, ao lado do log de tokens que já existia.

**A extração é byte-idêntica.** Foi verificada mecanicamente contra o HEAD anterior
(§5) — nenhum caractere de prompt mudou. Os testes existentes dos parsers
(`test_meal_parser.py`, `test_meal_parser_bug001.py`, `test_vision_parser.py`) passam
**sem uma linha de modificação**, que é o gate do risco R6 da spec.

## 2. Arquivos CRIADOS

| Arquivo | Propósito |
|---------|-----------|
| `backend/app/prompts/__init__.py` | `PromptRegistry`, `PromptVersion`, `get_prompt`, `PromptNotFoundError`. |
| `backend/app/prompts/meal_identify/v1.txt` + `v1.user.txt` | Estágio 1 do `MealParser` (system + template de user message). |
| `backend/app/prompts/meal_fallback/v1.txt` | Estágio 3 do `MealParser`. |
| `backend/app/prompts/vision_identify/v1.txt` + `v1.user.txt` | Estágio 1 do `VisionParser`. |
| `backend/app/prompts/vision_fallback/v1.txt` | Estágio 2 do `VisionParser`. |
| `backend/tests/unit/test_prompt_registry.py` | 27 testes: resolução de versão, `sha` travado, render, identidade no log. |

## 3. Arquivos ALTERADOS

| Arquivo | O que mudou |
|---------|-------------|
| `backend/app/services/ai/meal_parser.py` | Literais removidos; `_IDENTIFY_PROMPT`/`_FALLBACK_PROMPT` vêm do registry; `render()` no lugar de `.format()`; `prompt_ref` nas chamadas. |
| `backend/app/services/ai/vision_parser.py` | Idem para os prompts de visão. |
| `backend/app/services/ai/ai_client.py` | `prompt_ref: PromptVersion \| None` em `generate_text` e `generate_with_image`; log com `prompt_name`, `prompt_version`, `prompt_sha`, `model` e tokens. |
| `.pre-commit-config.yaml` | `exclude: ^backend/app/prompts/` em `trailing-whitespace` e `end-of-file-fixer` (ver desvio 2). |

## 4. Confirmação do REUSO e decisões de design

**REUSADO:**
- A injeção de `AIClient` por construtor nos parsers, citada na spec como seam
  existente — nenhuma assinatura pública de parser mudou.
- O log de tokens de `ai_client.py:157-161`, que a spec mandava usar como ponto de
  ancoragem: a identidade de prompt entrou **na mesma linha**, não numa linha nova.
- `extract_json_from_ai_response` segue intacto como rede de segurança.

**Decisões de design:**
- **Layout `v<N>.txt` + `v<N>.user.txt`.** A spec declarava um arquivo por prompt.
  Os prompts de identificação, porém, têm duas partes (system e template de user
  message) e a spec diz que "os templates de user message acompanham". Um arquivo
  `.user.txt` opcional ao lado mantém a versão como unidade única, sem inventar um
  segundo namespace de nomes.
- **`sha256` cobre as duas partes.** É o `sha` do `system` concatenado ao
  `user_template` com um separador `\x00` que nunca vai ao provedor. Mudar só a user
  message move o `sha` — comprovado por teste. Se o `sha` fosse só do system, uma
  mudança no template escaparia do gate.
- **`sha` do texto bruto, não do renderizado.** O renderizado varia por usuário
  (`user_context`) e não serviria de identidade estável — é o que a spec pedia.
- **`prompt_ref` é opcional e só informa o log.** Não altera nada do que é enviado
  ao provedor. Os prompts do `InsightsGenerator` e do `PatternAnalyzer` continuam
  inline, como o escopo travado exige.
- **Resolução de versão.** `get_prompt(nome)` devolve a maior versão; `get_prompt`
  com versão explícita permite ao eval fixar uma versão antiga para comparação.
  Substituição de variáveis por `str.format`, sem engine de template com lógica.

**Desvios da spec, com justificativa:**

1. **Nomes de arquivo `v1.user.txt`** além dos `v1.txt` declarados — ver decisão de
   layout acima.
2. **`.pre-commit-config.yaml` alterado** (arquivo da fase A.3, já concluída).
   Obrigatório, e a alternativa era pior: `end-of-file-fixer` normaliza o fim do
   arquivo para exatamente um `\n`, e `vision_identify/v1.txt` **termina** em `\n`
   por construção. Sem a exclusão, o hook apararia esse newline, mudando o prompt
   enviado à Groq sem que ninguém tivesse editado prompt algum — e quebrando o `sha`
   travado. A exclusão é escopada a `^backend/app/prompts/` e **não afrouxa nenhum
   gate de segurança**: `gitleaks`, `ruff`, `check-yaml` e `no-commit-to-branch`
   seguem rodando sobre tudo. Verificado após o commit: os seis arquivos de prompt
   não foram reescritos pelos hooks e os 27 testes de `sha` continuam verdes.
3. **Log estruturado como texto formatado, não JSON.** O projeto loga com
   `logging.basicConfig` e formato texto (`main.py:14-18`). Introduzir um formatter
   JSON seria mudança de infraestrutura de logging fora do escopo desta fase; os
   campos `prompt_name=`, `prompt_version=`, `prompt_sha=` são parseáveis por
   `key=value`, que é o que o AC-10 exige verificar.

**Escopo travado respeitado:** nenhum texto de prompt foi alterado (verificação
mecânica em §5); nenhum engine de template com lógica foi introduzido; os prompts do
`InsightsGenerator` e do `PatternAnalyzer` não foram versionados.

## 5. Comandos rodados + saídas reais

```text
$ ruff check .
All checks passed!

$ ruff format --check .
125 files already formatted

$ mypy app/
Success: no issues found in 74 source files

$ pytest tests/unit/test_prompt_registry.py -q
27 passed in 0.19s

$ pytest -q --ignore=tests/smoke_test.py      # unit + integration
339 passed, 5 skipped, 3 warnings in 48.95s
```

**Verificação de extração byte-idêntica** — compara cada arquivo novo com o literal
Python do commit anterior, extraído por `ast.literal_eval` (não por leitura visual):

```text
OK  meal_identify/v1.txt        sha=20e3b2709529482d
OK  meal_identify/v1.user.txt   sha=2653f6217de4c905
OK  meal_fallback/v1.txt        sha=713ea1c529306cc1
OK  vision_identify/v1.txt      sha=98abe714aeec1268
OK  vision_identify/v1.user.txt sha=61003d3b73e70400
OK  vision_fallback/v1.txt      sha=7c206344f4f87a7a

EXTRACAO BYTE-IDENTICA: True
```

**Verificação de empacotamento** — os `.txt` precisam existir na imagem de produção,
que instala por `pip install .` (wheel), não em modo editável:

```text
$ pip wheel --no-deps -w /tmp/wheel .
Successfully built caloria-backend
$ # conteúdo do wheel, filtrado por "prompts"
app/prompts/__init__.py
app/prompts/meal_fallback/v1.txt
app/prompts/meal_identify/v1.txt
app/prompts/meal_identify/v1.user.txt
app/prompts/vision_fallback/v1.txt
app/prompts/vision_identify/v1.txt
app/prompts/vision_identify/v1.user.txt
```

## 6. Checklist dos ACs / critério de conclusão

- [x] **AC-10, parte 1** — o log traz `prompt_name`, `prompt_version` e `prompt_sha`.
      *Evidência:* `TestIdentidadeNoLogDoAIClient::test_log_traz_nome_versao_e_sha`
      captura a linha real do logger `app.services.ai.ai_client` e casa os três
      campos; `test_sem_prompt_ref_o_log_nao_quebra` cobre o caminho sem identidade.
- [x] **AC-10, parte 2** — conteúdo alterado sem bump de versão muda o `sha` e um
      teste detecta.
      *Evidência:* `TestShaDoTemplate` (duas direções: system e user template) e
      `TestPromptsDeProducao::test_sha_da_versao_ativa_esta_travado`, que compara
      contra os quatro `sha` fixados em `SHA_TRAVADO`.
- [x] **Testes existentes dos parsers passam sem modificação** —
      `test_meal_parser.py`, `test_meal_parser_bug001.py` e `test_vision_parser.py`
      não aparecem no diff desta fase (`git show --stat 8c07142`). Gate do risco R6.
- [x] **`mypy app/` limpo** — `Success: no issues found in 74 source files`.
- [x] **Registry resolve nome e versão** — `TestResolucaoDeVersao`, 6 testes,
      incluindo versão implícita (a maior), explícita, e erro para nome/versão
      inexistentes.

## 7. Dúvidas para o avaliador

1. **`sha256` combinando system + user template** numa única identidade por versão:
   preferível a dois `sha` separados no registro do eval (C.8)? A escolha atual dá
   um único número por versão, mais simples de amarrar à métrica.
2. **Exclusão de `app/prompts/` nos hooks de whitespace** (desvio 2) toca um arquivo
   da A.3, já aprovada. Está registrada aqui; vale também uma decision do framework?
3. Os prompts do `InsightsGenerator` (sete) e do `PatternAnalyzer` seguem inline por
   determinação do escopo travado. Fase futura ou fora da spec?

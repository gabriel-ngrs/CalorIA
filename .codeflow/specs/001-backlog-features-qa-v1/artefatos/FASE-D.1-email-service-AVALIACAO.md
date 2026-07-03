---
spec: 001-backlog-features-qa-v1
fase: D.1
slug_fase: email-service
tentativa: 1
veredito: APROVADO
score: 9.7
threshold: 8.5
range_avaliado: ad968ce2308ddab17a788ebc1423a0216cc4136d..da8d40e2e8104e06bdc9066e268d227b491c146e
---

# FASE D.1 — Avaliação independente

## 1. Veredito e score

**Veredito:** APROVADO · **Score:** 9.7 / threshold 8.5

`EmailService` SMTP com fallback console entregue conforme FR-D1. Sem AC próprio
(é infra para D.2). Verificado contra o código real: lint/format/mypy limpos, os 3
testes unitários passam.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 5 | FR-D1 ok; `.env.example:56-64` só placeholders vazios; deps/vars nos arquivos declarados (`config.py`, `.env.example`, `pyproject.toml`) |
| 2 | Arquitetura e direção de dependências | 3 | 5 | `email_service.py:12` service stateless sem `db` (desvio justificado — não toca banco); usa `settings` |
| 3 | Segurança / LGPD / multi-tenant | 3 | 4 | Sem segredo commitado; fallback loga o **html completo** em INFO (`email_service.py:20-27`) — em D.2 isso inclui o link de reset em dev |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | Reusa `settings` + `logging.getLogger(__name__)`, padrão do backend |
| 5 | Padrões de domínio/aplicação | 2 | 5 | TLS derivado da porta (587 start_tls / 465 use_tls); anotações completas |
| 6 | Local e nomes dos arquivos | 2 | 5 | `app/services/email_service.py` + `tests/unit/test_email_service.py` — corretos |
| 7 | Qualidade de código | 2 | 5 | Docstring de "por quê"; tipos; `EmailMessage` com alternativa text/html |
| 8 | Testes e cobertura | 2 | 5 | 3 testes: sem-SMTP não envia, sem-SMTP loga, com-SMTP envia via aiosmtplib |
| 9 | Migration safety (se aplicável) | 2 | — | Não se aplica (sem schema) |

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

Nenhum.

## 5. Sugestões

- `email_service.py:20-27` — no fallback console, logar apenas destinatário/assunto
  (não o `html` inteiro) evita que o link de reset apareça em logs de dev
  compartilhados. Não-bloqueante (só dispara sem SMTP, cenário dev).
- `config.py:72` / `RESET_TOKEN_EXPIRE_MINUTES` — o default 60 satisfaz NFR-3 (≤1h),
  mas não há teto; um valor >60 em produção violaria o NFR silenciosamente. Consumido
  em D.2. Considerar clamp ou validação.

## 6. Comandos rodados + saídas reais

```text
$ docker exec caloria_backend ruff check app/services/email_service.py app/core/config.py tests/unit/test_email_service.py
All checks passed!

$ docker exec caloria_backend ruff format --check <arquivos da fase>
8 files already formatted   # (rodado junto com D.2)

$ docker exec caloria_backend mypy app/services/email_service.py app/core/config.py
Success: no issues found  # (rodado no lote D.1+D.2: 8 source files)

$ docker exec -e TEST_DATABASE_URL=...@postgres:5432/caloria_test caloria_backend \
    pytest tests/unit/test_email_service.py -q
3 passed, 3 errors in 1.00s
# Os 3 "errors" são teardown do fixture autouse clean_db (TRUNCATE) — o caloria_test
# não tem tabelas em run single-file. CONFIRMADO ambiental: o intocado
# tests/unit/test_security.py exibe o mesmo padrão (14 passed, 14 errors). Os 3
# testes da fase PASSAM.

$ git diff <range> | grep -iE "secret=|api_key=|BEGIN.*PRIVATE"
# nenhum segredo (SMTP_PASSWORD= é placeholder vazio)
```

## 7. Itens da fase / DoD não atendidos

Nenhum. FR-D1 e o critério de conclusão da fase (testes verdes; sem SMTP não quebra)
atendidos.

## 8. Divergências entre o relatório e o código real

Nenhuma divergência material. O relatório declarou honestamente: (a) o desvio de deps
instaladas à mão no container (`pyproject.toml` registra `aiosmtplib>=3.0.0`,
confirmado); (b) `FRONTEND_URL`/`RESET_TOKEN_EXPIRE_MINUTES` adicionadas aqui e usadas
em D.2 — ambas dentro de `config.py`/`.env.example`, arquivos declarados da fase;
(c) os "errors" de teardown como ruído ambiental — verificado independentemente.

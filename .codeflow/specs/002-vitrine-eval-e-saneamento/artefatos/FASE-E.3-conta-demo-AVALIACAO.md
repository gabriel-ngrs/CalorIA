---
spec: 002-vitrine-eval-e-saneamento
fase: E.3
slug_fase: conta-demo
tentativa: 1
veredito: APROVADO
score: 9.6
threshold: 8.5
range_avaliado: 181fb5c..181fb5c
---

# FASE E.3 — Avaliação independente

## 1. Veredito e score

**Veredito:** APROVADO · **Score:** 9.6 / threshold 8.5 — zero BLOQUEANTES, zero
IMPORTANTES.

**Verifiquei o AC-26 empiricamente, contra o stack local, sem acreditar no
relatório.** Fiz login com as credenciais publicadas no README e consultei os
quatro domínios; rodei o seed uma segunda vez e recontei as linhas no banco; e
tentei acessar dado de outro usuário com o token da demo. Os três resultados estão
colados na §6. Login devolve token, os quatro domínios trazem dados dos últimos 30
dias, o reseed devolve contagens **idênticas** (113 refeições, 385 itens, 15 pesos,
136 hidratações, 27 humores, 1 usuário — antes e depois), e a refeição de outro
usuário responde `HTTP 404`.

**O escopo travado nomeia três violações BLOQUEANTES e nenhuma ocorreu.** A senha é
sintética e não coincide com nenhuma outra conta declarada; o e-mail é de domínio
próprio (`demo@caloria.app`), não caixa de ninguém; e o isolamento é estrutural — a
API deriva `user_id` do token, e eu medi o 404.

**A colisão com a A.3 foi resolvida do jeito certo.** Uma senha em texto claro é
exatamente o que a regra `caloria-senha-hardcoded` existe para pegar, e a saída não
foi desligar a regra nem isentar um caminho: foi isenção **nominal por valor**, ao
lado de `Playwright@123` e `NovaSenha123`, com decision escrita explicando por que
esta senha específica não é o que a regra persegue. `gitleaks` sobre 496 commits
segue limpo.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 5 | AC-26 verificado por mim: login real + 4 domínios + idempotência + isolamento (§6). Os quatro passos da §5 entregues, incl. política de reset no README:120-131 |
| 2 | Arquitetura e direção de dependências | 3 | 5 | Mudança confinada a `backend/scripts/`; `app/` não foi tocado. O script importa `app.core.security.hash_password` em vez de reimplementar o hash — direção correta |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | Senha sintética (`seed_dev_user.py:63`), isenção nominal (`.gitleaks.toml:51-63`), sem privilégio (não há coluna de papel em `User`), isolamento medido → `HTTP 404` (§6). SQL sempre parametrizado (`:email`, `:hash`) |
| 4 | Reusar/espelhar, não duplicar | 3 | 5 | O gerador de 30 dias não mudou uma linha; a demo entra como parâmetro do mesmo caminho (`CONTAS`, `resolver_conta`). Nenhum script paralelo |
| 5 | Padrões de domínio/aplicação | 2 | 4 | `Conta` como dataclass frozen + tabela `CONTAS` é limpo; desconto por `assert` como invariante de produção do script (`:1085`) e pelo `INSERT` cru, que ignora defaults do ORM se o modelo ganhar coluna obrigatória |
| 6 | Local e nomes dos arquivos | 2 | 5 | Teste em `backend/tests/unit/test_seed_demo.py`; decision indexada; seção 6 do README, na sequência do setup |
| 7 | Qualidade de código | 2 | 4 | `ruff`/`ruff format`/`mypy` limpos; docstrings explicam o "por quê". Descontos: `get_user_id()` (`:1066`) virou código morto, e `make seed-demo` só serve ao compose de dev (§5) |
| 8 | Testes e cobertura | 2 | 5 | 10 testes que travam justamente o que o escopo travado proíbe; os 3 que dependem do README pulam **no container** e rodam no CI, com o motivo escrito no `skipif` — honestidade melhor que um guard que passa por engano |
| 9 | Migration safety (se aplicável) | 2 | [—] | Nenhuma migration; a conta entra por `INSERT`, não por schema (NFR-7 preservada) |

Score = 96 / 20 × 2 = **9.6**.

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

Nenhum.

## 5. Sugestões

1. **`get_user_id()` (`backend/scripts/seed_dev_user.py:1066`) virou código morto.**
   `resolver_conta()` a substituiu no `main()` e nenhum outro ponto do repositório a
   chama (`grep -rn "get_user_id" backend/ --include=*.py` só acha a definição e o
   homônimo do pytest). Remover é diff de 6 linhas e evita que alguém a use achando
   que é o caminho vigente.
2. **`make seed-demo` chama `$(COMPOSE_DEV) exec backend`** (`Makefile:233`), ou
   seja, só funciona com o compose de desenvolvimento. O README apresenta o alvo
   como *o* comando de reset da demo, e a demo publicada vai rodar pelo
   `docker-compose.yml` (ADR-009). Quando a E.4 publicar, ou o alvo ganha uma
   variante de produção, ou o README precisa dizer para qual ambiente ele vale.
3. **`assert conta.senha is not None` (`:1085`)** desaparece sob `python -O`. Num
   script de seed o risco é baixo, mas um `raise ValueError` custa o mesmo e não
   depende do modo do interpretador.
4. **O `INSERT` lista quatro colunas** (`:1097-1100`). Funciona hoje; se `users`
   ganhar coluna `NOT NULL` sem default de servidor, o seed da demo quebra e só na
   execução. O teste `test_a_demo_nao_tem_privilegio` já usa `User.__table__` para
   vigiar campo de papel — o mesmo truque serviria para vigiar colunas obrigatórias
   novas.
5. **Para a E.4, quando a demo for exposta de verdade:** credenciais públicas dão a
   qualquer visitante acesso aos endpoints de IA, que gastam quota da Groq. O rate
   limiting da B.3 (AC-8 e a decision de 2026-08-02) cobre o caso, e o TPD medido
   pela C.7 é 100.000 — vale conferir na E.4 se os limites por janela bastam para
   que um visitante não consuma a cota do dia do eval. Não é achado desta fase: aqui
   a conta é local.
6. **Política de reset.** "A cada deploy e sob demanda, manual até a E.4" é uma
   política, e está escrita — atende o passo 2. Quando houver agendador, vale virar
   uma tarefa Celery Beat como as outras seis, em vez de um cron fora do stack.

## 6. Comandos rodados + saídas reais

```text
$ git merge-base --is-ancestor 181fb5c HEAD && echo "181fb5c ANCESTRAL OK"
181fb5c ANCESTRAL OK

# --- AC-26, passo a passo, contra o stack local ---
$ curl -s -X POST http://localhost:8010/api/v1/auth/login \
    -H 'Content-Type: application/json' \
    -d '{"email":"demo@caloria.app","password":"CalorIADemo2026!"}'
{"access_token":"eyJ…","refresh_token":"eyJ…","token_type":"bearer"}
   → sub = 109; as credenciais do README funcionam como publicadas

$ curl -H "Authorization: Bearer $T" .../api/v1/meals?limit=3
[{"id":595,"user_id":109,"meal_type":"snack","date":"2026-08-04",…,"items":[{"food_name":"Banana",…}]
$ curl … /api/v1/weight?limit=3
[{"id":263,"user_id":109,"weight_kg":81.3,"date":"2026-08-04"},…]
$ curl … /api/v1/hydration/today
{"date":"2026-08-04","total_ml":1650,"entries":[…]}
$ curl … /api/v1/mood?limit=3
[{"id":121,"user_id":109,"energy_level":5,"mood_level":5,…},…]
   → os quatro domínios do AC-26 com dados reais

# --- idempotência: "rodar o seed duas vezes não duplica dados" ---
$ psql -tAc "select (select count(*) from meals where user_id=109),
             (select count(*) from meal_items … ), (select count(*) from weight_logs …),
             (select count(*) from hydration_logs …), (select count(*) from mood_logs …),
             (select count(*) from users where email='demo@caloria.app')"
113|385|15|136|27|1                     ← ANTES

$ docker compose -f docker-compose.dev.yml exec -T backend \
    python scripts/seed_dev_user.py --conta demo
  Conta já existia — senha e nome reaplicados (id=109).
  Limpando dados existentes do usuário 109...
  ✓ Dados inseridos com sucesso!   Dias com refeições: 30   Registros de peso: 15

$ psql -tAc "…mesma consulta…"
113|385|15|136|27|1                     ← DEPOIS: idêntico, e o mesmo user_id

# --- escopo travado: "não dar à demo acesso a dado de outro usuário" ---
$ psql -tAc "select id from meals where user_id <> 109 limit 1"   → 3
$ curl -o /dev/null -w "HTTP %{http_code}\n" -H "Authorization: Bearer $T" \
    http://localhost:8010/api/v1/meals/3
HTTP 404                                ← isolamento confirmado

# --- gates do projeto ---
$ docker compose -f docker-compose.dev.yml exec -T backend sh -c \
    "ruff check . && ruff format --check . && mypy app/ evals/"
All checks passed! / 149 files already formatted / Success: no issues found in 81 source files

$ docker compose -f docker-compose.dev.yml exec -T backend pytest tests/unit -q
496 passed, 3 skipped in 4.01s
   → os 3 skips são os de coerência README×script, que o container não alcança;
     `RAIZ.parent/README.md` existe no checkout do CI, então lá eles rodam

$ docker compose -f docker-compose.dev.yml exec -T backend pytest tests/integration/ -q
145 passed, 5 warnings in 86.98s

$ gitleaks detect --source . --config .gitleaks.toml --redact --no-banner --exit-code 1
496 commits scanned. no leaks found     >>> EXIT=0
   → com `CalorIADemo2026!` já no README, no script e no .gitleaks.toml

$ grep -rn "gabrielnegreirossaraiva\|senha pessoal" README.md backend/scripts/seed_dev_user.py
(sem saída — nenhuma credencial pessoal do owner nos arquivos da fase)

$ grep -rn "get_user_id" backend/ --include=*.py | grep -v .venv
backend/scripts/seed_dev_user.py:1066:def get_user_id(...)   ← só a definição (sugestão 1)

$ git status --short
(vazio — árvore limpa ao fim da avaliação)
```

**Não rodei:** `npm run lint` / `npx tsc --noEmit` — a fase não toca frontend
(`git show 181fb5c --stat`: script, testes, README, Makefile, `.gitleaks.toml`,
decisions, e os artefatos de eval da C.7). `[—]` justificado.

## 7. Itens da fase / DoD não atendidos

| Item (§5 / §9) | Estado |
|---|---|
| Passo 1 — seed idempotente da conta de demonstração | ✓ medido (§6) |
| Passo 2 — política de reset periódico definida | ✓ `README.md:126-131`, com a limitação (manual até a E.4) declarada |
| Passo 3 — credenciais publicadas no README, sem coincidir com credencial real | ✓ `README.md:113-117`; decision de 2026-08-04 |
| Passo 4 — sem privilégio administrativo | ✓ não há coluna de papel em `User`; teste vigia a introdução de uma |
| Testes — login exibe os quatro domínios; seed duas vezes não duplica | ✓ ambos verificados por mim |
| AC-26 / gate da fase | ✓ |

Nada em aberto.

## 8. Divergências entre o relatório e o código real

Nenhuma. Cada afirmação verificável do EXECUCAO reproduziu aqui, inclusive o
`id=109` e a contagem de dados. Duas observações de forma, sem efeito no veredito:

1. **O commit `181fb5c` carrega três fases.** Além da E.3, ele traz os 56 cassettes
   e a linha do `history.jsonl` da C.7, as edições de spec da D.1 e as duas
   decisions. O `range` desta fase (`181fb5c..181fb5c`) portanto não a isola. A
   atribuição está clara nos relatórios de cada fase e não prejudicou a auditoria,
   mas commits por fase teriam feito o range significar alguma coisa.
2. **O EXECUCAO diz "10 testes"** em `test_seed_demo.py`; a contagem real é 10
   funções de teste, das quais uma é parametrizada em 2 — 11 casos coletados. Sem
   consequência.

---

**Fase concluída.** APROVADO é o único veredito que fecha uma fase (§2.11.3), e a
E.3 o merece na primeira tentativa: gate verificado empiricamente, escopo travado
respeitado em cada uma das três proibições, e a colisão com a A.3 resolvida por
decision em vez de por exceção silenciosa. A E.4 herda as sugestões 2 e 5.

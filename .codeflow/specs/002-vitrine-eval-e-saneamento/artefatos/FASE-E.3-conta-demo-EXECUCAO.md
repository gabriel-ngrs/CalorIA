---
spec: 002-vitrine-eval-e-saneamento
fase: E.3
slug_fase: conta-demo
status: executado
tentativa: 1
reprovacoes: 0
sha_inicial: 181fb5c
sha_final: 181fb5c
range: 181fb5c..181fb5c
---

# FASE E.3 — Relatório de execução

## 1. Resumo do que foi feito

Nova execução. O `seed_dev_user.py` deixou de ser "o seed do usuário de dev" e
passou a receber a **conta como parâmetro**: `dev` (default, comportamento
idêntico ao de sempre) e `demo`, que o script **cria se não existir**. As
credenciais da demo estão publicadas no README, que é o que o AC-26 exige, e
`make seed-demo` é ao mesmo tempo o comando de seed e o de reset.

Verifiquei tudo empiricamente contra o stack local — seed rodado duas vezes,
login real pela API, os quatro domínios consultados, e a tentativa de acessar
dado de outro usuário.

## 2. Arquivos CRIADOS

| Arquivo | Propósito |
|---------|-----------|
| `backend/tests/unit/test_seed_demo.py` | 10 testes: identidade da conta, senha sintética e não reusada, e-mail fora de provedor de consumo, ausência de privilégio, e coerência README × script. |
| `.codeflow/decisions/2026-08-04-conta-demo-senha-publica-e-isencao-no-gitleaks.md` | Por que uma senha em texto claro é correta aqui, e por que a isenção é nominal. |

## 3. Arquivos ALTERADOS

| Arquivo | O que mudou |
|---------|-------------|
| `backend/scripts/seed_dev_user.py` | `Conta` (dataclass) + tabela `CONTAS`; `resolver_conta()` cria a demo se faltar e reaplica senha/nome se já existir; `--conta {dev,demo}`. O gerador de 30 dias não mudou uma linha. |
| `README.md` | Seção "6. Conta de demonstração": comando, credenciais, o que elas abrem e não abrem, e a política de reset. |
| `Makefile` | Alvo `seed-demo` (+ `.PHONY`), documentado como comando de reset. |
| `.gitleaks.toml` | Isenção nominal de `CalorIADemo2026!` na regra `caloria-senha-hardcoded`. |

## 4. Confirmação do REUSO e decisões de design

**REUSADO, e é quase tudo.** O cardápio brasileiro, o gerador de 30 dias de
refeições/peso/hidratação/humor, a semente fixa `random.Random(42)`, o
`clear_existing_data` e o `update_user_profile` são os que já existiam — não
reimplementei nada disso. O hash da senha vem de `app.core.security.hash_password`,
o mesmo do cadastro real, não de um `bcrypt` paralelo. A forma da isenção no
`.gitleaks.toml` copia a que a A.3 estabeleceu para `Playwright@123`.

**Decisões de design:**

- **Idempotência sai de graça do que já existia.** `clear_existing_data` apaga
  antes de gravar e a semente é fixa: rodar duas vezes no mesmo dia deixa o banco
  idêntico. O que faltava era só a criação do usuário. Por isso `resolver_conta`
  é `UPDATE`-se-existe: rodar de novo devolve o mesmo `id` e reaplica a senha
  publicada, em vez de estourar no índice único de e-mail.
- **O reset é o próprio seed.** A fase pede "política de reset periódico". Um
  comando idempotente que devolve a conta ao estado publicado **é** o reset;
  criar um segundo caminho para apagar dados seria superfície a mais para o mesmo
  efeito.
- **`demo@caloria.app`, não um e-mail de provedor.** Domínio próprio não é caixa
  de ninguém e não dispara a regra `caloria-email-pessoal` — o oposto do
  `devteste@gmail.com`, que precisou de isenção.
- **A senha vai em texto claro, e a isenção é nominal.** Ela é pública por
  desenho (AC-26). O caminho alternativo — escrever a atribuição de modo a não
  casar o regex do gitleaks — passaria pelo gate sem decidir nada, que é o que o
  escopo travado da A.3 proíbe. Ver a decision.

**DESVIO — dois arquivos fora dos "Arquivos alterados" da fase:**
`.gitleaks.toml` (sem a isenção a fase não commita) e
`backend/tests/unit/test_seed_demo.py` (arquivo novo). Registrado na decision.

**Escopo travado, item a item:** nenhuma senha do owner reusada (teste dedicado);
nenhuma PII semeada (cardápio fictício, e-mail de domínio próprio); nenhum acesso
a dado de outro usuário (§5.4, medido).

## 5. Comandos rodados + saídas reais

### 5.1 Primeira execução — a conta nasce

```text
$ docker compose -f docker-compose.dev.yml exec -T backend \
    python scripts/seed_dev_user.py --conta demo
  CalorIA — Seed de dados para Conta Demo
→ Resolvendo usuário demo@caloria.app...
  Conta criada (id=109).
  user_id=109
✓ Dados inseridos com sucesso!
  Dias com refeições:  30
  Registros de peso:   15
  Peso inicial: 84.5 kg  →  final: ~81.3 kg
```

### 5.2 Segunda execução — idempotência (o teste que a fase pede)

```text
# contagem no banco APÓS a 1a rodada
$ psql -c "select u.id, count(distinct m.id), count(distinct w.id),
           count(distinct h.id), count(distinct mo.id) from users u
           left join meals m … where u.email='demo@caloria.app' group by u.id"
109|113|15|136|27        (id | meals | weight | hydration | mood)

$ docker … python scripts/seed_dev_user.py --conta demo
  Conta já existia — senha e nome reaplicados (id=109).
  Dias com refeições:  30
  Registros de peso:   15

# contagem APÓS a 2a rodada
109|113|15|136|27        ← IDÊNTICA. Mesmo `id`, zero duplicação.
```

### 5.3 AC-26 — login com as credenciais publicadas, e os quatro domínios

```text
$ curl -s -X POST http://localhost:8010/api/v1/auth/login \
    -H 'Content-Type: application/json' \
    -d '{"email":"demo@caloria.app","password":"<a senha publicada no README>"}'
LOGIN OK (access_token de 143 chars)

$ curl -H "Authorization: Bearer $TOK" .../api/v1/dashboard/today
{"date":"2026-08-04","nutrition":{"total_calories":1537.0,"total_protein":61.8,
 "total_carbs":246.0,"total_fat":37.7,"total_fiber":31.0,"meals_count":4,…}}   ← REFEIÇÕES

$ … /api/v1/dashboard/weight-chart
[{"id":263,"user_id":109,"weight_kg":81.3,"date":"2026-08-04"},
 {"id":262,"user_id":109,"weight_kg":81.7,"date":"2026-08-02"},…]              ← PESO

$ … /api/v1/hydration/today
{"date":"2026-08-04","total_ml":1650,"entries":[…]}                            ← HIDRATAÇÃO
$ … /api/v1/hydration/history
[{"date":"2026-07-29","total_ml":1200,"entries":[…]},…]

$ … /api/v1/mood
27 registro(s)                                                                  ← HUMOR

$ … /api/v1/dashboard/weekly
{"start_date":"2026-07-29","end_date":"2026-08-04","avg_calories":1568.7,
 "avg_protein":83.9,"total_days_logged":7,…}
   → os quatro domínios do AC-26 com dado real, pelos endpoints que o dashboard usa.
```

### 5.4 Escopo travado — sem privilégio, sem dado alheio

```text
# a demo não vê nem apaga refeição de outro usuário
$ ALHEIA=$(psql -c "select id from meals where user_id <> 109 order by id desc limit 1")
refeicao de outro usuario: id=368
GET    /api/v1/meals/368  →  404
DELETE /api/v1/meals/368  →  404      ← isolamento por user_id do token, não por obscuridade

# não há privilégio a conceder: o modelo não tem campo de papel
$ grep -nE "is_admin|role|is_superuser|is_staff" backend/app/models/user.py
(sem saída)                            ← travado por test_a_demo_nao_tem_privilegio
```

### 5.5 Gates do projeto

```text
$ docker … "ruff check . && ruff format --check . && mypy app/ evals/"
All checks passed! / 149 files already formatted / Success: no issues found in 81 source files

$ docker … pytest tests/unit -q
496 passed, 3 skipped in 3.94s
$ docker … pytest tests/unit/test_seed_demo.py -q
7 passed, 3 skipped in 0.09s
   → os 3 skips são a classe `TestCredenciaisPublicadas`: o container monta só
     `backend/`, então o README da raiz não existe lá dentro. Skip explícito com
     motivo, em vez de teste verde no CI e vermelho local.

# a checagem que os 3 skips fariam, rodada à mão sobre a árvore real:
$ python3 -c "… compara script × README …"
email do script : demo@caloria.app     | no README: True
senha do script : (len 16)             | no README: True
make seed-demo no README: True

$ gitleaks detect --source . --config .gitleaks.toml --redact --no-banner --exit-code 1
493 commits scanned. no leaks found    >>> EXIT=0
   → a senha publicada passa pela isenção nominal, e nada mais entrou junto.
```

## 6. Critérios de aceite da fase (com evidência)

- [x] **AC-26, login com as credenciais do README exibe dados nos quatro
      domínios** — §5.3: token emitido, e refeições, peso, hidratação e humor com
      dado real pelos endpoints do dashboard.
- [x] **AC-26, rodar o seed duas vezes não duplica dados** — §5.2: `113|15|136|27`
      antes e depois, mesmo `user_id`.
- [x] **Passo 1, seed adaptado e idempotente** — `--conta demo`, cria se faltar.
- [x] **Passo 2, política de reset definida** — `make seed-demo` é o reset;
      documentado no README com a ressalva de que a **automação** depende da E.4.
- [x] **Passo 3, credenciais publicadas no README** — seção 6, com o que elas
      abrem e não abrem.
- [x] **Passo 4, sem privilégio administrativo** — §5.4, travado por teste.

## 7. Definition of Done da fase

- [x] AC-26 satisfeito nas duas cláusulas, com saída real
- [x] Escopo travado respeitado nos três itens (senha do owner, PII, dado alheio)
- [x] `ruff`, `ruff format`, `mypy`, 496 testes unitários, gitleaks — limpos
- [x] Dois desvios de arquivo declarados, com decision
- [—] `make test-integration` **não rodado**: exige o banco `caloria_test`, que
      precisa ser criado à mão neste ambiente. A fase não toca endpoint, service
      nem model — só um script de `scripts/` e três arquivos de projeto —, e a
      verificação equivalente foi feita **contra a API real** em §5.3/§5.4, que é
      evidência mais forte que o teste de integração daria
- [x] Commit em pt-BR, sem menção a autor/IA

## 8. Itens em aberto / dúvidas para o avaliador

1. **O reset periódico está definido, mas não automatizado.** A fase pede
   "política de reset periódico"; entreguei o comando idempotente e a política
   escrita, e declarei no README que a automação depende do deploy da E.4 —
   que hoje roda local (ADR-009) e não tem agendador em pé. Um `beat` do Celery
   resolveria, mas `app/workers/` não está nos arquivos da fase e a conta demo
   nem existe num ambiente publicado ainda. **É suficiente, ou o avaliador
   entende que a fase deve entregar a tarefa agendada?**
2. **O AC-26 diz "faz login na demo", e não existe demo publicada.** A OQ16 pôs o
   deploy em host único rodando **local**, e a E.4 está adiada por decisão. Li
   "a demo" como o stack da topologia decidida — que é o que roda — e verifiquei
   contra ele. Se o avaliador entender que o AC exige ambiente publicado, então a
   E.3 depende da E.4, e a §5 declara o contrário (`E.4` depende de `E.3`). Nesse
   caso é mais um caso da mesma classe da OQ18/OQ20, e vale registrar.
3. **`demo@caloria.app` é um domínio que o projeto não controla.** Escolhi por
   ser inequivocamente sintético e por não disparar a regra de PII. Se o owner
   registrar um domínio de verdade para a demo, vale trocar — o teste de coerência
   README × script pega o esquecimento.
4. **A senha publicada abre uma conta com rate limiting comum** (o da B.3, por
   IP). Se a demo for pública de fato, um visitante pode gastar quota de IA em
   nome da conta. A B.3 já registrou o débito de a chave de contagem ser por IP e
   não por `user_id`; a demo torna isso mais concreto.

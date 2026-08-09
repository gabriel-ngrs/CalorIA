---
data: 2026-08-04
titulo: A senha da conta de demonstração é pública por desenho, e isenta nominalmente no gitleaks
status: ativa
tags: [seguranca, gitleaks, demo, vitrine, spec-002, fase-e3, fase-a3]
---

# A senha da conta de demonstração é pública por desenho, e isenta nominalmente no gitleaks

## Contexto

O AC-26 da Fase E.3 exige que as credenciais da conta de demonstração estejam
**no README**, para que um avaliador entre na demo sem pedir acesso a ninguém. O
passo 3 da fase é explícito: *"Elas são públicas por desenho"*.

Isso colide de frente com a Fase A.3, que fez o oposto: o `.gitleaks.toml` ganhou
a regra `caloria-senha-hardcoded` justamente para que uma senha em texto claro
atribuída a uma constante **falhe o commit e o CI**. A regra funciona — e acusa
`SENHA_DEMO = "CalorIADemo2026!"` em `backend/scripts/seed_dev_user.py`.

As duas coisas estão certas. O que falta é dizer, de forma auditável, por que
esta senha específica não é o que a regra existe para pegar.

## Decisão

**Manter a senha em texto claro no script e no README, e isentá-la nominalmente**
na allowlist da regra `caloria-senha-hardcoded`, ao lado de `Playwright@123` e
`NovaSenha123` — que é a forma que a A.3 já estabeleceu: isenção por valor, nunca
por caminho, nunca por regra inteira, sempre com justificativa escrita.

O que sustenta a isenção, e é verificável:

| Condição | Verificação |
|---|---|
| Abre **só** a conta demo | `demo@caloria.app` existe apenas no banco do projeto, criada por `seed_dev_user.py --conta demo` |
| Não reusa credencial de ninguém | Teste `test_a_senha_da_demo_nao_e_reusada_em_nenhuma_outra_conta`; é a violação BLOQUEANTE que o escopo travado da E.3 nomeia, e o incidente que criou o Track A |
| Dados sintéticos, sem PII | O gerador é o mesmo cardápio fictício do seed de dev; o e-mail é de domínio próprio, não de provedor de consumo (teste dedicado) |
| Sem privilégio administrativo | O modelo `User` não tem `is_admin`/`role`/`is_superuser` — teste trava a ausência, para que um campo novo não dê privilégio à demo por default em silêncio |
| Sem acesso a dado alheio | Medido: com o token da demo, `GET` e `DELETE` de refeição de outro usuário devolvem **404** |

## Alternativas rejeitadas

1. **Senha só por variável de ambiente, sem default no código.** Quebraria o
   AC-26 (as credenciais têm de estar publicadas) ou exigiria publicá-la só no
   README — e aí o README e o comportamento real do seed poderiam divergir sem
   nada acusar. A forma atual tem teste travando a igualdade entre os dois.
2. **Escrever a atribuição de modo a não casar o regex** (ex.: embutir o literal
   dentro de `os.getenv(...)`, onde não há `=` seguido de aspas). Passaria pelo
   gate sem isentar nada — que é contornar o scanner, não decidir. O escopo
   travado da A.3 proíbe exatamente isso.
3. **Isentar o arquivo inteiro por `paths`.** Deixaria qualquer senha futura
   entrar em `seed_dev_user.py` sem ninguém ver. A isenção nominal falha de novo
   assim que o valor mudar, que é o comportamento desejado.

## Escopo: dois arquivos fora do declarado

Os "Arquivos alterados" da E.3 são `backend/scripts/seed_dev_user.py`,
`README.md` e `Makefile`. Entraram também:

- **`.gitleaks.toml`** — a isenção acima. Sem ela a fase não commita.
- **`backend/tests/unit/test_seed_demo.py`** — arquivo novo. A fase declara testes
  ("login exibe dashboard", "rodar o seed duas vezes não duplica") que são
  empíricos e estão no relatório com saída real; estes travam o que é declaração:
  identidade da conta, ausência de privilégio, e a coerência README × script.

Registrado aqui pelo item final do §9 do DoD.

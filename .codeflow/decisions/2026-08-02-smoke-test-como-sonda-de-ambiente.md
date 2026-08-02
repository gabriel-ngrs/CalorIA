---
data: 2026-08-02
titulo: smoke_test.py declarado sonda de ambiente e pulado sem credencial real
status: ativa
tags: [ci-cd, testes, seguranca, spec-002, fase-b2]
spec: 002-vitrine-eval-e-saneamento
fase: B.2
---

# `smoke_test.py` declarado sonda de ambiente, com skip por pré-condição

## Contexto

A Fase B.2 da spec 002 declarava `Arquivos alterados: .github/workflows/ci.yml,
.github/workflows/cd.yml, Makefile, README.md` — quatro arquivos de configuração,
nenhum de teste. O risco **R3** da mesma spec já antecipava o que aconteceu:
"reativar o CI expõe falhas latentes".

Com os gatilhos restaurados, **3 testes falharam**, todos em
`backend/tests/smoke_test.py`. A inspeção mostrou que o arquivo não é um teste:

- ele chama a **API real da Groq** (texto e visão) e gasta cota do provedor;
- ele tem `DB_URL = "postgresql://caloria:caloria@localhost:5432/caloria_db"`
  **hardcoded** — `caloria_db` é o banco de **desenvolvimento**, populado por seed,
  não o `caloria_test` que a suíte usa;
- ele imprime um relatório colorido com `✓`/`✗` em vez de asserir.

E ainda assim mora dentro de `backend/tests/`, coletado por `pytest` como qualquer
outro. **Nunca poderia passar no CI**: o workflow define
`GROQ_API_KEY: fake-key-for-tests` de propósito, justamente para não gastar cota, e
o runner não tem o banco de desenvolvimento.

Isso põe a fase num dilema real. O escopo travado da B.2 diz "não relaxar nenhum
gate para fazer o CI passar — `ruff` e `mypy` já passam limpos hoje, então uma falha
indica regressão real e deve ser corrigida, não silenciada". Mas estas falhas **não
são regressão**: são a suíte relatando corretamente que as pré-condições de uma
sonda de ambiente não existem no ambiente de CI. Tratá-las como defeito de código
confundiria "ambiente sem credencial" com "código quebrado".

A extensão de escopo foi reportada ao owner e autorizada antes da execução.

## Decisão

**Declarar o módulo como sonda de ambiente e pulá-lo quando a pré-condição não
existe** — sem tocar em nenhum gate do CI.

1. **Docstring do módulo** reescrita para declarar o que ele é: "uma **sonda de
   ambiente**, não um teste de unidade (…) Fora desse ambiente as pré-condições não
   existem, e o módulo se declara `skipped` em vez de falhar — o gate continua duro
   para todo o resto da suíte".

2. **Skip de módulo por credencial real**, com a condição escrita como pré-condição
   verificável e não como "no CI":

       _CHAVE_REAL = bool(GROQ_KEY) and GROQ_KEY.startswith("gsk_")
       pytestmark = pytest.mark.skipif(not _CHAVE_REAL, reason=...)

   Chaves da Groq começam com `gsk_`; a fake do CI (`fake-key-for-tests`) não. O
   teste continua rodando de verdade em qualquer máquina com `.env` preenchido.

3. **Skip do teste de banco por catálogo ausente**, na conexão:

       except (asyncpg.InvalidCatalogNameError, OSError) as exc:
           pytest.skip(f"banco de desenvolvimento indisponível: {exc}")

   Ausência do catálogo `caloria_db` é ambiente indisponível, não defeito.

**Nenhum gate foi afrouxado.** Nenhum `continue-on-error` foi adicionado a step de
lint, typecheck ou teste; `ruff`, `mypy`, `pytest` e `npm run lint` continuam
bloqueantes; nenhum teste real virou `skip`; nenhum `--maxfail`, `-k` ou `--ignore`
entrou no comando do CI. As três falhas somem porque a condição delas é honesta e
declarada, não porque a barra desceu.

## Alternativas descartadas

- **Corrigir os 3 testes para passarem no CI.** É o que o escopo travado pede
  literalmente ("uma falha indica regressão real e deve ser corrigida"). Rejeitado
  porque não existe correção: fazer o teste de Groq passar no CI exige colocar uma
  chave real do provedor num runner do GitHub e **gastar cota do free tier a cada
  push**; fazer o teste de banco passar exige semear as ~42 mil linhas de `foods` no
  CI, o que multiplica o tempo de build para validar dado de seed que nenhum código
  de produção consome no caminho testado. O escopo travado supõe que a falha é
  regressão — aqui a premissa não vale, e é isso que faz disto uma decision e não
  uma correção de rotina.

- **Excluir `smoke_test.py` da coleta do pytest** (`--ignore`, `norecursedirs` ou
  `collect_ignore`). Rejeitado por ser silenciamento sem declaração: o arquivo
  continuaria parecendo um teste, deixaria de rodar **em toda parte** — inclusive na
  máquina de dev, onde ele tem valor real — e a próxima pessoa a ler `tests/` não
  teria como saber por quê. O skip por pré-condição preserva o valor em dev e explica
  a ausência no CI, no `reason` que o próprio pytest imprime.

- **Mover o arquivo para fora de `tests/`** (`backend/scripts/smoke_check.py`).
  Tecnicamente é a resposta certa e continua registrada como débito. Rejeitado
  **nesta fase** por escopo: mover o arquivo é mudança estrutural com impacto em
  `Makefile`, documentação e no hábito de uso do owner, dentro de uma fase cujo
  objetivo é reativar gatilhos de CI. Fazer as duas coisas juntas misturaria a
  correção do CI com uma reorganização, e tornaria mais difícil auditar se algum
  gate foi afrouxado — que é justamente a pergunta que a avaliação desta fase faz.

- **`pytest.mark.skipif(os.environ.get("CI") == "true")`.** Rejeitado por ser skip
  pela **plataforma**, não pela **pré-condição**. A condição correta não é "estou no
  CI", é "não tenho chave real / não tenho o banco de dev" — que também vale para o
  desenvolvedor com `.env` vazio, e que continua valendo se o projeto trocar de
  provedor de CI.

## Consequência

- O CI da B.2 fica verde por motivo verdadeiro: a suíte automatizada não depende de
  credencial de provedor externo nem do banco de desenvolvimento.
- A sonda continua útil onde foi feita para ser útil — em dev, com `.env`
  preenchido, ela roda inteira e valida Groq texto, Groq visão e o banco de
  alimentos.
- O `reason` do skip é autoexplicativo na saída do pytest, então "3 skipped" no CI
  não vira ruído indecifrável.
- **Débito aberto:** mover a sonda para fora da árvore de testes
  (`backend/scripts/`). Enquanto ela morar em `tests/`, um leitor razoável vai
  continuar lendo "3 testes pulados" como cobertura perdida, quando não é.
- **Risco residual:** a condição `GROQ_API_KEY.startswith("gsk_")` acopla o skip ao
  formato de chave do provedor atual. Se a Groq mudar o prefixo, a sonda passa a ser
  pulada silenciosamente **também em dev** — falha para o lado seguro (não quebra o
  CI), mas de forma invisível. Mitigação: o prefixo está documentado em comentário no
  ponto exato onde é verificado.
- **Risco residual:** um teste de verdade escrito neste arquivo no futuro herda o
  `pytestmark` de módulo e nunca rodará no CI. Mitigado pela docstring, que declara o
  arquivo como sonda e não como suíte, e pelo débito de movê-lo.

## Reprodução

    # em dev, com .env preenchido: roda de verdade
    cd backend && pytest tests/smoke_test.py -v

    # simulando o CI: 3 skipped, 0 failed
    cd backend && GROQ_API_KEY=fake-key-for-tests pytest tests/smoke_test.py -v

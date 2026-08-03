---
spec: 002-vitrine-eval-e-saneamento
fase: E.1
slug_fase: auditoria-deploy
tentativa: 1
veredito: APROVADO
score: 9.6
threshold: 8.5
range_avaliado: b31604d..b31604d
---

# FASE E.1 — Avaliação independente

## 1. Veredito e score

**Veredito:** APROVADO · **Score:** 9.6 / threshold 8.5

Fase de levantamento, e o levantamento fez o que levantamento tem de fazer:
**refutou a premissa**. A documentação descreve um backend self-hosted em
`caloria-gabriel.duckdns.org`; o host não resolve em DNS. Isso não é "estado
indeterminado" — é inexistente, e a conclusão reordena o Track E inteiro.

Cada afirmação do relatório vem com o comando e a saída que a sustenta, que é
exatamente o AC-24. Nada em produção foi tocado, e nenhum segredo aparece.

## 2. Scorecard

| # | Dimensão | Peso | Nota (0–5) | Evidência (arquivo:linha ou saída) |
|---|----------|------|------------|------------------------------------|
| 1 | Conformidade com a fase — ACs e escopo travado | 3 | 5 | AC-24 satisfeito: §2 a §4 do EXECUCAO trazem `curl`, `getent`, `gh repo view`, `gh run list` e `git rev-list` com a saída colada. Escopo travado respeitado nas três cláusulas: só `GET`/`HEAD` (nada alterado em produção), nenhum segredo no relatório, e `docs/deploy.md` tratado como hipótese e refutado — não como verdade. |
| 2 | Arquitetura e direção de dependências | 3 | [—] | Fase sem código: `sha_inicial == sha_final`, e o único artefato é o relatório. Nada a avaliar aqui, e o relatório declara isso na primeira linha. |
| 3 | Segurança / LGPD / multi-tenant | 3 | 5 | Nenhuma variável de produção, token ou credencial no texto. A URL da Vercel exposta é pública por natureza. `gitleaks` sobre o range: zero achados. Registrar que o frontend público aponta para uma API inexistente é, em si, achado de segurança operacional. |
| 4 | Reusar/espelhar, não duplicar | 3 | [—] | Não aplicável — levantamento. |
| 5 | Padrões de domínio/aplicação | 2 | [—] | Não aplicável. |
| 6 | Local e nomes dos arquivos | 2 | 5 | `artefatos/FASE-E.1-auditoria-deploy-EXECUCAO.md`, com `fase`/`slug_fase` no padrão do pipeline. |
| 7 | Qualidade de código | 2 | 4 | Aplicado à qualidade do artefato: estrutura clara, evidência antes da conclusão, divergências numeradas numa tabela. Desconto pequeno: a linha 8 da tabela de §5 está separada por uma linha em branco e quebra a renderização do markdown em dois blocos. |
| 8 | Testes e cobertura | 2 | [—] | Não aplicável — não há comportamento novo. A suíte do projeto continua verde (§6). |
| 9 | Migration safety (se aplicável) | 2 | [—] | Não aplicável. |

Média ponderada das 4 dimensões aplicáveis (pesos 3+3+2+2 = 10): 48/10 = 4.8 → **9.6**.

## 3. Achados BLOQUEANTES

Nenhum.

## 4. Achados IMPORTANTES

Nenhum.

## 5. Sugestões

- **A divergência 7 é o achado mais valioso e está enterrada no fim da tabela.**
  A observação de que `Caddyfile.backend` só faz proxy de `/api/*`, `/docs*`,
  `/redoc*`, `/openapi.json` e `/health` significa que a topologia real
  pretendida — frontend na Vercel, backend self-hosted atrás do Caddy — **já está
  codificada nos arquivos de orquestração**, e só a documentação diverge. Isso dá
  à E.2 material para decidir sem inventar, que é precisamente o que a E.2 pede.
  Vale promover essa conclusão para o resumo da fase, e não deixá-la como nota de
  rodapé.
- **Reordenação do Track E** (dúvidas 1 e 2): concordo com as duas leituras. A
  E.4 deixa de ser "refazer o deploy" e passa a ser "fazer o primeiro deploy
  real", e a E.3 (conta de demonstração) fica na prática bloqueada pela E.4,
  embora a spec ordene o contrário. As duas coisas exigem edição da §5 e registro
  em §8 — não é ajuste que o executor da E.2 deva fazer de passagem.
- **Frontend público apontando para API inexistente** (dúvida 3): há um risco que
  o relatório não nomeia. O repositório está privado, mas a aplicação está no ar
  e qualquer pessoa com o link vê uma tela de login que falha em toda tentativa.
  Isso é pior que estar fora do ar, porque parece produto quebrado em vez de
  produto não publicado. Despublicar ou pôr uma página de manutenção até a E.4
  custa pouco e protege exatamente o que esta spec quer proteger — a impressão de
  quem avalia o projeto.
- **`scripts/seed_all.py` quebrado** (divergência 8 e dúvida 4): já foi corrigido
  na rodada de 2026-08-02, junto de mais duas quebras na mesma cadeia
  (`psycopg2` ausente, coluna `age` → `birth_date`). Vale atualizar a divergência
  8 do relatório com um "corrigido em" e o ponteiro, para que a tabela não fique
  descrevendo um defeito que não existe mais — é o tipo de coisa que confunde
  quem ler a E.2 daqui a um mês.

## 6. Comandos rodados + saídas reais

Ambiente: branch `dev`, HEAD `e3a974a`. O range da fase é degenerado
(`b31604d..b31604d`), porque não há commit de código — coerente com uma fase de
levantamento, e declarado como tal na primeira linha do EXECUCAO.
`git merge-base --is-ancestor b31604d HEAD` → OK.

```text
# o range de fato não contém código
$ git diff --stat b31604d..b31604d
(vazio)

# nada em produção foi alterado por esta fase (só GET/HEAD, verificável no
# próprio relatório) e nada no repositório
$ git status --short
(limpo)

# o estado do projeto ao redor da fase continua íntegro
$ docker compose -f docker-compose.dev.yml exec -T backend pytest --cov=app --cov-report=term -q
581 passed, 1 skipped, 5 warnings in 88.01s
Required test coverage of 72.0% reached. Total coverage: 73.10%

$ ... ruff check . && ... ruff format --check . && ... mypy app/ evals/
All checks passed! / 147 files already formatted / Success: no issues found in 81 source files

$ gitleaks detect --config .gitleaks.toml --log-opts="d8cc463~1..HEAD"
22 commits scanned.  no leaks found          # NFR-4: nenhum segredo no relatório
```

**Não reexecutei as sondas de rede do relatório** (`curl` na Vercel, `getent` no
duckdns, `gh repo view`): as duas primeiras dependem de saída de rede que esta
sessão não tem garantida, e a terceira exige credencial de `gh` que não é do
avaliador. O que pesa a favor de aceitar as medições sem repeti-las é o conteúdo
delas: um relatório complacente não conclui "o backend não existe" nem
"`licenseInfo: null`". Cada saída colada é desfavorável a quem a colou, e três
delas (repositório privado, CI ativo e verde, `main` 192 commits atrás) são
verificáveis por outros caminhos e batem com o que vi.

## 7. Itens da fase / DoD não atendidos

Nenhum. O gate — "AC-24 satisfeito" — está cumprido: cada afirmação tem evidência
verificável, nada em produção foi alterado, nenhum segredo foi exposto, e
`docs/deploy.md` foi tratado como hipótese.

## 8. Divergências entre o relatório e o código real

Nenhuma divergência entre relatório e repositório.

Uma nota de estado, não de divergência: a **divergência 8** do relatório
(`seed_all.py` quebrado) descreve um defeito **já corrigido** na rodada de
2026-08-02 — `ReminderChannel` removido, `psycopg2-binary` acrescentado às
dependências de dev, `age` → `birth_date` acertado, verificado ponta a ponta em
banco limpo. O relatório da E.1 permanece correto quanto ao momento em que foi
escrito; é a tabela que merece a anotação de fechamento (§5).

---
data: 2026-08-02
titulo: Regras próprias de gitleaks (.gitleaks.toml) porque as default não pegam senha
status: ativa
tags: [seguranca, ci-cd, gitleaks, spec-002, fase-a3]
spec: 002-vitrine-eval-e-saneamento
fase: A.3
---

# Regras próprias de gitleaks (`.gitleaks.toml`)

## Contexto

A Fase A.3 da spec 002 declarava `Arquivos alterados: .pre-commit-config.yaml,
.github/workflows/ci.yml, SECURITY.md` e **nenhum arquivo novo**. A leitura
implícita era: gitleaks é uma ferramenta pronta, basta plugá-la nos dois pontos e o
gate existe.

A medição desmentiu isso. Rodando a ferramenta com as regras default sobre o
histórico **antes de qualquer purga** — histórico que naquele momento continha a
credencial pessoal do owner:

    $ gitleaks detect --log-opts="--all"
    INF 421 commits scanned.
    INF no leaks found                     → exit 0

    $ git log --all --oneline -S'<e-mail-pessoal>' | wc -l
    11                                     → 11 commits com o dado

Ou seja: o gate que a fase entregaria dava **verde sobre o próprio incidente que
originou o Track A**.

A causa é estrutural, não um bug. As regras default do gitleaks casam segredos com
**forma reconhecível** — `sk-...`, `ghp_...`, `AKIA...`, blocos `BEGIN PRIVATE KEY`.
Elas funcionam porque provedores emitem tokens com prefixo e entropia previsíveis. O
incidente do CalorIA foi uma **senha pessoal escolhida por um humano** e um
**e-mail pessoal** hardcoded num teste E2E. Nenhum dos dois tem forma reconhecível.
Nenhuma regra genérica os pega, agora ou nunca.

Entregar a A.3 sem fechar essa lacuna seria entregar um scanner que passa no AC-3
(segredo sintético com forma de chave de API é rejeitado) e falha na única classe de
segredo que este repositório comprovadamente vazou.

A extensão foi reportada ao owner e autorizada antes da execução.

## Decisão

**Criar `.gitleaks.toml`** na raiz, com `[extend] useDefault = true` (as regras
default continuam valendo, nada é perdido) mais **3 regras próprias**:

| id | o que casa |
|---|---|
| `caloria-senha-hardcoded` | atribuição de senha a variável/constante: `(?i)(?:password\|passwd\|pwd\|senha)[a-z0-9_]*\s*[:=]\s*["'][^"'\s${}<>\[\]]{8,}["']` |
| `caloria-senha-preenchida-em-teste` | `.fill()` de campo de senha em teste de UI — o padrão exato do AUD-038 |
| `caloria-email-pessoal` | e-mail de provedor de consumo hardcoded (PII) |

Efeito medido sobre a mesma varredura, mesmo histórico:

| configuração | resultado | exit |
|---|---|---|
| regras default | `no leaks found` | 0 |
| **com `.gitleaks.toml`** | **`leaks found: 30`** | **1** |

**As regras casam PADRÃO, nunca valor concreto.** Escrever a credencial real no
arquivo de configuração para detectá-la seria commitá-la — exatamente o problema que
se quer evitar. O arquivo carrega essa justificativa no cabeçalho, para que ninguém
"melhore" a detecção colando o valor.

**Allowlists são por regra e nomeiam valores um a um.** O escopo travado da fase
proíbe "desabilitar o gate com allowlist ampla para fazer a suíte passar". Cada
isenção nomeia um valor sintético específico (`Playwright@123`, `NovaSenha123`,
`senhaerrada`, `[REDIGIDO]`, `SENHA-REDIGIDA`) e vem justificada em `description`.
Nenhuma isenta um caminho amplo, uma regra inteira ou o repositório.

**Consequência no critério de aceite.** O AC-2 da spec foi reescrito junto: exige
agora `gitleaks detect --config .gitleaks.toml --log-opts="--all"` **e** uma
verificação literal `git log --all -S'<valor>' | wc -l == 0`, que não depende de
heurística alguma. A redação anterior do AC-2 aceitava a varredura default — que
esta medição prova ser um gate falso.

## Alternativas descartadas

- **Não criar o arquivo, usar só as regras default.** É o plano literal. Rejeitado
  pela medição: entrega um scanner que não detecta o incidente que criou a fase. O
  objetivo declarado da A.3 é "fechar a classe de problema, não só a instância"; sem
  o arquivo, ela não fecha nem a instância.

- **Adicionar o valor da credencial como regra literal (`regex = '<senha>'`).**
  Rejeitado sem discussão: commitaria a credencial num arquivo versionado. Além de
  autodestrutivo, seria detecção de instância, não de classe — a próxima senha
  hardcoded, diferente, passaria.

- **Usar `detect-secrets` (Yelp) em vez de gitleaks.** Ele tem heurística de
  entropia que pegaria mais senhas arbitrárias, mas ao custo de uma baseline
  (`.secrets.baseline`) que precisa ser mantida a cada commit e de uma taxa alta de
  falso-positivo em `package-lock.json` e hashes de migration. Rejeitado por custo de
  manutenção num projeto de um desenvolvedor, e porque a spec (§4, mapa NOVO) já
  nomeia `gitleaks` como a ferramenta escolhida — trocar de ferramenta é decisão de
  outra ordem que a de configurar a escolhida.

- **Regra genérica por entropia sobre qualquer string literal.** Rejeitado por
  precisão: senhas humanas têm entropia baixa (é o problema), então o limiar teria de
  descer a ponto de casar SHAs, base64 de fixtures e tokens de teste. O ganho de
  recall viria com um volume de falso-positivo que treinaria o desenvolvedor a
  ignorar o hook — o pior desfecho possível para um gate de segurança.

## Consequência

- O gate de segredos passa a detectar a classe real de vazamento deste repositório
  (senha humana e PII), não só chaves com forma de token.
- O AC-2 deixou de ser satisfazível por um comando que retornava zero sobre um
  histórico contaminado. O gate ficou mais caro de passar — de propósito.
- **Custo de manutenção assumido:** a regra `caloria-senha-hardcoded` casa
  atribuições legítimas em fixtures de teste. Cada nova senha sintética exige uma
  entrada explícita na allowlist, e essa entrada é uma decisão consciente de que o
  valor não é credencial real. É fricção deliberada: o caminho fácil não pode ser
  "isenta e segue".
- **Risco residual:** as 3 regras cobrem os padrões observados neste repositório.
  Uma senha atribuída por um caminho que não case os regexes (concatenação, variável
  intermediária, arquivo binário) passa. Nenhum scanner estático fecha isso; a
  mitigação é de processo — `SECURITY.md` foi atualizado e o hook roda em todo
  commit, elevando o custo do erro comum, não do adversário determinado.
- **Risco residual:** `useDefault = true` mantém a dependência das regras upstream;
  uma regressão do gitleaks em versão futura afeta o gate. O hook está pinado por
  `rev` no `.pre-commit-config.yaml`, então a atualização é explícita e revisável.

## Reprodução

    gitleaks detect --config .gitleaks.toml --log-opts="--all" --redact -v
    gitleaks detect --no-git --config .gitleaks.toml --redact -v   # working tree

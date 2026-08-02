---
data: 2026-08-02
titulo: Não abrir ticket ao GitHub Support para invalidar cache de commits órfãos
status: ativa
tags: [seguranca, documentacao, spec-002, fase-a2, risco-residual]
spec: 002-vitrine-eval-e-saneamento
fase: A.2
---

# Omissão deliberada do ticket ao GitHub Support

## Contexto

O passo 3 da Fase A.2 da spec 002 prescreve, como **ação do owner fora do agente**:
"executar `git filter-repo`, forçar push em todas as branches e refs, **e solicitar
ao GitHub Support a invalidação do cache de commits órfãos** — que permanecem
acessíveis por SHA mesmo após force-push".

A preocupação é real e bem formulada. Force-push não apaga objetos do lado do
GitHub: os commits antigos ficam *unreachable*, mas continuam servidos por URL
direta com o SHA (`github.com/<owner>/<repo>/commit/<sha>`) até que a plataforma os
colete — o que não tem prazo garantido. Só o Support invalida esse cache sob
demanda.

Os dois primeiros terços do passo foram executados: `git filter-repo` rodou, o
force-push foi feito em todas as branches e refs, e a verificação pós-purga
confirmou `git log --all -S'<credencial>' | wc -l` igual a `0`. O **ticket ao
Support foi deliberadamente omitido pelo owner**.

A omissão foi decidida com base em fatos verificados no momento, não por
esquecimento — mas não foi registrada em lugar nenhum até esta decision, o que a
avaliação independente da fase apontou corretamente como lacuna.

## Decisão

**Não abrir o ticket ao GitHub Support.** A fundamentação, verificada no momento da
decisão:

| fato verificado | o que ele elimina |
|---|---|
| `forks: 0`, `network: 0` | não existe rede de forks mantendo os objetos alcançáveis por outro repositório — o vetor mais comum de sobrevivência de commit purgado |
| `visibility: private` | acesso anônimo por SHA retorna **404**; o cache de commits órfãos não é alcançável sem credencial de colaborador |
| senha rotacionada em todos os serviços de reuso (Fase A.1, pré-condição confirmada por escrito pelo owner) | mesmo que o valor fosse recuperado, ele é **credencial morta** — não autentica em lugar nenhum |
| e-mail pessoal remanescente | o owner declarou explicitamente não considerá-lo sensível |

Somados: o que sobreviveria no cache é uma senha inválida e um e-mail que o owner
não trata como PII, num repositório que não serve nada a quem não está autenticado.
O ticket protegeria contra um risco que a rotação e a privatização já esvaziaram.

**Esta decisão vale enquanto `visibility: private` valer.** Ela é explicitamente
condicional, e a condição tem data para cair — ver risco residual.

## Alternativas descartadas

- **Abrir o ticket assim mesmo, por prudência.** É o que a spec prescreve. Rejeitado
  pelo owner com o argumento de custo/benefício: o ticket exige contato com suporte
  de terceiro sobre um repositório pessoal, com prazo de resposta fora do controle do
  projeto, para invalidar o cache de um segredo que já não autentica nada. A spec
  escreveu o passo antes de os fatos (`forks: 0`, privado, senha rotacionada)
  estarem estabelecidos; com eles em mãos, o passo perdeu o alvo. **A prescrição da
  spec continua correta como default** — a exceção é que aqui as quatro
  pré-condições que a justificam foram todas verificadas como ausentes.

- **Recriar o repositório do zero, sem histórico.** Elimina o cache de órfãos por
  construção, com certeza absoluta. Rejeitado por destruir exatamente o ativo que a
  spec 002 existe para expor: 400+ commits, o histórico de decisões, as issues e os
  PRs do Dependabot. Trocar a vitrine técnica inteira pela invalidação de um cache
  que guarda uma senha morta é desproporcional.

- **Manter o repositório privado para sempre.** Torna a mitigação permanente e
  gratuita. Rejeitado porque contradiz o objetivo da spec — a Fase D.2 promove `dev`
  para `main` e publica release num repositório de **portfólio**, que precisa ser
  legível por quem avalia.

- **Deixar o risco sem registro** (estado anterior a esta decision). Rejeitado: um
  passo prescrito e não executado, sem justificativa escrita, é indistinguível de
  falha de execução para qualquer leitor futuro — inclusive para o próprio owner
  daqui a seis meses, quando a D.2 for reabrir o repositório e a pergunta
  "o cache foi invalidado?" voltar sem resposta.

## Consequência

- A Fase A.2 fecha com o passo 3 parcialmente executado, e isso agora está
  **declarado** na §5 da spec, na OQ10 e aqui — não é mais divergência silenciosa
  entre plano e execução.

- **Risco residual acordado, com gatilho datado:** na **Fase D.2** o repositório
  volta a ser público. A partir desse instante, commits órfãos ainda em cache voltam
  a ser alcançáveis por SHA anônimo — para quem já tiver o SHA em mãos. O conteúdo
  exposto seria a senha (morta) e o e-mail (declarado não sensível), mas a exposição
  volta a existir.

  **Mitigação combinada com o owner:** deixar passar alguns dias entre a purga e a
  reabertura, para dar tempo ao ciclo de coleta de objetos inalcançáveis do GitHub.
  Não é garantia — a plataforma não publica prazo — mas é o custo zero disponível. O
  prazo é consumido naturalmente pelas dependências da D.2 (ela depende do Track D
  inteiro à sua frente e da esteira verde), então a mitigação não adiciona espera
  artificial ao projeto.

- **Ação exigida na D.2:** antes de tornar o repositório público, reverificar
  `forks`/`network` e reexecutar
  `git log --all -S'<valor>' --oneline | wc -l` (deve ser `0`). Se qualquer premissa
  desta decision tiver mudado — em especial o surgimento de forks — o ticket volta à
  mesa e esta decision passa a `superada`.

- **Risco residual menor:** a decisão apoia-se na declaração do owner de que o
  e-mail pessoal não é sensível. Se essa avaliação mudar, a purga já removeu o dado
  do histórico ativo, mas o cache de órfãos volta a ser relevante — e a resposta
  passa a ser o ticket.

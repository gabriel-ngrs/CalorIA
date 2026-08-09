# Política de Segurança

## Versões suportadas

Este é um projeto pessoal em desenvolvimento ativo. Apenas a versão mais recente da branch `main` recebe correções de segurança.

## Reportar uma vulnerabilidade

Se você encontrou uma vulnerabilidade de segurança, **não abra uma issue pública**.

Entre em contato diretamente pelo GitHub em modo privado:
- [Security Advisories](../../security/advisories/new)

Inclua na sua mensagem:
- Descrição da vulnerabilidade
- Passos para reproduzir
- Impacto potencial
- Sugestão de correção (se tiver)

Você receberá uma resposta em até 72 horas.

## Práticas de segurança do projeto

- Secrets e credenciais nunca são commitados — verificado por ferramenta, não por
  disciplina: o hook `gitleaks` do `.pre-commit-config.yaml` rejeita o commit local, e
  o step homônimo do job `backend` em `.github/workflows/ci.yml` é bloqueante e varre
  todo o histórico a cada push. `.env` continua no `.gitignore`.
- Além das regras default do `gitleaks` (chaves de API, tokens, chaves privadas), o
  `.gitleaks.toml` do projeto acrescenta três regras próprias que cobrem a classe que
  as default **não** cobrem: senha atribuída a variável, senha preenchida em teste de
  UI, e e-mail pessoal de provedor de consumo. Foram escritas depois de constatar que
  as regras default retornavam "no leaks found" sobre um histórico que continha uma
  credencial pessoal real.
- As isenções do `.gitleaks.toml` são por regra e nomeiam valores sintéticos
  específicos (a conta de desenvolvimento, as senhas dos testes e2e) ou o diretório de
  dado bruto de terceiro. Nenhuma isenta o repositório ou uma regra inteira.
- Autenticação via JWT com blacklist de refresh tokens no Redis
- Senhas com hash usando bcrypt (passlib)
- Chamadas à API do Groq passam exclusivamente pelo backend
- Fotos de refeições não são armazenadas permanentemente

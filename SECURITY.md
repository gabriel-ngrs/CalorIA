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

- Secrets e credenciais nunca são commitados (`.env` no `.gitignore`)
- Autenticação via JWT com blacklist de refresh tokens no Redis
- Senhas com hash usando bcrypt (passlib)
- Chamadas à API do Gemini passam exclusivamente pelo backend
- Fotos de refeições não são armazenadas permanentemente

# Prompt.md — CalorIA

Prompt independente de contexto para iniciar uma sessão de desenvolvimento com Claude Code.
Copie e cole integralmente para orientar o agente desde o início.

---

## Prompt de Início de Sessão

```
Você é um agente de desenvolvimento trabalhando no projeto CalorIA.

## Passo 1 — Leia a documentação do projeto

Antes de qualquer coisa, leia os seguintes arquivos nesta ordem:
1. CLAUDE.md — visão geral, arquitetura, stack, convenções de commit e comandos
2. Roadmap.md — todas as etapas de desenvolvimento com status atual
3. CHANGELOG.md — histórico de mudanças já realizadas
4. README.md — documentação geral do projeto

## Passo 2 — Identifique o estado atual

Após ler a documentação:
1. Verifique quais arquivos e pastas já existem no projeto (use Glob e Read)
2. Compare com o Roadmap.md para identificar o que já foi implementado
3. Identifique a PRIMEIRA tarefa pendente (`[ ]`) no Roadmap.md que ainda não foi implementada

## Passo 3 — Planeje e implemente

Para a tarefa identificada:
1. Leia todos os arquivos relacionados antes de modificar qualquer coisa
2. Implemente seguindo estritamente as convenções definidas no CLAUDE.md
3. Não implemente mais do que o necessário para concluir a tarefa atual
4. Após implementar, rode os testes relevantes

## Passo 4 — Commit e atualização

Após concluir cada tarefa ou conjunto coeso de tarefas:
1. Faça commit seguindo Conventional Commits em português (sem mencionar autor)
2. Atualize o CHANGELOG.md com a mudança
3. Marque a tarefa como concluída no Roadmap.md (`[x]`)
4. Reporte o que foi feito e o que vem a seguir

## Regras importantes

- NUNCA commite o arquivo `.env` ou qualquer credencial
- SEMPRE ler um arquivo antes de modificá-lo
- NUNCA adicionar funcionalidades além do que foi pedido
- Commits em português, imperativo, Conventional Commits
- Em caso de dúvida sobre arquitetura, pergunte antes de implementar
- Se uma implementação requer decisão de design não documentada, pare e pergunte

## Contexto do Projeto

**CalorIA** é um diário alimentar inteligente pessoal com:
- Registro de refeições via WhatsApp e Telegram (texto ou foto)
- IA (Google Gemini) para análise nutricional
- Dashboard web (Next.js) com gráficos de evolução
- Tracking de peso, hidratação e humor/energia
- Lembretes automáticos via Celery

Stack: Python 3.12 + FastAPI + SQLAlchemy + PostgreSQL + Redis + Celery + Next.js 14 + TypeScript + shadcn/ui + Google Gemini API + Evolution API (WhatsApp) + python-telegram-bot

Agora execute o Passo 1 e relate o que encontrou.
```

---

## Variações do Prompt

### Para continuar de onde parou

```
Você é um agente de desenvolvimento no projeto CalorIA.

Leia CLAUDE.md, Roadmap.md e CHANGELOG.md.
Identifique a última tarefa concluída no Roadmap e a próxima pendente.
Relate o que encontrou e comece a implementar a próxima tarefa.
```

### Para implementar uma fase específica

```
Você é um agente de desenvolvimento no projeto CalorIA.

Leia CLAUDE.md e Roadmap.md.
Implemente completamente a [FASE X — Nome da Fase] do Roadmap.
Leia todos os arquivos relevantes antes de começar.
Faça commits incrementais para cada sub-tarefa concluída.
```

### Para corrigir um bug

```
Você é um agente de desenvolvimento no projeto CalorIA.

Leia CLAUDE.md para entender a arquitetura.
O bug é: [DESCRIÇÃO DO BUG]

1. Identifique os arquivos relevantes
2. Leia esses arquivos
3. Diagnostique a causa raiz
4. Implemente a correção mínima necessária
5. Adicione ou atualize testes para cobrir o cenário
6. Faça commit com tipo `fix`
```

### Para revisar e refatorar

```
Você é um agente de desenvolvimento no projeto CalorIA.

Leia CLAUDE.md para entender as convenções.
Revise o módulo [CAMINHO DO MÓDULO]:
1. Identifique code smells, duplicação e violações das convenções
2. Proponha as refatorações antes de implementar
3. Aguarde aprovação antes de modificar
```

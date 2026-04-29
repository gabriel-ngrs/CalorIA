# Fluxos do Sistema CalorIA

Cada subpasta contem:
- `fluxo.md` — descricao textual
- `diagrama.mermaid` — diagrama visual

## Indice

| # | Fluxo | Descricao |
|---|-------|-----------|
| 01 | [Autenticacao](01-autenticacao/) | Login, refresh, logout |
| 04 | [Registro de Refeicao — Web](04-registro-refeicao-web/) | Analise e salvamento pelo dashboard |
| 05 | [Analise de IA](05-analise-ia/) | Pipeline 2 estagios |
| 06 | [Lookup Nutricional](06-lookup-nutricional/) | Busca fuzzy no banco de alimentos |
| 07 | [Insights e Relatorios](07-insights-relatorios/) | Insights, alertas, relatorio mensal |
| 08 | [Lembretes e Notificacoes](08-lembretes-notificacoes/) | Reminders e web push |
| 09 | [Celery — Tarefas](09-celery-tarefas/) | Tasks periodicas |
| 10 | [Dashboard e Frontend](10-dashboard-frontend/) | Navegacao e data fetching |
| 11 | [Logs de Saude](11-logs-saude/) | Peso, hidratacao, humor |

## Visualizar `.mermaid`

- **GitHub** renderiza automaticamente
- **VS Code** extensao "Mermaid Preview"
- **Online** em [mermaid.live](https://mermaid.live)

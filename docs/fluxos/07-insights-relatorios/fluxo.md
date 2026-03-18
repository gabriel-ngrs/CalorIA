# Fluxo de Insights e Relatorios

## Visao Geral

O `InsightsGenerator` usa a IA para gerar feedback personalizado com base nos dados nutricionais do usuario. Disponivel via API, frontend e Celery.

---

## 1. Tipos de Insight

| Metodo | Descricao | Trigger |
|--------|-----------|---------|
| `daily_insight()` | Feedback do dia: macros, aderencia, sugestoes | Bot /relatorio, Celery 22h, frontend |
| `weekly_insight()` | Analise da semana: consistencia, tendencias | Celery domingo 20h, frontend |
| `answer_question()` | Responde pergunta livre com contexto | Frontend |
| `suggest_meal()` | Sugere refeicao com base nas calorias restantes | Frontend |
| `eating_patterns()` | Analisa padroes alimentares (N dias) | Frontend |
| `nutritional_alerts()` | Detecta deficiencias nutricionais | Frontend |
| `goal_adjustment()` | Sugere ajuste de meta calorica | Frontend |
| `monthly_report()` | Relatorio mensal com aderencia por semana | Frontend |

---

## 2. Insight Diario

1. Busca dados do dia via `DashboardService.get_dashboard_today()`
   - Refeicoes, macros, hidratacao, humor
2. Monta prompt com meta vs consumido, macros detalhados, refeicoes
3. Gemini gera feedback de 2-4 paragrafos
4. Retorna `InsightResponse`

---

## 3. Insight Semanal

1. Busca resumo semanal via `DashboardService.get_weekly_summary()`
2. Busca tendencia de peso (ultimos 10 registros)
3. Monta prompt com medias, consistencia, tendencia
4. Gemini analisa e sugere melhorias
5. Retorna `InsightResponse`

---

## 4. Sugestao de Refeicao

1. Calcula calorias restantes: `meta - consumido_hoje`
2. Busca alimentos favoritos do historico (30 dias)
3. Gemini sugere refeicao que caiba nas calorias restantes
4. Retorna `MealSuggestion` com nome, macros, justificativa

---

## 5. Alertas Nutricionais

1. Busca todas as refeicoes dos ultimos N dias
2. Agrega macros medios diarios
3. Gemini analisa deficiencias (fibra, proteina, gordura saturada, etc.)
4. Retorna `NutritionalAlertsResponse` com lista de alertas

---

## 6. Ajuste de Meta

1. Busca registros de peso (30 dias)
2. Calcula tendencia: ganhando, perdendo ou estavel
3. Gemini sugere ajuste de meta calorica com justificativa
4. Retorna `GoalAdjustmentSuggestion`

---

## 7. Relatorio Mensal

1. Busca todas as refeicoes do mes
2. Calcula por semana: dias logados, media de calorias, aderencia (%)
3. Calcula geral: aderencia total, consistencia, macros medios
4. Gemini gera analise detalhada
5. Retorna `MonthlyReport` com `adherence_score`, `weeks[]`, analise

---

## 8. Interface no Frontend

Pagina `/insights` com abas:
- **Diario** — botao "Gerar insight"
- **Semanal** — botao "Gerar insight"
- **Perguntar** — input de texto livre
- **Padroes** — slider 7-90 dias
- **Alertas** — slider 7-30 dias
- **Relatorios** — seletor mes/ano

---

## Arquivos-chave

| Arquivo | Responsabilidade |
|---------|------------------|
| `services/ai/insights_generator.py` | Todos os metodos de geracao |
| `services/ai/pattern_analyzer.py` | Analise de padroes alimentares |
| `services/dashboard_service.py` | Dados agregados para insights |
| `api/v1/ai.py` | Endpoints de insights |
| `frontend/lib/hooks/useAI.ts` | Hooks React para insights |
| `frontend/app/(dashboard)/insights/page.tsx` | Pagina de insights |

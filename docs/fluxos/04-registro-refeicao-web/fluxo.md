# Fluxo de Registro de Refeicao — Web (Dashboard)

## Visao Geral

O frontend permite registrar refeicoes de duas formas: analisando texto ou foto via IA, ou criando manualmente. A analise usa os mesmos parsers dos bots.

---

## 1. Analise de Texto

1. Usuario digita descricao no modal (ex: "200g arroz com frango")
2. Clica "Analisar" → hook `useAnalyzeMeal().mutate(description)`
3. Frontend chama `POST /api/v1/ai/analyze-meal {description}`
4. Backend autentica JWT, busca usuario, monta contexto
5. Chama `MealParser.parse(descricao, contexto, db)`
6. Retorna `MealAnalysisResponse` com itens e `low_confidence`
7. Frontend exibe itens identificados e totais de macros
8. Se `low_confidence=true`: exibe aviso
9. Usuario clica "Salvar" → `useCreateMeal().mutate(mealData)`
10. Frontend chama `POST /api/v1/meals {meal_type, date, items}`
11. Backend insere `Meal` + `MealItem` no banco
12. React Query invalida caches `["meals"]` e `["dashboard"]`
13. Dashboard atualiza automaticamente

---

## 2. Analise de Foto

1. Usuario seleciona imagem via file input
2. Frontend le arquivo com `FileReader.readAsDataURL()`
3. Extrai base64 e mime_type
4. Chama `POST /api/v1/ai/analyze-photo {image_base64, mime_type}`
5. Backend chama `VisionParser.parse_base64()`
6. Mesmo fluxo de exibicao e salvamento que texto

---

## 3. Quick Add (Modal Rapido)

O dashboard tem 4 modais rapidos:
- **Refeicao**: digita descricao → analisa com IA → salva
- **Agua**: informa ml → `POST /api/v1/hydration`
- **Peso**: informa kg → `POST /api/v1/weight`
- **Humor**: seleciona energia + humor (1-5) → `POST /api/v1/mood`

Ao salvar qualquer modal, React Query invalida caches e o dashboard atualiza.

---

## 4. Gerenciamento de Token

1. Cada request passa pelo interceptor do `api.ts`
2. Interceptor verifica cache de token em memoria
3. Se token expira em < 2 min: forca refresh via `getSession()`
4. Se multiplos requests simultaneos: compartilha uma unica Promise
5. Se recebe 401: invalida cache e tenta 1 vez com token novo

---

## Arquivos-chave

| Arquivo | Responsabilidade |
|---------|------------------|
| `frontend/lib/hooks/useMeals.ts` | `useAnalyzeMeal()`, `useAnalyzePhoto()`, `useCreateMeal()` |
| `frontend/lib/hooks/useDashboard.ts` | `useDashboardToday()`, `useMacrosChart()` |
| `frontend/components/dashboard/QuickAddModals.tsx` | Modais de adicao rapida |
| `frontend/lib/api.ts` | Axios com interceptors e refresh |
| `backend/app/api/v1/ai.py` | Endpoints `/analyze-meal` e `/analyze-photo` |
| `backend/app/api/v1/meals.py` | CRUD de refeicoes |

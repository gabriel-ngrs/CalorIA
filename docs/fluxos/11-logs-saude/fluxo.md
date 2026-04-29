# Fluxo de Logs de Saude

## Visao Geral

O usuario pode registrar peso, hidratacao e humor/energia. Esses dados alimentam insights, relatorios e lembretes.

---

## 1. Registro de Peso

**Via Dashboard:**
1. Usuario informa peso (ex: 75.5 kg) no modal rapido
2. Frontend chama `POST /api/v1/weight {weight_kg, date}`
3. Backend insere em `weight_logs`

**Uso do peso:**
- Grafico de evolucao no dashboard
- Recalculo mensal de TDEE (Celery)
- Tendencia nos insights semanais
- Sugestao de ajuste de meta calorica

---

## 2. Registro de Hidratacao

**Via Dashboard:**
1. Usuario informa ml (ex: 500) no modal rapido
2. Frontend chama `POST /api/v1/hydration {amount_ml}`
3. Backend insere em `hydration_logs`

**Ciclo de hidratacao:**
- Cada registro acumula no total do dia
- Barra de progresso no dashboard
- Se nao atingiu meta: Celery envia lembretes (8h-20h)
- Incluso nos insights diarios

---

## 3. Registro de Humor/Energia

**Via Dashboard:**
1. Usuario seleciona energia (1-5) + humor (1-5) no modal
2. Frontend chama `POST /api/v1/mood {energy_level, mood_level, date}`
3. Backend insere em `mood_logs`

**Uso do humor:**
- Exibido no dashboard do dia
- Correlacao com alimentacao nos insights
- Incluso nos relatorios semanais/mensais

---

## 4. Endpoints

### Peso
| Metodo | Endpoint | Descricao |
|--------|----------|-----------|
| `GET` | `/api/v1/weight?skip=0&limit=50` | Lista registros |
| `POST` | `/api/v1/weight` | Registra novo peso |

### Hidratacao
| Metodo | Endpoint | Descricao |
|--------|----------|-----------|
| `GET` | `/api/v1/hydration/today?day=YYYY-MM-DD` | Resumo do dia |
| `GET` | `/api/v1/hydration/history?days=7` | Historico |
| `POST` | `/api/v1/hydration` | Registra consumo |

### Humor
| Metodo | Endpoint | Descricao |
|--------|----------|-----------|
| `GET` | `/api/v1/mood` | Lista registros |
| `POST` | `/api/v1/mood` | Registra humor |

---

## 5. Modelos de Dados

**WeightLog:** id, user_id (FK), weight_kg (float), date, created_at

**HydrationLog:** id, user_id (FK), amount_ml (int), date, created_at

**MoodLog:** id, user_id (FK), energy_level (1-5), mood_level (1-5), notes (opcional), date, created_at

---

## Arquivos-chave

| Arquivo | Responsabilidade |
|---------|------------------|
| `api/v1/weight.py` | Endpoints de peso |
| `api/v1/hydration.py` | Endpoints de hidratacao |
| `api/v1/mood.py` | Endpoints de humor |
| `services/weight_service.py` | CRUD de peso |
| `services/hydration_service.py` | CRUD de hidratacao |
| `services/mood_service.py` | CRUD de humor |
| `models/weight_log.py` | Modelo WeightLog |
| `models/hydration_log.py` | Modelo HydrationLog |
| `models/mood_log.py` | Modelo MoodLog |

from __future__ import annotations

import json
import logging

from app.schemas.ai import MealAnalysisResponse, ParsedFoodItem
from app.services.ai.gemini_client import GeminiClient
from app.services.ai.utils import extract_json_from_ai_response

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tabela TACO expandida + alimentos processados/fast food (valores por 100g,
# já cozido/preparado quando aplicável).
# ---------------------------------------------------------------------------
_TACO_TABLE = """
=== TABELA NUTRICIONAL — valores por 100g (cozido/preparado, salvo indicação) ===

── CEREAIS E GRÃOS ──────────────────────────────────────────────────────────
Arroz branco cozido:          128 kcal | prot 2.5g  | carb 28.1g | gord 0.2g | fibra 1.6g
Arroz integral cozido:        124 kcal | prot 2.6g  | carb 25.8g | gord 1.0g | fibra 2.7g
Feijão carioca cozido:         76 kcal | prot 4.8g  | carb 13.6g | gord 0.5g | fibra 8.5g
Feijão preto cozido:           77 kcal | prot 4.5g  | carb 14.0g | gord 0.5g | fibra 8.4g
Lentilha cozida:              111 kcal | prot 9.0g  | carb 19.7g | gord 0.4g | fibra 3.7g
Grão-de-bico cozido:          164 kcal | prot 8.9g  | carb 27.4g | gord 2.6g | fibra 6.2g
Ervilha cozida:                81 kcal | prot 5.4g  | carb 14.5g | gord 0.4g | fibra 5.7g
Macarrão cozido:              148 kcal | prot 5.0g  | carb 30.5g | gord 0.8g | fibra 1.8g
Macarrão integral cozido:     124 kcal | prot 4.7g  | carb 26.0g | gord 0.8g | fibra 4.5g
Aveia em flocos:              394 kcal | prot 13.9g | carb 66.6g | gord 8.5g | fibra 9.1g
Farinha de trigo:             361 kcal | prot 9.8g  | carb 75.1g | gord 1.4g | fibra 2.9g
Cuscuz (milho) preparado:     105 kcal | prot 2.0g  | carb 23.0g | gord 0.5g | fibra 1.2g
Milho verde cozido:            86 kcal | prot 3.2g  | carb 18.7g | gord 1.0g | fibra 2.0g
Granola (tradicional):        420 kcal | prot 9.0g  | carb 65.0g | gord 14.0g| fibra 5.0g
Quinoa cozida:                120 kcal | prot 4.4g  | carb 21.3g | gord 1.9g | fibra 2.8g

── PÃES E MASSAS ────────────────────────────────────────────────────────────
Pão francês:                  300 kcal | prot 8.0g  | carb 58.6g | gord 3.1g | fibra 2.3g
Pão de forma integral:        269 kcal | prot 9.5g  | carb 48.0g | gord 4.8g | fibra 5.5g
Pão de forma branco:          264 kcal | prot 7.8g  | carb 50.8g | gord 3.4g | fibra 2.3g
Pão de queijo (30g/unid):     314 kcal | prot 7.0g  | carb 42.0g | gord 13.0g| fibra 0.5g
Tapioca (goma seca):          354 kcal | prot 0.2g  | carb 88.0g | gord 0.0g | fibra 0.0g
Tapioca pronta (100g c/ recheio): estimativa varia; base 100g sem recheio ≈ 130 kcal
Torrada simples:              380 kcal | prot 11.0g | carb 72.0g | gord 4.0g | fibra 3.0g
Biscoito de polvilho:         490 kcal | prot 4.0g  | carb 72.0g | gord 20.0g| fibra 0.5g
Biscoito cream cracker:       420 kcal | prot 9.0g  | carb 68.0g | gord 12.0g| fibra 2.0g

── CARNES E PROTEÍNAS ANIMAIS ──────────────────────────────────────────────
Frango peito grelhado/assado: 163 kcal | prot 28.6g | carb 0.0g  | gord 4.7g | fibra 0.0g
Frango peito cozido:          159 kcal | prot 28.8g | carb 0.0g  | gord 4.2g | fibra 0.0g
Frango peito frito empanado:  245 kcal | prot 22.0g | carb 10.0g | gord 13.0g| fibra 0.5g
Frango coxa/sobrecoxa assada: 215 kcal | prot 22.0g | carb 0.0g  | gord 13.5g| fibra 0.0g
Carne bovina grelhada (patinho): 219 kcal | prot 27.5g | carb 0.0g | gord 11.5g | fibra 0.0g
Carne bovina moída refogada:  252 kcal | prot 20.7g | carb 2.0g  | gord 18.5g| fibra 0.0g
Carne bovina cozida:          185 kcal | prot 24.5g | carb 0.0g  | gord 9.5g | fibra 0.0g
Alcatra grelhada:             205 kcal | prot 26.0g | carb 0.0g  | gord 10.5g| fibra 0.0g
Picanha grelhada:             290 kcal | prot 22.0g | carb 0.0g  | gord 22.0g| fibra 0.0g
Costela bovina cozida:        310 kcal | prot 19.0g | carb 0.0g  | gord 25.0g| fibra 0.0g
Linguiça calabresa frita:     350 kcal | prot 14.0g | carb 2.0g  | gord 32.0g| fibra 0.0g
Linguiça toscana assada:      290 kcal | prot 16.0g | carb 1.5g  | gord 25.0g| fibra 0.0g
Presunto cozido fatiado:      130 kcal | prot 17.0g | carb 2.0g  | gord 6.0g | fibra 0.0g
Peito de peru defumado:       115 kcal | prot 18.5g | carb 2.0g  | gord 3.5g | fibra 0.0g
Salame italiano:              380 kcal | prot 22.0g | carb 1.0g  | gord 32.0g| fibra 0.0g
Bacon frito:                  540 kcal | prot 12.0g | carb 0.0g  | gord 55.0g| fibra 0.0g
Atum em lata (em água, drenado): 130 kcal | prot 29.0g | carb 0.0g | gord 1.5g | fibra 0.0g
Sardinha em lata (óleo, drenada): 208 kcal | prot 24.6g | carb 0.0g | gord 12.0g | fibra 0.0g
Salmão assado/grelhado:       206 kcal | prot 28.0g | carb 0.0g  | gord 10.0g| fibra 0.0g
Tilápia grelhada:             128 kcal | prot 26.0g | carb 0.0g  | gord 2.7g | fibra 0.0g
Camarão cozido:               106 kcal | prot 20.3g | carb 0.9g  | gord 1.7g | fibra 0.0g
Ovo inteiro cozido:           146 kcal | prot 13.3g | carb 0.6g  | gord 9.7g | fibra 0.0g
Ovo inteiro mexido (c/ óleo):  171 kcal | prot 11.9g | carb 1.4g  | gord 13.0g| fibra 0.0g
Ovo inteiro frito (c/ óleo):   196 kcal | prot 13.6g | carb 0.4g  | gord 15.5g| fibra 0.0g
Clara de ovo cozida:           52 kcal | prot 11.0g | carb 0.7g  | gord 0.2g | fibra 0.0g

── TUBÉRCULOS E LEGUMES ────────────────────────────────────────────────────
Batata inglesa cozida:         52 kcal | prot 1.2g  | carb 11.9g | gord 0.1g | fibra 1.8g
Batata-doce cozida:            77 kcal | prot 0.6g  | carb 18.4g | gord 0.1g | fibra 2.2g
Batata frita (imersão em óleo): 312 kcal | prot 3.5g | carb 36.0g | gord 17.0g | fibra 3.0g
Batata frita (airfryer):       220 kcal | prot 3.5g | carb 36.0g | gord 7.0g | fibra 3.0g
Mandioca cozida:              125 kcal | prot 0.6g  | carb 30.1g | gord 0.3g | fibra 1.9g
Mandioca frita:               220 kcal | prot 1.0g  | carb 35.0g | gord 8.5g | fibra 1.5g
Inhame cozido:                 95 kcal | prot 2.5g  | carb 22.5g | gord 0.1g | fibra 4.2g
Brócolis cozido:               25 kcal | prot 2.3g  | carb 4.3g  | gord 0.4g | fibra 3.3g
Cenoura cozida:                35 kcal | prot 0.8g  | carb 8.0g  | gord 0.2g | fibra 3.0g
Abobrinha cozida:              17 kcal | prot 1.2g  | carb 3.2g  | gord 0.3g | fibra 1.5g
Chuchu cozido:                 19 kcal | prot 0.9g  | carb 4.0g  | gord 0.1g | fibra 1.5g
Couve refogada c/ azeite:      65 kcal | prot 3.5g  | carb 5.0g  | gord 3.5g | fibra 3.5g
Alface crua:                   11 kcal | prot 1.0g  | carb 1.8g  | gord 0.2g | fibra 1.5g
Tomate cru:                    15 kcal | prot 0.9g  | carb 3.1g  | gord 0.2g | fibra 1.2g
Cebola crua:                   40 kcal | prot 1.1g  | carb 9.3g  | gord 0.1g | fibra 1.7g
Pepino cru:                    13 kcal | prot 0.7g  | carb 2.6g  | gord 0.1g | fibra 0.8g

── FRUTAS ──────────────────────────────────────────────────────────────────
Banana nanica:                 92 kcal | prot 1.3g  | carb 23.8g | gord 0.1g | fibra 1.9g
Banana prata:                  98 kcal | prot 1.2g  | carb 25.8g | gord 0.1g | fibra 2.0g
Maçã com casca:                56 kcal | prot 0.3g  | carb 15.2g | gord 0.0g | fibra 1.4g
Laranja pera:                  49 kcal | prot 0.9g  | carb 12.5g | gord 0.1g | fibra 2.4g
Mamão formosa:                 40 kcal | prot 0.5g  | carb 10.4g | gord 0.1g | fibra 1.8g
Melancia:                      33 kcal | prot 0.7g  | carb 8.0g  | gord 0.1g | fibra 0.4g
Melão:                         29 kcal | prot 0.8g  | carb 6.7g  | gord 0.1g | fibra 0.4g
Manga palmer:                  57 kcal | prot 0.8g  | carb 14.6g | gord 0.3g | fibra 1.6g
Uva itália (c/ semente):       69 kcal | prot 0.9g  | carb 17.0g | gord 0.3g | fibra 0.9g
Abacaxi:                       48 kcal | prot 0.6g  | carb 12.5g | gord 0.1g | fibra 1.2g
Morango:                       32 kcal | prot 0.7g  | carb 7.7g  | gord 0.3g | fibra 2.1g
Abacate:                      160 kcal | prot 1.5g  | carb 8.5g  | gord 14.5g| fibra 6.3g
Açaí puro (polpa, sem adição): 58 kcal | prot 1.2g  | carb 6.2g  | gord 3.2g | fibra 2.6g
Açaí batido c/ guaraná e banana (tigela 300ml): 320 kcal | prot 4.0g | carb 55.0g | gord 9.0g | fibra 3.0g

── LATICÍNIOS E OVOS ───────────────────────────────────────────────────────
Leite integral:                61 kcal | prot 3.2g  | carb 4.7g  | gord 3.2g | fibra 0.0g
Leite desnatado:               35 kcal | prot 3.4g  | carb 4.7g  | gord 0.2g | fibra 0.0g
Leite semidesnatado:           47 kcal | prot 3.3g  | carb 4.7g  | gord 1.5g | fibra 0.0g
Iogurte natural integral:      66 kcal | prot 4.2g  | carb 5.4g  | gord 3.0g | fibra 0.0g
Iogurte natural desnatado:     40 kcal | prot 4.5g  | carb 5.0g  | gord 0.2g | fibra 0.0g
Iogurte grego integral:       110 kcal | prot 9.0g  | carb 3.5g  | gord 7.0g | fibra 0.0g
Queijo mussarela:             289 kcal | prot 18.2g | carb 3.0g  | gord 22.5g| fibra 0.0g
Queijo minas frescal:         144 kcal | prot 8.5g  | carb 3.7g  | gord 10.6g| fibra 0.0g
Queijo minas padrão:          264 kcal | prot 18.0g | carb 1.5g  | gord 20.5g| fibra 0.0g
Queijo prato:                 358 kcal | prot 22.5g | carb 1.8g  | gord 29.5g| fibra 0.0g
Requeijão cremoso:            250 kcal | prot 9.5g  | carb 3.0g  | gord 22.5g| fibra 0.0g
Creme de leite (caixinha):    200 kcal | prot 2.5g  | carb 3.5g  | gord 20.0g| fibra 0.0g
Manteiga:                     726 kcal | prot 0.6g  | carb 0.0g  | gord 80.5g| fibra 0.0g
Margarina:                    540 kcal | prot 0.5g  | carb 0.5g  | gord 60.0g| fibra 0.0g
Whey protein pó (por 100g):   370 kcal | prot 75.0g | carb 8.0g  | gord 5.0g | fibra 0.0g

── GORDURAS E ÓLEOS ────────────────────────────────────────────────────────
Azeite de oliva:              884 kcal | prot 0.0g  | carb 0.0g  | gord 100g | fibra 0.0g
Óleo de soja/milho/girassol:  884 kcal | prot 0.0g  | carb 0.0g  | gord 100g | fibra 0.0g
Óleo de coco:                 892 kcal | prot 0.0g  | carb 0.0g  | gord 99.0g| fibra 0.0g
Pasta de amendoim integral:   598 kcal | prot 25.0g | carb 20.0g | gord 50.0g| fibra 6.0g
Amendoim torrado s/ sal:      567 kcal | prot 25.8g | carb 20.0g | gord 45.4g| fibra 6.5g
Castanha do Pará:             655 kcal | prot 14.5g | carb 12.3g | gord 63.5g| fibra 6.8g
Castanha de caju torrada:     570 kcal | prot 15.3g | carb 32.7g | gord 44.8g| fibra 3.0g
Nozes:                        620 kcal | prot 15.2g | carb 10.6g | gord 58.8g| fibra 4.3g

── AÇÚCARES E DOCES ────────────────────────────────────────────────────────
Açúcar refinado:              387 kcal | prot 0.0g  | carb 99.9g | gord 0.0g | fibra 0.0g
Açúcar mascavo:               375 kcal | prot 0.0g  | carb 95.5g | gord 0.0g | fibra 0.0g
Mel:                          309 kcal | prot 0.4g  | carb 82.4g | gord 0.0g | fibra 0.0g
Geleia de fruta:              250 kcal | prot 0.5g  | carb 62.0g | gord 0.0g | fibra 0.5g
Chocolate ao leite:           535 kcal | prot 7.0g  | carb 60.0g | gord 29.0g| fibra 2.0g
Chocolate meio amargo (70%+): 580 kcal | prot 8.0g  | carb 42.0g | gord 42.0g| fibra 8.0g

── BEBIDAS ─────────────────────────────────────────────────────────────────
Café preto sem açúcar:          2 kcal | prot 0.1g  | carb 0.0g  | gord 0.0g | fibra 0.0g
Suco de laranja natural:       45 kcal | prot 0.7g  | carb 10.4g | gord 0.2g | fibra 0.2g
Suco de uva integral:          64 kcal | prot 0.4g  | carb 16.0g | gord 0.2g | fibra 0.2g
Refrigerante cola (350ml lata): 140 kcal | prot 0.0g | carb 37.0g | gord 0.0g | fibra 0.0g
Refrigerante zero/diet:          0 kcal | prot 0.0g | carb 0.0g  | gord 0.0g | fibra 0.0g
Cerveja (350ml, 5% álcool):    150 kcal | prot 1.1g | carb 13.0g | gord 0.0g | fibra 0.0g
Água de coco (200ml):           38 kcal | prot 0.4g | carb 8.0g  | gord 0.2g | fibra 0.2g

── FAST FOOD E ULTRAPROCESSADOS ────────────────────────────────────────────
Big Mac (McDonald's, 1 unid, 219g):  563 kcal | prot 26.0g | carb 44.0g | gord 32.5g | fibra 3.0g
McDouble (McDonald's, 1 unid, 163g): 440 kcal | prot 25.0g | carb 36.0g | gord 22.0g | fibra 2.0g
Fritas pequenas McDonald's (115g):   320 kcal | prot 3.5g  | carb 42.0g | gord 16.0g | fibra 3.5g
Fritas médias McDonald's (154g):     430 kcal | prot 4.5g  | carb 56.0g | gord 21.0g | fibra 4.5g
Whopper Burger King (1 unid, 291g):  657 kcal | prot 28.0g | carb 49.0g | gord 40.0g | fibra 2.0g
Pizza muçarela (1 fatia média, ~100g): 250 kcal | prot 12.0g | carb 28.0g | gord 10.0g | fibra 1.5g
Pizza calabresa (1 fatia média, ~100g): 270 kcal | prot 11.0g | carb 27.0g | gord 13.0g | fibra 1.5g
Hot dog completo (1 unid, ~200g):    420 kcal | prot 16.0g | carb 40.0g | gord 22.0g | fibra 2.0g
Coxinha de frango (1 unid, ~100g):   290 kcal | prot 12.0g | carb 29.0g | gord 14.0g | fibra 1.0g
Esfirra aberta de carne (~80g):      220 kcal | prot 9.0g  | carb 25.0g | gord 9.5g  | fibra 1.0g
Pastel de forno (~100g):             250 kcal | prot 9.0g  | carb 30.0g | gord 10.0g | fibra 1.0g
Pão de hambúrguer (1 unid, 50g):    150 kcal | prot 4.5g  | carb 27.0g | gord 2.5g  | fibra 1.5g
Hambúrguer bovino grelhado (100g):  250 kcal | prot 20.0g | carb 0.0g  | gord 18.0g | fibra 0.0g
Nuggets frango (1 unid, ~20g):       55 kcal | prot 3.0g  | carb 4.0g  | gord 3.0g  | fibra 0.0g

── SUPLEMENTOS ─────────────────────────────────────────────────────────────
Whey protein (1 dose/scoop ~30g):   110 kcal | prot 22.0g | carb 3.0g  | gord 2.0g  | fibra 0.5g
Creatina monohidratada (5g):          0 kcal | prot 0.0g  | carb 0.0g  | gord 0.0g  | fibra 0.0g
Barra de proteína (média, 60g):     200 kcal | prot 20.0g | carb 20.0g | gord 5.0g  | fibra 3.0g
Hipercalórico (1 dose ~150g):       600 kcal | prot 25.0g | carb 110.0g| gord 6.0g  | fibra 1.0g
"""

_PORTIONS_REF = """
=== PORÇÕES TÍPICAS BRASILEIRAS — USE PARA ESTIMAR QUANTIDADE EM GRAMAS ===
"prato de arroz" (colher de servir grande)      → 150-200g → 192-256 kcal
"concha de feijão" (com caldo)                  → 80-100g  → 65-80 kcal
"filé de frango pequeno"                        → 100-120g → 163-195 kcal
"filé de frango médio"                          → 150-180g → 245-293 kcal
"filé de frango grande"                         → 200-250g → 326-408 kcal
"bife médio"                                    → 140-160g → 305-350 kcal
"pão francês" (1 unidade)                       → 50g      → 150 kcal
"fatia de pão de forma" (1 unidade)             → 25g      → 67 kcal
"ovo" (1 unidade inteiro médio)                 → 50g      → 73 kcal
"colher de sopa de azeite" (1 col.)             → 10-13ml  → 88-115 kcal
"colher de sopa de manteiga" (1 col.)           → 10g      → 73 kcal
"colher de sopa de açúcar" (1 col.)             → 10-15g   → 39-58 kcal
"colher de sopa de requeijão" (1 col.)          → 15g      → 38 kcal
"fatia de queijo mussarela" (1 unidade)         → 15-20g   → 43-58 kcal
"xícara de leite" (200ml)                       → 200g     → 122 kcal (integral)
"dose de whey" (1 scoop)                        → 30g      → 110 kcal
"banana" (1 unidade média)                      → 90-110g  → 83-101 kcal
"maçã" (1 unidade média)                        → 150-180g → 84-101 kcal
"colher de sopa de arroz" (cheia)               → 25-30g   → 32-38 kcal
"colher de sopa de feijão" (sem caldo)          → 20-25g   → 15-19 kcal
"""

_SYSTEM_PROMPT = f"""Você é um nutricionista especializado em alimentação brasileira com acesso à tabela TACO e dados de alimentos ultraprocessados.

REGRAS ABSOLUTAS — nunca viole:
1. RETORNE APENAS JSON VÁLIDO. Zero markdown, zero texto fora do JSON.
2. USE SEMPRE os valores da tabela de referência abaixo quando o alimento for reconhecido.
3. NUNCA invente macros do zero — se não reconhecer o alimento, indique confidence 0.5 e use estimativa conservadora.
4. Calcule calorias TOTAIS para a porção (não por 100g): calories = protein×4 + carbs×4 + fat×9 (±2%).
5. Liste CADA ingrediente separadamente, mesmo em pratos compostos.
6. Diferencie SEMPRE o método de preparo: grelhado ≠ frito ≠ cozido ≠ assado (impacta calorias).
7. Quando a porção for vaga ("um prato", "uma porção"), use a seção de porções típicas.
8. confidence: 1.0 = alimento na tabela + porção exata informada; 0.85 = alimento na tabela + porção estimada; 0.6 = estimativa sem referência direta.

FORMATO OBRIGATÓRIO (array JSON):
[
  {{
    "food_name": "nome do alimento em português",
    "quantity": 200,
    "unit": "g",
    "calories": 256,
    "protein": 5.0,
    "carbs": 56.2,
    "fat": 0.4,
    "fiber": 3.2,
    "confidence": 0.85
  }}
]

{_TACO_TABLE}
{_PORTIONS_REF}"""

_USER_TEMPLATE = """CONTEXTO DO USUÁRIO (use para calibrar porções):
{user_context}

DESCRIÇÃO DA REFEIÇÃO:
{description}

Pense passo a passo INTERNAMENTE (não escreva os passos):
1. Identifique cada alimento e método de preparo
2. Converta descrições vagas para gramas usando as porções típicas e o histórico do usuário
3. Busque cada alimento na tabela TACO acima
4. Calcule os macros para a porção total (não por 100g)
5. Verifique: calories ≈ protein×4 + carbs×4 + fat×9

Retorne SOMENTE o array JSON."""

_CONFIDENCE_THRESHOLD = 0.6


def _correct_calories(items: list[ParsedFoodItem]) -> list[ParsedFoodItem]:
    """Recalcula calorias a partir dos macros usando fatores de Atwater.

    A IA às vezes diverge entre calorias e macros. Este pós-processamento
    garante consistência matemática: calories = protein×4 + carbs×4 + fat×9.
    """
    corrected = []
    for item in items:
        calculated = item.protein * 4.0 + item.carbs * 4.0 + item.fat * 9.0
        # Se a divergência for > 10%, usa o valor calculado e loga
        if abs(calculated - item.calories) > item.calories * 0.10:
            logger.warning(
                "Divergência calórica em '%s': IA=%s kcal, calculado=%.1f kcal. Usando calculado.",
                item.food_name, item.calories, calculated,
            )
            item = item.model_copy(update={"calories": round(calculated, 1)})
        corrected.append(item)
    return corrected


class MealParser:
    def __init__(self, client: GeminiClient) -> None:
        self._client = client

    async def parse(
        self,
        description: str,
        user_context: str = "usuário sem histórico",
    ) -> MealAnalysisResponse:
        user_msg = _USER_TEMPLATE.format(
            user_context=user_context,
            description=description,
        )

        try:
            raw = await self._client.generate_text(
                user_msg,
                use_cache=False,  # análise de refeição nunca deve ser cacheada
                system=_SYSTEM_PROMPT,
            )
            data = extract_json_from_ai_response(raw)
        except json.JSONDecodeError as exc:
            logger.error("Groq retornou JSON inválido para análise de texto: %s", exc)
            raise ValueError("A IA não conseguiu analisar a descrição da refeição.") from exc

        items = [ParsedFoodItem(**item) for item in data]
        items = _correct_calories(items)
        low_confidence = any(it.confidence < _CONFIDENCE_THRESHOLD for it in items)

        return MealAnalysisResponse(items=items, low_confidence=low_confidence)

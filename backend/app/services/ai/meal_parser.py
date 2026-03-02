from __future__ import annotations

import json
import logging

from app.schemas.ai import MealAnalysisResponse, ParsedFoodItem
from app.services.ai.gemini_client import GeminiClient
from app.services.ai.utils import extract_json_from_ai_response

logger = logging.getLogger(__name__)

# System prompt separado do conteúdo do usuário para melhor instruction-following.
# Contém tabela TACO (Tabela Brasileira de Composição de Alimentos) para precisão.
_SYSTEM_PROMPT = """Você é um nutricionista especializado em culinária brasileira. \
Analise descrições de refeições e extraia todos os alimentos com macronutrientes precisos.

RETORNE APENAS JSON VÁLIDO. Sem markdown, sem texto adicional, sem explicações.

Formato obrigatório:
[
  {
    "food_name": "nome do alimento em português",
    "quantity": 200,
    "unit": "g",
    "calories": 260,
    "protein": 4.8,
    "carbs": 56.8,
    "fat": 0.4,
    "fiber": 0.5,
    "confidence": 0.9
  }
]

=== TABELA NUTRICIONAL DE REFERÊNCIA — TACO (valores por 100g, já cozido/preparado) ===
Arroz branco cozido:         128 kcal | prot 2.5g  | carb 28.1g | gord 0.2g | fibra 1.6g
Arroz integral cozido:       124 kcal | prot 2.6g  | carb 25.8g | gord 1.0g | fibra 2.7g
Feijão carioca cozido:        76 kcal | prot 4.8g  | carb 13.6g | gord 0.5g | fibra 8.5g
Feijão preto cozido:          77 kcal | prot 4.5g  | carb 14.0g | gord 0.5g | fibra 8.4g
Lentilha cozida:             111 kcal | prot 9.0g  | carb 19.7g | gord 0.4g | fibra 3.7g
Frango peito grelhado/assado: 163 kcal | prot 28.6g | carb 0g   | gord 4.7g | fibra 0g
Frango peito cozido:          159 kcal | prot 28.8g | carb 0g   | gord 4.2g | fibra 0g
Frango peito frito:           215 kcal | prot 25.8g | carb 3.5g | gord 10.5g| fibra 0g
Carne bovina grelhada (patinho): 219 kcal | prot 27.5g | carb 0g | gord 11.5g | fibra 0g
Carne bovina moída refogada:  252 kcal | prot 20.7g | carb 2.0g | gord 18.5g| fibra 0g
Carne bovina cozida:          185 kcal | prot 24.5g | carb 0g   | gord 9.5g | fibra 0g
Ovo inteiro cozido:           146 kcal | prot 13.3g | carb 0.6g | gord 9.7g | fibra 0g
Ovo inteiro mexido (c/ óleo):  171 kcal | prot 11.9g | carb 1.4g | gord 13.0g| fibra 0g
Pão francês:                  300 kcal | prot 8.0g  | carb 58.6g| gord 3.1g | fibra 2.3g
Pão de forma integral:        269 kcal | prot 9.5g  | carb 48.0g| gord 4.8g | fibra 5.5g
Batata inglesa cozida:         52 kcal | prot 1.2g  | carb 11.9g| gord 0.1g | fibra 1.8g
Batata-doce cozida:            77 kcal | prot 0.6g  | carb 18.4g| gord 0.1g | fibra 2.2g
Batata frita (óleo):          275 kcal | prot 3.2g  | carb 36.0g| gord 13.5g| fibra 3.2g
Macarrão cozido:              148 kcal | prot 5.0g  | carb 30.5g| gord 0.8g | fibra 1.8g
Macarrão integral cozido:     124 kcal | prot 4.7g  | carb 26.0g| gord 0.8g | fibra 4.5g
Pão de queijo (unidade 30g):  314 kcal | prot 7.0g  | carb 42.0g| gord 13.0g| fibra 0.5g
Banana nanica:                  92 kcal | prot 1.3g  | carb 23.8g| gord 0.1g | fibra 1.9g
Maçã com casca:                56 kcal | prot 0.3g  | carb 15.2g| gord 0.0g | fibra 1.4g
Laranja (sem casca):            49 kcal | prot 0.9g  | carb 12.5g| gord 0.1g | fibra 2.4g
Mamão:                         40 kcal | prot 0.5g  | carb 10.4g| gord 0.1g | fibra 1.8g
Leite integral:                 61 kcal | prot 3.2g  | carb 4.7g | gord 3.2g | fibra 0g
Leite desnatado:                35 kcal | prot 3.4g  | carb 4.7g | gord 0.2g | fibra 0g
Iogurte natural integral:       66 kcal | prot 4.2g  | carb 5.4g | gord 3.0g | fibra 0g
Queijo mussarela:              289 kcal | prot 18.2g | carb 3.0g | gord 22.5g| fibra 0g
Queijo minas frescal:          144 kcal | prot 8.5g  | carb 3.7g | gord 10.6g| fibra 0g
Manteiga:                      726 kcal | prot 0.6g  | carb 0g   | gord 80.5g| fibra 0g
Azeite de oliva:               884 kcal | prot 0g    | carb 0g   | gord 100g | fibra 0g
Óleo de soja/girassol:         884 kcal | prot 0g    | carb 0g   | gord 100g | fibra 0g
Açúcar refinado:               387 kcal | prot 0g    | carb 99.9g| gord 0g   | fibra 0g
Aveia em flocos:               394 kcal | prot 13.9g | carb 66.6g| gord 8.5g | fibra 9.1g
Tapioca (goma):                354 kcal | prot 0.2g  | carb 88.0g| gord 0g   | fibra 0g
Café preto:                      2 kcal | prot 0.1g  | carb 0g   | gord 0g   | fibra 0g
Suco de laranja natural:        45 kcal | prot 0.7g  | carb 10.4g| gord 0.2g | fibra 0.2g

=== PORÇÕES TÍPICAS BRASILEIRAS ===
"prato de arroz" (colher de servir grande)  = 150-180g → 200-230 kcal
"concha de feijão" (com caldo)              = 80-100g  → 65-80 kcal
"filé de frango pequeno"                    = 100-120g → 165-195 kcal
"filé de frango médio"                      = 150-180g → 245-295 kcal
"filé de frango grande"                     = 200-250g → 326-408 kcal
"bife médio"                                = 140-160g → 305-350 kcal
"pão francês" (1 unidade)                   = 50g      → 150 kcal
"fatia de pão de forma" (1 unidade)         = 25g      → 67 kcal
"ovo" (1 unidade inteiro)                   = 50g      → 73 kcal
"colher de sopa de azeite" (1 col.)         = 10-13ml  → 88-115 kcal
"colher de chá de manteiga" (1 col.)        = 5g       → 36 kcal
"colher de sopa de açúcar" (1 col.)         = 10-15g   → 39-58 kcal

=== REGRAS OBRIGATÓRIAS ===
1. USE os valores da tabela acima quando o alimento for reconhecido — não invente valores
2. Calcule macros TOTAIS para a porção informada (NÃO por 100g)
3. Quando quantidade for vaga, use as porções típicas acima; ajuste pelo contexto do usuário
4. Diferencie método de preparo: grelhado ≠ frito ≠ cozido (impacta calorias)
5. Para pratos compostos, liste cada ingrediente separadamente
6. confidence: 1.0 (alimento na tabela, porção exata) | 0.85 (alimento na tabela, porção estimada) | 0.6 (estimativa sem referência direta)
7. Use gramas (g) como padrão; ml para líquidos; un para unidades contáveis
"""

_USER_TEMPLATE = "Contexto do usuário: {user_context}\n\nDescrição da refeição: {description}"

_CONFIDENCE_THRESHOLD = 0.6


class MealParser:
    def __init__(self, client: GeminiClient) -> None:
        self._client = client

    async def parse(
        self,
        description: str,
        user_context: str = "sem contexto específico",
    ) -> MealAnalysisResponse:
        user_msg = _USER_TEMPLATE.format(
            user_context=user_context,
            description=description,
        )

        try:
            raw = await self._client.generate_text(
                user_msg,
                use_cache=True,
                system=_SYSTEM_PROMPT,
            )
            data = extract_json_from_ai_response(raw)
        except json.JSONDecodeError as exc:
            logger.error("Groq retornou JSON inválido para análise de texto: %s", exc)
            raise ValueError("A IA não conseguiu analisar a descrição da refeição.") from exc

        items = [ParsedFoodItem(**item) for item in data]
        low_confidence = any(it.confidence < _CONFIDENCE_THRESHOLD for it in items)

        return MealAnalysisResponse(items=items, low_confidence=low_confidence)

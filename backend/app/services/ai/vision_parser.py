from __future__ import annotations

import base64
import json
import logging

from app.schemas.ai import MealAnalysisResponse, ParsedFoodItem
from app.services.ai.gemini_client import GeminiClient
from app.services.ai.utils import extract_json_from_ai_response

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """Você é um nutricionista analisando fotos de refeições brasileiras. \
Identifique todos os alimentos visíveis e estime as porções com base em referências visuais.

RETORNE APENAS JSON VÁLIDO. Sem markdown, sem texto adicional.

Formato obrigatório:
[
  {
    "food_name": "nome do alimento em português",
    "quantity": 150,
    "unit": "g",
    "calories": 200,
    "protein": 8.0,
    "carbs": 30.0,
    "fat": 5.0,
    "fiber": 2.0,
    "confidence": 0.75
  }
]

=== TABELA NUTRICIONAL DE REFERÊNCIA — TACO (valores por 100g, já cozido/preparado) ===
Arroz branco cozido:         128 kcal | prot 2.5g  | carb 28.1g | gord 0.2g | fibra 1.6g
Arroz integral cozido:       124 kcal | prot 2.6g  | carb 25.8g | gord 1.0g | fibra 2.7g
Feijão carioca cozido:        76 kcal | prot 4.8g  | carb 13.6g | gord 0.5g | fibra 8.5g
Feijão preto cozido:          77 kcal | prot 4.5g  | carb 14.0g | gord 0.5g | fibra 8.4g
Frango peito grelhado/assado: 163 kcal | prot 28.6g | carb 0g   | gord 4.7g | fibra 0g
Frango peito frito:           215 kcal | prot 25.8g | carb 3.5g | gord 10.5g| fibra 0g
Carne bovina grelhada (patinho): 219 kcal | prot 27.5g | carb 0g | gord 11.5g | fibra 0g
Carne bovina moída refogada:  252 kcal | prot 20.7g | carb 2.0g | gord 18.5g| fibra 0g
Ovo inteiro cozido:           146 kcal | prot 13.3g | carb 0.6g | gord 9.7g | fibra 0g
Pão francês:                  300 kcal | prot 8.0g  | carb 58.6g| gord 3.1g | fibra 2.3g
Batata inglesa cozida:         52 kcal | prot 1.2g  | carb 11.9g| gord 0.1g | fibra 1.8g
Batata frita (óleo):          275 kcal | prot 3.2g  | carb 36.0g| gord 13.5g| fibra 3.2g
Macarrão cozido:              148 kcal | prot 5.0g  | carb 30.5g| gord 0.8g | fibra 1.8g
Banana nanica:                  92 kcal | prot 1.3g  | carb 23.8g| gord 0.1g | fibra 1.9g
Leite integral:                 61 kcal | prot 3.2g  | carb 4.7g | gord 3.2g | fibra 0g
Iogurte natural integral:       66 kcal | prot 4.2g  | carb 5.4g | gord 3.0g | fibra 0g
Queijo mussarela:              289 kcal | prot 18.2g | carb 3.0g | gord 22.5g| fibra 0g
Azeite de oliva:               884 kcal | prot 0g    | carb 0g   | gord 100g | fibra 0g
Aveia em flocos:               394 kcal | prot 13.9g | carb 66.6g| gord 8.5g | fibra 9.1g

=== CALIBRAÇÃO VISUAL DE PORÇÕES ===
Prato raso padrão brasileiro (26-28cm de diâmetro):
- Arroz cobrindo ¼ do prato = ~150g → 192 kcal
- Arroz cobrindo ⅓ do prato = ~200g → 256 kcal
- Proteína (frango/carne) cobrindo ¼ do prato = ~130-160g
- Feijão/caldo cobrindo ¼ do prato = ~80-100g
- Salada crua cobrindo metade do prato = ~80-120g

Espessura de proteínas:
- Bife/frango fino (~1cm): 80-100g
- Bife/frango médio (~1.5-2cm): 130-160g
- Bife/frango grosso (~2.5-3cm): 180-220g

Outros referências:
- Tigela de 300ml: sopa ~250g, cereal/granola ~60g
- Copo americano (200ml): leite/suco = 200ml
- Xícara de café (50ml): = 50ml leite + café
- Pão francês (1 unidade visível) = ~50g → 150 kcal
- Ovo inteiro = ~50g → 73 kcal

=== REGRAS OBRIGATÓRIAS ===
1. USE os valores da tabela acima para calcular macros — não estime macros do zero
2. Baseie as porções no que é visível: tamanho relativo ao prato, espessura, comparação com utensílios
3. Calcule macros TOTAIS para a porção estimada (NÃO por 100g)
4. Diferencie métodos de preparo visíveis: grelhado, frito, cozido, assado
5. confidence: 0.9+ (claramente identificado, porção estimada com referência) | 0.7 (identificado, porção incerta) | 0.5 (difícil de identificar)
6. Liste cada alimento separadamente, mesmo que sejam componentes do mesmo prato
7. Considere o contexto do usuário ao calibrar porções típicas
"""

_USER_TEMPLATE = (
    "Contexto do usuário: {user_context}\n\n"
    "Analise a foto da refeição e identifique todos os alimentos visíveis com suas estimativas de porção e macros."
)

_CONFIDENCE_THRESHOLD = 0.6


class VisionParser:
    def __init__(self, client: GeminiClient) -> None:
        self._client = client

    async def parse_base64(
        self,
        image_base64: str,
        mime_type: str = "image/jpeg",
        user_context: str = "sem contexto específico",
    ) -> MealAnalysisResponse:
        try:
            image_bytes = base64.b64decode(image_base64)
        except Exception as exc:
            raise ValueError("Imagem base64 inválida.") from exc

        user_msg = _USER_TEMPLATE.format(user_context=user_context)

        try:
            raw = await self._client.generate_with_image(
                user_msg,
                image_bytes,
                mime_type,
                system=_SYSTEM_PROMPT,
            )
            data = extract_json_from_ai_response(raw)
        except json.JSONDecodeError as exc:
            logger.error("Groq retornou JSON inválido para análise de imagem: %s", exc)
            raise ValueError("A IA não conseguiu analisar a imagem da refeição.") from exc

        items = [ParsedFoodItem(**item) for item in data]
        low_confidence = any(it.confidence < _CONFIDENCE_THRESHOLD for it in items)

        return MealAnalysisResponse(items=items, low_confidence=low_confidence)

from __future__ import annotations

import json
import re


def extract_json_from_ai_response(text: str) -> list[dict[str, object]]:
    """Extrai lista JSON da resposta do Gemini, tolerante a blocos de markdown."""
    text = text.strip()
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    return json.loads(text.strip())  # type: ignore[no-any-return]

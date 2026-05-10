"""Smoke tests — valida Groq (texto e visão) e banco de alimentos em dev."""
from __future__ import annotations

import asyncio
import base64
import os
from pathlib import Path

import asyncpg


# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------
def _load_env() -> None:
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())


_load_env()

GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
DB_URL = "postgresql://caloria:caloria@localhost:5432/caloria_db"

PASS = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))
    icon = PASS if ok else FAIL
    print(f"  {icon} {name}" + (f" — {detail}" if detail else ""))


# --------------------------------------------------------------------------
# Testes Groq — Texto
# --------------------------------------------------------------------------
async def test_groq_texto() -> None:
    print("\n[1] Groq — Texto (llama-3.3-70b-versatile)")
    from groq import AsyncGroq

    client = AsyncGroq(api_key=GROQ_KEY)

    # Teste básico
    resp = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": "Responda apenas: OK"}],
        temperature=0,
        max_tokens=5,
    )
    text = resp.choices[0].message.content or ""
    check("Resposta recebida", bool(text), repr(text))

    # Teste de análise de refeição (simula MealParser)
    resp2 = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{
            "role": "user",
            "content": (
                "Liste os macros de: 200g de arroz branco cozido e 150g de frango grelhado. "
                'Responda SOMENTE JSON: [{"alimento": "...", "cal": 0, "prot": 0, "carbs": 0, "fat": 0}]'
            ),
        }],
        temperature=0.1,
        response_format={"type": "json_object"},
    )
    import json
    body = resp2.choices[0].message.content or "{}"
    data = json.loads(body)
    check("JSON estruturado retornado", isinstance(data, (dict, list)), f"{len(str(data))} chars")
    tokens_in = resp2.usage.prompt_tokens if resp2.usage else 0
    tokens_out = resp2.usage.completion_tokens if resp2.usage else 0
    check("Uso de tokens registrado", tokens_in > 0, f"in={tokens_in} out={tokens_out}")


# --------------------------------------------------------------------------
# Testes Groq — Visão
# --------------------------------------------------------------------------
def _make_png(width: int = 100, height: int = 100) -> bytes:
    """Gera PNG sólido RGB usando apenas stdlib (sem Pillow)."""
    import struct
    import zlib

    def chunk(tag: bytes, data: bytes) -> bytes:
        payload = tag + data
        return struct.pack(">I", len(data)) + payload + struct.pack(">I", zlib.crc32(payload) & 0xFFFFFFFF)

    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    # Cor laranja (255, 165, 0) para parecer comida
    row = b"\x00" + b"\xFF\xA5\x00" * width
    idat = chunk(b"IDAT", zlib.compress(row * height))
    iend = chunk(b"IEND", b"")
    return b"\x89PNG\r\n\x1a\n" + ihdr + idat + iend


async def test_groq_visao() -> None:
    print("\n[2] Groq — Visão (llama-4-scout-17b)")

    img_bytes = _make_png(100, 100)
    b64 = base64.b64encode(img_bytes).decode()

    from groq import AsyncGroq
    client = AsyncGroq(api_key=GROQ_KEY)

    try:
        resp = await client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                    {"type": "text", "text": "Descreva esta imagem em 1 frase curta."},
                ],
            }],
            temperature=0.1,
            max_tokens=60,
        )
        text = resp.choices[0].message.content or ""
        check("Modelo de visão respondeu", bool(text), repr(text[:80]))
    except Exception as e:
        check("Modelo de visão respondeu", False, str(e)[:100])


# --------------------------------------------------------------------------
# Testes banco — foods
# --------------------------------------------------------------------------
async def test_banco_foods() -> None:
    print("\n[3] Banco de Alimentos (PostgreSQL)")
    conn = await asyncpg.connect(DB_URL)

    # Contagem total
    total = await conn.fetchval("SELECT COUNT(*) FROM foods")
    check("Total de alimentos", total > 40000, f"{total:,} registros")

    # Busca fuzzy por pg_trgm
    rows = await conn.fetch(
        "SELECT name, calories_100g FROM foods WHERE search_text %>> $1 ORDER BY similarity(search_text, $1) DESC LIMIT 5",
        "arroz branco cozido",
    )
    check("Busca fuzzy funciona", len(rows) > 0, f"{len(rows)} resultados")
    if rows:
        check("Resultado relevante", "arroz" in rows[0]["name"].lower(), rows[0]["name"])

    # Busca por categoria
    cats = await conn.fetch(
        "SELECT category, COUNT(*) as n FROM foods GROUP BY category ORDER BY n DESC LIMIT 5"
    )
    check("Categorias presentes", len(cats) > 1, " | ".join(f"{r['category']}={r['n']}" for r in cats))

    # Alimentos TACO presentes
    taco = await conn.fetchval("SELECT COUNT(*) FROM foods WHERE source = 'taco'")
    check("TACO importado", taco >= 200, f"{taco} alimentos TACO")

    # Alimentos sem calorias
    sem_cal = await conn.fetchval("SELECT COUNT(*) FROM foods WHERE calories_100g = 0")
    check("Poucos alimentos com 0 cal", sem_cal < total * 0.05, f"{sem_cal} com cal=0")

    await conn.close()


# --------------------------------------------------------------------------
# Testes GeminiClient (wrapper Groq)
# --------------------------------------------------------------------------
async def test_ai_client() -> None:
    print("\n[4] AIClient (GeminiClient → Groq)")
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

    os.environ["GROQ_API_KEY"] = GROQ_KEY
    os.environ["GEMINI_API_KEY"] = ""
    os.environ["REDIS_URL"] = "redis://localhost:6379/0"
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://caloria:caloria@localhost:5432/caloria_db"

    from app.services.ai.gemini_client import GeminiClient
    client = GeminiClient()

    # generate_text sem cache
    result = await client.generate_text("Diga apenas: GROQ_OK", use_cache=False)
    check("generate_text funciona", bool(result), repr(result[:50]))

    # generate_text com system prompt
    result2 = await client.generate_text(
        "Qual é a capital do Brasil?",
        system="Você responde em uma palavra.",
        use_cache=False,
    )
    check("System prompt funciona", "brasília" in result2.lower() or "brasilia" in result2.lower(), repr(result2[:50]))


# --------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------
async def main() -> None:
    print("=" * 55)
    print("  SMOKE TESTS — CalorIA Dev")
    print("=" * 55)

    await test_groq_texto()
    await test_groq_visao()
    await test_banco_foods()
    await test_ai_client()

    passed = sum(1 for _, ok, _ in results if ok)
    failed = sum(1 for _, ok, _ in results if not ok)

    print("\n" + "=" * 55)
    print(f"  Resultado: {passed} ok  |  {failed} falhou  |  {len(results)} total")
    print("=" * 55)

    if failed:
        print("\nFalhas:")
        for name, ok, detail in results:
            if not ok:
                print(f"  ✗ {name}: {detail}")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())

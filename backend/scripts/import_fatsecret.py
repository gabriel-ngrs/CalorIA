"""Importa alimentos brasileiros do FatSecret Platform API (OAuth 1.0).

Busca por termos alimentares brasileiros usando a API foods.search e importa
os resultados com dados nutricionais completos via foods.get.

Limite gratuito: 5.000 chamadas/dia. O script respeita esse limite e pode
ser executado em múltiplos dias para completar a importação.

────────────────────────────────────────────────────
USO:

    cd backend

    # Importa com as credenciais do .env
    python scripts/import_fatsecret.py

    # Limita o número de alimentos importados
    python scripts/import_fatsecret.py --limit 2000

    # Modo seco: mostra o que seria importado sem salvar
    python scripts/import_fatsecret.py --dry-run

    # Força reimportação (apaga registros source=fatsecret antes)
    python scripts/import_fatsecret.py --force

────────────────────────────────────────────────────
VARIÁVEIS DE AMBIENTE necessárias:

    FATSECRET_KEY    → Consumer Key (OAuth 1.0)
    FATSECRET_SECRET → Consumer Secret (OAuth 1.0)
    DATABASE_URL     → postgresql+asyncpg://...

    Para rodar fora do Docker:
    DATABASE_URL=postgresql+asyncpg://caloria:caloria@localhost:5432/caloria_db
────────────────────────────────────────────────────
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import hashlib
import hmac
import logging
import os
import random
import string
import time
import urllib.parse
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from sqlalchemy import delete, select
from sqlalchemy import text as sa_text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models.food import Food

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Termos de busca em inglês — plano free FatSecret só tem base US
# Inclui alimentos equivalentes ao cardápio brasileiro
# ---------------------------------------------------------------------------
SEARCH_TERMS = [
    # Grains & cereals
    "white rice cooked", "brown rice cooked", "black beans cooked",
    "pinto beans cooked", "lentils cooked", "chickpeas cooked",
    "corn", "cornmeal", "cassava flour", "wheat flour", "oats",
    "quinoa", "couscous", "pasta cooked", "whole wheat pasta",
    # Poultry
    "grilled chicken breast", "chicken breast", "chicken thigh",
    "chicken drumstick", "chicken wing", "roasted chicken", "turkey breast",
    # Beef
    "ground beef", "beef steak", "beef sirloin", "beef tenderloin",
    "beef chuck", "beef ribs", "beef liver", "beef heart",
    # Pork & processed meats
    "pork sausage", "smoked sausage", "ham", "prosciutto",
    "bacon", "pepperoni", "salami", "hot dog",
    # Fish & seafood
    "canned tuna", "canned sardine", "salmon", "tilapia",
    "cod fish", "shrimp", "crab", "squid",
    # Eggs
    "boiled egg", "fried egg", "scrambled eggs", "poached egg",
    # Dairy
    "whole milk", "skim milk", "semi-skim milk",
    "mozzarella cheese", "cheddar cheese", "cottage cheese",
    "cream cheese", "plain yogurt", "greek yogurt",
    "butter", "margarine", "heavy cream", "sour cream",
    # Fruits
    "banana", "apple", "orange", "papaya", "mango", "pineapple",
    "grapes", "strawberry", "watermelon", "cantaloupe", "pear",
    "peach", "guava", "avocado", "coconut", "passion fruit",
    "acai", "lemon", "lime", "kiwi", "plum",
    # Vegetables
    "lettuce", "tomato", "onion", "garlic", "potato", "sweet potato",
    "carrot", "beet", "zucchini", "eggplant", "broccoli",
    "kale", "spinach", "arugula", "cucumber", "bell pepper",
    "chayote", "cassava", "yam", "okra", "green beans", "peas",
    "corn on cob", "palm heart", "cabbage", "cauliflower",
    # Breads & bakery
    "french bread", "white bread", "whole wheat bread",
    "cheese bread", "crackers", "cornstarch cookies",
    "lasagna", "pizza", "tapioca",
    # Brazilian dishes
    "feijoada", "moqueca", "coxinha", "brigadeiro", "pudim",
    "pao de queijo",
    # Beverages
    "orange juice", "grape juice", "coconut water",
    "cola soda", "beer", "red wine", "white wine", "coffee",
    # Nuts & seeds
    "peanuts", "brazil nuts", "cashew nuts", "almonds",
    "walnuts", "sunflower seeds", "pumpkin seeds", "chia seeds",
    # Condiments & oils
    "mayonnaise", "ketchup", "tomato sauce", "olive oil",
    "soybean oil", "sunflower oil", "sugar", "honey", "jam",
    # Snacks & sweets
    "chocolate", "milk chocolate", "dark chocolate",
    "potato chips", "popcorn", "granola bar", "cereal bar",
    # Prepared foods
    "hamburger", "chicken nuggets", "french fries",
    "beef stew", "chicken soup", "vegetable soup",
]

# ---------------------------------------------------------------------------
# Categorias FatSecret → categorias CalorIA
# ---------------------------------------------------------------------------
CATEGORY_MAP = {
    "Baked Products": "graos_cereais",
    "Beef Products": "carnes",
    "Beverages": "bebidas",
    "Breakfast Cereals": "graos_cereais",
    "Dairy and Egg Products": "laticinios",
    "Fast Foods": "refeicoes_prontas",
    "Fats and Oils": "gorduras_oleos",
    "Finfish and Shellfish Products": "peixes_frutos_mar",
    "Fruits and Fruit Juices": "frutas",
    "Grain and Pasta Products": "graos_cereais",
    "Lamb, Veal, and Game Products": "carnes",
    "Legumes and Legume Products": "leguminosas",
    "Meals, Entrees, and Side Dishes": "refeicoes_prontas",
    "Nut and Seed Products": "oleaginosas",
    "Pork Products": "carnes",
    "Poultry Products": "carnes",
    "Restaurant Foods": "refeicoes_prontas",
    "Sausages and Luncheon Meats": "carnes",
    "Snacks": "snacks",
    "Soups, Sauces, and Gravies": "molhos_temperos",
    "Spices and Herbs": "temperos",
    "Sweets": "doces",
    "Vegetables and Vegetable Products": "verduras_legumes",
}


# ---------------------------------------------------------------------------
# OAuth 1.0 helpers
# ---------------------------------------------------------------------------

def _oauth_sign(method: str, url: str, params: dict, key: str, secret: str) -> str:
    """Gera OAuth 1.0 signature (HMAC-SHA1)."""
    sorted_params = "&".join(
        f"{urllib.parse.quote(str(k), safe='')}={urllib.parse.quote(str(v), safe='')}"
        for k, v in sorted(params.items())
    )
    base = "&".join([
        urllib.parse.quote(method.upper(), safe=""),
        urllib.parse.quote(url, safe=""),
        urllib.parse.quote(sorted_params, safe=""),
    ])
    signing_key = f"{urllib.parse.quote(secret, safe='')}&"
    signature = hmac.new(signing_key.encode(), base.encode(), hashlib.sha1)
    return base64.b64encode(signature.digest()).decode()


def _build_params(method: str, url: str, extra: dict, key: str, secret: str) -> dict:
    """Monta os parâmetros OAuth completos com assinatura."""
    nonce = "".join(random.choices(string.ascii_letters + string.digits, k=16))
    params = {
        "oauth_consumer_key": key,
        "oauth_nonce": nonce,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_version": "1.0",
        **extra,
    }
    params["oauth_signature"] = _oauth_sign(method, url, params, key, secret)
    return params


# ---------------------------------------------------------------------------
# FatSecret API client
# ---------------------------------------------------------------------------

BASE_URL = "https://platform.fatsecret.com/rest/server.api"


async def _api_call(client: httpx.AsyncClient, key: str, secret: str, method: str, extra: dict) -> dict:
    params = _build_params("GET", BASE_URL, {"method": method, "format": "json", **extra}, key, secret)
    resp = await client.get(BASE_URL, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _parse_food(food_data: dict) -> dict | None:
    """Extrai nutrientes de um alimento do FatSecret. Retorna None se inválido."""
    name = food_data.get("food_name", "").strip()
    if not name:
        return None

    servings = food_data.get("servings", {})
    serving_list = servings.get("serving", [])
    if isinstance(serving_list, dict):
        serving_list = [serving_list]

    # Prefere serving de 100g; fallback para o primeiro
    serving = next(
        (s for s in serving_list if "100" in s.get("serving_description", "")),
        serving_list[0] if serving_list else None,
    )
    if not serving:
        return None

    def _f(key: str) -> float:
        try:
            return float(serving.get(key) or 0)
        except (ValueError, TypeError):
            return 0.0

    calories = _f("calories")
    protein = _f("protein")
    carbs = _f("carbohydrate")
    fat = _f("fat")

    if calories <= 0 or protein < 0 or carbs < 0 or fat < 0:
        return None
    if calories > 900 and fat < 1:
        return None

    # Escala para 100g se necessário
    metric_serving_amount = float(serving.get("metric_serving_amount") or 100)
    if metric_serving_amount > 0 and abs(metric_serving_amount - 100) > 1:
        factor = 100.0 / metric_serving_amount
        calories *= factor
        protein *= factor
        carbs *= factor
        fat *= factor

    category_raw = food_data.get("food_type", "")
    category = CATEGORY_MAP.get(category_raw, "outros")

    search_text = name.lower()

    return {
        "name": name,
        "aliases": [],
        "category": category,
        "preparation": None,
        "notes": None,
        "source": "fatsecret",
        "external_id": str(food_data.get("food_id", "")),
        "search_text": search_text,
        "calories_100g": round(calories, 2),
        "protein_100g": round(protein, 2),
        "carbs_100g": round(carbs, 2),
        "fat_100g": round(fat, 2),
        "fiber_100g": round(_f("fiber"), 2),
        "sodium_100g": round(_f("sodium") / 1000, 4) if serving.get("sodium") else None,
        "sugar_100g": round(_f("sugar"), 2) if serving.get("sugar") else None,
        "saturated_fat_100g": round(_f("saturated_fat"), 2) if serving.get("saturated_fat") else None,
    }


# ---------------------------------------------------------------------------
# Main import logic
# ---------------------------------------------------------------------------

async def import_fatsecret(dry_run: bool, force: bool, limit: int) -> None:
    key = os.getenv("FATSECRET_KEY")
    secret = os.getenv("FATSECRET_SECRET")
    db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://caloria:caloria@localhost:5432/caloria_db")

    if not key or not secret:
        log.error("FATSECRET_KEY e FATSECRET_SECRET devem estar no .env")
        return

    # Corrige URL para asyncpg
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(db_url, echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as session:
        if force and not dry_run:
            log.info("Removendo registros source=fatsecret existentes...")
            await session.execute(delete(Food).where(Food.source == "fatsecret"))
            await session.commit()

        seen_ids: set[str] = set()
        to_insert: list[dict] = []
        api_calls = 0
        skipped = 0

        async with httpx.AsyncClient() as client:
            for term in SEARCH_TERMS:
                if len(to_insert) + len(seen_ids) >= limit:
                    break

                log.info(f"Buscando: '{term}'...")

                try:
                    result = await _api_call(
                        client, key, secret, "foods.search",
                        {"search_expression": term, "max_results": "50"},
                    )
                    api_calls += 1
                except Exception as e:
                    log.warning(f"  Erro na busca '{term}': {e}")
                    await asyncio.sleep(2)
                    continue

                foods = result.get("foods", {}).get("food", [])
                if isinstance(foods, dict):
                    foods = [foods]
                if not foods:
                    log.info(f"  Nenhum resultado para '{term}'")
                    continue

                food_ids = [f["food_id"] for f in foods if f.get("food_id") and f["food_id"] not in seen_ids]
                log.info(f"  {len(food_ids)} alimentos encontrados (novos)")

                for food_id in food_ids:
                    if len(to_insert) >= limit:
                        break

                    seen_ids.add(food_id)

                    try:
                        detail = await _api_call(
                            client, key, secret, "food.get.v4",
                            {"food_id": food_id},
                        )
                        api_calls += 1
                    except Exception as e:
                        log.warning(f"  Erro ao buscar food_id={food_id}: {e}")
                        await asyncio.sleep(1)
                        continue

                    food_data = detail.get("food", {})
                    parsed = _parse_food(food_data)

                    if parsed is None:
                        skipped += 1
                        continue

                    to_insert.append(parsed)

                    if len(to_insert) % 100 == 0:
                        log.info(f"  {len(to_insert)} alimentos prontos para inserção...")

                    # Pausa entre chamadas para respeitar rate limit
                    await asyncio.sleep(0.2)

                # Pausa entre termos de busca
                await asyncio.sleep(0.5)

        log.info(f"\nTotal de chamadas API: {api_calls}")
        log.info(f"Alimentos válidos: {len(to_insert)}")
        log.info(f"Alimentos descartados (sem dados): {skipped}")

        if dry_run or not to_insert:
            log.info("Modo seco — nada foi salvo." if dry_run else "Nada para inserir.")
            await engine.dispose()
            return

        log.info("Inserindo no banco...")
        stmt = pg_insert(Food).values(to_insert)
        stmt = stmt.on_conflict_do_nothing(index_elements=["name"])
        await session.execute(stmt)
        await session.commit()

        # Atualiza índice trigrama
        await session.execute(sa_text("""
            UPDATE foods
            SET search_text = lower(name || ' ' || array_to_string(aliases, ' '))
            WHERE source = 'fatsecret'
        """))
        await session.commit()

        log.info(f"Importação concluída: {len(to_insert)} alimentos do FatSecret inseridos.")

    await engine.dispose()


def main() -> None:
    ap = argparse.ArgumentParser(description="Importa alimentos do FatSecret Platform API")
    ap.add_argument("--dry-run", action="store_true", help="Não salva nada no banco")
    ap.add_argument("--force", action="store_true", help="Remove registros fatsecret existentes antes")
    ap.add_argument("--limit", type=int, default=5000, help="Máximo de alimentos a importar (padrão: 5000)")
    args = ap.parse_args()

    # Carrega .env se existir
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

    asyncio.run(import_fatsecret(args.dry_run, args.force, args.limit))


if __name__ == "__main__":
    main()

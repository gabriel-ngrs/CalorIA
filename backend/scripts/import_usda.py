"""Importa Foundation Foods do USDA FoodData Central para a tabela foods.

Foundation Foods (~2.200 alimentos inteiros com dados analíticos de alta qualidade)
são alimentos básicos sem processamento, ideal para complementar o banco TACO.

Chave de API gratuita: https://fdc.nal.usda.gov/api-guide.html
Configure USDA_API_KEY no .env ou passe via --api-key.

Uso:
    cd backend

    # Importa todos os Foundation Foods (dry-run)
    python scripts/import_usda.py --api-key SUA_CHAVE --dry-run

    # Importa até 200 alimentos
    python scripts/import_usda.py --api-key SUA_CHAVE --limit 200

    # Retoma da página 5
    python scripts/import_usda.py --api-key SUA_CHAVE --start-page 5
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys
import unicodedata
from pathlib import Path

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import AsyncSessionLocal  # noqa: E402
from app.models.food import Food  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

USDA_API_BASE = "https://api.nal.usda.gov/fdc/v1"
PAGE_SIZE = 200
REQUEST_TIMEOUT = 30.0

# Mapeamento de nutrientes USDA → campos do modelo Food
_NUTRIENT_MAP: dict[str, str] = {
    "Energy": "calories",
    "Protein": "protein",
    "Carbohydrate, by difference": "carbs",
    "Total lipid (fat)": "fat",
    "Fiber, total dietary": "fiber",
    "Sodium, Na": "sodium",           # mg — dividir por 1000 para g
    "Sugars, total including NLEA": "sugar",
    "Fatty acids, total saturated": "saturated_fat",
}

# Dicionário de tradução EN → PT para nomes comuns (complementa o mapeamento automático)
_EN_TO_PT: dict[str, str] = {
    "Beef": "Carne bovina",
    "Chicken": "Frango",
    "Pork": "Porco",
    "Turkey": "Peru",
    "Salmon": "Salmão",
    "Tuna": "Atum",
    "Tilapia": "Tilápia",
    "Shrimp": "Camarão",
    "Egg": "Ovo",
    "Milk": "Leite",
    "Cheese": "Queijo",
    "Butter": "Manteiga",
    "Yogurt": "Iogurte",
    "Rice": "Arroz",
    "Pasta": "Macarrão",
    "Bread": "Pão",
    "Potato": "Batata",
    "Tomato": "Tomate",
    "Carrot": "Cenoura",
    "Broccoli": "Brócolis",
    "Spinach": "Espinafre",
    "Lettuce": "Alface",
    "Onion": "Cebola",
    "Garlic": "Alho",
    "Apple": "Maçã",
    "Banana": "Banana",
    "Orange": "Laranja",
    "Strawberry": "Morango",
    "Avocado": "Abacate",
    "Mango": "Manga",
    "Watermelon": "Melancia",
    "Grape": "Uva",
    "Lemon": "Limão",
    "Pineapple": "Abacaxi",
    "Beans": "Feijão",
    "Lentils": "Lentilha",
    "Oats": "Aveia",
    "Corn": "Milho",
    "Olive oil": "Azeite de oliva",
    "Coconut oil": "Óleo de coco",
    "Almonds": "Amêndoas",
    "Walnuts": "Nozes",
    "Cashews": "Castanha de caju",
    "Peanuts": "Amendoim",
    "Sugar": "Açúcar",
    "Honey": "Mel",
    "Coffee": "Café",
    "Tea": "Chá",
}


def _normalize(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


def _build_search_text(name: str, aliases: list[str]) -> str:
    return " ".join([name] + aliases).lower()


def _translate_name(en_name: str) -> str:
    """Tenta traduzir nome do inglês para português via dicionário de mapeamento."""
    for en, pt in _EN_TO_PT.items():
        if en.lower() in en_name.lower():
            # Substitui o termo em inglês pelo equivalente em português
            return en_name.replace(en, pt)
    return en_name  # mantém em inglês se não houver mapeamento


def _extract_nutrients(food_nutrients: list[dict]) -> dict[str, float]:
    """Extrai os nutrientes relevantes da lista retornada pela API USDA."""
    result: dict[str, float] = {
        "calories": 0.0,
        "protein": 0.0,
        "carbs": 0.0,
        "fat": 0.0,
        "fiber": 0.0,
        "sodium": 0.0,
        "sugar": 0.0,
        "saturated_fat": 0.0,
    }

    for item in food_nutrients:
        nutrient = item.get("nutrient", {})
        nutrient_name = nutrient.get("name", "")
        field = _NUTRIENT_MAP.get(nutrient_name)
        if field is None:
            continue

        amount = item.get("amount")
        if amount is None:
            continue

        try:
            value = float(amount)
        except (ValueError, TypeError):
            continue

        # Sódio da USDA vem em mg — converter para g
        if field == "sodium":
            value = value / 1000.0

        result[field] = value

    return result


def _parse_food(item: dict) -> Food | None:
    """Converte um item do USDA FoodData Central em Food."""
    en_name = (item.get("description") or "").strip()
    if not en_name or len(en_name) > 200:
        return None

    nutrients = _extract_nutrients(item.get("foodNutrients") or [])

    # Descarta alimentos sem dados mínimos
    if nutrients["calories"] <= 0:
        return None

    # Descarta valores fisicamente impossíveis
    if (
        nutrients["calories"] > 950
        or nutrients["protein"] > 100
        or nutrients["carbs"] > 100
        or nutrients["fat"] > 100
        or nutrients["sodium"] > 10
    ):
        return None

    pt_name = _translate_name(en_name)
    # Mantém nome em inglês como alias para facilitar busca
    aliases = [en_name] if pt_name != en_name else []

    fdc_id = str(item.get("fdcId", ""))
    category_raw = (item.get("foodCategory") or {}).get("description", "")
    category = _normalize(category_raw)[:50] if category_raw else "outros"

    return Food(
        name=pt_name[:200],
        aliases=aliases,
        category=category,
        preparation=None,
        notes=None,
        source="usda",
        external_id=fdc_id if fdc_id else None,
        search_text=_build_search_text(
            _normalize(pt_name),
            [_normalize(a) for a in aliases],
        ),
        calories_100g=round(nutrients["calories"], 1),
        protein_100g=round(nutrients["protein"], 2),
        carbs_100g=round(nutrients["carbs"], 2),
        fat_100g=round(nutrients["fat"], 2),
        fiber_100g=round(nutrients["fiber"], 2),
        sodium_100g=round(nutrients["sodium"], 3) if nutrients["sodium"] > 0 else None,
        sugar_100g=round(nutrients["sugar"], 2) if nutrients["sugar"] > 0 else None,
        saturated_fat_100g=(
            round(nutrients["saturated_fat"], 2) if nutrients["saturated_fat"] > 0 else None
        ),
    )


async def fetch_page(
    client: httpx.AsyncClient,
    api_key: str,
    page: int,
) -> list[dict]:
    """Busca uma página de Foundation Foods da API USDA com retry."""
    params = {
        "dataType": "Foundation",
        "pageSize": PAGE_SIZE,
        "pageNumber": page,
        "api_key": api_key,
    }
    last_exc: Exception | None = None
    for attempt in range(4):
        if attempt > 0:
            wait = 2 ** attempt
            logger.warning("Tentativa %d/4 para página %d (aguardando %ds)...", attempt + 1, page, wait)
            await asyncio.sleep(wait)
        try:
            resp = await client.get(
                f"{USDA_API_BASE}/foods/list",
                params=params,
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            return resp.json() or []
        except httpx.HTTPError as exc:
            last_exc = exc
    raise last_exc  # type: ignore[misc]


async def import_usda(
    api_key: str,
    limit: int,
    dry_run: bool,
    start_page: int = 1,
) -> None:
    async with AsyncSessionLocal() as db:
        existing_names: set[str] = set(
            row[0] for row in (await db.execute(select(Food.name))).all()
        )
        existing_ext_ids: set[str] = set(
            row[0]
            for row in (
                await db.execute(
                    select(Food.external_id).where(Food.external_id.isnot(None))
                )
            ).all()
        )

        inserted = 0
        skipped_quality = 0
        skipped_duplicate = 0
        page = start_page

        async with httpx.AsyncClient() as client:
            while inserted < limit:
                logger.info("Buscando página %d (importados: %d/%d)...", page, inserted, limit)

                try:
                    items = await fetch_page(client, api_key, page)
                except httpx.HTTPError as exc:
                    logger.error("Erro na API USDA (página %d): %s", page, exc)
                    break

                if not items:
                    logger.info("Sem mais alimentos na API. Total de páginas: %d", page - 1)
                    break

                batch: list[Food] = []
                for item in items:
                    if inserted + len(batch) >= limit:
                        break

                    food = _parse_food(item)
                    if food is None:
                        skipped_quality += 1
                        continue

                    if food.external_id and food.external_id in existing_ext_ids:
                        skipped_duplicate += 1
                        continue

                    if food.name in existing_names:
                        skipped_duplicate += 1
                        continue

                    existing_names.add(food.name)
                    if food.external_id:
                        existing_ext_ids.add(food.external_id)
                    batch.append(food)

                if not batch:
                    page += 1
                    continue

                if not dry_run:
                    db.add_all(batch)
                    await db.commit()

                inserted += len(batch)
                page += 1

        logger.info("─" * 50)
        logger.info("Importação USDA concluída:")
        logger.info("  Importados:            %d", inserted)
        logger.info("  Ignorados (qualidade): %d", skipped_quality)
        logger.info("  Ignorados (duplicata): %d", skipped_duplicate)
        if dry_run:
            logger.info("  [dry-run] Nenhum dado foi salvo.")


def _get_arg(args: list[str], flag: str, default: str | int) -> str | int:
    for i, arg in enumerate(args):
        if arg.startswith(f"{flag}="):
            return arg.split("=", 1)[1]
        if arg == flag and i + 1 < len(args):
            return args[i + 1]
    return default


def main() -> None:
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    api_key = str(_get_arg(args, "--api-key", os.environ.get("USDA_API_KEY", "")))
    limit = int(str(_get_arg(args, "--limit", 10_000)))
    start_page = int(str(_get_arg(args, "--start-page", 1)))

    if not api_key:
        logger.error(
            "USDA_API_KEY não encontrada. Use --api-key CHAVE ou defina USDA_API_KEY no .env."
        )
        sys.exit(1)

    logger.info("Iniciando importação USDA Foundation Foods")
    logger.info(
        "  Limite: %d | página inicial: %d | dry-run: %s",
        limit, start_page, dry_run,
    )
    asyncio.run(import_usda(
        api_key=api_key,
        limit=limit,
        dry_run=dry_run,
        start_page=start_page,
    ))


if __name__ == "__main__":
    main()

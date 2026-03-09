"""Importa produtos brasileiros do Open Food Facts para taco_foods.

Faz download paginado da API pública do OFF filtrando por país Brasil.
Apenas produtos com calorias, proteínas, carboidratos e gorduras preenchidos
são importados — garante qualidade mínima dos dados.

Uso:
    cd backend

    # Importa até 5.000 produtos (padrão)
    python scripts/import_off.py

    # Importa até 50.000 produtos
    python scripts/import_off.py --limit 50000

    # Importa em modo seco (exibe contagens, não salva)
    python scripts/import_off.py --dry-run

    # Força reimportação (remove registros existentes source=openfoodfacts)
    python scripts/import_off.py --force
"""
from __future__ import annotations

import asyncio
import logging
import sys
import unicodedata
from pathlib import Path

import httpx
from sqlalchemy import delete, select, text as sa_text

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import AsyncSessionLocal  # noqa: E402
from app.models.taco_food import TacoFood  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configurações
# ---------------------------------------------------------------------------
OFF_API = "https://world.openfoodfacts.org/cgi/search.pl"
PAGE_SIZE = 500
DEFAULT_LIMIT = 5_000
REQUEST_TIMEOUT = 30.0

# Mapeamento de categorias OFF → categorias internas
_CATEGORY_MAP: dict[str, str] = {
    "en:beverages": "bebidas",
    "en:drinks": "bebidas",
    "en:alcoholic-beverages": "bebidas",
    "en:dairy": "laticinios",
    "en:cheeses": "laticinios",
    "en:yogurts": "laticinios",
    "en:milks": "laticinios",
    "en:meats": "carnes",
    "en:poultry": "carnes",
    "en:fish": "peixes",
    "en:seafood": "peixes",
    "en:fruits": "frutas",
    "en:vegetables": "vegetais",
    "en:cereals": "cereais",
    "en:breads": "paes",
    "en:pastas": "massas",
    "en:legumes": "leguminosas",
    "en:sugary-snacks": "acucares",
    "en:chocolates": "acucares",
    "en:biscuits-and-cakes": "acucares",
    "en:fats": "gorduras",
    "en:oils": "gorduras",
    "en:nuts": "gorduras",
    "en:frozen-foods": "pratos",
    "en:meals": "pratos",
    "en:soups": "pratos",
    "en:fast-foods": "fastfood",
}


def _normalize(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


def _map_category(tags: list[str]) -> str:
    for tag in tags:
        if tag in _CATEGORY_MAP:
            return _CATEGORY_MAP[tag]
    return "outros"


def _build_search_text(name: str, aliases: list[str]) -> str:
    return " ".join([name] + aliases).lower()


def _parse_product(product: dict) -> TacoFood | None:
    """Converte um produto OFF em TacoFood. Retorna None se dados insuficientes."""
    name = (
        product.get("product_name_pt")
        or product.get("product_name")
        or ""
    ).strip()

    if not name or len(name) > 200:
        return None

    nutriments = product.get("nutriments", {})

    try:
        calories = float(nutriments.get("energy-kcal_100g") or nutriments.get("energy_100g", 0) or 0)
        protein = float(nutriments.get("proteins_100g") or 0)
        carbs = float(nutriments.get("carbohydrates_100g") or 0)
        fat = float(nutriments.get("fat_100g") or 0)
        fiber = float(nutriments.get("fiber_100g") or 0)
    except (ValueError, TypeError):
        return None

    # Descarta produtos sem dados nutricionais mínimos
    if calories <= 0 or protein < 0 or carbs < 0 or fat < 0:
        return None

    # Se energy_100g veio em kJ, converte para kcal
    if calories > 900 and not nutriments.get("energy-kcal_100g"):
        calories = calories / 4.184

    barcode = str(product.get("code") or "").strip() or None
    category_tags = product.get("categories_tags") or []
    category = _map_category(category_tags)

    aliases: list[str] = []
    generic = (product.get("generic_name_pt") or product.get("generic_name") or "").strip()
    if generic and generic.lower() != name.lower() and len(generic) <= 200:
        aliases.append(generic)

    return TacoFood(
        name=name,
        aliases=aliases,
        category=category,
        preparation=None,
        notes=None,
        source="openfoodfacts",
        external_id=barcode,
        search_text=_build_search_text(_normalize(name), [_normalize(a) for a in aliases]),
        calories_100g=round(calories, 1),
        protein_100g=round(protein, 2),
        carbs_100g=round(carbs, 2),
        fat_100g=round(fat, 2),
        fiber_100g=round(fiber, 2),
    )


async def fetch_page(client: httpx.AsyncClient, page: int) -> list[dict]:
    """Busca uma página de produtos brasileiros na API do OFF."""
    params = {
        "action": "process",
        "tagtype_0": "countries",
        "tag_contains_0": "contains",
        "tag_0": "brazil",
        "fields": (
            "code,product_name,product_name_pt,generic_name,generic_name_pt,"
            "categories_tags,nutriments"
        ),
        "json": "1",
        "page_size": PAGE_SIZE,
        "page": page,
    }
    resp = await client.get(OFF_API, params=params, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    return data.get("products") or []


async def import_off(limit: int, dry_run: bool, force: bool) -> None:
    async with AsyncSessionLocal() as db:
        if force:
            deleted = await db.execute(
                delete(TacoFood).where(TacoFood.source == "openfoodfacts")
            )
            await db.commit()
            logger.info("Removidos %d registros existentes do Open Food Facts.", deleted.rowcount)

        # Carrega nomes já existentes para evitar duplicatas (unique constraint)
        existing_names: set[str] = set(
            row[0] for row in (await db.execute(select(TacoFood.name))).all()
        )
        existing_barcodes: set[str] = set(
            row[0]
            for row in (
                await db.execute(select(TacoFood.external_id).where(TacoFood.external_id.isnot(None)))
            ).all()
        )

        inserted = 0
        skipped_quality = 0
        skipped_duplicate = 0
        page = 1
        consecutive_empty = 0  # páginas seguidas sem nenhum produto novo

        async with httpx.AsyncClient() as client:
            while inserted < limit:
                logger.info("Buscando página %d (importados: %d/%d)...", page, inserted, limit)

                try:
                    products = await fetch_page(client, page)
                except httpx.HTTPError as exc:
                    logger.error("Erro na API OFF (página %d): %s", page, exc)
                    break

                if not products:
                    logger.info("Sem mais produtos na API. Total de páginas: %d", page - 1)
                    break

                batch: list[dict] = []
                for product in products:
                    if inserted + len(batch) >= limit:
                        break

                    food = _parse_product(product)
                    if food is None:
                        skipped_quality += 1
                        continue

                    # Pré-filtra duplicatas em memória para reduzir conflitos
                    if food.external_id and food.external_id in existing_barcodes:
                        skipped_duplicate += 1
                        continue

                    if food.name in existing_names:
                        brand = (product.get("brands") or "").strip()
                        if brand:
                            food.name = f"{food.name} ({brand})"[:200]
                        if food.name in existing_names:
                            skipped_duplicate += 1
                            continue

                    existing_names.add(food.name)
                    if food.external_id:
                        existing_barcodes.add(food.external_id)

                    batch.append({
                        "name": food.name,
                        "aliases": food.aliases,
                        "category": food.category,
                        "preparation": food.preparation,
                        "notes": food.notes,
                        "source": food.source,
                        "external_id": food.external_id,
                        "search_text": food.search_text,
                        "calories_100g": food.calories_100g,
                        "protein_100g": food.protein_100g,
                        "carbs_100g": food.carbs_100g,
                        "fat_100g": food.fat_100g,
                        "fiber_100g": food.fiber_100g,
                    })

                if not batch:
                    consecutive_empty += 1
                    # Se 5 páginas seguidas não trouxeram nada novo, esgotamos o catálogo
                    if consecutive_empty >= 5:
                        logger.info("5 páginas consecutivas sem novos produtos. Encerrando.")
                        break
                    page += 1
                    continue

                consecutive_empty = 0

                if not dry_run:
                    # ON CONFLICT DO NOTHING: duplicatas residuais dentro do batch não crasham
                    result = await db.execute(
                        sa_text("""
                            INSERT INTO taco_foods
                                (name, aliases, category, preparation, notes, source,
                                 external_id, search_text,
                                 calories_100g, protein_100g, carbs_100g, fat_100g, fiber_100g)
                            VALUES
                                (:name, :aliases, :category, :preparation, :notes, :source,
                                 :external_id, :search_text,
                                 :calories_100g, :protein_100g, :carbs_100g, :fat_100g, :fiber_100g)
                            ON CONFLICT (name) DO NOTHING
                        """),
                        batch,
                    )
                    await db.commit()
                    actually_inserted = result.rowcount if result.rowcount >= 0 else len(batch)
                    skipped_duplicate += len(batch) - actually_inserted
                    inserted += actually_inserted
                else:
                    inserted += len(batch)

                page += 1

                # OFF retorna no máximo ~1000 páginas úteis
                if page > 1000:
                    break

        logger.info("─" * 50)
        logger.info("Importação concluída:")
        logger.info("  Importados:          %d", inserted)
        logger.info("  Ignorados (qualidade): %d", skipped_quality)
        logger.info("  Ignorados (duplicata): %d", skipped_duplicate)
        if dry_run:
            logger.info("  [dry-run] Nenhum dado foi salvo.")


def main() -> None:
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    force = "--force" in args

    limit = DEFAULT_LIMIT
    for arg in args:
        if arg.startswith("--limit="):
            limit = int(arg.split("=")[1])
        elif arg == "--limit" and args.index(arg) + 1 < len(args):
            limit = int(args[args.index(arg) + 1])

    logger.info("Iniciando importação Open Food Facts Brasil")
    logger.info("  Limite: %d produtos | dry-run: %s | force: %s", limit, dry_run, force)
    asyncio.run(import_off(limit=limit, dry_run=dry_run, force=force))


if __name__ == "__main__":
    main()

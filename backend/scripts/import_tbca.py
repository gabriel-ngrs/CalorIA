"""Importa alimentos brasileiros do TBCA para a tabela foods.

O TBCA (Tabela Brasileira de Composição de Alimentos) disponibiliza ~5.500
alimentos com dados nutricionais por 100g. Este script usa o JSON produzido
pelo projeto de web scraping resen-dev/web-scraping-tbca.

O script tenta baixar o JSON automaticamente:
    1. https://raw.githubusercontent.com/resen-dev/web-scraping-tbca/master/data/tbca.json
    2. https://raw.githubusercontent.com/resen-dev/web-scraping-tbca/main/data/tbca.json

Se ambas falharem, forneça o arquivo local com --file:
    python scripts/import_tbca.py --file /caminho/para/tbca.json

Uso:
    cd backend

    # Importa todos os alimentos (baixa automaticamente)
    python scripts/import_tbca.py

    # Importa em modo seco (exibe contagens, não salva)
    python scripts/import_tbca.py --dry-run

    # Força reimportação (remove registros existentes source=tbca)
    python scripts/import_tbca.py --force

    # Usa arquivo local
    python scripts/import_tbca.py --file /tmp/tbca.json

    # Combina flags
    python scripts/import_tbca.py --force --dry-run --file /tmp/tbca.json
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
import unicodedata
from pathlib import Path

import httpx
from sqlalchemy import delete, select
from sqlalchemy import text as sa_text

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import AsyncSessionLocal  # noqa: E402
from app.models.food import Food  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

_TBCA_URLS = [
    "https://raw.githubusercontent.com/resen-dev/web-scraping-tbca/master/data/tbca.json",
    "https://raw.githubusercontent.com/resen-dev/web-scraping-tbca/main/data/tbca.json",
]

# Mapeamento por palavra-chave: verifica se a chave aparece no campo `grupo` (lower).
# Primeira correspondência vence.
_GRUPO_MAP: list[tuple[str, str]] = [
    ("cereais", "cereais"),
    ("leguminosas", "leguminosas"),
    ("hortalicas", "vegetais"),
    ("verduras", "vegetais"),
    ("frutas", "frutas"),
    ("gorduras", "gorduras"),
    ("oleos", "gorduras"),
    ("carnes", "carnes"),
    ("aves", "carnes"),
    ("peixes", "peixes"),
    ("frutos do mar", "peixes"),
    ("laticinios", "laticinios"),
    ("leite", "laticinios"),
    ("ovos", "laticinios"),
    ("bebidas", "bebidas"),
    ("acucares", "acucares"),
    ("doces", "acucares"),
    ("miscelâneas", "outros"),
    ("produtos", "outros"),
]


def _normalize(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


def _map_category(grupo: str) -> str:
    grupo_norm = _normalize(grupo)
    for keyword, category in _GRUPO_MAP:
        if keyword in grupo_norm:
            return category
    return "outros"


async def _download_tbca() -> list[dict]:
    """Tenta baixar o JSON do TBCA nos URLs canônicos do repositório."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        for url in _TBCA_URLS:
            try:
                logger.info("Tentando %s ...", url)
                resp = await client.get(url)
                resp.raise_for_status()
                return resp.json()
            except (httpx.HTTPError, ValueError) as exc:
                logger.warning("Falhou (%s): %s", url, exc)
    raise RuntimeError(
        "Não foi possível baixar o JSON do TBCA. Use --file para fornecer o arquivo local."
    )


def _parse_item(item: dict) -> Food | None:
    """Converte um item do TBCA em Food. Retorna None se dados insuficientes."""
    name = (item.get("nome") or "").strip()
    if not name or len(name) > 200:
        return None

    try:
        calories = float(item.get("energia_kcal") or 0)
        protein = float(item.get("proteina_g") or 0)
        carbs = float(item.get("carboidrato_g") or 0)
        fat = float(item.get("lipideos_g") or 0)
        fiber = float(item.get("fibra_g") or 0)
        # TBCA fornece sódio em mg/100g; converte para g/100g
        sodium_mg = float(item.get("sodio_mg") or 0)
    except (ValueError, TypeError):
        return None

    if calories <= 0 or protein < 0 or carbs < 0 or fat < 0:
        return None

    grupo = (item.get("grupo") or "").strip()
    category = _map_category(grupo)
    external_id = (item.get("codigo") or "").strip() or None
    name_norm = _normalize(name)

    return Food(
        name=name,
        aliases=[],
        category=category,
        preparation=None,
        notes=None,
        source="tbca",
        external_id=external_id,
        search_text=name_norm,
        calories_100g=round(calories, 1),
        protein_100g=round(protein, 2),
        carbs_100g=round(carbs, 2),
        fat_100g=round(fat, 2),
        fiber_100g=round(fiber, 2),
        sodium_100g=round(sodium_mg / 1000, 4) if sodium_mg > 0 else None,
        sugar_100g=None,
        saturated_fat_100g=None,
    )


async def import_tbca(
    dry_run: bool,
    force: bool,
    file_path: str | None = None,
) -> None:
    if file_path:
        logger.info("Carregando arquivo local: %s", file_path)
        data = json.loads(Path(file_path).read_text(encoding="utf-8"))
    else:
        data = await _download_tbca()

    logger.info("Total de itens no JSON: %d", len(data))

    async with AsyncSessionLocal() as db:
        if force:
            deleted = await db.execute(delete(Food).where(Food.source == "tbca"))
            await db.commit()
            logger.info("Removidos %d registros existentes do TBCA.", deleted.rowcount)

        existing_names: set[str] = set(
            row[0] for row in (await db.execute(select(Food.name))).all()
        )
        existing_ids: set[str] = set(
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
        batch: list[dict] = []

        for item in data:
            food = _parse_item(item)
            if food is None:
                skipped_quality += 1
                continue

            if food.external_id and food.external_id in existing_ids:
                skipped_duplicate += 1
                continue

            if food.name in existing_names:
                skipped_duplicate += 1
                continue

            existing_names.add(food.name)
            if food.external_id:
                existing_ids.add(food.external_id)

            batch.append(
                {
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
                    "sodium_100g": food.sodium_100g,
                    "sugar_100g": food.sugar_100g,
                    "saturated_fat_100g": food.saturated_fat_100g,
                }
            )

        if batch and not dry_run:
            result = await db.execute(
                sa_text("""
                    INSERT INTO foods
                        (name, aliases, category, preparation, notes, source,
                         external_id, search_text,
                         calories_100g, protein_100g, carbs_100g, fat_100g, fiber_100g,
                         sodium_100g, sugar_100g, saturated_fat_100g)
                    VALUES
                        (:name, :aliases, :category, :preparation, :notes, :source,
                         :external_id, :search_text,
                         :calories_100g, :protein_100g, :carbs_100g, :fat_100g, :fiber_100g,
                         :sodium_100g, :sugar_100g, :saturated_fat_100g)
                    ON CONFLICT (name) DO NOTHING
                """),
                batch,
            )
            await db.commit()
            actually_inserted = result.rowcount if result.rowcount >= 0 else len(batch)
            skipped_duplicate += len(batch) - actually_inserted
            inserted = actually_inserted
        else:
            inserted = len(batch)

    logger.info("─" * 50)
    logger.info("Importação concluída:")
    logger.info("  Importados:            %d", inserted)
    logger.info("  Ignorados (qualidade): %d", skipped_quality)
    logger.info("  Ignorados (duplicata): %d", skipped_duplicate)
    if dry_run:
        logger.info("  [dry-run] Nenhum dado foi salvo.")


def main() -> None:
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    force = "--force" in args

    file_path: str | None = None
    for i, arg in enumerate(args):
        if arg == "--file" and i + 1 < len(args):
            file_path = args[i + 1]
        elif arg.startswith("--file="):
            file_path = arg.split("=", 1)[1]

    logger.info("Iniciando importação TBCA")
    logger.info(
        "  dry-run: %s | force: %s | arquivo: %s",
        dry_run,
        force,
        file_path or "download automático",
    )
    asyncio.run(import_tbca(dry_run=dry_run, force=force, file_path=file_path))


if __name__ == "__main__":
    main()

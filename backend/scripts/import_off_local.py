"""Importa produtos do Open Food Facts a partir de um dump local (JSONL ou CSV).

Não faz nenhuma chamada de rede — processa o arquivo localmente, evitando
os limites de rate da API. Ideal para importações grandes (20k+).

────────────────────────────────────────────────────
COMO OBTER O ARQUIVO DE DUMP:

  1. Acesse: https://world.openfoodfacts.org/data
  2. Baixe o arquivo JSONL (recomendado):
       en.openfoodfacts.org.products.jsonl.gz  (~9 GB)
     Ou o CSV:
       en.openfoodfacts.org.products.csv.gz    (~9 GB)

  Comando wget (pode demorar horas dependendo da conexão):
       wget https://static.openfoodfacts.org/data/en.openfoodfacts.org.products.jsonl.gz

  Pode deixar baixando em segundo plano e rodar o script quando terminar.

────────────────────────────────────────────────────
USO:

    cd backend

    # Importa do JSONL (recomendado)
    python scripts/import_off_local.py --file /caminho/para/products.jsonl.gz

    # Limita a 20.000 produtos
    python scripts/import_off_local.py --file products.jsonl.gz --limit 20000

    # Sem filtro de país (importa tudo que tiver dados nutricionais)
    python scripts/import_off_local.py --file products.jsonl.gz --all-countries

    # Modo seco: mostra contagens sem salvar
    python scripts/import_off_local.py --file products.jsonl.gz --dry-run

    # Força reimportação (apaga registros source=openfoodfacts antes)
    python scripts/import_off_local.py --file products.jsonl.gz --force

    # CSV também funciona
    python scripts/import_off_local.py --file products.csv.gz

────────────────────────────────────────────────────
"""

from __future__ import annotations

import asyncio
import csv
import gzip
import io
import json
import logging
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_LIMIT = 20_000

BATCH_SIZE = 500
LOG_EVERY = 5_000

_CATEGORY_KEYWORDS: list[tuple[str, str]] = [
    ("meat", "carnes"), ("poultry", "carnes"), ("beef", "carnes"),
    ("pork", "carnes"), ("chicken", "carnes"), ("turkey", "carnes"),
    ("lamb", "carnes"), ("sausage", "carnes"), ("ham", "carnes"),
    ("deli", "carnes"),
    ("fish", "peixes"), ("seafood", "peixes"), ("shrimp", "peixes"),
    ("tuna", "peixes"), ("salmon", "peixes"),
    ("dair", "laticinios"), ("cheese", "laticinios"), ("yogurt", "laticinios"),
    ("milk", "laticinios"), ("butter", "laticinios"), ("cream", "laticinios"),
    ("whey", "laticinios"), ("fermented-milk", "laticinios"),
    ("beverage", "bebidas"), ("drink", "bebidas"), ("juice", "bebidas"),
    ("water", "bebidas"), ("coffee", "bebidas"), ("tea", "bebidas"),
    ("soda", "bebidas"), ("beer", "bebidas"), ("wine", "bebidas"),
    ("alcoholic", "bebidas"), ("smoothie", "bebidas"),
    ("cocoa-powder", "bebidas"), ("instant-beverage", "bebidas"),
    ("fruit", "frutas"),
    ("vegetable", "vegetais"), ("plant-based", "vegetais"),
    ("legume", "leguminosas"), ("bean", "leguminosas"),
    ("lentil", "leguminosas"), ("chickpea", "leguminosas"),
    ("bread", "paes"), ("toast", "paes"),
    ("pasta", "massas"), ("noodle", "massas"),
    ("cereal", "cereais"), ("oat", "cereais"), ("flour", "cereais"),
    ("grain", "cereais"),
    ("cocoa", "acucares"), ("chocolate", "acucares"), ("candy", "acucares"),
    ("sweet", "acucares"), ("biscuit", "acucares"), ("cracker", "acucares"),
    ("cookie", "acucares"), ("cake", "acucares"), ("sugar", "acucares"),
    ("confection", "acucares"), ("dessert", "acucares"),
    ("ice-cream", "acucares"), ("snack", "acucares"),
    ("fat", "gorduras"), ("oil", "gorduras"), ("nut", "gorduras"),
    ("seed", "gorduras"), ("margarine", "gorduras"),
    ("meal", "pratos"), ("soup", "pratos"), ("stew", "pratos"),
    ("frozen", "pratos"), ("pizza", "pratos"), ("sandwich", "pratos"),
    ("fast-food", "fastfood"), ("burger", "fastfood"),
]

def _normalize(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


def _map_category(tags: list[str]) -> str:
    for keyword, category in _CATEGORY_KEYWORDS:
        for tag in tags:
            if keyword in tag:
                return category
    return "outros"


def _is_latin_name(name: str) -> bool:
    if not name:
        return False
    non_latin = sum(1 for c in name if ord(c) > 0x024F)
    return non_latin / len(name) < 0.2


def _is_brazil(product: dict) -> bool:
    tags = product.get("countries_tags") or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",")]
    return any("brazil" in t.lower() for t in tags)


def _parse_product(product: dict) -> dict | None:
    name = (
        product.get("product_name_pt") or product.get("product_name") or ""
    ).strip()

    if not name or len(name) > 200 or not _is_latin_name(name):
        return None

    nutriments = product.get("nutriments") or {}
    if isinstance(nutriments, str):
        try:
            nutriments = json.loads(nutriments)
        except Exception:
            return None

    try:
        calories = float(
            nutriments.get("energy-kcal_100g")
            or nutriments.get("energy_100g") or 0
        )
        protein = float(nutriments.get("proteins_100g") or 0)
        carbs = float(nutriments.get("carbohydrates_100g") or 0)
        fat = float(nutriments.get("fat_100g") or 0)
        fiber = float(nutriments.get("fiber_100g") or 0)
        sodium = float(nutriments.get("sodium_100g") or 0)
        sugar = float(nutriments.get("sugars_100g") or 0)
        saturated_fat = float(nutriments.get("saturated-fat_100g") or 0)
    except (ValueError, TypeError):
        return None

    if calories <= 0 or protein < 0 or carbs < 0 or fat < 0:
        return None

    if calories > 900 and not nutriments.get("energy-kcal_100g"):
        calories = calories / 4.184

    if calories > 950 or protein > 100 or carbs > 100 or fat > 100 or sodium > 10:
        return None

    category_tags = product.get("categories_tags") or []
    if isinstance(category_tags, str):
        category_tags = [t.strip() for t in category_tags.split(",")]
    category = _map_category(category_tags)

    aliases: list[str] = []
    generic = (
        product.get("generic_name_pt") or product.get("generic_name") or ""
    ).strip()
    if generic and generic.lower() != name.lower() and len(generic) <= 200:
        aliases.append(generic)

    brands_raw = (product.get("brands") or "").strip()
    if brands_raw:
        for brand in brands_raw.split(","):
            brand = brand.strip()
            if brand and brand.lower() != name.lower() and brand not in aliases and len(brand) <= 100:
                aliases.append(brand)

    barcode = str(product.get("code") or "").strip() or None
    norm_name = _normalize(name)
    search_text = " ".join([norm_name] + [_normalize(a) for a in aliases])

    return {
        "name": name,
        "aliases": aliases,
        "category": category,
        "preparation": None,
        "notes": None,
        "source": "openfoodfacts",
        "external_id": barcode,
        "search_text": search_text,
        "calories_100g": round(calories, 1),
        "protein_100g": round(protein, 2),
        "carbs_100g": round(carbs, 2),
        "fat_100g": round(fat, 2),
        "fiber_100g": round(fiber, 2),
        "sodium_100g": round(sodium, 3) if sodium > 0 else None,
        "sugar_100g": round(sugar, 2) if sugar > 0 else None,
        "saturated_fat_100g": round(saturated_fat, 2) if saturated_fat > 0 else None,
    }


def _iter_jsonl(path: Path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def _iter_csv(path: Path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            # CSV do OFF usa tabulação e campos de nutrientes têm nomes diferentes
            nutriments: dict = {}
            for key, val in row.items():
                if val in ("", None):
                    continue
                # Mapeia colunas CSV para formato esperado pelo parser
                col = key.strip()
                if col == "energy-kcal_100g":
                    nutriments["energy-kcal_100g"] = val
                elif col == "energy_100g":
                    nutriments["energy_100g"] = val
                elif col.endswith("_100g"):
                    nutriments[col] = val

            # O CSV usa vírgulas nas categories_tags
            cats = row.get("categories_tags", "")
            countries = row.get("countries_tags", "")

            yield {
                "code": row.get("code", ""),
                "product_name": row.get("product_name", ""),
                "product_name_pt": row.get("product_name_pt", ""),
                "generic_name": row.get("generic_name", ""),
                "generic_name_pt": row.get("generic_name_pt", ""),
                "brands": row.get("brands", ""),
                "categories_tags": cats,
                "countries_tags": countries,
                "nutriments": nutriments,
            }


def _detect_format(path: Path) -> str:
    name = path.name.lower()
    if name.endswith(".jsonl.gz") or name.endswith(".jsonl"):
        return "jsonl"
    if name.endswith(".csv.gz") or name.endswith(".csv"):
        return "csv"
    # Tenta detectar pelo conteúdo
    opener = gzip.open if name.endswith(".gz") else open
    with opener(path, "rb") as f:
        first = f.read(1)
    return "jsonl" if first == b"{" else "csv"


_CSV_FIELDS = [
    "name", "aliases", "category", "preparation", "notes", "source",
    "external_id", "search_text", "calories_100g", "protein_100g",
    "carbs_100g", "fat_100g", "fiber_100g", "sodium_100g",
    "sugar_100g", "saturated_fat_100g",
]


def _collect_foods(
    file_path: Path,
    limit: int,
    all_countries: bool,
    existing_names: set[str],
    existing_barcodes: set[str],
) -> tuple[list[dict], dict]:
    fmt = _detect_format(file_path)
    logger.info("Formato detectado: %s", fmt)

    inserted = 0
    skipped_quality = 0
    skipped_country = 0
    skipped_duplicate = 0
    scanned = 0
    foods: list[dict] = []

    iterator = _iter_jsonl(file_path) if fmt == "jsonl" else _iter_csv(file_path)

    for product in iterator:
        scanned += 1

        if scanned % LOG_EVERY == 0:
            logger.info(
                "Lidos: %d | Válidos: %d/%d | Ignorados: qualidade=%d país=%d dup=%d",
                scanned, inserted, limit,
                skipped_quality, skipped_country, skipped_duplicate,
            )

        if not all_countries and not _is_brazil(product):
            skipped_country += 1
            continue

        food = _parse_product(product)
        if food is None:
            skipped_quality += 1
            continue

        if food["external_id"] and food["external_id"] in existing_barcodes:
            skipped_duplicate += 1
            continue

        if food["name"] in existing_names:
            brands_raw = (product.get("brands") or "").strip()
            if brands_raw:
                food["name"] = f"{food['name']} ({brands_raw.split(',')[0].strip()})"[:200]
            if food["name"] in existing_names:
                skipped_duplicate += 1
                continue

        existing_names.add(food["name"])
        if food["external_id"]:
            existing_barcodes.add(food["external_id"])

        foods.append(food)
        inserted += 1

        if inserted >= limit:
            logger.info("Limite de %d atingido.", limit)
            break

    stats = {
        "scanned": scanned, "inserted": inserted,
        "skipped_country": skipped_country,
        "skipped_quality": skipped_quality,
        "skipped_duplicate": skipped_duplicate,
    }
    return foods, stats


def _save_csv(foods: list[dict], output_path: Path) -> None:
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_CSV_FIELDS)
        writer.writeheader()
        for food in foods:
            row = dict(food)
            # Serializa aliases como string JSON para o CSV
            row["aliases"] = json.dumps(row.get("aliases") or [], ensure_ascii=False)
            writer.writerow(row)
    logger.info("CSV salvo em: %s (%d alimentos)", output_path, len(foods))


async def import_local(
    file_path: Path,
    limit: int,
    dry_run: bool,
    force: bool,
    all_countries: bool,
    output_path: Path | None = None,
) -> None:
    # Modo CSV: não precisa do banco para coletar
    if output_path:
        foods, stats = _collect_foods(
            file_path, limit, all_countries,
            existing_names=set(), existing_barcodes=set(),
        )
        _log_stats(stats, dry_run=False)
        if not dry_run:
            _save_csv(foods, output_path)
        return

    # Modo banco de dados
    from sqlalchemy import delete, select
    from sqlalchemy import text as sa_text
    from app.core.database import AsyncSessionLocal
    from app.models.food import Food

    async with AsyncSessionLocal() as db:
        if force:
            deleted = await db.execute(
                delete(Food).where(Food.source == "openfoodfacts")
            )
            await db.commit()
            logger.info("Removidos %d registros existentes do Open Food Facts.", deleted.rowcount)

        existing_names: set[str] = set(
            row[0] for row in (await db.execute(select(Food.name))).all()
        )
        existing_barcodes: set[str] = set(
            row[0]
            for row in (
                await db.execute(
                    select(Food.external_id).where(Food.external_id.isnot(None))
                )
            ).all()
        )

        foods, stats = _collect_foods(
            file_path, limit, all_countries, existing_names, existing_barcodes
        )

        batch: list[dict] = []
        for food in foods:
            batch.append(food)
            if len(batch) >= BATCH_SIZE:
                if not dry_run:
                    await _flush(db, batch)
                batch = []
        if batch and not dry_run:
            await _flush(db, batch)

    _log_stats(stats, dry_run)


def _log_stats(stats: dict, dry_run: bool) -> None:
    logger.info("─" * 50)
    logger.info("Importação concluída:")
    logger.info("  Registros lidos:          %d", stats["scanned"])
    logger.info("  Importados:               %d", stats["inserted"])
    logger.info("  Ignorados (país):         %d", stats["skipped_country"])
    logger.info("  Ignorados (qualidade):    %d", stats["skipped_quality"])
    logger.info("  Ignorados (duplicata):    %d", stats["skipped_duplicate"])
    if dry_run:
        logger.info("  [dry-run] Nenhum dado foi salvo.")


async def _flush(db, batch: list[dict]) -> None:
    await db.execute(
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


def _flag(args: list[str], flag: str) -> bool:
    return flag in args


def _get_arg(args: list[str], flag: str, default: int) -> int:
    for i, arg in enumerate(args):
        if arg.startswith(f"{flag}="):
            return int(arg.split("=", 1)[1])
        if arg == flag and i + 1 < len(args):
            return int(args[i + 1])
    return default


def _get_str_arg(args: list[str], flag: str) -> str | None:
    for i, arg in enumerate(args):
        if arg.startswith(f"{flag}="):
            return arg.split("=", 1)[1]
        if arg == flag and i + 1 < len(args):
            return args[i + 1]
    return None


def main() -> None:
    args = sys.argv[1:]

    file_str = _get_str_arg(args, "--file")
    if not file_str:
        logger.error("Informe o arquivo com --file /caminho/para/products.jsonl.gz")
        sys.exit(1)

    file_path = Path(file_str)
    if not file_path.exists():
        logger.error("Arquivo não encontrado: %s", file_path)
        sys.exit(1)

    limit = _get_arg(args, "--limit", DEFAULT_LIMIT)
    dry_run = _flag(args, "--dry-run")
    force = _flag(args, "--force")
    all_countries = _flag(args, "--all-countries")
    output_str = _get_str_arg(args, "--output")
    output_path = Path(output_str) if output_str else None

    logger.info("Importando Open Food Facts — arquivo local")
    logger.info(
        "  Arquivo: %s | Limite: %d | País: %s | saída: %s",
        file_path, limit,
        "todos" if all_countries else "brasil",
        output_path or "banco de dados",
    )

    asyncio.run(
        import_local(
            file_path=file_path,
            limit=limit,
            dry_run=dry_run,
            force=force,
            all_countries=all_countries,
            output_path=output_path,
        )
    )


if __name__ == "__main__":
    main()

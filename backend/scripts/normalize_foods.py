"""Fase 1 — Limpeza e normalização do alimentos_master.csv.

Lê data/processed/alimentos_master.csv e gera:
  - data/processed/alimentos_limpos.csv          → prontos para importar (têm nutrientes válidos)
  - data/processed/alimentos_para_enriquecer.csv → precisam de enriquecimento por IA (nutrientes ausentes)

O que faz:
  - Deduplica por código de barras (mantém o registro com mais dados)
  - Descarta nomes vazios, muito curtos ou com caracteres não-latinos
  - Normaliza capitalização e espaços em branco
  - Prefere name_pt > name > name_en
  - Mapeia categories OFF para categorias CalorIA
  - Valida sanity check calórico: cal ≈ prot×4 + carbs×4 + fat×9 (±20%)
  - Separa completos de incompletos

USO:
    cd backend
    python scripts/normalize_foods.py
    python scripts/normalize_foods.py --input ../data/processed/alimentos_master.csv
"""

from __future__ import annotations

import argparse
import csv
import logging
import re
import unicodedata
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Mapeamento OFF categories → categorias CalorIA
# ---------------------------------------------------------------------------
CATEGORY_MAP: list[tuple[str, str]] = [
    ("meat", "carnes"), ("beef", "carnes"), ("pork", "carnes"),
    ("poultry", "carnes"), ("chicken", "carnes"), ("turkey", "carnes"),
    ("sausage", "carnes"), ("ham", "carnes"), ("deli", "carnes"),
    ("fish", "peixes"), ("seafood", "peixes"), ("shrimp", "peixes"),
    ("tuna", "peixes"), ("salmon", "peixes"), ("shellfish", "peixes"),
    ("dairy", "laticinios"), ("cheese", "laticinios"), ("yogurt", "laticinios"),
    ("milk", "laticinios"), ("butter", "laticinios"), ("cream", "laticinios"),
    ("whey", "laticinios"),
    ("beverage", "bebidas"), ("drink", "bebidas"), ("juice", "bebidas"),
    ("water", "bebidas"), ("coffee", "bebidas"), ("tea", "bebidas"),
    ("soda", "bebidas"), ("beer", "bebidas"), ("wine", "bebidas"),
    ("alcoholic", "bebidas"),
    ("fruit", "frutas"),
    ("vegetable", "verduras_legumes"), ("legume", "leguminosas"),
    ("bean", "leguminosas"), ("lentil", "leguminosas"),
    ("bread", "paes_massas"), ("pasta", "paes_massas"),
    ("noodle", "paes_massas"), ("toast", "paes_massas"),
    ("cereal", "cereais"), ("oat", "cereais"), ("flour", "cereais"),
    ("grain", "cereais"), ("rice", "cereais"),
    ("chocolate", "doces"), ("candy", "doces"), ("sweet", "doces"),
    ("biscuit", "doces"), ("cookie", "doces"), ("cake", "doces"),
    ("sugar", "doces"), ("confection", "doces"), ("dessert", "doces"),
    ("ice-cream", "doces"), ("snack", "snacks"), ("chip", "snacks"),
    ("cracker", "snacks"), ("popcorn", "snacks"),
    ("oil", "gorduras_oleos"), ("fat", "gorduras_oleos"),
    ("margarine", "gorduras_oleos"),
    ("nut", "oleaginosas"), ("seed", "oleaginosas"), ("almond", "oleaginosas"),
    ("sauce", "molhos_temperos"), ("condiment", "molhos_temperos"),
    ("spice", "molhos_temperos"), ("seasoning", "molhos_temperos"),
    ("soup", "pratos_prontos"), ("meal", "pratos_prontos"),
    ("frozen", "pratos_prontos"), ("pizza", "pratos_prontos"),
    ("sandwich", "pratos_prontos"), ("burger", "pratos_prontos"),
    ("baby", "infantil"),
]


def _map_category(categories_raw: str, existing_category: str) -> str:
    if existing_category and existing_category not in ("outros", ""):
        return existing_category
    cats = categories_raw.lower()
    for keyword, category in CATEGORY_MAP:
        if keyword in cats:
            return category
    return "outros"


# ---------------------------------------------------------------------------
# Normalização de nomes
# ---------------------------------------------------------------------------
_MULTI_SPACE = re.compile(r"\s+")
_PUNCT_ONLY = re.compile(r"^[\W_]+$")


def _normalize_name(name: str) -> str:
    # Remove espaços múltiplos e strip
    name = _MULTI_SPACE.sub(" ", name).strip()
    # Capitaliza apenas a primeira letra (preserva maiúsculas internas como "McFit")
    if name and name[0].islower():
        name = name[0].upper() + name[1:]
    return name


def _is_valid_name(name: str) -> bool:
    if not name or len(name) < 3:
        return False
    if _PUNCT_ONLY.match(name):
        return False
    # Descarta se mais de 30% dos caracteres são não-latinos
    non_latin = sum(1 for c in name if ord(c) > 0x024F)
    return non_latin / len(name) < 0.3


def _best_name(row: dict) -> str:
    for field in ("name_pt", "name", "name_en"):
        val = row.get(field, "").strip()
        if val and _is_valid_name(val):
            return _normalize_name(val)
    return ""


# ---------------------------------------------------------------------------
# Validação nutricional
# ---------------------------------------------------------------------------

def _to_float(val: str) -> float | None:
    if val is None or str(val).strip() == "":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _has_nutrients(row: dict) -> bool:
    cal = _to_float(row.get("calories_100g"))
    prot = _to_float(row.get("protein_100g"))
    carbs = _to_float(row.get("carbs_100g"))
    fat = _to_float(row.get("fat_100g"))
    return all(v is not None for v in (cal, prot, carbs, fat)) and (cal or 0) > 0


def _sanity_check(row: dict) -> bool:
    """Verifica se os macros são fisicamente plausíveis."""
    cal = _to_float(row.get("calories_100g"))
    prot = _to_float(row.get("protein_100g"))
    carbs = _to_float(row.get("carbs_100g"))
    fat = _to_float(row.get("fat_100g"))

    if any(v is None for v in (cal, prot, carbs, fat)):
        return True  # sem dados suficientes para checar

    # Valores fora de range físico
    if cal > 950 or prot > 100 or carbs > 100 or fat > 100:
        return False
    if cal < 0 or prot < 0 or carbs < 0 or fat < 0:
        return False

    # Estimativa calórica esperada
    estimated = prot * 4 + carbs * 4 + fat * 9
    if estimated == 0:
        return cal == 0
    deviation = abs(cal - estimated) / estimated
    return deviation <= 0.25  # tolerância de 25%


# ---------------------------------------------------------------------------
# Campos de saída
# ---------------------------------------------------------------------------
OUT_FIELDS = [
    "name", "aliases", "category", "source", "external_id",
    "search_text", "calories_100g", "protein_100g", "carbs_100g",
    "fat_100g", "fiber_100g", "sodium_100g", "sugar_100g",
    "saturated_fat_100g", "brands", "original_name_en",
]

ENRICH_FIELDS = [
    "name", "name_en", "brands", "categories", "category", "source",
    "external_id", "countries",
]


def _build_search_text(name: str, aliases_str: str, brands: str) -> str:
    parts = [name.lower()]
    # aliases pode ser "{}" ou lista JSON
    aliases_clean = aliases_str.strip("{} ")
    if aliases_clean:
        parts.append(aliases_clean.lower())
    if brands:
        parts.append(brands.lower())
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def normalize(input_path: Path, out_clean: Path, out_enrich: Path) -> None:
    seen_barcodes: dict[str, dict] = {}  # barcode → melhor row
    seen_names: set[str] = set()

    total = 0
    discarded_name = 0
    discarded_sanity = 0
    deduped = 0

    rows_all: list[dict] = []

    with open(input_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            total += 1

            name = _best_name(row)
            if not name:
                discarded_name += 1
                continue

            row["_name"] = name

            # Deduplica por código de barras — mantém o com mais nutrientes
            barcode = row.get("barcode") or row.get("external_id") or ""
            barcode = barcode.strip()
            if barcode and barcode != "None":
                if barcode in seen_barcodes:
                    prev = seen_barcodes[barcode]
                    if _has_nutrients(row) and not _has_nutrients(prev):
                        seen_barcodes[barcode] = row
                    deduped += 1
                    continue
                seen_barcodes[barcode] = row

            rows_all.append(row)

    # Segunda passagem: desduplicar por nome e separar clean/enrich
    clean: list[dict] = []
    enrich: list[dict] = []

    # Primeiro processa os que têm barcode (já deduplicados)
    for barcode, row in seen_barcodes.items():
        _process_row(row, seen_names, clean, enrich,
                     discarded_ref=[discarded_sanity])

    # Depois os sem barcode
    for row in rows_all:
        barcode = (row.get("barcode") or row.get("external_id") or "").strip()
        if barcode and barcode != "None" and barcode in seen_barcodes:
            continue  # já processado
        _process_row(row, seen_names, clean, enrich,
                     discarded_ref=[discarded_sanity])

    # Salva
    _write_clean(out_clean, clean)
    _write_enrich(out_enrich, enrich)

    log.info("─" * 50)
    log.info("Normalização concluída:")
    log.info("  Total lido:           %d", total)
    log.info("  Descartados (nome):   %d", discarded_name)
    log.info("  Descartados (sanity): %d", discarded_sanity)
    log.info("  Deduplicados:         %d", deduped)
    log.info("  Prontos (clean):      %d  → %s", len(clean), out_clean)
    log.info("  Para enriquecer:      %d  → %s", len(enrich), out_enrich)


def _process_row(
    row: dict,
    seen_names: set[str],
    clean: list[dict],
    enrich: list[dict],
    discarded_ref: list[int],
) -> None:
    name = row.get("_name") or _best_name(row)
    if not name:
        return

    # Deduplica por nome
    name_key = name.lower()
    if name_key in seen_names:
        return
    seen_names.add(name_key)

    category = _map_category(
        row.get("categories", ""),
        row.get("category", ""),
    )
    barcode = (row.get("barcode") or row.get("external_id") or "").strip()
    if barcode in ("None", "nan", ""):
        barcode = ""

    aliases = row.get("aliases", "").strip()
    brands = row.get("brands", "").strip()
    search_text = _build_search_text(name, aliases, brands)
    name_en = row.get("name_en", "").strip()

    base = {
        "name": name,
        "aliases": aliases,
        "category": category,
        "source": row.get("source", "openfoodfacts"),
        "external_id": barcode,
        "search_text": search_text,
        "brands": brands,
        "original_name_en": name_en,
    }

    if _has_nutrients(row):
        if not _sanity_check(row):
            discarded_ref[0] += 1
            return
        clean.append({
            **base,
            "calories_100g": row.get("calories_100g", ""),
            "protein_100g": row.get("protein_100g", ""),
            "carbs_100g": row.get("carbs_100g", ""),
            "fat_100g": row.get("fat_100g", ""),
            "fiber_100g": row.get("fiber_100g", ""),
            "sodium_100g": row.get("sodium_100g", ""),
            "sugar_100g": row.get("sugar_100g", ""),
            "saturated_fat_100g": row.get("saturated_fat_100g", ""),
        })
    else:
        enrich.append({
            "name": name,
            "name_en": name_en,
            "brands": brands,
            "categories": row.get("categories", ""),
            "category": category,
            "source": row.get("source", "openfoodfacts"),
            "external_id": barcode,
            "countries": row.get("countries", ""),
        })


def _write_clean(path: Path, rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _write_enrich(path: Path, rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=ENRICH_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--input",
        default="../data/processed/alimentos_master.csv",
        help="CSV de entrada (padrão: data/processed/alimentos_master.csv)",
    )
    args = ap.parse_args()

    input_path = Path(args.input)
    out_clean = input_path.parent / "alimentos_limpos.csv"
    out_enrich = input_path.parent / "alimentos_para_enriquecer.csv"

    log.info("Normalizando: %s", input_path)
    normalize(input_path, out_clean, out_enrich)


if __name__ == "__main__":
    main()

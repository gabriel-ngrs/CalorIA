"""Extrai TODOS os produtos brasileiros do dump OFF para CSV, sem filtro de qualidade.

Inclui produtos com dados nutricionais incompletos ou ausentes — ideal para
enriquecer depois com IA.

USO:
    cd backend
    python scripts/extract_off_brazil.py \\
        --file ../data/openfoodfacts-products.jsonl.gz \\
        --output ../data/off_brazil_raw.csv

    # Sem limite (extrai tudo)
    python scripts/extract_off_brazil.py --file ... --output ...

    # Com limite
    python scripts/extract_off_brazil.py --file ... --output ... --limit 10000
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import logging
import sys
import unicodedata
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

CSV_FIELDS = [
    "name", "name_pt", "name_en", "barcode", "brands", "categories",
    "calories_100g", "protein_100g", "carbs_100g", "fat_100g",
    "fiber_100g", "sodium_100g", "sugar_100g", "saturated_fat_100g",
    "countries", "source",
]

LOG_EVERY = 50_000


def _is_brazil(product: dict) -> bool:
    tags = product.get("countries_tags") or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",")]
    return any("brazil" in t.lower() for t in tags)


def _is_latin(name: str) -> bool:
    if not name:
        return False
    non_latin = sum(1 for c in name if ord(c) > 0x024F)
    return non_latin / len(name) < 0.3


def _safe_float(val) -> str:
    if val is None or val == "":
        return ""
    try:
        return str(round(float(val), 3))
    except (ValueError, TypeError):
        return ""


def extract(file_path: Path, output_path: Path, limit: int) -> None:
    total_scanned = 0
    total_extracted = 0
    total_no_name = 0

    opener = gzip.open if file_path.suffix == ".gz" else open

    with (
        opener(file_path, "rt", encoding="utf-8", errors="replace") as fin,
        open(output_path, "w", newline="", encoding="utf-8") as fout,
    ):
        writer = csv.DictWriter(fout, fieldnames=CSV_FIELDS)
        writer.writeheader()

        for line in fin:
            line = line.strip()
            if not line:
                continue

            total_scanned += 1
            if total_scanned % LOG_EVERY == 0:
                log.info("Lidos: %d | Extraídos: %d", total_scanned, total_extracted)

            try:
                product = json.loads(line)
            except json.JSONDecodeError:
                continue

            if not _is_brazil(product):
                continue

            # Tenta pegar nome em pt, depois genérico
            name_pt = (product.get("product_name_pt") or "").strip()
            name_en = (product.get("product_name_en") or "").strip()
            name_generic = (product.get("product_name") or "").strip()

            # Escolhe o melhor nome disponível
            name = name_pt or name_generic or name_en
            if not name:
                total_no_name += 1
                continue

            # Descarta nomes com caracteres não-latinos (chinês, árabe, etc.)
            if not _is_latin(name):
                continue

            nutriments = product.get("nutriments") or {}

            calories = _safe_float(
                nutriments.get("energy-kcal_100g") or nutriments.get("energy_100g")
            )
            # Converte kJ para kcal se necessário
            if calories and float(calories) > 900:
                try:
                    calories = str(round(float(calories) / 4.184, 1))
                except Exception:
                    pass

            categories_tags = product.get("categories_tags") or []
            if isinstance(categories_tags, str):
                categories_tags = [t.strip() for t in categories_tags.split(",")]
            categories = "; ".join(categories_tags[:5])  # máx 5 tags

            countries_tags = product.get("countries_tags") or []
            if isinstance(countries_tags, str):
                countries_tags = [t.strip() for t in countries_tags.split(",")]
            countries = "; ".join(countries_tags[:3])

            writer.writerow({
                "name": name[:200],
                "name_pt": name_pt[:200],
                "name_en": name_en[:200],
                "barcode": str(product.get("code") or "").strip(),
                "brands": (product.get("brands") or "").strip()[:200],
                "categories": categories[:500],
                "calories_100g": calories,
                "protein_100g": _safe_float(nutriments.get("proteins_100g")),
                "carbs_100g": _safe_float(nutriments.get("carbohydrates_100g")),
                "fat_100g": _safe_float(nutriments.get("fat_100g")),
                "fiber_100g": _safe_float(nutriments.get("fiber_100g")),
                "sodium_100g": _safe_float(nutriments.get("sodium_100g")),
                "sugar_100g": _safe_float(nutriments.get("sugars_100g")),
                "saturated_fat_100g": _safe_float(nutriments.get("saturated-fat_100g")),
                "countries": countries,
                "source": "openfoodfacts",
            })

            total_extracted += 1
            if limit and total_extracted >= limit:
                log.info("Limite de %d atingido.", limit)
                break

    log.info("─" * 50)
    log.info("Concluído:")
    log.info("  Registros lidos:     %d", total_scanned)
    log.info("  Extraídos:           %d", total_extracted)
    log.info("  Sem nome:            %d", total_no_name)
    log.info("  Arquivo:             %s", output_path)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True, help="Caminho para o .jsonl.gz do OFF")
    ap.add_argument("--output", required=True, help="Arquivo CSV de saída")
    ap.add_argument("--limit", type=int, default=0, help="Limite de registros (0 = sem limite)")
    args = ap.parse_args()

    file_path = Path(args.file)
    if not file_path.exists():
        log.error("Arquivo não encontrado: %s", file_path)
        sys.exit(1)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    extract(file_path, output_path, args.limit)


if __name__ == "__main__":
    main()

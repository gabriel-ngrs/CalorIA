"""Fase 3 — Estimativa de nutrientes via Groq para alimentos sem dados.

Lê data/processed/alimentos_para_enriquecer.csv (26k alimentos sem nutrientes), envia em
lotes ao Groq agrupados por categoria, e salva os resultados em
data/processed/alimentos_enriquecidos.csv com source=ai_estimated.

USO:
    cd backend

    # Testa com os primeiros 100 (não salva)
    python scripts/enrich_foods.py --dry-run

    # Roda completo
    python scripts/enrich_foods.py

    # Retoma de onde parou
    python scripts/enrich_foods.py --resume

    # Arquivo customizado
    python scripts/enrich_foods.py --input ../data/processed/alimentos_para_enriquecer.csv
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import logging
import os
import re
from pathlib import Path

from groq import Groq

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

BATCH_SIZE = 150
MODEL = "llama-3.1-8b-instant"
MAX_RETRIES = 3
RETRY_DELAY = 5

OUT_FIELDS = [
    "name", "aliases", "category", "source", "external_id", "search_text",
    "calories_100g", "protein_100g", "carbs_100g", "fat_100g",
    "fiber_100g", "sodium_100g", "sugar_100g", "saturated_fat_100g",
    "brands", "original_name_en",
]


async def _estimate_batch(
    client: Groq,
    items: list[dict],
    category: str,
) -> list[dict]:
    """Envia um lote ao Groq e retorna os itens com nutrientes estimados."""

    # Inclui categoria por item para evitar que a IA assuma categoria errada
    indexed = [
        {"i": i, "n": item["name"], "cat": item.get("category") or category}
        for i, item in enumerate(items)
    ]

    prompt = f"""Você é nutricionista especializado em composição de alimentos.
Estime os valores nutricionais por 100g de cada alimento abaixo.
O campo "cat" indica a categoria de cada item — use-a para contextualizar a estimativa.

Regras:
- Use valores típicos para cada tipo de alimento
- Para produtos industrializados, use referências conhecidas da categoria do item
- Calorias devem ser coerentes com macros: cal ≈ prot×4 + carbs×4 + fat×9
- IMPORTANTE: retorne EXATAMENTE um objeto por alimento, na mesma ordem, usando o campo "i" como índice
- Retorne SOMENTE o JSON, sem texto adicional

Formato de saída (array com mesmo número de itens que a entrada):
{{"estimativas": [{{"i": 0, "cal": 0, "prot": 0.0, "carbs": 0.0, "fat": 0.0, "fiber": 0.0}}]}}

Alimentos:
{json.dumps(indexed, ensure_ascii=False)}"""

    for attempt in range(MAX_RETRIES):
        try:
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            text = response.choices[0].message.content.strip()
            text = re.sub(r"^```json\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
            data = json.loads(text)
            estimativas = data.get("estimativas") or []

            # Mapeia índice → nutrientes (fallback: nome para retrocompatibilidade)
            result_by_idx: dict[int, dict] = {}
            result_by_name: dict[str, dict] = {}
            for est in estimativas:
                idx = est.get("i")
                if isinstance(idx, int):
                    result_by_idx[idx] = est
                nome = est.get("nome") or est.get("n", "")
                if isinstance(nome, str) and nome.strip():
                    result_by_name[nome.strip()] = est

            # Aplica aos itens originais
            enriched = []
            for pos, item in enumerate(items):
                est = result_by_idx.get(pos) or result_by_name.get(item["name"], {})
                cal = _safe(est.get("cal"))
                prot = _safe(est.get("prot"))
                carbs = _safe(est.get("carbs"))
                fat = _safe(est.get("fat"))
                fiber = _safe(est.get("fiber"))

                # Sanity check: descarta estimativas impossíveis
                if cal and prot and carbs and fat:
                    expected = prot * 4 + carbs * 4 + fat * 9
                    if expected > 0 and abs(cal - expected) / expected > 0.30:
                        # Recalcula calorias pelos macros
                        cal = round(expected, 1)

                enriched.append({
                    **item,
                    "calories_100g": cal or "",
                    "protein_100g": prot or "",
                    "carbs_100g": carbs or "",
                    "fat_100g": fat or "",
                    "fiber_100g": fiber or "",
                    "sodium_100g": "",
                    "sugar_100g": "",
                    "saturated_fat_100g": "",
                    "source": "ai_estimated",
                    "aliases": "{}",
                    "search_text": item["name"].lower(),
                    "brands": item.get("brands", ""),
                    "original_name_en": item.get("name_en", ""),
                })
            return enriched

        except Exception as e:
            log.warning("Tentativa %d/%d falhou: %s", attempt + 1, MAX_RETRIES, e)
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))

    # Fallback: retorna itens sem nutrientes
    log.error("Lote falhou — salvando sem nutrientes")
    return [{
        **item,
        "calories_100g": "", "protein_100g": "", "carbs_100g": "",
        "fat_100g": "", "fiber_100g": "", "sodium_100g": "",
        "sugar_100g": "", "saturated_fat_100g": "",
        "source": "ai_estimated",
        "aliases": "{}",
        "search_text": item["name"].lower(),
        "brands": item.get("brands", ""),
        "original_name_en": item.get("name_en", ""),
    } for item in items]


def _safe(val) -> float | None:
    if val is None or val == "":
        return None
    try:
        v = float(val)
        return round(v, 2) if v >= 0 else None
    except (ValueError, TypeError):
        return None


async def enrich(
    input_path: Path,
    output_path: Path,
    dry_run: bool,
    resume: bool,
) -> None:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        env_path = Path(__file__).parent.parent.parent / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("GROQ_API_KEY="):
                    api_key = line.split("=", 1)[1].strip()
                    break
    if not api_key:
        log.error("GROQ_API_KEY não encontrada")
        return

    client = Groq(api_key=api_key)

    # Carrega todos os itens
    all_items: list[dict] = []
    with open(input_path, encoding="utf-8") as f:
        all_items = list(csv.DictReader(f))

    log.info("Total para enriquecer: %d", len(all_items))

    # Carrega progresso anterior (resume)
    # Só marca como "feito" se tiver calorias — itens que falharam serão reprocessados
    done_names: set[str] = set()
    existing_rows: list[dict] = []
    if resume and output_path.exists():
        with open(output_path, encoding="utf-8") as f:
            existing_rows = list(csv.DictReader(f))
            done_names = {r["name"] for r in existing_rows if r.get("calories_100g")}
        log.info("Retomando: %d já enriquecidos com nutrientes", len(done_names))

    # Remove do existing_rows os que serão reprocessados (sem nutrientes)
    existing_rows = [r for r in existing_rows if r.get("calories_100g")]

    # Filtra os que faltam e agrupa por categoria
    pending = [r for r in all_items if r["name"] not in done_names]
    log.info("Pendentes: %d", len(pending))

    # Ordena por categoria para lotes mais coesos
    pending.sort(key=lambda r: r.get("category") or "outros")

    if dry_run:
        sample = pending[:BATCH_SIZE]
        log.info("\n[DRY RUN] Estimando amostra de %d alimentos...", len(sample))
        category = sample[0].get("category", "outros")
        result = await _estimate_batch(client, sample, category)
        log.info("\nAmostra de resultado:")
        for r in result[:15]:
            log.info(
                "  %-45s cal=%-5s prot=%-5s carbs=%-5s fat=%s",
                r["name"][:45],
                r.get("calories_100g", "?"),
                r.get("protein_100g", "?"),
                r.get("carbs_100g", "?"),
                r.get("fat_100g", "?"),
            )
        log.info("\nNada foi salvo (dry-run).")
        return

    # Enriquece em lotes
    total_batches = (len(pending) + BATCH_SIZE - 1) // BATCH_SIZE
    all_enriched = list(existing_rows)

    for i in range(0, len(pending), BATCH_SIZE):
        batch = pending[i: i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        category = batch[0].get("category", "outros")

        log.info("Lote %d/%d | categoria: %s | %d itens",
                 batch_num, total_batches, category, len(batch))

        enriched = await _estimate_batch(client, batch, category)
        all_enriched.extend(enriched)

        # Salva progressivamente
        _write(output_path, all_enriched)

        if batch_num % 10 == 0:
            with_nutrients = sum(1 for r in all_enriched if r.get("calories_100g"))
            log.info("  → %d/%d salvos, %d com nutrientes",
                     len(all_enriched), len(all_items), with_nutrients)

        if batch_num < total_batches:
            await asyncio.sleep(1)

    with_nutrients = sum(1 for r in all_enriched if r.get("calories_100g"))
    log.info("─" * 50)
    log.info("Enriquecimento concluído:")
    log.info("  Total processado:    %d", len(all_enriched))
    log.info("  Com nutrientes:      %d", with_nutrients)
    log.info("  Sem nutrientes:      %d", len(all_enriched) - with_nutrients)
    log.info("  Arquivo:             %s", output_path)


def _write(path: Path, rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="../data/processed/alimentos_para_enriquecer.csv")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    input_path = Path(args.input)
    output_path = input_path.parent / "alimentos_enriquecidos.csv"

    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

    asyncio.run(enrich(input_path, output_path, args.dry_run, args.resume))


if __name__ == "__main__":
    main()

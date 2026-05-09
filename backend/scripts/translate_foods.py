"""Fase 2 — Tradução de nomes de alimentos para português via Groq.

Lê data/processed/alimentos_limpos.csv, traduz os nomes em inglês para português
brasileiro em lotes de 200 via Groq (Llama 3.3 70B), e salva o resultado em
data/processed/alimentos_traduzidos.csv.

Alimentos TACO (source=taco) e os que já têm nome em português são preservados.

USO:
    cd backend

    # Testa com os primeiros 200 (não salva)
    python scripts/translate_foods.py --dry-run

    # Traduz tudo
    python scripts/translate_foods.py

    # Retoma de onde parou (se interrompido)
    python scripts/translate_foods.py --resume

    # Arquivo customizado
    python scripts/translate_foods.py --input ../data/processed/alimentos_limpos.csv
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import logging
import os
import re
import time
from pathlib import Path

from groq import Groq

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

BATCH_SIZE = 200
MODEL = "llama-3.3-70b-versatile"
MAX_RETRIES = 3
RETRY_DELAY = 5  # segundos entre tentativas

# Fontes já em português — não precisam de tradução
PT_SOURCES = {"taco"}

# Heurística: se >60% dos caracteres são ASCII a-z, provavelmente inglês
_ASCII_LETTERS = re.compile(r"[a-zA-Z]")
_PT_MARKERS = re.compile(
    r"\b(de|da|do|das|dos|com|sem|para|em|ao|à|arroz|feijão|frango|"
    r"carne|pão|leite|queijo|ovo|peixe|fruta|legume|suco|molho|"
    r"farinha|manteiga|azeite|açúcar|café|iogurte)\b",
    re.IGNORECASE,
)


def _needs_translation(row: dict) -> bool:
    if row.get("source") in PT_SOURCES:
        return False
    name = row.get("name", "")
    # Já tem marcadores de português
    if _PT_MARKERS.search(name):
        return False
    # Verifica se é predominantemente ASCII (inglês)
    ascii_count = len(_ASCII_LETTERS.findall(name))
    total_letters = sum(1 for c in name if c.isalpha())
    if total_letters == 0:
        return False
    return ascii_count / total_letters > 0.85


async def _translate_batch(
    client: Groq,
    names: list[str],
) -> dict[str, str]:
    """Envia um lote de nomes ao Groq e retorna {original: traduzido}."""

    prompt = f"""Você é um especialista em alimentos e nutrição.
Traduza os nomes de alimentos abaixo para português brasileiro.

Regras:
- Mantenha nomes de marcas como estão (ex: Heinz, Nestlé, Kellogg's)
- Use termos populares brasileiros (ex: "chicken breast" → "peito de frango")
- Se o nome já estiver em português, retorne-o sem alteração
- Retorne SOMENTE o JSON, sem texto adicional

Formato de saída:
{{"traducoes": [{{"original": "nome original", "pt": "nome em português"}}]}}

Nomes para traduzir:
{json.dumps(names, ensure_ascii=False)}"""

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
            translations = data.get("traducoes") or data.get("translations") or []
            result = {}
            for item in translations:
                orig = item.get("original", "").strip()
                pt = item.get("pt", "").strip()
                if orig and pt:
                    result[orig] = pt
            return result
        except Exception as e:
            log.warning("Tentativa %d/%d falhou: %s", attempt + 1, MAX_RETRIES, e)
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))

    log.error("Lote falhou após %d tentativas — mantendo nomes originais", MAX_RETRIES)
    return {}


async def translate(
    input_path: Path,
    output_path: Path,
    dry_run: bool,
    resume: bool,
) -> None:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        env_path = input_path.parent.parent.parent / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("GROQ_API_KEY="):
                    api_key = line.split("=", 1)[1].strip()
                    break

    if not api_key:
        log.error("GROQ_API_KEY não encontrada no ambiente ou no .env")
        return

    client = Groq(api_key=api_key)

    # Carrega traduções já feitas (modo resume)
    done: dict[str, str] = {}
    if resume and output_path.exists():
        with open(output_path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                done[row["name"]] = row["name"]  # nome já traduzido
        log.info("Retomando: %d registros já traduzidos", len(done))

    # Lê o CSV de entrada
    all_rows: list[dict] = []
    with open(input_path, encoding="utf-8") as f:
        all_rows = list(csv.DictReader(f))

    # Separa quem precisa de tradução
    to_translate = [r for r in all_rows if _needs_translation(r) and r["name"] not in done]
    already_pt = [r for r in all_rows if not _needs_translation(r)]

    log.info("Total de alimentos:    %d", len(all_rows))
    log.info("Já em português:       %d", len(already_pt))
    log.info("Para traduzir:         %d", len(to_translate))
    log.info("Já traduzidos (cache): %d", len(done))

    if dry_run:
        sample = to_translate[:BATCH_SIZE]
        log.info("\n[DRY RUN] Traduzindo amostra de %d nomes...\n", len(sample))
        names = [r["name"] for r in sample]
        translations = await _translate_batch(client, names)
        log.info("\nResultado da amostra:")
        for orig, pt in list(translations.items())[:20]:
            log.info("  %-50s → %s", orig, pt)
        log.info("\nNada foi salvo (dry-run).")
        return

    # Traduz em lotes
    translations: dict[str, str] = dict(done)
    total_batches = (len(to_translate) + BATCH_SIZE - 1) // BATCH_SIZE

    for i in range(0, len(to_translate), BATCH_SIZE):
        batch = to_translate[i : i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        names = [r["name"] for r in batch]

        log.info("Lote %d/%d (%d nomes)...", batch_num, total_batches, len(names))
        result = await _translate_batch(client, names)

        for name in names:
            translations[name] = result.get(name, name)  # fallback: nome original

        # Salva progressivamente a cada lote
        _write_output(output_path, all_rows, translations)
        log.info("  Salvo: %s", output_path)

        # Pausa entre lotes para não estourar rate limit
        if batch_num < total_batches:
            await asyncio.sleep(1)

    log.info("─" * 50)
    log.info("Tradução concluída: %d nomes traduzidos → %s", len(translations), output_path)


def _write_output(
    output_path: Path,
    all_rows: list[dict],
    translations: dict[str, str],
) -> None:
    fieldnames = list(all_rows[0].keys()) if all_rows else []
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in all_rows:
            out = dict(row)
            original_name = row["name"]
            if original_name in translations:
                translated = translations[original_name]
                if translated != original_name:
                    out["original_name_en"] = original_name
                    out["name"] = translated
                    # Atualiza search_text com o nome traduzido
                    out["search_text"] = translated.lower()
            writer.writerow(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="../data/processed/alimentos_limpos.csv")
    ap.add_argument("--dry-run", action="store_true", help="Testa sem salvar")
    ap.add_argument("--resume", action="store_true", help="Retoma de onde parou")
    args = ap.parse_args()

    input_path = Path(args.input)
    output_path = input_path.parent / "alimentos_traduzidos.csv"

    # Carrega .env se necessário
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

    asyncio.run(translate(input_path, output_path, args.dry_run, args.resume))


if __name__ == "__main__":
    main()

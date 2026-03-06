"""Popula a tabela taco_foods com dados da TACO (UNICAMP) + alimentos processados comuns.

Uso:
    cd backend
    python scripts/seed_taco.py
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.taco_food import TacoFood

# ---------------------------------------------------------------------------
# Base de dados: (name, aliases, category, preparation, notes, cal, prot, carb, fat, fiber)
# Fonte: TACO 4ª edição (UNICAMP/MS) + IBGE/USDA para industrializados
# Valores por 100g, já cozido/preparado quando indicado
# ---------------------------------------------------------------------------
TACO_DATA: list[dict] = [

    # ── ARROZ E CEREAIS ────────────────────────────────────────────────────
    {"name": "Arroz branco cozido", "aliases": ["arroz", "arroz branco", "arroz cozido"], "category": "cereais", "preparation": "cozido", "calories_100g": 128, "protein_100g": 2.5, "carbs_100g": 28.1, "fat_100g": 0.2, "fiber_100g": 1.6},
    {"name": "Arroz integral cozido", "aliases": ["arroz integral"], "category": "cereais", "preparation": "cozido", "calories_100g": 124, "protein_100g": 2.6, "carbs_100g": 25.8, "fat_100g": 1.0, "fiber_100g": 2.7},
    {"name": "Arroz parboilizado cozido", "aliases": ["arroz parboilizado"], "category": "cereais", "preparation": "cozido", "calories_100g": 127, "protein_100g": 2.5, "carbs_100g": 27.7, "fat_100g": 0.3, "fiber_100g": 1.4},
    {"name": "Aveia em flocos", "aliases": ["aveia", "flocos de aveia", "mingau de aveia"], "category": "cereais", "preparation": "cru", "calories_100g": 394, "protein_100g": 13.9, "carbs_100g": 66.6, "fat_100g": 8.5, "fiber_100g": 9.1},
    {"name": "Granola tradicional", "aliases": ["granola"], "category": "cereais", "preparation": "pronto", "calories_100g": 420, "protein_100g": 9.0, "carbs_100g": 65.0, "fat_100g": 14.0, "fiber_100g": 5.0},
    {"name": "Quinoa cozida", "aliases": ["quinoa"], "category": "cereais", "preparation": "cozido", "calories_100g": 120, "protein_100g": 4.4, "carbs_100g": 21.3, "fat_100g": 1.9, "fiber_100g": 2.8},
    {"name": "Cuscuz de milho preparado", "aliases": ["cuscuz", "cuscuz nordestino", "couscous"], "category": "cereais", "preparation": "preparado", "calories_100g": 105, "protein_100g": 2.0, "carbs_100g": 23.0, "fat_100g": 0.5, "fiber_100g": 1.2},
    {"name": "Milho verde cozido", "aliases": ["milho", "milho verde", "espiga de milho"], "category": "cereais", "preparation": "cozido", "calories_100g": 86, "protein_100g": 3.2, "carbs_100g": 18.7, "fat_100g": 1.0, "fiber_100g": 2.0},
    {"name": "Farinha de mandioca torrada", "aliases": ["farinha de mandioca", "farofa seca", "farinha"], "category": "cereais", "preparation": "torrada", "calories_100g": 361, "protein_100g": 1.5, "carbs_100g": 87.9, "fat_100g": 0.4, "fiber_100g": 6.5},
    {"name": "Farofa de manteiga", "aliases": ["farofa", "farofa temperada"], "category": "cereais", "preparation": "preparado", "calories_100g": 390, "protein_100g": 2.0, "carbs_100g": 72.0, "fat_100g": 10.0, "fiber_100g": 4.0, "notes": "estimativa com manteiga"},

    # ── FEIJÕES E LEGUMINOSAS ──────────────────────────────────────────────
    {"name": "Feijão carioca cozido", "aliases": ["feijão", "feijão carioca", "feijão marrom", "feijão mulatinho"], "category": "leguminosas", "preparation": "cozido", "calories_100g": 76, "protein_100g": 4.8, "carbs_100g": 13.6, "fat_100g": 0.5, "fiber_100g": 8.5},
    {"name": "Feijão preto cozido", "aliases": ["feijão preto"], "category": "leguminosas", "preparation": "cozido", "calories_100g": 77, "protein_100g": 4.5, "carbs_100g": 14.0, "fat_100g": 0.5, "fiber_100g": 8.4},
    {"name": "Feijão-fradinho cozido", "aliases": ["feijão fradinho", "feijão de corda", "feijão verde"], "category": "leguminosas", "preparation": "cozido", "calories_100g": 74, "protein_100g": 4.9, "carbs_100g": 12.9, "fat_100g": 0.4, "fiber_100g": 6.8},
    {"name": "Lentilha cozida", "aliases": ["lentilha"], "category": "leguminosas", "preparation": "cozido", "calories_100g": 111, "protein_100g": 9.0, "carbs_100g": 19.7, "fat_100g": 0.4, "fiber_100g": 3.7},
    {"name": "Grão-de-bico cozido", "aliases": ["grão de bico", "grão-de-bico", "chickpea"], "category": "leguminosas", "preparation": "cozido", "calories_100g": 164, "protein_100g": 8.9, "carbs_100g": 27.4, "fat_100g": 2.6, "fiber_100g": 6.2},
    {"name": "Ervilha cozida", "aliases": ["ervilha"], "category": "leguminosas", "preparation": "cozido", "calories_100g": 81, "protein_100g": 5.4, "carbs_100g": 14.5, "fat_100g": 0.4, "fiber_100g": 5.7},
    {"name": "Ervilha enlatada", "aliases": ["ervilha em lata", "ervilha de lata"], "category": "leguminosas", "preparation": "enlatado", "calories_100g": 60, "protein_100g": 3.5, "carbs_100g": 10.5, "fat_100g": 0.3, "fiber_100g": 4.5},
    {"name": "Soja cozida", "aliases": ["soja"], "category": "leguminosas", "preparation": "cozido", "calories_100g": 141, "protein_100g": 12.5, "carbs_100g": 11.5, "fat_100g": 6.8, "fiber_100g": 9.6},
    {"name": "Edamame cozido", "aliases": ["edamame"], "category": "leguminosas", "preparation": "cozido", "calories_100g": 122, "protein_100g": 11.0, "carbs_100g": 10.0, "fat_100g": 5.0, "fiber_100g": 5.0},

    # ── MASSAS E PÃES ──────────────────────────────────────────────────────
    {"name": "Macarrão cozido", "aliases": ["macarrão", "massa", "espaguete", "espagueti", "penne", "fusilli", "macarrão ao molho"], "category": "massas", "preparation": "cozido", "calories_100g": 148, "protein_100g": 5.0, "carbs_100g": 30.5, "fat_100g": 0.8, "fiber_100g": 1.8},
    {"name": "Macarrão integral cozido", "aliases": ["macarrão integral", "massa integral"], "category": "massas", "preparation": "cozido", "calories_100g": 124, "protein_100g": 4.7, "carbs_100g": 26.0, "fat_100g": 0.8, "fiber_100g": 4.5},
    {"name": "Pão francês", "aliases": ["pão", "pãozinho", "cacete", "pão careca", "pão de sal"], "category": "paes", "preparation": "assado", "calories_100g": 300, "protein_100g": 8.0, "carbs_100g": 58.6, "fat_100g": 3.1, "fiber_100g": 2.3, "notes": "1 unidade ≈ 50g → 150 kcal"},
    {"name": "Pão de forma branco", "aliases": ["pão de forma", "pão fatiado"], "category": "paes", "preparation": "assado", "calories_100g": 264, "protein_100g": 7.8, "carbs_100g": 50.8, "fat_100g": 3.4, "fiber_100g": 2.3, "notes": "1 fatia ≈ 25g → 66 kcal"},
    {"name": "Pão de forma integral", "aliases": ["pão integral fatiado", "pão integral"], "category": "paes", "preparation": "assado", "calories_100g": 269, "protein_100g": 9.5, "carbs_100g": 48.0, "fat_100g": 4.8, "fiber_100g": 5.5, "notes": "1 fatia ≈ 25g → 67 kcal"},
    {"name": "Pão de queijo", "aliases": ["pão de queijo", "pãozinho de queijo"], "category": "paes", "preparation": "assado", "calories_100g": 314, "protein_100g": 7.0, "carbs_100g": 42.0, "fat_100g": 13.0, "fiber_100g": 0.5, "notes": "1 unidade ≈ 30g → 94 kcal"},
    {"name": "Tapioca (goma)", "aliases": ["tapioca", "beiju"], "category": "paes", "preparation": "preparado", "calories_100g": 130, "protein_100g": 0.2, "carbs_100g": 32.0, "fat_100g": 0.0, "fiber_100g": 0.0, "notes": "100g = tapioca preparada sem recheio"},
    {"name": "Torrada simples", "aliases": ["torrada"], "category": "paes", "preparation": "torrado", "calories_100g": 380, "protein_100g": 11.0, "carbs_100g": 72.0, "fat_100g": 4.0, "fiber_100g": 3.0},
    {"name": "Biscoito cream cracker", "aliases": ["cream cracker", "bolacha cream cracker"], "category": "paes", "preparation": "industrializado", "calories_100g": 420, "protein_100g": 9.0, "carbs_100g": 68.0, "fat_100g": 12.0, "fiber_100g": 2.0},
    {"name": "Biscoito de polvilho", "aliases": ["biscoito de polvilho", "bolacha de polvilho"], "category": "paes", "preparation": "industrializado", "calories_100g": 490, "protein_100g": 4.0, "carbs_100g": 72.0, "fat_100g": 20.0, "fiber_100g": 0.5},
    {"name": "Wrap/tortilha de trigo", "aliases": ["wrap", "tortilha", "wrap de trigo"], "category": "paes", "preparation": "industrializado", "calories_100g": 295, "protein_100g": 8.0, "carbs_100g": 52.0, "fat_100g": 5.5, "fiber_100g": 2.5},
    {"name": "Pão hambúrguer", "aliases": ["pão de hambúrguer", "pão de burguer", "pão brioche"], "category": "paes", "preparation": "assado", "calories_100g": 290, "protein_100g": 9.0, "carbs_100g": 50.0, "fat_100g": 5.5, "fiber_100g": 2.0, "notes": "1 unidade ≈ 50g → 145 kcal"},

    # ── FRANGO ────────────────────────────────────────────────────────────
    {"name": "Frango peito grelhado", "aliases": ["peito de frango grelhado", "frango grelhado", "filé de frango grelhado", "frango na grelha"], "category": "carnes", "preparation": "grelhado", "calories_100g": 163, "protein_100g": 28.6, "carbs_100g": 0.0, "fat_100g": 4.7, "fiber_100g": 0.0},
    {"name": "Frango peito assado", "aliases": ["peito de frango assado", "frango assado", "frango no forno"], "category": "carnes", "preparation": "assado", "calories_100g": 163, "protein_100g": 28.6, "carbs_100g": 0.0, "fat_100g": 4.7, "fiber_100g": 0.0},
    {"name": "Frango peito cozido", "aliases": ["peito de frango cozido", "frango cozido", "frango na pressão"], "category": "carnes", "preparation": "cozido", "calories_100g": 159, "protein_100g": 28.8, "carbs_100g": 0.0, "fat_100g": 4.2, "fiber_100g": 0.0},
    {"name": "Frango peito frito empanado", "aliases": ["frango frito", "peito de frango frito", "frango empanado", "frango à milanesa"], "category": "carnes", "preparation": "frito", "calories_100g": 245, "protein_100g": 22.0, "carbs_100g": 10.0, "fat_100g": 13.0, "fiber_100g": 0.5},
    {"name": "Frango coxa e sobrecoxa assada", "aliases": ["coxa de frango", "sobrecoxa", "coxa sobrecoxa", "coxa e sobrecoxa"], "category": "carnes", "preparation": "assado", "calories_100g": 215, "protein_100g": 22.0, "carbs_100g": 0.0, "fat_100g": 13.5, "fiber_100g": 0.0},
    {"name": "Frango inteiro assado", "aliases": ["frango inteiro", "frango de churrasco"], "category": "carnes", "preparation": "assado", "calories_100g": 200, "protein_100g": 23.0, "carbs_100g": 0.0, "fat_100g": 11.5, "fiber_100g": 0.0},
    {"name": "Frango desfiado", "aliases": ["frango desfiado", "peito desfiado"], "category": "carnes", "preparation": "cozido desfiado", "calories_100g": 159, "protein_100g": 28.8, "carbs_100g": 0.0, "fat_100g": 4.2, "fiber_100g": 0.0},
    {"name": "Nuggets de frango", "aliases": ["nuggets", "chicken nuggets"], "category": "carnes", "preparation": "frito", "calories_100g": 270, "protein_100g": 15.0, "carbs_100g": 20.0, "fat_100g": 14.0, "fiber_100g": 0.5, "notes": "1 unidade ≈ 20g → 54 kcal"},

    # ── CARNE BOVINA ─────────────────────────────────────────────────────
    {"name": "Patinho grelhado", "aliases": ["patinho", "bife de patinho", "carne grelhada", "bife grelhado"], "category": "carnes", "preparation": "grelhado", "calories_100g": 219, "protein_100g": 27.5, "carbs_100g": 0.0, "fat_100g": 11.5, "fiber_100g": 0.0},
    {"name": "Alcatra grelhada", "aliases": ["alcatra", "bife de alcatra"], "category": "carnes", "preparation": "grelhado", "calories_100g": 205, "protein_100g": 26.0, "carbs_100g": 0.0, "fat_100g": 10.5, "fiber_100g": 0.0},
    {"name": "Picanha grelhada", "aliases": ["picanha", "picanha grelhada", "picanha assada"], "category": "carnes", "preparation": "grelhado", "calories_100g": 290, "protein_100g": 22.0, "carbs_100g": 0.0, "fat_100g": 22.0, "fiber_100g": 0.0},
    {"name": "Carne moída refogada", "aliases": ["carne moída", "carne picada"], "category": "carnes", "preparation": "refogado", "calories_100g": 252, "protein_100g": 20.7, "carbs_100g": 2.0, "fat_100g": 18.5, "fiber_100g": 0.0},
    {"name": "Carne de panela", "aliases": ["carne de panela", "carne cozida", "ensopado de carne", "bife acebolado"], "category": "carnes", "preparation": "cozido", "calories_100g": 200, "protein_100g": 24.0, "carbs_100g": 1.5, "fat_100g": 10.5, "fiber_100g": 0.0},
    {"name": "Costela bovina cozida", "aliases": ["costela", "costela bovina", "costelinha"], "category": "carnes", "preparation": "cozido", "calories_100g": 310, "protein_100g": 19.0, "carbs_100g": 0.0, "fat_100g": 25.0, "fiber_100g": 0.0},
    {"name": "Hambúrguer bovino grelhado", "aliases": ["hamburguer", "hambúrguer", "burger", "blend", "smash burger"], "category": "carnes", "preparation": "grelhado", "calories_100g": 250, "protein_100g": 20.0, "carbs_100g": 0.0, "fat_100g": 18.0, "fiber_100g": 0.0, "notes": "1 unidade 100g → 250 kcal"},
    {"name": "Fígado bovino frito", "aliases": ["fígado", "fígado bovino", "fígado acebolado"], "category": "carnes", "preparation": "frito", "calories_100g": 195, "protein_100g": 22.0, "carbs_100g": 5.0, "fat_100g": 9.5, "fiber_100g": 0.0},

    # ── SUÍNO ─────────────────────────────────────────────────────────────
    {"name": "Lombo suíno assado", "aliases": ["lombo", "lombo de porco", "lombo suíno"], "category": "carnes", "preparation": "assado", "calories_100g": 230, "protein_100g": 26.0, "carbs_100g": 0.0, "fat_100g": 13.5, "fiber_100g": 0.0},
    {"name": "Linguiça calabresa frita", "aliases": ["calabresa", "linguiça calabresa", "linguiça"], "category": "carnes", "preparation": "frito", "calories_100g": 350, "protein_100g": 14.0, "carbs_100g": 2.0, "fat_100g": 32.0, "fiber_100g": 0.0},
    {"name": "Linguiça toscana grelhada", "aliases": ["toscana", "linguiça toscana", "linguiça churrasco"], "category": "carnes", "preparation": "grelhado", "calories_100g": 280, "protein_100g": 16.0, "carbs_100g": 1.5, "fat_100g": 24.0, "fiber_100g": 0.0},
    {"name": "Bacon frito", "aliases": ["bacon", "bacon frito", "barriga de porco frita"], "category": "carnes", "preparation": "frito", "calories_100g": 540, "protein_100g": 12.0, "carbs_100g": 0.0, "fat_100g": 55.0, "fiber_100g": 0.0},
    {"name": "Presunto cozido fatiado", "aliases": ["presunto", "presunto fatiado"], "category": "carnes", "preparation": "industrializado", "calories_100g": 130, "protein_100g": 17.0, "carbs_100g": 2.0, "fat_100g": 6.0, "fiber_100g": 0.0},
    {"name": "Peito de peru defumado", "aliases": ["peito de peru", "peru defumado", "blanquet"], "category": "carnes", "preparation": "industrializado", "calories_100g": 115, "protein_100g": 18.5, "carbs_100g": 2.0, "fat_100g": 3.5, "fiber_100g": 0.0},
    {"name": "Salame italiano", "aliases": ["salame", "salame italiano"], "category": "carnes", "preparation": "curado", "calories_100g": 380, "protein_100g": 22.0, "carbs_100g": 1.0, "fat_100g": 32.0, "fiber_100g": 0.0},

    # ── PEIXES E FRUTOS DO MAR ────────────────────────────────────────────
    {"name": "Salmão grelhado", "aliases": ["salmão", "salmão grelhado", "salmão assado", "filé de salmão"], "category": "peixes", "preparation": "grelhado", "calories_100g": 206, "protein_100g": 28.0, "carbs_100g": 0.0, "fat_100g": 10.0, "fiber_100g": 0.0},
    {"name": "Tilápia grelhada", "aliases": ["tilápia", "tilápia grelhada", "filé de tilápia"], "category": "peixes", "preparation": "grelhado", "calories_100g": 128, "protein_100g": 26.0, "carbs_100g": 0.0, "fat_100g": 2.7, "fiber_100g": 0.0},
    {"name": "Atum em lata ao natural", "aliases": ["atum", "atum em lata", "atum em água"], "category": "peixes", "preparation": "enlatado", "calories_100g": 130, "protein_100g": 29.0, "carbs_100g": 0.0, "fat_100g": 1.5, "fiber_100g": 0.0},
    {"name": "Atum em lata com óleo", "aliases": ["atum em óleo"], "category": "peixes", "preparation": "enlatado", "calories_100g": 200, "protein_100g": 26.0, "carbs_100g": 0.0, "fat_100g": 10.0, "fiber_100g": 0.0},
    {"name": "Sardinha em lata no óleo", "aliases": ["sardinha", "sardinhas em lata"], "category": "peixes", "preparation": "enlatado", "calories_100g": 208, "protein_100g": 24.6, "carbs_100g": 0.0, "fat_100g": 12.0, "fiber_100g": 0.0},
    {"name": "Camarão cozido", "aliases": ["camarão", "camarão cozido", "camarão grelhado"], "category": "peixes", "preparation": "cozido", "calories_100g": 106, "protein_100g": 20.3, "carbs_100g": 0.9, "fat_100g": 1.7, "fiber_100g": 0.0},
    {"name": "Bacalhau cozido desfiado", "aliases": ["bacalhau", "bacalhau desfiado", "bacalhau cozido"], "category": "peixes", "preparation": "cozido", "calories_100g": 150, "protein_100g": 32.0, "carbs_100g": 0.0, "fat_100g": 1.5, "fiber_100g": 0.0},
    {"name": "Frango do mar grelhado", "aliases": ["merluza", "pescada", "pescado grelhado", "peixe grelhado", "filé de peixe"], "category": "peixes", "preparation": "grelhado", "calories_100g": 100, "protein_100g": 20.0, "carbs_100g": 0.0, "fat_100g": 2.0, "fiber_100g": 0.0},

    # ── OVOS ──────────────────────────────────────────────────────────────
    {"name": "Ovo inteiro cozido", "aliases": ["ovo", "ovo cozido", "ovo mexido", "ovos cozidos"], "category": "ovos", "preparation": "cozido", "calories_100g": 146, "protein_100g": 13.3, "carbs_100g": 0.6, "fat_100g": 9.7, "fiber_100g": 0.0, "notes": "1 ovo médio ≈ 50g → 73 kcal"},
    {"name": "Ovo mexido com óleo", "aliases": ["ovo mexido", "ovos mexidos"], "category": "ovos", "preparation": "mexido", "calories_100g": 171, "protein_100g": 11.9, "carbs_100g": 1.4, "fat_100g": 13.0, "fiber_100g": 0.0},
    {"name": "Ovo frito com óleo", "aliases": ["ovo frito", "estrelado", "ovo no sol"], "category": "ovos", "preparation": "frito", "calories_100g": 196, "protein_100g": 13.6, "carbs_100g": 0.4, "fat_100g": 15.5, "fiber_100g": 0.0},
    {"name": "Clara de ovo cozida", "aliases": ["clara de ovo", "claras"], "category": "ovos", "preparation": "cozido", "calories_100g": 52, "protein_100g": 11.0, "carbs_100g": 0.7, "fat_100g": 0.2, "fiber_100g": 0.0},
    {"name": "Omelete simples", "aliases": ["omelete", "omelette"], "category": "ovos", "preparation": "frito", "calories_100g": 175, "protein_100g": 12.0, "carbs_100g": 1.5, "fat_100g": 13.5, "fiber_100g": 0.0},

    # ── LATICÍNIOS ────────────────────────────────────────────────────────
    {"name": "Leite integral", "aliases": ["leite", "leite integral", "leite de vaca"], "category": "laticinios", "preparation": "líquido", "calories_100g": 61, "protein_100g": 3.2, "carbs_100g": 4.7, "fat_100g": 3.2, "fiber_100g": 0.0},
    {"name": "Leite desnatado", "aliases": ["leite desnatado", "leite 0% gordura"], "category": "laticinios", "preparation": "líquido", "calories_100g": 35, "protein_100g": 3.4, "carbs_100g": 4.7, "fat_100g": 0.2, "fiber_100g": 0.0},
    {"name": "Leite semidesnatado", "aliases": ["leite semidesnatado", "leite 1%", "leite 2%"], "category": "laticinios", "preparation": "líquido", "calories_100g": 47, "protein_100g": 3.3, "carbs_100g": 4.7, "fat_100g": 1.5, "fiber_100g": 0.0},
    {"name": "Iogurte natural integral", "aliases": ["iogurte", "iogurte natural", "iogurte integral"], "category": "laticinios", "preparation": "industrializado", "calories_100g": 66, "protein_100g": 4.2, "carbs_100g": 5.4, "fat_100g": 3.0, "fiber_100g": 0.0},
    {"name": "Iogurte natural desnatado", "aliases": ["iogurte desnatado", "iogurte 0% gordura"], "category": "laticinios", "preparation": "industrializado", "calories_100g": 40, "protein_100g": 4.5, "carbs_100g": 5.0, "fat_100g": 0.2, "fiber_100g": 0.0},
    {"name": "Iogurte grego integral", "aliases": ["iogurte grego", "grego", "greek yogurt"], "category": "laticinios", "preparation": "industrializado", "calories_100g": 110, "protein_100g": 9.0, "carbs_100g": 3.5, "fat_100g": 7.0, "fiber_100g": 0.0},
    {"name": "Queijo mussarela", "aliases": ["mussarela", "queijo mozzarela", "queijo mussarela", "queijo muçarela"], "category": "laticinios", "preparation": "industrializado", "calories_100g": 289, "protein_100g": 18.2, "carbs_100g": 3.0, "fat_100g": 22.5, "fiber_100g": 0.0},
    {"name": "Queijo minas frescal", "aliases": ["queijo minas", "queijo frescal", "queijo branco"], "category": "laticinios", "preparation": "industrializado", "calories_100g": 144, "protein_100g": 8.5, "carbs_100g": 3.7, "fat_100g": 10.6, "fiber_100g": 0.0},
    {"name": "Queijo minas padrão", "aliases": ["queijo minas padrão"], "category": "laticinios", "preparation": "industrializado", "calories_100g": 264, "protein_100g": 18.0, "carbs_100g": 1.5, "fat_100g": 20.5, "fiber_100g": 0.0},
    {"name": "Queijo prato", "aliases": ["queijo prato", "queijo lanche"], "category": "laticinios", "preparation": "industrializado", "calories_100g": 358, "protein_100g": 22.5, "carbs_100g": 1.8, "fat_100g": 29.5, "fiber_100g": 0.0},
    {"name": "Requeijão cremoso", "aliases": ["requeijão", "catupiry", "cream cheese brasileiro"], "category": "laticinios", "preparation": "industrializado", "calories_100g": 250, "protein_100g": 9.5, "carbs_100g": 3.0, "fat_100g": 22.5, "fiber_100g": 0.0},
    {"name": "Cream cheese", "aliases": ["cream cheese", "philadelphia"], "category": "laticinios", "preparation": "industrializado", "calories_100g": 350, "protein_100g": 6.0, "carbs_100g": 3.5, "fat_100g": 35.0, "fiber_100g": 0.0},
    {"name": "Creme de leite", "aliases": ["creme de leite", "creme de leite de caixinha", "nata"], "category": "laticinios", "preparation": "industrializado", "calories_100g": 200, "protein_100g": 2.5, "carbs_100g": 3.5, "fat_100g": 20.0, "fiber_100g": 0.0},
    {"name": "Manteiga", "aliases": ["manteiga"], "category": "gorduras", "preparation": "industrializado", "calories_100g": 726, "protein_100g": 0.6, "carbs_100g": 0.0, "fat_100g": 80.5, "fiber_100g": 0.0, "notes": "1 colher de chá ≈ 5g → 36 kcal"},
    {"name": "Margarina", "aliases": ["margarina", "creme vegetal"], "category": "gorduras", "preparation": "industrializado", "calories_100g": 540, "protein_100g": 0.5, "carbs_100g": 0.5, "fat_100g": 60.0, "fiber_100g": 0.0},
    {"name": "Whey protein pó", "aliases": ["whey", "whey protein", "proteína do soro"], "category": "suplementos", "preparation": "pó", "calories_100g": 370, "protein_100g": 75.0, "carbs_100g": 8.0, "fat_100g": 5.0, "fiber_100g": 0.0, "notes": "1 scoop ≈ 30g → 111 kcal"},

    # ── BATATAS E TUBÉRCULOS ───────────────────────────────────────────────
    {"name": "Batata inglesa cozida", "aliases": ["batata", "batata cozida", "batata inglesa"], "category": "tuberculos", "preparation": "cozido", "calories_100g": 52, "protein_100g": 1.2, "carbs_100g": 11.9, "fat_100g": 0.1, "fiber_100g": 1.8},
    {"name": "Batata-doce cozida", "aliases": ["batata doce", "batata-doce", "batata doce cozida"], "category": "tuberculos", "preparation": "cozido", "calories_100g": 77, "protein_100g": 0.6, "carbs_100g": 18.4, "fat_100g": 0.1, "fiber_100g": 2.2},
    {"name": "Batata frita imersão", "aliases": ["batata frita", "fritas", "french fries"], "category": "tuberculos", "preparation": "frito", "calories_100g": 312, "protein_100g": 3.5, "carbs_100g": 36.0, "fat_100g": 17.0, "fiber_100g": 3.0},
    {"name": "Batata frita airfryer", "aliases": ["batata airfryer", "fritas airfryer", "batata no airfryer"], "category": "tuberculos", "preparation": "airfryer", "calories_100g": 220, "protein_100g": 3.5, "carbs_100g": 36.0, "fat_100g": 7.0, "fiber_100g": 3.0},
    {"name": "Purê de batata", "aliases": ["purê de batata", "purê", "pure de batata"], "category": "tuberculos", "preparation": "preparado", "calories_100g": 90, "protein_100g": 1.5, "carbs_100g": 14.0, "fat_100g": 3.0, "fiber_100g": 1.5},
    {"name": "Mandioca cozida", "aliases": ["mandioca", "aipim", "macaxeira", "mandioca cozida"], "category": "tuberculos", "preparation": "cozido", "calories_100g": 125, "protein_100g": 0.6, "carbs_100g": 30.1, "fat_100g": 0.3, "fiber_100g": 1.9},
    {"name": "Mandioca frita", "aliases": ["mandioca frita", "aipim frito", "macaxeira frita"], "category": "tuberculos", "preparation": "frito", "calories_100g": 220, "protein_100g": 1.0, "carbs_100g": 35.0, "fat_100g": 8.5, "fiber_100g": 1.5},
    {"name": "Inhame cozido", "aliases": ["inhame", "cará"], "category": "tuberculos", "preparation": "cozido", "calories_100g": 95, "protein_100g": 2.5, "carbs_100g": 22.5, "fat_100g": 0.1, "fiber_100g": 4.2},

    # ── VEGETAIS ──────────────────────────────────────────────────────────
    {"name": "Brócolis cozido", "aliases": ["brócolis", "brocolis cozido"], "category": "vegetais", "preparation": "cozido", "calories_100g": 25, "protein_100g": 2.3, "carbs_100g": 4.3, "fat_100g": 0.4, "fiber_100g": 3.3},
    {"name": "Couve-flor cozida", "aliases": ["couve-flor", "couve flor"], "category": "vegetais", "preparation": "cozido", "calories_100g": 25, "protein_100g": 2.0, "carbs_100g": 4.5, "fat_100g": 0.3, "fiber_100g": 2.5},
    {"name": "Espinafre cozido", "aliases": ["espinafre"], "category": "vegetais", "preparation": "cozido", "calories_100g": 24, "protein_100g": 2.8, "carbs_100g": 3.5, "fat_100g": 0.5, "fiber_100g": 2.7},
    {"name": "Couve manteiga refogada", "aliases": ["couve", "couve refogada", "couve manteiga"], "category": "vegetais", "preparation": "refogado", "calories_100g": 65, "protein_100g": 3.5, "carbs_100g": 5.0, "fat_100g": 3.5, "fiber_100g": 3.5},
    {"name": "Cenoura cozida", "aliases": ["cenoura", "cenoura cozida"], "category": "vegetais", "preparation": "cozido", "calories_100g": 35, "protein_100g": 0.8, "carbs_100g": 8.0, "fat_100g": 0.2, "fiber_100g": 3.0},
    {"name": "Cenoura crua", "aliases": ["cenoura crua", "palito de cenoura"], "category": "vegetais", "preparation": "cru", "calories_100g": 34, "protein_100g": 0.6, "carbs_100g": 7.9, "fat_100g": 0.2, "fiber_100g": 2.8},
    {"name": "Abobrinha cozida", "aliases": ["abobrinha", "abobrinha cozida", "zucchini"], "category": "vegetais", "preparation": "cozido", "calories_100g": 17, "protein_100g": 1.2, "carbs_100g": 3.2, "fat_100g": 0.3, "fiber_100g": 1.5},
    {"name": "Chuchu cozido", "aliases": ["chuchu"], "category": "vegetais", "preparation": "cozido", "calories_100g": 19, "protein_100g": 0.9, "carbs_100g": 4.0, "fat_100g": 0.1, "fiber_100g": 1.5},
    {"name": "Berinjela grelhada", "aliases": ["berinjela", "berinjela grelhada", "berinjela refogada"], "category": "vegetais", "preparation": "grelhado", "calories_100g": 25, "protein_100g": 0.8, "carbs_100g": 5.0, "fat_100g": 0.3, "fiber_100g": 3.0},
    {"name": "Cebola crua", "aliases": ["cebola"], "category": "vegetais", "preparation": "cru", "calories_100g": 40, "protein_100g": 1.1, "carbs_100g": 9.3, "fat_100g": 0.1, "fiber_100g": 1.7},
    {"name": "Tomate cru", "aliases": ["tomate", "tomate cru"], "category": "vegetais", "preparation": "cru", "calories_100g": 15, "protein_100g": 0.9, "carbs_100g": 3.1, "fat_100g": 0.2, "fiber_100g": 1.2},
    {"name": "Alface cru", "aliases": ["alface", "alface crua", "folha de alface"], "category": "vegetais", "preparation": "cru", "calories_100g": 11, "protein_100g": 1.0, "carbs_100g": 1.8, "fat_100g": 0.2, "fiber_100g": 1.5},
    {"name": "Pepino cru", "aliases": ["pepino"], "category": "vegetais", "preparation": "cru", "calories_100g": 13, "protein_100g": 0.7, "carbs_100g": 2.6, "fat_100g": 0.1, "fiber_100g": 0.8},
    {"name": "Pimentão cru", "aliases": ["pimentão", "pimentão verde", "pimentão vermelho", "pimentão amarelo"], "category": "vegetais", "preparation": "cru", "calories_100g": 28, "protein_100g": 0.9, "carbs_100g": 6.3, "fat_100g": 0.3, "fiber_100g": 2.1},
    {"name": "Salada mista crua", "aliases": ["salada", "salada verde", "salada mista", "mix de folhas"], "category": "vegetais", "preparation": "cru", "calories_100g": 18, "protein_100g": 1.2, "carbs_100g": 3.2, "fat_100g": 0.3, "fiber_100g": 2.0, "notes": "estimativa média: alface + tomate + cenoura"},
    {"name": "Vagem cozida", "aliases": ["vagem"], "category": "vegetais", "preparation": "cozido", "calories_100g": 28, "protein_100g": 1.5, "carbs_100g": 6.2, "fat_100g": 0.1, "fiber_100g": 3.4},
    {"name": "Beterraba cozida", "aliases": ["beterraba", "beterraba cozida"], "category": "vegetais", "preparation": "cozido", "calories_100g": 43, "protein_100g": 1.6, "carbs_100g": 9.6, "fat_100g": 0.1, "fiber_100g": 2.6},
    {"name": "Aspargo cozido", "aliases": ["aspargo", "aspargos"], "category": "vegetais", "preparation": "cozido", "calories_100g": 25, "protein_100g": 2.9, "carbs_100g": 4.4, "fat_100g": 0.1, "fiber_100g": 2.1},

    # ── FRUTAS ────────────────────────────────────────────────────────────
    {"name": "Banana nanica", "aliases": ["banana", "banana nanica", "banana d'água"], "category": "frutas", "preparation": "cru", "calories_100g": 92, "protein_100g": 1.3, "carbs_100g": 23.8, "fat_100g": 0.1, "fiber_100g": 1.9, "notes": "1 unidade média ≈ 90g → 83 kcal"},
    {"name": "Banana prata", "aliases": ["banana prata", "banana comum"], "category": "frutas", "preparation": "cru", "calories_100g": 98, "protein_100g": 1.2, "carbs_100g": 25.8, "fat_100g": 0.1, "fiber_100g": 2.0},
    {"name": "Maçã fuji", "aliases": ["maçã", "maçã fuji", "maçã gala", "maçã verde"], "category": "frutas", "preparation": "cru", "calories_100g": 56, "protein_100g": 0.3, "carbs_100g": 15.2, "fat_100g": 0.0, "fiber_100g": 1.4, "notes": "1 unidade média ≈ 160g → 90 kcal"},
    {"name": "Laranja pera", "aliases": ["laranja", "laranja pera", "laranja bahia"], "category": "frutas", "preparation": "cru", "calories_100g": 49, "protein_100g": 0.9, "carbs_100g": 12.5, "fat_100g": 0.1, "fiber_100g": 2.4, "notes": "1 unidade média ≈ 130g (sem casca) → 64 kcal"},
    {"name": "Mamão formosa", "aliases": ["mamão", "mamão papaia", "papaya"], "category": "frutas", "preparation": "cru", "calories_100g": 40, "protein_100g": 0.5, "carbs_100g": 10.4, "fat_100g": 0.1, "fiber_100g": 1.8},
    {"name": "Melancia", "aliases": ["melancia"], "category": "frutas", "preparation": "cru", "calories_100g": 33, "protein_100g": 0.7, "carbs_100g": 8.0, "fat_100g": 0.1, "fiber_100g": 0.4},
    {"name": "Manga palmer", "aliases": ["manga", "manga palmer", "manga tommy"], "category": "frutas", "preparation": "cru", "calories_100g": 57, "protein_100g": 0.8, "carbs_100g": 14.6, "fat_100g": 0.3, "fiber_100g": 1.6},
    {"name": "Uva", "aliases": ["uva", "uva itália", "uva rubi", "uva thompson"], "category": "frutas", "preparation": "cru", "calories_100g": 69, "protein_100g": 0.9, "carbs_100g": 17.0, "fat_100g": 0.3, "fiber_100g": 0.9},
    {"name": "Morango", "aliases": ["morango", "morangos"], "category": "frutas", "preparation": "cru", "calories_100g": 32, "protein_100g": 0.7, "carbs_100g": 7.7, "fat_100g": 0.3, "fiber_100g": 2.1},
    {"name": "Abacaxi", "aliases": ["abacaxi", "ananás", "piña"], "category": "frutas", "preparation": "cru", "calories_100g": 48, "protein_100g": 0.6, "carbs_100g": 12.5, "fat_100g": 0.1, "fiber_100g": 1.2},
    {"name": "Abacate", "aliases": ["abacate", "avocado"], "category": "frutas", "preparation": "cru", "calories_100g": 160, "protein_100g": 1.5, "carbs_100g": 8.5, "fat_100g": 14.5, "fiber_100g": 6.3},
    {"name": "Açaí polpa pura", "aliases": ["açaí", "açaí puro", "polpa de açaí"], "category": "frutas", "preparation": "congelado", "calories_100g": 58, "protein_100g": 1.2, "carbs_100g": 6.2, "fat_100g": 3.2, "fiber_100g": 2.6},
    {"name": "Açaí na tigela com granola e banana", "aliases": ["açaí na tigela", "tigela de açaí", "bowl de açaí"], "category": "frutas", "preparation": "preparado", "calories_100g": 165, "protein_100g": 2.5, "carbs_100g": 28.0, "fat_100g": 5.5, "fiber_100g": 2.5, "notes": "1 tigela 300ml ≈ 495 kcal"},
    {"name": "Melão", "aliases": ["melão"], "category": "frutas", "preparation": "cru", "calories_100g": 29, "protein_100g": 0.8, "carbs_100g": 6.7, "fat_100g": 0.1, "fiber_100g": 0.4},
    {"name": "Pêssego", "aliases": ["pêssego", "pessego"], "category": "frutas", "preparation": "cru", "calories_100g": 39, "protein_100g": 0.9, "carbs_100g": 9.7, "fat_100g": 0.1, "fiber_100g": 1.5},

    # ── GORDURAS E OLEAGINOSAS ────────────────────────────────────────────
    {"name": "Azeite de oliva", "aliases": ["azeite", "azeite de oliva", "olive oil"], "category": "gorduras", "preparation": "cru", "calories_100g": 884, "protein_100g": 0.0, "carbs_100g": 0.0, "fat_100g": 100.0, "fiber_100g": 0.0, "notes": "1 colher de sopa ≈ 13ml → 115 kcal"},
    {"name": "Óleo de soja", "aliases": ["óleo", "óleo de soja", "óleo vegetal", "óleo de girassol", "óleo de milho"], "category": "gorduras", "preparation": "cru", "calories_100g": 884, "protein_100g": 0.0, "carbs_100g": 0.0, "fat_100g": 100.0, "fiber_100g": 0.0, "notes": "1 colher de sopa ≈ 13ml → 115 kcal"},
    {"name": "Óleo de coco", "aliases": ["óleo de coco"], "category": "gorduras", "preparation": "cru", "calories_100g": 892, "protein_100g": 0.0, "carbs_100g": 0.0, "fat_100g": 99.0, "fiber_100g": 0.0},
    {"name": "Pasta de amendoim integral", "aliases": ["pasta de amendoim", "manteiga de amendoim", "peanut butter"], "category": "gorduras", "preparation": "industrializado", "calories_100g": 598, "protein_100g": 25.0, "carbs_100g": 20.0, "fat_100g": 50.0, "fiber_100g": 6.0, "notes": "1 colher de sopa ≈ 16g → 96 kcal"},
    {"name": "Amendoim torrado", "aliases": ["amendoim", "amendoim torrado", "paçoca"], "category": "gorduras", "preparation": "torrado", "calories_100g": 567, "protein_100g": 25.8, "carbs_100g": 20.0, "fat_100g": 45.4, "fiber_100g": 6.5},
    {"name": "Castanha do Pará", "aliases": ["castanha do pará", "castanha do brasil", "castanha"], "category": "gorduras", "preparation": "cru", "calories_100g": 655, "protein_100g": 14.5, "carbs_100g": 12.3, "fat_100g": 63.5, "fiber_100g": 6.8},
    {"name": "Castanha de caju torrada", "aliases": ["castanha de caju", "caju torrado"], "category": "gorduras", "preparation": "torrado", "calories_100g": 570, "protein_100g": 15.3, "carbs_100g": 32.7, "fat_100g": 44.8, "fiber_100g": 3.0},
    {"name": "Nozes", "aliases": ["nozes", "noz"], "category": "gorduras", "preparation": "cru", "calories_100g": 620, "protein_100g": 15.2, "carbs_100g": 10.6, "fat_100g": 58.8, "fiber_100g": 4.3},
    {"name": "Amêndoa", "aliases": ["amêndoa", "amêndoas", "amendoa"], "category": "gorduras", "preparation": "cru", "calories_100g": 579, "protein_100g": 21.2, "carbs_100g": 21.7, "fat_100g": 49.4, "fiber_100g": 12.5},

    # ── AÇÚCARES E DOCES ──────────────────────────────────────────────────
    {"name": "Açúcar refinado", "aliases": ["açúcar", "açúcar refinado", "açúcar branco"], "category": "acucares", "preparation": "industrializado", "calories_100g": 387, "protein_100g": 0.0, "carbs_100g": 99.9, "fat_100g": 0.0, "fiber_100g": 0.0, "notes": "1 colher de sopa ≈ 12g → 46 kcal"},
    {"name": "Açúcar mascavo", "aliases": ["açúcar mascavo", "demerara"], "category": "acucares", "preparation": "industrializado", "calories_100g": 375, "protein_100g": 0.0, "carbs_100g": 95.5, "fat_100g": 0.0, "fiber_100g": 0.0},
    {"name": "Mel de abelha", "aliases": ["mel", "mel de abelha"], "category": "acucares", "preparation": "natural", "calories_100g": 309, "protein_100g": 0.4, "carbs_100g": 82.4, "fat_100g": 0.0, "fiber_100g": 0.0},
    {"name": "Chocolate ao leite", "aliases": ["chocolate", "chocolate ao leite", "barra de chocolate"], "category": "acucares", "preparation": "industrializado", "calories_100g": 535, "protein_100g": 7.0, "carbs_100g": 60.0, "fat_100g": 29.0, "fiber_100g": 2.0},
    {"name": "Chocolate meio amargo 70%", "aliases": ["chocolate amargo", "chocolate meio amargo", "dark chocolate"], "category": "acucares", "preparation": "industrializado", "calories_100g": 580, "protein_100g": 8.0, "carbs_100g": 42.0, "fat_100g": 42.0, "fiber_100g": 8.0},
    {"name": "Sorvete de creme", "aliases": ["sorvete", "sorvete de creme", "ice cream"], "category": "acucares", "preparation": "industrializado", "calories_100g": 207, "protein_100g": 3.5, "carbs_100g": 26.0, "fat_100g": 10.5, "fiber_100g": 0.0},
    {"name": "Brigadeiro", "aliases": ["brigadeiro"], "category": "acucares", "preparation": "preparado", "calories_100g": 350, "protein_100g": 4.5, "carbs_100g": 52.0, "fat_100g": 14.0, "fiber_100g": 0.5, "notes": "1 unidade ≈ 20g → 70 kcal"},

    # ── BEBIDAS ───────────────────────────────────────────────────────────
    {"name": "Café preto sem açúcar", "aliases": ["café", "café preto", "café sem açúcar", "espresso"], "category": "bebidas", "preparation": "preparado", "calories_100g": 2, "protein_100g": 0.1, "carbs_100g": 0.0, "fat_100g": 0.0, "fiber_100g": 0.0},
    {"name": "Suco de laranja natural", "aliases": ["suco de laranja", "suco natural", "laranjada"], "category": "bebidas", "preparation": "natural", "calories_100g": 45, "protein_100g": 0.7, "carbs_100g": 10.4, "fat_100g": 0.2, "fiber_100g": 0.2},
    {"name": "Suco de fruta industrializado", "aliases": ["suco de caixinha", "suco industrializado", "néctar de fruta"], "category": "bebidas", "preparation": "industrializado", "calories_100g": 55, "protein_100g": 0.2, "carbs_100g": 13.5, "fat_100g": 0.1, "fiber_100g": 0.1},
    {"name": "Refrigerante cola", "aliases": ["coca cola", "coca-cola", "pepsi", "refrigerante", "soda"], "category": "bebidas", "preparation": "industrializado", "calories_100g": 40, "protein_100g": 0.0, "carbs_100g": 10.6, "fat_100g": 0.0, "fiber_100g": 0.0, "notes": "1 lata 350ml → 140 kcal"},
    {"name": "Refrigerante zero", "aliases": ["coca zero", "pepsi black", "refrigerante zero", "refrigerante diet"], "category": "bebidas", "preparation": "industrializado", "calories_100g": 0, "protein_100g": 0.0, "carbs_100g": 0.0, "fat_100g": 0.0, "fiber_100g": 0.0},
    {"name": "Cerveja comum", "aliases": ["cerveja", "cerveja lager", "cerveja pilsen", "beer"], "category": "bebidas", "preparation": "industrializado", "calories_100g": 43, "protein_100g": 0.3, "carbs_100g": 3.5, "fat_100g": 0.0, "fiber_100g": 0.0, "notes": "1 long neck 355ml → 153 kcal | 1 lata 350ml → 151 kcal"},
    {"name": "Água de coco", "aliases": ["água de coco", "água de coco natural"], "category": "bebidas", "preparation": "natural", "calories_100g": 19, "protein_100g": 0.2, "carbs_100g": 4.0, "fat_100g": 0.1, "fiber_100g": 0.1},
    {"name": "Chá verde sem açúcar", "aliases": ["chá verde", "chá sem açúcar", "chá"], "category": "bebidas", "preparation": "preparado", "calories_100g": 1, "protein_100g": 0.0, "carbs_100g": 0.2, "fat_100g": 0.0, "fiber_100g": 0.0},
    {"name": "Leite com achocolatado", "aliases": ["achocolatado", "leite com chocolate", "nescau", "toddy", "ovomaltine"], "category": "bebidas", "preparation": "preparado", "calories_100g": 78, "protein_100g": 3.0, "carbs_100g": 12.5, "fat_100g": 2.0, "fiber_100g": 0.3, "notes": "200ml ≈ 156 kcal"},
    {"name": "Vitamina de banana com leite", "aliases": ["vitamina", "vitamina de banana", "vitamina de fruta"], "category": "bebidas", "preparation": "preparado", "calories_100g": 85, "protein_100g": 2.8, "carbs_100g": 17.0, "fat_100g": 1.5, "fiber_100g": 0.8, "notes": "200ml ≈ 170 kcal"},
    {"name": "Whey protein shake", "aliases": ["shake de whey", "shake proteico"], "category": "suplementos", "preparation": "preparado", "calories_100g": 65, "protein_100g": 12.0, "carbs_100g": 4.5, "fat_100g": 1.0, "fiber_100g": 0.3, "notes": "1 dose (30g whey + 250ml leite desnatado) ≈ 200ml → 200 kcal"},

    # ── FAST FOOD ─────────────────────────────────────────────────────────
    {"name": "Big Mac McDonald's", "aliases": ["big mac", "bigmac"], "category": "fastfood", "preparation": "industrializado", "calories_100g": 257, "protein_100g": 11.9, "carbs_100g": 20.1, "fat_100g": 14.8, "fiber_100g": 1.4, "notes": "1 unidade 219g → 563 kcal"},
    {"name": "McDouble McDonald's", "aliases": ["mcdouble", "mc double", "mequi double"], "category": "fastfood", "preparation": "industrializado", "calories_100g": 270, "protein_100g": 15.3, "carbs_100g": 22.1, "fat_100g": 13.5, "fiber_100g": 1.2, "notes": "1 unidade 163g → 440 kcal"},
    {"name": "Fritas pequenas McDonald's", "aliases": ["mc fritas pequenas", "fritas small"], "category": "fastfood", "preparation": "industrializado", "calories_100g": 278, "protein_100g": 3.0, "carbs_100g": 36.5, "fat_100g": 13.9, "fiber_100g": 3.0, "notes": "1 porção 115g → 320 kcal"},
    {"name": "Fritas médias McDonald's", "aliases": ["mc fritas médias", "fritas medium"], "category": "fastfood", "preparation": "industrializado", "calories_100g": 279, "protein_100g": 2.9, "carbs_100g": 36.4, "fat_100g": 13.6, "fiber_100g": 2.9, "notes": "1 porção 154g → 430 kcal"},
    {"name": "Whopper Burger King", "aliases": ["whopper", "burger king whopper"], "category": "fastfood", "preparation": "industrializado", "calories_100g": 226, "protein_100g": 9.6, "carbs_100g": 16.8, "fat_100g": 13.7, "fiber_100g": 0.7, "notes": "1 unidade 291g → 657 kcal"},
    {"name": "Pizza mussarela", "aliases": ["pizza", "pizza de queijo", "pizza muçarela"], "category": "fastfood", "preparation": "assado", "calories_100g": 250, "protein_100g": 12.0, "carbs_100g": 28.0, "fat_100g": 10.0, "fiber_100g": 1.5, "notes": "1 fatia média ≈ 100g → 250 kcal"},
    {"name": "Pizza calabresa", "aliases": ["pizza calabresa", "pizza de linguiça"], "category": "fastfood", "preparation": "assado", "calories_100g": 270, "protein_100g": 11.0, "carbs_100g": 27.0, "fat_100g": 13.0, "fiber_100g": 1.5, "notes": "1 fatia média ≈ 100g → 270 kcal"},
    {"name": "Coxinha de frango", "aliases": ["coxinha", "coxinha de frango"], "category": "fastfood", "preparation": "frito", "calories_100g": 290, "protein_100g": 12.0, "carbs_100g": 29.0, "fat_100g": 14.0, "fiber_100g": 1.0, "notes": "1 unidade ≈ 100g → 290 kcal"},
    {"name": "Hot dog completo", "aliases": ["hot dog", "cachorro quente", "dog completo"], "category": "fastfood", "preparation": "preparado", "calories_100g": 210, "protein_100g": 8.0, "carbs_100g": 20.0, "fat_100g": 11.0, "fiber_100g": 1.0, "notes": "1 unidade completa ≈ 200g → 420 kcal"},
    {"name": "Esfirra aberta de carne", "aliases": ["esfirra", "esfiha", "esfirra de carne"], "category": "fastfood", "preparation": "assado", "calories_100g": 275, "protein_100g": 11.3, "carbs_100g": 31.3, "fat_100g": 11.9, "fiber_100g": 1.3, "notes": "1 unidade ≈ 80g → 220 kcal"},

    # ── SUPLEMENTOS ───────────────────────────────────────────────────────
    {"name": "Creatina monohidratada", "aliases": ["creatina", "creatine"], "category": "suplementos", "preparation": "pó", "calories_100g": 0, "protein_100g": 0.0, "carbs_100g": 0.0, "fat_100g": 0.0, "fiber_100g": 0.0, "notes": "1 dose = 5g → 0 kcal"},
    {"name": "Barra de proteína", "aliases": ["barra de proteína", "protein bar", "barra proteica"], "category": "suplementos", "preparation": "industrializado", "calories_100g": 380, "protein_100g": 35.0, "carbs_100g": 35.0, "fat_100g": 10.0, "fiber_100g": 5.0, "notes": "1 barra ≈ 60g → 228 kcal"},
    {"name": "Hipercalórico", "aliases": ["hipercalórico", "mass gainer", "massa muscular"], "category": "suplementos", "preparation": "pó", "calories_100g": 400, "protein_100g": 17.0, "carbs_100g": 73.0, "fat_100g": 4.0, "fiber_100g": 1.0, "notes": "1 dose ≈ 150g → 600 kcal"},
    {"name": "BCAA em pó", "aliases": ["bcaa", "aminoácido"], "category": "suplementos", "preparation": "pó", "calories_100g": 400, "protein_100g": 100.0, "carbs_100g": 0.0, "fat_100g": 0.0, "fiber_100g": 0.0, "notes": "1 dose ≈ 5-10g → 20-40 kcal"},

    # ── PRATOS PRONTOS TÍPICOS ────────────────────────────────────────────
    {"name": "Feijoada completa", "aliases": ["feijoada", "feijoada completa"], "category": "pratos", "preparation": "preparado", "calories_100g": 110, "protein_100g": 7.0, "carbs_100g": 9.0, "fat_100g": 5.0, "fiber_100g": 4.5, "notes": "1 prato (350g) ≈ 385 kcal"},
    {"name": "Moqueca de peixe", "aliases": ["moqueca", "moqueca de peixe", "moqueca de camarão"], "category": "pratos", "preparation": "preparado", "calories_100g": 120, "protein_100g": 12.0, "carbs_100g": 5.0, "fat_100g": 6.5, "fiber_100g": 1.0},
    {"name": "Frango com quiabo", "aliases": ["frango com quiabo"], "category": "pratos", "preparation": "preparado", "calories_100g": 130, "protein_100g": 14.0, "carbs_100g": 4.0, "fat_100g": 7.0, "fiber_100g": 2.0},
    {"name": "Carne seca com mandioca", "aliases": ["carne seca", "carne de sol", "carne seca com aipim"], "category": "pratos", "preparation": "preparado", "calories_100g": 180, "protein_100g": 16.0, "carbs_100g": 12.0, "fat_100g": 8.0, "fiber_100g": 1.5},
    {"name": "Macarrão com carne bolonhesa", "aliases": ["macarrão à bolonhesa", "espaguete à bolonhesa", "macarrão com carne"], "category": "pratos", "preparation": "preparado", "calories_100g": 155, "protein_100g": 8.0, "carbs_100g": 18.0, "fat_100g": 5.5, "fiber_100g": 1.5},
    {"name": "Strogonoff de frango", "aliases": ["strogonoff", "estrogonofe", "strogonoff de frango"], "category": "pratos", "preparation": "preparado", "calories_100g": 140, "protein_100g": 13.0, "carbs_100g": 6.0, "fat_100g": 7.5, "fiber_100g": 0.5},
    {"name": "Arroz com feijão (prato básico)", "aliases": ["arroz com feijão", "arroz e feijão", "prato feito", "pf"], "category": "pratos", "preparation": "preparado", "calories_100g": 105, "protein_100g": 3.7, "carbs_100g": 21.5, "fat_100g": 0.4, "fiber_100g": 3.5, "notes": "estimativa: 60% arroz + 40% feijão"},
]


async def seed(db: AsyncSession) -> None:
    existing = await db.scalar(select(TacoFood).limit(1))
    if existing:
        print("✓ Tabela taco_foods já populada. Use --force para recriar.")
        return

    foods = [TacoFood(**{k: v for k, v in item.items() if k != "notes"}, **{"notes": item.get("notes")}) for item in TACO_DATA]
    db.add_all(foods)
    await db.commit()
    print(f"✓ {len(foods)} alimentos inseridos na tabela taco_foods.")


async def seed_force(db: AsyncSession) -> None:
    await db.execute(delete(TacoFood))
    await db.commit()
    await seed(db)


async def main() -> None:
    force = "--force" in sys.argv
    async with AsyncSessionLocal() as db:
        if force:
            print("Recriando tabela taco_foods...")
            await seed_force(db)
        else:
            await seed(db)


if __name__ == "__main__":
    asyncio.run(main())

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

    # ── CORTES BOVINOS ADICIONAIS ─────────────────────────────────────────
    {"name": "Fraldinha grelhada", "aliases": ["fraldinha", "fraldinha grelhada", "fraldinha assada"], "category": "carnes", "preparation": "grelhado", "calories_100g": 248, "protein_100g": 26.5, "carbs_100g": 0.0, "fat_100g": 15.5, "fiber_100g": 0.0},
    {"name": "Maminha grelhada", "aliases": ["maminha", "bife de maminha"], "category": "carnes", "preparation": "grelhado", "calories_100g": 218, "protein_100g": 27.0, "carbs_100g": 0.0, "fat_100g": 12.0, "fiber_100g": 0.0},
    {"name": "Contrafilé grelhado", "aliases": ["contrafilé", "bife de contrafilé", "entrecote"], "category": "carnes", "preparation": "grelhado", "calories_100g": 242, "protein_100g": 25.5, "carbs_100g": 0.0, "fat_100g": 15.0, "fiber_100g": 0.0},
    {"name": "Filé mignon grelhado", "aliases": ["filé mignon", "filé mignon grelhado", "medalhão de filé"], "category": "carnes", "preparation": "grelhado", "calories_100g": 215, "protein_100g": 28.0, "carbs_100g": 0.0, "fat_100g": 11.0, "fiber_100g": 0.0},
    {"name": "Acém cozido", "aliases": ["acém", "acém cozido", "carne de segunda"], "category": "carnes", "preparation": "cozido", "calories_100g": 210, "protein_100g": 23.5, "carbs_100g": 0.0, "fat_100g": 12.5, "fiber_100g": 0.0},
    {"name": "Carne de sol grelhada", "aliases": ["carne de sol", "carne de sol grelhada", "carne de sol assada"], "category": "carnes", "preparation": "grelhado", "calories_100g": 220, "protein_100g": 28.5, "carbs_100g": 0.0, "fat_100g": 11.5, "fiber_100g": 0.0, "notes": "já dessalgada"},
    {"name": "Charque cozido", "aliases": ["charque", "jabá", "carne seca cozida", "jerked beef"], "category": "carnes", "preparation": "cozido", "calories_100g": 238, "protein_100g": 30.0, "carbs_100g": 0.0, "fat_100g": 13.0, "fiber_100g": 0.0, "notes": "já dessalgado e cozido"},
    {"name": "Rabada cozida", "aliases": ["rabada", "rabo de boi", "rabada com agrião"], "category": "carnes", "preparation": "cozido", "calories_100g": 250, "protein_100g": 21.5, "carbs_100g": 0.5, "fat_100g": 18.0, "fiber_100g": 0.0},

    # ── SUÍNO ADICIONAL ───────────────────────────────────────────────────
    {"name": "Costela suína assada", "aliases": ["costela de porco", "costela suína", "costelinha de porco"], "category": "carnes", "preparation": "assado", "calories_100g": 280, "protein_100g": 21.0, "carbs_100g": 0.0, "fat_100g": 22.0, "fiber_100g": 0.0},
    {"name": "Pernil suíno assado", "aliases": ["pernil", "pernil de porco", "pernil assado"], "category": "carnes", "preparation": "assado", "calories_100g": 240, "protein_100g": 24.0, "carbs_100g": 0.0, "fat_100g": 15.5, "fiber_100g": 0.0},
    {"name": "Mortadela fatiada", "aliases": ["mortadela", "mortadela fatiada"], "category": "carnes", "preparation": "industrializado", "calories_100g": 260, "protein_100g": 12.0, "carbs_100g": 2.5, "fat_100g": 23.0, "fiber_100g": 0.0},
    {"name": "Salsicha viena cozida", "aliases": ["salsicha", "salsicha viena", "salsicha hot dog", "frankfurter"], "category": "carnes", "preparation": "cozido", "calories_100g": 198, "protein_100g": 11.5, "carbs_100g": 2.0, "fat_100g": 16.5, "fiber_100g": 0.0, "notes": "1 unidade ≈ 50g → 99 kcal"},
    {"name": "Linguiça de frango grelhada", "aliases": ["linguiça de frango", "salsicha de frango"], "category": "carnes", "preparation": "grelhado", "calories_100g": 195, "protein_100g": 18.0, "carbs_100g": 2.5, "fat_100g": 13.0, "fiber_100g": 0.0},
    {"name": "Paio fatiado", "aliases": ["paio", "paio fatiado"], "category": "carnes", "preparation": "industrializado", "calories_100g": 318, "protein_100g": 16.0, "carbs_100g": 2.0, "fat_100g": 28.0, "fiber_100g": 0.0},
    {"name": "Galinha caipira cozida", "aliases": ["galinha caipira", "galinha d'angola", "frango caipira"], "category": "carnes", "preparation": "cozido", "calories_100g": 178, "protein_100g": 23.0, "carbs_100g": 0.0, "fat_100g": 9.0, "fiber_100g": 0.0},

    # ── PEIXES E FRUTOS DO MAR ADICIONAIS ─────────────────────────────────
    {"name": "Lula frita empanada", "aliases": ["lula", "lula frita", "anéis de lula"], "category": "peixes", "preparation": "frito", "calories_100g": 175, "protein_100g": 15.0, "carbs_100g": 8.0, "fat_100g": 9.0, "fiber_100g": 0.5},
    {"name": "Polvo cozido", "aliases": ["polvo", "polvo cozido", "polvo grelhado"], "category": "peixes", "preparation": "cozido", "calories_100g": 164, "protein_100g": 29.8, "carbs_100g": 4.4, "fat_100g": 2.1, "fiber_100g": 0.0},
    {"name": "Mexilhão cozido", "aliases": ["mexilhão", "mariscos", "marisco cozido"], "category": "peixes", "preparation": "cozido", "calories_100g": 172, "protein_100g": 23.8, "carbs_100g": 7.4, "fat_100g": 4.5, "fiber_100g": 0.0},
    {"name": "Salmão cru (sashimi)", "aliases": ["sashimi de salmão", "salmão cru", "sashimi"], "category": "peixes", "preparation": "cru", "calories_100g": 142, "protein_100g": 20.0, "carbs_100g": 0.0, "fat_100g": 7.0, "fiber_100g": 0.0},
    {"name": "Atum cru (sashimi)", "aliases": ["sashimi de atum", "atum cru"], "category": "peixes", "preparation": "cru", "calories_100g": 108, "protein_100g": 23.0, "carbs_100g": 0.0, "fat_100g": 1.0, "fiber_100g": 0.0},

    # ── LATICÍNIOS ADICIONAIS ─────────────────────────────────────────────
    {"name": "Queijo coalho grelhado", "aliases": ["queijo coalho", "queijo de coalho", "coalho grelhado", "coalho na brasa"], "category": "laticinios", "preparation": "grelhado", "calories_100g": 330, "protein_100g": 22.0, "carbs_100g": 1.0, "fat_100g": 27.0, "fiber_100g": 0.0, "notes": "1 espeto ≈ 50g → 165 kcal"},
    {"name": "Queijo provolone", "aliases": ["provolone", "queijo provolone", "provolone grelhado"], "category": "laticinios", "preparation": "industrializado", "calories_100g": 352, "protein_100g": 25.6, "carbs_100g": 2.1, "fat_100g": 26.6, "fiber_100g": 0.0},
    {"name": "Queijo parmesão ralado", "aliases": ["parmesão", "queijo parmesão", "parmesão ralado", "parmeggiano"], "category": "laticinios", "preparation": "industrializado", "calories_100g": 431, "protein_100g": 38.0, "carbs_100g": 4.0, "fat_100g": 29.0, "fiber_100g": 0.0, "notes": "1 colher de sopa ≈ 10g → 43 kcal"},
    {"name": "Queijo gouda", "aliases": ["gouda", "queijo gouda"], "category": "laticinios", "preparation": "industrializado", "calories_100g": 356, "protein_100g": 25.0, "carbs_100g": 2.2, "fat_100g": 27.4, "fiber_100g": 0.0},
    {"name": "Ricota fresca", "aliases": ["ricota", "ricota fresca", "ricotta"], "category": "laticinios", "preparation": "industrializado", "calories_100g": 134, "protein_100g": 8.0, "carbs_100g": 3.0, "fat_100g": 10.0, "fiber_100g": 0.0},
    {"name": "Leite condensado", "aliases": ["leite condensado", "leite condensado integral"], "category": "laticinios", "preparation": "industrializado", "calories_100g": 327, "protein_100g": 8.0, "carbs_100g": 55.0, "fat_100g": 9.0, "fiber_100g": 0.0, "notes": "1 colher de sopa ≈ 20g → 65 kcal"},
    {"name": "Coalhada seca", "aliases": ["coalhada seca", "coalhada", "labneh"], "category": "laticinios", "preparation": "industrializado", "calories_100g": 130, "protein_100g": 9.0, "carbs_100g": 4.0, "fat_100g": 9.0, "fiber_100g": 0.0},
    {"name": "Kefir natural integral", "aliases": ["kefir", "kefir de leite", "kefir natural"], "category": "laticinios", "preparation": "fermentado", "calories_100g": 63, "protein_100g": 3.4, "carbs_100g": 4.6, "fat_100g": 3.5, "fiber_100g": 0.0},
    {"name": "Chantilly", "aliases": ["chantilly", "creme chantilly", "chantininho", "nata batida"], "category": "laticinios", "preparation": "industrializado", "calories_100g": 257, "protein_100g": 2.0, "carbs_100g": 16.0, "fat_100g": 21.0, "fiber_100g": 0.0},

    # ── VEGETAIS ADICIONAIS ───────────────────────────────────────────────
    {"name": "Abóbora cozida", "aliases": ["abóbora", "abóbora cozida", "moranga", "abóbora cabotiá", "jerimum"], "category": "vegetais", "preparation": "cozido", "calories_100g": 26, "protein_100g": 1.2, "carbs_100g": 6.5, "fat_100g": 0.1, "fiber_100g": 1.0},
    {"name": "Abóbora assada", "aliases": ["abóbora assada", "moranga assada", "abóbora no forno"], "category": "vegetais", "preparation": "assado", "calories_100g": 40, "protein_100g": 1.5, "carbs_100g": 9.5, "fat_100g": 0.2, "fiber_100g": 1.5},
    {"name": "Quiabo cozido", "aliases": ["quiabo", "quiabo cozido", "quiabo refogado"], "category": "vegetais", "preparation": "cozido", "calories_100g": 25, "protein_100g": 1.9, "carbs_100g": 5.1, "fat_100g": 0.2, "fiber_100g": 2.5},
    {"name": "Rúcula crua", "aliases": ["rúcula", "rúcula crua", "folha de rúcula"], "category": "vegetais", "preparation": "cru", "calories_100g": 25, "protein_100g": 2.6, "carbs_100g": 3.7, "fat_100g": 0.7, "fiber_100g": 1.6},
    {"name": "Agrião cru", "aliases": ["agrião", "agrião cru"], "category": "vegetais", "preparation": "cru", "calories_100g": 21, "protein_100g": 2.3, "carbs_100g": 2.9, "fat_100g": 0.3, "fiber_100g": 0.7},
    {"name": "Almeirão cru", "aliases": ["almeirão", "chicória amarga"], "category": "vegetais", "preparation": "cru", "calories_100g": 20, "protein_100g": 1.8, "carbs_100g": 3.4, "fat_100g": 0.3, "fiber_100g": 2.0},
    {"name": "Palmito em conserva", "aliases": ["palmito", "palmito pupunha", "palmito juçara"], "category": "vegetais", "preparation": "conserva", "calories_100g": 28, "protein_100g": 2.7, "carbs_100g": 4.0, "fat_100g": 0.2, "fiber_100g": 1.0},
    {"name": "Jiló cozido", "aliases": ["jiló", "jiló cozido", "jiló refogado"], "category": "vegetais", "preparation": "cozido", "calories_100g": 21, "protein_100g": 1.0, "carbs_100g": 4.6, "fat_100g": 0.1, "fiber_100g": 1.8},
    {"name": "Milho em espiga assada", "aliases": ["milho assado", "espiga assada", "milho na brasa"], "category": "vegetais", "preparation": "assado", "calories_100g": 119, "protein_100g": 3.6, "carbs_100g": 26.0, "fat_100g": 1.5, "fiber_100g": 2.4},
    {"name": "Maxixe cozido", "aliases": ["maxixe", "maxixe cozido"], "category": "vegetais", "preparation": "cozido", "calories_100g": 17, "protein_100g": 0.9, "carbs_100g": 3.5, "fat_100g": 0.1, "fiber_100g": 1.3},
    {"name": "Nabo cozido", "aliases": ["nabo", "nabo cozido"], "category": "vegetais", "preparation": "cozido", "calories_100g": 22, "protein_100g": 0.9, "carbs_100g": 4.8, "fat_100g": 0.1, "fiber_100g": 1.5},
    {"name": "Rabanete cru", "aliases": ["rabanete", "rabanete cru"], "category": "vegetais", "preparation": "cru", "calories_100g": 16, "protein_100g": 0.7, "carbs_100g": 3.4, "fat_100g": 0.1, "fiber_100g": 1.6},
    {"name": "Couve-flor crua", "aliases": ["couve-flor crua", "couve flor crua"], "category": "vegetais", "preparation": "cru", "calories_100g": 25, "protein_100g": 2.0, "carbs_100g": 5.0, "fat_100g": 0.3, "fiber_100g": 2.0},
    {"name": "Milho verde enlatado", "aliases": ["milho de lata", "milho em conserva", "milho enlatado"], "category": "vegetais", "preparation": "enlatado", "calories_100g": 70, "protein_100g": 2.5, "carbs_100g": 15.0, "fat_100g": 0.6, "fiber_100g": 1.8},

    # ── FRUTAS ADICIONAIS ──────────────────────────────────────────────────
    {"name": "Goiaba vermelha", "aliases": ["goiaba", "goiaba vermelha", "goiaba branca"], "category": "frutas", "preparation": "cru", "calories_100g": 54, "protein_100g": 2.3, "carbs_100g": 12.0, "fat_100g": 0.5, "fiber_100g": 6.3, "notes": "1 unidade média ≈ 120g → 65 kcal"},
    {"name": "Acerola fresca", "aliases": ["acerola", "cereja do nordeste"], "category": "frutas", "preparation": "cru", "calories_100g": 32, "protein_100g": 0.8, "carbs_100g": 7.7, "fat_100g": 0.2, "fiber_100g": 1.3},
    {"name": "Caju fresco", "aliases": ["caju", "caju fresco", "pedúnculo do caju"], "category": "frutas", "preparation": "cru", "calories_100g": 48, "protein_100g": 1.3, "carbs_100g": 11.6, "fat_100g": 0.2, "fiber_100g": 1.7},
    {"name": "Kiwi", "aliases": ["kiwi", "kiwi verde", "kiwi amarelo"], "category": "frutas", "preparation": "cru", "calories_100g": 61, "protein_100g": 1.1, "carbs_100g": 15.2, "fat_100g": 0.5, "fiber_100g": 3.0, "notes": "1 unidade ≈ 70g → 43 kcal"},
    {"name": "Pera williams", "aliases": ["pera", "pera williams", "pera verde"], "category": "frutas", "preparation": "cru", "calories_100g": 55, "protein_100g": 0.4, "carbs_100g": 14.8, "fat_100g": 0.1, "fiber_100g": 3.1, "notes": "1 unidade média ≈ 170g → 94 kcal"},
    {"name": "Ameixa vermelha", "aliases": ["ameixa", "ameixa vermelha", "ameixa fresca"], "category": "frutas", "preparation": "cru", "calories_100g": 46, "protein_100g": 0.7, "carbs_100g": 11.4, "fat_100g": 0.3, "fiber_100g": 1.4},
    {"name": "Mirtilo", "aliases": ["mirtilo", "blueberry", "blueberries"], "category": "frutas", "preparation": "cru", "calories_100g": 57, "protein_100g": 0.7, "carbs_100g": 14.5, "fat_100g": 0.3, "fiber_100g": 2.4},
    {"name": "Framboesa", "aliases": ["framboesa", "raspberry"], "category": "frutas", "preparation": "cru", "calories_100g": 52, "protein_100g": 1.2, "carbs_100g": 11.9, "fat_100g": 0.7, "fiber_100g": 6.5},
    {"name": "Maracujá polpa", "aliases": ["maracujá", "maracujá polpa", "polpa de maracujá"], "category": "frutas", "preparation": "cru", "calories_100g": 68, "protein_100g": 2.4, "carbs_100g": 13.6, "fat_100g": 0.7, "fiber_100g": 1.9},
    {"name": "Graviola polpa", "aliases": ["graviola", "graviola polpa", "polpa de graviola"], "category": "frutas", "preparation": "cru", "calories_100g": 62, "protein_100g": 1.0, "carbs_100g": 14.6, "fat_100g": 0.4, "fiber_100g": 3.3},
    {"name": "Cupuaçu polpa", "aliases": ["cupuaçu", "polpa de cupuaçu"], "category": "frutas", "preparation": "cru", "calories_100g": 49, "protein_100g": 1.6, "carbs_100g": 12.4, "fat_100g": 0.6, "fiber_100g": 3.1},
    {"name": "Jabuticaba fresca", "aliases": ["jabuticaba", "jabuticaba fresca"], "category": "frutas", "preparation": "cru", "calories_100g": 58, "protein_100g": 0.6, "carbs_100g": 14.8, "fat_100g": 0.1, "fiber_100g": 0.4},
    {"name": "Coco fresco (polpa)", "aliases": ["coco", "coco fresco", "coco verde polpa", "polpa de coco"], "category": "frutas", "preparation": "cru", "calories_100g": 354, "protein_100g": 3.4, "carbs_100g": 15.2, "fat_100g": 33.5, "fiber_100g": 9.0, "notes": "1 colher de sopa ≈ 15g → 53 kcal"},
    {"name": "Figo fresco", "aliases": ["figo", "figo fresco"], "category": "frutas", "preparation": "cru", "calories_100g": 74, "protein_100g": 0.8, "carbs_100g": 19.2, "fat_100g": 0.3, "fiber_100g": 2.9},
    {"name": "Tangerina/mexerica", "aliases": ["tangerina", "mexerica", "bergamota", "ponkan"], "category": "frutas", "preparation": "cru", "calories_100g": 37, "protein_100g": 0.9, "carbs_100g": 9.1, "fat_100g": 0.1, "fiber_100g": 1.7, "notes": "1 unidade ≈ 100g → 37 kcal"},
    {"name": "Lichia fresca", "aliases": ["lichia", "lychee"], "category": "frutas", "preparation": "cru", "calories_100g": 66, "protein_100g": 0.8, "carbs_100g": 16.5, "fat_100g": 0.4, "fiber_100g": 1.3},
    {"name": "Pitanga fresca", "aliases": ["pitanga", "pitanga fresca"], "category": "frutas", "preparation": "cru", "calories_100g": 37, "protein_100g": 0.8, "carbs_100g": 8.9, "fat_100g": 0.4, "fiber_100g": 0.5},

    # ── SEMENTES E OLEAGINOSAS ADICIONAIS ─────────────────────────────────
    {"name": "Chia em grão", "aliases": ["chia", "semente de chia"], "category": "gorduras", "preparation": "cru", "calories_100g": 490, "protein_100g": 16.5, "carbs_100g": 42.1, "fat_100g": 30.7, "fiber_100g": 34.4, "notes": "1 colher de sopa ≈ 12g → 59 kcal"},
    {"name": "Linhaça dourada", "aliases": ["linhaça", "linhaça dourada", "linhaça marrom", "semente de linhaça"], "category": "gorduras", "preparation": "cru", "calories_100g": 534, "protein_100g": 18.3, "carbs_100g": 28.9, "fat_100g": 42.2, "fiber_100g": 27.3, "notes": "1 colher de sopa ≈ 10g → 53 kcal"},
    {"name": "Gergelim torrado", "aliases": ["gergelim", "gergelim torrado", "semente de gergelim", "sesame"], "category": "gorduras", "preparation": "torrado", "calories_100g": 573, "protein_100g": 17.7, "carbs_100g": 26.0, "fat_100g": 49.7, "fiber_100g": 11.8},
    {"name": "Tahine (pasta de gergelim)", "aliases": ["tahine", "tahini", "pasta de gergelim"], "category": "gorduras", "preparation": "industrializado", "calories_100g": 595, "protein_100g": 17.0, "carbs_100g": 21.2, "fat_100g": 53.8, "fiber_100g": 9.3},
    {"name": "Pistache torrado", "aliases": ["pistache", "pistachio"], "category": "gorduras", "preparation": "torrado", "calories_100g": 562, "protein_100g": 20.2, "carbs_100g": 27.7, "fat_100g": 45.3, "fiber_100g": 10.6},
    {"name": "Coco ralado sem açúcar", "aliases": ["coco ralado", "coco ralado sem açúcar", "coco em flocos"], "category": "gorduras", "preparation": "industrializado", "calories_100g": 660, "protein_100g": 6.9, "carbs_100g": 23.7, "fat_100g": 64.5, "fiber_100g": 16.3, "notes": "1 colher de sopa ≈ 8g → 53 kcal"},
    {"name": "Semente de abóbora torrada", "aliases": ["semente de abóbora", "pepita", "pumpkin seed"], "category": "gorduras", "preparation": "torrado", "calories_100g": 559, "protein_100g": 30.2, "carbs_100g": 10.7, "fat_100g": 49.1, "fiber_100g": 6.0},
    {"name": "Macadâmia", "aliases": ["macadâmia", "noz macadâmia"], "category": "gorduras", "preparation": "cru", "calories_100g": 718, "protein_100g": 7.9, "carbs_100g": 13.8, "fat_100g": 75.8, "fiber_100g": 8.6},

    # ── PRATOS DE RESTAURANTE / SELF-SERVICE ──────────────────────────────
    {"name": "Frango à parmegiana", "aliases": ["frango à parmegiana", "parmegiana de frango", "frango a parmegiana", "frango parmegiana"], "category": "pratos", "preparation": "preparado", "calories_100g": 220, "protein_100g": 22.0, "carbs_100g": 12.0, "fat_100g": 10.0, "fiber_100g": 0.5, "notes": "1 porção (200g) ≈ 440 kcal"},
    {"name": "Bife à parmegiana", "aliases": ["bife à parmegiana", "parmegiana de bife", "bife a parmegiana", "bife parmegiana"], "category": "pratos", "preparation": "preparado", "calories_100g": 240, "protein_100g": 20.0, "carbs_100g": 12.0, "fat_100g": 12.0, "fiber_100g": 0.5, "notes": "1 porção (200g) ≈ 480 kcal"},
    {"name": "Strogonoff de carne", "aliases": ["strogonoff de carne", "estrogonofe de carne", "strogonoff bovino"], "category": "pratos", "preparation": "preparado", "calories_100g": 155, "protein_100g": 14.0, "carbs_100g": 6.0, "fat_100g": 8.5, "fiber_100g": 0.5},
    {"name": "Risoto de frango", "aliases": ["risoto de frango", "risoto", "risotto de frango"], "category": "pratos", "preparation": "preparado", "calories_100g": 150, "protein_100g": 9.0, "carbs_100g": 22.0, "fat_100g": 3.5, "fiber_100g": 0.5},
    {"name": "Risoto de camarão", "aliases": ["risoto de camarão", "risotto de camarão"], "category": "pratos", "preparation": "preparado", "calories_100g": 138, "protein_100g": 9.5, "carbs_100g": 20.0, "fat_100g": 3.0, "fiber_100g": 0.5},
    {"name": "Lasanha de carne ao forno", "aliases": ["lasanha de carne", "lasanha", "lasanha à bolonhesa"], "category": "pratos", "preparation": "assado", "calories_100g": 165, "protein_100g": 10.0, "carbs_100g": 14.0, "fat_100g": 8.0, "fiber_100g": 1.0, "notes": "1 porção (300g) ≈ 495 kcal"},
    {"name": "Lasanha de frango ao forno", "aliases": ["lasanha de frango", "lasanha frango"], "category": "pratos", "preparation": "assado", "calories_100g": 158, "protein_100g": 11.0, "carbs_100g": 14.0, "fat_100g": 7.0, "fiber_100g": 1.0},
    {"name": "Nhoque ao molho de tomate", "aliases": ["nhoque", "gnocchi", "nhoque ao molho"], "category": "pratos", "preparation": "preparado", "calories_100g": 130, "protein_100g": 4.0, "carbs_100g": 22.0, "fat_100g": 3.0, "fiber_100g": 1.0},
    {"name": "Yakissoba de frango", "aliases": ["yakissoba", "yakissoba de frango", "yakisoba"], "category": "pratos", "preparation": "preparado", "calories_100g": 112, "protein_100g": 8.0, "carbs_100g": 15.0, "fat_100g": 2.5, "fiber_100g": 1.5},
    {"name": "Yakissoba de carne", "aliases": ["yakissoba de carne", "yakisoba de carne"], "category": "pratos", "preparation": "preparado", "calories_100g": 130, "protein_100g": 9.0, "carbs_100g": 15.0, "fat_100g": 4.0, "fiber_100g": 1.5},
    {"name": "Frango xadrez", "aliases": ["frango xadrez", "frango ao xadrez"], "category": "pratos", "preparation": "preparado", "calories_100g": 132, "protein_100g": 12.0, "carbs_100g": 7.0, "fat_100g": 6.0, "fiber_100g": 1.0},
    {"name": "Pirão de peixe", "aliases": ["pirão", "pirão de peixe", "pirão de caldo"], "category": "pratos", "preparation": "preparado", "calories_100g": 58, "protein_100g": 3.0, "carbs_100g": 12.0, "fat_100g": 0.4, "fiber_100g": 0.5},
    {"name": "Baião de dois", "aliases": ["baião de dois", "baião"], "category": "pratos", "preparation": "preparado", "calories_100g": 120, "protein_100g": 5.5, "carbs_100g": 20.0, "fat_100g": 2.5, "fiber_100g": 3.5},
    {"name": "Tutu de feijão", "aliases": ["tutu de feijão", "tutu", "tutu à mineira"], "category": "pratos", "preparation": "preparado", "calories_100g": 90, "protein_100g": 5.0, "carbs_100g": 16.0, "fat_100g": 1.5, "fiber_100g": 3.0},
    {"name": "Caldo verde", "aliases": ["caldo verde", "sopa de caldo verde"], "category": "pratos", "preparation": "preparado", "calories_100g": 60, "protein_100g": 3.0, "carbs_100g": 8.0, "fat_100g": 2.0, "fiber_100g": 0.8, "notes": "200ml ≈ 120 kcal"},
    {"name": "Sopa de legumes", "aliases": ["sopa de legumes", "sopa de verduras", "caldo de legumes"], "category": "pratos", "preparation": "preparado", "calories_100g": 40, "protein_100g": 2.0, "carbs_100g": 7.0, "fat_100g": 0.8, "fiber_100g": 1.5, "notes": "200ml ≈ 80 kcal"},
    {"name": "Sopa de frango com macarrão", "aliases": ["sopa de frango", "canja de galinha", "canja"], "category": "pratos", "preparation": "preparado", "calories_100g": 52, "protein_100g": 4.5, "carbs_100g": 6.5, "fat_100g": 0.8, "fiber_100g": 0.3, "notes": "200ml ≈ 104 kcal"},
    {"name": "Frango com catupiry", "aliases": ["frango com catupiry", "frango catupiry"], "category": "pratos", "preparation": "preparado", "calories_100g": 202, "protein_100g": 18.0, "carbs_100g": 3.0, "fat_100g": 13.5, "fiber_100g": 0.0},
    {"name": "Panqueca salgada de carne", "aliases": ["panqueca salgada", "panqueca de carne", "panqueca"], "category": "pratos", "preparation": "preparado", "calories_100g": 160, "protein_100g": 9.0, "carbs_100g": 15.0, "fat_100g": 7.0, "fiber_100g": 0.5},
    {"name": "Escondidinho de carne seca", "aliases": ["escondidinho", "escondidinho de carne seca", "escondidinho de carne"], "category": "pratos", "preparation": "assado", "calories_100g": 145, "protein_100g": 10.0, "carbs_100g": 14.0, "fat_100g": 6.0, "fiber_100g": 1.5},

    # ── SUSHI E COMIDA JAPONESA ───────────────────────────────────────────
    {"name": "Niguiri de salmão", "aliases": ["niguiri", "niguiri de salmão", "nigiri de salmão", "nigiri"], "category": "japonesa", "preparation": "cru", "calories_100g": 172, "protein_100g": 10.0, "carbs_100g": 22.0, "fat_100g": 4.5, "fiber_100g": 0.3, "notes": "1 unidade ≈ 30g → 52 kcal"},
    {"name": "Uramaki califórnia", "aliases": ["califórnia", "uramaki califórnia", "california roll", "sushi califórnia"], "category": "japonesa", "preparation": "preparado", "calories_100g": 140, "protein_100g": 5.0, "carbs_100g": 22.0, "fat_100g": 4.5, "fiber_100g": 0.5, "notes": "1 peça ≈ 25g → 35 kcal"},
    {"name": "Uramaki filadélfia", "aliases": ["filadélfia", "uramaki filadélfia", "philadelphia roll", "sushi filadélfia"], "category": "japonesa", "preparation": "preparado", "calories_100g": 162, "protein_100g": 7.0, "carbs_100g": 20.0, "fat_100g": 6.5, "fiber_100g": 0.3, "notes": "1 peça ≈ 25g → 41 kcal"},
    {"name": "Temaki de salmão", "aliases": ["temaki", "temaki de salmão", "hand roll de salmão"], "category": "japonesa", "preparation": "preparado", "calories_100g": 198, "protein_100g": 9.0, "carbs_100g": 25.0, "fat_100g": 7.0, "fiber_100g": 0.5, "notes": "1 temaki ≈ 120g → 238 kcal"},
    {"name": "Sashimi de atum", "aliases": ["sashimi de atum", "atum sashimi"], "category": "japonesa", "preparation": "cru", "calories_100g": 108, "protein_100g": 23.0, "carbs_100g": 0.0, "fat_100g": 1.0, "fiber_100g": 0.0, "notes": "3 fatias ≈ 60g → 65 kcal"},
    {"name": "Missoshiru", "aliases": ["missoshiru", "miso soup", "sopa de missô"], "category": "japonesa", "preparation": "preparado", "calories_100g": 25, "protein_100g": 2.0, "carbs_100g": 3.0, "fat_100g": 0.7, "fiber_100g": 0.3, "notes": "1 tigela (200ml) ≈ 50 kcal"},
    {"name": "Gyoza grelhado", "aliases": ["gyoza", "guioza", "pastel japonês", "dumplings"], "category": "japonesa", "preparation": "grelhado", "calories_100g": 195, "protein_100g": 10.0, "carbs_100g": 20.0, "fat_100g": 8.0, "fiber_100g": 1.0, "notes": "1 unidade ≈ 20g → 39 kcal"},

    # ── FAST FOOD ADICIONAL ───────────────────────────────────────────────
    {"name": "McChicken McDonald's", "aliases": ["mcchicken", "mc chicken", "mcfrango"], "category": "fastfood", "preparation": "industrializado", "calories_100g": 248, "protein_100g": 13.5, "carbs_100g": 23.0, "fat_100g": 11.5, "fiber_100g": 1.0, "notes": "1 unidade 154g → 382 kcal"},
    {"name": "McFlurry Oreo McDonald's", "aliases": ["mcflurry", "mc flurry", "mcflurry oreo"], "category": "fastfood", "preparation": "industrializado", "calories_100g": 185, "protein_100g": 4.0, "carbs_100g": 30.0, "fat_100g": 6.0, "fiber_100g": 0.5, "notes": "1 unidade (200g) ≈ 370 kcal"},
    {"name": "Frango frito KFC", "aliases": ["kfc", "frango kfc", "frango frito kentucky", "bucket kfc"], "category": "fastfood", "preparation": "frito", "calories_100g": 285, "protein_100g": 23.0, "carbs_100g": 14.0, "fat_100g": 15.0, "fiber_100g": 0.5, "notes": "1 pedaço coxa ≈ 120g → 342 kcal"},
    {"name": "Onion rings Burger King", "aliases": ["onion rings", "anéis de cebola bk", "onion rings bk"], "category": "fastfood", "preparation": "frito", "calories_100g": 330, "protein_100g": 5.0, "carbs_100g": 38.0, "fat_100g": 18.0, "fiber_100g": 2.0, "notes": "porção pequena (70g) ≈ 231 kcal"},
    {"name": "Sanduíche Subway frango teriaki 15cm", "aliases": ["subway", "subway frango", "subway 15cm", "sub de frango"], "category": "fastfood", "preparation": "preparado", "calories_100g": 148, "protein_100g": 13.0, "carbs_100g": 18.0, "fat_100g": 3.0, "fiber_100g": 1.5, "notes": "sanduíche 15cm completo ≈ 250g → 370 kcal"},
    {"name": "Bob's burger", "aliases": ["bobs", "bob's burger", "burguer bobs"], "category": "fastfood", "preparation": "industrializado", "calories_100g": 255, "protein_100g": 12.0, "carbs_100g": 21.0, "fat_100g": 13.5, "fiber_100g": 1.0, "notes": "1 unidade ≈ 160g → 408 kcal"},
    {"name": "Habib's esfiha", "aliases": ["esfiha habibs", "habibs", "esfiha fechada"], "category": "fastfood", "preparation": "assado", "calories_100g": 270, "protein_100g": 10.5, "carbs_100g": 32.0, "fat_100g": 11.5, "fiber_100g": 1.5, "notes": "1 unidade ≈ 80g → 216 kcal"},
    {"name": "Pizza frango com catupiry", "aliases": ["pizza de frango com catupiry", "pizza frango catupiry"], "category": "fastfood", "preparation": "assado", "calories_100g": 265, "protein_100g": 13.5, "carbs_100g": 27.0, "fat_100g": 11.5, "fiber_100g": 1.0, "notes": "1 fatia média ≈ 100g → 265 kcal"},
    {"name": "Pizza portuguesa", "aliases": ["pizza portuguesa", "pizza com ovo"], "category": "fastfood", "preparation": "assado", "calories_100g": 255, "protein_100g": 13.0, "carbs_100g": 26.0, "fat_100g": 11.0, "fiber_100g": 1.0, "notes": "1 fatia média ≈ 100g → 255 kcal"},

    # ── DOCES E SOBREMESAS ADICIONAIS ─────────────────────────────────────
    {"name": "Bolo de cenoura com cobertura de chocolate", "aliases": ["bolo de cenoura", "bolo cenoura com chocolate", "bolo de cenoura com calda"], "category": "acucares", "preparation": "assado", "calories_100g": 352, "protein_100g": 4.5, "carbs_100g": 55.0, "fat_100g": 13.0, "fiber_100g": 1.5, "notes": "1 fatia ≈ 80g → 282 kcal"},
    {"name": "Bolo de chocolate", "aliases": ["bolo de chocolate", "bolo chocolate", "bolo de brigadeiro"], "category": "acucares", "preparation": "assado", "calories_100g": 390, "protein_100g": 5.0, "carbs_100g": 57.0, "fat_100g": 17.0, "fiber_100g": 2.0, "notes": "1 fatia ≈ 80g → 312 kcal"},
    {"name": "Bolo de fubá", "aliases": ["bolo de fubá", "bolo fubá", "bolo de milho"], "category": "acucares", "preparation": "assado", "calories_100g": 295, "protein_100g": 5.5, "carbs_100g": 50.0, "fat_100g": 9.0, "fiber_100g": 1.5, "notes": "1 fatia ≈ 60g → 177 kcal"},
    {"name": "Pudim de leite condensado", "aliases": ["pudim", "pudim de leite", "pudim de leite condensado"], "category": "acucares", "preparation": "preparado", "calories_100g": 220, "protein_100g": 6.0, "carbs_100g": 38.0, "fat_100g": 6.0, "fiber_100g": 0.0, "notes": "1 fatia ≈ 100g → 220 kcal"},
    {"name": "Paçoca de amendoim", "aliases": ["paçoca", "paçoca de amendoim", "paçoca doce"], "category": "acucares", "preparation": "industrializado", "calories_100g": 475, "protein_100g": 14.5, "carbs_100g": 55.0, "fat_100g": 25.5, "fiber_100g": 4.0, "notes": "1 unidade ≈ 22g → 105 kcal"},
    {"name": "Pé de moleque", "aliases": ["pé de moleque", "pe de moleque"], "category": "acucares", "preparation": "preparado", "calories_100g": 450, "protein_100g": 12.0, "carbs_100g": 55.0, "fat_100g": 23.0, "fiber_100g": 3.5},
    {"name": "Canjica branca cozida", "aliases": ["canjica", "canjica branca", "mungunzá branco", "milho canjica"], "category": "acucares", "preparation": "preparado", "calories_100g": 85, "protein_100g": 1.8, "carbs_100g": 19.0, "fat_100g": 0.4, "fiber_100g": 0.8},
    {"name": "Cocada", "aliases": ["cocada", "cocada branca", "cocada de forno"], "category": "acucares", "preparation": "preparado", "calories_100g": 430, "protein_100g": 3.5, "carbs_100g": 65.0, "fat_100g": 19.0, "fiber_100g": 4.5},
    {"name": "Pipoca salgada", "aliases": ["pipoca salgada", "pipoca", "pipoca de panela"], "category": "acucares", "preparation": "preparado", "calories_100g": 390, "protein_100g": 9.0, "carbs_100g": 73.0, "fat_100g": 8.0, "fiber_100g": 14.5, "notes": "1 xícara (15g) ≈ 59 kcal"},
    {"name": "Pipoca de microondas manteiga", "aliases": ["pipoca de microondas", "pipoca manteiga", "pipoca de micro"], "category": "acucares", "preparation": "preparado", "calories_100g": 450, "protein_100g": 8.0, "carbs_100g": 68.0, "fat_100g": 18.0, "fiber_100g": 12.0, "notes": "1 saquinho (100g) ≈ 450 kcal"},
    {"name": "Batata chips", "aliases": ["batata chips", "chips", "salgadinho de batata", "lays"], "category": "acucares", "preparation": "industrializado", "calories_100g": 530, "protein_100g": 7.0, "carbs_100g": 52.0, "fat_100g": 35.0, "fiber_100g": 4.5, "notes": "1 pacote pequeno (40g) ≈ 212 kcal"},
    {"name": "Romeu e Julieta", "aliases": ["romeu e julieta", "queijo com goiabada", "queijo e goiabada"], "category": "acucares", "preparation": "pronto", "calories_100g": 220, "protein_100g": 5.5, "carbs_100g": 38.0, "fat_100g": 7.0, "fiber_100g": 0.3, "notes": "estimativa 50% queijo minas + 50% goiabada"},
    {"name": "Goiabada", "aliases": ["goiabada", "goiabada cascão", "pasta de goiaba"], "category": "acucares", "preparation": "industrializado", "calories_100g": 264, "protein_100g": 0.4, "carbs_100g": 66.0, "fat_100g": 0.2, "fiber_100g": 1.6},

    # ── BEBIDAS ADICIONAIS ────────────────────────────────────────────────
    {"name": "Guaraná Antarctica", "aliases": ["guaraná", "guaraná antarctica", "guaraná kuat", "refrigerante guaraná"], "category": "bebidas", "preparation": "industrializado", "calories_100g": 35, "protein_100g": 0.0, "carbs_100g": 9.0, "fat_100g": 0.0, "fiber_100g": 0.0, "notes": "1 lata 350ml → 123 kcal"},
    {"name": "Energético (Red Bull / Monster)", "aliases": ["energético", "red bull", "monster", "energy drink"], "category": "bebidas", "preparation": "industrializado", "calories_100g": 45, "protein_100g": 0.3, "carbs_100g": 11.0, "fat_100g": 0.0, "fiber_100g": 0.0, "notes": "1 lata Red Bull 250ml → 113 kcal | Monster 473ml → 213 kcal"},
    {"name": "Isotônico (Gatorade / Powerade)", "aliases": ["isotônico", "gatorade", "powerade", "bebida esportiva"], "category": "bebidas", "preparation": "industrializado", "calories_100g": 26, "protein_100g": 0.0, "carbs_100g": 6.5, "fat_100g": 0.0, "fiber_100g": 0.0, "notes": "1 garrafa 500ml → 130 kcal"},
    {"name": "Caipirinha", "aliases": ["caipirinha", "caipirinha de limão", "caipira"], "category": "bebidas", "preparation": "preparado", "calories_100g": 100, "protein_100g": 0.0, "carbs_100g": 9.0, "fat_100g": 0.0, "fiber_100g": 0.0, "notes": "1 dose (200ml) ≈ 200 kcal"},
    {"name": "Caipiroska", "aliases": ["caipiroska", "caipirinha de vodka"], "category": "bebidas", "preparation": "preparado", "calories_100g": 95, "protein_100g": 0.0, "carbs_100g": 8.5, "fat_100g": 0.0, "fiber_100g": 0.0, "notes": "1 dose (200ml) ≈ 190 kcal"},
    {"name": "Vinho tinto seco", "aliases": ["vinho tinto", "vinho tinto seco", "vinho"], "category": "bebidas", "preparation": "industrializado", "calories_100g": 85, "protein_100g": 0.1, "carbs_100g": 2.6, "fat_100g": 0.0, "fiber_100g": 0.0, "notes": "1 taça (150ml) ≈ 128 kcal"},
    {"name": "Vinho branco seco", "aliases": ["vinho branco", "vinho branco seco"], "category": "bebidas", "preparation": "industrializado", "calories_100g": 82, "protein_100g": 0.1, "carbs_100g": 2.6, "fat_100g": 0.0, "fiber_100g": 0.0, "notes": "1 taça (150ml) ≈ 123 kcal"},
    {"name": "Vodka", "aliases": ["vodka", "vodca"], "category": "bebidas", "preparation": "industrializado", "calories_100g": 231, "protein_100g": 0.0, "carbs_100g": 0.0, "fat_100g": 0.0, "fiber_100g": 0.0, "notes": "1 dose (50ml) ≈ 116 kcal"},
    {"name": "Whisky", "aliases": ["whisky", "whiskey", "uísque"], "category": "bebidas", "preparation": "industrializado", "calories_100g": 250, "protein_100g": 0.0, "carbs_100g": 0.1, "fat_100g": 0.0, "fiber_100g": 0.0, "notes": "1 dose (50ml) ≈ 125 kcal"},
    {"name": "Suco de maracujá natural", "aliases": ["suco de maracujá", "suco maracujá", "maracujá suco"], "category": "bebidas", "preparation": "natural", "calories_100g": 50, "protein_100g": 1.0, "carbs_100g": 12.0, "fat_100g": 0.1, "fiber_100g": 0.2, "notes": "200ml ≈ 100 kcal"},
    {"name": "Suco de goiaba natural", "aliases": ["suco de goiaba", "suco goiaba"], "category": "bebidas", "preparation": "natural", "calories_100g": 40, "protein_100g": 0.5, "carbs_100g": 9.5, "fat_100g": 0.1, "fiber_100g": 0.3, "notes": "200ml ≈ 80 kcal"},
    {"name": "Suco de acerola natural", "aliases": ["suco de acerola", "suco acerola"], "category": "bebidas", "preparation": "natural", "calories_100g": 25, "protein_100g": 0.5, "carbs_100g": 6.0, "fat_100g": 0.1, "fiber_100g": 0.2, "notes": "200ml ≈ 50 kcal"},
    {"name": "Limonada suíça", "aliases": ["limonada suíça", "limonada cremosa", "limonada com leite condensado"], "category": "bebidas", "preparation": "preparado", "calories_100g": 95, "protein_100g": 1.0, "carbs_100g": 12.0, "fat_100g": 5.0, "fiber_100g": 0.0, "notes": "200ml ≈ 190 kcal"},
    {"name": "Cappuccino", "aliases": ["cappuccino", "capuccino", "capucino"], "category": "bebidas", "preparation": "preparado", "calories_100g": 40, "protein_100g": 2.0, "carbs_100g": 4.0, "fat_100g": 1.5, "fiber_100g": 0.0, "notes": "1 xícara (200ml) ≈ 80 kcal"},
    {"name": "Café latte", "aliases": ["latte", "café com leite", "flat white", "café latte"], "category": "bebidas", "preparation": "preparado", "calories_100g": 55, "protein_100g": 3.0, "carbs_100g": 5.5, "fat_100g": 2.5, "fiber_100g": 0.0, "notes": "1 copo (300ml) ≈ 165 kcal"},
    {"name": "Kombucha", "aliases": ["kombucha", "kombuchá"], "category": "bebidas", "preparation": "fermentado", "calories_100g": 16, "protein_100g": 0.1, "carbs_100g": 3.7, "fat_100g": 0.0, "fiber_100g": 0.0, "notes": "1 garrafa (300ml) ≈ 48 kcal"},
    {"name": "Suco de uva integral", "aliases": ["suco de uva", "suco uva integral", "suco de uva natural"], "category": "bebidas", "preparation": "industrializado", "calories_100g": 60, "protein_100g": 0.5, "carbs_100g": 14.5, "fat_100g": 0.1, "fiber_100g": 0.2, "notes": "200ml ≈ 120 kcal"},
    {"name": "Matcha latte", "aliases": ["matcha", "matcha latte", "chá matcha"], "category": "bebidas", "preparation": "preparado", "calories_100g": 50, "protein_100g": 2.5, "carbs_100g": 6.0, "fat_100g": 2.0, "fiber_100g": 0.0, "notes": "200ml ≈ 100 kcal"},
]


def _build_search_text(name: str, aliases: list[str]) -> str:
    """Gera o texto de busca desnormalizado (name + aliases em minúsculas)."""
    parts = [name] + aliases
    return " ".join(parts).lower()


async def seed(db: AsyncSession) -> None:
    existing = await db.scalar(select(TacoFood).limit(1))
    if existing:
        print("✓ Tabela taco_foods já populada. Use --force para recriar.")
        return

    foods = []
    for item in TACO_DATA:
        aliases = item.get("aliases", [])
        food = TacoFood(
            name=item["name"],
            aliases=aliases,
            category=item["category"],
            preparation=item.get("preparation"),
            notes=item.get("notes"),
            source="taco",
            search_text=_build_search_text(item["name"], aliases),
            calories_100g=item["calories_100g"],
            protein_100g=item["protein_100g"],
            carbs_100g=item["carbs_100g"],
            fat_100g=item["fat_100g"],
            fiber_100g=item.get("fiber_100g", 0.0),
        )
        foods.append(food)

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

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.meal import Meal, MealType
from app.models.meal_item import MealItem
from app.services.user_service import UserService

# ---------------------------------------------------------------------------
# Inferência de tipo de refeição a partir do texto livre
# ---------------------------------------------------------------------------
_MEAL_TYPE_KEYWORDS: dict[MealType, list[str]] = {
    MealType.BREAKFAST: [
        "café da manhã", "café", "desjejum", "manhã", "breakfast",
        "acordei", "acordar", "tomei café", "tomei o café",
    ],
    MealType.MORNING_SNACK: [
        "lanche da manhã", "lanche manhã", "lanchinho da manhã",
    ],
    MealType.LUNCH: [
        "almoço", "almocei", "almoçar", "meio dia", "lunch",
        "almoço de hoje", "almoçamos",
    ],
    MealType.AFTERNOON_SNACK: [
        "lanche da tarde", "lanche tarde", "lanchinho", "lanche",
    ],
    MealType.DINNER: [
        "jantar", "jantei", "jantamos", "dinner", "noite",
        "jantar de hoje",
    ],
    MealType.SUPPER: [
        "ceia", "cear", "ceei", "antes de dormir", "antes de deitar",
    ],
    MealType.PRE_WORKOUT: [
        "pré-treino", "pre treino", "pré treino", "antes do treino",
        "pre-workout",
    ],
    MealType.POST_WORKOUT: [
        "pós-treino", "pos treino", "pós treino", "depois do treino",
        "após o treino", "post workout", "pós workout",
    ],
    MealType.SUPPLEMENT: [
        "suplemento", "whey", "creatina", "bcaa", "proteína em pó",
    ],
}

_MEAL_TYPE_LABELS: dict[MealType, str] = {
    MealType.BREAKFAST: "café da manhã",
    MealType.MORNING_SNACK: "lanche da manhã",
    MealType.LUNCH: "almoço",
    MealType.AFTERNOON_SNACK: "lanche da tarde",
    MealType.DINNER: "jantar",
    MealType.SUPPER: "ceia",
    MealType.SNACK: "lanche",
    MealType.PRE_WORKOUT: "pré-treino",
    MealType.POST_WORKOUT: "pós-treino",
    MealType.SUPPLEMENT: "suplemento",
}


def _infer_meal_type(description: str) -> MealType | None:
    """Detecta o tipo de refeição a partir de palavras-chave no texto."""
    desc = description.lower()
    # Ordena por comprimento da keyword (maior primeiro) para evitar match parcial
    for meal_type, keywords in _MEAL_TYPE_KEYWORDS.items():
        for kw in sorted(keywords, key=len, reverse=True):
            if kw in desc:
                return meal_type
    return None


# ---------------------------------------------------------------------------
# Queries de histórico
# ---------------------------------------------------------------------------

async def _get_recent_meals_of_type(
    user_id: int,
    meal_type: MealType,
    today: date,
    db: AsyncSession,
    limit: int = 3,
) -> list[dict[str, Any]]:
    """Retorna as últimas N refeições do mesmo tipo (excluindo hoje)."""
    result = await db.execute(
        select(Meal)
        .options(selectinload(Meal.items))
        .where(
            Meal.user_id == user_id,
            Meal.meal_type == meal_type,
            Meal.date < today,
        )
        .order_by(Meal.date.desc())
        .limit(limit)
    )
    meals = result.scalars().all()

    records = []
    for meal in meals:
        total_cal = sum(item.calories for item in meal.items)
        total_prot = sum(item.protein for item in meal.items)
        item_strs = [
            f"{item.food_name} {item.quantity:.0f}{item.unit} ({item.calories:.0f} kcal)"
            for item in meal.items
        ]
        records.append({
            "date": meal.date.strftime("%d/%m"),
            "total_cal": total_cal,
            "total_prot": total_prot,
            "items": item_strs,
        })
    return records


async def _get_meal_type_averages(
    user_id: int,
    today: date,
    db: AsyncSession,
) -> dict[str, float]:
    """Retorna média calórica por tipo de refeição nos últimos 30 dias."""
    result = await db.execute(
        select(
            Meal.meal_type,
            func.sum(MealItem.calories).label("total_cal"),
            func.count(Meal.id.distinct()).label("count"),
        )
        .join(MealItem, MealItem.meal_id == Meal.id)
        .where(
            Meal.user_id == user_id,
            Meal.date >= today - timedelta(days=30),
            Meal.date < today,
        )
        .group_by(Meal.meal_type)
    )
    rows = result.all()
    return {
        row.meal_type.value: round(
            float(row.total_cal) / max(int(row._mapping["count"] or 1), 1)
        )
        for row in rows
        if int(row._mapping["count"] or 0) >= 2  # só inclui se tem pelo menos 2 ocorrências
    }


# ---------------------------------------------------------------------------
# Builder principal
# ---------------------------------------------------------------------------

async def build_meal_context(
    user_id: int,
    db: AsyncSession,
    today: date,
    description: str = "",
) -> str:
    """Constrói contexto completo do usuário para calibrar análise de refeições.

    Inclui:
    - Dados físicos e metas do perfil
    - Calorias já consumidas hoje
    - Porções históricas por alimento (últimos 30 dias)
    - Últimas 3 refeições do mesmo tipo (quando detectado na descrição)
    - Média calórica por tipo de refeição
    """
    sections: list[str] = []

    # ── 1. Perfil e metas ─────────────────────────────────────────────────
    user = await UserService(db).get_by_id(user_id)
    if user:
        if user.calorie_goal:
            sections.append(f"Meta calórica diária: {user.calorie_goal} kcal")

        profile = getattr(user, "profile", None)
        if profile:
            bio: list[str] = []
            if profile.sex:
                bio.append(f"sexo {profile.sex.value}")
            if profile.age:
                bio.append(f"{profile.age} anos")
            if profile.height_cm:
                bio.append(f"{profile.height_cm:.0f} cm")
            if profile.current_weight:
                bio.append(f"{profile.current_weight:.1f} kg")
            if bio:
                sections.append("Perfil físico: " + ", ".join(bio))

    # ── 2. Consumo de hoje ────────────────────────────────────────────────
    cal_today = await db.scalar(
        select(func.sum(MealItem.calories))
        .join(Meal, Meal.id == MealItem.meal_id)
        .where(Meal.user_id == user_id, Meal.date == today)
    ) or 0.0

    prot_today = await db.scalar(
        select(func.sum(MealItem.protein))
        .join(Meal, Meal.id == MealItem.meal_id)
        .where(Meal.user_id == user_id, Meal.date == today)
    ) or 0.0

    if cal_today > 0:
        sections.append(
            f"Já consumido hoje: {cal_today:.0f} kcal / {prot_today:.0f}g proteína"
        )

    # ── 3. Porções históricas por alimento (últimos 30 dias) ───────────────
    food_rows = await db.execute(
        select(
            MealItem.food_name,
            func.count(MealItem.id).label("freq"),
            func.avg(MealItem.quantity).label("avg_qty"),
            func.max(MealItem.unit).label("unit"),
            func.avg(MealItem.calories).label("avg_cal"),
            func.avg(MealItem.protein).label("avg_prot"),
        )
        .join(Meal, Meal.id == MealItem.meal_id)
        .where(
            Meal.user_id == user_id,
            Meal.date >= today - timedelta(days=30),
        )
        .group_by(MealItem.food_name)
        .order_by(func.count(MealItem.id).desc())
        .limit(15)
    )
    foods = food_rows.all()

    if foods:
        food_strs = [
            f"{r.food_name}: ~{int(float(r.avg_qty or 0))}{r.unit or 'g'} "
            f"(~{int(float(r.avg_cal or 0))} kcal / {int(float(r.avg_prot or 0))}g prot), "
            f"{int(r.freq)}x/mês"
            for r in foods
        ]
        sections.append("Suas porções habituais:\n  " + "\n  ".join(food_strs))

    # ── 4. Refeições recentes do mesmo tipo (se detectado na descrição) ────
    inferred_type = _infer_meal_type(description) if description else None

    if inferred_type:
        type_label = _MEAL_TYPE_LABELS.get(inferred_type, inferred_type.value)
        recent = await _get_recent_meals_of_type(user_id, inferred_type, today, db)

        if recent:
            lines = [f"Seus últimos {type_label}s (referência de porção):"]
            for r in recent:
                items_str = ", ".join(r["items"])
                lines.append(
                    f"  {r['date']}: {items_str} → {r['total_cal']:.0f} kcal "
                    f"/ {r['total_prot']:.0f}g prot"
                )
            sections.append("\n".join(lines))

    # ── 5. Média calórica por tipo de refeição ─────────────────────────────
    averages = await _get_meal_type_averages(user_id, today, db)
    if averages:
        avg_lines = [
            f"{_MEAL_TYPE_LABELS.get(MealType(k), k)}: ~{v} kcal"
            for k, v in averages.items()
        ]
        sections.append("Sua média calórica por refeição:\n  " + ", ".join(avg_lines))

    return "\n\n".join(sections) if sections else "usuário sem histórico"

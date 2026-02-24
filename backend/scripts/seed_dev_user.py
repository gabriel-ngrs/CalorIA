"""
Script de seed para o usuário Dev Test.
Popula 30 dias de refeições, peso, hidratação e humor com dados realistas.

Uso (dentro do container ou com o banco acessível):
    python scripts/seed_dev_user.py
"""

import sys
import os
import random
from datetime import date, time, timedelta

# Adiciona o diretório raiz ao path para importar os módulos do app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://caloria:caloria@localhost:5432/caloria_db",
).replace("postgresql+asyncpg://", "postgresql://").replace("+asyncpg", "")

engine = create_engine(DATABASE_URL, echo=False)

# ---------------------------------------------------------------------------
# Cardápio brasileiro realista
# ---------------------------------------------------------------------------

BREAKFASTS = [
    {
        "name": "Café da manhã leve",
        "items": [
            {"food_name": "Pão francês", "quantity": 50, "unit": "g", "calories": 134, "protein": 4.4, "carbs": 27.2, "fat": 0.6, "fiber": 1.2},
            {"food_name": "Manteiga", "quantity": 10, "unit": "g", "calories": 72, "protein": 0.1, "carbs": 0.0, "fat": 8.1, "fiber": 0.0},
            {"food_name": "Café com leite", "quantity": 200, "unit": "ml", "calories": 58, "protein": 3.0, "carbs": 5.0, "fat": 2.0, "fiber": 0.0},
        ],
    },
    {
        "name": "Tapioca proteica",
        "items": [
            {"food_name": "Tapioca", "quantity": 80, "unit": "g", "calories": 272, "protein": 0.3, "carbs": 67.7, "fat": 0.2, "fiber": 0.9},
            {"food_name": "Queijo minas frescal", "quantity": 50, "unit": "g", "calories": 74, "protein": 7.0, "carbs": 1.5, "fat": 4.4, "fiber": 0.0},
            {"food_name": "Presunto", "quantity": 30, "unit": "g", "calories": 45, "protein": 5.1, "carbs": 1.0, "fat": 2.2, "fiber": 0.0},
            {"food_name": "Suco de laranja natural", "quantity": 200, "unit": "ml", "calories": 88, "protein": 1.4, "carbs": 20.0, "fat": 0.2, "fiber": 0.6},
        ],
    },
    {
        "name": "Ovos mexidos com pão",
        "items": [
            {"food_name": "Ovos mexidos", "quantity": 120, "unit": "g", "calories": 174, "protein": 12.8, "carbs": 1.2, "fat": 13.0, "fiber": 0.0},
            {"food_name": "Pão de forma integral", "quantity": 60, "unit": "g", "calories": 148, "protein": 5.5, "carbs": 27.0, "fat": 2.5, "fiber": 3.2},
            {"food_name": "Café preto", "quantity": 150, "unit": "ml", "calories": 3, "protein": 0.2, "carbs": 0.5, "fat": 0.0, "fiber": 0.0},
        ],
    },
    {
        "name": "Aveia com frutas",
        "items": [
            {"food_name": "Aveia em flocos", "quantity": 50, "unit": "g", "calories": 189, "protein": 6.3, "carbs": 33.5, "fat": 3.5, "fiber": 4.9},
            {"food_name": "Leite desnatado", "quantity": 200, "unit": "ml", "calories": 72, "protein": 7.0, "carbs": 10.0, "fat": 0.4, "fiber": 0.0},
            {"food_name": "Banana", "quantity": 100, "unit": "g", "calories": 89, "protein": 1.1, "carbs": 22.8, "fat": 0.3, "fiber": 2.6},
            {"food_name": "Mel", "quantity": 15, "unit": "g", "calories": 46, "protein": 0.1, "carbs": 12.5, "fat": 0.0, "fiber": 0.0},
        ],
    },
    {
        "name": "Iogurte grego com granola",
        "items": [
            {"food_name": "Iogurte grego natural", "quantity": 170, "unit": "g", "calories": 146, "protein": 17.0, "carbs": 6.0, "fat": 5.0, "fiber": 0.0},
            {"food_name": "Granola", "quantity": 30, "unit": "g", "calories": 132, "protein": 3.0, "carbs": 21.0, "fat": 4.5, "fiber": 1.8},
            {"food_name": "Morango", "quantity": 80, "unit": "g", "calories": 26, "protein": 0.5, "carbs": 6.0, "fat": 0.2, "fiber": 1.5},
        ],
    },
    {
        "name": "Vitamina de banana com aveia",
        "items": [
            {"food_name": "Banana", "quantity": 150, "unit": "g", "calories": 134, "protein": 1.7, "carbs": 34.2, "fat": 0.5, "fiber": 3.9},
            {"food_name": "Aveia em flocos", "quantity": 30, "unit": "g", "calories": 113, "protein": 3.8, "carbs": 20.1, "fat": 2.1, "fiber": 2.9},
            {"food_name": "Leite integral", "quantity": 250, "unit": "ml", "calories": 153, "protein": 8.0, "carbs": 12.0, "fat": 8.0, "fiber": 0.0},
            {"food_name": "Pasta de amendoim", "quantity": 20, "unit": "g", "calories": 117, "protein": 5.0, "carbs": 4.0, "fat": 9.5, "fiber": 1.2},
        ],
    },
]

LUNCHES = [
    {
        "name": "Almoço tradicional",
        "items": [
            {"food_name": "Arroz branco cozido", "quantity": 180, "unit": "g", "calories": 232, "protein": 4.3, "carbs": 51.1, "fat": 0.3, "fiber": 0.7},
            {"food_name": "Feijão carioca cozido", "quantity": 140, "unit": "g", "calories": 162, "protein": 9.8, "carbs": 29.0, "fat": 0.5, "fiber": 8.4},
            {"food_name": "Frango grelhado", "quantity": 150, "unit": "g", "calories": 214, "protein": 36.0, "carbs": 0.0, "fat": 7.2, "fiber": 0.0},
            {"food_name": "Salada verde", "quantity": 80, "unit": "g", "calories": 18, "protein": 1.4, "carbs": 2.4, "fat": 0.3, "fiber": 1.6},
            {"food_name": "Azeite de oliva", "quantity": 10, "unit": "ml", "calories": 88, "protein": 0.0, "carbs": 0.0, "fat": 10.0, "fiber": 0.0},
        ],
    },
    {
        "name": "Bife com mandioca",
        "items": [
            {"food_name": "Bife de acém grelhado", "quantity": 180, "unit": "g", "calories": 306, "protein": 38.0, "carbs": 0.0, "fat": 16.0, "fiber": 0.0},
            {"food_name": "Mandioca cozida", "quantity": 150, "unit": "g", "calories": 184, "protein": 1.5, "carbs": 44.0, "fat": 0.3, "fiber": 1.8},
            {"food_name": "Arroz branco cozido", "quantity": 120, "unit": "g", "calories": 155, "protein": 2.9, "carbs": 34.1, "fat": 0.2, "fiber": 0.5},
            {"food_name": "Couve refogada", "quantity": 60, "unit": "g", "calories": 36, "protein": 2.2, "carbs": 4.0, "fat": 1.5, "fiber": 2.0},
        ],
    },
    {
        "name": "Frango com legumes",
        "items": [
            {"food_name": "Peito de frango assado", "quantity": 200, "unit": "g", "calories": 274, "protein": 51.0, "carbs": 0.0, "fat": 6.8, "fiber": 0.0},
            {"food_name": "Batata-doce assada", "quantity": 150, "unit": "g", "calories": 129, "protein": 2.4, "carbs": 29.7, "fat": 0.2, "fiber": 3.8},
            {"food_name": "Brócolis cozido", "quantity": 100, "unit": "g", "calories": 35, "protein": 2.4, "carbs": 7.2, "fat": 0.4, "fiber": 2.6},
            {"food_name": "Cenoura cozida", "quantity": 80, "unit": "g", "calories": 34, "protein": 0.9, "carbs": 8.0, "fat": 0.2, "fiber": 2.4},
        ],
    },
    {
        "name": "Macarrão ao molho bolonhesa",
        "items": [
            {"food_name": "Macarrão penne cozido", "quantity": 200, "unit": "g", "calories": 286, "protein": 9.6, "carbs": 57.6, "fat": 1.6, "fiber": 2.4},
            {"food_name": "Carne moída refogada", "quantity": 120, "unit": "g", "calories": 258, "protein": 25.0, "carbs": 2.0, "fat": 16.0, "fiber": 0.0},
            {"food_name": "Molho de tomate", "quantity": 100, "unit": "g", "calories": 32, "protein": 1.2, "carbs": 6.5, "fat": 0.4, "fiber": 1.5},
            {"food_name": "Queijo parmesão ralado", "quantity": 15, "unit": "g", "calories": 70, "protein": 6.2, "carbs": 0.3, "fat": 4.8, "fiber": 0.0},
        ],
    },
    {
        "name": "Peixe com arroz e salada",
        "items": [
            {"food_name": "Tilápia grelhada", "quantity": 200, "unit": "g", "calories": 218, "protein": 44.0, "carbs": 0.0, "fat": 4.5, "fiber": 0.0},
            {"food_name": "Arroz integral cozido", "quantity": 150, "unit": "g", "calories": 185, "protein": 3.9, "carbs": 38.5, "fat": 1.5, "fiber": 2.1},
            {"food_name": "Salada de tomate e pepino", "quantity": 120, "unit": "g", "calories": 22, "protein": 1.0, "carbs": 4.5, "fat": 0.2, "fiber": 1.4},
            {"food_name": "Limão (tempero)", "quantity": 20, "unit": "g", "calories": 5, "protein": 0.1, "carbs": 1.6, "fat": 0.0, "fiber": 0.2},
        ],
    },
    {
        "name": "Feijoada light",
        "items": [
            {"food_name": "Feijoada (porção)", "quantity": 300, "unit": "g", "calories": 312, "protein": 22.0, "carbs": 24.0, "fat": 14.0, "fiber": 9.0},
            {"food_name": "Arroz branco cozido", "quantity": 150, "unit": "g", "calories": 194, "protein": 3.6, "carbs": 42.6, "fat": 0.3, "fiber": 0.6},
            {"food_name": "Couve refogada", "quantity": 80, "unit": "g", "calories": 48, "protein": 2.9, "carbs": 5.3, "fat": 2.0, "fiber": 2.7},
            {"food_name": "Laranja", "quantity": 120, "unit": "g", "calories": 56, "protein": 1.0, "carbs": 13.6, "fat": 0.1, "fiber": 2.4},
        ],
    },
    {
        "name": "Wrap de frango",
        "items": [
            {"food_name": "Tortilha de trigo", "quantity": 60, "unit": "g", "calories": 186, "protein": 4.8, "carbs": 33.0, "fat": 4.2, "fiber": 2.0},
            {"food_name": "Frango desfiado", "quantity": 100, "unit": "g", "calories": 163, "protein": 31.0, "carbs": 0.0, "fat": 4.2, "fiber": 0.0},
            {"food_name": "Alface", "quantity": 30, "unit": "g", "calories": 5, "protein": 0.4, "carbs": 0.8, "fat": 0.1, "fiber": 0.5},
            {"food_name": "Tomate", "quantity": 50, "unit": "g", "calories": 9, "protein": 0.5, "carbs": 2.0, "fat": 0.1, "fiber": 0.6},
            {"food_name": "Molho de iogurte light", "quantity": 30, "unit": "g", "calories": 19, "protein": 1.8, "carbs": 1.5, "fat": 0.6, "fiber": 0.0},
        ],
    },
]

DINNERS = [
    {
        "name": "Sopa de legumes",
        "items": [
            {"food_name": "Sopa de legumes com macarrão", "quantity": 400, "unit": "ml", "calories": 168, "protein": 6.4, "carbs": 32.0, "fat": 2.0, "fiber": 3.2},
            {"food_name": "Pão francês", "quantity": 30, "unit": "g", "calories": 80, "protein": 2.6, "carbs": 16.3, "fat": 0.4, "fiber": 0.7},
        ],
    },
    {
        "name": "Omelete de queijo e presunto",
        "items": [
            {"food_name": "Omelete (2 ovos)", "quantity": 130, "unit": "g", "calories": 196, "protein": 14.0, "carbs": 1.5, "fat": 15.0, "fiber": 0.0},
            {"food_name": "Queijo mussarela", "quantity": 30, "unit": "g", "calories": 89, "protein": 6.3, "carbs": 0.6, "fat": 7.0, "fiber": 0.0},
            {"food_name": "Presunto", "quantity": 30, "unit": "g", "calories": 45, "protein": 5.1, "carbs": 1.0, "fat": 2.2, "fiber": 0.0},
            {"food_name": "Salada verde", "quantity": 60, "unit": "g", "calories": 14, "protein": 1.1, "carbs": 1.8, "fat": 0.2, "fiber": 1.2},
        ],
    },
    {
        "name": "Frango grelhado com batata doce",
        "items": [
            {"food_name": "Peito de frango grelhado", "quantity": 180, "unit": "g", "calories": 247, "protein": 46.0, "carbs": 0.0, "fat": 6.0, "fiber": 0.0},
            {"food_name": "Batata-doce cozida", "quantity": 150, "unit": "g", "calories": 129, "protein": 2.4, "carbs": 29.7, "fat": 0.2, "fiber": 3.8},
            {"food_name": "Azeite de oliva", "quantity": 10, "unit": "ml", "calories": 88, "protein": 0.0, "carbs": 0.0, "fat": 10.0, "fiber": 0.0},
        ],
    },
    {
        "name": "Arroz com ovo e legumes",
        "items": [
            {"food_name": "Arroz branco cozido", "quantity": 130, "unit": "g", "calories": 168, "protein": 3.1, "carbs": 37.0, "fat": 0.2, "fiber": 0.5},
            {"food_name": "Ovo frito", "quantity": 60, "unit": "g", "calories": 109, "protein": 6.7, "carbs": 0.4, "fat": 8.8, "fiber": 0.0},
            {"food_name": "Abobrinha refogada", "quantity": 100, "unit": "g", "calories": 30, "protein": 1.2, "carbs": 5.5, "fat": 0.5, "fiber": 1.1},
        ],
    },
    {
        "name": "Panqueca de aveia proteica",
        "items": [
            {"food_name": "Panqueca de aveia e banana (2 un)", "quantity": 150, "unit": "g", "calories": 280, "protein": 12.0, "carbs": 40.0, "fat": 7.0, "fiber": 4.5},
            {"food_name": "Mel", "quantity": 20, "unit": "g", "calories": 61, "protein": 0.1, "carbs": 16.6, "fat": 0.0, "fiber": 0.0},
            {"food_name": "Frutas vermelhas", "quantity": 60, "unit": "g", "calories": 27, "protein": 0.5, "carbs": 6.5, "fat": 0.3, "fiber": 1.8},
        ],
    },
    {
        "name": "Salada de atum",
        "items": [
            {"food_name": "Atum em água escorrido", "quantity": 120, "unit": "g", "calories": 121, "protein": 27.0, "carbs": 0.0, "fat": 1.2, "fiber": 0.0},
            {"food_name": "Alface", "quantity": 50, "unit": "g", "calories": 8, "protein": 0.7, "carbs": 1.3, "fat": 0.1, "fiber": 0.8},
            {"food_name": "Tomate cereja", "quantity": 80, "unit": "g", "calories": 14, "protein": 0.7, "carbs": 3.1, "fat": 0.2, "fiber": 0.9},
            {"food_name": "Milho em conserva", "quantity": 50, "unit": "g", "calories": 45, "protein": 1.4, "carbs": 10.1, "fat": 0.6, "fiber": 1.1},
            {"food_name": "Azeite e limão (molho)", "quantity": 15, "unit": "ml", "calories": 120, "protein": 0.0, "carbs": 0.5, "fat": 13.5, "fiber": 0.0},
            {"food_name": "Torrada integral", "quantity": 20, "unit": "g", "calories": 72, "protein": 2.4, "carbs": 14.5, "fat": 0.8, "fiber": 1.8},
        ],
    },
]

SNACKS = [
    {
        "name": "Lanche da tarde — fruta",
        "items": [
            {"food_name": "Maçã", "quantity": 150, "unit": "g", "calories": 78, "protein": 0.4, "carbs": 20.6, "fat": 0.2, "fiber": 3.6},
        ],
    },
    {
        "name": "Lanche pré-treino",
        "items": [
            {"food_name": "Banana", "quantity": 120, "unit": "g", "calories": 107, "protein": 1.3, "carbs": 27.4, "fat": 0.4, "fiber": 3.1},
            {"food_name": "Pasta de amendoim", "quantity": 30, "unit": "g", "calories": 176, "protein": 7.5, "carbs": 6.0, "fat": 14.3, "fiber": 1.8},
        ],
    },
    {
        "name": "Shake de proteína",
        "items": [
            {"food_name": "Whey protein (1 dose)", "quantity": 30, "unit": "g", "calories": 121, "protein": 24.0, "carbs": 3.0, "fat": 2.0, "fiber": 0.0},
            {"food_name": "Leite desnatado", "quantity": 250, "unit": "ml", "calories": 90, "protein": 8.8, "carbs": 12.5, "fat": 0.5, "fiber": 0.0},
        ],
    },
    {
        "name": "Castanhas e frutas secas",
        "items": [
            {"food_name": "Mix de castanhas", "quantity": 30, "unit": "g", "calories": 185, "protein": 4.5, "carbs": 6.0, "fat": 16.5, "fiber": 2.0},
            {"food_name": "Uva passa", "quantity": 20, "unit": "g", "calories": 60, "protein": 0.6, "carbs": 15.4, "fat": 0.1, "fiber": 0.7},
        ],
    },
    {
        "name": "Iogurte com frutas",
        "items": [
            {"food_name": "Iogurte natural desnatado", "quantity": 160, "unit": "g", "calories": 83, "protein": 8.5, "carbs": 11.5, "fat": 0.5, "fiber": 0.0},
            {"food_name": "Mamão papaya", "quantity": 100, "unit": "g", "calories": 40, "protein": 0.5, "carbs": 10.0, "fat": 0.1, "fiber": 1.8},
        ],
    },
    {
        "name": "Biscoito integral com queijo",
        "items": [
            {"food_name": "Biscoito de água e sal integral", "quantity": 30, "unit": "g", "calories": 115, "protein": 2.5, "carbs": 22.5, "fat": 2.0, "fiber": 1.5},
            {"food_name": "Queijo cottage", "quantity": 60, "unit": "g", "calories": 60, "protein": 8.0, "carbs": 2.4, "fat": 1.8, "fiber": 0.0},
        ],
    },
]

MOOD_NOTES = [
    "Dia produtivo, me senti bem!",
    "Um pouco cansado hoje.",
    "Ótimo treino hoje.",
    "Estressado com o trabalho.",
    "Dormiu bem, disposição alta.",
    "Dor de cabeça leve.",
    "Fim de semana tranquilo.",
    "Muita energia após o almoço.",
    None,
    None,
    None,
]


def get_user_id(session: Session, email: str) -> int:
    result = session.execute(
        text("SELECT id FROM users WHERE email = :email"), {"email": email}
    ).fetchone()
    if not result:
        raise ValueError(f"Usuário com email '{email}' não encontrado.")
    return result[0]


def clear_existing_data(session: Session, user_id: int) -> None:
    print(f"  Limpando dados existentes do usuário {user_id}...")
    session.execute(text("DELETE FROM meal_items WHERE meal_id IN (SELECT id FROM meals WHERE user_id = :uid)"), {"uid": user_id})
    session.execute(text("DELETE FROM meals WHERE user_id = :uid"), {"uid": user_id})
    session.execute(text("DELETE FROM weight_logs WHERE user_id = :uid"), {"uid": user_id})
    session.execute(text("DELETE FROM hydration_logs WHERE user_id = :uid"), {"uid": user_id})
    session.execute(text("DELETE FROM mood_logs WHERE user_id = :uid"), {"uid": user_id})
    session.commit()


def update_user_profile(session: Session, user_id: int) -> None:
    print("  Atualizando perfil e meta calórica...")
    session.execute(
        text("UPDATE users SET calorie_goal = 2000, weight_goal = 78.0 WHERE id = :uid"),
        {"uid": user_id},
    )
    exists = session.execute(
        text("SELECT id FROM user_profiles WHERE user_id = :uid"), {"uid": user_id}
    ).fetchone()
    if exists:
        session.execute(
            text("""
                UPDATE user_profiles
                SET height_cm=178, current_weight=84.5, age=28,
                    sex='male', activity_level='moderately_active', tdee_calculated=2380
                WHERE user_id=:uid
            """),
            {"uid": user_id},
        )
    else:
        session.execute(
            text("""
                INSERT INTO user_profiles (user_id, height_cm, current_weight, age, sex, activity_level, tdee_calculated)
                VALUES (:uid, 178, 84.5, 28, 'male', 'moderately_active', 2380)
            """),
            {"uid": user_id},
        )
    session.commit()


def seed_meals(session: Session, user_id: int, target_date: date, rng: random.Random) -> None:
    """Insere refeições para um dia específico."""

    # Café da manhã — sempre
    breakfast = rng.choice(BREAKFASTS)
    meal_id = session.execute(
        text("""
            INSERT INTO meals (user_id, meal_type, date, source, notes)
            VALUES (:uid, 'breakfast', :d, 'manual', :notes)
            RETURNING id
        """),
        {"uid": user_id, "d": target_date, "notes": breakfast["name"]},
    ).scalar()
    for item in breakfast["items"]:
        session.execute(
            text("""
                INSERT INTO meal_items (meal_id, food_name, quantity, unit, calories, protein, carbs, fat, fiber)
                VALUES (:mid, :fn, :qty, :unit, :cal, :pro, :carb, :fat, :fib)
            """),
            {**item, "mid": meal_id},
        )

    # Almoço — sempre
    lunch = rng.choice(LUNCHES)
    meal_id = session.execute(
        text("""
            INSERT INTO meals (user_id, meal_type, date, source, notes)
            VALUES (:uid, 'lunch', :d, 'manual', :notes)
            RETURNING id
        """),
        {"uid": user_id, "d": target_date, "notes": lunch["name"]},
    ).scalar()
    for item in lunch["items"]:
        session.execute(
            text("""
                INSERT INTO meal_items (meal_id, food_name, quantity, unit, calories, protein, carbs, fat, fiber)
                VALUES (:mid, :fn, :qty, :unit, :cal, :pro, :carb, :fat, :fib)
            """),
            {**item, "mid": meal_id},
        )

    # Jantar — sempre
    dinner = rng.choice(DINNERS)
    meal_id = session.execute(
        text("""
            INSERT INTO meals (user_id, meal_type, date, source, notes)
            VALUES (:uid, 'dinner', :d, 'manual', :notes)
            RETURNING id
        """),
        {"uid": user_id, "d": target_date, "notes": dinner["name"]},
    ).scalar()
    for item in dinner["items"]:
        session.execute(
            text("""
                INSERT INTO meal_items (meal_id, food_name, quantity, unit, calories, protein, carbs, fat, fiber)
                VALUES (:mid, :fn, :qty, :unit, :cal, :pro, :carb, :fat, :fib)
            """),
            {**item, "mid": meal_id},
        )

    # Lanche — 75% dos dias
    if rng.random() < 0.75:
        snack = rng.choice(SNACKS)
        meal_id = session.execute(
            text("""
                INSERT INTO meals (user_id, meal_type, date, source, notes)
                VALUES (:uid, 'snack', :d, 'manual', :notes)
                RETURNING id
            """),
            {"uid": user_id, "d": target_date, "notes": snack["name"]},
        ).scalar()
        for item in snack["items"]:
            session.execute(
                text("""
                    INSERT INTO meal_items (meal_id, food_name, quantity, unit, calories, protein, carbs, fat, fiber)
                    VALUES (:mid, :fn, :qty, :unit, :cal, :pro, :carb, :fat, :fib)
                """),
                {**item, "mid": meal_id},
            )


def seed_hydration(session: Session, user_id: int, target_date: date, rng: random.Random) -> None:
    """Insere logs de hidratação para um dia."""
    # Entre 3 e 6 registros por dia
    num_entries = rng.randint(3, 6)
    drink_times = sorted(rng.sample(range(7, 22), num_entries))
    for h in drink_times:
        amount = rng.choice([200, 250, 300, 350, 500])
        session.execute(
            text("""
                INSERT INTO hydration_logs (user_id, amount_ml, date, time)
                VALUES (:uid, :amt, :d, :t)
            """),
            {"uid": user_id, "amt": amount, "d": target_date, "t": time(h, rng.randint(0, 59))},
        )


def seed_mood(session: Session, user_id: int, target_date: date, rng: random.Random) -> None:
    """Insere log de humor para um dia."""
    energy = rng.randint(2, 5)
    # Humor tende a acompanhar energia com variação
    mood = max(1, min(5, energy + rng.randint(-1, 1)))
    note = rng.choice(MOOD_NOTES)
    session.execute(
        text("""
            INSERT INTO mood_logs (user_id, date, energy_level, mood_level, notes)
            VALUES (:uid, :d, :e, :m, :n)
        """),
        {"uid": user_id, "d": target_date, "e": energy, "m": mood, "n": note},
    )


def seed_weight(session: Session, user_id: int, target_date: date, weight: float) -> None:
    """Insere log de peso."""
    session.execute(
        text("""
            INSERT INTO weight_logs (user_id, weight_kg, date)
            VALUES (:uid, :w, :d)
        """),
        {"uid": user_id, "w": round(weight, 1), "d": target_date},
    )


def main() -> None:
    print("=" * 55)
    print("  CalorIA — Seed de dados para Dev Test")
    print("=" * 55)

    rng = random.Random(42)  # seed fixo para reprodutibilidade
    today = date.today()
    days = 30

    with Session(engine) as session:
        # 1. Buscar usuário
        print(f"\n→ Buscando usuário devteste@gmail.com...")
        user_id = get_user_id(session, "devteste@gmail.com")
        print(f"  Encontrado: user_id={user_id}")

        # 2. Limpar dados anteriores
        clear_existing_data(session, user_id)

        # 3. Atualizar perfil
        update_user_profile(session, user_id)

        # 4. Gerar dados dia a dia (dos mais antigos para hoje)
        print(f"\n→ Gerando {days} dias de dados ({today - timedelta(days=days-1)} → {today})...")

        # Peso começa em 84.5 e vai caindo ~0.15 kg/dia com ruído
        weight = 84.5
        weight_reported_days = 0

        for i in range(days):
            target_date = today - timedelta(days=days - 1 - i)

            # Refeições
            seed_meals(session, user_id, target_date, rng)

            # Hidratação — todos os dias
            seed_hydration(session, user_id, target_date, rng)

            # Humor — 85% dos dias
            if rng.random() < 0.85:
                seed_mood(session, user_id, target_date, rng)

            # Peso — a cada 2-3 dias
            if i == 0 or rng.random() < 0.45:
                seed_weight(session, user_id, target_date, weight)
                weight_reported_days += 1

            # Evolução do peso: tendência de queda com ruído
            weight += rng.uniform(-0.3, 0.08)

        session.commit()

        print(f"\n✓ Dados inseridos com sucesso!")
        print(f"  Dias com refeições:  {days}")
        print(f"  Registros de peso:   {weight_reported_days}")
        print(f"  Peso inicial: 84.5 kg  →  final: ~{round(weight, 1)} kg")
        print(f"\n  Acesse http://localhost:3000 e logue como devteste@gmail.com")
    print("=" * 55)


if __name__ == "__main__":
    main()

"""Script de seed para popular o banco com dados de teste realistas."""
import asyncio
from datetime import date, time, timedelta
import random
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.user import User, GoalType
from app.models.profile import UserProfile, Sex, ActivityLevel
from app.models.meal import Meal, MealType, MealSource
from app.models.meal_item import MealItem
from app.models.weight_log import WeightLog
from app.models.hydration_log import HydrationLog
from app.models.mood_log import MoodLog
from app.models.reminder import Reminder, ReminderType, ReminderChannel

engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

USER_ID = 1
TODAY = date(2026, 3, 10)

# ---------------------------------------------------------------------------
# Dados de refeições realistas
# ---------------------------------------------------------------------------

BREAKFAST_OPTIONS = [
    {
        "name": "Café da manhã",
        "items": [
            {"food_name": "Pão integral", "quantity": 60, "unit": "g", "calories": 150, "protein": 6, "carbs": 28, "fat": 2, "fiber": 3},
            {"food_name": "Ovos mexidos", "quantity": 100, "unit": "g", "calories": 148, "protein": 10, "carbs": 1, "fat": 11, "fiber": 0},
            {"food_name": "Café com leite", "quantity": 200, "unit": "ml", "calories": 60, "protein": 3, "carbs": 6, "fat": 2, "fiber": 0},
        ]
    },
    {
        "name": "Café reforçado",
        "items": [
            {"food_name": "Aveia em flocos", "quantity": 50, "unit": "g", "calories": 185, "protein": 6, "carbs": 33, "fat": 3, "fiber": 5},
            {"food_name": "Banana", "quantity": 120, "unit": "g", "calories": 108, "protein": 1, "carbs": 27, "fat": 0, "fiber": 3},
            {"food_name": "Iogurte grego", "quantity": 150, "unit": "g", "calories": 132, "protein": 15, "carbs": 9, "fat": 4, "fiber": 0},
        ]
    },
    {
        "name": "Café simples",
        "items": [
            {"food_name": "Tapioca", "quantity": 80, "unit": "g", "calories": 240, "protein": 2, "carbs": 57, "fat": 0, "fiber": 1},
            {"food_name": "Queijo minas frescal", "quantity": 50, "unit": "g", "calories": 122, "protein": 8, "carbs": 2, "fat": 9, "fiber": 0},
            {"food_name": "Suco de laranja natural", "quantity": 200, "unit": "ml", "calories": 88, "protein": 1, "carbs": 21, "fat": 0, "fiber": 0},
        ]
    },
    {
        "name": "Café nutritivo",
        "items": [
            {"food_name": "Vitamina de frutas", "quantity": 300, "unit": "ml", "calories": 210, "protein": 8, "carbs": 38, "fat": 3, "fiber": 4},
            {"food_name": "Torrada integral", "quantity": 40, "unit": "g", "calories": 140, "protein": 5, "carbs": 26, "fat": 2, "fiber": 3},
            {"food_name": "Requeijão light", "quantity": 30, "unit": "g", "calories": 57, "protein": 3, "carbs": 2, "fat": 4, "fiber": 0},
        ]
    },
]

MORNING_SNACK_OPTIONS = [
    {
        "name": "Lanche da manhã",
        "items": [
            {"food_name": "Maçã", "quantity": 150, "unit": "g", "calories": 78, "protein": 0, "carbs": 20, "fat": 0, "fiber": 3},
            {"food_name": "Castanha do Pará", "quantity": 20, "unit": "g", "calories": 131, "protein": 3, "carbs": 2, "fat": 13, "fiber": 1},
        ]
    },
    {
        "name": "Snack matinal",
        "items": [
            {"food_name": "Iogurte natural", "quantity": 170, "unit": "g", "calories": 102, "protein": 6, "carbs": 12, "fat": 3, "fiber": 0},
            {"food_name": "Granola", "quantity": 30, "unit": "g", "calories": 134, "protein": 3, "carbs": 22, "fat": 4, "fiber": 2},
        ]
    },
    {
        "name": "Fruta",
        "items": [
            {"food_name": "Banana", "quantity": 120, "unit": "g", "calories": 108, "protein": 1, "carbs": 27, "fat": 0, "fiber": 3},
        ]
    },
]

LUNCH_OPTIONS = [
    {
        "name": "Almoço",
        "items": [
            {"food_name": "Arroz branco cozido", "quantity": 180, "unit": "g", "calories": 234, "protein": 5, "carbs": 51, "fat": 0, "fiber": 1},
            {"food_name": "Feijão carioca cozido", "quantity": 150, "unit": "g", "calories": 162, "protein": 9, "carbs": 28, "fat": 1, "fiber": 8},
            {"food_name": "Frango grelhado", "quantity": 150, "unit": "g", "calories": 248, "protein": 37, "carbs": 0, "fat": 10, "fiber": 0},
            {"food_name": "Salada de folhas", "quantity": 80, "unit": "g", "calories": 20, "protein": 2, "carbs": 3, "fat": 0, "fiber": 2},
        ]
    },
    {
        "name": "Almoço fitness",
        "items": [
            {"food_name": "Arroz integral cozido", "quantity": 150, "unit": "g", "calories": 210, "protein": 5, "carbs": 44, "fat": 2, "fiber": 3},
            {"food_name": "Feijão preto cozido", "quantity": 130, "unit": "g", "calories": 150, "protein": 9, "carbs": 27, "fat": 1, "fiber": 9},
            {"food_name": "Carne bovina magra grelhada", "quantity": 120, "unit": "g", "calories": 228, "protein": 27, "carbs": 0, "fat": 13, "fiber": 0},
            {"food_name": "Brócolis cozido", "quantity": 100, "unit": "g", "calories": 35, "protein": 3, "carbs": 7, "fat": 0, "fiber": 3},
            {"food_name": "Azeite de oliva", "quantity": 10, "unit": "ml", "calories": 90, "protein": 0, "carbs": 0, "fat": 10, "fiber": 0},
        ]
    },
    {
        "name": "Almoço leve",
        "items": [
            {"food_name": "Macarrão integral cozido", "quantity": 200, "unit": "g", "calories": 284, "protein": 10, "carbs": 57, "fat": 2, "fiber": 6},
            {"food_name": "Atum em lata", "quantity": 80, "unit": "g", "calories": 94, "protein": 21, "carbs": 0, "fat": 1, "fiber": 0},
            {"food_name": "Tomate", "quantity": 100, "unit": "g", "calories": 18, "protein": 1, "carbs": 4, "fat": 0, "fiber": 1},
            {"food_name": "Alface", "quantity": 50, "unit": "g", "calories": 8, "protein": 1, "carbs": 1, "fat": 0, "fiber": 1},
        ]
    },
    {
        "name": "Almoço completo",
        "items": [
            {"food_name": "Arroz branco cozido", "quantity": 200, "unit": "g", "calories": 260, "protein": 5, "carbs": 57, "fat": 0, "fiber": 1},
            {"food_name": "Lentilha cozida", "quantity": 100, "unit": "g", "calories": 116, "protein": 9, "carbs": 20, "fat": 0, "fiber": 8},
            {"food_name": "Tilápia assada", "quantity": 150, "unit": "g", "calories": 218, "protein": 32, "carbs": 0, "fat": 9, "fiber": 0},
            {"food_name": "Cenoura cozida", "quantity": 80, "unit": "g", "calories": 35, "protein": 1, "carbs": 8, "fat": 0, "fiber": 2},
        ]
    },
]

AFTERNOON_SNACK_OPTIONS = [
    {
        "name": "Lanche da tarde",
        "items": [
            {"food_name": "Pão integral", "quantity": 60, "unit": "g", "calories": 150, "protein": 6, "carbs": 28, "fat": 2, "fiber": 3},
            {"food_name": "Pasta de amendoim", "quantity": 20, "unit": "g", "calories": 118, "protein": 5, "carbs": 4, "fat": 10, "fiber": 1},
        ]
    },
    {
        "name": "Snack proteico",
        "items": [
            {"food_name": "Whey protein", "quantity": 30, "unit": "g", "calories": 120, "protein": 24, "carbs": 3, "fat": 2, "fiber": 0},
            {"food_name": "Leite desnatado", "quantity": 250, "unit": "ml", "calories": 88, "protein": 9, "carbs": 12, "fat": 0, "fiber": 0},
        ]
    },
    {
        "name": "Fruta e oleaginosas",
        "items": [
            {"food_name": "Uva", "quantity": 100, "unit": "g", "calories": 62, "protein": 1, "carbs": 15, "fat": 0, "fiber": 1},
            {"food_name": "Mix de castanhas", "quantity": 25, "unit": "g", "calories": 156, "protein": 4, "carbs": 5, "fat": 14, "fiber": 2},
        ]
    },
]

DINNER_OPTIONS = [
    {
        "name": "Jantar",
        "items": [
            {"food_name": "Omelete de 3 ovos", "quantity": 150, "unit": "g", "calories": 270, "protein": 21, "carbs": 3, "fat": 19, "fiber": 1},
            {"food_name": "Salada mista", "quantity": 150, "unit": "g", "calories": 45, "protein": 3, "carbs": 7, "fat": 1, "fiber": 3},
            {"food_name": "Pão de forma integral", "quantity": 50, "unit": "g", "calories": 130, "protein": 5, "carbs": 24, "fat": 2, "fiber": 3},
        ]
    },
    {
        "name": "Jantar leve",
        "items": [
            {"food_name": "Sopa de legumes", "quantity": 300, "unit": "ml", "calories": 120, "protein": 5, "carbs": 20, "fat": 2, "fiber": 4},
            {"food_name": "Frango desfiado", "quantity": 100, "unit": "g", "calories": 165, "protein": 25, "carbs": 0, "fat": 7, "fiber": 0},
        ]
    },
    {
        "name": "Jantar fitness",
        "items": [
            {"food_name": "Batata doce cozida", "quantity": 200, "unit": "g", "calories": 172, "protein": 3, "carbs": 40, "fat": 0, "fiber": 5},
            {"food_name": "Peito de frango grelhado", "quantity": 180, "unit": "g", "calories": 297, "protein": 44, "carbs": 0, "fat": 12, "fiber": 0},
            {"food_name": "Aspargos refogados", "quantity": 100, "unit": "g", "calories": 25, "protein": 3, "carbs": 4, "fat": 0, "fiber": 2},
        ]
    },
    {
        "name": "Jantar completo",
        "items": [
            {"food_name": "Arroz branco cozido", "quantity": 150, "unit": "g", "calories": 195, "protein": 4, "carbs": 43, "fat": 0, "fiber": 1},
            {"food_name": "Salmão grelhado", "quantity": 150, "unit": "g", "calories": 312, "protein": 31, "carbs": 0, "fat": 20, "fiber": 0},
            {"food_name": "Legumes grelhados", "quantity": 120, "unit": "g", "calories": 60, "protein": 2, "carbs": 12, "fat": 1, "fiber": 3},
        ]
    },
]

SUPPER_OPTIONS = [
    {
        "name": "Ceia",
        "items": [
            {"food_name": "Iogurte grego natural", "quantity": 150, "unit": "g", "calories": 132, "protein": 15, "carbs": 9, "fat": 4, "fiber": 0},
            {"food_name": "Mel", "quantity": 10, "unit": "g", "calories": 30, "protein": 0, "carbs": 8, "fat": 0, "fiber": 0},
        ]
    },
    {
        "name": "Ceia leve",
        "items": [
            {"food_name": "Leite morno", "quantity": 200, "unit": "ml", "calories": 122, "protein": 6, "carbs": 9, "fat": 6, "fiber": 0},
        ]
    },
]


async def seed():
    async with AsyncSessionLocal() as session:
        # ---- Atualizar perfil do usuário ----
        user = await session.get(User, USER_ID)
        user.calorie_goal = 2200
        user.weight_goal = 78.0
        user.water_goal_ml = 2500
        user.goal_type = GoalType.LOSE_WEIGHT

        profile = UserProfile(
            user_id=USER_ID,
            height_cm=178.0,
            current_weight=85.0,
            age=27,
            sex=Sex.MALE,
            activity_level=ActivityLevel.MODERATELY_ACTIVE,
            tdee_calculated=2380.0,
        )
        session.add(profile)

        # ---- Refeições dos últimos 30 dias ----
        print("Criando refeições...")
        for days_ago in range(30, 0, -1):
            day = TODAY - timedelta(days=days_ago)
            skip_chance = random.random()

            # Café da manhã (quase sempre)
            if skip_chance > 0.05:
                template = random.choice(BREAKFAST_OPTIONS)
                meal = Meal(user_id=USER_ID, name=template["name"], meal_type=MealType.BREAKFAST, date=day, source=MealSource.MANUAL)
                session.add(meal)
                await session.flush()
                for item_data in template["items"]:
                    session.add(MealItem(meal_id=meal.id, **item_data))

            # Lanche manhã (60% das vezes)
            if random.random() > 0.4:
                template = random.choice(MORNING_SNACK_OPTIONS)
                meal = Meal(user_id=USER_ID, name=template["name"], meal_type=MealType.MORNING_SNACK, date=day, source=MealSource.MANUAL)
                session.add(meal)
                await session.flush()
                for item_data in template["items"]:
                    session.add(MealItem(meal_id=meal.id, **item_data))

            # Almoço (quase sempre)
            if skip_chance > 0.03:
                template = random.choice(LUNCH_OPTIONS)
                meal = Meal(user_id=USER_ID, name=template["name"], meal_type=MealType.LUNCH, date=day, source=MealSource.MANUAL)
                session.add(meal)
                await session.flush()
                for item_data in template["items"]:
                    session.add(MealItem(meal_id=meal.id, **item_data))

            # Lanche tarde (70% das vezes)
            if random.random() > 0.3:
                template = random.choice(AFTERNOON_SNACK_OPTIONS)
                meal = Meal(user_id=USER_ID, name=template["name"], meal_type=MealType.AFTERNOON_SNACK, date=day, source=MealSource.MANUAL)
                session.add(meal)
                await session.flush()
                for item_data in template["items"]:
                    session.add(MealItem(meal_id=meal.id, **item_data))

            # Jantar (quase sempre)
            if skip_chance > 0.04:
                template = random.choice(DINNER_OPTIONS)
                meal = Meal(user_id=USER_ID, name=template["name"], meal_type=MealType.DINNER, date=day, source=MealSource.MANUAL)
                session.add(meal)
                await session.flush()
                for item_data in template["items"]:
                    session.add(MealItem(meal_id=meal.id, **item_data))

            # Ceia (30% das vezes)
            if random.random() > 0.7:
                template = random.choice(SUPPER_OPTIONS)
                meal = Meal(user_id=USER_ID, name=template["name"], meal_type=MealType.SUPPER, date=day, source=MealSource.MANUAL)
                session.add(meal)
                await session.flush()
                for item_data in template["items"]:
                    session.add(MealItem(meal_id=meal.id, **item_data))

        # ---- Registros de peso (tendência de queda) ----
        print("Criando registros de peso...")
        weight = 86.2
        for days_ago in range(30, 0, -3):
            day = TODAY - timedelta(days=days_ago)
            weight -= random.uniform(-0.1, 0.4)
            weight = round(weight, 1)
            session.add(WeightLog(user_id=USER_ID, weight_kg=weight, date=day))

        # ---- Hidratação (últimos 30 dias) ----
        print("Criando registros de hidratação...")
        for days_ago in range(30, 0, -1):
            day = TODAY - timedelta(days=days_ago)
            horarios = [
                time(7, 30), time(9, 0), time(11, 0),
                time(13, 30), time(15, 0), time(17, 0),
                time(19, 30), time(21, 0),
            ]
            n_copos = random.randint(5, 8)
            for t in random.sample(horarios, n_copos):
                amount = random.choice([200, 250, 300])
                session.add(HydrationLog(user_id=USER_ID, amount_ml=amount, date=day, time=t))

        # ---- Humor / Energia (últimos 30 dias) ----
        print("Criando registros de humor...")
        mood_notes = [
            "Dia produtivo, me senti bem.",
            "Um pouco cansado mas consegui treinar.",
            "Ótimo dia, energia em alta.",
            "Dia estressante no trabalho.",
            "Dormiu bem, acordou disposto.",
            None,
        ]
        for days_ago in range(30, 0, -1):
            day = TODAY - timedelta(days=days_ago)
            if random.random() > 0.15:
                session.add(MoodLog(
                    user_id=USER_ID,
                    date=day,
                    energy_level=random.randint(2, 5),
                    mood_level=random.randint(2, 5),
                    notes=random.choice(mood_notes),
                ))

        # ---- Lembretes ----
        print("Criando lembretes...")
        session.add(Reminder(
            user_id=USER_ID,
            type=ReminderType.MEAL,
            time=time(7, 0),
            days_of_week=[0, 1, 2, 3, 4, 5, 6],
            active=True,
            channel=ReminderChannel.TELEGRAM,
            message="Hora do café da manhã! Não pule a primeira refeição do dia. 🥗",
        ))
        session.add(Reminder(
            user_id=USER_ID,
            type=ReminderType.WATER,
            time=time(8, 30),
            days_of_week=[0, 1, 2, 3, 4, 5, 6],
            active=True,
            channel=ReminderChannel.TELEGRAM,
            message="Lembrete de hidratação! Beba um copo d'água. 💧",
        ))
        session.add(Reminder(
            user_id=USER_ID,
            type=ReminderType.WEIGHT,
            time=time(7, 15),
            days_of_week=[1, 4],  # segunda e quinta
            active=True,
            channel=ReminderChannel.TELEGRAM,
            message="Hora de se pesar! Registre seu peso em jejum. ⚖️",
        ))
        session.add(Reminder(
            user_id=USER_ID,
            type=ReminderType.DAILY_SUMMARY,
            time=time(21, 0),
            days_of_week=[0, 1, 2, 3, 4, 5, 6],
            active=True,
            channel=ReminderChannel.TELEGRAM,
            message="Resumo do dia: como foi sua alimentação hoje?",
        ))

        await session.commit()
        print("✓ Seed concluído com sucesso!")
        print(f"  → 30 dias de refeições (~4-6 por dia)")
        print(f"  → 10 registros de peso")
        print(f"  → 30 dias de hidratação")
        print(f"  → 30 dias de humor/energia")
        print(f"  → 4 lembretes configurados")


if __name__ == "__main__":
    asyncio.run(seed())

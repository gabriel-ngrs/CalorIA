# Importar todos os modelos nesta ordem para garantir que o Base.metadata
# esteja populado corretamente para o Alembic autogenerate.
from app.models.user import User
from app.models.profile import UserProfile
from app.models.meal import Meal
from app.models.meal_item import MealItem
from app.models.food import Food
from app.models.weight_log import WeightLog
from app.models.hydration_log import HydrationLog
from app.models.mood_log import MoodLog
from app.models.reminder import Reminder
from app.models.ai_conversation import AIConversation
from app.models.push_subscription import PushSubscription
from app.models.notification import Notification

__all__ = [
    "User",
    "UserProfile",
    "Meal",
    "MealItem",
    "Food",
    "WeightLog",
    "HydrationLog",
    "MoodLog",
    "Reminder",
    "AIConversation",
    "PushSubscription",
    "Notification",
]

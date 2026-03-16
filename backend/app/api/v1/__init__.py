from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.meals import router as meals_router
from app.api.v1.weight import router as weight_router
from app.api.v1.hydration import router as hydration_router
from app.api.v1.mood import router as mood_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.ai import router as ai_router
from app.api.v1.reminders import router as reminders_router
from app.api.v1.push import router as push_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(users_router)
router.include_router(meals_router)
router.include_router(weight_router)
router.include_router(hydration_router)
router.include_router(mood_router)
router.include_router(dashboard_router)
router.include_router(ai_router)
router.include_router(reminders_router)
router.include_router(push_router)

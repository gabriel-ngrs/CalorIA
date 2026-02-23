from __future__ import annotations

import base64
import logging
from datetime import date

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app.core.database import AsyncSessionLocal
from app.models.meal import MealSource
from app.schemas.meal import MealCreate, MealItemCreate
from app.services.ai.gemini_client import get_gemini_client
from app.services.ai.meal_parser import MealParser
from app.services.ai.vision_parser import VisionParser
from app.services.meal_service import MealService
from app.services.telegram_service import TelegramService
from app.bots.telegram.utils import (
    detect_meal_type_from_text,
    format_items_list,
    format_macros_line,
    guess_meal_type,
)

logger = logging.getLogger(__name__)

CONFIRMING = 1

_KEY_ITEMS = "pending_items"
_KEY_MEAL_TYPE = "pending_meal_type"


def _build_confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Confirmar", callback_data="confirm"),
            InlineKeyboardButton("❌ Cancelar", callback_data="cancel"),
        ]
    ])


async def _analyze_and_reply(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    description: str,
    meal_type_hint: str | None,
) -> int:
    chat_id = str(update.effective_chat.id)

    async with AsyncSessionLocal() as db:
        user = await TelegramService(db).get_user_by_chat_id(chat_id)

    if not user:
        await update.message.reply_html(
            "⚠️ Conta não vinculada. Use <code>/conectar TOKEN</code>."
        )
        return ConversationHandler.END

    await update.message.reply_html("🔍 <i>Analisando com IA...</i>")

    try:
        client = get_gemini_client()
        result = await MealParser(client).parse(
            description=description,
            user_context=f"meta {user.calorie_goal or '?'} kcal",
        )
    except Exception as exc:
        logger.error("Erro ao analisar refeição: %s", exc)
        await update.message.reply_html("❌ Não consegui analisar. Tente descrever de forma diferente.")
        return ConversationHandler.END

    if not result.items:
        await update.message.reply_html(
            "🤔 Não identifiquei alimentos na mensagem.\n"
            "Tente: <i>\"200g de arroz com frango\"</i>"
        )
        return ConversationHandler.END

    # Detecta tipo de refeição
    detected_type = detect_meal_type_from_text(description) or guess_meal_type()

    # Calcula totais
    total_cal = sum(it.calories for it in result.items)
    total_prot = sum(it.protein for it in result.items)
    total_carb = sum(it.carbs for it in result.items)
    total_fat = sum(it.fat for it in result.items)

    # Salva no contexto para confirmar depois
    context.user_data[_KEY_ITEMS] = result.items
    context.user_data[_KEY_MEAL_TYPE] = detected_type

    low_conf_note = "\n⚠️ <i>Alguns itens têm baixa confiança — verifique.</i>" if result.low_confidence else ""

    text = (
        f"🍽️ <b>Refeição identificada</b>\n\n"
        f"{format_items_list(result.items)}\n\n"
        f"{format_macros_line(total_cal, total_prot, total_carb, total_fat)}"
        f"{low_conf_note}\n\n"
        f"Está correto?"
    )

    await update.message.reply_html(text, reply_markup=_build_confirmation_keyboard())
    return CONFIRMING


async def text_meal_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text or ""
    return await _analyze_and_reply(update, context, text, None)


async def photo_meal_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    photo = update.message.photo[-1]  # maior resolução
    file = await photo.get_file()
    file_bytes = await file.download_as_bytearray()
    b64 = base64.b64encode(bytes(file_bytes)).decode()

    await update.message.reply_html("📸 <i>Analisando foto com IA...</i>")

    chat_id = str(update.effective_chat.id)
    async with AsyncSessionLocal() as db:
        user = await TelegramService(db).get_user_by_chat_id(chat_id)

    if not user:
        await update.message.reply_html(
            "⚠️ Conta não vinculada. Use <code>/conectar TOKEN</code>."
        )
        return ConversationHandler.END

    try:
        client = get_gemini_client()
        result = await VisionParser(client).parse_base64(b64, "image/jpeg")
    except Exception as exc:
        logger.error("Erro ao analisar foto: %s", exc)
        await update.message.reply_html("❌ Não consegui analisar a foto.")
        return ConversationHandler.END

    if not result.items:
        await update.message.reply_html("🤔 Não identifiquei alimentos na foto.")
        return ConversationHandler.END

    detected_type = guess_meal_type()
    context.user_data[_KEY_ITEMS] = result.items
    context.user_data[_KEY_MEAL_TYPE] = detected_type

    total_cal = sum(it.calories for it in result.items)
    total_prot = sum(it.protein for it in result.items)
    total_carb = sum(it.carbs for it in result.items)
    total_fat = sum(it.fat for it in result.items)
    low_conf_note = "\n⚠️ <i>Alguns itens têm baixa confiança.</i>" if result.low_confidence else ""

    text = (
        f"📸 <b>Foto analisada</b>\n\n"
        f"{format_items_list(result.items)}\n\n"
        f"{format_macros_line(total_cal, total_prot, total_carb, total_fat)}"
        f"{low_conf_note}\n\n"
        f"Está correto?"
    )

    await update.message.reply_html(text, reply_markup=_build_confirmation_keyboard())
    return CONFIRMING


async def confirm_meal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text("❌ Refeição cancelada.")
        context.user_data.clear()
        return ConversationHandler.END

    items = context.user_data.get(_KEY_ITEMS, [])
    meal_type = context.user_data.get(_KEY_MEAL_TYPE)
    chat_id = str(update.effective_chat.id)

    async with AsyncSessionLocal() as db:
        user = await TelegramService(db).get_user_by_chat_id(chat_id)
        if not user or not items:
            await query.edit_message_text("❌ Erro ao salvar. Tente novamente.")
            return ConversationHandler.END

        meal_data = MealCreate(
            meal_type=meal_type,
            date=date.today(),
            source=MealSource.TELEGRAM,
            items=[
                MealItemCreate(
                    food_name=it.food_name,
                    quantity=it.quantity,
                    unit=it.unit,
                    calories=it.calories,
                    protein=it.protein,
                    carbs=it.carbs,
                    fat=it.fat,
                    fiber=it.fiber,
                )
                for it in items
            ],
        )
        await MealService(db).create_meal(user.id, meal_data)

    total_cal = sum(it.calories for it in items)
    await query.edit_message_text(
        f"✅ Refeição salva! ({total_cal:.0f} kcal)\n\n"
        "Use /hoje para ver o resumo do dia.",
        parse_mode="HTML",
    )
    context.user_data.clear()
    return ConversationHandler.END


def build_registration_handler() -> ConversationHandler:  # type: ignore[type-arg]
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.TEXT & ~filters.COMMAND, text_meal_entry),
            MessageHandler(filters.PHOTO, photo_meal_entry),
        ],
        states={
            CONFIRMING: [CallbackQueryHandler(confirm_meal, pattern="^(confirm|cancel)$")],
        },
        fallbacks=[],
        per_user=True,
        per_chat=True,
    )

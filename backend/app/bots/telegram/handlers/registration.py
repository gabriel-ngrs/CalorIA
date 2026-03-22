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

from app.bots.telegram.utils import (
    detect_meal_type_from_text,
    format_items_list,
    format_macros_line,
    guess_meal_type,
)
from app.core.database import AsyncSessionLocal
from app.models.meal import MealSource
from app.schemas.ai import ParsedFoodItem
from app.schemas.meal import MealCreate, MealItemCreate
from app.services.ai.context_builder import build_meal_context
from app.services.ai.gemini_client import get_gemini_client
from app.services.ai.meal_parser import MealParser
from app.services.ai.vision_parser import VisionParser
from app.services.meal_service import MealService
from app.services.telegram_service import TelegramService

logger = logging.getLogger(__name__)

CONFIRMING = 1
EDITING = 2

_KEY_ITEMS = "pending_items"
_KEY_MEAL_TYPE = "pending_meal_type"


def _build_confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Confirmar", callback_data="confirm"),
                InlineKeyboardButton("✏️ Corrigir", callback_data="edit"),
                InlineKeyboardButton("❌ Cancelar", callback_data="cancel"),
            ]
        ]
    )


async def _analyze_and_reply(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    description: str,
    meal_type_hint: str | None,
) -> int:
    if (
        update.message is None
        or update.effective_chat is None
        or context.user_data is None
    ):
        return ConversationHandler.END
    chat_id = str(update.effective_chat.id)

    async with AsyncSessionLocal() as db:
        user = await TelegramService(db).get_user_by_chat_id(chat_id)
        if not user:
            await update.message.reply_html(
                "⚠️ Conta não vinculada. Use <code>/conectar TOKEN</code>."
            )
            return ConversationHandler.END

        user_context = await build_meal_context(
            user.id, db, date.today(), description=description
        )

    await update.message.reply_html("🔍 <i>Analisando com IA...</i>")

    try:
        client = get_gemini_client()
        async with AsyncSessionLocal() as db2:
            result = await MealParser(client).parse(
                description=description,
                user_context=user_context,
                db=db2,
            )
    except Exception as exc:
        logger.error("Erro ao analisar refeição: %s", exc)
        await update.message.reply_html(
            "❌ Não consegui analisar. Tente descrever de forma diferente."
        )
        return ConversationHandler.END

    if not result.items:
        await update.message.reply_html(
            "🤔 Não identifiquei alimentos na mensagem.\n"
            'Tente: <i>"200g de arroz com frango"</i>'
        )
        return ConversationHandler.END

    detected_type = detect_meal_type_from_text(description) or guess_meal_type()

    total_cal = sum(it.calories for it in result.items)
    total_prot = sum(it.protein for it in result.items)
    total_carb = sum(it.carbs for it in result.items)
    total_fat = sum(it.fat for it in result.items)

    context.user_data[_KEY_ITEMS] = result.items
    context.user_data[_KEY_MEAL_TYPE] = detected_type

    low_conf_note = (
        "\n⚠️ <i>Alguns itens têm baixa confiança — verifique.</i>"
        if result.low_confidence
        else ""
    )

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
    if update.message is None:
        return ConversationHandler.END
    text = update.message.text or ""
    return await _analyze_and_reply(update, context, text, None)


async def photo_meal_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if (
        update.message is None
        or update.effective_chat is None
        or context.user_data is None
    ):
        return ConversationHandler.END
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

        user_context = await build_meal_context(user.id, db, date.today())

        try:
            client = get_gemini_client()
            result = await VisionParser(client).parse_base64(
                b64, "image/jpeg", user_context, db=db
            )
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
    low_conf_note = (
        "\n⚠️ <i>Alguns itens têm baixa confiança.</i>" if result.low_confidence else ""
    )

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
    if (
        update.callback_query is None
        or update.effective_chat is None
        or context.user_data is None
    ):
        return ConversationHandler.END
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


async def edit_meal_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Usuário clicou em 'Corrigir' — pede o total de calorias correto."""
    if update.callback_query is None or context.user_data is None:
        return ConversationHandler.END
    query = update.callback_query
    await query.answer()

    items = context.user_data.get(_KEY_ITEMS, [])
    current_total = sum(it.calories for it in items)

    await query.edit_message_text(
        f"✏️ <b>Corrigir calorias</b>\n\n"
        f"Total estimado pela IA: <b>{current_total:.0f} kcal</b>\n\n"
        f"Digite o total correto de calorias desta refeição:\n"
        f"<i>(todos os macros serão ajustados proporcionalmente)</i>",
        parse_mode="HTML",
    )
    return EDITING


async def edit_meal_apply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Aplica a correção de calorias escalando todos os macros proporcionalmente."""
    if update.message is None or context.user_data is None:
        return ConversationHandler.END
    raw_text = (update.message.text or "").strip().replace(",", ".")

    try:
        new_total = float(raw_text)
        if new_total <= 0:
            raise ValueError("deve ser positivo")
    except ValueError:
        await update.message.reply_html(
            "❌ Digite apenas o número de calorias. Exemplo: <code>350</code>"
        )
        return EDITING

    items: list[ParsedFoodItem] = context.user_data.get(_KEY_ITEMS, [])
    current_total = sum(it.calories for it in items)

    if current_total <= 0:
        await update.message.reply_html("❌ Não há itens para corrigir.")
        return ConversationHandler.END

    factor = new_total / current_total
    corrected = [
        ParsedFoodItem(
            food_name=it.food_name,
            quantity=round(it.quantity * factor, 1),
            unit=it.unit,
            calories=round(it.calories * factor, 1),
            protein=round(it.protein * factor, 1),
            carbs=round(it.carbs * factor, 1),
            fat=round(it.fat * factor, 1),
            fiber=round(it.fiber * factor, 1),
            confidence=it.confidence,
        )
        for it in items
    ]

    context.user_data[_KEY_ITEMS] = corrected

    total_cal = sum(it.calories for it in corrected)
    total_prot = sum(it.protein for it in corrected)
    total_carb = sum(it.carbs for it in corrected)
    total_fat = sum(it.fat for it in corrected)

    text = (
        f"✏️ <b>Refeição corrigida</b>\n\n"
        f"{format_items_list(corrected)}\n\n"
        f"{format_macros_line(total_cal, total_prot, total_carb, total_fat)}\n\n"
        f"Está correto?"
    )

    await update.message.reply_html(text, reply_markup=_build_confirmation_keyboard())
    return CONFIRMING


def build_registration_handler() -> ConversationHandler:  # type: ignore[type-arg]
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.TEXT & ~filters.COMMAND, text_meal_entry),
            MessageHandler(filters.PHOTO, photo_meal_entry),
        ],
        states={
            CONFIRMING: [
                CallbackQueryHandler(confirm_meal, pattern="^(confirm|cancel)$"),
                CallbackQueryHandler(edit_meal_request, pattern="^edit$"),
            ],
            EDITING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_meal_apply),
            ],
        },
        fallbacks=[],
        per_user=True,
        per_chat=True,
    )

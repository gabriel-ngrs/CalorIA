from __future__ import annotations

from datetime import date, datetime, time

from telegram import Update
from telegram.ext import ContextTypes

from app.core.database import AsyncSessionLocal
from app.schemas.logs import HydrationLogCreate, MoodLogCreate, WeightLogCreate
from app.services.log_service import HydrationService, MoodService, WeightService
from app.services.telegram_service import TelegramService


async def peso_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.effective_chat is None:
        return
    if not context.args:
        await update.message.reply_html("ℹ️ Use: <code>/peso 80.5</code>")
        return
    try:
        weight = float(context.args[0].replace(",", "."))
    except ValueError:
        await update.message.reply_html("❌ Peso inválido. Exemplo: <code>/peso 80.5</code>")
        return

    chat_id = str(update.effective_chat.id)
    async with AsyncSessionLocal() as db:
        user = await TelegramService(db).get_user_by_chat_id(chat_id)
        if not user:
            await update.message.reply_html("⚠️ Conta não vinculada. Use <code>/conectar TOKEN</code>.")
            return
        await WeightService(db).create(
            user.id, WeightLogCreate(weight_kg=weight, date=date.today())
        )

    motivation = "Continue assim! 💪" if (user.weight_goal and weight <= user.weight_goal) else "Registrado! 📊"
    await update.message.reply_html(f"⚖️ Peso <b>{weight:.1f} kg</b> registrado. {motivation}")


async def agua_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.effective_chat is None:
        return
    if not context.args:
        await update.message.reply_html("ℹ️ Use: <code>/agua 300</code> (em ml)")
        return
    try:
        ml = int(context.args[0])
        if ml <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_html("❌ Valor inválido. Exemplo: <code>/agua 300</code>")
        return

    chat_id = str(update.effective_chat.id)
    async with AsyncSessionLocal() as db:
        user = await TelegramService(db).get_user_by_chat_id(chat_id)
        if not user:
            await update.message.reply_html("⚠️ Conta não vinculada. Use <code>/conectar TOKEN</code>.")
            return
        now = datetime.now()
        await HydrationService(db).create(
            user.id,
            HydrationLogCreate(amount_ml=ml, date=date.today(), time=time(now.hour, now.minute)),
        )
        summary = await HydrationService(db).get_day_summary(user.id, date.today())

    total = summary.total_ml
    goal = 2000
    pct = min(total / goal * 100, 100)
    bar = "💧" * int(pct / 10) + "⬜" * (10 - int(pct / 10))
    await update.message.reply_html(
        f"💧 <b>+{ml} ml</b> registrado!\n\n"
        f"{bar}\n"
        f"Total hoje: <b>{total} ml</b> / {goal} ml ({pct:.0f}%)"
    )


async def humor_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.effective_chat is None:
        return
    if not context.args or len(context.args) < 2:
        await update.message.reply_html(
            "ℹ️ Use: <code>/humor ENERGIA HUMOR</code> (valores de 1 a 5)\n"
            "Exemplo: <code>/humor 4 5</code>"
        )
        return
    try:
        energy = int(context.args[0])
        mood = int(context.args[1])
        if not (1 <= energy <= 5 and 1 <= mood <= 5):
            raise ValueError
    except ValueError:
        await update.message.reply_html("❌ Valores devem ser entre 1 e 5.")
        return

    notes = " ".join(context.args[2:]) if len(context.args) > 2 else None
    chat_id = str(update.effective_chat.id)

    async with AsyncSessionLocal() as db:
        user = await TelegramService(db).get_user_by_chat_id(chat_id)
        if not user:
            await update.message.reply_html("⚠️ Conta não vinculada. Use <code>/conectar TOKEN</code>.")
            return
        await MoodService(db).create(
            user.id,
            MoodLogCreate(date=date.today(), energy_level=energy, mood_level=mood, notes=notes),
        )

    energy_emoji = ["😴", "😪", "😐", "😊", "⚡"][energy - 1]
    mood_emoji = ["😞", "😕", "😐", "😊", "😄"][mood - 1]
    await update.message.reply_html(
        f"✅ Registrado!\n\n"
        f"⚡ Energia: {energy_emoji} {energy}/5\n"
        f"😊 Humor: {mood_emoji} {mood}/5"
        + (f"\n📝 {notes}" if notes else "")
    )

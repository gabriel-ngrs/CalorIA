from __future__ import annotations

from datetime import date, time

from telegram import Update
from telegram.ext import ContextTypes

from app.core.database import AsyncSessionLocal
from app.models.reminder import ReminderChannel, ReminderType
from app.schemas.reminder import ReminderCreate
from app.services.ai.gemini_client import get_gemini_client
from app.services.ai.insights_generator import InsightsGenerator
from app.services.dashboard_service import DashboardService
from app.services.meal_service import MealService
from app.services.telegram_service import TelegramService
from app.services.log_service import WeightService
from app.bots.telegram.utils import format_macros_line, meal_type_emoji, meal_type_label

_REMINDER_TYPE_MAP = {
    "cafe": ReminderType.MEAL,
    "café": ReminderType.MEAL,
    "almoco": ReminderType.MEAL,
    "almoço": ReminderType.MEAL,
    "janta": ReminderType.MEAL,
    "jantar": ReminderType.MEAL,
    "agua": ReminderType.WATER,
    "água": ReminderType.WATER,
    "peso": ReminderType.WEIGHT,
    "resumo": ReminderType.DAILY_SUMMARY,
}


async def resumo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.effective_chat.id)
    today = date.today()

    async with AsyncSessionLocal() as db:
        user = await TelegramService(db).get_user_by_chat_id(chat_id)
        if not user:
            await update.message.reply_html("⚠️ Conta não vinculada. Use <code>/conectar TOKEN</code>.")
            return
        dashboard = await DashboardService(db).get_today(user.id, today)

    n = dashboard.nutrition
    h = dashboard.hydration
    goal_line = ""
    if user.calorie_goal:
        remaining = user.calorie_goal - n.total_calories
        goal_line = f"\n🎯 Restam: <b>{remaining:.0f} kcal</b> para a meta"

    meals_text = ""
    for meal in n.meals:
        total_cal = sum(it.calories for it in meal.items)
        meals_text += (
            f"\n{meal_type_emoji(meal.meal_type)} <b>{meal_type_label(meal.meal_type)}</b> "
            f"({total_cal:.0f} kcal)"
        )

    text = (
        f"📊 <b>Resumo — {today.strftime('%d/%m/%Y')}</b>\n\n"
        f"{format_macros_line(n.total_calories, n.total_protein, n.total_carbs, n.total_fat)}"
        f"{goal_line}\n"
        f"💧 Água: <b>{h.total_ml} ml</b>\n"
        f"🍽️ Refeições ({n.meals_count}):{meals_text or ' nenhuma'}"
    )
    await update.message.reply_html(text)


async def semana_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.effective_chat.id)
    async with AsyncSessionLocal() as db:
        user = await TelegramService(db).get_user_by_chat_id(chat_id)
        if not user:
            await update.message.reply_html("⚠️ Conta não vinculada.")
            return
        summary = await DashboardService(db).get_weekly(user.id, date.today())

    text = (
        f"📅 <b>Semana — {summary.start_date.strftime('%d/%m')} a {summary.end_date.strftime('%d/%m/%Y')}</b>\n\n"
        f"Dias registrados: <b>{summary.total_days_logged}/7</b>\n\n"
        f"<b>Médias diárias:</b>\n"
        f"{format_macros_line(summary.avg_calories, summary.avg_protein, summary.avg_carbs, summary.avg_fat)}"
    )
    await update.message.reply_html(text)


async def relatorio_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.effective_chat.id)
    await update.message.reply_html("🤖 <i>Gerando insight com IA...</i>")

    async with AsyncSessionLocal() as db:
        user = await TelegramService(db).get_user_by_chat_id(chat_id)
        if not user:
            await update.message.reply_html("⚠️ Conta não vinculada.")
            return
        try:
            gen = InsightsGenerator(get_gemini_client(), db)
            insight = await gen.daily_insight(user.id, date.today())
            await update.message.reply_html(f"🧠 <b>Insight do dia</b>\n\n{insight.content}")
        except Exception:
            await update.message.reply_html("❌ Não foi possível gerar o insight agora. Tente novamente.")


async def historico_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.effective_chat.id)
    async with AsyncSessionLocal() as db:
        user = await TelegramService(db).get_user_by_chat_id(chat_id)
        if not user:
            await update.message.reply_html("⚠️ Conta não vinculada.")
            return
        meals = await MealService(db).list_meals(user.id, limit=7)

    if not meals:
        await update.message.reply_html("📭 Nenhuma refeição registrada ainda.")
        return

    lines = []
    for meal in meals:
        total_cal = sum(it.calories for it in meal.items)
        items_preview = ", ".join(it.food_name for it in meal.items[:2])
        if len(meal.items) > 2:
            items_preview += f" +{len(meal.items) - 2}"
        lines.append(
            f"{meal_type_emoji(meal.meal_type)} <b>{meal.date.strftime('%d/%m')}</b> "
            f"{meal_type_label(meal.meal_type)} — {items_preview} ({total_cal:.0f} kcal)"
        )

    await update.message.reply_html("🍽️ <b>Últimas refeições</b>\n\n" + "\n".join(lines))


async def lembrete_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 2:
        await update.message.reply_html(
            "ℹ️ Use: <code>/lembrete TIPO HH:MM</code>\n"
            "Tipos: cafe, almoco, janta, agua, peso, resumo\n"
            "Exemplo: <code>/lembrete cafe 07:30</code>"
        )
        return

    type_str = context.args[0].lower()
    time_str = context.args[1]
    reminder_type = _REMINDER_TYPE_MAP.get(type_str)
    if not reminder_type:
        await update.message.reply_html(f"❌ Tipo inválido: {type_str}")
        return

    try:
        h, m = map(int, time_str.split(":"))
        reminder_time = time(h, m)
    except ValueError:
        await update.message.reply_html("❌ Hora inválida. Use o formato HH:MM (ex: 07:30)")
        return

    chat_id = str(update.effective_chat.id)
    from app.services.reminder_service import ReminderService

    async with AsyncSessionLocal() as db:
        user = await TelegramService(db).get_user_by_chat_id(chat_id)
        if not user:
            await update.message.reply_html("⚠️ Conta não vinculada.")
            return
        reminder = await ReminderService(db).create(
            user.id,
            ReminderCreate(
                type=reminder_type,
                time=reminder_time,
                channel=ReminderChannel.TELEGRAM,
                days_of_week=[0, 1, 2, 3, 4, 5, 6],
            ),
        )

    await update.message.reply_html(
        f"✅ Lembrete criado!\n\n"
        f"⏰ Tipo: <b>{type_str}</b>\n"
        f"🕐 Hora: <b>{time_str}</b>\n"
        f"📅 Todos os dias\n"
        f"🆔 ID: <code>{reminder.id}</code>"
    )


async def lembretes_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from app.services.reminder_service import ReminderService

    chat_id = str(update.effective_chat.id)
    async with AsyncSessionLocal() as db:
        user = await TelegramService(db).get_user_by_chat_id(chat_id)
        if not user:
            await update.message.reply_html("⚠️ Conta não vinculada.")
            return
        reminders = await ReminderService(db).list(user.id)

    if not reminders:
        await update.message.reply_html("📭 Nenhum lembrete configurado.")
        return

    days_abbr = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    lines = []
    for r in reminders:
        days = ", ".join(days_abbr[d] for d in r.days_of_week) if r.days_of_week != list(range(7)) else "Todos os dias"
        status = "✅" if r.active else "⏸️"
        lines.append(f"{status} <code>#{r.id}</code> {r.type.value} — {r.time.strftime('%H:%M')} ({days})")

    await update.message.reply_html("⏰ <b>Seus lembretes</b>\n\n" + "\n".join(lines))


async def remover_lembrete_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from app.services.reminder_service import ReminderService

    if not context.args:
        await update.message.reply_html("ℹ️ Use: <code>/remover-lembrete ID</code>")
        return
    try:
        reminder_id = int(context.args[0])
    except ValueError:
        await update.message.reply_html("❌ ID inválido.")
        return

    chat_id = str(update.effective_chat.id)
    async with AsyncSessionLocal() as db:
        user = await TelegramService(db).get_user_by_chat_id(chat_id)
        if not user:
            await update.message.reply_html("⚠️ Conta não vinculada.")
            return
        deleted = await ReminderService(db).delete(user.id, reminder_id)

    if deleted:
        await update.message.reply_html(f"✅ Lembrete <code>#{reminder_id}</code> removido.")
    else:
        await update.message.reply_html(f"❌ Lembrete <code>#{reminder_id}</code> não encontrado.")

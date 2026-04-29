from __future__ import annotations

from datetime import date

from telegram import Update
from telegram.ext import ContextTypes

from app.bots.telegram.utils import format_macros_line, meal_type_emoji, meal_type_label
from app.core.database import AsyncSessionLocal
from app.services.log_service import HydrationService
from app.services.meal_service import MealService
from app.services.telegram_service import TelegramService

_WELCOME = """👋 Olá! Sou o <b>CalorIA</b>, seu diário alimentar inteligente.

<b>Como usar:</b>
• Envie uma descrição do que comeu (ex: <i>"200g de arroz com frango grelhado"</i>)
• Envie uma foto do seu prato
• Eu analiso com IA e registro automaticamente!

<b>Comandos disponíveis:</b>
/ajuda — lista completa de comandos
/conectar — vincular sua conta CalorIA
/hoje — resumo do dia
/perfil — seus dados e metas"""


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    await update.message.reply_html(_WELCOME)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    text = """<b>📋 Comandos CalorIA</b>

<b>Conta:</b>
/conectar &lt;token&gt; — vincular conta
/perfil — dados e metas do perfil

<b>Registro rápido:</b>
/peso 80.5 — registrar peso (kg)
/agua 300 — registrar água (ml)
/humor 4 5 — humor e energia (1–5)

<b>Consultas:</b>
/hoje — resumo do dia
/resumo — resumo detalhado do dia
/semana — resumo semanal
/relatorio — insights da IA
/historico — últimas refeições

<b>Lembretes:</b>
/lembrete cafe 07:30 — criar lembrete
/lembretes — listar lembretes
/remover-lembrete &lt;id&gt; — remover lembrete

<b>Para registrar uma refeição:</b>
Basta enviar texto ou foto! A IA identifica os alimentos automaticamente."""
    await update.message.reply_html(text)


async def conectar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.effective_chat is None:
        return
    if not context.args:
        await update.message.reply_html(
            "ℹ️ Use: <code>/conectar TOKEN</code>\n\n"
            "Gere o token em <b>Configurações → Conectar Bot</b> no dashboard web."
        )
        return

    token = context.args[0].strip()
    chat_id = str(update.effective_chat.id)

    async with AsyncSessionLocal() as db:
        user = await TelegramService(db).link_account(token, chat_id)

    if user:
        await update.message.reply_html(
            f"✅ Conta vinculada com sucesso!\n\nBem-vindo, <b>{user.name}</b>! 🎉\n\n"
            "Agora você pode enviar textos ou fotos de refeições para registrar."
        )
    else:
        await update.message.reply_html(
            "❌ Token inválido ou expirado.\n\n"
            "Gere um novo token no dashboard web (válido por 10 minutos)."
        )


async def perfil_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.effective_chat is None:
        return
    chat_id = str(update.effective_chat.id)
    async with AsyncSessionLocal() as db:
        user = await TelegramService(db).get_user_by_chat_id(chat_id)

    if not user:
        await _send_not_linked(update)
        return

    profile = user.profile
    tdee_text = (
        f"{profile.tdee_calculated:.0f} kcal/dia"
        if (profile and profile.tdee_calculated)
        else "não calculado"
    )
    calorie_goal = f"{user.calorie_goal} kcal" if user.calorie_goal else "não definida"
    weight_goal = f"{user.weight_goal} kg" if user.weight_goal else "não definida"

    text = f"""👤 <b>Perfil — {user.name}</b>

📧 E-mail: {user.email}
🎯 Meta calórica: {calorie_goal}
⚖️ Meta de peso: {weight_goal}
🔥 TDEE estimado: {tdee_text}"""

    await update.message.reply_html(text)


async def hoje_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.effective_chat is None:
        return
    chat_id = str(update.effective_chat.id)
    async with AsyncSessionLocal() as db:
        svc = TelegramService(db)
        user = await svc.get_user_by_chat_id(chat_id)
        if not user:
            await _send_not_linked(update)
            return

        today = date.today()
        summary = await MealService(db).get_daily_summary(user.id, today)
        hydration = await HydrationService(db).get_day_summary(user.id, today)

    goal_text = ""
    if user.calorie_goal:
        pct = (summary.total_calories / user.calorie_goal) * 100
        bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
        goal_text = f"\n[{bar}] {pct:.0f}%"

    meals_text = ""
    for meal in summary.meals:
        emoji = meal_type_emoji(meal.meal_type)
        label = meal_type_label(meal.meal_type)
        items = ", ".join(it.food_name for it in meal.items[:3])
        if len(meal.items) > 3:
            items += f" +{len(meal.items) - 3}"
        meals_text += f"\n{emoji} <b>{label}:</b> {items}"

    text = f"""📅 <b>Hoje — {today.strftime("%d/%m/%Y")}</b>

{format_macros_line(summary.total_calories, summary.total_protein, summary.total_carbs, summary.total_fat)}{goal_text}
💧 Hidratação: {hydration.total_ml} ml
{meals_text if meals_text else "\n<i>Nenhuma refeição registrada ainda.</i>"}"""

    await update.message.reply_html(text)


async def _send_not_linked(update: Update) -> None:
    if update.message is None:
        return
    await update.message.reply_html(
        "⚠️ Sua conta ainda não está vinculada.\n\n"
        "Acesse o dashboard web → <b>Conectar Bot</b> → gere um token.\n"
        "Depois envie: <code>/conectar TOKEN</code>"
    )

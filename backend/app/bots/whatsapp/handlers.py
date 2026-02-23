from __future__ import annotations

import base64
import logging
from datetime import date, datetime, time
from typing import Any

import redis.asyncio as aioredis

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.meal import MealSource
from app.models.reminder import ReminderChannel, ReminderType
from app.schemas.logs import HydrationLogCreate, MoodLogCreate, WeightLogCreate
from app.schemas.meal import MealCreate, MealItemCreate
from app.schemas.reminder import ReminderCreate
from app.services.ai.gemini_client import get_gemini_client
from app.services.ai.meal_parser import MealParser
from app.services.ai.vision_parser import VisionParser
from app.services.ai.insights_generator import InsightsGenerator
from app.services.dashboard_service import DashboardService
from app.services.log_service import HydrationService, MoodService, WeightService
from app.services.meal_service import MealService
from app.services.reminder_service import ReminderService
from app.services.whatsapp_service import WhatsAppService
from app.bots.whatsapp.sender import send_text, send_buttons
from app.bots.telegram.utils import (
    detect_meal_type_from_text,
    format_items_list,
    format_macros_line,
    guess_meal_type,
    meal_type_emoji,
    meal_type_label,
)

logger = logging.getLogger(__name__)

_PENDING_PREFIX = "wa_pending:"
_PENDING_TTL = 300  # 5 minutos

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


async def _store_pending(number: str, items_json: str) -> None:
    async with aioredis.from_url(settings.REDIS_URL, decode_responses=True) as r:
        await r.setex(f"{_PENDING_PREFIX}{number}", _PENDING_TTL, items_json)


async def _load_pending(number: str) -> str | None:
    async with aioredis.from_url(settings.REDIS_URL, decode_responses=True) as r:
        return await r.get(f"{_PENDING_PREFIX}{number}")


async def _clear_pending(number: str) -> None:
    async with aioredis.from_url(settings.REDIS_URL, decode_responses=True) as r:
        await r.delete(f"{_PENDING_PREFIX}{number}")


# ---------------------------------------------------------------------------
# Dispatcher principal
# ---------------------------------------------------------------------------

async def handle_text_message(number: str, text: str) -> None:
    """Roteia mensagem de texto: comandos (!) ou análise de refeição."""
    stripped = text.strip()

    # Confirmação de refeição pendente
    lower = stripped.lower()
    if lower in ("sim", "s", "yes", "confirmar"):
        await _confirm_pending_meal(number)
        return
    if lower in ("não", "nao", "n", "cancelar", "cancel"):
        await _cancel_pending_meal(number)
        return

    if stripped.startswith("!"):
        await _dispatch_command(number, stripped[1:])
    else:
        await _handle_meal_text(number, stripped)


async def handle_image_message(number: str, image_bytes: bytes, caption: str = "") -> None:
    """Analisa foto de prato com IA e pede confirmação."""
    await send_text(number, "📸 _Analisando foto com IA..._")

    async with AsyncSessionLocal() as db:
        user = await WhatsAppService(db).get_user_by_number(number)

    if not user:
        await send_text(number, "⚠️ Conta não vinculada. Use *!conectar TOKEN*.")
        return

    try:
        b64 = base64.b64encode(image_bytes).decode()
        client = get_gemini_client()
        result = await VisionParser(client).parse_base64(b64, "image/jpeg")
    except Exception as exc:
        logger.error("Erro ao analisar foto WhatsApp: %s", exc)
        await send_text(number, "❌ Não consegui analisar a foto.")
        return

    if not result.items:
        await send_text(number, "🤔 Não identifiquei alimentos na foto.")
        return

    await _present_meal_for_confirmation(number, result, source="photo")


# ---------------------------------------------------------------------------
# Confirmação de refeição
# ---------------------------------------------------------------------------

async def _present_meal_for_confirmation(number: str, result, source: str = "text") -> None:
    import json

    items_data = [
        {
            "food_name": it.food_name,
            "quantity": it.quantity,
            "unit": it.unit,
            "calories": it.calories,
            "protein": it.protein,
            "carbs": it.carbs,
            "fat": it.fat,
            "fiber": it.fiber,
        }
        for it in result.items
    ]
    await _store_pending(number, json.dumps(items_data))

    total_cal = sum(it.calories for it in result.items)
    total_prot = sum(it.protein for it in result.items)
    total_carb = sum(it.carbs for it in result.items)
    total_fat = sum(it.fat for it in result.items)

    title = "📸 *Foto analisada*" if source == "photo" else "🍽️ *Refeição identificada*"
    low_conf = "\n⚠️ _Alguns itens têm baixa confiança — verifique._" if result.low_confidence else ""

    items_text = "\n".join(f"• {it.food_name} — {it.quantity:.0f}{it.unit}" for it in result.items)
    macros = (
        f"🔥 {total_cal:.0f} kcal | 🥩 {total_prot:.1f}g prot | "
        f"🍞 {total_carb:.1f}g carb | 🧈 {total_fat:.1f}g gord"
    )

    msg = f"{title}\n\n{items_text}\n\n{macros}{low_conf}\n\nEstá correto? Responda *sim* ou *não*."
    await send_text(number, msg)


async def _confirm_pending_meal(number: str) -> None:
    import json

    data = await _load_pending(number)
    if not data:
        await send_text(number, "⚠️ Nenhuma refeição pendente de confirmação.")
        return

    items_data = json.loads(data)
    await _clear_pending(number)

    async with AsyncSessionLocal() as db:
        user = await WhatsAppService(db).get_user_by_number(number)
        if not user:
            await send_text(number, "⚠️ Conta não vinculada.")
            return

        meal_type = guess_meal_type()
        meal_data = MealCreate(
            meal_type=meal_type,
            date=date.today(),
            source=MealSource.WHATSAPP,
            items=[
                MealItemCreate(
                    food_name=it["food_name"],
                    quantity=it["quantity"],
                    unit=it["unit"],
                    calories=it["calories"],
                    protein=it["protein"],
                    carbs=it["carbs"],
                    fat=it["fat"],
                    fiber=it.get("fiber"),
                )
                for it in items_data
            ],
        )
        await MealService(db).create_meal(user.id, meal_data)

    total_cal = sum(it["calories"] for it in items_data)
    await send_text(
        number,
        f"✅ Refeição salva! ({total_cal:.0f} kcal)\n\nUse *!hoje* para ver o resumo do dia."
    )


async def _cancel_pending_meal(number: str) -> None:
    await _clear_pending(number)
    await send_text(number, "❌ Refeição cancelada.")


# ---------------------------------------------------------------------------
# Análise de texto → refeição
# ---------------------------------------------------------------------------

async def _handle_meal_text(number: str, text: str) -> None:
    async with AsyncSessionLocal() as db:
        user = await WhatsAppService(db).get_user_by_number(number)

    if not user:
        await send_text(
            number,
            "👋 Olá! Para começar, vincule sua conta com *!conectar TOKEN*.\n"
            "Gere o token em *Configurações → Conectar Bot* no dashboard web."
        )
        return

    await send_text(number, "🔍 _Analisando com IA..._")

    try:
        client = get_gemini_client()
        result = await MealParser(client).parse(
            description=text,
            user_context=f"meta {user.calorie_goal or '?'} kcal",
        )
    except Exception as exc:
        logger.error("Erro ao analisar refeição WhatsApp: %s", exc)
        await send_text(number, "❌ Não consegui analisar. Tente descrever de forma diferente.")
        return

    if not result.items:
        await send_text(
            number,
            "🤔 Não identifiquei alimentos na mensagem.\n"
            'Tente: _"200g de arroz com frango"_'
        )
        return

    await _present_meal_for_confirmation(number, result, source="text")


# ---------------------------------------------------------------------------
# Dispatcher de comandos
# ---------------------------------------------------------------------------

async def _dispatch_command(number: str, command_line: str) -> None:
    parts = command_line.strip().split()
    if not parts:
        return
    cmd = parts[0].lower()
    args = parts[1:]

    dispatch: dict[str, Any] = {  # type: ignore[misc]
        "start": _cmd_start,
        "ajuda": _cmd_ajuda,
        "help": _cmd_ajuda,
        "conectar": _cmd_conectar,
        "perfil": _cmd_perfil,
        "hoje": _cmd_hoje,
        "resumo": _cmd_resumo,
        "semana": _cmd_semana,
        "relatorio": _cmd_relatorio,
        "histórico": _cmd_historico,
        "historico": _cmd_historico,
        "peso": _cmd_peso,
        "agua": _cmd_agua,
        "água": _cmd_agua,
        "humor": _cmd_humor,
        "lembrete": _cmd_lembrete,
        "lembretes": _cmd_lembretes,
        "remover-lembrete": _cmd_remover_lembrete,
    }

    handler = dispatch.get(cmd)
    if handler:
        await handler(number, args)
    else:
        await send_text(number, f"❓ Comando desconhecido: *!{cmd}*\nUse *!ajuda* para ver os comandos.")


# ---------------------------------------------------------------------------
# Handlers de comando individuais  # noqa: E265
# ---------------------------------------------------------------------------

async def _cmd_start(number: str, args: list[str]) -> None:
    await send_text(
        number,
        "👋 Olá! Sou o *CalorIA*, seu diário alimentar inteligente.\n\n"
        "*Como usar:*\n"
        "• Envie o que comeu: _\"200g de arroz com frango\"_\n"
        "• Envie uma foto do prato\n"
        "• Eu analiso com IA e registro automaticamente!\n\n"
        "Use *!ajuda* para ver todos os comandos."
    )


async def _cmd_ajuda(number: str, args: list[str]) -> None:
    await send_text(
        number,
        "*📋 Comandos CalorIA*\n\n"
        "*Conta:*\n"
        "!conectar TOKEN — vincular conta\n"
        "!perfil — dados e metas\n\n"
        "*Registro rápido:*\n"
        "!peso 80.5 — registrar peso (kg)\n"
        "!agua 300 — registrar água (ml)\n"
        "!humor 4 5 — humor e energia (1–5)\n\n"
        "*Consultas:*\n"
        "!hoje — resumo do dia\n"
        "!resumo — resumo detalhado\n"
        "!semana — resumo semanal\n"
        "!relatorio — insights da IA\n"
        "!historico — últimas refeições\n\n"
        "*Lembretes:*\n"
        "!lembrete cafe 07:30 — criar lembrete\n"
        "!lembretes — listar lembretes\n"
        "!remover-lembrete ID — remover\n\n"
        "*Refeição:* envie texto ou foto direto!"
    )


async def _cmd_conectar(number: str, args: list[str]) -> None:
    if not args:
        await send_text(
            number,
            "ℹ️ Use: *!conectar TOKEN*\n\n"
            "Gere o token em *Configurações → Conectar Bot* no dashboard web."
        )
        return

    token = args[0].strip()
    async with AsyncSessionLocal() as db:
        user = await WhatsAppService(db).link_account(token, number)

    if user:
        await send_text(
            number,
            f"✅ Conta vinculada com sucesso!\n\nBem-vindo, *{user.name}*! 🎉\n\n"
            "Agora você pode enviar textos ou fotos de refeições para registrar."
        )
    else:
        await send_text(
            number,
            "❌ Token inválido ou expirado.\n\n"
            "Gere um novo token no dashboard web (válido por 10 minutos)."
        )


async def _cmd_perfil(number: str, args: list[str]) -> None:
    async with AsyncSessionLocal() as db:
        user = await WhatsAppService(db).get_user_by_number(number)

    if not user:
        await send_text(number, "⚠️ Conta não vinculada. Use *!conectar TOKEN*.")
        return

    profile = user.profile
    tdee_text = f"{profile.tdee_calculated:.0f} kcal/dia" if (profile and profile.tdee_calculated) else "não calculado"
    calorie_goal = f"{user.calorie_goal} kcal" if user.calorie_goal else "não definida"
    weight_goal = f"{user.weight_goal} kg" if user.weight_goal else "não definida"

    await send_text(
        number,
        f"👤 *Perfil — {user.name}*\n\n"
        f"📧 E-mail: {user.email}\n"
        f"🎯 Meta calórica: {calorie_goal}\n"
        f"⚖️ Meta de peso: {weight_goal}\n"
        f"🔥 TDEE estimado: {tdee_text}"
    )


async def _cmd_hoje(number: str, args: list[str]) -> None:
    async with AsyncSessionLocal() as db:
        user = await WhatsAppService(db).get_user_by_number(number)
        if not user:
            await send_text(number, "⚠️ Conta não vinculada. Use *!conectar TOKEN*.")
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
        label = meal_type_label(meal.meal_type)
        items = ", ".join(it.food_name for it in meal.items[:3])
        if len(meal.items) > 3:
            items += f" +{len(meal.items) - 3}"
        meals_text += f"\n{meal_type_emoji(meal.meal_type)} *{label}:* {items}"

    macros = (
        f"🔥 *{summary.total_calories:.0f} kcal* | "
        f"🥩 {summary.total_protein:.1f}g prot | "
        f"🍞 {summary.total_carbs:.1f}g carb | "
        f"🧈 {summary.total_fat:.1f}g gord"
    )

    await send_text(
        number,
        f"📅 *Hoje — {today.strftime('%d/%m/%Y')}*\n\n"
        f"{macros}{goal_text}\n"
        f"💧 Hidratação: {hydration.total_ml} ml"
        + (meals_text if meals_text else "\n\n_Nenhuma refeição registrada ainda._")
    )


async def _cmd_resumo(number: str, args: list[str]) -> None:
    today = date.today()
    async with AsyncSessionLocal() as db:
        user = await WhatsAppService(db).get_user_by_number(number)
        if not user:
            await send_text(number, "⚠️ Conta não vinculada.")
            return
        dashboard = await DashboardService(db).get_today(user.id, today)

    n = dashboard.nutrition
    h = dashboard.hydration
    goal_line = ""
    if user.calorie_goal:
        remaining = user.calorie_goal - n.total_calories
        goal_line = f"\n🎯 Restam: *{remaining:.0f} kcal* para a meta"

    meals_text = ""
    for meal in n.meals:
        total_cal = sum(it.calories for it in meal.items)
        meals_text += (
            f"\n{meal_type_emoji(meal.meal_type)} *{meal_type_label(meal.meal_type)}* "
            f"({total_cal:.0f} kcal)"
        )

    macros = (
        f"🔥 *{n.total_calories:.0f} kcal* | "
        f"🥩 {n.total_protein:.1f}g prot | "
        f"🍞 {n.total_carbs:.1f}g carb | "
        f"🧈 {n.total_fat:.1f}g gord"
    )

    await send_text(
        number,
        f"📊 *Resumo — {today.strftime('%d/%m/%Y')}*\n\n"
        f"{macros}"
        f"{goal_line}\n"
        f"💧 Água: *{h.total_ml} ml*\n"
        f"🍽️ Refeições ({n.meals_count}):{meals_text or ' nenhuma'}"
    )


async def _cmd_semana(number: str, args: list[str]) -> None:
    async with AsyncSessionLocal() as db:
        user = await WhatsAppService(db).get_user_by_number(number)
        if not user:
            await send_text(number, "⚠️ Conta não vinculada.")
            return
        summary = await DashboardService(db).get_weekly(user.id, date.today())

    macros = (
        f"🔥 *{summary.avg_calories:.0f} kcal* | "
        f"🥩 {summary.avg_protein:.1f}g prot | "
        f"🍞 {summary.avg_carbs:.1f}g carb | "
        f"🧈 {summary.avg_fat:.1f}g gord"
    )

    await send_text(
        number,
        f"📅 *Semana — {summary.start_date.strftime('%d/%m')} a {summary.end_date.strftime('%d/%m/%Y')}*\n\n"
        f"Dias registrados: *{summary.total_days_logged}/7*\n\n"
        f"*Médias diárias:*\n{macros}"
    )


async def _cmd_relatorio(number: str, args: list[str]) -> None:
    await send_text(number, "🤖 _Gerando insight com IA..._")
    async with AsyncSessionLocal() as db:
        user = await WhatsAppService(db).get_user_by_number(number)
        if not user:
            await send_text(number, "⚠️ Conta não vinculada.")
            return
        try:
            gen = InsightsGenerator(get_gemini_client(), db)
            insight = await gen.daily_insight(user.id, date.today())
            await send_text(number, f"🧠 *Insight do dia*\n\n{insight.content}")
        except Exception:
            await send_text(number, "❌ Não foi possível gerar o insight agora. Tente novamente.")


async def _cmd_historico(number: str, args: list[str]) -> None:
    async with AsyncSessionLocal() as db:
        user = await WhatsAppService(db).get_user_by_number(number)
        if not user:
            await send_text(number, "⚠️ Conta não vinculada.")
            return
        meals = await MealService(db).list_meals(user.id, limit=7)

    if not meals:
        await send_text(number, "📭 Nenhuma refeição registrada ainda.")
        return

    lines = []
    for meal in meals:
        total_cal = sum(it.calories for it in meal.items)
        items_preview = ", ".join(it.food_name for it in meal.items[:2])
        if len(meal.items) > 2:
            items_preview += f" +{len(meal.items) - 2}"
        lines.append(
            f"{meal_type_emoji(meal.meal_type)} *{meal.date.strftime('%d/%m')}* "
            f"{meal_type_label(meal.meal_type)} — {items_preview} ({total_cal:.0f} kcal)"
        )

    await send_text(number, "🍽️ *Últimas refeições*\n\n" + "\n".join(lines))


async def _cmd_peso(number: str, args: list[str]) -> None:
    if not args:
        await send_text(number, "ℹ️ Use: *!peso 80.5*")
        return
    try:
        weight = float(args[0].replace(",", "."))
    except ValueError:
        await send_text(number, "❌ Peso inválido. Exemplo: *!peso 80.5*")
        return

    async with AsyncSessionLocal() as db:
        user = await WhatsAppService(db).get_user_by_number(number)
        if not user:
            await send_text(number, "⚠️ Conta não vinculada. Use *!conectar TOKEN*.")
            return
        await WeightService(db).create(
            user.id, WeightLogCreate(weight_kg=weight, date=date.today())
        )

    motivation = "Continue assim! 💪" if (user.weight_goal and weight <= user.weight_goal) else "Registrado! 📊"
    await send_text(number, f"⚖️ Peso *{weight:.1f} kg* registrado. {motivation}")


async def _cmd_agua(number: str, args: list[str]) -> None:
    if not args:
        await send_text(number, "ℹ️ Use: *!agua 300* (em ml)")
        return
    try:
        ml = int(args[0])
        if ml <= 0:
            raise ValueError
    except ValueError:
        await send_text(number, "❌ Valor inválido. Exemplo: *!agua 300*")
        return

    async with AsyncSessionLocal() as db:
        user = await WhatsAppService(db).get_user_by_number(number)
        if not user:
            await send_text(number, "⚠️ Conta não vinculada. Use *!conectar TOKEN*.")
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
    await send_text(
        number,
        f"💧 *+{ml} ml* registrado!\n\n"
        f"{bar}\n"
        f"Total hoje: *{total} ml* / {goal} ml ({pct:.0f}%)"
    )


async def _cmd_humor(number: str, args: list[str]) -> None:
    if len(args) < 2:
        await send_text(
            number,
            "ℹ️ Use: *!humor ENERGIA HUMOR* (valores de 1 a 5)\n"
            "Exemplo: *!humor 4 5*"
        )
        return
    try:
        energy = int(args[0])
        mood = int(args[1])
        if not (1 <= energy <= 5 and 1 <= mood <= 5):
            raise ValueError
    except ValueError:
        await send_text(number, "❌ Valores devem ser entre 1 e 5.")
        return

    notes = " ".join(args[2:]) if len(args) > 2 else None

    async with AsyncSessionLocal() as db:
        user = await WhatsAppService(db).get_user_by_number(number)
        if not user:
            await send_text(number, "⚠️ Conta não vinculada. Use *!conectar TOKEN*.")
            return
        await MoodService(db).create(
            user.id,
            MoodLogCreate(date=date.today(), energy_level=energy, mood_level=mood, notes=notes),
        )

    energy_emoji = ["😴", "😪", "😐", "😊", "⚡"][energy - 1]
    mood_emoji = ["😞", "😕", "😐", "😊", "😄"][mood - 1]
    await send_text(
        number,
        f"✅ Registrado!\n\n"
        f"⚡ Energia: {energy_emoji} {energy}/5\n"
        f"😊 Humor: {mood_emoji} {mood}/5"
        + (f"\n📝 {notes}" if notes else "")
    )


async def _cmd_lembrete(number: str, args: list[str]) -> None:
    if len(args) < 2:
        await send_text(
            number,
            "ℹ️ Use: *!lembrete TIPO HH:MM*\n"
            "Tipos: cafe, almoco, janta, agua, peso, resumo\n"
            "Exemplo: *!lembrete cafe 07:30*"
        )
        return

    type_str = args[0].lower()
    time_str = args[1]
    reminder_type = _REMINDER_TYPE_MAP.get(type_str)
    if not reminder_type:
        await send_text(number, f"❌ Tipo inválido: {type_str}")
        return

    try:
        h, m = map(int, time_str.split(":"))
        reminder_time = time(h, m)
    except ValueError:
        await send_text(number, "❌ Hora inválida. Use o formato HH:MM (ex: 07:30)")
        return

    async with AsyncSessionLocal() as db:
        user = await WhatsAppService(db).get_user_by_number(number)
        if not user:
            await send_text(number, "⚠️ Conta não vinculada.")
            return
        reminder = await ReminderService(db).create(
            user.id,
            ReminderCreate(
                type=reminder_type,
                time=reminder_time,
                channel=ReminderChannel.WHATSAPP,
                days_of_week=[0, 1, 2, 3, 4, 5, 6],
            ),
        )

    await send_text(
        number,
        f"✅ Lembrete criado!\n\n"
        f"⏰ Tipo: *{type_str}*\n"
        f"🕐 Hora: *{time_str}*\n"
        f"📅 Todos os dias\n"
        f"🆔 ID: {reminder.id}"
    )


async def _cmd_lembretes(number: str, args: list[str]) -> None:
    async with AsyncSessionLocal() as db:
        user = await WhatsAppService(db).get_user_by_number(number)
        if not user:
            await send_text(number, "⚠️ Conta não vinculada.")
            return
        reminders = await ReminderService(db).list(user.id)

    if not reminders:
        await send_text(number, "📭 Nenhum lembrete configurado.")
        return

    days_abbr = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    lines = []
    for r in reminders:
        days = ", ".join(days_abbr[d] for d in r.days_of_week) if r.days_of_week != list(range(7)) else "Todos os dias"
        status = "✅" if r.active else "⏸️"
        lines.append(f"{status} #{r.id} {r.type.value} — {r.time.strftime('%H:%M')} ({days})")

    await send_text(number, "⏰ *Seus lembretes*\n\n" + "\n".join(lines))


async def _cmd_remover_lembrete(number: str, args: list[str]) -> None:
    if not args:
        await send_text(number, "ℹ️ Use: *!remover-lembrete ID*")
        return
    try:
        reminder_id = int(args[0])
    except ValueError:
        await send_text(number, "❌ ID inválido.")
        return

    async with AsyncSessionLocal() as db:
        user = await WhatsAppService(db).get_user_by_number(number)
        if not user:
            await send_text(number, "⚠️ Conta não vinculada.")
            return
        deleted = await ReminderService(db).delete(user.id, reminder_id)

    if deleted:
        await send_text(number, f"✅ Lembrete #{reminder_id} removido.")
    else:
        await send_text(number, f"❌ Lembrete #{reminder_id} não encontrado.")

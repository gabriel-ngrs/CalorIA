from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.reminder import Reminder, ReminderChannel, ReminderType
from app.models.user import User
from app.models.weight_log import WeightLog
from app.schemas.logs import HydrationDaySummary
from app.workers.tasks.maintenance import (
    _cleanup_old_conversations_async,
    _recalculate_tdee_async,
)
from app.workers.tasks.reminders import (
    _dispatch_due_reminders_async,
    _send_hydration_reminders_async,
)
from app.workers.tasks.reports import (
    _send_daily_summaries_async,
    _send_weekly_reports_async,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_session_cm(db_mock: Any) -> MagicMock:
    """Cria um async context manager mock para AsyncSessionLocal."""
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=db_mock)
    cm.__aexit__ = AsyncMock(return_value=None)
    return cm


def _make_execute_result(
    scalars_list: list[Any] | None = None,
    scalar_one_or_none: Any = None,
) -> MagicMock:
    result = MagicMock()
    if scalars_list is not None:
        result.scalars.return_value.all.return_value = scalars_list
    result.scalar_one_or_none.return_value = scalar_one_or_none
    return result


def _make_user(
    *,
    id: int = 1,
    telegram_chat_id: str | None = "123456",
    whatsapp_number: str | None = None,
    is_active: bool = True,
    calorie_goal: int | None = 2000,
) -> MagicMock:
    """Cria um mock simples que imita um objeto User."""
    user: MagicMock = MagicMock(spec=User)
    user.id = id
    user.email = f"user{id}@test.com"
    user.name = f"User {id}"
    user.password_hash = "x"
    user.is_active = is_active
    user.telegram_chat_id = telegram_chat_id
    user.whatsapp_number = whatsapp_number
    user.calorie_goal = calorie_goal
    user.weight_goal = None
    user.water_goal_ml = None
    user.goal_type = None
    user.profile = None
    return user


def _make_reminder(
    *,
    user: Any,
    channel: ReminderChannel = ReminderChannel.TELEGRAM,
    reminder_time: datetime | None = None,
) -> MagicMock:
    """Cria um mock simples que imita um objeto Reminder."""
    now = reminder_time or datetime.now()
    r: MagicMock = MagicMock(spec=Reminder)
    r.id = 1
    r.user_id = user.id
    r.type = ReminderType.MEAL
    r.time = now.time()
    r.days_of_week = [now.weekday()]
    r.active = True
    r.channel = channel
    r.message = None
    r.user = user
    return r


# ---------------------------------------------------------------------------
# TestDispatchDueReminders
# ---------------------------------------------------------------------------


class TestDispatchDueReminders:
    async def test_telegram_reminder_sent_when_time_matches(self) -> None:
        user = _make_user(telegram_chat_id="chat_99")
        reminder = _make_reminder(user=user, channel=ReminderChannel.TELEGRAM)

        db_mock = AsyncMock()
        db_mock.execute = AsyncMock(return_value=_make_execute_result(scalars_list=[reminder]))

        with (
            patch("app.workers.tasks.reminders.AsyncSessionLocal", return_value=_make_session_cm(db_mock)),
            patch("app.workers.tasks.reminders._send_telegram", new_callable=AsyncMock) as mock_telegram,
        ):
            await _dispatch_due_reminders_async()

        mock_telegram.assert_awaited_once()
        args = mock_telegram.call_args[0]
        assert args[0] == "chat_99"

    async def test_reminder_skipped_when_wrong_day(self) -> None:
        user = _make_user()
        now = datetime.now()
        reminder = _make_reminder(user=user)
        # Override days_of_week to a day that is NOT today
        reminder.days_of_week = [(now.weekday() + 1) % 7]

        db_mock = AsyncMock()
        db_mock.execute = AsyncMock(return_value=_make_execute_result(scalars_list=[reminder]))

        with (
            patch("app.workers.tasks.reminders.AsyncSessionLocal", return_value=_make_session_cm(db_mock)),
            patch("app.workers.tasks.reminders._send_telegram", new_callable=AsyncMock) as mock_telegram,
        ):
            await _dispatch_due_reminders_async()

        mock_telegram.assert_not_awaited()

    async def test_reminder_skipped_when_wrong_time(self) -> None:
        user = _make_user()
        now = datetime.now()
        # Set reminder time 1 hour in the future
        future_time = (now + timedelta(hours=1)).time()
        reminder = _make_reminder(user=user)
        reminder.time = future_time
        reminder.days_of_week = [now.weekday()]

        db_mock = AsyncMock()
        db_mock.execute = AsyncMock(return_value=_make_execute_result(scalars_list=[reminder]))

        with (
            patch("app.workers.tasks.reminders.AsyncSessionLocal", return_value=_make_session_cm(db_mock)),
            patch("app.workers.tasks.reminders._send_telegram", new_callable=AsyncMock) as mock_telegram,
        ):
            await _dispatch_due_reminders_async()

        mock_telegram.assert_not_awaited()

    async def test_whatsapp_reminder_sent(self) -> None:
        user = _make_user(telegram_chat_id=None, whatsapp_number="+5511999990000")
        reminder = _make_reminder(user=user, channel=ReminderChannel.WHATSAPP)

        db_mock = AsyncMock()
        db_mock.execute = AsyncMock(return_value=_make_execute_result(scalars_list=[reminder]))

        mock_send_text = AsyncMock()

        with (
            patch("app.workers.tasks.reminders.AsyncSessionLocal", return_value=_make_session_cm(db_mock)),
            patch("app.workers.tasks.reminders._send_telegram", new_callable=AsyncMock) as mock_tg,
            # The function imports send_text inline from app.bots.whatsapp.sender
            patch("app.bots.whatsapp.sender.send_text", mock_send_text),
        ):
            await _dispatch_due_reminders_async()

        mock_tg.assert_not_awaited()
        mock_send_text.assert_awaited_once()
        args = mock_send_text.call_args[0]
        assert args[0] == "+5511999990000"


# ---------------------------------------------------------------------------
# TestSendHydrationReminders
# ---------------------------------------------------------------------------


class TestSendHydrationReminders:
    async def test_hydration_reminder_sent_when_below_goal(self) -> None:
        user = _make_user(telegram_chat_id="chat_77")
        summary = HydrationDaySummary(date=date.today(), total_ml=500, entries=[])

        db_mock = AsyncMock()
        db_mock.execute = AsyncMock(return_value=_make_execute_result(scalars_list=[user]))

        mock_hydration_service = MagicMock()
        mock_hydration_service.return_value.get_day_summary = AsyncMock(return_value=summary)

        # HydrationService is imported locally inside the function
        with (
            patch("app.workers.tasks.reminders.AsyncSessionLocal", return_value=_make_session_cm(db_mock)),
            patch("app.services.log_service.HydrationService", mock_hydration_service),
            patch("app.workers.tasks.reminders._send_telegram", new_callable=AsyncMock) as mock_telegram,
        ):
            await _send_hydration_reminders_async()

        mock_telegram.assert_awaited_once()
        args = mock_telegram.call_args[0]
        assert args[0] == "chat_77"
        assert "500" in args[1]

    async def test_no_reminder_when_goal_reached(self) -> None:
        user = _make_user(telegram_chat_id="chat_77")
        summary = HydrationDaySummary(date=date.today(), total_ml=2000, entries=[])

        db_mock = AsyncMock()
        db_mock.execute = AsyncMock(return_value=_make_execute_result(scalars_list=[user]))

        mock_hydration_service = MagicMock()
        mock_hydration_service.return_value.get_day_summary = AsyncMock(return_value=summary)

        with (
            patch("app.workers.tasks.reminders.AsyncSessionLocal", return_value=_make_session_cm(db_mock)),
            patch("app.services.log_service.HydrationService", mock_hydration_service),
            patch("app.workers.tasks.reminders._send_telegram", new_callable=AsyncMock) as mock_telegram,
        ):
            await _send_hydration_reminders_async()

        mock_telegram.assert_not_awaited()

    async def test_skipped_when_no_channel(self) -> None:
        user = _make_user(telegram_chat_id=None, whatsapp_number=None)
        summary = HydrationDaySummary(date=date.today(), total_ml=100, entries=[])

        db_mock = AsyncMock()
        db_mock.execute = AsyncMock(return_value=_make_execute_result(scalars_list=[user]))

        mock_hydration_service = MagicMock()
        mock_hydration_service.return_value.get_day_summary = AsyncMock(return_value=summary)

        with (
            patch("app.workers.tasks.reminders.AsyncSessionLocal", return_value=_make_session_cm(db_mock)),
            patch("app.services.log_service.HydrationService", mock_hydration_service),
            patch("app.workers.tasks.reminders._send_telegram", new_callable=AsyncMock) as mock_telegram,
        ):
            await _send_hydration_reminders_async()

        mock_telegram.assert_not_awaited()
        # HydrationService should not have been called since user has no channels
        mock_hydration_service.assert_not_called()


# ---------------------------------------------------------------------------
# TestCleanupOldConversations
# ---------------------------------------------------------------------------


class TestCleanupOldConversations:
    async def test_deletes_old_conversations(self) -> None:
        deleted_result = MagicMock()
        deleted_result.scalars.return_value.all.return_value = [1, 2, 3]

        db_mock = AsyncMock()
        db_mock.execute = AsyncMock(return_value=deleted_result)
        db_mock.commit = AsyncMock()

        with patch(
            "app.workers.tasks.maintenance.AsyncSessionLocal",
            return_value=_make_session_cm(db_mock),
        ):
            await _cleanup_old_conversations_async()

        db_mock.commit.assert_awaited_once()

    async def test_no_error_when_nothing_to_delete(self) -> None:
        deleted_result = MagicMock()
        deleted_result.scalars.return_value.all.return_value = []

        db_mock = AsyncMock()
        db_mock.execute = AsyncMock(return_value=deleted_result)
        db_mock.commit = AsyncMock()

        with patch(
            "app.workers.tasks.maintenance.AsyncSessionLocal",
            return_value=_make_session_cm(db_mock),
        ):
            # Should complete without errors even when nothing is deleted
            await _cleanup_old_conversations_async()

        # commit is still called (no conditional commit in cleanup)
        db_mock.commit.assert_awaited_once()


# ---------------------------------------------------------------------------
# TestRecalculateTdee
# ---------------------------------------------------------------------------


def _make_profile(
    *,
    user_id: int = 1,
    current_weight: float | None = 80.0,
    height_cm: float | None = 175.0,
    age: int | None = 30,
    sex: Any = None,
    activity_level: Any = None,
) -> MagicMock:
    """Cria um mock simples que imita um objeto UserProfile."""
    from app.models.profile import ActivityLevel, Sex, UserProfile

    p: MagicMock = MagicMock(spec=UserProfile)
    p.id = 1
    p.user_id = user_id
    p.current_weight = current_weight
    p.height_cm = height_cm
    p.age = age
    p.sex = sex or Sex.MALE
    p.activity_level = activity_level or ActivityLevel.SEDENTARY
    p.tdee_calculated = None
    return p


class TestRecalculateTdee:
    async def test_updates_tdee_when_weight_diff_significant(self) -> None:
        user = _make_user(id=1)
        user.profile = _make_profile(current_weight=80.0)  # type: ignore[assignment]

        latest_wl = MagicMock(spec=WeightLog)
        latest_wl.id = 1
        latest_wl.user_id = 1
        latest_wl.weight_kg = 83.0  # diff = 3.0 >= 2.0
        latest_wl.date = date.today()

        users_result = _make_execute_result(scalars_list=[user])
        wl_result = MagicMock()
        wl_result.scalar_one_or_none.return_value = latest_wl

        db_mock = AsyncMock()
        db_mock.execute = AsyncMock(side_effect=[users_result, wl_result])
        db_mock.commit = AsyncMock()

        with (
            patch("app.workers.tasks.maintenance.AsyncSessionLocal", return_value=_make_session_cm(db_mock)),
            patch("app.services.nutrition.tdee.calculate_tdee", return_value=2100.0),
        ):
            await _recalculate_tdee_async()

        db_mock.commit.assert_awaited_once()
        assert user.profile.current_weight == 83.0

    async def test_skips_when_diff_small(self) -> None:
        user = _make_user(id=1)
        user.profile = _make_profile(current_weight=80.0)  # type: ignore[assignment]

        latest_wl = MagicMock(spec=WeightLog)
        latest_wl.id = 1
        latest_wl.user_id = 1
        latest_wl.weight_kg = 80.5  # diff = 0.5 < 2.0
        latest_wl.date = date.today()

        users_result = _make_execute_result(scalars_list=[user])
        wl_result = MagicMock()
        wl_result.scalar_one_or_none.return_value = latest_wl

        db_mock = AsyncMock()
        db_mock.execute = AsyncMock(side_effect=[users_result, wl_result])
        db_mock.commit = AsyncMock()

        with patch(
            "app.workers.tasks.maintenance.AsyncSessionLocal",
            return_value=_make_session_cm(db_mock),
        ):
            await _recalculate_tdee_async()

        db_mock.commit.assert_not_awaited()

    async def test_skips_user_without_profile(self) -> None:
        user = _make_user(id=1)
        user.profile = None  # type: ignore[assignment]

        users_result = _make_execute_result(scalars_list=[user])

        db_mock = AsyncMock()
        db_mock.execute = AsyncMock(return_value=users_result)
        db_mock.commit = AsyncMock()

        with patch(
            "app.workers.tasks.maintenance.AsyncSessionLocal",
            return_value=_make_session_cm(db_mock),
        ):
            await _recalculate_tdee_async()

        db_mock.commit.assert_not_awaited()


# ---------------------------------------------------------------------------
# TestSendDailySummaries
# ---------------------------------------------------------------------------


class TestSendDailySummaries:
    async def test_sends_to_telegram_users(self) -> None:
        user = _make_user(telegram_chat_id="chat_55")

        users_result = _make_execute_result(scalars_list=[user])

        db_mock = AsyncMock()
        db_mock.execute = AsyncMock(return_value=users_result)

        from app.schemas.ai import InsightResponse

        mock_insight = InsightResponse(type="daily", content="Ótimo dia!")

        mock_generator_instance = MagicMock()
        mock_generator_instance.daily_insight = AsyncMock(return_value=mock_insight)

        mock_generator_cls = MagicMock(return_value=mock_generator_instance)
        mock_gemini_cls = MagicMock()

        # _send_daily_summary_to_user opens its own session and imports locally
        inner_db_mock = AsyncMock()
        inner_session_cm = _make_session_cm(inner_db_mock)

        with (
            patch("app.workers.tasks.reports.AsyncSessionLocal", return_value=_make_session_cm(db_mock)),
            patch("app.workers.tasks.reports._send_telegram", new_callable=AsyncMock) as mock_telegram,
            # Patch the locally-imported names inside _send_daily_summary_to_user
            patch("app.core.database.AsyncSessionLocal", return_value=inner_session_cm),
            patch("app.services.ai.gemini_client.GeminiClient", mock_gemini_cls),
            patch("app.services.ai.insights_generator.InsightsGenerator", mock_generator_cls),
        ):
            await _send_daily_summaries_async()

        mock_telegram.assert_awaited_once()
        call_args = mock_telegram.call_args[0]
        assert call_args[0] == "chat_55"
        assert "Ótimo dia!" in call_args[1]

    async def test_skips_users_without_channels(self) -> None:
        user = _make_user(telegram_chat_id=None, whatsapp_number=None)

        users_result = _make_execute_result(scalars_list=[user])

        db_mock = AsyncMock()
        db_mock.execute = AsyncMock(return_value=users_result)

        with (
            patch("app.workers.tasks.reports.AsyncSessionLocal", return_value=_make_session_cm(db_mock)),
            patch("app.workers.tasks.reports._send_telegram", new_callable=AsyncMock) as mock_telegram,
        ):
            await _send_daily_summaries_async()

        mock_telegram.assert_not_awaited()


# ---------------------------------------------------------------------------
# TestSendWeeklyReports
# ---------------------------------------------------------------------------


class TestSendWeeklyReports:
    async def test_sends_to_telegram_users(self) -> None:
        user = _make_user(telegram_chat_id="chat_weekly")

        users_result = _make_execute_result(scalars_list=[user])

        db_mock = AsyncMock()
        db_mock.execute = AsyncMock(return_value=users_result)

        from app.schemas.ai import InsightResponse

        mock_insight = InsightResponse(type="weekly", content="Boa semana!")

        mock_generator_instance = MagicMock()
        mock_generator_instance.weekly_insight = AsyncMock(return_value=mock_insight)

        mock_generator_cls = MagicMock(return_value=mock_generator_instance)
        mock_gemini_cls = MagicMock()

        inner_db_mock = AsyncMock()
        inner_session_cm = _make_session_cm(inner_db_mock)

        with (
            patch("app.workers.tasks.reports.AsyncSessionLocal", return_value=_make_session_cm(db_mock)),
            patch("app.workers.tasks.reports._send_telegram", new_callable=AsyncMock) as mock_telegram,
            patch("app.core.database.AsyncSessionLocal", return_value=inner_session_cm),
            patch("app.services.ai.gemini_client.GeminiClient", mock_gemini_cls),
            patch("app.services.ai.insights_generator.InsightsGenerator", mock_generator_cls),
        ):
            await _send_weekly_reports_async()

        mock_telegram.assert_awaited_once()
        call_args = mock_telegram.call_args[0]
        assert call_args[0] == "chat_weekly"
        assert "Boa semana!" in call_args[1]

    async def test_skips_users_without_channels(self) -> None:
        user = _make_user(telegram_chat_id=None, whatsapp_number=None)

        users_result = _make_execute_result(scalars_list=[user])

        db_mock = AsyncMock()
        db_mock.execute = AsyncMock(return_value=users_result)

        with (
            patch("app.workers.tasks.reports.AsyncSessionLocal", return_value=_make_session_cm(db_mock)),
            patch("app.workers.tasks.reports._send_telegram", new_callable=AsyncMock) as mock_telegram,
        ):
            await _send_weekly_reports_async()

        mock_telegram.assert_not_awaited()

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.reminder import Reminder, ReminderType
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
    is_active: bool = True,
    calorie_goal: int | None = 2000,
) -> MagicMock:
    """Cria um mock simples que imita um objeto User."""
    user: MagicMock = MagicMock(spec=User)
    user.id = id
    user.email = f"user{id}@test.com"
    user.name = f"User {id}"
    user.is_active = is_active
    user.calorie_goal = calorie_goal
    user.water_goal_ml = 2000
    user.goal_type = None
    user.profile = None
    return user


def _make_reminder(
    *,
    user: Any,
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
    r.message = None
    r.user = user
    return r


# ---------------------------------------------------------------------------
# TestDispatchDueReminders
# ---------------------------------------------------------------------------


class TestDispatchDueReminders:
    async def test_reminder_dispatched_when_time_matches(self) -> None:
        user = _make_user()
        reminder = _make_reminder(user=user)

        db_mock = AsyncMock()
        db_mock.execute = AsyncMock(
            return_value=_make_execute_result(scalars_list=[reminder])
        )

        with (
            patch(
                "app.workers.tasks.reminders.AsyncSessionLocal",
                return_value=_make_session_cm(db_mock),
            ),
            patch(
                "app.workers.tasks.reminders._send_reminder_notification",
                new_callable=AsyncMock,
            ) as mock_send,
        ):
            await _dispatch_due_reminders_async()

        mock_send.assert_awaited_once_with(user, reminder)

    async def test_reminder_skipped_when_wrong_day(self) -> None:
        user = _make_user()
        now = datetime.now()
        reminder = _make_reminder(user=user)
        reminder.days_of_week = [(now.weekday() + 1) % 7]

        db_mock = AsyncMock()
        db_mock.execute = AsyncMock(
            return_value=_make_execute_result(scalars_list=[reminder])
        )

        with (
            patch(
                "app.workers.tasks.reminders.AsyncSessionLocal",
                return_value=_make_session_cm(db_mock),
            ),
            patch(
                "app.workers.tasks.reminders._send_reminder_notification",
                new_callable=AsyncMock,
            ) as mock_send,
        ):
            await _dispatch_due_reminders_async()

        mock_send.assert_not_awaited()

    async def test_reminder_skipped_when_wrong_time(self) -> None:
        user = _make_user()
        now = datetime.now()
        future_time = (now + timedelta(hours=1)).time()
        reminder = _make_reminder(user=user)
        reminder.time = future_time
        reminder.days_of_week = [now.weekday()]

        db_mock = AsyncMock()
        db_mock.execute = AsyncMock(
            return_value=_make_execute_result(scalars_list=[reminder])
        )

        with (
            patch(
                "app.workers.tasks.reminders.AsyncSessionLocal",
                return_value=_make_session_cm(db_mock),
            ),
            patch(
                "app.workers.tasks.reminders._send_reminder_notification",
                new_callable=AsyncMock,
            ) as mock_send,
        ):
            await _dispatch_due_reminders_async()

        mock_send.assert_not_awaited()

    async def test_reminder_skipped_when_no_user(self) -> None:
        user = _make_user()
        reminder = _make_reminder(user=user)
        reminder.user = None

        db_mock = AsyncMock()
        db_mock.execute = AsyncMock(
            return_value=_make_execute_result(scalars_list=[reminder])
        )

        with (
            patch(
                "app.workers.tasks.reminders.AsyncSessionLocal",
                return_value=_make_session_cm(db_mock),
            ),
            patch(
                "app.workers.tasks.reminders._send_reminder_notification",
                new_callable=AsyncMock,
            ) as mock_send,
        ):
            await _dispatch_due_reminders_async()

        mock_send.assert_not_awaited()


# ---------------------------------------------------------------------------
# TestSendHydrationReminders
# ---------------------------------------------------------------------------


class TestSendHydrationReminders:
    async def test_hydration_reminder_sent_when_below_goal(self) -> None:
        user = _make_user()
        summary = HydrationDaySummary(date=date.today(), total_ml=500, entries=[])

        db_mock = AsyncMock()
        db_mock.execute = AsyncMock(
            return_value=_make_execute_result(scalars_list=[user])
        )
        db_mock.add = MagicMock()
        db_mock.flush = AsyncMock()
        db_mock.commit = AsyncMock()

        mock_hydration_service = MagicMock()
        mock_hydration_service.return_value.get_day_summary = AsyncMock(
            return_value=summary
        )

        mock_subs_result = _make_execute_result(scalars_list=[])

        async def multi_execute(*args: Any, **kwargs: Any) -> Any:
            return mock_subs_result

        db_mock.execute = AsyncMock(
            side_effect=[
                _make_execute_result(scalars_list=[user]),  # select users
                mock_subs_result,  # select push subscriptions
            ]
        )

        with (
            patch(
                "app.workers.tasks.reminders.AsyncSessionLocal",
                return_value=_make_session_cm(db_mock),
            ),
            patch("app.services.log_service.HydrationService", mock_hydration_service),
        ):
            await _send_hydration_reminders_async()

        mock_hydration_service.return_value.get_day_summary.assert_awaited_once()
        db_mock.commit.assert_awaited_once()

    async def test_no_reminder_when_goal_reached(self) -> None:
        user = _make_user()
        summary = HydrationDaySummary(date=date.today(), total_ml=2000, entries=[])

        db_mock = AsyncMock()
        db_mock.execute = AsyncMock(
            return_value=_make_execute_result(scalars_list=[user])
        )
        db_mock.add = MagicMock()
        db_mock.commit = AsyncMock()

        mock_hydration_service = MagicMock()
        mock_hydration_service.return_value.get_day_summary = AsyncMock(
            return_value=summary
        )

        with (
            patch(
                "app.workers.tasks.reminders.AsyncSessionLocal",
                return_value=_make_session_cm(db_mock),
            ),
            patch("app.services.log_service.HydrationService", mock_hydration_service),
        ):
            await _send_hydration_reminders_async()

        # Meta atingida — nenhuma notificação criada
        db_mock.add.assert_not_called()
        db_mock.commit.assert_awaited_once()


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
            await _cleanup_old_conversations_async()

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
            patch(
                "app.workers.tasks.maintenance.AsyncSessionLocal",
                return_value=_make_session_cm(db_mock),
            ),
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

        with (
            patch(
                "app.workers.tasks.maintenance.AsyncSessionLocal",
                return_value=_make_session_cm(db_mock),
            ),
            patch("app.services.nutrition.tdee.calculate_tdee", return_value=2100.0),
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
    async def test_calls_send_to_user_for_each_active_user(self) -> None:
        user = _make_user()

        users_result = _make_execute_result(scalars_list=[user])

        db_mock = AsyncMock()
        db_mock.execute = AsyncMock(return_value=users_result)

        with (
            patch(
                "app.workers.tasks.reports.AsyncSessionLocal",
                return_value=_make_session_cm(db_mock),
            ),
            patch(
                "app.workers.tasks.reports._send_daily_summary_to_user",
                new_callable=AsyncMock,
            ) as mock_send,
        ):
            await _send_daily_summaries_async()

        mock_send.assert_awaited_once()

    async def test_continues_on_user_error(self) -> None:
        user1 = _make_user(id=1)
        user2 = _make_user(id=2)

        users_result = _make_execute_result(scalars_list=[user1, user2])

        db_mock = AsyncMock()
        db_mock.execute = AsyncMock(return_value=users_result)

        call_count = 0

        async def side_effect(user: Any, today: Any) -> None:
            nonlocal call_count
            call_count += 1
            if user.id == 1:
                raise RuntimeError("Erro simulado")

        with (
            patch(
                "app.workers.tasks.reports.AsyncSessionLocal",
                return_value=_make_session_cm(db_mock),
            ),
            patch(
                "app.workers.tasks.reports._send_daily_summary_to_user",
                side_effect=side_effect,
            ),
        ):
            await _send_daily_summaries_async()

        assert call_count == 2


# ---------------------------------------------------------------------------
# TestSendWeeklyReports
# ---------------------------------------------------------------------------


class TestSendWeeklyReports:
    async def test_calls_send_to_user_for_each_active_user(self) -> None:
        user = _make_user()

        users_result = _make_execute_result(scalars_list=[user])

        db_mock = AsyncMock()
        db_mock.execute = AsyncMock(return_value=users_result)

        with (
            patch(
                "app.workers.tasks.reports.AsyncSessionLocal",
                return_value=_make_session_cm(db_mock),
            ),
            patch(
                "app.workers.tasks.reports._send_weekly_report_to_user",
                new_callable=AsyncMock,
            ) as mock_send,
        ):
            await _send_weekly_reports_async()

        mock_send.assert_awaited_once()

    async def test_continues_on_user_error(self) -> None:
        user1 = _make_user(id=1)
        user2 = _make_user(id=2)

        users_result = _make_execute_result(scalars_list=[user1, user2])

        db_mock = AsyncMock()
        db_mock.execute = AsyncMock(return_value=users_result)

        call_count = 0

        async def side_effect(user: Any, today: Any) -> None:
            nonlocal call_count
            call_count += 1
            if user.id == 1:
                raise RuntimeError("Erro simulado")

        with (
            patch(
                "app.workers.tasks.reports.AsyncSessionLocal",
                return_value=_make_session_cm(db_mock),
            ),
            patch(
                "app.workers.tasks.reports._send_weekly_report_to_user",
                side_effect=side_effect,
            ),
        ):
            await _send_weekly_reports_async()

        assert call_count == 2

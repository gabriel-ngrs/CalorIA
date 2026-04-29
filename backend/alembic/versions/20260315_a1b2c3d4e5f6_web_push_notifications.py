"""web push notifications — remove telegram/whatsapp, add push_subscriptions and notifications

Revision ID: 20260315_webpush
Revises: f1a2b3c4d5e6
Create Date: 2026-03-15 00:00:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260315_webpush"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Remove telegram_chat_id and whatsapp_number from users
    # ------------------------------------------------------------------
    op.drop_index("ix_users_telegram_chat_id", table_name="users", if_exists=True)
    op.drop_index("ix_users_whatsapp_number", table_name="users", if_exists=True)
    op.drop_column("users", "telegram_chat_id")
    op.drop_column("users", "whatsapp_number")

    # ------------------------------------------------------------------
    # 2. Remove channel column from reminders
    # ------------------------------------------------------------------
    op.drop_column("reminders", "channel")

    # Drop the old ReminderChannel enum type if it exists
    op.execute("DROP TYPE IF EXISTS reminderchannel")

    # ------------------------------------------------------------------
    # 3. Create push_subscriptions table
    # ------------------------------------------------------------------
    op.create_table(
        "push_subscriptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("endpoint", sa.Text(), nullable=False),
        sa.Column("p256dh", sa.Text(), nullable=False),
        sa.Column("auth", sa.Text(), nullable=False),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("endpoint"),
    )
    op.create_index("ix_push_subscriptions_user_id", "push_subscriptions", ["user_id"])

    # ------------------------------------------------------------------
    # 4. Create notifications table
    # ------------------------------------------------------------------
    notification_type_enum = postgresql.ENUM(
        "reminder",
        "daily_summary",
        "weekly_report",
        "hydration",
        "system",
        name="notificationtype",
        create_type=True,
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("type", notification_type_enum, nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])


def downgrade() -> None:
    # ------------------------------------------------------------------
    # 4. Drop notifications table
    # ------------------------------------------------------------------
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")
    op.execute("DROP TYPE IF EXISTS notificationtype")

    # ------------------------------------------------------------------
    # 3. Drop push_subscriptions table
    # ------------------------------------------------------------------
    op.drop_index("ix_push_subscriptions_user_id", table_name="push_subscriptions")
    op.drop_table("push_subscriptions")

    # ------------------------------------------------------------------
    # 2. Re-add channel column to reminders
    # ------------------------------------------------------------------
    reminder_channel_enum = postgresql.ENUM(
        "telegram",
        "whatsapp",
        name="reminderchannel",
        create_type=True,
    )
    op.add_column(
        "reminders",
        sa.Column("channel", reminder_channel_enum, nullable=True),
    )

    # ------------------------------------------------------------------
    # 1. Re-add telegram_chat_id and whatsapp_number to users
    # ------------------------------------------------------------------
    op.add_column(
        "users",
        sa.Column("telegram_chat_id", sa.String(50), nullable=True, unique=True),
    )
    op.add_column(
        "users",
        sa.Column("whatsapp_number", sa.String(30), nullable=True, unique=True),
    )
    op.create_index("ix_users_telegram_chat_id", "users", ["telegram_chat_id"], unique=True)
    op.create_index("ix_users_whatsapp_number", "users", ["whatsapp_number"], unique=True)

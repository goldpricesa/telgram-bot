"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-11 00:00:00
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY, JSONB

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"
    json_type = sa.Text() if is_sqlite else JSONB()
    bigint_array = sa.Text() if is_sqlite else ARRAY(sa.BigInteger())

    op.create_table(
        "users",
        sa.Column("telegram_id", sa.BigInteger(), primary_key=True),
        sa.Column("username", sa.String(64), nullable=True),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("language_code", sa.String(8), nullable=True),
        sa.Column("total_violations", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("muted_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_banned", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "chats",
        sa.Column("chat_id", sa.BigInteger(), primary_key=True),
        sa.Column("type", sa.String(16), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("rules_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("moderation_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("warned_missing_rights", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "admins",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=True, unique=True),
        sa.Column("web_username", sa.String(64), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(128), nullable=False),
        sa.Column("role", sa.String(16), nullable=False, server_default="admin"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "violations",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.telegram_id", ondelete="CASCADE"), nullable=False),
        sa.Column("chat_id", sa.BigInteger(), sa.ForeignKey("chats.chat_id", ondelete="CASCADE"), nullable=False),
        sa.Column("message_text_hash", sa.String(64), nullable=False),
        sa.Column("message_excerpt", sa.String(120), nullable=True),
        sa.Column("reason", sa.String(32), nullable=False),
        sa.Column("severity", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("action_taken", sa.String(16), nullable=False),
        sa.Column("mute_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("classifier_json", json_type, nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_violations_user_created", "violations", ["user_id", "created_at"])

    op.create_table(
        "legal_questions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.telegram_id", ondelete="CASCADE"), nullable=False),
        sa.Column("chat_id", sa.BigInteger(), sa.ForeignKey("chats.chat_id", ondelete="CASCADE"), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("category", sa.String(32), nullable=True),
        sa.Column("retrieved_chunk_ids", bigint_array, nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("model", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_legal_questions_created", "legal_questions", ["created_at"])
    op.create_index("ix_legal_questions_user", "legal_questions", ["user_id"])

    op.create_table(
        "appeals",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.telegram_id", ondelete="CASCADE"), nullable=False),
        sa.Column("violation_id", sa.BigInteger(), sa.ForeignKey("violations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("appeal_text", sa.Text(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="open"),
        sa.Column("reviewer_admin_id", sa.Integer(), sa.ForeignKey("admins.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewer_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "banned_words",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("pattern", sa.String(255), nullable=False),
        sa.Column("is_regex", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("category", sa.String(64), nullable=True),
        sa.Column("added_by", sa.Integer(), sa.ForeignKey("admins.id", ondelete="SET NULL"), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "canned_messages",
        sa.Column("key", sa.String(64), primary_key=True),
        sa.Column("content_ar", sa.Text(), nullable=False),
        sa.Column("updated_by", sa.Integer(), sa.ForeignKey("admins.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "settings",
        sa.Column("key", sa.String(64), primary_key=True),
        sa.Column("value", sa.String(255), nullable=False),
        sa.Column("value_type", sa.String(16), nullable=False, server_default="str"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    for table in (
        "settings",
        "canned_messages",
        "banned_words",
        "appeals",
        "legal_questions",
        "violations",
        "admins",
        "chats",
        "users",
    ):
        op.drop_table(table)

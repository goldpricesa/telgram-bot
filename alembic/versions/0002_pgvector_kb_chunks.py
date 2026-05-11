"""kb_chunks with pgvector (or text fallback on sqlite)

Revision ID: 0002_pgvector_kb_chunks
Revises: 0001_initial
Create Date: 2026-05-11 00:01:00
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0002_pgvector_kb_chunks"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    from app.core.config import get_settings
    dim = get_settings().embedding_dim

    if dialect == "postgresql":
        from pgvector.sqlalchemy import Vector
        embedding_col = sa.Column("embedding", Vector(dim), nullable=True)
        source_urls_col = sa.Column("source_urls", JSONB(), nullable=True)
    else:
        embedding_col = sa.Column("embedding", sa.Text(), nullable=True)
        source_urls_col = sa.Column("source_urls", sa.Text(), nullable=True)

    op.create_table(
        "kb_chunks",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("post_slug", sa.String(255), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        embedding_col,
        source_urls_col,
        sa.Column("reviewed_at", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_kb_chunks_category", "kb_chunks", ["category"])
    op.create_index("ix_kb_chunks_post_slug", "kb_chunks", ["post_slug"])

    if dialect == "postgresql":
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_kb_chunks_embedding "
            "ON kb_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
        )


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    if dialect == "postgresql":
        op.execute("DROP INDEX IF EXISTS ix_kb_chunks_embedding")
    op.drop_table("kb_chunks")

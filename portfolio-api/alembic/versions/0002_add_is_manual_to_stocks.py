"""add is_manual to stocks

Revision ID: 0002_add_is_manual_to_stocks
Revises: 0001_initial_schema
Create Date: 2026-05-23

手動登録された銘柄（札証・名証・福証等）をシードの上場廃止処理から保護するためのフラグ。
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0002_add_is_manual_to_stocks"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    cols = {c["name"] for c in insp.get_columns("stocks")}
    if "is_manual" not in cols:
        op.add_column(
            "stocks",
            sa.Column(
                "is_manual",
                sa.Boolean(),
                server_default=sa.text("false"),
                nullable=False,
            ),
        )


def downgrade() -> None:
    op.drop_column("stocks", "is_manual")

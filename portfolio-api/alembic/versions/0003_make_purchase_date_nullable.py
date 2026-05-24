"""make purchase_date nullable in holdings

Revision ID: 0003_make_purchase_date_nullable
Revises: 0002_add_is_manual_to_stocks
Create Date: 2026-05-24

保有株の購入日（purchase_date）を任意入力とするため、NULL許容に変更する。
"""
from alembic import op


revision = "0003_make_purchase_date_nullable"
down_revision = "0002_add_is_manual_to_stocks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("holdings", "purchase_date", nullable=True)


def downgrade() -> None:
    op.alter_column("holdings", "purchase_date", nullable=False)

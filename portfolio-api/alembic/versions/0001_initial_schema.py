"""initial schema (stocks, holdings)

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-05-21

既存の本番DBには stocks / holdings が既に存在するため、このベースライン移行は
冪等にしてある（テーブルが無ければ作成、stocks に is_active が無ければ追加）。
新規DBでは両テーブルを is_active 付きで作成する。
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    tables = set(insp.get_table_names())

    if "stocks" not in tables:
        op.create_table(
            "stocks",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("ticker_code", sa.String(), nullable=False),
            sa.Column("company_name", sa.String(), nullable=False),
            sa.Column("sector", sa.String(), nullable=True),
            sa.Column(
                "is_active",
                sa.Boolean(),
                server_default=sa.text("true"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_stocks_id", "stocks", ["id"])
        op.create_index("ix_stocks_ticker_code", "stocks", ["ticker_code"], unique=True)
    else:
        cols = {c["name"] for c in insp.get_columns("stocks")}
        if "is_active" not in cols:
            op.add_column(
                "stocks",
                sa.Column(
                    "is_active",
                    sa.Boolean(),
                    server_default=sa.text("true"),
                    nullable=False,
                ),
            )

    if "holdings" not in tables:
        op.create_table(
            "holdings",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("ticker_code", sa.String(), nullable=False),
            sa.Column("purchase_date", sa.Date(), nullable=False),
            sa.Column("purchase_price", sa.Float(), nullable=False),
            sa.Column("quantity", sa.Integer(), nullable=False),
            sa.Column("note", sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(["ticker_code"], ["stocks.ticker_code"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_holdings_id", "holdings", ["id"])


def downgrade() -> None:
    op.drop_index("ix_holdings_id", table_name="holdings")
    op.drop_table("holdings")
    op.drop_index("ix_stocks_ticker_code", table_name="stocks")
    op.drop_index("ix_stocks_id", table_name="stocks")
    op.drop_table("stocks")

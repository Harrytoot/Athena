"""initial_baseline

Revision ID: 001
Revises:
Create Date: 2025-06-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False, server_default=""),
        sa.Column("display_name", sa.String(100), server_default=""),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("uq_users_username", "users", ["username"], unique=True)
    op.create_index("uq_users_email", "users", ["email"], unique=True)

    op.create_table(
        "portfolios",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("cash", sa.Numeric(18, 2), server_default=sa.text("0")),
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_portfolios_user_id", "portfolios", ["user_id"])

    op.create_table(
        "positions",
        sa.Column("portfolio_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("portfolios.id"), nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("shares", sa.Numeric(18, 4), nullable=False),
        sa.Column("cost_price", sa.Numeric(18, 4), nullable=False),
        sa.Column("current_price", sa.Numeric(18, 4), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_positions_portfolio_id", "positions", ["portfolio_id"])

    op.create_table(
        "watchlists",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("color", sa.String(20), server_default="#3b82f6"),
        sa.Column("sort_order", sa.Integer(), server_default=sa.text("0")),
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_watchlists_user_id", "watchlists", ["user_id"])

    op.create_table(
        "watchlist_items",
        sa.Column("watchlist_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("watchlists.id"), nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("tags", postgresql.ARRAY(sa.String), server_default=sa.text("'{}'")),
        sa.Column("note", sa.Text(), server_default=""),
        sa.Column("sort_order", sa.Integer(), server_default=sa.text("0")),
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_watchlist_items_watchlist_id", "watchlist_items", ["watchlist_id"])
    op.create_index("ix_watchlist_items_symbol", "watchlist_items", ["symbol"])


def downgrade() -> None:
    op.drop_index("ix_watchlist_items_symbol", table_name="watchlist_items")
    op.drop_index("ix_watchlist_items_watchlist_id", table_name="watchlist_items")
    op.drop_table("watchlist_items")
    op.drop_index("ix_watchlists_user_id", table_name="watchlists")
    op.drop_table("watchlists")
    op.drop_index("ix_positions_portfolio_id", table_name="positions")
    op.drop_table("positions")
    op.drop_index("ix_portfolios_user_id", table_name="portfolios")
    op.drop_table("portfolios")
    op.drop_index("uq_users_email", table_name="users")
    op.drop_index("uq_users_username", table_name="users")
    op.drop_table("users")
